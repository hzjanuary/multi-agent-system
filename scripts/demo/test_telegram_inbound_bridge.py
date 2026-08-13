import io
import json
import os
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from scripts.demo.telegram_inbound_bridge import (
    ApiError,
    BridgeConfig,
    EXAMPLE_MESSAGE,
    LLMExtractionError,
    ParsedCustomerRequest,
    ReferenceEvidencePriceSummary,
    ReferenceEvidenceSourceSummary,
    ReferenceEvidenceSummary,
    TelegramPendingQuote,
    TrustedFinalPrice,
    UnsupportedMixedRequest,
    WorkflowCreationResult,
    build_workflow_create_payload,
    config_from_env,
    customer_product_name,
    extract_customer_request,
    extract_trusted_price_from_knowledge,
    extract_trusted_price_from_workflow,
    follow_up_message,
    format_final_price,
    format_vnd,
    greeting_message,
    handle_update,
    is_greeting_message,
    latest_approval_decision,
    llm_extract_customer_request,
    parse_args,
    parse_llm_extraction_result,
    parse_customer_request,
    process_pending_approvals,
    reference_evidence_for_request,
    reference_evidence_from_price_research_result,
    register_pending_quote,
    safe_evidence_url,
    sender_display_name,
    telegram_approval_changes_requested_reply,
    telegram_approval_rejected_reply,
    telegram_final_quote_reply,
    telegram_manual_final_quote_reply,
    telegram_run_failed_reply,
    telegram_workflow_reply,
    trusted_price_from_mapping,
    unsupported_mixed_item_message,
)
from scripts.demo.catalog import (
    CATALOG_ITEMS,
    CATALOG_VERSION,
    OFFICE_365_ADDON_ID,
    compatible_addons,
    find_catalog_item,
    get_catalog_item_by_name,
    supported_item_families,
)


class DemoCatalogTests(unittest.TestCase):
    def test_catalog_contains_all_supported_item_families(self) -> None:
        self.assertEqual(
            set(supported_item_families()),
            {
                "Standard business laptop",
                "Business desktop PC",
                "Office monitor",
                "Office printer",
                "Wireless keyboard and mouse combo",
            },
        )
        for item in CATALOG_ITEMS:
            with self.subTest(item=item.item_id):
                self.assertTrue(item.item_id)
                self.assertTrue(item.display_name)
                self.assertTrue(item.normalized_item_name)
                self.assertTrue(item.aliases_en)
                self.assertTrue(item.aliases_vi)
                self.assertTrue(item.demo_only)

    def test_catalog_alias_normalization_english_and_vietnamese(self) -> None:
        examples = {
            "business laptop": "Standard business laptop",
            "máy tính xách tay": "Standard business laptop",
            "desktop pc": "Business desktop PC",
            "máy tính để bàn": "Business desktop PC",
            "office monitor": "Office monitor",
            "màn hình văn phòng": "Office monitor",
            "hp printer": "Office printer",
            "máy in hp": "Office printer",
            "wireless keyboard and mouse": "Wireless keyboard and mouse combo",
            "bộ bàn phím chuột": "Wireless keyboard and mouse combo",
        }
        for alias, expected_name in examples.items():
            with self.subTest(alias=alias):
                item = find_catalog_item(alias)
                self.assertIsNotNone(item)
                assert item is not None
                self.assertEqual(item.normalized_item_name, expected_name)

    def test_catalog_addon_compatibility(self) -> None:
        laptop = get_catalog_item_by_name("Standard business laptop")
        desktop = get_catalog_item_by_name("Business desktop PC")
        monitor = get_catalog_item_by_name("Office monitor")
        assert laptop is not None
        assert desktop is not None
        assert monitor is not None

        self.assertTrue(compatible_addons(laptop, (OFFICE_365_ADDON_ID,)))
        self.assertTrue(compatible_addons(desktop, (OFFICE_365_ADDON_ID,)))
        self.assertFalse(compatible_addons(monitor, (OFFICE_365_ADDON_ID,)))


