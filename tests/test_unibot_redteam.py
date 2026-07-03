from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.redteam import (  # noqa: E402
    REDTEAM_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
    THREAT_MODEL_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
    build_redteam_claim_alignment,
    build_threat_model_release_review_board_claim_alignment,
    run_redteam_smoke,
)
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

    def test_redteam_claim_alignment_links_review_board_chain(self) -> None:
        report = run_redteam_smoke()
        alignment = report["claim_alignment"]

        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertTrue(alignment["practice_only"])
        self.assertTrue(alignment["public_summary_only"])
        self.assertTrue(alignment["hash_or_category_evidence_only"])
        self.assertEqual(
            alignment["manual_publication_claim_contract"]["expected_schema_version"],
            REDTEAM_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        )
        self.assertIn("redteam", alignment["unique_readiness_check_ids"])
        self.assertIn("notebook_template", alignment["unique_readiness_check_ids"])
        self.assertIn("browser_extension_demo_handoff", alignment["unique_readiness_check_ids"])
        self.assertIn("browser_manifest_content_boundary", alignment["unique_readiness_check_ids"])
        self.assertIn("local_demo_run", alignment["unique_readiness_check_ids"])
        self.assertIn("publication_package", alignment["unique_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["unique_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertEqual(alignment["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(alignment["missing_release_review_board_claim_human_gates"], [])
        self.assertIn("exam clearance", alignment["blocked_claims"])

    def test_redteam_claim_alignment_blocks_failed_report(self) -> None:
        report = run_redteam_smoke()
        report["status"] = "fail"
        report["failed_count"] = 1
        report["scenarios"][0]["passed"] = False
        alignment = build_redteam_claim_alignment(report)

        self.assertEqual(alignment["status"], "blocked")
        self.assertEqual(alignment["public_safety_status"], "pass")

    def test_threat_model_claim_alignment_links_review_board_chain(self) -> None:
        threat_model = (ROOT / "docs" / "unibot" / "UNIBOT_THREAT_MODEL.md").read_text(encoding="utf-8")
        alignment = build_threat_model_release_review_board_claim_alignment(threat_model)

        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(
            alignment["manual_publication_claim_contract"]["expected_schema_version"],
            THREAT_MODEL_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        )
        self.assertEqual(alignment["missing_required_phrases"], [])
        self.assertIn("source_cards", alignment["unique_readiness_check_ids"])
        self.assertIn("source_card_drift_guard", alignment["unique_readiness_check_ids"])
        self.assertIn("redteam", alignment["unique_readiness_check_ids"])
        self.assertIn("publication_package", alignment["unique_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["unique_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertEqual(alignment["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(alignment["missing_release_review_board_claim_human_gates"], [])
        self.assertIn("exam clearance", alignment["blocked_claims"])

    def test_threat_model_claim_alignment_blocks_missing_control_language(self) -> None:
        alignment = build_threat_model_release_review_board_claim_alignment("# thin threat model\n")

        self.assertEqual(alignment["status"], "blocked")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertIn("Postfilter blocks final solutions", alignment["missing_required_phrases"])

    def test_redteam_api_route(self) -> None:
        status, report = route_request("/api/unibot/redteam/run", {})

        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["scenario_count"], report["passed_count"])


if __name__ == "__main__":
    unittest.main()
