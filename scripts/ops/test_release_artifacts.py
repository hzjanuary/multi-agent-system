"""Adversarial artifact and license checks, entirely offline."""

import hashlib
import io
import json
from pathlib import Path
import secrets
import subprocess
import tarfile
import tempfile
import unittest

from scripts.ops import release_artifacts as gate
from scripts.ops import scan_secrets as scanner


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.files = {p: b"safe\n" for p in gate.REQUIRED}
        self.files[scanner.ALLOWLIST] = b'{"version":1,"entries":[]}'
        self.files["backend/Dockerfile"] = b"FROM scratch\n"
        self.files[".dockerignore"] = b"**\n!LICENSE\n"
        for path, data in self.files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Verification",
            "-c",
            "user.email=verify@example.invalid",
            "commit",
            "-qm",
            "fixture",
        )

    def git(self, *args):
        return gate.git(self.root, *args)

    def archive(self, members=None):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w") as archive:
            for path, data in (members or self.files).items():
                entry = tarfile.TarInfo(path)
                entry.size = len(data)
                archive.addfile(entry, io.BytesIO(data))
        return output.getvalue()

    def test_source_archive_matches_git_and_requires_materials(self):
        path = self.root / "source.tar"
        path.write_bytes(self.git("archive", "HEAD"))
        self.assertEqual(gate.check_archive(self.root, "HEAD", path)["status"], "PASS")
        changed = {**self.files, "README.md": b"tampered"}
        path.write_bytes(self.archive(changed))
        with self.assertRaises(gate.GateError):
            gate.check_archive(self.root, "HEAD", path)
        with self.assertRaises(gate.GateError):
            gate.validate_files({"README.md": b"safe"})

    def test_archive_private_paths_traversal_and_links_rejected(self):
        for path in (
            ".maos/auth.json",
            "private.env",
            "../LICENSE",
            "/LICENSE",
            "a//b",
            "a/./b",
            "dump.sql.gz",
        ):
            with self.subTest(path=path), self.assertRaises(gate.GateError):
                gate.archive_members(self.archive({path: b"safe"}))
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w") as archive:
            link = tarfile.TarInfo("linked")
            link.type = tarfile.SYMTYPE
            link.linkname = "/private.env"
            archive.addfile(link)
        with self.assertRaises(gate.GateError):
            gate.archive_members(output.getvalue())

    def test_force_added_private_file_and_index_symlink_rejected(self):
        (self.root / "private.env").write_text("safe")
        self.git("add", "-f", "private.env")
        with self.assertRaises(gate.GateError):
            gate.check_index(self.root)
        self.git("rm", "--cached", "private.env")
        (self.root / "link").symlink_to("LICENSE")
        self.git("add", "link")
        with self.assertRaises(gate.GateError):
            gate.check_index(self.root)

    def test_context_rejects_untracked_and_modified_inputs(self):
        self.assertEqual(gate.check_context(self.root, "HEAD")["status"], "PASS")
        target = self.root / "backend/app/private.env"
        target.parent.mkdir(parents=True)
        target.write_text("safe")
        with self.assertRaises(gate.GateError):
            gate.check_context(self.root, "HEAD")
        target.unlink()
        (self.root / "LICENSE").write_text("changed")
        with self.assertRaises(gate.GateError):
            gate.check_context(self.root, "HEAD")

    def test_archive_secret_adjacent_to_approved_text_blocked(self):
        value = "gsk_" + secrets.token_hex(24)
        line = "synthetic fixture"
        self.files[scanner.ALLOWLIST] = json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "path": "tests/probe.py",
                        "line_sha256": hashlib.sha256(line.encode()).hexdigest(),
                        "reason": "Exact fixture",
                    }
                ],
            }
        ).encode()
        self.files["tests/probe.py"] = (line + '\nAPI_KEY="' + value + '"').encode()
        with self.assertRaises(gate.GateError) as error:
            gate.validate_files(self.files)
        self.assertNotIn(value, str(error.exception))

    def test_policy_must_match_index(self):
        target = self.root / scanner.ALLOWLIST
        target.write_text('{"version":1,"entries":[],"changed":true}')
        result = scanner.scan_repository(
            repo_root=self.root, strict=True, allow_test_placeholders=True
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["findings"][0]["kind"], "scan_setup_error")

    def test_runtime_license_and_source_integrity_is_independent(self):
        source = {
            "LICENSE": b"MIT",
            "NOTICE": b"project",
            "backend/app/main.py": b"safe",
            "release/third-party/sources.json": b'{"sources":[],"license_references":[]}',
            "release/third-party/stack.json": b"{}",
        }
        runtime = gate.expected_runtime(source)
        runtime["licenses/inventory.json"] = (
            b'{"python":[],"license_texts":[],"deployment_stack":{}}'
        )
        gate.validate_image_files(runtime, source)
        for path, value in (
            ("app/main.py", b"changed"),
            ("licenses/project/LICENSE", b"missing"),
            ("app/tests/fake.py", b"safe"),
            ("private.env", b"safe"),
        ):
            with self.subTest(path=path), self.assertRaises(gate.GateError):
                gate.validate_image_files({**runtime, path: value}, source)
