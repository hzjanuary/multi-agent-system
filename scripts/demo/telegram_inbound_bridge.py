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
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_BACKEND_API_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_FRONTEND_BASE_URL = "http://localhost:3000"
DEFAULT_MANAGER_EMAIL = "manager@example.test"
DEFAULT_MANAGER_PASSWORD = "DemoPassword123!"
DEFAULT_POLL_INTERVAL_SECONDS = 2.0
EXAMPLE_MESSAGE = (
    "We would like to purchase 50 standard business laptops for a new "
    "operations team. We signed a master agreement in May 2026. Please provide "
    "your best quotation with the applicable discount."
)
MAX_TEXT_LENGTH = 2000
HTTP_TIMEOUT_SECONDS = 15
PARSER_VERSION = "telegram-demo-parser-v2"
SUPPORTED_ITEM_NAME = "Standard business laptop"
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


@dataclass(frozen=True)
class ParsedCustomerRequest:
    original_text: str
    quantity: int
    item_name: str
    language: str
    requested_addons: tuple[str, ...] = ()

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
class WorkflowCreationResult:
    workflow_id: str
    status: str


class BridgeError(Exception):
    """Safe local-demo bridge error."""


class ApiError(BridgeError):
    """Safe API error with bounded public message."""


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
    )


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
            HELPFUL_REQUEST_PROMPT,
        )
        return

    text = text.strip()[:MAX_TEXT_LENGTH]
    if text.startswith("/"):
        handle_command(config, chat_id, text)
        return
    if is_greeting_message(text):
        send_or_log_reply(config, chat_id, HELPFUL_REQUEST_PROMPT)
        return

    parsed = parse_customer_request(text)
    if parsed is None:
        send_or_log_reply(config, chat_id, HELPFUL_REQUEST_PROMPT)
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
        send_or_log_reply(config, chat_id, help_command_message())
        return
    send_or_log_reply(
        config,
        chat_id,
        "Only /start and /help are supported.\n" + HELPFUL_REQUEST_PROMPT,
    )


def help_command_message() -> str:
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
    match = re.search(
        r"\b(\d{1,5})\s+"
        r"(?:cai|chiec|bo|cay|may|pcs?|units?)?\s*"
        r"("
        r"(?:standard\s+)?(?:business\s+)?(?:laptops?|notebooks?)"
        r"|laptop(?:\s+doanh\s+nhan)?"
        r"|may\s+tinh\s+xach\s+tay(?:\s+doanh\s+nhan)?(?:\s+tieu\s+chuan)?"
        r")\b",
        searchable,
    )
    if not match:
        return None

    quantity = int(match.group(1))
    if quantity <= 0:
        return None

    return ParsedCustomerRequest(
        original_text=normalized,
        quantity=quantity,
        item_name=SUPPORTED_ITEM_NAME,
        language=detect_language(normalized, searchable),
        requested_addons=detect_requested_addons(searchable),
    )


def normalize_for_matching(value: str) -> str:
    ascii_text = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


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
        "cai ",
        "co cai",
        "cai san",
    )
    if has_vietnamese_marks or any(marker in searchable_text for marker in vietnamese_markers):
        return "vi"
    return "en"


def detect_requested_addons(searchable_text: str) -> tuple[str, ...]:
    addon_patterns = (
        r"\boffice\s*365\b",
        r"\bmicrosoft\s*365\b",
        r"\bcai\s+san\s+office\b",
        r"\bco\s+office\b",
        r"\bco\s+cai\s+office\b",
    )
    if any(re.search(pattern, searchable_text) for pattern in addon_patterns):
        return ("office_365",)
    return ()


def addon_display_label(addon: str) -> str:
    if addon == "office_365":
        return "Office 365"
    return addon.replace("_", " ").title()


def build_workflow_create_payload(
    parsed: ParsedCustomerRequest,
    *,
    customer_name: str,
    chat_id: str,
    message_id: str,
) -> dict[str, Any]:
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
            "attributes": {
                "source": "telegram",
                "telegram_chat_id": str(chat_id),
                "telegram_message_id": str(message_id),
                "demo": True,
                "language": parsed.language,
                "requested_addons": list(parsed.requested_addons),
                "parser_version": PARSER_VERSION,
            },
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
) -> str:
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
