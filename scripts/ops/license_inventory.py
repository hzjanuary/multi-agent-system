"""Build a deterministic inventory and ship actual dependency notices, without imports."""

from __future__ import annotations
import argparse
import hashlib
import importlib.metadata as metadata
import json
import re
import shutil
import subprocess
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(out: Path, supplements: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    source = json.loads((supplements / "sources.json").read_text())
    sources = source["sources"]
    references = source.get("license_references", [])
    for entry in [*sources, *references]:
        path = supplements / Path(entry["file"]).name
        if path.is_symlink() or sha(path) != entry["sha256"]:
            raise ValueError("supplement integrity failure")
    packages = []
    for distribution in sorted(
        metadata.distributions(), key=lambda d: d.metadata["Name"].lower()
    ):
        name = distribution.metadata["Name"]
        normalized = re.sub("[-_.]+", "-", name).lower()
        matching = [
            e
            for e in sources
            if e["package"] == normalized and e["version"] == distribution.version
        ]
        files = []
        for member in distribution.files or ():
            base = Path(str(member)).name.lower()
            if base.startswith(
                ("license", "copying", "copyright", "notice")
            ) and not base.endswith((".py", ".pyc", ".so")):
                original = Path(distribution.locate_file(member))
                if not original.is_file():
                    raise ValueError("missing declared notice")
                contents = original.read_bytes()
                if not contents.strip():
                    raise ValueError("empty notice")
                target = (
                    out
                    / "python"
                    / normalized
                    / (hashlib.sha256(contents).hexdigest()[:12] + "-" + original.name)
                )
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(contents)
                files.append(
                    {
                        "path": str(target.relative_to(out)),
                        "sha256": sha(target),
                        "installed_source": str(original),
                    }
                )
        for entry in matching:
            original = supplements / Path(entry["file"]).name
            target = out / "python" / normalized / original.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            files.append(
                {
                    "path": str(target.relative_to(out)),
                    "sha256": sha(target),
                    "upstream_evidence": entry,
                }
            )
        expression = distribution.metadata.get("License-Expression")
        declaration = distribution.metadata.get("License")
        classifiers = [
            c
            for c in distribution.metadata.get_all("Classifier", [])
            if c.startswith("License")
        ]
        if not files or not any((expression, declaration, classifiers)):
            raise ValueError("dependency license evidence incomplete: " + normalized)
        packages.append(
            {
                "name": normalized,
                "version": distribution.version,
                "license_expression": expression,
                "license_metadata": declaration,
                "license_classifiers": classifiers,
                "notice_files": files,
                "supplemented": bool(matching),
            }
        )
    actual_versions = {p["name"]: p["version"] for p in packages}
    if any(actual_versions.get(e["package"]) != e["version"] for e in sources):
        raise ValueError("stale supplemental notice version")
    reference_files = []
    for entry in references:
        original = supplements / Path(entry["file"]).name
        target = out / "texts" / original.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        reference_files.append({**entry, "path": str(target.relative_to(out))})
    certifi = next(p for p in packages if p["name"] == "certifi")
    if "MPL" not in (certifi["license_metadata"] or "") or not any(
        e["license"] == "MPL-2.0" for e in references
    ):
        raise ValueError("certifi MPL notice/text must be reviewed")
    import certifi as certificates

    bundle = Path(certificates.where())
    if not bundle.is_file():
        raise ValueError("certifi source bundle missing")
    os_packages = []
    result = subprocess.run(
        ["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"],
        check=True,
        text=True,
        capture_output=True,
    )
    for row in result.stdout.splitlines():
        name, version = row.split("\t")
        copyright_file = Path("/usr/share/doc") / name.split(":", 1)[0] / "copyright"
        if not copyright_file.is_file():
            raise ValueError("OS copyright evidence missing: " + name)
        os_packages.append(
            {
                "name": name,
                "version": version,
                "copyright_file": str(copyright_file),
                "sha256": sha(copyright_file),
            }
        )
    stack = json.loads((supplements / "stack.json").read_text())
    inventory = {
        "schema_version": 1,
        "scope": "Actual installed distributions and base OS, not just root MIT metadata",
        "project": {
            "license": "MIT",
            "materials": ["project/LICENSE", "project/NOTICE"],
        },
        "python": packages,
        "license_texts": reference_files,
        "certifi_source": {
            "installed_readable_source": str(bundle),
            "sha256": sha(bundle),
            "license": "MPL-2.0",
            "notice": "The unmodified readable PEM source and upstream notice are shipped; MPL does not relicense application code.",
        },
        "os": {
            "packages": os_packages,
            "common_license_directory": "/usr/share/common-licenses",
            "python_base_license": "/usr/local/LICENSE",
            "source_access": "Debian source packages: https://sources.debian.org/ ; Python: https://www.python.org/downloads/source/",
        },
        "deployment_stack": stack,
        "claim": "License declarations and notice integrity are recorded; no universal legal compatibility or enterprise certification is asserted.",
    }
    if not Path("/usr/local/LICENSE").is_file():
        raise ValueError("Python base license missing")
    (out / "inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    )
    return inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--supplements", type=Path, required=True)
    args = parser.parse_args()
    inventory = generate(args.output, args.supplements)
    print(
        json.dumps(
            {
                "status": "PASS",
                "python_distributions": len(inventory["python"]),
                "os_packages": len(inventory["os"]["packages"]),
            }
        )
    )


if __name__ == "__main__":
    main()
