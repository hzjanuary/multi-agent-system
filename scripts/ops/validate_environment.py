#!/usr/bin/env python3
"""Read-only production environment validation for SPEC-027.

The script validates env shape, risky flags, tracked local override state, and
optionally Compose config. It never prints secret values and never mutates
files, containers, databases, providers, or runtime state.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

CommandRunner = Callable[[list[str], Path], "CommandResult"]

STABLE_DEFAULTS: dict[str, str] = {
    "LLM_PROVIDER": "fake",
    "LLM_RUNTIME_ENABLED": "false",
    "PRICE_RESEARCH_ENABLED": "false",
    "RAG_ENABLED": "false",
    "OUTBOUND_COMMUNICATION_ENABLED": "false",
    "OUTBOUND_SEND_ENABLED": "false",
    "TELEGRAM_LLM_EXTRACTION_ENABLED": "false",
    "TELEGRAM_SALES_REPLY_ENABLED": "false",
}
RISKY_TRUE_FLAGS = {
    "LLM_RUNTIME_ENABLED",
    "PRICE_RESEARCH_ENABLED",
    "OUTBOUND_SEND_ENABLED",
    "RAG_ENABLED",
    "TELEGRAM_LLM_EXTRACTION_ENABLED",
}
SECRET_KEYS = {
    "TAVILY_API_KEY",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "MINIO_SECRET_KEY",
    "JWT_SECRET_KEY",
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
    "TELEGRAM_BOT_TOKEN",
}
PLACEHOLDER_MARKERS = (
    "change-me",
    "changeme",
    "demo",
    "example",
    "fake",
    "placeholder",
    "test",
    "your-token-here",
)


@dataclass(frozen=True)
class CommandResult:
    """Safe command result without exposing command output by default."""

    returncode: int
    summary: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Read-only production env validation. Runs no migrations, starts no "
            "containers, calls no providers, and prints no secret values."
        ),
    )
    parser.add_argument(
        "--env-file",
        default="docs/deployment/.env.production.example",
        help="Env file to inspect. Defaults to docs/deployment/.env.production.example.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a bounded JSON summary.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat risky flag deviations and tracked overrides as failures.",
    )
    parser.add_argument(
        "--skip-compose-check",
        action="store_true",
        help="Skip docker compose config validation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    result = validate_environment(
        repo_root=Path(args.repo_root),
        env_file=Path(args.env_file),
        strict=bool(args.strict),
        skip_compose_check=bool(args.skip_compose_check),
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human_summary(result)
    return 0 if result["passed"] else 1


def validate_environment(
    *,
    repo_root: Path,
    env_file: Path,
    strict: bool,
    skip_compose_check: bool,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Validate env shape and optional Compose config without mutation."""
    root = repo_root.resolve()
    env_path = env_file if env_file.is_absolute() else root / env_file
    runner = command_runner or run_command
    warnings: list[str] = []
    failures: list[str] = []
    checks: list[dict[str, str]] = []

    if not env_path.exists():
        failures.append(f"Env file not found: {safe_relative(env_path, root)}")
        checks.append({"name": "env_file_exists", "status": "FAIL"})
        return build_result(checks, warnings, failures)

    checks.append({"name": "env_file_exists", "status": "PASS"})
    env_values, parse_warnings = parse_env_file(env_path)
    warnings.extend(parse_warnings)
    checks.append({"name": "env_file_parse", "status": "PASS"})

    review_stable_defaults(env_values, warnings, failures, checks, strict=strict)
    review_secret_keys(env_values, warnings, checks)
    review_tracked_override(root, warnings, failures, checks, strict=strict, runner=runner)

    if skip_compose_check:
        checks.append({"name": "compose_config", "status": "SKIP"})
        checks.append({"name": "production_compose_config", "status": "SKIP"})
    else:
        run_compose_checks(root, env_file, checks, failures, runner)

    return build_result(checks, warnings, failures)


def parse_env_file(path: Path) -> tuple[dict[str, str], list[str]]:
    """Parse simple KEY=VALUE env files without shell evaluation."""
    values: dict[str, str] = {}
    warnings: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            warnings.append(f"Ignored non-assignment line {line_number}.")
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            warnings.append(f"Ignored invalid env key at line {line_number}.")
            continue
        values[key] = strip_quotes(value.strip())
    return values, warnings


