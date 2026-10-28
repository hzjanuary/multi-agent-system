"""Test-only nonproduction configuration. Real DB tests require an isolated URL."""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://maos_test:maos-isolated-test-only@127.0.0.1:55429/maos_test",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-8Kx2zHc4Jy9Mnp6Wq1Fv7Ba0Rsd3Ue5L")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:56329/0")
os.environ.setdefault("APP_ENV", "testing")
