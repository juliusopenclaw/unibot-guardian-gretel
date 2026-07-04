from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.public_safety import scan_text  # noqa: E402
from unibot.release_runbook import (  # noqa: E402
    build_release_runbook,
    build_release_runbook_evidence_alignment,
    build_release_runbook_markdown,
    release_runbook_evidence_hash,
    release_runbook_gate_hash,
    synthetic_release_runbook_workspace_card,
)
from unibot.server import route_request  # noqa: E402


class UniBotReleaseRunbookTests(unittest.TestCase):
    def test_release_runbook_has_public_draft_boundary(self) -> None:
        runbook = build_release_runbook()

        self.assertEqual(runbook["schema_version"], "unibot-release-runbook-v1")
        self.assertEqual(runbook["status"], "public_draft_runbook_not_exam_release")
        self.assertTrue(runbook["manual_review_required"])
        self.assertEqual(runbook["exam_deployment_status"], "not_cleared")
        self.assertIn("exam deployment", runbook["not_ready_for"])
        self.assertIn("public draft review", runbook["ready_for"])
        self.assertEqual(runbook["release_evidence_alignment"]["status"], "ready")
        self.assertEqual(runbook["release_evidence_alignment"]["public_safety_status"], "pass")
        self.assertEqual(runbook["release_evidence_alignment"]["unmapped_gate_ids"], [])
        self.assertEqual(runbook["release_evidence_alignment"]["missing_review_board_thesis_evaluation_check_ids"], [])
        self.assertEqual(runbook["release_evidence_alignment"]["missing_review_board_thesis_evaluation_human_gates"], [])
        self.assertTrue(runbook["release_evidence_alignment"]["workspace_card_release_runbook_gate_linked"])

    def test_release_runbook_evidence_alignment_maps_gates_to_review_contracts(self) -> None:
        runbook = build_release_runbook()
        alignment = build_release_runbook_evidence_alignment(runbook["release_gates"])
        by_gate = {item["gate_id"]: item for item in alignment["release_gates"]}

        self.assertEqual(alignment["schema_version"], "unibot-release-runbook-evidence-alignment-v1")
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["release_gate_count"], len(runbook["release_gates"]))
        self.assertEqual(alignment["unmapped_gate_ids"], [])
        self.assertIn("unibot-readiness-evidence-snapshot-v1", alignment["readiness_snapshot_contract"]["expected_schema_version"])
        self.assertIn("unibot-review-board-evidence-alignment-v1", alignment["review_board_contract"]["expected_schema_version"])
        self.assertEqual(
            alignment["review_board_thesis_evaluation_claim_contract"]["expected_schema_version"],
            "unibot-review-board-thesis-evaluation-claim-alignment-v1",
        )
        self.assertEqual(alignment["review_board_thesis_evaluation_claim_contract"]["required_status"], "ready")
        self.assertIn("unibot-github-issue-evidence-traceability-v1", alignment["github_issue_contract"]["expected_schema_version"])
        self.assertTrue(alignment["github_issue_contract"]["manual_publish_only"])
        self.assertIn("public_safety", by_gate["public_safety_scan"]["readiness_check_ids"])
        self.assertIn("review_board_packet", by_gate["exam_authority_clearance"]["readiness_check_ids"])
        self.assertIn("gretel_bachelor_thesis_package", by_gate["exam_authority_clearance"]["readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["review_board_thesis_evaluation_claim_contract"]["required_readiness_check_ids"])
        self.assertIn("adaptive_task_plan", alignment["review_board_thesis_evaluation_claim_contract"]["required_readiness_check_ids"])
        self.assertIn(
            "python_exam_local_cycle_operator_workspace_card",
            alignment["review_board_thesis_evaluation_claim_contract"]["required_readiness_check_ids"],
        )
        self.assertIn("python_exam_local_cycle_operator_workspace_card", by_gate["readiness_check"]["readiness_check_ids"])
        self.assertIn("github_issue_bundle", by_gate["github_issue_manual_review"]["readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("public_safety_required", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "pandas")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_release_runbook_gate_linked"])

    def test_release_runbook_hash_helpers_link_gates_and_evidence(self) -> None:
        runbook = build_release_runbook()
        alignment = runbook["release_evidence_alignment"]

        self.assertTrue(release_runbook_gate_hash(runbook["release_gates"]))
        self.assertTrue(release_runbook_evidence_hash(alignment["release_gates"]))
        self.assertNotEqual(release_runbook_gate_hash(runbook["release_gates"]), release_runbook_evidence_hash(alignment["release_gates"]))

    def test_release_runbook_evidence_alignment_rejects_unlinked_workspace_card_hashes(self) -> None:
        runbook = build_release_runbook()
        card = synthetic_release_runbook_workspace_card()
        card["workspace_card_summary"]["checkpoint_hash"] = "wrong-release-gate-hash"
        card["workspace_card_summary"]["task_hash"] = "wrong-release-evidence-hash"

        alignment = build_release_runbook_evidence_alignment(runbook["release_gates"], card)

        self.assertEqual(alignment["status"], "blocked")
        self.assertFalse(alignment["workspace_card_release_runbook_gate_linked"])
        self.assertEqual(
            alignment["workspace_card_release_runbook_gate_issue"],
            "release runbook gate/evidence hashes are not linked to workspace-card readiness",
        )

    def test_quickstart_and_contributor_rules_cover_public_workflow(self) -> None:
        runbook = build_release_runbook()
        payload = json.dumps(runbook, ensure_ascii=False)

        self.assertIn("python3 -m unibot.server", payload)
        self.assertIn("/api/unibot/health", payload)
        self.assertIn("unibot/browser_extension", payload)
        self.assertIn("/api/unibot/readiness-check", payload)
        self.assertIn("/api/unibot/github-issue-bundle", payload)
        self.assertIn("/api/unibot/stakeholder/decision-request", payload)
        self.assertIn("/api/unibot/stakeholder/decision-request-markdown", payload)
        self.assertIn("/api/unibot/stakeholder/decision-request/validate-receipt", payload)
        self.assertIn("/api/unibot/stakeholder/decision-journal/summary", payload)
        self.assertIn("/api/unibot/stakeholder/decision-record-journal/append", payload)
        self.assertIn("/api/unibot/stakeholder/decision-record-journal/summary", payload)
        self.assertIn("/api/unibot/course/extraction-batch-plan", payload)
        self.assertIn("/api/unibot/course/private-extraction/run-batch", payload)
        self.assertIn("/api/unibot/course/video-transcription/run-batch", payload)
        self.assertIn("/api/unibot/course/extraction-receipts/append", payload)
        self.assertIn("/api/unibot/course/extraction-receipts/summary", payload)
        self.assertIn("/api/unibot/course/extraction-review/validate", payload)
        self.assertIn("/api/unibot/course/extraction-review/apply-plan", payload)
        self.assertIn("/api/unibot/course/extraction-manifest/apply-dry-run", payload)
        self.assertIn("/api/unibot/course/tutor-index/dry-run", payload)
        self.assertIn("/api/unibot/course/tutor-index/respond-dry-run", payload)
        self.assertIn("/api/unibot/course/private-tutor-use-flow/dry-run", payload)
        self.assertIn("/api/unibot/exam-workspace/notebook-checkpoint/adapt", payload)
        self.assertIn("/api/unibot/exam-workspace/operator-run", payload)
        self.assertIn("/api/unibot/exam-workspace/session-console", payload)
        self.assertIn("/api/unibot/exam-workspace/run-history-export-review", payload)
        self.assertIn("/api/unibot/course/exam-coverage-dashboard", payload)
        self.assertIn("/api/unibot/course/per-skill-action-router", payload)
        self.assertIn("/api/unibot/course/routed-action-executor", payload)
        self.assertIn("/api/unibot/course/exam-run-packet", payload)
        self.assertIn("/api/unibot/course/exam-packet-timeline", payload)
        self.assertIn("/api/unibot/course/timeline-export-review-packet", payload)
        self.assertIn("/api/unibot/course/timeline-export-receipt-journal/append", payload)
        self.assertIn("/api/unibot/course/timeline-export-receipt-journal/summary", payload)
        self.assertIn("/api/unibot/course/review-chain-integrity-check", payload)
        self.assertIn("/api/unibot/course/python-exam-readiness-console", payload)
        self.assertIn("/api/unibot/course/python-exam-cockpit-flow", payload)
        self.assertIn("/api/unibot/course/python-exam-live-control-surface", payload)
        self.assertIn("/api/unibot/course/python-exam-evidence-export-preview", payload)
        self.assertIn("/api/unibot/course/python-exam-confirmed-local-export-draft", payload)
        self.assertIn("/api/unibot/course/python-exam-draft-package-review-console", payload)
        self.assertIn("/api/unibot/exam-workspace/run-dry-run", payload)
        self.assertIn("/api/unibot/course/material-coverage/run", payload)
        self.assertIn("/api/unibot/course/exam-skill-drilldown", payload)
        self.assertIn("/api/unibot/course/skill-to-workspace-live-flow", payload)
        self.assertIn("/api/unibot/course/skill-to-workspace-session-carryover", payload)
        self.assertIn("/api/unibot/course/python-exam-source-grounded-tutor-drill-pack", payload)
        self.assertIn("/api/unibot/course/python-exam-drill-session-runner", payload)
        self.assertIn("/api/unibot/course/python-exam-drill-session-review-loop", payload)
        self.assertIn("/api/unibot/course/python-exam-drill-loop-control-panel", payload)
        self.assertIn("/api/unibot/course/python-exam-drill-loop-progress-journal", payload)
        self.assertIn("/api/unibot/course/python-exam-resume-launcher", payload)
        self.assertIn("/api/unibot/course/python-exam-active-study-loop-dashboard", payload)
        self.assertIn("/api/unibot/course/python-exam-active-study-guided-runner", payload)
        self.assertIn("/api/unibot/course/python-exam-guided-action-execution-bridge", payload)
        self.assertIn("/api/unibot/course/python-exam-safe-cycle-console", payload)
        self.assertIn("/api/unibot/course/python-exam-safe-cycle-operator-gate", payload)
        self.assertIn("/api/unibot/course/python-exam-operator-gate-decision-receipt", payload)
        self.assertIn("/api/unibot/course/python-exam-local-cycle-start-packet", payload)
        self.assertIn("/api/unibot/course/python-exam-local-cycle-operator-workspace-card", payload)
        self.assertIn("/api/unibot/course/python-exam-local-cycle-readiness-handoff", payload)
        self.assertIn("review_python_exam_local_cycle_operator_workspace_card", payload)
        self.assertIn("/api/unibot/course/python-exam-full-local-rehearsal-pack", payload)
        self.assertIn("/api/unibot/course/python-exam-rehearsal-playback-gap-coach", payload)
        self.assertIn("review_python_exam_rehearsal_playback_gap_coach", payload)
        self.assertIn("/api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop", payload)
        self.assertIn("run_python_exam_gap_coach_guided_rehearsal_loop", payload)
        self.assertIn("/api/unibot/course/python-exam-guided-loop-control-surface", payload)
        self.assertIn("review_python_exam_guided_loop_control_surface", payload)
        self.assertIn("review_python_exam_local_cycle_manual_confirmation_console", payload)
        self.assertIn("/api/unibot/course/python-exam-local-cycle-manual-confirmation-console", payload)
        self.assertIn("review_python_exam_manual_cycle_launch_receipt", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-cycle-launch-receipt", payload)
        self.assertIn("review_python_exam_manual_cycle_evidence_binder", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-cycle-evidence-binder", payload)
        self.assertIn("review_python_exam_manual_post_cycle_receipt_intake", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-post-cycle-receipt-intake", payload)
        self.assertIn("review_python_exam_manual_cycle_closure_ledger", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-cycle-closure-ledger", payload)
        self.assertIn("review_python_exam_manual_cycle_review_timeline", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-cycle-review-timeline", payload)
        self.assertIn("review_python_exam_manual_cycle_review_packet", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-cycle-review-packet", payload)
        self.assertIn("review_python_exam_manual_review_export_preview", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-review-export-preview", payload)
        self.assertIn("review_python_exam_manual_review_export_authorization_gate", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-review-export-authorization-gate", payload)
        self.assertIn("review_python_exam_manual_export_review_queue", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-export-review-queue", payload)
        self.assertIn("review_python_exam_manual_export_reviewer_packet", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-export-reviewer-packet", payload)
        self.assertIn("review_python_exam_manual_archive_decision_draft", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-archive-decision-draft", payload)
        self.assertIn("review_python_exam_manual_final_review_handoff", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-final-review-handoff", payload)
        self.assertIn("review_python_exam_manual_final_review_receipt_ledger", payload)
        self.assertIn("/api/unibot/course/python-exam-manual-final-review-receipt-ledger", payload)
        self.assertIn("review_python_exam_final_review_ledger_integrity_gate", payload)
        self.assertIn("/api/unibot/course/python-exam-final-review-ledger-integrity-gate", payload)
        self.assertIn("review_python_exam_final_manual_review_console", payload)
        self.assertIn("/api/unibot/course/python-exam-final-manual-review-console", payload)
        self.assertIn("review_python_exam_final_manual_review_action_lock", payload)
        self.assertIn("/api/unibot/course/python-exam-final-manual-review-action-lock", payload)
        self.assertIn("review_python_exam_locked_final_review_board", payload)
        self.assertIn("/api/unibot/course/python-exam-locked-final-review-board", payload)
        self.assertIn("review_python_exam_locked_final_review_gap_resolver", payload)
        self.assertIn("/api/unibot/course/python-exam-locked-final-review-gap-resolver", payload)
        self.assertIn("/api/unibot/exam-workspace/launch-flow/dry-run", payload)
        self.assertIn("/api/unibot/course/extraction-deferral/validate", payload)
        self.assertIn("/api/unibot/course/extraction-completion-report", payload)
        self.assertIn("/api/unibot/course/extraction-manifest-update-plan", payload)
        self.assertIn("/api/unibot/course/tutor-coverage-plan", payload)
        self.assertIn("/api/unibot/course/study-session-plan", payload)
        self.assertIn("/api/unibot/course/study-session-receipt/validate", payload)
        self.assertIn("/api/unibot/course/study-session-review-report", payload)
        self.assertIn("Eigenleistung percentages", payload)
        self.assertIn("synthetic tasks", payload)
        self.assertIn("manual review", payload)

    def test_markdown_and_api_routes(self) -> None:
        markdown = build_release_runbook_markdown()

        self.assertIn("# UniBot Release And Contributor Runbook", markdown)
        self.assertIn("Exam deployment: not_cleared", markdown)
        self.assertIn("Contributor Rules", markdown)
        self.assertIn("Release Gates", markdown)
        self.assertIn("Release Evidence Alignment", markdown)
        self.assertIn("Snapshot schema", markdown)
        self.assertIn("Review-board thesis/evaluation schema", markdown)

        status, runbook = route_request("/api/unibot/release-runbook", {})
        self.assertEqual(status, 200)
        self.assertEqual(runbook["schema_version"], "unibot-release-runbook-v1")

        status, response = route_request("/api/unibot/release-runbook-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Troubleshooting", response["markdown"])

    def test_release_runbook_is_public_safe(self) -> None:
        payload = json.dumps(build_release_runbook(), ensure_ascii=False)

        self.assertEqual(scan_text(payload, "release-runbook")["status"], "pass")
        self.assertNotIn("raw_external_ai_output", payload)
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("official_grade", payload)
        self.assertNotIn("approved for exam", payload.lower())


if __name__ == "__main__":
    unittest.main()
