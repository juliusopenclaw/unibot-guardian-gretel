from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unibot.readiness as readiness_module  # noqa: E402
from unibot.readiness import (  # noqa: E402
    build_autonomous_loop_docs_traceability,
    build_readiness_evidence_snapshot,
    build_readiness_markdown,
    build_readiness_runtime_guard,
    default_public_paths,
    run_readiness_check,
)
from unibot.autonomous_research_loop import build_autonomous_research_loop  # noqa: E402
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
        self.assertIn("readiness_runtime_guard", check_ids)
        self.assertIn("redteam", check_ids)
        self.assertIn("publication_package", check_ids)
        self.assertIn("evaluation_packet", check_ids)
        self.assertIn("authority_handoff", check_ids)
        self.assertIn("notebook_template", check_ids)
        self.assertIn("source_card_drift_guard", check_ids)
        self.assertIn("course_material_policy", check_ids)
        self.assertIn("adaptive_task_plan", check_ids)
        self.assertIn("local_demo_run", check_ids)
        self.assertIn("browser_extension_demo_handoff", check_ids)
        self.assertIn("browser_manifest_content_boundary", check_ids)
        self.assertIn("demo_feedback_contract", check_ids)
        self.assertIn("demo_feedback_triage", check_ids)
        self.assertIn("github_issue_bundle", check_ids)
        self.assertIn("release_runbook", check_ids)
        self.assertIn("compliance_matrix", check_ids)
        self.assertIn("pilot_protocol", check_ids)
        self.assertIn("data_protection_screening", check_ids)
        self.assertIn("review_board_packet", check_ids)
        self.assertIn("stakeholder_submission_bundle", check_ids)
        self.assertIn("stakeholder_decision_request", check_ids)
        self.assertIn("stakeholder_decision_journal", check_ids)
        self.assertIn("external_decision_record_journal", check_ids)
        self.assertIn("external_decision_state", check_ids)
        self.assertIn("extraction_receipt_journal", check_ids)
        self.assertIn("exam_packet_timeline", check_ids)
        self.assertIn("timeline_export_review_packet", check_ids)
        self.assertIn("timeline_export_receipt_journal", check_ids)
        self.assertIn("material_coverage_run", check_ids)
        self.assertIn("extraction_progress", check_ids)
        self.assertIn("extraction_manifest_update", check_ids)
        self.assertIn("extraction_manifest_apply", check_ids)
        self.assertIn("extraction_completion", check_ids)
        self.assertIn("extraction_human_review", check_ids)
        self.assertIn("private_tutor_use_flow", check_ids)
        self.assertIn("study_session", check_ids)
        self.assertIn("notebook_checkpoint", check_ids)
        self.assertIn("exam_workspace_launch", check_ids)
        self.assertIn("exam_workspace_run", check_ids)
        self.assertIn("exam_workspace_run_history", check_ids)
        self.assertIn("gretel_glm_evolve_lane", check_ids)
        self.assertIn("gretel_bachelor_thesis_package", check_ids)
        self.assertIn("gretel_autonomous_research_loop", check_ids)
        self.assertIn("exam_boundary", check_ids)
        self.assertIn("public draft review", report["ready_for"])
        self.assertIn("exam deployment", report["not_ready_for"])
        self.assertEqual(report["runtime_guard"]["status"], "budget_guard_ready")
        self.assertEqual(report["runtime_guard"]["routine_budget"]["default_execution_mode"], "focused_readiness")
        self.assertIs(report["runtime_guard"]["routine_budget"]["full_suite_required_by_default"], False)
        self.assertIs(report["runtime_guard"]["routine_budget"]["provider_calls_allowed_by_default"], False)
        self.assertIs(report["runtime_guard"]["routine_budget"]["external_actions_allowed_by_default"], False)
        self.assertEqual(report["source_card_drift"]["status"], "pass")
        self.assertEqual(report["source_card_drift"]["missing_required_source_card_ids"], [])
        self.assertEqual(report["source_card_drift"]["unlisted_high_risk_source_card_ids"], [])
        redteam = next(check for check in report["checks"] if check["check_id"] == "redteam")
        self.assertEqual(
            redteam["evidence"]["manual_publication_claim_contract_status"],
            "unibot-redteam-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(redteam["evidence"]["claim_alignment_status"], "ready")
        self.assertEqual(redteam["evidence"]["claim_alignment_public_safety_status"], "pass")
        self.assertTrue(redteam["evidence"]["hash_or_category_evidence_only"])
        self.assertTrue(redteam["evidence"]["notebook_handoff_claim_linked"])
        self.assertTrue(redteam["evidence"]["browser_handoff_claim_linked"])
        self.assertTrue(redteam["evidence"]["browser_manifest_boundary_linked"])
        self.assertTrue(redteam["evidence"]["local_demo_claim_linked"])
        self.assertTrue(redteam["evidence"]["publication_claim_linked"])
        self.assertTrue(redteam["evidence"]["review_board_claim_linked"])
        self.assertTrue(redteam["evidence"]["human_submission_gate_linked"])
        self.assertTrue(redteam["evidence"]["exam_clearance_blocked"])
        self.assertEqual(redteam["evidence"]["threat_model_claim_alignment_status"], "ready")
        self.assertEqual(
            redteam["evidence"]["threat_model_claim_contract_status"],
            "unibot-threat-model-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(redteam["evidence"]["threat_model_missing_required_phrase_count"], 0)
        self.assertTrue(redteam["evidence"]["threat_model_source_cards_linked"])
        self.assertTrue(redteam["evidence"]["threat_model_release_runbook_linked"])
        publication = next(check for check in report["checks"] if check["check_id"] == "publication_package")
        self.assertEqual(publication["evidence"]["reproducibility_alignment_status"], "ready")
        self.assertIn("human_submission_review_required", publication["evidence"]["reproducibility_alignment_human_gates"])
        evaluation = next(check for check in report["checks"] if check["check_id"] == "evaluation_packet")
        self.assertEqual(evaluation["evidence"]["learner_agency_alignment_status"], "ready")
        self.assertIn(
            "human_submission_review_required",
            evaluation["evidence"]["learner_agency_alignment_human_gates"],
        )
        authority = next(check for check in report["checks"] if check["check_id"] == "authority_handoff")
        self.assertEqual(authority["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(authority["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            authority["evidence"]["release_claim_alignment_contract_status"],
            "unibot-authority-handoff-release-review-board-claim-alignment-v1",
        )
        self.assertTrue(authority["evidence"]["review_board_claim_linked"])
        self.assertTrue(authority["evidence"]["source_card_drift_claim_linked"])
        self.assertTrue(authority["evidence"]["compliance_claim_linked"])
        self.assertTrue(authority["evidence"]["public_safety_claim_linked"])
        self.assertTrue(authority["evidence"]["human_submission_gate_linked"])
        self.assertTrue(authority["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(authority["evidence"]["exam_clearance_blocked"])
        self.assertIn(
            "written_university_clearance_required_before_exam_use",
            authority["evidence"]["release_claim_alignment_human_gates"],
        )
        stakeholder_submission = next(check for check in report["checks"] if check["check_id"] == "stakeholder_submission_bundle")
        self.assertEqual(stakeholder_submission["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(stakeholder_submission["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            stakeholder_submission["evidence"]["release_claim_alignment_contract_status"],
            "unibot-stakeholder-submission-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(stakeholder_submission["evidence"]["decision_lane_count"], 2)
        self.assertTrue(stakeholder_submission["evidence"]["review_board_claim_linked"])
        self.assertTrue(stakeholder_submission["evidence"]["authority_handoff_claim_linked"])
        self.assertTrue(stakeholder_submission["evidence"]["data_protection_claim_linked"])
        self.assertTrue(stakeholder_submission["evidence"]["source_card_drift_claim_linked"])
        self.assertTrue(stakeholder_submission["evidence"]["human_submission_gate_linked"])
        self.assertTrue(stakeholder_submission["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(stakeholder_submission["evidence"]["exam_clearance_blocked"])
        self.assertTrue(stakeholder_submission["evidence"]["automatic_submission_blocked"])
        self.assertIn(
            "written_university_clearance_required_before_exam_use",
            stakeholder_submission["evidence"]["release_claim_alignment_human_gates"],
        )
        stakeholder_decision = next(check for check in report["checks"] if check["check_id"] == "stakeholder_decision_request")
        self.assertEqual(stakeholder_decision["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(stakeholder_decision["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            stakeholder_decision["evidence"]["release_claim_alignment_contract_status"],
            "unibot-stakeholder-decision-request-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(stakeholder_decision["evidence"]["lane_id"], "rights_privacy_local_extraction")
        self.assertFalse(stakeholder_decision["evidence"]["receipt_tool_sent_message"])
        self.assertFalse(stakeholder_decision["evidence"]["receipt_raw_decision_text_included"])
        self.assertTrue(stakeholder_decision["evidence"]["submission_bundle_claim_linked"])
        self.assertTrue(stakeholder_decision["evidence"]["review_board_claim_linked"])
        self.assertTrue(stakeholder_decision["evidence"]["data_protection_claim_linked"])
        self.assertTrue(stakeholder_decision["evidence"]["human_submission_gate_linked"])
        self.assertTrue(stakeholder_decision["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(stakeholder_decision["evidence"]["automatic_external_send_blocked"])
        self.assertTrue(stakeholder_decision["evidence"]["raw_decision_storage_blocked"])
        self.assertTrue(stakeholder_decision["evidence"]["exam_clearance_blocked"])
        stakeholder_journal = next(check for check in report["checks"] if check["check_id"] == "stakeholder_decision_journal")
        self.assertEqual(stakeholder_journal["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(stakeholder_journal["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            stakeholder_journal["evidence"]["release_claim_alignment_contract_status"],
            "unibot-stakeholder-decision-journal-release-review-board-claim-alignment-v1",
        )
        self.assertIn("decision_request_prepared", stakeholder_journal["evidence"]["event_types"])
        self.assertIn("decision_request_receipt_validated", stakeholder_journal["evidence"]["event_types"])
        self.assertTrue(stakeholder_journal["evidence"]["decision_request_claim_linked"])
        self.assertTrue(stakeholder_journal["evidence"]["submission_bundle_claim_linked"])
        self.assertTrue(stakeholder_journal["evidence"]["data_protection_claim_linked"])
        self.assertTrue(stakeholder_journal["evidence"]["review_board_claim_linked"])
        self.assertTrue(stakeholder_journal["evidence"]["human_submission_gate_linked"])
        self.assertTrue(stakeholder_journal["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(stakeholder_journal["evidence"]["raw_decision_storage_blocked"])
        self.assertTrue(stakeholder_journal["evidence"]["tool_sent_message_blocked"])
        self.assertTrue(stakeholder_journal["evidence"]["automatic_gate_change_blocked"])
        self.assertTrue(stakeholder_journal["evidence"]["exam_clearance_blocked"])
        external_journal = next(check for check in report["checks"] if check["check_id"] == "external_decision_record_journal")
        self.assertEqual(external_journal["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(external_journal["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            external_journal["evidence"]["release_claim_alignment_contract_status"],
            "unibot-external-decision-record-journal-release-review-board-claim-alignment-v1",
        )
        self.assertIn("local_extraction_decision", external_journal["evidence"]["record_types"])
        self.assertIn("exam_clearance", external_journal["evidence"]["record_types"])
        self.assertIn("extraction_deferral", external_journal["evidence"]["record_types"])
        self.assertIn("manual_deployment_go", external_journal["evidence"]["record_types"])
        self.assertTrue(external_journal["evidence"]["decision_journal_claim_linked"])
        self.assertTrue(external_journal["evidence"]["data_protection_claim_linked"])
        self.assertTrue(external_journal["evidence"]["authority_handoff_claim_linked"])
        self.assertTrue(external_journal["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(external_journal["evidence"]["human_submission_gate_linked"])
        self.assertTrue(external_journal["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(external_journal["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(external_journal["evidence"]["raw_decision_storage_blocked"])
        self.assertTrue(external_journal["evidence"]["deployment_switch_blocked"])
        self.assertTrue(external_journal["evidence"]["exam_deployment_blocked"])
        external_state = next(check for check in report["checks"] if check["check_id"] == "external_decision_state")
        self.assertEqual(external_state["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(external_state["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            external_state["evidence"]["release_claim_alignment_contract_status"],
            "unibot-external-decision-state-release-review-board-claim-alignment-v1",
        )
        self.assertTrue(external_state["evidence"]["decision_record_journal_claim_linked"])
        self.assertTrue(external_state["evidence"]["data_protection_claim_linked"])
        self.assertTrue(external_state["evidence"]["authority_handoff_claim_linked"])
        self.assertTrue(external_state["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(external_state["evidence"]["human_submission_gate_linked"])
        self.assertTrue(external_state["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(external_state["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(external_state["evidence"]["raw_decision_storage_blocked"])
        self.assertTrue(external_state["evidence"]["silent_deployment_switch_blocked"])
        self.assertTrue(external_state["evidence"]["exam_deployment_blocked"])
        receipt_journal = next(check for check in report["checks"] if check["check_id"] == "extraction_receipt_journal")
        self.assertEqual(receipt_journal["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(receipt_journal["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            receipt_journal["evidence"]["release_claim_alignment_contract_status"],
            "unibot-extraction-receipt-journal-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(receipt_journal["evidence"]["accepted_record_count"], 2)
        self.assertGreaterEqual(receipt_journal["evidence"]["ready_for_human_review_count"], 1)
        self.assertGreaterEqual(receipt_journal["evidence"]["eligible_for_private_tutor_index_count"], 1)
        self.assertTrue(receipt_journal["evidence"]["data_protection_claim_linked"])
        self.assertTrue(receipt_journal["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(receipt_journal["evidence"]["course_material_policy_claim_linked"])
        self.assertTrue(receipt_journal["evidence"]["review_board_claim_linked"])
        self.assertTrue(receipt_journal["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(receipt_journal["evidence"]["human_submission_gate_linked"])
        self.assertTrue(receipt_journal["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(receipt_journal["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(receipt_journal["evidence"]["hash_only_records"])
        self.assertTrue(receipt_journal["evidence"]["raw_text_storage_blocked"])
        self.assertTrue(receipt_journal["evidence"]["local_path_storage_blocked"])
        self.assertTrue(receipt_journal["evidence"]["manifest_update_by_receipt_alone_blocked"])
        self.assertTrue(receipt_journal["evidence"]["cloud_processing_blocked"])
        self.assertTrue(receipt_journal["evidence"]["exam_deployment_blocked"])
        extraction_progress = next(check for check in report["checks"] if check["check_id"] == "extraction_progress")
        self.assertEqual(extraction_progress["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(extraction_progress["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            extraction_progress["evidence"]["release_claim_alignment_contract_status"],
            "unibot-extraction-progress-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(extraction_progress["evidence"]["report_public_safety_status"], "pass")
        self.assertEqual(extraction_progress["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertGreaterEqual(extraction_progress["evidence"]["valid_receipt_count"], 2)
        self.assertGreaterEqual(extraction_progress["evidence"]["review_queue_count"], 1)
        self.assertGreaterEqual(extraction_progress["evidence"]["manifest_update_candidate_count"], 1)
        self.assertTrue(extraction_progress["evidence"]["receipt_journal_claim_linked"])
        self.assertTrue(extraction_progress["evidence"]["course_material_policy_claim_linked"])
        self.assertTrue(extraction_progress["evidence"]["data_protection_claim_linked"])
        self.assertTrue(extraction_progress["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(extraction_progress["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(extraction_progress["evidence"]["human_submission_gate_linked"])
        self.assertTrue(extraction_progress["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(extraction_progress["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(extraction_progress["evidence"]["review_queue_hash_only"])
        self.assertTrue(extraction_progress["evidence"]["manifest_candidates_private_metadata_only"])
        self.assertTrue(extraction_progress["evidence"]["raw_text_in_progress_blocked"])
        self.assertTrue(extraction_progress["evidence"]["local_path_in_progress_blocked"])
        self.assertTrue(extraction_progress["evidence"]["tutor_retrieval_without_manifest_update_blocked"])
        self.assertTrue(extraction_progress["evidence"]["cloud_processing_blocked"])
        self.assertTrue(extraction_progress["evidence"]["exam_deployment_blocked"])
        manifest_update = next(check for check in report["checks"] if check["check_id"] == "extraction_manifest_update")
        self.assertEqual(manifest_update["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(manifest_update["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            manifest_update["evidence"]["release_claim_alignment_contract_status"],
            "unibot-extraction-manifest-update-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(manifest_update["evidence"]["plan_public_safety_status"], "pass")
        self.assertEqual(manifest_update["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertGreaterEqual(manifest_update["evidence"]["candidate_count"], 1)
        self.assertGreaterEqual(manifest_update["evidence"]["ready_to_apply_private_count"], 1)
        self.assertTrue(manifest_update["evidence"]["progress_claim_linked"])
        self.assertTrue(manifest_update["evidence"]["receipt_journal_claim_linked"])
        self.assertTrue(manifest_update["evidence"]["course_material_policy_claim_linked"])
        self.assertTrue(manifest_update["evidence"]["data_protection_claim_linked"])
        self.assertTrue(manifest_update["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(manifest_update["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(manifest_update["evidence"]["human_submission_gate_linked"])
        self.assertTrue(manifest_update["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(manifest_update["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(manifest_update["evidence"]["execution_boundary_blocks_file_write_raw_and_paths"])
        self.assertTrue(manifest_update["evidence"]["candidates_private_metadata_only"])
        self.assertTrue(manifest_update["evidence"]["manifest_file_write_by_planning_blocked"])
        self.assertTrue(manifest_update["evidence"]["raw_text_storage_blocked"])
        self.assertTrue(manifest_update["evidence"]["local_source_path_exposure_blocked"])
        self.assertTrue(manifest_update["evidence"]["public_release_by_plan_blocked"])
        self.assertTrue(manifest_update["evidence"]["cloud_processing_blocked"])
        self.assertTrue(manifest_update["evidence"]["exam_deployment_blocked"])
        manifest_apply = next(check for check in report["checks"] if check["check_id"] == "extraction_manifest_apply")
        self.assertEqual(manifest_apply["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(manifest_apply["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            manifest_apply["evidence"]["release_claim_alignment_contract_status"],
            "unibot-extraction-manifest-apply-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(manifest_apply["evidence"]["dry_run_public_safety_status"], "pass")
        self.assertEqual(manifest_apply["evidence"]["confirmed_public_safety_status"], "pass")
        self.assertEqual(manifest_apply["evidence"]["dry_run_status"], "manifest_apply_dry_run_ready")
        self.assertEqual(manifest_apply["evidence"]["confirmed_status"], "private_manifest_applied")
        self.assertGreaterEqual(manifest_apply["evidence"]["dry_run_records_to_apply_count"], 1)
        self.assertGreaterEqual(manifest_apply["evidence"]["confirmed_applied_count"], 1)
        self.assertTrue(manifest_apply["evidence"]["manifest_update_claim_linked"])
        self.assertTrue(manifest_apply["evidence"]["progress_claim_linked"])
        self.assertTrue(manifest_apply["evidence"]["receipt_journal_claim_linked"])
        self.assertTrue(manifest_apply["evidence"]["course_material_policy_claim_linked"])
        self.assertTrue(manifest_apply["evidence"]["data_protection_claim_linked"])
        self.assertTrue(manifest_apply["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(manifest_apply["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(manifest_apply["evidence"]["human_submission_gate_linked"])
        self.assertTrue(manifest_apply["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(manifest_apply["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(manifest_apply["evidence"]["dry_run_does_not_write"])
        self.assertTrue(manifest_apply["evidence"]["confirmed_write_requires_operator_confirmation"])
        self.assertTrue(manifest_apply["evidence"]["public_outputs_hide_paths_and_raw_text"])
        self.assertTrue(manifest_apply["evidence"]["tutor_indexing_never_started"])
        self.assertTrue(manifest_apply["evidence"]["raw_text_returned_blocked"])
        self.assertTrue(manifest_apply["evidence"]["local_path_returned_blocked"])
        self.assertTrue(manifest_apply["evidence"]["private_manifest_path_returned_blocked"])
        self.assertTrue(manifest_apply["evidence"]["tutor_indexing_started_blocked"])
        self.assertTrue(manifest_apply["evidence"]["cloud_processing_blocked"])
        self.assertTrue(manifest_apply["evidence"]["exam_deployment_blocked"])
        completion = next(check for check in report["checks"] if check["check_id"] == "extraction_completion")
        self.assertEqual(completion["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(completion["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            completion["evidence"]["release_claim_alignment_contract_status"],
            "unibot-extraction-completion-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(completion["evidence"]["receipt_completion_public_safety_status"], "pass")
        self.assertEqual(completion["evidence"]["deferral_completion_public_safety_status"], "pass")
        self.assertEqual(completion["evidence"]["receipt_completion_status"], "complete_by_reviewed_receipts")
        self.assertEqual(completion["evidence"]["deferral_completion_status"], "complete_intentionally_deferred")
        self.assertGreaterEqual(completion["evidence"]["receipt_completed_job_count"], completion["evidence"]["receipt_open_job_count"])
        self.assertGreaterEqual(completion["evidence"]["deferral_deferred_job_count"], completion["evidence"]["deferral_open_job_count"])
        self.assertTrue(completion["evidence"]["receipt_journal_claim_linked"])
        self.assertTrue(completion["evidence"]["progress_claim_linked"])
        self.assertTrue(completion["evidence"]["manifest_update_claim_linked"])
        self.assertTrue(completion["evidence"]["manifest_apply_claim_linked"])
        self.assertTrue(completion["evidence"]["data_protection_claim_linked"])
        self.assertTrue(completion["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(completion["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(completion["evidence"]["human_submission_gate_linked"])
        self.assertTrue(completion["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(completion["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(completion["evidence"]["receipt_completion_covers_all_jobs"])
        self.assertTrue(completion["evidence"]["deferral_completion_covers_all_jobs_hash_only"])
        self.assertTrue(completion["evidence"]["completion_boundaries_block_execution_manifest_and_exam"])
        self.assertTrue(completion["evidence"]["raw_deferral_reason_storage_blocked"])
        self.assertTrue(completion["evidence"]["manifest_update_by_completion_report_blocked"])
        self.assertTrue(completion["evidence"]["tutor_indexing_by_completion_report_blocked"])
        self.assertTrue(completion["evidence"]["cloud_processing_blocked"])
        self.assertTrue(completion["evidence"]["exam_deployment_blocked"])
        human_review = next(check for check in report["checks"] if check["check_id"] == "extraction_human_review")
        self.assertEqual(human_review["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(human_review["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            human_review["evidence"]["release_claim_alignment_contract_status"],
            "unibot-extraction-human-review-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(human_review["evidence"]["plan_public_safety_status"], "pass")
        self.assertEqual(human_review["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertEqual(human_review["evidence"]["plan_status"], "review_decisions_recorded_manifest_apply_plan_ready")
        self.assertGreaterEqual(human_review["evidence"]["stored_review_decision_count"], 1)
        self.assertEqual(human_review["evidence"]["invalid_review_decision_count"], 0)
        self.assertGreaterEqual(human_review["evidence"]["appended_review_receipt_count"], 1)
        self.assertGreaterEqual(human_review["evidence"]["appended_review_record_count"], 1)
        self.assertGreaterEqual(
            human_review["evidence"]["post_reviewed_for_private_tutor_count"],
            human_review["evidence"]["appended_review_receipt_count"],
        )
        self.assertGreaterEqual(
            human_review["evidence"]["ready_to_apply_private_count"],
            human_review["evidence"]["appended_review_receipt_count"],
        )
        self.assertTrue(human_review["evidence"]["receipt_journal_claim_linked"])
        self.assertTrue(human_review["evidence"]["progress_claim_linked"])
        self.assertTrue(human_review["evidence"]["completion_claim_linked"])
        self.assertTrue(human_review["evidence"]["manifest_update_claim_linked"])
        self.assertTrue(human_review["evidence"]["manifest_apply_claim_linked"])
        self.assertTrue(human_review["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(human_review["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(human_review["evidence"]["human_submission_gate_linked"])
        self.assertTrue(human_review["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(human_review["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(human_review["evidence"]["review_decisions_recorded_hash_only"])
        self.assertTrue(human_review["evidence"]["local_private_artifact_review_required"])
        self.assertTrue(human_review["evidence"]["private_manifest_plan_only"])
        self.assertTrue(human_review["evidence"]["completion_evidence_linked"])
        self.assertTrue(human_review["evidence"]["raw_review_notes_storage_blocked"])
        self.assertTrue(human_review["evidence"]["raw_text_returned_blocked"])
        self.assertTrue(human_review["evidence"]["manifest_write_by_human_review_alone_blocked"])
        self.assertTrue(human_review["evidence"]["tutor_indexing_by_human_review_alone_blocked"])
        self.assertTrue(human_review["evidence"]["cloud_processing_blocked"])
        self.assertTrue(human_review["evidence"]["exam_deployment_blocked"])
        tutor_flow = next(check for check in report["checks"] if check["check_id"] == "private_tutor_use_flow")
        self.assertEqual(tutor_flow["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(tutor_flow["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            tutor_flow["evidence"]["release_claim_alignment_contract_status"],
            "unibot-private-tutor-use-flow-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(tutor_flow["evidence"]["workspace_card_private_use_alignment_status"], "ready")
        self.assertEqual(
            tutor_flow["evidence"]["workspace_card_private_use_alignment_public_safety_status"],
            "pass",
        )
        self.assertEqual(
            tutor_flow["evidence"]["workspace_card_private_use_alignment_contract_status"],
            "unibot-private-tutor-use-flow-workspace-card-private-use-alignment-v1",
        )
        self.assertEqual(
            tutor_flow["evidence"]["workspace_card_private_use_receipt_status"],
            "private_tutor_use_flow_receipt_ready_not_exam_clearance",
        )
        self.assertEqual(tutor_flow["evidence"]["flow_public_safety_status"], "pass")
        self.assertEqual(tutor_flow["evidence"]["flow_status"], "private_tutor_use_flow_ready_with_ledger")
        self.assertEqual(tutor_flow["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertEqual(tutor_flow["evidence"]["manifest_apply_status"], "private_manifest_applied")
        self.assertTrue(tutor_flow["evidence"]["manifest_written"])
        self.assertEqual(tutor_flow["evidence"]["tutor_index_status"], "private_tutor_index_built")
        self.assertTrue(tutor_flow["evidence"]["tutor_index_built"])
        self.assertGreaterEqual(tutor_flow["evidence"]["tutor_index_anchor_count"], 1)
        self.assertEqual(tutor_flow["evidence"]["tutor_response_status"], "allowed")
        self.assertIn(tutor_flow["evidence"]["effective_help_level"], {"A0", "A1", "A2"})
        self.assertGreaterEqual(tutor_flow["evidence"]["source_anchor_count"], 1)
        self.assertEqual(tutor_flow["evidence"]["ledger_status"], "stored")
        self.assertTrue(tutor_flow["evidence"]["ledger_written"])
        self.assertEqual(tutor_flow["evidence"]["study_receipt_status"], "ok_study_session_receipt")
        self.assertTrue(tutor_flow["evidence"]["human_review_claim_linked"])
        self.assertTrue(tutor_flow["evidence"]["manifest_apply_claim_linked"])
        self.assertTrue(tutor_flow["evidence"]["completion_claim_linked"])
        self.assertTrue(tutor_flow["evidence"]["evaluation_claim_linked"])
        self.assertTrue(tutor_flow["evidence"]["review_board_claim_linked"])
        self.assertTrue(tutor_flow["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(tutor_flow["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(tutor_flow["evidence"]["human_submission_gate_linked"])
        self.assertTrue(tutor_flow["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(tutor_flow["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(tutor_flow["evidence"]["reviewed_private_manifest_evidence_operator_confirmed"])
        self.assertTrue(tutor_flow["evidence"]["hash_only_tutor_index_operator_confirmed"])
        self.assertTrue(tutor_flow["evidence"]["learner_agency_a0_a2_source_anchored"])
        self.assertTrue(tutor_flow["evidence"]["help_ledger_operator_confirmed_hash_only"])
        self.assertTrue(tutor_flow["evidence"]["workspace_card_private_tutor_flow_gate_linked"])
        self.assertTrue(tutor_flow["evidence"]["workspace_card_operator_prefill_hash_present"])
        self.assertTrue(tutor_flow["evidence"]["public_outputs_hide_private_data"])
        self.assertTrue(tutor_flow["evidence"]["high_stakes_actions_not_started"])
        self.assertTrue(tutor_flow["evidence"]["raw_query_returned_blocked"])
        self.assertTrue(tutor_flow["evidence"]["raw_text_returned_blocked"])
        self.assertTrue(tutor_flow["evidence"]["unconfirmed_manifest_apply_blocked"])
        self.assertTrue(tutor_flow["evidence"]["unconfirmed_tutor_index_build_blocked"])
        self.assertTrue(tutor_flow["evidence"]["complete_code_or_final_answer_tutoring_blocked"])
        self.assertTrue(tutor_flow["evidence"]["cloud_processing_blocked"])
        self.assertTrue(tutor_flow["evidence"]["exam_deployment_blocked"])
        study_session = next(check for check in report["checks"] if check["check_id"] == "study_session")
        self.assertEqual(study_session["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(study_session["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            study_session["evidence"]["release_claim_alignment_contract_status"],
            "unibot-study-session-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(study_session["evidence"]["workspace_card_study_alignment_status"], "ready")
        self.assertEqual(study_session["evidence"]["workspace_card_study_alignment_public_safety_status"], "pass")
        self.assertEqual(
            study_session["evidence"]["workspace_card_study_alignment_contract_status"],
            "unibot-study-session-workspace-card-study-alignment-v1",
        )
        self.assertEqual(
            study_session["evidence"]["workspace_card_study_receipt_status"],
            "study_session_review_receipt_ready_not_exam_clearance",
        )
        self.assertEqual(study_session["evidence"]["review_public_safety_status"], "pass")
        self.assertEqual(study_session["evidence"]["review_status"], "study_session_evidence_ready_for_human_review")
        self.assertEqual(study_session["evidence"]["study_session_status"], "ready_for_course_bound_practice")
        self.assertEqual(study_session["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertGreaterEqual(study_session["evidence"]["planned_task_count"], 1)
        self.assertGreaterEqual(study_session["evidence"]["valid_receipt_count"], 1)
        self.assertEqual(study_session["evidence"]["blocked_receipt_count"], 0)
        self.assertEqual(study_session["evidence"]["repeat_task_required_count"], 0)
        self.assertEqual(study_session["evidence"]["missing_planned_receipt_count"], 0)
        self.assertEqual(study_session["evidence"]["repeat_validation_status"], "repeat_task_required")
        self.assertEqual(study_session["evidence"]["repeat_validation_public_safety_status"], "pass")
        self.assertTrue(study_session["evidence"]["repeat_task_required"])
        self.assertTrue(study_session["evidence"]["private_tutor_use_flow_claim_linked"])
        self.assertTrue(study_session["evidence"]["evaluation_claim_linked"])
        self.assertTrue(study_session["evidence"]["review_board_claim_linked"])
        self.assertTrue(study_session["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(study_session["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(study_session["evidence"]["human_submission_gate_linked"])
        self.assertTrue(study_session["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(study_session["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(study_session["evidence"]["study_plan_ready_for_course_bound_practice"])
        self.assertTrue(study_session["evidence"]["hash_only_receipts_with_required_evidence"])
        self.assertTrue(study_session["evidence"]["learner_agency_profile_complete"])
        self.assertTrue(study_session["evidence"]["a6_or_final_solution_forces_repeat"])
        self.assertTrue(study_session["evidence"]["workspace_card_study_session_gate_linked"])
        self.assertTrue(study_session["evidence"]["workspace_card_operator_prefill_hash_present"])
        self.assertTrue(study_session["evidence"]["non_grading_human_review_only"])
        self.assertTrue(study_session["evidence"]["raw_reflection_storage_blocked"])
        self.assertTrue(study_session["evidence"]["final_solution_acceptance_blocked"])
        self.assertTrue(study_session["evidence"]["eigenleistung_percentage_claim_blocked"])
        self.assertTrue(study_session["evidence"]["automatic_grading_blocked"])
        self.assertTrue(study_session["evidence"]["proctoring_blocked"])
        self.assertTrue(study_session["evidence"]["ki_detection_evidence_blocked"])
        self.assertTrue(study_session["evidence"]["cloud_processing_blocked"])
        self.assertTrue(study_session["evidence"]["exam_deployment_blocked"])
        checkpoint = next(check for check in report["checks"] if check["check_id"] == "notebook_checkpoint")
        self.assertEqual(checkpoint["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(checkpoint["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            checkpoint["evidence"]["release_claim_alignment_contract_status"],
            "unibot-notebook-checkpoint-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(checkpoint["evidence"]["ready_public_safety_status"], "pass")
        self.assertEqual(checkpoint["evidence"]["stored_public_safety_status"], "pass")
        self.assertEqual(checkpoint["evidence"]["repeat_public_safety_status"], "pass")
        self.assertEqual(checkpoint["evidence"]["ready_checkpoint_status"], "notebook_checkpoint_ready")
        self.assertEqual(checkpoint["evidence"]["stored_checkpoint_status"], "notebook_checkpoint_ready")
        self.assertEqual(checkpoint["evidence"]["repeat_checkpoint_status"], "notebook_checkpoint_repeat_task_required")
        self.assertEqual(checkpoint["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertEqual(checkpoint["evidence"]["study_receipt_status"], "ok_study_session_receipt")
        self.assertTrue(checkpoint["evidence"]["checkpoint_hash_present"])
        self.assertEqual(checkpoint["evidence"]["checkpoint_journal_status"], "stored")
        self.assertTrue(checkpoint["evidence"]["checkpoint_journal_written"])
        self.assertEqual(checkpoint["evidence"]["repeat_receipt_status"], "repeat_task_required")
        self.assertTrue(checkpoint["evidence"]["repeat_task_required"])
        self.assertTrue(checkpoint["evidence"]["study_session_claim_linked"])
        self.assertTrue(checkpoint["evidence"]["private_tutor_use_flow_claim_linked"])
        self.assertTrue(checkpoint["evidence"]["evaluation_claim_linked"])
        self.assertTrue(checkpoint["evidence"]["review_board_claim_linked"])
        self.assertTrue(checkpoint["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(checkpoint["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(checkpoint["evidence"]["human_submission_gate_linked"])
        self.assertTrue(checkpoint["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(checkpoint["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(checkpoint["evidence"]["hash_only_checkpoint_ready"])
        self.assertTrue(checkpoint["evidence"]["operator_confirmed_journal_hash_only"])
        self.assertTrue(checkpoint["evidence"]["a6_or_final_solution_forces_repeat"])
        self.assertEqual(checkpoint["evidence"]["workspace_card_checkpoint_receipt_alignment_status"], "ready")
        self.assertEqual(
            checkpoint["evidence"]["workspace_card_checkpoint_receipt_alignment_public_safety_status"], "pass"
        )
        self.assertEqual(
            checkpoint["evidence"]["workspace_card_checkpoint_receipt_alignment_contract_status"],
            "unibot-notebook-checkpoint-workspace-card-checkpoint-receipt-alignment-v1",
        )
        self.assertTrue(checkpoint["evidence"]["checkpoint_report_hash_present"])
        self.assertTrue(checkpoint["evidence"]["checkpoint_receipt_hash_present"])
        self.assertTrue(checkpoint["evidence"]["stored_checkpoint_receipt_hash_present"])
        self.assertTrue(checkpoint["evidence"]["workspace_card_checkpoint_receipt_gate_linked"])
        self.assertTrue(checkpoint["evidence"]["workspace_card_checkpoint_receipt_gate_linked_contract"])
        self.assertTrue(checkpoint["evidence"]["checkpoint_receipt_study_session_reference_preserved"])
        self.assertTrue(checkpoint["evidence"]["checkpoint_receipt_operator_journal_boundary_preserved"])
        self.assertTrue(checkpoint["evidence"]["checkpoint_receipt_local_write_boundary_not_exam_clearance"])
        self.assertTrue(checkpoint["evidence"]["checkpoint_receipt_hashes_present_contract"])
        self.assertTrue(checkpoint["evidence"]["public_outputs_hide_private_notebook_data"])
        self.assertTrue(checkpoint["evidence"]["high_stakes_actions_not_started"])
        self.assertTrue(checkpoint["evidence"]["raw_notebook_code_returned_blocked"])
        self.assertTrue(checkpoint["evidence"]["raw_cell_text_returned_blocked"])
        self.assertTrue(checkpoint["evidence"]["unconfirmed_checkpoint_journal_write_blocked"])
        self.assertTrue(checkpoint["evidence"]["final_solution_acceptance_blocked"])
        self.assertTrue(checkpoint["evidence"]["eigenleistung_percentage_claim_blocked"])
        self.assertTrue(checkpoint["evidence"]["automatic_grading_blocked"])
        self.assertTrue(checkpoint["evidence"]["proctoring_blocked"])
        self.assertTrue(checkpoint["evidence"]["ki_detection_evidence_blocked"])
        self.assertTrue(checkpoint["evidence"]["cloud_processing_blocked"])
        self.assertTrue(checkpoint["evidence"]["exam_deployment_blocked"])
        launch = next(check for check in report["checks"] if check["check_id"] == "exam_workspace_launch")
        self.assertEqual(launch["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(launch["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            launch["evidence"]["release_claim_alignment_contract_status"],
            "unibot-exam-workspace-launch-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(launch["evidence"]["launch_status"], "exam_workspace_launch_dry_run_ready")
        self.assertEqual(launch["evidence"]["launch_public_safety_status"], "pass")
        self.assertEqual(launch["evidence"]["blocked_public_safety_status"], "pass")
        self.assertEqual(
            launch["evidence"]["blocked_launch_status"],
            "exam_workspace_launch_notebook_checkpoint_repeat_task_required",
        )
        self.assertEqual(launch["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertEqual(launch["evidence"]["checkpoint_status"], "notebook_checkpoint_ready")
        self.assertTrue(launch["evidence"]["checkpoint_hash_present"])
        self.assertEqual(launch["evidence"]["study_receipt_status"], "ok_study_session_receipt")
        self.assertEqual(launch["evidence"]["tutor_status"], "allowed")
        self.assertEqual(launch["evidence"]["help_ledger_preview_status"], "preview_ready")
        self.assertFalse(launch["evidence"]["general_help_ledger_written"])
        self.assertFalse(launch["evidence"]["exam_ledger_written"])
        self.assertEqual(launch["evidence"]["workspace_card_launch_receipt_alignment_status"], "ready")
        self.assertEqual(launch["evidence"]["workspace_card_launch_receipt_alignment_public_safety_status"], "pass")
        self.assertEqual(
            launch["evidence"]["workspace_card_launch_receipt_alignment_contract_status"],
            "unibot-exam-workspace-launch-workspace-card-launch-receipt-alignment-v1",
        )
        self.assertTrue(launch["evidence"]["launch_hash_present"])
        self.assertTrue(launch["evidence"]["launch_receipt_hash_present"])
        self.assertTrue(launch["evidence"]["blocked_launch_receipt_hash_present"])
        self.assertTrue(launch["evidence"]["workspace_card_launch_receipt_gate_linked"])
        self.assertTrue(launch["evidence"]["workspace_card_launch_receipt_gate_linked_contract"])
        self.assertTrue(launch["evidence"]["launch_ready_with_receipt"])
        self.assertTrue(launch["evidence"]["launch_coverage_start_point_preserved"])
        self.assertTrue(launch["evidence"]["launch_private_tutor_study_checkpoint_references_preserved"])
        self.assertTrue(launch["evidence"]["launch_receipt_hashes_present_contract"])
        self.assertTrue(launch["evidence"]["launch_operator_reviewed_boundary_preserved"])
        self.assertTrue(launch["evidence"]["repeat_task_required"])
        self.assertTrue(launch["evidence"]["notebook_checkpoint_claim_linked"])
        self.assertTrue(launch["evidence"]["study_session_claim_linked"])
        self.assertTrue(launch["evidence"]["private_tutor_use_flow_claim_linked"])
        self.assertTrue(launch["evidence"]["evaluation_claim_linked"])
        self.assertTrue(launch["evidence"]["review_board_claim_linked"])
        self.assertTrue(launch["evidence"]["external_decision_state_claim_linked"])
        self.assertTrue(launch["evidence"]["exam_boundary_claim_linked"])
        self.assertTrue(launch["evidence"]["human_submission_gate_linked"])
        self.assertTrue(launch["evidence"]["datenschutz_gate_linked"])
        self.assertTrue(launch["evidence"]["written_clearance_gate_linked"])
        self.assertTrue(launch["evidence"]["launch_public_safe"])
        self.assertTrue(launch["evidence"]["blocked_launch_public_safe"])
        self.assertTrue(launch["evidence"]["notebook_checkpoint_linked_hash_only"])
        self.assertTrue(launch["evidence"]["private_tutor_use_and_study_receipt_linked"])
        self.assertTrue(launch["evidence"]["dry_run_operator_boundaries_hold"])
        self.assertTrue(launch["evidence"]["blocked_checkpoint_stops_launch"])
        self.assertTrue(launch["evidence"]["public_outputs_hide_private_data"])
        self.assertTrue(launch["evidence"]["high_stakes_actions_not_started"])
        self.assertTrue(launch["evidence"]["raw_notebook_code_returned_blocked"])
        self.assertTrue(launch["evidence"]["raw_cell_text_returned_blocked"])
        self.assertTrue(launch["evidence"]["final_solution_acceptance_blocked"])
        self.assertTrue(launch["evidence"]["eigenleistung_percentage_claim_blocked"])
        self.assertTrue(launch["evidence"]["automatic_grading_blocked"])
        self.assertTrue(launch["evidence"]["proctoring_blocked"])
        self.assertTrue(launch["evidence"]["ki_detection_evidence_blocked"])
        self.assertTrue(launch["evidence"]["cloud_processing_blocked"])
        self.assertTrue(launch["evidence"]["exam_deployment_blocked"])
        self.assertTrue(launch["evidence"]["exam_clearance_blocked"])
        run = next(check for check in report["checks"] if check["check_id"] == "exam_workspace_run")
        self.assertEqual(run["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(run["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            run["evidence"]["release_claim_alignment_contract_status"],
            "unibot-exam-workspace-run-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(run["evidence"]["run_status"], "exam_workspace_ready_with_exam_ledger")
        self.assertEqual(run["evidence"]["run_public_safety_status"], "pass")
        self.assertEqual(run["evidence"]["waiting_public_safety_status"], "pass")
        self.assertEqual(run["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertEqual(run["evidence"]["workspace_card_run_receipt_alignment_status"], "ready")
        self.assertEqual(run["evidence"]["workspace_card_run_receipt_alignment_public_safety_status"], "pass")
        self.assertEqual(
            run["evidence"]["workspace_card_run_receipt_alignment_contract_status"],
            "unibot-exam-workspace-run-workspace-card-run-receipt-alignment-v1",
        )
        self.assertTrue(run["evidence"]["run_hash_present"])
        self.assertTrue(run["evidence"]["run_receipt_hash_present"])
        self.assertTrue(run["evidence"]["waiting_run_receipt_hash_present"])
        self.assertTrue(run["evidence"]["workspace_card_run_receipt_gate_linked"])
        self.assertTrue(run["evidence"]["workspace_card_run_receipt_gate_linked_contract"])
        self.assertTrue(run["evidence"]["run_ready_with_receipts"])
        self.assertTrue(run["evidence"]["run_private_tutor_study_ledger_references_preserved"])
        self.assertTrue(run["evidence"]["run_notebook_checkpoint_hash_only_preserved"])
        self.assertTrue(run["evidence"]["run_receipt_hashes_present_contract"])
        self.assertTrue(run["evidence"]["run_operator_confirmed_local_write_boundary_preserved"])
        self.assertTrue(run["evidence"]["run_waiting_mode_no_write_boundary_preserved"])
        self.assertTrue(run["evidence"]["export_not_cleared_receipt"])
        self.assertTrue(run["evidence"]["human_reviewable_independence_evidence"])
        self.assertTrue(run["evidence"]["workspace_card_readiness_gate_linked"])
        history = next(check for check in report["checks"] if check["check_id"] == "exam_workspace_run_history")
        self.assertEqual(history["evidence"]["release_claim_alignment_status"], "ready")
        self.assertEqual(history["evidence"]["release_claim_alignment_public_safety_status"], "pass")
        self.assertEqual(
            history["evidence"]["release_claim_alignment_contract_status"],
            "unibot-exam-workspace-run-history-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(history["evidence"]["history_status"], "exam_workspace_run_history_export_review_ready")
        self.assertEqual(history["evidence"]["history_public_safety_status"], "pass")
        self.assertEqual(history["evidence"]["waiting_public_safety_status"], "pass")
        self.assertEqual(history["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertEqual(history["evidence"]["workspace_card_history_receipt_alignment_status"], "ready")
        self.assertEqual(history["evidence"]["workspace_card_history_receipt_alignment_public_safety_status"], "pass")
        self.assertEqual(
            history["evidence"]["workspace_card_history_receipt_alignment_contract_status"],
            "unibot-exam-workspace-run-history-workspace-card-history-receipt-alignment-v1",
        )
        self.assertTrue(history["evidence"]["history_hash_present"])
        self.assertTrue(history["evidence"]["history_receipt_hash_present"])
        self.assertTrue(history["evidence"]["waiting_history_receipt_hash_present"])
        self.assertTrue(history["evidence"]["workspace_card_history_receipt_gate_linked"])
        self.assertTrue(history["evidence"]["workspace_card_history_receipt_gate_linked_contract"])
        self.assertTrue(history["evidence"]["history_export_review_ready"])
        self.assertTrue(history["evidence"]["session_console_receipts_preserved"])
        self.assertTrue(history["evidence"]["checkpoint_hashes_and_help_profile_preserved"])
        self.assertTrue(history["evidence"]["reflection_review_status_preserved"])
        self.assertTrue(history["evidence"]["export_receipt_reference_preserved"])
        self.assertTrue(history["evidence"]["operator_confirmation_boundary_preserved"])
        self.assertTrue(history["evidence"]["history_receipt_hashes_present_contract"])
        self.assertTrue(history["evidence"]["history_waiting_mode_no_reviewable_export"])
        self.assertTrue(history["evidence"]["workspace_card_readiness_gate_linked"])
        notebook = next(check for check in report["checks"] if check["check_id"] == "notebook_template")
        self.assertEqual(
            notebook["evidence"]["manual_publication_claim_contract_status"],
            "unibot-notebook-handoff-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(notebook["evidence"]["handoff_claim_alignment_status"], "ready")
        self.assertEqual(notebook["evidence"]["handoff_claim_alignment_public_safety_status"], "pass")
        self.assertTrue(notebook["evidence"]["practice_only"])
        self.assertTrue(notebook["evidence"]["local_only"])
        self.assertTrue(notebook["evidence"]["public_summary_only"])
        self.assertTrue(notebook["evidence"]["browser_handoff_claim_linked"])
        self.assertTrue(notebook["evidence"]["browser_manifest_boundary_linked"])
        self.assertTrue(notebook["evidence"]["local_demo_claim_linked"])
        self.assertTrue(notebook["evidence"]["demo_feedback_claim_linked"])
        self.assertTrue(notebook["evidence"]["publication_claim_linked"])
        self.assertTrue(notebook["evidence"]["review_board_claim_linked"])
        self.assertTrue(notebook["evidence"]["human_submission_gate_linked"])
        self.assertTrue(notebook["evidence"]["exam_clearance_blocked"])
        review_board = next(check for check in report["checks"] if check["check_id"] == "review_board_packet")
        self.assertEqual(review_board["evidence"]["evidence_alignment_status"], "ready")
        self.assertGreaterEqual(review_board["evidence"]["readiness_snapshot_gate_count"], 10)
        github_bundle = next(check for check in report["checks"] if check["check_id"] == "github_issue_bundle")
        self.assertEqual(github_bundle["evidence"]["evidence_traceability_status"], "ready")
        self.assertTrue(github_bundle["evidence"]["manual_publish_only"])
        release_runbook = next(check for check in report["checks"] if check["check_id"] == "release_runbook")
        self.assertEqual(release_runbook["evidence"]["release_evidence_alignment_status"], "ready")
        self.assertEqual(release_runbook["evidence"]["review_board_thesis_evaluation_claim_contract_status"], "ready")
        command_center = next(check for check in report["checks"] if check["check_id"] == "orchestration_command_center")
        self.assertEqual(command_center["evidence"]["workspace_card_route_alignment_status"], "ready")
        self.assertEqual(command_center["evidence"]["workspace_card_route_alignment_public_safety_status"], "pass")
        self.assertGreaterEqual(command_center["evidence"]["active_harness_count"], 3)
        self.assertGreaterEqual(command_center["evidence"]["active_route_count"], 1)
        self.assertTrue(command_center["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(command_center["evidence"]["workspace_card_command_center_gate_linked"])
        self.assertTrue(command_center["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(command_center["evidence"]["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(command_center["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(command_center["evidence"]["raw_workspace_card_returned"])
        browser_handoff = next(check for check in report["checks"] if check["check_id"] == "browser_extension_demo_handoff")
        self.assertEqual(browser_handoff["evidence"]["contract_status"], "unibot-browser-extension-release-review-board-claim-alignment-v1")
        self.assertTrue(browser_handoff["evidence"]["local_demo_claim_linked"])
        self.assertTrue(browser_handoff["evidence"]["demo_feedback_claim_linked"])
        self.assertTrue(browser_handoff["evidence"]["human_submission_gate_linked"])
        self.assertTrue(browser_handoff["evidence"]["exam_clearance_blocked"])
        self.assertIn("written_university_clearance_required_before_exam_use", release_runbook["evidence"]["release_alignment_human_gates"])
        browser_boundary = next(check for check in report["checks"] if check["check_id"] == "browser_manifest_content_boundary")
        self.assertEqual(browser_boundary["evidence"]["contract_status"], "unibot-browser-manifest-content-boundary-claim-alignment-v1")
        self.assertEqual(browser_boundary["evidence"]["permission_count"], 3)
        self.assertFalse(browser_boundary["evidence"]["all_urls_requested"])
        self.assertTrue(browser_boundary["evidence"]["sidepanel_claim_linked"])
        self.assertTrue(browser_boundary["evidence"]["human_submission_gate_linked"])
        self.assertTrue(browser_boundary["evidence"]["exam_security_claim_blocked"])
        compliance = next(check for check in report["checks"] if check["check_id"] == "compliance_matrix")
        self.assertEqual(compliance["evidence"]["compliance_drift_alignment_status"], "ready")
        self.assertIn("written_university_clearance_required_before_exam_use", compliance["evidence"]["compliance_alignment_human_gates"])
        pilot = next(check for check in report["checks"] if check["check_id"] == "pilot_protocol")
        self.assertEqual(pilot["evidence"]["pilot_evidence_alignment_status"], "ready")
        self.assertIn("datenschutz_review_required_before_real_pilot", pilot["evidence"]["pilot_alignment_human_gates"])
        data_protection = next(check for check in report["checks"] if check["check_id"] == "data_protection_screening")
        self.assertEqual(data_protection["evidence"]["data_protection_evidence_alignment_status"], "ready")
        self.assertIn(
            "datenschutz_review_required_before_real_pilot",
            data_protection["evidence"]["data_protection_alignment_human_gates"],
        )
        source_cards = next(check for check in report["checks"] if check["check_id"] == "source_cards")
        self.assertEqual(
            source_cards["evidence"]["manual_publication_claim_contract_status"],
            "unibot-source-card-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(source_cards["evidence"]["claim_alignment_status"], "ready")
        self.assertEqual(source_cards["evidence"]["claim_alignment_public_safety_status"], "pass")
        self.assertTrue(source_cards["evidence"]["public_link_only"])
        self.assertTrue(source_cards["evidence"]["all_cards_have_product_rules"])
        source_drift = next(check for check in report["checks"] if check["check_id"] == "source_card_drift_guard")
        self.assertEqual(source_drift["evidence"]["source_card_claim_alignment_status"], "ready")
        self.assertTrue(source_drift["evidence"]["redteam_claim_linked"])
        self.assertTrue(source_drift["evidence"]["notebook_handoff_claim_linked"])
        self.assertTrue(source_drift["evidence"]["publication_claim_linked"])
        self.assertTrue(source_drift["evidence"]["review_board_claim_linked"])
        self.assertTrue(source_drift["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(source_drift["evidence"]["workspace_card_source_gate_linked"])
        self.assertFalse(source_drift["evidence"]["raw_workspace_card_returned"])
        self.assertTrue(source_drift["evidence"]["human_submission_gate_linked"])
        self.assertTrue(source_drift["evidence"]["exam_clearance_blocked"])
        course_material = next(check for check in report["checks"] if check["check_id"] == "course_material_policy")
        self.assertEqual(course_material["evidence"]["material_public_boundary_alignment_status"], "ready")
        self.assertIn(
            "human_submission_review_required",
            course_material["evidence"]["material_public_boundary_alignment_human_gates"],
        )
        adaptive = next(check for check in report["checks"] if check["check_id"] == "adaptive_task_plan")
        self.assertEqual(adaptive["evidence"]["source_boundary_alignment_status"], "ready")
        self.assertIn(
            "human_submission_review_required",
            adaptive["evidence"]["source_boundary_alignment_human_gates"],
        )
        glm = next(check for check in report["checks"] if check["check_id"] == "gretel_glm_evolve_lane")
        self.assertEqual(glm["evidence"]["provider_redaction_alignment_status"], "ready")
        self.assertIn(
            "provider_call_requires_explicit_go_and_redaction_receipt",
            glm["evidence"]["provider_redaction_alignment_human_gates"],
        )
        self.assertTrue(glm["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(glm["evidence"]["workspace_card_glm_gate_linked"])
        self.assertFalse(glm["evidence"]["raw_workspace_card_returned"])
        autonomous_loop = next(check for check in report["checks"] if check["check_id"] == "gretel_autonomous_research_loop")
        previous_closed_work_id = (
            "autonomous_queue_docs_traceability_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_gate"
        )
        current_candidate_work_id = (
            "autonomous_queue_docs_traceability_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_gate"
        )
        current_candidate_review_gate = (
            "autonomous_queue_docs_traceability_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness"
        )
        self.assertEqual(
            autonomous_loop["evidence"]["candidate_receipt_work_id"],
            current_candidate_work_id,
        )
        self.assertEqual(autonomous_loop["evidence"]["candidate_work_items"], 1)
        self.assertEqual(autonomous_loop["evidence"]["ready_work_items"], 0)
        self.assertTrue(autonomous_loop["evidence"]["candidate_receipt_hash_present"])
        self.assertEqual(autonomous_loop["evidence"]["candidate_review_status"], "candidate_review_ready")
        self.assertEqual(autonomous_loop["evidence"]["candidate_review_public_safety_status"], "pass")
        self.assertEqual(autonomous_loop["evidence"]["candidate_review_surface"], "autonomous_queue_candidate_review")
        self.assertTrue(autonomous_loop["evidence"]["candidate_review_hash_present"])
        self.assertEqual(autonomous_loop["evidence"]["candidate_review_receipt_status"], "candidate_review_ready")
        self.assertTrue(autonomous_loop["evidence"]["candidate_review_receipt_hash_present"])
        self.assertTrue(autonomous_loop["evidence"]["candidate_review_receipt_hash_matches_review"])
        self.assertFalse(autonomous_loop["evidence"]["candidate_review_auto_promotion_allowed"])
        self.assertEqual(
            autonomous_loop["evidence"]["candidate_review_promotion_recommendation"],
            "keep_candidate_not_runnable",
        )
        self.assertEqual(autonomous_loop["evidence"]["candidate_rotation_status"], "candidate_rotation_receipt_ready")
        self.assertEqual(autonomous_loop["evidence"]["candidate_rotation_public_safety_status"], "pass")
        self.assertEqual(
            autonomous_loop["evidence"]["candidate_rotation_previous_closed_work_id"],
            previous_closed_work_id,
        )
        self.assertEqual(autonomous_loop["evidence"]["candidate_rotation_previous_closed_commit"], "22ee3a3")
        self.assertEqual(
            autonomous_loop["evidence"]["candidate_rotation_selected_work_id"],
            current_candidate_work_id,
        )
        self.assertTrue(autonomous_loop["evidence"]["candidate_rotation_hash_present"])
        self.assertEqual(
            autonomous_loop["evidence"]["candidate_rotation_receipt_status"],
            "candidate_rotation_receipt_ready",
        )
        self.assertTrue(autonomous_loop["evidence"]["candidate_rotation_receipt_hash_matches_rotation"])
        self.assertFalse(autonomous_loop["evidence"]["candidate_rotation_auto_promotion_allowed"])
        self.assertEqual(
            autonomous_loop["evidence"]["single_candidate_continuity_status"],
            "single_candidate_continuity_ready",
        )
        self.assertEqual(
            autonomous_loop["evidence"]["single_candidate_continuity_public_safety_status"],
            "pass",
        )
        self.assertEqual(
            autonomous_loop["evidence"]["single_candidate_continuity_selected_work_id"],
            current_candidate_work_id,
        )
        self.assertEqual(autonomous_loop["evidence"]["single_candidate_continuity_selected_status"], "candidate")
        self.assertEqual(
            autonomous_loop["evidence"]["single_candidate_continuity_review_gate"],
            current_candidate_review_gate,
        )
        self.assertTrue(autonomous_loop["evidence"]["single_candidate_continuity_review_gate_matches_candidate_receipt"])
        self.assertEqual(autonomous_loop["evidence"]["single_candidate_continuity_ready_work_items"], 0)
        self.assertEqual(autonomous_loop["evidence"]["single_candidate_continuity_candidate_work_items"], 1)
        self.assertTrue(autonomous_loop["evidence"]["single_candidate_continuity_hash_present"])
        self.assertEqual(
            autonomous_loop["evidence"]["single_candidate_continuity_receipt_status"],
            "single_candidate_continuity_ready",
        )
        self.assertTrue(autonomous_loop["evidence"]["single_candidate_continuity_receipt_hash_matches_continuity"])
        self.assertFalse(autonomous_loop["evidence"]["single_candidate_continuity_auto_promotion_allowed"])
        self.assertEqual(autonomous_loop["evidence"]["queue_integrity_status"], "queue_integrity_ready")
        self.assertEqual(autonomous_loop["evidence"]["queue_integrity_public_safety_status"], "pass")
        self.assertGreaterEqual(autonomous_loop["evidence"]["queue_integrity_queue_count"], 156)
        self.assertEqual(
            autonomous_loop["evidence"]["queue_integrity_highest_priority_work_id"],
            current_candidate_work_id,
        )
        self.assertEqual(
            autonomous_loop["evidence"]["queue_integrity_selected_work_id"],
            current_candidate_work_id,
        )
        self.assertEqual(autonomous_loop["evidence"]["queue_integrity_missing_priorities"], [])
        self.assertEqual(autonomous_loop["evidence"]["queue_integrity_duplicate_priorities"], [])
        self.assertEqual(autonomous_loop["evidence"]["queue_integrity_missing_closure_commit_work_ids"], [])
        self.assertEqual(autonomous_loop["evidence"]["queue_integrity_duplicate_closure_commits"], [])
        self.assertEqual(autonomous_loop["evidence"]["queue_integrity_failed_contract_ids"], [])
        self.assertTrue(autonomous_loop["evidence"]["queue_integrity_hash_present"])
        self.assertEqual(autonomous_loop["evidence"]["queue_integrity_receipt_status"], "queue_integrity_ready")
        self.assertTrue(autonomous_loop["evidence"]["queue_integrity_receipt_hash_matches_report"])
        self.assertEqual(autonomous_loop["evidence"]["docs_traceability_status"], "ready")
        self.assertEqual(autonomous_loop["evidence"]["docs_traceability_public_safety_status"], "pass")
        self.assertTrue(autonomous_loop["evidence"]["docs_traceability_current_candidate_documented"])
        self.assertTrue(autonomous_loop["evidence"]["docs_traceability_previous_closure_documented"])
        self.assertTrue(autonomous_loop["evidence"]["docs_traceability_readiness_gate_match_rule_documented"])
        self.assertTrue(autonomous_loop["evidence"]["docs_traceability_promotion_blocker_documented"])
        self.assertEqual(autonomous_loop["evidence"]["docs_traceability_failed_contract_ids"], [])
        self.assertEqual(
            autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_status"],
            "docs_traceability_negative_evidence_receipt_ready",
        )
        self.assertEqual(
            autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_public_safety_status"],
            "pass",
        )
        self.assertTrue(autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_hash_present"])
        self.assertTrue(
            autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_hash_matches_loop_receipt"]
        )
        self.assertEqual(
            autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_negative_harness_commit"],
            "1f7b05d",
        )
        self.assertEqual(
            autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_negative_evidence_commit"],
            "b0d9d42",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_receipt_commit"
            ],
            "c2fca9a",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_commit"
            ],
            "e84d853",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_commit"
            ],
            "f5bb021",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_commit"
            ],
            "fd5dd4f",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_commit"
            ],
            "57d649c",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_commit"
            ],
            "60ba49e",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_commit"
            ],
            "883b80e",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "468358c",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "35d7de0",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "536a5ae",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "06d9c48",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "3a15aad",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "ef199b2",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "f31c122",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "0d98bc5",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "a95536a",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "ba2684d",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "f01d737",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "2e60207",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "d36dbfd",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "f966650",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "8fab4a0",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "00fb3d9",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "48b5144",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "52f4ec8",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "180d5c5",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "49ef7d9",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "2105ec7",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "6677b7a",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "754a13b",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "a40892b",
        )
        self.assertEqual(
            autonomous_loop["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "22ee3a3",
        )
        self.assertEqual(
            autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_selected_work_id"],
            current_candidate_work_id,
        )
        self.assertEqual(
            autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_review_gate"],
            current_candidate_review_gate,
        )
        self.assertEqual(
            autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_failed_contract_ids"],
            [],
        )
        self.assertFalse(autonomous_loop["evidence"]["docs_traceability_negative_evidence_receipt_auto_promotion_allowed"])
        loop_payload = build_autonomous_research_loop()
        self.assertEqual(
            loop_payload["docs_traceability_negative_evidence_receipt"]["failed_contract_ids"],
            [],
        )
        self.assertEqual(autonomous_loop["evidence"]["workspace_card_budget_alignment_status"], "ready")
        self.assertEqual(autonomous_loop["evidence"]["workspace_card_budget_alignment_public_safety_status"], "pass")
        self.assertTrue(autonomous_loop["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(autonomous_loop["evidence"]["workspace_card_autonomous_loop_gate_linked"])
        self.assertTrue(autonomous_loop["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(autonomous_loop["evidence"]["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(autonomous_loop["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(autonomous_loop["evidence"]["raw_workspace_card_returned"])
        review_chain = next(check for check in report["checks"] if check["check_id"] == "review_chain_integrity")
        self.assertEqual(review_chain["evidence"]["workspace_card_chain_alignment_status"], "ready")
        self.assertEqual(review_chain["evidence"]["workspace_card_chain_alignment_public_safety_status"], "pass")
        self.assertEqual(review_chain["evidence"]["issue_count"], 0)
        self.assertEqual(review_chain["evidence"]["checked_link_count"], 4)
        self.assertTrue(review_chain["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(review_chain["evidence"]["workspace_card_review_chain_gate_linked"])
        self.assertTrue(review_chain["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(review_chain["evidence"]["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(review_chain["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(review_chain["evidence"]["raw_workspace_card_returned"])
        timeline_receipt_journal = next(
            check for check in report["checks"] if check["check_id"] == "timeline_export_receipt_journal"
        )
        self.assertEqual(
            timeline_receipt_journal["evidence"]["workspace_card_journal_alignment_status"],
            "ready",
        )
        self.assertEqual(
            timeline_receipt_journal["evidence"]["workspace_card_journal_alignment_public_safety_status"],
            "pass",
        )
        self.assertEqual(timeline_receipt_journal["evidence"]["append_status"], "write_preview_ready")
        self.assertFalse(timeline_receipt_journal["evidence"]["journal_written"])
        self.assertEqual(timeline_receipt_journal["evidence"]["accepted_record_count"], 1)
        self.assertEqual(timeline_receipt_journal["evidence"]["blocked_record_count"], 0)
        self.assertEqual(timeline_receipt_journal["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertTrue(timeline_receipt_journal["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(timeline_receipt_journal["evidence"]["workspace_card_timeline_receipt_journal_gate_linked"])
        self.assertTrue(timeline_receipt_journal["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(
            timeline_receipt_journal["evidence"]["workspace_card_help_ledger_status"],
            "help_ledger_preview_ready",
        )
        self.assertTrue(timeline_receipt_journal["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(timeline_receipt_journal["evidence"]["raw_workspace_card_returned"])
        timeline_review_packet = next(
            check for check in report["checks"] if check["check_id"] == "timeline_export_review_packet"
        )
        self.assertEqual(timeline_review_packet["evidence"]["workspace_card_review_alignment_status"], "ready")
        self.assertEqual(
            timeline_review_packet["evidence"]["workspace_card_review_alignment_public_safety_status"],
            "pass",
        )
        self.assertEqual(
            timeline_review_packet["evidence"]["review_packet_status"],
            "timeline_export_review_packet_ready",
        )
        self.assertEqual(
            timeline_review_packet["evidence"]["receipt_status"],
            "timeline_export_review_packet_receipt_ready_not_exam_clearance",
        )
        self.assertFalse(timeline_review_packet["evidence"]["local_write_started"])
        self.assertGreaterEqual(timeline_review_packet["evidence"]["event_count"], 1)
        self.assertGreaterEqual(timeline_review_packet["evidence"]["reviewer_question_count"], 1)
        self.assertEqual(timeline_review_packet["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertTrue(timeline_review_packet["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(timeline_review_packet["evidence"]["workspace_card_timeline_review_packet_gate_linked"])
        self.assertTrue(timeline_review_packet["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(
            timeline_review_packet["evidence"]["workspace_card_help_ledger_status"],
            "help_ledger_preview_ready",
        )
        self.assertTrue(timeline_review_packet["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(timeline_review_packet["evidence"]["raw_workspace_card_returned"])
        material_coverage_run = next(
            check for check in report["checks"] if check["check_id"] == "material_coverage_run"
        )
        self.assertEqual(
            material_coverage_run["evidence"]["workspace_card_coverage_alignment_status"],
            "ready",
        )
        self.assertEqual(
            material_coverage_run["evidence"]["workspace_card_coverage_alignment_public_safety_status"],
            "pass",
        )
        self.assertIn(
            material_coverage_run["evidence"]["coverage_status"],
            {
                "course_material_coverage_needs_materials",
                "course_material_coverage_needs_private_manifest_apply",
                "course_material_coverage_needs_tutor_index_build",
                "course_material_coverage_ready_for_exam_workspace",
                "course_material_coverage_needs_extraction_or_transcription",
                "course_material_coverage_needs_anchor_review",
            },
        )
        self.assertEqual(
            material_coverage_run["evidence"]["receipt_status"],
            "material_coverage_receipt_ready_not_exam_clearance",
        )
        self.assertGreaterEqual(material_coverage_run["evidence"]["skill_count"], 1)
        self.assertGreaterEqual(material_coverage_run["evidence"]["visible_skill_count"], 1)
        self.assertGreaterEqual(material_coverage_run["evidence"]["source_anchor_count"], 0)
        self.assertGreaterEqual(material_coverage_run["evidence"]["notebook_anchor_count"], 0)
        self.assertGreaterEqual(material_coverage_run["evidence"]["ocr_gap_count"], 0)
        self.assertGreaterEqual(material_coverage_run["evidence"]["video_gap_count"], 0)
        self.assertEqual(material_coverage_run["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertTrue(material_coverage_run["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(material_coverage_run["evidence"]["workspace_card_material_coverage_gate_linked"])
        self.assertTrue(material_coverage_run["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(
            material_coverage_run["evidence"]["workspace_card_help_ledger_status"],
            "help_ledger_preview_ready",
        )
        self.assertTrue(material_coverage_run["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(material_coverage_run["evidence"]["raw_workspace_card_returned"])
        course_exam_coverage_dashboard = next(
            check for check in report["checks"] if check["check_id"] == "course_exam_coverage_dashboard"
        )
        self.assertEqual(
            course_exam_coverage_dashboard["evidence"]["workspace_card_dashboard_alignment_status"],
            "ready",
        )
        self.assertEqual(
            course_exam_coverage_dashboard["evidence"]["workspace_card_dashboard_alignment_public_safety_status"],
            "pass",
        )
        self.assertEqual(
            course_exam_coverage_dashboard["evidence"]["dashboard_status"],
            "course_exam_coverage_dashboard_ready",
        )
        self.assertEqual(
            course_exam_coverage_dashboard["evidence"]["receipt_status"],
            "dashboard_receipt_ready_not_exam_clearance",
        )
        self.assertGreaterEqual(course_exam_coverage_dashboard["evidence"]["skill_count"], 1)
        self.assertGreaterEqual(course_exam_coverage_dashboard["evidence"]["visible_skill_count"], 1)
        self.assertGreaterEqual(course_exam_coverage_dashboard["evidence"]["workspace_ready_skill_count"], 0)
        self.assertGreaterEqual(course_exam_coverage_dashboard["evidence"]["checkpoint_hash_count"], 0)
        self.assertGreaterEqual(course_exam_coverage_dashboard["evidence"]["open_operator_confirmation_count"], 0)
        self.assertEqual(course_exam_coverage_dashboard["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertTrue(course_exam_coverage_dashboard["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(
            course_exam_coverage_dashboard["evidence"]["workspace_card_course_exam_dashboard_gate_linked"]
        )
        self.assertTrue(course_exam_coverage_dashboard["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(
            course_exam_coverage_dashboard["evidence"]["workspace_card_help_ledger_status"],
            "help_ledger_preview_ready",
        )
        self.assertTrue(course_exam_coverage_dashboard["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(course_exam_coverage_dashboard["evidence"]["raw_workspace_card_returned"])
        course_per_skill_action_router = next(
            check for check in report["checks"] if check["check_id"] == "course_per_skill_action_router"
        )
        self.assertEqual(
            course_per_skill_action_router["evidence"]["workspace_card_route_alignment_status"],
            "ready",
        )
        self.assertEqual(
            course_per_skill_action_router["evidence"]["workspace_card_route_alignment_public_safety_status"],
            "pass",
        )
        self.assertEqual(
            course_per_skill_action_router["evidence"]["router_status"],
            "course_per_skill_action_router_ready",
        )
        self.assertEqual(
            course_per_skill_action_router["evidence"]["receipt_status"],
            "router_receipt_ready_not_exam_clearance",
        )
        self.assertNotEqual(course_per_skill_action_router["evidence"]["route_id"], "missing")
        self.assertNotEqual(course_per_skill_action_router["evidence"]["route_endpoint"], "")
        self.assertTrue(course_per_skill_action_router["evidence"]["dry_run_by_default"])
        self.assertTrue(
            course_per_skill_action_router["evidence"]["requires_operator_confirmation_for_local_writes"]
        )
        self.assertGreaterEqual(course_per_skill_action_router["evidence"]["route_count"], 1)
        self.assertEqual(course_per_skill_action_router["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertTrue(course_per_skill_action_router["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(
            course_per_skill_action_router["evidence"]["workspace_card_course_per_skill_router_gate_linked"]
        )
        self.assertTrue(course_per_skill_action_router["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(
            course_per_skill_action_router["evidence"]["workspace_card_help_ledger_status"],
            "help_ledger_preview_ready",
        )
        self.assertTrue(course_per_skill_action_router["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(course_per_skill_action_router["evidence"]["raw_workspace_card_returned"])
        routed_action_executor = next(
            check for check in report["checks"] if check["check_id"] == "routed_action_executor"
        )
        self.assertEqual(
            routed_action_executor["evidence"]["workspace_card_execution_alignment_status"],
            "ready",
        )
        self.assertEqual(
            routed_action_executor["evidence"]["workspace_card_execution_alignment_public_safety_status"],
            "pass",
        )
        self.assertEqual(routed_action_executor["evidence"]["executor_status"], "routed_action_executor_ready")
        self.assertEqual(
            routed_action_executor["evidence"]["receipt_status"],
            "executor_receipt_ready_not_exam_clearance",
        )
        self.assertNotEqual(routed_action_executor["evidence"]["route_id"], "missing")
        self.assertNotEqual(routed_action_executor["evidence"]["executed_artifact_type"], "missing")
        self.assertNotEqual(routed_action_executor["evidence"]["executed_status"], "missing")
        self.assertTrue(routed_action_executor["evidence"]["executed_result_hash_present"])
        self.assertFalse(routed_action_executor["evidence"]["local_write_started"])
        self.assertTrue(routed_action_executor["evidence"]["dry_run_by_default"])
        self.assertTrue(routed_action_executor["evidence"]["local_write_confirmations_are_explicit"])
        self.assertEqual(routed_action_executor["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertTrue(routed_action_executor["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(routed_action_executor["evidence"]["workspace_card_routed_action_executor_gate_linked"])
        self.assertTrue(routed_action_executor["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(
            routed_action_executor["evidence"]["workspace_card_help_ledger_status"],
            "help_ledger_preview_ready",
        )
        self.assertTrue(routed_action_executor["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(routed_action_executor["evidence"]["raw_workspace_card_returned"])
        exam_run_packet = next(check for check in report["checks"] if check["check_id"] == "exam_run_packet")
        self.assertEqual(exam_run_packet["evidence"]["workspace_card_packet_alignment_status"], "ready")
        self.assertEqual(
            exam_run_packet["evidence"]["workspace_card_packet_alignment_public_safety_status"],
            "pass",
        )
        self.assertEqual(exam_run_packet["evidence"]["packet_status"], "exam_run_packet_ready")
        self.assertEqual(
            exam_run_packet["evidence"]["receipt_status"],
            "exam_run_packet_receipt_ready_not_exam_clearance",
        )
        self.assertNotEqual(exam_run_packet["evidence"]["route_id"], "missing")
        self.assertNotEqual(exam_run_packet["evidence"]["executed_artifact_type"], "missing")
        self.assertNotEqual(exam_run_packet["evidence"]["executed_status"], "missing")
        self.assertTrue(exam_run_packet["evidence"]["executed_result_hash_present"])
        self.assertFalse(exam_run_packet["evidence"]["local_write_started"])
        self.assertEqual(
            exam_run_packet["evidence"]["local_cycle_chain_snapshot_status"],
            "python_exam_local_cycle_chain_snapshot_ready",
        )
        self.assertTrue(exam_run_packet["evidence"]["local_cycle_chain_snapshot_hash_present"])
        self.assertEqual(exam_run_packet["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertTrue(exam_run_packet["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(exam_run_packet["evidence"]["workspace_card_exam_run_packet_gate_linked"])
        self.assertTrue(exam_run_packet["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(
            exam_run_packet["evidence"]["workspace_card_help_ledger_status"],
            "help_ledger_preview_ready",
        )
        self.assertTrue(exam_run_packet["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(exam_run_packet["evidence"]["raw_workspace_card_returned"])
        exam_packet_timeline = next(check for check in report["checks"] if check["check_id"] == "exam_packet_timeline")
        self.assertEqual(exam_packet_timeline["evidence"]["workspace_card_timeline_alignment_status"], "ready")
        self.assertEqual(
            exam_packet_timeline["evidence"]["workspace_card_timeline_alignment_public_safety_status"],
            "pass",
        )
        self.assertEqual(exam_packet_timeline["evidence"]["timeline_status"], "exam_packet_timeline_ready")
        self.assertEqual(
            exam_packet_timeline["evidence"]["receipt_status"],
            "exam_packet_timeline_receipt_ready_not_exam_clearance",
        )
        self.assertGreaterEqual(exam_packet_timeline["evidence"]["event_count"], 1)
        self.assertGreaterEqual(exam_packet_timeline["evidence"]["visible_event_count"], 1)
        self.assertGreaterEqual(exam_packet_timeline["evidence"]["packet_receipt_count"], 1)
        self.assertEqual(exam_packet_timeline["evidence"]["export_review_preview_status"], "timeline_export_review_ready")
        self.assertEqual(exam_packet_timeline["evidence"]["exam_deployment_status"], "not_cleared")
        self.assertTrue(exam_packet_timeline["evidence"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(exam_packet_timeline["evidence"]["workspace_card_exam_packet_timeline_gate_linked"])
        self.assertTrue(exam_packet_timeline["evidence"]["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(
            exam_packet_timeline["evidence"]["workspace_card_help_ledger_status"],
            "help_ledger_preview_ready",
        )
        self.assertTrue(exam_packet_timeline["evidence"]["workspace_card_help_ledger_hash_present"])
        self.assertFalse(exam_packet_timeline["evidence"]["raw_workspace_card_returned"])
        self.assertEqual(report["evidence_snapshot"]["status"], "ready")
        self.assertEqual(report["evidence_snapshot"]["public_safety_status"], "pass")
        self.assertEqual(report["evidence_snapshot"]["failed_check_ids"], [])
        self.assertEqual(report["evidence_snapshot"]["scientific_gate_passed_count"], report["evidence_snapshot"]["scientific_gate_count"])
        self.assertIn("gretel_bachelor_thesis_package", [gate["check_id"] for gate in report["evidence_snapshot"]["scientific_gates"]])

    def test_readiness_runtime_guard_keeps_recurring_runs_lightweight(self) -> None:
        guard = build_readiness_runtime_guard(public_file_count=123)

        self.assertEqual(guard["status"], "budget_guard_ready")
        self.assertEqual(guard["public_safety_status"], "pass")
        self.assertEqual(guard["routine_budget"]["default_reasoning_effort"], "low")
        self.assertEqual(guard["routine_budget"]["max_active_work_items_per_run"], 1)
        self.assertIs(guard["routine_budget"]["full_suite_required_by_default"], False)
        self.assertIs(guard["routine_budget"]["provider_calls_allowed_by_default"], False)
        self.assertIs(guard["routine_budget"]["external_actions_allowed_by_default"], False)
        self.assertIn("python3 -m pytest tests/test_unibot_readiness.py -q", guard["routine_commands"])
        self.assertIn("full pytest suite", guard["expensive_or_escalated_by_default"])
        self.assertEqual(guard["current_public_file_scan_count"], 123)

    def test_autonomous_loop_docs_traceability_blocks_missing_public_docs(self) -> None:
        loop = build_autonomous_research_loop()
        complete_loop_doc = "\n".join(
            [
                loop["next_recommended_work_id"],
                loop["candidate_rotation_receipt"]["previous_closed_work_id"],
                loop["candidate_rotation_receipt"]["previous_closed_commit"],
                "Candidate lanes are not runnable work; promotion requires a new closed-harnessed receipt or an explicit ready item with bounded scope and tests.",
            ]
        )
        complete_readiness_doc = "\n".join(
            [
                "review gate matching the current candidate receipt",
                "Candidate lanes are not runnable work; promotion requires a new closed-harnessed receipt or an explicit ready item with bounded scope and tests.",
            ]
        )

        ready = build_autonomous_loop_docs_traceability(loop, complete_loop_doc, complete_readiness_doc)
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(ready["public_safety_status"], "pass")
        self.assertEqual(ready["failed_contract_ids"], [])

        missing_candidate = build_autonomous_loop_docs_traceability(
            loop,
            complete_loop_doc.replace(loop["next_recommended_work_id"], ""),
            complete_readiness_doc,
        )
        self.assertEqual(missing_candidate["status"], "blocked")
        self.assertIn("current_candidate_documented", missing_candidate["failed_contract_ids"])

        missing_closure = build_autonomous_loop_docs_traceability(
            loop,
            complete_loop_doc.replace(loop["candidate_rotation_receipt"]["previous_closed_commit"], ""),
            complete_readiness_doc,
        )
        self.assertEqual(missing_closure["status"], "blocked")
        self.assertIn("previous_closure_documented", missing_closure["failed_contract_ids"])

        missing_gate_rule = build_autonomous_loop_docs_traceability(loop, complete_loop_doc, "")
        self.assertEqual(missing_gate_rule["status"], "blocked")
        self.assertIn("readiness_gate_match_rule_documented", missing_gate_rule["failed_contract_ids"])

        missing_promotion_blocker = build_autonomous_loop_docs_traceability(
            loop,
            complete_loop_doc,
            complete_readiness_doc.replace("Candidate lanes are not runnable work;", ""),
        )
        self.assertEqual(missing_promotion_blocker["status"], "blocked")
        self.assertIn("promotion_blocker_documented", missing_promotion_blocker["failed_contract_ids"])

    def test_readiness_blocks_bad_docs_traceability_negative_evidence_receipt(self) -> None:
        original_builder = readiness_module.build_autonomous_research_loop

        def run_with_loop(loop: dict[str, object]) -> dict[str, object]:
            readiness_module.build_autonomous_research_loop = lambda: loop
            try:
                return readiness_module.run_readiness_check()
            finally:
                readiness_module.build_autonomous_research_loop = original_builder

        missing_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        del missing_loop["docs_traceability_negative_evidence_receipt"]
        missing_report = run_with_loop(missing_loop)
        missing_check = next(
            check for check in missing_report["checks"] if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_check["passed"])
        self.assertEqual(missing_check["evidence"]["docs_traceability_negative_evidence_receipt_status"], "missing")
        self.assertFalse(missing_check["evidence"]["docs_traceability_negative_evidence_receipt_hash_present"])
        self.assertFalse(
            missing_check["evidence"]["docs_traceability_negative_evidence_receipt_hash_matches_loop_receipt"]
        )
        self.assertEqual(
            missing_check["evidence"]["docs_traceability_negative_evidence_receipt_failed_contract_ids"],
            ["missing_docs_traceability_negative_evidence_receipt"],
        )
        self.assertNotEqual(missing_report["status"], "public_draft_ready")

        mismatched_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        mismatched_loop["docs_traceability_negative_evidence_receipt"]["evidence_hash"] = "wrong-evidence-hash"
        mismatched_report = run_with_loop(mismatched_loop)
        mismatched_check = next(
            check for check in mismatched_report["checks"] if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(mismatched_check["passed"])
        self.assertEqual(
            mismatched_check["evidence"]["docs_traceability_negative_evidence_receipt_status"],
            "docs_traceability_negative_evidence_receipt_ready",
        )
        self.assertTrue(mismatched_check["evidence"]["docs_traceability_negative_evidence_receipt_hash_present"])
        self.assertFalse(
            mismatched_check["evidence"]["docs_traceability_negative_evidence_receipt_hash_matches_loop_receipt"]
        )
        self.assertNotEqual(mismatched_report["status"], "public_draft_ready")

        missing_tail_commit_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_commit"
        ] = ""
        missing_tail_commit_report = run_with_loop(missing_tail_commit_loop)
        missing_tail_commit_check = next(
            check
            for check in missing_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_tail_commit_check["passed"])
        self.assertEqual(
            missing_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(missing_tail_commit_report["status"], "public_draft_ready")

        missing_receipt_visibility_commit_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_receipt_visibility_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_commit_report = run_with_loop(missing_receipt_visibility_commit_loop)
        missing_receipt_visibility_commit_check = next(
            check
            for check in missing_receipt_visibility_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(missing_receipt_visibility_commit_report["status"], "public_draft_ready")

        missing_receipt_visibility_readiness_commit_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_receipt_visibility_readiness_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_commit"
        ] = ""
        missing_receipt_visibility_readiness_commit_report = run_with_loop(
            missing_receipt_visibility_readiness_commit_loop
        )
        missing_receipt_visibility_readiness_commit_check = next(
            check
            for check in missing_receipt_visibility_readiness_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_readiness_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_readiness_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_readiness_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_commit_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_receipt_visibility_receipt_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_commit_loop
        )
        missing_receipt_visibility_receipt_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_readiness_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_readiness_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_commit"
        ] = ""
        missing_receipt_visibility_receipt_readiness_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_readiness_commit_loop
        )
        missing_receipt_visibility_receipt_readiness_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_readiness_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_readiness_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_readiness_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_readiness_commit_report["status"],
            "public_draft_ready",
        )

        missing_readiness_tail_commit_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_readiness_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_readiness_tail_commit_report = run_with_loop(missing_readiness_tail_commit_loop)
        missing_readiness_tail_commit_check = next(
            check
            for check in missing_readiness_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_readiness_tail_commit_check["passed"])
        self.assertEqual(
            missing_readiness_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(missing_readiness_tail_commit_report["status"], "public_draft_ready")

        missing_queue_integrity_hash_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_queue_integrity_hash_loop["receipt"]["queue_integrity_hash"] = ""
        missing_queue_integrity_hash_report = run_with_loop(missing_queue_integrity_hash_loop)
        missing_queue_integrity_hash_check = next(
            check
            for check in missing_queue_integrity_hash_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_queue_integrity_hash_check["passed"])
        self.assertFalse(
            missing_queue_integrity_hash_check["evidence"]["queue_integrity_receipt_hash_matches_report"]
        )
        self.assertNotEqual(missing_queue_integrity_hash_report["status"], "public_draft_ready")

        missing_receipt_binding_tail_commit_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_receipt_binding_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_binding_tail_commit_report = run_with_loop(missing_receipt_binding_tail_commit_loop)
        missing_receipt_binding_tail_commit_check = next(
            check
            for check in missing_receipt_binding_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_binding_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_binding_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(missing_receipt_binding_tail_commit_report["status"], "public_draft_ready")

        missing_receipt_binding_readiness_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_binding_readiness_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
        ] = ""
        missing_receipt_binding_readiness_tail_commit_report = run_with_loop(
            missing_receipt_binding_readiness_tail_commit_loop
        )
        missing_receipt_binding_readiness_tail_commit_check = next(
            check
            for check in missing_receipt_binding_readiness_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_binding_readiness_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_binding_readiness_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_binding_readiness_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_binding_receipt_tail_commit_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_receipt_binding_receipt_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_binding_receipt_tail_commit_report = run_with_loop(
            missing_receipt_binding_receipt_tail_commit_loop
        )
        missing_receipt_binding_receipt_tail_commit_check = next(
            check
            for check in missing_receipt_binding_receipt_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_binding_receipt_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_binding_receipt_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_binding_receipt_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_current_receipt_binding_tail_commit_loop = json.loads(json.dumps(build_autonomous_research_loop()))
        missing_current_receipt_binding_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_current_receipt_binding_tail_commit_report = run_with_loop(
            missing_current_receipt_binding_tail_commit_loop
        )
        missing_current_receipt_binding_tail_commit_check = next(
            check
            for check in missing_current_receipt_binding_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_current_receipt_binding_tail_commit_check["passed"])
        self.assertEqual(
            missing_current_receipt_binding_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_current_receipt_binding_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_current_receipt_binding_readiness_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_current_receipt_binding_readiness_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
        ] = ""
        missing_current_receipt_binding_readiness_tail_commit_report = run_with_loop(
            missing_current_receipt_binding_readiness_tail_commit_loop
        )
        missing_current_receipt_binding_readiness_tail_commit_check = next(
            check
            for check in missing_current_receipt_binding_readiness_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_current_receipt_binding_readiness_tail_commit_check["passed"])
        self.assertEqual(
            missing_current_receipt_binding_readiness_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_current_receipt_binding_readiness_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_current_receipt_binding_receipt_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_current_receipt_binding_receipt_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_current_receipt_binding_receipt_tail_commit_report = run_with_loop(
            missing_current_receipt_binding_receipt_tail_commit_loop
        )
        missing_current_receipt_binding_receipt_tail_commit_check = next(
            check
            for check in missing_current_receipt_binding_receipt_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_current_receipt_binding_receipt_tail_commit_check["passed"])
        self.assertEqual(
            missing_current_receipt_binding_receipt_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_current_receipt_binding_receipt_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_receipt_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_receipt_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_receipt_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_receipt_commit_loop
        )
        missing_receipt_visibility_receipt_receipt_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_receipt_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_receipt_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_receipt_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_receipt_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_readiness_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_readiness_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
        ] = ""
        missing_receipt_visibility_receipt_readiness_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_readiness_commit_loop
        )
        missing_receipt_visibility_receipt_readiness_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_readiness_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_readiness_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_readiness_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_readiness_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_receipt_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_receipt_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_receipt_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_receipt_tail_commit_loop
        )
        missing_receipt_visibility_receipt_receipt_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_receipt_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_receipt_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_receipt_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_receipt_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_readiness_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_readiness_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
        ] = ""
        missing_receipt_visibility_receipt_readiness_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_readiness_tail_commit_loop
        )
        missing_receipt_visibility_receipt_readiness_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_readiness_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_readiness_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_readiness_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_readiness_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_receipt_final_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_receipt_final_tail_commit_loop["docs_traceability_negative_evidence_receipt"][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_receipt_final_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_receipt_final_tail_commit_loop
        )
        missing_receipt_visibility_receipt_receipt_final_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_receipt_final_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_receipt_final_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_receipt_final_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_receipt_final_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_readiness_final_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_readiness_final_tail_commit_loop[
            "docs_traceability_negative_evidence_receipt"
        ][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_readiness_final_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_readiness_final_tail_commit_loop
        )
        missing_receipt_visibility_receipt_readiness_final_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_readiness_final_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_readiness_final_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_readiness_final_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_readiness_final_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_binding_final_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_binding_final_tail_commit_loop[
            "docs_traceability_negative_evidence_receipt"
        ][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_binding_final_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_binding_final_tail_commit_loop
        )
        missing_receipt_visibility_receipt_binding_final_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_binding_final_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_binding_final_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_binding_final_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_binding_final_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_binding_readiness_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_binding_readiness_tail_commit_loop[
            "docs_traceability_negative_evidence_receipt"
        ][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_binding_readiness_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_binding_readiness_tail_commit_loop
        )
        missing_receipt_visibility_receipt_binding_readiness_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_binding_readiness_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_binding_readiness_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_binding_readiness_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_binding_readiness_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_binding_receipt_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_binding_receipt_tail_commit_loop[
            "docs_traceability_negative_evidence_receipt"
        ][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_binding_receipt_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_binding_receipt_tail_commit_loop
        )
        missing_receipt_visibility_receipt_binding_receipt_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_binding_receipt_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_binding_receipt_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_binding_receipt_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_binding_receipt_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_loop[
            "docs_traceability_negative_evidence_receipt"
        ][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_loop
        )
        missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_loop[
            "docs_traceability_negative_evidence_receipt"
        ][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_loop
        )
        missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_loop[
            "docs_traceability_negative_evidence_receipt"
        ][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
        ] = ""
        missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_loop
        )
        missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_binding_receipt_readiness_tail_commit_report["status"],
            "public_draft_ready",
        )

        missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_loop = json.loads(
            json.dumps(build_autonomous_research_loop())
        )
        missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_loop[
            "docs_traceability_negative_evidence_receipt"
        ][
            "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
        ] = ""
        missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_report = run_with_loop(
            missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_loop
        )
        missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_check = next(
            check
            for check in missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_report["checks"]
            if check["check_id"] == "gretel_autonomous_research_loop"
        )

        self.assertFalse(missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_check["passed"])
        self.assertEqual(
            missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_check["evidence"][
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit"
            ],
            "",
        )
        self.assertNotEqual(
            missing_receipt_visibility_receipt_binding_receipt_receipt_tail_commit_report["status"],
            "public_draft_ready",
        )

    def test_readiness_evidence_snapshot_is_compact_public_safe_and_stable(self) -> None:
        report = run_readiness_check()
        snapshot = report["evidence_snapshot"]
        rebuilt = build_readiness_evidence_snapshot(report)

        self.assertEqual(snapshot["schema_version"], "unibot-readiness-evidence-snapshot-v1")
        self.assertEqual(snapshot["status"], "ready")
        self.assertEqual(snapshot["public_safety_status"], "pass")
        self.assertEqual(snapshot["readiness_status"], "public_draft_ready")
        self.assertEqual(snapshot["exam_deployment_status"], "not_cleared")
        self.assertEqual(snapshot["snapshot_hash"], rebuilt["snapshot_hash"])
        self.assertEqual(snapshot["scientific_gate_hash"], rebuilt["scientific_gate_hash"])
        self.assertGreaterEqual(snapshot["scientific_gate_count"], 10)
        self.assertEqual(snapshot["scientific_gate_passed_count"], snapshot["scientific_gate_count"])
        self.assertEqual(snapshot["failed_check_ids"], [])
        self.assertLess(len(json.dumps(snapshot, ensure_ascii=False)), 8000)
        self.assertIn("not exam clearance", snapshot["human_gate_reminder"])
        alignment = snapshot["workspace_card_snapshot_alignment"]
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["snapshot_hash"], snapshot["snapshot_hash"])
        self.assertEqual(alignment["scientific_gate_hash"], snapshot["scientific_gate_hash"])
        self.assertEqual(alignment["workspace_card_check_id"], "python_exam_local_cycle_operator_workspace_card")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_operator_prefill_hash_present"])
        self.assertFalse(alignment["raw_workspace_card_returned"])
        self.assertTrue(alignment["contracts"]["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["contracts"]["workspace_card_hash_metadata_preserved"])
        self.assertTrue(alignment["contracts"]["workspace_card_public_metadata_only"])
        self.assertTrue(alignment["contracts"]["high_stakes_boundaries_blocked"])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("exam clearance", alignment["blocked_claims"])

    def test_readiness_evidence_snapshot_blocks_when_workspace_card_link_breaks(self) -> None:
        report = run_readiness_check()
        workspace_card = next(
            check for check in report["checks"] if check["check_id"] == "python_exam_local_cycle_operator_workspace_card"
        )
        workspace_card["evidence"]["help_ledger_preview_hash_present"] = False

        snapshot = build_readiness_evidence_snapshot(report)

        self.assertEqual(snapshot["status"], "blocked")
        alignment = snapshot["workspace_card_snapshot_alignment"]
        self.assertEqual(alignment["status"], "blocked")
        self.assertIn("workspace_card_readiness_gate_linked", alignment["failed_contract_ids"])
        self.assertFalse(alignment["raw_workspace_card_returned"])

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
        self.assertIn("Runtime guard: budget_guard_ready", markdown)
        self.assertIn("Source-card drift: pass", markdown)
        self.assertIn("Evidence snapshot: ready", markdown)
        self.assertIn("`readiness_runtime_guard`: pass", markdown)
        self.assertIn("`source_card_drift_guard`: pass", markdown)

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
