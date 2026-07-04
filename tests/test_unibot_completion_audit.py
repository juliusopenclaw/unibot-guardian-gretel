from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.completion_audit import (  # noqa: E402
    build_completion_audit,
    build_completion_audit_workspace_card_closure_alignment,
    completion_audit_hash,
    completion_closure_hash,
    synthetic_completion_audit_workspace_card,
)
from unibot.external_decision_journal import (  # noqa: E402
    append_external_decision_journal_record,
    read_external_decision_journal,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_completion_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text(
        "pandas DataFrame columns dtypes boxplot debugging",
        encoding="utf-8",
    )
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "lecture.mov").write_bytes(b"video")


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
        "decision_reference": "synthetic written exam clearance",
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
        "deferral_reason": "current scope uses reviewed anchors while remaining extraction is intentionally deferred",
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic written extraction deferral",
        "human_review_before_future_tutor_use": True,
        "raw_text_public_release_allowed": False,
        "exam_deployment_status": "not_cleared",
    }


class UniBotCompletionAuditTests(unittest.TestCase):
    def test_completion_audit_marks_public_draft_ready_with_nonblocking_exam_reminder(self) -> None:
        audit = build_completion_audit()
        requirements = {item["requirement_id"]: item for item in audit["requirements"]}
        payload = json.dumps(audit, ensure_ascii=False)

        self.assertEqual(audit["artifact_type"], "unibot_project_completion_audit")
        self.assertEqual(audit["public_safety_status"], "pass")
        self.assertTrue(audit["public_draft_ready"])
        self.assertTrue(audit["goal_complete"])
        self.assertEqual(audit["status"], "complete")
        self.assertEqual(audit["exam_deployment_status"], "not_cleared")
        alignment = audit["workspace_card_closure_alignment"]
        self.assertEqual(alignment["schema_version"], "unibot-completion-audit-workspace-card-closure-alignment-v1")
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["alignment_public_safety_status"], "pass")
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertEqual(alignment["completion_audit_hash"], completion_audit_hash(audit))
        self.assertEqual(alignment["completion_closure_hash"], completion_closure_hash(audit))
        self.assertTrue(alignment["goal_complete"])
        self.assertTrue(alignment["public_draft_ready"])
        self.assertEqual(alignment["readiness_snapshot_status"], "ready")
        self.assertTrue(alignment["readiness_snapshot_hash_present"])
        self.assertEqual(alignment["command_center_route_alignment_status"], "ready")
        self.assertTrue(alignment["command_center_route_gate_linked"])
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertIn("completion_audit", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_completion_gate_linked"])
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertFalse(alignment["raw_workspace_card_returned"])
        self.assertIn("exam deployment", alignment["blocked_claims"])
        self.assertEqual(audit["open_count"], 0)
        self.assertEqual(audit["reminder_count"], 1)
        self.assertEqual(requirements["local_cycle_stop_and_go_chain"]["status"], "passed")
        self.assertTrue(requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_chain_present"])
        self.assertTrue(requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_chain_present"])
        self.assertIn(
            "P1 Rehearsal Playback Gap Coach for safe next-action selection",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Gap-Coach Guided Rehearsal Loop for next-step preparation",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Guided Loop Control Surface for visible next-click review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Confirmation Console for local cycle stop-go review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Cycle Launch Receipt for final local-cycle stop-go evidence",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Cycle Evidence Binder for hash-only pre/post cycle review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Post-Cycle Receipt Intake for human-run hash evidence",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Cycle Closure Ledger for hash-only cycle closure",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Cycle Review Timeline for chronological hash review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Cycle Review Packet for compact human review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Review Export Preview without export write",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Review Export Authorization Gate before export review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Export Review Queue for hash-only candidate review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Export Reviewer Packet for human review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Archive Decision Draft without archive or submission",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Final Review Handoff before any export archive or submission",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Manual Final Review Receipt Ledger for chronological hash review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Final Review Ledger Integrity Gate before export archive or submission proximity",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Final Manual Review Console for one human-readable hash-only view",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Final Manual Review Action Lock before export archive or submission proximity",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Locked Final Review Board for one final human hash-only review",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "P1 Locked Final Review Gap Resolver for one safe human follow-up",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["command_center_workstream_sequence"],
        )
        self.assertIn(
            "review_python_exam_rehearsal_playback_gap_coach",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "run_python_exam_gap_coach_guided_rehearsal_loop",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_guided_loop_control_surface",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_local_cycle_manual_confirmation_console",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_cycle_launch_receipt",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_cycle_evidence_binder",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_post_cycle_receipt_intake",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_cycle_closure_ledger",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_cycle_review_timeline",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_cycle_review_packet",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_review_export_preview",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_review_export_authorization_gate",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_export_review_queue",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_export_reviewer_packet",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_archive_decision_draft",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_final_review_handoff",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_manual_final_review_receipt_ledger",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_final_review_ledger_integrity_gate",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_final_manual_review_console",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_final_manual_review_action_lock",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_locked_final_review_board",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertIn(
            "review_python_exam_locked_final_review_gap_resolver",
            requirements["local_cycle_stop_and_go_chain"]["evidence"]["runbook_quickstart_step_ids"],
        )
        self.assertEqual(requirements["real_exam_authority_clearance"]["status"], "reminder")
        self.assertFalse(requirements["real_exam_authority_clearance"]["evidence"]["technical_blocker"])
        self.assertEqual(
            audit["external_real_world_reminders"][0]["reminder_id"],
            "real_exam_authority_clearance",
        )
        self.assertEqual(requirements["sidepanel_pm_flow"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_pipeline"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_decision_packet"]["status"], "passed")
        self.assertEqual(requirements["institutional_clearance_workflow"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_operator_harness"]["status"], "passed")
        self.assertEqual(requirements["stakeholder_submission_bundle"]["status"], "passed")
        self.assertEqual(requirements["stakeholder_decision_request_harness"]["status"], "passed")
        self.assertEqual(requirements["stakeholder_decision_journal_harness"]["status"], "passed")
        self.assertEqual(requirements["external_decision_state_harness"]["status"], "passed")
        self.assertEqual(requirements["external_decision_record_journal_harness"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_progress_harness"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_receipt_journal_harness"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_completion_harness"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_batch_harness"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_batch_receipt_harness"]["status"], "passed")
        self.assertEqual(requirements["course_extraction_manifest_update_harness"]["status"], "passed")
        self.assertEqual(requirements["course_tutor_coverage_harness"]["status"], "passed")
        self.assertEqual(requirements["course_study_session_harness"]["status"], "passed")
        self.assertEqual(requirements["course_study_session_receipt_harness"]["status"], "passed")
        self.assertEqual(scan_text(payload, "completion-audit-test")["status"], "pass")

    def test_completion_audit_workspace_card_alignment_rejects_unlinked_hashes(self) -> None:
        audit = build_completion_audit()
        workspace_card = synthetic_completion_audit_workspace_card()
        workspace_card["workspace_card_summary"]["checkpoint_hash"] = "wrong-audit-hash"
        workspace_card["workspace_card_summary"]["task_hash"] = "wrong-closure-hash"

        alignment = build_completion_audit_workspace_card_closure_alignment(audit, workspace_card)

        self.assertEqual(alignment["status"], "blocked")
        self.assertIn("workspace_card_completion_gate_linked", alignment["failed_contract_ids"])
        self.assertFalse(alignment["workspace_card_completion_gate_linked"])
        self.assertFalse(alignment["raw_workspace_card_returned"])

    def test_completion_audit_counts_real_material_extraction_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_completion_fixture(fixture_root)

            audit = build_completion_audit(base_path=str(fixture_root), review_policy="local_private_tutor")
            requirements = {item["requirement_id"]: item for item in audit["requirements"]}
            extraction = requirements["course_material_extraction_complete"]
            pipeline = requirements["course_extraction_pipeline"]
            decision_packet = requirements["course_extraction_decision_packet"]
            clearance = requirements["institutional_clearance_workflow"]
            operator = requirements["course_extraction_operator_harness"]
            submission = requirements["stakeholder_submission_bundle"]
            request = requirements["stakeholder_decision_request_harness"]
            journal = requirements["stakeholder_decision_journal_harness"]
            decision_state = requirements["external_decision_state_harness"]
            progress = requirements["course_extraction_progress_harness"]
            receipt_journal = requirements["course_extraction_receipt_journal_harness"]
            completion_harness = requirements["course_extraction_completion_harness"]
            batch = requirements["course_extraction_batch_harness"]
            batch_receipt = requirements["course_extraction_batch_receipt_harness"]
            manifest_update = requirements["course_extraction_manifest_update_harness"]
            coverage = requirements["course_tutor_coverage_harness"]
            study = requirements["course_study_session_harness"]
            receipt = requirements["course_study_session_receipt_harness"]

            self.assertEqual(audit["public_safety_status"], "pass")
            self.assertEqual(pipeline["status"], "passed")
            self.assertEqual(pipeline["evidence"]["job_count"], 2)
            self.assertEqual(decision_packet["status"], "passed")
            self.assertEqual(clearance["status"], "passed")
            self.assertEqual(operator["status"], "passed")
            self.assertEqual(submission["status"], "passed")
            self.assertEqual(request["status"], "passed")
            self.assertEqual(request["evidence"]["lane_id"], "rights_privacy_local_extraction")
            self.assertTrue(request["evidence"]["markdown_review_export_present"])
            self.assertEqual(journal["status"], "passed")
            self.assertFalse(journal["evidence"]["raw_text_stored"])
            self.assertEqual(decision_state["status"], "passed")
            self.assertEqual(requirements["external_decision_record_journal_harness"]["status"], "passed")
            self.assertEqual(progress["status"], "passed")
            self.assertEqual(receipt_journal["status"], "passed")
            self.assertFalse(receipt_journal["evidence"]["raw_text_stored"])
            self.assertEqual(receipt_journal["evidence"]["progress_receipt_count"], 1)
            self.assertEqual(completion_harness["status"], "passed")
            self.assertEqual(completion_harness["evidence"]["deferral_status"], "ok_extraction_deferral_record")
            self.assertEqual(batch["status"], "passed")
            self.assertEqual(batch["evidence"]["job_count"], 2)
            self.assertGreaterEqual(batch["evidence"]["batch_count"], 1)
            self.assertEqual(batch_receipt["status"], "passed")
            self.assertEqual(batch_receipt["evidence"]["selected_batch_job_count"], 2)
            self.assertEqual(manifest_update["status"], "passed")
            self.assertEqual(manifest_update["evidence"]["candidate_count"], 0)
            self.assertEqual(coverage["status"], "passed")
            self.assertGreaterEqual(coverage["evidence"]["current_ready_skill_count"], 1)
            self.assertEqual(study["status"], "passed")
            self.assertGreaterEqual(study["evidence"]["task_count"], 1)
            self.assertEqual(receipt["status"], "passed")
            self.assertFalse(receipt["evidence"]["raw_text_stored"])
            self.assertEqual(extraction["status"], "open")
            self.assertEqual(extraction["evidence"]["ocr_queue_count"], 1)
            self.assertEqual(extraction["evidence"]["transcription_queue_count"], 1)
            self.assertFalse(audit["goal_complete"])
            self.assertTrue(audit["next_best_actions"])

    def test_completion_audit_api_route(self) -> None:
        status, audit = route_request("/api/unibot/completion-audit", {})

        self.assertEqual(status, 200)
        self.assertEqual(audit["artifact_type"], "unibot_project_completion_audit")
        self.assertTrue(audit["public_draft_ready"])
        self.assertTrue(audit["goal_complete"])
        self.assertEqual(audit["workspace_card_closure_alignment"]["status"], "ready")
        self.assertTrue(audit["workspace_card_closure_alignment"]["workspace_card_completion_gate_linked"])
        self.assertEqual(audit["open_count"], 0)
        self.assertGreaterEqual(audit["reminder_count"], 1)
        self.assertTrue(audit["external_real_world_reminders"])

    def test_completion_audit_can_count_valid_exam_clearance_without_deploying(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_completion_fixture(fixture_root)

            audit = build_completion_audit(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                exam_clearance_record=valid_exam_clearance(),
            )
            requirements = {item["requirement_id"]: item for item in audit["requirements"]}

            self.assertEqual(audit["exam_deployment_status"], "not_cleared")
            self.assertEqual(requirements["real_exam_authority_clearance"]["status"], "passed")
            self.assertEqual(audit["reminder_count"], 0)
            self.assertEqual(audit["external_real_world_reminders"][0]["status"], "recorded_not_deployed")
            self.assertEqual(
                requirements["real_exam_authority_clearance"]["evidence"]["exam_authority_status"],
                "ok_exam_controlled_gateway_clearance_record",
            )
            self.assertEqual(requirements["course_material_extraction_complete"]["status"], "open")
            self.assertFalse(audit["goal_complete"])

    def test_completion_audit_can_close_with_valid_deferral_and_exam_clearance_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_completion_fixture(fixture_root)

            audit = build_completion_audit(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                exam_clearance_record=valid_exam_clearance(),
                extraction_deferral_record=valid_extraction_deferral(),
            )
            requirements = {item["requirement_id"]: item for item in audit["requirements"]}

            self.assertEqual(audit["public_safety_status"], "pass")
            self.assertTrue(audit["goal_complete"])
            self.assertEqual(audit["status"], "complete")
            self.assertEqual(requirements["course_material_extraction_complete"]["status"], "passed")
            self.assertEqual(
                requirements["course_material_extraction_complete"]["evidence"]["completion_status"],
                "complete_intentionally_deferred",
            )
            self.assertEqual(requirements["real_exam_authority_clearance"]["status"], "passed")

    def test_completion_audit_can_close_from_external_decision_journal_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir) / "materials"
            fixture_root.mkdir()
            write_completion_fixture(fixture_root)
            journal_path = Path(temp_dir) / "decision_records.jsonl"

            append_external_decision_journal_record(
                record_type="exam_clearance",
                record=valid_exam_clearance(),
                path=journal_path,
            )
            append_external_decision_journal_record(
                record_type="extraction_deferral",
                record=valid_extraction_deferral(),
                path=journal_path,
            )
            records = read_external_decision_journal(path=journal_path)["records"]

            audit = build_completion_audit(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                external_decision_records=records,
            )
            requirements = {item["requirement_id"]: item for item in audit["requirements"]}

            self.assertEqual(audit["public_safety_status"], "pass")
            self.assertTrue(audit["goal_complete"])
            self.assertEqual(audit["status"], "complete")
            self.assertEqual(audit["exam_deployment_status"], "not_cleared")
            self.assertEqual(requirements["real_exam_authority_clearance"]["status"], "passed")
            self.assertTrue(
                requirements["real_exam_authority_clearance"]["evidence"]["journal_exam_clearance_record_valid"]
            )
            self.assertEqual(requirements["course_material_extraction_complete"]["status"], "passed")
            self.assertEqual(
                requirements["course_material_extraction_complete"]["evidence"]["completion_status"],
                "complete_intentionally_deferred_by_external_decision_journal",
            )
            self.assertTrue(
                requirements["course_material_extraction_complete"]["evidence"][
                    "journal_deferral_covers_required_job_types"
                ]
            )

            status, route_audit = route_request(
                "/api/unibot/completion-audit",
                {
                    "base_path": str(fixture_root),
                    "review_policy": "local_private_tutor",
                    "decision_record_journal_path": str(journal_path),
                },
            )
            self.assertEqual(status, 200)
            self.assertTrue(route_audit["goal_complete"])
            self.assertEqual(route_audit["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
