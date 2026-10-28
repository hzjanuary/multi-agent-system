import json
import unittest
from scripts.ops.openrouter_quota import sanitize


class QuotaTests(unittest.TestCase):
    def test_missing_null_and_zero_are_distinct(self):
        result = sanitize(
            {
                "data": {
                    "limit": None,
                    "usage": 0,
                    "free_model_daily_requests": {
                        "used": 50,
                        "limit": 50,
                        "remaining": 0,
                    },
                    "budgets": [],
                    "effective_budget": None,
                }
            }
        )
        self.assertIsNone(result["quota"]["limit"])
        self.assertEqual(result["quota"]["usage"], 0)
        self.assertIn("limit_remaining", result["missing_fields"])
        self.assertEqual(result["free_request_quota"], "INSUFFICIENT_FOR_TWO")
        self.assertEqual(
            sanitize({"data": {"usage": 0}})["free_request_quota"], "UNKNOWN"
        )

    def test_closed_budget_selection_excludes_identifiers_and_text(self):
        secret = "never-retain-secret"
        b = {
            "guardrail_id": secret,
            "budget_id": secret,
            "label": secret,
            "limit_usd": 0,
            "remaining_usd": 0,
            "spend_usd": 0,
            "include_byok": False,
            "reset_interval": "daily",
            "resets_at": "2026-10-28T00:00:00Z",
        }
        result = sanitize(
            {
                "data": {
                    "label": secret,
                    "free_model_daily_requests": None,
                    "budgets": [b],
                    "effective_budget": b,
                }
            }
        )
        self.assertNotIn(secret, json.dumps(result))
        self.assertEqual(result["quota"]["budgets"][0]["remaining_usd"], 0)
        self.assertIsNone(result["quota"]["free_model_daily_requests"])
        self.assertEqual(result["free_request_quota"], "UNKNOWN")

    def test_bad_values_do_not_become_quota(self):
        result = sanitize(
            {
                "data": {
                    "limit": "secret",
                    "free_model_daily_requests": {"remaining": True, "limit": 50},
                    "budgets": "secret",
                }
            }
        )
        self.assertNotIn("secret", json.dumps(result))
        self.assertEqual(result["free_request_quota"], "UNKNOWN")
        self.assertIn("budgets", result["invalid_fields"])

    def test_nested_null_is_not_missing_or_numeric_zero(self):
        result = sanitize(
            {
                "data": {
                    "free_model_daily_requests": {"used": None, "remaining": 0},
                    "budgets": [{"remaining_usd": None, "limit_usd": 0}],
                }
            }
        )
        self.assertIsNone(result["quota"]["free_model_daily_requests"]["used"])
        self.assertNotIn("limit", result["quota"]["free_model_daily_requests"])
        self.assertIsNone(result["quota"]["budgets"][0]["remaining_usd"])
        self.assertEqual(result["free_request_quota"], "UNKNOWN")

    def test_one_lookup_guard_no_polling_or_secret_retention(self):
        import io
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts.ops import openrouter_quota as q

        response = io.BytesIO(
            b'{"data":{"free_model_daily_requests":{"used":0,"limit":50,"remaining":50},"label":"private-label","budgets":[],"effective_budget":null}}'
        )
        response.status = 200
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(q.smoke, "PRIVATE", directory), patch.object(
                q.smoke,
                "load_private",
                return_value=({"OPENROUTER_API_KEY": "test-private-key"}, {}),
            ), patch.object(q, "build_opener") as opener:
                opener.return_value.open.return_value = response
                value = q.lookup()
                request = opener.return_value.open.call_args.args[0]
                self.assertEqual(request.get_method(), "GET")
                self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/key")
                self.assertIsNone(request.data)
                with self.assertRaises(FileExistsError):
                    q.lookup()
                self.assertEqual(opener.return_value.open.call_count, 1)
                self.assertNotIn("private-label", json.dumps(value))
                self.assertNotIn("test-private-key", json.dumps(value))
