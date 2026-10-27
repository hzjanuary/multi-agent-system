"""Independent Git, source-archive, build-input and runtime-image release gates."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.ops.release_policy import build_input, prohibited_path
from scripts.ops.scan_secrets import (
    ALLOWLIST,
    decode_text,
    index_entries,
    read_input,
    scan_text,
)

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {"LICENSE", "NOTICE", "README.md", "SECURITY.md", "CONTRIBUTING.md"}


class GateError(ValueError):
    pass


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True
    ).stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path, revision: str) -> dict[str, bytes]:
    revision = (
        git(root, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
    )
    files = {}
    for row in git(root, "ls-tree", "-rz", revision).split(b"\0"):
        if not row:
            continue
        metadata, encoded = row.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        path = encoded.decode()
        check_path(path, mode)
        if kind != "blob":
            raise GateError("unsupported_git_object")
        files[path] = git(root, "cat-file", "blob", oid)
    validate_files(files)
    return files


def check_path(path: str, mode: str = "100644") -> None:
    reason = prohibited_path(path)
    if reason or mode not in {"100644", "100755"}:
        raise GateError((reason or "symlink_or_special_path") + ":" + path)


def validate_files(files: dict[str, bytes]) -> None:
    if not REQUIRED <= files.keys():
        raise GateError("required_release_material_missing")
    allowances = {}
    policy = json.loads(files[ALLOWLIST])
    if policy["version"] != 1:
        raise GateError("fixture_policy_version")
    for entry in policy["entries"]:
        check_path(entry["path"])
        allowances.setdefault(entry["path"], set()).add(entry["line_sha256"])
    for path, data in files.items():
        check_path(path)
        findings = scan_text(
            decode_text(data),
            path=path,
            allow_test_placeholders=True,
            allowances=allowances,
        )
        if findings:
            raise GateError(
                "secret:" + path + ":" + str(findings[0].line) + ":" + findings[0].kind
            )


def check_index(root: Path) -> dict:
    entries = index_entries(root)
    for path, mode, _ in entries:
        check_path(path, mode)
        read_input(
            root, path
        )  # Reject working-tree symlinks even when index is regular.
    return {"status": "PASS", "gate": "tracked_paths", "files": len(entries)}


def archive_members(data: bytes) -> dict[str, bytes]:
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
        for member in archive:
            path = member.name
            if member.isdir():
                check_path(path.rstrip("/"))
                continue
            check_path(path)
            if not member.isfile() or path in files or member.size > 16 * 1024 * 1024:
                raise GateError("unsafe_archive_member:" + path)
            stream = archive.extractfile(member)
            if stream is None:
                raise GateError("unreadable_archive_member")
            files[path] = stream.read()
    return files


def check_archive(root: Path, revision: str, archive: Path) -> dict:
    expected = snapshot(root, revision)
    actual = archive_members(archive.read_bytes())
    validate_files(actual)
    if actual != expected:
        raise GateError("archive_manifest_integrity")
    return {
        "status": "PASS",
        "gate": "source_archive",
        "files": len(actual),
        "sha256": digest(archive.read_bytes()),
    }


def check_context(root: Path, revision: str) -> dict:
    if (root / "backend/Dockerfile.dockerignore").exists() or (
        root / "backend/Dockerfile.dockerignore"
    ).is_symlink():
        raise GateError("unexpected_dockerfile_ignore_override")
    files = snapshot(root, revision)
    expected = {p: b for p, b in files.items() if build_input(p)}
    for path, contents in expected.items():
        if read_input(root, path) != contents:
            raise GateError("modified_build_input:" + path)
    for prefix in (
        "backend/app",
        "backend/maos_examples",
        "backend/alembic",
        "release/third-party",
    ):
        for path in (root / prefix).rglob("*"):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise GateError("symlink_build_input:" + relative)
            if path.is_file() and relative not in expected:
                # Only interpreter caches are excluded mechanically, never secrets.
                if "__pycache__" in path.parts and path.suffix == ".pyc":
                    continue
                raise GateError("untracked_or_private_build_input:" + relative)
    for path in (".dockerignore", "backend/Dockerfile"):
        if read_input(root, path) != files[path]:
            raise GateError("modified_context_policy")
    return {
        "status": "PASS",
        "gate": "build_inputs",
        "files": len(expected),
        "content_sha256": digest(
            b"".join(
                p.encode() + b"\0" + hashlib.sha256(b).digest()
                for p, b in sorted(expected.items())
            )
        ),
    }


# Runs without network or application imports, as the image's default user.
COLLECT = r"""
import base64, hashlib, importlib.metadata as md, json, pathlib, re
root=pathlib.Path('/app')
files={}
for p in root.rglob('*'):
    if p.is_symlink(): raise ValueError('app symlink')
    if p.is_file(): files[str(p.relative_to(root))]=base64.b64encode(p.read_bytes()).decode()
inv=json.loads((root/'licenses/inventory.json').read_text())
actual={re.sub('[-_.]+','-',d.metadata['Name']).lower():d.version for d in md.distributions()}
assert actual=={p['name']:p['version'] for p in inv['python']}, 'distribution inventory mismatch'
for package in inv['python']:
    assert package['notice_files'] and any((package['license_expression'],package['license_metadata'],package['license_classifiers']))
    for notice in package['notice_files']:
        assert hashlib.sha256((root/'licenses'/notice['path']).read_bytes()).hexdigest()==notice['sha256']
        if 'installed_source' in notice:
            assert hashlib.sha256(pathlib.Path(notice['installed_source']).read_bytes()).hexdigest()==notice['sha256']
