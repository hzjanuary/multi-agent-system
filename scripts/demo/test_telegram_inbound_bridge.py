import unittest

from scripts.demo.telegram_inbound_bridge import (
    BridgeConfig,
    EXAMPLE_MESSAGE,
    build_workflow_create_payload,
    is_greeting_message,
    parse_customer_request,
    sender_display_name,
    telegram_workflow_reply,
)


class TelegramInboundBridgeParserTests(unittest.TestCase):
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
            "telegram-demo-parser-v2",
        )
        self.assertEqual(
            payload["metadata"]["attributes"]["telegram_chat_id"],
            "12345",
        )
        self.assertEqual(
            payload["metadata"]["attributes"]["telegram_message_id"],
            "67890",
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


if __name__ == "__main__":
    unittest.main()
