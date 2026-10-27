"""Headless operator CLI. Configuration discovery never starts the application."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import ipaddress
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

VERSION = "0.2.0"


def local_model_endpoint(endpoint: str) -> bool:
    hostname = urlsplit(endpoint).hostname or ""
    if hostname in {"localhost", "host.docker.internal"} or (
        hostname and "." not in hostname and ":" not in hostname
    ):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return hostname.endswith(".local")
    return address.is_private or address.is_loopback or address.is_link_local


def private_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp = tempfile.mkstemp(dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def config_init(output: Path) -> dict[str, str]:
    template = Path(__file__).parent / "config" / "default.env"
    existing = output.read_text() if output.exists() else ""
    # Preserve every existing assignment, including operator comments and values.
    values = dict(
        line.split("=", 1)
        for line in existing.splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    )
    generated = {
        "JWT_SECRET_KEY": secrets.token_urlsafe(48),
        "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
        "MAOS_UID": str(os.getuid()),
        "MAOS_GID": str(os.getgid()),
    }
    generated["DATABASE_URL"] = (
        "postgresql+asyncpg://"
        + (values.get("POSTGRES_USER") or "maos")
        + ":"
        + (values.get("POSTGRES_PASSWORD") or generated["POSTGRES_PASSWORD"])
        + "@postgres:5432/"
        + (values.get("POSTGRES_DB") or "maos")
    )
    lines = existing.splitlines()
    for line in template.read_text().splitlines():
        if "=" not in line or line.startswith("#"):
            if not existing:
                lines.append(line)
            continue
        key, default = line.split("=", 1)
        if key in values and values[key]:
            continue
        value = generated.get(key, default)
        if key in values:
            lines = [
                f"{key}={value}" if text.startswith(f"{key}=") else text
                for text in lines
            ]
        else:
            lines.append(f"{key}={value}")
    private_write(output, "\n".join(lines) + "\n")
    cli = output.parent / "cli"
    cli.mkdir(exist_ok=True, mode=0o700)
    cli.chmod(0o700)
    return {"configuration": str(output), "status": "initialized"}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Multi-Agent OS operator CLI")
    p.add_argument("--version", action="version", version=VERSION)
    p.add_argument("--json", action="store_true", help="Stable JSON output")
    p.add_argument(
        "--api-url", default=os.getenv("MAOS_API_URL", "http://127.0.0.1:8000")
    )
    p.add_argument(
        "--auth-file",
        type=Path,
        default=Path(
            os.getenv("MAOS_AUTH_FILE", str(Path.home() / ".maos" / "auth.json"))
        ),
    )
    sub = p.add_subparsers(dest="group", required=True)
    config = sub.add_parser("config").add_subparsers(dest="action", required=True)
    config.add_parser("init").add_argument(
        "--output", type=Path, default=Path(".maos/.env")
    )
    sub.add_parser("doctor")
    sub.add_parser("migrate")
    admin = sub.add_parser("admin").add_subparsers(dest="action", required=True)
    for name in ("bootstrap", "create-user", "set-role"):
        command = admin.add_parser(name)
        command.add_argument("--email")
        if name != "bootstrap":
            command.add_argument(
                "--role", choices=["admin", "operator", "viewer"], required=True
            )
        if name != "set-role":
            command.add_argument("--password-stdin", action="store_true")
    auth = sub.add_parser("auth").add_subparsers(dest="action", required=True)
    login = auth.add_parser("login")
    login.add_argument("--email")
    login.add_argument("--password-stdin", action="store_true")
    auth.add_parser("logout")
    workflow = sub.add_parser("workflow").add_subparsers(dest="action", required=True)
    workflow.add_parser("list")
    workflow.add_parser("validate")
    show = workflow.add_parser("show")
    show.add_argument("workflow_id")
    show.add_argument("--version")
    run = sub.add_parser("run").add_subparsers(dest="action", required=True)
    create = run.add_parser("create")
    create.add_argument("workflow_id")
    create.add_argument("--version", required=True)
    create.add_argument("--input", type=Path, required=True)
    create.add_argument("--idempotency-key")
    listing = run.add_parser("list")
    listing.add_argument("--status")
    listing.add_argument("--workflow-id")
    listing.add_argument("--limit", type=int, default=100)
    listing.add_argument("--offset", type=int, default=0)
    for name in (
        "start",
        "show",
        "events",
        "approve",
        "reject",
        "resume",
        "cancel",
        "nodes",
        "approvals",
    ):
        command = run.add_parser(name)
        command.add_argument("run_id")
        if name in ("start", "resume"):
            command.add_argument("--idempotency-key")
        if name in ("events", "nodes", "approvals"):
            command.add_argument("--limit", type=int, default=100)
        if name == "events":
            command.add_argument("--follow", action="store_true")
            command.add_argument("--after-sequence", type=int, default=0)
        if name in ("approve", "reject"):
            command.add_argument("approval_id")
            command.add_argument("--expected-revision", type=int, required=True)
            command.add_argument("--content-revision", type=int, required=True)
            command.add_argument("--content-hash", required=True)
            command.add_argument("--comment")
    provider = sub.add_parser("provider").add_subparsers(dest="action", required=True)
    check = provider.add_parser("check")
    check.add_argument("--enable-remote", action="store_true")
    check.add_argument("--max-calls", type=int, default=1)
    check.add_argument("--max-tokens", type=int, default=128)
    return p


async def local(args: argparse.Namespace) -> Any:
    if args.group == "config":
        return config_init(args.output)
    if args.group == "admin":
        from app.administration import provision, set_role

        email = args.email or input("Email: ").strip()
        if args.action == "set-role":
            return await set_role(email, args.role)
        password = (
            sys.stdin.readline().rstrip("\n")
            if args.password_stdin
            else getpass.getpass("Password (12+ characters): ")
        )
        return await provision(
            email,
            password,
            role=getattr(args, "role", "admin"),
            bootstrap=args.action == "bootstrap",
        )
    if args.group == "migrate":
        from alembic.config import Config

        from alembic import command

        command.upgrade(
            Config(str(Path(__file__).parent.parent / "alembic.ini")), "head"
        )
        return {"status": "migrated"}
    if args.group == "doctor":
        from app.config import get_settings
        from app.core.readiness import ReadinessChecker

        checks = await ReadinessChecker(get_settings()).check_all()
        result = [c.model_dump(mode="json") for c in checks]
        from app.core.worker_health import worker_available
        from app.db import get_session_factory

        try:
            available = await worker_available(get_session_factory())
        except Exception:
            available = False
        healthy = available and all(not c.required or c.status == "ok" for c in checks)
        return {
            "checks": result,
            "worker_available": available,
            "status": "ready" if healthy else "not_ready",
        }
    if args.group == "provider":
        from pydantic import BaseModel

        from app.config import get_settings
        from app.definitions import AgentDefinition
        from app.llm.service import LLMService

        settings = get_settings().llm_settings
        if (
            settings.provider.value not in ("ollama", "openai_compatible")
            or not local_model_endpoint(settings.endpoint)
        ) and not args.enable_remote:
            raise ValueError("remote_probe_requires_enablement")
        if args.max_calls != 1 or not 16 <= args.max_tokens <= 256:
            raise ValueError("probe_budget: max-calls must be 1; max-tokens 16..256")

        class ProbeInput(BaseModel):
            text: str

        class ProbeOutput(BaseModel):
            ok: bool

        agent = AgentDefinition(
            "provider_probe",
            "1",
            "Probe",
            "Connectivity check",
            'Return {"ok":true} as JSON.',
            ProbeInput,
            ProbeOutput,
            max_tokens=args.max_tokens,
        )
        used = 0

        async def reserve() -> None:
            nonlocal used
            used += 1
            if used > 1:
                raise ValueError("probe_budget_exhausted")

        service = LLMService(
            settings=settings.model_copy(
                update={"max_retries": 0, "max_output_tokens": args.max_tokens}
            )
        )
        output, metadata = await service.invoke(
            agent, {"text": "Check configured provider connectivity."}, reserve
        )
        return {"output": output, "metadata": metadata}
    raise ValueError("unknown_local_command")


async def remote(args: argparse.Namespace) -> Any:
    import httpx

    credentials: dict[str, Any] = {}
    if args.auth_file.exists():
        if args.auth_file.stat().st_mode & 0o077:
            raise ValueError("unsafe_auth_file_permissions: expected 0600")
        credentials = json.loads(args.auth_file.read_text())
    access_token = credentials.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    async with httpx.AsyncClient(base_url=args.api_url, timeout=30) as client:

        async def request(
            method: str, path: str, body: Any = None, params: Any = None
        ) -> Any:
            extra = (
                {"Idempotency-Key": args.idempotency_key}
                if getattr(args, "idempotency_key", None)
                else {}
            )
            response = await client.request(
                method, path, json=body, params=params, headers={**headers, **extra}
            )
            if response.is_error:
                try:
                    code = (
                        response.json().get("detail", {}).get("code", "request_failed")
                    )
                except (ValueError, AttributeError):
                    code = "request_failed"
                raise ValueError(f"{code}: HTTP {response.status_code}")
            return response.json()

        if args.group == "auth":
            if args.action == "login":
                email = args.email or input("Email: ").strip()
                password = (
                    sys.stdin.readline().rstrip("\n")
                    if args.password_stdin
                    else getpass.getpass("Password: ")
                )
                result = await request(
                    "POST", "/api/v1/auth/login", {"email": email, "password": password}
                )
                private_write(args.auth_file, json.dumps(result))
                return {"status": "authenticated"}
            if credentials:
                await request(
                    "POST",
                    "/api/v1/auth/logout",
                    {"refresh_token": credentials["refresh_token"]},
                )
                args.auth_file.unlink()
            return {"status": "logged_out"}
        if args.group == "workflow":
            if args.action == "show":
                return await request(
                    "GET",
                    f"/api/v1/workflows/{args.workflow_id}",
                    params={"version": args.version} if args.version else {},
                )
            result = await request("GET", "/api/v1/workflows")
            return (
                {"valid": True, "workflows": result}
                if args.action == "validate"
                else result
            )
        prefix = "/api/v1/runs"
        if args.action == "create":
            return await request(
                "POST",
                prefix,
                {
                    "workflow_id": args.workflow_id,
                    "version": args.version,
                    "input": json.loads(args.input.read_text()),
                },
            )
        if args.action == "list":
            return await request(
                "GET",
                prefix,
                params={
                    k: v
                    for k, v in {
                        "status": args.status,
                        "workflow_id": args.workflow_id,
                        "limit": args.limit,
                        "offset": args.offset,
                    }.items()
                    if v is not None
                },
            )
        path = f"{prefix}/{args.run_id}"
        if args.action == "show":
            return await request("GET", path)
        if args.action in ("approve", "reject"):
            return await request(
                "POST",
                f"{path}/approvals/{args.approval_id}/decision",
                {
                    "decision": args.action,
                    "expected_revision": args.expected_revision,
                    "content_revision": args.content_revision,
                    "content_hash": args.content_hash,
                    "comment": args.comment,
                },
            )
        if args.action == "events":
            cursor = args.after_sequence
            while True:
                batch = await request(
                    "GET",
                    path + "/events",
                    params={"after_sequence": cursor, "limit": args.limit},
                )
                if not args.follow:
                    return batch
                for event in batch:
                    print(json.dumps(event), flush=True)
                    cursor = event["sequence"]
                await asyncio.sleep(1)
        if args.action in ("nodes", "approvals"):
            return await request(
                "GET", path + "/" + args.action, params={"limit": args.limit}
            )
        return await request("POST", path + "/" + args.action)


def main() -> int:
    args = parser().parse_args()
    try:
        # Alembic's async env owns its event loop.
        if args.group == "migrate":
            from alembic.config import Config

            from alembic import command

            command.upgrade(
                Config(str(Path(__file__).parent.parent / "alembic.ini")), "head"
            )
            result = {"status": "migrated"}
        else:
            result = asyncio.run(
                local(args)
                if args.group in ("config", "doctor", "admin", "provider")
                else remote(args)
            )
        print(
            json.dumps(result, default=str)
            if args.json
            else json.dumps(result, indent=2, default=str)
        )
        if args.group == "doctor" and result.get("status") != "ready":
            print(
                "doctor_failed: required dependency/configuration "
                "or worker unavailable",
                file=sys.stderr,
            )
            return 1
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        # Never echo arbitrary exception strings containing secrets/provider bodies.
        safe = (
            str(error)
            if isinstance(error, ValueError) and type(error) is ValueError
            else type(error).__name__
        )
        print(
            json.dumps({"error": {"code": "command_failed", "message": safe}}),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
