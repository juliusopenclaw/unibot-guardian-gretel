from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .adaptive_tasks import generate_adaptive_practice_plan
from .autonomy_v3 import AutonomyStore, ProviderGate, WorkItemV3, autonomy_doctor
from .autonomous_research_loop import build_autonomous_research_loop, build_autonomous_research_markdown
from .bachelor_thesis import build_bachelor_thesis_markdown, build_bachelor_thesis_package
from .clearance import (
    build_institutional_clearance_board,
    build_institutional_presentation_markdown,
    build_institutional_presentation_packet,
    build_regulatory_profile,
    validate_clearance_record,
)
from .compliance import build_compliance_matrix, build_compliance_matrix_markdown
from .completion_audit import build_completion_audit
from .course_tutor import (
    build_course_exam_scope,
    build_course_material_compiler_plan,
    course_tutor_response,
    next_course_task,
    run_course_tutor_eval,
    scan_course_intake,
)
from .course_exam_coverage_dashboard import build_course_exam_coverage_dashboard
from .course_per_skill_action_router import build_course_per_skill_action_router
from .demo import build_local_demo_markdown, build_local_demo_run
from .decision_request import (
    build_stakeholder_decision_request,
    build_stakeholder_decision_request_markdown,
    validate_decision_request_receipt,
)
from .decision_journal import (
    append_decision_request_journal_event,
    append_prepared_request_to_journal,
    read_decision_journal,
    summarize_decision_journal,
)
from .decision_state import build_external_decision_state
from .evaluation import build_evaluation_markdown, build_evaluation_packet, synthetic_tasks
from .extraction_decision import build_extraction_decision_packet, validate_extraction_decision_record
from .extraction_decision_context import resolve_extraction_decision_context
from .extraction_decision_intake import (
    build_local_extraction_decision_intake_packet,
    record_local_extraction_decision_and_build_intake_packet,
)
from .extraction_decision_workspace import (
    prepare_local_extraction_decision_workspace,
    record_local_extraction_decision_workspace,
)
from .extraction import build_course_extraction_queue, build_extraction_run_manifest
from .extraction_batches import build_extraction_batch_plan, build_extraction_batch_receipt_packet
from .extraction_completion import build_extraction_completion_report, validate_extraction_deferral_record
from .extraction_human_review import (
    build_extraction_human_review_apply_plan,
    validate_extraction_human_review_decision,
)
from .extraction_manifest_apply import build_private_manifest_apply_dry_run
from .extraction_manifest_update import build_extraction_manifest_update_plan
from .extraction_operator import build_extraction_operator_packet, validate_extraction_receipt
from .extraction_progress import build_extraction_progress_report
from .exam_packet_timeline import build_exam_packet_timeline
from .exam_run_packet_builder import build_exam_run_packet
from .exam_notebook_checkpoint import build_exam_notebook_checkpoint_adapter_dry_run
from .exam_skill_drilldown import build_exam_skill_drilldown
from .exam_workspace_launch_flow import build_exam_workspace_launch_flow_dry_run
from .exam_workspace_operator_run import build_exam_workspace_operator_run_dry_run
from .exam_workspace_run import build_exam_workspace_run_dry_run
from .exam_workspace_run_history import build_exam_workspace_run_history_export_review
from .exam_workspace_session_console import build_exam_workspace_session_console
from .extraction_receipt_journal import (
    append_extraction_receipt_record,
    extraction_receipts_for_progress,
    read_extraction_receipt_journal,
    summarize_extraction_receipt_journal,
)
from .external_decision_journal import (
    append_external_decision_journal_record,
    read_external_decision_journal,
    summarize_external_decision_journal,
)
from .feedback import (
    append_demo_feedback,
    demo_feedback_template,
    export_public_demo_feedback_summary,
    read_demo_feedback,
    summarize_demo_feedback,
    validate_demo_feedback,
)
from .guardian import (
    classify_external_ai_output,
    generate_socratic_prompt_card,
    guardian_practice_flow,
)
from .github_issues import build_github_issue_bundle, build_github_issue_bundle_markdown
from .gretel_glm_evolve import (
    build_glm_evolve_markdown,
    build_glm_evolve_work_packet,
    build_glm_rsi_workboard,
    validate_glm_evolve_proposal,
)
from .handoff import build_authority_handoff_markdown, build_authority_handoff_packet
from .ledger import append_ledger_event, export_public_ledger_summary, read_ledger, summarize_ledger
from .learning_session import HELP_LEVELS_V1, LearningSession
from .loop_lab import run_loop_lab
from .material_coverage_run import build_course_material_coverage_run
from .materials import (
    build_demo_material_manifest,
    build_material_manifest,
    build_public_material_summary,
    normalize_material_record,
    validate_material_record,
)
from .notebooks import audit_practice_notebook, generate_practice_notebook
from .notebook_intake import NotebookIntakeError, import_notebook
from .ocr_first_operator import run_controlled_ocr_first_batch_1
from .orchestration import (
    build_context_packet,
    build_orchestration_markdown,
    build_unibot_command_center,
    validate_chat_handoff,
)
from .paperclip_evaluation_bridge import (
    build_paperclip_evaluation_markdown,
    build_paperclip_evaluation_request,
    paperclip_status,
    validate_paperclip_evaluation_request,
)
from .pilot import (
    build_controlled_pilot_clearance_receipt_template,
    build_controlled_pilot_launch_gate,
    build_pilot_protocol,
    build_pilot_protocol_markdown,
)
from .privacy import build_data_protection_screening, build_data_protection_screening_markdown
from .private_tutor_use_flow import build_private_tutor_use_flow_dry_run
from .private_extraction_runner import run_private_extraction_batch
from .video_transcription_runner import run_video_transcription_batch
from .review_board import build_review_board_packet, build_review_board_packet_markdown
from .publication import build_publication_markdown, build_publication_package
from .public_safety import scan_text
from .python_exam_cockpit_flow import build_python_exam_cockpit_flow
from .python_exam_confirmed_local_export_draft import build_python_exam_confirmed_local_export_draft
from .python_exam_draft_package_review_console import build_python_exam_draft_package_review_console
from .python_exam_evidence_export_preview import build_python_exam_evidence_export_preview
from .python_exam_full_local_rehearsal_pack import build_python_exam_full_local_rehearsal_pack
from .python_exam_guided_action_execution_bridge import build_python_exam_guided_action_execution_bridge
from .python_exam_human_handoff_packet import build_python_exam_human_handoff_packet
from .python_exam_live_control_surface import build_python_exam_live_control_surface
from .python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet
from .python_exam_local_cycle_chain_snapshot import build_python_exam_local_cycle_chain_snapshot
from .python_exam_local_cycle_manual_confirmation_console import (
    build_python_exam_local_cycle_manual_confirmation_console,
)
from .python_exam_local_cycle_operator_workspace_card import build_python_exam_local_cycle_operator_workspace_card
from .python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff
from .python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review
from .python_exam_manual_archive_decision_draft import build_python_exam_manual_archive_decision_draft
from .python_exam_manual_cycle_closure_ledger import build_python_exam_manual_cycle_closure_ledger
from .python_exam_manual_cycle_evidence_binder import build_python_exam_manual_cycle_evidence_binder
from .python_exam_manual_cycle_launch_receipt import build_python_exam_manual_cycle_launch_receipt
from .python_exam_manual_cycle_review_packet import build_python_exam_manual_cycle_review_packet
from .python_exam_manual_cycle_review_timeline import build_python_exam_manual_cycle_review_timeline
from .python_exam_manual_export_reviewer_packet import build_python_exam_manual_export_reviewer_packet
from .python_exam_manual_export_review_queue import build_python_exam_manual_export_review_queue
from .python_exam_manual_final_review_handoff import build_python_exam_manual_final_review_handoff
from .python_exam_manual_final_review_receipt_ledger import build_python_exam_manual_final_review_receipt_ledger
from .python_exam_manual_review_export_authorization_gate import (
    build_python_exam_manual_review_export_authorization_gate,
)
from .python_exam_manual_review_export_preview import build_python_exam_manual_review_export_preview
from .python_exam_manual_post_cycle_receipt_intake import build_python_exam_manual_post_cycle_receipt_intake
from .python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt
from .python_exam_gap_coach_guided_rehearsal_loop import build_python_exam_gap_coach_guided_rehearsal_loop
from .python_exam_guided_loop_control_surface import build_python_exam_guided_loop_control_surface
from .python_exam_guided_session_playback_journal import build_python_exam_guided_session_playback_journal
from .python_exam_final_review_ledger_integrity_gate import build_python_exam_final_review_ledger_integrity_gate
from .python_exam_final_manual_review_console import build_python_exam_final_manual_review_console
from .python_exam_final_manual_review_action_lock import build_python_exam_final_manual_review_action_lock
from .python_exam_locked_final_review_board import build_python_exam_locked_final_review_board
from .python_exam_locked_final_review_gap_resolver import build_python_exam_locked_final_review_gap_resolver
from .python_exam_rehearsal_playback_gap_coach import build_python_exam_rehearsal_playback_gap_coach
from .python_exam_readiness_console import build_python_exam_readiness_console
from .python_exam_active_study_guided_runner import build_python_exam_active_study_guided_runner
from .python_exam_active_study_loop_dashboard import build_python_exam_active_study_loop_dashboard
from .python_exam_drill_loop_control_panel import build_python_exam_drill_loop_control_panel
from .python_exam_drill_loop_progress_journal import (
    build_python_exam_drill_loop_progress_journal,
    summarize_python_exam_drill_loop_progress_journal,
)
from .python_exam_resume_launcher import build_python_exam_resume_launcher
from .python_exam_safe_cycle_console import build_python_exam_safe_cycle_console
from .python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate
from .python_exam_drill_session_runner import build_python_exam_drill_session_runner
from .python_exam_drill_session_review_loop import build_python_exam_drill_session_review_loop
from .python_exam_source_grounded_tutor_drill_pack import build_python_exam_source_grounded_tutor_drill_pack
from .readiness import build_readiness_markdown, run_readiness_check
from .release_runbook import build_release_runbook, build_release_runbook_markdown
from .redteam import run_redteam_smoke
from .routed_action_executor import build_routed_action_executor
from .simulation_loop import run_gretel_unibot_loop
from .skill_to_workspace_session_carryover import build_skill_to_workspace_session_carryover
from .skill_to_workspace_live_flow import build_skill_to_workspace_live_flow
from .source_cards import build_source_card_drift_report, get_source_card, list_source_cards
from .study_session import build_course_study_session_plan, build_study_session_review_report, validate_study_session_receipt
from .submission import build_stakeholder_submission_bundle, build_stakeholder_submission_markdown
from .timeline_export_receipt_journal import (
    build_timeline_export_receipt_journal_append,
    summarize_timeline_export_receipt_journal,
)
from .timeline_export_review_packet import build_timeline_export_review_packet
from .review_chain_integrity import build_review_chain_integrity_check
from .socratic_tutor import build_tutor_turn
from .triage import build_feedback_triage, build_feedback_triage_markdown
from .tutor_coverage import build_course_tutor_coverage_plan
from .tutor_index import build_private_index_tutor_response_dry_run, build_private_tutor_index_dry_run

from exam_mode import (
    append_exam_ledger_event,
    exam_tutor_response,
    export_exam_package,
    freeze_exam_materials,
    import_exam_materials,
    open_exam_notebook,
    run_exam_notebook_cell,
    start_exam_gateway_session,
)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_REQUEST_BODY_BYTES = 64 * 1024
PAIRING_TTL_SECONDS = 10 * 60
PAIRING_ATTEMPT_LIMIT = 5
CHROME_EXTENSION_ORIGIN = re.compile(r"^chrome-extension://[a-p]{32}$")


def payload_receipts_with_journal(payload: dict[str, Any], key: str = "receipts") -> tuple[list[dict[str, Any]] | None, str]:
    receipts = payload.get(key, [])
    if not isinstance(receipts, list):
        return None, f"invalid-{key.replace('_', '-')}"
    filtered = [item for item in receipts if isinstance(item, dict)]
    journal_path = payload.get("receipt_journal_path", payload.get("journal_path"))
    if journal_path:
        filtered.extend(extraction_receipts_for_progress(path=str(journal_path)))
    return filtered, ""


