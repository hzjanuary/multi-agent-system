"""Tests for read-only tracked-file secret scan."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.ops import scan_secrets


class ScanSecretsTests(unittest.TestCase):
    """Validate secret scan behavior."""

    def test_placeholder_values_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "example.env", "TAVILY_API_KEY=change-me-in-production\nJWT_SECRET_KEY=fake\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=True,
                tracked_files=["example.env"],
            )

            self.assertTrue(result["passed"])
            self.assertEqual(result["findings"], [])

    def test_suspicious_api_key_detected_without_value(self) -> None:
        secret_value = "tvly-real-secret-value-123456789"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "config.env", f"TAVILY_API_KEY={secret_value}\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=False,
                tracked_files=["config.env"],
            )
            output = io.StringIO()
            with redirect_stdout(output):
                scan_secrets.print_human_summary(result)

            self.assertFalse(result["passed"])
            self.assertNotIn(secret_value, json.dumps(result))
            self.assertNotIn(secret_value, output.getvalue())
            self.assertIn("TAVILY_API_KEY", json.dumps(result))

    def test_telegram_token_pattern_detected_and_redacted(self) -> None:
        token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "bot.txt", f"token={token}\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=False,
                tracked_files=["bot.txt"],
            )

            self.assertFalse(result["passed"])
            self.assertNotIn(token, json.dumps(result))
            self.assertTrue(any(item["kind"] == "telegram_bot_token" for item in result["findings"]))

    def test_private_key_marker_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "private.pem", "-----BEGIN PRIVATE KEY-----\nredacted\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=False,
                tracked_files=["private.pem"],
            )

            self.assertFalse(result["passed"])
            self.assertTrue(any(item["kind"] == "private_key_marker" for item in result["findings"]))

    def test_node_modules_and_git_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "node_modules/pkg/config.env", "TAVILY_API_KEY=real-secret-123456\n")
            write(root, ".git/config", "TAVILY_API_KEY=real-secret-123456\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=False,
                tracked_files=["node_modules/pkg/config.env", ".git/config"],
            )

            self.assertTrue(result["passed"])
            self.assertEqual(result["scanned_files"], 0)

    def test_tracked_file_only_behavior_uses_supplied_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "tracked.env", "TAVILY_API_KEY=real-secret-123456\n")
            write(root, "untracked.env", "GROQ_API_KEY=real-secret-654321\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=False,
                tracked_files=["tracked.env"],
            )

            self.assertFalse(result["passed"])
            self.assertEqual(result["scanned_files"], 1)
            self.assertTrue(all(item["path"] == "tracked.env" for item in result["findings"]))

    def test_json_output_shape_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "safe.env", "TAVILY_API_KEY=\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=False,
                allow_test_placeholders=True,
                tracked_files=["safe.env"],
            )

            self.assertEqual(
                set(result),
                {
                    "passed",
                    "findings",
                    "warnings",
                    "scanned_files",
                    "deterministic",
                    "destructive_actions",
                    "provider_calls",
                    "secrets_printed",
                },
            )

    def test_strict_mode_fails_on_suspicious_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "unsafe.env", "OPENROUTER_API_KEY=real-secret-123456\n")

            strict = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=False,
                tracked_files=["unsafe.env"],
            )
            non_strict = scan_secrets.scan_repository(
                repo_root=root,
                strict=False,
                allow_test_placeholders=False,
                tracked_files=["unsafe.env"],
            )

            self.assertFalse(strict["passed"])
            self.assertTrue(non_strict["passed"])

    def test_allow_test_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "fixture.env", "GEMINI_API_KEY=fixture-local-value\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=True,
                tracked_files=["fixture.env"],
            )

            self.assertTrue(result["passed"])

    def test_allow_test_placeholders_skips_test_fixtures(self) -> None:
        token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "scripts/ops/test_fixture.py", f"FAKE_TOKEN = '{token}'\n")

            result = scan_secrets.scan_repository(
                repo_root=root,
                strict=True,
                allow_test_placeholders=True,
                tracked_files=["scripts/ops/test_fixture.py"],
            )

            self.assertTrue(result["passed"])
            self.assertEqual(result["findings"], [])


def write(root: Path, relative: str, content: str) -> None:
    """Write fixture content."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
