#!/usr/bin/env python3
"""Deterministic Telegram parser benchmark runner for SPEC-022.

The runner uses the existing local Telegram parser path only. It does not call
Telegram, backend APIs, LLM providers, Tavily, web search, or email providers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.demo.catalog import find_catalog_item  # noqa: E402
from scripts.demo.telegram_inbound_bridge import (  # noqa: E402
    BridgeConfig,
    ParsedCustomerRequest,
    UnsupportedMixedRequest,
    detect_unsupported_item_mentions,
    extract_customer_request,
    is_greeting_message,
)

DEFAULT_CASES_PATH = Path(__file__).with_name("telegram_parser_cases.json")
BENCHMARK_GENERATED_AT = "1970-01-01T00:00:00Z"
REQUIRED_CASE_FIELDS = {
    "id",
    "language",
    "category",
    "input_message",
    "expected_should_create_workflow",
    "expected_normalized_item_name",
    "expected_quantity",
    "expected_requested_addons",
    "expected_safety_outcome",
}
FORBIDDEN_OUTPUT_CLAIMS = (
    "final quote",
    "approved quote",
    "approved quotation",
    "in stock",
    "stock available",
    "delivery date",
    "will deliver",
    "discount approved",
    "email sent",
    "sent to customer",
)


@dataclass(frozen=True)
class ActualOutcome:
    should_create_workflow: bool
    safety_outcome: str
    normalized_item_name: str | None = None
    quantity: int | None = None
    requested_addons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    language: str
    category: str
    passed: bool
    expected_safety_outcome: str
    actual_safety_outcome: str
    errors: tuple[str, ...]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        dataset = load_dataset(args.cases)
        results = evaluate_dataset(dataset)
    except ValueError as error:
        print(f"Benchmark setup failed: {error}", file=sys.stderr)
        return 2

    metrics = build_metrics(dataset, results)
    human_summary = format_human_summary(metrics)
    if contains_forbidden_claim(human_summary):
        print("Benchmark output blocked by forbidden-claim safety check.", file=sys.stderr)
        return 2
    print(human_summary)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.write_text(
            json.dumps(metrics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 0 if metrics["failed_cases"] == 0 else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate deterministic Telegram RFQ parser behavior against the "
            "SPEC-022 benchmark dataset."
        )
    )
    parser.add_argument(
        "--cases",
        default=str(DEFAULT_CASES_PATH),
        help="Path to the Telegram parser benchmark JSON dataset.",
    )
    parser.add_argument(
        "--output-json",
        help="Optional path for machine-readable benchmark metrics JSON.",
    )
    return parser.parse_args(argv)


def load_dataset(path: str | Path) -> dict[str, Any]:
    dataset_path = Path(path)
    try:
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load dataset {dataset_path}") from error
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset: dict[str, Any]) -> None:
    if not isinstance(dataset.get("benchmark_name"), str):
        raise ValueError("dataset benchmark_name must be a string")
    if not isinstance(dataset.get("version"), str):
        raise ValueError("dataset version must be a string")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("dataset cases must be a non-empty list")

    seen_ids: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"case at index {index} must be an object")
        missing = REQUIRED_CASE_FIELDS.difference(case)
        if missing:
            raise ValueError(f"case {index} missing fields: {sorted(missing)}")
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"case {index} id must be a non-empty string")
        if case_id in seen_ids:
            raise ValueError(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)
        if case["language"] not in {"en", "vi"}:
            raise ValueError(f"case {case_id} language must be en or vi")
        if not isinstance(case["category"], str) or not case["category"]:
            raise ValueError(f"case {case_id} category must be a string")
        if not isinstance(case["input_message"], str) or not case["input_message"]:
            raise ValueError(f"case {case_id} input_message must be a string")
        if not isinstance(case["expected_should_create_workflow"], bool):
            raise ValueError(
                f"case {case_id} expected_should_create_workflow must be bool"
            )
        if not isinstance(case["expected_requested_addons"], list):
            raise ValueError(
                f"case {case_id} expected_requested_addons must be a list"
            )
        if not isinstance(case["expected_safety_outcome"], str):
            raise ValueError(f"case {case_id} expected_safety_outcome must be string")


def evaluate_dataset(dataset: dict[str, Any]) -> list[CaseResult]:
    config = deterministic_config()
    return [evaluate_case(case, config) for case in dataset["cases"]]


def deterministic_config() -> BridgeConfig:
    return BridgeConfig(
        telegram_bot_token=None,
        backend_api_base_url="http://localhost:8000/api/v1",
        frontend_base_url="http://localhost:3000",
        manager_email="manager@example.test",
        manager_password="DemoPassword123!",
        poll_interval_seconds=2.0,
        allowed_chat_id=None,
        dry_run=True,
        once=True,
        auto_run=True,
        llm_extraction_enabled=False,
        llm_provider="ollama",
        llm_model="qwen2.5:7b-instruct-q4_K_M",
        llm_base_url="http://localhost:11434",
        llm_timeout_seconds=30,
        sales_replies_enabled=False,
    )


def evaluate_case(case: dict[str, Any], config: BridgeConfig) -> CaseResult:
    actual = classify_message(case["input_message"], config)
    errors: list[str] = []

    compare_value(
        errors,
        "should_create_workflow",
        case["expected_should_create_workflow"],
        actual.should_create_workflow,
    )
    compare_value(
        errors,
        "safety_outcome",
        case["expected_safety_outcome"],
        actual.safety_outcome,
    )
    compare_value(
        errors,
        "normalized_item_name",
        case["expected_normalized_item_name"],
        actual.normalized_item_name,
    )
    compare_value(errors, "quantity", case["expected_quantity"], actual.quantity)
    compare_value(
        errors,
        "requested_addons",
        tuple(case["expected_requested_addons"]),
        actual.requested_addons,
    )

    return CaseResult(
        case_id=case["id"],
        language=case["language"],
        category=case["category"],
        passed=not errors,
        expected_safety_outcome=case["expected_safety_outcome"],
        actual_safety_outcome=actual.safety_outcome,
        errors=tuple(errors),
    )


def classify_message(text: str, config: BridgeConfig) -> ActualOutcome:
    if is_greeting_message(text):
        return ActualOutcome(
            should_create_workflow=False,
            safety_outcome="greeting_help",
        )

    extracted = extract_customer_request(text, config)
    if isinstance(extracted, ParsedCustomerRequest):
        return ActualOutcome(
            should_create_workflow=True,
            safety_outcome="create_workflow",
            normalized_item_name=extracted.item_name,
            quantity=extracted.quantity,
            requested_addons=tuple(extracted.requested_addons),
        )
    if isinstance(extracted, UnsupportedMixedRequest):
        supported = extracted.supported
        return ActualOutcome(
            should_create_workflow=False,
            safety_outcome="mixed_item_blocked",
            normalized_item_name=supported.item_name if supported else None,
            quantity=supported.quantity if supported else None,
            requested_addons=tuple(supported.requested_addons) if supported else (),
        )

    unsupported = detect_unsupported_item_mentions(text)
    if unsupported:
        return ActualOutcome(
            should_create_workflow=False,
            safety_outcome="unsupported_item",
            quantity=unsupported[0].quantity,
        )

    catalog_item = find_catalog_item(text)
    if catalog_item is not None:
        return ActualOutcome(
            should_create_workflow=False,
            safety_outcome="missing_quantity",
            normalized_item_name=catalog_item.normalized_item_name,
        )

    quantity = first_quantity(text)
    if quantity is not None:
        return ActualOutcome(
            should_create_workflow=False,
            safety_outcome="missing_item",
            quantity=quantity,
        )

    return ActualOutcome(
        should_create_workflow=False,
        safety_outcome="ask_clarification",
    )


def first_quantity(text: str) -> int | None:
    match = re.search(r"\b(\d{1,5})\b", text)
    return int(match.group(1)) if match else None


def compare_value(
    errors: list[str],
    field: str,
    expected: object,
    actual: object,
) -> None:
    if expected != actual:
        errors.append(f"{field}: expected {expected!r}, got {actual!r}")


def build_metrics(dataset: dict[str, Any], results: list[CaseResult]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failures = [failure_summary(result) for result in results if not result.passed]
    category_breakdown = breakdown(results, "category")
    language_breakdown = breakdown(results, "language")
    safety_violations = [
        result.case_id
        for result in results
        if not result.passed and result.category in safety_categories()
    ]

    return {
        "benchmark_name": dataset["benchmark_name"],
        "version": dataset["version"],
        "generated_at": BENCHMARK_GENERATED_AT,
        "deterministic": True,
        "provider_calls": False,
        "live_network_calls": False,
        "total_cases": total,
        "passed_cases": passed,
        "failed_cases": total - passed,
        "accuracy": round(passed / total, 4) if total else 0.0,
        "category_breakdown": category_breakdown,
        "language_breakdown": language_breakdown,
        "safety_violations": safety_violations,
        "failures": failures,
    }


def safety_categories() -> set[str]:
    return {
        "unsupported_item",
        "mixed_supported_unsupported",
        "safety_forbidden_claims",
    }


def failure_summary(result: CaseResult) -> dict[str, Any]:
    return {
        "id": result.case_id,
        "category": result.category,
        "language": result.language,
        "expected_safety_outcome": result.expected_safety_outcome,
        "actual_safety_outcome": result.actual_safety_outcome,
        "errors": list(result.errors),
    }


def breakdown(results: list[CaseResult], field: str) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "passed": 0, "failed": 0}
    )
    for result in results:
        key = getattr(result, field)
        counts[key]["total"] += 1
        if result.passed:
            counts[key]["passed"] += 1
        else:
            counts[key]["failed"] += 1
    return dict(sorted(counts.items()))


def format_human_summary(metrics: dict[str, Any]) -> str:
    lines = [
        "SPEC-022 Telegram parser benchmark",
        f"Dataset: {metrics['benchmark_name']} ({metrics['version']})",
        (
            f"Result: {metrics['passed_cases']}/{metrics['total_cases']} "
            f"cases passed; accuracy {metrics['accuracy']:.4f}"
        ),
        (
            "Mode: deterministic, no provider calls, no live network calls, "
            "no backend API calls"
        ),
        f"Safety violations: {len(metrics['safety_violations'])}",
        "Category breakdown:",
    ]
    for category, values in metrics["category_breakdown"].items():
        lines.append(
            f"  - {category}: {values['passed']}/{values['total']} passed"
        )
    if metrics["failures"]:
        lines.append("Failures:")
        for failure in metrics["failures"]:
            lines.append(
                "  - "
                f"{failure['id']}: expected {failure['expected_safety_outcome']}, "
                f"got {failure['actual_safety_outcome']}"
            )
    return "\n".join(lines)


def contains_forbidden_claim(value: str) -> bool:
    normalized = value.lower()
    return any(claim in normalized for claim in FORBIDDEN_OUTPUT_CLAIMS)


if __name__ == "__main__":
    raise SystemExit(main())
