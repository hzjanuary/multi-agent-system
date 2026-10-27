"""Reproduce original SPEC-030 findings using synthetic values and immutable baseline."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
import types

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.ops.scan_secrets import scan_text

BASELINE = "320e527a48ef9a6a2e725342ce165e3d6835931e"
IMAGE = "sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959"


def main():
    original = subprocess.check_output(
        ["git", "show", BASELINE + ":scripts/ops/scan_secrets.py"]
    )
    module = types.ModuleType("baseline_scanner")
    sys.modules[module.__name__] = module
    exec(compile(original, "baseline-scanner", "exec"), module.__dict__)
    key = "gsk_" + secrets.token_hex(24)
    probes = [
        (
            "test_source",
            "backend/app/tests/test_probe.py",
            'GROQ_API_KEY="' + key + '"',
        ),
        (
            "credential_dsn",
            "config.txt",
            "postgresql://user:" + secrets.token_hex(24) + "@db.invalid/app",
        ),
        (
            "substring_exception",
            "notes.txt",
            "GROQ_API_KEY=" + secrets.token_hex(16) + "example" + secrets.token_hex(16),
        ),
    ]
    results = []
    for category, path, text in probes:
        old = module.scan_text(text, path=path, allow_test_placeholders=True)
        new = scan_text(text, path=path, allow_test_placeholders=True, allowances={})
        results.append(
            {"probe": category, "old_findings": len(old), "new_findings": len(new)}
        )
    paths = (
        "/app/LICENSE",
        "/app/NOTICE",
        "/app/licenses/project/LICENSE",
        "/app/licenses/project/NOTICE",
    )
    command = (
        "import json;from pathlib import Path;print(json.dumps({p:Path(p).is_file() for p in "
        + repr(paths)
        + "}))"
    )
    old_materials = json.loads(
        subprocess.check_output(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                IMAGE,
                "python",
                "-c",
                command,
            ]
        )
    )
    assert not any(old_materials.values())
    assert all(r["old_findings"] == 0 and r["new_findings"] > 0 for r in results)
    print(
        json.dumps(
            {
                "status": "PASS",
                "baseline_source": BASELINE,
                "baseline_image": IMAGE,
                "baseline_scanner_sha256": hashlib.sha256(original).hexdigest(),
                "probes": results,
                "baseline_license_paths": old_materials,
                "generation_requests": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
