#!/usr/bin/env python3
"""Prepare an isolated, opt-in OpenRouter free-route smoke; never auto-run inference."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import shlex
import socket
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from uuid import uuid4

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.ops.live_text_review import read_config

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / ".maos/openrouter-free-smoke"
MODEL = "google/gemma-4-31b-it:free"
CANONICAL = "google/gemma-4-31b-it-20260402"
ADDITIONAL_ID = "gemma26-20261027"
ADDITIONAL_MODEL = "google/gemma-4-26b-a4b-it:free"
ADDITIONAL_CANONICAL = "google/gemma-4-26b-a4b-it-20260403"
PREVIOUS_RUN = "75039b34-2bf1-4e89-a1c1-704dd2f0be28"
ROUTE = "google-ai-studio"
PREFERENCES = {
    "data_collection": "allow",
    "zdr": False,
    "allow_fallbacks": False,
    "require_parameters": True,
    "only": [ROUTE],
    "max_price": {"prompt": 0, "completion": 0, "request": 0},
}
API = "https://openrouter.ai/api/v1"


class Failure(Exception):
    """A safe, bounded error code; never arbitrary process/provider output."""


def check(condition: Any, code: str) -> None:
    if not condition:
        raise Failure(code)


def private_write(path: Path, value: str, *, exclusive: bool = False) -> None:
    if exclusive:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(value)
        return
    check(not path.is_symlink(), "private_file_must_not_be_symlink")
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(value)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    private_write(path, json.dumps(value, indent=2) + "\n", exclusive=exclusive)


def sanitized_environment(config: dict[str, str]) -> dict[str, str]:
    # --env-file does not override the caller's shell. Never reuse its key or
    # Compose overrides, including when preparing a still-blank private key.
    return {
        key: value
        for key, value in os.environ.items()
        if key not in config
        and not key.startswith("COMPOSE_")
        and key not in {"OPENROUTER_API_KEY", "MAOS_AUTH_FILE", "MAOS_API_URL"}
    }


def process(
    arguments: list[str], config: dict[str, str], **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        arguments,
        cwd=ROOT,
        env=sanitized_environment(config),
        text=True,
        capture_output=True,
        check=False,
        **kwargs,
    )
    check(result.returncode == 0, "command_failed_output_withheld")
    return result


def attempt_directory(directory: Path) -> Path:
    pointer = directory / "active-additional.json"
    if not pointer.exists():
        return directory
    check(
        not pointer.is_symlink() and stat.S_IMODE(pointer.stat().st_mode) == 0o600,
        "private_active_pointer_required",
    )
    check(
        json.loads(pointer.read_text()) == {"attempt_id": ADDITIONAL_ID},
        "unknown_additional_attempt",
    )
    target = directory / "attempts" / ADDITIONAL_ID
    check(
        target.is_dir()
        and not target.is_symlink()
        and stat.S_IMODE(target.stat().st_mode) == 0o700,
        "private_attempt_directory_required",
    )
    return target


def compose_arguments(directory: Path, config: dict[str, str]) -> list[str]:
    return [
        "docker",
        "compose",
        "--project-name",
        config["COMPOSE_PROJECT_NAME"],
        "--env-file",
        str(directory / "private.env"),
        "-f",
        str(ROOT / "docker-compose.yml"),
        "-f",
        str(attempt_directory(directory) / "compose.private.json"),
    ]


def available_port() -> int:
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", 58031))
        except OSError:
            listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def prepare(directory: Path, image: str) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    check(not directory.is_symlink(), "private_directory_must_not_be_symlink")
    directory.chmod(0o700)
    check(
        not any(directory.iterdir()),
        "preparation_requires_empty_private_directory_no_overwrites",
    )
    identity = process(
        ["docker", "image", "inspect", image, "--format", "{{.Id}}"], {}
    ).stdout.strip()
    check(
        bool(re.fullmatch(r"sha256:[a-f0-9]{64}", identity)),
        "invalid_local_image_identity",
    )
    revision = process(
        [
            "docker",
            "image",
            "inspect",
            identity,
            "--format",
            '{{index .Config.Labels "org.opencontainers.image.revision"}}',
        ],
        {},
    ).stdout.strip()
    check(
        bool(re.fullmatch(r"[a-f0-9]{40}", revision)), "source_revision_label_required"
    )
    process(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--volume",
            f"{directory}:/config",
            "--entrypoint",
            "python",
            identity,
            "-m",
            "app.cli",
            "config",
            "init",
            "--output",
            "/config/private.env",
        ],
        {},
    )
    config = read_config(directory / "private.env")
    suffix = uuid4().hex[:12]
    config.update(
        {
            "COMPOSE_PROJECT_NAME": "maos-or-free-" + suffix,
            "POSTGRES_DB": "maos_or_free_" + suffix,
            "POSTGRES_USER": "maos_or_free_" + suffix,
            "MAOS_UID": str(os.getuid()),
            "MAOS_GID": str(os.getgid()),
            "MAOS_API_PORT": str(available_port()),
            "LLM_PROVIDER": "openrouter",
            "LLM_MODEL": MODEL,
            "OPENROUTER_API_KEY": "",
            "OPENROUTER_PROVIDER_PREFERENCES": json.dumps(
                PREFERENCES, separators=(",", ":")
            ),
            "OPENAI_COMPATIBLE_API_KEY": "",
            "GROQ_API_KEY": "",
            "GEMINI_API_KEY": "",
            "LLM_MAX_RETRIES": "0",
            "LLM_MAX_OUTPUT_TOKENS": "1024",
            "MAX_PROVIDER_CALLS": "2",
            "MAOS_EXTENSION_MODULES": "maos_examples.text_review",
            "LOG_REDACTION_ENABLED": "true",
            "LOG_LEVEL": "INFO",
        }
    )
    config["DATABASE_URL"] = (
        f"postgresql+asyncpg://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}"
        f"@postgres:5432/{config['POSTGRES_DB']}"
    )
    private_write(
        directory / "private.env",
        "".join(f"{key}={shlex.quote(value)}\n" for key, value in config.items()),
    )
    (directory / "cli").mkdir(exist_ok=True, mode=0o700)
    (directory / "cli").chmod(0o700)
    overlay = {
        "services": {
            service: {"image": identity, "pull_policy": "never"}
            for service in ("api", "worker", "cli")
        }
    }
    overlay["services"]["cli"]["volumes"] = [f"{directory / 'cli'}:/cli"]
    save_json(directory / "compose.private.json", overlay, exclusive=True)
    private_write(directory / "input.txt", "", exclusive=True)
    manifest = {
        "image_id": identity,
        "image_tag": image,
        "source_revision": revision,
        "project": config["COMPOSE_PROJECT_NAME"],
        "model": MODEL,
        "route": ROUTE,
    }
    save_json(directory / "manifest.json", manifest, exclusive=True)
    return {
        "status": "PREPARED",
        "project": manifest["project"],
        "image_id": identity,
        "source_revision": revision,
        "key_present": False,
        "inference": "NOT_RUN",
    }


def load_private(directory: Path) -> tuple[dict[str, str], dict[str, Any]]:
    check(
        directory.is_dir() and not directory.is_symlink(), "private_directory_required"
    )
    check(
        stat.S_IMODE(directory.stat().st_mode) == 0o700,
        "private_directory_requires_0700",
    )
    for name in ("private.env", "manifest.json", "compose.private.json", "input.txt"):
        path = directory / name
        check(
            path.is_file()
            and not path.is_symlink()
            and stat.S_IMODE(path.stat().st_mode) == 0o600,
            "private_files_require_0600",
        )
    config = read_config(directory / "private.env")
    target = attempt_directory(directory)
    for name in ("manifest.json", "compose.private.json"):
        file = target / name
        check(
            not file.is_symlink() and stat.S_IMODE(file.stat().st_mode) == 0o600,
            "private_active_files_required",
        )
    manifest = json.loads((target / "manifest.json").read_text())
    selected_model = ADDITIONAL_MODEL if target != directory else MODEL
    if target != directory:
        check(
            manifest.get("attempt_id") == ADDITIONAL_ID
            and manifest.get("previous_run_id") == PREVIOUS_RUN
            and manifest.get("previous_consumed") == 1
            and manifest.get("cumulative_max") == 3,
            "additional_budget_identity_changed",
        )
    check(
        manifest["model"] == selected_model and manifest["route"] == ROUTE,
        "fixed_selection_changed",
    )
    check(
        config["COMPOSE_PROJECT_NAME"] == manifest["project"]
        and bool(re.fullmatch(r"maos-or-free-[a-f0-9]{12}", manifest["project"])),
        "dedicated_project_required",
    )
    expected = {
        "LLM_PROVIDER": "openrouter",
        "LLM_MODEL": selected_model,
        "LLM_MAX_RETRIES": "0",
        "LLM_MAX_OUTPUT_TOKENS": "1024",
        "MAX_PROVIDER_CALLS": "2",
        "MAOS_EXTENSION_MODULES": "maos_examples.text_review",
        "LOG_REDACTION_ENABLED": "true",
    }
    check(
        all(config.get(key) == value for key, value in expected.items()),
        "private_budget_or_selection_changed",
    )
    check(
        json.loads(config["OPENROUTER_PROVIDER_PREFERENCES"]) == PREFERENCES,
        "private_routing_policy_changed",
    )
    check(
        config["POSTGRES_DB"] == manifest["project"].replace("-", "_")
        and config["POSTGRES_USER"] == config["POSTGRES_DB"],
        "dedicated_database_required",
    )
    check(
        config["DATABASE_URL"]
        == f"postgresql+asyncpg://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}@postgres:5432/{config['POSTGRES_DB']}",
        "dedicated_database_url_required",
    )
    return config, manifest


def get_public(path: str) -> dict[str, Any]:
    request = Request(API + path, method="GET", headers={"Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        check(response.geturl() == API + path, "metadata_redirect_rejected")
        raw = response.read(16 * 1024 * 1024 + 1)
    check(len(raw) <= 16 * 1024 * 1024, "metadata_response_too_large")
    value = json.loads(raw)
    check(isinstance(value, dict), "invalid_public_metadata")
    return value


def zero_price(pricing: dict[str, Any], field: str, *, optional: bool = False) -> bool:
    if optional and field not in pricing:
        return True
    try:
        return (
            not isinstance(pricing.get(field), bool)
            and Decimal(str(pricing[field])).is_finite()
            and Decimal(str(pricing[field])) == 0
        )
    except (KeyError, InvalidOperation, ValueError):
        return False


def validate_metadata(
    catalog: dict[str, Any],
    details: dict[str, Any],
    endpoints: dict[str, Any],
    *,
    model_id: str = MODEL,
    canonical: str = CANONICAL,
) -> dict[str, Any]:
    models = [entry for entry in catalog["data"] if entry.get("id") == model_id]
    check(len(models) == 1, "fixed_free_model_missing_or_ambiguous")
    detail, data = details["data"], endpoints["data"]
    check(
        detail["id"] == model_id and data["id"] == model_id,
        "metadata_resolved_to_different_variant",
    )
    for model in (models[0], detail):
        check(
            model.get("canonical_slug") == canonical, "verified_canonical_model_changed"
        )
        check(
            all(
                zero_price(model["pricing"], field)
                for field in ("prompt", "completion")
            ),
            "free_variant_model_pricing_changed",
        )
        check(
            zero_price(model["pricing"], "request", optional=True),
            "nonzero_model_request_price",
        )
        check(
            "text" in model["architecture"]["output_modalities"], "text_output_required"
        )
        check(
            set(("max_tokens", "temperature", "response_format"))
            <= set(model["supported_parameters"]),
            "model_required_parameters_missing",
        )
    check(
        detail.get("reasoning", {}).get("mandatory") is False
        and detail.get("reasoning", {}).get("default_enabled") is False,
        "reasoning_must_explicitly_be_optional",
    )
    matches = [
        entry
        for entry in data["endpoints"]
        if entry.get("tag", "").split(":", 1)[0].split("/", 1)[0] == ROUTE
    ]
    check(
        len(matches) == 1 and matches[0]["tag"] == ROUTE,
        "provider_prefix_is_ambiguous_or_unavailable",
    )
    route = matches[0]
    check(route.get("provider_name") == "Google AI Studio", "verified_provider_changed")
    check(route.get("status") == 0, "selected_route_unavailable")
    check(
        all(zero_price(route["pricing"], field) for field in ("prompt", "completion")),
        "selected_route_no_longer_free",
    )
    check(
        zero_price(route["pricing"], "request", optional=True),
        "nonzero_route_request_price",
    )
    check(
        set(("max_tokens", "temperature", "response_format"))
        <= set(route["supported_parameters"]),
        "route_required_parameters_missing",
    )
    check(
        route.get("max_completion_tokens", 0) >= 1024
        and route.get("context_length", 0) >= 16384,
        "route_token_capacity_insufficient",
    )
    return {
        "model": model_id,
        "route": ROUTE,
        "prompt_price": "0",
        "completion_price": "0",
        "request_price": route["pricing"].get(
            "request", "unknown_omitted_for_free_variant"
        ),
        "response_format": "json_object",
        "reasoning_mandatory": False,
    }


def resolved_compose(
    directory: Path,
    config: dict[str, str],
    manifest: dict[str, Any],
    *,
    running: bool = False,
) -> None:
    resolved = json.loads(
        process(
            compose_arguments(directory, config)
            + ["--profile", "cli", "config", "--format", "json"],
            config,
        ).stdout
    )
    check(resolved["name"] == manifest["project"], "compose_project_mismatch")
    for name in ("api", "worker", "cli"):
        service = resolved["services"][name]
        check(service["image"] == manifest["image_id"], "compose_image_not_pinned")
        check(
            all(
                service["environment"].get(key) == value
                for key, value in config.items()
                if key in service["environment"]
            ),
            "compose_environment_mismatch",
        )
        for key in (
            "OPENROUTER_PROVIDER_PREFERENCES",
            "OPENROUTER_API_KEY",
            "DATABASE_URL",
            "LLM_MODEL",
            "MAX_PROVIDER_CALLS",
            "LLM_MAX_RETRIES",
            "LLM_MAX_OUTPUT_TOKENS",
        ):
            check(
                service["environment"].get(key) == config[key],
                "required_compose_environment_missing",
            )
        mounts = service.get("volumes", [])
        if name == "cli":
            check(
                len(mounts) == 1
                and mounts[0]["target"] == "/cli"
                and Path(mounts[0]["source"]).resolve() == directory / "cli",
                "cli_credentials_not_isolated",
            )
        else:
            check(not mounts, "runtime_must_not_mount_operator_credentials")
        if running and name in ("api", "worker"):
            ids = process(
                compose_arguments(directory, config) + ["ps", "-q", name], config
            ).stdout.split()
            check(len(ids) == 1, "dedicated_runtime_service_required")
            actual = json.loads(process(["docker", "inspect", ids[0]], config).stdout)[
                0
            ]
            check(
                actual["Image"] == manifest["image_id"] and actual["State"]["Running"],
                "running_image_mismatch",
            )
            check(not actual.get("Mounts"), "running_runtime_has_unexpected_mounts")
            actual_env = dict(
                value.split("=", 1) for value in actual["Config"]["Env"] if "=" in value
            )
            check(
                all(
                    actual_env.get(key) == value
                    for key, value in service["environment"].items()
                ),
                "running_environment_mismatch_recreate_services",
            )
    ports = resolved["services"]["api"]["ports"]
    check(
        len(ports) == 1
        and ports[0].get("host_ip") == "127.0.0.1"
        and str(ports[0]["published"]) == config["MAOS_API_PORT"],
        "private_loopback_port_required",
    )
    volume = resolved["volumes"]["maos_postgres_data"]["name"]
    check(
        volume == manifest["project"] + "_maos_postgres_data",
        "dedicated_database_volume_required",
    )
    storage = resolved["services"]["postgres"].get("volumes", [])
    check(
        len(storage) == 1
        and storage[0].get("type") == "volume"
        and storage[0].get("source") == "maos_postgres_data"
        and storage[0].get("target") == "/var/lib/postgresql/data",
        "postgres_must_use_only_dedicated_volume",
    )
    check(
        resolved["services"]["postgres"]["environment"].get("POSTGRES_DB")
        == config["POSTGRES_DB"]
        and resolved["services"]["postgres"]["environment"].get("POSTGRES_USER")
        == config["POSTGRES_USER"],
        "postgres_identity_mismatch",
    )
    if running:
        ids = process(
            compose_arguments(directory, config) + ["ps", "-q", "postgres"], config
        ).stdout.split()
        check(len(ids) == 1, "dedicated_postgres_required")
        database = json.loads(process(["docker", "inspect", ids[0]], config).stdout)[0]
        mounts = database.get("Mounts", [])
        check(
            database["State"]["Running"]
            and len(mounts) == 1
            and mounts[0].get("Type") == "volume"
            and mounts[0].get("Name") == volume
            and mounts[0].get("Destination") == "/var/lib/postgresql/data",
            "running_postgres_volume_not_isolated",
        )


def preflight(
    directory: Path, *, metadata_only: bool = False, running: bool = False
) -> dict[str, Any]:
    config, manifest = load_private(directory)
    check(
        metadata_only or bool(config.get("OPENROUTER_API_KEY", "").strip()),
        "enter_private_key_locally_first",
    )
    resolved_compose(directory, config, manifest, running=running)
    target = attempt_directory(directory)
    model = manifest["model"]
    canonical = ADDITIONAL_CANONICAL if target != directory else CANONICAL
    snapshot = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "catalog": get_public("/models"),
        "details": get_public("/model/" + model),
        "endpoints": get_public("/models/" + model + "/endpoints"),
    }
    # Public raw metadata only; never credentials or resolved Compose output.
    save_json(target / "public-metadata.json", snapshot)
    result = validate_metadata(
        snapshot["catalog"],
        snapshot["details"],
        snapshot["endpoints"],
        model_id=model,
        canonical=canonical,
    )
    result.update(
        {
            "status": "PREFLIGHT_PASS",
            "key_present": bool(config.get("OPENROUTER_API_KEY")),
            "inference": "NOT_RUN",
        }
    )
    save_json(target / "preflight.json", result)
    return result


def prepare_additional(directory: Path, image: str, authorized: bool) -> dict[str, Any]:
    """One explicit continuation slot, not an arbitrary repeat-attempt factory."""
    check(authorized, "explicit_two_additional_call_authorization_required")
    check(
        not (directory / "active-additional.json").exists(),
        "additional_attempt_already_prepared",
    )
    config, old_manifest = load_private(directory)
    old = json.loads((directory / "api-evidence.json").read_text())["run"]
    check(
        old["id"] == PREVIOUS_RUN
        and old["status"] == "FAILED"
        and old["call_count"] == 1,
        "previous_run_evidence_mismatch",
    )
    proof = json.loads((ROOT / "docs/release/openrouter-live-attempt.json").read_text())
    for artifact in proof["private_artifacts"]:
        check(
            hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest()
            == artifact["sha256"],
            "historical_evidence_changed",
        )
    quota = json.loads(
        (directory / "quota-correction-20261027/sanitized.json").read_text()
    )
    check(
        quota.get("free_request_quota") != "INSUFFICIENT_FOR_TWO",
        "insufficient_free_request_quota",
    )
    rows = process(
        compose_arguments(directory, config) + ["ps", "--all", "--format", "json"],
        config,
    ).stdout.splitlines()
    check(
        all(json.loads(line)["State"] == "exited" for line in rows if line.strip()),
        "stop_isolated_services_before_profile_change",
    )
    identity = process(
        ["docker", "image", "inspect", image, "--format", "{{.Id}}"], config
    ).stdout.strip()
    revision = process(
        [
            "docker",
            "image",
            "inspect",
            identity,
            "--format",
            '{{index .Config.Labels "org.opencontainers.image.revision"}}',
        ],
        config,
    ).stdout.strip()
    check(
        bool(re.fullmatch(r"sha256:[a-f0-9]{64}", identity))
        and bool(re.fullmatch(r"[a-f0-9]{40}", revision)),
        "source_labeled_local_image_required",
    )
    parent = directory / "attempts"
    parent.mkdir(mode=0o700, exist_ok=True)
    check(
        not parent.is_symlink() and stat.S_IMODE(parent.stat().st_mode) == 0o700,
        "private_attempt_parent_required",
    )
    target = parent / ADDITIONAL_ID
    target.mkdir(mode=0o700, exist_ok=False)
    manifest = {
        **old_manifest,
        "attempt_id": ADDITIONAL_ID,
        "model": ADDITIONAL_MODEL,
        "image_id": identity,
        "image_tag": image,
        "source_revision": revision,
        "previous_run_id": PREVIOUS_RUN,
        "previous_consumed": 1,
        "cumulative_max": 3,
    }
    save_json(
        target / "authorization.json",
        {
            **manifest,
            "additional_call_limit": 2,
            "old_attempt_sha256": hashlib.sha256(
                (directory / "attempt.json").read_bytes()
            ).hexdigest(),
            "quota_snapshot": quota,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        exclusive=True,
    )
    save_json(target / "manifest.json", manifest, exclusive=True)
    overlay = {
        "services": {
            name: {"image": identity, "pull_policy": "never"}
            for name in ("api", "worker", "cli")
        }
    }
    overlay["services"]["cli"]["volumes"] = [f"{directory / 'cli'}:/cli"]
    save_json(target / "compose.private.json", overlay, exclusive=True)
    config["LLM_MODEL"] = ADDITIONAL_MODEL
    private_write(
        directory / "private.env",
        "".join(f"{name}={shlex.quote(value)}\n" for name, value in config.items()),
    )
    save_json(
        directory / "active-additional.json",
        {"attempt_id": ADDITIONAL_ID},
        exclusive=True,
    )
    resolved_compose(directory, config, manifest)
    return {
        "status": "PREPARED",
        "attempt_id": ADDITIONAL_ID,
        "additional_call_limit": 2,
        "previous_consumed": 1,
        "cumulative_max": 3,
        "source_revision": revision,
        "image_id": identity,
        "inference": "NOT_RUN",
    }


def set_key(directory: Path) -> dict[str, Any]:
    config, _ = load_private(directory)
    check(
        not (directory / "attempt.json").exists(),
        "attempt_already_reserved_never_reset_budget",
    )
    key = getpass.getpass("Dedicated OpenRouter key (hidden, stored privately): ")
    check(
        bool(key.strip()) and not any(char.isspace() for char in key),
        "invalid_key_format",
    )
    config["OPENROUTER_API_KEY"] = key
    private_write(
        directory / "private.env",
        "".join(f"{name}={shlex.quote(value)}\n" for name, value in config.items()),
    )
    return {
        "status": "KEY_STORED",
        "inference": "NOT_RUN",
        "next": "recreate_api_and_worker_then_preflight",
    }


def run_once(directory: Path, approve: bool) -> dict[str, Any]:
    target = attempt_directory(directory)
    check(approve, "explicit_run_approval_required")
    check(
        not (target / "attempt.json").exists(),
        "attempt_already_reserved_never_reset_budget",
    )
    preflight(directory, running=True)
    config, manifest = load_private(directory)
    auth = directory / "cli/auth.json"
    check(
        auth.is_file()
        and not auth.is_symlink()
        and stat.S_IMODE(auth.stat().st_mode) == 0o600,
        "private_cli_login_required",
    )
    text = (directory / "input.txt").read_text()
    check(
        bool(text.strip()) and len(text) <= 16000,
        "user_input_required_1_to_16000_characters",
    )
    attempt = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "project": manifest["project"],
        "model": manifest.get("model", MODEL),
        "attempt_id": manifest.get("attempt_id", "original"),
        "image_id": manifest.get("image_id"),
        "source_revision": manifest.get("source_revision"),
        "previous_run_id": manifest.get("previous_run_id"),
        "previous_consumed": manifest.get("previous_consumed", 0),
        "cumulative_max": manifest.get("cumulative_max", 2),
        "route": ROUTE,
        "max_calls": 2,
        "max_output_tokens": 1024,
        "retry": False,
    }
    save_json(target / "attempt.json", attempt, exclusive=True)
    # Permanent reservation precedes the only invocation. A failure/crash is not
    # permission to reset the two-call budget or replay this command.
    with open(
        target / "live.stdout.json",
        "x",
        opener=lambda path, flags: os.open(path, flags | os.O_NOFOLLOW, 0o600),
    ) as stdout, open(
        target / "live.stderr.json",
        "x",
        opener=lambda path, flags: os.open(path, flags | os.O_NOFOLLOW, 0o600),
    ) as stderr:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/ops/live_text_review.py"),
                "--api-url",
                "http://127.0.0.1:" + config["MAOS_API_PORT"],
                "--env-file",
                str(directory / "private.env"),
                "--auth-file",
                str(auth),
                "--input",
                str(directory / "input.txt"),
                "--enable-remote",
                "--approve",
                "--max-calls",
                "2",
                "--max-output-tokens",
                "1024",
            ],
            cwd=ROOT,
            env=sanitized_environment(config),
            text=True,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    result = {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "attempt_retained": True,
        "evidence": "private live.stdout.json and live.stderr.json",
        "inference": "ATTEMPTED",
    }
    result["api_evidence"] = collect_evidence(target, config, auth)
    save_json(target / "outcome.json", result)
    return result


def collect_evidence(directory: Path, config: dict[str, str], auth: Path) -> str:
    """GET-only post-attempt evidence, including partial failures; never replay."""
    try:
        messages = []
        for name in ("live.stdout.json", "live.stderr.json"):
            for line in (directory / name).read_text().splitlines():
                try:
                    messages.append(json.loads(line))
                except ValueError:
                    continue
        run_ids = {
            message.get("run_id")
            for message in messages
            if isinstance(message, dict) and message.get("run_id")
        }
        if len(run_ids) != 1:
            return "no_run_id_observed"
        run_id = run_ids.pop()
        check(
            bool(re.fullmatch(r"[a-fA-F0-9-]{36}", run_id)), "invalid_observed_run_id"
        )
        token = json.loads(auth.read_text())["access_token"]
        evidence = {}
        incomplete = False
        for suffix in (
            "",
            "/nodes",
            "/events?after_sequence=0&limit=500",
            "/approvals",
        ):
            request = Request(
                "http://127.0.0.1:"
                + config["MAOS_API_PORT"]
                + "/api/v1/runs/"
                + run_id
                + suffix,
                method="GET",
                headers={
                    "Authorization": "Bearer " + token,
                    "Accept": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    raw = response.read(2097153)
                check(len(raw) <= 2097152, "api_evidence_too_large")
                evidence[suffix or "run"] = json.loads(raw)
            except (OSError, Failure, ValueError, TypeError) as error:
                incomplete = True
                evidence[suffix or "run"] = {
                    "status": "UNAVAILABLE",
                    "code": type(error).__name__,
                }
        save_json(directory / "api-evidence.json", evidence, exclusive=True)
        return (
            "saved_privately_partial"
            if incomplete
            else "saved_privately_may_contain_user_text"
        )
    except (OSError, Failure, ValueError, KeyError, TypeError):
        return "unavailable_no_retry"


def safe_compose_arguments(arguments: list[str]) -> list[str]:
    """Allow operator lifecycle/CLI commands without changing the isolation."""
    prefix = []
    if arguments[:2] == ["--profile", "cli"]:
        prefix, arguments = arguments[:2], arguments[2:]
    check(
        bool(arguments) and arguments[0] in {"up", "stop", "down", "ps", "run", "exec"},
        "compose_command_not_allowed",
    )
    forbidden = {
        "-v",
        "--volumes",
        "--build",
        "--pull",
        "--env",
        "-e",
        "--env-file",
        "--env-from-file",
        "--volume",
        "--entrypoint",
        "--name",
        "--publish",
        "-p",
        "--project-name",
        "-f",
        "--file",
        "--project-directory",
        "--rmi",
        "--user",
        "-u",
        "--privileged",
        "--cap-add",
        "--device",
        "--service-ports",
        "--scale",
        "--attach",
        "--attach-dependencies",
    }
    check(
        not any(
            argument.split("=", 1)[0] in forbidden
            or (
                len(argument) > 2
                and argument[:2] in {"-e", "-v", "-p", "-f", "-u"}
                and not argument.startswith("--")
            )
            for argument in arguments
        ),
        "compose_override_or_volume_deletion_forbidden",
    )
    if arguments[0] == "up":
        arguments = [arguments[0], "--no-build", *arguments[1:]]
    elif arguments[0] == "run":
        # Compose run has no --no-build flag. The existing immutable local image,
        # pull_policy=never and forbidden --build prevent a replacement build.
        arguments = [arguments[0], "--pull", "never", *arguments[1:]]
    return prefix + arguments


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=PRIVATE)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare").add_argument("--image", required=True)
    additional = commands.add_parser("prepare-additional")
    additional.add_argument("--image", required=True)
    additional.add_argument("--authorize-two-additional", action="store_true")
    commands.add_parser("preflight").add_argument(
        "--metadata-only", action="store_true"
    )
    commands.add_parser("set-key")
    commands.add_parser("run").add_argument("--approve", action="store_true")
    compose = commands.add_parser("compose")
    compose.add_argument("--profile", choices=["cli"])
    compose.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        directory = args.directory.absolute()
        check(directory == PRIVATE, "fixed_private_directory_required")
        if args.command == "prepare":
            result = prepare(directory, args.image)
        elif args.command == "prepare-additional":
            result = prepare_additional(
                directory, args.image, args.authorize_two_additional
            )
        elif args.command == "preflight":
            result = preflight(directory, metadata_only=args.metadata_only)
        elif args.command == "set-key":
            result = set_key(directory)
        elif args.command == "run":
            result = run_once(directory, args.approve)
        else:
            config, manifest = load_private(directory)
            resolved_compose(directory, config, manifest)
            arguments = safe_compose_arguments(
                (["--profile", "cli"] if args.profile else []) + args.arguments
            )
            code = subprocess.run(
                compose_arguments(directory, config) + arguments,
                cwd=ROOT,
                env=sanitized_environment(config),
                check=False,
            ).returncode
            return code
        print(json.dumps(result))
        return 1 if result["status"] == "FAIL" else 0
    except (Failure, OSError, KeyError, ValueError, TypeError) as error:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "code": (
                        str(error)
                        if isinstance(error, Failure)
                        else type(error).__name__
                    ),
                    "inference": "NOT_AUTOMATICALLY_RETRIED",
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