def strip_quotes(value: str) -> str:
    """Strip matching single or double quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def review_stable_defaults(
    env_values: dict[str, str],
    warnings: list[str],
    failures: list[str],
    checks: list[dict[str, str]],
    *,
    strict: bool,
) -> None:
    """Review stable default flags and risky deviations."""
    for key, expected in STABLE_DEFAULTS.items():
        raw_value = env_values.get(key)
        if raw_value is None:
            warnings.append(f"{key} is not present; confirm default remains {expected}.")
            checks.append({"name": f"default:{key}", "status": "WARN"})
            continue
        normalized = normalize_boolish(raw_value)
        expected_normalized = normalize_boolish(expected)
        if normalized == expected_normalized:
            checks.append({"name": f"default:{key}", "status": "PASS"})
            continue
        message = f"{key} is set away from stable default; value redacted."
        if strict:
            failures.append(message)
            checks.append({"name": f"default:{key}", "status": "FAIL"})
        else:
            warnings.append(message)
            checks.append({"name": f"default:{key}", "status": "WARN"})


def review_secret_keys(
    env_values: dict[str, str],
    warnings: list[str],
    checks: list[dict[str, str]],
) -> None:
    """Review secret-bearing keys without printing values."""
    for key in sorted(SECRET_KEYS):
        if key not in env_values:
            continue
        value = env_values[key]
        if is_placeholder_value(value):
            checks.append({"name": f"secret_placeholder:{key}", "status": "PASS"})
        else:
            warnings.append(f"{key} is populated; value redacted. Confirm it is local and untracked.")
            checks.append({"name": f"secret_present:{key}", "status": "WARN"})


def review_tracked_override(
    repo_root: Path,
    warnings: list[str],
    failures: list[str],
    checks: list[dict[str, str]],
    *,
    strict: bool,
    runner: CommandRunner,
) -> None:
    """Check whether docker-compose.override.yml is tracked."""
    result = runner(["git", "ls-files", "docker-compose.override.yml"], repo_root)
    if result.returncode != 0:
        warnings.append("Could not inspect tracked docker-compose.override.yml state.")
        checks.append({"name": "tracked_compose_override", "status": "WARN"})
        return
    if result.summary.strip():
        message = "docker-compose.override.yml is tracked; it must remain local-only."
        if strict:
            failures.append(message)
            checks.append({"name": "tracked_compose_override", "status": "FAIL"})
        else:
            warnings.append(message)
            checks.append({"name": "tracked_compose_override", "status": "WARN"})
        return
    checks.append({"name": "tracked_compose_override", "status": "PASS"})


def run_compose_checks(
    repo_root: Path,
    env_file: Path,
    checks: list[dict[str, str]],
    failures: list[str],
    runner: CommandRunner,
) -> None:
    """Run read-only Compose config validation."""
    local_result = runner(["docker", "compose", "config"], repo_root)
    append_command_check("compose_config", local_result, checks, failures)
    prod_result = runner(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.prod.yml",
            "--env-file",
            str(env_file),
            "config",
        ],
        repo_root,
    )
    append_command_check("production_compose_config", prod_result, checks, failures)


def append_command_check(
    name: str,
    result: CommandResult,
    checks: list[dict[str, str]],
    failures: list[str],
) -> None:
    """Append a bounded command check result."""
    if result.returncode == 0:
        checks.append({"name": name, "status": "PASS"})
    else:
        checks.append({"name": name, "status": "FAIL"})
        failures.append(f"{name} failed: {result.summary}")


def run_command(command: list[str], cwd: Path) -> CommandResult:
    """Run a read-only validation command with bounded output."""
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return CommandResult(returncode=3, summary=type(error).__name__)
    if completed.returncode == 0 and command[:2] == ["git", "ls-files"]:
        summary = completed.stdout.strip()
    elif completed.returncode == 0:
        summary = "ok"
    else:
        summary = first_safe_line(completed.stderr or completed.stdout)
    return CommandResult(returncode=completed.returncode, summary=summary)


def first_safe_line(output: str) -> str:
    """Return a bounded non-secret command summary."""
    for line in output.splitlines():
        stripped = line.strip()
        if stripped:
            return redact_text(stripped)[:160]
    return "command failed"


def normalize_boolish(value: str) -> str:
    """Normalize common boolean text."""
    lowered = value.strip().strip('"').strip("'").lower()
    if lowered in {"1", "yes", "y", "on", "true"}:
        return "true"
    if lowered in {"0", "no", "n", "off", "false"}:
        return "false"
    return lowered


def is_placeholder_value(value: str) -> bool:
    """Return true when a value is empty or clearly placeholder/demo/test data."""
    normalized = value.strip().strip('"').strip("'").lower()
    if normalized == "":
        return True
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def redact_text(text: str) -> str:
    """Redact assignment values and bearer-like tokens from output."""
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1<redacted>", text)
    return re.sub(
        r"(?i)(token|key|secret|password|authorization)([A-Za-z0-9_ -]*[:=]\s*)\S+",
        r"\1\2<redacted>",
        text,
    )


def safe_relative(path: Path, root: Path) -> str:
    """Return a safe path display."""
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return path.name


def build_result(
    checks: list[dict[str, str]],
    warnings: list[str],
    failures: list[str],
) -> dict[str, Any]:
    """Build stable output."""
    return {
        "passed": not failures,
        "warnings": warnings,
        "failures": failures,
        "checks": checks,
        "deterministic": True,
        "destructive_actions": False,
        "provider_calls": False,
        "secrets_printed": False,
    }


def print_human_summary(result: dict[str, Any]) -> None:
    """Print bounded human output."""
    status = "PASS" if result["passed"] else "FAIL"
    print(f"{status}: production environment validation")
    for check in result["checks"]:
        print(f"- {check['status']}: {check['name']}")
    for warning in result["warnings"]:
        print(f"WARN: {warning}")
    for failure in result["failures"]:
        print(f"FAIL: {failure}")
    print("Safety: deterministic=true destructive_actions=false provider_calls=false secrets_printed=false")


if __name__ == "__main__":
    sys.exit(main())
