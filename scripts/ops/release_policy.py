"""Shared deny rules for committed and distributed paths; not an ignore mechanism."""

from pathlib import PurePosixPath

SAFE_ENV_TEMPLATES = {
    ".env.example",
    "backend/.env.example",
    "backend/app/config/default.env",
}
PRIVATE_PARTS = {
    ".git",
    ".maos",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "node_modules",
    "private-evidence",
    ".private",
}
PRIVATE_NAMES = {
    "private.env",
    "auth.json",
    "credentials.json",
    "token.json",
    "tokens.json",
    ".netrc",
    ".pgpass",
    ".git-credentials",
    "id_rsa",
    "id_ed25519",
    "docker-compose.override.yml",
}
PRIVATE_SUFFIXES = {
    ".dump",
    ".pgdump",
    ".backup",
    ".bak",
    ".bkp",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".sql",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}
BUILD_FILES = {
    "LICENSE",
    "NOTICE",
    "backend/Dockerfile",
    "backend/pyproject.toml",
    "backend/poetry.lock",
    "backend/alembic.ini",
    "scripts/ops/license_inventory.py",
}
BUILD_PREFIXES = (
    "backend/app/",
    "backend/maos_examples/",
    "backend/alembic/",
    "release/third-party/",
)


def prohibited_path(path: str) -> str | None:
    p = PurePosixPath(path)
    if (
        not path
        or p.is_absolute()
        or "\\" in path
        or any(ord(c) < 32 for c in path)
        or ".." in p.parts
        or p.as_posix() != path
    ):
        return "unsafe_path"
    parts = {v.lower() for v in p.parts}
    name = p.name.lower()
    if parts & PRIVATE_PARTS:
        return "private_directory"
    if path in SAFE_ENV_TEMPLATES:
        return None
    if (
        name in PRIVATE_NAMES
        or name.startswith(".env")
        or name.endswith(".env")
        or ".private." in name
    ):
        return "private_configuration"
    if p.suffix.lower() in PRIVATE_SUFFIXES or name.endswith(
        (".sql.gz", ".dump.gz", ".tar.gpg", ".dump.age")
    ):
        return "private_export_or_key"
    if name.endswith((".pyc", ".pyo")):
        return "compiled_cache"
    return None


def build_input(path: str) -> bool:
    return path in BUILD_FILES or path.startswith(BUILD_PREFIXES)
