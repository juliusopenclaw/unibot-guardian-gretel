from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.readiness import (  # noqa: E402
    build_readiness_evidence_snapshot,
    build_readiness_markdown,
    build_readiness_runtime_guard,
    default_public_paths,
    run_readiness_check,
)
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
        self.assertIn("extraction_progress", check_ids)
        self.assertIn("extraction_manifest_update", check_ids)
        self.assertIn("extraction_manifest_apply", check_ids)
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
        self.assertGreaterEqual(snapshot["scientific_gate_count"], 10)
        self.assertEqual(snapshot["scientific_gate_passed_count"], snapshot["scientific_gate_count"])
        self.assertEqual(snapshot["failed_check_ids"], [])
        self.assertLess(len(json.dumps(snapshot, ensure_ascii=False)), 6000)
        self.assertIn("not exam clearance", snapshot["human_gate_reminder"])

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
