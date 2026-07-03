from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.bachelor_thesis import (  # noqa: E402
    build_bachelor_thesis_evidence_index,
    build_bachelor_thesis_evaluation_claim_alignment,
    build_bachelor_thesis_markdown,
    build_bachelor_thesis_package,
)
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
        self.assertEqual(package["evidence_index"]["status"], "ready")
        self.assertEqual(package["evidence_index"]["public_safety_status"], "pass")
        self.assertEqual(package["evaluation_claim_alignment"]["status"], "ready")
        self.assertEqual(package["evaluation_claim_alignment"]["public_safety_status"], "pass")

    def test_evidence_index_maps_claims_to_sources_tests_and_human_gates(self) -> None:
        index = build_bachelor_thesis_evidence_index()
        by_id = {item["claim_id"]: item for item in index["evidence_items"]}

        self.assertEqual(index["schema_version"], "unibot-gretel-bachelor-thesis-evidence-index-v1")
        self.assertEqual(index["status"], "ready")
        self.assertEqual(index["public_safety_status"], "pass")
        self.assertEqual(index["source_card_drift_status"], "pass")
        self.assertGreaterEqual(index["claim_count"], 6)
        self.assertGreaterEqual(index["source_card_count"], index["required_source_card_count"])
        self.assertIn("gretel_bachelor_thesis_package", index["required_readiness_check_ids"])
        self.assertIn("source_card_drift_guard", index["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", index["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", index["required_human_gates"])
        self.assertIn("glm_52_basis", by_id)
        self.assertIn("zai-glm-52", by_id["glm_52_basis"]["source_card_ids"])
        self.assertIn("evaluation_learner_agency_boundary", by_id)
        self.assertIn("evaluation_packet", by_id["evaluation_learner_agency_boundary"]["readiness_check_ids"])
        self.assertIn("adaptive_task_plan", by_id["evaluation_learner_agency_boundary"]["readiness_check_ids"])
        self.assertTrue(all(item["acceptance_tests"] for item in index["evidence_items"]))
        self.assertTrue(all(item["readiness_check_ids"] for item in index["evidence_items"]))

    def test_evaluation_claim_alignment_traces_thesis_claims_to_evaluation_and_adaptive_boundaries(self) -> None:
        package = build_bachelor_thesis_package()
        alignment = build_bachelor_thesis_evaluation_claim_alignment(package["evidence_index"])

        self.assertEqual(alignment["schema_version"], "unibot-gretel-thesis-evaluation-claim-alignment-v1")
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertTrue(all(alignment["contracts"].values()))
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("adaptive_task_plan", alignment["required_readiness_check_ids"])
        self.assertIn("gretel_bachelor_thesis_package", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])

        sections = {section["section_id"]: section for section in alignment["sections"]}
        self.assertIn("evaluation_learner_agency_boundary", sections["learner_agency_claim_trace"]["claim_ids"])
        self.assertIn("official grades", sections["no_high_stakes_claim"]["excluded_measures"])
        self.assertIn("source_card_drift_guard", sections["source_card_claim_trace"]["readiness_check_ids"])

    def test_evaluation_claim_alignment_blocks_unready_evaluation_trace(self) -> None:
        evidence_index = build_bachelor_thesis_evidence_index()
        evaluation_packet = {
            "learner_agency_boundary_alignment": {
                "status": "needs_review",
                "public_safety_status": "pass",
                "contracts": {"adaptive_plan_boundary_ready": False},
            },
            "measurement_plan": {
                "excluded_measures": ["official grades", "real exam performance", "disciplinary KI detection"],
            },
        }
        alignment = build_bachelor_thesis_evaluation_claim_alignment(evidence_index, evaluation_packet)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("evaluation_alignment_ready", alignment["failed_contract_ids"])
        self.assertIn("adaptive_trace_in_evaluation_ready", alignment["failed_contract_ids"])

    def test_package_is_public_safe_and_keeps_exam_boundary(self) -> None:
        payload = json.dumps(build_bachelor_thesis_package(), ensure_ascii=False)

        self.assertEqual(scan_text(payload, "bachelor-thesis-package")["status"], "pass")
        self.assertIn("real university thesis submission without human review", payload)
        self.assertIn("source_card_drift_guard", payload)
        self.assertIn("written_university_clearance_required_before_exam_use", payload)
        self.assertIn("evaluation_learner_agency_boundary", payload)
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
        self.assertIn("## Evidence Index", markdown)
        self.assertIn("## Evaluation Claim Alignment", markdown)
        self.assertIn("Source-card drift: pass", markdown)
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
