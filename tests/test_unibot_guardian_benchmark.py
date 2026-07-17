from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from unibot.autonomy_v3 import PublicContextBuilder
from unibot.guardian_benchmark import (
    MAX_ALLOWED_FALSE_BLOCK_RATE,
    evaluate_guardian_benchmark,
    guardian_semantic_precision_work_item,
    held_out_cases,
    separate_evaluation_corpus_summary,
)


class GuardianSemanticPrecisionBenchmarkTests(unittest.TestCase):
    def test_fixed_held_out_suite_meets_the_release_thresholds(self) -> None:
        cases = held_out_cases()
        report = evaluate_guardian_benchmark(cases)

        self.assertEqual(len(cases), 60)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["held_out_provider_policy"], "forbidden")
        self.assertEqual(report["metrics"]["solution_block_recall"], 1.0)
        self.assertEqual(report["metrics"]["source_binding_precision"], 1.0)
        self.assertLessEqual(report["metrics"]["allowed_false_block_rate"], MAX_ALLOWED_FALSE_BLOCK_RATE)
        self.assertFalse(report["notebook_code_executed"])
        self.assertFalse(report["automatic_fix_created"])
        self.assertEqual(report["benchmark_scope"]["held_out_guardian_case_count"], 60)
        self.assertEqual(report["benchmark_scope"]["separate_evaluation_corpus"]["task_count"], 180)
        self.assertFalse(report["benchmark_scope"]["separate_evaluation_corpus"]["guardian_cli_executed"])

    def test_source_binding_gate_uses_detected_risk_and_available_source_card(self) -> None:
        cases = list(held_out_cases())
        source_risk_index = next(index for index, case in enumerate(cases) if case.family == "source_binding_error")
        cases[source_risk_index] = replace(cases[source_risk_index], source_card_id="synthetic-missing-source-card")

        report = evaluate_guardian_benchmark(cases)

        self.assertEqual(report["status"], "blocked")
        self.assertLess(report["metrics"]["source_binding_precision"], 1.0)
        self.assertGreaterEqual(report["failure_count"], 1)

    def test_separate_evaluation_corpus_is_explicitly_not_guardian_cli_evidence(self) -> None:
        summary = separate_evaluation_corpus_summary()

        self.assertEqual(summary["task_count"], 180)
        self.assertEqual(summary["status"], "separate_public_synthetic_evaluation")
        self.assertFalse(summary["guardian_cli_executed"])

    def test_report_contains_only_aggregate_and_synthetic_failure_data(self) -> None:
        report = evaluate_guardian_benchmark()
        serialized = json.dumps(report, ensure_ascii=False)

        self.assertFalse(report["raw_case_text_in_report"])
        self.assertNotIn(cases_text_fragment(), serialized)
        self.assertTrue(all(set(item) == {"case_id", "family", "failure_class"} for item in report["failure_classes"]))

    def test_work_item_has_four_write_paths_and_excludes_held_out_provider_context(self) -> None:
        item = guardian_semantic_precision_work_item("a" * 40)

        self.assertEqual(item.validate(), [])
        self.assertEqual(item.validate_for_execution(), [])
        self.assertEqual(len(item.allowed_files), 4)
        self.assertEqual(item.evolution_chunk.failure_class, "guardian.semantic_precision")
        self.assertGreaterEqual(len(item.evolution_chunk.transfer_targets), 2)
        self.assertNotIn("tests/test_unibot_guardian_benchmark.py", item.public_context_files)
        self.assertNotIn("unibot/guardian_benchmark.py", item.public_context_files)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in item.public_context_files:
                candidate = root / relative
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.write_text("public synthetic implementation context\n", encoding="utf-8")
            held_out = root / "tests" / "test_unibot_guardian_benchmark.py"
            held_out.parent.mkdir(parents=True, exist_ok=True)
            held_out.write_text(cases_text_fragment(), encoding="utf-8")

            context = PublicContextBuilder(root).build(item)

        serialized = json.dumps(context, ensure_ascii=False)
        self.assertNotIn("tests/test_unibot_guardian_benchmark.py", [entry["path"] for entry in context["files"]])
        self.assertNotIn(cases_text_fragment(), serialized)


def cases_text_fragment() -> str:
    return "provider-withheld-synthetic-guardian-case"


if __name__ == "__main__":
    unittest.main()
