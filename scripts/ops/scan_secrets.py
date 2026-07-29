#!/usr/bin/env python3
"""Read-only tracked-file secret scanner for SPEC-027."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SKIP_PARTS = {
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
}
LOCAL_SENSITIVE_FILES = (
    "docker-compose.override.yml",
    ".env",
    "backend/.env",
    "frontend/.env.local",
)
SECRET_ASSIGNMENT_KEYS = (
    "API_KEY",
    "BEARER_TOKEN",
    "DATABASE_URL",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "JWT_SECRET",
    "JWT_SECRET_KEY",
    "MINIO_SECRET_KEY",
    "OPENROUTER_API_KEY",
    "PASSWORD",
    "POSTGRES_PASSWORD",
    "SECRET_KEY",
    "TAVILY_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TOKEN",
)
PLACEHOLDER_MARKERS = (
    "${",
    "<",
    "...",
    "change-me",
    "changeme",
    "demo",
    "example",
    "fake",
    "localhost",
    "minioadmin",
    "placeholder",
    "postgres",
    "test",
    "your-token-here",
)
MAX_HUMAN_FINDINGS = 50
TELEGRAM_TOKEN_RE = re.compile(r"\b\d{7,12}:[A-Za-z0-9_-]{30,}\b")
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
BEARER_RE = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/=-]{20,})")
ASSIGNMENT_RE = re.compile(
    r"\b("
    + "|".join(re.escape(key) for key in SECRET_ASSIGNMENT_KEYS)
    + r")\b\s*[:=]\s*['\"]?([^'\"\s#]+)"
)


@dataclass(frozen=True)
class Finding:
    """A redacted secret finding."""

    path: str
    line: int
    kind: str
    severity: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-safe form."""
        return {
            "path": self.path,
            "line": self.line,
            "kind": self.kind,
            "severity": self.severity,
            "detail": self.detail,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(
        description=(
            "Read-only tracked-file secret scan. Scans git-tracked files by "
            "default, skips local env files, and never prints secret values."
        ),
    )
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when suspicious findings are present.",
    )
    parser.add_argument(
        "--allow-test-placeholders",
        action="store_true",
        help="Allow demo/test/example placeholder values without blocking findings.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    result = scan_repository(
        repo_root=Path(args.repo_root),
        strict=bool(args.strict),
        allow_test_placeholders=bool(args.allow_test_placeholders),
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human_summary(result)
    return 0 if result["passed"] else 1


def scan_repository(
    *,
    repo_root: Path,
    strict: bool,
    allow_test_placeholders: bool,
    tracked_files: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Scan tracked files for secret risks without printing values."""
    root = repo_root.resolve()
    warnings = local_sensitive_file_warnings(root)
    files = list(tracked_files) if tracked_files is not None else git_tracked_files(root)
    findings: list[Finding] = []
    scanned_files = 0
    for relative in files:
        if should_skip_path(relative):
            continue
        path = root / relative
        if not path.is_file():
            continue
        text = read_text_safely(path)
        if text is None:
            continue
        scanned_files += 1
        findings.extend(
            scan_text(
                text,
                path=relative,
                allow_test_placeholders=allow_test_placeholders,
            ),
        )

    blocking = [finding for finding in findings if finding.severity == "blocking"]
    return {
        "passed": not (strict and blocking),
        "findings": [finding.as_dict() for finding in findings],
        "warnings": warnings,
        "scanned_files": scanned_files,
        "deterministic": True,
        "destructive_actions": False,
        "provider_calls": False,
        "secrets_printed": False,
    }


def git_tracked_files(repo_root: Path) -> list[str]:
    """Return tracked files from git ls-files."""
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def local_sensitive_file_warnings(repo_root: Path) -> list[str]:
    """Warn when common sensitive local files exist."""
    warnings: list[str] = []
    for relative in LOCAL_SENSITIVE_FILES:
        if (repo_root / relative).exists():
            warnings.append(f"Local sensitive file exists and was not scanned by default: {relative}")
    return warnings


def should_skip_path(relative: str) -> bool:
    """Return true when a path should not be scanned."""
    parts = set(Path(relative).parts)
    return bool(parts.intersection(SKIP_PARTS))


def read_text_safely(path: Path) -> str | None:
    """Read text files and skip binary/unreadable files."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_text(
    text: str,
    *,
    path: str,
    allow_test_placeholders: bool,
) -> list[Finding]:
    """Scan file text and return redacted findings."""
    findings: list[Finding] = []
    if allow_test_placeholders and is_test_fixture_path(path):
        return findings
    for line_number, line in enumerate(text.splitlines(), 1):
        if PRIVATE_KEY_RE.search(line):
            findings.append(finding(path, line_number, "private_key_marker"))
        if TELEGRAM_TOKEN_RE.search(line):
            findings.append(finding(path, line_number, "telegram_bot_token"))
        if JWT_RE.search(line):
            findings.append(finding(path, line_number, "jwt_like_value"))
        if BEARER_RE.search(line):
            token = BEARER_RE.search(line).group(1)  # type: ignore[union-attr]
            if not is_allowed_placeholder(token, allow_test_placeholders):
                findings.append(finding(path, line_number, "bearer_token"))
        for match in ASSIGNMENT_RE.finditer(line):
            key = match.group(1).upper()
            value = match.group(2)
            if is_allowed_placeholder(value, allow_test_placeholders) or is_code_declaration(value):
                continue
            findings.append(finding(path, line_number, f"secret_assignment:{key}"))
    return findings


def finding(path: str, line: int, kind: str) -> Finding:
    """Create a redacted finding."""
    return Finding(
        path=path,
        line=line,
        kind=kind,
        severity="blocking",
        detail="suspicious value redacted",
    )


def is_allowed_placeholder(value: str, allow_test_placeholders: bool) -> bool:
    """Return true for empty/documented placeholder values."""
    normalized = value.strip().strip('"').strip("'").lower()
    if normalized == "":
        return True
    if any(marker in normalized for marker in PLACEHOLDER_MARKERS):
        return True
    if allow_test_placeholders and any(marker in normalized for marker in ("demo", "fixture", "local", "sample")):
        return True
    return False


def is_test_fixture_path(path: str) -> bool:
    """Return true for test fixture paths where fake secret samples are expected."""
    parts = Path(path).parts
    return any(part in {"tests", "testdata", "fixtures"} for part in parts) or any(
        part.startswith("test_") for part in parts
    )


def is_code_declaration(value: str) -> bool:
    """Return true for typed code declarations, not concrete secret values."""
    normalized = value.strip().strip('"').strip("'")
    return normalized in {
        "Any",
        "Field(",
        "Optional",
        "SecretStr",
        "str",
    } or normalized.startswith(("Field(", "SecretStr(", "SettingsConfigDict("))


def print_human_summary(result: dict[str, Any]) -> None:
    """Print bounded human summary."""
    status = "PASS" if result["passed"] else "FAIL"
    print(f"{status}: tracked-file secret scan")
    print(f"Scanned files: {result['scanned_files']}")
    for warning in result["warnings"]:
        print(f"WARN: {warning}")
    for item in result["findings"][:MAX_HUMAN_FINDINGS]:
        print(f"{item['severity'].upper()}: {item['path']}:{item['line']} {item['kind']} ({item['detail']})")
    omitted = len(result["findings"]) - MAX_HUMAN_FINDINGS
    if omitted > 0:
        print(f"... {omitted} additional redacted findings omitted from human output")
    print("Safety: deterministic=true destructive_actions=false provider_calls=false secrets_printed=false")


if __name__ == "__main__":
    sys.exit(main())