class TelegramInboundBridgeParserTests(unittest.TestCase):
    def config(self, *, sales: bool = False, llm: bool = False) -> BridgeConfig:
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
            llm_extraction_enabled=llm,
            llm_provider="ollama",
            llm_model="qwen2.5:7b-instruct-q4_K_M",
            llm_base_url="http://localhost:11434",
            llm_timeout_seconds=30,
            sales_replies_enabled=sales,
        )

    def test_board_demo_phrase_parses_quantity_and_laptops(self) -> None:
        parsed = parse_customer_request(EXAMPLE_MESSAGE)

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 50)
        self.assertEqual(parsed.item_name, "Standard business laptop")
        self.assertEqual(parsed.language, "en")

    def test_parser_accepts_simple_laptop_variations(self) -> None:
        examples = [
            ("50 laptops", 50),
            ("purchase 20 laptops", 20),
            ("buy 10 laptops", 10),
            ("quote for 5 business laptops", 5),
            ("quotation for 7 standard business laptops", 7),
        ]

        for text, expected_quantity in examples:
            with self.subTest(text=text):
                parsed = parse_customer_request(text)
                self.assertIsNotNone(parsed)
                assert parsed is not None
                self.assertEqual(parsed.quantity, expected_quantity)
                self.assertEqual(parsed.item_name, "Standard business laptop")

    def test_parser_accepts_vietnamese_laptop_request_with_office_365(self) -> None:
        parsed = parse_customer_request(
            "tôi muốn mua 50 cái máy tính xách tay doanh nhân tiêu chuẩn "
            "có cài sẵn office 365"
        )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 50)
        self.assertEqual(parsed.item_name, "Standard business laptop")
        self.assertEqual(parsed.language, "vi")
        self.assertEqual(parsed.requested_addons, ("office_365",))
        self.assertEqual(parsed.options_summary, "Office 365")

    def test_parser_accepts_vietnamese_laptop_variations(self) -> None:
        examples = [
            ("tôi muốn mua 50 máy tính xách tay", 50),
            ("cần báo giá 50 laptop", 50),
            ("báo giá cho 30 máy tính xách tay", 30),
            ("mua 20 laptop cho phòng kinh doanh", 20),
            ("cần 15 laptop doanh nhân", 15),
            ("50 máy tính xách tay có cài office 365", 50),
        ]

        for text, expected_quantity in examples:
            with self.subTest(text=text):
                parsed = parse_customer_request(text)
                self.assertIsNotNone(parsed)
                assert parsed is not None
                self.assertEqual(parsed.quantity, expected_quantity)
                self.assertEqual(parsed.item_name, "Standard business laptop")
                self.assertEqual(parsed.language, "vi")

    def test_greetings_do_not_parse_as_procurement_requests(self) -> None:
        for text in ["xin chào", "hello", "hi"]:
            with self.subTest(text=text):
                self.assertTrue(is_greeting_message(text))
                self.assertIsNone(parse_customer_request(text))

    def test_parser_rejects_missing_quantity_or_item(self) -> None:
        self.assertIsNone(parse_customer_request("please send a quotation"))
        self.assertIsNone(parse_customer_request("quote for laptops"))
        self.assertIsNone(parse_customer_request("quote for 12"))
        self.assertIsNone(parse_customer_request("tôi muốn mua máy tính xách tay"))
        self.assertIsNone(parse_customer_request("cần báo giá laptop"))
        self.assertIsNone(parse_customer_request("quote for 10 ergonomic chairs"))

    def test_office_365_addon_detection(self) -> None:
        examples = [
            "50 máy tính xách tay có cài office 365",
            "50 laptop có office",
            "50 laptop microsoft 365",
            "50 laptop cài sẵn office",
        ]

        for text in examples:
            with self.subTest(text=text):
                parsed = parse_customer_request(text)
                self.assertIsNotNone(parsed)
                assert parsed is not None
                self.assertEqual(parsed.requested_addons, ("office_365",))

    def test_workflow_payload_matches_existing_create_contract(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None

        payload = build_workflow_create_payload(
            parsed,
            customer_name="Ada Customer",
            chat_id="12345",
            message_id="67890",
        )

        self.assertEqual(payload["workflow_type"], "procurement_quotation")
        self.assertEqual(payload["domain"], "it_equipment")
        self.assertEqual(payload["request"]["source"], "telegram")
        self.assertEqual(
            payload["request"]["request_text"],
            "quote for 50 standard business laptops",
        )
        self.assertEqual(payload["request"]["customer"]["name"], "Ada Customer")
        self.assertEqual(
            payload["request"]["items"],
            [{"name": "Standard business laptop", "quantity": 50}],
        )
        self.assertEqual(payload["request"]["requested_addons"], [])
        self.assertEqual(payload["metadata"]["state_version"], 1)
        self.assertEqual(payload["metadata"]["tags"]["source"], "telegram")
        self.assertTrue(payload["metadata"]["attributes"]["demo"])
        self.assertEqual(payload["metadata"]["attributes"]["language"], "en")
        self.assertEqual(payload["metadata"]["attributes"]["requested_addons"], [])
        self.assertEqual(
            payload["metadata"]["attributes"]["parser_version"],
            "telegram-demo-parser-v4",
        )
        self.assertEqual(
            payload["metadata"]["attributes"]["extraction_mode"],
            "deterministic",
        )
        self.assertEqual(
            payload["metadata"]["attributes"]["telegram_chat_id"],
            "12345",
        )
        self.assertEqual(
            payload["metadata"]["attributes"]["telegram_message_id"],
            "67890",
        )
        self.assertEqual(
            payload["metadata"]["attributes"]["catalog"],
            {
                "catalog_version": CATALOG_VERSION,
                "item_id": "standard_business_laptop",
                "normalized_item_name": "Standard business laptop",
                "item_family": "business_laptop",
                "requested_addons": [],
            },
        )

    def test_vietnamese_payload_includes_language_and_requested_addons(self) -> None:
        parsed = parse_customer_request("cần báo giá 50 laptop có office")
        assert parsed is not None

        payload = build_workflow_create_payload(
            parsed,
            customer_name="Vietnamese Customer",
            chat_id="12345",
            message_id="67890",
        )

        self.assertEqual(payload["metadata"]["attributes"]["language"], "vi")
        self.assertEqual(
            payload["metadata"]["attributes"]["requested_addons"],
            ["office_365"],
        )
        self.assertEqual(payload["request"]["requested_addons"], ["office_365"])

    def test_reply_summary_mentions_parsed_request_and_addons(self) -> None:
        parsed = parse_customer_request("cần báo giá 50 laptop có office")
        assert parsed is not None
        config = BridgeConfig(
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

        reply = telegram_workflow_reply(
            config=config,
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
        )

        self.assertIn("Parsed: 50 x Standard business laptop", reply)
        self.assertIn("Options: Office 365", reply)
        self.assertIn("Human approval is required before resume", reply)

    def test_supported_catalog_item_examples_create_requests(self) -> None:
        examples = [
            ("báo giá 20 máy tính bàn văn phòng", 20, "Business desktop PC", "vi"),
            ("báo giá 10 màn hình văn phòng", 10, "Office monitor", "vi"),
            ("báo giá 5 máy in văn phòng", 5, "Office printer", "vi"),
            (
                "báo giá 30 bộ bàn phím chuột không dây",
                30,
                "Wireless keyboard and mouse combo",
                "vi",
            ),
            ("quote 15 business desktop PCs", 15, "Business desktop PC", "en"),
            ("quote 12 office monitors", 12, "Office monitor", "en"),
            ("quote 3 office printers", 3, "Office printer", "en"),
            (
                "quote 25 wireless keyboard and mouse combos",
                25,
                "Wireless keyboard and mouse combo",
                "en",
            ),
        ]
        for text, quantity, item_name, language in examples:
            with self.subTest(text=text):
                parsed = parse_customer_request(text)
                self.assertIsNotNone(parsed)
                assert parsed is not None
                self.assertEqual(parsed.quantity, quantity)
                self.assertEqual(parsed.item_name, item_name)
                self.assertEqual(parsed.language, language)

    def test_laptop_van_phong_with_office_365_still_creates_request(self) -> None:
        parsed = parse_customer_request("báo giá 20 laptop văn phòng kèm office 365")

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 20)
        self.assertEqual(parsed.item_name, "Standard business laptop")
        self.assertEqual(parsed.requested_addons, ("office_365",))

    def test_incompatible_addon_request_does_not_create_workflow(self) -> None:
        self.assertIsNone(parse_customer_request("báo giá 10 màn hình kèm office 365"))

    def test_printer_is_now_supported_catalog_item(self) -> None:
        parsed = extract_customer_request("báo giá 5 máy in hp", self.config())

        self.assertIsInstance(parsed, ParsedCustomerRequest)
        assert isinstance(parsed, ParsedCustomerRequest)
        self.assertEqual(parsed.quantity, 5)
        self.assertEqual(parsed.item_name, "Office printer")

    def test_mixed_laptop_and_projector_request_does_not_create_workflow(self) -> None:
        parsed = extract_customer_request(
            "báo giá 20 laptop và 3 máy chiếu",
            self.config(),
        )

        self.assertIsInstance(parsed, UnsupportedMixedRequest)
        assert isinstance(parsed, UnsupportedMixedRequest)
        self.assertIsNotNone(parsed.supported)
        assert parsed.supported is not None
        self.assertEqual(parsed.supported.quantity, 20)
        self.assertEqual(parsed.supported.item_name, "Standard business laptop")
        self.assertEqual(parsed.unsupported_summary, "3 x projector")

    def test_technical_mixed_item_reply_mentions_supported_and_unsupported(self) -> None:
        parsed = extract_customer_request(
            "quote 10 monitors and 2 servers",
            self.config(),
        )
        assert isinstance(parsed, UnsupportedMixedRequest)

        reply = unsupported_mixed_item_message(self.config(), parsed)

        self.assertIn("Supported: 10 x Office monitor", reply)
        self.assertIn("Unsupported: 2 x server", reply)
        self.assertIn("Please send a request with supported items only", reply)
        self.assertIn("office printers", reply)

    def test_sales_mixed_item_reply_is_customer_friendly(self) -> None:
        parsed = extract_customer_request(
            "báo giá 5 máy in và 2 máy chủ",
            self.config(sales=True),
        )
        assert isinstance(parsed, UnsupportedMixedRequest)

        reply = unsupported_mixed_item_message(self.config(sales=True), parsed)

        self.assertIn("Em đã nhận được yêu cầu gồm 5 x máy in văn phòng", reply)
        self.assertIn("2 x server", reply)
        self.assertIn("catalog demo chỉ hỗ trợ laptop", reply)
        self.assertIn("chưa tạo báo giá để tránh thiếu thông tin", reply)
        self.assertIn("báo giá 20 laptop văn phòng tiêu chuẩn", reply)

    def test_llm_supported_only_result_is_blocked_when_original_mentions_server(self) -> None:
        llm_only_laptop = ParsedCustomerRequest(
            original_text="báo giá 20 cái laptop và 5 máy chủ",
            quantity=20,
            item_name="Standard business laptop",
            language="vi",
            extraction_mode="llm",
            llm_provider="ollama",
            llm_model="qwen2.5:7b-instruct-q4_K_M",
        )

        parsed = extract_customer_request(
            "báo giá 20 cái laptop và 5 máy chủ",
            self.config(llm=True),
            llm_extractor=lambda _text, _config: llm_only_laptop,
        )

        self.assertIsInstance(parsed, UnsupportedMixedRequest)
        assert isinstance(parsed, UnsupportedMixedRequest)
        self.assertEqual(parsed.supported_summary, "20 x Standard business laptop")
        self.assertEqual(parsed.unsupported_summary, "5 x server")

    def test_unsupported_only_item_does_not_create_workflow(self) -> None:
        self.assertIsNone(extract_customer_request("báo giá 3 máy chiếu", self.config()))
        self.assertIsNone(extract_customer_request("quote 2 servers", self.config()))

    def test_mixed_request_with_generic_unknown_item_is_refused(self) -> None:
        parsed = extract_customer_request(
            "báo giá 20 cái laptop và 5 cái ghế văn phòng",
            self.config(),
        )

        self.assertIsInstance(parsed, UnsupportedMixedRequest)
        assert isinstance(parsed, UnsupportedMixedRequest)
        self.assertEqual(parsed.supported_summary, "20 x Standard business laptop")
        self.assertEqual(parsed.unsupported_summary, "5 x ghế văn phòng")

    def test_mixed_request_with_second_catalog_item_is_refused(self) -> None:
        parsed = extract_customer_request(
            "báo giá 20 laptop và 3 máy in",
            self.config(),
        )

        self.assertIsInstance(parsed, UnsupportedMixedRequest)
        assert isinstance(parsed, UnsupportedMixedRequest)
        self.assertEqual(parsed.supported_summary, "20 x Standard business laptop")
        self.assertEqual(parsed.unsupported_summary, "3 x Office printer")

    def test_laptop_with_screen_qualifier_still_creates_request(self) -> None:
        parsed = extract_customer_request(
            "báo giá 20 laptop màn hình LED",
            self.config(),
        )

        self.assertIsInstance(parsed, ParsedCustomerRequest)
        assert isinstance(parsed, ParsedCustomerRequest)
        self.assertEqual(parsed.quantity, 20)
        self.assertEqual(parsed.item_name, "Standard business laptop")

    def test_unsupported_generic_only_item_does_not_create_workflow(self) -> None:
        self.assertIsNone(extract_customer_request("quote 2 ergonomic chairs", self.config()))
        self.assertIsNone(extract_customer_request("cần 3 cái quạt điện", self.config()))

    def test_laptop_only_vietnamese_request_still_creates_request(self) -> None:
        parsed = extract_customer_request("báo giá 20 laptop", self.config())

        self.assertIsInstance(parsed, ParsedCustomerRequest)
        assert isinstance(parsed, ParsedCustomerRequest)
        self.assertEqual(parsed.quantity, 20)
        self.assertEqual(parsed.item_name, "Standard business laptop")

    def test_laptop_with_office_still_creates_request(self) -> None:
        parsed = extract_customer_request(
            "tôi muốn mua 50 cái máy tính xách tay doanh nhân tiêu chuẩn có cài sẵn office 365",
            self.config(),
        )

        self.assertIsInstance(parsed, ParsedCustomerRequest)
        assert isinstance(parsed, ParsedCustomerRequest)
        self.assertEqual(parsed.quantity, 50)
        self.assertEqual(parsed.requested_addons, ("office_365",))

    def test_greeting_and_missing_quantity_remain_followups(self) -> None:
        self.assertTrue(is_greeting_message("xin chào"))
        self.assertIsNone(extract_customer_request("xin chào", self.config()))
        self.assertIsNone(extract_customer_request("tôi muốn mua laptop", self.config()))

    def test_mixed_item_reply_does_not_expose_raw_llm_or_provider_payload(self) -> None:
        parsed = extract_customer_request(
            "báo giá 20 cái laptop và 5 máy chủ",
            self.config(sales=True),
        )
        assert isinstance(parsed, UnsupportedMixedRequest)

        reply = unsupported_mixed_item_message(self.config(sales=True), parsed).lower()

        self.assertNotIn("prompt", reply)
        self.assertNotIn("provider_payload", reply)
        self.assertNotIn("raw_response", reply)
        self.assertNotIn("traceback", reply)

    def test_sender_display_name_uses_safe_telegram_profile_fields(self) -> None:
        self.assertEqual(
            sender_display_name(
                {"from": {"first_name": "Ada", "last_name": "Lovelace"}}
            ),
            "Ada Lovelace",
        )
        self.assertEqual(
            sender_display_name({"from": {"username": "procurement_user"}}),
            "@procurement_user",
        )
        self.assertEqual(sender_display_name({}), "Telegram Customer")


class TelegramInboundBridgeLLMExtractionTests(unittest.TestCase):
    def config(self, *, enabled: bool = True) -> BridgeConfig:
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
            llm_extraction_enabled=enabled,
            llm_provider="ollama",
            llm_model="qwen2.5:7b-instruct-q4_K_M",
            llm_base_url="http://localhost:11434",
            llm_timeout_seconds=30,
            sales_replies_enabled=False,
        )

    def test_llm_json_parses_when_clean(self) -> None:
        parsed = parse_llm_extraction_result(
            '{"language":"vi","intent":"procurement_rfq","items":[{"name":"laptop","quantity":50}],"requested_addons":["office_365"],"needs_follow_up":false,"follow_up_question":""}',
            original_text="cần báo giá 50 laptop có office 365",
            provider="ollama",
            model="qwen2.5:7b-instruct-q4_K_M",
        )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 50)
        self.assertEqual(parsed.item_name, "Standard business laptop")
        self.assertEqual(parsed.requested_addons, ("office_365",))
        self.assertEqual(parsed.extraction_mode, "llm")
        self.assertEqual(parsed.llm_provider, "ollama")

    def test_llm_json_parses_when_fenced(self) -> None:
        parsed = parse_llm_extraction_result(
            '```json\n{"language":"en","intent":"procurement_rfq","items":[{"name":"notebook","quantity":"12"}],"requested_addons":[],"needs_follow_up":false,"follow_up_question":""}\n```',
            original_text="please quote 12 notebooks",
            provider="ollama",
            model="qwen2.5:7b-instruct-q4_K_M",
        )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 12)
        self.assertEqual(parsed.item_name, "Standard business laptop")
        self.assertEqual(parsed.language, "en")

    def test_llm_missed_office_addon_but_normalizer_adds_it(self) -> None:
        parsed = parse_llm_extraction_result(
            '{"language":"vi","intent":"procurement_rfq","items":[{"name":"máy tính xách tay","quantity":50}],"requested_addons":[],"needs_follow_up":false,"follow_up_question":""}',
            original_text="50 máy tính xách tay có cài office 365",
            provider="ollama",
            model="qwen2.5:7b-instruct-q4_K_M",
        )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.requested_addons, ("office_365",))

    def test_llm_long_item_name_normalizes_to_standard_laptop(self) -> None:
        parsed = parse_llm_extraction_result(
            '{"language":"en","intent":"procurement_rfq","items":[{"name":"premium business laptop with office 365 preinstalled","quantity":25}],"requested_addons":[],"needs_follow_up":false,"follow_up_question":""}',
            original_text="quote 25 premium business laptop with office 365 preinstalled",
            provider="ollama",
            model="qwen2.5:7b-instruct-q4_K_M",
        )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.item_name, "Standard business laptop")
        self.assertEqual(parsed.requested_addons, ("office_365",))

    def test_llm_invalid_json_falls_back_to_deterministic_parser(self) -> None:
        parsed = extract_customer_request(
            "quote for 50 standard business laptops",
            self.config(),
            llm_extractor=lambda _text, _config: (_ for _ in ()).throw(
                LLMExtractionError("bad json")
            ),
        )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 50)
        self.assertEqual(parsed.extraction_mode, "fallback")
        self.assertEqual(parsed.llm_provider, "ollama")

    def test_llm_timeout_error_falls_back_to_deterministic_parser(self) -> None:
        def timeout_extractor(_text: str, _config: BridgeConfig) -> None:
            raise LLMExtractionError("timeout")

        parsed = extract_customer_request(
            "cần báo giá 50 laptop",
            self.config(),
            llm_extractor=timeout_extractor,
        )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 50)
        self.assertEqual(parsed.extraction_mode, "fallback")

    def test_llm_payload_requests_strict_json_and_disables_thinking(self) -> None:
        captured: dict[str, object] = {}

        class FakeResponse:
            def __init__(self, payload: dict[str, object]) -> None:
                self._data = json.dumps(payload).encode("utf-8")

            def __enter__(self) -> FakeResponse:
                return self

            def __exit__(self, *exc: object) -> bool:
                return False

            def read(self) -> bytes:
                return self._data

        def fake_urlopen(request: Any, timeout: int) -> FakeResponse:
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return FakeResponse(
                {
                    "message": {
                        "content": '{"language":"vi","intent":"procurement_rfq","items":[{"name":"laptop","quantity":50}],"requested_addons":[],"needs_follow_up":false,"follow_up_question":""}'
                    }
                }
            )

        with patch(
            "scripts.demo.telegram_inbound_bridge.urllib.request.urlopen",
            fake_urlopen,
        ):
            parsed = llm_extract_customer_request(
                "cần báo giá 50 laptop",
                self.config(),
            )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 50)
        payload = captured["payload"]
        assert isinstance(payload, dict)
        self.assertIs(payload.get("think"), False)
        self.assertEqual(payload.get("format"), "json")
        self.assertEqual(captured["timeout"], 30)

    def test_llm_extraction_uses_thinking_field_when_content_is_empty(self) -> None:
        class FakeResponse:
            def __init__(self) -> None:
                self._data = json.dumps(
                    {
                        "message": {
                            "content": "",
                            "thinking": '{"language":"en","intent":"procurement_rfq","items":[{"name":"monitor","quantity":4}],"requested_addons":[],"needs_follow_up":false,"follow_up_question":""}',
                        }
                    }
                ).encode("utf-8")

            def __enter__(self) -> FakeResponse:
                return self

            def __exit__(self, *exc: object) -> bool:
                return False

            def read(self) -> bytes:
                return self._data

        with patch(
            "scripts.demo.telegram_inbound_bridge.urllib.request.urlopen",
            lambda request, timeout: FakeResponse(),
        ):
            parsed = llm_extract_customer_request(
                "quote 4 monitors",
                self.config(),
            )

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.quantity, 4)
        self.assertEqual(parsed.item_name, "Office monitor")

    def test_llm_extraction_raises_when_content_and_thinking_empty(self) -> None:
        class FakeResponse:
            def __enter__(self) -> FakeResponse:
                return self

            def __exit__(self, *exc: object) -> bool:
                return False

            def read(self) -> bytes:
                return b'{"message": {"content": "", "thinking": ""}}'

        with patch(
            "scripts.demo.telegram_inbound_bridge.urllib.request.urlopen",
            lambda request, timeout: FakeResponse(),
        ):
            with self.assertRaises(LLMExtractionError):
                llm_extract_customer_request(
                    "cần báo giá 50 laptop",
                    self.config(),
                )

    def test_llm_timeout_default_is_ninety_seconds(self) -> None:
        args = parse_args([])
        with patch.dict("os.environ", {}, clear=True):
            config = config_from_env(args)

        self.assertEqual(config.llm_timeout_seconds, 90)

    def test_missing_quantity_follow_up_does_not_create_request(self) -> None:
        parsed = parse_llm_extraction_result(
            '{"language":"vi","intent":"procurement_rfq","items":[{"name":"laptop","quantity":0}],"requested_addons":[],"needs_follow_up":true,"follow_up_question":"Bạn cần bao nhiêu laptop?"}',
            original_text="tôi muốn mua laptop",
            provider="ollama",
            model="qwen2.5:7b-instruct-q4_K_M",
        )

        self.assertIsNone(parsed)

    def test_unsupported_item_follow_up_does_not_create_request(self) -> None:
        parsed = parse_llm_extraction_result(
            '{"language":"en","intent":"procurement_rfq","items":[{"name":"ergonomic chair","quantity":10}],"requested_addons":[],"needs_follow_up":true,"follow_up_question":"Which supported item?"}',
            original_text="quote for 10 chairs",
            provider="ollama",
            model="qwen2.5:7b-instruct-q4_K_M",
        )

        self.assertIsNone(parsed)

    def test_extraction_metadata_is_bounded_and_safe(self) -> None:
        parsed = parse_llm_extraction_result(
            '{"language":"en","intent":"procurement_rfq","items":[{"name":"laptop","quantity":50}],"requested_addons":[],"needs_follow_up":false,"follow_up_question":""}',
            original_text="quote for 50 laptops",
            provider="ollama",
            model="qwen2.5:7b-instruct-q4_K_M",
        )
        assert parsed is not None

        payload = build_workflow_create_payload(
            parsed,
            customer_name="Ada Customer",
            chat_id="12345",
            message_id="67890",
        )
        attributes = payload["metadata"]["attributes"]

        self.assertEqual(attributes["extraction_mode"], "llm")
        self.assertEqual(attributes["llm_provider"], "ollama")
        self.assertEqual(attributes["llm_model"], "qwen2.5:7b-instruct-q4_K_M")
        serialized = str(attributes).lower()
        self.assertNotIn("prompt", serialized)
        self.assertNotIn("provider_payload", serialized)
        self.assertNotIn("raw_response", serialized)

    def test_no_workflow_creation_for_greeting(self) -> None:
        parsed = parse_llm_extraction_result(
            '{"language":"vi","intent":"greeting","items":[],"requested_addons":[],"needs_follow_up":true,"follow_up_question":"Bạn cần mua gì?"}',
            original_text="xin chào",
            provider="ollama",
            model="qwen2.5:7b-instruct-q4_K_M",
        )

        self.assertIsNone(parsed)


