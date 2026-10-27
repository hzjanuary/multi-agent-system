"""Non-inference clean-clone installation rehearsal; retains isolated state on stop."""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def execute(command, *, cwd=None, stdin=None):
    result = subprocess.run(
        command, cwd=cwd, input=stdin, text=True, capture_output=True, timeout=180
    )
    if result.returncode:
        # Responses/configuration never enter a public exception or terminal log.
        raise RuntimeError("verification command failed: " + command[0])
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if directory.exists() or not args.project.startswith("maos-spec030-"):
        raise SystemExit("Refusing existing directory or non-verification project")
    if (
        subprocess.run(
            ["docker", "volume", "inspect", args.project + "_maos_postgres_data"],
            capture_output=True,
        ).returncode
        == 0
    ):
        raise SystemExit("Refusing existing verification volume")
    revision = execute(["git", "rev-parse", "HEAD"], cwd=ROOT).strip()
    info = json.loads(execute(["docker", "image", "inspect", args.image]))[0]
    if (
        info["Config"].get("Labels", {}).get("org.opencontainers.image.revision")
        != args.source
    ):
        raise SystemExit("Image source mismatch")
    directory.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    execute(["git", "clone", "--quiet", "--no-local", str(ROOT), str(directory)])
    execute(["git", "checkout", "--quiet", revision], cwd=directory)
    directory.chmod(0o700)
    private = directory / ".maos"
    private.mkdir(mode=0o700)
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
        ]
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
    password_file.write_text(password + "\n")
    password_file.chmod(0o600)
    base = [
        "docker",
        "compose",
        "--env-file",
        ".maos/.env",
        "--project-name",
        args.project,
    ]
    proof = {
        "source_clone": revision,
        "runtime_source": args.source,
        "image": info["Id"],
        "project": args.project,
        "generation_requests": 0,
        "model_availability": "NOT_CHECKED; loopback closed endpoint; no provider check",
    }
    commands = []

    def compose(*arguments, stdin=None):
        commands.append(list(arguments))
        return execute(base + list(arguments), cwd=directory, stdin=stdin)

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
            ).strip()
        )

    try:
        compose("config", "--quiet")
        # Validate development Compose without emitting its resolved secrets.
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
        )
        compose("up", "-d", "--wait", "postgres", "redis")
        compose("run", "--rm", "--no-deps", "api", "python", "-m", "app.cli", "migrate")
        proof["empty_after_migration"] = counts()
        if any(proof["empty_after_migration"].values()):
            raise RuntimeError("installation not empty")
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
        )
        proof["after_explicit_bootstrap"] = counts()
        compose("up", "-d", "--wait", "api", "worker")
        proof["runtime_security_controls"] = {}
        for service in ("api", "worker"):
            container = compose("ps", "--quiet", service).strip()
            inspect = json.loads(execute(["docker", "inspect", container]))[0]
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
                raise RuntimeError("runtime containment not delivered")
            proof["runtime_security_controls"][service] = controls
        proof["doctor"] = json.loads(
            compose("exec", "-T", "api", "python", "-m", "app.cli", "--json", "doctor")
        )
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
        )
        workflows = json.loads(
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
            )
        )
        proof["workflow_discovery"] = workflows
        proof["run_listing"] = json.loads(
            compose(
                "--profile", "cli", "run", "--rm", "-T", "cli", "--json", "run", "list"
            )
        )
        proof["auth_file_mode"] = oct(
            (private / "cli/auth.json").stat().st_mode & 0o777
        )
        if proof["auth_file_mode"] != "0o600":
            raise RuntimeError("CLI file mode")
        proof["final_counts"] = counts()
        proof["status"] = "PASS"
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError):
        proof["status"] = "FAIL"
        proof["failure_operation"] = commands[-1] if commands else []
    finally:
        try:
            compose("stop")
            proof["services_stopped_volumes_retained"] = True
        except (RuntimeError, subprocess.SubprocessError):
            proof["services_stopped_volumes_retained"] = False
        proof["commands"] = commands
        evidence = private / "install-evidence.json"
        evidence.write_text(json.dumps(proof, indent=2) + "\n")
        evidence.chmod(0o600)
    print(
        json.dumps(
            {
                "status": proof["status"],
                "generation_requests": 0,
                "evidence": str(args.directory / ".maos/install-evidence.json"),
            }
        )
    )
    if proof["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
