"""Execute inside the actual runtime image; no credentials or inference required."""

import importlib.util
import os
from pathlib import Path

from app.definitions import load_registry

root = Path("/app")
assert os.geteuid() != 0, "runtime must default to an unprivileged user"
assert (root / "alembic.ini").is_file()
assert (root / "alembic/versions/029_headless_01.py").is_file()
assert (root / "app/config/default.env").is_file()
assert (root / "app/cli.py").is_file()
assert importlib.util.find_spec("maos_examples.text_review") is not None
assert load_registry(()).workflows == {}, "examples must be explicitly enabled"
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
):
    assert importlib.util.find_spec(package) is None, package
for name in ("frontend", "datasets", ".harness-core", ".harness-backup"):
    assert not (root / name).exists(), name
print("release-content: PASS")
