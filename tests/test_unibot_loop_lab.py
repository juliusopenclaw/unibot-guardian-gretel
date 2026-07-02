from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.loop_lab import (  # noqa: E402
    compare_with_previous,
    core25_dataset,
    loop_lab_to_markdown,
    run_loop_lab,
)
from unibot.public_safety import scan_text  # noqa: E402


SCRIPT = ROOT / "scripts" / "unibot_loop_lab_smoke.py"


class UniBotLoopLabTests(unittest.TestCase):
    def test_core25_dataset_contract_is_public_safe(self) -> None:
        cases = core25_dataset()
        ids = [case.scenario_id for case in cases]

        self.assertEqual(len(cases), 25)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(case.mode == "exam_controlled" for case in cases))
        self.assertTrue(any("prompt_injection_or_policy_evasion" in case.expected_categories for case in cases))
        self.assertTrue(any("private_or_sensitive_data" in case.expected_categories for case in cases))
        self.assertEqual(scan_text(json.dumps([case.to_public_dict() for case in cases], ensure_ascii=False), "core25")["status"], "pass")

    def test_loop_lab_report_scores_all_scenarios_and_keeps_raw_output_out(self) -> None:
        report = run_loop_lab(compare_previous=False)
        payload = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["artifact_type"], "unibot_loop_lab_report_v2")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["scenario_count"], 25)
        self.assertEqual(report["grader_summary"]["passed_scenarios"], 25)
        self.assertEqual(report["grader_summary"]["failed_scenarios"], 0)
        self.assertEqual(report["golden_rules_summary"]["status"], "pass")
        self.assertEqual(report["public_safety"]["status"], "pass")
        self.assertTrue(report["policy"]["three_golden_rules_are_hard_gates"])
        self.assertNotIn("Hier ist die komplette Loesung", payload)
        self.assertNotIn("```python", payload)
        self.assertNotIn("/" + "Users", payload)
        self.assertNotIn("learner" + "@" + "example.invalid", payload)

    def test_backlog_contains_p0_control_items_for_risky_cases(self) -> None:
        report = run_loop_lab(compare_previous=False)
        p0_ids = {item["scenario_id"] for item in report["backlog_items"] if item["priority"] == "P0"}

        self.assertIn("solution_leak_a6", p0_ids)
        self.assertIn("prompt_injection_a5", p0_ids)
        self.assertIn("privacy_slip_a3", p0_ids)
        self.assertIn("exam_controlled_no_approval_a2", p0_ids)
        self.assertTrue(all(item["public_safe"] for item in report["backlog_items"]))

    def test_regression_detects_improved_and_regressed_cases(self) -> None:
        current = run_loop_lab(compare_previous=False)
        previous = deepcopy(current)
        previous["grades"][0]["status"] = "fail"
        current["grades"][1]["status"] = "fail"

        comparison = compare_with_previous(current, previous)
        by_id = {item["scenario_id"]: item for item in comparison["items"]}

        self.assertEqual(by_id[current["grades"][0]["scenario_id"]]["change"], "improved")
        self.assertEqual(by_id[current["grades"][1]["scenario_id"]]["change"], "regressed")
        self.assertIn(current["grades"][1]["scenario_id"], comparison["golden_rule_regressions"])
        self.assertEqual(comparison["status"], "regressed")

    def test_persisted_run_stores_public_safe_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_loop_lab(persist=True, compare_previous=True, history_dir=tmp)
            stored = sorted(Path(tmp).glob("loop_lab_*.json"))
            markdown = sorted(Path(tmp).glob("loop_lab_*.md"))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["persistence"]["status"], "stored")
        self.assertEqual(len(stored), 1)
        self.assertEqual(len(markdown), 1)
        self.assertNotIn("/" + "Users", report["persistence"]["json_path"])

    def test_loop_lab_api_route_returns_report(self) -> None:
        from unibot.server import route_request

        status, report = route_request("/api/unibot/loop-lab/run", payload={"compare_previous": False})

        self.assertEqual(status, 200)
        self.assertEqual(report["artifact_type"], "unibot_loop_lab_report_v2")
        self.assertEqual(report["status"], "pass")

    def test_markdown_and_smoke_script_are_public_safe(self) -> None:
        report = run_loop_lab(compare_previous=False)
        markdown = loop_lab_to_markdown(report)
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--json", "--no-compare"],
            check=True,
            capture_output=True,
            text=True,
        )
        smoke = json.loads(completed.stdout)

        self.assertEqual(scan_text(markdown, "loop-lab-markdown")["status"], "pass")
        self.assertEqual(smoke["status"], "pass")
        self.assertEqual(smoke["scenario_count"], 25)


if __name__ == "__main__":
    unittest.main()
