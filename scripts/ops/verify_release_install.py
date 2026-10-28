"""Non-inference clean-clone rehearsal with isolated configuration and safe proof."""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
# Host/Docker client settings only. Never inherit application, provider or Compose
# interpolation variables (including variables newly added to the application).
HOST_ENV = {
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "TMPDIR",
    "TMP",
    "TEMP",
    "LANG",
    "LC_ALL",
    "XDG_CONFIG_HOME",
    "XDG_RUNTIME_DIR",
    "SSH_AUTH_SOCK",
    "DOCKER_HOST",
    "DOCKER_CONTEXT",
    "DOCKER_CONFIG",
    "DOCKER_TLS_VERIFY",
    "DOCKER_CERT_PATH",
    "DOCKER_API_VERSION",
    "DOCKER_TLS",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "no_proxy",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
}
SERVICES = ("api", "worker", "postgres", "redis")


def isolated_environment(parent=None):
    parent = os.environ if parent is None else parent
    return {key: value for key, value in parent.items() if key in HOST_ENV}


def private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Set permissions before writing, even with an ordinary caller umask.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


class VerificationFailure(RuntimeError):
    def __init__(self, stage, operation, category, exit_code=None):
        self.detail = dict(
            stage=stage, operation=operation, category=category, exit_code=exit_code
        )
        super().__init__(category)  # No command, output, environment or stdin.


