from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.publication import (  # noqa: E402
    build_publication_markdown,
    build_publication_package,
    build_publication_reproducibility_alignment,
)
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
        self.assertIn("gretel_autonomous_research_loop", package)
        self.assertIn("manual review", package["github_issue_policy"])
        self.assertIn("Gretel-built", package["gretel_bachelor_thesis_policy"])
        self.assertIn("budgeted local autonomous research loop", package["gretel_autonomy_policy"])
        self.assertEqual(package["publication_reproducibility_alignment"]["status"], "ready")
        self.assertEqual(package["publication_reproducibility_alignment"]["public_safety_status"], "pass")
        self.assertEqual(package["publication_reproducibility_alignment"]["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(package["publication_reproducibility_alignment"]["missing_release_review_board_claim_human_gates"], [])
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
        self.assertTrue(package["release_gates"]["gretel_autonomous_research_loop_ready"])
        self.assertTrue(package["release_gates"]["release_ready"])

    def test_publication_reproducibility_alignment_maps_release_evidence(self) -> None:
        package = build_publication_package()
        alignment = build_publication_reproducibility_alignment(package)
        by_section = {section["section_id"]: section for section in alignment["sections"]}

        self.assertEqual(alignment["schema_version"], "unibot-publication-reproducibility-alignment-v1")
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_artifact_ids"], [])
        self.assertEqual(alignment["missing_release_gate_ids"], [])
        self.assertEqual(alignment["missing_policy_keys"], [])
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertEqual(alignment["failed_release_review_board_claim_trace_ids"], [])
        self.assertIn("publication_package", alignment["required_readiness_check_ids"])
        self.assertIn("release_runbook", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("pilot_protocol", alignment["required_readiness_check_ids"])
        self.assertIn("data_protection_screening", alignment["required_readiness_check_ids"])
        self.assertIn("gretel_bachelor_thesis_package", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("adaptive_task_plan", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("public_safety_required", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertIn("provider_call_requires_explicit_go_and_redaction_receipt", alignment["required_human_gates"])
        release_claim_contract = alignment["publication_release_review_board_claim_contract"]
        self.assertEqual(
            release_claim_contract["expected_schema_version"],
            "unibot-publication-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            release_claim_contract["required_pilot_release_review_board_schema_version"],
            "unibot-pilot-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            release_claim_contract["required_data_protection_release_review_board_schema_version"],
            "unibot-data-protection-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            release_claim_contract["required_review_board_thesis_evaluation_schema_version"],
            "unibot-review-board-thesis-evaluation-claim-alignment-v1",
        )
        self.assertEqual(
            release_claim_contract["required_trace_ids"],
            [
                "data_protection_release_review_board_claim",
                "pilot_release_review_board_claim",
                "publication_public_safety_claim",
                "release_runbook_review_board_claim",
                "review_board_thesis_evaluation_claim",
            ],
        )
        trace_by_id = {row["trace_id"]: row for row in alignment["release_review_board_claim_trace"]}
        self.assertEqual(
            trace_by_id["pilot_release_review_board_claim"]["alignment_schema_version"],
            "unibot-pilot-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            trace_by_id["data_protection_release_review_board_claim"]["alignment_schema_version"],
            "unibot-data-protection-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            trace_by_id["review_board_thesis_evaluation_claim"]["alignment_status"],
            "ready",
        )
        self.assertIn(
            "human_submission_review_required",
            trace_by_id["release_runbook_review_board_claim"]["human_gates"],
        )
        self.assertEqual(
            trace_by_id["publication_public_safety_claim"]["claim_boundary"],
            "public_safe_draft_only_not_exam_deployment_or_university_submission",
        )
        self.assertEqual(alignment["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(alignment["missing_release_review_board_claim_human_gates"], [])
        self.assertEqual(alignment["release_boundary"], "public_draft_only_not_exam_deployment_not_university_submission")
        self.assertTrue(alignment["contracts"]["release_ready_public_draft_only"])
        self.assertTrue(alignment["contracts"]["private_groups_excluded"])
        self.assertTrue(alignment["contracts"]["gretel_thesis_claim_source_bound"])
        self.assertTrue(alignment["contracts"]["pilot_claim_contract_ready"])
        self.assertTrue(alignment["contracts"]["data_protection_claim_contract_ready"])
        self.assertTrue(alignment["contracts"]["review_board_thesis_evaluation_claim_ready"])
        self.assertTrue(alignment["contracts"]["glm_provider_locked"])
        self.assertIn("pilot_protocol", by_section["release_review_board_claim_bundle"]["artifact_ids"])
        self.assertIn("data_protection_screening_ready", by_section["release_review_board_claim_bundle"]["release_gate_ids"])
        self.assertIn("gretel_bachelor_thesis_package", by_section["gretel_glm_thesis_bundle"]["artifact_ids"])
        self.assertIn("release_runbook_ready", by_section["manual_release_boundary"]["release_gate_ids"])

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
        self.assertIn("Reproducibility Alignment", markdown)
        self.assertIn(
            "Release review-board claim alignment: unibot-publication-release-review-board-claim-alignment-v1",
            markdown,
        )
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
        self.assertIn("Gretel autonomous research loop", markdown)

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
