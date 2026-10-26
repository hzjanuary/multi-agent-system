#!/usr/bin/env python3
"""Explicit public-API smoke with two real calls and an authenticated approval.

Requires a dedicated configured installation and user-supplied text. Does not
seed records, download models, select a fake provider or print credentials/text.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4


class SmokeFailure(Exception):
    pass


def read_config(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise SmokeFailure("invalid_configuration_file")
        key, value = line.split("=", 1)
        parsed = shlex.split(value, comments=True)
        if len(parsed) > 1:
            raise SmokeFailure("configuration_values_with_spaces_must_be_quoted")
        values[key.strip()] = parsed[0] if parsed else ""
    return values


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def is_local_endpoint(endpoint: str) -> bool:
    host = urlsplit(endpoint).hostname or ""
    if host in {
        "localhost",
        "host.docker.internal",
        "ollama",
        "model",
        "model-service",
    }:
        return True
    try:
        address = ipaddress.ip_address(host)
        return address.is_loopback or address.is_private
    except ValueError:
        return False


def selected_profile(config: dict[str, str]) -> dict[str, str]:
    provider = config.get("LLM_PROVIDER", "ollama")
    endpoints = {
        "ollama": config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "openai_compatible": config.get("OPENAI_COMPATIBLE_BASE_URL", ""),
        "groq": "https://api.groq.com/openai/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
    }
    if provider not in endpoints or not config.get("LLM_MODEL", "").strip():
        raise SmokeFailure("real_provider_and_explicit_model_required")
    return {
        "profile": "default",
        "provider": provider,
        "model": config["LLM_MODEL"].strip(),
        "endpoint_hash": digest(endpoints[provider].rstrip("/")),
        "max_output_tokens": str(int(config.get("LLM_MAX_OUTPUT_TOKENS", "1024"))),
        "max_retries": str(int(config.get("LLM_MAX_RETRIES", "2"))),
        "timeout_seconds": str(int(config.get("LLM_TIMEOUT_SECONDS", "60"))),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--auth-file", type=Path, required=True)
    parser.add_argument(
        "--input", type=Path, required=True, help="User-supplied UTF-8 text"
    )
    parser.add_argument("--enable-remote", action="store_true")
    parser.add_argument(
        "--approve",
        action="store_true",
        help=(
            "Explicitly authorize the authenticated smoke principal "
            "to approve the reviewed result"
        ),
    )
    parser.add_argument("--max-calls", type=int, choices=[2], default=2)
    parser.add_argument("--max-output-tokens", type=int, default=1024)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    args = parser.parse_args()
    run_id = None
    headers: dict[str, str] = {}
    try:
        if not args.approve:
            raise SmokeFailure(
                "explicit_approval_enablement_required: "
                "pass --approve for this pure-tool smoke"
            )
        if (
            not 16 <= args.max_output_tokens <= 32768
            or not 10 <= args.timeout_seconds <= 1800
        ):
            raise SmokeFailure("invalid_smoke_budget")
        config = read_config(args.env_file)
        profile = selected_profile(config)
        provider = profile["provider"]
        endpoint = (
            config.get("OLLAMA_BASE_URL", "http://localhost:11434")
            if provider == "ollama"
            else config.get("OPENAI_COMPATIBLE_BASE_URL", "")
        )
        if (
            provider not in {"ollama", "openai_compatible"}
            or not is_local_endpoint(endpoint)
        ) and not args.enable_remote:
            raise SmokeFailure("remote_provider_requires_explicit_enablement")
        if int(config.get("LLM_MAX_RETRIES", "2")) != 0:
            raise SmokeFailure("dedicated_smoke_requires_LLM_MAX_RETRIES_0")
        if int(config.get("MAX_PROVIDER_CALLS", "16")) != args.max_calls:
            raise SmokeFailure("dedicated_smoke_requires_MAX_PROVIDER_CALLS_2")
        if (
            not 1
            <= int(config.get("LLM_MAX_OUTPUT_TOKENS", "1024"))
            <= args.max_output_tokens
        ):
            raise SmokeFailure("configured_output_token_limit_exceeds_smoke_budget")
        if "maos_examples.text_review" not in config.get(
            "MAOS_EXTENSION_MODULES", ""
        ).split(","):
            raise SmokeFailure("text_review_extension_not_explicitly_enabled")
        if args.auth_file.stat().st_mode & 0o077:
            raise SmokeFailure("auth_file_must_have_mode_0600")
        credentials = json.loads(args.auth_file.read_text())
        headers = {
            "Authorization": "Bearer " + credentials["access_token"],
            "Content-Type": "application/json",
        }
        api = urlsplit(args.api_url)
        if (
            api.scheme not in {"http", "https"}
            or not api.hostname
            or api.username
            or api.password
            or api.query
            or api.fragment
        ):
            raise SmokeFailure("invalid_api_base_url")
        text = args.input.read_text()
        if not text.strip() or len(text) > 16000:
            raise SmokeFailure("input_must_contain_1_to_16000_characters")

        def request(
            method: str, path: str, body: Any = None, idempotency: str | None = None
        ) -> Any:
            extra = {"Idempotency-Key": idempotency} if idempotency else {}
            message = Request(
                args.api_url.rstrip("/") + "/api/v1" + path,
                data=json.dumps(body).encode() if body is not None else None,
                headers={**headers, **extra},
                method=method,
            )
            try:
                with urlopen(message, timeout=15) as response:
                    return json.loads(response.read(2097152))
            except HTTPError as error:
                raise SmokeFailure(f"api_request_failed_HTTP_{error.code}") from None
            except (URLError, TimeoutError, ValueError):
                raise SmokeFailure("api_unavailable_or_invalid_response") from None

        definition = request("GET", "/workflows/text_review?version=1.0.0")
        if definition["limits"]["max_calls"] != args.max_calls:
            raise SmokeFailure("api_workflow_call_limit_does_not_match_smoke_budget")
        run = request(
            "POST",
            "/runs",
            {"workflow_id": "text_review", "version": "1.0.0", "input": {"text": text}},
            str(uuid4()),
        )
        run_id = run["id"]
        if run["provider_profile"] != profile:
            raise SmokeFailure(
                "api_provider_profile_does_not_match_explicit_configuration"
            )
        request("POST", f"/runs/{run_id}/start", {}, str(uuid4()))
        deadline = time.monotonic() + args.timeout_seconds

        def wait_for(target: str) -> dict[str, Any]:
            while time.monotonic() < deadline:
                current = request("GET", f"/runs/{run_id}")
                if not isinstance(current, dict):
                    raise SmokeFailure("invalid_run_response")
                if current["status"] == target:
                    return current
                if current["status"] in {
                    "FAILED",
                    "REJECTED",
                    "CANCELLED",
                    "INTERRUPTED",
                    "COMPLETED",
                }:
                    raise SmokeFailure("unexpected_run_outcome_" + current["status"])
                time.sleep(0.5)
            raise SmokeFailure("smoke_deadline_exceeded")

        run = wait_for("WAITING_APPROVAL")
        nodes = request("GET", f"/runs/{run_id}/nodes")
        agents = [
            node
            for node in nodes
            if node["kind"] == "agent" and node["status"] == "COMPLETED"
        ]
        if len(agents) != 2 or run["call_count"] != 2:
            raise SmokeFailure("two_real_agent_steps_not_observed")
        for node in agents:
            metadata = node["execution_metadata"]
            if (
                metadata["provider"] != provider
                or not metadata["model"]
                or metadata["attempt_count"] != 1
            ):
                raise SmokeFailure("unexpected_provider_attempt_metadata")
        if any(node["node_id"] == "assemble" for node in nodes):
            raise SmokeFailure("downstream_tool_executed_before_approval")
        approvals = request("GET", f"/runs/{run_id}/approvals")
        pending = [a for a in approvals if a["decision"] is None]
        if len(pending) != 1:
            raise SmokeFailure("expected_one_pending_approval")
        approval = pending[0]
        if digest(approval["content"]) != approval["content_hash"]:
            raise SmokeFailure("approval_content_identity_mismatch")
        request(
            "POST",
            f"/runs/{run_id}/approvals/{approval['id']}/decision",
            {
                "decision": "approve",
                "expected_revision": run["revision"],
                "content_revision": approval["content_revision"],
                "content_hash": approval["content_hash"],
            },
        )
        paused = request("GET", f"/runs/{run_id}")
        if paused["status"] != "APPROVED":
            raise SmokeFailure("approval_implicitly_resumed_execution")
        request("POST", f"/runs/{run_id}/resume", {}, str(uuid4()))
        completed = wait_for("COMPLETED")
        if completed["call_count"] != 2 or not completed["final_output"]:
            raise SmokeFailure("final_result_or_call_budget_invalid")
        events = request("GET", f"/runs/{run_id}/events?after_sequence=0&limit=500")
        if [event["sequence"] for event in events] != list(
            range(1, completed["event_sequence"] + 1)
        ):
            raise SmokeFailure("event_replay_sequence_gap")
        commit = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            or "unknown"
        )
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "checked_commit": commit,
                    "run_id": run_id,
                    "definition_hash": run["definition_hash"],
                    "provider": provider,
                    "model": profile["model"],
                    "provider_calls": completed["call_count"],
                    "requested_output_token_budget": args.max_calls
                    * args.max_output_tokens,
                    "approval_id": approval["id"],
                    "approval_content_hash": approval["content_hash"],
                    "event_count": len(events),
                    "final_output_hash": digest(completed["final_output"]),
                }
            )
        )
        return 0
    except (SmokeFailure, OSError, KeyError, ValueError, TypeError) as error:
        # Never print arbitrary provider responses, raw prompts or credential errors.
        safe = str(error) if isinstance(error, SmokeFailure) else type(error).__name__
        print(
            json.dumps({"status": "FAIL", "code": safe, "run_id": run_id}),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
