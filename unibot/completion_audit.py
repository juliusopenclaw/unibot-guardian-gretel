from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .clearance import build_institutional_clearance_board
from .course_tutor import DEFAULT_COURSE_ID, build_course_material_compiler_plan, safe_course_id
from .decision_journal import sanitize_decision_journal_event
from .decision_request import build_stakeholder_decision_request, build_stakeholder_decision_request_markdown
from .decision_state import build_external_decision_state
from .extraction_decision import build_extraction_decision_packet
from .extraction import build_course_extraction_queue
from .extraction_batches import build_extraction_batch_plan, build_extraction_batch_receipt_packet
from .extraction_completion import build_extraction_completion_report, validate_extraction_deferral_record
from .extraction_manifest_update import build_extraction_manifest_update_plan
from .extraction_operator import build_extraction_operator_packet
from .extraction_progress import build_extraction_progress_report
from .extraction_receipt_journal import sanitize_extraction_receipt_record, summarize_extraction_receipt_records
from .external_decision_journal import sanitize_external_decision_journal_record, summarize_external_decision_records
from .materials import sha256_text
from .orchestration import build_unibot_command_center
from .public_safety import scan_text
from .readiness import run_readiness_check
from .release_runbook import build_release_runbook
from .submission import build_stakeholder_submission_bundle
from .study_session import build_course_study_session_plan, build_study_session_review_report, validate_study_session_receipt
from .tutor_coverage import build_course_tutor_coverage_plan


COMPLETION_AUDIT_SCHEMA_VERSION = "unibot-completion-audit-v1"
ROOT = Path(__file__).resolve().parents[1]


