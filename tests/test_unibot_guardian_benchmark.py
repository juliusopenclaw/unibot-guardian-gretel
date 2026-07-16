from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from unibot.autonomy_v3 import PublicContextBuilder
from unibot.guardian_benchmark import (
    MAX_ALLOWED_FALSE_BLOCK_RATE,
    evaluate_guardian_benchmark,
    guardian_semantic_precision_work_item,
    held_out_cases,
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

    def test_report_contains_only_aggregate_and_synthetic_failure_data(self) -> None:
        report = evaluate_guardian_benchmark()
        serialized = json.dumps(report, ensure_ascii=False)

        self.assertFalse(report["raw_case_text_in_report"])
        self.assertNotIn(cases_text_fragment(), serialized)
        self.assertTrue(all(set(item) == {"case_id", "family", "failure_class"} for item in report["failure_classes"]))

    def test_work_item_has_four_write_paths_and_excludes_held_out_provider_context(self) -> None:
        item = guardian_semantic_precision_work_item("a" * 40)

        self.assertEqual(item.validate(), [])
        self.assertEqual(len(item.allowed_files), 4)
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
