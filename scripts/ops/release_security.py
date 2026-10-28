"""Pinned vulnerability tooling and fail-closed release security summaries."""

from __future__ import annotations
import argparse
import hashlib
import io
import datetime
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def install_trivy(destination: Path) -> None:
    lock = json.loads((ROOT / "release/tools.lock.json").read_text())["trivy"]
    with urllib.request.urlopen(lock["url"], timeout=120) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != lock["archive_sha256"]:
        raise ValueError("tool archive integrity failure")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as stream:
        member = stream.getmember("trivy")
        if not member.isfile():
            raise ValueError("tool is not regular file")
        binary = stream.extractfile(member).read()
    if hashlib.sha256(binary).hexdigest() != lock["binary_sha256"]:
        raise ValueError("tool binary integrity failure")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.write_bytes(binary)
    destination.chmod(0o700)


def summarize(report: dict) -> dict:
    if not isinstance(report.get("Results"), list) or not report.get(
        "Metadata", {}
    ).get("OS"):
        raise ValueError("missing OS scan evidence")
    if not any(r.get("Class") == "os-pkgs" for r in report["Results"]):
        raise ValueError("OS result missing")
    rows = []
    for result in report["Results"]:
        for item in result.get("Vulnerabilities", []):
            rows.append(
                {
                    "id": item["VulnerabilityID"],
                    "package": item["PkgName"],
                    "installed": item["InstalledVersion"],
                    "fixed": item.get("FixedVersion") or None,
                    "severity": item["Severity"],
                    "class": result.get("Class"),
                    "reference": item.get("PrimaryURL"),
                    "vendor_severity": item.get("VendorSeverity"),
                    "severity_source": item.get("SeveritySource"),
                    "vendor_status": item.get("Status"),
                    "data_source": item.get("DataSource"),
                }
            )
    counts = {
        level: sum(row["severity"] == level for row in rows)
        for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
    }
    return {
        "status": "FAIL" if counts["HIGH"] or counts["CRITICAL"] else "PASS",
        "gate": "OS_and_language_vulnerabilities",
        "policy": "All HIGH/CRITICAL findings block release, including unfixed; no exceptions or ignore-unfixed",
        "counts": counts,
        "os": report["Metadata"]["OS"],
        "unique_cves": len({r["id"] for r in rows}),
        "affected_packages": len({(r["class"], r["package"]) for r in rows}),
        "by_class": {
            group: {
                "rows": sum(r["class"] == group for r in rows),
                "unique_cves": len({r["id"] for r in rows if r["class"] == group}),
                "packages": len({r["package"] for r in rows if r["class"] == group}),
                "counts": {
                    level: sum(
                        r["class"] == group and r["severity"] == level for r in rows
                    )
                    for level in counts
                },
            }
            for group in sorted({r["class"] for r in rows})
        },
        "findings": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("install-trivy", "scan-image"))
    parser.add_argument("--tool", type=Path, required=True)
    parser.add_argument("--image")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=Path.home() / ".cache/trivy")
    parser.add_argument(
        "--skip-db-update",
        action="store_true",
        help="Use a previously captured DB for comparable scans",
    )
    args = parser.parse_args()
    try:
        if args.operation == "install-trivy":
            install_trivy(args.tool)
            print('{"status":"PASS","gate":"tool_integrity"}')
            return
        lock = json.loads((ROOT / "release/tools.lock.json").read_text())["trivy"]
        if hashlib.sha256(args.tool.read_bytes()).hexdigest() != lock["binary_sha256"]:
            raise ValueError("tool integrity failure")
        args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
        raw = args.output / "image-vulnerabilities.private.json"
        metadata_path = args.cache_dir / "db/metadata.json"
        db_before = metadata_path.read_bytes() if metadata_path.exists() else None
        common = [
            str(args.tool.resolve()),
            "--cache-dir",
            str(args.cache_dir.resolve()),
            "image",
            "--ignorefile",
            "/dev/null",
        ]
        if args.skip_db_update:
            if db_before is None:
                raise ValueError("frozen DB missing")
            common += ["--skip-db-update"]
        result = subprocess.run(
            common
            + [
                "--timeout",
                "5m",
                "--scanners",
                "vuln",
                "--format",
                "json",
                "--output",
                str(raw),
                args.image,
            ],
            capture_output=True,
        )
        if result.returncode:
            raise ValueError("scan unavailable")
        raw.chmod(0o600)
        report = json.loads(raw.read_text())
        summary = summarize(report)
        db_after = metadata_path.read_bytes()
        if args.skip_db_update and db_after != db_before:
            raise ValueError("frozen DB changed")
        summary["provenance"] = {
            "scanner": "Trivy",
            "version": lock["version"],
            "binary_sha256": lock["binary_sha256"],
            "image": report["Metadata"].get("ImageID"),
            "scan_created_at": report.get("CreatedAt"),
            "database": json.loads(db_after),
            "database_sha256": hashlib.sha256(
                (args.cache_dir / "db/trivy.db").read_bytes()
            ).hexdigest(),
            "database_updates_disabled": args.skip_db_update,
            "ignorefile": "/dev/null",
            "ignore_unfixed": False,
            "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        (args.output / "image-vulnerabilities.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        subprocess.run(
            common
            + [
                "--timeout",
                "5m",
                "--format",
                "cyclonedx",
                "--output",
                str(args.output / "sbom.cdx.json"),
                args.image,
            ],
            check=True,
            capture_output=True,
        )
        print(json.dumps({k: v for k, v in summary.items() if k != "findings"}))
        sys.exit(0 if summary["status"] == "PASS" else 1)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(
            '{"status":"FAIL","gate":"vulnerability_scan","reason":"scan unavailable or incomplete; not a clean result"}'
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
