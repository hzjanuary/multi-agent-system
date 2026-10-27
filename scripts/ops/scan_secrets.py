#!/usr/bin/env python3
"""Fail-closed index/worktree secret and private-path gate. Values never enter reports."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.ops.release_policy import prohibited_path

ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = "scripts/ci/secret-fixtures.json"
MAX_BYTES = 16 * 1024 * 1024
TELEGRAM_TOKEN_RE = re.compile(r"\b\d{7,12}:[A-Za-z0-9_-]{30,}\b")
JWT_RE = re.compile(
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
PROVIDER_RE = re.compile(
    r"\b(?:gsk_[A-Za-z0-9]{24,}|sk-or-v1-[A-Za-z0-9]{32,}|sk-(?:proj-)?[A-Za-z0-9_-]{32,}|AIza[A-Za-z0-9_-]{30,}|tvly-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{20,})"
)
BEARER_RE = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/=-]{20,})")
DSN_RE = re.compile(
    r'(?i)\b(?:postgres(?:ql)?(?:\+asyncpg)?|mysql(?:\+\w+)?|redis|rediss|mongodb(?:\+srv)?)://[^\s\'"<>/@:]+:([^@\s\'"<>]+)@'
)
ASSIGNMENT_RE = re.compile(
    r"""(?i)(?<![\w])['"]?([A-Z][A-Z0-9_]*(?:API_KEY|PASSWORD|SECRET|SECRET_KEY|TOKEN)|API_KEY|PASSWORD|SECRET|TOKEN|DATABASE_URL)['"]?\s*[:=]\s*("(?:\\.|[^"\n])*"|'(?:\\.|[^'\n])*'|\$\{[^}\n]*\}|[^\s,;]+)"""
)
GENERATED_SECRET_RE = re.compile(
    r"\$\((?:python|python3) -c 'import secrets; print\(secrets\.(?:token_hex|token_urlsafe)\([1-9][0-9]*\)\)'\)"
)
REFERENCE_RE = re.compile(r"\$\{[A-Z_][A-Z0-9_]*(?::[-?][^{}]*)?\}")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    severity: str = "blocking"
    detail: str = "value withheld"

    def as_dict(self) -> dict[str, Any]:
        return dict(
            path=self.path,
            line=self.line,
            kind=self.kind,
            severity=self.severity,
            detail=self.detail,
        )


def load_allowances(root: Path) -> dict[str, set[str]]:
    data = json.loads((root / ALLOWLIST).read_text())
    if data.get("version") != 1 or not isinstance(data.get("entries"), list):
        raise ValueError("invalid fixture policy")
    result: dict[str, set[str]] = {}
    for entry in data["entries"]:
        if (
            set(entry) != {"path", "line_sha256", "reason"}
            or not entry["reason"]
            or not re.fullmatch("[a-f0-9]{64}", entry["line_sha256"])
            or prohibited_path(entry["path"])
        ):
            raise ValueError("invalid fixture allowance")
        result.setdefault(entry["path"], set()).add(entry["line_sha256"])
    return result


def reference(value: str) -> bool:
    # References are safe only without a concrete credential default. Error text
    # does not become a credential; all provider-shaped tokens are scanned anyway.
    match = REFERENCE_RE.fullmatch(value)
    return bool(match and (":-" not in value or value.endswith(":-}")))


def scan_text(
    text: str,
    *,
    path: str,
    allow_test_placeholders: bool,
    allowances: dict[str, set[str]] | None = None,
) -> list[Finding]:
    approved = (
        allowances
        if allowances is not None
        else (load_allowances(ROOT) if allow_test_placeholders else {})
    )
    findings: list[Finding] = []
    for number, line in enumerate(text.splitlines(), 1):
        if allow_test_placeholders and hashlib.sha256(
            line.encode()
        ).hexdigest() in approved.get(path, set()):
            continue
        kinds: set[str] = set()
        for name, pattern in [
            ("private_key_marker", PRIVATE_KEY_RE),
            ("provider_key", PROVIDER_RE),
            ("telegram_bot_token", TELEGRAM_TOKEN_RE),
            ("jwt_like_value", JWT_RE),
            ("bearer_token", BEARER_RE),
        ]:
            if pattern.search(line):
                kinds.add(name)
        for match in DSN_RE.finditer(line):
            if not reference(match.group(1)):
                kinds.add("credential_connection_string")
        for match in ASSIGNMENT_RE.finditer(line):
            key, value = match.groups()
            quoted = value[:1] in {'"', "'"} and value[-1:] == value[:1]
            if quoted:
                try:
                    value = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    kinds.add("unparsed_secret_assignment")
                    continue
            if value == "" or reference(value):
                continue
            if value.startswith(
                ("$(python", "$(python3")
            ) and GENERATED_SECRET_RE.search(line[match.start() :]):
                continue
            if path.endswith(".py") and not quoted:
                # Python names/calls are not literal credentials. Prefix/DSN
                # detection above still inspects the entire source line.
                continue
            kinds.add("secret_assignment:" + key.upper())
        findings.extend(Finding(path, number, kind) for kind in sorted(kinds))
    return findings


