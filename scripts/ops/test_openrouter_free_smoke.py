"""No generation, paid calls, model downloads, real keys, or real Docker mutations."""

from __future__ import annotations

import copy
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ops import openrouter_free_smoke as smoke


def metadata() -> tuple[dict, dict, dict]:
    model = {
        "id": smoke.MODEL,
        "canonical_slug": smoke.CANONICAL,
        "pricing": {"prompt": "0", "completion": "0"},
        "architecture": {"output_modalities": ["text"]},
        "supported_parameters": ["max_tokens", "temperature", "response_format"],
        "reasoning": {"mandatory": False, "default_enabled": False},
    }
    endpoint = {
        "tag": smoke.ROUTE,
        "provider_name": "Google AI Studio",
        "status": 0,
        "pricing": {"prompt": "0", "completion": "0"},
        "supported_parameters": ["max_tokens", "temperature", "response_format"],
        "context_length": 262144,
        "max_completion_tokens": 32768,
    }
    return (
        {"data": [copy.deepcopy(model)]},
        {"data": model},
        {"data": {"id": smoke.MODEL, "endpoints": [endpoint]}},
    )


class MetadataTests(unittest.TestCase):
    def test_explicit_free_variant_and_omitted_request_fee(self) -> None:
        result = smoke.validate_metadata(*metadata())
        self.assertEqual(
            result["request_price"], "not_applicable_omitted_for_free_variant"
        )
        self.assertEqual(result["response_format"], "json_object")

    def test_rejects_paid_canonical_details(self) -> None:
        catalog, model, endpoints = metadata()
        endpoints["data"]["id"] = smoke.MODEL.removesuffix(":free")
        with self.assertRaisesRegex(smoke.Failure, "different_variant"):
            smoke.validate_metadata(catalog, model, endpoints)

    def test_zero_price_is_explicit_finite_nonnegative_zero(self) -> None:
        for invalid in (None, True, "NaN", "Infinity", "0.000001", "-0.1", "unknown"):
            with self.subTest(invalid=invalid):
                self.assertFalse(smoke.zero_price({"prompt": invalid}, "prompt"))
        self.assertFalse(smoke.zero_price({}, "prompt"))
        self.assertTrue(smoke.zero_price({}, "request", optional=True))

    def test_rejects_fee_route_drift_and_missing_capabilities(self) -> None:
        changes = [
            ("pricing", {"prompt": "0.01", "completion": "0"}),
            ("pricing", {"prompt": "0", "completion": "0", "request": "1"}),
            ("status", 1),
            ("supported_parameters", ["max_tokens"]),
            ("max_completion_tokens", 512),
            ("tag", smoke.ROUTE + "/other"),
        ]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                catalog, model, endpoints = metadata()
                endpoints["data"]["endpoints"][0][field] = value
                with self.assertRaises(smoke.Failure):
                    smoke.validate_metadata(catalog, model, endpoints)

    def test_rejects_ambiguous_prefix_even_when_other_variant_is_paid(self) -> None:
        catalog, model, endpoints = metadata()
        other = copy.deepcopy(endpoints["data"]["endpoints"][0])
        other.update(
            {
                "tag": smoke.ROUTE + "/paid",
                "pricing": {"prompt": "1", "completion": "1"},
            }
        )
        endpoints["data"]["endpoints"].append(other)
        with self.assertRaisesRegex(smoke.Failure, "ambiguous"):
            smoke.validate_metadata(catalog, model, endpoints)

    def test_optional_reasoning_must_be_explicit(self) -> None:
        catalog, model, endpoints = metadata()
        for reasoning in ({}, {"mandatory": True}):
            model["data"]["reasoning"] = reasoning
            with self.assertRaisesRegex(smoke.Failure, "optional"):
                smoke.validate_metadata(catalog, model, endpoints)

    def test_public_metadata_is_get_only_without_credentials(self) -> None:
        response = io.BytesIO(b'{"data": []}')
        response.geturl = lambda: smoke.API + "/models"
        with patch.object(smoke, "urlopen", return_value=response) as mocked:
            self.assertEqual(smoke.get_public("/models"), {"data": []})
        request = mocked.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIsNone(request.data)
        self.assertNotIn("Authorization", request.headers)


