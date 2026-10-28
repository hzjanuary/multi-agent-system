"""Missing/changed license evidence must fail the build, not imply compliance."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.ops.license_inventory import generate


class LicenseInventoryTests(unittest.TestCase):
    def test_supplement_hash_and_exact_installed_version_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            notice = root / "LICENSE"
            notice.write_text("MIT synthetic license")
            source = {
                "sources": [
                    {
                        "package": "absent-package",
                        "version": "1",
                        "file": "LICENSE",
                        "sha256": "0" * 64,
                    }
                ]
            }
            (root / "sources.json").write_text(json.dumps(source))
            with self.assertRaisesRegex(ValueError, "integrity"):
                generate(root / "out", root)
            import hashlib

            source["sources"][0]["sha256"] = hashlib.sha256(
                notice.read_bytes()
            ).hexdigest()
            (root / "sources.json").write_text(json.dumps(source))
            with patch(
                "scripts.ops.license_inventory.metadata.distributions", return_value=[]
            ):
                with self.assertRaisesRegex(ValueError, "stale"):
                    generate(root / "out", root)

    def test_metadata_declaration_without_full_text_is_not_sufficient(self):
        class Distribution:
            metadata = {"Name": "synthetic-package", "License": "MIT"}
            version = "1"
            files = ()

        class Metadata(dict):
            def get_all(self, key, default):
                return default

        distribution = Distribution()
        distribution.metadata = Metadata(distribution.metadata)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "sources.json").write_text('{"sources":[]}')
            with patch(
                "scripts.ops.license_inventory.metadata.distributions",
                return_value=[distribution],
            ):
                with self.assertRaisesRegex(ValueError, "incomplete"):
                    generate(root / "out", root)
