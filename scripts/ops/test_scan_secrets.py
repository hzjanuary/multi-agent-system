"""Adversarial synthetic probes: no realistic secret literal is committed."""

import contextlib
import hashlib
import io
import json
import secrets
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ops import scan_secrets as scanner


class ScanSecretsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write(scanner.ALLOWLIST, json.dumps({"version": 1, "entries": []}))

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def scan(self, paths, strict=True):
        return scanner.scan_repository(
            repo_root=self.root,
            strict=strict,
            allow_test_placeholders=True,
            tracked_files=paths,
        )

    def key(self):
        return "gsk_" + secrets.token_hex(24)

    def test_test_source_is_not_excluded_and_reports_are_sanitized(self):
        value = self.key()
        self.write("backend/app/tests/test_probe.py", f'GROQ_API_KEY = "{value}"\n')
        result = self.scan(["backend/app/tests/test_probe.py"])
        self.assertFalse(result["passed"])
        self.assertNotIn(value, json.dumps(result))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            scanner.print_human_summary(result)
        self.assertNotIn(value, output.getvalue())

    def test_password_dsn_detected_for_postgres_and_other_schemes(self):
        value = secrets.token_hex(24)
        for scheme in (
            "postgres",
            "postgresql",
            "postgresql+asyncpg",
            "mysql",
            "redis",
            "mongodb+srv",
        ):
            self.write(
                "config.txt", f"DATABASE_URL={scheme}://user:{value}@db.invalid/app\n"
            )
            result = self.scan(["config.txt"])
            self.assertFalse(result["passed"], scheme)
            self.assertIn(
                "credential_connection_string", {f["kind"] for f in result["findings"]}
            )
            self.assertNotIn(value, json.dumps(result))

    def test_placeholder_substrings_and_filename_do_not_allow_a_credential(self):
        for marker in (
            "test",
            "example",
            "demo",
            "placeholder",
            "postgres",
            "sample",
            "fake",
        ):
            value = secrets.token_hex(16) + marker + secrets.token_hex(16)
            self.write("example-placeholder-demo.txt", "GROQ_API_KEY=" + value + "\n")
            self.assertFalse(self.scan(["example-placeholder-demo.txt"])["passed"])

    def test_exact_file_line_allowance_does_not_allow_adjacent_or_appended_key(self):
        value = self.key()
        path = "tests/fixture.py"
        line = f'GROQ_API_KEY="{value}"'
        self.write(
            scanner.ALLOWLIST,
            json.dumps(
                {
                    "version": 1,
                    "entries": [
                        {
                            "path": path,
                            "line_sha256": hashlib.sha256(line.encode()).hexdigest(),
                            "reason": "Only this generated synthetic test fixture",
                        }
                    ],
                }
            ),
        )
        self.write(path, line + "\n")
        self.assertTrue(self.scan([path])["passed"])
        other = self.key()
        for text in (
            line + '\nOPENROUTER_API_KEY="' + other + '"\n',
            line + '; API_KEY="' + other + '"\n',
        ):
            self.write(path, text)
            self.assertFalse(self.scan([path])["passed"])
        self.write("tests/other.py", line + "\n")
        self.assertFalse(self.scan(["tests/other.py"])["passed"])

    def test_force_added_private_paths_rejected_with_no_secret_content(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".gitignore", ".maos/\n")
        self.write(".maos/auth.json", "{}")
        subprocess.run(
            ["git", "add", "-f", ".maos/auth.json"], cwd=self.root, check=True
        )
        result = scanner.scan_repository(
            repo_root=self.root, strict=True, allow_test_placeholders=False
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["findings"][0]["kind"], "private_directory")

    def test_sensitive_exports_and_configs_outside_private_dir_rejected(self):
        for path in (
            ".env.production",
            "backend/private.env",
            "auth.json",
            "credentials.json",
            "backup.dump",
            "export.sql",
            "x/db.sqlite",
            "key.pem",
        ):
            self.write(path, "{}")
            self.assertFalse(self.scan([path])["passed"], path)

    def test_staged_secret_detected_even_after_worktree_overwritten(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        value = self.key()
        self.write("test_source.py", f'GROQ_API_KEY="{value}"')
        subprocess.run(["git", "add", "test_source.py"], cwd=self.root, check=True)
        self.write("test_source.py", "# innocent worktree")
        result = scanner.scan_repository(
            repo_root=self.root, strict=True, allow_test_placeholders=False
        )
        self.assertFalse(result["passed"])
        self.assertNotIn(value, json.dumps(result))

    def test_missing_unreadable_and_symlink_inputs_fail_closed_even_non_strict(self):
        self.assertFalse(self.scan(["missing.txt"], strict=False)["passed"])
        p = self.write("unreadable.txt", "text")
        p.chmod(0)
        self.assertFalse(self.scan(["unreadable.txt"], strict=False)["passed"])
        p.chmod(0o600)
        (self.root / "link.txt").symlink_to(p)
        self.assertFalse(self.scan(["link.txt"], strict=False)["passed"])
        self.assertFalse(self.scan(["../escape"], strict=False)["passed"])

    def test_index_failure_does_not_return_empty_success(self):
        with patch.object(
            scanner.subprocess,
            "run",
            side_effect=OSError("secret error must not be printed"),
        ):
            result = scanner.scan_repository(
                repo_root=self.root, strict=False, allow_test_placeholders=False
            )
        self.assertFalse(result["passed"])
        self.assertNotIn("secret error", json.dumps(result))

    def test_binary_or_bad_allowlist_fails_closed(self):
        (self.root / "opaque.bin").write_bytes(b"\0\xff")
        self.assertFalse(self.scan(["opaque.bin"], strict=False)["passed"])
        self.write(scanner.ALLOWLIST, "{bad")
        self.assertFalse(self.scan([], strict=False)["passed"])

    def test_utf16_text_is_scanned(self):
        (self.root / "encoded.txt").write_bytes(
            ("API_KEY=" + self.key()).encode("utf-16")
        )
        self.assertFalse(self.scan(["encoded.txt"])["passed"])

    def test_empty_values_and_references_not_literals(self):
        self.write(
            "safe.txt",
            "GROQ_API_KEY=\nTOKEN=${TOKEN}\nTOKEN=${TOKEN:-}\nPOSTGRES_PASSWORD=${POSTGRES_PASSWORD:?Generate private config}\n",
        )
        self.assertTrue(self.scan(["safe.txt"])["passed"])
        self.write("safe.txt", "TOKEN=${TOKEN:-" + secrets.token_hex(24) + "}\n")
        self.assertFalse(self.scan(["safe.txt"])["passed"])

    def test_exact_random_generator_does_not_mask_another_literal(self):
        generated = 'echo "JWT_SECRET_KEY=$(python -c \'import secrets; print(secrets.token_hex(32))\')" >> "$GITHUB_ENV"'
        self.assertFalse(
            scanner.scan_text(
                generated,
                path=".github/workflows/ci.yml",
                allow_test_placeholders=False,
            )
        )
        text = generated + "\nJWT_SECRET_KEY=" + secrets.token_hex(32)
        self.assertTrue(
            scanner.scan_text(
                text, path=".github/workflows/ci.yml", allow_test_placeholders=False
            )
        )
        self.assertTrue(
            scanner.scan_text(
                "JWT_SECRET_KEY=$(printf " + secrets.token_hex(24) + ")",
                path="build.sh",
                allow_test_placeholders=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