class IsolationTests(unittest.TestCase):
    def test_private_profile_is_gitignored_and_outside_docker_context(self) -> None:
        self.assertIn(".maos/", (smoke.ROOT / ".gitignore").read_text().splitlines())
        self.assertIn(
            ".maos/", (smoke.ROOT / "backend/.dockerignore").read_text().splitlines()
        )
        self.assertFalse(smoke.PRIVATE.is_relative_to(smoke.ROOT / "backend"))

    def test_compose_preserves_only_explicit_cli_profile_and_prevents_overrides(
        self,
    ) -> None:
        self.assertEqual(
            smoke.safe_compose_arguments(
                ["--profile", "cli", "run", "--rm", "cli", "auth", "login"]
            ),
            ["--profile", "cli", "run", "--no-build", "--rm", "cli", "auth", "login"],
        )
        self.assertEqual(
            smoke.safe_compose_arguments(
                ["exec", "api", "python", "-m", "app.cli", "doctor"]
            )[0],
            "exec",
        )
        for arguments in (
            ["down", "-v"],
            ["down", "--volumes=true"],
            ["run", "-eKEY=secret", "cli"],
            ["up", "--pull=always"],
            ["--profile", "ollama", "up"],
            ["config", "--format", "json"],
            ["run", "-v/shared:/cli", "cli"],
            ["run", "--privileged", "cli"],
        ):
            with self.subTest(arguments=arguments), self.assertRaises(smoke.Failure):
                smoke.safe_compose_arguments(arguments)

    def test_effective_compose_rejects_shared_cli_credentials_and_environment_drift(
        self,
    ) -> None:
        directory = Path("/private/test")
        config = {
            "COMPOSE_PROJECT_NAME": "maos-or-free-test",
            "MAOS_API_PORT": "58031",
            "OPENROUTER_PROVIDER_PREFERENCES": json.dumps(smoke.PREFERENCES),
            "OPENROUTER_API_KEY": "",
            "DATABASE_URL": "dedicated-db",
            "LLM_MODEL": smoke.MODEL,
            "MAX_PROVIDER_CALLS": "2",
            "LLM_MAX_RETRIES": "0",
            "LLM_MAX_OUTPUT_TOKENS": "1024",
            "POSTGRES_DB": "maos_or_free_test",
            "POSTGRES_USER": "maos_or_free_test",
        }
        manifest = {
            "project": config["COMPOSE_PROJECT_NAME"],
            "image_id": "sha256:" + "a" * 64,
        }
        resolved = {
            "name": manifest["project"],
            "services": {
                name: {"image": manifest["image_id"], "environment": config.copy()}
                for name in ("api", "worker", "cli")
            },
            "volumes": {
                "maos_postgres_data": {
                    "name": manifest["project"] + "_maos_postgres_data"
                }
            },
        }
        resolved["services"]["api"]["ports"] = [
            {"host_ip": "127.0.0.1", "published": "58031"}
        ]
        resolved["services"]["cli"]["volumes"] = [
            {"source": str(directory / "cli"), "target": "/cli"}
        ]
        resolved["services"]["postgres"] = {
            "environment": {
                "POSTGRES_DB": config["POSTGRES_DB"],
                "POSTGRES_USER": config["POSTGRES_USER"],
            },
            "volumes": [
                {
                    "type": "volume",
                    "source": "maos_postgres_data",
                    "target": "/var/lib/postgresql/data",
                }
            ],
        }
        for drift in (None, "mount", "env", "volume", "port", "image"):
            changed = copy.deepcopy(resolved)
            if drift == "mount":
                changed["services"]["cli"]["volumes"][0][
                    "source"
                ] = "/operator/.maos/cli"
            elif drift == "env":
                changed["services"]["worker"]["environment"][
                    "OPENROUTER_API_KEY"
                ] = "host-key"
            elif drift == "volume":
                changed["volumes"]["maos_postgres_data"]["name"] = "operator-data"
            elif drift == "port":
                changed["services"]["api"]["ports"][0]["host_ip"] = "0.0.0.0"
            elif drift == "image":
                changed["services"]["api"]["image"] = "mutable:latest"
            with self.subTest(drift=drift), patch.object(
                smoke,
                "process",
                return_value=subprocess.CompletedProcess(
                    [], 0, json.dumps(changed), ""
                ),
            ):
                if drift:
                    with self.assertRaises(smoke.Failure):
                        smoke.resolved_compose(directory, config, manifest)
                else:
                    smoke.resolved_compose(directory, config, manifest)

    def test_host_key_and_all_private_config_and_compose_overrides_are_removed(
        self,
    ) -> None:
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "host-key",
                "COMPOSE_FILE": "other.yml",
                "COMPOSE_PROJECT_NAME": "operator-data",
                "LLM_MODEL": "paid-model",
                "PATH": "/bin",
            },
            clear=True,
        ):
            self.assertEqual(
                smoke.sanitized_environment({"LLM_MODEL": smoke.MODEL}),
                {"PATH": "/bin"},
            )

    def test_private_file_write_never_overwrites_exclusive_reservation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "attempt.json"
            smoke.save_json(path, {"attempt": 1}, exclusive=True)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                smoke.save_json(path, {"attempt": 2}, exclusive=True)
            self.assertEqual(json.loads(path.read_text()), {"attempt": 1})

    def test_prepare_uses_existing_image_config_init_without_network_and_blank_key(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            identity = "sha256:" + "a" * 64
            calls = []

            def fake_process(arguments, config):
                calls.append(arguments)
                if arguments[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(
                        arguments,
                        0,
                        (identity if arguments[-1] == "{{.Id}}" else "b" * 40) + "\n",
                        "",
                    )
                smoke.private_write(
                    directory / "private.env",
                    "POSTGRES_PASSWORD=generated-private\nJWT_SECRET_KEY=generated-private-jwt\n",
                )
                (directory / "cli").mkdir(mode=0o700)
                return subprocess.CompletedProcess(arguments, 0, "", "")

            with patch.object(smoke, "process", side_effect=fake_process), patch.object(
                smoke, "available_port", return_value=58031
            ):
                result = smoke.prepare(directory, "dedicated:test")
            config = smoke.read_config(directory / "private.env")
            self.assertEqual(result["inference"], "NOT_RUN")
            self.assertEqual(config["OPENROUTER_API_KEY"], "")
            self.assertEqual(config["LLM_MAX_RETRIES"], "0")
            self.assertEqual(
                json.loads(config["OPENROUTER_PROVIDER_PREFERENCES"]), smoke.PREFERENCES
            )
            self.assertEqual((directory / "input.txt").read_text(), "")
            self.assertIn("none", calls[2])
            self.assertEqual(
                calls[2][-5:],
                ["app.cli", "config", "init", "--output", "/config/private.env"],
            )
            config, manifest = smoke.load_private(directory)
            overlay = json.loads((directory / "compose.private.json").read_text())
            self.assertEqual(
                overlay["services"]["cli"]["volumes"],
                [str(directory / "cli") + ":/cli"],
            )
            self.assertEqual(manifest["image_id"], identity)
            with self.assertRaisesRegex(smoke.Failure, "no_overwrites"):
                smoke.prepare(directory, "dedicated:test")

    def test_missing_approval_never_runs_preflight_or_reserves_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            smoke, "preflight"
        ) as preflight:
            with self.assertRaisesRegex(smoke.Failure, "approval"):
                smoke.run_once(Path(temporary), False)
            preflight.assert_not_called()
            self.assertFalse((Path(temporary) / "attempt.json").exists())

    def test_get_only_evidence_retains_partial_reads_and_uses_api_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            auth = directory / "auth.json"
            smoke.private_write(auth, '{"access_token":"api-session-only"}')
            smoke.private_write(
                directory / "live.stdout.json",
                '{"status":"FAIL","run_id":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}\n',
            )
            smoke.private_write(directory / "live.stderr.json", "")
            requests = []

            def fake_get(request, **kwargs):
                requests.append(request)
                self.assertEqual(request.get_method(), "GET")
                self.assertEqual(
                    request.get_header("Authorization"), "Bearer api-session-only"
                )
                self.assertIsNone(request.data)
                if request.full_url.endswith("/nodes"):
                    raise OSError("arbitrary sensitive remote error")
                return io.BytesIO(b'{"state":"partial"}')

            with patch.object(smoke, "urlopen", side_effect=fake_get):
                result = smoke.collect_evidence(
                    directory,
                    {
                        "MAOS_API_PORT": "58031",
                        "OPENROUTER_API_KEY": "never-use-provider-key",
                    },
                    auth,
                )
            self.assertEqual(result, "saved_privately_partial")
            self.assertEqual(len(requests), 4)
            evidence = (directory / "api-evidence.json").read_text()
            self.assertIn('"state": "partial"', evidence)
            self.assertIn('"code": "OSError"', evidence)
            self.assertNotIn("sensitive", evidence)
            self.assertNotIn("never-use-provider-key", evidence)

    def test_failed_live_attempt_is_permanently_reserved_with_private_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "cli").mkdir()
            smoke.private_write(
                directory / "cli/auth.json", '{"access_token":"dedicated-api-session"}'
            )
            smoke.private_write(
                directory / "input.txt", "User supplied nonsensitive text"
            )
            config = {
                "MAOS_API_PORT": "58031",
                "OPENROUTER_API_KEY": "dedicated-provider-key",
            }

            def fake_run(arguments, **kwargs):
                self.assertTrue((directory / "attempt.json").exists())
                self.assertEqual(
                    arguments[-5:],
                    ["--approve", "--max-calls", "2", "--max-output-tokens", "1024"],
                )
                self.assertNotIn("OPENROUTER_API_KEY", kwargs["env"])
                kwargs["stderr"].write(
                    '{"status":"FAIL","code":"partial_failure","run_id":null}\n'
                )
                return subprocess.CompletedProcess(arguments, 1)

            with patch.object(smoke, "preflight"), patch.object(
                smoke, "load_private", return_value=(config, {"project": "dedicated"})
            ), patch.object(
                smoke.subprocess, "run", side_effect=fake_run
            ) as runner, patch.dict(
                os.environ, {"OPENROUTER_API_KEY": "must-not-reuse"}
            ):
                result = smoke.run_once(directory, True)
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["api_evidence"], "no_run_id_observed")
                with self.assertRaisesRegex(smoke.Failure, "already_reserved"):
                    smoke.run_once(directory, True)
                self.assertEqual(runner.call_count, 1)
            for path in directory.glob("*.json"):
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
