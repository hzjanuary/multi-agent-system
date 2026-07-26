import unittest
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
    UnsupportedMixedRequest,
    WorkflowCreationResult,
    build_workflow_create_payload,
    config_from_env,
    extract_customer_request,
    follow_up_message,
    greeting_message,
    is_greeting_message,
    parse_args,
    parse_llm_extraction_result,
    parse_customer_request,
    sender_display_name,
    telegram_run_failed_reply,
    telegram_workflow_reply,
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
        self.assertIn("workflow-123", reply)
        self.assertIn("WAITING_APPROVAL", reply)
        self.assertIn("http://localhost:3000/workflows/workflow-123", reply)
        self.assertIn(
            "http://localhost:3000/agent-monitor?workflowId=workflow-123",
            reply,
        )
        self.assertIn("Đây chưa phải báo giá cuối cùng", reply)

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
        self.assertIn("WAITING_APPROVAL", reply)

    def test_sales_reply_with_evidence_mentions_reference_evidence_only(self) -> None:
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

        self.assertIn("Tham khảo giá nội bộ", reply)
        self.assertIn("provider: tavily", reply)
        self.assertIn("sources: 1", reply)
        self.assertIn("confidence 0.72", reply)
        self.assertIn("Supplier reference listing", reply)
        self.assertIn("https://supplier.example/laptops", reply)
        self.assertIn("không phải báo giá cuối cùng", reply)

    def test_sales_reply_with_reference_price_labels_amount_as_reference(self) -> None:
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

        self.assertIn("Reference evidence is available for internal review", reply)
        self.assertIn("Reference only: Unit reference: 12000000 VND / unit", reply)
        self.assertIn("not final quotation", reply)
        self.assertNotIn("approved quotation", reply.lower())

    def test_sales_reply_bounds_source_titles_and_urls(self) -> None:
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

        self.assertIn("Second source", reply)
        self.assertNotIn("Third source should not render", reply)
        self.assertLessEqual(len(reply), 3900)

    def test_empty_evidence_produces_manual_review_wording(self) -> None:
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

        self.assertIn("đang chờ rà soát thủ công", reply)
        self.assertNotIn("Giá tham khảo:", reply)

    def test_low_confidence_evidence_produces_caution_wording(self) -> None:
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

        self.assertIn("pending manual pricing review", reply)
        self.assertIn("Low confidence (0.20)", reply)
        self.assertNotIn("Reference only:", reply)

    def test_evidence_marked_final_quote_is_downgraded(self) -> None:
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

        self.assertIn("requires internal review", reply)
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
        self.assertIn("Manual source", reply)

    def test_sales_run_failed_reply_hides_raw_backend_error_json(self) -> None:
        parsed = self.vietnamese_parsed_request()
        reply = telegram_run_failed_reply(
            config=self.config(sales=True),
            parsed=parsed,
            workflow=WorkflowCreationResult("workflow-123", "CREATED"),
            error=ApiError('HTTP 500: {"traceback":"secret stack","detail":"raw"}'),
        )

        self.assertIn("workflow-123", reply)
        self.assertIn("http://localhost:3000/workflows/workflow-123", reply)
        self.assertIn("chưa hoàn tất", reply)
        self.assertNotIn("traceback", reply)
        self.assertNotIn("HTTP 500", reply)
        self.assertNotIn('{"', reply)

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


if __name__ == "__main__":
    unittest.main()