class TelegramInboundBridgeSalesReplyTests(unittest.TestCase):
    def config(self, *, sales: bool = False) -> BridgeConfig:
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
            sales_replies_enabled=sales,
        )

    def vietnamese_parsed_request(self) -> object:
        parsed = parse_customer_request("cần báo giá 50 laptop có office 365")
        assert parsed is not None
        return parsed

    def test_default_technical_reply_remains_available(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None

        reply = telegram_workflow_reply(
            config=self.config(),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
        )

        self.assertIn("Parsed: 50 x Standard business laptop", reply)
        self.assertIn("The workflow was created and run to the approval boundary.", reply)
        self.assertIn("Human approval is required before resume", reply)

    def test_sales_replies_flag_enables_sales_response(self) -> None:
        args = parse_args(["--sales-replies"])
        with patch.dict("os.environ", {}, clear=True):
            config = config_from_env(args)

        self.assertTrue(config.sales_replies_enabled)

    def test_sales_replies_env_enables_sales_response(self) -> None:
        args = parse_args([])
        with patch.dict("os.environ", {"TELEGRAM_SALES_REPLY_ENABLED": "true"}, clear=True):
            config = config_from_env(args)

        self.assertTrue(config.sales_replies_enabled)

    def test_vietnamese_success_sales_reply_is_customer_friendly(self) -> None:
        parsed = self.vietnamese_parsed_request()

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
        )

        self.assertIn("Cảm ơn anh/chị", reply)
        self.assertIn("50 x Standard business laptop", reply)
        self.assertIn("Office 365", reply)
        self.assertIn("Đây chưa phải báo giá cuối cùng", reply)
        self.assertNotIn("workflow-123", reply)
        self.assertNotIn("WAITING_APPROVAL", reply)
        self.assertNotIn("localhost", reply)
        self.assertNotIn("http://", reply)

    def test_sales_reply_with_no_evidence_is_semantically_unchanged(self) -> None:
        parsed = self.vietnamese_parsed_request()

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
        )

        self.assertNotIn("Tham khảo giá nội bộ", reply)
        self.assertIn("Cảm ơn anh/chị", reply)
        self.assertNotIn("WAITING_APPROVAL", reply)

    def test_sales_reply_never_leaks_reference_evidence_to_customer(self) -> None:
        parsed = self.vietnamese_parsed_request()
        evidence = ReferenceEvidenceSummary(
            provider="tavily",
            evidence_label="reference_price_research",
            sources=(
                ReferenceEvidenceSourceSummary(
                    title="Supplier reference listing",
                    url="https://supplier.example/laptops",
                ),
            ),
            confidence=0.72,
            warnings=("Manual pricing review is required.",),
            is_final_quote=False,
        )

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        )

        self.assertNotIn("Tham khảo giá nội bộ", reply)
        self.assertNotIn("tavily", reply)
        self.assertNotIn("confidence 0.72", reply)
        self.assertNotIn("Supplier reference listing", reply)
        self.assertNotIn("https://supplier.example/laptops", reply)
        self.assertIn("chưa phải báo giá cuối cùng", reply)

    def test_sales_reply_never_displays_reference_amounts_to_customer(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None
        evidence = ReferenceEvidenceSummary(
            provider="manual",
            evidence_label="reference_price_research",
            reference_prices=(
                ReferenceEvidencePriceSummary(
                    label="Unit reference",
                    amount="12000000",
                    currency="VND",
                    unit="unit",
                ),
            ),
            sources=(
                ReferenceEvidenceSourceSummary(
                    title="Manual catalog reference",
                    url="https://catalog.example/reference",
                ),
            ),
            confidence=0.8,
            is_final_quote=False,
        )

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        )

        self.assertNotIn("Reference evidence is available for internal review", reply)
        self.assertNotIn("Reference only: Unit reference: 12000000 VND / unit", reply)
        self.assertNotIn("12000000", reply)
        self.assertNotIn("approved quotation", reply.lower())
        self.assertIn("This is not a final quotation yet", reply)

    def test_sales_reply_never_renders_source_titles_or_urls(self) -> None:
        parsed = self.vietnamese_parsed_request()
        evidence = ReferenceEvidenceSummary(
            provider="tavily",
            evidence_label="reference_price_research",
            sources=(
                ReferenceEvidenceSourceSummary(
                    title="Supplier " + ("very long " * 80),
                    url="https://supplier.example/" + ("path/" * 120),
                ),
                ReferenceEvidenceSourceSummary(
                    title="Second source",
                    url="https://supplier.example/second",
                ),
                ReferenceEvidenceSourceSummary(
                    title="Third source should not render",
                    url="https://supplier.example/third",
                ),
            ),
            confidence=0.9,
        )

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        )

        self.assertNotIn("Second source", reply)
        self.assertNotIn("Third source should not render", reply)
        self.assertLessEqual(len(reply), 3900)

    def test_empty_evidence_does_not_reach_customer_reply(self) -> None:
        parsed = self.vietnamese_parsed_request()
        evidence = ReferenceEvidenceSummary(
            provider="tavily",
            evidence_label="reference_price_research",
            warnings=("No structured price metadata found.",),
            is_final_quote=False,
        )

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        )

        self.assertNotIn("đang chờ rà soát thủ công", reply)
        self.assertNotIn("Giá tham khảo:", reply)
        self.assertNotIn("No structured price metadata", reply)

    def test_low_confidence_evidence_never_reaches_customer(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None
        evidence = ReferenceEvidenceSummary(
            provider="tavily",
            evidence_label="reference_price_research",
            sources=(ReferenceEvidenceSourceSummary(title="Low confidence source"),),
            confidence=0.2,
            is_final_quote=False,
        )

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        )

        self.assertNotIn("pending manual pricing review", reply)
        self.assertNotIn("Low confidence (0.20)", reply)
        self.assertNotIn("Reference only:", reply)
        self.assertNotIn("Low confidence source", reply)

    def test_evidence_final_quote_flag_never_reaches_customer(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None
        evidence = ReferenceEvidenceSummary(
            provider="manual",
            evidence_label="reference_price_research",
            reference_prices=(
                ReferenceEvidencePriceSummary(
                    label="Approved final quote",
                    amount="12000000",
                    currency="VND",
                ),
            ),
            is_final_quote=True,
        )

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        ).lower()

        self.assertNotIn("requires internal review", reply)
        self.assertNotIn("approved final quote", reply)
        self.assertNotIn("12000000", reply)

    def test_technical_reply_ignores_evidence_and_remains_compatible(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None
        evidence = ReferenceEvidenceSummary(
            provider="tavily",
            evidence_label="reference_price_research",
            sources=(ReferenceEvidenceSourceSummary(title="Supplier source"),),
            confidence=0.8,
        )

        reply = telegram_workflow_reply(
            config=self.config(sales=False),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        )

        self.assertIn("Parsed: 50 x Standard business laptop", reply)
        self.assertNotIn("Supplier source", reply)
        self.assertNotIn("Reference evidence", reply)

    def test_sales_reference_evidence_redacts_secrets_and_raw_payloads(self) -> None:
        parsed = self.vietnamese_parsed_request()
        evidence = ReferenceEvidenceSummary(
            provider="tavily",
            evidence_label="reference_price_research",
            sources=(
                ReferenceEvidenceSourceSummary(
                    title="provider_payload raw_response secret token",
                    url="https://supplier.example/?api_key=secret",
                ),
            ),
            reference_prices=(
                ReferenceEvidencePriceSummary(
                    label="raw_prompt chain-of-thought",
                    amount="12000000",
                    currency="VND",
                ),
            ),
            warnings=("authorization bearer token raw_provider",),
            confidence=0.9,
        )

        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        ).lower()

        self.assertNotIn("provider_payload", reply)
        self.assertNotIn("raw_response", reply)
        self.assertNotIn("raw_prompt", reply)
        self.assertNotIn("api_key", reply)
        self.assertNotIn("authorization", reply)
        self.assertNotIn("bearer", reply)
        self.assertNotIn("chain-of-thought", reply)

    def test_sales_evidence_reply_does_not_attempt_network(self) -> None:
        parsed = self.vietnamese_parsed_request()
        evidence = ReferenceEvidenceSummary(
            provider="manual",
            evidence_label="reference_price_research",
            sources=(ReferenceEvidenceSourceSummary(title="Manual source"),),
            confidence=0.8,
        )

        with patch("urllib.request.urlopen") as urlopen:
            reply = telegram_workflow_reply(
                config=self.config(sales=True),
                parsed=parsed,
                workflow_id="workflow-123",
                status="WAITING_APPROVAL",
                auto_run=True,
                evidence=evidence,
            )

        urlopen.assert_not_called()
        self.assertNotIn("Manual source", reply)
        self.assertIn("Cảm ơn anh/chị", reply)

    def test_sales_run_failed_reply_hides_raw_backend_error_json(self) -> None:
        parsed = self.vietnamese_parsed_request()
        reply = telegram_run_failed_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow=WorkflowCreationResult("workflow-123", "CREATED"),
            error=ApiError('HTTP 500: {"traceback":"secret stack","detail":"raw"}'),
        )

        self.assertNotIn("workflow-123", reply)
        self.assertNotIn("http://localhost:3000/workflows/workflow-123", reply)
        self.assertNotIn("CREATED", reply)
        self.assertNotIn("traceback", reply)
        self.assertNotIn("HTTP 500", reply)
        self.assertNotIn('{"', reply)
        self.assertIn("Rất tiếc", reply)
        self.assertIn("hoàn tất báo giá", reply)

    def test_technical_run_failed_reply_keeps_error_detail(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None

        reply = telegram_run_failed_reply(
            config=self.config(),
            parsed=parsed,
            workflow=WorkflowCreationResult("workflow-123", "CREATED"),
            error=ApiError("HTTP 500: backend unavailable"),
        )

        self.assertIn("Run error: HTTP 500: backend unavailable", reply)

    def test_sales_greeting_reply_does_not_create_workflow(self) -> None:
        self.assertIsNone(parse_customer_request("xin chào"))
        reply = greeting_message(self.config(sales=True), "xin chào")

        self.assertIn("Em chào anh/chị", reply)
        self.assertIn("báo giá 50 laptop", reply)

    def test_sales_missing_quantity_reply_does_not_create_workflow(self) -> None:
        self.assertIsNone(parse_customer_request("tôi muốn mua laptop"))
        reply = follow_up_message(self.config(sales=True), "tôi muốn mua laptop")

        self.assertIn("Em cần thêm số lượng", reply)
        self.assertIn("báo giá 50 laptop", reply)

    def test_sales_unsupported_item_reply_does_not_create_workflow(self) -> None:
        self.assertIsNone(parse_customer_request("quote for 10 ergonomic chairs"))
        reply = follow_up_message(self.config(sales=True), "quote for 10 ergonomic chairs")

        self.assertIn("Please include quantity and item", reply)
        self.assertIn("standard business laptops", reply)

    def test_sales_replies_do_not_contain_forbidden_claims(self) -> None:
        parsed = self.vietnamese_parsed_request()
        evidence = ReferenceEvidenceSummary(
            provider="manual",
            evidence_label="reference_price_research",
            reference_prices=(
                ReferenceEvidencePriceSummary(
                    label="Unit reference",
                    amount="12000000",
                    currency="VND",
                    unit="unit",
                ),
            ),
            sources=(ReferenceEvidenceSourceSummary(title="Manual source"),),
            confidence=0.8,
        )
        reply = telegram_workflow_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow_id="workflow-123",
            status="WAITING_APPROVAL",
            auto_run=True,
            evidence=evidence,
        ).lower()

        forbidden = (
            "final quote",
            "final approved quote",
            "approved quote",
            "approved quotation",
            "in stock",
            "delivery date",
            "will deliver",
            "ships by",
            "email sent",
            "stock available",
            "discount approved",
        )
        for claim in forbidden:
            with self.subTest(claim=claim):
                self.assertNotIn(claim, reply)


