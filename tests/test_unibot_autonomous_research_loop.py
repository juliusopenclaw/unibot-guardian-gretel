from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.autonomous_research_loop import (  # noqa: E402
    autonomous_loop_budget_hash,
    autonomous_loop_receipt_hash,
    build_autonomous_research_loop,
    build_autonomous_loop_workspace_card_alignment,
    build_autonomous_research_markdown,
    build_unibot_intent_contract,
    synthetic_autonomous_loop_workspace_card,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotAutonomousResearchLoopTests(unittest.TestCase):
    def test_intent_contract_names_user_intent_and_always_use_standards(self) -> None:
        contract = build_unibot_intent_contract()
        intent_ids = {item["intent_id"] for item in contract["product_intents"]}

        self.assertEqual(contract["owner"], "Gretel")
        self.assertIn("bachelor-thesis-level research project", contract["north_star"])
        self.assertIn("socratic_integrity_layer", intent_ids)
        self.assertIn("open_science_reproducibility", intent_ids)
        self.assertIn("glm_scientific_engineering", intent_ids)
        self.assertIn("autonomous_quality_loop", intent_ids)
        self.assertIn("public-safety scan", contract["always_use_standards"])
        self.assertIn("readiness check", contract["always_use_standards"])
        self.assertIn("Gretel/GLM proposal-only lane", contract["always_use_standards"])

    def test_autonomous_loop_is_budgeted_public_safe_and_not_external(self) -> None:
        loop = build_autonomous_research_loop()
        payload = json.dumps(loop, ensure_ascii=False)

        self.assertEqual(loop["schema_version"], "unibot-gretel-autonomous-research-loop-v1")
        self.assertEqual(loop["status"], "ready_for_budgeted_recurring_local_runs")
        self.assertEqual(loop["public_safety_status"], "pass")
        self.assertEqual(scan_text(payload, "autonomous-loop")["status"], "pass")
        self.assertEqual(loop["budget_policy"]["cadence"]["recommended_cron"], "every_6_hours")
        self.assertEqual(loop["budget_policy"]["token_policy"]["default_reasoning_effort"], "low")
        self.assertFalse(loop["safety"]["provider_call_executed"])
        self.assertFalse(loop["safety"]["autonomous_github_push"])
        self.assertFalse(loop["safety"]["mail_calendar_chat_actions"])
        self.assertFalse(loop["safety"]["final_go"])
        self.assertIn("publish or push to GitHub without explicit human review", loop["budget_policy"]["blocked_autonomous_actions"])
        self.assertNotIn("/" + "Users/", payload)
        self.assertNotIn("api" + "_key", payload.lower())

    def test_autonomous_loop_workspace_card_alignment_links_budget_and_receipt(self) -> None:
        loop = build_autonomous_research_loop()
        alignment = loop["workspace_card_budget_alignment"]

        self.assertEqual(alignment["schema_version"], "unibot-autonomous-research-loop-workspace-card-budget-alignment-v1")
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertEqual(alignment["budget_hash"], autonomous_loop_budget_hash(loop))
        self.assertEqual(alignment["receipt_hash"], autonomous_loop_receipt_hash(loop))
        self.assertEqual(alignment["recommended_cron"], "every_6_hours")
        self.assertEqual(alignment["max_active_work_item_per_run"], 1)
        self.assertEqual(alignment["default_reasoning_effort"], "low")
        self.assertEqual(alignment["ready_work_items"], 1)
        self.assertGreaterEqual(alignment["closed_harnessed_work_items"], 1)
        self.assertIn("gretel_autonomous_research_loop", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_operator_prefill_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_autonomous_loop_gate_linked"])
        self.assertFalse(alignment["raw_workspace_card_returned"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_autonomous_loop_hash_helpers_separate_budget_and_receipt_state(self) -> None:
        loop = build_autonomous_research_loop()

        self.assertEqual(len(autonomous_loop_budget_hash(loop)), 64)
        self.assertEqual(len(autonomous_loop_receipt_hash(loop)), 64)
        self.assertNotEqual(autonomous_loop_budget_hash(loop), autonomous_loop_receipt_hash(loop))

    def test_autonomous_loop_workspace_card_alignment_rejects_unlinked_hashes(self) -> None:
        loop = build_autonomous_research_loop()
        workspace_card = synthetic_autonomous_loop_workspace_card()
        workspace_card["workspace_card_summary"]["checkpoint_hash"] = "wrong-budget-hash"
        workspace_card["workspace_card_summary"]["task_hash"] = "wrong-receipt-hash"

        alignment = build_autonomous_loop_workspace_card_alignment(loop, workspace_card)

        self.assertEqual(alignment["status"], "blocked")
        self.assertIn("workspace_card_autonomous_loop_gate_linked", alignment["failed_contract_ids"])
        self.assertFalse(alignment["workspace_card_autonomous_loop_gate_linked"])
        self.assertFalse(alignment["raw_workspace_card_returned"])

    def test_work_queue_is_small_testable_and_harnessed(self) -> None:
        loop = build_autonomous_research_loop()
        queue = loop["work_queue"]
        by_id = {item["work_id"]: item for item in queue}

        self.assertGreaterEqual(len(queue), 57)
        self.assertEqual(by_id["intent_contract_regression_pack"]["status"], "closed_harnessed")
        self.assertEqual(by_id["intent_contract_regression_pack"]["closure_evidence"]["commit"], "fa942b0")
        self.assertEqual(by_id["scientific_evaluation_depth"]["status"], "closed_harnessed")
        self.assertEqual(by_id["scientific_evaluation_depth"]["closure_evidence"]["commit"], "2b6473b")
        self.assertEqual(by_id["github_review_packet_hardening"]["status"], "closed_harnessed")
        self.assertEqual(by_id["github_review_packet_hardening"]["closure_evidence"]["commit"], "9a28675")
        self.assertEqual(by_id["autonomy_progress_memory"]["status"], "closed_harnessed")
        self.assertEqual(by_id["autonomy_progress_memory"]["closure_evidence"]["commit"], "5d16846")
        self.assertEqual(by_id["readiness_perf_guard"]["status"], "closed_harnessed")
        self.assertEqual(by_id["readiness_perf_guard"]["closure_evidence"]["commit"], "c6581a3")
        self.assertEqual(by_id["source_card_drift_guard"]["status"], "closed_harnessed")
        self.assertEqual(by_id["source_card_drift_guard"]["closure_evidence"]["commit"], "afeb0d5")
        self.assertEqual(by_id["bachelor_thesis_evidence_index"]["status"], "closed_harnessed")
        self.assertEqual(by_id["bachelor_thesis_evidence_index"]["closure_evidence"]["commit"], "400fc92")
        self.assertEqual(by_id["readiness_evidence_snapshot"]["status"], "closed_harnessed")
        self.assertEqual(by_id["readiness_evidence_snapshot"]["closure_evidence"]["commit"], "19d6f8c")
        self.assertEqual(by_id["review_board_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["review_board_evidence_alignment"]["closure_evidence"]["commit"], "f449f88")
        self.assertEqual(by_id["feedback_issue_evidence_traceability"]["status"], "closed_harnessed")
        self.assertEqual(by_id["feedback_issue_evidence_traceability"]["closure_evidence"]["commit"], "99d36ff")
        self.assertEqual(by_id["release_runbook_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["release_runbook_evidence_alignment"]["closure_evidence"]["commit"], "be671ff")
        self.assertEqual(by_id["compliance_drift_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["compliance_drift_evidence_alignment"]["closure_evidence"]["commit"], "92cb2f1")
        self.assertEqual(by_id["pilot_protocol_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["pilot_protocol_evidence_alignment"]["closure_evidence"]["commit"], "30a81a8")
        self.assertEqual(by_id["pilot_protocol_evidence_alignment"]["review_gate"], "pilot_ethics_data_human_review_traceability")
        self.assertEqual(by_id["data_protection_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["data_protection_evidence_alignment"]["closure_evidence"]["commit"], "4b5fbbc")
        self.assertEqual(by_id["data_protection_evidence_alignment"]["review_gate"], "datenschutz_pilot_records_human_review_traceability")
        self.assertEqual(by_id["glm_provider_redaction_evidence_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["glm_provider_redaction_evidence_alignment"]["closure_evidence"]["commit"], "a41b060")
        self.assertEqual(
            by_id["glm_provider_redaction_evidence_alignment"]["review_gate"],
            "glm_redacted_proposal_provider_lock_human_review_traceability",
        )
        self.assertEqual(by_id["open_science_reproducibility_release_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["open_science_reproducibility_release_alignment"]["closure_evidence"]["commit"], "ecfa4f8")
        self.assertEqual(
            by_id["open_science_reproducibility_release_alignment"]["review_gate"],
            "open_science_reproducibility_release_human_review_traceability",
        )
        self.assertEqual(by_id["course_material_public_boundary_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["course_material_public_boundary_alignment"]["closure_evidence"]["commit"], "ca9c426")
        self.assertEqual(
            by_id["course_material_public_boundary_alignment"]["review_gate"],
            "course_material_public_private_boundary_traceability",
        )
        self.assertEqual(by_id["adaptive_task_source_boundary_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["adaptive_task_source_boundary_alignment"]["closure_evidence"]["commit"], "00bc10e")
        self.assertEqual(
            by_id["adaptive_task_source_boundary_alignment"]["review_gate"],
            "adaptive_tasks_public_material_source_boundary_traceability",
        )
        self.assertEqual(by_id["evaluation_learner_agency_boundary_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["evaluation_learner_agency_boundary_alignment"]["closure_evidence"]["commit"], "7c04e0d")
        self.assertEqual(
            by_id["evaluation_learner_agency_boundary_alignment"]["review_gate"],
            "evaluation_learner_agency_source_boundary_traceability",
        )
        self.assertEqual(by_id["bachelor_thesis_evaluation_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["bachelor_thesis_evaluation_claim_alignment"]["closure_evidence"]["commit"], "5fcdbfe")
        self.assertEqual(
            by_id["bachelor_thesis_evaluation_claim_alignment"]["review_gate"],
            "bachelor_thesis_evaluation_claim_traceability",
        )
        self.assertEqual(by_id["review_board_thesis_evaluation_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["review_board_thesis_evaluation_claim_alignment"]["closure_evidence"]["commit"], "20a66a0")
        self.assertEqual(
            by_id["review_board_thesis_evaluation_claim_alignment"]["review_gate"],
            "review_board_thesis_evaluation_claim_traceability",
        )
        self.assertEqual(by_id["release_runbook_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["release_runbook_review_board_claim_alignment"]["closure_evidence"]["commit"], "77f5b61")
        self.assertEqual(
            by_id["release_runbook_review_board_claim_alignment"]["review_gate"],
            "release_runbook_review_board_thesis_claim_traceability",
        )
        self.assertEqual(by_id["compliance_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["compliance_release_review_board_claim_alignment"]["closure_evidence"]["commit"], "6170a9a")
        self.assertEqual(
            by_id["compliance_release_review_board_claim_alignment"]["review_gate"],
            "compliance_release_review_board_thesis_claim_traceability",
        )
        self.assertEqual(by_id["pilot_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(by_id["pilot_release_review_board_claim_alignment"]["closure_evidence"]["commit"], "582c574")
        self.assertEqual(
            by_id["pilot_release_review_board_claim_alignment"]["review_gate"],
            "pilot_release_review_board_thesis_claim_traceability",
        )
        self.assertEqual(by_id["data_protection_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["data_protection_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "447a37e",
        )
        self.assertEqual(
            by_id["data_protection_release_review_board_claim_alignment"]["review_gate"],
            "data_protection_release_review_board_thesis_claim_traceability",
        )
        self.assertEqual(by_id["publication_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["publication_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "d794a40",
        )
        self.assertEqual(
            by_id["publication_release_review_board_claim_alignment"]["review_gate"],
            "publication_release_review_board_thesis_claim_traceability",
        )
        self.assertEqual(by_id["github_issue_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["github_issue_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "16dcbb3",
        )
        self.assertEqual(
            by_id["github_issue_release_review_board_claim_alignment"]["review_gate"],
            "github_issue_release_review_board_thesis_claim_traceability",
        )
        self.assertEqual(by_id["feedback_triage_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["feedback_triage_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "c74e157",
        )
        self.assertEqual(
            by_id["feedback_triage_release_review_board_claim_alignment"]["review_gate"],
            "feedback_triage_release_review_board_thesis_claim_traceability",
        )
        self.assertIn("unibot/triage.py", by_id["feedback_triage_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["demo_feedback_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["demo_feedback_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "9940ac7",
        )
        self.assertEqual(
            by_id["demo_feedback_release_review_board_claim_alignment"]["review_gate"],
            "demo_feedback_release_review_board_thesis_claim_traceability",
        )
        self.assertIn("unibot/feedback.py", by_id["demo_feedback_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["local_demo_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["local_demo_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "4cd091d",
        )
        self.assertEqual(
            by_id["local_demo_release_review_board_claim_alignment"]["review_gate"],
            "local_demo_release_review_board_thesis_claim_traceability",
        )
        self.assertIn("unibot/demo.py", by_id["local_demo_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["browser_extension_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["browser_extension_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "3db6902",
        )
        self.assertEqual(
            by_id["browser_extension_release_review_board_claim_alignment"]["review_gate"],
            "browser_extension_release_review_board_thesis_claim_traceability",
        )
        self.assertIn("unibot/browser_extension/sidepanel.js", by_id["browser_extension_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["browser_manifest_content_boundary_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["browser_manifest_content_boundary_claim_alignment"]["closure_evidence"]["commit"],
            "1032d84",
        )
        self.assertEqual(
            by_id["browser_manifest_content_boundary_claim_alignment"]["review_gate"],
            "browser_manifest_content_boundary_claim_traceability",
        )
        self.assertIn("unibot/browser_extension/manifest.json", by_id["browser_manifest_content_boundary_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["notebook_handoff_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["notebook_handoff_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "74c074a",
        )
        self.assertEqual(
            by_id["notebook_handoff_release_review_board_claim_alignment"]["review_gate"],
            "notebook_handoff_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/notebooks.py", by_id["notebook_handoff_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["redteam_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["redteam_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "639a2cb",
        )
        self.assertEqual(
            by_id["redteam_release_review_board_claim_alignment"]["review_gate"],
            "redteam_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/redteam.py", by_id["redteam_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["source_card_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["source_card_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "bda02d3",
        )
        self.assertEqual(
            by_id["source_card_release_review_board_claim_alignment"]["review_gate"],
            "source_card_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/source_cards.py", by_id["source_card_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["threat_model_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["threat_model_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "fb2c4e9",
        )
        self.assertEqual(
            by_id["threat_model_release_review_board_claim_alignment"]["review_gate"],
            "threat_model_release_review_board_claim_traceability",
        )
        self.assertIn("docs/unibot/UNIBOT_THREAT_MODEL.md", by_id["threat_model_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["review_board_packet_release_claim_summary_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["review_board_packet_release_claim_summary_alignment"]["closure_evidence"]["commit"],
            "bf2c654",
        )
        self.assertEqual(
            by_id["review_board_packet_release_claim_summary_alignment"]["review_gate"],
            "review_board_packet_release_claim_summary_traceability",
        )
        self.assertIn("unibot/review_board.py", by_id["review_board_packet_release_claim_summary_alignment"]["allowed_files"])
        self.assertEqual(by_id["authority_handoff_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["authority_handoff_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "5867d66",
        )
        self.assertEqual(
            by_id["authority_handoff_release_review_board_claim_alignment"]["review_gate"],
            "authority_handoff_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/handoff.py", by_id["authority_handoff_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["stakeholder_submission_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["stakeholder_submission_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "408debe",
        )
        self.assertEqual(
            by_id["stakeholder_submission_release_review_board_claim_alignment"]["review_gate"],
            "stakeholder_submission_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/submission.py", by_id["stakeholder_submission_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["stakeholder_decision_request_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["stakeholder_decision_request_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "99060f6",
        )
        self.assertEqual(
            by_id["stakeholder_decision_request_release_review_board_claim_alignment"]["review_gate"],
            "stakeholder_decision_request_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/decision_request.py", by_id["stakeholder_decision_request_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["stakeholder_decision_journal_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["stakeholder_decision_journal_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "a6052b7",
        )
        self.assertEqual(
            by_id["stakeholder_decision_journal_release_review_board_claim_alignment"]["review_gate"],
            "stakeholder_decision_journal_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/decision_journal.py", by_id["stakeholder_decision_journal_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["external_decision_record_journal_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["external_decision_record_journal_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "e785479",
        )
        self.assertEqual(
            by_id["external_decision_record_journal_release_review_board_claim_alignment"]["review_gate"],
            "external_decision_record_journal_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/external_decision_journal.py", by_id["external_decision_record_journal_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["external_decision_state_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["external_decision_state_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "05fb04e",
        )
        self.assertEqual(
            by_id["external_decision_state_release_review_board_claim_alignment"]["review_gate"],
            "external_decision_state_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/decision_state.py", by_id["external_decision_state_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["extraction_receipt_journal_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["extraction_receipt_journal_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "51b537a",
        )
        self.assertEqual(
            by_id["extraction_receipt_journal_release_review_board_claim_alignment"]["review_gate"],
            "extraction_receipt_journal_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/extraction_receipt_journal.py", by_id["extraction_receipt_journal_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["extraction_progress_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["extraction_progress_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "8562658",
        )
        self.assertEqual(
            by_id["extraction_progress_release_review_board_claim_alignment"]["review_gate"],
            "extraction_progress_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/extraction_progress.py", by_id["extraction_progress_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["extraction_manifest_update_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["extraction_manifest_update_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "49d4fa2",
        )
        self.assertEqual(
            by_id["extraction_manifest_update_release_review_board_claim_alignment"]["review_gate"],
            "extraction_manifest_update_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/extraction_manifest_update.py", by_id["extraction_manifest_update_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["extraction_manifest_apply_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["extraction_manifest_apply_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "fbda8fe",
        )
        self.assertEqual(
            by_id["extraction_manifest_apply_release_review_board_claim_alignment"]["review_gate"],
            "extraction_manifest_apply_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/extraction_manifest_apply.py", by_id["extraction_manifest_apply_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["extraction_completion_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["extraction_completion_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "19f9bfe",
        )
        self.assertEqual(
            by_id["extraction_completion_release_review_board_claim_alignment"]["review_gate"],
            "extraction_completion_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/extraction_completion.py", by_id["extraction_completion_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["extraction_human_review_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["extraction_human_review_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "0cecaf4",
        )
        self.assertEqual(
            by_id["extraction_human_review_release_review_board_claim_alignment"]["review_gate"],
            "extraction_human_review_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/extraction_human_review.py", by_id["extraction_human_review_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["private_tutor_use_flow_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["private_tutor_use_flow_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "d850fa2",
        )
        self.assertEqual(
            by_id["private_tutor_use_flow_release_review_board_claim_alignment"]["review_gate"],
            "private_tutor_use_flow_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/private_tutor_use_flow.py", by_id["private_tutor_use_flow_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["study_session_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["study_session_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "934f817",
        )
        self.assertEqual(
            by_id["study_session_release_review_board_claim_alignment"]["review_gate"],
            "study_session_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/study_session.py", by_id["study_session_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["notebook_checkpoint_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["notebook_checkpoint_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "fb0b59e",
        )
        self.assertEqual(
            by_id["notebook_checkpoint_release_review_board_claim_alignment"]["review_gate"],
            "notebook_checkpoint_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/exam_notebook_checkpoint.py", by_id["notebook_checkpoint_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["exam_workspace_launch_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["exam_workspace_launch_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "0a3d05f",
        )
        self.assertEqual(
            by_id["exam_workspace_launch_release_review_board_claim_alignment"]["review_gate"],
            "exam_workspace_launch_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/exam_workspace_launch_flow.py", by_id["exam_workspace_launch_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["exam_workspace_run_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["exam_workspace_run_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "c6a0dbf",
        )
        self.assertEqual(
            by_id["exam_workspace_run_release_review_board_claim_alignment"]["review_gate"],
            "exam_workspace_run_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/exam_workspace_run.py", by_id["exam_workspace_run_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["exam_workspace_run_history_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["exam_workspace_run_history_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "2581243",
        )
        self.assertEqual(
            by_id["exam_workspace_run_history_release_review_board_claim_alignment"]["review_gate"],
            "exam_workspace_run_history_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/exam_workspace_run_history.py", by_id["exam_workspace_run_history_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["exam_workspace_operator_run_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["exam_workspace_operator_run_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "b5fee21",
        )
        self.assertEqual(
            by_id["exam_workspace_operator_run_release_review_board_claim_alignment"]["review_gate"],
            "exam_workspace_operator_run_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/exam_workspace_operator_run.py", by_id["exam_workspace_operator_run_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["exam_workspace_session_console_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["exam_workspace_session_console_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "e5d013b",
        )
        self.assertEqual(
            by_id["exam_workspace_session_console_release_review_board_claim_alignment"]["review_gate"],
            "exam_workspace_session_console_release_review_board_claim_traceability",
        )
        self.assertIn("unibot/exam_workspace_session_console.py", by_id["exam_workspace_session_console_release_review_board_claim_alignment"]["allowed_files"])
        self.assertEqual(by_id["python_exam_local_cycle_start_packet_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["python_exam_local_cycle_start_packet_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "72c555c",
        )
        self.assertEqual(
            by_id["python_exam_local_cycle_start_packet_release_review_board_claim_alignment"]["review_gate"],
            "python_exam_local_cycle_start_packet_release_review_board_claim_traceability",
        )
        self.assertIn(
            "unibot/python_exam_local_cycle_start_packet.py",
            by_id["python_exam_local_cycle_start_packet_release_review_board_claim_alignment"]["allowed_files"],
        )
        self.assertEqual(by_id["python_exam_local_cycle_readiness_review_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["python_exam_local_cycle_readiness_review_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "c0511e5",
        )
        self.assertEqual(
            by_id["python_exam_local_cycle_readiness_review_release_review_board_claim_alignment"]["review_gate"],
            "python_exam_local_cycle_readiness_review_release_review_board_claim_traceability",
        )
        self.assertIn(
            "unibot/python_exam_local_cycle_readiness_review.py",
            by_id["python_exam_local_cycle_readiness_review_release_review_board_claim_alignment"]["allowed_files"],
        )
        self.assertEqual(by_id["python_exam_local_cycle_readiness_handoff_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["python_exam_local_cycle_readiness_handoff_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "31fc0c8",
        )
        self.assertEqual(
            by_id["python_exam_local_cycle_readiness_handoff_release_review_board_claim_alignment"]["review_gate"],
            "python_exam_local_cycle_readiness_handoff_release_review_board_claim_traceability",
        )
        self.assertIn(
            "unibot/python_exam_local_cycle_readiness_handoff.py",
            by_id["python_exam_local_cycle_readiness_handoff_release_review_board_claim_alignment"]["allowed_files"],
        )
        self.assertEqual(by_id["python_exam_local_cycle_operator_workspace_card_release_review_board_claim_alignment"]["status"], "closed_harnessed")
        self.assertEqual(
            by_id["python_exam_local_cycle_operator_workspace_card_release_review_board_claim_alignment"]["closure_evidence"]["commit"],
            "87abb96",
        )
        self.assertEqual(
            by_id["python_exam_local_cycle_operator_workspace_card_release_review_board_claim_alignment"]["review_gate"],
            "python_exam_local_cycle_operator_workspace_card_release_review_board_claim_traceability",
        )
        self.assertIn(
            "unibot/python_exam_local_cycle_operator_workspace_card.py",
            by_id["python_exam_local_cycle_operator_workspace_card_release_review_board_claim_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_workspace_session_console_local_cycle_workspace_card_readiness_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_workspace_session_console_local_cycle_workspace_card_readiness_link_alignment"]["closure_evidence"]["commit"],
            "4543a62",
        )
        self.assertEqual(
            by_id["exam_workspace_session_console_local_cycle_workspace_card_readiness_link_alignment"]["review_gate"],
            "exam_workspace_session_console_local_cycle_workspace_card_readiness_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_session_console.py",
            by_id["exam_workspace_session_console_local_cycle_workspace_card_readiness_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_workspace_run_history_local_cycle_workspace_card_review_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_workspace_run_history_local_cycle_workspace_card_review_link_alignment"]["closure_evidence"]["commit"],
            "99c0914",
        )
        self.assertEqual(
            by_id["exam_workspace_run_history_local_cycle_workspace_card_review_link_alignment"]["review_gate"],
            "exam_workspace_run_history_local_cycle_workspace_card_review_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_run_history.py",
            by_id["exam_workspace_run_history_local_cycle_workspace_card_review_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_workspace_operator_run_local_cycle_workspace_card_start_view_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_workspace_operator_run_local_cycle_workspace_card_start_view_link_alignment"]["closure_evidence"]["commit"],
            "1064cda",
        )
        self.assertEqual(
            by_id["exam_workspace_operator_run_local_cycle_workspace_card_start_view_link_alignment"]["review_gate"],
            "exam_workspace_operator_run_local_cycle_workspace_card_start_view_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_operator_run.py",
            by_id["exam_workspace_operator_run_local_cycle_workspace_card_start_view_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_workspace_launch_local_cycle_workspace_card_gate_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_workspace_launch_local_cycle_workspace_card_gate_link_alignment"]["closure_evidence"]["commit"],
            "d06c1b9",
        )
        self.assertEqual(
            by_id["exam_workspace_launch_local_cycle_workspace_card_gate_link_alignment"]["review_gate"],
            "exam_workspace_launch_local_cycle_workspace_card_gate_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_launch_flow.py",
            by_id["exam_workspace_launch_local_cycle_workspace_card_gate_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_workspace_run_local_cycle_workspace_card_execution_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_workspace_run_local_cycle_workspace_card_execution_link_alignment"]["closure_evidence"]["commit"],
            "20eb12b",
        )
        self.assertEqual(
            by_id["exam_workspace_run_local_cycle_workspace_card_execution_link_alignment"]["review_gate"],
            "exam_workspace_run_local_cycle_workspace_card_execution_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_run.py",
            by_id["exam_workspace_run_local_cycle_workspace_card_execution_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["notebook_checkpoint_local_cycle_workspace_card_checkpoint_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["notebook_checkpoint_local_cycle_workspace_card_checkpoint_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "988cf65",
        )
        self.assertEqual(
            by_id["notebook_checkpoint_local_cycle_workspace_card_checkpoint_link_alignment"]["review_gate"],
            "notebook_checkpoint_local_cycle_workspace_card_checkpoint_link_traceability",
        )
        self.assertIn(
            "unibot/exam_notebook_checkpoint.py",
            by_id["notebook_checkpoint_local_cycle_workspace_card_checkpoint_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["study_session_local_cycle_workspace_card_reflection_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["study_session_local_cycle_workspace_card_reflection_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "77d12b5",
        )
        self.assertEqual(
            by_id["study_session_local_cycle_workspace_card_reflection_link_alignment"]["review_gate"],
            "study_session_local_cycle_workspace_card_reflection_link_traceability",
        )
        self.assertIn(
            "unibot/study_session.py",
            by_id["study_session_local_cycle_workspace_card_reflection_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["private_tutor_use_flow_local_cycle_workspace_card_help_ledger_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["private_tutor_use_flow_local_cycle_workspace_card_help_ledger_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "89f4938",
        )
        self.assertEqual(
            by_id["private_tutor_use_flow_local_cycle_workspace_card_help_ledger_link_alignment"]["review_gate"],
            "private_tutor_use_flow_local_cycle_workspace_card_help_ledger_link_traceability",
        )
        self.assertIn(
            "unibot/private_tutor_use_flow.py",
            by_id["private_tutor_use_flow_local_cycle_workspace_card_help_ledger_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["extraction_manifest_apply_local_cycle_workspace_card_manifest_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["extraction_manifest_apply_local_cycle_workspace_card_manifest_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "7e16ae9",
        )
        self.assertEqual(
            by_id["extraction_manifest_apply_local_cycle_workspace_card_manifest_link_alignment"]["review_gate"],
            "extraction_manifest_apply_local_cycle_workspace_card_manifest_link_traceability",
        )
        self.assertIn(
            "unibot/extraction_manifest_apply.py",
            by_id["extraction_manifest_apply_local_cycle_workspace_card_manifest_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["extraction_manifest_update_local_cycle_workspace_card_candidate_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["extraction_manifest_update_local_cycle_workspace_card_candidate_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "97b8634",
        )
        self.assertEqual(
            by_id["extraction_manifest_update_local_cycle_workspace_card_candidate_link_alignment"]["review_gate"],
            "extraction_manifest_update_local_cycle_workspace_card_candidate_link_traceability",
        )
        self.assertIn(
            "unibot/extraction_manifest_update.py",
            by_id["extraction_manifest_update_local_cycle_workspace_card_candidate_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["extraction_progress_local_cycle_workspace_card_queue_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["extraction_progress_local_cycle_workspace_card_queue_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "4414ee2",
        )
        self.assertEqual(
            by_id["extraction_progress_local_cycle_workspace_card_queue_link_alignment"]["review_gate"],
            "extraction_progress_local_cycle_workspace_card_queue_link_traceability",
        )
        self.assertIn(
            "unibot/extraction_progress.py",
            by_id["extraction_progress_local_cycle_workspace_card_queue_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["extraction_receipt_journal_local_cycle_workspace_card_receipt_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["extraction_receipt_journal_local_cycle_workspace_card_receipt_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "942a59b",
        )
        self.assertEqual(
            by_id["extraction_receipt_journal_local_cycle_workspace_card_receipt_link_alignment"]["review_gate"],
            "extraction_receipt_journal_local_cycle_workspace_card_receipt_link_traceability",
        )
        self.assertIn(
            "unibot/extraction_receipt_journal.py",
            by_id["extraction_receipt_journal_local_cycle_workspace_card_receipt_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["external_decision_state_local_cycle_workspace_card_gate_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["external_decision_state_local_cycle_workspace_card_gate_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "dcebb68",
        )
        self.assertEqual(
            by_id["external_decision_state_local_cycle_workspace_card_gate_link_alignment"]["review_gate"],
            "external_decision_state_local_cycle_workspace_card_gate_link_traceability",
        )
        self.assertIn(
            "unibot/decision_state.py",
            by_id["external_decision_state_local_cycle_workspace_card_gate_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["external_decision_record_journal_local_cycle_workspace_card_record_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["external_decision_record_journal_local_cycle_workspace_card_record_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "59be092",
        )
        self.assertEqual(
            by_id["external_decision_record_journal_local_cycle_workspace_card_record_link_alignment"]["review_gate"],
            "external_decision_record_journal_local_cycle_workspace_card_record_link_traceability",
        )
        self.assertIn(
            "unibot/external_decision_journal.py",
            by_id["external_decision_record_journal_local_cycle_workspace_card_record_link_alignment"][
                "allowed_files"
            ],
        )
        self.assertEqual(
            by_id["stakeholder_decision_journal_local_cycle_workspace_card_request_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["stakeholder_decision_journal_local_cycle_workspace_card_request_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "6d7f5d0",
        )
        self.assertEqual(
            by_id["stakeholder_decision_journal_local_cycle_workspace_card_request_link_alignment"]["review_gate"],
            "stakeholder_decision_journal_local_cycle_workspace_card_request_link_traceability",
        )
        self.assertIn(
            "unibot/decision_journal.py",
            by_id["stakeholder_decision_journal_local_cycle_workspace_card_request_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["stakeholder_decision_request_local_cycle_workspace_card_packet_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["stakeholder_decision_request_local_cycle_workspace_card_packet_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "2809248",
        )
        self.assertEqual(
            by_id["stakeholder_decision_request_local_cycle_workspace_card_packet_link_alignment"]["review_gate"],
            "stakeholder_decision_request_local_cycle_workspace_card_packet_link_traceability",
        )
        self.assertIn(
            "unibot/decision_request.py",
            by_id["stakeholder_decision_request_local_cycle_workspace_card_packet_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["stakeholder_submission_bundle_local_cycle_workspace_card_lane_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["stakeholder_submission_bundle_local_cycle_workspace_card_lane_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "57fafbd",
        )
        self.assertEqual(
            by_id["stakeholder_submission_bundle_local_cycle_workspace_card_lane_link_alignment"]["review_gate"],
            "stakeholder_submission_bundle_local_cycle_workspace_card_lane_link_traceability",
        )
        self.assertIn(
            "unibot/submission.py",
            by_id["stakeholder_submission_bundle_local_cycle_workspace_card_lane_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["authority_handoff_local_cycle_workspace_card_authority_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["authority_handoff_local_cycle_workspace_card_authority_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "9e4b6b9",
        )
        self.assertEqual(
            by_id["authority_handoff_local_cycle_workspace_card_authority_link_alignment"]["review_gate"],
            "authority_handoff_local_cycle_workspace_card_authority_link_traceability",
        )
        self.assertIn(
            "unibot/handoff.py",
            by_id["authority_handoff_local_cycle_workspace_card_authority_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["review_board_packet_local_cycle_workspace_card_review_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["review_board_packet_local_cycle_workspace_card_review_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "3865e19",
        )
        self.assertEqual(
            by_id["review_board_packet_local_cycle_workspace_card_review_link_alignment"]["review_gate"],
            "review_board_packet_local_cycle_workspace_card_review_link_traceability",
        )
        self.assertIn(
            "unibot/review_board.py",
            by_id["review_board_packet_local_cycle_workspace_card_review_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["release_runbook_local_cycle_workspace_card_release_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["release_runbook_local_cycle_workspace_card_release_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "74b9311",
        )
        self.assertEqual(
            by_id["release_runbook_local_cycle_workspace_card_release_link_alignment"]["review_gate"],
            "release_runbook_local_cycle_workspace_card_release_link_traceability",
        )
        self.assertIn(
            "unibot/release_runbook.py",
            by_id["release_runbook_local_cycle_workspace_card_release_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["publication_package_local_cycle_workspace_card_publication_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["publication_package_local_cycle_workspace_card_publication_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "7dee620",
        )
        self.assertEqual(
            by_id["publication_package_local_cycle_workspace_card_publication_link_alignment"]["review_gate"],
            "publication_package_local_cycle_workspace_card_publication_link_traceability",
        )
        self.assertIn(
            "unibot/publication.py",
            by_id["publication_package_local_cycle_workspace_card_publication_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["bachelor_thesis_package_local_cycle_workspace_card_thesis_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["bachelor_thesis_package_local_cycle_workspace_card_thesis_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "49c1da7",
        )
        self.assertEqual(
            by_id["bachelor_thesis_package_local_cycle_workspace_card_thesis_link_alignment"]["review_gate"],
            "bachelor_thesis_package_local_cycle_workspace_card_thesis_link_traceability",
        )
        self.assertIn(
            "unibot/bachelor_thesis.py",
            by_id["bachelor_thesis_package_local_cycle_workspace_card_thesis_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["gretel_glm_evolve_lane_local_cycle_workspace_card_glm_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["gretel_glm_evolve_lane_local_cycle_workspace_card_glm_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "89b774a",
        )
        self.assertEqual(
            by_id["gretel_glm_evolve_lane_local_cycle_workspace_card_glm_link_alignment"]["review_gate"],
            "gretel_glm_evolve_lane_local_cycle_workspace_card_glm_link_traceability",
        )
        self.assertIn(
            "unibot/gretel_glm_evolve.py",
            by_id["gretel_glm_evolve_lane_local_cycle_workspace_card_glm_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["source_card_drift_guard_local_cycle_workspace_card_source_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["source_card_drift_guard_local_cycle_workspace_card_source_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "f2efef7",
        )
        self.assertEqual(
            by_id["source_card_drift_guard_local_cycle_workspace_card_source_link_alignment"]["review_gate"],
            "source_card_drift_guard_local_cycle_workspace_card_source_link_traceability",
        )
        self.assertIn(
            "unibot/source_cards.py",
            by_id["source_card_drift_guard_local_cycle_workspace_card_source_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["readiness_evidence_snapshot_local_cycle_workspace_card_snapshot_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["readiness_evidence_snapshot_local_cycle_workspace_card_snapshot_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "3ad3e5f",
        )
        self.assertEqual(
            by_id["readiness_evidence_snapshot_local_cycle_workspace_card_snapshot_link_alignment"]["review_gate"],
            "readiness_evidence_snapshot_local_cycle_workspace_card_snapshot_link_traceability",
        )
        self.assertIn(
            "unibot/readiness.py",
            by_id["readiness_evidence_snapshot_local_cycle_workspace_card_snapshot_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["autonomous_research_loop_local_cycle_workspace_card_budget_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["autonomous_research_loop_local_cycle_workspace_card_budget_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "2a43b20",
        )
        self.assertEqual(
            by_id["autonomous_research_loop_local_cycle_workspace_card_budget_link_alignment"]["review_gate"],
            "autonomous_research_loop_local_cycle_workspace_card_budget_link_traceability",
        )
        self.assertIn(
            "unibot/autonomous_research_loop.py",
            by_id["autonomous_research_loop_local_cycle_workspace_card_budget_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["paperclip_evaluation_bridge_local_cycle_workspace_card_control_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["paperclip_evaluation_bridge_local_cycle_workspace_card_control_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "eb7b327",
        )
        self.assertEqual(
            by_id["paperclip_evaluation_bridge_local_cycle_workspace_card_control_link_alignment"]["review_gate"],
            "paperclip_evaluation_bridge_local_cycle_workspace_card_control_link_traceability",
        )
        self.assertIn(
            "unibot/paperclip_evaluation_bridge.py",
            by_id["paperclip_evaluation_bridge_local_cycle_workspace_card_control_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["command_center_local_cycle_workspace_card_route_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["command_center_local_cycle_workspace_card_route_link_alignment"]["closure_evidence"]["commit"],
            "6d2ed1b",
        )
        self.assertEqual(
            by_id["command_center_local_cycle_workspace_card_route_link_alignment"]["review_gate"],
            "command_center_local_cycle_workspace_card_route_link_traceability",
        )
        self.assertIn(
            "unibot/orchestration.py",
            by_id["command_center_local_cycle_workspace_card_route_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["completion_audit_local_cycle_workspace_card_closure_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["completion_audit_local_cycle_workspace_card_closure_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "85b1667",
        )
        self.assertEqual(
            by_id["completion_audit_local_cycle_workspace_card_closure_link_alignment"]["review_gate"],
            "completion_audit_local_cycle_workspace_card_closure_link_traceability",
        )
        self.assertIn(
            "unibot/completion_audit.py",
            by_id["completion_audit_local_cycle_workspace_card_closure_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["review_chain_integrity_local_cycle_workspace_card_chain_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["review_chain_integrity_local_cycle_workspace_card_chain_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "d8c6612",
        )
        self.assertEqual(
            by_id["review_chain_integrity_local_cycle_workspace_card_chain_link_alignment"]["review_gate"],
            "review_chain_integrity_local_cycle_workspace_card_chain_link_traceability",
        )
        self.assertIn(
            "unibot/review_chain_integrity.py",
            by_id["review_chain_integrity_local_cycle_workspace_card_chain_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["timeline_export_receipt_journal_local_cycle_workspace_card_journal_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["timeline_export_receipt_journal_local_cycle_workspace_card_journal_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "bf1359f",
        )
        self.assertEqual(
            by_id["timeline_export_receipt_journal_local_cycle_workspace_card_journal_link_alignment"]["review_gate"],
            "timeline_export_receipt_journal_local_cycle_workspace_card_journal_link_traceability",
        )
        self.assertIn(
            "unibot/timeline_export_receipt_journal.py",
            by_id["timeline_export_receipt_journal_local_cycle_workspace_card_journal_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["timeline_export_review_packet_local_cycle_workspace_card_review_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["timeline_export_review_packet_local_cycle_workspace_card_review_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "338f1b6",
        )
        self.assertEqual(
            by_id["timeline_export_review_packet_local_cycle_workspace_card_review_link_alignment"]["review_gate"],
            "timeline_export_review_packet_local_cycle_workspace_card_review_link_traceability",
        )
        self.assertIn(
            "unibot/timeline_export_review_packet.py",
            by_id["timeline_export_review_packet_local_cycle_workspace_card_review_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_packet_timeline_local_cycle_workspace_card_timeline_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_packet_timeline_local_cycle_workspace_card_timeline_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "58c8882",
        )
        self.assertEqual(
            by_id["exam_packet_timeline_local_cycle_workspace_card_timeline_link_alignment"]["review_gate"],
            "exam_packet_timeline_local_cycle_workspace_card_timeline_link_traceability",
        )
        self.assertIn(
            "unibot/exam_packet_timeline.py",
            by_id["exam_packet_timeline_local_cycle_workspace_card_timeline_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_run_packet_local_cycle_workspace_card_packet_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_run_packet_local_cycle_workspace_card_packet_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "e8db021",
        )
        self.assertEqual(
            by_id["exam_run_packet_local_cycle_workspace_card_packet_link_alignment"]["review_gate"],
            "exam_run_packet_local_cycle_workspace_card_packet_link_traceability",
        )
        self.assertIn(
            "unibot/exam_run_packet_builder.py",
            by_id["exam_run_packet_local_cycle_workspace_card_packet_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["routed_action_executor_local_cycle_workspace_card_execution_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["routed_action_executor_local_cycle_workspace_card_execution_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "d390b41",
        )
        self.assertEqual(
            by_id["routed_action_executor_local_cycle_workspace_card_execution_link_alignment"]["review_gate"],
            "routed_action_executor_local_cycle_workspace_card_execution_link_traceability",
        )
        self.assertIn(
            "unibot/routed_action_executor.py",
            by_id["routed_action_executor_local_cycle_workspace_card_execution_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["course_per_skill_action_router_local_cycle_workspace_card_route_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["course_per_skill_action_router_local_cycle_workspace_card_route_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "e5e4e42",
        )
        self.assertEqual(
            by_id["course_per_skill_action_router_local_cycle_workspace_card_route_link_alignment"]["review_gate"],
            "course_per_skill_action_router_local_cycle_workspace_card_route_link_traceability",
        )
        self.assertIn(
            "unibot/course_per_skill_action_router.py",
            by_id["course_per_skill_action_router_local_cycle_workspace_card_route_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["course_exam_coverage_dashboard_local_cycle_workspace_card_dashboard_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["course_exam_coverage_dashboard_local_cycle_workspace_card_dashboard_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "624fde3",
        )
        self.assertEqual(
            by_id["course_exam_coverage_dashboard_local_cycle_workspace_card_dashboard_link_alignment"]["review_gate"],
            "course_exam_coverage_dashboard_local_cycle_workspace_card_dashboard_link_traceability",
        )
        self.assertIn(
            "unibot/course_exam_coverage_dashboard.py",
            by_id["course_exam_coverage_dashboard_local_cycle_workspace_card_dashboard_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["material_coverage_run_local_cycle_workspace_card_coverage_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["material_coverage_run_local_cycle_workspace_card_coverage_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "6c44c96",
        )
        self.assertEqual(
            by_id["material_coverage_run_local_cycle_workspace_card_coverage_link_alignment"]["review_gate"],
            "material_coverage_run_local_cycle_workspace_card_coverage_link_traceability",
        )
        self.assertIn(
            "unibot/material_coverage_run.py",
            by_id["material_coverage_run_local_cycle_workspace_card_coverage_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["private_tutor_use_flow_local_cycle_workspace_card_private_use_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["private_tutor_use_flow_local_cycle_workspace_card_private_use_link_alignment"]["closure_evidence"][
                "commit"
            ],
            "8142628",
        )
        self.assertEqual(
            by_id["private_tutor_use_flow_local_cycle_workspace_card_private_use_link_alignment"]["review_gate"],
            "private_tutor_use_flow_local_cycle_workspace_card_private_use_link_traceability",
        )
        self.assertIn(
            "unibot/private_tutor_use_flow.py",
            by_id["private_tutor_use_flow_local_cycle_workspace_card_private_use_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["study_session_local_cycle_workspace_card_study_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["study_session_local_cycle_workspace_card_study_link_alignment"]["closure_evidence"]["commit"],
            "99a6626",
        )
        self.assertEqual(
            by_id["study_session_local_cycle_workspace_card_study_link_alignment"]["review_gate"],
            "study_session_local_cycle_workspace_card_study_link_traceability",
        )
        self.assertIn(
            "unibot/study_session.py",
            by_id["study_session_local_cycle_workspace_card_study_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["notebook_checkpoint_local_cycle_workspace_card_checkpoint_receipt_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["notebook_checkpoint_local_cycle_workspace_card_checkpoint_receipt_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "da5e026",
        )
        self.assertEqual(
            by_id["notebook_checkpoint_local_cycle_workspace_card_checkpoint_receipt_link_alignment"]["review_gate"],
            "notebook_checkpoint_local_cycle_workspace_card_checkpoint_receipt_link_traceability",
        )
        self.assertIn(
            "unibot/exam_notebook_checkpoint.py",
            by_id["notebook_checkpoint_local_cycle_workspace_card_checkpoint_receipt_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_workspace_launch_local_cycle_workspace_card_launch_receipt_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_workspace_launch_local_cycle_workspace_card_launch_receipt_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "df68605",
        )
        self.assertEqual(
            by_id["exam_workspace_launch_local_cycle_workspace_card_launch_receipt_link_alignment"]["review_gate"],
            "exam_workspace_launch_local_cycle_workspace_card_launch_receipt_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_launch_flow.py",
            by_id["exam_workspace_launch_local_cycle_workspace_card_launch_receipt_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_workspace_run_local_cycle_workspace_card_run_receipt_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_workspace_run_local_cycle_workspace_card_run_receipt_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "ae66b36",
        )
        self.assertEqual(
            by_id["exam_workspace_run_local_cycle_workspace_card_run_receipt_link_alignment"]["review_gate"],
            "exam_workspace_run_local_cycle_workspace_card_run_receipt_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_run.py",
            by_id["exam_workspace_run_local_cycle_workspace_card_run_receipt_link_alignment"]["allowed_files"],
        )
        self.assertEqual(
            by_id["exam_workspace_run_history_local_cycle_workspace_card_history_receipt_link_alignment"]["status"],
            "closed_harnessed",
        )
        self.assertEqual(
            by_id["exam_workspace_run_history_local_cycle_workspace_card_history_receipt_link_alignment"][
                "closure_evidence"
            ]["commit"],
            "9da9539",
        )
        self.assertEqual(
            by_id["exam_workspace_run_history_local_cycle_workspace_card_history_receipt_link_alignment"]["review_gate"],
            "exam_workspace_run_history_local_cycle_workspace_card_history_receipt_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_run_history.py",
            by_id["exam_workspace_run_history_local_cycle_workspace_card_history_receipt_link_alignment"][
                "allowed_files"
            ],
        )
        self.assertEqual(
            by_id["exam_workspace_operator_run_local_cycle_workspace_card_operator_receipt_link_alignment"]["status"],
            "ready",
        )
        self.assertEqual(
            by_id["exam_workspace_operator_run_local_cycle_workspace_card_operator_receipt_link_alignment"][
                "review_gate"
            ],
            "exam_workspace_operator_run_local_cycle_workspace_card_operator_receipt_link_traceability",
        )
        self.assertIn(
            "unibot/exam_workspace_operator_run.py",
            by_id["exam_workspace_operator_run_local_cycle_workspace_card_operator_receipt_link_alignment"][
                "allowed_files"
            ],
        )
        self.assertEqual(
            loop["next_recommended_work_id"],
            "exam_workspace_operator_run_local_cycle_workspace_card_operator_receipt_link_alignment",
        )
        self.assertEqual(loop["receipt"]["closed_harnessed_work_items"], 105)
        self.assertEqual(loop["receipt"]["ready_work_items"], 1)
        self.assertLessEqual(loop["budget_policy"]["cadence"]["max_active_work_item_per_run"], 1)
        for item in queue:
            self.assertIn("acceptance_tests", item)
            self.assertTrue(item["acceptance_tests"])
            self.assertIn("review_gate", item)
            self.assertLessEqual(len(item["allowed_files"]), 4)

    def test_markdown_and_api_routes(self) -> None:
        markdown = build_autonomous_research_markdown()

        self.assertIn("# UniBot Gretel Autonomous Research Loop", markdown)
        self.assertIn("Public safety: pass", markdown)
        self.assertIn("Default reasoning effort: low", markdown)
        self.assertIn("Workspace-card gate linked: True", markdown)
        self.assertIn("Autonomous GitHub push: False", markdown)
        self.assertIn("Closed harnessed items: 105", markdown)
        self.assertIn(
            "Next recommended work: exam_workspace_operator_run_local_cycle_workspace_card_operator_receipt_link_alignment",
            markdown,
        )

        status, loop = route_request("/api/unibot/autonomous-research-loop", {})
        self.assertEqual(status, 200)
        self.assertEqual(loop["status"], "ready_for_budgeted_recurring_local_runs")

        status, response = route_request("/api/unibot/autonomous-research-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("North Star", response["markdown"])


if __name__ == "__main__":
    unittest.main()
