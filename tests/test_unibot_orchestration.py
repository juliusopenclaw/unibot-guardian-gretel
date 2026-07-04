from __future__ import annotations

import os
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.course_tutor import build_course_material_compiler_plan  # noqa: E402
from unibot.orchestration import (  # noqa: E402
    build_context_packet,
    build_command_center_workspace_card_route_alignment,
    build_orchestration_markdown,
    build_unibot_command_center,
    command_center_hash,
    command_center_route_hash,
    synthetic_command_center_workspace_card,
    validate_chat_handoff,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_orchestration_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text(
        "pandas DataFrame read_csv columns dtypes groupby boxplot",
        encoding="utf-8",
    )
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "lecture.mov").write_bytes(b"video")
    (root / "Week 1" / "solution_key.ipynb").write_text(
        json.dumps({"cells": [{"source": ["solution key"]}]}),
        encoding="utf-8",
    )


class UniBotOrchestrationTests(unittest.TestCase):
    def test_course_material_compiler_plan_builds_public_safe_queues(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_orchestration_fixture(fixture_root)

            compiler = build_course_material_compiler_plan(base_path=str(fixture_root), review_policy="staged")
            payload = json.dumps(compiler, ensure_ascii=False)

            self.assertEqual(compiler["artifact_type"], "course_material_compiler_plan")
            self.assertEqual(compiler["exam_deployment_status"], "not_cleared")
            self.assertEqual(compiler["public_safety_status"], "pass")
            self.assertEqual(compiler["counts"]["record_count"], 4)
            self.assertEqual(compiler["counts"]["review_ready_count"], 1)
            self.assertEqual(compiler["counts"]["ocr_queue_count"], 1)
            self.assertEqual(compiler["counts"]["transcription_queue_count"], 1)
            self.assertEqual(compiler["counts"]["solution_or_exam_quarantine_count"], 1)
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(scan_text(payload, "compiler-plan-test")["status"], "pass")

    def test_command_center_contains_roles_gates_and_scope_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_orchestration_fixture(fixture_root)

            center = build_unibot_command_center(base_path=str(fixture_root), review_policy="local_private_tutor")
            payload = json.dumps(center, ensure_ascii=False)

            self.assertEqual(center["artifact_type"], "unibot_orchestration_command_center")
            self.assertEqual(center["status"], "ready_to_orchestrate")
            self.assertEqual(center["deployment_line"]["exam_deployment_status"], "not_cleared")
            self.assertGreaterEqual(len(center["role_lanes"]), 7)
            self.assertIn("project_management", center["golden_rules"])
            self.assertGreaterEqual(center["scope_status"]["ready_skill_count"], 1)
            self.assertIn("pipeline smoke passes", center["acceptance_gates"])
            self.assertIn(
                "POST /api/unibot/course/extraction-batch-receipt-packet",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/private-extraction/run-batch",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/video-transcription/run-batch",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/extraction-manifest-update-plan",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/extraction-receipts/append",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/extraction-receipts/summary",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/extraction-deferral/validate",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/extraction-completion-report",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/tutor-coverage-plan",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/study-session-plan",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/study-session-receipt/validate",
                center["active_harnesses"][0]["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/study-session-review-report",
                center["active_harnesses"][0]["sequence"],
            )
            exam_workspace_harness = next(
                item for item in center["active_harnesses"] if item["harness_id"] == "exam_workspace_run"
            )
            self.assertIn(
                "POST /api/unibot/exam-workspace/run-dry-run",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/exam-workspace/launch-flow/dry-run",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/skill-to-workspace-live-flow",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/skill-to-workspace-session-carryover",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-source-grounded-tutor-drill-pack",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-drill-session-runner",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-drill-session-review-loop",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-drill-loop-control-panel",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-drill-loop-progress-journal",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-resume-launcher",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-active-study-loop-dashboard",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-active-study-guided-runner",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-guided-action-execution-bridge",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-safe-cycle-console",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-safe-cycle-operator-gate",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-operator-gate-decision-receipt",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-local-cycle-start-packet",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-local-cycle-readiness-review",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-local-cycle-readiness-handoff",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-local-cycle-operator-workspace-card",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-local-cycle-chain-snapshot",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-local-cycle-manual-confirmation-console",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-cycle-launch-receipt",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "P1 Local Cycle Operator Workspace Card and manual cycle preview",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Confirmation Console for local cycle stop-go review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Cycle Launch Receipt for final local-cycle stop-go evidence",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Cycle Evidence Binder for hash-only pre/post cycle review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Post-Cycle Receipt Intake for human-run hash evidence",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Cycle Closure Ledger for hash-only cycle closure",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Cycle Review Timeline for chronological hash review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Cycle Review Packet for compact human review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Review Export Preview without export write",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Review Export Authorization Gate before export review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Export Review Queue for hash-only candidate review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Export Reviewer Packet for human review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Archive Decision Draft without archive or submission",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Final Review Handoff before any export archive or submission",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Manual Final Review Receipt Ledger for chronological hash review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Final Review Ledger Integrity Gate before export archive or submission proximity",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Final Manual Review Console for one human-readable hash-only view",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Final Manual Review Action Lock before export archive or submission proximity",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Locked Final Review Board for one final human hash-only review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Locked Final Review Gap Resolver for one safe human follow-up",
                center["workstream_sequence"],
            )
            self.assertIn(
                "POST /api/unibot/exam-workspace/notebook-checkpoint/adapt",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-cycle-evidence-binder",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-post-cycle-receipt-intake",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-cycle-closure-ledger",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-cycle-review-timeline",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-cycle-review-packet",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-review-export-preview",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-review-export-authorization-gate",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-export-review-queue",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-export-reviewer-packet",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-archive-decision-draft",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-final-review-handoff",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-manual-final-review-receipt-ledger",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-final-review-ledger-integrity-gate",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-final-manual-review-console",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-final-manual-review-action-lock",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-locked-final-review-board",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-locked-final-review-gap-resolver",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/exam-workspace/operator-run",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/exam-workspace/session-console",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/exam-workspace/run-history-export-review",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/exam-coverage-dashboard",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/per-skill-action-router",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/routed-action-executor",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/exam-run-packet",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/exam-packet-timeline",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/timeline-export-review-packet",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/timeline-export-receipt-journal/append",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/timeline-export-receipt-journal/summary",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/review-chain-integrity-check",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-readiness-console",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-cockpit-flow",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-live-control-surface",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-evidence-export-preview",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-confirmed-local-export-draft",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-draft-package-review-console",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-full-local-rehearsal-pack",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-rehearsal-playback-gap-coach",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/python-exam-guided-loop-control-surface",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "P1 Rehearsal Playback Gap Coach for safe next-action selection",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Gap-Coach Guided Rehearsal Loop for next-step preparation",
                center["workstream_sequence"],
            )
            self.assertIn(
                "P1 Guided Loop Control Surface for visible next-click review",
                center["workstream_sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/material-coverage/run",
                exam_workspace_harness["sequence"],
            )
            self.assertIn(
                "POST /api/unibot/course/exam-skill-drilldown",
                exam_workspace_harness["sequence"],
            )
            self.assertIn("no raw query", exam_workspace_harness["boundary"])
            decision_harness = next(
                item for item in center["active_harnesses"] if item["harness_id"] == "external_decision_record_journal"
            )
            self.assertIn(
                "POST /api/unibot/stakeholder/decision-record-journal/append",
                decision_harness["sequence"],
            )
            self.assertIn("no exam deployment switch", decision_harness["boundary"])
            alignment = center["workspace_card_route_alignment"]
            self.assertEqual(
                alignment["schema_version"],
                "unibot-command-center-workspace-card-route-alignment-v1",
            )
            self.assertEqual(alignment["status"], "ready")
            self.assertEqual(alignment["alignment_public_safety_status"], "pass")
            self.assertEqual(alignment["failed_contract_ids"], [])
            self.assertEqual(alignment["command_center_hash"], command_center_hash(center))
            self.assertEqual(alignment["route_hash"], command_center_route_hash(center))
            self.assertEqual(alignment["command_center_status"], "ready_to_orchestrate")
            self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
            self.assertGreaterEqual(alignment["role_lane_count"], 7)
            self.assertGreaterEqual(alignment["active_harness_count"], 3)
            self.assertGreaterEqual(alignment["active_route_count"], 1)
            self.assertIn("orchestration_command_center", alignment["required_readiness_check_ids"])
            self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
            self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
            self.assertTrue(alignment["workspace_card_command_center_gate_linked"])
            self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
            self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
            self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
            self.assertFalse(alignment["raw_workspace_card_returned"])
            self.assertIn("exam deployment", alignment["blocked_claims"])
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(center["public_safety_status"], "pass")

    def test_command_center_workspace_card_alignment_rejects_unlinked_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_orchestration_fixture(fixture_root)
            center = build_unibot_command_center(base_path=str(fixture_root), review_policy="local_private_tutor")
            workspace_card = synthetic_command_center_workspace_card()
            workspace_card["workspace_card_summary"]["checkpoint_hash"] = "wrong-command-hash"
            workspace_card["workspace_card_summary"]["task_hash"] = "wrong-route-hash"

            alignment = build_command_center_workspace_card_route_alignment(center, workspace_card)

            self.assertEqual(alignment["status"], "blocked")
            self.assertIn("workspace_card_command_center_gate_linked", alignment["failed_contract_ids"])
            self.assertFalse(alignment["workspace_card_command_center_gate_linked"])
            self.assertFalse(alignment["raw_workspace_card_returned"])

    def test_command_center_uses_configured_course_material_root_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_orchestration_fixture(fixture_root)

            with patch.dict(os.environ, {"UNIBOT_COURSE_MATERIAL_ROOT": str(fixture_root)}, clear=False):
                center = build_unibot_command_center(review_policy="staged")

            self.assertEqual(center["material_status"]["record_count"], 4)
            self.assertEqual(center["material_status"]["review_ready_count"], 1)
            self.assertEqual(center["material_status"]["ocr_queue_count"], 1)
            self.assertEqual(center["material_status"]["transcription_queue_count"], 1)
            self.assertEqual(center["material_status"]["solution_or_exam_quarantine_count"], 1)
            self.assertEqual(center["scope_status"]["status"], "ok")
            self.assertEqual(center["scope_status"]["needs_review_skill_count"], 2)
            self.assertEqual(center["next_sprint"]["focus"], "Course Material Compiler")
            self.assertIn("increase reviewed source anchors", center["next_sprint"]["outcome"])

    def test_command_center_auto_promotes_local_course_root_when_review_policy_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_orchestration_fixture(fixture_root)

            with patch.dict(os.environ, {"UNIBOT_COURSE_MATERIAL_ROOT": str(fixture_root)}, clear=False):
                status, center = route_request("/api/unibot/orchestration/command-center", {})

        self.assertEqual(status, 200)
        self.assertEqual(center["material_status"]["review_ready_count"], 0)
        self.assertGreaterEqual(center["material_status"]["private_tutor_index_count"], 1)
        self.assertGreaterEqual(center["material_status"]["solution_or_exam_quarantine_count"], 1)
        self.assertGreaterEqual(center["scope_status"]["ready_skill_count"], 1)
        self.assertEqual(center["scope_status"]["needs_review_skill_count"], 0)
        self.assertEqual(center["deployment_line"]["exam_deployment_status"], "not_cleared")

    def test_context_packet_and_handoff_validation(self) -> None:
        packet = build_context_packet("exam_gateway")
        self.assertEqual(packet["artifact_type"], "unibot_context_packet")
        self.assertEqual(packet["role"]["role_id"], "exam_gateway")
        self.assertEqual(
            packet["mode_gates"]["exam_controlled_gateway"],
            "not_cleared; real-world authority clearance is a reminder, not a technical delivery blocker",
        )

        valid = validate_chat_handoff(
            {
                "role_id": "exam_gateway",
                "goal": "Expose the exam gateway through the local API.",
                "changed_files": ["unibot/server.py", "exam_mode.py"],
                "tests": ["python3 -m pytest tests/test_unibot_exam_gateway.py -q"],
                "risks": ["exam use stays blocked until written authority clearance"],
                "evidence": ["gateway E2E test"],
                "next_step": "run pipeline smoke",
            }
        )
        self.assertEqual(valid["status"], "ok")

        blocked = validate_chat_handoff(
            {
                "role_id": "exam_gateway",
                "goal": "Run a live external call.",
                "changed_files": ["unibot/server.py"],
                "tests": ["not run"],
                "risks": ["live external action"],
                "evidence": ["manual note"],
                "next_step": "continue",
                "external_live_action": True,
            }
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("external_live_action_requires_explicit_go", blocked["issues"])

    def test_orchestration_api_routes_and_markdown(self) -> None:
        status, center = route_request("/api/unibot/orchestration/command-center", {})
        self.assertEqual(status, 200)
        self.assertEqual(center["status"], "ready_to_orchestrate")
        self.assertEqual(center["workspace_card_route_alignment"]["status"], "ready")
        self.assertTrue(center["workspace_card_route_alignment"]["workspace_card_command_center_gate_linked"])

        status, packet = route_request("/api/unibot/orchestration/context-packet", {"role_id": "qa_redteam"})
        self.assertEqual(status, 200)
        self.assertEqual(packet["role"]["role_id"], "qa_redteam")

        status, validation = route_request(
            "/api/unibot/orchestration/handoff/validate",
            {
                "handoff": {
                    "role_id": "qa_redteam",
                    "goal": "Run smoke.",
                    "changed_files": ["scripts/unibot_pipeline_smoke.py"],
                    "tests": ["python3 scripts/unibot_pipeline_smoke.py --json"],
                    "risks": ["real exam use remains not cleared"],
                    "evidence": ["pipeline smoke"],
                    "next_step": "ship handoff",
                }
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(validation["status"], "ok")

        status, markdown = route_request("/api/unibot/orchestration/command-center-markdown", {})
        self.assertEqual(status, 200)
        self.assertIn("# UniBot Command Center", markdown["markdown"])
        self.assertIn("Exam deployment: not_cleared", markdown["markdown"])
        self.assertIn("Workspace-card gate linked: True", markdown["markdown"])
        self.assertIn("# UniBot Command Center", build_orchestration_markdown())


if __name__ == "__main__":
    unittest.main()
