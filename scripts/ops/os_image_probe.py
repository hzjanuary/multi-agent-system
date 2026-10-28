"""Read-only runtime evidence, executed in a network-disabled release container."""

import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess


def main():
    result = subprocess.run(
        [
            "dpkg-query",
            "-W",
            "-f=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\t${Essential}\n",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    packages = []
    for row in result.stdout.splitlines():
        name, version, source, source_version, essential = row.split("\t")
        packages.append(
            {
                "name": name,
                "version": version,
                "source": source,
                "source_version": source_version,
                "essential": essential == "yes",
            }
        )
    paths = (
        "/usr/bin/mount",
        "/usr/bin/umount",
        "/usr/bin/nsenter",
        "/usr/bin/infocmp",
        "/usr/lib/systemd/systemd-homed",
        "/usr/libexec/systemd/systemd-homed",
        "/usr/local/bin/pip",
        "/usr/local/lib/python3.12/ensurepip",
    )
    modules = {}
    for module in ("Archive::Tar", "Pod::Text"):
        modules[module] = (
            subprocess.run(
                ["perl", "-M" + module, "-e", "exit 0"], capture_output=True
            ).returncode
            == 0
        )
    capability_keys = {"CapEff", "CapBnd", "NoNewPrivs"}
    status = {
        key: value.strip()
        for line in Path("/proc/self/status").read_text().splitlines()
        if ":" in line
        for key, value in [line.split(":", 1)]
        if key in capability_keys
    }
    nsenter = subprocess.run(["nsenter", "--help"], capture_output=True, text=True)
    suid = []
    for folder in ("/usr/bin", "/usr/sbin"):
        for path in Path(folder).iterdir():
            if path.is_file() and path.stat().st_mode & stat.S_ISUID:
                suid.append(str(path))
    print(
        json.dumps(
            {
                "uid": os.getuid(),
                "packages": packages,
                "paths": {p: Path(p).exists() for p in paths},
                "perl_modules_loadable": modules,
                "perl_module_files": [
                    str(p)
                    for base in (
                        Path("/usr/share/perl"),
                        Path("/usr/share/perl5"),
                        Path("/usr/lib"),
                    )
                    for pattern in ("**/Archive/Tar.pm", "**/Pod/Text.pm")
                    for p in base.glob(pattern)
                ],
                "pip_importable": importlib.util.find_spec("pip") is not None,
                "python_packages": {
                    d.metadata["Name"]: d.version
                    for d in importlib.metadata.distributions()
                },
                "capabilities": status,
                "nsenter_join_cgroup_option": "--join-cgroup" in nsenter.stdout,
                "setuid_files": sorted(suid),
                "fstab_empty": not Path("/etc/fstab").read_text().strip(),
            }
        )
    )


if __name__ == "__main__":
    main()
