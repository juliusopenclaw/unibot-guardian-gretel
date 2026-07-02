from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.bachelor_thesis import build_bachelor_thesis_markdown, build_bachelor_thesis_package  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotBachelorThesisTests(unittest.TestCase):
    def test_package_labels_gretel_as_builder_and_uses_glm_52(self) -> None:
        package = build_bachelor_thesis_package()

        self.assertEqual(package["schema_version"], "unibot-gretel-bachelor-thesis-package-v1")
        self.assertEqual(package["status"], "public_scientific_draft_bachelor_thesis_level_not_real_submission")
        self.assertEqual(package["authorship_statement"]["builder"], "Gretel")
        self.assertEqual(package["authorship_statement"]["documentation_author"], "Gretel")
        self.assertIn("not by Julius", package["authorship_statement"]["programmer_claim"])
        self.assertEqual(package["glm_technology_basis"]["primary_model_hint"], "zai/glm-5.2")
        self.assertEqual(package["glm_technology_basis"]["provider_call_default"], "disabled")
        self.assertIn("bachelor_thesis_level_research_package", package["submission_type"])
        self.assertIn("does not mean this artifact is a real university thesis submission", package["level_statement"])
        self.assertTrue(package["review_gates"]["human_submission_review_required"])
        self.assertTrue(package["review_gates"]["no_autonomous_github_publish"])
        self.assertTrue(package["review_gates"]["no_final_go_by_gretel_or_glm"])

    def test_package_is_public_safe_and_keeps_exam_boundary(self) -> None:
        payload = json.dumps(build_bachelor_thesis_package(), ensure_ascii=False)

        self.assertEqual(scan_text(payload, "bachelor-thesis-package")["status"], "pass")
        self.assertIn("real university thesis submission without human review", payload)
        self.assertIn("exam deployment", payload)
        self.assertNotIn("/" + "Users/", payload)
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("api" + "_key", payload.lower())
        self.assertNotIn("raw_external_ai_output", payload)

    def test_markdown_and_api_routes(self) -> None:
        markdown = build_bachelor_thesis_markdown()

        self.assertIn("# UniBot Gretel Bachelor-Thesis-Level Package", markdown)
        self.assertIn("Builder: Gretel", markdown)
        self.assertIn("Model hint: zai/glm-5.2", markdown)
        self.assertIn("Public safety: pass", markdown)

        status, package = route_request("/api/unibot/bachelor-thesis-package", {})
        self.assertEqual(status, 200)
        self.assertEqual(package["authorship_statement"]["builder"], "Gretel")

        status, response = route_request("/api/unibot/bachelor-thesis-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Programmer claim", response["markdown"])


if __name__ == "__main__":
    unittest.main()
