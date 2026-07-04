from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.private_tutor_use_flow import (  # noqa: E402
    build_private_tutor_use_flow_dry_run,
    build_private_tutor_use_flow_release_claim_alignment,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_flow_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "pandas_boxplot_slides.pdf").write_bytes(b"%PDF-1.4\nfixture")


def valid_decision() -> dict[str, object]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic private tutor use flow decision",
    }


def reviewed_receipt_for_job(job: dict[str, object]) -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "e" * 64,
        "extracted_text_char_count": 1200,
        "private_artifact_reference": "private tutor use flow artifact ref",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


def study_receipt_evidence() -> dict[str, object]:
    return {
        "prediction_present": True,
        "notebook_action_present": True,
        "reflection_present": True,
    }


class UniBotPrivateTutorUseFlowTests(unittest.TestCase):
    def test_private_tutor_use_flow_waits_without_manifest_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "index.json"
            write_flow_fixture(root)

            report = build_private_tutor_use_flow_dry_run(
                "Wie pruefe ich pandas Spalten?",
                base_path=str(root),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "course_private_tutor_use_flow_dry_run")
            self.assertEqual(report["status"], "waiting_for_manifest_apply_rights_decision")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertFalse(report["manifest_apply_summary"]["manifest_written"])
            self.assertFalse(report["tutor_index_summary"]["tutor_index_built"])
            self.assertFalse(report["ledger_append_summary"]["ledger_written"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(manifest_path.exists())
            self.assertFalse(index_path.exists())
            self.assertNotIn("Wie pruefe ich", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "private-tutor-use-flow-waiting")["status"], "pass")

    def test_private_tutor_use_flow_runs_confirmed_local_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            manifest_journal_path = Path(temp_dir) / "manifest_apply.jsonl"
            index_path = Path(temp_dir) / "index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            ledger_path = Path(temp_dir) / "help_ledger.jsonl"
            write_flow_fixture(root)
            queue = build_course_extraction_queue(
                base_path=str(root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = reviewed_receipt_for_job(queue["jobs"][0])

            status, report = route_request(
                "/api/unibot/course/private-tutor-use-flow/dry-run",
                {
                    "query": "Wie pruefe ich mit pandas die Spalten vor dem Boxplot?",
                    "base_path": str(root),
                    "decision_record": valid_decision(),
                    "receipts": [receipt],
                    "private_manifest_path": str(manifest_path),
                    "manifest_apply_journal_path": str(manifest_journal_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(index_journal_path),
                    "ledger_path": str(ledger_path),
                    "operator_confirmed_manifest_apply": True,
                    "operator_confirmed_tutor_index_build": True,
                    "operator_confirmed_help_ledger_append": True,
                    "requested_help_level": "A2",
                    "study_receipt": study_receipt_evidence(),
                },
            )
            payload = json.dumps(report, ensure_ascii=False)
            ledger_text = ledger_path.read_text(encoding="utf-8")

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "private_tutor_use_flow_ready_with_ledger")
            self.assertTrue(report["manifest_apply_summary"]["manifest_written"])
            self.assertTrue(report["tutor_index_summary"]["tutor_index_built"])
            self.assertEqual(report["tutor_response_summary"]["status"], "allowed")
            self.assertEqual(report["tutor_response_summary"]["effective_help_level"], "A2")
            self.assertTrue(report["ledger_append_summary"]["ledger_written"])
            self.assertEqual(report["study_receipt_validation"]["status"], "ok_study_session_receipt")
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["ledger_path_returned"])
            self.assertFalse(report["automatic_grading_started"])
            self.assertFalse(report["proctoring_started"])
            self.assertFalse(report["ai_detection_started"])
            self.assertTrue(manifest_path.exists())
            self.assertTrue(index_path.exists())
            self.assertTrue(ledger_path.exists())
            self.assertNotIn("Wie pruefe ich", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertNotIn(str(temp_dir), ledger_text)
            self.assertNotIn("private tutor use flow artifact ref", payload)
            self.assertEqual(scan_text(payload, "private-tutor-use-flow-confirmed")["status"], "pass")
            self.assertEqual(scan_text(ledger_text, "private-tutor-use-flow-ledger")["status"], "pass")

    def test_private_tutor_use_flow_release_claim_alignment_links_private_learning_boundaries(self) -> None:
        alignment = build_private_tutor_use_flow_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-private-tutor-use-flow-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["flow_public_safety_status"], "pass")
        self.assertEqual(alignment["flow_status"], "private_tutor_use_flow_ready_with_ledger")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertEqual(alignment["manifest_apply_status"], "private_manifest_applied")
        self.assertTrue(alignment["manifest_written"])
        self.assertEqual(alignment["tutor_index_status"], "private_tutor_index_built")
        self.assertTrue(alignment["tutor_index_built"])
        self.assertGreaterEqual(alignment["tutor_index_anchor_count"], 1)
        self.assertEqual(alignment["tutor_response_status"], "allowed")
        self.assertIn(alignment["effective_help_level"], {"A0", "A1", "A2"})
        self.assertGreaterEqual(alignment["source_anchor_count"], 1)
        self.assertEqual(alignment["ledger_status"], "stored")
        self.assertTrue(alignment["ledger_written"])
        self.assertEqual(alignment["study_receipt_status"], "ok_study_session_receipt")
        self.assertIn("private_tutor_use_flow", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_human_review", alignment["required_readiness_check_ids"])
        self.assertIn("extraction_manifest_apply", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["reviewed_private_manifest_evidence_operator_confirmed"])
        self.assertTrue(alignment["contracts"]["hash_only_tutor_index_operator_confirmed"])
        self.assertTrue(alignment["contracts"]["learner_agency_a0_a2_source_anchored"])
        self.assertTrue(alignment["contracts"]["help_ledger_operator_confirmed_hash_only"])
        self.assertTrue(alignment["contracts"]["public_outputs_hide_private_data"])
        self.assertTrue(alignment["contracts"]["high_stakes_actions_not_started"])
        self.assertIn("private manifest apply without operator confirmation", alignment["blocked_claims"])
        self.assertIn("private tutor index build without operator confirmation", alignment["blocked_claims"])
        self.assertIn("complete code or final-answer tutoring", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_private_tutor_use_flow_release_claim_alignment_blocks_unconfirmed_or_high_stakes_claims(self) -> None:
        flow = build_private_tutor_use_flow_release_claim_alignment()["policy"]
        self.assertIn("operator-confirmed", flow)
        report = {
            "status": "private_tutor_use_flow_ready_with_ledger",
            "public_safety_status": "pass",
            "exam_deployment_status": "cleared",
            "execution_boundary": "Private tutor returns raw text and clears exam deployment.",
            "manifest_apply_summary": {
                "status": "private_manifest_applied",
                "manifest_written": True,
                "path_returned": True,
            },
            "tutor_index_summary": {
                "status": "private_tutor_index_built",
                "tutor_index_built": True,
                "path_returned": True,
                "anchor_count": 0,
            },
            "tutor_response_summary": {
                "status": "allowed",
                "effective_help_level": "A6",
                "source_anchor_count": 0,
                "raw_query_returned": True,
            },
            "ledger_append_summary": {"status": "stored", "ledger_written": True, "path_returned": True, "event_hash": ""},
            "study_receipt_validation": {"status": "blocked"},
            "operator_confirmed_manifest_apply": False,
            "operator_confirmed_tutor_index_build": False,
            "operator_confirmed_help_ledger_append": False,
            "raw_query_returned": True,
            "raw_text_returned": True,
            "local_paths_returned": True,
            "private_manifest_path_returned": True,
            "tutor_index_path_returned": True,
            "ledger_path_returned": True,
            "automatic_grading_started": True,
            "proctoring_started": True,
            "ai_detection_started": True,
        }

        alignment = build_private_tutor_use_flow_release_claim_alignment(report)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("reviewed_private_manifest_evidence_operator_confirmed", alignment["failed_contract_ids"])
        self.assertIn("hash_only_tutor_index_operator_confirmed", alignment["failed_contract_ids"])
        self.assertIn("learner_agency_a0_a2_source_anchored", alignment["failed_contract_ids"])
        self.assertIn("help_ledger_operator_confirmed_hash_only", alignment["failed_contract_ids"])
        self.assertIn("public_outputs_hide_private_data", alignment["failed_contract_ids"])
        self.assertIn("high_stakes_actions_not_started", alignment["failed_contract_ids"])


if __name__ == "__main__":
    unittest.main()
