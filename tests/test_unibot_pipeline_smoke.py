from __future__ import annotations

import os
import json
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "unibot_pipeline_smoke.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("unibot_pipeline_smoke", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load pipeline smoke module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class UniBotPipelineSmokeTests(unittest.TestCase):
    def test_isolated_unit_copy_has_local_git_provenance(self) -> None:
        smoke = _load_smoke_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fixture.txt").write_text("synthetic", encoding="utf-8")
            ready, reason = smoke._initialize_isolated_git_repository(root)

            self.assertTrue(ready, reason)
            commit = subprocess.run(
                ["git", "rev-parse", "--verify", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            status = subprocess.run(
                ["git", "status", "--porcelain=v1"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(commit.returncode, 0)
        self.assertEqual(len(commit.stdout.strip()), 40)
        self.assertEqual(status.stdout.strip(), "")

    def test_smoke_script_emits_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            env = dict(os.environ)
            env["UNIBOT_EXAM_WORKSPACE_ROOT"] = temp_root
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--json"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload.get("status"), "pass")
        self.assertIsInstance(payload.get("checks"), list)
        self.assertEqual(len(payload.get("checks", [])), payload.get("check_count"))
        self.assertGreater(payload.get("check_count", 0), 0)
        self.assertEqual(payload.get("passed_count"), payload.get("check_count"))
        self.assertEqual(payload.get("failed_count"), 0)
        review_board = next(check for check in payload["checks"] if check["name"] == "review_board_packet_ready")
        self.assertIn("reviewers=", review_board["details"])
        self.assertIn("open_decisions=", review_board["details"])
        self.assertIn("exam=not_cleared", review_board["details"])
        clearance = next(check for check in payload["checks"] if check["name"] == "institutional_clearance_board")
        self.assertIn("scopes=", clearance["details"])
        self.assertIn("exam=not_cleared", clearance["details"])
        operator = next(check for check in payload["checks"] if check["name"] == "course_extraction_operator_packet")
        self.assertIn("decision=ok_authorizes_local_extraction", operator["details"])
        private_run = next(check for check in payload["checks"] if check["name"] == "private_extraction_run_batch")
        self.assertIn("extracted=3", private_run["details"])
        self.assertIn("stored=3", private_run["details"])
        private_ocr_run = next(check for check in payload["checks"] if check["name"] == "private_extraction_run_ocr_filter")
        self.assertIn("extracted=3", private_ocr_run["details"])
        self.assertIn("stored=3", private_ocr_run["details"])
        private_ocr_bridge = next(
            check for check in payload["checks"] if check["name"] == "private_extraction_run_ocr_journal_bridge"
        )
        self.assertIn("source=external_decision_record_journal", private_ocr_bridge["details"])
        self.assertIn("extracted=3", private_ocr_bridge["details"])
        self.assertIn("stored=3", private_ocr_bridge["details"])
        local_intake = next(
            check for check in payload["checks"] if check["name"] == "local_extraction_decision_intake_record"
        )
        self.assertIn("source=external_decision_record_journal", local_intake["details"])
        self.assertIn("ocr=3", local_intake["details"])
        local_intake_reports = next(
            check for check in payload["checks"] if check["name"] == "local_extraction_decision_intake_post_run_reports"
        )
        self.assertIn("progress=receipts_ready_for_human_review", local_intake_reports["details"])
        self.assertIn("manifest=waiting_for_reviewed_receipts", local_intake_reports["details"])
        workspace_prepare = next(
            check for check in payload["checks"] if check["name"] == "local_extraction_decision_workspace_prepare"
        )
        self.assertIn("dry_run=waiting_for_valid_decision_or_receipts", workspace_prepare["details"])
        self.assertIn("template=written", workspace_prepare["details"])
        workspace_record = next(
            check for check in payload["checks"] if check["name"] == "local_extraction_decision_workspace_record"
        )
        self.assertIn("dry_run=ocr_first_batch_1_start_ready", workspace_record["details"])
        self.assertIn("ocr_ready=True", workspace_record["details"])
        ocr_wait = next(
            check for check in payload["checks"] if check["name"] == "ocr_first_operator_waits_for_confirmation"
        )
        self.assertIn("started=False", ocr_wait["details"])
        ocr_run = next(
            check for check in payload["checks"] if check["name"] == "ocr_first_operator_run_reports"
        )
        self.assertIn("selected=3", ocr_run["details"])
        self.assertIn("stored=3", ocr_run["details"])
        self.assertIn("progress=receipts_ready_for_human_review", ocr_run["details"])
        human_review = next(
            check for check in payload["checks"] if check["name"] == "extraction_human_review_apply_plan"
        )
        self.assertIn("appended=3", human_review["details"])
        self.assertIn("ready_after=0", human_review["details"])
        self.assertIn("candidates=3", human_review["details"])
        manifest_apply = next(
            check for check in payload["checks"] if check["name"] == "private_manifest_apply_dry_run_and_confirmed_apply"
        )
        self.assertIn("dry=manifest_apply_dry_run_ready", manifest_apply["details"])
        self.assertIn("delta=3", manifest_apply["details"])
        self.assertIn("apply=private_manifest_applied", manifest_apply["details"])
        self.assertIn("applied=3", manifest_apply["details"])
        self.assertIn("indexing=False", manifest_apply["details"])
        tutor_index = next(
            check for check in payload["checks"] if check["name"] == "private_tutor_index_dry_run_and_confirmed_build"
        )
        self.assertIn("dry=tutor_index_dry_run_ready", tutor_index["details"])
        self.assertIn("anchors=", tutor_index["details"])
        self.assertIn("skills=", tutor_index["details"])
        self.assertIn("build=private_tutor_index_built", tutor_index["details"])
        self.assertIn("built=True", tutor_index["details"])
        index_response = next(
            check for check in payload["checks"] if check["name"] == "private_index_tutor_response_dry_run"
        )
        self.assertIn("result=allowed", index_response["details"])
        self.assertIn("anchors=", index_response["details"])
        self.assertIn("help=A2", index_response["details"])
        self.assertIn("raw_query=False", index_response["details"])
        tutor_flow = next(check for check in payload["checks"] if check["name"] == "private_tutor_use_flow_dry_run")
        self.assertIn("result=private_tutor_use_flow_ready_with_ledger", tutor_flow["details"])
        self.assertIn("tutor=allowed", tutor_flow["details"])
        self.assertIn("ledger=True", tutor_flow["details"])
        self.assertIn("receipt=ok_study_session_receipt", tutor_flow["details"])
        self.assertIn("raw_query=False", tutor_flow["details"])
        checkpoint = next(check for check in payload["checks"] if check["name"] == "exam_notebook_checkpoint_adapter")
        self.assertIn("result=notebook_checkpoint_ready", checkpoint["details"])
        self.assertIn("raw_cell=False", checkpoint["details"])
        operator_run = next(check for check in payload["checks"] if check["name"] == "exam_workspace_operator_run")
        self.assertIn("result=exam_workspace_operator_dry_run_ready", operator_run["details"])
        self.assertIn("view=ready_to_start_dry_run", operator_run["details"])
        self.assertIn("confirmations=0", operator_run["details"])
        session_console = next(check for check in payload["checks"] if check["name"] == "exam_workspace_session_console")
        self.assertIn("result=exam_workspace_session_console_ready", session_console["details"])
        self.assertIn("view=ready_dry_run", session_console["details"])
        self.assertIn("skill=python_lists", session_console["details"])
        run_history = next(check for check in payload["checks"] if check["name"] == "exam_workspace_run_history_export_review")
        self.assertIn("result=exam_workspace_run_history_export_review_ready", run_history["details"])
        self.assertIn("runs=", run_history["details"])
        self.assertIn("export=export_review_ready", run_history["details"])
        dashboard = next(check for check in payload["checks"] if check["name"] == "course_exam_coverage_dashboard")
        self.assertIn("result=course_exam_coverage_dashboard_ready", dashboard["details"])
        self.assertIn("skills=", dashboard["details"])
        self.assertIn("ready=", dashboard["details"])
        self.assertIn("history=", dashboard["details"])
        router = next(check for check in payload["checks"] if check["name"] == "course_per_skill_action_router")
        self.assertIn("result=course_per_skill_action_router_ready", router["details"])
        self.assertIn("skill=python_lists", router["details"])
        self.assertIn("route=review_open_operator_confirmations", router["details"])
        executor = next(check for check in payload["checks"] if check["name"] == "routed_action_executor")
        self.assertIn("result=routed_action_executor_ready", executor["details"])
        self.assertIn("route=review_open_operator_confirmations", executor["details"])
        self.assertIn("executed=exam_workspace_run_history_export_review", executor["details"])
        packet = next(check for check in payload["checks"] if check["name"] == "exam_run_packet")
        self.assertIn("result=exam_run_packet_ready", packet["details"])
        self.assertIn("skill=python_lists", packet["details"])
        self.assertIn("route=review_open_operator_confirmations", packet["details"])
        timeline = next(check for check in payload["checks"] if check["name"] == "exam_packet_timeline")
        self.assertIn("result=exam_packet_timeline_ready", timeline["details"])
        self.assertIn("skill=python_lists", timeline["details"])
        self.assertIn("events=", timeline["details"])
        export_review = next(check for check in payload["checks"] if check["name"] == "timeline_export_review_packet")
        self.assertIn("result=timeline_export_review_packet_ready", export_review["details"])
        self.assertIn("skill=python_lists", export_review["details"])
        self.assertIn("events=", export_review["details"])
        receipt_journal = next(check for check in payload["checks"] if check["name"] == "timeline_export_receipt_journal")
        self.assertIn("preview=write_preview_ready", receipt_journal["details"])
        self.assertIn("append=stored", receipt_journal["details"])
        self.assertIn("summary_records=1", receipt_journal["details"])
        chain_integrity = next(check for check in payload["checks"] if check["name"] == "review_chain_integrity")
        self.assertIn("result=review_chain_integrity_pass", chain_integrity["details"])
        self.assertIn("issues=0", chain_integrity["details"])
        readiness_console = next(check for check in payload["checks"] if check["name"] == "python_exam_readiness_console")
        self.assertIn("result=python_exam_readiness_console_ready", readiness_console["details"])
        self.assertIn("skill=python_lists", readiness_console["details"])
        self.assertIn("chain=review_chain_integrity_pass", readiness_console["details"])
        cockpit = next(check for check in payload["checks"] if check["name"] == "python_exam_cockpit_flow")
        self.assertIn("result=python_exam_cockpit_flow_ready", cockpit["details"])
        self.assertIn("steps=9/9", cockpit["details"])
        live_control = next(check for check in payload["checks"] if check["name"] == "python_exam_live_control_surface")
        self.assertIn("result=python_exam_live_control_surface_ready", live_control["details"])
        self.assertIn("actions=9/9", live_control["details"])
        evidence_preview = next(check for check in payload["checks"] if check["name"] == "python_exam_evidence_export_preview")
        self.assertIn("result=python_exam_evidence_export_preview_ready", evidence_preview["details"])
        self.assertIn("steps=9", evidence_preview["details"])
        self.assertIn("actions=9", evidence_preview["details"])
        tutor_drill = next(
            check for check in payload["checks"] if check["name"] == "python_exam_source_grounded_tutor_drill_pack"
        )
        self.assertIn("result=python_exam_source_grounded_tutor_drill_pack_ready", tutor_drill["details"])
        self.assertIn("skill=python_lists", tutor_drill["details"])
        self.assertIn("microtasks=", tutor_drill["details"])
        self.assertIn("drills=1/1", tutor_drill["details"])
        drill_session = next(check for check in payload["checks"] if check["name"] == "python_exam_drill_session_runner")
        self.assertIn("result=python_exam_drill_session_runner_ready", drill_session["details"])
        self.assertIn("skill=python_lists", drill_session["details"])
        self.assertIn("checkpoint=notebook_checkpoint_ready", drill_session["details"])
        self.assertIn("receipt=drill_session_receipt_ready_not_exam_clearance", drill_session["details"])
        drill_review = next(check for check in payload["checks"] if check["name"] == "python_exam_drill_session_review_loop")
        self.assertIn("result=python_exam_drill_session_review_loop_ready", drill_review["details"])
        self.assertIn("skill=python_lists", drill_review["details"])
        self.assertIn("next=run_next_microtask", drill_review["details"])
        self.assertIn("receipt=drill_session_review_loop_receipt_ready_not_exam_clearance", drill_review["details"])
        drill_panel = next(check for check in payload["checks"] if check["name"] == "python_exam_drill_loop_control_panel")
        self.assertIn("result=python_exam_drill_loop_control_panel_ready", drill_panel["details"])
        self.assertIn("skill=python_lists", drill_panel["details"])
        self.assertIn("next=run_next_microtask", drill_panel["details"])
        self.assertIn("cards=3", drill_panel["details"])
        drill_progress = next(
            check for check in payload["checks"] if check["name"] == "python_exam_drill_loop_progress_journal"
        )
        self.assertIn("result=write_preview_ready", drill_progress["details"])
        self.assertIn("skill=python_lists", drill_progress["details"])
        self.assertIn("resume=run_next_microtask", drill_progress["details"])
        self.assertIn("written=False", drill_progress["details"])
        resume_launcher = next(check for check in payload["checks"] if check["name"] == "python_exam_resume_launcher")
        self.assertIn("result=python_exam_resume_launcher_next_microtask_ready", resume_launcher["details"])
        self.assertIn("action=run_next_microtask", resume_launcher["details"])
        self.assertIn("skill=python_lists", resume_launcher["details"])
        self.assertIn("route=control_panel", resume_launcher["details"])
        active_loop = next(check for check in payload["checks"] if check["name"] == "python_exam_active_study_loop_dashboard")
        self.assertIn("result=python_exam_active_study_loop_dashboard_ready", active_loop["details"])
        self.assertIn("skill=python_lists", active_loop["details"])
        self.assertIn("next=run_next_microtask", active_loop["details"])
        self.assertIn("rows=", active_loop["details"])
        guided_runner = next(
            check for check in payload["checks"] if check["name"] == "python_exam_active_study_guided_runner"
        )
        self.assertIn("result=python_exam_active_study_guided_runner_ready", guided_runner["details"])
        self.assertIn("skill=python_lists", guided_runner["details"])
        self.assertIn("action=run_next_microtask", guided_runner["details"])
        self.assertIn("route=control_panel", guided_runner["details"])
        execution_bridge = next(
            check for check in payload["checks"] if check["name"] == "python_exam_guided_action_execution_bridge"
        )
        self.assertIn("result=python_exam_guided_action_execution_bridge_ready", execution_bridge["details"])
        self.assertIn("skill=python_lists", execution_bridge["details"])
        self.assertIn("action=run_next_microtask", execution_bridge["details"])
        self.assertIn("preview=control_panel_execution_preview_ready", execution_bridge["details"])
        safe_cycle = next(check for check in payload["checks"] if check["name"] == "python_exam_safe_cycle_console")
        self.assertIn("result=python_exam_safe_cycle_console_ready", safe_cycle["details"])
        self.assertIn("skill=python_lists", safe_cycle["details"])
        self.assertIn("cycle=safe_cycle_ready_for_operator_review", safe_cycle["details"])
        self.assertIn("next=run_next_microtask", safe_cycle["details"])
        operator_gate = next(check for check in payload["checks"] if check["name"] == "python_exam_safe_cycle_operator_gate")
        self.assertIn("result=python_exam_safe_cycle_operator_gate_ready", operator_gate["details"])
        self.assertIn("skill=python_lists", operator_gate["details"])
        self.assertIn("cards=5", operator_gate["details"])
        self.assertIn("confirmed=0", operator_gate["details"])
        decision_receipt = next(
            check for check in payload["checks"] if check["name"] == "python_exam_operator_gate_decision_receipt"
        )
        self.assertIn("result=python_exam_operator_gate_decision_receipt_ready", decision_receipt["details"])
        self.assertIn("skill=python_lists", decision_receipt["details"])
        self.assertIn("open=5", decision_receipt["details"])
        self.assertIn("next=open_control_panel", decision_receipt["details"])
        start_packet = next(check for check in payload["checks"] if check["name"] == "python_exam_local_cycle_start_packet")
        self.assertIn("result=python_exam_local_cycle_start_packet_ready", start_packet["details"])
        self.assertIn("skill=python_lists", start_packet["details"])
        self.assertIn("start=blocked_for_confirmation", start_packet["details"])
        self.assertIn("open=5", start_packet["details"])
        readiness_review = next(
            check for check in payload["checks"] if check["name"] == "python_exam_local_cycle_readiness_review"
        )
        self.assertIn("result=python_exam_local_cycle_readiness_review_ready", readiness_review["details"])
        self.assertIn("skill=python_lists", readiness_review["details"])
        self.assertIn("recommendation=request_missing_confirmation_review", readiness_review["details"])
        self.assertIn("start=blocked_for_confirmation", readiness_review["details"])
        manual_confirmation = next(
            check for check in payload["checks"] if check["name"] == "python_exam_local_cycle_manual_confirmation_console"
        )
        self.assertIn("result=python_exam_local_cycle_manual_confirmation_console_ready", manual_confirmation["details"])
        self.assertIn("skill=python_lists", manual_confirmation["details"])
        self.assertIn("next=review_missing_confirmation", manual_confirmation["details"])
        self.assertIn("open=5", manual_confirmation["details"])
        launch_receipt = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_cycle_launch_receipt"
        )
        self.assertIn("result=python_exam_manual_cycle_launch_receipt_ready", launch_receipt["details"])
        self.assertIn("skill=python_lists", launch_receipt["details"])
        self.assertIn("decision=stay_in_confirmation_review", launch_receipt["details"])
        self.assertIn("open=5", launch_receipt["details"])
        evidence_binder = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_cycle_evidence_binder"
        )
        self.assertIn("result=python_exam_manual_cycle_evidence_binder_ready", evidence_binder["details"])
        self.assertIn("skill=python_lists", evidence_binder["details"])
        self.assertIn("action=continue_confirmation_review", evidence_binder["details"])
        self.assertIn("open=5", evidence_binder["details"])
        post_cycle_intake = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_post_cycle_receipt_intake"
        )
        self.assertIn("result=python_exam_manual_post_cycle_receipt_intake_ready", post_cycle_intake["details"])
        self.assertIn("skill=python_lists", post_cycle_intake["details"])
        self.assertIn("recommendation=keep_post_cycle_review_open", post_cycle_intake["details"])
        self.assertIn("metadata=post_cycle_hash_metadata_missing", post_cycle_intake["details"])
        closure_ledger = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_cycle_closure_ledger"
        )
        self.assertIn("result=python_exam_manual_cycle_closure_ledger_ready", closure_ledger["details"])
        self.assertIn("skill=python_lists", closure_ledger["details"])
        self.assertIn("decision=keep_cycle_open", closure_ledger["details"])
        self.assertIn("post=keep_post_cycle_review_open", closure_ledger["details"])
        review_timeline = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_cycle_review_timeline"
        )
        self.assertIn("result=python_exam_manual_cycle_review_timeline_ready", review_timeline["details"])
        self.assertIn("skill=python_lists", review_timeline["details"])
        self.assertIn("recommendation=continue_cycle_review", review_timeline["details"])
        self.assertIn("events=5", review_timeline["details"])
        review_packet = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_cycle_review_packet"
        )
        self.assertIn("result=python_exam_manual_cycle_review_packet_ready", review_packet["details"])
        self.assertIn("skill=python_lists", review_packet["details"])
        self.assertIn("recommendation=keep_review_packet_open", review_packet["details"])
        self.assertIn("timeline=continue_cycle_review", review_packet["details"])
        export_preview = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_review_export_preview"
        )
        self.assertIn("result=python_exam_manual_review_export_preview_ready", export_preview["details"])
        self.assertIn("skill=python_lists", export_preview["details"])
        self.assertIn("recommendation=keep_export_preview_open", export_preview["details"])
        self.assertIn("export_created=False", export_preview["details"])
        authorization_gate = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_review_export_authorization_gate"
        )
        self.assertIn("result=python_exam_manual_review_export_authorization_gate_ready", authorization_gate["details"])
        self.assertIn("skill=python_lists", authorization_gate["details"])
        self.assertIn("decision=keep_export_blocked", authorization_gate["details"])
        self.assertIn("export_created=False", authorization_gate["details"])
        export_review_queue = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_export_review_queue"
        )
        self.assertIn("result=python_exam_manual_export_review_queue_ready", export_review_queue["details"])
        self.assertIn("skill=python_lists", export_review_queue["details"])
        self.assertIn("recommendation=keep_queue_open", export_review_queue["details"])
        self.assertIn("export_created=False", export_review_queue["details"])
        export_reviewer_packet = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_export_reviewer_packet"
        )
        self.assertIn("result=python_exam_manual_export_reviewer_packet_ready", export_reviewer_packet["details"])
        self.assertIn("skill=python_lists", export_reviewer_packet["details"])
        self.assertIn("recommendation=keep_reviewer_packet_open", export_reviewer_packet["details"])
        self.assertIn("export_created=False", export_reviewer_packet["details"])
        archive_decision_draft = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_archive_decision_draft"
        )
        self.assertIn("result=python_exam_manual_archive_decision_draft_ready", archive_decision_draft["details"])
        self.assertIn("skill=python_lists", archive_decision_draft["details"])
        self.assertIn("recommendation=keep_archive_decision_draft_open", archive_decision_draft["details"])
        self.assertIn("archive_created=False", archive_decision_draft["details"])
        final_review_handoff = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_final_review_handoff"
        )
        self.assertIn("result=python_exam_manual_final_review_handoff_ready", final_review_handoff["details"])
        self.assertIn("skill=python_lists", final_review_handoff["details"])
        self.assertIn("recommendation=keep_final_handoff_open", final_review_handoff["details"])
        self.assertIn("archive_created=False", final_review_handoff["details"])
        final_review_receipt_ledger = next(
            check for check in payload["checks"] if check["name"] == "python_exam_manual_final_review_receipt_ledger"
        )
        self.assertIn(
            "result=python_exam_manual_final_review_receipt_ledger_ready",
            final_review_receipt_ledger["details"],
        )
        self.assertIn("skill=python_lists", final_review_receipt_ledger["details"])
        self.assertIn("recommendation=keep_final_ledger_open", final_review_receipt_ledger["details"])
        self.assertIn("events=5", final_review_receipt_ledger["details"])
        self.assertIn("archive_created=False", final_review_receipt_ledger["details"])
        final_review_integrity_gate = next(
            check for check in payload["checks"] if check["name"] == "python_exam_final_review_ledger_integrity_gate"
        )
        self.assertIn(
            "result=python_exam_final_review_ledger_integrity_gate_ready",
            final_review_integrity_gate["details"],
        )
        self.assertIn("skill=python_lists", final_review_integrity_gate["details"])
        self.assertIn("recommendation=keep_integrity_gate_open", final_review_integrity_gate["details"])
        self.assertIn("issues=", final_review_integrity_gate["details"])
        self.assertIn("archive_created=False", final_review_integrity_gate["details"])
        final_manual_review_console = next(
            check for check in payload["checks"] if check["name"] == "python_exam_final_manual_review_console"
        )
        self.assertIn(
            "result=python_exam_final_manual_review_console_ready",
            final_manual_review_console["details"],
        )
        self.assertIn("skill=python_lists", final_manual_review_console["details"])
        self.assertIn("recommendation=keep_final_console_open", final_manual_review_console["details"])
        self.assertIn("archive_created=False", final_manual_review_console["details"])
        final_manual_review_action_lock = next(
            check for check in payload["checks"] if check["name"] == "python_exam_final_manual_review_action_lock"
        )
        self.assertIn(
            "result=python_exam_final_manual_review_action_lock_ready",
            final_manual_review_action_lock["details"],
        )
        self.assertIn("skill=python_lists", final_manual_review_action_lock["details"])
        self.assertIn("recommendation=keep_action_locked", final_manual_review_action_lock["details"])
        self.assertIn("archive_created=False", final_manual_review_action_lock["details"])
        locked_final_review_board = next(
            check for check in payload["checks"] if check["name"] == "python_exam_locked_final_review_board"
        )
        self.assertIn(
            "result=python_exam_locked_final_review_board_ready",
            locked_final_review_board["details"],
        )
        self.assertIn("skill=python_lists", locked_final_review_board["details"])
        self.assertIn("recommendation=keep_final_board_open", locked_final_review_board["details"])
        self.assertIn("archive_created=False", locked_final_review_board["details"])
        export_draft_preview = next(
            check for check in payload["checks"] if check["name"] == "python_exam_confirmed_local_export_draft_preview"
        )
        self.assertIn("result=python_exam_confirmed_local_export_draft_preview_ready", export_draft_preview["details"])
        self.assertIn("written=False", export_draft_preview["details"])
        export_draft_write = next(
            check for check in payload["checks"] if check["name"] == "python_exam_confirmed_local_export_draft_write"
        )
        self.assertIn("result=python_exam_confirmed_local_export_draft_written", export_draft_write["details"])
        self.assertIn("written=True", export_draft_write["details"])
        draft_review = next(
            check for check in payload["checks"] if check["name"] == "python_exam_draft_package_review_console"
        )
        self.assertIn("result=python_exam_draft_package_review_console_ready", draft_review["details"])
        self.assertIn("integrity=file_hash_integrity_pass", draft_review["details"])
        self.assertIn("draft=written", draft_review["details"])
        full_rehearsal = next(
            check for check in payload["checks"] if check["name"] == "python_exam_full_local_rehearsal_pack"
        )
        self.assertIn("result=python_exam_full_local_rehearsal_pack_ready", full_rehearsal["details"])
        self.assertIn("steps=12/12", full_rehearsal["details"])
        gap_coach = next(
            check for check in payload["checks"] if check["name"] == "python_exam_rehearsal_playback_gap_coach"
        )
        self.assertIn("result=python_exam_rehearsal_playback_gap_coach_ready", gap_coach["details"])
        self.assertIn("action=review_operator_confirmation", gap_coach["details"])
        guided_loop = next(
            check for check in payload["checks"] if check["name"] == "python_exam_gap_coach_guided_rehearsal_loop"
        )
        self.assertIn("result=python_exam_gap_coach_guided_rehearsal_loop_ready", guided_loop["details"])
        self.assertIn("action=review_operator_confirmation", guided_loop["details"])
        self.assertIn("route=operator_confirmation_review", guided_loop["details"])
        loop_surface = next(
            check for check in payload["checks"] if check["name"] == "python_exam_guided_loop_control_surface"
        )
        self.assertIn("result=python_exam_guided_loop_control_surface_ready", loop_surface["details"])
        self.assertIn("click=review_operator_confirmation_cards", loop_surface["details"])
        self.assertIn("route=operator_confirmation_review", loop_surface["details"])
        gap_resolver = next(
            check for check in payload["checks"] if check["name"] == "python_exam_locked_final_review_gap_resolver"
        )
        self.assertIn("result=python_exam_locked_final_review_gap_resolver_ready", gap_resolver["details"])
        self.assertIn("skill=python_lists", gap_resolver["details"])
        self.assertIn("recommendation=keep_gap_resolver_open", gap_resolver["details"])
        self.assertIn("layer=notebook_checkpoint_hash", gap_resolver["details"])
        self.assertIn("archive_created=False", gap_resolver["details"])
        drilldown = next(check for check in payload["checks"] if check["name"] == "exam_skill_drilldown")
        self.assertIn("result=exam_skill_drilldown_ready_for_workspace", drilldown["details"])
        self.assertIn("selected=python_lists", drilldown["details"])
        self.assertIn("action=ready", drilldown["details"])
        self.assertIn("live=ready_to_execute_operator_dry_run", drilldown["details"])
        skill_to_workspace = next(check for check in payload["checks"] if check["name"] == "skill_to_workspace_live_flow")
        self.assertIn("result=skill_to_workspace_live_flow_ready", skill_to_workspace["details"])
        self.assertIn("skill=python_lists", skill_to_workspace["details"])
        self.assertIn("operator=exam_workspace_operator_dry_run_ready", skill_to_workspace["details"])
        self.assertIn("confirmations=0", skill_to_workspace["details"])
        carryover = next(check for check in payload["checks"] if check["name"] == "skill_to_workspace_session_carryover")
        self.assertIn("result=skill_to_workspace_session_carryover_ready", carryover["details"])
        self.assertIn("session=exam_workspace_session_console_ready", carryover["details"])
        self.assertIn("evidence=python_exam_evidence_export_preview_ready", carryover["details"])
        self.assertIn("handoff=python_exam_human_handoff_packet_ready", carryover["details"])
        submission = next(check for check in payload["checks"] if check["name"] == "stakeholder_submission_bundle")
        self.assertIn("lanes=", submission["details"])
        self.assertIn("exam=not_cleared", submission["details"])
        request = next(check for check in payload["checks"] if check["name"] == "stakeholder_decision_request")
        self.assertIn("lane=rights_privacy_local_extraction", request["details"])
        self.assertIn("receipt=draft_not_sent", request["details"])
        request_markdown = next(check for check in payload["checks"] if check["name"] == "stakeholder_decision_request_markdown")
        self.assertIn("result=ok", request_markdown["details"])
        receipt = next(check for check in payload["checks"] if check["name"] == "stakeholder_decision_request_receipt")
        self.assertIn("result=ok_manual_request_receipt", receipt["details"])
        journal = next(check for check in payload["checks"] if check["name"] == "stakeholder_decision_journal")
        self.assertIn("events=2", journal["details"])
        self.assertIn("sent=1", journal["details"])
        decision_state = next(check for check in payload["checks"] if check["name"] == "external_decision_state")
        self.assertIn("exam=not_cleared", decision_state["details"])
        self.assertIn("deployment_go=True", decision_state["details"])
        decision_record_journal = next(
            check for check in payload["checks"] if check["name"] == "external_decision_record_journal"
        )
        self.assertIn("accepted=2", decision_record_journal["details"])
        self.assertIn("exam_deployment=not_cleared", decision_record_journal["details"])
        progress = next(check for check in payload["checks"] if check["name"] == "course_extraction_progress_report")
        self.assertIn("review=1", progress["details"])
        receipt_journal = next(check for check in payload["checks"] if check["name"] == "course_extraction_receipt_journal")
        self.assertIn("append=stored", receipt_journal["details"])
        self.assertIn("progress=1", receipt_journal["details"])
        completion = next(check for check in payload["checks"] if check["name"] == "course_extraction_completion_report")
        self.assertIn("deferral=ok_extraction_deferral_record", completion["details"])
        self.assertIn("completion=complete_intentionally_deferred", completion["details"])
        batch_plan = next(check for check in payload["checks"] if check["name"] == "course_extraction_batch_plan")
        self.assertIn("batches=", batch_plan["details"])
        batch_receipt = next(check for check in payload["checks"] if check["name"] == "course_extraction_batch_receipt_packet")
        self.assertIn("templates=", batch_receipt["details"])
        manifest_update = next(check for check in payload["checks"] if check["name"] == "course_extraction_manifest_update_plan")
        self.assertIn("ready=1", manifest_update["details"])
        coverage = next(check for check in payload["checks"] if check["name"] == "course_tutor_coverage_plan")
        self.assertIn("candidates=", coverage["details"])
        study = next(check for check in payload["checks"] if check["name"] == "course_study_session_plan")
        self.assertIn("tasks=", study["details"])
        study_receipt = next(check for check in payload["checks"] if check["name"] == "course_study_session_receipt_validation")
        self.assertIn("result=ok_study_session_receipt", study_receipt["details"])
        self.assertIn("raw_text=False", study_receipt["details"])
        study_review = next(check for check in payload["checks"] if check["name"] == "course_study_session_review_report")
        self.assertIn("valid=1", study_review["details"])


if __name__ == "__main__":
    unittest.main()