for notice in inv['license_texts']:
    assert hashlib.sha256((root/'licenses'/notice['path']).read_bytes()).hexdigest()==notice['sha256']
for package in inv['os']['packages']:
    assert hashlib.sha256(pathlib.Path(package['copyright_file']).read_bytes()).hexdigest()==package['sha256']
assert pathlib.Path(inv['os']['python_base_license']).is_file()
cert=inv['certifi_source']
assert hashlib.sha256(pathlib.Path(cert['installed_readable_source']).read_bytes()).hexdigest()==cert['sha256']
print(json.dumps({'files':files,'python_distributions':len(actual),'os_packages':len(inv['os']['packages'])}))
"""


def expected_runtime(files: dict[str, bytes]) -> dict[str, bytes]:
    result = {"licenses/project/" + p: files[p] for p in ("LICENSE", "NOTICE")}
    for path, data in files.items():
        if (
            path.startswith(
                ("backend/app/", "backend/maos_examples/", "backend/alembic/")
            )
            or path == "backend/alembic.ini"
        ):
            if not path.startswith("backend/app/tests/"):
                result[path.removeprefix("backend/")] = data
    return result


def validate_image_files(files: dict[str, bytes], source: dict[str, bytes]) -> None:
    expected = expected_runtime(source)
    for path, data in expected.items():
        if files.get(path) != data:
            raise GateError("shipped_file_integrity:" + path)
    for path, data in files.items():
        if path.startswith("licenses/"):
            continue  # These texts are independently hashed against inventory below.
        mapped = "backend/" + path
        check_path(mapped)
        if path not in expected or any(
            part in {"tests", "demo", "fake.py"} for part in Path(path).parts
        ):
            raise GateError("unexpected_runtime_file:" + path)
        if scan_text(decode_text(data), path=mapped, allow_test_placeholders=False):
            raise GateError("runtime_secret:" + path)
    inventory = json.loads(files["licenses/inventory.json"])
    for entry in json.loads(source["release/third-party/sources.json"])["sources"]:
        matches = [
            p
            for p in inventory["python"]
            if p["name"] == entry["package"] and p["version"] == entry["version"]
        ]
        if not matches or not any(
            n["sha256"] == entry["sha256"] for n in matches[0]["notice_files"]
        ):
            raise GateError("upstream_notice_integrity")
    texts = json.loads(source["release/third-party/sources.json"])["license_references"]
    for entry in texts:
        if not any(n["sha256"] == entry["sha256"] for n in inventory["license_texts"]):
            raise GateError("license_text_integrity")
    if inventory["deployment_stack"] != json.loads(
        source["release/third-party/stack.json"]
    ):
        raise GateError("stack_inventory_integrity")
    allowed_licenses = {
        "licenses/inventory.json",
        "licenses/project/LICENSE",
        "licenses/project/NOTICE",
    }
    for package in inventory["python"]:
        allowed_licenses.update(
            "licenses/" + n["path"] for n in package["notice_files"]
        )
    allowed_licenses.update("licenses/" + n["path"] for n in inventory["license_texts"])
    if {p for p in files if p.startswith("licenses/")} != allowed_licenses:
        raise GateError("unexpected_license_material")


def check_image(root: Path, revision: str, image: str) -> dict:
    source = snapshot(root, revision)
    sha = git(root, "rev-parse", revision).decode().strip()
    config = json.loads(
        subprocess.run(
            ["docker", "image", "inspect", image], check=True, capture_output=True
        ).stdout
    )[0]
    if (
        config["Config"].get("Labels", {}).get("org.opencontainers.image.revision")
        != sha
    ):
        raise GateError("image_revision_mismatch")
    if config["Config"].get("User") in (None, "", "root", "0"):
        raise GateError("root_runtime")
    for row in config["Config"].get("Env", []):
        if scan_text(row, path="image-config", allow_test_placeholders=False):
            raise GateError("image_environment_secret")
    run = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            image,
            "python",
            "-c",
            COLLECT,
        ],
        capture_output=True,
        timeout=120,
    )
    if run.returncode:
        raise GateError("image_inventory_or_collection_failed")
    collected = json.loads(run.stdout)
    files = {
        p: base64.b64decode(data, validate=True)
        for p, data in collected.pop("files").items()
    }
    validate_image_files(files, source)
    return {
        "status": "PASS",
        "gate": "release_image",
        "source": sha,
        "image": config["Id"],
        "shipped_files": len(files),
        **collected,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("index", "source", "context", "image"))
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--image")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        if args.operation == "index":
            result = check_index(args.root)
        elif args.operation == "source":
            result = check_archive(args.root, args.revision, args.archive)
        elif args.operation == "context":
            result = check_context(args.root, args.revision)
        else:
            result = check_image(args.root, args.revision, args.image)
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # Never emit raw subprocess errors, file contents or resolved configuration.
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "gate": args.operation,
                    "detail": "artifact/policy/integrity check failed; inspect with focused offline tests",
                }
            )
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
