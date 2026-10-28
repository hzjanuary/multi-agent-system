"""Execute inside the runtime image; no credentials or inference required."""

import importlib.util
import os
from pathlib import Path
import sys


def main() -> None:
    root = Path("/app")
    # An absolute mounted script sets sys.path[0] to '/', unlike python -m.
    sys.path.insert(0, str(root))
    from app.definitions import load_registry

    assert os.geteuid() != 0, "runtime must default to an unprivileged user"
    assert (root / "alembic.ini").is_file()
    assert (root / "alembic/versions/029_headless_01.py").is_file()
    assert (root / "app/config/default.env").is_file()
    assert (root / "app/cli.py").is_file()
    assert importlib.util.find_spec("maos_examples.text_review") is not None
    assert load_registry(()).workflows == {}, "examples must be explicitly enabled"
    assert (
        load_registry("maos_examples.text_review").get("text_review").version == "1.0.0"
    )
    for package in (
        "app.tests",
        "app.demo",
        "app.knowledge",
        "app.vectorstore",
        "app.storage",
        "app.price_research",
        "app.outbound",
        "app.llm.clients.fake",
        "qdrant_client",
        "minio",
        "pytest",
        "poetry",
        "pip",
        "ensurepip",
    ):
        assert importlib.util.find_spec(package) is None, package
    for name in (
        "frontend",
        "datasets",
        ".harness-core",
        ".harness-backup",
        ".maos",
        "private.env",
    ):
        assert not (root / name).exists(), name
    for path in (
        "/bin/mount",
        "/usr/bin/mount",
        "/bin/umount",
        "/usr/bin/umount",
        "/usr/local/bin/pip",
        "/usr/local/bin/pip3",
    ):
        assert not Path(path).exists(), path
    print("release-content: PASS")


if __name__ == "__main__":
    main()
