"""Tests for read-only environment validation."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.ops import validate_environment
from scripts.ops.validate_environment import CommandResult


def ok_runner(command: list[str], cwd: Path) -> CommandResult:
    """Return successful command results, including clean git ls-files."""
    if command[:2] == ["git", "ls-files"]:
        return CommandResult(returncode=0, summary="")
    return CommandResult(returncode=0, summary="ok")


class ValidateEnvironmentTests(unittest.TestCase):
    """Validate environment script behavior."""

    def test_valid_env_file_passes_with_skipped_compose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / "prod.env"
            env_path.write_text(stable_env(), encoding="utf-8")

            result = validate_environment.validate_environment(
                repo_root=root,
                env_file=env_path,
                strict=False,
                skip_compose_check=True,
                command_runner=ok_runner,
            )

            self.assertTrue(result["passed"])
            self.assertEqual(result["deterministic"], True)
            self.assertEqual(result["destructive_actions"], False)
            self.assertEqual(result["provider_calls"], False)
            self.assertEqual(result["secrets_printed"], False)

    def test_risky_flags_warn_in_non_strict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / "prod.env"
            env_path.write_text(
                stable_env().replace("RAG_ENABLED=false", "RAG_ENABLED=true"),
                encoding="utf-8",
            )

            result = validate_environment.validate_environment(
                repo_root=root,
                env_file=env_path,
                strict=False,
                skip_compose_check=True,
                command_runner=ok_runner,
            )

            self.assertTrue(result["passed"])
            self.assertTrue(any("RAG_ENABLED" in warning for warning in result["warnings"]))

    def test_risky_flags_fail_in_strict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / "prod.env"
            env_path.write_text(
                stable_env().replace("LLM_PROVIDER=fake", "LLM_PROVIDER=groq"),
                encoding="utf-8",
            )

            result = validate_environment.validate_environment(
                repo_root=root,
                env_file=env_path,
                strict=True,
                skip_compose_check=True,
                command_runner=ok_runner,
            )

            self.assertFalse(result["passed"])
            self.assertTrue(any("LLM_PROVIDER" in failure for failure in result["failures"]))

    def test_secret_like_env_values_are_redacted(self) -> None:
        secret_value = "tvly-real-secret-value-123456789"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / "prod.env"
            env_path.write_text(stable_env() + f"\nTAVILY_API_KEY={secret_value}\n", encoding="utf-8")

            result = validate_environment.validate_environment(
                repo_root=root,
                env_file=env_path,
                strict=False,
                skip_compose_check=True,
                command_runner=ok_runner,
            )
            output = io.StringIO()
            with redirect_stdout(output):
                validate_environment.print_human_summary(result)

            self.assertNotIn(secret_value, json.dumps(result))
            self.assertNotIn(secret_value, output.getvalue())
            self.assertIn("TAVILY_API_KEY", output.getvalue())

    def test_missing_env_file_fails_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = validate_environment.validate_environment(
                repo_root=root,
                env_file=root / "missing.env",
                strict=False,
                skip_compose_check=True,
                command_runner=ok_runner,
            )

            self.assertFalse(result["passed"])
            self.assertTrue(result["failures"])

    def test_json_output_shape_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / "prod.env"
            env_path.write_text(stable_env(), encoding="utf-8")

            result = validate_environment.validate_environment(
                repo_root=root,
                env_file=env_path,
                strict=False,
                skip_compose_check=True,
                command_runner=ok_runner,
            )

            self.assertEqual(
                set(result),
                {
                    "passed",
                    "warnings",
                    "failures",
                    "checks",
                    "deterministic",
                    "destructive_actions",
                    "provider_calls",
                    "secrets_printed",
                },
            )

    def test_compose_checks_can_be_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / "prod.env"
            env_path.write_text(stable_env(), encoding="utf-8")

            result = validate_environment.validate_environment(
                repo_root=root,
                env_file=env_path,
                strict=False,
                skip_compose_check=True,
                command_runner=ok_runner,
            )

            skipped = [check for check in result["checks"] if check["status"] == "SKIP"]
            self.assertEqual({check["name"] for check in skipped}, {"compose_config", "production_compose_config"})

    def test_tracked_compose_override_fails_in_strict(self) -> None:
        def tracked_runner(command: list[str], cwd: Path) -> CommandResult:
            if command[:2] == ["git", "ls-files"]:
                return CommandResult(returncode=0, summary="docker-compose.override.yml")
            return CommandResult(returncode=0, summary="ok")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_path = root / "prod.env"
            env_path.write_text(stable_env(), encoding="utf-8")

            result = validate_environment.validate_environment(
                repo_root=root,
                env_file=env_path,
                strict=True,
                skip_compose_check=True,
                command_runner=tracked_runner,
            )

            self.assertFalse(result["passed"])
            self.assertTrue(any("docker-compose.override.yml" in failure for failure in result["failures"]))


def stable_env() -> str:
    """Return a stable deterministic env fixture."""
    return "\n".join(
        [
            "LLM_PROVIDER=fake",
            "LLM_RUNTIME_ENABLED=false",
            "PRICE_RESEARCH_ENABLED=false",
            "RAG_ENABLED=false",
            "OUTBOUND_COMMUNICATION_ENABLED=false",
            "OUTBOUND_SEND_ENABLED=false",
            "TELEGRAM_LLM_EXTRACTION_ENABLED=false",
            "TELEGRAM_SALES_REPLY_ENABLED=false",
            "JWT_SECRET_KEY=change-me-in-production",
            "",
        ],
    )


if __name__ == "__main__":
    unittest.main()