def route_request(path: str, payload: dict[str, Any] | None = None, method: str = "POST") -> tuple[int, dict[str, Any]]:
    parsed = urlparse(path)
    query_payload = {key: values[-1] for key, values in parse_qs(parsed.query).items() if values}
    payload = {**query_payload, **(payload or {})}
    path = parsed.path
    if method == "GET" and path in {"/health", "/api/unibot/health", "/api/v2/health"}:
        return 200, {
            "status": "ok",
            "service": "unibot-guardian-local",
            "storage": "local-only",
            "raw_output_policy": "hash-only by default",
            "api_version": "v2",
            "authentication": "one-time pairing and session token",
        }
    if path == "/api/v2/socratic/help":
        help_level = str(payload.get("help_level", payload.get("requested_help_level", "A2"))).upper()
        if help_level not in {"A0", "A1", "A2"}:
            return 400, {
                "status": "blocked-help-level",
                "allowed_help_levels": ["A0", "A1", "A2"],
                "exam_deployment_status": "not_cleared",
            }
        return 200, guardian_practice_flow(
            task=str(payload.get("task", "")),
            external_output=str(payload.get("external_output", "")),
            requested_help_level=help_level,
            mode="practice_overlay",
            tool=str(payload.get("tool", "browser_mantle_v2")),
            source_card_ids=list(payload.get("source_card_ids", []) or []),
            accessibility_used=bool(payload.get("accessibility_used", False)),
            approval_reference=None,
            student_reflection=str(payload.get("student_reflection", "")),
        )
    if path == "/api/v2/notebooks/import":
        source = str(payload.get("url", payload.get("source", ""))).strip()
        if not source.startswith("https://"):
            return 400, {"status": "public-https-url-required"}
        try:
            manifest = import_notebook(source, Path.cwd() / ".unibot" / "notebooks")
        except (NotebookIntakeError, FileExistsError) as exc:
            return 400, {"status": "notebook-import-blocked", "reason": str(exc)}
        return 200, dict(manifest)
    if path == "/api/v2/session/export":
        return 200, export_public_ledger_summary()
    if path == "/api/unibot/prompt-card":
        return 200, generate_socratic_prompt_card(
            task=str(payload.get("task", "")),
            tool=str(payload.get("tool", "colab_gemini")),
            mode=str(payload.get("mode", "practice_overlay")),
            source_card_ids=list(payload.get("source_card_ids", []) or []),
        )
    if path == "/api/unibot/review-output":
        return 200, classify_external_ai_output(
            external_output=str(payload.get("external_output", "")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            mode=str(payload.get("mode", "practice_overlay")),
            approval_reference=payload.get("approval_reference"),
        )
    if path == "/api/unibot/practice-flow":
        return 200, guardian_practice_flow(
            task=str(payload.get("task", "")),
            external_output=str(payload.get("external_output", "")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            mode=str(payload.get("mode", "practice_overlay")),
            tool=str(payload.get("tool", "colab_gemini")),
            source_card_ids=list(payload.get("source_card_ids", []) or []),
            accessibility_used=bool(payload.get("accessibility_used", False)),
            approval_reference=payload.get("approval_reference"),
            student_reflection=str(payload.get("student_reflection", "")),
        )
    if path == "/api/unibot/notebook-template":
        return 200, generate_practice_notebook(
            task=str(payload.get("task", "")),
            mode=str(payload.get("mode", "practice_overlay")),
            source_card_ids=list(payload.get("source_card_ids", []) or []),
            title=payload.get("title"),
        )
    if path == "/api/unibot/notebook/audit":
        notebook = payload.get("notebook")
        if not isinstance(notebook, dict):
            return 400, {"status": "invalid-notebook"}
        return 200, audit_practice_notebook(notebook)
    if path == "/api/unibot/ledger/append":
        event = payload.get("event")
        if not isinstance(event, dict):
            return 400, {"status": "invalid-event"}
        stored = append_ledger_event(event, path=payload.get("ledger_path"))
        return 200, {
            "status": stored["status"],
            "record": stored["record"],
            "storage": "local-only",
            "path": stored["path"],
        }
    if path == "/api/unibot/ledger/list":
        return 200, read_ledger(path=payload.get("ledger_path"), limit=payload.get("limit"))
    if path == "/api/unibot/ledger/summary":
        return 200, summarize_ledger(path=payload.get("ledger_path"))
    if path == "/api/unibot/ledger/public-summary":
        return 200, export_public_ledger_summary(path=payload.get("ledger_path"))
    if path == "/api/unibot/public-safety-scan":
        return 200, scan_text(
            text=str(payload.get("text", "")),
            source_name=str(payload.get("source_name", "browser-input")),
        )
    if path == "/api/unibot/materials/manifest":
        records = payload.get("records")
        if records is None:
            return 200, build_demo_material_manifest()
        if not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, build_material_manifest(records)
    if path == "/api/unibot/materials/public-summary":
        records = payload.get("records")
        if records is None:
            records = build_demo_material_manifest()["records"]
        if not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, build_public_material_summary(records)
    if path == "/api/unibot/materials/validate":
        record = payload.get("record")
        if not isinstance(record, dict):
            return 400, {"status": "invalid-record"}
        normalized = normalize_material_record(record, content_text=str(payload.get("content_text", "")))
        return 200, {
            "status": "ok",
            "record": normalized.to_public_summary_dict(),
            "validation": validate_material_record(normalized),
        }
    if path == "/api/unibot/course/intake-scan":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        return 200, scan_course_intake(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/index/build":
        records = payload.get("records")
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, build_course_exam_scope(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            records=records,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/compiler-plan":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        return 200, build_course_material_compiler_plan(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-queue":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        return 200, build_course_extraction_queue(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            rights_decision_reference=payload.get("rights_decision_reference") if payload.get("rights_decision_reference") else None,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-run-manifest":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        return 200, build_extraction_run_manifest(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            rights_decision_reference=payload.get("rights_decision_reference") if payload.get("rights_decision_reference") else None,
            dry_run=bool(payload.get("dry_run", True)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-decision-packet":
        return 200, build_extraction_decision_packet(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-decision/validate":
        decision = payload.get("decision", payload)
        if not isinstance(decision, dict):
            return 400, {"status": "invalid-decision"}
        return 200, validate_extraction_decision_record(decision)
    if path == "/api/unibot/course/extraction-decision/local-intake":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            batch_size = int(payload.get("batch_size", 12) or 12)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        job_types = payload.get("job_types")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if job_types is not None and not isinstance(job_types, list):
            return 400, {"status": "invalid-job-types"}
        return 200, build_local_extraction_decision_intake_packet(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            job_types=job_types,
            batch_size=batch_size,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-decision/local-intake/record":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            batch_size = int(payload.get("batch_size", 12) or 12)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record", payload.get("record"))
        job_types = payload.get("job_types")
        if not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if job_types is not None and not isinstance(job_types, list):
            return 400, {"status": "invalid-job-types"}
        return 200, record_local_extraction_decision_and_build_intake_packet(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            job_types=job_types,
            batch_size=batch_size,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-decision/workspace/prepare":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            batch_size = int(payload.get("batch_size", 12) or 12)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        job_types = payload.get("job_types")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if job_types is not None and not isinstance(job_types, list):
            return 400, {"status": "invalid-job-types"}
        return 200, prepare_local_extraction_decision_workspace(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            workspace_dir=payload.get("workspace_dir", payload.get("decision_workspace_dir")),
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_output_dir=payload.get("private_output_dir"),
            job_types=job_types,
            batch_size=batch_size,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-decision/workspace/record":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            batch_size = int(payload.get("batch_size", 12) or 12)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record", payload.get("record"))
        job_types = payload.get("job_types")
        if not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if job_types is not None and not isinstance(job_types, list):
            return 400, {"status": "invalid-job-types"}
        return 200, record_local_extraction_decision_workspace(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            workspace_dir=payload.get("workspace_dir", payload.get("decision_workspace_dir")),
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_output_dir=payload.get("private_output_dir"),
            job_types=job_types,
            batch_size=batch_size,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-operator-packet":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            job_limit = int(payload.get("job_limit", 12) or 12)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        return 200, build_extraction_operator_packet(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            job_limit=job_limit,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-receipt/validate":
        receipt = payload.get("receipt")
        decision_record = payload.get("decision_record")
        decision_context = resolve_extraction_decision_context(
            decision_record=decision_record if isinstance(decision_record, dict) else None,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
        )
        if not isinstance(receipt, dict):
            return 400, {"status": "invalid-receipt"}
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        return 200, validate_extraction_receipt(
            receipt,
            decision_record=decision_record,
            decision_reference_hash=str(decision_context.get("rights_decision_reference_hash", "")),
        )
    if path == "/api/unibot/course/extraction-receipts/append":
        receipt = payload.get("receipt")
        decision_record = payload.get("decision_record")
        decision_context = resolve_extraction_decision_context(
            decision_record=decision_record if isinstance(decision_record, dict) else None,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
        )
        if not isinstance(receipt, dict):
            return 400, {"status": "invalid-receipt"}
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        return 200, append_extraction_receipt_record(
            receipt,
            decision_record=decision_record,
            decision_reference_hash=str(decision_context.get("rights_decision_reference_hash", "")),
            path=payload.get("receipt_journal_path", payload.get("journal_path")),
        )
    if path == "/api/unibot/course/extraction-receipts/list":
        try:
            limit = int(payload.get("limit")) if payload.get("limit") is not None else None
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        return 200, read_extraction_receipt_journal(
            path=payload.get("receipt_journal_path", payload.get("journal_path")),
            limit=limit,
        )
    if path == "/api/unibot/course/extraction-receipts/summary":
        return 200, summarize_extraction_receipt_journal(
            path=payload.get("receipt_journal_path", payload.get("journal_path")),
        )
    if path == "/api/unibot/course/extraction-review/validate":
        receipt = payload.get("receipt")
        review_decision = payload.get("review_decision", payload.get("decision"))
        decision_record = payload.get("decision_record")
        decision_context = resolve_extraction_decision_context(
            decision_record=decision_record if isinstance(decision_record, dict) else None,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
        )
        if not isinstance(receipt, dict):
            return 400, {"status": "invalid-receipt"}
        if not isinstance(review_decision, dict):
            return 400, {"status": "invalid-review-decision"}
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        return 200, validate_extraction_human_review_decision(
            review_decision,
            receipt=receipt,
            decision_reference_hash=str(decision_context.get("rights_decision_reference_hash", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-review/apply-plan":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        review_decisions = payload.get("review_decisions", [])
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if review_decisions is None:
            review_decisions = []
        if not isinstance(review_decisions, list):
            return 400, {"status": "invalid-review-decisions"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_extraction_human_review_apply_plan(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            review_journal_path=payload.get("review_journal_path"),
            receipts=receipts,
            review_decisions=[item for item in review_decisions if isinstance(item, dict)],
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-deferral/validate":
        record = payload.get("deferral_record", payload.get("record", payload))
        if not isinstance(record, dict):
            return 400, {"status": "invalid-deferral-record"}
        return 200, validate_extraction_deferral_record(
            record,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-completion-report":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        deferral_record = payload.get("deferral_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if deferral_record is not None and not isinstance(deferral_record, dict):
            return 400, {"status": "invalid-deferral-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_extraction_completion_report(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            receipts=receipts,
            deferral_record=deferral_record,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/private-extraction/run-batch":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            max_jobs = int(payload.get("max_jobs", 8) or 8)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        job_types = payload.get("job_types")
        job_ids = payload.get("job_ids")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if job_types is not None and not isinstance(job_types, list):
            return 400, {"status": "invalid-job-types"}
        if job_ids is not None and not isinstance(job_ids, list):
            return 400, {"status": "invalid-job-ids"}
        return 200, run_private_extraction_batch(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_output_dir=payload.get("private_output_dir"),
            max_jobs=max_jobs,
            job_types=job_types,
            job_ids=job_ids,
            human_review_status=str(payload.get("human_review_status", "pending_review")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/ocr-first/operator-run":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            batch_size = int(payload.get("batch_size", 12) or 12)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        return 200, run_controlled_ocr_first_batch_1(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            workspace_dir=payload.get("workspace_dir", payload.get("decision_workspace_dir")),
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_output_dir=payload.get("private_output_dir"),
            batch_size=batch_size,
            operator_confirmed_dry_run=bool(payload.get("operator_confirmed_dry_run", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/video-transcription/run-batch":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            max_jobs = int(payload.get("max_jobs", 8) or 8)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        return 200, run_video_transcription_batch(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_output_dir=payload.get("private_output_dir"),
            max_jobs=max_jobs,
            human_review_status=str(payload.get("human_review_status", "pending_review")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-progress-report":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_extraction_progress_report(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-batch-plan":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            batch_size = int(payload.get("batch_size", 12) or 12)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        job_types = payload.get("job_types")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if job_types is not None and not isinstance(job_types, list):
            return 400, {"status": "invalid-job-types"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_extraction_batch_plan(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            batch_size=batch_size,
            job_types=job_types,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-batch-receipt-packet":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            batch_size = int(payload.get("batch_size", 12) or 12)
            batch_index_raw = payload.get("batch_index")
            batch_index = int(batch_index_raw) if batch_index_raw not in {None, ""} else None
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        job_types = payload.get("job_types")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if job_types is not None and not isinstance(job_types, list):
            return 400, {"status": "invalid-job-types"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_extraction_batch_receipt_packet(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            batch_size=batch_size,
            batch_index=batch_index,
            job_types=job_types,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-manifest-update-plan":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_extraction_manifest_update_plan(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/extraction-manifest/apply-dry-run":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_private_manifest_apply_dry_run(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/tutor-index/dry-run":
        return 200, build_private_tutor_index_dry_run(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            private_manifest_path=payload.get("private_manifest_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/tutor-index/respond-dry-run":
        return 200, build_private_index_tutor_response_dry_run(
            query=str(payload.get("query", payload.get("task", ""))),
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            tutor_index_path=payload.get("tutor_index_path"),
            mode=str(payload.get("mode", "exam_controlled_gateway")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/private-tutor-use-flow/dry-run":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        return 200, build_private_tutor_use_flow_dry_run(
            query=str(payload.get("query", payload.get("task", ""))),
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            mode=str(payload.get("mode", "exam_controlled_gateway")),
            exam_status=str(payload.get("exam_status", "strict")),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            study_receipt=study_receipt,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/material-coverage/run":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_course_material_coverage_run(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/exam-skill-drilldown":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_exam_skill_drilldown(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/skill-to-workspace-live-flow":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        local_cycle_readiness_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review"))
        local_cycle_readiness_handoff = payload.get("python_exam_local_cycle_readiness_handoff", payload.get("handoff"))
        local_cycle_workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        local_cycle_chain_snapshot = payload.get("python_exam_local_cycle_chain_snapshot", payload.get("local_cycle_chain_snapshot"))
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        return 200, build_skill_to_workspace_live_flow(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            operator_confirmed_exam_workspace_run=bool(payload.get("operator_confirmed_exam_workspace_run", False)),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            operator_confirmed_exam_ledger_append=bool(payload.get("operator_confirmed_exam_ledger_append", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/skill-to-workspace-session-carryover":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
            repeat_run_index = int(payload.get("repeat_run_index", 1) or 1)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        live_flow = payload.get("skill_to_workspace_live_flow", payload.get("live_flow"))
        chain = payload.get("review_chain_integrity_check", payload.get("chain_integrity_report"))
        review = payload.get("timeline_export_review_packet", payload.get("review_packet"))
        journal = payload.get("timeline_export_receipt_journal_summary", payload.get("receipt_journal_summary"))
        previous_console_receipts = payload.get("previous_console_receipts", [])
        for value, error in [
            (decision_record, "invalid-decision-record"),
            (study_receipt, "invalid-study-receipt"),
            (notebook_checkpoint, "invalid-notebook-checkpoint"),
            (live_flow, "invalid-skill-to-workspace-live-flow"),
            (chain, "invalid-review-chain-integrity-check"),
            (review, "invalid-timeline-export-review-packet"),
            (journal, "invalid-timeline-export-receipt-journal-summary"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        if receipt_error:
            return 400, {"status": receipt_error}
        if not isinstance(previous_console_receipts, list):
            return 400, {"status": "invalid-previous-console-receipts"}
        return 200, build_skill_to_workspace_session_carryover(
            skill_to_workspace_live_flow=live_flow,
            review_chain_integrity_check=chain,
            timeline_export_review_packet=review,
            timeline_export_receipt_journal_summary=journal,
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            repeat_run_index=repeat_run_index,
            previous_console_receipts=[item for item in previous_console_receipts if isinstance(item, dict)],
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            operator_confirmed_exam_workspace_run=bool(payload.get("operator_confirmed_exam_workspace_run", False)),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            operator_confirmed_exam_ledger_append=bool(payload.get("operator_confirmed_exam_ledger_append", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-source-grounded-tutor-drill-pack":
        dashboard = payload.get("course_exam_coverage_dashboard", payload.get("dashboard_report"))
        drilldown = payload.get("exam_skill_drilldown", payload.get("drilldown_report"))
        carryover = payload.get("skill_to_workspace_session_carryover", payload.get("session_carryover"))
        for value, error in [
            (dashboard, "invalid-course-exam-coverage-dashboard"),
            (drilldown, "invalid-exam-skill-drilldown"),
            (carryover, "invalid-skill-to-workspace-session-carryover"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        try:
            max_drills = int(payload.get("max_drills", 12) or 12)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-drills"}
        return 200, build_python_exam_source_grounded_tutor_drill_pack(
            course_exam_coverage_dashboard=dashboard,
            exam_skill_drilldown=drilldown,
            skill_to_workspace_session_carryover=carryover,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            max_drills=max_drills,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-drill-session-runner":
        tutor_drill_pack = payload.get("python_exam_tutor_drill_pack", payload.get("tutor_drill_pack"))
        carryover = payload.get("skill_to_workspace_session_carryover", payload.get("session_carryover"))
        notebook_checkpoint = payload.get("notebook_checkpoint")
        for value, error in [
            (tutor_drill_pack, "invalid-python-exam-tutor-drill-pack"),
            (carryover, "invalid-skill-to-workspace-session-carryover"),
            (notebook_checkpoint, "invalid-notebook-checkpoint"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        try:
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-cell-index"}
        return 200, build_python_exam_drill_session_runner(
            python_exam_tutor_drill_pack=tutor_drill_pack,
            skill_to_workspace_session_carryover=carryover,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            selected_task_id=str(payload.get("selected_task_id", "")),
            selected_task_hash=str(payload.get("selected_task_hash", "")),
            cell_source=str(payload.get("cell_source", "")),
            notebook_checkpoint=notebook_checkpoint,
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            student_reflection=str(payload.get("student_reflection", "")),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-drill-session-review-loop":
        drill_session = payload.get("python_exam_drill_session_runner", payload.get("drill_session_runner"))
        tutor_drill_pack = payload.get("python_exam_tutor_drill_pack", payload.get("tutor_drill_pack"))
        previous_review_loops = payload.get("previous_review_loops", [])
        for value, error in [
            (drill_session, "invalid-python-exam-drill-session-runner"),
            (tutor_drill_pack, "invalid-python-exam-tutor-drill-pack"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        if previous_review_loops is not None and not isinstance(previous_review_loops, list):
            return 400, {"status": "invalid-previous-review-loops"}
        return 200, build_python_exam_drill_session_review_loop(
            python_exam_drill_session_runner=drill_session,
            python_exam_tutor_drill_pack=tutor_drill_pack,
            previous_review_loops=[item for item in (previous_review_loops or []) if isinstance(item, dict)],
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-drill-loop-control-panel":
        tutor_drill_pack = payload.get("python_exam_tutor_drill_pack", payload.get("tutor_drill_pack"))
        carryover = payload.get("skill_to_workspace_session_carryover", payload.get("session_carryover"))
        drill_session = payload.get("python_exam_drill_session_runner", payload.get("drill_session_runner"))
        review_loop = payload.get("python_exam_drill_session_review_loop", payload.get("drill_session_review_loop"))
        notebook_checkpoint = payload.get("notebook_checkpoint")
        previous_review_loops = payload.get("previous_review_loops", [])
        for value, error in [
            (tutor_drill_pack, "invalid-python-exam-tutor-drill-pack"),
            (carryover, "invalid-skill-to-workspace-session-carryover"),
            (drill_session, "invalid-python-exam-drill-session-runner"),
            (review_loop, "invalid-python-exam-drill-session-review-loop"),
            (notebook_checkpoint, "invalid-notebook-checkpoint"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        if previous_review_loops is not None and not isinstance(previous_review_loops, list):
            return 400, {"status": "invalid-previous-review-loops"}
        try:
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-cell-index"}
        return 200, build_python_exam_drill_loop_control_panel(
            python_exam_tutor_drill_pack=tutor_drill_pack,
            skill_to_workspace_session_carryover=carryover,
            python_exam_drill_session_runner=drill_session,
            python_exam_drill_session_review_loop=review_loop,
            previous_review_loops=[item for item in (previous_review_loops or []) if isinstance(item, dict)],
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            selected_task_id=str(payload.get("selected_task_id", "")),
            selected_task_hash=str(payload.get("selected_task_hash", "")),
            cell_source=str(payload.get("cell_source", "")),
            notebook_checkpoint=notebook_checkpoint,
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            student_reflection=str(payload.get("student_reflection", "")),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-drill-loop-progress-journal":
        control_panel = payload.get("python_exam_drill_loop_control_panel", payload.get("drill_loop_control_panel"))
        previous_records = payload.get("previous_records", [])
        if control_panel is not None and not isinstance(control_panel, dict):
            return 400, {"status": "invalid-python-exam-drill-loop-control-panel"}
        if previous_records is not None and not isinstance(previous_records, list):
            return 400, {"status": "invalid-previous-records"}
        return 200, build_python_exam_drill_loop_progress_journal(
            python_exam_drill_loop_control_panel=control_panel,
            progress_journal_path=payload.get("progress_journal_path"),
            previous_records=[item for item in (previous_records or []) if isinstance(item, dict)],
            operator_confirmed_progress_journal_append=bool(
                payload.get("operator_confirmed_progress_journal_append", False)
            ),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-drill-loop-progress-journal/summary":
        return 200, summarize_python_exam_drill_loop_progress_journal(
            path=payload.get("progress_journal_path"),
        )
    if path == "/api/unibot/course/python-exam-resume-launcher":
        progress_journal = payload.get("python_exam_drill_loop_progress_journal", payload.get("progress_journal"))
        progress_summary = payload.get("progress_journal_summary")
        previous_records = payload.get("previous_records", [])
        if progress_journal is not None and not isinstance(progress_journal, dict):
            return 400, {"status": "invalid-python-exam-drill-loop-progress-journal"}
        if progress_summary is not None and not isinstance(progress_summary, dict):
            return 400, {"status": "invalid-progress-journal-summary"}
        if previous_records is not None and not isinstance(previous_records, list):
            return 400, {"status": "invalid-previous-records"}
        return 200, build_python_exam_resume_launcher(
            python_exam_drill_loop_progress_journal=progress_journal,
            progress_journal_summary=progress_summary,
            progress_journal_path=payload.get("progress_journal_path"),
            previous_records=[item for item in (previous_records or []) if isinstance(item, dict)],
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-active-study-loop-dashboard":
        coverage_dashboard = payload.get("course_exam_coverage_dashboard", payload.get("coverage_dashboard"))
        drill_pack = payload.get("python_exam_tutor_drill_pack", payload.get("tutor_drill_pack"))
        control_panel = payload.get("python_exam_drill_loop_control_panel", payload.get("drill_loop_control_panel"))
        progress_journal = payload.get("python_exam_drill_loop_progress_journal", payload.get("progress_journal"))
        resume_launcher = payload.get("python_exam_resume_launcher", payload.get("resume_launcher"))
        for value, error in [
            (coverage_dashboard, "invalid-course-exam-coverage-dashboard"),
            (drill_pack, "invalid-python-exam-tutor-drill-pack"),
            (control_panel, "invalid-python-exam-drill-loop-control-panel"),
            (progress_journal, "invalid-python-exam-drill-loop-progress-journal"),
            (resume_launcher, "invalid-python-exam-resume-launcher"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_active_study_loop_dashboard(
            course_exam_coverage_dashboard=coverage_dashboard,
            python_exam_tutor_drill_pack=drill_pack,
            python_exam_drill_loop_control_panel=control_panel,
            python_exam_drill_loop_progress_journal=progress_journal,
            python_exam_resume_launcher=resume_launcher,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-active-study-guided-runner":
        active_dashboard = payload.get("python_exam_active_study_loop_dashboard", payload.get("active_study_loop_dashboard"))
        resume_launcher = payload.get("python_exam_resume_launcher", payload.get("resume_launcher"))
        control_panel = payload.get("python_exam_drill_loop_control_panel", payload.get("drill_loop_control_panel"))
        for value, error in [
            (active_dashboard, "invalid-python-exam-active-study-loop-dashboard"),
            (resume_launcher, "invalid-python-exam-resume-launcher"),
            (control_panel, "invalid-python-exam-drill-loop-control-panel"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_active_study_guided_runner(
            python_exam_active_study_loop_dashboard=active_dashboard,
            python_exam_resume_launcher=resume_launcher,
            python_exam_drill_loop_control_panel=control_panel,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            requested_action=str(payload.get("requested_action", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-guided-action-execution-bridge":
        guided_runner = payload.get("python_exam_active_study_guided_runner", payload.get("guided_runner"))
        control_panel = payload.get("python_exam_drill_loop_control_panel", payload.get("drill_loop_control_panel"))
        progress_journal = payload.get("python_exam_drill_loop_progress_journal", payload.get("progress_journal"))
        for value, error in [
            (guided_runner, "invalid-python-exam-active-study-guided-runner"),
            (control_panel, "invalid-python-exam-drill-loop-control-panel"),
            (progress_journal, "invalid-python-exam-drill-loop-progress-journal"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_guided_action_execution_bridge(
            python_exam_active_study_guided_runner=guided_runner,
            python_exam_drill_loop_control_panel=control_panel,
            python_exam_drill_loop_progress_journal=progress_journal,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-safe-cycle-console":
        active_dashboard = payload.get("python_exam_active_study_loop_dashboard", payload.get("active_study_loop_dashboard"))
        guided_runner = payload.get("python_exam_active_study_guided_runner", payload.get("guided_runner"))
        execution_bridge = payload.get("python_exam_guided_action_execution_bridge", payload.get("execution_bridge"))
        control_panel = payload.get("python_exam_drill_loop_control_panel", payload.get("drill_loop_control_panel"))
        progress_journal = payload.get("python_exam_drill_loop_progress_journal", payload.get("progress_journal"))
        for value, error in [
            (active_dashboard, "invalid-python-exam-active-study-loop-dashboard"),
            (guided_runner, "invalid-python-exam-active-study-guided-runner"),
            (execution_bridge, "invalid-python-exam-guided-action-execution-bridge"),
            (control_panel, "invalid-python-exam-drill-loop-control-panel"),
            (progress_journal, "invalid-python-exam-drill-loop-progress-journal"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_safe_cycle_console(
            python_exam_active_study_loop_dashboard=active_dashboard,
            python_exam_active_study_guided_runner=guided_runner,
            python_exam_guided_action_execution_bridge=execution_bridge,
            python_exam_drill_loop_control_panel=control_panel,
            python_exam_drill_loop_progress_journal=progress_journal,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-safe-cycle-operator-gate":
        safe_cycle_console = payload.get("python_exam_safe_cycle_console", payload.get("safe_cycle_console"))
        if safe_cycle_console is not None and not isinstance(safe_cycle_console, dict):
            return 400, {"status": "invalid-python-exam-safe-cycle-console"}
        return 200, build_python_exam_safe_cycle_operator_gate(
            python_exam_safe_cycle_console=safe_cycle_console,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-operator-gate-decision-receipt":
        operator_gate = payload.get("python_exam_safe_cycle_operator_gate", payload.get("operator_gate"))
        confirmed_steps = payload.get("confirmed_step_ids", [])
        if operator_gate is not None and not isinstance(operator_gate, dict):
            return 400, {"status": "invalid-python-exam-safe-cycle-operator-gate"}
        if confirmed_steps is not None and not isinstance(confirmed_steps, list):
            return 400, {"status": "invalid-confirmed-step-ids"}
        return 200, build_python_exam_operator_gate_decision_receipt(
            python_exam_safe_cycle_operator_gate=operator_gate,
            confirmed_step_ids=[str(item) for item in (confirmed_steps or [])],
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-local-cycle-start-packet":
        safe_cycle_console = payload.get("python_exam_safe_cycle_console", payload.get("safe_cycle_console"))
        operator_gate = payload.get("python_exam_safe_cycle_operator_gate", payload.get("operator_gate"))
        decision_receipt = payload.get("python_exam_operator_gate_decision_receipt", payload.get("decision_receipt"))
        for value, error in [
            (safe_cycle_console, "invalid-python-exam-safe-cycle-console"),
            (operator_gate, "invalid-python-exam-safe-cycle-operator-gate"),
            (decision_receipt, "invalid-python-exam-operator-gate-decision-receipt"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_local_cycle_start_packet(
            python_exam_safe_cycle_console=safe_cycle_console,
            python_exam_safe_cycle_operator_gate=operator_gate,
            python_exam_operator_gate_decision_receipt=decision_receipt,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-local-cycle-readiness-review":
        start_packet = payload.get("python_exam_local_cycle_start_packet", payload.get("local_cycle_start_packet"))
        if start_packet is not None and not isinstance(start_packet, dict):
            return 400, {"status": "invalid-python-exam-local-cycle-start-packet"}
        return 200, build_python_exam_local_cycle_readiness_review(
            python_exam_local_cycle_start_packet=start_packet,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-local-cycle-readiness-handoff":
        readiness_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review"))
        start_packet = payload.get("python_exam_local_cycle_start_packet", payload.get("local_cycle_start_packet"))
        for value, error in [
            (readiness_review, "invalid-python-exam-local-cycle-readiness-review"),
            (start_packet, "invalid-python-exam-local-cycle-start-packet"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_local_cycle_readiness_handoff(
            python_exam_local_cycle_readiness_review=readiness_review,
            python_exam_local_cycle_start_packet=start_packet,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-local-cycle-operator-workspace-card":
        readiness_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review"))
        readiness_handoff = payload.get("python_exam_local_cycle_readiness_handoff", payload.get("readiness_handoff"))
        start_packet = payload.get("python_exam_local_cycle_start_packet", payload.get("local_cycle_start_packet"))
        for value, error in [
            (readiness_review, "invalid-python-exam-local-cycle-readiness-review"),
            (readiness_handoff, "invalid-python-exam-local-cycle-readiness-handoff"),
            (start_packet, "invalid-python-exam-local-cycle-start-packet"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_local_cycle_operator_workspace_card(
            python_exam_local_cycle_readiness_review=readiness_review,
            python_exam_local_cycle_readiness_handoff=readiness_handoff,
            python_exam_local_cycle_start_packet=start_packet,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-local-cycle-chain-snapshot":
        readiness_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review"))
        readiness_handoff = payload.get("python_exam_local_cycle_readiness_handoff", payload.get("readiness_handoff"))
        workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        for value, error in [
            (readiness_review, "invalid-python-exam-local-cycle-readiness-review"),
            (readiness_handoff, "invalid-python-exam-local-cycle-readiness-handoff"),
            (workspace_card, "invalid-python-exam-local-cycle-operator-workspace-card"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_local_cycle_chain_snapshot(
            python_exam_local_cycle_readiness_review=readiness_review,
            python_exam_local_cycle_readiness_handoff=readiness_handoff,
            python_exam_local_cycle_operator_workspace_card=workspace_card,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-local-cycle-manual-confirmation-console":
        readiness_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review"))
        readiness_handoff = payload.get("python_exam_local_cycle_readiness_handoff", payload.get("readiness_handoff"))
        workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        chain_snapshot = payload.get("python_exam_local_cycle_chain_snapshot", payload.get("chain_snapshot"))
        for value, error in [
            (readiness_review, "invalid-python-exam-local-cycle-readiness-review"),
            (readiness_handoff, "invalid-python-exam-local-cycle-readiness-handoff"),
            (workspace_card, "invalid-python-exam-local-cycle-operator-workspace-card"),
            (chain_snapshot, "invalid-python-exam-local-cycle-chain-snapshot"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_local_cycle_manual_confirmation_console(
            python_exam_local_cycle_readiness_review=readiness_review,
            python_exam_local_cycle_readiness_handoff=readiness_handoff,
            python_exam_local_cycle_operator_workspace_card=workspace_card,
            python_exam_local_cycle_chain_snapshot=chain_snapshot,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-cycle-launch-receipt":
        manual_console = payload.get("python_exam_manual_confirmation_console", payload.get("manual_confirmation_console"))
        chain_snapshot = payload.get("python_exam_local_cycle_chain_snapshot", payload.get("chain_snapshot"))
        workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        readiness_handoff = payload.get("python_exam_local_cycle_readiness_handoff", payload.get("readiness_handoff"))
        for value, error in [
            (manual_console, "invalid-python-exam-manual-confirmation-console"),
            (chain_snapshot, "invalid-python-exam-local-cycle-chain-snapshot"),
            (workspace_card, "invalid-python-exam-local-cycle-operator-workspace-card"),
            (readiness_handoff, "invalid-python-exam-local-cycle-readiness-handoff"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_cycle_launch_receipt(
            python_exam_manual_confirmation_console=manual_console,
            python_exam_local_cycle_chain_snapshot=chain_snapshot,
            python_exam_local_cycle_operator_workspace_card=workspace_card,
            python_exam_local_cycle_readiness_handoff=readiness_handoff,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-cycle-evidence-binder":
        launch_receipt = payload.get("python_exam_manual_cycle_launch_receipt", payload.get("manual_cycle_launch_receipt"))
        manual_console = payload.get("python_exam_manual_confirmation_console", payload.get("manual_confirmation_console"))
        chain_snapshot = payload.get("python_exam_local_cycle_chain_snapshot", payload.get("chain_snapshot"))
        workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        readiness_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review"))
        for value, error in [
            (launch_receipt, "invalid-python-exam-manual-cycle-launch-receipt"),
            (manual_console, "invalid-python-exam-manual-confirmation-console"),
            (chain_snapshot, "invalid-python-exam-local-cycle-chain-snapshot"),
            (workspace_card, "invalid-python-exam-local-cycle-operator-workspace-card"),
            (readiness_review, "invalid-python-exam-local-cycle-readiness-review"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_cycle_evidence_binder(
            python_exam_manual_cycle_launch_receipt=launch_receipt,
            python_exam_manual_confirmation_console=manual_console,
            python_exam_local_cycle_chain_snapshot=chain_snapshot,
            python_exam_local_cycle_operator_workspace_card=workspace_card,
            python_exam_local_cycle_readiness_review=readiness_review,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-post-cycle-receipt-intake":
        evidence_binder = payload.get("python_exam_manual_cycle_evidence_binder", payload.get("manual_cycle_evidence_binder"))
        launch_receipt = payload.get("python_exam_manual_cycle_launch_receipt", payload.get("manual_cycle_launch_receipt"))
        manual_console = payload.get("python_exam_manual_confirmation_console", payload.get("manual_confirmation_console"))
        post_cycle_hash_metadata = payload.get("post_cycle_hash_metadata", payload.get("human_post_cycle_hash_metadata"))
        for value, error in [
            (evidence_binder, "invalid-python-exam-manual-cycle-evidence-binder"),
            (launch_receipt, "invalid-python-exam-manual-cycle-launch-receipt"),
            (manual_console, "invalid-python-exam-manual-confirmation-console"),
            (post_cycle_hash_metadata, "invalid-post-cycle-hash-metadata"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_post_cycle_receipt_intake(
            python_exam_manual_cycle_evidence_binder=evidence_binder,
            python_exam_manual_cycle_launch_receipt=launch_receipt,
            python_exam_manual_confirmation_console=manual_console,
            post_cycle_hash_metadata=post_cycle_hash_metadata,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-cycle-closure-ledger":
        post_cycle_intake = payload.get(
            "python_exam_manual_post_cycle_receipt_intake",
            payload.get("manual_post_cycle_receipt_intake"),
        )
        evidence_binder = payload.get("python_exam_manual_cycle_evidence_binder", payload.get("manual_cycle_evidence_binder"))
        launch_receipt = payload.get("python_exam_manual_cycle_launch_receipt", payload.get("manual_cycle_launch_receipt"))
        manual_console = payload.get("python_exam_manual_confirmation_console", payload.get("manual_confirmation_console"))
        for value, error in [
            (post_cycle_intake, "invalid-python-exam-manual-post-cycle-receipt-intake"),
            (evidence_binder, "invalid-python-exam-manual-cycle-evidence-binder"),
            (launch_receipt, "invalid-python-exam-manual-cycle-launch-receipt"),
            (manual_console, "invalid-python-exam-manual-confirmation-console"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_cycle_closure_ledger(
            python_exam_manual_post_cycle_receipt_intake=post_cycle_intake,
            python_exam_manual_cycle_evidence_binder=evidence_binder,
            python_exam_manual_cycle_launch_receipt=launch_receipt,
            python_exam_manual_confirmation_console=manual_console,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-cycle-review-timeline":
        closure_ledger = payload.get("python_exam_manual_cycle_closure_ledger", payload.get("manual_cycle_closure_ledger"))
        post_cycle_intake = payload.get(
            "python_exam_manual_post_cycle_receipt_intake",
            payload.get("manual_post_cycle_receipt_intake"),
        )
        evidence_binder = payload.get("python_exam_manual_cycle_evidence_binder", payload.get("manual_cycle_evidence_binder"))
        launch_receipt = payload.get("python_exam_manual_cycle_launch_receipt", payload.get("manual_cycle_launch_receipt"))
        manual_console = payload.get("python_exam_manual_confirmation_console", payload.get("manual_confirmation_console"))
        for value, error in [
            (closure_ledger, "invalid-python-exam-manual-cycle-closure-ledger"),
            (post_cycle_intake, "invalid-python-exam-manual-post-cycle-receipt-intake"),
            (evidence_binder, "invalid-python-exam-manual-cycle-evidence-binder"),
            (launch_receipt, "invalid-python-exam-manual-cycle-launch-receipt"),
            (manual_console, "invalid-python-exam-manual-confirmation-console"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_cycle_review_timeline(
            python_exam_manual_cycle_closure_ledger=closure_ledger,
            python_exam_manual_post_cycle_receipt_intake=post_cycle_intake,
            python_exam_manual_cycle_evidence_binder=evidence_binder,
            python_exam_manual_cycle_launch_receipt=launch_receipt,
            python_exam_manual_confirmation_console=manual_console,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-cycle-review-packet":
        review_timeline = payload.get("python_exam_manual_cycle_review_timeline", payload.get("manual_cycle_review_timeline"))
        closure_ledger = payload.get("python_exam_manual_cycle_closure_ledger", payload.get("manual_cycle_closure_ledger"))
        post_cycle_intake = payload.get(
            "python_exam_manual_post_cycle_receipt_intake",
            payload.get("manual_post_cycle_receipt_intake"),
        )
        evidence_binder = payload.get("python_exam_manual_cycle_evidence_binder", payload.get("manual_cycle_evidence_binder"))
        launch_receipt = payload.get("python_exam_manual_cycle_launch_receipt", payload.get("manual_cycle_launch_receipt"))
        manual_console = payload.get("python_exam_manual_confirmation_console", payload.get("manual_confirmation_console"))
        for value, error in [
            (review_timeline, "invalid-python-exam-manual-cycle-review-timeline"),
            (closure_ledger, "invalid-python-exam-manual-cycle-closure-ledger"),
            (post_cycle_intake, "invalid-python-exam-manual-post-cycle-receipt-intake"),
            (evidence_binder, "invalid-python-exam-manual-cycle-evidence-binder"),
            (launch_receipt, "invalid-python-exam-manual-cycle-launch-receipt"),
            (manual_console, "invalid-python-exam-manual-confirmation-console"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_cycle_review_packet(
            python_exam_manual_cycle_review_timeline=review_timeline,
            python_exam_manual_cycle_closure_ledger=closure_ledger,
            python_exam_manual_post_cycle_receipt_intake=post_cycle_intake,
            python_exam_manual_cycle_evidence_binder=evidence_binder,
            python_exam_manual_cycle_launch_receipt=launch_receipt,
            python_exam_manual_confirmation_console=manual_console,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-review-export-preview":
        review_packet = payload.get("python_exam_manual_cycle_review_packet", payload.get("manual_cycle_review_packet"))
        review_timeline = payload.get("python_exam_manual_cycle_review_timeline", payload.get("manual_cycle_review_timeline"))
        closure_ledger = payload.get("python_exam_manual_cycle_closure_ledger", payload.get("manual_cycle_closure_ledger"))
        post_cycle_intake = payload.get(
            "python_exam_manual_post_cycle_receipt_intake",
            payload.get("manual_post_cycle_receipt_intake"),
        )
        evidence_binder = payload.get("python_exam_manual_cycle_evidence_binder", payload.get("manual_cycle_evidence_binder"))
        launch_receipt = payload.get("python_exam_manual_cycle_launch_receipt", payload.get("manual_cycle_launch_receipt"))
        manual_console = payload.get("python_exam_manual_confirmation_console", payload.get("manual_confirmation_console"))
        for value, error in [
            (review_packet, "invalid-python-exam-manual-cycle-review-packet"),
            (review_timeline, "invalid-python-exam-manual-cycle-review-timeline"),
            (closure_ledger, "invalid-python-exam-manual-cycle-closure-ledger"),
            (post_cycle_intake, "invalid-python-exam-manual-post-cycle-receipt-intake"),
            (evidence_binder, "invalid-python-exam-manual-cycle-evidence-binder"),
            (launch_receipt, "invalid-python-exam-manual-cycle-launch-receipt"),
            (manual_console, "invalid-python-exam-manual-confirmation-console"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_review_export_preview(
            python_exam_manual_cycle_review_packet=review_packet,
            python_exam_manual_cycle_review_timeline=review_timeline,
            python_exam_manual_cycle_closure_ledger=closure_ledger,
            python_exam_manual_post_cycle_receipt_intake=post_cycle_intake,
            python_exam_manual_cycle_evidence_binder=evidence_binder,
            python_exam_manual_cycle_launch_receipt=launch_receipt,
            python_exam_manual_confirmation_console=manual_console,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-review-export-authorization-gate":
        export_preview = payload.get(
            "python_exam_manual_review_export_preview",
            payload.get("manual_review_export_preview"),
        )
        review_packet = payload.get("python_exam_manual_cycle_review_packet", payload.get("manual_cycle_review_packet"))
        review_timeline = payload.get("python_exam_manual_cycle_review_timeline", payload.get("manual_cycle_review_timeline"))
        closure_ledger = payload.get("python_exam_manual_cycle_closure_ledger", payload.get("manual_cycle_closure_ledger"))
        for value, error in [
            (export_preview, "invalid-python-exam-manual-review-export-preview"),
            (review_packet, "invalid-python-exam-manual-cycle-review-packet"),
            (review_timeline, "invalid-python-exam-manual-cycle-review-timeline"),
            (closure_ledger, "invalid-python-exam-manual-cycle-closure-ledger"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_review_export_authorization_gate(
            python_exam_manual_review_export_preview=export_preview,
            python_exam_manual_cycle_review_packet=review_packet,
            python_exam_manual_cycle_review_timeline=review_timeline,
            python_exam_manual_cycle_closure_ledger=closure_ledger,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-export-review-queue":
        authorization_gate = payload.get(
            "python_exam_manual_review_export_authorization_gate",
            payload.get("manual_review_export_authorization_gate"),
        )
        export_preview = payload.get(
            "python_exam_manual_review_export_preview",
            payload.get("manual_review_export_preview"),
        )
        review_packet = payload.get("python_exam_manual_cycle_review_packet", payload.get("manual_cycle_review_packet"))
        review_timeline = payload.get("python_exam_manual_cycle_review_timeline", payload.get("manual_cycle_review_timeline"))
        queue_candidates = payload.get("queue_candidates", [])
        for value, error in [
            (authorization_gate, "invalid-python-exam-manual-review-export-authorization-gate"),
            (export_preview, "invalid-python-exam-manual-review-export-preview"),
            (review_packet, "invalid-python-exam-manual-cycle-review-packet"),
            (review_timeline, "invalid-python-exam-manual-cycle-review-timeline"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        if queue_candidates is not None and not isinstance(queue_candidates, list):
            return 400, {"status": "invalid-python-exam-manual-export-review-queue-candidates"}
        return 200, build_python_exam_manual_export_review_queue(
            python_exam_manual_review_export_authorization_gate=authorization_gate,
            python_exam_manual_review_export_preview=export_preview,
            python_exam_manual_cycle_review_packet=review_packet,
            python_exam_manual_cycle_review_timeline=review_timeline,
            queue_candidates=queue_candidates,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-export-reviewer-packet":
        export_review_queue = payload.get(
            "python_exam_manual_export_review_queue",
            payload.get("manual_export_review_queue"),
        )
        authorization_gate = payload.get(
            "python_exam_manual_review_export_authorization_gate",
            payload.get("manual_review_export_authorization_gate"),
        )
        export_preview = payload.get(
            "python_exam_manual_review_export_preview",
            payload.get("manual_review_export_preview"),
        )
        review_packet = payload.get("python_exam_manual_cycle_review_packet", payload.get("manual_cycle_review_packet"))
        review_timeline = payload.get("python_exam_manual_cycle_review_timeline", payload.get("manual_cycle_review_timeline"))
        for value, error in [
            (export_review_queue, "invalid-python-exam-manual-export-review-queue"),
            (authorization_gate, "invalid-python-exam-manual-review-export-authorization-gate"),
            (export_preview, "invalid-python-exam-manual-review-export-preview"),
            (review_packet, "invalid-python-exam-manual-cycle-review-packet"),
            (review_timeline, "invalid-python-exam-manual-cycle-review-timeline"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_export_reviewer_packet(
            python_exam_manual_export_review_queue=export_review_queue,
            python_exam_manual_review_export_authorization_gate=authorization_gate,
            python_exam_manual_review_export_preview=export_preview,
            python_exam_manual_cycle_review_packet=review_packet,
            python_exam_manual_cycle_review_timeline=review_timeline,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-archive-decision-draft":
        reviewer_packet = payload.get(
            "python_exam_manual_export_reviewer_packet",
            payload.get("manual_export_reviewer_packet"),
        )
        export_review_queue = payload.get(
            "python_exam_manual_export_review_queue",
            payload.get("manual_export_review_queue"),
        )
        authorization_gate = payload.get(
            "python_exam_manual_review_export_authorization_gate",
            payload.get("manual_review_export_authorization_gate"),
        )
        export_preview = payload.get(
            "python_exam_manual_review_export_preview",
            payload.get("manual_review_export_preview"),
        )
        for value, error in [
            (reviewer_packet, "invalid-python-exam-manual-export-reviewer-packet"),
            (export_review_queue, "invalid-python-exam-manual-export-review-queue"),
            (authorization_gate, "invalid-python-exam-manual-review-export-authorization-gate"),
            (export_preview, "invalid-python-exam-manual-review-export-preview"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_archive_decision_draft(
            python_exam_manual_export_reviewer_packet=reviewer_packet,
            python_exam_manual_export_review_queue=export_review_queue,
            python_exam_manual_review_export_authorization_gate=authorization_gate,
            python_exam_manual_review_export_preview=export_preview,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-final-review-handoff":
        archive_decision_draft = payload.get(
            "python_exam_manual_archive_decision_draft",
            payload.get("manual_archive_decision_draft"),
        )
        reviewer_packet = payload.get(
            "python_exam_manual_export_reviewer_packet",
            payload.get("manual_export_reviewer_packet"),
        )
        export_review_queue = payload.get(
            "python_exam_manual_export_review_queue",
            payload.get("manual_export_review_queue"),
        )
        authorization_gate = payload.get(
            "python_exam_manual_review_export_authorization_gate",
            payload.get("manual_review_export_authorization_gate"),
        )
        for value, error in [
            (archive_decision_draft, "invalid-python-exam-manual-archive-decision-draft"),
            (reviewer_packet, "invalid-python-exam-manual-export-reviewer-packet"),
            (export_review_queue, "invalid-python-exam-manual-export-review-queue"),
            (authorization_gate, "invalid-python-exam-manual-review-export-authorization-gate"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_final_review_handoff(
            python_exam_manual_archive_decision_draft=archive_decision_draft,
            python_exam_manual_export_reviewer_packet=reviewer_packet,
            python_exam_manual_export_review_queue=export_review_queue,
            python_exam_manual_review_export_authorization_gate=authorization_gate,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-manual-final-review-receipt-ledger":
        final_review_handoff = payload.get(
            "python_exam_manual_final_review_handoff",
            payload.get("manual_final_review_handoff"),
        )
        archive_decision_draft = payload.get(
            "python_exam_manual_archive_decision_draft",
            payload.get("manual_archive_decision_draft"),
        )
        reviewer_packet = payload.get(
            "python_exam_manual_export_reviewer_packet",
            payload.get("manual_export_reviewer_packet"),
        )
        export_review_queue = payload.get(
            "python_exam_manual_export_review_queue",
            payload.get("manual_export_review_queue"),
        )
        for value, error in [
            (final_review_handoff, "invalid-python-exam-manual-final-review-handoff"),
            (archive_decision_draft, "invalid-python-exam-manual-archive-decision-draft"),
            (reviewer_packet, "invalid-python-exam-manual-export-reviewer-packet"),
            (export_review_queue, "invalid-python-exam-manual-export-review-queue"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_manual_final_review_receipt_ledger(
            python_exam_manual_final_review_handoff=final_review_handoff,
            python_exam_manual_archive_decision_draft=archive_decision_draft,
            python_exam_manual_export_reviewer_packet=reviewer_packet,
            python_exam_manual_export_review_queue=export_review_queue,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-final-review-ledger-integrity-gate":
        final_review_receipt_ledger = payload.get(
            "python_exam_manual_final_review_receipt_ledger",
            payload.get("manual_final_review_receipt_ledger"),
        )
        final_review_handoff = payload.get(
            "python_exam_manual_final_review_handoff",
            payload.get("manual_final_review_handoff"),
        )
        archive_decision_draft = payload.get(
            "python_exam_manual_archive_decision_draft",
            payload.get("manual_archive_decision_draft"),
        )
        reviewer_packet = payload.get(
            "python_exam_manual_export_reviewer_packet",
            payload.get("manual_export_reviewer_packet"),
        )
        export_review_queue = payload.get(
            "python_exam_manual_export_review_queue",
            payload.get("manual_export_review_queue"),
        )
        for value, error in [
            (final_review_receipt_ledger, "invalid-python-exam-manual-final-review-receipt-ledger"),
            (final_review_handoff, "invalid-python-exam-manual-final-review-handoff"),
            (archive_decision_draft, "invalid-python-exam-manual-archive-decision-draft"),
            (reviewer_packet, "invalid-python-exam-manual-export-reviewer-packet"),
            (export_review_queue, "invalid-python-exam-manual-export-review-queue"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_final_review_ledger_integrity_gate(
            python_exam_manual_final_review_receipt_ledger=final_review_receipt_ledger,
            python_exam_manual_final_review_handoff=final_review_handoff,
            python_exam_manual_archive_decision_draft=archive_decision_draft,
            python_exam_manual_export_reviewer_packet=reviewer_packet,
            python_exam_manual_export_review_queue=export_review_queue,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-final-manual-review-console":
        final_review_integrity_gate = payload.get(
            "python_exam_final_review_ledger_integrity_gate",
            payload.get("final_review_ledger_integrity_gate"),
        )
        final_review_receipt_ledger = payload.get(
            "python_exam_manual_final_review_receipt_ledger",
            payload.get("manual_final_review_receipt_ledger"),
        )
        final_review_handoff = payload.get(
            "python_exam_manual_final_review_handoff",
            payload.get("manual_final_review_handoff"),
        )
        archive_decision_draft = payload.get(
            "python_exam_manual_archive_decision_draft",
            payload.get("manual_archive_decision_draft"),
        )
        reviewer_packet = payload.get(
            "python_exam_manual_export_reviewer_packet",
            payload.get("manual_export_reviewer_packet"),
        )
        export_review_queue = payload.get(
            "python_exam_manual_export_review_queue",
            payload.get("manual_export_review_queue"),
        )
        for value, error in [
            (final_review_integrity_gate, "invalid-python-exam-final-review-ledger-integrity-gate"),
            (final_review_receipt_ledger, "invalid-python-exam-manual-final-review-receipt-ledger"),
            (final_review_handoff, "invalid-python-exam-manual-final-review-handoff"),
            (archive_decision_draft, "invalid-python-exam-manual-archive-decision-draft"),
            (reviewer_packet, "invalid-python-exam-manual-export-reviewer-packet"),
            (export_review_queue, "invalid-python-exam-manual-export-review-queue"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_final_manual_review_console(
            python_exam_final_review_ledger_integrity_gate=final_review_integrity_gate,
            python_exam_manual_final_review_receipt_ledger=final_review_receipt_ledger,
            python_exam_manual_final_review_handoff=final_review_handoff,
            python_exam_manual_archive_decision_draft=archive_decision_draft,
            python_exam_manual_export_reviewer_packet=reviewer_packet,
            python_exam_manual_export_review_queue=export_review_queue,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-final-manual-review-action-lock":
        final_review_console = payload.get(
            "python_exam_final_manual_review_console",
            payload.get("final_manual_review_console"),
        )
        final_review_integrity_gate = payload.get(
            "python_exam_final_review_ledger_integrity_gate",
            payload.get("final_review_ledger_integrity_gate"),
        )
        final_review_receipt_ledger = payload.get(
            "python_exam_manual_final_review_receipt_ledger",
            payload.get("manual_final_review_receipt_ledger"),
        )
        for value, error in [
            (final_review_console, "invalid-python-exam-final-manual-review-console"),
            (final_review_integrity_gate, "invalid-python-exam-final-review-ledger-integrity-gate"),
            (final_review_receipt_ledger, "invalid-python-exam-manual-final-review-receipt-ledger"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_final_manual_review_action_lock(
            python_exam_final_manual_review_console=final_review_console,
            python_exam_final_review_ledger_integrity_gate=final_review_integrity_gate,
            python_exam_manual_final_review_receipt_ledger=final_review_receipt_ledger,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-locked-final-review-board":
        final_review_action_lock = payload.get(
            "python_exam_final_manual_review_action_lock",
            payload.get("final_manual_review_action_lock"),
        )
        final_review_console = payload.get(
            "python_exam_final_manual_review_console",
            payload.get("final_manual_review_console"),
        )
        final_review_integrity_gate = payload.get(
            "python_exam_final_review_ledger_integrity_gate",
            payload.get("final_review_ledger_integrity_gate"),
        )
        final_review_receipt_ledger = payload.get(
            "python_exam_manual_final_review_receipt_ledger",
            payload.get("manual_final_review_receipt_ledger"),
        )
        draft_package_review_console = payload.get(
            "python_exam_draft_package_review_console",
            payload.get("draft_package_review_console"),
        )
        human_handoff_packet = payload.get(
            "python_exam_human_handoff_packet",
            payload.get("human_handoff_packet"),
        )
        full_local_rehearsal_pack = payload.get(
            "python_exam_full_local_rehearsal_pack",
            payload.get("full_local_rehearsal_pack"),
        )
        for value, error in [
            (final_review_action_lock, "invalid-python-exam-final-manual-review-action-lock"),
            (final_review_console, "invalid-python-exam-final-manual-review-console"),
            (final_review_integrity_gate, "invalid-python-exam-final-review-ledger-integrity-gate"),
            (final_review_receipt_ledger, "invalid-python-exam-manual-final-review-receipt-ledger"),
            (draft_package_review_console, "invalid-python-exam-draft-package-review-console"),
            (human_handoff_packet, "invalid-python-exam-human-handoff-packet"),
            (full_local_rehearsal_pack, "invalid-python-exam-full-local-rehearsal-pack"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_locked_final_review_board(
            python_exam_final_manual_review_action_lock=final_review_action_lock,
            python_exam_final_manual_review_console=final_review_console,
            python_exam_final_review_ledger_integrity_gate=final_review_integrity_gate,
            python_exam_manual_final_review_receipt_ledger=final_review_receipt_ledger,
            python_exam_draft_package_review_console=draft_package_review_console,
            python_exam_human_handoff_packet=human_handoff_packet,
            python_exam_full_local_rehearsal_pack=full_local_rehearsal_pack,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-locked-final-review-gap-resolver":
        locked_final_review_board = payload.get(
            "python_exam_locked_final_review_board",
            payload.get("locked_final_review_board"),
        )
        final_review_action_lock = payload.get(
            "python_exam_final_manual_review_action_lock",
            payload.get("final_manual_review_action_lock"),
        )
        full_local_rehearsal_pack = payload.get(
            "python_exam_full_local_rehearsal_pack",
            payload.get("full_local_rehearsal_pack"),
        )
        rehearsal_playback_gap_coach = payload.get(
            "python_exam_rehearsal_playback_gap_coach",
            payload.get("rehearsal_playback_gap_coach"),
        )
        guided_loop_control_surface = payload.get(
            "python_exam_guided_loop_control_surface",
            payload.get("guided_loop_control_surface"),
        )
        for value, error in [
            (locked_final_review_board, "invalid-python-exam-locked-final-review-board"),
            (final_review_action_lock, "invalid-python-exam-final-manual-review-action-lock"),
            (full_local_rehearsal_pack, "invalid-python-exam-full-local-rehearsal-pack"),
            (rehearsal_playback_gap_coach, "invalid-python-exam-rehearsal-playback-gap-coach"),
            (guided_loop_control_surface, "invalid-python-exam-guided-loop-control-surface"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_locked_final_review_gap_resolver(
            python_exam_locked_final_review_board=locked_final_review_board,
            python_exam_final_manual_review_action_lock=final_review_action_lock,
            python_exam_full_local_rehearsal_pack=full_local_rehearsal_pack,
            python_exam_rehearsal_playback_gap_coach=rehearsal_playback_gap_coach,
            python_exam_guided_loop_control_surface=guided_loop_control_surface,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/exam-workspace/launch-flow/dry-run":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        return 200, build_exam_workspace_launch_flow_dry_run(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            query=str(payload.get("query", payload.get("task", ""))),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            operator_confirmed_exam_workspace_run=bool(payload.get("operator_confirmed_exam_workspace_run", False)),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            operator_confirmed_exam_ledger_append=bool(payload.get("operator_confirmed_exam_ledger_append", False)),
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/exam-workspace/notebook-checkpoint/adapt":
        try:
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-cell-index"}
        notebook_checkpoint = payload.get("notebook_checkpoint")
        source_card_ids = payload.get("source_card_ids", [])
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if not isinstance(source_card_ids, list):
            return 400, {"status": "invalid-source-card-ids"}
        return 200, build_exam_notebook_checkpoint_adapter_dry_run(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            task_id=str(payload.get("task_id", "")),
            skill_tag=str(payload.get("skill_tag", "")),
            source_card_ids=source_card_ids,
            source_anchor_id=str(payload.get("source_anchor_id", "")),
            cell_source=str(payload.get("cell_source", "")),
            notebook_checkpoint=notebook_checkpoint,
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            prediction_present=bool(payload.get("prediction_present", False)),
            retrieval_response_present=bool(payload.get("retrieval_response_present", False)),
            notebook_action_present=bool(payload.get("notebook_action_present", False)),
            reflection_present=bool(payload.get("reflection_present", False)),
            student_reflection=str(payload.get("student_reflection", "")),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/exam-workspace/operator-run":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        local_cycle_workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if local_cycle_workspace_card is not None and not isinstance(local_cycle_workspace_card, dict):
            return 400, {"status": "invalid-python-exam-local-cycle-operator-workspace-card"}
        return 200, build_exam_workspace_operator_run_dry_run(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            query=str(payload.get("query", payload.get("task", ""))),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            python_exam_local_cycle_operator_workspace_card=local_cycle_workspace_card,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            operator_confirmed_exam_workspace_run=bool(payload.get("operator_confirmed_exam_workspace_run", False)),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            operator_confirmed_exam_ledger_append=bool(payload.get("operator_confirmed_exam_ledger_append", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/exam-workspace/session-console":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
            repeat_run_index = int(payload.get("repeat_run_index", 1) or 1)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        local_cycle_workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        previous_console_receipts = payload.get("previous_console_receipts", [])
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if local_cycle_workspace_card is not None and not isinstance(local_cycle_workspace_card, dict):
            return 400, {"status": "invalid-python-exam-local-cycle-operator-workspace-card"}
        if not isinstance(previous_console_receipts, list):
            return 400, {"status": "invalid-previous-console-receipts"}
        return 200, build_exam_workspace_session_console(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            query=str(payload.get("query", payload.get("task", ""))),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            python_exam_local_cycle_operator_workspace_card=local_cycle_workspace_card,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            repeat_run_index=repeat_run_index,
            previous_console_receipts=previous_console_receipts,
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            operator_confirmed_exam_workspace_run=bool(payload.get("operator_confirmed_exam_workspace_run", False)),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            operator_confirmed_exam_ledger_append=bool(payload.get("operator_confirmed_exam_ledger_append", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/exam-workspace/run-history-export-review":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
            repeat_run_index = int(payload.get("repeat_run_index", 1) or 1)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        local_cycle_workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        console_reports = payload.get("console_reports", [])
        console_receipts = payload.get("console_receipts", payload.get("previous_console_receipts", []))
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if local_cycle_workspace_card is not None and not isinstance(local_cycle_workspace_card, dict):
            return 400, {"status": "invalid-python-exam-local-cycle-operator-workspace-card"}
        if not isinstance(console_reports, list):
            return 400, {"status": "invalid-console-reports"}
        if not isinstance(console_receipts, list):
            return 400, {"status": "invalid-console-receipts"}
        return 200, build_exam_workspace_run_history_export_review(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            console_reports=console_reports,
            console_receipts=console_receipts,
            build_current_console=bool(payload.get("build_current_console", not console_reports and not console_receipts)),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            query=str(payload.get("query", payload.get("task", ""))),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            python_exam_local_cycle_operator_workspace_card=local_cycle_workspace_card,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            repeat_run_index=repeat_run_index,
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            operator_confirmed_exam_workspace_run=bool(payload.get("operator_confirmed_exam_workspace_run", False)),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            operator_confirmed_exam_ledger_append=bool(payload.get("operator_confirmed_exam_ledger_append", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/exam-coverage-dashboard":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        console_reports = payload.get("console_reports", [])
        console_receipts = payload.get("console_receipts", payload.get("previous_console_receipts", []))
        run_history_report = payload.get("run_history_report")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if not isinstance(console_reports, list):
            return 400, {"status": "invalid-console-reports"}
        if not isinstance(console_receipts, list):
            return 400, {"status": "invalid-console-receipts"}
        if run_history_report is not None and not isinstance(run_history_report, dict):
            return 400, {"status": "invalid-run-history-report"}
        return 200, build_course_exam_coverage_dashboard(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            console_reports=console_reports,
            console_receipts=console_receipts,
            run_history_report=run_history_report,
            build_current_console=bool(payload.get("build_current_console", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/per-skill-action-router":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        console_reports = payload.get("console_reports", [])
        console_receipts = payload.get("console_receipts", payload.get("previous_console_receipts", []))
        run_history_report = payload.get("run_history_report")
        dashboard_report = payload.get("dashboard_report")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if not isinstance(console_reports, list):
            return 400, {"status": "invalid-console-reports"}
        if not isinstance(console_receipts, list):
            return 400, {"status": "invalid-console-receipts"}
        if run_history_report is not None and not isinstance(run_history_report, dict):
            return 400, {"status": "invalid-run-history-report"}
        if dashboard_report is not None and not isinstance(dashboard_report, dict):
            return 400, {"status": "invalid-dashboard-report"}
        return 200, build_course_per_skill_action_router(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            dashboard_report=dashboard_report,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            console_reports=console_reports,
            console_receipts=console_receipts,
            run_history_report=run_history_report,
            build_current_console=bool(payload.get("build_current_console", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/routed-action-executor":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
            repeat_run_index = int(payload.get("repeat_run_index", 1) or 1)
            max_jobs = int(payload.get("max_jobs", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        console_reports = payload.get("console_reports", [])
        console_receipts = payload.get("console_receipts", payload.get("previous_console_receipts", []))
        run_history_report = payload.get("run_history_report")
        dashboard_report = payload.get("dashboard_report")
        router_report = payload.get("router_report")
        selected_route = payload.get("selected_route")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if not isinstance(console_reports, list):
            return 400, {"status": "invalid-console-reports"}
        if not isinstance(console_receipts, list):
            return 400, {"status": "invalid-console-receipts"}
        if run_history_report is not None and not isinstance(run_history_report, dict):
            return 400, {"status": "invalid-run-history-report"}
        if dashboard_report is not None and not isinstance(dashboard_report, dict):
            return 400, {"status": "invalid-dashboard-report"}
        if router_report is not None and not isinstance(router_report, dict):
            return 400, {"status": "invalid-router-report"}
        if selected_route is not None and not isinstance(selected_route, dict):
            return 400, {"status": "invalid-selected-route"}
        return 200, build_routed_action_executor(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            router_report=router_report,
            selected_route=selected_route,
            dashboard_report=dashboard_report,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            private_output_dir=payload.get("private_output_dir"),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            console_reports=console_reports,
            console_receipts=console_receipts,
            run_history_report=run_history_report,
            query=str(payload.get("query", payload.get("task", ""))),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            repeat_run_index=repeat_run_index,
            operator_confirmed_checkpoint_store=bool(payload.get("operator_confirmed_checkpoint_store", False)),
            operator_confirmed_exam_workspace_run=bool(payload.get("operator_confirmed_exam_workspace_run", False)),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            operator_confirmed_exam_ledger_append=bool(payload.get("operator_confirmed_exam_ledger_append", False)),
            operator_confirmed_private_extraction_run=bool(payload.get("operator_confirmed_private_extraction_run", False)),
            operator_confirmed_video_transcription_run=bool(payload.get("operator_confirmed_video_transcription_run", False)),
            max_jobs=max_jobs,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/exam-run-packet":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        console_reports = payload.get("console_reports", [])
        console_receipts = payload.get("console_receipts", payload.get("previous_console_receipts", []))
        run_history_report = payload.get("run_history_report")
        dashboard_report = payload.get("dashboard_report")
        router_report = payload.get("router_report")
        executor_report = payload.get("executor_report")
        local_cycle_readiness_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review"))
        local_cycle_readiness_handoff = payload.get("python_exam_local_cycle_readiness_handoff", payload.get("handoff"))
        local_cycle_workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card", payload.get("workspace_card")),
        )
        local_cycle_chain_snapshot = payload.get("python_exam_local_cycle_chain_snapshot", payload.get("local_cycle_chain_snapshot"))
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if not isinstance(console_reports, list):
            return 400, {"status": "invalid-console-reports"}
        if not isinstance(console_receipts, list):
            return 400, {"status": "invalid-console-receipts"}
        if run_history_report is not None and not isinstance(run_history_report, dict):
            return 400, {"status": "invalid-run-history-report"}
        if dashboard_report is not None and not isinstance(dashboard_report, dict):
            return 400, {"status": "invalid-dashboard-report"}
        if router_report is not None and not isinstance(router_report, dict):
            return 400, {"status": "invalid-router-report"}
        if executor_report is not None and not isinstance(executor_report, dict):
            return 400, {"status": "invalid-executor-report"}
        for value, error in [
            (local_cycle_readiness_review, "invalid-python-exam-local-cycle-readiness-review"),
            (local_cycle_readiness_handoff, "invalid-python-exam-local-cycle-readiness-handoff"),
            (local_cycle_workspace_card, "invalid-python-exam-local-cycle-operator-workspace-card"),
            (local_cycle_chain_snapshot, "invalid-python-exam-local-cycle-chain-snapshot"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_exam_run_packet(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            dashboard_report=dashboard_report,
            router_report=router_report,
            executor_report=executor_report,
            run_history_report=run_history_report,
            console_reports=console_reports,
            console_receipts=console_receipts,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            query=str(payload.get("query", payload.get("task", ""))),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            python_exam_local_cycle_readiness_review=local_cycle_readiness_review,
            python_exam_local_cycle_readiness_handoff=local_cycle_readiness_handoff,
            python_exam_local_cycle_operator_workspace_card=local_cycle_workspace_card,
            python_exam_local_cycle_chain_snapshot=local_cycle_chain_snapshot,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/exam-packet-timeline":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        console_reports = payload.get("console_reports", [])
        console_receipts = payload.get("console_receipts", payload.get("previous_console_receipts", []))
        run_history_report = payload.get("run_history_report")
        dashboard_report = payload.get("dashboard_report")
        router_report = payload.get("router_report")
        executor_report = payload.get("executor_report")
        exam_run_packet = payload.get("exam_run_packet")
        exam_run_packets = payload.get("exam_run_packets", [])
        local_cycle_readiness_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review"))
        local_cycle_readiness_handoff = payload.get("python_exam_local_cycle_readiness_handoff", payload.get("handoff"))
        local_cycle_workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        local_cycle_chain_snapshot = payload.get("python_exam_local_cycle_chain_snapshot", payload.get("local_cycle_chain_snapshot"))
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if not isinstance(console_reports, list):
            return 400, {"status": "invalid-console-reports"}
        if not isinstance(console_receipts, list):
            return 400, {"status": "invalid-console-receipts"}
        if run_history_report is not None and not isinstance(run_history_report, dict):
            return 400, {"status": "invalid-run-history-report"}
        if dashboard_report is not None and not isinstance(dashboard_report, dict):
            return 400, {"status": "invalid-dashboard-report"}
        if router_report is not None and not isinstance(router_report, dict):
            return 400, {"status": "invalid-router-report"}
        if executor_report is not None and not isinstance(executor_report, dict):
            return 400, {"status": "invalid-executor-report"}
        if exam_run_packet is not None and not isinstance(exam_run_packet, dict):
            return 400, {"status": "invalid-exam-run-packet"}
        if not isinstance(exam_run_packets, list):
            return 400, {"status": "invalid-exam-run-packets"}
        for value, error in [
            (local_cycle_readiness_review, "invalid-python-exam-local-cycle-readiness-review"),
            (local_cycle_readiness_handoff, "invalid-python-exam-local-cycle-readiness-handoff"),
            (local_cycle_workspace_card, "invalid-python-exam-local-cycle-operator-workspace-card"),
            (local_cycle_chain_snapshot, "invalid-python-exam-local-cycle-chain-snapshot"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_exam_packet_timeline(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            exam_run_packets=exam_run_packets,
            exam_run_packet=exam_run_packet,
            dashboard_report=dashboard_report,
            router_report=router_report,
            executor_report=executor_report,
            run_history_report=run_history_report,
            console_reports=console_reports,
            console_receipts=console_receipts,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            query=str(payload.get("query", payload.get("task", ""))),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            python_exam_local_cycle_readiness_review=local_cycle_readiness_review,
            python_exam_local_cycle_readiness_handoff=local_cycle_readiness_handoff,
            python_exam_local_cycle_operator_workspace_card=local_cycle_workspace_card,
            python_exam_local_cycle_chain_snapshot=local_cycle_chain_snapshot,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/timeline-export-review-packet":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        console_reports = payload.get("console_reports", [])
        console_receipts = payload.get("console_receipts", payload.get("previous_console_receipts", []))
        run_history_report = payload.get("run_history_report")
        dashboard_report = payload.get("dashboard_report")
        router_report = payload.get("router_report")
        executor_report = payload.get("executor_report")
        exam_run_packet = payload.get("exam_run_packet")
        exam_run_packets = payload.get("exam_run_packets", [])
        exam_packet_timeline = payload.get("exam_packet_timeline")
        exam_packet_timelines = payload.get("exam_packet_timelines", [])
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if not isinstance(console_reports, list):
            return 400, {"status": "invalid-console-reports"}
        if not isinstance(console_receipts, list):
            return 400, {"status": "invalid-console-receipts"}
        if run_history_report is not None and not isinstance(run_history_report, dict):
            return 400, {"status": "invalid-run-history-report"}
        if dashboard_report is not None and not isinstance(dashboard_report, dict):
            return 400, {"status": "invalid-dashboard-report"}
        if router_report is not None and not isinstance(router_report, dict):
            return 400, {"status": "invalid-router-report"}
        if executor_report is not None and not isinstance(executor_report, dict):
            return 400, {"status": "invalid-executor-report"}
        if exam_run_packet is not None and not isinstance(exam_run_packet, dict):
            return 400, {"status": "invalid-exam-run-packet"}
        if not isinstance(exam_run_packets, list):
            return 400, {"status": "invalid-exam-run-packets"}
        if exam_packet_timeline is not None and not isinstance(exam_packet_timeline, dict):
            return 400, {"status": "invalid-exam-packet-timeline"}
        if not isinstance(exam_packet_timelines, list):
            return 400, {"status": "invalid-exam-packet-timelines"}
        return 200, build_timeline_export_review_packet(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            exam_packet_timeline=exam_packet_timeline,
            exam_packet_timelines=exam_packet_timelines,
            exam_run_packets=exam_run_packets,
            exam_run_packet=exam_run_packet,
            dashboard_report=dashboard_report,
            router_report=router_report,
            executor_report=executor_report,
            run_history_report=run_history_report,
            console_reports=console_reports,
            console_receipts=console_receipts,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            query=str(payload.get("query", payload.get("task", ""))),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            operator_confirmed_local_export_receipt=bool(payload.get("operator_confirmed_local_export_receipt", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/timeline-export-receipt-journal/append":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook_checkpoint = payload.get("notebook_checkpoint")
        console_reports = payload.get("console_reports", [])
        console_receipts = payload.get("console_receipts", payload.get("previous_console_receipts", []))
        run_history_report = payload.get("run_history_report")
        dashboard_report = payload.get("dashboard_report")
        router_report = payload.get("router_report")
        executor_report = payload.get("executor_report")
        exam_run_packet = payload.get("exam_run_packet")
        exam_run_packets = payload.get("exam_run_packets", [])
        exam_packet_timeline = payload.get("exam_packet_timeline")
        exam_packet_timelines = payload.get("exam_packet_timelines", [])
        review_packet = payload.get("review_packet", payload.get("timeline_export_review_packet"))
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook_checkpoint is not None and not isinstance(notebook_checkpoint, dict):
            return 400, {"status": "invalid-notebook-checkpoint"}
        if not isinstance(console_reports, list):
            return 400, {"status": "invalid-console-reports"}
        if not isinstance(console_receipts, list):
            return 400, {"status": "invalid-console-receipts"}
        if run_history_report is not None and not isinstance(run_history_report, dict):
            return 400, {"status": "invalid-run-history-report"}
        if dashboard_report is not None and not isinstance(dashboard_report, dict):
            return 400, {"status": "invalid-dashboard-report"}
        if router_report is not None and not isinstance(router_report, dict):
            return 400, {"status": "invalid-router-report"}
        if executor_report is not None and not isinstance(executor_report, dict):
            return 400, {"status": "invalid-executor-report"}
        if exam_run_packet is not None and not isinstance(exam_run_packet, dict):
            return 400, {"status": "invalid-exam-run-packet"}
        if not isinstance(exam_run_packets, list):
            return 400, {"status": "invalid-exam-run-packets"}
        if exam_packet_timeline is not None and not isinstance(exam_packet_timeline, dict):
            return 400, {"status": "invalid-exam-packet-timeline"}
        if not isinstance(exam_packet_timelines, list):
            return 400, {"status": "invalid-exam-packet-timelines"}
        if review_packet is not None and not isinstance(review_packet, dict):
            return 400, {"status": "invalid-review-packet"}
        return 200, build_timeline_export_receipt_journal_append(
            review_packet=review_packet,
            journal_path=payload.get("timeline_export_receipt_journal_path", payload.get("journal_path")),
            operator_confirmed_timeline_export_receipt_journal_append=bool(
                payload.get("operator_confirmed_timeline_export_receipt_journal_append", False)
            ),
            public_safe=bool(payload.get("public_safe", True)),
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            focus_query=str(payload.get("focus_query", payload.get("query", payload.get("task", "")))),
            exam_packet_timeline=exam_packet_timeline,
            exam_packet_timelines=exam_packet_timelines,
            exam_run_packets=exam_run_packets,
            exam_run_packet=exam_run_packet,
            dashboard_report=dashboard_report,
            router_report=router_report,
            executor_report=executor_report,
            run_history_report=run_history_report,
            console_reports=console_reports,
            console_receipts=console_receipts,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path"),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            checkpoint_journal_path=payload.get("checkpoint_journal_path"),
            query=str(payload.get("query", payload.get("task", ""))),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            notebook_checkpoint=notebook_checkpoint,
            cell_source=str(payload.get("cell_source", "")),
            cell_index=cell_index,
            cell_id=str(payload.get("cell_id", "")),
            cell_type=str(payload.get("cell_type", "code")),
            operator_confirmed_local_export_receipt=bool(payload.get("operator_confirmed_local_export_receipt", False)),
        )
    if path == "/api/unibot/course/timeline-export-receipt-journal/summary":
        return 200, summarize_timeline_export_receipt_journal(
            path=payload.get("timeline_export_receipt_journal_path", payload.get("journal_path"))
        )
    if path == "/api/unibot/course/review-chain-integrity-check":
        exam_run_packet = payload.get("exam_run_packet")
        exam_packet_timeline = payload.get("exam_packet_timeline")
        timeline_export_review_packet = payload.get("timeline_export_review_packet")
        timeline_export_receipt_journal_append = payload.get("timeline_export_receipt_journal_append")
        timeline_export_receipt_journal_summary = payload.get("timeline_export_receipt_journal_summary")
        if exam_run_packet is not None and not isinstance(exam_run_packet, dict):
            return 400, {"status": "invalid-exam-run-packet"}
        if exam_packet_timeline is not None and not isinstance(exam_packet_timeline, dict):
            return 400, {"status": "invalid-exam-packet-timeline"}
        if timeline_export_review_packet is not None and not isinstance(timeline_export_review_packet, dict):
            return 400, {"status": "invalid-timeline-export-review-packet"}
        if timeline_export_receipt_journal_append is not None and not isinstance(timeline_export_receipt_journal_append, dict):
            return 400, {"status": "invalid-timeline-export-receipt-journal-append"}
        if timeline_export_receipt_journal_summary is not None and not isinstance(timeline_export_receipt_journal_summary, dict):
            return 400, {"status": "invalid-timeline-export-receipt-journal-summary"}
        return 200, build_review_chain_integrity_check(
            exam_run_packet=exam_run_packet,
            exam_packet_timeline=exam_packet_timeline,
            timeline_export_review_packet=timeline_export_review_packet,
            timeline_export_receipt_journal_append=timeline_export_receipt_journal_append,
            timeline_export_receipt_journal_summary=timeline_export_receipt_journal_summary,
            timeline_export_receipt_journal_path=payload.get("timeline_export_receipt_journal_path", payload.get("journal_path")),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-readiness-console":
        course_exam_coverage_dashboard = payload.get("course_exam_coverage_dashboard", payload.get("dashboard_report"))
        exam_skill_drilldown = payload.get("exam_skill_drilldown", payload.get("drilldown_report"))
        review_chain_integrity_check = payload.get("review_chain_integrity_check", payload.get("chain_integrity_report"))
        timeline_export_receipt_journal_summary = payload.get(
            "timeline_export_receipt_journal_summary", payload.get("receipt_journal_summary")
        )
        if course_exam_coverage_dashboard is not None and not isinstance(course_exam_coverage_dashboard, dict):
            return 400, {"status": "invalid-course-exam-coverage-dashboard"}
        if exam_skill_drilldown is not None and not isinstance(exam_skill_drilldown, dict):
            return 400, {"status": "invalid-exam-skill-drilldown"}
        if review_chain_integrity_check is not None and not isinstance(review_chain_integrity_check, dict):
            return 400, {"status": "invalid-review-chain-integrity-check"}
        if timeline_export_receipt_journal_summary is not None and not isinstance(timeline_export_receipt_journal_summary, dict):
            return 400, {"status": "invalid-timeline-export-receipt-journal-summary"}
        return 200, build_python_exam_readiness_console(
            course_exam_coverage_dashboard=course_exam_coverage_dashboard,
            exam_skill_drilldown=exam_skill_drilldown,
            review_chain_integrity_check=review_chain_integrity_check,
            timeline_export_receipt_journal_summary=timeline_export_receipt_journal_summary,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-cockpit-flow":
        python_exam_readiness_console = payload.get("python_exam_readiness_console", payload.get("readiness_console"))
        exam_skill_drilldown = payload.get("exam_skill_drilldown", payload.get("drilldown_report"))
        exam_workspace_operator_run = payload.get("exam_workspace_operator_run", payload.get("operator_report"))
        exam_workspace_session_console = payload.get("exam_workspace_session_console", payload.get("session_console_report"))
        notebook_checkpoint = payload.get("notebook_checkpoint")
        review_chain_integrity_check = payload.get("review_chain_integrity_check", payload.get("chain_integrity_report"))
        timeline_export_review_packet = payload.get("timeline_export_review_packet", payload.get("review_packet"))
        timeline_export_receipt_journal_summary = payload.get(
            "timeline_export_receipt_journal_summary", payload.get("receipt_journal_summary")
        )
        for value, error in [
            (python_exam_readiness_console, "invalid-python-exam-readiness-console"),
            (exam_skill_drilldown, "invalid-exam-skill-drilldown"),
            (exam_workspace_operator_run, "invalid-exam-workspace-operator-run"),
            (exam_workspace_session_console, "invalid-exam-workspace-session-console"),
            (notebook_checkpoint, "invalid-notebook-checkpoint"),
            (review_chain_integrity_check, "invalid-review-chain-integrity-check"),
            (timeline_export_review_packet, "invalid-timeline-export-review-packet"),
            (timeline_export_receipt_journal_summary, "invalid-timeline-export-receipt-journal-summary"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_cockpit_flow(
            python_exam_readiness_console=python_exam_readiness_console,
            exam_skill_drilldown=exam_skill_drilldown,
            exam_workspace_operator_run=exam_workspace_operator_run,
            exam_workspace_session_console=exam_workspace_session_console,
            notebook_checkpoint=notebook_checkpoint,
            review_chain_integrity_check=review_chain_integrity_check,
            timeline_export_review_packet=timeline_export_review_packet,
            timeline_export_receipt_journal_summary=timeline_export_receipt_journal_summary,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-live-control-surface":
        python_exam_cockpit_flow = payload.get("python_exam_cockpit_flow", payload.get("cockpit_flow"))
        python_exam_readiness_console = payload.get("python_exam_readiness_console", payload.get("readiness_console"))
        exam_skill_drilldown = payload.get("exam_skill_drilldown", payload.get("drilldown_report"))
        python_exam_local_cycle_operator_workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        exam_workspace_operator_run = payload.get("exam_workspace_operator_run", payload.get("operator_report"))
        exam_workspace_session_console = payload.get("exam_workspace_session_console", payload.get("session_console_report"))
        notebook_checkpoint = payload.get("notebook_checkpoint")
        review_chain_integrity_check = payload.get("review_chain_integrity_check", payload.get("chain_integrity_report"))
        timeline_export_review_packet = payload.get("timeline_export_review_packet", payload.get("review_packet"))
        timeline_export_receipt_journal_summary = payload.get(
            "timeline_export_receipt_journal_summary", payload.get("receipt_journal_summary")
        )
        for value, error in [
            (python_exam_cockpit_flow, "invalid-python-exam-cockpit-flow"),
            (python_exam_readiness_console, "invalid-python-exam-readiness-console"),
            (exam_skill_drilldown, "invalid-exam-skill-drilldown"),
            (python_exam_local_cycle_operator_workspace_card, "invalid-python-exam-local-cycle-operator-workspace-card"),
            (exam_workspace_operator_run, "invalid-exam-workspace-operator-run"),
            (exam_workspace_session_console, "invalid-exam-workspace-session-console"),
            (notebook_checkpoint, "invalid-notebook-checkpoint"),
            (review_chain_integrity_check, "invalid-review-chain-integrity-check"),
            (timeline_export_review_packet, "invalid-timeline-export-review-packet"),
            (timeline_export_receipt_journal_summary, "invalid-timeline-export-receipt-journal-summary"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_live_control_surface(
            python_exam_cockpit_flow=python_exam_cockpit_flow,
            python_exam_readiness_console=python_exam_readiness_console,
            exam_skill_drilldown=exam_skill_drilldown,
            python_exam_local_cycle_operator_workspace_card=python_exam_local_cycle_operator_workspace_card,
            exam_workspace_operator_run=exam_workspace_operator_run,
            exam_workspace_session_console=exam_workspace_session_console,
            notebook_checkpoint=notebook_checkpoint,
            review_chain_integrity_check=review_chain_integrity_check,
            timeline_export_review_packet=timeline_export_review_packet,
            timeline_export_receipt_journal_summary=timeline_export_receipt_journal_summary,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-evidence-export-preview":
        python_exam_live_control_surface = payload.get("python_exam_live_control_surface", payload.get("live_control_surface"))
        python_exam_cockpit_flow = payload.get("python_exam_cockpit_flow", payload.get("cockpit_flow"))
        python_exam_readiness_console = payload.get("python_exam_readiness_console", payload.get("readiness_console"))
        exam_skill_drilldown = payload.get("exam_skill_drilldown", payload.get("drilldown_report"))
        exam_workspace_operator_run = payload.get("exam_workspace_operator_run", payload.get("operator_report"))
        exam_workspace_session_console = payload.get("exam_workspace_session_console", payload.get("session_console_report"))
        notebook_checkpoint = payload.get("notebook_checkpoint")
        review_chain_integrity_check = payload.get("review_chain_integrity_check", payload.get("chain_integrity_report"))
        timeline_export_review_packet = payload.get("timeline_export_review_packet", payload.get("review_packet"))
        timeline_export_receipt_journal_summary = payload.get(
            "timeline_export_receipt_journal_summary", payload.get("receipt_journal_summary")
        )
        for value, error in [
            (python_exam_live_control_surface, "invalid-python-exam-live-control-surface"),
            (python_exam_cockpit_flow, "invalid-python-exam-cockpit-flow"),
            (python_exam_readiness_console, "invalid-python-exam-readiness-console"),
            (exam_skill_drilldown, "invalid-exam-skill-drilldown"),
            (exam_workspace_operator_run, "invalid-exam-workspace-operator-run"),
            (exam_workspace_session_console, "invalid-exam-workspace-session-console"),
            (notebook_checkpoint, "invalid-notebook-checkpoint"),
            (review_chain_integrity_check, "invalid-review-chain-integrity-check"),
            (timeline_export_review_packet, "invalid-timeline-export-review-packet"),
            (timeline_export_receipt_journal_summary, "invalid-timeline-export-receipt-journal-summary"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_evidence_export_preview(
            python_exam_live_control_surface=python_exam_live_control_surface,
            python_exam_cockpit_flow=python_exam_cockpit_flow,
            python_exam_readiness_console=python_exam_readiness_console,
            exam_skill_drilldown=exam_skill_drilldown,
            exam_workspace_operator_run=exam_workspace_operator_run,
            exam_workspace_session_console=exam_workspace_session_console,
            notebook_checkpoint=notebook_checkpoint,
            review_chain_integrity_check=review_chain_integrity_check,
            timeline_export_review_packet=timeline_export_review_packet,
            timeline_export_receipt_journal_summary=timeline_export_receipt_journal_summary,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-confirmed-local-export-draft":
        python_exam_evidence_export_preview = payload.get(
            "python_exam_evidence_export_preview", payload.get("evidence_export_preview")
        )
        if python_exam_evidence_export_preview is not None and not isinstance(python_exam_evidence_export_preview, dict):
            return 400, {"status": "invalid-python-exam-evidence-export-preview"}
        return 200, build_python_exam_confirmed_local_export_draft(
            python_exam_evidence_export_preview=python_exam_evidence_export_preview,
            export_draft_dir=payload.get("export_draft_dir"),
            operator_confirmed_local_export_draft_write=bool(
                payload.get("operator_confirmed_local_export_draft_write", False)
            ),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-draft-package-review-console":
        python_exam_confirmed_local_export_draft = payload.get(
            "python_exam_confirmed_local_export_draft", payload.get("local_export_draft")
        )
        python_exam_evidence_export_preview = payload.get(
            "python_exam_evidence_export_preview", payload.get("evidence_export_preview")
        )
        if python_exam_confirmed_local_export_draft is not None and not isinstance(
            python_exam_confirmed_local_export_draft, dict
        ):
            return 400, {"status": "invalid-python-exam-confirmed-local-export-draft"}
        if python_exam_evidence_export_preview is not None and not isinstance(python_exam_evidence_export_preview, dict):
            return 400, {"status": "invalid-python-exam-evidence-export-preview"}
        return 200, build_python_exam_draft_package_review_console(
            python_exam_confirmed_local_export_draft=python_exam_confirmed_local_export_draft,
            python_exam_evidence_export_preview=python_exam_evidence_export_preview,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-human-handoff-packet":
        python_exam_draft_package_review_console = payload.get(
            "python_exam_draft_package_review_console", payload.get("draft_package_review_console")
        )
        python_exam_evidence_export_preview = payload.get(
            "python_exam_evidence_export_preview", payload.get("evidence_export_preview")
        )
        python_exam_confirmed_local_export_draft = payload.get(
            "python_exam_confirmed_local_export_draft", payload.get("local_export_draft")
        )
        for value, error in [
            (python_exam_draft_package_review_console, "invalid-python-exam-draft-package-review-console"),
            (python_exam_evidence_export_preview, "invalid-python-exam-evidence-export-preview"),
            (python_exam_confirmed_local_export_draft, "invalid-python-exam-confirmed-local-export-draft"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_human_handoff_packet(
            python_exam_draft_package_review_console=python_exam_draft_package_review_console,
            python_exam_evidence_export_preview=python_exam_evidence_export_preview,
            python_exam_confirmed_local_export_draft=python_exam_confirmed_local_export_draft,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-full-local-rehearsal-pack":
        exam_skill_drilldown = payload.get("exam_skill_drilldown", payload.get("drilldown_report"))
        local_review = payload.get("python_exam_local_cycle_readiness_review", payload.get("local_cycle_readiness_review"))
        local_handoff = payload.get("python_exam_local_cycle_readiness_handoff", payload.get("local_cycle_readiness_handoff"))
        local_workspace_card = payload.get(
            "python_exam_local_cycle_operator_workspace_card",
            payload.get("local_cycle_operator_workspace_card"),
        )
        local_chain = payload.get("python_exam_local_cycle_chain_snapshot", payload.get("local_cycle_chain_snapshot"))
        exam_workspace_operator_run = payload.get("exam_workspace_operator_run", payload.get("operator_report"))
        exam_workspace_session_console = payload.get("exam_workspace_session_console", payload.get("session_console_report"))
        exam_workspace_run_history = payload.get(
            "exam_workspace_run_history_export_review",
            payload.get("run_history_report"),
        )
        course_dashboard = payload.get("course_exam_coverage_dashboard", payload.get("dashboard_report"))
        per_skill_router = payload.get("course_per_skill_action_router", payload.get("router_report"))
        routed_executor = payload.get("routed_action_executor", payload.get("executor_report"))
        exam_run_packet = payload.get("exam_run_packet")
        exam_packet_timeline = payload.get("exam_packet_timeline")
        timeline_export_review_packet = payload.get("timeline_export_review_packet", payload.get("review_packet"))
        timeline_export_receipt_journal_summary = payload.get(
            "timeline_export_receipt_journal_summary",
            payload.get("receipt_journal_summary"),
        )
        review_chain_integrity_check = payload.get("review_chain_integrity_check", payload.get("chain_integrity_report"))
        readiness_console = payload.get("python_exam_readiness_console", payload.get("readiness_console"))
        cockpit_flow = payload.get("python_exam_cockpit_flow", payload.get("cockpit_flow"))
        live_control_surface = payload.get("python_exam_live_control_surface", payload.get("live_control_surface"))
        evidence_preview = payload.get("python_exam_evidence_export_preview", payload.get("evidence_export_preview"))
        local_export_draft = payload.get("python_exam_confirmed_local_export_draft", payload.get("local_export_draft"))
        draft_review_console = payload.get(
            "python_exam_draft_package_review_console",
            payload.get("draft_package_review_console"),
        )
        human_handoff = payload.get("python_exam_human_handoff_packet", payload.get("human_handoff_packet"))
        for value, error in [
            (exam_skill_drilldown, "invalid-exam-skill-drilldown"),
            (local_review, "invalid-python-exam-local-cycle-readiness-review"),
            (local_handoff, "invalid-python-exam-local-cycle-readiness-handoff"),
            (local_workspace_card, "invalid-python-exam-local-cycle-operator-workspace-card"),
            (local_chain, "invalid-python-exam-local-cycle-chain-snapshot"),
            (exam_workspace_operator_run, "invalid-exam-workspace-operator-run"),
            (exam_workspace_session_console, "invalid-exam-workspace-session-console"),
            (exam_workspace_run_history, "invalid-exam-workspace-run-history-export-review"),
            (course_dashboard, "invalid-course-exam-coverage-dashboard"),
            (per_skill_router, "invalid-course-per-skill-action-router"),
            (routed_executor, "invalid-routed-action-executor"),
            (exam_run_packet, "invalid-exam-run-packet"),
            (exam_packet_timeline, "invalid-exam-packet-timeline"),
            (timeline_export_review_packet, "invalid-timeline-export-review-packet"),
            (timeline_export_receipt_journal_summary, "invalid-timeline-export-receipt-journal-summary"),
            (review_chain_integrity_check, "invalid-review-chain-integrity-check"),
            (readiness_console, "invalid-python-exam-readiness-console"),
            (cockpit_flow, "invalid-python-exam-cockpit-flow"),
            (live_control_surface, "invalid-python-exam-live-control-surface"),
            (evidence_preview, "invalid-python-exam-evidence-export-preview"),
            (local_export_draft, "invalid-python-exam-confirmed-local-export-draft"),
            (draft_review_console, "invalid-python-exam-draft-package-review-console"),
            (human_handoff, "invalid-python-exam-human-handoff-packet"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_full_local_rehearsal_pack(
            exam_skill_drilldown=exam_skill_drilldown,
            python_exam_local_cycle_readiness_review=local_review,
            python_exam_local_cycle_readiness_handoff=local_handoff,
            python_exam_local_cycle_operator_workspace_card=local_workspace_card,
            python_exam_local_cycle_chain_snapshot=local_chain,
            exam_workspace_operator_run=exam_workspace_operator_run,
            exam_workspace_session_console=exam_workspace_session_console,
            exam_workspace_run_history_export_review=exam_workspace_run_history,
            course_exam_coverage_dashboard=course_dashboard,
            course_per_skill_action_router=per_skill_router,
            routed_action_executor=routed_executor,
            exam_run_packet=exam_run_packet,
            exam_packet_timeline=exam_packet_timeline,
            timeline_export_review_packet=timeline_export_review_packet,
            timeline_export_receipt_journal_summary=timeline_export_receipt_journal_summary,
            review_chain_integrity_check=review_chain_integrity_check,
            python_exam_readiness_console=readiness_console,
            python_exam_cockpit_flow=cockpit_flow,
            python_exam_live_control_surface=live_control_surface,
            python_exam_evidence_export_preview=evidence_preview,
            python_exam_confirmed_local_export_draft=local_export_draft,
            python_exam_draft_package_review_console=draft_review_console,
            python_exam_human_handoff_packet=human_handoff,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-rehearsal-playback-gap-coach":
        full_rehearsal = payload.get(
            "python_exam_full_local_rehearsal_pack",
            payload.get("full_local_rehearsal_pack"),
        )
        if full_rehearsal is not None and not isinstance(full_rehearsal, dict):
            return 400, {"status": "invalid-python-exam-full-local-rehearsal-pack"}
        return 200, build_python_exam_rehearsal_playback_gap_coach(
            python_exam_full_local_rehearsal_pack=full_rehearsal,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop":
        gap_coach = payload.get(
            "python_exam_rehearsal_playback_gap_coach",
            payload.get("rehearsal_playback_gap_coach"),
        )
        if gap_coach is not None and not isinstance(gap_coach, dict):
            return 400, {"status": "invalid-python-exam-rehearsal-playback-gap-coach"}
        return 200, build_python_exam_gap_coach_guided_rehearsal_loop(
            python_exam_rehearsal_playback_gap_coach=gap_coach,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            requested_action_key=str(payload.get("requested_action_key", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-guided-loop-control-surface":
        guided_loop = payload.get(
            "python_exam_gap_coach_guided_rehearsal_loop",
            payload.get("gap_coach_guided_rehearsal_loop"),
        )
        gap_coach = payload.get(
            "python_exam_rehearsal_playback_gap_coach",
            payload.get("rehearsal_playback_gap_coach"),
        )
        for value, error in [
            (guided_loop, "invalid-python-exam-gap-coach-guided-rehearsal-loop"),
            (gap_coach, "invalid-python-exam-rehearsal-playback-gap-coach"),
        ]:
            if value is not None and not isinstance(value, dict):
                return 400, {"status": error}
        return 200, build_python_exam_guided_loop_control_surface(
            python_exam_gap_coach_guided_rehearsal_loop=guided_loop,
            python_exam_rehearsal_playback_gap_coach=gap_coach,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            operator_confirmed_dry_run_request=bool(payload.get("operator_confirmed_dry_run_request", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/python-exam-guided-session-playback-journal":
        control_surface = payload.get(
            "python_exam_guided_loop_control_surface",
            payload.get("guided_loop_control_surface"),
        )
        previous_surfaces = payload.get("previous_control_surfaces", [])
        if control_surface is not None and not isinstance(control_surface, dict):
            return 400, {"status": "invalid-python-exam-guided-loop-control-surface"}
        if previous_surfaces is not None and not isinstance(previous_surfaces, list):
            return 400, {"status": "invalid-previous-control-surfaces"}
        if isinstance(previous_surfaces, list) and any(not isinstance(item, dict) for item in previous_surfaces):
            return 400, {"status": "invalid-previous-control-surface-item"}
        return 200, build_python_exam_guided_session_playback_journal(
            python_exam_guided_loop_control_surface=control_surface,
            previous_control_surfaces=previous_surfaces,
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/exam-workspace/run-dry-run":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            cell_index = int(payload.get("cell_index", 0) or 0)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-numeric-parameter"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        study_receipt = payload.get("study_receipt")
        notebook = payload.get("notebook")
        material_files = payload.get("material_files", [])
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        if study_receipt is not None and not isinstance(study_receipt, dict):
            return 400, {"status": "invalid-study-receipt"}
        if notebook is not None and not isinstance(notebook, dict):
            return 400, {"status": "invalid-notebook"}
        if not isinstance(material_files, list):
            return 400, {"status": "invalid-material-files"}
        return 200, build_exam_workspace_run_dry_run(
            query=str(payload.get("query", payload.get("task", ""))),
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            receipt_journal_path=payload.get("receipt_journal_path", payload.get("journal_path")),
            private_manifest_path=payload.get("private_manifest_path"),
            manifest_apply_journal_path=payload.get("manifest_apply_journal_path"),
            tutor_index_path=payload.get("tutor_index_path"),
            tutor_index_journal_path=payload.get("tutor_index_journal_path"),
            ledger_path=payload.get("ledger_path"),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "strict")),
            notebook=notebook,
            notebook_content_base64=payload.get("notebook_content_base64"),
            notebook_filename=str(payload.get("notebook_filename", "exam_workspace_notebook.ipynb")),
            cell_index=cell_index,
            cell_id=payload.get("cell_id"),
            cell_type=str(payload.get("cell_type", "code")),
            cell_source=str(payload.get("cell_source", "")),
            notebook_work_sha256_override=str(payload.get("notebook_work_sha256_override", "")),
            material_files=material_files,
            student_reflection=str(payload.get("student_reflection", "")),
            study_receipt=study_receipt,
            operator_confirmed_exam_workspace_run=bool(payload.get("operator_confirmed_exam_workspace_run", False)),
            operator_confirmed_manifest_apply=bool(payload.get("operator_confirmed_manifest_apply", False)),
            operator_confirmed_tutor_index_build=bool(payload.get("operator_confirmed_tutor_index_build", False)),
            operator_confirmed_help_ledger_append=bool(payload.get("operator_confirmed_help_ledger_append", False)),
            operator_confirmed_exam_ledger_append=bool(payload.get("operator_confirmed_exam_ledger_append", False)),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/institutional-clearance/board":
        return 200, build_institutional_clearance_board(
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/institutional/profile":
        return 200, build_regulatory_profile(
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/institutional/presentation":
        return 200, build_institutional_presentation_packet(
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/institutional/presentation-markdown":
        packet = build_institutional_presentation_packet(
            public_safe=bool(payload.get("public_safe", True)),
        )
        return 200, {
            "status": packet["status"],
            "markdown": build_institutional_presentation_markdown(packet),
        }
    if path == "/api/unibot/institutional-clearance/validate":
        record = payload.get("record", payload)
        if not isinstance(record, dict):
            return 400, {"status": "invalid-record"}
        return 200, validate_clearance_record(record)
    if path == "/api/unibot/stakeholder/submission-bundle":
        return 200, build_stakeholder_submission_bundle(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/stakeholder/submission-bundle-markdown":
        return 200, {
            "status": "ok",
            "markdown": build_stakeholder_submission_markdown(
                course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
                base_path=payload.get("base_path") if payload.get("base_path") else None,
                review_policy=str(payload.get("review_policy", "staged")),
            ),
        }
    if path == "/api/unibot/stakeholder/decision-request":
        return 200, build_stakeholder_decision_request(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            lane_id=str(payload.get("lane_id", "rights_privacy_local_extraction")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/stakeholder/decision-request-markdown":
        return 200, {
            "status": "ok",
            "markdown": build_stakeholder_decision_request_markdown(
                course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
                lane_id=str(payload.get("lane_id", "rights_privacy_local_extraction")),
                base_path=payload.get("base_path") if payload.get("base_path") else None,
                review_policy=str(payload.get("review_policy", "staged")),
            ),
        }
    if path == "/api/unibot/stakeholder/decision-request/validate-receipt":
        receipt = payload.get("receipt", payload)
        if not isinstance(receipt, dict):
            return 400, {"status": "invalid-receipt"}
        return 200, validate_decision_request_receipt(receipt)
    if path == "/api/unibot/stakeholder/decision-journal/append":
        event = payload.get("event")
        if not isinstance(event, dict):
            return 400, {"status": "invalid-event"}
        stored = append_decision_request_journal_event(event, path=payload.get("journal_path"))
        return 200, {
            "status": stored["status"],
            "record": stored["record"],
            "storage": "local-only",
            "path": stored["path"],
        }
    if path == "/api/unibot/stakeholder/decision-journal/append-prepared-request":
        return 200, append_prepared_request_to_journal(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            lane_id=str(payload.get("lane_id", "rights_privacy_local_extraction")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            markdown=str(payload.get("markdown", "")),
            path=payload.get("journal_path"),
        )
    if path == "/api/unibot/stakeholder/decision-journal/list":
        return 200, read_decision_journal(path=payload.get("journal_path"), limit=payload.get("limit"))
    if path == "/api/unibot/stakeholder/decision-journal/summary":
        return 200, summarize_decision_journal(path=payload.get("journal_path"))
    if path == "/api/unibot/stakeholder/decision-state":
        extraction_record = payload.get("extraction_decision_record")
        exam_record = payload.get("exam_clearance_record")
        if extraction_record is not None and not isinstance(extraction_record, dict):
            return 400, {"status": "invalid-extraction-decision-record"}
        if exam_record is not None and not isinstance(exam_record, dict):
            return 400, {"status": "invalid-exam-clearance-record"}
        return 200, build_external_decision_state(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            extraction_decision_record=extraction_record,
            exam_clearance_record=exam_record,
            deployment_go_reference=payload.get("deployment_go_reference") if payload.get("deployment_go_reference") else None,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/stakeholder/decision-record-journal/append":
        record_type = str(payload.get("record_type", ""))
        record = payload.get("record")
        if record is not None and not isinstance(record, dict):
            return 400, {"status": "invalid-record"}
        return 200, append_external_decision_journal_record(
            record_type=record_type,
            record=record,
            deployment_go_reference=payload.get("deployment_go_reference") if payload.get("deployment_go_reference") else None,
            path=payload.get("decision_record_journal_path", payload.get("journal_path")),
        )
    if path == "/api/unibot/stakeholder/decision-record-journal/list":
        try:
            limit = int(payload.get("limit")) if payload.get("limit") is not None else None
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        return 200, read_external_decision_journal(
            path=payload.get("decision_record_journal_path", payload.get("journal_path")),
            limit=limit,
        )
    if path == "/api/unibot/stakeholder/decision-record-journal/summary":
        return 200, summarize_external_decision_journal(
            path=payload.get("decision_record_journal_path", payload.get("journal_path")),
        )
    if path == "/api/unibot/course/exam-scope":
        records = payload.get("records")
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, build_course_exam_scope(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            records=records,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/tutor-coverage-plan":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-files"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_course_tutor_coverage_plan(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            decision_record_journal_path=payload.get("decision_record_journal_path", payload.get("external_decision_journal_path")),
            receipts=receipts,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/study-session-plan":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            max_items = int(payload.get("max_items", 5) or 5)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        receipts, receipt_error = payload_receipts_with_journal(payload, "receipts")
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if receipt_error:
            return 400, {"status": receipt_error}
        return 200, build_course_study_session_plan(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            receipts=receipts,
            focus_query=str(payload.get("focus_query", payload.get("query", ""))),
            max_items=max_items,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/study-session-receipt/validate":
        receipt = payload.get("receipt", payload)
        if not isinstance(receipt, dict):
            return 400, {"status": "invalid-receipt"}
        expected_ids = payload.get("expected_task_ids")
        if expected_ids is not None and not isinstance(expected_ids, list):
            return 400, {"status": "invalid-expected-task-ids"}
        return 200, validate_study_session_receipt(
            receipt,
            expected_task_ids={str(item) for item in expected_ids} if expected_ids is not None else None,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/study-session-review-report":
        try:
            max_files = int(payload.get("max_files", 260) or 260)
            max_items = int(payload.get("max_items", 5) or 5)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-limit"}
        decision_record = payload.get("decision_record")
        extraction_receipts, extraction_receipt_error = payload_receipts_with_journal(
            payload,
            "extraction_receipts" if "extraction_receipts" in payload else "receipts",
        )
        study_receipts = payload.get("study_receipts", [])
        if decision_record is not None and not isinstance(decision_record, dict):
            return 400, {"status": "invalid-decision-record"}
        if extraction_receipt_error:
            return 400, {"status": "invalid-extraction-receipts"}
        if not isinstance(study_receipts, list):
            return 400, {"status": "invalid-study-receipts"}
        return 200, build_study_session_review_report(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            max_files=max_files,
            review_policy=str(payload.get("review_policy", "staged")),
            decision_record=decision_record,
            extraction_receipts=extraction_receipts,
            study_receipts=[item for item in study_receipts if isinstance(item, dict)],
            focus_query=str(payload.get("focus_query", payload.get("query", ""))),
            max_items=max_items,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/tutor/respond":
        records = payload.get("records")
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, course_tutor_response(
            query=str(payload.get("query", payload.get("task", ""))),
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            mode=str(payload.get("mode", "course_tutor_mode")),
            requested_help_level=str(payload.get("requested_help_level", "A2")),
            exam_status=str(payload.get("exam_status", "practice")),
            records=records,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/tutor/next-task":
        records = payload.get("records")
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, next_course_task(
            query=str(payload.get("query", payload.get("task", ""))),
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            records=records,
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/course/eval/run":
        return 200, run_course_tutor_eval()
    if path == "/api/unibot/orchestration/command-center":
        return 200, build_unibot_command_center(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=payload.get("review_policy"),
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/orchestration/context-packet":
        return 200, build_context_packet(
            role_id=str(payload.get("role_id", "")),
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
        )
    if path == "/api/unibot/orchestration/handoff/validate":
        handoff = payload.get("handoff", payload)
        if not isinstance(handoff, dict):
            return 400, {"status": "invalid-handoff"}
        return 200, validate_chat_handoff(handoff)
    if path == "/api/unibot/orchestration/command-center-markdown":
        return 200, {
            "status": "ok",
            "markdown": build_orchestration_markdown(
                course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
                base_path=payload.get("base_path") if payload.get("base_path") else None,
                review_policy=payload.get("review_policy"),
            ),
        }
    if path == "/api/exam/session/start":
        return 200, start_exam_gateway_session(payload)
    if path == "/api/exam/materials/import":
        return 200, import_exam_materials(payload)
    if path == "/api/exam/materials/freeze":
        return 200, freeze_exam_materials(payload)
    if path == "/api/exam/notebook/open":
        return 200, open_exam_notebook(payload)
    if path == "/api/exam/notebook/run-cell":
        return 200, run_exam_notebook_cell(payload)
    if path == "/api/exam/tutor/respond":
        return 200, exam_tutor_response(payload)
    if path == "/api/exam/ledger/append":
        return 200, append_exam_ledger_event(payload)
    if path == "/api/exam/export-package":
        return 200, export_exam_package(payload)
    if path == "/api/unibot/tasks/adaptive-plan":
        skill_state = payload.get("skill_state")
        records = payload.get("records")
        if skill_state is not None and not isinstance(skill_state, dict):
            return 400, {"status": "invalid-skill-state"}
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        try:
            max_tasks = int(payload.get("max_tasks", 3) or 3)
        except (TypeError, ValueError):
            return 400, {"status": "invalid-max-tasks"}
        return 200, generate_adaptive_practice_plan(
            skill_state=skill_state,
            material_records=records,
            max_tasks=max_tasks,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/redteam/run":
        return 200, run_redteam_smoke()
    if path == "/api/unibot/gretel-loop/run":
        return 200, run_gretel_unibot_loop(
            gretel_url=payload.get("gretel_url") if payload.get("gretel_url") else None,
            unibot_url=payload.get("unibot_url") if payload.get("unibot_url") else None,
            deepseek_live=bool(payload.get("deepseek_live", False)),
            deepseek_credential=payload.get("deepseek_credential") if payload.get("deepseek_credential") else None,
        )
    if path == "/api/unibot/gretel-glm-evolve/work-packet":
        return 200, build_glm_evolve_work_packet(
            work_id=str(payload.get("work_id", "unibot-open-science-gretel-glm-evolve-v1")),
            task_kind=str(payload.get("task_kind", "architecture_and_harness_proposal")),
            model_hint=str(payload.get("model_hint", "zai/glm-5.2")),
        )
    if path == "/api/unibot/gretel-glm-evolve/validate-proposal":
        proposal = payload.get("proposal", payload)
        if not isinstance(proposal, dict):
            return 400, {"status": "invalid-proposal"}
        return 200, validate_glm_evolve_proposal(proposal)
    if path == "/api/unibot/gretel-glm-evolve/markdown":
        return 200, {"status": "ok", "markdown": build_glm_evolve_markdown()}
    if path == "/api/unibot/gretel-glm-evolve/workboard":
        return 200, build_glm_rsi_workboard(
            work_id=str(payload.get("work_id", "unibot-glm-rsi-open-science-workboard-v1")),
            include_blocked_fixture=bool(payload.get("include_blocked_fixture", True)),
        )
    if path == "/api/unibot/paperclip/status":
        return 200, paperclip_status()
    if path == "/api/unibot/paperclip/evaluation-request":
        return 200, build_paperclip_evaluation_request(
            goal=str(payload.get("goal", "Review UniBot Socratic Mantel architecture and harness next steps.")),
            agent_role=str(payload.get("agent_role", "GLM Proposal Reviewer")),
            budget_class=str(payload.get("budget_class", "small")),
            model_hint=str(payload.get("model_hint", "zai/glm-5.2")),
        )
    if path == "/api/unibot/paperclip/validate-request":
        request = payload.get("request", payload)
        if not isinstance(request, dict):
            return 400, {"status": "invalid-request"}
        return 200, validate_paperclip_evaluation_request(request)
    if path == "/api/unibot/paperclip/markdown":
        return 200, {"status": "ok", "markdown": build_paperclip_evaluation_markdown()}
    if path == "/api/unibot/loop-lab/run":
        return 200, run_loop_lab(
            dataset=str(payload.get("dataset", "core25")),
            persist=bool(payload.get("persist", False)),
            compare_previous=bool(payload.get("compare_previous", True)),
            live_gretel_url=payload.get("gretel_url") if payload.get("gretel_url") else None,
            live_unibot_url=payload.get("unibot_url") if payload.get("unibot_url") else None,
            deepseek_live=bool(payload.get("deepseek_live", False)),
        )
    if path == "/api/unibot/demo-run":
        return 200, build_local_demo_run()
    if path == "/api/unibot/demo-run-markdown":
        return 200, {"status": "ok", "markdown": build_local_demo_markdown()}
    if path == "/api/unibot/demo-feedback/template":
        return 200, demo_feedback_template()
    if path == "/api/unibot/demo-feedback/validate":
        feedback = payload.get("feedback", payload)
        if not isinstance(feedback, dict):
            return 400, {"status": "invalid-feedback"}
        return 200, validate_demo_feedback(feedback)
    if path == "/api/unibot/demo-feedback/append":
        feedback = payload.get("feedback")
        if not isinstance(feedback, dict):
            return 400, {"status": "invalid-feedback"}
        return 200, append_demo_feedback(feedback, path=payload.get("feedback_path"))
    if path == "/api/unibot/demo-feedback/list":
        return 200, read_demo_feedback(path=payload.get("feedback_path"), limit=payload.get("limit"))
    if path == "/api/unibot/demo-feedback/summary":
        return 200, summarize_demo_feedback(path=payload.get("feedback_path"))
    if path == "/api/unibot/demo-feedback/public-summary":
        return 200, export_public_demo_feedback_summary(path=payload.get("feedback_path"))
    if path == "/api/unibot/demo-feedback/triage":
        records = payload.get("records")
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, build_feedback_triage(path=payload.get("feedback_path"), records=records)
    if path == "/api/unibot/demo-feedback/triage-markdown":
        records = payload.get("records")
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, {
            "status": "ok",
            "markdown": build_feedback_triage_markdown(path=payload.get("feedback_path"), records=records),
        }
    if path == "/api/unibot/github-issue-bundle":
        records = payload.get("records")
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, build_github_issue_bundle(path=payload.get("feedback_path"), records=records)
    if path == "/api/unibot/github-issue-bundle-markdown":
        records = payload.get("records")
        if records is not None and not isinstance(records, list):
            return 400, {"status": "invalid-records"}
        return 200, {
            "status": "ok",
            "markdown": build_github_issue_bundle_markdown(path=payload.get("feedback_path"), records=records),
        }
    if path == "/api/unibot/authority-packet":
        return 200, build_authority_handoff_packet(ledger_path=payload.get("ledger_path"))
    if path == "/api/unibot/authority-packet-markdown":
        return 200, {
            "status": "ok",
            "markdown": build_authority_handoff_markdown(ledger_path=payload.get("ledger_path")),
        }
    if path == "/api/unibot/evaluation-packet":
        return 200, build_evaluation_packet()
    if path == "/api/unibot/evaluation-packet-markdown":
        return 200, {"status": "ok", "markdown": build_evaluation_markdown()}
    if path == "/api/unibot/evaluation-tasks":
        return 200, {"status": "ok", "tasks": synthetic_tasks()}
    if path == "/api/unibot/pilot-protocol":
        return 200, build_pilot_protocol()
    if path == "/api/unibot/pilot-protocol-markdown":
        return 200, {"status": "ok", "markdown": build_pilot_protocol_markdown()}
    if path == "/api/unibot/pilot/clearance-receipt-template":
        return 200, build_controlled_pilot_clearance_receipt_template()
    if path == "/api/unibot/pilot/launch-gate":
        clearance_receipt = payload.get("clearance_receipt", payload)
        if not isinstance(clearance_receipt, dict):
            return 400, {
                "status": "invalid-clearance-receipt",
                "policy": "clearance_receipt must be a field-level object and must not contain raw approval text",
            }
        return 200, build_controlled_pilot_launch_gate(clearance_receipt=clearance_receipt)
    if path == "/api/unibot/data-protection-screening":
        return 200, build_data_protection_screening()
    if path == "/api/unibot/data-protection-screening-markdown":
        return 200, {"status": "ok", "markdown": build_data_protection_screening_markdown()}
    if path == "/api/unibot/review-board-packet":
        return 200, build_review_board_packet(
            python_exam_local_cycle_readiness_review=payload.get("python_exam_local_cycle_readiness_review", payload.get("readiness_review")),
            python_exam_local_cycle_readiness_handoff=payload.get("python_exam_local_cycle_readiness_handoff", payload.get("handoff")),
            python_exam_local_cycle_operator_workspace_card=payload.get(
                "python_exam_local_cycle_operator_workspace_card",
                payload.get("local_cycle_operator_workspace_card"),
            ),
            selected_skill_tag=str(payload.get("selected_skill_tag", "")),
        )
    if path == "/api/unibot/review-board-packet-markdown":
        return 200, {"status": "ok", "markdown": build_review_board_packet_markdown()}
    if path == "/api/unibot/bachelor-thesis-package":
        return 200, build_bachelor_thesis_package()
    if path == "/api/unibot/bachelor-thesis-markdown":
        return 200, {"status": "ok", "markdown": build_bachelor_thesis_markdown()}
    if path == "/api/unibot/autonomous-research-loop":
        return 200, build_autonomous_research_loop()
    if path == "/api/unibot/autonomous-research-markdown":
        return 200, {"status": "ok", "markdown": build_autonomous_research_markdown()}
    if path == "/api/unibot/publication-package":
        return 200, build_publication_package()
    if path == "/api/unibot/publication-package-markdown":
        return 200, {"status": "ok", "markdown": build_publication_markdown()}
    if path == "/api/unibot/readiness-check":
        return 200, run_readiness_check()
    if path == "/api/unibot/readiness-markdown":
        return 200, {"status": "ok", "markdown": build_readiness_markdown()}
    if path == "/api/unibot/completion-audit":
        extraction_record = payload.get("extraction_decision_record")
        exam_record = payload.get("exam_clearance_record")
        extraction_deferral_record = payload.get("extraction_deferral_record", payload.get("deferral_record"))
        external_decision_records = payload.get("external_decision_records")
        decision_record_journal_path = payload.get(
            "decision_record_journal_path",
            payload.get("external_decision_journal_path"),
        )
        extraction_receipts, extraction_receipt_error = payload_receipts_with_journal(payload, "extraction_receipts")
        if extraction_record is not None and not isinstance(extraction_record, dict):
            return 400, {"status": "invalid-extraction-decision-record"}
        if exam_record is not None and not isinstance(exam_record, dict):
            return 400, {"status": "invalid-exam-clearance-record"}
        if extraction_deferral_record is not None and not isinstance(extraction_deferral_record, dict):
            return 400, {"status": "invalid-extraction-deferral-record"}
        if external_decision_records is not None and not isinstance(external_decision_records, list):
            return 400, {"status": "invalid-external-decision-records"}
        if extraction_receipt_error:
            return 400, {"status": "invalid-extraction-receipts"}
        combined_external_decision_records = [
            item for item in (external_decision_records or []) if isinstance(item, dict)
        ]
        if decision_record_journal_path:
            journal_payload = read_external_decision_journal(path=str(decision_record_journal_path))
            combined_external_decision_records.extend(
                item for item in journal_payload.get("records", []) if isinstance(item, dict)
            )
        return 200, build_completion_audit(
            course_id=str(payload.get("course_id", "introduction-to-python-neuroscience-cologne")),
            base_path=payload.get("base_path") if payload.get("base_path") else None,
            review_policy=str(payload.get("review_policy", "staged")),
            extraction_decision_record=extraction_record,
            exam_clearance_record=exam_record,
            deployment_go_reference=payload.get("deployment_go_reference") if payload.get("deployment_go_reference") else None,
            extraction_receipts=extraction_receipts,
            extraction_deferral_record=extraction_deferral_record,
            external_decision_records=combined_external_decision_records,
            public_safe=bool(payload.get("public_safe", True)),
        )
    if path == "/api/unibot/release-runbook":
        return 200, build_release_runbook()
    if path == "/api/unibot/release-runbook-markdown":
        return 200, {"status": "ok", "markdown": build_release_runbook_markdown()}
    if path == "/api/unibot/source-cards":
        cards = list_source_cards(source_kind=payload.get("source_kind"))
        return 200, {"status": "ok", "count": len(cards), "source_cards": cards}
    if path == "/api/unibot/source-card-drift-report":
        return 200, build_source_card_drift_report()
    if path == "/api/unibot/source-card":
        source_id = str(payload.get("source_id", ""))
        card = get_source_card(source_id)
        if card is None:
            return 404, {"status": "not-found", "source_id": source_id}
        return 200, {"status": "ok", "source_card": card}
    if path == "/api/unibot/compliance-matrix":
        return 200, build_compliance_matrix()
    if path == "/api/unibot/compliance-matrix-markdown":
        return 200, {"status": "ok", "markdown": build_compliance_matrix_markdown()}
    if path == "/api/unibot/autonomy/provider/status":
        store = AutonomyStore()
        try:
            return 200, ProviderGate(store=store).status()
        finally:
            store.close()
    if path == "/api/unibot/autonomy/provider/park":
        store = AutonomyStore()
        try:
            return 200, ProviderGate(store=store).park()
        finally:
            store.close()
    if path == "/api/unibot/autonomy/provider/unpark":
        store = AutonomyStore()
        try:
            try:
                return 200, ProviderGate(store=store).unpark(str(payload.get("scope", "")))
            except ValueError as error:
                return 400, {"status": "blocked", "reason": str(error)}
        finally:
            store.close()
    if path == "/api/unibot/autonomy/doctor":
        store = AutonomyStore()
        try:
            return 200, {**autonomy_doctor(store), "rollout": store.rollout_status(), "watcher_active": False}
        finally:
            store.close()
    if path == "/api/unibot/autonomy/rollout/status":
        store = AutonomyStore()
        try:
            return 200, {
                "status": "ok",
                "rollout": store.rollout_status(),
                "recovered_runs": store.recover_interrupted_runs(),
                "watcher_active": False,
            }
        finally:
            store.close()
    if path == "/api/unibot/autonomy/work-item/claim":
        item_payload = payload.get("work_item", payload)
        if not isinstance(item_payload, dict):
            return 400, {"status": "blocked", "reason": "work_item_must_be_object"}
        try:
            item = WorkItemV3.from_dict(item_payload)
        except ValueError as error:
            return 400, {"status": "blocked", "reason": str(error)}
        store = AutonomyStore()
        try:
            store.save_work_item(item)
            return 200, {"status": "queued", "work_item": item.to_dict(), "automatic_merge": False}
        finally:
            store.close()
    if path == "/api/unibot/autonomy/audit":
        store = AutonomyStore()
        try:
            run = store.get_run(str(payload.get("run_id", "")))
            return (200 if run else 404), {"status": "ok" if run else "not_found", "run": run, "automatic_merge": False}
        finally:
            store.close()
    return 404, {"status": "not-found", "path": path}


class UniBotHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler: type[BaseHTTPRequestHandler],
        *,
        session_token: str | None = None,
        pairing_code: str | None = None,
        allowed_origins: set[str] | None = None,
    ) -> None:
        super().__init__(server_address, request_handler)
        self.session_token = session_token or secrets.token_urlsafe(32)
        self.pairing_code = pairing_code or f"{secrets.randbelow(100_000_000):08d}"
        self.pairing_expires_at = time.monotonic() + PAIRING_TTL_SECONDS
        self.pairing_attempts = 0
        self.allowed_origins = set(allowed_origins or set())
        self.paired_origin = ""
        session_hash = hashlib.sha256(self.session_token.encode("utf-8")).hexdigest()[:16]
        self.session_ledger_path = Path.cwd() / ".unibot" / "sessions" / f"{session_hash}.jsonl"
        self.learning_session: LearningSession | None = None


class UniBotRequestHandler(BaseHTTPRequestHandler):
    server_version = "UniBotGuardian/0.2"

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def do_OPTIONS(self) -> None:
        if not self._host_allowed():
            self._write_json(403, {"status": "blocked-host"})
            return
        origin = self.headers.get("Origin", "")
        path = urlparse(self.path).path
        if not self._origin_allowed(origin) and not (path == "/api/v2/pair" and self._pair_origin_allowed(origin)):
            self._write_json(403, {"status": "blocked-origin"})
            return
        self.send_response(204)
        self._send_cors_headers(origin, allow_pair_origin=path == "/api/v2/pair")
        self._send_security_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if not self._host_allowed():
            self._write_json(403, {"status": "blocked-host"})
            return
        path = urlparse(self.path).path
        if path not in {"/health", "/api/unibot/health", "/api/v2/health"}:
            if not self._request_authorized():
                return
        if path == "/api/v2/session":
            self._write_json(200, self._session_summary())
            return
        if path == "/api/v2/session/export":
            server = self._security_server()
            response = server.learning_session.report() if server and server.learning_session else self._session_summary()
            self._write_json(200, response)
            return
        status, response = route_request(self.path, method="GET")
        self._write_json(status, response)

    def do_POST(self) -> None:
        if not self._host_allowed():
            self._write_json(403, {"status": "blocked-host"})
            return
        payload = self._read_payload()
        if payload is None:
            return
        path = urlparse(self.path).path
        if path == "/api/v2/pair":
            self._handle_pair(payload)
            return
        if not self._request_authorized():
            return
        server = self._security_server()
        if path == "/api/v2/session/contracts":
            if server is None:
                self._write_json(503, {"status": "secure-server-configuration-required"})
                return
            try:
                server.learning_session = LearningSession.start(
                    payload,
                    storage_root=server.session_ledger_path.parent / "learning",
                )
            except ValueError as exc:
                self._write_json(400, {"status": "invalid-session-contract", "reason": str(exc)})
                return
            self._write_json(201, {"status": "active", "contract": server.learning_session.contract})
            return
        if path == "/api/v2/socratic/help" and server and server.learning_session:
            try:
                response = build_tutor_turn(server.learning_session, payload)
            except ValueError as exc:
                self._write_json(400, {"status": "tutor-turn-blocked", "reason": str(exc)})
                return
            self._write_json(200, response)
            return
        if path == "/api/v2/session/export":
            response = server.learning_session.report() if server and server.learning_session else self._session_summary()
            self._write_json(200, response)
            return
        if path == "/api/v2/session":
            self._write_json(200, self._session_summary())
            return
        status, response = route_request(self.path, payload=payload, method="POST")
        if path == "/api/v2/socratic/help" and status == 200 and isinstance(response.get("guardian_event"), dict):
            server = self._security_server()
            if server is None:
                self._write_json(503, {"status": "secure-server-configuration-required"})
                return
            stored = append_ledger_event(response["guardian_event"], path=server.session_ledger_path)
            response["session_ledger"] = {
                "status": stored["status"],
                "raw_output_stored": False,
                "local_path_returned": False,
            }
        self._write_json(status, response)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def _security_server(self) -> UniBotHTTPServer | None:
        return self.server if isinstance(self.server, UniBotHTTPServer) else None

    def _host_allowed(self) -> bool:
        host_header = self.headers.get("Host", "")
        try:
            hostname = urlparse(f"//{host_header}").hostname or ""
        except ValueError:
            return False
        server = self._security_server()
        bound_host = str(server.server_address[0]) if server else ""
        return hostname.lower() in {"127.0.0.1", "localhost", "::1", bound_host.lower()}

    def _origin_allowed(self, origin: str) -> bool:
        if not origin:
            return True
        server = self._security_server()
        return server is not None and origin in server.allowed_origins

    def _pair_origin_allowed(self, origin: str) -> bool:
        return not origin or bool(CHROME_EXTENSION_ORIGIN.fullmatch(origin))

    def _request_authorized(self) -> bool:
        server = self._security_server()
        if server is None:
            self._write_json(503, {"status": "secure-server-configuration-required"})
            return False
        origin = self.headers.get("Origin", "")
        if not self._origin_allowed(origin):
            self._write_json(403, {"status": "blocked-origin"})
            return False
        presented = self.headers.get("X-UniBot-Token", "")
        if not presented or not hmac.compare_digest(presented, server.session_token):
            self._write_json(401, {"status": "session-token-required"})
            return False
        return True

    def _read_payload(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            self._write_json(400, {"status": "invalid-content-length"})
            return None
        if length < 0 or length > MAX_REQUEST_BODY_BYTES:
            self._write_json(413, {"status": "request-body-too-large"})
            return None
        content_type = self.headers.get("Content-Type", "application/json").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._write_json(415, {"status": "application-json-required"})
            return None
        raw_body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._write_json(400, {"status": "invalid-json"})
            return None
        if not isinstance(payload, dict):
            self._write_json(400, {"status": "json-object-required"})
            return None
        return payload

    def _handle_pair(self, payload: dict[str, Any]) -> None:
        server = self._security_server()
        origin = self.headers.get("Origin", "")
        if server is None:
            self._write_json(503, {"status": "secure-server-configuration-required"})
            return
        if not self._pair_origin_allowed(origin):
            self._write_json(403, {"status": "blocked-origin"})
            return
        if time.monotonic() > server.pairing_expires_at:
            self._write_json(410, {"status": "pairing-code-expired"}, allow_pair_origin=True)
            return
        if server.pairing_attempts >= PAIRING_ATTEMPT_LIMIT:
            self._write_json(429, {"status": "pairing-attempt-limit"}, allow_pair_origin=True)
            return
        server.pairing_attempts += 1
        supplied_code = str(payload.get("pairing_code", ""))
        if not hmac.compare_digest(supplied_code, server.pairing_code):
            self._write_json(401, {"status": "invalid-pairing-code"}, allow_pair_origin=True)
            return
        if origin:
            server.allowed_origins = {origin}
            server.paired_origin = origin
        server.pairing_code = ""
        self._write_json(
            200,
            {
                "status": "paired",
                "session_token": server.session_token,
                "allowed_origin": server.paired_origin,
                "allowed_help_levels": list(HELP_LEVELS_V1),
                "exam_deployment_status": "not_cleared",
            },
            allow_pair_origin=True,
        )

    def _session_summary(self) -> dict[str, Any]:
        server = self._security_server()
        if server is None:
            return {"status": "secure-server-configuration-required"}
        summary = export_public_ledger_summary(path=server.session_ledger_path)
        response = {
            **summary,
            "status": "paired" if not server.pairing_code else "awaiting_pairing",
            "allowed_origin": server.paired_origin,
            "allowed_help_levels": list(HELP_LEVELS_V1),
            "exam_deployment_status": "not_cleared",
        }
        if server.learning_session:
            response["learning_contract"] = server.learning_session.contract
            response["learning_summary"] = server.learning_session.summary()
        return response

    def _send_cors_headers(self, origin: str, *, allow_pair_origin: bool = False) -> None:
        if origin and (self._origin_allowed(origin) or (allow_pair_origin and self._pair_origin_allowed(origin))):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type, x-unibot-token")

    def _send_security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")

    def _write_json(self, status: int, response: dict[str, Any], *, allow_pair_origin: bool = False) -> None:
        body = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers(self.headers.get("Origin", ""), allow_pair_origin=allow_pair_origin)
        self._send_security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    session_token: str | None = None,
    pairing_code: str | None = None,
    allowed_origins: set[str] | None = None,
) -> UniBotHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("UniBot API may bind to loopback only")
    return UniBotHTTPServer(
        (host, port),
        UniBotRequestHandler,
        session_token=session_token,
        pairing_code=pairing_code,
        allowed_origins=allowed_origins,
    )


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, *, show_pairing_code: bool = True) -> None:
    server = create_server(host, port)
    print(f"UniBot Guardian local API listening on http://{host}:{server.server_address[1]}")
    if show_pairing_code:
        print(f"One-time pairing code: {server.pairing_code}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the separate UniBot Guardian local API.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", default=DEFAULT_PORT, type=int)
    parser.add_argument("--pair", action="store_true", help="show the one-time browser pairing code")
    args = parser.parse_args()
    run(args.host, args.port, show_pairing_code=True)


if __name__ == "__main__":
    main()