class TelegramPostApprovalTests(unittest.TestCase):
    def config(self, *, sales: bool = True) -> BridgeConfig:
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
            sales_replies_enabled=sales,
            price_research_enabled=False,
            approval_poll_interval_seconds=3.0,
            final_quote_enabled=True,
        )

    def english_parsed(self) -> ParsedCustomerRequest:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None
        return parsed

    def laptop_20_parsed(self) -> ParsedCustomerRequest:
        parsed = parse_customer_request("báo giá cho tôi 20 laptop văn phòng tiêu chuẩn")
        assert parsed is not None
        return parsed

    def internal_laptop_knowledge_response(self) -> dict[str, Any]:
        return {
            "results": [
                {
                    "metadata": {
                        "normalized_item_name": "Office monitor",
                        "observed_price": "3200000",
                        "currency": "VND",
                        "quantity_basis": 1,
                        "price_label": "Internal demo catalog unit price",
                    }
                },
                {
                    "metadata": {
                        "normalized_item_name": "Standard business laptop",
                        "observed_price": "18500000",
                        "currency": "VND",
                        "quantity_basis": 1,
                        "price_label": "Internal demo catalog unit price",
                    }
                },
            ]
        }

    def test_format_final_price_keeps_trusted_precision(self) -> None:
        self.assertEqual(format_final_price(Decimal("952.56")), "952.56")
        self.assertEqual(format_final_price(Decimal("952")), "952")
        self.assertEqual(format_final_price(Decimal("0.5")), "0.50")
        self.assertEqual(format_final_price(Decimal("0")), "0")

    def test_format_vnd_groups_digits_and_preserves_fractional_value(self) -> None:
        self.assertEqual(format_vnd(Decimal("18500000")), "18.500.000 VND")
        self.assertEqual(format_vnd(Decimal("370000000")), "370.000.000 VND")
        self.assertEqual(format_vnd(Decimal("18500000.50")), "18.500.000,5 VND")

    def test_customer_product_name_localizes_only_for_presentation(self) -> None:
        self.assertEqual(
            customer_product_name("Standard business laptop", "vi"),
            "Laptop văn phòng tiêu chuẩn",
        )
        self.assertEqual(
            customer_product_name("Standard business laptop", "en"),
            "Standard business laptop",
        )

    def test_trusted_price_from_mapping_accepts_structured_price(self) -> None:
        price = trusted_price_from_mapping(
            {
                "unit_price": 952.56,
                "currency": "USD",
                "unit": "unit",
                "quantity_basis": 1,
            }
        )

        self.assertIsNotNone(price)
        assert price is not None
        self.assertEqual(price.unit_price, Decimal("952.56"))
        self.assertEqual(price.currency, "USD")
        self.assertEqual(price.unit, "unit")

    def test_trusted_price_from_mapping_never_accepts_prose_or_missing_currency(self) -> None:
        self.assertIsNone(
            trusted_price_from_mapping({"unit_price": "around twelve dollars"})
        )
        self.assertIsNone(
            trusted_price_from_mapping({"unit_price": 952.56})
        )
        self.assertIsNone(
            trusted_price_from_mapping({"unit_price": 952.56, "currency": "dollar"})
        )
        self.assertIsNone(
            trusted_price_from_mapping({"unit_price": -5, "currency": "USD"})
        )
        self.assertIsNone(
            trusted_price_from_mapping({"observed_price": None, "currency": "USD"})
        )

    def test_extract_trusted_price_from_knowledge_requires_structured_result(self) -> None:
        price = extract_trusted_price_from_knowledge(
            {
                "results": [
                    {
                        "chunk_index": 0,
                        "checksum": "abc",
                        "metadata": {
                            "embedding_provider": "demo",
                            "demo_reference_only": True,
                        },
                        "content": "The price is around 952 dollars per unit.",
                    }
                ]
            }
        )
        self.assertIsNone(price)

        price = extract_trusted_price_from_knowledge(
            {
                "results": [
                    {
                        "document_title": "Internal Demo Catalog - Office Monitor",
                        "metadata": {
                            "observed_price": "3200000",
                            "currency": "VND",
                            "unit": "unit",
                            "quantity_basis": 1,
                            "price_label": "Internal demo catalog unit price",
                        },
                    },
                ]
            }
        )
        self.assertIsNotNone(price)
        assert price is not None
        self.assertEqual(price.unit_price, Decimal("3200000"))
        self.assertEqual(price.currency, "VND")

        price = extract_trusted_price_from_knowledge(
            {
                "results": [
                    {
                        "metadata": {
                            "normalized_item_name": "Standard business laptop",
                            "observed_price": "18500000",
                            "currency": "VND",
                        },
                    },
                    {
                        "metadata": {
                            "normalized_item_name": "Office monitor",
                            "observed_price": "3200000",
                            "currency": "VND",
                        },
                    },
                ]
            },
            item_name="Office monitor",
        )
        self.assertIsNotNone(price)
        assert price is not None
        self.assertEqual(price.unit_price, Decimal("3200000"))

        price = extract_trusted_price_from_knowledge(
            {
                "results": [
                    {
                        "unit_price": 952.56,
                        "currency": "USD",
                        "unit": "unit",
                    }
                ]
            }
        )
        self.assertIsNotNone(price)
        assert price is not None
        self.assertEqual(price.unit_price, Decimal("952.56"))

    def test_telegram_final_quote_reply_includes_total_and_no_internal_ids(self) -> None:
        reply = telegram_final_quote_reply(
            self.config(),
            self.english_parsed(),
            TrustedFinalPrice(
                unit_price=Decimal("952.56"),
                currency="USD",
                unit="unit",
            ),
        )

        self.assertIn("📋 QUOTATION", reply)
        self.assertIn("• Standard business laptop", reply)
        self.assertIn("• Quantity: 50 unit", reply)
        self.assertIn("• Unit price: 952.56 USD per unit", reply)
        self.assertIn("• Total: 47628.00 USD", reply)
        self.assertIn("Reference configuration:", reply)
        self.assertIn("Suggested software:", reply)
        self.assertIn("Software license costs are excluded", reply)
        self.assertNotIn("workflow-123", reply)
        self.assertNotIn("WAITING_APPROVAL", reply)
        self.assertNotIn("http://", reply)
        self.assertNotIn("evidenc", reply.lower())

    def test_vietnamese_laptop_final_quote_is_customer_ready(self) -> None:
        parsed = self.laptop_20_parsed()
        assert parsed is not None
        reply = telegram_final_quote_reply(
            self.config(),
            parsed,
            TrustedFinalPrice(
                unit_price=Decimal("18500000"),
                currency="VND",
                unit="unit",
            ),
        )

        self.assertIn(
            "Yêu cầu của anh/chị đã được quản lý phê duyệt",
            reply,
        )
        self.assertIn("📋 BÁO GIÁ LAPTOP VĂN PHÒNG TIÊU CHUẨN", reply)
        self.assertIn("• Laptop văn phòng tiêu chuẩn", reply)
        self.assertIn("• Số lượng: 20 máy", reply)
        self.assertIn("Cấu hình tham khảo:", reply)
        self.assertIn("Phần mềm gợi ý:", reply)
        self.assertIn("• Đơn giá: 18.500.000 VND / máy", reply)
        self.assertIn("• Tổng cộng: 370.000.000 VND", reply)
        self.assertIn("Chi phí license phần mềm chưa bao gồm", reply)
        self.assertIn("thương hiệu/model sẽ được xác nhận", reply)
        self.assertNotIn("http://", reply)
        self.assertNotIn("workflow-123", reply)
        self.assertNotIn("WAITING_APPROVAL", reply)
        self.assertNotIn("RAG", reply)
        self.assertNotIn("Qdrant", reply)
        self.assertNotIn("Groq", reply)
        self.assertNotIn("Tavily", reply)

    def test_monitor_and_printer_quotes_use_natural_vietnamese_units(self) -> None:
        examples = (
            (
                "báo giá 30 màn hình văn phòng",
                Decimal("3200000"),
                "Màn hình văn phòng",
                "30 màn hình",
                "96.000.000 VND",
            ),
            (
                "báo giá 5 máy in văn phòng",
                Decimal("4500000"),
                "Máy in văn phòng",
                "5 máy",
                "22.500.000 VND",
            ),
        )
        for request, unit_price, product_name, quantity, total in examples:
            with self.subTest(request=request):
                parsed = parse_customer_request(request)
                assert parsed is not None
                reply = telegram_final_quote_reply(
                    self.config(),
                    parsed,
                    TrustedFinalPrice(
                        unit_price=unit_price,
                        currency="VND",
                        unit="unit",
                    ),
                )

                self.assertIn(f"• {product_name}", reply)
                self.assertIn(f"• Số lượng: {quantity}", reply)
                self.assertIn(f"• Tổng cộng: {total}", reply)
                self.assertNotIn("Cấu hình tham khảo:", reply)
                self.assertNotIn("Phần mềm gợi ý:", reply)

    def test_telegram_manual_final_quote_reply_is_safe_fallback(self) -> None:
        reply = telegram_manual_final_quote_reply(self.config(), self.english_parsed())

        self.assertIn("approved", reply)
        self.assertIn("operator", reply)
        self.assertNotIn("http://", reply)
        self.assertNotIn("workflow", reply.lower())

    def test_telegram_approval_rejected_reply_keeps_comment_but_no_ids(self) -> None:
        reply = telegram_approval_rejected_reply(
            self.config(),
            self.english_parsed(),
            "Not in approved policy",
        )

        self.assertIn("not approved", reply)
        self.assertIn("Not in approved policy", reply)
        self.assertNotIn("http://", reply)
        self.assertNotIn("workflow", reply.lower())

    def test_telegram_approval_changes_requested_reply_keeps_comment(self) -> None:
        reply = telegram_approval_changes_requested_reply(
            self.config(),
            self.english_parsed(),
            "Need quantity and delivery location",
        )

        self.assertIn("needs more information", reply)
        self.assertIn("Need quantity and delivery location", reply)
        self.assertNotIn("http://", reply)

    def test_latest_approval_decision_normalizes_approve_reject_request_changes(self) -> None:
        with patch(
            "scripts.demo.telegram_inbound_bridge.fetch_approval_history",
            return_value={
                "approvals": [
                    {"decision": "request_changes", "comment": "add PO number"},
                    {"decision": "approve", "comment": "Approved by manager"},
                ]
            },
        ):
            decision, comment = latest_approval_decision(
                self.config(), "token", "workflow-1"
            )
        self.assertEqual(decision, "approve")
        self.assertEqual(comment, "Approved by manager")

        with patch(
            "scripts.demo.telegram_inbound_bridge.fetch_approval_history",
            return_value={
                "approvals": [
                    {"decision": "reject", "comment": "Out of budget"}
                ]
            },
        ):
            decision, comment = latest_approval_decision(
                self.config(), "token", "workflow-1"
            )
        self.assertEqual(decision, "reject")
        self.assertEqual(comment, "Out of budget")

    def test_latest_approval_decision_unknown_decision_is_never_approve(self) -> None:
        with patch(
            "scripts.demo.telegram_inbound_bridge.fetch_approval_history",
            return_value={
                "approvals": [
                    {"decision": "mystery_action", "comment": None}
                ]
            },
        ):
            decision, comment = latest_approval_decision(
                self.config(), "token", "workflow-1"
            )
        self.assertEqual(decision, "request_changes")
        self.assertIsNone(comment)

    def test_latest_approval_decision_empty_history_is_none(self) -> None:
        with patch(
            "scripts.demo.telegram_inbound_bridge.fetch_approval_history",
            return_value={"approvals": []},
        ):
            decision, comment = latest_approval_decision(
                self.config(), "token", "workflow-1"
            )
        self.assertIsNone(decision)
        self.assertIsNone(comment)

    def test_register_pending_quote_only_when_final_quote_enabled(self) -> None:
        pending: dict[str, TelegramPendingQuote] = {}
        workflow = WorkflowCreationResult("workflow-123", "WAITING_APPROVAL")
        parsed = self.english_parsed()

        register_pending_quote(
            pending,
            self.config(),
            "chat-1",
            workflow,
            parsed,
        )
        self.assertIn("chat-1", pending)
        self.assertEqual(pending["chat-1"].workflow_id, "workflow-123")
        self.assertFalse(pending["chat-1"].resumed)

        disabled = replace(self.config(), final_quote_enabled=False)
        register_pending_quote(
            pending,
            disabled,
            "chat-2",
            workflow,
            parsed,
        )
        self.assertNotIn("chat-2", pending)

    def test_process_pending_approvals_approve_resumes_and_sends_final_quote(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.english_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []

        def fake_reply(config: BridgeConfig, chat_id: str, text: str) -> None:
            replies.append(text)

        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("approve", "Approved"),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
            side_effect=[
                {"workflow": {"status": "APPROVED"}},
                {"workflow": {"status": "COMPLETED"}},
            ],
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            return_value="QUOTED",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.extract_trusted_price_from_workflow",
            return_value=TrustedFinalPrice(
                unit_price=Decimal("952.56"),
                currency="USD",
                unit="unit",
            ),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=fake_reply,
        ):
            process_pending_approvals(self.config(), pending)

        self.assertEqual(len(replies), 1)
        self.assertIn("• Standard business laptop", replies[0])
        self.assertIn("• Total: 47628.00 USD", replies[0])
        self.assertNotIn("chat-1", pending)

    def test_process_pending_approvals_approve_without_price_falls_back(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.english_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []

        def fake_reply(config: BridgeConfig, chat_id: str, text: str) -> None:
            replies.append(text)

        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("approve", None),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
            side_effect=[
                {"workflow": {"status": "APPROVED"}},
                {"workflow": {"status": "COMPLETED"}},
            ],
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            return_value="QUOTED",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.extract_trusted_price_from_workflow",
            return_value=None,
        ), patch(
            "scripts.demo.telegram_inbound_bridge.knowledge_pricing_search",
            return_value={"results": []},
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=fake_reply,
        ):
            process_pending_approvals(self.config(), pending)

        self.assertEqual(len(replies), 1)
        self.assertIn("does not yet have a trusted final price", replies[0])
        self.assertNotIn("chat-1", pending)

    def test_process_pending_approvals_selects_matching_internal_laptop_price(self) -> None:
        parsed = parse_customer_request("báo giá cho tôi 10 laptop văn phòng tiêu chuẩn")
        assert parsed is not None
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=parsed,
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []

        def fake_reply(config: BridgeConfig, chat_id: str, text: str) -> None:
            replies.append(text)

        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("approve", None),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
            side_effect=[
                {"workflow": {"status": "APPROVED"}},
                {"workflow": {"status": "COMPLETED"}},
            ],
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            return_value="COMPLETED",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.extract_trusted_price_from_workflow",
            return_value=None,
        ), patch(
            "scripts.demo.telegram_inbound_bridge.knowledge_pricing_search",
            return_value={
                "results": [
                    {
                        "metadata": {
                            "normalized_item_name": "Office monitor",
                            "observed_price": "3200000",
                            "currency": "VND",
                            "quantity_basis": 1,
                            "price_label": "Internal demo catalog unit price",
                        }
                    },
                    {
                        "metadata": {
                            "normalized_item_name": "Office printer",
                            "observed_price": "4500000",
                            "currency": "VND",
                            "quantity_basis": 1,
                            "price_label": "Internal demo catalog unit price",
                        }
                    },
                    {
                        "metadata": {
                            "normalized_item_name": "Standard business laptop",
                            "observed_price": "18500000",
                            "currency": "VND",
                            "quantity_basis": 1,
                            "price_label": "Internal demo catalog unit price",
                        }
                    },
                ]
            },
        ) as knowledge_search, patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=fake_reply,
        ):
            process_pending_approvals(self.config(), pending)

        self.assertEqual(len(replies), 1)
        self.assertIn("• Đơn giá: 18.500.000 VND / máy", replies[0])
        self.assertIn("• Tổng cộng: 185.000.000 VND", replies[0])
        knowledge_search.assert_called_once()
        self.assertNotIn("chat-1", pending)

    def test_process_pending_approvals_reject_never_resumes(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.english_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []

        def fake_reply(config: BridgeConfig, chat_id: str, text: str) -> None:
            replies.append(text)

        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("reject", "Out of budget"),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            side_effect=AssertionError("resume must not be called on reject"),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=fake_reply,
        ):
            process_pending_approvals(self.config(), pending)

        self.assertEqual(len(replies), 1)
        self.assertIn("not approved", replies[0])
        self.assertNotIn("chat-1", pending)

    def test_completed_before_bridge_resume_skips_resume_and_quotes(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.laptop_20_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []
        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("approve", None),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
            return_value={"workflow": {"status": "COMPLETED"}},
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
        ) as resume, patch(
            "scripts.demo.telegram_inbound_bridge.extract_trusted_price_from_workflow",
            return_value=None,
        ), patch(
            "scripts.demo.telegram_inbound_bridge.knowledge_pricing_search",
            return_value=self.internal_laptop_knowledge_response(),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=lambda _config, _chat_id, text: replies.append(text),
        ):
            process_pending_approvals(self.config(), pending)

        resume.assert_not_called()
        self.assertIn("• Đơn giá: 18.500.000 VND / máy", replies[0])
        self.assertIn("• Tổng cộng: 370.000.000 VND", replies[0])
        self.assertNotIn("chat-1", pending)

    def test_completed_resume_conflict_is_treated_as_race_success(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.laptop_20_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []
        race_error = ApiError(
            'HTTP 409: {"detail":{"code":"workflow_resume_not_allowed",'
            '"message":"Workflow resume requires APPROVED, got COMPLETED."}}'
        )
        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("approve", None),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
            side_effect=[
                {"workflow": {"status": "APPROVED"}},
                {"workflow": {"status": "COMPLETED"}},
            ],
        ) as fetch_state, patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            side_effect=race_error,
        ) as resume, patch(
            "scripts.demo.telegram_inbound_bridge.extract_trusted_price_from_workflow",
            return_value=None,
        ), patch(
            "scripts.demo.telegram_inbound_bridge.knowledge_pricing_search",
            return_value=self.internal_laptop_knowledge_response(),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=lambda _config, _chat_id, text: replies.append(text),
        ):
            process_pending_approvals(self.config(), pending)

        resume.assert_called_once()
        self.assertEqual(fetch_state.call_count, 2)
        self.assertIn("• Tổng cộng: 370.000.000 VND", replies[0])
        self.assertNotIn("Resume failed", replies[0])
        self.assertNotIn("chat-1", pending)

    def test_completed_resume_conflict_without_completed_refresh_fails_safe(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.laptop_20_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []
        race_error = ApiError(
            'HTTP 409: {"detail":{"code":"workflow_resume_not_allowed",'
            '"message":"Workflow resume requires APPROVED, got WAITING_APPROVAL."}}'
        )
        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("approve", None),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
            side_effect=[
                {"workflow": {"status": "APPROVED"}},
                {"workflow": {"status": "APPROVED"}},
            ],
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            side_effect=race_error,
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=lambda _config, _chat_id, text: replies.append(text),
        ):
            process_pending_approvals(self.config(), pending)

        self.assertEqual(len(replies), 1)
        self.assertIn("mức giá chính thức đủ tin cậy", replies[0])
        self.assertNotIn("chat-1", pending)

    def test_unrelated_resume_conflict_is_not_swallowed(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.laptop_20_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []
        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("approve", None),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
            return_value={"workflow": {"status": "APPROVED"}},
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            side_effect=ApiError(
                'HTTP 409: {"detail":{"code":"approval_conflict",'
                '"message":"another approval conflict"}}'
            ),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=lambda _config, _chat_id, text: replies.append(text),
        ):
            process_pending_approvals(self.config(), pending)

        self.assertEqual(len(replies), 1)
        self.assertIn("mức giá chính thức đủ tin cậy", replies[0])
        self.assertNotIn("chat-1", pending)

    def test_completed_without_persisted_approval_does_not_quote(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.laptop_20_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=(None, None),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
        ) as fetch_state, patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
        ) as send_reply:
            process_pending_approvals(self.config(), pending)

        fetch_state.assert_not_called()
        send_reply.assert_not_called()
        self.assertIn("chat-1", pending)

    def test_process_pending_approvals_request_changes_never_resumes(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.english_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []

        def fake_reply(config: BridgeConfig, chat_id: str, text: str) -> None:
            replies.append(text)

        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("request_changes", "Add PO number"),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            side_effect=AssertionError("resume must not be called on request_changes"),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=fake_reply,
        ):
            process_pending_approvals(self.config(), pending)

        self.assertEqual(len(replies), 1)
        self.assertIn("needs more information", replies[0])
        self.assertNotIn("chat-1", pending)

    def test_process_pending_approvals_resume_failure_sends_safe_fallback(self) -> None:
        pending = {
            "chat-1": TelegramPendingQuote(
                workflow_id="workflow-123",
                parsed=self.english_parsed(),
                created_status="WAITING_APPROVAL",
            )
        }
        replies: list[str] = []

        def fake_reply(config: BridgeConfig, chat_id: str, text: str) -> None:
            replies.append(text)

        with patch(
            "scripts.demo.telegram_inbound_bridge.backend_login",
            return_value="token",
        ), patch(
            "scripts.demo.telegram_inbound_bridge.latest_approval_decision",
            return_value=("approve", None),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.fetch_workflow_state",
            return_value={"workflow": {"status": "APPROVED"}},
        ), patch(
            "scripts.demo.telegram_inbound_bridge.resume_approved_workflow",
            side_effect=ApiError("backend unavailable"),
        ), patch(
            "scripts.demo.telegram_inbound_bridge.send_or_log_reply",
            side_effect=fake_reply,
        ):
            process_pending_approvals(self.config(), pending)

        self.assertEqual(len(replies), 1)
        self.assertIn("operator", replies[0])
        self.assertNotIn("chat-1", pending)


