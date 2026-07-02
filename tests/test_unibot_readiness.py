from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.readiness import build_readiness_markdown, default_public_paths, run_readiness_check  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotReadinessTests(unittest.TestCase):
    def test_default_public_paths_include_core_docs_code_and_tests(self) -> None:
        paths = default_public_paths()
        names = {path.name for path in paths}

        self.assertIn("UNIBOT_PIPELINE.md", names)
        self.assertIn("CONTRIBUTING.md", names)
        self.assertIn("SECURITY.md", names)
        self.assertIn("guardian.py", names)
        self.assertIn("publication.py", names)
        self.assertIn("test_unibot_readiness.py", names)

    def test_readiness_check_passes_for_public_draft(self) -> None:
        report = run_readiness_check()
        check_ids = {check["check_id"] for check in report["checks"]}

        self.assertEqual(report["schema_version"], "unibot-readiness-check-v1")
        self.assertEqual(report["status"], "public_draft_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(report["passed_count"], report["check_count"])
        self.assertIn("public_safety", check_ids)
        self.assertIn("redteam", check_ids)
        self.assertIn("publication_package", check_ids)
        self.assertIn("evaluation_packet", check_ids)
        self.assertIn("authority_handoff", check_ids)
        self.assertIn("course_material_policy", check_ids)
        self.assertIn("adaptive_task_plan", check_ids)
        self.assertIn("local_demo_run", check_ids)
        self.assertIn("demo_feedback_contract", check_ids)
        self.assertIn("demo_feedback_triage", check_ids)
        self.assertIn("github_issue_bundle", check_ids)
        self.assertIn("release_runbook", check_ids)
        self.assertIn("compliance_matrix", check_ids)
        self.assertIn("pilot_protocol", check_ids)
        self.assertIn("data_protection_screening", check_ids)
        self.assertIn("review_board_packet", check_ids)
        self.assertIn("gretel_glm_evolve_lane", check_ids)
        self.assertIn("gretel_bachelor_thesis_package", check_ids)
        self.assertIn("gretel_autonomous_research_loop", check_ids)
        self.assertIn("exam_boundary", check_ids)
        self.assertIn("public draft review", report["ready_for"])
        self.assertIn("exam deployment", report["not_ready_for"])

    def test_readiness_check_blocks_when_public_scan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            risky = Path(tmp) / "risky.md"
            risky.write_text("api" + "_key = sk-test\n", encoding="utf-8")
            report = run_readiness_check([risky])

        self.assertEqual(report["status"], "blocked")
        self.assertGreater(report["failed_count"], 0)
        public_check = next(check for check in report["checks"] if check["check_id"] == "public_safety")
        self.assertFalse(public_check["passed"])

    def test_readiness_markdown_and_api_routes(self) -> None:
        markdown = build_readiness_markdown()
        self.assertIn("# UniBot Readiness Check", markdown)
        self.assertIn("public_draft_ready", markdown)
        self.assertIn("Exam deployment: not_cleared", markdown)

        status, report = route_request("/api/unibot/readiness-check", {})
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "public_draft_ready")

        status, response = route_request("/api/unibot/readiness-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Policy:", response["markdown"])

    def test_readiness_report_is_public_safe(self) -> None:
        payload = json.dumps(run_readiness_check(), ensure_ascii=False)

        self.assertNotIn("raw_external_ai_output", payload)
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("official_grade", payload)
        self.assertIn("not exam clearance", payload)


if __name__ == "__main__":
    unittest.main()
