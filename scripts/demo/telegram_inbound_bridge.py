#!/usr/bin/env python3
"""Local Telegram inbound bridge for the procurement workflow demo.

This script is intentionally local-demo only. It polls Telegram, converts
bounded text requests into existing workflow API calls, optionally runs the
created workflow, and stops at WAITING_APPROVAL for human approval.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from scripts.demo.catalog import (
    CATALOG_ITEMS,
    CATALOG_VERSION,
    CatalogItem,
    addon_display_label,
    compatible_addons,
    detect_requested_addons as detect_catalog_requested_addons,
    find_catalog_item,
    get_catalog_item_by_name,
    normalize_for_catalog_match,
)

DEFAULT_BACKEND_API_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_FRONTEND_BASE_URL = "http://localhost:3000"
DEFAULT_MANAGER_EMAIL = "manager@example.test"
DEFAULT_MANAGER_PASSWORD = "DemoPassword123!"
DEFAULT_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_TELEGRAM_LLM_PROVIDER = "ollama"
DEFAULT_TELEGRAM_LLM_MODEL = "qwen2.5:7b-instruct-q4_K_M"
DEFAULT_TELEGRAM_LLM_BASE_URL = "http://localhost:11434"
DEFAULT_TELEGRAM_LLM_TIMEOUT_SECONDS = 90
EXAMPLE_MESSAGE = (
    "We would like to purchase 50 standard business laptops for a new "
    "operations team. We signed a master agreement in May 2026. Please provide "
    "your best quotation with the applicable discount."
)
MAX_TEXT_LENGTH = 2000
MAX_EVIDENCE_TEXT_LENGTH = 220
MAX_EVIDENCE_URL_LENGTH = 300
MAX_EVIDENCE_ITEMS = 2
HTTP_TIMEOUT_SECONDS = 15
PARSER_VERSION = "telegram-demo-parser-v4"
HELPFUL_REQUEST_PROMPT = (
    "Please include quantity and item.\n"
    "English example: quote for 50 standard business laptops.\n"
    "Ví dụ tiếng Việt: cần báo giá 50 máy tính xách tay."
)


@dataclass(frozen=True)
class BridgeConfig:
    telegram_bot_token: str | None
    backend_api_base_url: str
    frontend_base_url: str
    manager_email: str
    manager_password: str
    poll_interval_seconds: float
    allowed_chat_id: str | None
    dry_run: bool
    once: bool
    auto_run: bool
    llm_extraction_enabled: bool
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_timeout_seconds: int
    sales_replies_enabled: bool


@dataclass(frozen=True)
class ParsedCustomerRequest:
    original_text: str
    quantity: int
    item_name: str
    language: str
    requested_addons: tuple[str, ...] = ()
    extraction_mode: str = "deterministic"
    llm_provider: str | None = None
    llm_model: str | None = None
    catalog_item_id: str | None = None
    item_family: str | None = None
    catalog_version: str = CATALOG_VERSION

    @property
    def summary(self) -> str:
        return f"{self.quantity} x {self.item_name}"

    @property
    def options_summary(self) -> str | None:
        if not self.requested_addons:
            return None
        labels = [addon_display_label(addon) for addon in self.requested_addons]
        return ", ".join(labels)


@dataclass(frozen=True)
class UnsupportedItemMention:
    quantity: int | None
    item_label: str
    display_label: str
    normalized_item_name: str | None = None

    @property
    def summary(self) -> str:
        quantity = f"{self.quantity} x " if self.quantity is not None else ""
        return f"{quantity}{self.display_label}"


@dataclass(frozen=True)
class UnsupportedMixedRequest:
    original_text: str
    language: str
    supported: ParsedCustomerRequest | None
    unsupported_items: tuple[UnsupportedItemMention, ...]

    @property
    def supported_summary(self) -> str:
        return self.supported.summary if self.supported else "none"

    @property
    def unsupported_summary(self) -> str:
        return ", ".join(item.summary for item in self.unsupported_items)


@dataclass(frozen=True)
class WorkflowCreationResult:
    workflow_id: str
    status: str


@dataclass(frozen=True)
class ReferenceEvidenceSourceSummary:
    title: str
    url: str | None = None


@dataclass(frozen=True)
class ReferenceEvidencePriceSummary:
    label: str
    amount: str | None = None
    currency: str | None = None
    unit: str | None = None


@dataclass(frozen=True)
class ReferenceEvidenceSummary:
    provider: str
    evidence_label: str
    reference_prices: tuple[ReferenceEvidencePriceSummary, ...] = ()
    sources: tuple[ReferenceEvidenceSourceSummary, ...] = ()
    confidence: float | None = None
    warnings: tuple[str, ...] = ()
    retrieved_at: str | None = None
    is_final_quote: bool = False


class BridgeError(Exception):
    """Safe local-demo bridge error."""


class ApiError(BridgeError):
    """Safe API error with bounded public message."""


class LLMExtractionError(BridgeError):
    """Safe LLM extraction error that is never shown to Telegram users."""


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = config_from_env(args)

    if config.dry_run and config.once and not config.telegram_bot_token:
        parsed = parse_customer_request(EXAMPLE_MESSAGE)
        if parsed is None:
            print("Dry run parser failed for the built-in example.")
            return 1
        payload = build_workflow_create_payload(
            parsed,
            customer_name="Telegram Customer",
            chat_id="dry-run-chat",
            message_id="dry-run-message",
        )
        print("Dry run: TELEGRAM_BOT_TOKEN is not set; no Telegram or backend calls.")
        print(json.dumps({"parsed": parsed.summary, "payload": payload}, indent=2))
        return 0

    if not config.telegram_bot_token:
        print(
            "TELEGRAM_BOT_TOKEN is required unless using --dry-run --once.",
            file=sys.stderr,
        )
        return 2

    print("Telegram inbound bridge started for local demo.")
    print(
        "Polling Telegram updates. Tokens, backend access tokens, and passwords "
        "will not be printed."
    )

    offset: int | None = None
    while True:
        try:
            updates = telegram_get_updates(config.telegram_bot_token, offset)
        except ApiError as error:
            print(f"Telegram polling failed: {error}", file=sys.stderr)
            if config.once:
                return 1
            time.sleep(config.poll_interval_seconds)
            continue

        for update in updates:
            update_id = update.get("update_id")
            if isinstance(update_id, int):
                offset = update_id + 1
            handle_update(config, update)

        if config.once:
            return 0
        time.sleep(config.poll_interval_seconds)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Poll Telegram locally and convert procurement messages into "
            "existing backend workflow API calls."
        )
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse only; do not call backend writes.")
    parser.add_argument("--once", action="store_true", help="Poll once and exit.")
    parser.add_argument(
        "--allowed-chat-id",
        help="Optional Telegram chat id allowlist for the local demo.",
    )
    parser.add_argument(
        "--auto-run",
        action="store_true",
        dest="auto_run",
        help="Run created workflows automatically (default).",
    )
    parser.add_argument(
        "--no-auto-run",
        action="store_false",
        dest="auto_run",
        help="Only create workflows; do not call /run.",
    )
    llm_group = parser.add_mutually_exclusive_group()
    llm_group.add_argument(
        "--llm-extraction",
        action="store_true",
        dest="llm_extraction",
        help="Enable optional LLM-backed RFQ extraction before deterministic fallback.",
    )
    llm_group.add_argument(
        "--no-llm-extraction",
        action="store_false",
        dest="llm_extraction",
        help="Disable optional LLM extraction and use deterministic parsing only.",
    )
    parser.set_defaults(llm_extraction=None)
    reply_group = parser.add_mutually_exclusive_group()
    reply_group.add_argument(
        "--sales-replies",
        action="store_true",
        dest="sales_replies",
        help="Use customer-friendly local-demo sales reply templates.",
    )
    reply_group.add_argument(
        "--technical-replies",
        action="store_false",
        dest="sales_replies",
        help="Use technical demo reply templates (default).",
    )
    parser.set_defaults(sales_replies=None)
    parser.set_defaults(auto_run=True)
    return parser.parse_args(argv)


def config_from_env(args: argparse.Namespace) -> BridgeConfig:
    return BridgeConfig(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
        backend_api_base_url=os.getenv(
            "BACKEND_API_BASE_URL", DEFAULT_BACKEND_API_BASE_URL
        ).rstrip("/"),
        frontend_base_url=os.getenv("FRONTEND_BASE_URL", DEFAULT_FRONTEND_BASE_URL).rstrip(
            "/"
        ),
        manager_email=os.getenv("DEMO_MANAGER_EMAIL", DEFAULT_MANAGER_EMAIL),
        manager_password=os.getenv("DEMO_MANAGER_PASSWORD", DEFAULT_MANAGER_PASSWORD),
        poll_interval_seconds=float(
            os.getenv(
                "TELEGRAM_POLL_INTERVAL_SECONDS",
                str(DEFAULT_POLL_INTERVAL_SECONDS),
            )
        ),
        allowed_chat_id=args.allowed_chat_id,
        dry_run=bool(args.dry_run),
        once=bool(args.once),
        auto_run=bool(args.auto_run),
        llm_extraction_enabled=resolve_bool_flag(
            args.llm_extraction,
            os.getenv("TELEGRAM_LLM_EXTRACTION_ENABLED", "false"),
        ),
        llm_provider=os.getenv(
            "TELEGRAM_LLM_PROVIDER",
            DEFAULT_TELEGRAM_LLM_PROVIDER,
        ).strip().lower(),
        llm_model=(
            os.getenv("TELEGRAM_LLM_MODEL")
            or os.getenv("OLLAMA_MODEL")
            or DEFAULT_TELEGRAM_LLM_MODEL
        ).strip(),
        llm_base_url=(
            os.getenv("TELEGRAM_LLM_BASE_URL")
            or os.getenv("OLLAMA_BASE_URL")
            or DEFAULT_TELEGRAM_LLM_BASE_URL
        ).strip().rstrip("/"),
        llm_timeout_seconds=int(
            os.getenv(
                "TELEGRAM_LLM_TIMEOUT_SECONDS",
                str(DEFAULT_TELEGRAM_LLM_TIMEOUT_SECONDS),
            )
        ),
        sales_replies_enabled=resolve_bool_flag(
            args.sales_replies,
            os.getenv("TELEGRAM_SALES_REPLY_ENABLED", "false"),
        ),
    )


def resolve_bool_flag(cli_value: bool | None, env_value: str) -> bool:
    if cli_value is not None:
        return cli_value
    return env_value.strip().lower() in {"1", "true", "yes", "on"}


def handle_update(config: BridgeConfig, update: dict[str, Any]) -> None:
    message = update.get("message")
    if not isinstance(message, dict):
        return

    chat = message.get("chat")
    if not isinstance(chat, dict):
        return
    chat_id = str(chat.get("id", ""))
    if config.allowed_chat_id and chat_id != config.allowed_chat_id:
        return

    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        send_or_log_reply(
            config,
            chat_id,
            follow_up_message(config, ""),
        )
        return

    text = text.strip()[:MAX_TEXT_LENGTH]
    if text.startswith("/"):
        handle_command(config, chat_id, text)
        return
    if is_greeting_message(text):
        send_or_log_reply(config, chat_id, greeting_message(config, text))
        return

    parsed = extract_customer_request(text, config)
    if isinstance(parsed, UnsupportedMixedRequest):
        send_or_log_reply(config, chat_id, unsupported_mixed_item_message(config, parsed))
        return
    if parsed is None:
        send_or_log_reply(config, chat_id, follow_up_message(config, text))
        return

    customer_name = sender_display_name(message)
    message_id = str(message.get("message_id", ""))
    payload = build_workflow_create_payload(
        parsed,
        customer_name=customer_name,
        chat_id=chat_id,
        message_id=message_id,
    )

    if config.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "chat_id": chat_id,
                    "summary": parsed.summary,
                    "payload": payload,
                },
                indent=2,
            )
        )
        return

    try:
        access_token = backend_login(config)
        workflow = create_workflow(config, access_token, payload)
    except ApiError as error:
        reply = f"Local demo bridge could not create the workflow: {error}"
    else:
        run_status = workflow.status
        if config.auto_run:
            try:
                run_status = run_workflow(config, access_token, workflow.workflow_id)
            except ApiError as error:
                reply = telegram_run_failed_reply(
                    config=config,
                    parsed=parsed,
                    workflow=workflow,
                    error=error,
                )
            else:
                reply = telegram_workflow_reply(
                    config=config,
                    parsed=parsed,
                    workflow_id=workflow.workflow_id,
                    status=run_status,
                    auto_run=config.auto_run,
                )
        else:
            reply = telegram_workflow_reply(
                config=config,
                parsed=parsed,
                workflow_id=workflow.workflow_id,
                status=run_status,
                auto_run=config.auto_run,
            )
    send_or_log_reply(config, chat_id, reply)


def handle_command(config: BridgeConfig, chat_id: str, text: str) -> None:
    command = text.split(maxsplit=1)[0].lower()
    if command in {"/start", "/help"}:
        send_or_log_reply(config, chat_id, help_command_message(config))
        return
    send_or_log_reply(
        config,
        chat_id,
        "Only /start and /help are supported.\n" + follow_up_message(config, text),
    )


def help_command_message(config: BridgeConfig | None = None) -> str:
    if config and config.sales_replies_enabled:
        return sales_greeting_message("xin chào")
    return (
        "Send a procurement request such as:\n"
        "English: quote for 50 standard business laptops\n"
        "Tiếng Việt: tôi muốn mua 50 máy tính xách tay có cài Office 365\n"
        "The local demo bridge creates a workflow, runs it to "
        "WAITING_APPROVAL, and requires Manager approval in the web UI."
    )


def is_greeting_message(text: str) -> bool:
    normalized = normalize_for_matching(text)
    return normalized in {"xin chao", "chao", "hello", "hi"}


def parse_customer_request(text: str) -> ParsedCustomerRequest | None:
    normalized = re.sub(r"\s+", " ", text.strip())[:MAX_TEXT_LENGTH]
    searchable = normalize_for_matching(normalized)
    matched = find_catalog_item_with_quantity(searchable)
    if matched is None:
        return None

    quantity, catalog_item = matched
    if quantity <= 0:
        return None
    requested_addons = detect_requested_addons(searchable)
    if not compatible_addons(catalog_item, requested_addons):
        return None

    return ParsedCustomerRequest(
        original_text=normalized,
        quantity=quantity,
        item_name=catalog_item.normalized_item_name,
        language=detect_language(normalized, searchable),
        requested_addons=requested_addons,
        catalog_item_id=catalog_item.item_id,
        item_family=catalog_item.item_family,
        catalog_version=CATALOG_VERSION,
    )


def find_catalog_item_with_quantity(searchable: str) -> tuple[int, CatalogItem] | None:
    for item in CATALOG_ITEMS:
        for alias in sorted(item.normalized_aliases, key=len, reverse=True):
            match = re.search(quantity_alias_regex(alias), searchable)
            if match:
                return int(match.group(1)), item
    return None


def quantity_alias_regex(alias: str) -> str:
    return (
        r"\b(\d{1,5})\s+"
        r"(?:cai|chiec|bo|cay|may|pcs?|units?)?\s*"
        + re.escape(alias)
        + r"(?![a-z0-9])"
    )


def extract_customer_request(
    text: str,
    config: BridgeConfig,
    *,
    llm_extractor: Any | None = None,
) -> ParsedCustomerRequest | UnsupportedMixedRequest | None:
    """Extract a customer RFQ with optional LLM parsing and deterministic fallback."""
    def apply_unsupported_item_guard(
        parsed: ParsedCustomerRequest | None,
        *,
        extraction_mode: str | None = None,
    ) -> ParsedCustomerRequest | UnsupportedMixedRequest | None:
        normalized = re.sub(r"\s+", " ", text.strip())[:MAX_TEXT_LENGTH]
        unsupported_items = merge_unsupported_mentions(
            detect_unsupported_item_mentions(text),
            detect_other_item_mentions(
                text,
                parsed.item_name if parsed is not None else None,
            ),
        )
        if unsupported_items and parsed is not None:
            guarded_parsed = (
                parsed_with_extraction_metadata(
                    parsed,
                    extraction_mode=extraction_mode,
                    llm_provider=config.llm_provider,
                    llm_model=config.llm_model,
                )
                if parsed is not None and extraction_mode is not None
                else parsed
            )
            return UnsupportedMixedRequest(
                original_text=normalized,
                language=(
                    guarded_parsed.language
                    if guarded_parsed is not None
                    else detect_language(normalized, normalize_for_matching(normalized))
                ),
                supported=guarded_parsed,
                unsupported_items=unsupported_items,
            )
        if parsed is None:
            return None
        if extraction_mode is None:
            return parsed
        return parsed_with_extraction_metadata(
            parsed,
            extraction_mode=extraction_mode,
            llm_provider=config.llm_provider,
            llm_model=config.llm_model,
        )

    if not config.llm_extraction_enabled:
        return apply_unsupported_item_guard(parse_customer_request(text))

    extractor = llm_extractor or llm_extract_customer_request
    try:
        llm_parsed = extractor(text, config)
    except LLMExtractionError:
        llm_parsed = None
    if llm_parsed is not None:
        return apply_unsupported_item_guard(llm_parsed)

    deterministic = parse_customer_request(text)
    return apply_unsupported_item_guard(deterministic, extraction_mode="fallback")


def llm_extract_customer_request(
    text: str,
    config: BridgeConfig,
) -> ParsedCustomerRequest | None:
    """Use a local provider call for extraction, then normalize deterministically."""
    if config.llm_provider != "ollama":
        raise LLMExtractionError("unsupported Telegram LLM provider")
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": llm_extraction_system_prompt()},
            {"role": "user", "content": text[:MAX_TEXT_LENGTH]},
        ],
        "stream": False,
        "think": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 500},
    }
    request = urllib.request.Request(
        f"{config.llm_base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=max(1, min(config.llm_timeout_seconds, 120)),
        ) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (
        TimeoutError,
        urllib.error.HTTPError,
        urllib.error.URLError,
        json.JSONDecodeError,
    ) as error:
        raise LLMExtractionError("Telegram LLM extraction failed") from error

    message = response_payload.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        thinking = message.get("thinking") if isinstance(message, dict) else None
        if isinstance(thinking, str) and thinking.strip():
            content = thinking
    if not isinstance(content, str) or not content.strip():
        raise LLMExtractionError("Telegram LLM extraction returned no content")
    return parse_llm_extraction_result(
        content,
        original_text=text,
        provider=config.llm_provider,
        model=config.llm_model,
    )


def llm_extraction_system_prompt() -> str:
    return (
        "Extract a procurement RFQ intent from one Telegram message. Return exactly "
        "one JSON object and no markdown. Shape: {\"language\":\"vi|en|unknown\","
        "\"intent\":\"procurement_rfq|greeting|unsupported|other\","
        "\"items\":[{\"name\":\"...\",\"quantity\":0}],\"requested_addons\":[],"
        "\"needs_follow_up\":true,\"follow_up_question\":\"...\"}. Rules: use "
        "canonical item names when possible. laptop, laptops, notebook, máy tính "
        "xách tay, laptop doanh nhân -> Standard business laptop. desktop pc, "
        "máy tính bàn -> Business desktop PC. monitor, màn hình -> Office monitor. "
        "printer, máy in -> Office printer. keyboard mouse combo, bộ bàn phím "
        "chuột -> Wireless keyboard and mouse combo. office 365, microsoft 365, "
        "cài sẵn office, có office -> requested_addons [\"office_365\"]. Do not "
        "include add-ons inside item name. If quantity is missing or item is "
        "unknown, needs_follow_up=true. Return JSON only."
    )


def parse_llm_extraction_result(
    value: str,
    *,
    original_text: str,
    provider: str,
    model: str,
) -> ParsedCustomerRequest | None:
    data = extract_json_object(value)
    if data is None:
        raise LLMExtractionError("invalid Telegram LLM JSON")
    return parsed_request_from_llm_data(
        data,
        original_text=original_text,
        provider=provider,
        model=model,
    )


def extract_json_object(value: str) -> dict[str, Any] | None:
    stripped = value.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.S)
    candidate = fenced.group(1) if fenced else stripped
    if not candidate.startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end <= start:
            return None
        candidate = candidate[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def parsed_request_from_llm_data(
    data: dict[str, Any],
    *,
    original_text: str,
    provider: str,
    model: str,
) -> ParsedCustomerRequest | None:
    intent = str(data.get("intent", "other")).strip().lower()
    if intent in {"greeting", "unsupported", "other"}:
        return None
    if intent != "procurement_rfq":
        return None

    items = data.get("items")
    if not isinstance(items, list) or not items:
        return None
    first_item = items[0]
    if not isinstance(first_item, dict):
        return None

    quantity = coerce_positive_quantity(first_item.get("quantity"))
    catalog_item = canonical_catalog_item(str(first_item.get("name", "")))
    if quantity is None or catalog_item is None:
        return None

    original_normalized = re.sub(r"\s+", " ", original_text.strip())[:MAX_TEXT_LENGTH]
    searchable = normalize_for_matching(
        f"{original_normalized} {first_item.get('name', '')}"
    )
    requested_addons = canonical_requested_addons(
        data.get("requested_addons"),
        searchable,
    )
    if not compatible_addons(catalog_item, requested_addons):
        return None
    raw_language = str(data.get("language", "unknown")).strip().lower()
    language = (
        raw_language
        if raw_language in {"vi", "en"}
        else detect_language(original_normalized, searchable)
    )
    return ParsedCustomerRequest(
        original_text=original_normalized,
        quantity=quantity,
        item_name=catalog_item.normalized_item_name,
        language=language,
        requested_addons=requested_addons,
        extraction_mode="llm",
        llm_provider=provider,
        llm_model=model[:200],
        catalog_item_id=catalog_item.item_id,
        item_family=catalog_item.item_family,
        catalog_version=CATALOG_VERSION,
    )


def coerce_positive_quantity(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and re.fullmatch(r"\d{1,5}", value.strip()):
        quantity = int(value.strip())
        return quantity if quantity > 0 else None
    return None


def canonical_catalog_item(value: str) -> CatalogItem | None:
    return get_catalog_item_by_name(value) or find_catalog_item(value)


def canonical_requested_addons(
    llm_addons: Any,
    searchable_text: str,
) -> tuple[str, ...]:
    addons: list[str] = []
    if isinstance(llm_addons, list):
        for addon in llm_addons:
            normalized = normalize_for_matching(str(addon))
            if normalized in {"office 365", "office_365", "microsoft 365", "m365"}:
                addons.append("office_365")
    addons.extend(detect_requested_addons(searchable_text))
    return tuple(dict.fromkeys(addons))


def parsed_with_extraction_metadata(
    parsed: ParsedCustomerRequest,
    *,
    extraction_mode: str,
    llm_provider: str | None,
    llm_model: str | None,
) -> ParsedCustomerRequest:
    return ParsedCustomerRequest(
        original_text=parsed.original_text,
        quantity=parsed.quantity,
        item_name=parsed.item_name,
        language=parsed.language,
        requested_addons=parsed.requested_addons,
        extraction_mode=extraction_mode,
        llm_provider=llm_provider,
        llm_model=llm_model[:200] if llm_model else None,
        catalog_item_id=parsed.catalog_item_id,
        item_family=parsed.item_family,
        catalog_version=parsed.catalog_version,
    )


def normalize_for_matching(value: str) -> str:
    return normalize_for_catalog_match(value)


def detect_language(original_text: str, searchable_text: str) -> str:
    has_vietnamese_marks = normalize_for_matching(original_text) != original_text.lower()
    vietnamese_markers = (
        "toi ",
        "muon ",
        "mua ",
        "can ",
        "bao gia",
        "may tinh xach tay",
        "doanh nhan",
        "tieu chuan",
        "phong kinh doanh",
        "van phong",
        "may tinh ban",
        "may tinh de ban",
        "may bo",
        "man hinh",
        "may in",
        "ban phim",
        "chuot",
        "cai ",
        "co cai",
        "cai san",
        "kem ",
        "bo ",
    )
    if has_vietnamese_marks or any(marker in searchable_text for marker in vietnamese_markers):
        return "vi"
    return "en"


def detect_requested_addons(searchable_text: str) -> tuple[str, ...]:
    return detect_catalog_requested_addons(searchable_text)


def detect_unsupported_item_mentions(text: str) -> tuple[UnsupportedItemMention, ...]:
    searchable = normalize_for_matching(text)
    unsupported: list[UnsupportedItemMention] = []
    unsupported_patterns = (
        ("projector", "projector", ("projector", "projectors", "may chieu")),
        ("server", "server", ("server", "servers", "may chu")),
        ("phone", "phone", ("phone", "phones", "dien thoai")),
        ("camera", "camera giám sát", ("camera", "camera giam sat")),
        ("router", "bộ định tuyến", ("router", "routers", "bo dinh tuyen")),
    )
    for item_label, display_label, aliases in unsupported_patterns:
        for alias in aliases:
            match = re.search(
                r"(?:\b(\d{1,5})\s+"
                r"(?:cai|chiec|bo|cay|may|pcs?|units?)?\s*)?"
                + re.escape(alias)
                + r"(?![a-z0-9])",
                searchable,
            )
            if match:
                quantity = int(match.group(1)) if match.group(1) else None
                unsupported.append(
                    UnsupportedItemMention(
                        quantity=quantity,
                        item_label=item_label,
                        display_label=display_label,
                    )
                )
                break
    return tuple(unsupported)


_GENERIC_ITEM_REGEX = re.compile(
    r"\b(\d{1,5})\s+"
    r"(?:cai|chiec|bo|cay|pcs?|units?|cái|chiếc|bộ|cây)?\s*"
    r"([^\W\d_][^\W\d_ ]*(?:[-\s][^\W\d_][^\W\d_ ]*){0,8})",
    re.IGNORECASE,
)

_TRAILING_ITEM_CONNECTORS = frozenset(
    {"va", "and", "with", "for", "co", "kem", "cung", "them"}
)

_UNSUPPORTED_ITEM_ALIASES = frozenset(
    {
        "projector",
        "projectors",
        "may chieu",
        "server",
        "servers",
        "may chu",
        "phone",
        "phones",
        "dien thoai",
        "camera",
        "camera giam sat",
        "router",
        "routers",
        "bo dinh tuyen",
    }
)


def strip_trailing_connectors(value: str) -> str:
    words = value.split()
    normalized_words = normalize_for_matching(value).split()
    if len(words) != len(normalized_words):
        return value.strip()
    while (
        normalized_words
        and normalized_words[-1].strip(".,;") in _TRAILING_ITEM_CONNECTORS
    ):
        normalized_words.pop()
        words.pop()
    return " ".join(words).strip()


def merge_unsupported_mentions(
    *groups: tuple[UnsupportedItemMention, ...],
) -> tuple[UnsupportedItemMention, ...]:
    return tuple(dict.fromkeys(item for group in groups for item in group))


def detect_other_item_mentions(
    text: str,
    extracted_item_name: str | None,
) -> tuple[UnsupportedItemMention, ...]:
    """Find catalog or generic item mentions beyond the extracted single item.

    The bridge creates one item per quotation request. Mentioning a second
    catalog item or an unknown quantity-word item means the message mixes
    products, so the bridge refuses to create a partial workflow instead of
    silently dropping the other item.
    """
    searchable = normalize_for_matching(text)
    mentions: list[UnsupportedItemMention] = []

    for item in CATALOG_ITEMS:
        if item.normalized_item_name == extracted_item_name:
            continue
        for alias in sorted(item.normalized_aliases, key=len, reverse=True):
            match = re.search(quantity_alias_regex(alias), searchable)
            if match:
                mentions.append(
                    UnsupportedItemMention(
                        quantity=int(match.group(1)),
                        item_label=item.normalized_item_name,
                        display_label=item.display_name,
                    )
                )
                break

    for match in _GENERIC_ITEM_REGEX.finditer(text):
        raw_value = match.group(2)
        normalized_value = normalize_for_matching(raw_value)
        if find_catalog_item(normalized_value) is not None:
            continue
        if any(alias in normalized_value for alias in _UNSUPPORTED_ITEM_ALIASES):
            continue
        label = strip_trailing_connectors(raw_value)
        if not label:
            continue
        quantity = int(match.group(1)) if match.group(1) else None
        mentions.append(
            UnsupportedItemMention(
                quantity=quantity,
                item_label="unsupported_item",
                display_label=label,
            )
        )

    return tuple(mentions)


def build_workflow_create_payload(
    parsed: ParsedCustomerRequest,
    *,
    customer_name: str,
    chat_id: str,
    message_id: str,
) -> dict[str, Any]:
    attributes: dict[str, Any] = {
        "source": "telegram",
        "telegram_chat_id": str(chat_id),
        "telegram_message_id": str(message_id),
        "demo": True,
        "language": parsed.language,
        "requested_addons": list(parsed.requested_addons),
        "parser_version": PARSER_VERSION,
        "extraction_mode": parsed.extraction_mode,
    }
    if parsed.llm_provider:
        attributes["llm_provider"] = parsed.llm_provider[:80]
    if parsed.llm_model:
        attributes["llm_model"] = parsed.llm_model[:200]
    if parsed.catalog_item_id:
        attributes["catalog"] = {
            "catalog_version": parsed.catalog_version,
            "item_id": parsed.catalog_item_id,
            "normalized_item_name": parsed.item_name,
            "item_family": parsed.item_family,
            "requested_addons": list(parsed.requested_addons),
        }

    return {
        "workflow_type": "procurement_quotation",
        "domain": "it_equipment",
        "request": {
            "raw_text": parsed.original_text,
            "request_text": parsed.original_text,
            "source": "telegram",
            "customer": {"name": customer_name or "Telegram Customer"},
            "items": [{"name": parsed.item_name, "quantity": parsed.quantity}],
            "requested_addons": list(parsed.requested_addons),
        },
        "metadata": {
            "state_version": 1,
            "tags": {"source": "telegram", "demo": "true"},
            "attributes": attributes,
        },
    }


def sender_display_name(message: dict[str, Any]) -> str:
    sender = message.get("from")
    if not isinstance(sender, dict):
        return "Telegram Customer"
    first_name = sender.get("first_name")
    last_name = sender.get("last_name")
    username = sender.get("username")
    parts = [part for part in (first_name, last_name) if isinstance(part, str)]
    if parts:
        return " ".join(parts)[:120]
    if isinstance(username, str) and username:
        return f"@{username}"[:120]
    return "Telegram Customer"


def backend_login(config: BridgeConfig) -> str:
    response = json_api_request(
        "POST",
        f"{config.backend_api_base_url}/auth/login",
        {"email": config.manager_email, "password": config.manager_password},
    )
    token = response.get("access_token")
    if not isinstance(token, str) or not token:
        raise ApiError("backend login response did not include an access token")
    return token


def create_workflow(
    config: BridgeConfig,
    access_token: str,
    payload: dict[str, Any],
) -> WorkflowCreationResult:
    response = json_api_request(
        "POST",
        f"{config.backend_api_base_url}/workflows",
        payload,
        access_token=access_token,
    )
    workflow = response.get("workflow")
    if not isinstance(workflow, dict):
        raise ApiError("workflow create response was missing workflow")
    workflow_id = workflow.get("workflow_id")
    status = workflow.get("status")
    if not isinstance(workflow_id, str) or not isinstance(status, str):
        raise ApiError("workflow create response was missing id/status")
    print(f"Created workflow {workflow_id} with status {status}.")
    return WorkflowCreationResult(workflow_id=workflow_id, status=status)


def run_workflow(config: BridgeConfig, access_token: str, workflow_id: str) -> str:
    try:
        response = json_api_request(
            "POST",
            f"{config.backend_api_base_url}/workflows/{urllib.parse.quote(workflow_id)}/run",
            {},
            access_token=access_token,
        )
    except ApiError as error:
        raise ApiError(f"workflow was created but /run failed: {error}") from error
    status = response.get("status")
    if not isinstance(status, str):
        raise ApiError("workflow run response was missing status")
    print(f"Ran workflow {workflow_id}; status is {status}.")
    return status


def json_api_request(
    method: str,
    url: str,
    payload: dict[str, Any],
    *,
    access_token: str | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise ApiError(safe_http_error(error)) from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ApiError(bound_text(str(error))) from error


def telegram_get_updates(token: str, offset: int | None) -> list[dict[str, Any]]:
    params: dict[str, str] = {"timeout": "20", "allowed_updates": json.dumps(["message"])}
    if offset is not None:
        params["offset"] = str(offset)
    url = telegram_url(token, "getUpdates", params)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise ApiError(safe_http_error(error)) from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ApiError(bound_text(str(error))) from error
    if payload.get("ok") is not True:
        raise ApiError("Telegram getUpdates returned ok=false")
    result = payload.get("result")
    return result if isinstance(result, list) else []


def telegram_send_message(token: str, chat_id: str, text: str) -> None:
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text[:3900]}).encode(
        "utf-8"
    )
    request = urllib.request.Request(
        telegram_url(token, "sendMessage"),
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            json.loads(response.read().decode("utf-8"))
    except Exception as error:  # noqa: BLE001 - safe local console fallback
        print(f"Telegram sendMessage failed: {bound_text(str(error))}", file=sys.stderr)


def telegram_url(
    token: str,
    method: str,
    params: dict[str, str] | None = None,
) -> str:
    base = f"https://api.telegram.org/bot{urllib.parse.quote(token)}/{method}"
    if params:
        return f"{base}?{urllib.parse.urlencode(params)}"
    return base


def send_or_log_reply(config: BridgeConfig, chat_id: str, text: str) -> None:
    if config.dry_run:
        print(json.dumps({"dry_run_reply": text[:1000]}, indent=2))
        return
    if not config.telegram_bot_token:
        print("Telegram reply skipped: TELEGRAM_BOT_TOKEN is not configured.")
        return
    telegram_send_message(config.telegram_bot_token, chat_id, text)


def telegram_workflow_reply(
    *,
    config: BridgeConfig,
    parsed: ParsedCustomerRequest,
    workflow_id: str,
    status: str,
    auto_run: bool,
    evidence: ReferenceEvidenceSummary | None = None,
) -> str:
    if config.sales_replies_enabled:
        return telegram_sales_workflow_reply(
            config=config,
            parsed=parsed,
            workflow_id=workflow_id,
            status=status,
            auto_run=auto_run,
            evidence=evidence,
        )
    workflow_url = f"{config.frontend_base_url}/workflows/{workflow_id}"
    monitor_url = f"{config.frontend_base_url}/agent-monitor?workflowId={workflow_id}"
    action = (
        "The workflow was created and run to the approval boundary."
        if auto_run
        else "The workflow was created. Click Run workflow in the UI to start it."
    )
    options_line = (
        f"Options: {parsed.options_summary}\n" if parsed.options_summary else ""
    )
    return (
        f"Parsed: {parsed.summary}\n"
        f"{options_line}"
        f"Workflow id: {workflow_id}\n"
        f"Status: {status}\n"
        f"{action}\n"
        f"Workflow: {workflow_url}\n"
        f"Agent monitor: {monitor_url}\n"
        "Human approval is required before resume. No auto-approval or auto-resume is performed."
    )


def telegram_run_failed_reply(
    *,
    config: BridgeConfig,
    parsed: ParsedCustomerRequest,
    workflow: WorkflowCreationResult,
    error: ApiError,
) -> str:
    if config.sales_replies_enabled:
        return telegram_sales_run_failed_reply(
            config=config,
            parsed=parsed,
            workflow=workflow,
        )
    workflow_url = f"{config.frontend_base_url}/workflows/{workflow.workflow_id}"
    monitor_url = f"{config.frontend_base_url}/agent-monitor?workflowId={workflow.workflow_id}"
    options_line = (
        f"Options: {parsed.options_summary}\n" if parsed.options_summary else ""
    )
    return (
        "Received request and created the workflow, but auto-run did not complete.\n"
        f"Parsed: {parsed.summary}\n"
        f"{options_line}"
        f"Workflow id: {workflow.workflow_id}\n"
        f"Status: {workflow.status}\n"
        f"Workflow: {workflow_url}\n"
        f"Agent monitor: {monitor_url}\n"
        f"Run error: {bound_text(str(error))}\n"
        "Open the workflow in the UI and click Run workflow after the backend is ready."
    )


def telegram_sales_workflow_reply(
    *,
    config: BridgeConfig,
    parsed: ParsedCustomerRequest,
    workflow_id: str,
    status: str,
    auto_run: bool,
    evidence: ReferenceEvidenceSummary | None = None,
) -> str:
    workflow_url = f"{config.frontend_base_url}/workflows/{workflow_id}"
    monitor_url = f"{config.frontend_base_url}/agent-monitor?workflowId={workflow_id}"
    options = (
        f" kèm {parsed.options_summary}" if parsed.options_summary else ""
    )
    evidence_text = format_sales_reference_evidence(evidence, parsed.language)
    if parsed.language == "vi":
        processing = (
            "Yêu cầu đã được chuyển vào hệ thống xử lý báo giá nội bộ để kiểm tra "
            "chính sách giá, hợp đồng/chiết khấu áp dụng, tuân thủ và điều kiện "
            "phê duyệt."
            if auto_run
            else "Yêu cầu đã được ghi nhận trong hệ thống nội bộ. Nhân sự vận hành "
            "sẽ bấm Run workflow để bắt đầu kiểm tra."
        )
        return (
            f"Cảm ơn anh/chị. Em đã ghi nhận nhu cầu {parsed.summary}{options}.\n\n"
            f"{processing}\n\n"
            f"{evidence_text}"
            f"Mã yêu cầu: {workflow_id}\n"
            f"Trạng thái: {status} — đang chờ quản lý phê duyệt nếu đã chạy tới "
            "ranh giới phê duyệt.\n"
            f"Link theo dõi nội bộ: {workflow_url}\n"
            f"Agent Monitor: {monitor_url}\n\n"
            "Lưu ý: Đây chưa phải báo giá cuối cùng. Báo giá chỉ được hoàn tất "
            "sau khi quản lý phê duyệt. Hệ thống không tự phê duyệt, không tự "
            "resume và không gửi email thật."
        )
    return (
        f"Thank you. I recorded the request for {parsed.summary}{options}.\n\n"
        "The request has been transferred into the internal quotation workflow "
        "to check pricing policy, contract/discount rules, compliance, and "
        "approval requirements.\n\n"
        f"{evidence_text}"
        f"Request id: {workflow_id}\n"
        f"Status: {status}\n"
        f"Internal workflow: {workflow_url}\n"
        f"Agent Monitor: {monitor_url}\n\n"
        "Note: this is not a customer-ready quotation. The quotation is completed "
        "only after manager approval. The system does not auto-approve, "
        "auto-resume, or send real email."
    )


def format_sales_reference_evidence(
    evidence: ReferenceEvidenceSummary | None,
    language: str,
) -> str:
    """Render bounded reference evidence for sales replies without fetching it."""
    if evidence is None:
        return ""
    provider = safe_evidence_text(evidence.provider, limit=80) or "unknown"
    if evidence.is_final_quote:
        return (
            "Tham khảo giá: bằng chứng cần được rà soát nội bộ trước khi phản hồi "
            "khách hàng. Chưa phát hành báo giá.\n\n"
            if language == "vi"
            else (
                "Reference evidence requires internal review before customer "
                "response. No customer-ready quotation has been issued.\n\n"
            )
        )

    prices = safe_reference_prices(evidence.reference_prices)
    sources = safe_reference_sources(evidence.sources)
    warnings = safe_evidence_warnings(evidence.warnings)
    confidence = normalized_confidence(evidence.confidence)
    has_usable_evidence = bool(prices or sources) and (
        confidence is None or confidence >= 0.5
    )

    if not has_usable_evidence:
        caution = low_confidence_text(confidence, language)
        warning_text = f" {warnings[0]}" if warnings else ""
        if language == "vi":
            return (
                "Tham khảo giá: đang chờ rà soát thủ công; chưa có bằng chứng "
                f"đủ tin cậy để hiển thị cho báo giá.{caution}{warning_text}\n\n"
            )
        return (
            "Reference evidence: pending manual pricing review; no reliable "
            f"customer-ready pricing evidence is available.{caution}{warning_text}\n\n"
        )

    source_count = len(evidence.sources)
    confidence_text = (
        f", confidence {confidence:.2f}" if confidence is not None else ""
    )
    if language == "vi":
        lines = [
            "Tham khảo giá nội bộ: đã có bằng chứng tham khảo để quản lý rà soát "
            f"(provider: {provider}, sources: {source_count}{confidence_text})."
        ]
        lines.extend(f"- Giá tham khảo: {price}" for price in prices)
        lines.extend(f"- Nguồn: {source}" for source in sources)
        lines.append("Tất cả số tiền chỉ là tham khảo, không phải báo giá cuối cùng.")
    else:
        lines = [
            "Reference evidence is available for internal review "
            f"(provider: {provider}, sources: {source_count}{confidence_text})."
        ]
        lines.extend(f"- Reference only: {price}" for price in prices)
        lines.extend(f"- Source: {source}" for source in sources)
        lines.append("All amounts are reference only, not final quotation.")
    if warnings:
        lines.append(f"Warning: {warnings[0]}")
    return "\n".join(lines) + "\n\n"


def safe_reference_prices(
    prices: tuple[ReferenceEvidencePriceSummary, ...],
) -> list[str]:
    safe_prices: list[str] = []
    for price in prices[:MAX_EVIDENCE_ITEMS]:
        label = safe_evidence_text(price.label, limit=80) or "reference price"
        amount = safe_evidence_text(price.amount or "", limit=80)
        currency = safe_evidence_text(price.currency or "", limit=12)
        unit = safe_evidence_text(price.unit or "", limit=40)
        amount_parts = [part for part in (amount, currency) if part]
        amount_text = " ".join(amount_parts)
        suffix = f" / {unit}" if unit else ""
        if amount_text:
            safe_prices.append(f"{label}: {amount_text}{suffix}")
        else:
            safe_prices.append(label)
    return safe_prices


def safe_reference_sources(
    sources: tuple[ReferenceEvidenceSourceSummary, ...],
) -> list[str]:
    safe_sources: list[str] = []
    for source in sources[:MAX_EVIDENCE_ITEMS]:
        title = safe_evidence_text(source.title) or "reference source"
        url = safe_evidence_url(source.url)
        safe_sources.append(f"{title} ({url})" if url else title)
    return safe_sources


def safe_evidence_warnings(warnings: tuple[str, ...]) -> list[str]:
    return [
        warning
        for warning in (
            safe_evidence_text(value, limit=180)
            for value in warnings[:MAX_EVIDENCE_ITEMS]
        )
        if warning
    ]


def normalized_confidence(value: float | None) -> float | None:
    if value is None:
        return None
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value


def low_confidence_text(confidence: float | None, language: str) -> str:
    if confidence is None or confidence >= 0.5:
        return ""
    if language == "vi":
        return f" Độ tin cậy thấp ({confidence:.2f})."
    return f" Low confidence ({confidence:.2f})."


def safe_evidence_url(value: str | None) -> str | None:
    safe = safe_evidence_text(value or "", limit=MAX_EVIDENCE_URL_LENGTH)
    if not safe:
        return None
    if contains_sensitive_marker(safe):
        return None
    return safe


def safe_evidence_text(
    value: str | None,
    *,
    limit: int = MAX_EVIDENCE_TEXT_LENGTH,
) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"<[^>]*>", " ", value)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return None
    if contains_sensitive_marker(normalized):
        return "[redacted]"
    return normalized[:limit].strip()


def contains_sensitive_marker(value: str) -> bool:
    return bool(
        re.search(
            r"(?i)(api[_-]?key|authorization|bearer|cookie|jwt|password|"
            r"provider_payload|raw_prompt|raw_provider|secret|token|"
            r"chain[-_ ]?of[-_ ]?thought)",
            value,
        )
    )


def telegram_sales_run_failed_reply(
    *,
    config: BridgeConfig,
    parsed: ParsedCustomerRequest,
    workflow: WorkflowCreationResult,
) -> str:
    workflow_url = f"{config.frontend_base_url}/workflows/{workflow.workflow_id}"
    monitor_url = f"{config.frontend_base_url}/agent-monitor?workflowId={workflow.workflow_id}"
    options = (
        f" kèm {parsed.options_summary}" if parsed.options_summary else ""
    )
    if parsed.language == "vi":
        return (
            f"Cảm ơn anh/chị. Em đã ghi nhận nhu cầu {parsed.summary}{options}.\n\n"
            "Yêu cầu đã được tạo trong hệ thống nội bộ nhưng bước xử lý tự động "
            "chưa hoàn tất. Nhân sự vận hành sẽ mở workflow và bấm Run workflow "
            "sau khi backend sẵn sàng.\n\n"
            f"Mã yêu cầu: {workflow.workflow_id}\n"
            f"Trạng thái hiện tại: {workflow.status}\n"
            f"Link theo dõi nội bộ: {workflow_url}\n"
            f"Agent Monitor: {monitor_url}\n\n"
            "Lưu ý: Đây chưa phải báo giá cuối cùng và chưa có phê duyệt quản lý."
        )
    return (
        f"Thank you. I recorded the request for {parsed.summary}{options}.\n\n"
        "The request was created in the internal workflow system, but automated "
        "processing has not completed. The operator should open the workflow and "
        "click Run workflow after the backend is ready.\n\n"
        f"Request id: {workflow.workflow_id}\n"
        f"Current status: {workflow.status}\n"
        f"Internal workflow: {workflow_url}\n"
        f"Agent Monitor: {monitor_url}\n\n"
        "Note: this is not a customer-ready quotation and no manager approval has "
        "been issued."
    )


def greeting_message(config: BridgeConfig, text: str) -> str:
    if config.sales_replies_enabled:
        return sales_greeting_message(text)
    return HELPFUL_REQUEST_PROMPT


def follow_up_message(config: BridgeConfig, text: str) -> str:
    if config.sales_replies_enabled:
        return sales_follow_up_message(text)
    return HELPFUL_REQUEST_PROMPT


def unsupported_mixed_item_message(
    config: BridgeConfig,
    request: UnsupportedMixedRequest,
) -> str:
    if config.sales_replies_enabled:
        return sales_unsupported_mixed_item_message(request)
    return technical_unsupported_mixed_item_message(request)


def technical_unsupported_mixed_item_message(request: UnsupportedMixedRequest) -> str:
    return (
        "I found a supported item and an unsupported item. "
        f"Supported: {request.supported_summary}. "
        f"Unsupported: {request.unsupported_summary}. "
        "Please send a request with supported items only from the demo catalog. "
        "The current demo catalog supports laptops, desktop PCs, office "
        "monitors, office printers, and wireless keyboard/mouse combos."
    )


def sales_unsupported_mixed_item_message(request: UnsupportedMixedRequest) -> str:
    if request.language == "vi":
        supported = request.supported_summary.replace(
            "Standard business laptop",
            "laptop",
        ).replace(
            "Business desktop PC",
            "máy tính bàn",
        ).replace(
            "Office monitor",
            "màn hình văn phòng",
        ).replace(
            "Office printer",
            "máy in văn phòng",
        ).replace(
            "Wireless keyboard and mouse combo",
            "bộ bàn phím chuột không dây",
        )
        return (
            f"Em đã nhận được yêu cầu gồm {supported} và "
            f"{request.unsupported_summary}. Hiện catalog demo chỉ hỗ trợ laptop, "
            "máy tính bàn, màn hình văn phòng, máy in văn phòng và bộ bàn phím "
            "chuột. Mặt hàng chưa hỗ trợ chưa có trong catalog demo, nên em "
            "chưa tạo báo giá để tránh thiếu thông tin. Anh/chị có thể gửi riêng "
            "yêu cầu với mặt hàng được hỗ trợ, ví dụ: báo giá 20 laptop văn phòng "
            "tiêu chuẩn."
        )
    return (
        f"I found a supported catalog request ({request.supported_summary}) and "
        f"an unsupported item ({request.unsupported_summary}). The current demo "
        "catalog supports laptops, desktop PCs, office monitors, office printers, "
        "and wireless keyboard/mouse combos, so I have not created a partial "
        "workflow. Please send an RFQ with supported items only or add product "
        "catalog/pricing first."
    )


def sales_greeting_message(text: str) -> str:
    if preferred_reply_language(text) == "vi":
        return (
            "Em chào anh/chị. Anh/chị có thể gửi nhu cầu mua sắm theo mẫu: "
            "báo giá 50 laptop văn phòng tiêu chuẩn có Office 365.\n"
            "English example: quote for 50 standard business laptops with Office 365."
        )
    return (
        "Hello. Please send a procurement request such as: quote for 50 standard "
        "business laptops with Office 365.\n"
        "Ví dụ tiếng Việt: báo giá 50 laptop văn phòng tiêu chuẩn có Office 365."
    )


def sales_follow_up_message(text: str) -> str:
    if preferred_reply_language(text) == "vi":
        return (
            "Em cần thêm số lượng và mặt hàng để lập yêu cầu báo giá. "
            "Ví dụ: báo giá 50 laptop văn phòng tiêu chuẩn có Office 365.\n"
            "English example: quote for 50 standard business laptops."
        )
    return (
        "Please include quantity and item, for example: quote for 50 standard "
        "business laptops.\n"
        "Ví dụ tiếng Việt: báo giá 50 laptop văn phòng tiêu chuẩn có Office 365."
    )


def preferred_reply_language(text: str) -> str:
    searchable = normalize_for_matching(text)
    return detect_language(text, searchable)


def safe_http_error(error: urllib.error.HTTPError) -> str:
    try:
        body = error.read().decode("utf-8")
    except Exception:  # noqa: BLE001 - safe fallback
        body = ""
    message = f"HTTP {error.code}"
    if body:
        message = f"{message}: {body}"
    return bound_text(message)


def bound_text(value: str, limit: int = 500) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized if len(normalized) <= limit else f"{normalized[:limit]}..."


if __name__ == "__main__":
    raise SystemExit(main())
