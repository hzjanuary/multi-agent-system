"""Offline campaign tests; no Docker mutation, real secrets or generation."""

import io
import json
import subprocess
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.ops import direct_smoke_campaign as runner


def failed(code="provider_rate_limit", status=429, calls=1):
    return {
        "profile": "groq-smoke",
        "status": "FAIL",
        "run_status": "FAILED",
        "smoke_failure_code": "unexpected_run_outcome_FAILED",
        "calls": calls,
        "run_id": "11111111-1111-1111-1111-111111111111",
        "error": {"code": code},
        "nodes": [
            {
                "node_id": "analyze",
                "kind": "agent",
                "status": "FAILED",
                "execution_metadata": {"provider_diagnostics": {"http_status": status}},
            }
        ],
    }


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.legacy = self.root / "legacy"
        self.legacy.mkdir(mode=0o700)
        (self.legacy / "cli").mkdir(mode=0o700)
        runner.common.private_write(
            self.legacy / "input.txt", "ORIGINAL_NON_SENSITIVE_INPUT"
        )
        runner.common.private_write(self.legacy / "attempt.json", "original untouched")
        self.directory = self.root / "direct"
        self.addCleanup(patch.stopall)
        patch.object(runner, "ROOT", self.root).start()
        patch.object(runner, "PRIVATE", self.directory).start()
        patch.object(runner.common, "PRIVATE", self.legacy).start()
        self.base = {
            "COMPOSE_PROJECT_NAME": "maos-or-free-test",
            "DATABASE_URL": "postgresql+asyncpg://test:test@postgres/test",
            "POSTGRES_DB": "test",
            "POSTGRES_USER": "test",
            "POSTGRES_PASSWORD": "test-only",
            "JWT_SECRET_KEY": "test-app-secret",
            "JWT_ALGORITHM": "HS256",
            "MAOS_API_PORT": "58031",
            "MAOS_UID": "1000",
            "MAOS_GID": "1000",
            "MAOS_EXTENSION_MODULES": "maos_examples.text_review",
            "OPENROUTER_API_KEY": "test-old-or-secret",
            "OPENROUTER_PROVIDER_PREFERENCES": '{"data_collection":"allow"}',
        }
        patch.object(
            runner.common, "load_private", return_value=(self.base, {})
        ).start()
        patch.object(
            runner,
            "history_artifacts",
            return_value={
                "legacy/attempt.json": runner.digest(
                    (self.legacy / "attempt.json").read_bytes()
                )
            },
        ).start()

        def process(args, config):
            if "ps" in args:
                return subprocess.CompletedProcess(args, 0, "", "")
            if args[:3] == ["docker", "image", "inspect"]:
                return subprocess.CompletedProcess(
                    args,
                    0,
                    ("sha256:" + "a" * 64 if args[-1] == "{{.Id}}" else "b" * 40)
                    + "\n",
                    "",
                )
            raise AssertionError("Unexpected real command")

        patch.object(runner.common, "process", side_effect=process).start()
        runner.prepare("test-image")

    def ready(self):
        with patch.object(
            runner.getpass,
            "getpass",
            side_effect=["test-groq-key", "c" * 32, "test-cf-token"],
        ), patch("builtins.input", side_effect=["GROQ_FREE", "WORKERS_FREE"]), patch(
            "builtins.print"
        ):
            runner.credentials()

    def test_preparation_is_opt_in_blank_secrets_and_preserves_history(self):
        for name in runner.ORDER:
            c = runner.config_for(name)
            for key in runner.CREDENTIALS:
                self.assertEqual(c[key], "")
            self.assertEqual(
                (self.directory / name / "private.env").stat().st_mode & 0o777, 0o600
            )
        self.assertEqual(
            (self.legacy / "attempt.json").read_text(), "original untouched"
        )
        self.assertFalse((self.directory / "campaign.json").exists())
        with self.assertRaisesRegex(runner.Failure, "already_prepared"):
            runner.prepare("test-image")

    def test_credentials_mapping_and_plan_binding_never_mix_providers(self):
        self.ready()
        groq = runner.config_for(runner.ORDER[0], ready=True)
        cf = runner.config_for(runner.ORDER[1], ready=True)
        self.assertEqual(groq["GROQ_API_KEY"], "test-groq-key")
        self.assertEqual(groq["OPENAI_COMPATIBLE_API_KEY"], "")
        self.assertEqual(cf["GROQ_API_KEY"], "")
        self.assertEqual(cf["OPENAI_COMPATIBLE_API_KEY"], "test-cf-token")
        self.assertEqual(
            cf["OPENAI_COMPATIBLE_BASE_URL"],
            "https://api.cloudflare.com/client/v4/accounts/" + "c" * 32 + "/ai/v1",
        )
        cf["OPENAI_COMPATIBLE_API_KEY"] = "test-changed-key"
        runner.write_env(self.directory / runner.ORDER[1] / "private.env", cf)
        with self.assertRaisesRegex(runner.Failure, "reconfirm_free_plan"):
            runner.config_for(runner.ORDER[1], ready=True)

    def test_missing_credentials_causes_zero_generation_and_no_metadata(self):
        with patch.object(runner, "metadata_get") as get, patch.object(
            runner, "phase"
        ) as phase:
            with self.assertRaisesRegex(runner.Failure, "credentials"):
                runner.campaign(True)
            get.assert_not_called()
            phase.assert_not_called()
        self.assertFalse((self.directory / "campaign.json").exists())

    def test_metadata_is_get_only_and_preflight_uses_correct_keys(self):
        self.ready()
        data = [
            {"data": [{"id": runner.MODELS[runner.ORDER[0]], "active": True}]},
            {"success": True, "result": [{"name": runner.MODELS[runner.ORDER[1]]}]},
            {
                "success": True,
                "result": {
                    "input": {
                        "oneOf": [
                            {
                                "properties": {
                                    "max_tokens": {},
                                    "temperature": {},
                                    "response_format": {},
                                }
                            }
                        ]
                    }
                },
            },
        ]
        with patch.object(
            runner, "metadata_get", side_effect=data
        ) as get, patch.object(runner, "resolved"):
            result = runner.preflight()
            self.assertEqual(result["generation_requests"], 0)
            self.assertEqual(get.call_args_list[0].args[1], "test-groq-key")
            self.assertTrue(
                all(call.args[1] == "test-cf-token" for call in get.call_args_list[1:])
            )
            self.assertNotIn("test-cf-token", json.dumps(result))
        response = io.BytesIO(b'{"data":[]}')
        response.code = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/json"
        with patch.object(runner, "build_opener") as opener:
            opener.return_value.open.return_value = response
            runner.metadata_get("https://api.groq.com/openai/v1/models", "test-key")
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.get_method(), "GET")
            self.assertIsNone(request.data)
            self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
            self.assertEqual(
                request.get_header("User-agent"), runner.METADATA_USER_AGENT
            )
        with self.assertRaisesRegex(runner.Failure, "metadata_url"):
            runner.metadata_get(
                "https://openrouter.ai/api/v1/chat/completions", "test-key"
            )

    def test_metadata_errors_identify_target_not_edge_and_never_retain_secrets(self):
        for url, provider, operation, body, mime, code in (
            (
                "https://api.groq.com/openai/v1/models",
                "groq",
                "models.list",
                b"error code: 1010\n test-key PRIVATE_INPUT",
                "text/plain",
                1010,
            ),
            (
                "https://api.cloudflare.com/client/v4/accounts/"
                + "c" * 32
                + "/ai/models/search?search=model",
                "cloudflare",
                "models.search",
                b'{"success":false,"errors":[{"code":10000,"type":"authentication_error","message":"test-key PRIVATE_INPUT"}]}',
                "application/json",
                10000,
            ),
        ):
            headers = Message()
            headers["Content-Type"] = mime
            headers["Server"] = "cloudflare"
            headers["cf-ray"] = "123abc-SIN"
            headers["x-request-id"] = "metadata-request-1"
            error = HTTPError(url, 403, "not retained", headers, io.BytesIO(body))
            with self.subTest(provider=provider), patch.object(
                runner, "build_opener"
            ) as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaises(runner.MetadataFailure) as caught:
                    runner.metadata_get(url, "test-key")
                value = caught.exception.diagnostic
                self.assertEqual(value["target_provider"], provider)
                self.assertEqual(value["operation"], operation)
                self.assertEqual(value["http_status"], 403)
                self.assertEqual(value["error_code"], code)
                self.assertEqual(value["auth_scheme"], "Bearer")
                self.assertTrue(value["authorization_header_sent"])
                self.assertFalse(value["body_persisted"])
                self.assertEqual(
                    value["response_identifiers"]["header.cf-ray"]["value"],
                    "123abc-SIN",
                )
                self.assertEqual(
                    value["response_identifiers"]["header.x-groq-request-id"]["state"],
                    "not_returned",
                )
                opener.return_value.open.assert_called_once()
        for path in (self.directory / "metadata-diagnostics").glob("*.json"):
            text = path.read_text()
            self.assertNotIn("test-key", text)
            self.assertNotIn("PRIVATE_INPUT", text)
            self.assertNotIn("c" * 32, text)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_metadata_diagnostic_withholds_echoes_and_handles_html_or_missing_fields(
        self,
    ):
        class Response:
            code = 403
            headers = Message()

        target = runner.metadata_target("https://api.groq.com/openai/v1/models")
        response = Response()
        response.headers["x-request-id"] = "test-key"
        value = runner.metadata_diagnostic(
            target,
            response,
            b'{"error":{"code":"test-key","type":"Bearer-secret","message":"PRIVATE_INPUT"}}',
            "test-key",
            "https://api.groq.com/openai/v1/models",
        )
        self.assertEqual(value["content_type_state"], "not_returned")
        self.assertIsNone(value["error_code"])
        self.assertIsNone(value["error_type"])
        self.assertEqual(value["error_code_state"], "withheld_unsafe")
        self.assertEqual(value["error_type_state"], "withheld_unsafe")
        self.assertEqual(
            value["response_identifiers"]["header.x-request-id"]["state"],
            "withheld_unsafe",
        )
        self.assertNotIn("test-key", json.dumps(value))
        self.assertNotIn("PRIVATE_INPUT", json.dumps(value))
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        html = runner.metadata_diagnostic(
            target, response, b"<h1>Error 1010</h1><p>PRIVATE_INPUT</p>", "test-key", ""
        )
        self.assertEqual(html["response_kind"], "html")
        self.assertEqual(html["error_code"], 1010)
        self.assertNotIn("PRIVATE_INPUT", json.dumps(html))

    def test_metadata_exact_hosts_paths_and_no_redirect_forwarding(self):
        for url in (
            "https://api.groq.com/openai/v1/models/../chat/completions",
            "https://api.groq.com/openai/v1/models?other=secret",
            "https://api.groq.com.evil/openai/v1/models",
            "https://user@api.groq.com/openai/v1/models",
            "https://api.cloudflare.com/client/v4/accounts/"
            + "c" * 32
            + "/ai/v1/models",
        ):
            with self.subTest(url=url), patch.object(runner, "build_opener") as opener:
                with self.assertRaisesRegex(runner.Failure, "metadata_url"):
                    runner.metadata_get(url, "test-key")
                opener.assert_not_called()
        self.assertIsNone(
            runner.NoRedirect().redirect_request(
                None, None, 302, "", {}, "https://other.invalid"
            )
        )

    def test_groq_success_never_invokes_cloudflare(self):
        def execute(name):
            return {"profile": name, "status": "PASS", "calls": 2}

        with patch.object(runner, "phase", side_effect=execute) as phase, patch.object(
            runner, "activate"
        ) as switch:
            outcome = runner.execute_sequence(phase, switch)
            self.assertEqual(outcome["status"], "PASS")
            self.assertEqual(phase.call_count, 1)
            self.assertEqual(phase.call_args.args, ("groq-smoke",))
            switch.assert_not_called()
            self.assertEqual(outcome["cloudflare"], "UNUSED_NOT_LIVE_VERIFIED")

    def test_eligible_availability_failure_runs_only_one_separate_cloudflare_workflow(
        self,
    ):
        for code, status in [
            ("provider_rate_limit", 429),
            ("provider_timeout", None),
            ("provider_unavailable", None),
            ("provider_unavailable", 500),
            ("provider_unavailable", 502),
            ("provider_unavailable", 503),
            ("provider_unavailable", 504),
        ]:
            with self.subTest(code=code, status=status), patch.object(
                runner,
                "phase",
                side_effect=[
                    failed(code, status, 2),
                    {
                        "profile": "cloudflare-smoke",
                        "status": "PASS",
                        "calls": 2,
                        "run_id": "22222222-2222-2222-2222-222222222222",
                    },
                ],
            ) as phase, patch.object(runner, "activate") as switch:
                outcome = runner.execute_sequence(phase, switch)
                self.assertEqual(
                    [call.args for call in phase.call_args_list],
                    [("groq-smoke",), ("cloudflare-smoke",)],
                )
                self.assertNotEqual(
                    outcome["attempts"][0]["run_id"], outcome["attempts"][1]["run_id"]
                )
                self.assertEqual(sum(v["calls"] for v in outcome["attempts"]), 4)
                switch.assert_called_once_with("cloudflare-smoke")

    def test_fatal_errors_and_unsafe_states_do_not_trigger_fallback(self):
        variants = [
            failed("provider_configuration", 400),
            failed("provider_authentication", 401),
            failed("provider_authentication", 403),
            failed("provider_unknown", 402),
            failed("provider_invalid_response", 400),
            failed("provider_invalid_response", 200),
            failed("execution_failed", None),
            failed("provider_unavailable", 501),
            failed(calls=0),
        ]
        for state in (
            "RUNNING",
            "WAITING_APPROVAL",
            "APPROVED",
            "CANCELLED",
            "INTERRUPTED",
        ):
            v = failed()
            v["run_status"] = state
            variants.append(v)
        for hint in (
            "billing_required",
            "payment_required",
            "model_not_found",
            "unsupported_parameter",
            "invalid_api_key",
        ):
            v = failed("provider_unavailable", 500)
            v["nodes"][0]["execution_metadata"]["provider_diagnostics"][
                "error_code"
            ] = hint
            variants.append(v)
        v = failed()
        v["smoke_failure_code"] = "api_request_failed_HTTP_500"
        variants.append(v)
        for item in variants:
            with self.subTest(item=item), patch.object(runner, "activate") as switch:
                runner.execute_sequence(lambda name: item, switch)
                switch.assert_not_called()

    def test_cloudflare_failure_stops_without_third_provider(self):
        with patch.object(
            runner, "phase", side_effect=[failed(), failed("provider_unavailable", 503)]
        ) as phase, patch.object(runner, "activate") as switch:
            result = runner.execute_sequence(phase, switch)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(phase.call_count, 2)
            self.assertEqual(switch.call_count, 1)

    def test_per_provider_and_campaign_reinvocation_budget_guards(self):
        with self.assertRaisesRegex(runner.Failure, "provider_budget"):
            runner.execute_sequence(
                lambda name: {"status": "PASS", "calls": 3}, lambda name: None
            )
        runner.save(
            self.directory / "campaign.json", {"reserved": True}, exclusive=True
        )
        with patch.object(runner, "preflight") as preflight, patch.object(
            runner, "phase"
        ) as phase:
            with self.assertRaisesRegex(runner.Failure, "already_reserved"):
                runner.campaign(True)
            preflight.assert_not_called()
            phase.assert_not_called()

    def test_safe_switch_stops_services_and_refuses_active_work(self):
        self.ready()
        with patch.object(runner, "compose") as compose, patch.object(
            runner, "sql_read", return_value="1"
        ):
            with self.assertRaisesRegex(runner.Failure, "active_or_uncertain"):
                runner.activate("cloudflare-smoke")
            self.assertEqual(compose.call_count, 1)
            self.assertEqual(compose.call_args.args[1], ["stop", "api", "worker"])
        with patch.object(runner, "compose") as compose, patch.object(
            runner, "sql_read", return_value="0"
        ), patch.object(runner, "resolved"):
            runner.activate("cloudflare-smoke")
            self.assertEqual(
                compose.call_args_list[-1].args,
                ("cloudflare-smoke", ["up", "-d", "--wait", "api", "worker"]),
            )

    def test_each_phase_uses_original_input_and_own_pinned_env_and_marker(self):
        self.ready()
        m = runner.manifest()
        runner.common.private_write(
            self.legacy / "cli/auth.json", '{"access_token":"test-session"}'
        )
        commands = []

        def run(args, **kwargs):
            commands.append(args)
            return subprocess.CompletedProcess(args, 0)

        def collect(folder, config, auth):
            identifier = (
                "11111111-1111-1111-1111-111111111111"
                if folder.name == "groq-smoke"
                else "22222222-2222-2222-2222-222222222222"
            )
            runner.save(
                folder / "api-evidence.json",
                {
                    "run": {"id": identifier, "status": "COMPLETED", "call_count": 2},
                    "/nodes": [],
                },
                exclusive=True,
            )
            return "saved_privately_may_contain_user_text"

        with patch.object(runner.subprocess, "run", side_effect=run), patch.object(
            runner.common, "collect_evidence", side_effect=collect
        ), patch.object(runner, "verify_history", return_value=True):
            for name in runner.ORDER:
                runner.phase(name)
            with self.assertRaises(FileExistsError):
                runner.phase("groq-smoke")
        self.assertEqual(len(commands), 2)
        self.assertEqual(
            [cmd[cmd.index("--input") + 1] for cmd in commands], [m["input_file"]] * 2
        )
        self.assertEqual(
            [Path(cmd[cmd.index("--env-file") + 1]).parent.name for cmd in commands],
            list(runner.ORDER),
        )
        self.assertTrue(
            all(
                "--approve" in cmd and "--max-calls" in cmd and cmd[-1] == "1024"
                for cmd in commands
            )
        )
        self.assertEqual(
            (self.legacy / "attempt.json").read_text(), "original untouched"
        )

    def test_database_and_secret_identity_cannot_be_changed_per_profile(self):
        c = runner.config_for("groq-smoke")
        c["DATABASE_URL"] = "postgresql+asyncpg://other:other@host/prod"
        runner.write_env(self.directory / "groq-smoke/private.env", c)
        with self.assertRaisesRegex(runner.Failure, "database_or_auth"):
            runner.config_for("groq-smoke")

    def test_campaign_reservation_covers_both_runs_and_reinvocation(self):
        self.ready()
        outcomes = [
            failed(calls=2),
            {"profile": "cloudflare-smoke", "status": "PASS", "calls": 2},
        ]

        def execute(name):
            self.assertTrue((self.directory / "campaign.json").is_file())
            return outcomes.pop(0)

        with patch.object(runner, "preflight"), patch.object(
            runner, "resolved"
        ), patch.object(runner, "api_get"), patch.object(
            runner, "verify_history"
        ), patch.object(
            runner, "phase", side_effect=execute
        ) as phase, patch.object(
            runner, "activate"
        ), patch.object(
            runner, "compose"
        ):
            result = runner.campaign(True)
            self.assertEqual(result["new_consumed"], 4)
            self.assertEqual(result["cumulative_consumed"], 6)
            self.assertEqual(phase.call_count, 2)

            with self.assertRaisesRegex(runner.Failure, "already_reserved"):
                runner.campaign(True)
            self.assertEqual(phase.call_count, 2)

    def seal_parent(self):
        self.ready()
        run = {
            "id": "33333333-3333-3333-3333-333333333333",
            "status": "FAILED",
            "call_count": 1,
            "owner": None,
            "lease_expires_at": None,
        }
        runner.save(
            self.directory / "campaign.json", {"old_marker": True}, exclusive=True
        )
        runner.save(
            self.directory / "outcome.json",
            {
                "status": "FAIL",
                "new_consumed": 1,
                "cumulative_consumed": 3,
                "attempts": [
                    {"profile": "groq-smoke", "run_id": run["id"], "calls": 1}
                ],
            },
            exclusive=True,
        )
        runner.save(
            self.directory / "groq-smoke/api-evidence.json",
            {"run": run},
            exclusive=True,
        )
        runner.save(
            self.directory / "groq-smoke/attempt.json", {"consumed": 1}, exclusive=True
        )
        return run

    def test_additional_campaign_preserves_parent_and_allocates_once_across_ids(self):
        self.seal_parent()
        before = {p: p.read_bytes() for p in self.directory.rglob("*") if p.is_file()}
        result = runner.new_campaign("permission-fix")
        self.assertEqual(result["generation_requests"], 0)
        self.assertTrue(all(p.read_bytes() == raw for p, raw in before.items()))
        self.assertFalse(
            (self.directory / "campaigns/permission-fix/campaign.json").exists()
        )
        for identifier in ("permission-fix", "other-id"):
            with self.assertRaisesRegex(runner.Failure, "already_allocated"):
                runner.new_campaign(identifier)
        with self.assertRaisesRegex(runner.Failure, "already_reserved"):
            runner.campaign(True)
        runner.select_campaign("permission-fix")
        m = runner.manifest()
        self.assertEqual(
            (m["historical_consumed"], m["new_limit"], m["cumulative_limit"]), (3, 4, 7)
        )
        self.assertEqual(len(m["historical_runs"]), 3)
        for n in runner.ORDER:
            config = runner.config_for(n, ready=True)
            parent = runner.common.read_config(self.directory / n / "private.env")
            self.assertEqual(config, parent)

    def test_additional_campaign_requires_confirmed_history_terminal_parent_and_keys(
        self,
    ):
        run = self.seal_parent()
        for changed in (
            {"call_count": 2},
            {"status": "RUNNING"},
            {"owner": "worker"},
            {"lease_expires_at": "future"},
        ):
            runner.save(
                self.directory / "groq-smoke/api-evidence.json",
                {"run": {**run, **changed}},
            )
            with self.assertRaisesRegex(runner.Failure, "terminal"):
                runner.new_campaign("permission-fix")
            self.assertFalse((self.directory / "new-campaign.json").exists())
        runner.save(self.directory / "groq-smoke/api-evidence.json", {"run": run})
        for identifier in ("../escape", "UPPER", ""):
            with self.assertRaisesRegex(runner.Failure, "identifier"):
                runner.new_campaign(identifier)
        config = runner.config_for("groq-smoke")
        config["GROQ_API_KEY"] = ""
        runner.write_env(self.directory / "groq-smoke/private.env", config)
        with self.assertRaisesRegex(runner.Failure, "credentials"):
            runner.new_campaign("permission-fix")
        self.assertFalse((self.directory / "new-campaign.json").exists())

    def test_additional_campaign_validates_parent_artifacts_and_selection(self):
        self.seal_parent()
        runner.new_campaign("permission-fix")
        with self.assertRaisesRegex(runner.Failure, "not_authorized"):
            runner.select_campaign("different-id")
        runner.select_campaign("permission-fix")
        runner.save(self.directory / "campaign.json", {"modified": True})
        with self.assertRaisesRegex(runner.Failure, "historical_evidence_changed"):
            runner.manifest()

    def test_additional_campaign_checks_all_three_historical_runs(self):
        parent = self.seal_parent()
        (self.legacy / "attempts" / runner.common.ADDITIONAL_ID).mkdir(parents=True)
        records = [
            {"id": v, "status": "FAILED", "call_count": 1}
            for v in runner.HISTORICAL_RUNS
        ] + [parent]
        runner.save(self.legacy / "api-evidence.json", {"run": records[0]})
        runner.save(
            self.legacy
            / "attempts"
            / runner.common.ADDITIONAL_ID
            / "api-evidence.json",
            {"run": records[1]},
        )
        runner.new_campaign("permission-fix")
        runner.select_campaign("permission-fix")
        with patch.object(runner, "api_get", side_effect=records) as get:
            self.assertTrue(runner.verify_history("groq-smoke"))
            self.assertEqual(get.call_count, 3)

    def test_additional_campaign_four_new_seven_total_and_cannot_repeat(self):
        self.seal_parent()
        runner.new_campaign("permission-fix")
        runner.select_campaign("permission-fix")
        outcomes = [
            failed(calls=2),
            {"profile": "cloudflare-smoke", "status": "PASS", "calls": 2},
        ]

        def execute(name):
            marker = json.loads((runner.PRIVATE / "campaign.json").read_text())
            self.assertEqual(
                (
                    marker["historical_consumed"],
                    marker["new_reserved_max"],
                    marker["cumulative_max"],
                ),
                (3, 4, 7),
            )
            self.assertEqual(marker["campaign_id"], "permission-fix")
            return outcomes.pop(0)

        with patch.object(runner, "preflight"), patch.object(
            runner, "resolved"
        ), patch.object(runner, "api_get"), patch.object(
            runner, "verify_history"
        ), patch.object(
            runner, "phase", side_effect=execute
        ) as phase, patch.object(
            runner, "activate"
        ), patch.object(
            runner, "compose"
        ):
            result = runner.campaign(True)
            self.assertEqual(
                (result["new_consumed"], result["cumulative_consumed"]), (4, 7)
            )
            with self.assertRaisesRegex(runner.Failure, "already_reserved"):
                runner.campaign(True)
            self.assertEqual(phase.call_count, 2)
        self.assertEqual(
            json.loads((self.directory / "outcome.json").read_text())["new_consumed"], 1
        )
