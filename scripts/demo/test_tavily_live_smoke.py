from __future__ import annotations

import contextlib
import io
import json
import os
import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from scripts.demo import tavily_live_smoke


class TavilyLiveSmokeTests(unittest.TestCase):
    def test_missing_confirmation_refuses_live_run(self) -> None:
        calls: list[tavily_live_smoke.SmokeRequest] = []

        async def runner(
            config: tavily_live_smoke.LiveSmokeConfig,
            request: tavily_live_smoke.SmokeRequest,
        ) -> dict[str, object]:
            calls.append(request)
            return sample_result(request)

        exit_code, output = run_main(
            [
                "--provider",
                "tavily",
                "--item",
                "Standard business laptop",
            ],
            provider_runner=runner,
            env={"TAVILY_API_KEY": "tvly-secret-key"},
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(calls, [])
        self.assertEqual(output["error_code"], "missing_confirmation")
        self.assertNotIn("tvly-secret-key", json.dumps(output))

    def test_missing_tavily_key_refuses_live_run_safely(self) -> None:
        exit_code, output = run_main(
            [
                "--provider",
                "tavily",
                "--item",
                "Standard business laptop",
                "--confirm-live-provider",
            ],
            env={"TAVILY_API_KEY": ""},
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output["error_code"], "missing_api_key")
        self.assertIn("Tavily provider key", output["message"])

    def test_dry_run_requires_no_key_and_does_not_call_provider(self) -> None:
        calls: list[tavily_live_smoke.SmokeRequest] = []

        async def runner(
            config: tavily_live_smoke.LiveSmokeConfig,
            request: tavily_live_smoke.SmokeRequest,
        ) -> dict[str, object]:
            calls.append(request)
            return sample_result(request)

        exit_code, output = run_main(
            [
                "--provider",
                "tavily",
                "--item",
                "Standard business laptop",
                "--region",
                "VN",
                "--currency",
                "VND",
                "--dry-run",
            ],
            provider_runner=runner,
            env={"TAVILY_API_KEY": ""},
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls, [])
        self.assertTrue(output["dry_run"])
        self.assertFalse(output["provider_call"])
        self.assertEqual(output["request"]["normalized_item_name"], "Standard business laptop")

    def test_successful_mocked_provider_output_is_bounded_json(self) -> None:
        async def runner(
            config: tavily_live_smoke.LiveSmokeConfig,
            request: tavily_live_smoke.SmokeRequest,
        ) -> dict[str, object]:
            return sample_result(request)

        exit_code, output = run_main(
            [
                "--provider",
                "tavily",
                "--item",
                "Standard business laptop",
                "--requested-addon",
                "office_365",
                "--confirm-live-provider",
            ],
            provider_runner=runner,
            env={"TAVILY_API_KEY": "tvly-secret-key"},
        )

        output_text = json.dumps(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(output["status"], "ok")
        self.assertTrue(output["provider_call"])
        self.assertFalse(output["result"]["is_final_quote"])
        self.assertEqual(output["result"]["provider"], "tavily")
        self.assertEqual(output["result"]["sources"][0]["source_type"], "external_web")
        self.assertEqual(output["result"]["reference_prices"][0]["amount"], "12000000")
        self.assertNotIn("tvly-secret-key", output_text)
        self.assertNotIn("Authorization", output_text)
        self.assertNotIn("raw provider payload", output_text)
        self.assertNotIn("<strong>", output_text)

    def test_redacts_sensitive_output_values(self) -> None:
        async def runner(
            config: tavily_live_smoke.LiveSmokeConfig,
            request: tavily_live_smoke.SmokeRequest,
        ) -> dict[str, object]:
            return {
                "item_name": request.item_name,
                "normalized_item_name": request.normalized_item_name,
                "quantity": request.quantity,
                "region": request.region,
                "currency": request.currency,
                "reference_prices": [
                    {
                        "label": "authorization bearer token",
                        "amount": "12000000",
                        "currency": "VND",
                    },
                ],
                "sources": [
                    {
                        "title": "provider_payload secret",
                        "url": "https://example.test/?api_key=secret",
                        "snippet": "<strong>safe html removed</strong>",
                        "source_type": "external_web",
                        "confidence": 0.5,
                    },
                ],
                "confidence": 0.5,
                "retrieved_at": datetime(2026, 7, 26, tzinfo=UTC).isoformat(),
                "warnings": ["raw_provider secret token"],
                "provider": "tavily",
            }

        exit_code, output = run_main(
            [
                "--provider",
                "tavily",
                "--item",
                "Standard business laptop",
                "--confirm-live-provider",
            ],
            provider_runner=runner,
            env={"TAVILY_API_KEY": "tvly-secret-key"},
        )

        output_text = json.dumps(output).lower()
        self.assertEqual(exit_code, 0)
        self.assertIn("[redacted]", output_text)
        self.assertNotIn("api_key", output_text)
        self.assertNotIn("secret", output_text)
        self.assertNotIn("authorization", output_text)
        self.assertNotIn("bearer", output_text)
        self.assertNotIn("raw_provider", output_text)
        self.assertNotIn("tvly-secret-key", output_text)
        self.assertNotIn("<strong>", output_text)

    def test_unsupported_provider_exits_nonzero(self) -> None:
        exit_code, output = run_main(
            ["--provider", "unknown", "--item", "Standard business laptop", "--dry-run"],
            env={"TAVILY_API_KEY": ""},
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(output["error_code"], "unsupported_provider")

    def test_provider_error_prints_safe_message_only(self) -> None:
        async def runner(
            config: tavily_live_smoke.LiveSmokeConfig,
            request: tavily_live_smoke.SmokeRequest,
        ) -> dict[str, object]:
            raise RuntimeError("provider failed with token secret")

        exit_code, output = run_main(
            [
                "--provider",
                "tavily",
                "--item",
                "Standard business laptop",
                "--confirm-live-provider",
            ],
            provider_runner=runner,
            env={"TAVILY_API_KEY": "tvly-secret-key"},
        )

        output_text = json.dumps(output).lower()
        self.assertEqual(exit_code, 1)
        self.assertEqual(output["error_code"], "provider_error")
        self.assertIn("[redacted]", output_text)
        self.assertNotIn("token", output_text)
        self.assertNotIn("secret", output_text)
        self.assertNotIn("tvly-secret-key", output_text)

    def test_provider_timeout_prints_safe_message_only(self) -> None:
        async def runner(
            config: tavily_live_smoke.LiveSmokeConfig,
            request: tavily_live_smoke.SmokeRequest,
        ) -> dict[str, object]:
            raise TimeoutError("timeout with token secret")

        exit_code, output = run_main(
            [
                "--provider",
                "tavily",
                "--item",
                "Standard business laptop",
                "--confirm-live-provider",
            ],
            provider_runner=runner,
            env={"TAVILY_API_KEY": "tvly-secret-key"},
        )

        output_text = json.dumps(output).lower()
        self.assertEqual(exit_code, 1)
        self.assertEqual(output["error_code"], "provider_timeout")
        self.assertNotIn("token", output_text)
        self.assertNotIn("secret", output_text)
        self.assertNotIn("tvly-secret-key", output_text)

    def test_forbidden_claims_are_absent_from_success_output(self) -> None:
        async def runner(
            config: tavily_live_smoke.LiveSmokeConfig,
            request: tavily_live_smoke.SmokeRequest,
        ) -> dict[str, object]:
            return sample_result(request)

        exit_code, output = run_main(
            [
                "--provider",
                "tavily",
                "--item",
                "Standard business laptop",
                "--confirm-live-provider",
            ],
            provider_runner=runner,
            env={"TAVILY_API_KEY": "tvly-secret-key"},
        )

        self.assertEqual(exit_code, 0)
        text = json.dumps(output).lower()
        forbidden = (
            "final quote",
            "approved quote",
            "approved quotation",
            "in stock",
            "stock available",
            "delivery date",
            "will deliver",
            "discount approved",
            "email sent",
        )
        for claim in forbidden:
            self.assertNotIn(claim, text)


def run_main(
    argv: list[str],
    *,
    provider_runner: tavily_live_smoke.ProviderRunner | None = None,
    env: dict[str, str],
) -> tuple[int, dict[str, object]]:
    stdout = io.StringIO()
    with patch.dict(os.environ, env, clear=False), contextlib.redirect_stdout(stdout):
        exit_code = tavily_live_smoke.main(argv, provider_runner=provider_runner)
    return exit_code, json.loads(stdout.getvalue())


def sample_result(request: tavily_live_smoke.SmokeRequest) -> dict[str, object]:
    return {
        "item_name": request.item_name,
        "normalized_item_name": request.normalized_item_name,
        "quantity": request.quantity,
        "region": request.region,
        "currency": request.currency,
        "reference_prices": [
            {
                "label": "Manual reference amount",
                "amount": "12000000",
                "currency": "VND",
                "unit": "unit",
                "quantity_basis": 1,
            },
        ],
        "sources": [
            {
                "title": "Supplier reference listing",
                "url": "https://supplier.example/laptops",
                "snippet": "<strong>Reference evidence for internal review.</strong>",
                "source_type": "external_web",
                "confidence": 0.74,
            },
        ],
        "confidence": 0.74,
        "retrieved_at": datetime(2026, 7, 26, tzinfo=UTC).isoformat(),
        "warnings": ["External web evidence is reference material."],
        "provider": "tavily",
        "is_final_quote": False,
        "evidence_label": "reference_price_research",
    }


if __name__ == "__main__":
    unittest.main()
