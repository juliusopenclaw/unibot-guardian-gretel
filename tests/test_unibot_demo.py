from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.demo import build_local_demo_markdown, build_local_demo_run  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotDemoTests(unittest.TestCase):
    def test_demo_run_contains_practice_walkthrough(self) -> None:
        demo = build_local_demo_run()
        scenario_ids = {scenario["scenario_id"] for scenario in demo["scenarios"]}

        self.assertEqual(demo["schema_version"], "unibot-demo-run-v1")
        self.assertEqual(demo["status"], "practice_demo_ready_not_exam")
        self.assertEqual(demo["public_safety_status"], "pass")
        self.assertGreaterEqual(demo["scenario_count"], 7)
        self.assertIn("demo_setup", scenario_ids)
        self.assertIn("demo_prompt_card", scenario_ids)
        self.assertIn("demo_block_solution", scenario_ids)
        self.assertIn("demo_allowed_flow_and_ledger", scenario_ids)
        self.assertIn("demo_adaptive_tasks", scenario_ids)
        self.assertIn("demo_notebook_template", scenario_ids)
        self.assertIn("demo_redteam_smoke", scenario_ids)
        self.assertIn("exam deployment", demo["not_ready_for"])

    def test_demo_run_is_public_safe_and_has_bug_report_template(self) -> None:
        demo = build_local_demo_run()
        payload = json.dumps(demo, ensure_ascii=False)

        self.assertEqual(scan_text(payload, "demo")["status"], "pass")
        self.assertNotIn("raw_external_ai_output", payload)
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("official_grade", payload)
        self.assertTrue(demo["bug_report_template"]["private_data_removed"])

    def test_demo_markdown_and_api_routes(self) -> None:
        markdown = build_local_demo_markdown()

        self.assertIn("# UniBot Local Demo Test Plan", markdown)
        self.assertIn("practice demo only", markdown)
        self.assertIn("Bug Report Template", markdown)
        self.assertIn("/api/unibot/demo-feedback/validate", markdown)

        status, demo = route_request("/api/unibot/demo-run", {})
        self.assertEqual(status, 200)
        self.assertEqual(demo["schema_version"], "unibot-demo-run-v1")

        status, response = route_request("/api/unibot/demo-run-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Notebook handoff", response["markdown"])


if __name__ == "__main__":
    unittest.main()
