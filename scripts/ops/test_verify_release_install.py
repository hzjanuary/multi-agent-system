"""Clean installation must resist CI environment overrides without inference."""

import argparse
import copy
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.ops import verify_release_install as install


def profile():
    values = dict(
        line.split("=", 1)
        for line in (install.ROOT / "backend/app/config/default.env")
        .read_text()
        .splitlines()
        if "=" in line and not line.startswith("#")
    )
    values.update(
        POSTGRES_PASSWORD=secrets.token_urlsafe(32),
        JWT_SECRET_KEY=secrets.token_urlsafe(48),
        MAOS_UID=str(os.getuid()),
        MAOS_GID=str(os.getgid()),
        COMPOSE_PROJECT_NAME="maos-spec030-unit",
        MAOS_IMAGE="multi-agent-os:unit",
        APP_ENV="production",
        LLM_MODEL="packaging-check-no-inference",
        OLLAMA_BASE_URL="http://127.0.0.1:9",
        LLM_MAX_RETRIES="0",
        MAOS_EXTENSION_MODULES="maos_examples.text_review",
        MAX_PROVIDER_CALLS="2",
    )
    values["DATABASE_URL"] = (
        "postgresql+asyncpg://maos:"
        + values["POSTGRES_PASSWORD"]
        + "@postgres:5432/maos"
    )
    return values


