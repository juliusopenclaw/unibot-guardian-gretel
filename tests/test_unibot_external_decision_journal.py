from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.external_decision_journal import (  # noqa: E402
    append_external_decision_journal_record,
    build_external_decision_record_journal_release_claim_alignment,
    read_external_decision_journal,
    sanitize_external_decision_journal_record,
    summarize_external_decision_journal,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def valid_exam_clearance() -> dict[str, object]:
    return {
        "clearance_scope": "exam_controlled_gateway",
        "decision_status": "approved",
        "reviewer_roles": [
            "Pruefungsamt",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
            "Inklusionsbuero / Nachteilsausgleich",
        ],
        "decision_reference": "synthetic written exam clearance for journal",
        "allowed_modes": ["exam_controlled_gateway", "controlled_notebook"],
        "help_levels_allowed": ["A0", "A1", "A2"],
        "no_proctoring": True,
        "no_ai_detection": True,
        "no_automatic_grading": True,
        "human_review_required": True,
        "raw_text_public_release_allowed": False,
    }


def valid_extraction_deferral() -> dict[str, object]:
    return {
        "deferral_scope": "course_material_extraction",
        "decision_status": "approved_deferral",
        "deferred_job_types": ["ocr", "transcription"],
        "deferral_reason": "synthetic journal deferral for current public draft planning",
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic written extraction deferral for journal",
        "human_review_before_future_tutor_use": True,
        "raw_text_public_release_allowed": False,
        "exam_deployment_status": "not_cleared",
    }


class UniBotExternalDecisionJournalTests(unittest.TestCase):
    def test_valid_exam_record_is_hash_only_and_public_safe(self) -> None:
        record = sanitize_external_decision_journal_record(
            record_type="exam_clearance",
            record=valid_exam_clearance(),
        )
        payload = json.dumps(record, ensure_ascii=False)

        self.assertEqual(record["artifact_type"], "unibot_external_decision_record_journal_record")
        self.assertEqual(record["status"], "accepted")
        self.assertEqual(record["public_safety_status"], "pass")
        self.assertEqual(record["event"]["validation_status"], "ok_exam_controlled_gateway_clearance_record")
        self.assertEqual(record["event"]["exam_deployment_status"], "not_cleared")
        self.assertFalse(record["event"]["raw_record_stored"])
        self.assertFalse(record["event"]["raw_decision_reference_stored"])
        self.assertTrue(record["event"]["decision_reference_hash"])
        self.assertNotIn("synthetic written exam clearance for journal", payload)
        self.assertEqual(scan_text(payload, "external-decision-journal-test")["status"], "pass")

    def test_external_decision_record_release_claim_alignment_is_hash_only_and_gate_bound(self) -> None:
        alignment = build_external_decision_record_journal_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-external-decision-record-journal-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("local_extraction_decision", alignment["record_types"])
        self.assertIn("exam_clearance", alignment["record_types"])
        self.assertIn("extraction_deferral", alignment["record_types"])
        self.assertIn("manual_deployment_go", alignment["record_types"])
        self.assertIn("external_decision_record_journal", alignment["required_readiness_check_ids"])
        self.assertIn("stakeholder_decision_journal", alignment["required_readiness_check_ids"])
        self.assertIn("data_protection_screening", alignment["required_readiness_check_ids"])
        self.assertIn("authority_handoff", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertIn("raw written decision storage", alignment["blocked_claims"])
        self.assertIn("deployment switch", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_external_decision_record_release_claim_alignment_blocks_raw_or_deploy_records(self) -> None:
        record = sanitize_external_decision_journal_record(
            record_type="manual_deployment_go",
            deployment_go_reference="synthetic deployment go",
        )
        record["event"]["exam_deployment_status"] = "deployed"
        record["event"]["deployment_effect"] = "deployed"
        record["event"]["raw_deployment_go_reference_stored"] = True

        alignment = build_external_decision_record_journal_release_claim_alignment([record])

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("records_store_no_raw_decisions_or_deploy_text", alignment["failed_contract_ids"])
        self.assertIn("local_extraction_record_hash_only", alignment["failed_contract_ids"])
        self.assertIn("exam_clearance_record_hash_only_not_deployed", alignment["failed_contract_ids"])
        self.assertIn("extraction_deferral_record_hash_only", alignment["failed_contract_ids"])
        self.assertIn("manual_deployment_go_hash_only_no_switch", alignment["failed_contract_ids"])

    def test_invalid_record_is_blocked_and_not_stored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "decision_records.jsonl"
            result = append_external_decision_journal_record(
                record_type="exam_clearance",
                record={"clearance_scope": "exam_controlled_gateway"},
                path=path,
            )

            self.assertEqual(result["status"], "blocked")
            self.assertFalse(path.exists())
            self.assertIn("exam_clearance_record_not_valid", result["record"]["event"]["issues"])

    def test_append_read_and_summary_cover_exam_and_deferral_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "decision_records.jsonl"

            exam = append_external_decision_journal_record(
                record_type="exam_clearance",
                record=valid_exam_clearance(),
                path=path,
            )
            deferral = append_external_decision_journal_record(
                record_type="extraction_deferral",
                record=valid_extraction_deferral(),
                path=path,
            )
            listed = read_external_decision_journal(path=path)
            summary = summarize_external_decision_journal(path=path)

            self.assertEqual(exam["status"], "stored")
            self.assertEqual(deferral["status"], "stored")
            self.assertEqual(listed["count"], 2)
            self.assertEqual(summary["artifact_type"], "unibot_external_decision_record_journal_summary")
            self.assertEqual(summary["public_safety_status"], "pass")
            self.assertEqual(summary["accepted_record_count"], 2)
            self.assertTrue(summary["gate_summary"]["exam_clearance_record_valid"])
            self.assertTrue(summary["gate_summary"]["extraction_deferral_record_valid"])
            self.assertEqual(summary["gate_summary"]["exam_deployment_status"], "not_cleared")
            self.assertTrue(summary["extraction_deferral_summary"]["covers_ocr"])
            self.assertTrue(summary["extraction_deferral_summary"]["covers_transcription"])

    def test_api_routes_append_list_and_summarize(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = str(Path(temp_dir) / "decision_records.jsonl")

            status, append_payload = route_request(
                "/api/unibot/stakeholder/decision-record-journal/append",
                {
                    "record_type": "exam_clearance",
                    "record": valid_exam_clearance(),
                    "decision_record_journal_path": path,
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(append_payload["status"], "stored")

            status, listed = route_request(
                "/api/unibot/stakeholder/decision-record-journal/list",
                {"decision_record_journal_path": path},
            )
            self.assertEqual(status, 200)
            self.assertEqual(listed["count"], 1)

            status, summary = route_request(
                "/api/unibot/stakeholder/decision-record-journal/summary",
                {"decision_record_journal_path": path},
            )
            self.assertEqual(status, 200)
            self.assertTrue(summary["gate_summary"]["exam_clearance_record_valid"])
            self.assertEqual(summary["gate_summary"]["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
