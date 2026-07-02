from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.publication import build_publication_markdown, build_publication_package  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotPublicationTests(unittest.TestCase):
    def test_publication_package_contains_system_data_and_limitations(self) -> None:
        package = build_publication_package()

        self.assertEqual(package["schema_version"], "unibot-publication-package-v1")
        self.assertEqual(package["status"], "public_draft_not_exam_release")
        self.assertEqual(package["system_card"]["name"], "UniBot Guardian")
        self.assertIn("practice_overlay", package["system_card"]["supported_modes"])
        self.assertIn("exam_controlled", package["system_card"]["blocked_or_not_cleared_modes"])
        self.assertIn("data_card", package)
        self.assertIn("course_material_public_summary", package)
        self.assertIn("adaptive_task_plan_demo", package)
        self.assertIn("local_demo_run", package)
        self.assertIn("demo_feedback_template", package)
        self.assertIn("demo_feedback_public_summary", package)
        self.assertIn("demo_feedback_triage", package)
        self.assertIn("github_issue_bundle", package)
        self.assertIn("release_runbook", package)
        self.assertIn("compliance_matrix", package)
        self.assertIn("pilot_protocol", package)
        self.assertIn("data_protection_screening", package)
        self.assertIn("review_board_packet", package)
        self.assertIn("gretel_glm_evolve_lane", package)
        self.assertIn("gretel_bachelor_thesis_package", package)
        self.assertIn("manual review", package["github_issue_policy"])
        self.assertIn("Gretel-built", package["gretel_bachelor_thesis_policy"])
        self.assertIn("public draft", package["release_runbook_policy"])
        self.assertIn("not legal advice", package["compliance_matrix_policy"])
        self.assertIn("planning draft", package["pilot_protocol_policy"])
        self.assertIn("planning draft", package["data_protection_policy"])
        self.assertIn("not written institutional approval", package["review_board_policy"])
        self.assertGreaterEqual(len(package["limitations"]), 4)
        self.assertTrue(package["release_gates"]["course_material_policy_ready"])
        self.assertTrue(package["release_gates"]["adaptive_task_plan_ready"])
        self.assertTrue(package["release_gates"]["local_demo_run_ready"])
        self.assertTrue(package["release_gates"]["demo_feedback_contract_ready"])
        self.assertTrue(package["release_gates"]["release_runbook_ready"])
        self.assertTrue(package["release_gates"]["compliance_matrix_ready"])
        self.assertTrue(package["release_gates"]["pilot_protocol_ready"])
        self.assertTrue(package["release_gates"]["data_protection_screening_ready"])
        self.assertTrue(package["release_gates"]["review_board_packet_ready"])
        self.assertTrue(package["release_gates"]["gretel_glm_evolve_lane_ready"])
        self.assertTrue(package["release_gates"]["gretel_bachelor_thesis_package_ready"])
        self.assertTrue(package["release_gates"]["release_ready"])

    def test_publication_package_excludes_private_and_exam_materials(self) -> None:
        package_text = json.dumps(build_publication_package(), ensure_ascii=False)

        self.assertNotIn("raw_external_ai_output", package_text)
        self.assertNotIn("solution_key", package_text)
        self.assertNotIn("official_grade", package_text)
        self.assertIn("private course-material directory", package_text)
        self.assertIn("excluded_file_groups", package_text)
        self.assertIn("not as exam deployment", package_text)

    def test_publication_markdown_and_api_routes(self) -> None:
        markdown = build_publication_markdown()
        self.assertIn("# UniBot Public Reproduction Package", markdown)
        self.assertIn("System Card", markdown)
        self.assertIn("Data Card", markdown)
        self.assertIn("Release Gates", markdown)
        self.assertIn("Course-material policy", markdown)
        self.assertIn("Adaptive task plan", markdown)
        self.assertIn("Local demo run", markdown)
        self.assertIn("Demo feedback contract", markdown)
        self.assertIn("Release runbook", markdown)
        self.assertIn("Compliance matrix", markdown)
        self.assertIn("Pilot protocol", markdown)
        self.assertIn("Data protection screening", markdown)
        self.assertIn("Review board packet", markdown)
        self.assertIn("Gretel GLM evolve lane", markdown)
        self.assertIn("Gretel Bachelor thesis package", markdown)

        status, package = route_request("/api/unibot/publication-package", {})
        self.assertEqual(status, 200)
        self.assertEqual(package["schema_version"], "unibot-publication-package-v1")

        status, response = route_request("/api/unibot/publication-package-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Excluded File Groups", response["markdown"])

    def test_publication_package_is_public_safe(self) -> None:
        package_text = json.dumps(build_publication_package(), ensure_ascii=False)
        lowered = package_text.lower()

        self.assertEqual(scan_text(package_text, "publication-package")["status"], "pass")
        self.assertIn("no proctoring", lowered)
        self.assertIn("no automatic grading", lowered)
        self.assertIn("no exam-security guarantee", lowered)
        self.assertIn("medical or accommodation personal data", lowered)
        self.assertNotIn("student@example", lowered)
        self.assertNotIn("sk-test", lowered)


if __name__ == "__main__":
    unittest.main()