def build_completion_audit(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    review_policy: str = "staged",
    extraction_decision_record: dict[str, Any] | None = None,
    exam_clearance_record: dict[str, Any] | None = None,
    deployment_go_reference: str | None = None,
    extraction_receipts: list[dict[str, Any]] | None = None,
    extraction_deferral_record: dict[str, Any] | None = None,
    external_decision_records: list[dict[str, Any]] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    readiness = run_readiness_check()
    command_center = build_unibot_command_center(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    release_runbook = build_release_runbook()
    compiler = build_course_material_compiler_plan(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    extraction_queue = build_course_extraction_queue(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    decision_packet = build_extraction_decision_packet(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    clearance_board = build_institutional_clearance_board(public_safe=public_safe)
    operator_packet = build_extraction_operator_packet(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    submission_bundle = build_stakeholder_submission_bundle(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    decision_request = build_stakeholder_decision_request(
        course_id,
        lane_id="rights_privacy_local_extraction",
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    decision_request_markdown = build_stakeholder_decision_request_markdown(
        course_id,
        lane_id="rights_privacy_local_extraction",
        base_path=base_path,
        review_policy=review_policy,
    )
    journal_request_record = sanitize_decision_journal_event(
        {
            "event_type": "decision_request_prepared",
            "request": decision_request,
            "markdown": decision_request_markdown,
        }
    )
    journal_receipt = dict(decision_request.get("receipt_template", {}))
    journal_receipt.update(
        {
            "manual_submission_status": "sent_for_human_review",
            "channel": "manual review channel",
            "submission_reference": "synthetic journal audit receipt reference",
        }
    )
    journal_receipt_record = sanitize_decision_journal_event(
        {
            "event_type": "decision_request_receipt_validated",
            "receipt": journal_receipt,
        }
    )
    decision_state = build_external_decision_state(
        course_id,
        extraction_decision_record=extraction_decision_record,
        exam_clearance_record=exam_clearance_record,
        deployment_go_reference=deployment_go_reference,
        public_safe=public_safe,
    )
    external_decision_summary = summarize_external_decision_records(
        external_decision_records or [],
        status="ok" if external_decision_records else "empty",
    )
    progress_report = build_extraction_progress_report(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=extraction_decision_record,
        receipts=extraction_receipts or [],
        public_safe=public_safe,
    )
    journal_decision_record = extraction_decision_record or audit_extraction_decision_record()
    journal_receipt = {
        "job_id": "audit-extraction-job",
        "material_id": "audit-extraction-material",
        "job_type": "ocr",
        "extraction_status": "extracted_private",
        "raw_text_sha256": "e" * 64,
        "extracted_text_char_count": 512,
        "private_artifact_reference": "synthetic private extraction audit artifact",
        "human_review_status": "pending_review",
        "decision_reference_hash": sha256_text(str(journal_decision_record.get("decision_reference", ""))),
    }
    extraction_receipt_journal_record = sanitize_extraction_receipt_record(
        journal_receipt,
        decision_record=journal_decision_record,
    )
    extraction_receipt_journal_summary = summarize_extraction_receipt_records(
        [extraction_receipt_journal_record],
        status="ok",
    )
    completion_harness_deferral = audit_extraction_deferral_record()
    extraction_completion_harness = build_extraction_completion_report(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=journal_decision_record,
        receipts=extraction_receipts or [],
        deferral_record=completion_harness_deferral,
        public_safe=public_safe,
    )
    extraction_deferral_validation = validate_extraction_deferral_record(
        completion_harness_deferral,
        public_safe=public_safe,
    )
    external_decision_journal_exam_record = sanitize_external_decision_journal_record(
        record_type="exam_clearance",
        record=audit_exam_clearance_record(),
    )
    external_decision_journal_deferral_record = sanitize_external_decision_journal_record(
        record_type="extraction_deferral",
        record=completion_harness_deferral,
    )
    external_decision_journal_summary = summarize_external_decision_records(
        [external_decision_journal_exam_record, external_decision_journal_deferral_record],
        status="ok",
    )
    extraction_completion_report = build_extraction_completion_report(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=extraction_decision_record,
        receipts=extraction_receipts or [],
        deferral_record=extraction_deferral_record,
        public_safe=public_safe,
    )
    batch_plan = build_extraction_batch_plan(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=extraction_decision_record,
        receipts=extraction_receipts or [],
        public_safe=public_safe,
    )
    batch_receipt_packet = build_extraction_batch_receipt_packet(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=extraction_decision_record,
        receipts=extraction_receipts or [],
        public_safe=public_safe,
    )
    manifest_update_plan = build_extraction_manifest_update_plan(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=extraction_decision_record,
        receipts=extraction_receipts or [],
        public_safe=public_safe,
    )
    tutor_coverage_plan = build_course_tutor_coverage_plan(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=extraction_decision_record,
        receipts=extraction_receipts or [],
        public_safe=public_safe,
    )
    study_session_plan = build_course_study_session_plan(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=extraction_decision_record,
        receipts=extraction_receipts or [],
        public_safe=public_safe,
    )
    synthetic_study_receipt = {
        "task_id": (study_session_plan.get("tasks") or [{"task_id": "audit-study-task"}])[0].get("task_id", "audit-study-task"),
        "skill_tag": (study_session_plan.get("tasks") or [{"skill_tag": "pandas"}])[0].get("skill_tag", "pandas"),
        "source_anchor_id": "audit-source-anchor",
        "prediction_present": True,
        "retrieval_response_present": True,
        "notebook_action_present": True,
        "reflection": "Ich pruefe den kleinsten naechsten Schritt.",
        "help_level": "A2",
    }
    study_receipt_validation = validate_study_session_receipt(
        synthetic_study_receipt,
        expected_task_ids={task.get("task_id", "") for task in study_session_plan.get("tasks", []) if task.get("task_id")}
        or None,
        public_safe=public_safe,
    )
    study_review_report = build_study_session_review_report(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        decision_record=extraction_decision_record,
        extraction_receipts=extraction_receipts or [],
        study_receipts=[synthetic_study_receipt],
        public_safe=public_safe,
    )
    counts = compiler.get("counts", {})
    extraction_open = int(counts.get("ocr_queue_count", 0) or 0) + int(counts.get("transcription_queue_count", 0) or 0)
    sidepanel = sidepanel_pm_status()

    external_gate_summary = external_decision_summary.get("gate_summary", {})
    external_deferral_summary = external_decision_summary.get("extraction_deferral_summary", {})
    local_cycle_chain_steps = [
        "P1 Local Cycle Readiness Review and confirmation routing",
        "P1 Readiness handoff and operator-run prefill",
        "P1 Local Cycle Operator Workspace Card and manual cycle preview",
        "P1 Local Cycle Chain Snapshot and evidence-chain preview",
        "P1 Manual Confirmation Console for local cycle stop-go review",
        "P1 Manual Cycle Launch Receipt for final local-cycle stop-go evidence",
        "P1 Manual Cycle Evidence Binder for hash-only pre/post cycle review",
        "P1 Manual Post-Cycle Receipt Intake for human-run hash evidence",
        "P1 Manual Cycle Closure Ledger for hash-only cycle closure",
        "P1 Manual Cycle Review Timeline for chronological hash review",
        "P1 Manual Cycle Review Packet for compact human review",
        "P1 Manual Review Export Preview without export write",
        "P1 Manual Review Export Authorization Gate before export review",
        "P1 Manual Export Review Queue for hash-only candidate review",
        "P1 Manual Export Reviewer Packet for human review",
        "P1 Manual Archive Decision Draft without archive or submission",
        "P1 Manual Final Review Handoff before any export archive or submission",
        "P1 Manual Final Review Receipt Ledger for chronological hash review",
        "P1 Final Review Ledger Integrity Gate before export archive or submission proximity",
        "P1 Final Manual Review Console for one human-readable hash-only view",
        "P1 Final Manual Review Action Lock before export archive or submission proximity",
        "P1 Locked Final Review Board for one final human hash-only review",
        "P1 Locked Final Review Gap Resolver for one safe human follow-up",
        "P1 Full Local Rehearsal Pack for end-to-end Python exam dry-run review",
        "P1 Rehearsal Playback Gap Coach for safe next-action selection",
        "P1 Gap-Coach Guided Rehearsal Loop for next-step preparation",
        "P1 Guided Loop Control Surface for visible next-click review",
    ]
    command_center_sequence = [str(item) for item in command_center.get("workstream_sequence", []) or []]
    command_center_chain_present = all(item in command_center_sequence for item in local_cycle_chain_steps)
    runbook_quickstart_steps = release_runbook.get("quickstart_steps", []) if isinstance(release_runbook.get("quickstart_steps"), list) else []
    runbook_chain_step_ids = [str(item.get("step_id", "")) for item in runbook_quickstart_steps if isinstance(item, dict)]
    runbook_chain_commands = [str(item.get("command", "")) for item in runbook_quickstart_steps if isinstance(item, dict)]
    runbook_chain_present = (
        "review_python_exam_local_cycle_readiness_review" in runbook_chain_step_ids
        and "handoff_python_exam_local_cycle_readiness" in runbook_chain_step_ids
        and "review_python_exam_local_cycle_operator_workspace_card" in runbook_chain_step_ids
        and "review_python_exam_local_cycle_chain_snapshot" in runbook_chain_step_ids
        and "review_python_exam_local_cycle_manual_confirmation_console" in runbook_chain_step_ids
        and "review_python_exam_manual_cycle_launch_receipt" in runbook_chain_step_ids
        and "review_python_exam_manual_cycle_evidence_binder" in runbook_chain_step_ids
        and "review_python_exam_manual_post_cycle_receipt_intake" in runbook_chain_step_ids
        and "review_python_exam_manual_cycle_closure_ledger" in runbook_chain_step_ids
        and "review_python_exam_manual_cycle_review_timeline" in runbook_chain_step_ids
        and "review_python_exam_manual_cycle_review_packet" in runbook_chain_step_ids
        and "review_python_exam_manual_review_export_preview" in runbook_chain_step_ids
        and "review_python_exam_manual_review_export_authorization_gate" in runbook_chain_step_ids
        and "review_python_exam_manual_export_review_queue" in runbook_chain_step_ids
        and "review_python_exam_manual_export_reviewer_packet" in runbook_chain_step_ids
        and "review_python_exam_manual_archive_decision_draft" in runbook_chain_step_ids
        and "review_python_exam_manual_final_review_handoff" in runbook_chain_step_ids
        and "review_python_exam_manual_final_review_receipt_ledger" in runbook_chain_step_ids
        and "review_python_exam_final_review_ledger_integrity_gate" in runbook_chain_step_ids
        and "review_python_exam_final_manual_review_console" in runbook_chain_step_ids
        and "review_python_exam_final_manual_review_action_lock" in runbook_chain_step_ids
        and "review_python_exam_locked_final_review_board" in runbook_chain_step_ids
        and "review_python_exam_locked_final_review_gap_resolver" in runbook_chain_step_ids
        and "review_python_exam_full_local_rehearsal_pack" in runbook_chain_step_ids
        and "review_python_exam_rehearsal_playback_gap_coach" in runbook_chain_step_ids
        and "run_python_exam_gap_coach_guided_rehearsal_loop" in runbook_chain_step_ids
        and "review_python_exam_guided_loop_control_surface" in runbook_chain_step_ids
        and "POST /api/unibot/course/python-exam-local-cycle-operator-workspace-card" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-local-cycle-chain-snapshot" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-local-cycle-manual-confirmation-console" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-cycle-launch-receipt" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-cycle-evidence-binder" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-post-cycle-receipt-intake" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-cycle-closure-ledger" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-cycle-review-timeline" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-cycle-review-packet" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-review-export-preview" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-review-export-authorization-gate" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-export-review-queue" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-export-reviewer-packet" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-archive-decision-draft" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-final-review-handoff" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-manual-final-review-receipt-ledger" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-final-review-ledger-integrity-gate" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-final-manual-review-console" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-final-manual-review-action-lock" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-locked-final-review-board" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-locked-final-review-gap-resolver" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-full-local-rehearsal-pack" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-rehearsal-playback-gap-coach" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop" in runbook_chain_commands
        and "POST /api/unibot/course/python-exam-guided-loop-control-surface" in runbook_chain_commands
        and release_runbook.get("status") == "public_draft_runbook_not_exam_release"
        and release_runbook.get("exam_deployment_status") == "not_cleared"
    )
    required_deferred_types: set[str] = set()
    if int(counts.get("ocr_queue_count", 0) or 0) > 0:
        required_deferred_types.add("ocr")
    if int(counts.get("transcription_queue_count", 0) or 0) > 0:
        required_deferred_types.add("transcription")
    journal_deferred_types = set(str(item) for item in external_deferral_summary.get("deferred_job_types", []) or [])
    journal_deferral_covers_required = (
        bool(required_deferred_types)
        and external_gate_summary.get("extraction_deferral_record_valid") is True
        and required_deferred_types.issubset(journal_deferred_types)
    )
    extraction_completion_status = str(extraction_completion_report.get("status", "unknown"))
    extraction_completion_accepted = extraction_completion_status in {
        "complete_no_open_extraction_jobs",
        "complete_by_reviewed_receipts",
        "complete_intentionally_deferred",
    }
    course_material_extraction_complete = extraction_completion_accepted or journal_deferral_covers_required
    exam_clearance_record_valid = (
        decision_state.get("gate_summary", {}).get("exam_clearance_record_valid") is True
        or external_gate_summary.get("exam_clearance_record_valid") is True
    )

    requirements = [
        requirement(
            "orchestration_command_center",
            "Project manager command center, role lanes, handoff contract, and acceptance gates exist.",
            command_center.get("status") == "ready_to_orchestrate"
            and command_center.get("public_safety_status") == "pass"
            and len(command_center.get("role_lanes", [])) >= 7,
            "passed",
            {
                "status": command_center.get("status"),
                "role_lane_count": len(command_center.get("role_lanes", [])),
                "public_safety_status": command_center.get("public_safety_status"),
            },
        ),
        requirement(
            "local_cycle_stop_and_go_chain",
            "Command center and release runbook expose the Local Cycle Review -> Handoff -> Workspace Card stop-and-go chain.",
            command_center_chain_present and runbook_chain_present,
            "passed",
            {
                "command_center_workstream_sequence": command_center_sequence,
                "command_center_chain_present": command_center_chain_present,
                "runbook_quickstart_step_ids": runbook_chain_step_ids,
                "runbook_quickstart_commands": runbook_chain_commands,
                "runbook_chain_present": runbook_chain_present,
                "release_runbook_status": release_runbook.get("status"),
                "release_runbook_exam_deployment_status": release_runbook.get("exam_deployment_status"),
            },
        ),
        requirement(
            "three_golden_rules",
            "Project-management and safety golden rules are explicit and active.",
            len(command_center.get("golden_rules", {}).get("project_management", [])) == 3
            and len(command_center.get("golden_rules", {}).get("safety", [])) == 3,
            "passed",
            {
                "pm_rule_count": len(command_center.get("golden_rules", {}).get("project_management", [])),
                "safety_rule_count": len(command_center.get("golden_rules", {}).get("safety", [])),
            },
        ),
        requirement(
            "public_draft_readiness",
            "Public-safe draft and local practice demo are ready.",
            readiness.get("status") == "public_draft_ready" and readiness.get("failed_count") == 0,
            "passed",
            {
                "status": readiness.get("status"),
                "passed_count": readiness.get("passed_count"),
                "check_count": readiness.get("check_count"),
                "public_safety_findings": public_safety_findings(readiness),
            },
        ),
        requirement(
            "sidepanel_pm_flow",
            "Browser side panel exposes Command Center, compiler plan, and context packet flow.",
            sidepanel["status"] == "present",
            "passed",
            sidepanel,
        ),
        requirement(
            "course_material_compiler",
            "Course-material compiler creates safe queues for reviewed tutor anchors, OCR, transcription, and quarantine.",
            compiler.get("public_safety_status") == "pass"
            and "private_tutor_index_count" in counts
            and "solution_or_exam_quarantine_count" in counts,
            "passed",
            {
                "compiler_status": compiler.get("status"),
                "public_safety_status": compiler.get("public_safety_status"),
                "counts": counts,
            },
        ),
        requirement(
            "course_extraction_pipeline",
            "Private-only OCR/transcription queue and rights gate exist before processing course media.",
            extraction_queue.get("artifact_type") == "course_extraction_queue"
            and extraction_queue.get("public_safety_status") == "pass"
            and "rights_gate" in extraction_queue
            and "job_count" in extraction_queue.get("counts", {}),
            "failed",
            {
                "status": extraction_queue.get("status"),
                "public_safety_status": extraction_queue.get("public_safety_status"),
                "job_count": extraction_queue.get("counts", {}).get("job_count", 0),
                "blocked_until_rights_decision_count": extraction_queue.get("counts", {}).get("blocked_until_rights_decision_count", 0),
                "rights_authorized": extraction_queue.get("rights_gate", {}).get("authorized", False),
            },
        ),
        requirement(
            "course_extraction_decision_packet",
            "Rights/privacy decision packet exists before any local OCR/transcription processing.",
            decision_packet.get("artifact_type") == "course_extraction_rights_privacy_decision_packet"
            and decision_packet.get("public_safety_status") == "pass"
            and len(decision_packet.get("required_reviewer_roles", [])) >= 3,
            "failed",
            {
                "status": decision_packet.get("status"),
                "public_safety_status": decision_packet.get("public_safety_status"),
                "required_reviewer_roles": decision_packet.get("required_reviewer_roles", []),
            },
        ),
        requirement(
            "institutional_clearance_workflow",
            "Stakeholder clearance board and record validator exist before any real pilot or exam authority switch.",
            clearance_board.get("artifact_type") == "unibot_institutional_clearance_board"
            and clearance_board.get("public_safety_status") == "pass"
            and clearance_board.get("exam_deployment_status") == "not_cleared"
            and len(clearance_board.get("scope_lanes", [])) >= 4,
            "failed",
            {
                "status": clearance_board.get("status"),
                "public_safety_status": clearance_board.get("public_safety_status"),
                "exam_deployment_status": clearance_board.get("exam_deployment_status"),
                "scope_lane_count": len(clearance_board.get("scope_lanes", [])),
            },
        ),
        requirement(
            "course_extraction_operator_harness",
            "A gated operator packet and receipt contract exist for future local OCR/transcription runs.",
            operator_packet.get("artifact_type") == "course_extraction_operator_packet"
            and operator_packet.get("public_safety_status") == "pass"
            and operator_packet.get("exam_deployment_status") == "not_cleared"
            and "receipt_contract" in operator_packet,
            "failed",
            {
                "status": operator_packet.get("status"),
                "public_safety_status": operator_packet.get("public_safety_status"),
                "exam_deployment_status": operator_packet.get("exam_deployment_status"),
                "job_batch_count": operator_packet.get("job_batch_count", 0),
                "decision_validation_status": operator_packet.get("decision_validation", {}).get("status"),
            },
        ),
        requirement(
            "stakeholder_submission_bundle",
            "A public-safe submission bundle exists for the two remaining human decision gates.",
            submission_bundle.get("artifact_type") == "unibot_stakeholder_submission_bundle"
            and submission_bundle.get("public_safety_status") == "pass"
            and submission_bundle.get("exam_deployment_status") == "not_cleared"
            and len(submission_bundle.get("decision_lanes", [])) >= 2,
            "failed",
            {
                "status": submission_bundle.get("status"),
                "public_safety_status": submission_bundle.get("public_safety_status"),
                "exam_deployment_status": submission_bundle.get("exam_deployment_status"),
                "decision_lane_count": len(submission_bundle.get("decision_lanes", [])),
                "open_external_gates": submission_bundle.get("open_external_gates", []),
            },
        ),
        requirement(
            "stakeholder_decision_request_harness",
            "A lane-specific public-safe manual decision request, Markdown review export, and receipt template exist before contacting reviewers.",
            decision_request.get("artifact_type") == "unibot_stakeholder_decision_request"
            and decision_request.get("public_safety_status") == "pass"
            and decision_request.get("status") == "ready_for_manual_review_not_sent"
            and decision_request.get("exam_deployment_status") == "not_cleared"
            and decision_request.get("receipt_template", {}).get("tool_sent_message") is False
            and "# UniBot Stakeholder Decision Request" in decision_request_markdown,
            "failed",
            {
                "status": decision_request.get("status"),
                "lane_id": decision_request.get("lane_id"),
                "public_safety_status": decision_request.get("public_safety_status"),
                "exam_deployment_status": decision_request.get("exam_deployment_status"),
                "request_id_present": bool(decision_request.get("request_id")),
                "receipt_status": decision_request.get("receipt_template", {}).get("manual_submission_status"),
                "markdown_review_export_present": "# UniBot Stakeholder Decision Request" in decision_request_markdown,
            },
        ),
        requirement(
            "stakeholder_decision_journal_harness",
            "A local hash-only journal can record prepared stakeholder requests and validated manual request receipts without raw messages.",
            journal_request_record.get("artifact_type") == "unibot_stakeholder_decision_journal_record"
            and journal_request_record.get("status") == "accepted"
            and journal_request_record.get("public_safety_status") == "pass"
            and journal_receipt_record.get("status") == "accepted"
            and journal_receipt_record.get("public_safety_status") == "pass"
            and journal_receipt_record.get("event", {}).get("raw_submission_reference_stored") is False,
            "failed",
            {
                "request_record_status": journal_request_record.get("status"),
                "receipt_record_status": journal_receipt_record.get("status"),
                "request_event_type": journal_request_record.get("event", {}).get("event_type"),
                "receipt_event_type": journal_receipt_record.get("event", {}).get("event_type"),
                "public_safety_statuses": [
                    journal_request_record.get("public_safety_status"),
                    journal_receipt_record.get("public_safety_status"),
                ],
                "raw_text_stored": bool(journal_request_record.get("event", {}).get("raw_text_stored"))
                or bool(journal_receipt_record.get("event", {}).get("raw_text_stored")),
            },
        ),
        requirement(
            "external_decision_state_harness",
            "Incoming written decision records can be validated and summarized without exposing raw decisions.",
            decision_state.get("artifact_type") == "unibot_external_decision_state"
            and decision_state.get("public_safety_status") == "pass"
            and decision_state.get("exam_deployment_status") == "not_cleared",
            "failed",
            {
                "status": decision_state.get("status"),
                "public_safety_status": decision_state.get("public_safety_status"),
                "local_extraction_status": decision_state.get("local_extraction_decision", {}).get("status"),
                "exam_authority_status": decision_state.get("exam_authority_decision", {}).get("status"),
                "exam_deployment_status": decision_state.get("exam_deployment_status"),
            },
        ),
        requirement(
            "external_decision_record_journal_harness",
            "Validated incoming decision records can be stored as local hash-only evidence without raw written decisions or deployment side effects.",
            external_decision_journal_exam_record.get("artifact_type") == "unibot_external_decision_record_journal_record"
            and external_decision_journal_exam_record.get("status") == "accepted"
            and external_decision_journal_exam_record.get("public_safety_status") == "pass"
            and external_decision_journal_exam_record.get("event", {}).get("raw_record_stored") is False
            and external_decision_journal_deferral_record.get("status") == "accepted"
            and external_decision_journal_summary.get("artifact_type") == "unibot_external_decision_record_journal_summary"
            and external_decision_journal_summary.get("public_safety_status") == "pass"
            and external_decision_journal_summary.get("gate_summary", {}).get("exam_clearance_record_valid") is True
            and external_decision_journal_summary.get("gate_summary", {}).get("extraction_deferral_record_valid") is True
            and external_decision_journal_summary.get("gate_summary", {}).get("exam_deployment_status") == "not_cleared",
            "failed",
            {
                "exam_record_status": external_decision_journal_exam_record.get("status"),
                "deferral_record_status": external_decision_journal_deferral_record.get("status"),
                "summary_status": external_decision_journal_summary.get("status"),
                "public_safety_statuses": [
                    external_decision_journal_exam_record.get("public_safety_status"),
                    external_decision_journal_deferral_record.get("public_safety_status"),
                    external_decision_journal_summary.get("public_safety_status"),
                ],
                "raw_record_stored": external_decision_journal_exam_record.get("event", {}).get("raw_record_stored"),
                "exam_deployment_status": external_decision_journal_summary.get("gate_summary", {}).get("exam_deployment_status"),
            },
        ),
        requirement(
            "course_extraction_progress_harness",
            "Extraction receipts can be aggregated into a public-safe human review queue and manifest-update candidates.",
            progress_report.get("artifact_type") == "course_extraction_progress_report"
            and progress_report.get("public_safety_status") == "pass"
            and progress_report.get("exam_deployment_status") == "not_cleared",
            "failed",
            {
                "status": progress_report.get("status"),
                "public_safety_status": progress_report.get("public_safety_status"),
                "receipt_count": progress_report.get("receipt_summary", {}).get("receipt_count", 0),
                "ready_for_human_review_count": progress_report.get("receipt_summary", {}).get("ready_for_human_review_count", 0),
                "eligible_for_private_tutor_index_count": progress_report.get("receipt_summary", {}).get("eligible_for_private_tutor_index_count", 0),
            },
        ),
        requirement(
            "course_extraction_receipt_journal_harness",
            "Validated extraction receipts can be stored in a local hash-only journal and summarized without raw course text.",
            extraction_receipt_journal_record.get("artifact_type") == "course_extraction_receipt_journal_record"
            and extraction_receipt_journal_record.get("status") == "accepted"
            and extraction_receipt_journal_record.get("public_safety_status") == "pass"
            and extraction_receipt_journal_record.get("event", {}).get("raw_text_stored") is False
            and extraction_receipt_journal_summary.get("artifact_type") == "course_extraction_receipt_journal_summary"
            and extraction_receipt_journal_summary.get("public_safety_status") == "pass"
            and extraction_receipt_journal_summary.get("progress_receipt_count", 0) == 1,
            "failed",
            {
                "record_status": extraction_receipt_journal_record.get("status"),
                "summary_status": extraction_receipt_journal_summary.get("status"),
                "public_safety_statuses": [
                    extraction_receipt_journal_record.get("public_safety_status"),
                    extraction_receipt_journal_summary.get("public_safety_status"),
                ],
                "raw_text_stored": extraction_receipt_journal_record.get("event", {}).get("raw_text_stored"),
                "progress_receipt_count": extraction_receipt_journal_summary.get("progress_receipt_count", 0),
            },
        ),
        requirement(
            "course_extraction_completion_harness",
            "Extraction completion can be classified from reviewed receipts or a valid intentional deferral record without raw text.",
            extraction_completion_harness.get("artifact_type") == "course_extraction_completion_report"
            and extraction_completion_harness.get("public_safety_status") == "pass"
            and extraction_completion_harness.get("exam_deployment_status") == "not_cleared"
            and extraction_deferral_validation.get("artifact_type") == "course_extraction_deferral_validation"
            and extraction_deferral_validation.get("status") == "ok_extraction_deferral_record"
            and extraction_deferral_validation.get("public_safety_status") == "pass"
            and extraction_deferral_validation.get("raw_decision_reference_stored") is False,
            "failed",
            {
                "completion_status": extraction_completion_harness.get("status"),
                "deferral_status": extraction_deferral_validation.get("status"),
                "public_safety_statuses": [
                    extraction_completion_harness.get("public_safety_status"),
                    extraction_deferral_validation.get("public_safety_status"),
                ],
                "raw_decision_reference_stored": extraction_deferral_validation.get("raw_decision_reference_stored"),
            },
        ),
        requirement(
            "course_extraction_batch_harness",
            "Local OCR/transcription jobs can be planned into receipt-gated public-safe batches without performing extraction.",
            batch_plan.get("artifact_type") == "course_extraction_batch_plan"
            and batch_plan.get("public_safety_status") == "pass"
            and batch_plan.get("exam_deployment_status") == "not_cleared"
            and batch_plan.get("execution_boundary", "").startswith("This is a plan-only extraction backlog"),
            "failed",
            {
                "status": batch_plan.get("status"),
                "public_safety_status": batch_plan.get("public_safety_status"),
                "job_count": batch_plan.get("coverage", {}).get("job_count", 0),
                "batch_count": batch_plan.get("coverage", {}).get("batch_count", 0),
                "expected_receipt_count": batch_plan.get("receipt_backlog", {}).get("expected_receipt_count", 0),
                "execution_boundary": batch_plan.get("execution_boundary", ""),
            },
        ),
        requirement(
            "course_extraction_batch_receipt_harness",
            "A selected extraction batch can be turned into a public-safe receipt and human-review workflow packet.",
            batch_receipt_packet.get("artifact_type") == "course_extraction_batch_receipt_packet"
            and batch_receipt_packet.get("public_safety_status") == "pass"
            and batch_receipt_packet.get("exam_deployment_status") == "not_cleared"
            and batch_receipt_packet.get("execution_boundary", "").startswith("This is a packet-only extraction receipt workflow")
            and "receipt_contract" in batch_receipt_packet,
            "failed",
            {
                "status": batch_receipt_packet.get("status"),
                "public_safety_status": batch_receipt_packet.get("public_safety_status"),
                "selected_batch_index": batch_receipt_packet.get("selected_batch", {}).get("batch_index", 0),
                "selected_batch_job_count": batch_receipt_packet.get("selected_batch", {}).get("job_count", 0),
                "receipt_template_count": len(batch_receipt_packet.get("receipt_templates", [])),
                "execution_boundary": batch_receipt_packet.get("execution_boundary", ""),
            },
        ),
        requirement(
            "course_extraction_manifest_update_harness",
            "Reviewed extraction receipts can be converted into a public-safe private manifest metadata update plan.",
            manifest_update_plan.get("artifact_type") == "course_extraction_manifest_update_plan"
            and manifest_update_plan.get("public_safety_status") == "pass"
            and manifest_update_plan.get("exam_deployment_status") == "not_cleared"
            and manifest_update_plan.get("execution_boundary", "").startswith("This is a private manifest metadata update plan")
            and "manifest_update_contract" in manifest_update_plan,
            "failed",
            {
                "status": manifest_update_plan.get("status"),
                "public_safety_status": manifest_update_plan.get("public_safety_status"),
                "candidate_count": manifest_update_plan.get("candidate_summary", {}).get("candidate_count", 0),
                "ready_to_apply_private_count": manifest_update_plan.get("candidate_summary", {}).get("ready_to_apply_private_count", 0),
                "execution_boundary": manifest_update_plan.get("execution_boundary", ""),
            },
        ),
        requirement(
            "course_tutor_coverage_harness",
            "Current and projected course-tutor skill coverage can be forecast from reviewed private manifest candidates.",
            tutor_coverage_plan.get("artifact_type") == "course_tutor_coverage_plan"
            and tutor_coverage_plan.get("public_safety_status") == "pass"
            and tutor_coverage_plan.get("exam_deployment_status") == "not_cleared"
            and tutor_coverage_plan.get("execution_boundary", "").startswith("This is a forecast-only tutor coverage plan"),
            "failed",
            {
                "status": tutor_coverage_plan.get("status"),
                "public_safety_status": tutor_coverage_plan.get("public_safety_status"),
                "current_ready_skill_count": tutor_coverage_plan.get("current_scope_summary", {}).get("ready_skill_count", 0),
                "projected_ready_skill_count": tutor_coverage_plan.get("projected_scope_summary", {}).get("ready_skill_count", 0),
                "ready_skill_uplift": tutor_coverage_plan.get("projected_scope_summary", {}).get("ready_skill_uplift", 0),
                "candidate_material_count": tutor_coverage_plan.get("projected_scope_summary", {}).get("candidate_material_count", 0),
            },
        ),
        requirement(
            "course_study_session_harness",
            "Course-bound retrieval, notebook, reflection, and spacing tasks can be generated from reviewed tutor anchors.",
            study_session_plan.get("artifact_type") == "course_study_session_plan"
            and study_session_plan.get("public_safety_status") == "pass"
            and study_session_plan.get("exam_deployment_status") == "not_cleared"
            and study_session_plan.get("execution_boundary", "").startswith("This is a study-session plan")
            and "session_contract" in study_session_plan,
            "failed",
            {
                "status": study_session_plan.get("status"),
                "public_safety_status": study_session_plan.get("public_safety_status"),
                "task_count": study_session_plan.get("task_count", 0),
                "ready_task_count": study_session_plan.get("ready_task_count", 0),
                "coverage_status": study_session_plan.get("coverage_summary", {}).get("coverage_status"),
            },
        ),
        requirement(
            "course_study_session_receipt_harness",
            "Study-session evidence receipts and review reports can be validated without grading or storing raw student text.",
            study_receipt_validation.get("artifact_type") == "course_study_session_receipt_validation"
            and study_receipt_validation.get("public_safety_status") == "pass"
            and study_receipt_validation.get("exam_deployment_status") == "not_cleared"
            and study_receipt_validation.get("raw_text_stored") is False
            and study_review_report.get("artifact_type") == "course_study_session_review_report"
            and study_review_report.get("public_safety_status") == "pass"
            and study_review_report.get("exam_deployment_status") == "not_cleared",
            "failed",
            {
                "receipt_status": study_receipt_validation.get("status"),
                "review_status": study_review_report.get("status"),
                "public_safety_statuses": [
                    study_receipt_validation.get("public_safety_status"),
                    study_review_report.get("public_safety_status"),
                ],
                "raw_text_stored": study_receipt_validation.get("raw_text_stored"),
                "valid_receipt_count": study_review_report.get("receipt_summary", {}).get("valid_receipt_count", 0),
            },
        ),
        requirement(
            "course_material_extraction_complete",
            "OCR and transcription queues are empty or intentionally deferred.",
            course_material_extraction_complete,
            "open",
            {
                "ocr_queue_count": counts.get("ocr_queue_count", 0),
                "transcription_queue_count": counts.get("transcription_queue_count", 0),
                "open_extraction_count": extraction_open,
                "completion_status": extraction_completion_status
                if extraction_completion_accepted
                else "complete_intentionally_deferred_by_external_decision_journal"
                if journal_deferral_covers_required
                else extraction_completion_status,
                "completion_public_safety_status": extraction_completion_report.get("public_safety_status"),
                "deferred_job_count": extraction_completion_report.get("job_summary", {}).get("deferred_job_count", 0),
                "missing_job_count": extraction_completion_report.get("job_summary", {}).get("missing_job_count", 0),
                "journal_extraction_deferral_record_valid": external_gate_summary.get("extraction_deferral_record_valid") is True,
                "journal_deferred_job_types": sorted(journal_deferred_types),
                "journal_required_deferred_job_types": sorted(required_deferred_types),
                "journal_deferral_covers_required_job_types": journal_deferral_covers_required,
                "policy": "open extraction work is allowed for public draft but prevents full course-tutor completion",
            },
        ),
        requirement(
            "real_exam_authority_clearance",
            "Real exam gateway clearance is a real-world reminder, not a technical delivery blocker.",
            exam_clearance_record_valid,
            "reminder",
            {
                "exam_deployment_status": readiness.get("exam_deployment_status"),
                "exam_authority_status": decision_state.get("exam_authority_decision", {}).get("status"),
                "journal_exam_clearance_record_valid": external_gate_summary.get("exam_clearance_record_valid") is True,
                "journal_accepted_record_count": external_decision_summary.get("accepted_record_count", 0),
                "journal_public_safety_status": external_decision_summary.get("public_safety_status"),
                "deployment_switch_status": decision_state.get("exam_authority_decision", {}).get("deployment_switch_status"),
                "technical_blocker": False,
                "policy": "written clearance is tracked as a real-world reminder; UniBot stays not_cleared and does not claim exam approval",
            },
        ),
    ]
    failed = [item for item in requirements if item["status"] == "failed"]
    open_items = [item for item in requirements if item["status"] == "open"]
    reminder_items = [item for item in requirements if item["status"] == "reminder"]
    audit = {
        "schema_version": COMPLETION_AUDIT_SCHEMA_VERSION,
        "artifact_type": "unibot_project_completion_audit",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "blocked" if failed else "public_draft_ready_project_in_progress" if open_items else "complete",
        "goal_complete": not failed and not open_items,
        "public_draft_ready": readiness.get("status") == "public_draft_ready" and not failed,
        "exam_deployment_status": readiness.get("exam_deployment_status"),
        "requirement_count": len(requirements),
        "passed_count": len([item for item in requirements if item["status"] == "passed"]),
        "open_count": len(open_items),
        "reminder_count": len(reminder_items),
        "failed_count": len(failed),
        "requirements": requirements,
        "external_real_world_reminders": external_real_world_reminders(reminder_items, requirements),
        "next_best_actions": next_best_actions(open_items, counts),
        "completion_policy": (
            "Technical bot delivery is complete when no failed or open technical requirements remain. "
            "Real-world exam clearance is tracked as a reminder and never changes exam_deployment_status by itself."
        ),
    }
    attach_public_scan(audit, public_safe=public_safe, source_name="unibot-completion-audit")
    return audit


def requirement(
    requirement_id: str,
    statement: str,
    condition: bool,
    unmet_status: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "statement": statement,
        "status": "passed" if condition else unmet_status,
        "evidence": evidence,
    }


def public_safety_findings(readiness: dict[str, Any]) -> int:
    for check in readiness.get("checks", []):
        if check.get("check_id") == "public_safety":
            return int(check.get("evidence", {}).get("finding_count", 0) or 0)
    return -1


def audit_extraction_decision_record() -> dict[str, Any]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "synthetic local retention fixture",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic completion audit extraction receipt journal decision",
    }


def audit_extraction_deferral_record() -> dict[str, Any]:
    return {
        "deferral_scope": "course_material_extraction",
        "decision_status": "approved_deferral",
        "deferred_job_types": ["ocr", "transcription"],
        "deferral_reason": "synthetic completion audit deferral for current public draft evidence",
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic completion audit extraction deferral decision",
        "human_review_before_future_tutor_use": True,
        "raw_text_public_release_allowed": False,
        "exam_deployment_status": "not_cleared",
    }


def audit_exam_clearance_record() -> dict[str, Any]:
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
        "decision_reference": "synthetic completion audit exam clearance decision",
        "allowed_modes": ["exam_controlled_gateway", "controlled_notebook"],
        "help_levels_allowed": ["A0", "A1", "A2"],
        "no_proctoring": True,
        "no_ai_detection": True,
        "no_automatic_grading": True,
        "human_review_required": True,
        "raw_text_public_release_allowed": False,
    }


def sidepanel_pm_status() -> dict[str, Any]:
    html_path = ROOT / "unibot" / "browser_extension" / "sidepanel.html"
    script_path = ROOT / "unibot" / "browser_extension" / "sidepanel.js"
    try:
        html = html_path.read_text(encoding="utf-8")
        script = script_path.read_text(encoding="utf-8")
    except OSError:
        return {"status": "missing", "missing": ["sidepanel files"]}
    required_html = ['id="commandCenter"', 'id="compilerPlan"', 'id="operatorPacket"', 'id="privateExtractionRun"', 'id="privateExtractionRunOcr"', 'id="ocrFirstOperatorRun"', 'id="videoTranscriptionRun"', 'id="extractionProgress"', 'id="extractionReceiptJournal"', 'id="extractionHumanReviewPlan"', 'id="privateManifestApplyDryRun"', 'id="privateTutorIndexDryRun"', 'id="privateIndexTutorResponse"', 'id="privateTutorUseFlow"', 'id="notebookCell"', 'id="notebookCheckpointAdapter"', 'id="confirmCheckpointStore"', 'id="confirmExamWorkspaceRun"', 'id="confirmManifestApply"', 'id="confirmTutorIndexBuild"', 'id="confirmHelpLedgerAppend"', 'id="confirmExamLedgerAppend"', 'id="confirmTimelineExportReceiptJournalAppend"', 'id="confirmDrillLoopProgressJournalAppend"', 'id="confirmLocalExportDraftWrite"', 'id="examWorkspaceRun"', 'id="extractionDeferralValidate"', 'id="extractionCompletionReport"', 'id="extractionBatchPlan"', 'id="extractionBatchPlanOcr"', 'id="batchReceiptPacket"', 'id="batchReceiptPacketOcr"', 'id="manifestUpdatePlan"', 'id="tutorCoveragePlan"', 'id="materialCoverageRun"', 'id="examSkillDrilldown"', 'id="skillToWorkspaceRun"', 'id="skillToWorkspaceSessionCarryover"', 'id="examSessionConsole"', 'id="examRunHistoryReview"', 'id="courseExamCoverageDashboard"', 'id="perSkillActionRouter"', 'id="executeRoutedAction"', 'id="examRunPacket"', 'id="examPacketTimeline"', 'id="timelineExportReviewPacket"', 'id="timelineExportReceiptJournalAppend"', 'id="timelineExportReceiptJournalSummary"', 'id="reviewChainIntegrityCheck"', 'id="pythonExamReadinessConsole"', 'id="pythonExamCockpitFlow"', 'id="pythonExamLiveControlSurface"', 'id="pythonExamEvidenceExportPreview"', 'id="pythonExamTutorDrillPack"', 'id="pythonExamDrillSessionRunner"', 'id="pythonExamDrillSessionReviewLoop"', 'id="pythonExamDrillLoopControlPanel"', 'id="pythonExamDrillLoopProgressJournal"', 'id="pythonExamResumeLauncher"', 'id="pythonExamActiveStudyLoopDashboard"', 'id="pythonExamActiveStudyGuidedRunner"', 'id="pythonExamGuidedActionExecutionBridge"', 'id="pythonExamSafeCycleConsole"', 'id="pythonExamSafeCycleOperatorGate"', 'id="pythonExamOperatorGateDecisionReceipt"', 'id="pythonExamLocalCycleStartPacket"', 'id="pythonExamConfirmedLocalExportDraft"', 'id="pythonExamDraftPackageReviewConsole"', 'id="pythonExamHumanHandoffPacket"', 'id="examWorkspaceOperatorRun"', 'id="examWorkspaceLaunchFlow"', 'id="studySessionPlan"', 'id="studyReceiptValidate"', 'id="studyReviewReport"', 'id="clearanceBoard"', 'id="submissionBundle"', 'id="decisionRequest"', 'id="decisionRequestMarkdown"', 'id="decisionJournal"', 'id="decisionRecordJournal"', 'id="decisionState"', 'id="localDecisionIntake"', 'id="localDecisionWorkspace"', 'id="contextPacket"']
    required_script = [
        "/api/unibot/orchestration/command-center",
        "/api/unibot/course/compiler-plan",
        "/api/unibot/course/extraction-operator-packet",
        "/api/unibot/course/private-extraction/run-batch",
        "/api/unibot/course/video-transcription/run-batch",
        "/api/unibot/course/extraction-progress-report",
        "/api/unibot/course/extraction-receipts/summary",
        "/api/unibot/course/extraction-review/apply-plan",
        "/api/unibot/course/extraction-manifest/apply-dry-run",
        "/api/unibot/course/tutor-index/dry-run",
        "/api/unibot/course/tutor-index/respond-dry-run",
        "/api/unibot/course/private-tutor-use-flow/dry-run",
        "/api/unibot/exam-workspace/notebook-checkpoint/adapt",
        "/api/unibot/exam-workspace/operator-run",
        "/api/unibot/exam-workspace/session-console",
        "/api/unibot/exam-workspace/run-history-export-review",
        "/api/unibot/course/exam-coverage-dashboard",
        "/api/unibot/course/per-skill-action-router",
        "/api/unibot/course/routed-action-executor",
        "/api/unibot/course/exam-run-packet",
        "/api/unibot/course/exam-packet-timeline",
        "/api/unibot/course/timeline-export-review-packet",
        "/api/unibot/course/timeline-export-receipt-journal/append",
        "/api/unibot/course/timeline-export-receipt-journal/summary",
        "/api/unibot/course/review-chain-integrity-check",
        "/api/unibot/course/python-exam-readiness-console",
        "/api/unibot/course/python-exam-cockpit-flow",
        "/api/unibot/course/python-exam-live-control-surface",
        "/api/unibot/course/python-exam-evidence-export-preview",
        "/api/unibot/course/python-exam-source-grounded-tutor-drill-pack",
        "/api/unibot/course/python-exam-drill-session-runner",
        "/api/unibot/course/python-exam-drill-session-review-loop",
        "/api/unibot/course/python-exam-drill-loop-control-panel",
        "/api/unibot/course/python-exam-drill-loop-progress-journal",
        "renderPythonExamDrillLoopProgressJournal",
        "/api/unibot/course/python-exam-resume-launcher",
        "renderPythonExamResumeLauncher",
        "/api/unibot/course/python-exam-active-study-loop-dashboard",
        "renderPythonExamActiveStudyLoopDashboard",
        "/api/unibot/course/python-exam-active-study-guided-runner",
        "renderPythonExamActiveStudyGuidedRunner",
        "/api/unibot/course/python-exam-guided-action-execution-bridge",
        "renderPythonExamGuidedActionExecutionBridge",
        "/api/unibot/course/python-exam-safe-cycle-console",
        "renderPythonExamSafeCycleConsole",
        "/api/unibot/course/python-exam-safe-cycle-operator-gate",
        "renderPythonExamSafeCycleOperatorGate",
        "/api/unibot/course/python-exam-operator-gate-decision-receipt",
        "renderPythonExamOperatorGateDecisionReceipt",
        "/api/unibot/course/python-exam-local-cycle-start-packet",
        "renderPythonExamLocalCycleStartPacket",
        "/api/unibot/course/python-exam-confirmed-local-export-draft",
        "/api/unibot/course/python-exam-draft-package-review-console",
        "/api/unibot/course/python-exam-human-handoff-packet",
        "/api/unibot/exam-workspace/run-dry-run",
        "/api/unibot/course/extraction-deferral/validate",
        "/api/unibot/course/extraction-completion-report",
        "/api/unibot/course/extraction-batch-plan",
        "/api/unibot/course/extraction-batch-receipt-packet",
        'job_types: ["ocr"]',
        "/api/unibot/course/extraction-manifest-update-plan",
        "/api/unibot/course/tutor-coverage-plan",
        "/api/unibot/course/material-coverage/run",
        "/api/unibot/course/exam-skill-drilldown",
        "/api/unibot/course/skill-to-workspace-live-flow",
        "/api/unibot/course/skill-to-workspace-session-carryover",
        "/api/unibot/exam-workspace/launch-flow/dry-run",
        "/api/unibot/course/study-session-plan",
        "/api/unibot/course/study-session-receipt/validate",
        "/api/unibot/course/study-session-review-report",
        "/api/unibot/institutional-clearance/board",
        "/api/unibot/stakeholder/submission-bundle",
        "/api/unibot/stakeholder/decision-request",
        "/api/unibot/stakeholder/decision-request-markdown",
        "/api/unibot/stakeholder/decision-journal/summary",
        "/api/unibot/stakeholder/decision-record-journal/summary",
        "/api/unibot/stakeholder/decision-state",
        "/api/unibot/orchestration/context-packet",
        "renderCommandCenter",
        "renderCompilerPlan",
        "renderOperatorPacket",
        "renderPrivateExtractionRun",
        "renderVideoTranscriptionRun",
        "renderExtractionProgress",
        "renderExtractionReceiptJournal",
        "renderExtractionHumanReviewPlan",
        "renderPrivateManifestApplyDryRun",
        "renderPrivateTutorIndexDryRun",
        "renderPrivateIndexTutorResponse",
        "renderPrivateTutorUseFlow",
        "renderNotebookCheckpointAdapter",
        "renderExamSkillDrilldown",
        "renderSkillToWorkspaceLiveFlow",
        "skillWorkspaceLiveFlowPayload",
        "renderSkillToWorkspaceSessionCarryover",
        "skillWorkspaceSessionCarryoverPayload",
        "skillWorkspaceOperatorPayload",
        "renderExamSessionConsole",
        "skillWorkspaceSessionConsolePayload",
        "renderExamRunHistoryReview",
        "renderCourseExamCoverageDashboard",
        "renderPerSkillActionRouter",
        "renderRoutedActionExecutor",
        "renderExamRunPacket",
        "renderExamPacketTimeline",
        "renderTimelineExportReviewPacket",
        "renderTimelineExportReceiptJournalAppend",
        "renderTimelineExportReceiptJournalSummary",
        "renderReviewChainIntegrityCheck",
        "renderPythonExamReadinessConsole",
        "renderPythonExamCockpitFlow",
        "renderPythonExamTutorDrillPack",
        "renderPythonExamDrillSessionRunner",
        "renderPythonExamDrillSessionReviewLoop",
        "renderPythonExamDrillLoopControlPanel",
        "renderExamWorkspaceOperatorRun",
        "renderExtractionDeferralValidation",
        "renderExtractionCompletionReport",
        "renderExtractionBatchPlan",
        "renderBatchReceiptPacket",
        "renderManifestUpdatePlan",
        "renderTutorCoveragePlan",
        "renderStudySessionPlan",
        "renderExamWorkspaceLaunchFlow",
        "renderStudyReceiptValidation",
        "renderStudyReviewReport",
        "renderClearanceBoard",
        "renderSubmissionBundle",
        "renderDecisionRequest",
        "renderDecisionJournal",
        "renderDecisionRecordJournal",
        "renderDecisionState",
        "renderContextPacket",
    ]
    missing = [item for item in required_html if item not in html] + [item for item in required_script if item not in script]
    return {
        "status": "present" if not missing else "missing",
        "missing": missing,
        "html_controls": len(required_html) - len([item for item in required_html if item in missing]),
        "script_contracts": len(required_script) - len([item for item in required_script if item in missing]),
    }


def next_best_actions(open_items: list[dict[str, Any]], counts: dict[str, Any]) -> list[str]:
    action_ids = {item["requirement_id"] for item in open_items}
    actions: list[str] = []
    if "course_material_extraction_complete" in action_ids:
        actions.append(
            f"Use the rights/privacy stakeholder decision-request packet, validate a manual request receipt, then either process the local extraction queue with receipts or record a valid intentional deferral: OCR {counts.get('ocr_queue_count', 0)} files and transcribe {counts.get('transcription_queue_count', 0)} videos."
        )
    return actions or ["Technical delivery gates are clear; keep regression pipeline green and use external_real_world_reminders for non-blocking clearance follow-up."]


def external_real_world_reminders(
    reminder_items: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reminders: list[dict[str, Any]] = []
    exam_requirement = next(
        (item for item in requirements if item.get("requirement_id") == "real_exam_authority_clearance"),
        None,
    )
    if exam_requirement and exam_requirement.get("status") == "passed":
        reminders.append(
            {
                "reminder_id": "real_exam_authority_clearance",
                "status": "recorded_not_deployed",
                "technical_blocker": False,
                "exam_deployment_status": exam_requirement.get("evidence", {}).get("exam_deployment_status", "not_cleared"),
                "message": "Written exam clearance evidence is recorded, but UniBot still does not switch real exam deployment automatically.",
            }
        )
    for item in reminder_items:
        if item.get("requirement_id") != "real_exam_authority_clearance":
            continue
        reminders.append(
            {
                "reminder_id": "real_exam_authority_clearance",
                "status": "external_real_world_follow_up",
                "technical_blocker": False,
                "exam_deployment_status": item.get("evidence", {}).get("exam_deployment_status", "not_cleared"),
                "message": "Reale Pruefungsfreigabe in der echten Welt klaeren; UniBot erinnert daran und bleibt not_cleared.",
            }
        )
    return reminders


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