class TelegramReferenceEvidenceTests(unittest.TestCase):
    def config(self, *, sales: bool = False) -> BridgeConfig:
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
            sales_replies_enabled=sales,
            price_research_enabled=True,
        )

    def provider_independent_result(self) -> SimpleNamespace:
        return SimpleNamespace(
            provider="reference_provider",
            evidence_label="reference_price_research",
            retrieved_at="2026-08-11T08:00:00Z",
            confidence=0.85,
            is_final_quote=False,
            reference_prices=(
                SimpleNamespace(
                    label="Market reference",
                    amount="12000000",
                    currency="VND",
                    unit="unit",
                ),
                SimpleNamespace(
                    label="Vendor reference",
                    amount=Decimal("12000000"),
                    currency="VND",
                    unit="unit",
                ),
                SimpleNamespace(
                    label="Third reference",
                    amount="11000000",
                    currency="VND",
                    unit="unit",
                ),
            ),
            sources=(
                SimpleNamespace(
                    title="Public supplier page",
                    url="https://supplier.example/prices",
                ),
                SimpleNamespace(
                    title="Internal notes",
                    url="file:///etc/shadow",
                ),
                SimpleNamespace(
                    title="Leak",
                    url="https://supplier.example/?api_key=secret",
                ),
                SimpleNamespace(
                    title="Snippet holder",
                    url="https://supplier.example/",
                    snippet="raw_response secret provider_payload chain_of_thought",
                ),
            ),
            warnings=("rate limited once",),
        )

    def test_mapper_builds_bounded_summary_from_provider_independent_result(self) -> None:
        mapped = reference_evidence_from_price_research_result(
            self.provider_independent_result()
        )

        self.assertIsNotNone(mapped)
        assert mapped is not None
        self.assertEqual(mapped.provider, "reference_provider")
        self.assertEqual(mapped.evidence_label, "reference_price_research")
        self.assertEqual(mapped.retrieved_at, "2026-08-11T08:00:00Z")
        self.assertEqual(mapped.confidence, 0.85)
        self.assertFalse(mapped.is_final_quote)
        self.assertEqual(mapped.warnings, ("rate limited once",))
        self.assertEqual(len(mapped.reference_prices), 2)
        self.assertEqual(len(mapped.sources), 2)
        self.assertEqual(mapped.reference_prices[0].amount, "12000000")
        self.assertEqual(mapped.reference_prices[1].amount, "12000000")

    def test_mapper_never_echoes_raw_snippets(self) -> None:
        mapped = reference_evidence_from_price_research_result(
            self.provider_independent_result()
        )

        self.assertIsNotNone(mapped)
        assert mapped is not None
        rendered = str(mapped)
        for marker in ("raw_response", "secret", "provider_payload", "chain_of_thought"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, rendered)
        self.assertIsNone(
            next((s.url for s in mapped.sources if s.title == "Leak"), None)
        )
        self.assertIsNone(
            next((s.url for s in mapped.sources if s.title == "Internal notes"), None)
        )

    def test_mapper_drops_non_http_urls_and_sensitive_urls(self) -> None:
        mapped = reference_evidence_from_price_research_result(
            self.provider_independent_result()
        )

        self.assertIsNotNone(mapped)
        assert mapped is not None
        urls = [source.url for source in mapped.sources]
        self.assertIn("https://supplier.example/prices", urls)
        self.assertNotIn("file:///etc/shadow", urls)
        self.assertNotIn("https://supplier.example/?api_key=secret", urls)

    def test_mapper_ignores_prose_amounts(self) -> None:
        result = self.provider_independent_result()
        result.reference_prices = (
            SimpleNamespace(
                label="Prose price",
                amount="around twelve million VND",
                currency="VND",
                unit="unit",
            ),
        )

        mapped = reference_evidence_from_price_research_result(result)

        self.assertIsNotNone(mapped)
        assert mapped is not None
        self.assertEqual(len(mapped.reference_prices), 1)
        self.assertIsNone(mapped.reference_prices[0].amount)

    def test_mapper_returns_none_for_none(self) -> None:
        self.assertIsNone(reference_evidence_from_price_research_result(None))

    def test_mapper_accepts_dict_shaped_contract(self) -> None:
        result = {
            "provider": "tavily",
            "evidence_label": "reference_price_research",
            "retrieved_at": "2026-08-11T08:00:00Z",
            "confidence": 0.75,
            "is_final_quote": False,
            "warnings": [],
            "reference_prices": [
                {
                    "label": "Market reference",
                    "amount": "12000000",
                    "currency": "VND",
                    "unit": "unit",
                },
                {
                    "label": "Vendor reference",
                    "amount": "11500000",
                    "currency": "VND",
                    "unit": "unit",
                },
            ],
            "sources": [
                {
                    "title": "Public supplier page",
                    "url": "https://supplier.example/prices",
                },
                {
                    "title": "Leak",
                    "url": "https://supplier.example/?api_key=secret",
                },
            ],
        }

        mapped = reference_evidence_from_price_research_result(result)

        self.assertIsNotNone(mapped)
        assert mapped is not None
        self.assertEqual(mapped.provider, "tavily")
        self.assertEqual(mapped.confidence, 0.75)
        self.assertEqual(len(mapped.reference_prices), 2)
        self.assertEqual(mapped.reference_prices[1].amount, "11500000")
        self.assertEqual(len(mapped.sources), 2)
        self.assertIsNone(mapped.sources[1].url)

    def test_evidence_disabled_does_not_call_provider(self) -> None:
        called = []

        def provider(parsed: Any, config: BridgeConfig) -> Any:
            called.append(parsed)
            return None

        config = replace(self.config(sales=True), price_research_enabled=False)
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None

        evidence = reference_evidence_for_request(
            config,
            parsed,
            evidence_provider=provider,
        )

        self.assertIsNone(evidence)
        self.assertEqual(called, [])

    def test_evidence_provider_raises_degrades_to_none(self) -> None:
        def provider(parsed: Any, config: BridgeConfig) -> Any:
            raise RuntimeError("provider exploded")

        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None

        evidence = reference_evidence_for_request(
            self.config(sales=True),
            parsed,
            evidence_provider=provider,
        )

        self.assertIsNone(evidence)

    def test_evidence_provider_returning_wrong_type_degrades_to_none(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None

        evidence = reference_evidence_for_request(
            self.config(sales=True),
            parsed,
            evidence_provider=lambda parsed, config: {"not": "evidence"},
        )

        self.assertIsNone(evidence)

    def test_config_price_research_enabled_from_environment(self) -> None:
        with patch.dict(
            os.environ,
            {"PRICE_RESEARCH_ENABLED": "true"},
            clear=False,
        ):
            config = config_from_env(
                SimpleNamespace(
                    allowed_chat_id=None,
                    dry_run=True,
                    once=True,
                    auto_run=True,
                    llm_extraction=None,
                    sales_replies=None,
                )
            )
        self.assertTrue(config.price_research_enabled)

        with patch.dict(
            os.environ,
            {"PRICE_RESEARCH_ENABLED": "false"},
            clear=False,
        ):
            config = config_from_env(
                SimpleNamespace(
                    allowed_chat_id=None,
                    dry_run=True,
                    once=True,
                    auto_run=True,
                    llm_extraction=None,
                    sales_replies=None,
                )
            )
        self.assertFalse(config.price_research_enabled)

    def test_handle_update_wires_evidence_into_dry_run_log(self) -> None:
        parsed = parse_customer_request("quote for 50 standard business laptops")
        assert parsed is not None
        expected = ReferenceEvidenceSummary(
            provider="reference_provider",
            evidence_label="reference_price_research",
            reference_prices=(
                ReferenceEvidencePriceSummary(
                    label="Market reference",
                    amount="12000000",
                    currency="VND",
                    unit="unit",
                ),
            ),
            sources=(ReferenceEvidenceSourceSummary(title="Public supplier page"),),
            confidence=0.8,
        )

        def provider(parsed: Any, config: BridgeConfig) -> ReferenceEvidenceSummary:
            return expected

        update = {
            "message": {
                "chat": {"id": 12345},
                "message_id": 42,
                "from": {"first_name": "Test"},
                "text": "quote for 50 standard business laptops",
            }
        }
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            handle_update(
                self.config(sales=True),
                update,
                evidence_provider=provider,
            )

        log = json.loads(buffer.getvalue())
        self.assertIn("reference_evidence", log)
        self.assertIsNotNone(log["reference_evidence"])
        self.assertEqual(
            log["reference_evidence"]["provider"],
            "reference_provider",
        )
        self.assertEqual(
            log["reference_evidence"]["reference_prices"][0]["amount"],
            "12000000",
        )

    def test_safe_evidence_url_accepts_only_http_and_https(self) -> None:
        self.assertEqual(
            safe_evidence_url("https://supplier.example/prices"),
            "https://supplier.example/prices",
        )
        self.assertEqual(
            safe_evidence_url("http://supplier.example/prices"),
            "http://supplier.example/prices",
        )
        self.assertIsNone(safe_evidence_url("file:///etc/shadow"))
        self.assertIsNone(safe_evidence_url("ftp://supplier.example/prices"))
        self.assertIsNone(safe_evidence_url("javascript:alert(1)"))
        self.assertIsNone(safe_evidence_url("https://supplier.example/?api_key=secret"))


if __name__ == "__main__":
    unittest.main()