def resolved(values):
    runtime = {key: value.strip('"') for key, value in values.items()}
    return {
        "name": values["COMPOSE_PROJECT_NAME"],
        "services": {
            **{
                name: {
                    "image": values["MAOS_IMAGE"],
                    "environment": copy.deepcopy(runtime),
                }
                for name in ("api", "worker", "cli")
            },
            "postgres": {
                "environment": {
                    key: values[key]
                    for key in ("POSTGRES_PASSWORD", "POSTGRES_USER", "POSTGRES_DB")
                }
            },
        },
    }


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.values = profile()
        host_database = (
            "postgresql+asyncpg://maos:"
            + secrets.token_urlsafe(24)
            + "@localhost:5432/ci_host_db"
        )
        self.hostile = {
            "DATABASE_URL": host_database,
            "REDIS_URL": "redis://localhost:6379/15",
            "JWT_SECRET_KEY": secrets.token_urlsafe(48),
            "APP_ENV": "testing",
            "LLM_PROVIDER": "groq",
            "LLM_MODEL": "wrong-host-model",
            "GROQ_API_KEY": secrets.token_urlsafe(40),
            "COMPOSE_FILE": "wrong.yml",
            "COMPOSE_PROJECT_NAME": "do-not-use-parent",
            "MAOS_API_URL": "http://localhost:1",
            "MAOS_AUTH_FILE": "/parent/auth.json",
            "NEW_FUTURE_RUNTIME_SETTING": "host-value",
        }

    def test_subprocess_environment_is_positive_host_allowlist(self):
        with patch.dict(os.environ, self.hostile):
            executor = install.Executor()
        self.assertTrue(set(executor.environment) <= install.HOST_ENV)
        self.assertFalse(set(self.hostile) & executor.environment.keys())
        self.assertEqual(executor.environment.get("PATH"), os.environ.get("PATH"))
        for key in ("DOCKER_HOST", "DOCKER_CONFIG", "SSH_AUTH_SOCK", "HTTPS_PROXY"):
            self.assertEqual(
                install.isolated_environment({key: "synthetic"}), {key: "synthetic"}
            )

    @unittest.skipUnless(
        shutil.which("docker"), "Docker Compose required; no containers started"
    )
    def test_actual_compose_resolution_ignores_hostile_parent_for_api_worker_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            envfile = Path(directory) / "profile.env"
            envfile.write_text(
                "\n".join(key + "=" + value for key, value in self.values.items())
            )
            envfile.chmod(0o600)
            with patch.dict(os.environ, self.hostile):
                executor = install.Executor()
                actual = json.loads(
                    executor(
                        [
                            "docker",
                            "compose",
                            "--env-file",
                            str(envfile),
                            "--project-name",
                            self.values["COMPOSE_PROJECT_NAME"],
                            "-f",
                            str(install.ROOT / "docker-compose.yml"),
                            "--profile",
                            "cli",
                            "config",
                            "--format",
                            "json",
                        ],
                        operation="resolve_compose",
                    )
                )
            result = install.validate_configuration(actual, self.values)
            self.assertEqual(result["database_host"], "postgres")
            self.assertEqual(result["redis_host"], "redis")
            for name in ("api", "worker", "cli"):
                env = actual["services"][name]["environment"]
                for key in (
                    "DATABASE_URL",
                    "REDIS_URL",
                    "JWT_SECRET_KEY",
                    "APP_ENV",
                    "LLM_MODEL",
                ):
                    self.assertEqual(env[key], self.values[key])
            self.assertNotIn(self.values["POSTGRES_PASSWORD"], json.dumps(result))

    def test_host_database_jwt_model_and_provider_leaks_fail_closed(self):
        for name in ("api", "worker", "cli"):
            for key in (
                "DATABASE_URL",
                "REDIS_URL",
                "JWT_SECRET_KEY",
                "APP_ENV",
                "LLM_MODEL",
                "GROQ_API_KEY",
            ):
                config = resolved(self.values)
                config["services"][name]["environment"][key] = self.hostile[key]
                with self.subTest(service=name, key=key), self.assertRaises(
                    install.VerificationFailure
                ) as error:
                    install.validate_configuration(config, self.values)
                self.assertEqual(
                    error.exception.detail["category"], "isolated_profile_mismatch"
                )
                self.assertNotIn(self.hostile[key], str(error.exception))

    def test_failure_exit_and_stage_safe_public_diagnostics(self):
        with patch.dict(os.environ, self.hostile):
            executor = install.Executor()
        executor.stage = "migration"
        secret = self.values["JWT_SECRET_KEY"]
        with patch.object(
            install.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(
                ["docker"], 17, stdout=secret, stderr=secret
            ),
        ) as process, self.assertRaises(install.VerificationFailure) as error:
            executor(["docker", "compose"], operation="migrate", stdin=secret)
        self.assertEqual(
            error.exception.detail,
            dict(
                stage="migration",
                operation="migrate",
                category="subprocess_exit",
                exit_code=17,
            ),
        )
        self.assertEqual(process.call_args.kwargs["env"], executor.environment)
        proof = dict(
            status="FAIL",
            failure=error.exception.detail,
            generation_requests=0,
            records=executor.records,
            environment=self.hostile,
            doctor={"secret": secret},
        )
        public = json.dumps(install.public_summary(proof))
        self.assertNotIn(secret, public)
        self.assertNotIn("stdout", public)
        self.assertEqual(executor.records[0]["stderr"], secret)  # Private only.

    def test_timeout_has_safe_category_and_no_exception_body(self):
        executor = install.Executor()
        with patch.object(
            install.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(
                self.values["JWT_SECRET_KEY"],
                180,
                output=self.values["POSTGRES_PASSWORD"],
            ),
        ), self.assertRaises(install.VerificationFailure) as error:
            executor(["docker"], operation="start_dependencies")
        self.assertEqual(error.exception.detail["category"], "process_timeout")
        self.assertNotIn(self.values["JWT_SECRET_KEY"], str(error.exception))

    def test_service_status_drops_arbitrary_output(self):
        secret = self.values["POSTGRES_PASSWORD"]
        output = json.dumps(
            [
                dict(
                    Service="api",
                    State="exited",
                    Health="",
                    ExitCode=2,
                    Command=secret,
                    Environment={"secret": secret},
                ),
                dict(Service="unknown-" + secret, State=secret),
            ]
        )
        status = install.service_status(output)
        self.assertEqual(status["services"]["api"]["exit_code"], 2)
        self.assertNotIn(secret, json.dumps(status))
        self.assertEqual(
            install.service_status("not JSON"), {"collection": "unavailable"}
        )

    def test_existing_evidence_and_resources_are_never_overwritten_or_stopped(self):
        with tempfile.TemporaryDirectory() as directory:
            args = argparse.Namespace(
                directory=Path(directory), project="maos-spec030-existing"
            )
            marker = Path(directory) / "attempt.json"
            marker.write_text("preserve")
            executor = install.Executor()
            with patch.object(install.subprocess, "run") as process, self.assertRaises(
                install.VerificationFailure
            ):
                install.rehearse(args, executor, {})
            process.assert_not_called()
            self.assertEqual(marker.read_text(), "preserve")
        with tempfile.TemporaryDirectory() as directory:
            args.directory = Path(directory) / "new"
            with patch.object(
                install.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, "existing-id", ""),
            ) as process, self.assertRaises(install.VerificationFailure):
                install.rehearse(args, executor, {})
            self.assertEqual(process.call_count, 1)
            self.assertFalse(args.directory.exists())

    def test_failure_preserves_proof_and_stops_only_created_project_services(self):
        with tempfile.TemporaryDirectory() as directory:
            args = argparse.Namespace(
                directory=Path(directory) / "clone",
                project="maos-spec030-unit",
                image="multi-agent-os:unit",
                source="unit-revision",
            )
            executor = install.Executor()
            calls = []

            def fake(command, **kwargs):
                calls.append(command)
                if command[:3] == ["git", "rev-parse", "HEAD"]:
                    output = args.source
                elif command[:3] == ["docker", "image", "inspect"]:
                    output = json.dumps(
                        [
                            {
                                "Config": {
                                    "Labels": {
                                        "org.opencontainers.image.revision": args.source
                                    }
                                },
                                "Id": "sha256:unit",
                            }
                        ]
                    )
                elif command[:2] == ["git", "clone"]:
                    args.directory.mkdir()
                    output = ""
                elif "init" in command:
                    (args.directory / ".maos/.env").write_text(
                        "\n".join(k + "=" + v for k, v in self.values.items())
                    )
                    output = ""
                elif "config" in command and "json" in command:
                    output = json.dumps(
                        resolved(
                            dict(
                                line.split("=", 1)
                                for line in (args.directory / ".maos/.env")
                                .read_text()
                                .splitlines()
                            )
                        )
                    )
                elif "migrate" in command:
                    return subprocess.CompletedProcess(
                        command, 29, "", self.values["JWT_SECRET_KEY"]
                    )
                elif "--all" in command:
                    output = json.dumps(
                        [
                            dict(
                                Service="postgres",
                                State="exited",
                                Health="",
                                ExitCode=0,
                            )
                        ]
                    )
                else:
                    output = ""
                return subprocess.CompletedProcess(command, 0, output, "")

            proof = dict(status="FAIL", containers_start_attempted=False)
            with patch.object(
                install.subprocess, "run", side_effect=fake
            ), self.assertRaises(install.VerificationFailure) as error:
                install.rehearse(args, executor, proof)
            self.assertEqual(error.exception.detail["stage"], "migration")
            self.assertEqual(error.exception.detail["exit_code"], 29)
            self.assertTrue(proof["services_stopped_volumes_retained"])
            stops = [command for command in calls if "stop" in command]
            self.assertEqual(len(stops), 1)
            self.assertEqual(stops[0][-4:], list(install.SERVICES))
            self.assertIn(args.project, stops[0])
            self.assertFalse(any("down" in command for command in calls))
            self.assertTrue((args.directory / ".maos/.env").exists())
            self.assertTrue(
                (args.directory / ".maos/verification-admin-password").exists()
            )

    def test_private_records_have_restrictive_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proof.json"
            install.private_json(path, {"value": self.values["POSTGRES_PASSWORD"]})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_main_refusal_preserves_existing_private_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "existing"
            private = target / ".maos"
            private.mkdir(parents=True)
            evidence = private / "install-evidence.json"
            evidence.write_text("historical-proof")
            public = Path(directory) / "public-summary.json"
            arguments = [
                "verify_release_install",
                "--image",
                "unused:unit",
                "--source",
                "unit-revision",
                "--directory",
                str(target),
                "--project",
                "maos-spec030-unit",
                "--public-diagnostic",
                str(public),
            ]
            with patch.object(sys, "argv", arguments), patch(
                "builtins.print"
            ), self.assertRaises(SystemExit) as error:
                install.main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(evidence.read_text(), "historical-proof")
            self.assertFalse(
                json.loads(public.read_text())["containers_start_attempted"]
            )

    def test_ci_retains_only_allowlisted_install_summary(self):
        workflow = (install.ROOT / ".github/workflows/ci.yml").read_text()
        upload = workflow.split("Retain sanitized release proof", 1)[1]
        self.assertIn("if: always()", upload)
        self.assertIn(".maos/clean-install-summary.json", upload)
        self.assertNotIn("install-evidence.json", upload)
        self.assertNotIn("process-records.json", upload)
        self.assertNotIn(".maos/**", upload)
