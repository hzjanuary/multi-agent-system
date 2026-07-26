import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.evaluation.evaluate_demo_safety import (
    DEFAULT_CASES_PATH,
    FORBIDDEN_OUTPUT_CLAIMS,
    REQUIRED_CATEGORIES,
    build_metrics,
    evaluate_dataset,
    format_human_summary,
    load_dataset,
    main,
)


class DemoSafetyEvaluationTests(unittest.TestCase):
    def load_default_dataset(self) -> dict[str, object]:
        return load_dataset(DEFAULT_CASES_PATH)

    def test_dataset_schema_is_valid_and_ids_are_unique(self) -> None:
        dataset = self.load_default_dataset()
        cases = dataset["cases"]
        self.assertIsInstance(cases, list)
        case_ids = [case["id"] for case in cases]

        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_dataset_covers_all_required_categories(self) -> None:
        dataset = self.load_default_dataset()
        categories = {case["category"] for case in dataset["cases"]}

        self.assertEqual(categories, REQUIRED_CATEGORIES)

    def test_dataset_covers_required_safety_outcomes(self) -> None:
        dataset = self.load_default_dataset()
        outcomes = {case["expected_safety_outcome"] for case in dataset["cases"]}

        self.assertIn("transition_allowed", outcomes)
        self.assertIn("transition_blocked", outcomes)
        self.assertIn("preview_available", outcomes)
        self.assertIn("preview_disabled", outcomes)
        self.assertIn("preview_blocked_by_policy", outcomes)
        self.assertIn("preview_unavailable", outcomes)
        self.assertIn("send_blocked", outcomes)
        self.assertIn("unsafe_flag_rejected", outcomes)
        self.assertIn("sensitive_content_rejected", outcomes)
        self.assertIn("catalog_commitments_absent", outcomes)
        self.assertIn("defaults_safe", outcomes)

    def test_runner_succeeds_on_current_dataset(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        self.assertIn("39/39 cases passed", buffer.getvalue())

    def test_runner_fails_on_wrong_expectation(self) -> None:
        dataset = copy.deepcopy(self.load_default_dataset())
        dataset["cases"][0]["expected_safety_outcome"] = "transition_blocked"

        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir) / "wrong_cases.json"
            dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = main(["--cases", str(dataset_path)])

        self.assertEqual(exit_code, 1)
        self.assertIn("Failures:", buffer.getvalue())

    def test_metrics_json_shape_is_stable(self) -> None:
        dataset = self.load_default_dataset()
        metrics = build_metrics(dataset, evaluate_dataset(dataset))

        self.assertEqual(
            metrics["benchmark_name"],
            "demo_safety_workflow_evidence_matrix",
        )
        self.assertEqual(metrics["version"], "spec-022-sprint-2")
        self.assertEqual(metrics["generated_at"], "1970-01-01T00:00:00Z")
        self.assertTrue(metrics["deterministic"])
        self.assertFalse(metrics["provider_calls"])
        self.assertFalse(metrics["live_network_calls"])
        self.assertFalse(metrics["backend_api_calls"])
        self.assertFalse(metrics["database_required"])
        self.assertFalse(metrics["email_sent"])
        self.assertEqual(metrics["total_cases"], 39)
        self.assertEqual(metrics["passed_cases"], 39)
        self.assertEqual(metrics["failed_cases"], 0)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertIn("category_breakdown", metrics)
        self.assertEqual(metrics["failures"], [])

    def test_output_json_file_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "metrics.json"
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = main(["--output-json", str(output_path)])
            metrics = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(metrics["total_cases"], 39)
        self.assertEqual(metrics["failed_cases"], 0)

    def test_no_forbidden_claims_appear_in_outputs(self) -> None:
        dataset = self.load_default_dataset()
        metrics = build_metrics(dataset, evaluate_dataset(dataset))
        human_output = format_human_summary(metrics)
        machine_output = json.dumps(metrics, sort_keys=True)
        combined = f"{human_output}\n{machine_output}".lower()

        for claim in FORBIDDEN_OUTPUT_CLAIMS:
            with self.subTest(claim=claim):
                self.assertNotIn(claim, combined)

    def test_no_network_provider_backend_api_or_database_calls_are_required(self) -> None:
        with patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = main([])

        self.assertEqual(exit_code, 0)

    def test_outbound_send_remains_impossible(self) -> None:
        dataset = self.load_default_dataset()
        results = evaluate_dataset(dataset)
        send_case = next(
            result
            for result in results
            if result.case_id == "outbound-send-impossible"
        )

        self.assertTrue(send_case.passed)
        self.assertEqual(send_case.actual_safety_outcome, "send_blocked")

    def test_defaults_remain_no_key_and_disabled(self) -> None:
        dataset = self.load_default_dataset()
        results = evaluate_dataset(dataset)
        default_case = next(
            result
            for result in results
            if result.case_id == "settings-stable-no-key-defaults"
        )

        self.assertTrue(default_case.passed)
        self.assertEqual(default_case.actual_safety_outcome, "defaults_safe")


if __name__ == "__main__":
    unittest.main()
