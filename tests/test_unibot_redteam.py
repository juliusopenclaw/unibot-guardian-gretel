from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.redteam import run_redteam_smoke  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotRedTeamTests(unittest.TestCase):
    def test_redteam_smoke_passes_required_scenarios(self) -> None:
        report = run_redteam_smoke()
        scenario_ids = {scenario["scenario_id"] for scenario in report["scenarios"]}

        self.assertEqual(report["schema_version"], "unibot-redteam-smoke-v1")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["failed_count"], 0)
        self.assertGreaterEqual(report["scenario_count"], 9)
        self.assertIn("rt_solution_output", scenario_ids)
        self.assertIn("rt_privacy_output", scenario_ids)
        self.assertIn("rt_source_risk", scenario_ids)
        self.assertIn("rt_exam_mode_gate", scenario_ids)
        self.assertIn("rt_a6_repeat_task", scenario_ids)
        self.assertIn("rt_notebook_audit", scenario_ids)
        self.assertIn("rt_public_safety", scenario_ids)
        self.assertIn("rt_ledger_redaction", scenario_ids)
        self.assertIn("rt_socratic_hint_allowed", scenario_ids)

    def test_redteam_report_does_not_store_raw_fixture_text(self) -> None:
        report_text = json.dumps(run_redteam_smoke(), ensure_ascii=False)

        self.assertNotIn("werte = [1, 2, 3]", report_text)
        self.assertNotIn("sk-test", report_text)
        self.assertNotIn("private/notebook.ipynb", report_text)
        self.assertIn("raw_output_hash", report_text)

    def test_redteam_api_route(self) -> None:
        status, report = route_request("/api/unibot/redteam/run", {})

        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["scenario_count"], report["passed_count"])


if __name__ == "__main__":
    unittest.main()
