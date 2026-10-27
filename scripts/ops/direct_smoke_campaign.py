#!/usr/bin/env python3
"""Opt-in, single-use Groq -> Cloudflare whole-workflow campaign; preparation is inert."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import UUID, uuid4

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.ops import openrouter_free_smoke as common

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / ".maos/direct-smoke"
ORDER = ("groq-smoke", "cloudflare-smoke")
MODELS = {
    "groq-smoke": "openai/gpt-oss-20b",
    "cloudflare-smoke": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
}
HISTORICAL_RUNS = (
    "75039b34-2bf1-4e89-a1c1-704dd2f0be28",
    "ea28e301-a82b-48d1-9be8-5fa34e215601",
)
CREDENTIALS = (
    "OPENROUTER_API_KEY",
    "GROQ_API_KEY",
    "OPENAI_COMPATIBLE_API_KEY",
    "GEMINI_API_KEY",
)
METADATA_USER_AGENT = "Multi-Agent-OS/SPEC-029-metadata-preflight"
check, Failure, save = common.check, common.Failure, common.save_json


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_env(path, config):
    common.private_write(
        path, "".join(f"{k}={shlex.quote(v)}\n" for k, v in config.items())
    )


def history_artifacts():
    result = {}
    for name in ("openrouter-live-attempt.json", "openrouter-additional-attempt.json"):
        evidence = ROOT / "docs/release" / name
        proof = json.loads(evidence.read_text())
        for entry in proof["private_artifacts"]:
            path = ROOT / entry["path"]
            check(
                digest(path.read_bytes()) == entry["sha256"],
                "historical_evidence_changed",
            )
            result[entry["path"]] = entry["sha256"]
    return result


def application_binding(config):
    keys = (
        "DATABASE_URL",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "JWT_SECRET_KEY",
        "JWT_ALGORITHM",
        "MAOS_API_PORT",
        "MAOS_UID",
        "MAOS_GID",
    )
    return digest(
        json.dumps({k: config.get(k, "") for k in keys}, sort_keys=True).encode()
    )


def prepare(image):
    check(not PRIVATE.exists(), "campaign_already_prepared_no_overwrite")
    base, _ = common.load_private(common.PRIVATE)
    artifacts = history_artifacts()
    rows = common.process(
        common.compose_arguments(common.PRIVATE, base)
        + ["ps", "--all", "--format", "json"],
        base,
    ).stdout.splitlines()
    check(
        all(json.loads(v)["State"] == "exited" for v in rows if v.strip()),
        "stop_isolated_services_first",
    )
    image_id = common.process(
        ["docker", "image", "inspect", image, "--format", "{{.Id}}"], base
    ).stdout.strip()
    revision = common.process(
        [
            "docker",
            "image",
            "inspect",
            image_id,
            "--format",
            '{{index .Config.Labels "org.opencontainers.image.revision"}}',
        ],
        base,
    ).stdout.strip()
    check(
        bool(re.fullmatch(r"sha256:[a-f0-9]{64}", image_id))
        and bool(re.fullmatch(r"[a-f0-9]{40}", revision)),
        "source_labeled_image_required",
    )
    PRIVATE.mkdir(mode=0o700)
    for name in ORDER:
        folder = PRIVATE / name
        folder.mkdir(mode=0o700)
        config = dict(base)
        for key in CREDENTIALS:
            config[key] = ""
        config.update(
            LLM_MODEL=MODELS[name],
            LLM_MAX_RETRIES="0",
            LLM_MAX_OUTPUT_TOKENS="1024",
            MAX_PROVIDER_CALLS="2",
            OPENROUTER_PROVIDER_PREFERENCES="",
            GROQ_REASONING_EFFORT="",
            OPENAI_COMPATIBLE_BASE_URL="",
            CLOUDFLARE_ACCOUNT_ID="",
        )
        config["LLM_PROVIDER"] = "groq" if name == ORDER[0] else "openai_compatible"
        if name == ORDER[0]:
            config["GROQ_REASONING_EFFORT"] = "low"
        write_env(folder / "private.env", config)
    manifest = {
        "source": revision,
        "image_id": image_id,
        "image_tag": image,
        "project": base["COMPOSE_PROJECT_NAME"],
        "application_binding": application_binding(base),
        "cli_directory": str(common.PRIVATE / "cli"),
        "input_file": str(common.PRIVATE / "input.txt"),
        "input_sha256": digest((common.PRIVATE / "input.txt").read_bytes()),
        "historical_consumed": 2,
        "historical_runs": list(HISTORICAL_RUNS),
        "historical_artifacts": artifacts,
        "per_provider_limit": 2,
        "new_limit": 4,
        "cumulative_limit": 6,
        "order": list(ORDER),
    }
    save(PRIVATE / "manifest.json", manifest, exclusive=True)
    overlay = {
        "services": {
            k: {"image": image_id, "pull_policy": "never"}
            for k in ("api", "worker", "cli")
        }
    }
    overlay["services"]["cli"]["volumes"] = [f'{common.PRIVATE / "cli"}:/cli']
    save(PRIVATE / "compose.private.json", overlay, exclusive=True)
    return {
        "status": "PREPARED",
        "source": revision,
        "image_id": image_id,
        "credentials": "unset",
        "generation_requests": 0,
    }


def manifest():
    check(
        PRIVATE.is_dir()
        and not PRIVATE.is_symlink()
        and stat.S_IMODE(PRIVATE.stat().st_mode) == 0o700,
        "private_campaign_directory_required",
    )
    value = json.loads((PRIVATE / "manifest.json").read_text())
    check(
        value["order"] == list(ORDER)
        and value["per_provider_limit"] == 2
        and value["new_limit"] == 4
        and value["cumulative_limit"] == 6
        and value["historical_consumed"] == 2,
        "campaign_budget_identity_changed",
    )
    check(value["historical_runs"] == list(HISTORICAL_RUNS), "historical_links_changed")
    for path, checksum in value["historical_artifacts"].items():
        check(
            digest((ROOT / path).read_bytes()) == checksum,
            "historical_evidence_changed",
        )
    return value


def config_for(name, *, ready=False):
    check(name in ORDER, "unknown_profile")
    m = manifest()
    path = PRIVATE / name / "private.env"
    check(
        not path.is_symlink() and stat.S_IMODE(path.stat().st_mode) == 0o600,
        "private_env_requires_0600",
    )
    c = common.read_config(path)
    expected = {
        "LLM_PROVIDER": "groq" if name == ORDER[0] else "openai_compatible",
        "LLM_MODEL": MODELS[name],
        "LLM_MAX_RETRIES": "0",
        "MAX_PROVIDER_CALLS": "2",
        "LLM_MAX_OUTPUT_TOKENS": "1024",
        "MAOS_EXTENSION_MODULES": "maos_examples.text_review",
        "OPENROUTER_API_KEY": "",
        "OPENROUTER_PROVIDER_PREFERENCES": "",
        "GEMINI_API_KEY": "",
        "GROQ_REASONING_EFFORT": "low" if name == ORDER[0] else "",
    }
    check(
        all(c.get(k) == v for k, v in expected.items()),
        "profile_policy_or_budget_changed",
    )
    check(c["COMPOSE_PROJECT_NAME"] == m["project"], "isolated_project_changed")
    check(
        application_binding(c) == m["application_binding"],
        "existing_database_or_auth_configuration_changed",
    )
    if name == ORDER[0]:
        check(
            c["OPENAI_COMPATIBLE_API_KEY"] == ""
            and c["OPENAI_COMPATIBLE_BASE_URL"] == ""
            and c["CLOUDFLARE_ACCOUNT_ID"] == "",
            "groq_profile_has_foreign_credentials",
        )
        key = c["GROQ_API_KEY"]
    else:
        check(c["GROQ_API_KEY"] == "", "cloudflare_profile_has_groq_credential")
        account = c["CLOUDFLARE_ACCOUNT_ID"]
        check(
            not account or bool(re.fullmatch(r"[a-fA-F0-9]{32}", account)),
            "invalid_cloudflare_account_id",
        )
        expected_base = (
            f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1"
            if account
            else ""
        )
        check(
            c["OPENAI_COMPATIBLE_BASE_URL"] == expected_base,
            "cloudflare_endpoint_not_pinned",
        )
        key = c["OPENAI_COMPATIBLE_API_KEY"]
    if ready:
        check(
            bool(key.strip())
            and (name == ORDER[0] or bool(c["CLOUDFLARE_ACCOUNT_ID"])),
            "enter_both_provider_credentials_locally_first",
        )
        plan = json.loads((PRIVATE / name / "plan.json").read_text())
        check(
            plan["plan"] == ("GROQ_FREE" if name == ORDER[0] else "WORKERS_FREE"),
            "free_plan_required",
        )
        check(
            plan["binding"] == digest((key + c["CLOUDFLARE_ACCOUNT_ID"]).encode()),
            "reconfirm_free_plan_for_changed_credentials",
        )
    return c


def credentials():
    check(not (PRIVATE / "campaign.json").exists(), "campaign_already_reserved")
    groq, cf = config_for(ORDER[0]), config_for(ORDER[1])
    key = getpass.getpass("Groq API key for the intended FREE organization (hidden): ")
    account = getpass.getpass(
        "Cloudflare Account ID, intended WORKERS FREE account (hidden): "
    )
    token = getpass.getpass(
        "Scoped Workers AI token, Read + Edit for ONLY that account (hidden): "
    )
    check(bool(key) and not any(x.isspace() for x in key), "invalid_groq_key")
    check(bool(re.fullmatch(r"[a-fA-F0-9]{32}", account)), "invalid_account_id")
    check(
        bool(token) and not any(x.isspace() for x in token), "invalid_cloudflare_token"
    )
    print(
        "Check Groq Console > intended organization > Settings > Billing: Free, not Developer/paid/trial credits."
    )
    check(
        input("Type GROQ_FREE only after checking: ").strip() == "GROQ_FREE",
        "groq_free_plan_not_confirmed",
    )
    print(
        "Check Cloudflare > intended account > Workers & Pages > Plans: Workers FREE; Workers AI quota must hard-stop at the free allowance. Do not upgrade or enable billing."
    )
    check(
        input("Type WORKERS_FREE only after checking: ").strip() == "WORKERS_FREE",
        "cloudflare_free_plan_not_confirmed",
    )
    groq["GROQ_API_KEY"] = key
    cf["CLOUDFLARE_ACCOUNT_ID"] = account
    cf["OPENAI_COMPATIBLE_API_KEY"] = token
    cf["OPENAI_COMPATIBLE_BASE_URL"] = (
        f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1"
    )
    for name, c, secret, plan in (
        (ORDER[0], groq, key, "GROQ_FREE"),
        (ORDER[1], cf, token, "WORKERS_FREE"),
    ):
        write_env(PRIVATE / name / "private.env", c)
        save(
            PRIVATE / name / "plan.json",
            {
                "plan": plan,
                "confirmed_at": now(),
                "binding": digest((secret + c["CLOUDFLARE_ACCOUNT_ID"]).encode()),
                "source": "operator dashboard check, not API-inferred",
            },
            exclusive=False,
        )
    return {"status": "CREDENTIALS_STORED", "generation_requests": 0}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class MetadataFailure(Failure):
    """Only closed, sanitized diagnostics may cross the CLI error boundary."""

    def __init__(self, code, diagnostic):
        super().__init__(code)
        self.diagnostic = diagnostic


def metadata_target(url):
    parsed = urlsplit(url)
    groq = (
        parsed.netloc == "api.groq.com"
        and parsed.path == "/openai/v1/models"
        and not parsed.query
    )
    cloudflare = parsed.netloc == "api.cloudflare.com" and re.fullmatch(
        r"/client/v4/accounts/[a-fA-F0-9]{32}/ai/models/(search|schema)",
        parsed.path,
    )
    check(
        parsed.scheme == "https"
        and not parsed.fragment
        and (groq or (cloudflare and bool(parsed.query))),
        "non_inference_metadata_url_required",
    )
    return {
        "target_provider": "groq" if groq else "cloudflare",
        "operation": "models.list" if groq else "models." + cloudflare.group(1),
        "method": "GET",
        "hostname": parsed.hostname,
        "path": re.sub(r"/accounts/[^/]+/", "/accounts/{ACCOUNT_ID}/", parsed.path),
    }


def metadata_diagnostic(target, response, raw, key, url):
    """Never keep raw bodies, messages, arbitrary headers or account identifiers."""
    denied = [key, *re.findall(r"/accounts/([^/]+)/", url)]

    def label(value):
        if isinstance(value, int) and not isinstance(value, bool):
            return value if abs(value) <= 999999 else None
        if not isinstance(value, str) or not re.fullmatch(
            r"[A-Za-z0-9_.:/;-]{1,128}", value
        ):
            return None
        if any(v and v in value for v in denied) or re.search(
            r"(?i)bearer|authorization|sk-|eyJ", value
        ):
            return None
        return value

    headers = response.headers
    content_type = headers.get("Content-Type")
    mime = content_type.split(";", 1)[0].strip().lower() if content_type else None
    result = {
        **target,
        "collected_at": now(),
        "auth_scheme": "Bearer",
        "authorization_header_sent": True,
        "http_status": response.code,
        "content_type": label(mime),
        "content_type_state": (
            "not_returned"
            if content_type is None
            else "returned" if label(mime) is not None else "withheld_unsafe"
        ),
        "body_collected": True,
        "body_complete": len(raw) <= 2097152,
        "body_persisted": False,
        "response_kind": "unknown",
        "error_code": None,
        "error_type": None,
        "error_code_state": "not_returned",
        "error_type_state": "not_returned",
        "error_fields_state": "not_returned",
        "response_identifiers": {},
    }
    for name in ("x-request-id", "x-groq-request-id", "cf-ray"):
        value = headers.get(name)
        safe = label(value)
        result["response_identifiers"]["header." + name] = {
            "value": safe,
            "state": (
                "not_returned"
                if value is None
                else "returned" if safe is not None else "withheld_unsafe"
            ),
        }
    try:
        body = json.loads(raw) if result["body_complete"] else None
    except (ValueError, UnicodeError):
        body = None
    if isinstance(body, (dict, list)):
        result["response_kind"] = "json"
        error = body.get("error") if isinstance(body, dict) else None
        if not isinstance(error, dict):
            errors = body.get("errors") if isinstance(body, dict) else None
            error = errors[0] if isinstance(errors, list) and errors else None
        if isinstance(error, dict):
            for name in ("code", "type"):
                value = error.get(name)
                result["error_" + name] = label(value)
                result["error_" + name + "_state"] = (
                    "not_returned"
                    if name not in error
                    else (
                        "returned_null"
                        if value is None
                        else (
                            "returned"
                            if label(value) is not None
                            else "withheld_unsafe"
                        )
                    )
                )
            result["error_fields_state"] = "collected; absent_or_unsafe_values_are_null"
            result["error_fields_source"] = "json.error_or_errors[0]"
    else:
        result["response_kind"] = (
            "html"
            if mime == "text/html"
            else "text" if mime == "text/plain" else "non_json"
        )
        # Recognize only a numeric error marker, never free-form HTML/text.
        match = re.search(rb"(?i)\berror\s*(?:code\s*)?[:\s]\s*([0-9]{3,5})\b", raw)
        if match:
            result["error_code"] = int(match.group(1))
            result["error_code_state"] = "returned"
            result["error_fields_state"] = "numeric_marker_returned; type_not_returned"
            result["error_fields_source"] = "non_json_numeric_error_marker"
        if not result["body_complete"]:
            result["error_fields_state"] = "not_fully_collected_body_exceeds_limit"
            result["error_code_state"] = result["error_type_state"] = (
                "not_fully_collected"
            )
    return result


def metadata_get(url, key):
    target = metadata_target(url)
    request = Request(
        url,
        method="GET",
        headers={
            "Authorization": "Bearer " + key,
            "Accept": "application/json",
            "User-Agent": METADATA_USER_AGENT,
        },
    )
    try:
        response = build_opener(ProxyHandler({}), NoRedirect()).open(
            request, timeout=25
        )
    except HTTPError as error:
        response = error
    with response:
        raw = response.read(2097153)
    diagnostic = metadata_diagnostic(target, response, raw, key, url)
    diagnostic["request_user_agent"] = METADATA_USER_AGENT
    folder = PRIVATE / "metadata-diagnostics"
    folder.mkdir(mode=0o700, exist_ok=True)
    save(folder / (uuid4().hex + ".json"), diagnostic, exclusive=True)
    if not 200 <= response.code < 300:
        raise MetadataFailure(
            f"metadata_{target['target_provider']}_{target['operation']}_HTTP_{response.code}",
            diagnostic,
        ) from None
    check(len(raw) <= 2097152, "metadata_too_large")
    return json.loads(raw)


def schema_properties(definition):
    if not isinstance(definition, dict):
        return set()
    names = set(definition.get("properties", {}))
    for key in ("oneOf", "anyOf", "allOf"):
        for branch in definition.get(key, []):
            names |= schema_properties(branch)
    return names


def preflight():
    result = {
        "status": "PREFLIGHT_PASS",
        "checked_at": now(),
        "generation_requests": 0,
        "profiles": {},
    }
    # Validate both secrets/plans BEFORE issuing either metadata GET.
    configs = {name: config_for(name, ready=True) for name in ORDER}
    groq = metadata_get(
        "https://api.groq.com/openai/v1/models", configs[ORDER[0]]["GROQ_API_KEY"]
    )
    matches = [
        v
        for v in groq.get("data", [])
        if v.get("id") == MODELS[ORDER[0]] and v.get("active", True) is True
    ]
    check(len(matches) == 1, "groq_model_unavailable")
    result["profiles"][ORDER[0]] = {
        "model": MODELS[ORDER[0]],
        "active": True,
        "free_plan": "operator-confirmed; no tier field in models API",
    }
    c = configs[ORDER[1]]
    base = c["OPENAI_COMPATIBLE_BASE_URL"].removesuffix("/v1")
    models = metadata_get(
        base
        + "/models/search?"
        + urlencode({"search": MODELS[ORDER[1]], "include_deprecated": "false"}),
        c["OPENAI_COMPATIBLE_API_KEY"],
    )
    check(models.get("success") is True, "cloudflare_model_search_failed")
    check(
        any(v.get("name") == MODELS[ORDER[1]] for v in models.get("result", [])),
        "cloudflare_model_unavailable",
    )
    schema = metadata_get(
        base + "/models/schema?" + urlencode({"model": MODELS[ORDER[1]]}),
        c["OPENAI_COMPATIBLE_API_KEY"],
    )
    check(schema.get("success") is True, "cloudflare_schema_lookup_failed")
    definition = schema.get("result", {}).get("input", {})
    if isinstance(definition, str):
        definition = json.loads(definition)
    check(
        {"max_tokens", "temperature", "response_format"}
        <= schema_properties(definition),
        "cloudflare_required_parameters_not_advertised",
    )
    result["profiles"][ORDER[1]] = {
        "model": MODELS[ORDER[1]],
        "json_and_token_schema": True,
        "free_plan": "operator-confirmed Workers Free hard quota; not zero model pricing",
    }
    for name in ORDER:
        resolved(name)
    save(PRIVATE / "preflight.json", result)
    return result


def active():
    path = PRIVATE / "active.json"
    name = json.loads(path.read_text())["profile"] if path.exists() else ORDER[0]
    check(name in ORDER, "unknown_active_profile")
    return name


def compose_args(name):
    c = config_for(name)
    return [
        "docker",
        "compose",
        "--project-name",
        c["COMPOSE_PROJECT_NAME"],
        "--env-file",
        str(PRIVATE / name / "private.env"),
        "-f",
        str(ROOT / "docker-compose.yml"),
        "-f",
        str(PRIVATE / "compose.private.json"),
    ]


def compose(name, args):
    c = config_for(name)
    return common.process(compose_args(name) + common.safe_compose_arguments(args), c)


def resolved(name, running=False):
    c, m = config_for(name), manifest()
    value = json.loads(
        common.process(
            compose_args(name) + ["--profile", "cli", "config", "--format", "json"], c
        ).stdout
    )
    check(value["name"] == m["project"], "compose_project_changed")
    check(
        value["volumes"]["maos_postgres_data"]["name"]
        == m["project"] + "_maos_postgres_data",
        "volume_namespace_changed",
    )
    for service in ("api", "worker", "cli"):
        d = value["services"][service]
        check(d["image"] == m["image_id"], "image_not_pinned")
        for key in (
            "LLM_PROVIDER",
            "LLM_MODEL",
            "MAX_PROVIDER_CALLS",
            "LLM_MAX_RETRIES",
            "LLM_MAX_OUTPUT_TOKENS",
            "GROQ_REASONING_EFFORT",
            *CREDENTIALS,
            "OPENAI_COMPATIBLE_BASE_URL",
            "OPENROUTER_PROVIDER_PREFERENCES",
        ):
            check(
                d["environment"].get(key) == c[key],
                "compose_profile_environment_mismatch",
            )
        if service == "cli":
            mounts = d.get("volumes", [])
            check(
                len(mounts) == 1
                and mounts[0]["source"] == m["cli_directory"]
                and mounts[0]["target"] == "/cli",
                "cli_state_not_reused",
            )
        else:
            check(not d.get("volumes"), "unexpected_runtime_mount")
        if running and service != "cli":
            ids = common.process(
                compose_args(name) + ["ps", "-q", service], c
            ).stdout.split()
            check(len(ids) == 1, "running_service_required")
            actual = json.loads(
                common.process(["docker", "inspect", ids[0]], c).stdout
            )[0]
            check(
                actual["State"]["Running"] and actual["Image"] == m["image_id"],
                "running_image_mismatch",
            )
            actual_env = dict(
                x.split("=", 1) for x in actual["Config"]["Env"] if "=" in x
            )
            check(
                all(actual_env.get(k) == v for k, v in d["environment"].items()),
                "running_profile_mismatch",
            )
    storage = value["services"]["postgres"]
    check(
        all(
            storage["environment"].get(k) == c[k]
            for k in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
        ),
        "postgres_identity_changed",
    )
    mounts = storage.get("volumes", [])
    check(
        len(mounts) == 1
        and mounts[0]["type"] == "volume"
        and mounts[0]["source"] == "maos_postgres_data",
        "postgres_volume_changed",
    )
    if running:
        ids = common.process(
            compose_args(name) + ["ps", "-q", "postgres"], c
        ).stdout.split()
        check(len(ids) == 1, "postgres_required")
        actual = json.loads(common.process(["docker", "inspect", ids[0]], c).stdout)[0]
        check(
            actual["State"]["Running"]
            and len(actual["Mounts"]) == 1
            and actual["Mounts"][0].get("Name") == m["project"] + "_maos_postgres_data",
            "actual_postgres_volume_changed",
        )
    return True


def sql_read(name, statement):
    c = config_for(name)
    return common.process(
        compose_args(name)
        + [
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            c["POSTGRES_USER"],
            "-d",
            c["POSTGRES_DB"],
            "-Atc",
            statement,
        ],
        c,
    ).stdout.strip()


def no_active_work(name):
    # API and worker must already be stopped, preventing creation/dispatch races.
    statement = "SELECT (SELECT count(*) FROM jobs WHERE status <> 'DONE') + (SELECT count(*) FROM runs WHERE status='RUNNING' OR owner IS NOT NULL OR lease_expires_at IS NOT NULL) + (SELECT count(*) FROM node_executions WHERE status='EXECUTING')"
    check(
        sql_read(name, statement) == "0",
        "active_or_uncertain_execution_prevents_profile_switch",
    )


def activate(name):
    config_for(name, ready=True)
    compose(active(), ["stop", "api", "worker"])
    no_active_work(name)
    save(PRIVATE / "active.json", {"profile": name})
    compose(name, ["up", "-d", "--wait", "api", "worker"])
    resolved(name, running=True)


def api_get(name, path):
    c, m = config_for(name), manifest()
    auth = Path(m["cli_directory"]) / "auth.json"
    check(
        auth.is_file() and not auth.is_symlink() and auth.stat().st_mode & 0o077 == 0,
        "local_cli_login_required",
    )
    credentials = json.loads(auth.read_text())
    request = Request(
        "http://127.0.0.1:" + c["MAOS_API_PORT"] + "/api/v1" + path,
        method="GET",
        headers={"Authorization": "Bearer " + credentials["access_token"]},
    )
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(
            request, timeout=15
        ) as response:
            raw = response.read(2097153)
    except HTTPError as error:
        raise Failure(
            "local_cli_login_required"
            if error.code == 401
            else f"api_read_HTTP_{error.code}"
        ) from None
    check(len(raw) <= 2097152, "api_evidence_too_large")
    return json.loads(raw)


def verify_history(name):
    expected = [
        json.loads((common.PRIVATE / "api-evidence.json").read_text())["run"],
        json.loads(
            (
                common.PRIVATE / "attempts" / common.ADDITIONAL_ID / "api-evidence.json"
            ).read_text()
        )["run"],
    ]
    for record in expected:
        check(
            api_get(name, "/runs/" + record["id"]) == record, "historical_run_mutated"
        )
    return True


def phase(name):
    m, c = manifest(), config_for(name, ready=True)
    folder = PRIVATE / name
    check(
        digest(Path(m["input_file"]).read_bytes()) == m["input_sha256"],
        "original_input_changed",
    )
    save(
        folder / "attempt.json",
        {
            "profile": name,
            "model": MODELS[name],
            "max_calls": 2,
            "source": m["source"],
            "image_id": m["image_id"],
            "input_sha256": m["input_sha256"],
            "started_at": now(),
        },
        exclusive=True,
    )
    auth = Path(m["cli_directory"]) / "auth.json"
    with open(
        folder / "live.stdout.json",
        "x",
        opener=lambda path, flags: os.open(path, flags | os.O_NOFOLLOW, 0o600),
    ) as stdout, open(
        folder / "live.stderr.json",
        "x",
        opener=lambda path, flags: os.open(path, flags | os.O_NOFOLLOW, 0o600),
    ) as stderr:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/ops/live_text_review.py"),
                "--api-url",
                "http://127.0.0.1:" + c["MAOS_API_PORT"],
                "--env-file",
                str(folder / "private.env"),
                "--auth-file",
                str(auth),
                "--input",
                m["input_file"],
                "--enable-remote",
                "--approve",
                "--max-calls",
                "2",
                "--max-output-tokens",
                "1024",
            ],
            cwd=ROOT,
            env=common.sanitized_environment(c),
            text=True,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    collected = common.collect_evidence(folder, c, auth)
    check(
        collected == "saved_privately_may_contain_user_text",
        "incomplete_phase_evidence_no_fallback",
    )
    evidence = json.loads((folder / "api-evidence.json").read_text())
    run = evidence["run"]
    check(0 <= run["call_count"] <= 2, "provider_budget_violation")
    messages = []
    for line in (folder / "live.stderr.json").read_text().splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                messages.append(value.get("code"))
        except ValueError:
            pass
    result = {
        "profile": name,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "run_id": str(UUID(run["id"])),
        "calls": run["call_count"],
        "run_status": run["status"],
        "error": run.get("error"),
        "nodes": [
            {
                "node_id": n["node_id"],
                "kind": n["kind"],
                "status": n["status"],
                "execution_metadata": n["execution_metadata"],
            }
            for n in evidence["/nodes"]
        ],
        "smoke_failure_code": messages[-1] if messages else None,
    }
    if result["status"] == "PASS":
        check(
            run["status"] == "COMPLETED" and run["call_count"] == 2,
            "inconsistent_success",
        )
    verify_history(name)
    save(folder / "outcome.json", result, exclusive=True)
    return result


def fallback_reason(result):
    if (
        result.get("status") != "FAIL"
        or result.get("run_status") != "FAILED"
        or result.get("smoke_failure_code") != "unexpected_run_outcome_FAILED"
        or not 1 <= result.get("calls", 0) <= 2
    ):
        return None
    code = (result.get("error") or {}).get("code")
    failed = [
        n
        for n in result.get("nodes", [])
        if n["kind"] == "agent" and n["status"] == "FAILED"
    ]
    if len(failed) != 1:
        return None
    d = failed[0]["execution_metadata"].get("provider_diagnostics", {})
    codes = (
        str(d.get("error_code", "")).lower()
        + " "
        + str(d.get("error_type", "")).lower()
    )
    if any(
        word in codes
        for word in (
            "billing",
            "payment",
            "credit",
            "auth",
            "permission",
            "model_not",
            "unknown_model",
            "invalid",
            "unsupported",
            "insufficient_quota",
        )
    ):
        return None
    status = d.get("http_status")
    if code == "provider_rate_limit" and status == 429:
        return "provider_HTTP_429"
    if code in ("provider_timeout", "provider_unavailable") and status is None:
        return "provider_connection_or_timeout"
    if code == "provider_unavailable" and status in (500, 502, 503, 504):
        return f"provider_HTTP_{status}"
    return None


def execute_sequence(execute, switch):
    """At most one whole workflow per provider. No checkpoint is passed across runs."""
    groq = execute(ORDER[0])
    check(
        isinstance(groq.get("calls"), int)
        and not isinstance(groq["calls"], bool)
        and 0 <= groq["calls"] <= 2,
        "provider_budget_violation",
    )
    if groq["status"] == "PASS":
        return {
            "status": "PASS",
            "attempts": [groq],
            "fallback_reason": None,
            "cloudflare": "UNUSED_NOT_LIVE_VERIFIED",
        }
    reason = fallback_reason(groq)
    if reason is None:
        return {
            "status": "FAIL",
            "attempts": [groq],
            "fallback_reason": None,
            "cloudflare": "NOT_ATTEMPTED_FATAL_PRIMARY_FAILURE",
        }
    switch(ORDER[1])
    cloudflare = execute(ORDER[1])
    check(
        isinstance(cloudflare.get("calls"), int)
        and not isinstance(cloudflare["calls"], bool)
        and 0 <= cloudflare["calls"] <= 2,
        "provider_budget_violation",
    )
    return {
        "status": cloudflare["status"],
        "attempts": [groq, cloudflare],
        "fallback_reason": reason,
        "cloudflare": "ATTEMPTED",
    }


def start():
    check(
        not (PRIVATE / "campaign.json").exists(),
        "campaign_already_reserved_never_reset_budget",
    )
    for name in ORDER:
        config_for(name, ready=True)
    compose(active(), ["up", "-d", "--wait", "postgres", "redis"])
    activate(ORDER[0])
    return {"status": "SERVICES_READY", "generation_requests": 0}


def campaign(approve):
    check(approve, "explicit_approval_option_required")
    check(
        not (PRIVATE / "campaign.json").exists(),
        "campaign_already_reserved_never_reset_budget",
    )
    preflight()
    check(active() == ORDER[0], "start_primary_profile_first")
    resolved(ORDER[0], running=True)
    api_get(ORDER[0], "/workflows")
    verify_history(ORDER[0])
    m = manifest()
    save(
        PRIVATE / "campaign.json",
        {
            "started_at": now(),
            "source": m["source"],
            "image_id": m["image_id"],
            "historical_runs": m["historical_runs"],
            "historical_consumed": 2,
            "per_provider_reserved_max": 2,
            "new_reserved_max": 4,
            "cumulative_max": 6,
            "order": list(ORDER),
            "input_sha256": m["input_sha256"],
        },
        exclusive=True,
    )
    reserved = True
    try:
        result = execute_sequence(phase, activate)
        result["new_consumed"] = sum(v["calls"] for v in result["attempts"])
        check(result["new_consumed"] <= 4, "campaign_budget_violation")
        result["cumulative_consumed"] = 2 + result["new_consumed"]
        save(PRIVATE / "outcome.json", result, exclusive=True)
        return result
    except Exception as error:
        if reserved and not (PRIVATE / "outcome.json").exists():
            save(
                PRIVATE / "outcome.json",
                {
                    "status": "FAIL",
                    "error_class": type(error).__name__,
                    "new_consumed": None,
                    "cumulative_consumed": None,
                    "new_reserved_max": 4,
                    "cumulative_max": 6,
                    "partial_evidence_retained": True,
                    "retry": False,
                },
                exclusive=True,
            )
        raise
    finally:
        compose(active(), ["stop"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("prepare").add_argument("--image", required=True)
    sub.add_parser("set-credentials")
    sub.add_parser("preflight")
    sub.add_parser("start")
    sub.add_parser("run").add_argument("--approve", action="store_true")
    command = sub.add_parser("compose")
    command.add_argument("--profile", choices=["cli"])
    command.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            value = prepare(args.image)
        elif args.action == "set-credentials":
            value = credentials()
        elif args.action == "preflight":
            value = preflight()
        elif args.action == "start":
            value = start()
        elif args.action == "run":
            value = campaign(args.approve)
        else:
            name = active()
            config_for(name, ready=args.arguments[:1] not in (["stop"], ["ps"]))
            resolved(name)
            params = (["--profile", "cli"] if args.profile else []) + args.arguments
            code = subprocess.run(
                compose_args(name) + common.safe_compose_arguments(params),
                cwd=ROOT,
                env=common.sanitized_environment(config_for(name)),
                check=False,
            ).returncode
            return code
        # Do not print phase records or provider text; evidence is private.
        print(
            json.dumps(
                {
                    k: v
                    for k, v in value.items()
                    if k
                    in (
                        "status",
                        "source",
                        "image_id",
                        "generation_requests",
                        "credentials",
                        "new_consumed",
                        "cumulative_consumed",
                        "fallback_reason",
                        "cloudflare",
                    )
                }
            )
        )
        return 1 if value["status"] == "FAIL" else 0
    except (Failure, OSError, ValueError, KeyError, TypeError) as error:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "code": (
                        str(error)
                        if isinstance(error, Failure)
                        else type(error).__name__
                    ),
                    "generation": "NEVER_AUTOMATICALLY_RETRIED",
                    **(
                        {"metadata_diagnostic": error.diagnostic}
                        if isinstance(error, MetadataFailure)
                        else {}
                    ),
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