class Executor:
    def __init__(self):
        self.environment = isolated_environment()
        self.stage = "preflight"
        self.operation = "initialize"
        self.records = []

    def __call__(self, command, *, operation, cwd=None, stdin=None, allowed=(0,)):
        self.operation = operation  # Call-site constant, never derived from output.
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=self.environment,
                input=stdin,
                text=True,
                capture_output=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            raise VerificationFailure(
                self.stage, operation, "process_timeout"
            ) from None
        except OSError:
            raise VerificationFailure(
                self.stage, operation, "process_unavailable"
            ) from None
        self.records.append(
            dict(
                stage=self.stage,
                operation=operation,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        if result.returncode not in allowed:
            raise VerificationFailure(
                self.stage, operation, "subprocess_exit", result.returncode
            )
        return result.stdout


def validate_configuration(config, profile):
    """Compare secrets in memory; export only booleans and fixed safe hostnames."""
    try:
        services = config["services"]
        expected_db = urlsplit(profile["DATABASE_URL"])
        if (
            expected_db.hostname != "postgres"
            or not expected_db.password
            or expected_db.password != profile["POSTGRES_PASSWORD"]
            or expected_db.username != profile["POSTGRES_USER"]
            or expected_db.path != "/" + profile["POSTGRES_DB"]
            or not profile["JWT_SECRET_KEY"]
        ):
            raise ValueError
        for name in ("api", "worker", "cli"):
            actual = services[name]["environment"]
            for key in (
                "DATABASE_URL",
                "JWT_SECRET_KEY",
                "REDIS_URL",
                "APP_ENV",
                "LLM_PROVIDER",
                "LLM_MODEL",
                "LLM_MAX_RETRIES",
                "MAX_PROVIDER_CALLS",
                "OLLAMA_BASE_URL",
                "MAOS_EXTENSION_MODULES",
            ):
                if actual[key] != profile[key]:
                    raise ValueError
            if (
                urlsplit(actual["DATABASE_URL"]).hostname != "postgres"
                or urlsplit(actual["REDIS_URL"]).hostname != "redis"
                or services[name]["image"] != profile["MAOS_IMAGE"]
            ):
                raise ValueError
            # Every generated runtime value must survive Compose interpolation.
            for key in actual.keys() & profile.keys():
                expected = profile[key].strip('"')
                if str(actual[key]) != expected:
                    raise ValueError
            if any(
                actual.get(key)
                for key in (
                    "GROQ_API_KEY",
                    "GEMINI_API_KEY",
                    "OPENROUTER_API_KEY",
                    "OPENAI_COMPATIBLE_API_KEY",
                    "OPENROUTER_PROVIDER_PREFERENCES",
                )
            ):
                raise ValueError
        pg = services["postgres"]["environment"]
        if (
            any(
                pg[key] != profile[key]
                for key in ("POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_USER")
            )
            or config["name"] != profile["COMPOSE_PROJECT_NAME"]
        ):
            raise ValueError
        cli = services["cli"]["environment"]
        if (
            cli["MAOS_API_URL"] != "http://api:8000"
            or cli["MAOS_AUTH_FILE"] != "/cli/auth.json"
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise VerificationFailure(
            "configuration", "validate_resolved_profile", "isolated_profile_mismatch"
        ) from None
    return dict(
        status="PASS",
        services=["api", "worker", "cli"],
        database_host="postgres",
        redis_host="redis",
        profile_credentials_match=True,
        provider_credentials_absent=True,
    )


def service_status(output):
    """Allowlisted states only; never container names, commands or environments."""
    try:
        rows = json.loads(output)
        rows = rows if isinstance(rows, list) else [rows]
    except ValueError:
        try:
            rows = [json.loads(line) for line in output.splitlines() if line]
        except ValueError:
            return {"collection": "unavailable"}
    statuses = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("Service") not in SERVICES:
            continue
        statuses[row["Service"]] = {
            "state": (
                row.get("State")
                if row.get("State")
                in {
                    "created",
                    "running",
                    "paused",
                    "restarting",
                    "removing",
                    "exited",
                    "dead",
                }
                else "unknown"
            ),
            "health": (
                row.get("Health")
                if row.get("Health") in {"", "healthy", "unhealthy", "starting"}
                else "unknown"
            ),
            "exit_code": (
                row.get("ExitCode") if type(row.get("ExitCode")) is int else None
            ),
        }
    return {"collection": "collected", "services": statuses}


def rehearse(args, execute, proof):
    directory = args.directory.resolve()
    if directory.exists() or not args.project.startswith("maos-spec030-"):
        raise VerificationFailure(
            "preflight", "reserve_project", "existing_or_invalid_project"
        )
    # Refuse all existing project resources before allowing cleanup of this project.
    for resource, command in (
        ("containers", ["docker", "ps", "-aq"]),
        ("networks", ["docker", "network", "ls", "-q"]),
        ("volumes", ["docker", "volume", "ls", "-q"]),
    ):
        if execute(
            command + ["--filter", "label=com.docker.compose.project=" + args.project],
            operation="check_existing_" + resource,
        ).strip():
            raise VerificationFailure(
                "preflight", "reserve_project", "existing_project_resources"
            )
    # Also detect an older/unlabelled volume of the canonical name.
    if execute(
        [
            "docker",
            "volume",
            "ls",
            "-q",
            "--filter",
            "name=^" + args.project + "_maos_postgres_data$",
        ],
        operation="check_existing_database_volume",
    ).strip():
        raise VerificationFailure(
            "preflight", "reserve_project", "existing_project_resources"
        )
    revision = execute(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, operation="source_revision"
    ).strip()
    info = json.loads(
        execute(["docker", "image", "inspect", args.image], operation="image_identity")
    )[0]
    if (
        info["Config"].get("Labels", {}).get("org.opencontainers.image.revision")
        != args.source
    ):
        raise VerificationFailure("preflight", "image_identity", "source_mismatch")
    proof.update(
        source_clone=revision,
        runtime_source=args.source,
        image=info["Id"],
        model_availability="NOT_CHECKED; closed loopback endpoint; no provider check",
    )
    directory.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    execute.stage = "clone"
    execute(
        ["git", "clone", "--quiet", "--no-local", str(ROOT), str(directory)],
        operation="clone_source",
    )
    execute(
        ["git", "checkout", "--quiet", revision],
        cwd=directory,
        operation="checkout_source",
    )
    directory.chmod(0o700)
    private = directory / ".maos"
    private.mkdir(mode=0o700)
    proof["private_evidence_created"] = True
    execute.stage = "configuration"
    execute(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--mount",
            f"type=bind,source={private},target=/config",
            args.image,
            "python",
            "-m",
            "app.cli",
            "config",
            "init",
            "--output",
            "/config/.env",
        ],
        operation="generate_private_profile",
    )
    envfile = private / ".env"
    env = dict(
        line.split("=", 1)
        for line in envfile.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )
    env.update(
        COMPOSE_PROJECT_NAME=args.project,
        MAOS_IMAGE=args.image,
        MAOS_API_PORT="18030",
        APP_ENV="production",
        REDIS_URL="redis://redis:6379/0",
        LLM_PROVIDER="ollama",
        LLM_MODEL="packaging-check-no-inference",
        OLLAMA_BASE_URL="http://127.0.0.1:9",
        MAOS_EXTENSION_MODULES="maos_examples.text_review",
        LLM_MAX_RETRIES="0",
        MAX_PROVIDER_CALLS="2",
    )
    envfile.write_text("\n".join(k + "=" + v for k, v in env.items()) + "\n")
    envfile.chmod(0o600)
    password = secrets.token_urlsafe(32)
    password_file = private / "verification-admin-password"
    password_file.touch(mode=0o600)
    password_file.write_text(password + "\n")
    base = [
        "docker",
        "compose",
        "--env-file",
        ".maos/.env",
        "--project-name",
        args.project,
    ]

    def compose(*arguments, operation, stdin=None):
        return execute(
            base + list(arguments), cwd=directory, stdin=stdin, operation=operation
        )

    def counts():
        return json.loads(
            compose(
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "maos",
                "-d",
                "maos",
                "-At",
                "-c",
                "SELECT json_build_object('users',(SELECT count(*) FROM users),'runs',(SELECT count(*) FROM runs),'events',(SELECT count(*) FROM run_events));",
                operation="database_counts",
            ).strip()
        )

    try:
        proof["resolved_configuration"] = validate_configuration(
            json.loads(
                compose(
                    "--profile",
                    "cli",
                    "config",
                    "--format",
                    "json",
                    operation="resolve_compose",
                )
            ),
            env,
        )
        execute(
            base
            + [
                "-f",
                "docker-compose.yml",
                "-f",
                "docker-compose.override.example.yml",
                "config",
                "--quiet",
            ],
            cwd=directory,
            operation="validate_development_compose",
        )
        execute.stage = "dependencies"
        # Set before dispatch: a failed 'up' can still have created containers.
        proof["containers_start_attempted"] = True
        compose(
            "up", "-d", "--wait", "postgres", "redis", operation="start_dependencies"
        )
        execute.stage = "migration"
        compose(
            "run",
            "--rm",
            "--no-deps",
            "api",
            "python",
            "-m",
            "app.cli",
            "migrate",
            operation="migrate",
        )
        proof["empty_after_migration"] = counts()
        if any(proof["empty_after_migration"].values()):
            raise VerificationFailure(
                "migration", "database_counts", "installation_not_empty"
            )
        execute.stage = "bootstrap"
        compose(
            "run",
            "--rm",
            "-T",
            "--no-deps",
            "api",
            "python",
            "-m",
            "app.cli",
            "admin",
            "bootstrap",
            "--email",
            "verification@example.invalid",
            "--password-stdin",
            stdin=password + "\n",
            operation="bootstrap_admin",
        )
        proof["after_explicit_bootstrap"] = counts()
        execute.stage = "runtime"
        compose("up", "-d", "--wait", "api", "worker", operation="start_application")
        proof["runtime_security_controls"] = {}
        for service in ("api", "worker"):
            container = compose(
                "ps", "--quiet", service, operation="identify_" + service
            ).strip()
            inspect = json.loads(
                execute(
                    ["docker", "inspect", container], operation="inspect_" + service
                )
            )[0]
            controls = {
                "cap_drop": inspect["HostConfig"].get("CapDrop"),
                "security_opt": inspect["HostConfig"].get("SecurityOpt"),
                "user": inspect["Config"].get("User"),
            }
            if (
                not any(v.lower() == "all" for v in (controls["cap_drop"] or []))
                or not any(
                    v.startswith("no-new-privileges")
                    for v in (controls["security_opt"] or [])
                )
                or controls["user"] in ("", "root", "0")
            ):
                raise VerificationFailure(
                    "runtime", "containment", "runtime_containment_mismatch"
                )
            proof["runtime_security_controls"][service] = controls
        proof["doctor"] = json.loads(
            compose(
                "exec",
                "-T",
                "api",
                "python",
                "-m",
                "app.cli",
                "--json",
                "doctor",
                operation="doctor",
            )
        )
        execute.stage = "cli"
        compose(
            "--profile",
            "cli",
            "run",
            "--rm",
            "-T",
            "cli",
            "auth",
            "login",
            "--email",
            "verification@example.invalid",
            "--password-stdin",
            stdin=password + "\n",
            operation="cli_login",
        )
        proof["workflow_discovery"] = json.loads(
            compose(
                "--profile",
                "cli",
                "run",
                "--rm",
                "-T",
                "cli",
                "--json",
                "workflow",
                "list",
                operation="workflow_discovery",
            )
        )
        proof["run_listing"] = json.loads(
            compose(
                "--profile",
                "cli",
                "run",
                "--rm",
                "-T",
                "cli",
                "--json",
                "run",
                "list",
                operation="run_listing",
            )
        )
        proof["auth_file_mode"] = oct(
            (private / "cli/auth.json").stat().st_mode & 0o777
        )
        if proof["auth_file_mode"] != "0o600":
            raise VerificationFailure(
                "cli", "auth_permissions", "private_file_permissions"
            )
        proof["final_counts"] = counts()
        proof["status"] = "PASS"
    except (OSError, ValueError, KeyError, TypeError):
        raise VerificationFailure(
            execute.stage, execute.operation, "invalid_or_unavailable_evidence"
        ) from None
    finally:
        if proof["containers_start_attempted"]:
            execute.stage = "cleanup"
            try:
                proof["service_status_before_stop"] = service_status(
                    compose(
                        "ps",
                        "--all",
                        "--format",
                        "json",
                        operation="collect_service_status",
                    )
                )
            except (VerificationFailure, ValueError):
                proof["service_status_before_stop"] = {"collection": "unavailable"}
            try:
                # Only the four services in our newly reserved project; never down/-v.
                compose("stop", *SERVICES, operation="stop_created_services")
                proof["service_status_after_stop"] = service_status(
                    compose(
                        "ps",
                        "--all",
                        "--format",
                        "json",
                        operation="verify_stopped_services",
                    )
                )
                stopped = proof["service_status_after_stop"]
                if stopped["collection"] != "collected" or any(
                    row["state"] not in {"exited", "dead", "created"}
                    for row in stopped["services"].values()
                ):
                    raise VerificationFailure(
                        "cleanup", "verify_stopped_services", "services_not_stopped"
                    )
                proof["services_stopped_volumes_retained"] = True
            except VerificationFailure:
                proof["services_stopped_volumes_retained"] = False
                proof["status"] = "FAIL"
                proof["cleanup_failure"] = True


def public_summary(proof):
    # A positive allowlist, independent of detailed private command/output records.
    keys = (
        "status",
        "source_clone",
        "runtime_source",
        "image",
        "generation_requests",
        "containers_start_attempted",
        "services_stopped_volumes_retained",
        "failure",
        "cleanup_failure",
        "resolved_configuration",
        "service_status_before_stop",
        "service_status_after_stop",
    )
    return {key: proof[key] for key in keys if key in proof}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--public-diagnostic",
        type=Path,
        default=ROOT / ".maos/clean-install-summary.json",
    )
    args = parser.parse_args()
    execute = Executor()
    proof = dict(
        status="FAIL",
        generation_requests=0,
        containers_start_attempted=False,
        services_stopped_volumes_retained=False,
    )
    try:
        rehearse(args, execute, proof)
    except VerificationFailure as error:
        proof["status"] = "FAIL"
        proof["failure"] = error.detail
    except (OSError, ValueError, KeyError, TypeError):
        proof["status"] = "FAIL"
        proof["failure"] = dict(
            stage=execute.stage,
            operation=execute.operation,
            category="invalid_or_unavailable_evidence",
            exit_code=None,
        )
    private = args.directory / ".maos"
    if proof.get("private_evidence_created"):
        private_json(private / "install-evidence.json", proof)
        private_json(private / "process-records.json", execute.records)
    summary = public_summary(proof)
    private_json(args.public_diagnostic, summary)
    print(json.dumps(summary))
    if proof["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
