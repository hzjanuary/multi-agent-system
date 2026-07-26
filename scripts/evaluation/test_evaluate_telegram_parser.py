import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.demo.catalog import supported_item_families
from scripts.evaluation.evaluate_telegram_parser import (
    DEFAULT_CASES_PATH,
    FORBIDDEN_OUTPUT_CLAIMS,
    build_metrics,
    evaluate_dataset,
    format_human_summary,
    load_dataset,
    main,
)


class TelegramParserEvaluationTests(unittest.TestCase):
    def load_default_dataset(self) -> dict[str, object]:
        return load_dataset(DEFAULT_CASES_PATH)

    def test_dataset_schema_is_valid_and_ids_are_unique(self) -> None:
        dataset = self.load_default_dataset()
        cases = dataset["cases"]
        self.assertIsInstance(cases, list)
        case_ids = [case["id"] for case in cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_dataset_contains_english_and_vietnamese_cases(self) -> None:
        dataset = self.load_default_dataset()
        languages = {case["language"] for case in dataset["cases"]}

        self.assertEqual(languages, {"en", "vi"})

    def test_dataset_covers_all_supported_item_families(self) -> None:
        dataset = self.load_default_dataset()
        expected_names = {
            case["expected_normalized_item_name"]
            for case in dataset["cases"]
            if case["expected_should_create_workflow"]
        }

        self.assertTrue(set(supported_item_families()).issubset(expected_names))

    def test_dataset_covers_unsupported_and_mixed_cases(self) -> None:
        dataset = self.load_default_dataset()
        categories = {case["category"] for case in dataset["cases"]}

        self.assertIn("unsupported_item", categories)
        self.assertIn("mixed_supported_unsupported", categories)
        self.assertIn("missing_quantity", categories)
        self.assertIn("missing_item", categories)
        self.assertIn("greeting_or_help", categories)
        self.assertIn("safety_forbidden_claims", categories)

    def test_runner_succeeds_on_current_dataset(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("25/25 cases passed", output)

    def test_runner_fails_on_wrong_expectation(self) -> None:
        dataset = copy.deepcopy(self.load_default_dataset())
        dataset["cases"][0]["expected_quantity"] = 999

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

        self.assertEqual(metrics["benchmark_name"], "telegram_parser_rfq_matrix")
        self.assertEqual(metrics["version"], "spec-022-sprint-1")
        self.assertEqual(metrics["generated_at"], "1970-01-01T00:00:00Z")
        self.assertTrue(metrics["deterministic"])
        self.assertFalse(metrics["provider_calls"])
        self.assertFalse(metrics["live_network_calls"])
        self.assertEqual(metrics["total_cases"], 25)
        self.assertEqual(metrics["passed_cases"], 25)
        self.assertEqual(metrics["failed_cases"], 0)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertIn("category_breakdown", metrics)
        self.assertIn("language_breakdown", metrics)
        self.assertEqual(metrics["failures"], [])

    def test_output_json_file_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "metrics.json"
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = main(["--output-json", str(output_path)])
            metrics = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(metrics["total_cases"], 25)
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

    def test_no_network_provider_or_backend_calls_are_required(self) -> None:
        with patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = main([])

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