def index_entries(root: Path) -> list[tuple[str, str, str]]:
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=60,
    )
    entries = []
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, oid, stage = metadata.decode().split()
        if stage != "0":
            raise ValueError("unmerged index")
        entries.append((path.decode("utf-8"), mode, oid))
    if not entries:
        raise ValueError("empty or unreadable index")
    return entries


def decode_text(data: bytes) -> str:
    if len(data) > MAX_BYTES:
        raise ValueError("input exceeds scan bound")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    text = data.decode("utf-8-sig")
    if "\0" in text:
        raise ValueError("binary input requires explicit review")
    return text


def read_input(root: Path, relative: str) -> bytes:
    path = root
    for part in Path(relative).parts:
        path /= part
        if path.is_symlink():
            raise ValueError("symlink input")
    info = path.stat()
    if (
        not stat.S_ISREG(info.st_mode)
        or not info.st_mode & 0o444
        or info.st_size > MAX_BYTES
    ):
        raise ValueError("unreadable input")
    return path.read_bytes()


def scan_repository(
    *,
    repo_root: Path,
    strict: bool,
    allow_test_placeholders: bool,
    tracked_files: Iterable[str] | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    findings: list[Finding] = []
    scanned = 0
    failed = False
    try:
        approved = load_allowances(root) if allow_test_placeholders else {}
        entries = (
            [(p, "100644", None) for p in tracked_files]
            if tracked_files is not None
            else index_entries(root)
        )
        if tracked_files is None and allow_test_placeholders:
            policy_entry = next((e for e in entries if e[0] == ALLOWLIST), None)
            if policy_entry is None:
                raise ValueError("untracked fixture policy")
            indexed_policy = subprocess.run(
                ["git", "cat-file", "blob", policy_entry[2]],
                cwd=root,
                check=True,
                capture_output=True,
                timeout=30,
            ).stdout
            if indexed_policy != read_input(root, ALLOWLIST):
                raise ValueError("fixture policy differs from index")
        for path, mode, oid in entries:
            kind = prohibited_path(path)
            if kind or mode not in ("100644", "100755"):
                findings.append(Finding(path, 0, kind or "unsupported_index_mode"))
                continue
            try:
                working = read_input(root, path)
                contents = [working]
                if oid:
                    indexed = subprocess.run(
                        ["git", "cat-file", "blob", oid],
                        cwd=root,
                        check=True,
                        capture_output=True,
                        timeout=30,
                    ).stdout
                    if indexed != working:
                        contents.append(indexed)
                for data in contents:
                    findings.extend(
                        scan_text(
                            decode_text(data),
                            path=path,
                            allow_test_placeholders=allow_test_placeholders,
                            allowances=approved,
                        )
                    )
                scanned += 1
            except (OSError, ValueError, subprocess.SubprocessError):
                failed = True
                findings.append(Finding(path, 0, "scan_input_error"))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        failed = True
        findings.append(Finding("<scan>", 0, "scan_setup_error"))
    findings = list(dict.fromkeys(findings))
    return {
        "passed": not failed and not findings,
        "findings": [f.as_dict() for f in findings],
        "warnings": [],
        "scanned_files": scanned,
        "deterministic": True,
        "destructive_actions": False,
        "provider_calls": False,
        "secrets_printed": False,
    }


def print_human_summary(result: dict[str, Any]) -> None:
    print(
        ("PASS" if result["passed"] else "FAIL")
        + ": full tracked-file secret/path scan"
    )
    print("Scanned files:", result["scanned_files"])
    for value in result["findings"][:100]:
        print(f"{value['path']}:{value['line']} {value['kind']} (value withheld)")
    if len(result["findings"]) > 100:
        print("Additional findings:", len(result["findings"]) - 100)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Compatibility flag; blocking findings always fail",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--allow-approved-fixtures",
        "--allow-test-placeholders",
        dest="allow_test_placeholders",
        action="store_true",
        help="Use exact file/full-line hashes in reviewed fixture policy; never skip test files",
    )
    args = parser.parse_args(argv)
    result = scan_repository(
        repo_root=Path(args.repo_root),
        strict=args.strict,
        allow_test_placeholders=args.allow_test_placeholders,
    )
    (
        print(json.dumps(result, indent=2) if args.json else "", end="")
        if args.json
        else print_human_summary(result)
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
