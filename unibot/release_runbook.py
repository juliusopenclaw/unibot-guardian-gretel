from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .materials import sha256_text
from .public_safety import scan_text


RELEASE_RUNBOOK_SCHEMA_VERSION = "unibot-release-runbook-v1"


def build_release_runbook_evidence_alignment(
    release_gates: list[dict[str, Any]],
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate_ids = [str(gate["gate_id"]) for gate in release_gates]
    gate_map = {
        "public_safety_scan": {
            "readiness_check_ids": ["public_safety"],
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "human_gates": ["public_safety_required"],
        },
        "redteam_smoke": {
            "readiness_check_ids": ["redteam", "evaluation_packet", "adaptive_task_plan"],
            "source_card_ids": ["openai-evals", "dfg-gwp"],
            "human_gates": ["human_review_required"],
        },
        "publication_package": {
            "readiness_check_ids": ["publication_package", "gretel_bachelor_thesis_package", "review_board_packet"],
            "source_card_ids": ["dfg-gwp", "zai-glm-52"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        "readiness_check": {
            "readiness_check_ids": [
                "readiness_runtime_guard",
                "source_card_drift_guard",
                "gretel_autonomous_research_loop",
                "python_exam_local_cycle_operator_workspace_card",
            ],
            "source_card_ids": ["dfg-gwp", "eu-ai-act-2024"],
            "human_gates": ["human_review_required"],
        },
        "github_issue_manual_review": {
            "readiness_check_ids": ["github_issue_bundle", "demo_feedback_triage"],
            "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
            "human_gates": ["human_review_before_github_create", "public_safety_required"],
        },
        "exam_authority_clearance": {
            "readiness_check_ids": ["exam_boundary", "review_board_packet", "compliance_matrix", "gretel_bachelor_thesis_package"],
            "source_card_ids": ["hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq", "eu-ai-act-2024"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    }
    gate_rows = [
        {
            "gate_id": gate_id,
            "required": bool(next(gate for gate in release_gates if gate["gate_id"] == gate_id)["required"]),
            "readiness_check_ids": gate_map.get(gate_id, {}).get("readiness_check_ids", []),
            "source_card_ids": gate_map.get(gate_id, {}).get("source_card_ids", []),
            "human_gates": gate_map.get(gate_id, {}).get("human_gates", []),
            "manual_review_required": True,
        }
        for gate_id in gate_ids
    ]
    workspace_card = safe_release_runbook_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_release_runbook_workspace_card(),
        release_gate_hash=release_runbook_gate_hash(release_gates),
        release_evidence_hash=release_runbook_evidence_hash(gate_rows),
    )
    workspace_card_readiness_gate_linked = (
        workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") != ""
        and workspace_card.get("exam_deployment_status") == "not_cleared"
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False
    )
    alignment = {
        "schema_version": "unibot-release-runbook-evidence-alignment-v1",
        "status": "ready",
        "release_gate_count": len(gate_rows),
        "required_release_gate_count": len([row for row in gate_rows if row["required"]]),
        "readiness_snapshot_contract": {
            "expected_schema_version": "unibot-readiness-evidence-snapshot-v1",
            "required_status": "ready",
            "use": "Confirm release-facing work remains public-safe, source-bound, and not exam clearance.",
        },
        "review_board_contract": {
            "expected_schema_version": "unibot-review-board-evidence-alignment-v1",
            "required_status": "ready",
            "use": "Human review board alignment must stay ready before authority-facing release language.",
        },
        "review_board_thesis_evaluation_claim_contract": {
            "expected_schema_version": "unibot-review-board-thesis-evaluation-claim-alignment-v1",
            "required_status": "ready",
            "required_readiness_check_ids": [
                "review_board_packet",
                "gretel_bachelor_thesis_package",
                "evaluation_packet",
                "adaptive_task_plan",
                "python_exam_local_cycle_operator_workspace_card",
            ],
            "required_human_gates": [
                "human_submission_review_required",
                "public_safety_required",
                "written_university_clearance_required_before_exam_use",
            ],
            "use": "Release language must keep review-board thesis/evaluation learner-agency claims human-gated and not exam clearance.",
        },
        "github_issue_contract": {
            "expected_schema_version": "unibot-github-issue-evidence-traceability-v1",
            "required_status": "ready",
            "manual_publish_only": True,
        },
        "release_gates": gate_rows,
        "unique_readiness_check_ids": sorted({check_id for row in gate_rows for check_id in row["readiness_check_ids"]}),
        "unique_source_card_ids": sorted({source_id for row in gate_rows for source_id in row["source_card_ids"]}),
        "required_human_gates": sorted({gate for row in gate_rows for gate in row["human_gates"]}),
        "unmapped_gate_ids": sorted(gate_id for gate_id in gate_ids if gate_id not in gate_map),
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_release_runbook_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == release_runbook_gate_hash(release_gates)
        and workspace_card.get("task_hash") == release_runbook_evidence_hash(gate_rows),
        "human_gate_reminder": "Release runbook alignment is not exam clearance, legal approval, provider approval, GitHub publication, or thesis submission approval.",
    }
    if not alignment["workspace_card_release_runbook_gate_linked"]:
        alignment["status"] = "blocked"
        alignment["workspace_card_release_runbook_gate_issue"] = "release runbook gate/evidence hashes are not linked to workspace-card readiness"
    else:
        alignment["workspace_card_release_runbook_gate_issue"] = ""
    if alignment["unmapped_gate_ids"] or not all(row["manual_review_required"] for row in gate_rows):
        alignment["status"] = "blocked"
    if not set(alignment["review_board_thesis_evaluation_claim_contract"]["required_readiness_check_ids"]).issubset(
        set(alignment["unique_readiness_check_ids"])
    ):
        alignment["status"] = "blocked"
        alignment["missing_review_board_thesis_evaluation_check_ids"] = sorted(
            set(alignment["review_board_thesis_evaluation_claim_contract"]["required_readiness_check_ids"])
            - set(alignment["unique_readiness_check_ids"])
        )
    else:
        alignment["missing_review_board_thesis_evaluation_check_ids"] = []
    if not set(alignment["review_board_thesis_evaluation_claim_contract"]["required_human_gates"]).issubset(
        set(alignment["required_human_gates"])
    ):
        alignment["status"] = "blocked"
        alignment["missing_review_board_thesis_evaluation_human_gates"] = sorted(
            set(alignment["review_board_thesis_evaluation_claim_contract"]["required_human_gates"])
            - set(alignment["required_human_gates"])
        )
    else:
        alignment["missing_review_board_thesis_evaluation_human_gates"] = []
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "release-runbook-evidence-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
    return alignment


def synthetic_release_runbook_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic release runbook workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic release-runbook prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_release_runbook_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_release_gates_before_manual_publication",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__RELEASE_RUNBOOK_EVIDENCE_HASH__",
            "checkpoint_hash": "__RELEASE_RUNBOOK_GATE_HASH__",
            "source_card_ids": ["dfg-gwp", "eu-ai-act-2024"],
            "source_anchor_count": 2,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def release_runbook_gate_hash(release_gates: list[dict[str, Any]]) -> str:
    return sha256_text(json.dumps(release_gates, sort_keys=True, ensure_ascii=False))


def release_runbook_evidence_hash(gate_rows: list[dict[str, Any]]) -> str:
    return sha256_text(
        json.dumps(
            {
                "release_gates": gate_rows,
                "manual_review_required": True,
                "exam_deployment_status": "not_cleared",
                "manual_publication_only": True,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def safe_release_runbook_workspace_card(
    workspace_card: dict[str, Any],
    *,
    release_gate_hash: str = "",
    release_evidence_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    review = workspace_card.get("readiness_review", {}) if isinstance(workspace_card.get("readiness_review"), dict) else {}
    handoff = workspace_card.get("readiness_handoff", {}) if isinstance(workspace_card.get("readiness_handoff"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if release_gate_hash and checkpoint_hash == "__RELEASE_RUNBOOK_GATE_HASH__":
        checkpoint_hash = release_gate_hash
    if release_evidence_hash and task_hash == "__RELEASE_RUNBOOK_EVIDENCE_HASH__":
        task_hash = release_evidence_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_release_runbook"))
        ),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", review.get("next_safe_action", ""))),
        "next_safe_user_action": str(summary.get("next_safe_user_action", review.get("next_safe_user_action", ""))),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", handoff.get("operator_run_endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", handoff.get("operator_run_method", "POST"))),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": task_hash,
        "checkpoint_hash": checkpoint_hash,
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }


def build_release_runbook() -> dict[str, Any]:
    runbook = {
        "schema_version": RELEASE_RUNBOOK_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "public_draft_runbook_not_exam_release",
        "manual_review_required": True,
        "exam_deployment_status": "not_cleared",
        "purpose": (
            "Public-safe contributor and release checklist for the separate UniBot Guardian track."
        ),
        "boundaries": [
            "No proctoring.",
            "No KI detection as evidence.",
            "No automatic grading.",
            "No decision on accommodation.",
            "No real exam deployment without written authority clearance.",
            "No private course files, emails, local paths, or personal health details in public work.",
        ],
        "ready_for": [
            "public draft review",
            "local practice demo",
            "synthetic issue triage",
            "source-card and test contributions",
        ],
        "not_ready_for": [
            "exam deployment",
            "official grading",
            "proctoring",
            "KI-detection use",
            "processing private course material in public repositories",
        ],
        "quickstart_steps": [
            {
                "step_id": "start_local_service",
                "label": "Start the local UniBot service.",
                "command": "python3 -m unibot.server",
                "success_check": "GET /api/unibot/health returns status ok.",
            },
            {
                "step_id": "load_browser_mantle",
                "label": "Load the browser mantle for practice pages.",
                "command": "Load unpacked extension from unibot/browser_extension in Chrome-compatible browsers.",
                "success_check": "Side panel opens and shows Prompt Card, Review, Ledger, and Demo Feedback areas.",
            },
            {
                "step_id": "run_local_demo",
                "label": "Run the local practice demo.",
                "command": "POST /api/unibot/demo-run",
                "success_check": "Status is practice_demo_ready_not_exam.",
            },
            {
                "step_id": "check_readiness",
                "label": "Run the public-draft readiness check.",
                "command": "POST /api/unibot/readiness-check",
                "success_check": "Status is public_draft_ready and exam deployment remains not_cleared.",
            },
            {
                "step_id": "collect_demo_feedback",
                "label": "Validate and store public-safe demo feedback.",
                "command": "POST /api/unibot/demo-feedback/validate then POST /api/unibot/demo-feedback/append",
                "success_check": "Feedback is accepted only when private_data_removed is true.",
            },
            {
                "step_id": "triage_feedback",
                "label": "Convert sanitized feedback into reviewable work items.",
                "command": "POST /api/unibot/demo-feedback/triage and POST /api/unibot/github-issue-bundle",
                "success_check": "Issue bundle is ready and marked for manual review.",
            },
            {
                "step_id": "inspect_clearance_board",
                "label": "Inspect stakeholder clearance lanes before any authority-facing claim.",
                "command": "POST /api/unibot/institutional-clearance/board",
                "success_check": "Board is public-safe and exam deployment remains not_cleared.",
            },
            {
                "step_id": "validate_clearance_record",
                "label": "Validate a written scope record without switching deployment.",
                "command": "POST /api/unibot/institutional-clearance/validate",
                "success_check": "Record is accepted only for its named scope and raw written text is not stored.",
            },
            {
                "step_id": "prepare_local_extraction_decision_intake",
                "label": "Prepare or inspect the local rights/privacy decision intake packet.",
                "command": "POST /api/unibot/course/extraction-decision/local-intake",
                "success_check": "Packet is public-safe, exposes the minimum decision record template, journal gate, OCR-first readiness, receipt-journal status, and post-run report status without raw decisions, raw course text, or local paths.",
            },
            {
                "step_id": "record_local_extraction_decision",
                "label": "Store a valid local-extraction decision as hash-only journal evidence.",
                "command": "POST /api/unibot/course/extraction-decision/local-intake/record",
                "success_check": "Valid records append only a hash-only local_extraction_decision event and return an intake packet showing OCR-first readiness; invalid records are blocked and not stored.",
            },
            {
                "step_id": "prepare_local_extraction_decision_workspace",
                "label": "Prepare the local Decision-Record workspace and dry-run receipt.",
                "command": "POST /api/unibot/course/extraction-decision/workspace/prepare",
                "success_check": "Workspace writes a JSON template plus hash-only manifest under the local UniBot guardian directory and returns a dry-run receipt without raw decisions, raw course text, local paths, or OCR execution.",
            },
            {
                "step_id": "record_local_extraction_decision_workspace",
                "label": "Record a valid local decision through the workspace and verify OCR-first readiness.",
                "command": "POST /api/unibot/course/extraction-decision/workspace/record",
                "success_check": "Valid records are appended hash-only, invalid records are not stored, and the dry-run receipt shows whether OCR-first Batch 1 is start-ready.",
            },
            {
                "step_id": "run_controlled_ocr_first_operator",
                "label": "Run controlled OCR-first Batch 1 after dry-run confirmation.",
                "command": "POST /api/unibot/course/ocr-first/operator-run",
                "success_check": "Operator checks the current dry-run receipt, requires operator_confirmed_dry_run true before private OCR starts, writes hash-only receipts, and returns Progress/Manifest/Tutor-Coverage summaries without raw text or local paths.",
            },
            {
                "step_id": "prepare_extraction_operator",
                "label": "Prepare the gated private extraction operator packet.",
                "command": "POST /api/unibot/course/extraction-operator-packet",
                "success_check": "Packet is public-safe, metadata-only, and ready only after a valid local-extraction decision.",
            },
            {
                "step_id": "build_extraction_batch_plan",
                "label": "Plan local OCR/transcription work into receipt-gated batches.",
                "command": "POST /api/unibot/course/extraction-batch-plan",
                "success_check": "Batch plan is public-safe, plan-only, exposes counts/batch ids/receipt backlog without local paths, and accepts job_types for OCR-first or transcription-only planning.",
            },
            {
                "step_id": "build_batch_receipt_packet",
                "label": "Prepare the selected batch receipt and human-review workflow.",
                "command": "POST /api/unibot/course/extraction-batch-receipt-packet",
                "success_check": "Packet is public-safe, packet-only, exposes receipt templates plus review checklist without local paths or raw text, and uses the same job_types filter as the plan.",
            },
            {
                "step_id": "run_private_text_container_extraction",
                "label": "Run the local private DOCX/text-PDF/PPTX extraction harness after a valid decision.",
                "command": "POST /api/unibot/course/private-extraction/run-batch",
                "success_check": "Runner writes raw text only to private local artifacts, appends hash-only receipts when requested, supports job_types ['ocr'] for OCR-first Batch 1, can use decision_record_journal_path as a hash-only decision bridge, and keeps human review pending unless explicitly marked reviewed.",
            },
            {
                "step_id": "run_private_video_transcription",
                "label": "Run the local private video transcription harness after a valid decision.",
                "command": "POST /api/unibot/course/video-transcription/run-batch",
                "success_check": "Runner ingests sidecar transcripts when present, reports missing local ASR adapters clearly, and returns only hash/count receipt metadata.",
            },
            {
                "step_id": "validate_extraction_receipts",
                "label": "Validate one receipt per local OCR/transcription job.",
                "command": "POST /api/unibot/course/extraction-receipt/validate",
                "success_check": "Receipt stores hashes, counts, and review state only; raw extracted text is blocked.",
            },
            {
                "step_id": "record_extraction_receipts",
                "label": "Store validated extraction receipts in the local hash-only journal.",
                "command": "POST /api/unibot/course/extraction-receipts/append then POST /api/unibot/course/extraction-receipts/summary",
                "success_check": "Journal stores accepted receipt evidence only and exposes progress-ready receipts without raw text or local paths.",
            },
            {
                "step_id": "record_human_review_apply_plan",
                "label": "Record hash-only human review decisions and prepare the private manifest apply plan.",
                "command": "POST /api/unibot/course/extraction-review/validate then POST /api/unibot/course/extraction-review/apply-plan",
                "success_check": "Accepted review decisions append reviewed_for_private_tutor receipts and hash-only review records, then return manifest and tutor-coverage previews without writing manifests or starting tutor indexing.",
            },
            {
                "step_id": "run_private_manifest_apply_dry_run",
                "label": "Preview and optionally apply reviewed private manifest metadata.",
                "command": "POST /api/unibot/course/extraction-manifest/apply-dry-run",
                "success_check": "Dry-run returns a metadata delta plus ExamScopeMap/Tutor-Coverage previews; local manifest writes happen only when operator_confirmed_manifest_apply is true, and tutor indexing never starts here.",
            },
            {
                "step_id": "run_private_tutor_index_dry_run",
                "label": "Preview and optionally build the private tutor source-anchor index.",
                "command": "POST /api/unibot/course/tutor-index/dry-run",
                "success_check": "Dry-run reads the private manifest, returns hash-only source anchors, ExamScopeMap coverage gaps, and writes a local index only when operator_confirmed_tutor_index_build is true.",
            },
            {
                "step_id": "run_private_index_tutor_response_dry_run",
                "label": "Preview an A0-A2 tutor response from the private hash-only index.",
                "command": "POST /api/unibot/course/tutor-index/respond-dry-run",
                "success_check": "Response reads only the hash-only tutor index, returns source anchors, Socratic questions, and a Help-Ledger preview while returning the query as a hash only.",
            },
            {
                "step_id": "run_private_tutor_use_flow_dry_run",
                "label": "Run the connected private tutor use flow as one local dry-run.",
                "command": "POST /api/unibot/course/private-tutor-use-flow/dry-run",
                "success_check": "Flow chains private manifest apply, hash-only tutor-index build, A0-A2 response, optional Help-Ledger append, and study-receipt validation without raw query/text or local paths in the response.",
            },
            {
                "step_id": "run_exam_workspace_dry_run",
                "label": "Run the controlled exam workspace as one notebook-centered dry-run.",
                "command": "POST /api/unibot/exam-workspace/run-dry-run",
                "success_check": "Flow links material freeze, notebook cell checkpoint, private tutor sidecar, Help-Ledger evidence, study-receipt validation, and export receipt while returning no raw query, notebook code, private text, or local paths and staying not_cleared.",
            },
            {
                "step_id": "adapt_local_notebook_checkpoint",
                "label": "Turn a local notebook cell or hash-only checkpoint into reviewable evidence.",
                "command": "POST /api/unibot/exam-workspace/notebook-checkpoint/adapt",
                "success_check": "Adapter returns only hashes, Cell-Checkpoint metadata, Study-Receipt validation, Help-Ledger preview, and optional hash-only journal evidence; raw cell text, notebook code, local paths, values, final interpretation, grading, proctoring, AI detection, and clearance claims stay out.",
            },
            {
                "step_id": "review_exam_skill_drilldown",
                "label": "Review the course-exact Python exam skill drilldown.",
                "command": "POST /api/unibot/course/exam-skill-drilldown",
                "success_check": "Drilldown returns a selectable metadata-only skill map, selected-skill readiness, material gaps, notebook-checkpoint template, Help-Ledger preview template, and dry-run operator action template without raw course text, raw query, notebook code, local paths, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "run_skill_to_workspace_live_flow",
                "label": "Prefill and run the Start Exam Workspace Operator Dry-Run from the selected Python skill.",
                "command": "POST /api/unibot/course/skill-to-workspace-live-flow",
                "success_check": "Live Flow selects the drilldown skill, prefills the operator run with skill tag, source-card/anchor metadata, notebook-checkpoint template, A0-A2 help and Help-Ledger preview, executes dry-run by default, and shows individual local write confirmations without raw queries, course raw text, notebook code, local paths, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "run_skill_to_workspace_session_carryover",
                "label": "Carry the Skill-to-Workspace receipt into Session, Evidence Preview, and Handoff.",
                "command": "POST /api/unibot/course/skill-to-workspace-session-carryover",
                "success_check": "Carryover passes the operator dry-run receipt into Session Console, Run History, Evidence Export Preview, and Human Handoff Packet using only receipt ids, skill tag, checkpoint hash, A0-A2 profile, source-card/anchor metadata, operator confirmations, and not_cleared status. It remains dry-run by default and returns no raw queries, course raw text, notebook code, local paths, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "build_python_exam_source_grounded_tutor_drill_pack",
                "label": "Build the source-grounded A0-A2 Python Exam Tutor Drill Pack.",
                "command": "POST /api/unibot/course/python-exam-source-grounded-tutor-drill-pack",
                "success_check": "Drill Pack turns Course Exam Coverage Dashboard, Exam-Skill Drilldown, and Skill-to-Workspace Session Carryover into safe microtasks, retrieval questions, notebook-checkpoint template hashes, typical-error hints, Source-Card anchors, Help-Ledger previews, and not_cleared receipts without raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "run_python_exam_drill_session_runner",
                "label": "Run one source-grounded Microtask as a hash-only Python Exam Drill Session.",
                "command": "POST /api/unibot/course/python-exam-drill-session-runner",
                "success_check": "Runner selects one safe microtask from the Tutor Drill Pack, links it to Skill-to-Workspace Carryover, hashes the local notebook checkpoint through the checkpoint adapter, previews Help-Ledger evidence, and emits a not_cleared receipt. It writes only after explicit operator confirmation and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_drill_session_loop",
                "label": "Review one Drill Session and choose the next safe microtask or repeat.",
                "command": "POST /api/unibot/course/python-exam-drill-session-review-loop",
                "success_check": "Review Loop consumes only Drill Session hashes, Source-Card metadata, A0-A2 help status, Help-Ledger preview, Carryover receipts, reflection status, and not_cleared receipt, then suggests next_microtask, repeat_current_microtask, or return_to_skill_dashboard without scores, percentages, rankings, grades, raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "show_python_exam_drill_loop_control_panel",
                "label": "Show the combined Tutor Drill Pack -> Drill Session -> Review Loop control panel.",
                "command": "POST /api/unibot/course/python-exam-drill-loop-control-panel",
                "success_check": "Control Panel shows the selected Python skill, current microtask hash, checkpoint hash, Source-Card anchors, A0-A2 help, Help-Ledger preview, Carryover receipt, reflection status, Next-Step action, and not_cleared receipt across Pack, Session, and Review. It remains dry-run, writes only after operator confirmation, and exposes no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "preview_or_append_python_exam_drill_loop_progress_journal",
                "label": "Preview or append the hash-only Drill Loop Progress Journal for resume/recovery.",
                "command": "POST /api/unibot/course/python-exam-drill-loop-progress-journal",
                "success_check": "Progress Journal previews by default and appends only with explicit operator confirmation. Each entry stores only skill tag, microtask hash, checkpoint hash, Source-Card anchors, A0-A2 help level, Help-Ledger event hash, Carryover receipt, Review Loop receipt, next-step action, reflection status, and not_cleared receipt. It provides resume/recovery without raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "launch_python_exam_resume_from_progress_journal",
                "label": "Use the Progress Journal resume state to prefill the next safe Control Panel action.",
                "command": "POST /api/unibot/course/python-exam-resume-launcher",
                "success_check": "Resume Launcher reads only hash-only Progress Journal metadata and decides run_next_microtask, repeat_current_microtask, return_to_skill_dashboard, or start_first_microtask. It returns a dry-run Control Panel or dashboard prefill with skill tag, task hash, checkpoint hash, Source-Card anchors, A0-A2 help level, receipts, and not_cleared status only; no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "show_python_exam_active_study_loop_dashboard",
                "label": "Show the per-skill Active Study Loop dashboard across coverage, drills, progress, and resume state.",
                "command": "POST /api/unibot/course/python-exam-active-study-loop-dashboard",
                "success_check": "Active Study Loop Dashboard merges Course Exam Coverage Dashboard, Source-Grounded Tutor Drill Pack, Drill Loop Control Panel, Progress Journal, and Resume Launcher into one metadata-only per-skill view. It shows readiness, last safe microtask, next microtask/repeat/return status, Source-Card coverage, A0-A2 help level, checkpoint, ledger, review receipts, open repeats, completed skill loops, and next safe action; it writes nothing and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "run_python_exam_active_study_guided_runner",
                "label": "Turn the Active Study Loop dashboard selection into the next safe dry-run Action Card.",
                "command": "POST /api/unibot/course/python-exam-active-study-guided-runner",
                "success_check": "Guided Runner consumes only the selected Active Study Loop row, Resume Launcher metadata, and Control Panel receipts, then prepares a dry-run Action Card for run_next_microtask, repeat_current_microtask, start_first_microtask, return_to_skill_dashboard, or review_skill_readiness. It includes skill tag, task/checkpoint hashes, Source-Card anchors, A0-A2 help level, receipts, and operator confirmations; it writes nothing by default and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "preview_python_exam_guided_action_execution_bridge",
                "label": "Translate the Guided Runner Action Card into the next concrete metadata-only work-cycle preview.",
                "command": "POST /api/unibot/course/python-exam-guided-action-execution-bridge",
                "success_check": "Execution Bridge consumes only the Guided Runner Action Card, Control Panel receipt metadata, and Progress Journal preview metadata. It prepares a Control Panel Preview for run_next_microtask, repeat_current_microtask, or start_first_microtask, or a Dashboard Return Preview for return_to_skill_dashboard/review_skill_readiness. It shows skill tag, task/checkpoint hashes, Source-Card anchors, A0-A2 help level, receipts, and an all-false operator confirmation matrix; it writes nothing by default and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "show_python_exam_safe_cycle_console",
                "label": "Show the current Python exam safe work-cycle across dashboard, guided runner, bridge, control panel, and progress journal.",
                "command": "POST /api/unibot/course/python-exam-safe-cycle-console",
                "success_check": "Safe Cycle Console merges Active Study Dashboard, Guided Runner, Execution Bridge, Drill Loop Control Panel, and Progress Journal into one metadata-only current-cycle view. It shows selected skill, next safe action, Control Panel or Dashboard Return preview, task/checkpoint hashes, Source-Card anchors, A0-A2 help level, Help-Ledger, Review, Progress receipts, operator confirmation matrix, cycle status, and next safe user action; it writes nothing by default and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_safe_cycle_operator_gate",
                "label": "Review separate human confirmation cards before continuing the local safe cycle.",
                "command": "POST /api/unibot/course/python-exam-safe-cycle-operator-gate",
                "success_check": "Operator Gate consumes only Safe Cycle Console metadata and shows separate confirmation cards for Control Panel open, notebook checkpoint preparation, A0-A2 help use, Help-Ledger preview review, and Progress-Journal append preparation. All confirmations remain false by default; no local writes start automatically, and no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims are returned.",
            },
            {
                "step_id": "review_python_exam_operator_gate_decision_receipt",
                "label": "Create a hash-only decision receipt for the current Operator Gate confirmation state.",
                "command": "POST /api/unibot/course/python-exam-operator-gate-decision-receipt",
                "success_check": "Decision Receipt consumes only Operator Gate metadata and records confirmed/unconfirmed card hashes, next confirmable step, and the next allowed local action without executing it. Default remains no confirmations, no local writes, dry-run, A0-A2, and not_cleared; no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims are returned.",
            },
            {
                "step_id": "review_python_exam_local_cycle_start_packet",
                "label": "Create the final metadata-only start packet for the next local Python exam cycle.",
                "command": "POST /api/unibot/course/python-exam-local-cycle-start-packet",
                "success_check": "Local Cycle Start Packet consumes only Safe Cycle Console, Operator Gate, and Decision Receipt metadata. It states blocked_for_confirmation or ready_after_human_confirmation, lists skill tag, next safe action, task/checkpoint hashes, Source-Card anchors, A0-A2 help level, Gate/Decision receipt hashes, open confirmations, confirmed hash metadata, and next safe user action. It never executes local actions and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_local_cycle_readiness_review",
                "label": "Review whether the local Python exam cycle is still blocked or ready for manual local review.",
                "command": "POST /api/unibot/course/python-exam-local-cycle-readiness-review",
                "success_check": "Readiness Review consumes only the Local Cycle Start Packet and returns one recommendation: keep_blocked, request_missing_confirmation_review, or ready_for_manual_local_cycle_review. It inspects packet status, open confirmations, confirmed hash metadata, Gate/Decision/Start receipt hashes, skill tag, next safe action, task/checkpoint hashes, Source-Card anchors, and A0-A2 help level, while returning no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "handoff_python_exam_local_cycle_readiness",
                "label": "Turn the readiness review into an operator-run prefill and manual local-cycle handoff.",
                "command": "POST /api/unibot/course/python-exam-local-cycle-readiness-handoff",
                "success_check": "Readiness Handoff consumes only the Readiness Review and Local Cycle Start Packet, then prepares a dry-run operator-run prefill plus a manual handoff packet with skill tag, task/checkpoint hashes, Source-Card anchors, A0-A2 help level, open/confirmed counts, and not_cleared status. It never executes local actions and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_local_cycle_operator_workspace_card",
                "label": "Review the notebook-first local-cycle operator workspace card before any manual local cycle.",
                "command": "POST /api/unibot/course/python-exam-local-cycle-operator-workspace-card",
                "success_check": "Local Cycle Operator Workspace Card consumes only the Readiness Review, Readiness Handoff, and Local Cycle Start Packet, then compacts recommendation, help-ledger preview, operator-run prefill, manual handoff, skill tag, task/checkpoint hashes, Source-Card anchors, A0-A2 help level, and not_cleared state into a notebook-first metadata-only view. It never executes local actions and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_local_cycle_chain_snapshot",
                "label": "Review the hash-only local-cycle evidence chain before any manual local cycle.",
                "command": "POST /api/unibot/course/python-exam-local-cycle-chain-snapshot",
                "success_check": "Local Cycle Chain Snapshot consumes only the Readiness Review, Readiness Handoff, and Local Cycle Operator Workspace Card, then compacts the review recommendation, handoff prefill, workspace card, task/checkpoint hashes, Source-Card anchors, help-ledger preview hash, and receipt hashes into a hash-only evidence chain. It never executes local actions and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_local_cycle_manual_confirmation_console",
                "label": "Review open and confirmed local-cycle operator confirmations side by side.",
                "command": "POST /api/unibot/course/python-exam-local-cycle-manual-confirmation-console",
                "success_check": "Manual Confirmation Console consumes only Readiness Review, Handoff, Operator Workspace Card, and Chain Snapshot metadata, then shows open and confirmed confirmation hashes side by side and returns exactly one next manual action: review_missing_confirmation, confirm_hash_metadata_manually, refresh_start_packet_review, or continue_to_manual_local_cycle. It never executes or writes local actions and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_cycle_launch_receipt",
                "label": "Review the final hash-only launch receipt before any manual local cycle action.",
                "command": "POST /api/unibot/course/python-exam-manual-cycle-launch-receipt",
                "success_check": "Manual Cycle Launch Receipt consumes only Manual Confirmation Console, Chain Snapshot, Operator Workspace Card, and Operator-Run Prefill metadata, then returns one launch decision: stay_in_confirmation_review, ready_for_manual_local_cycle, refresh_manual_console, or abort_manual_cycle_review. It executes nothing, writes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_cycle_evidence_binder",
                "label": "Bind the manual local-cycle stop-go chain into one hash-only evidence packet.",
                "command": "POST /api/unibot/course/python-exam-manual-cycle-evidence-binder",
                "success_check": "Manual Cycle Evidence Binder consumes only Launch Receipt, Manual Confirmation Console, Chain Snapshot, Operator Workspace Card, and Readiness Review metadata, then returns one next safe review action with launch decision, open/confirmed confirmation hashes, Source-Card anchors, task/checkpoint hashes, Help-Ledger preview hash, Gate/Decision/Start/Chain/Launch receipt hashes, and not_cleared status. It executes nothing, writes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_post_cycle_receipt_intake",
                "label": "Review hash-only post-cycle receipt metadata after a human-run local cycle action.",
                "command": "POST /api/unibot/course/python-exam-manual-post-cycle-receipt-intake",
                "success_check": "Manual Post-Cycle Receipt Intake consumes only Evidence Binder, Launch Receipt, Manual Confirmation Console, and optional human-provided post-cycle hash metadata such as notebook checkpoint hash, Help-Ledger entry hash, task hash, Source-Card anchors, and operator reflection hash. It returns exactly one recommendation: keep_post_cycle_review_open, request_missing_post_cycle_hashes, accept_hash_only_post_cycle_receipt_for_human_review, or reject_post_cycle_receipt. It executes nothing, writes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_cycle_closure_ledger",
                "label": "Close or keep open the manual local-cycle ledger for human review.",
                "command": "POST /api/unibot/course/python-exam-manual-cycle-closure-ledger",
                "success_check": "Manual Cycle Closure Ledger consumes only Post-Cycle Receipt Intake, Evidence Binder, Launch Receipt, and Manual Confirmation Console metadata. It documents the pre-cycle stop-go chain, post-cycle intake recommendation, missing hashes, accepted post-cycle hashes, Source-Card anchors, task/checkpoint hashes, Help-Ledger hash, operator reflection hash, and next safe review action, then returns exactly one ledger decision: keep_cycle_open, request_post_cycle_hash_review, close_cycle_for_human_review, or reject_cycle_closure. It executes nothing, writes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_cycle_review_timeline",
                "label": "Review the chronological hash-only timeline for the manual local cycle.",
                "command": "POST /api/unibot/course/python-exam-manual-cycle-review-timeline",
                "success_check": "Manual Cycle Review Timeline consumes only Closure Ledger, Post-Cycle Receipt Intake, Evidence Binder, Launch Receipt, and Manual Confirmation Console metadata. It presents Pre-Cycle Stop-Go, Launch Decision, Evidence Binder, Post-Cycle Intake, Closure Ledger, missing hashes, accepted post-cycle hashes, Source-Card anchors, task/checkpoint hashes, Help-Ledger hash, operator reflection hash, and next safe review action, then returns one recommendation: continue_cycle_review, collect_missing_hashes, ready_for_human_timeline_review, or reject_timeline_review. It executes nothing, writes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_cycle_review_packet",
                "label": "Review the compact hash-only packet before submission or archiving.",
                "command": "POST /api/unibot/course/python-exam-manual-cycle-review-packet",
                "success_check": "Manual Cycle Review Packet consumes only Review Timeline, Closure Ledger, Post-Cycle Receipt Intake, Evidence Binder, Launch Receipt, and Manual Confirmation Console metadata. It bundles timeline recommendation, closure decision, missing hashes, accepted post-cycle hashes, Source-Card anchors, task/checkpoint hashes, Help-Ledger hash, operator reflection hash, receipt hashes, timeline event hashes, and next safe review action, then returns one packet recommendation: keep_review_packet_open, request_hash_completion, ready_for_human_packet_review, or reject_review_packet. It executes nothing, writes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_review_export_preview",
                "label": "Preview the hash-only export manifest before any archive or submission decision.",
                "command": "POST /api/unibot/course/python-exam-manual-review-export-preview",
                "success_check": "Manual Review Export Preview consumes only Review Packet, Review Timeline, Closure Ledger, Post-Cycle Receipt Intake, Evidence Binder, Launch Receipt, and Manual Confirmation Console metadata. It bundles packet recommendation, timeline recommendation, closure decision, missing hashes, accepted post-cycle hashes, Source-Card anchors, task/checkpoint hashes, Help-Ledger hash, operator reflection hash, receipt hashes, timeline event hashes, export manifest hash, and next safe review action, then returns one export-preview recommendation: keep_export_preview_open, request_hash_completion, ready_for_human_export_review, or reject_export_preview. It executes nothing, writes nothing, creates no export, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_review_export_authorization_gate",
                "label": "Gate the hash-only export preview before any human export authorization review.",
                "command": "POST /api/unibot/course/python-exam-manual-review-export-authorization-gate",
                "success_check": "Manual Review Export Authorization Gate consumes only Manual Review Export Preview, Review Packet, Review Timeline, and Closure Ledger metadata. It bundles export-preview recommendation, export manifest hash, packet/timeline/closure decisions, missing hashes, accepted post-cycle hashes, receipt hashes, timeline event hashes, and next safe review action, then returns one authorization gate decision: keep_export_blocked, request_hash_completion, ready_for_manual_export_authorization_review, or reject_export_authorization. It executes nothing, writes nothing, starts no local action, creates no export, authorizes no export, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_export_review_queue",
                "label": "Queue hash-only export-review candidates for human review.",
                "command": "POST /api/unibot/course/python-exam-manual-export-review-queue",
                "success_check": "Manual Export Review Queue consumes only Export Authorization Gate, Export Preview, Review Packet, Review Timeline, and optional hash-only queue candidate metadata. It groups each candidate by gate decision, export manifest hash, authorization gate hash, preview/packet/timeline receipt hashes, missing hashes, accepted post-cycle hashes, skill tag, help level, Source-Card anchors, timeline event hashes, and next safe review action, then returns one queue recommendation: keep_queue_open, request_hash_completion, ready_for_manual_export_review_queue, or reject_queue_entry. It executes nothing, writes nothing, starts no local action, creates no export, authorizes no export, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_export_reviewer_packet",
                "label": "Review the hash-only export reviewer packet before any archive or submission decision.",
                "command": "POST /api/unibot/course/python-exam-manual-export-reviewer-packet",
                "success_check": "Manual Export Reviewer Packet consumes only Manual Export Review Queue, Export Authorization Gate, Export Preview, Review Packet, and Review Timeline metadata. It bundles queue recommendation, candidate hashes, gate decisions, export manifest hash, authorization gate hash, preview/packet/timeline receipt hashes, missing hashes, accepted post-cycle hashes, skill tag, help level, Source-Card anchors, timeline event hashes, queue hash, and next safe review action, then returns one packet recommendation: keep_reviewer_packet_open, request_hash_completion, ready_for_human_reviewer_packet, or reject_reviewer_packet. It executes nothing, writes nothing, starts no local action, creates no export, authorizes no export, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_archive_decision_draft",
                "label": "Draft the hash-only archive or submission decision for human review.",
                "command": "POST /api/unibot/course/python-exam-manual-archive-decision-draft",
                "success_check": "Manual Archive Decision Draft consumes only Manual Export Reviewer Packet, Manual Export Review Queue, Export Authorization Gate, and Export Preview metadata. It bundles reviewer-packet recommendation, queue recommendation, candidate hashes, reviewer-packet hash, queue hash, export manifest hash, authorization gate hash, receipt hashes, missing hashes, accepted post-cycle hashes, skill tag, help level, Source-Card anchors, timeline event hashes, and next safe decision action, then returns one draft recommendation: keep_archive_decision_draft_open, request_hash_completion, ready_for_manual_archive_decision_review, or reject_archive_decision_draft. It executes nothing, writes nothing, starts no local action, creates no export, archives nothing, submits nothing, authorizes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_final_review_handoff",
                "label": "Review the final hash-only handoff before any export, archive, or submission action.",
                "command": "POST /api/unibot/course/python-exam-manual-final-review-handoff",
                "success_check": "Manual Final Review Handoff consumes only Manual Archive Decision Draft, Manual Export Reviewer Packet, Manual Export Review Queue, and Export Authorization Gate metadata. It bundles archive-decision-draft recommendation, reviewer-packet recommendation, queue recommendation, gate decisions, candidate hashes, draft hash, reviewer-packet hash, queue hash, export manifest hash, authorization gate hash, receipt hashes, missing hashes, accepted post-cycle hashes, skill tag, help level, Source-Card anchors, timeline event hashes, and next safe human review action, then returns one handoff recommendation: keep_final_handoff_open, request_hash_completion, ready_for_manual_final_review, or reject_final_handoff. It executes nothing, writes nothing, starts no local action, creates no export, archives nothing, submits nothing, authorizes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_manual_final_review_receipt_ledger",
                "label": "Review the chronological hash-only final review receipt ledger.",
                "command": "POST /api/unibot/course/python-exam-manual-final-review-receipt-ledger",
                "success_check": "Manual Final Review Receipt Ledger consumes only Manual Final Review Handoff, Manual Archive Decision Draft, Manual Export Reviewer Packet, and Manual Export Review Queue metadata. It bundles handoff recommendation, archive-decision-draft recommendation, reviewer-packet recommendation, queue recommendation, gate decisions, handoff hash, draft hash, reviewer-packet hash, queue hash, export manifest hash, authorization gate hash, receipt hashes, candidate hashes, missing hashes, accepted post-cycle hashes, skill tag, help level, Source-Card anchors, timeline event hashes, ledger event hashes, and next safe human review action, then returns one ledger recommendation: keep_final_ledger_open, request_hash_completion, ready_for_manual_final_ledger_review, or reject_final_ledger. It executes nothing, writes nothing, starts no local action, creates no export, archives nothing, submits nothing, authorizes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_final_review_ledger_integrity_gate",
                "label": "Gate the final review ledger for hash-chain integrity before any export, archive, or submission proximity.",
                "command": "POST /api/unibot/course/python-exam-final-review-ledger-integrity-gate",
                "success_check": "Final Review Ledger Integrity Gate consumes only Manual Final Review Receipt Ledger, Manual Final Review Handoff, Manual Archive Decision Draft, Manual Export Reviewer Packet, and Manual Export Review Queue metadata. It compares ledger event hashes, handoff hash, draft hash, reviewer-packet hash, queue hash, export manifest hash, authorization gate hash, receipt hashes, candidate hashes, missing hashes, accepted post-cycle hashes, skill tag, help level, Source-Card anchors, timeline event hashes, and next safe human review action, then returns one gate recommendation: keep_integrity_gate_open, request_hash_reconciliation, ready_for_manual_integrity_review, or reject_integrity_chain. It executes nothing, writes nothing, starts no local action, creates no export, archives nothing, submits nothing, authorizes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_final_manual_review_console",
                "label": "Review the single final hash-only human console before any export, archive, or submission proximity.",
                "command": "POST /api/unibot/course/python-exam-final-manual-review-console",
                "success_check": "Final Manual Review Console consumes only Final Review Ledger Integrity Gate, Manual Final Review Receipt Ledger, Manual Final Review Handoff, Manual Archive Decision Draft, Manual Export Reviewer Packet, and Manual Export Review Queue metadata. It shows gate recommendation, ledger recommendation, handoff recommendation, draft/reviewer/queue recommendations, integrity issues, missing hashes, mismatched hashes, Source-Card anchors, help level, skill tag, receipt hashes, timeline/ledger event hashes, accepted post-cycle hashes, and exactly one next safe human review action, then returns one console recommendation: keep_final_console_open, request_integrity_reconciliation, ready_for_manual_console_review, or reject_final_console. It executes nothing, writes nothing, starts no local action, creates no export, archives nothing, submits nothing, authorizes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_final_manual_review_action_lock",
                "label": "Review the final hash-only action lock before any export, archive, or submission proximity.",
                "command": "POST /api/unibot/course/python-exam-final-manual-review-action-lock",
                "success_check": "Final Manual Review Action Lock consumes only Final Manual Review Console, Final Review Ledger Integrity Gate, and Manual Final Review Receipt Ledger metadata. It checks console recommendation, integrity-gate recommendation, open integrity issues, missing hashes, mismatched hashes, receipt hashes, timeline/ledger event hashes, skill tag, help level, Source-Card anchors, and next safe human review action, then returns one lock recommendation: keep_action_locked, request_manual_reconciliation, ready_for_manual_action_review, or reject_action_path. It executes nothing, writes nothing, starts no local action, creates no export, archives nothing, submits nothing, authorizes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_locked_final_review_board",
                "label": "Review the locked final hash-only board before any export, archive, or submission proximity.",
                "command": "POST /api/unibot/course/python-exam-locked-final-review-board",
                "success_check": "Locked Final Review Board consumes only Final Manual Review Action Lock, Final Manual Review Console, Final Review Ledger Integrity Gate, Manual Final Review Receipt Ledger, Draft Package Review Console, Human Handoff Packet, and Full Local Rehearsal Pack metadata. It shows lock recommendation, console/gate/ledger recommendations, draft/handoff/rehearsal status, open hash issues, missing hashes, mismatched hashes, receipt hashes, timeline/ledger event hashes, skill tag, help level, Source-Card anchors, accepted post-cycle hashes, and exactly one next safe human review action, then returns one board recommendation: keep_final_board_open, request_manual_reconciliation, ready_for_human_final_board_review, or reject_final_board. It executes nothing, writes nothing, starts no local action, creates no export, archives nothing, submits nothing, authorizes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_locked_final_review_gap_resolver",
                "label": "Review the locked final hash-only gap resolver before any rehearsal recheck or final board follow-up.",
                "command": "POST /api/unibot/course/python-exam-locked-final-review-gap-resolver",
                "success_check": "Locked Final Review Gap Resolver consumes only Locked Final Review Board, Final Manual Review Action Lock, Full Local Rehearsal Pack, Rehearsal Playback Gap Coach, and Guided Loop Control Surface metadata. It shows board recommendation, lock recommendation, open hash issues, missing hashes, mismatched hashes, affected review layer, receipt hashes, timeline/ledger event hashes, skill tag, help level, Source-Card anchors, rehearsal/gap-coach status, and one prioritized non-executing repair card, then returns one resolver recommendation: keep_gap_resolver_open, request_manual_reconciliation, ready_for_manual_rehearsal_recheck, or reject_gap_resolution. It executes nothing, writes nothing, starts no local action, creates no export, archives nothing, submits nothing, authorizes nothing, and returns no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, scores, percentages, rankings, grades, proctoring, AI detection, automatic grading, or clearance claims.",
            },
            {
                "step_id": "start_exam_workspace_operator_run",
                "label": "Review the Start Exam Workspace operator receipt.",
                "command": "POST /api/unibot/exam-workspace/operator-run",
                "success_check": "Operator run merges material coverage, notebook checkpoint, A2 tutor state, Help-Ledger preview, export receipt, and individual operator confirmations into one human-readable dry-run view; default remains no local writes and not_cleared.",
            },
            {
                "step_id": "review_exam_workspace_session_console",
                "label": "Review the Exam Workspace Session Console.",
                "command": "POST /api/unibot/exam-workspace/session-console",
                "success_check": "Console summarizes selected skill, workspace status, notebook checkpoint hash, A0-A2 tutor state, Help-Ledger preview, export receipt, open operator confirmations, and repeat dry-run receipt evidence without raw queries, course raw text, notebook code, local paths, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "review_exam_workspace_run_history_export",
                "label": "Review the hash-only run history and export review package.",
                "command": "POST /api/unibot/exam-workspace/run-history-export-review",
                "success_check": "Review aggregates Session Console receipts into skill, checkpoint hashes, help-level profile, Help-Ledger preview, blockers, operator confirmations, export receipt, and reflection status without raw queries, course raw text, notebook code, local paths, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "review_course_exam_coverage_dashboard",
                "label": "Review the per-skill Course Exam Coverage Dashboard.",
                "command": "POST /api/unibot/course/exam-coverage-dashboard",
                "success_check": "Dashboard merges material coverage, skill readiness, source/notebook anchors, OCR/video gaps, checkpoint hashes, help-level profile, operator confirmations, and next safe step per Python exam skill without raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "route_per_skill_next_action",
                "label": "Route the selected Python exam skill to the next safe dry-run action.",
                "command": "POST /api/unibot/course/per-skill-action-router",
                "success_check": "Router returns one primary dry-run route plus secondary endpoints, A0-A2 help policy, payload template, operator-confirmation status, and safety contract without executing writes or exposing raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "execute_routed_dry_run",
                "label": "Execute the selected router route as a controlled dry-run.",
                "command": "POST /api/unibot/course/routed-action-executor",
                "success_check": "Executor consumes selected_route and payload template, runs the matching dry-run harness, returns result summary and receipt only, keeps write-capable routes behind explicit operator confirmations, and exposes no raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "build_exam_run_packet",
                "label": "Build the compact exam-near work packet for the selected Python skill.",
                "command": "POST /api/unibot/course/exam-run-packet",
                "success_check": "Packet joins Dashboard, Router, Executor, Session Console receipts, and Run-History Export Review into readiness, selected route, dry-run receipt, checkpoint hashes, help-level profile, open confirmations, next safe action, and human-reviewable independence trace without raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "review_exam_packet_timeline",
                "label": "Review the compact timeline for the selected Python skill.",
                "command": "POST /api/unibot/course/exam-packet-timeline",
                "success_check": "Timeline shows metadata/hash events only: packet receipt, route, executed dry-run, checkpoint hashes, help-level profile, open operator confirmations, reflection status, and next safe action without raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "build_timeline_export_review_packet",
                "label": "Build the human-reviewable Timeline Export Review Packet.",
                "command": "POST /api/unibot/course/timeline-export-review-packet",
                "success_check": "Packet bundles per-skill timeline events, packet receipts, router/executor receipts, checkpoint hashes, help-level profile, open operator confirmations, reflection status, next safe action, and reviewer questions; optional local export receipt remains behind operator confirmation and not_cleared without raw queries, course raw text, notebook code, local paths, values, solutions, final interpretations, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "preview_or_append_timeline_export_receipt_journal",
                "label": "Preview or append the Timeline Export Receipt Journal record.",
                "command": "POST /api/unibot/course/timeline-export-receipt-journal/append",
                "success_check": "Without operator confirmation, returns a write preview only; with confirmation, appends a local hash-/metadata-only receipt record containing receipt id/hash, skill tags, event/checkpoint/question counts, help profile, open confirmations, reflection status, timestamp, and not_cleared status without returning local paths or raw data.",
            },
            {
                "step_id": "summarize_timeline_export_receipt_journal",
                "label": "Summarize repeated Timeline Export Receipt Journal records.",
                "command": "POST /api/unibot/course/timeline-export-receipt-journal/summary",
                "success_check": "Summary aggregates accepted/blocked records, skill tags, event/checkpoint/question counts, help profile, open confirmations, and reflection status while preserving not_cleared and excluding raw queries, course raw text, notebook code, local paths, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "check_review_chain_integrity",
                "label": "Check the metadata-only review chain integrity.",
                "command": "POST /api/unibot/course/review-chain-integrity-check",
                "success_check": "Checks Exam Run Packet, Exam Packet Timeline, Timeline Export Review Packet, and Receipt Journal Summary/Append for receipt ids/hashes, counts, skill tags, help profile, confirmations, reflection, journal status, and not_cleared; marks missing, duplicate, or contradictory links and returns the next safe action without raw data or clearance claims.",
            },
            {
                "step_id": "show_python_exam_readiness_console",
                "label": "Show the selected Python skill readiness console.",
                "command": "POST /api/unibot/course/python-exam-readiness-console",
                "success_check": "Combines Course Coverage, Exam-Skill Drilldown, Review Chain Integrity, and Receipt Journal Summary into selected-skill readiness, material/tutor coverage, latest checkpoint hash, A0-A2 help status, open operator confirmations, review-chain status, next safe action, and real-world clearance reminder while preserving not_cleared and excluding raw data, code, paths, values, solutions, grading, proctoring, AI detection, and clearance claims.",
            },
            {
                "step_id": "run_python_exam_cockpit_flow",
                "label": "Show the guided Python Exam Cockpit Flow step bar.",
                "command": "POST /api/unibot/course/python-exam-cockpit-flow",
                "success_check": "Shows the ordered cockpit sequence Skill selection -> Readiness -> Start Exam Workspace Operator Dry-Run -> Session Console -> Notebook Checkpoint -> A0-A2 Tutor Sidecar -> Help-/Exam-Ledger Preview -> Review Chain Integrity -> Export/Receipt Summary with status, next safe action, open operator confirmations, and evidence receipts; it performs no local writes itself, remains dry-run by default, preserves not_cleared, and excludes raw data, code, paths, values, solutions, grading, proctoring, AI detection, and clearance claims.",
            },
            {
                "step_id": "show_python_exam_live_control_surface",
                "label": "Show the sidepanel-first Python Exam Live Control Surface.",
                "command": "POST /api/unibot/course/python-exam-live-control-surface",
                "success_check": "Maps every Cockpit Flow step to one direct safe sidepanel action with status lights, current step, evidence receipts, open operator confirmations, A0-A2 help status, dry-run default, and next safe action. It performs no local writes itself, preserves not_cleared, and excludes raw data, code, paths, values, solutions, grading, proctoring, AI detection, and clearance claims.",
            },
            {
                "step_id": "show_python_exam_evidence_export_preview",
                "label": "Show the Python Exam Evidence Export Preview manifest.",
                "command": "POST /api/unibot/course/python-exam-evidence-export-preview",
                "success_check": "Bundles selected-skill readiness, cockpit steps, Live Control actions, evidence receipts, A0-A2 help profile, open operator confirmations, review-chain status, notebook checkpoint hash, receipt-journal summary, and human-review questions into a preview-only manifest. It writes no local export package, requires a future explicit operator confirmation for export writes, preserves not_cleared, and excludes raw data, code, paths, values, solutions, grading, proctoring, AI detection, and clearance claims.",
            },
            {
                "step_id": "write_python_exam_confirmed_local_export_draft",
                "label": "Preview or write the confirmed local Python Exam Export Draft.",
                "command": "POST /api/unibot/course/python-exam-confirmed-local-export-draft",
                "success_check": "Dry-run returns a write preview by default. With operator_confirmed_local_export_draft_write true and a ready Evidence Export Preview, it writes a local hash-based draft package containing manifest, process log, not_cleared receipt, and draft receipt, while the API output returns only package id/hash, file hashes, counts, confirmation status, and not_cleared state. It never exposes local paths, raw data, code, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_draft_package",
                "label": "Review the Python Exam Draft Package without exposing local paths.",
                "command": "POST /api/unibot/course/python-exam-draft-package-review-console",
                "success_check": "Checks written-or-preview draft status, package id/hash, file-hash integrity, manifest presence, not_cleared receipt, process log, A0-A2 help profile, review-chain status, receipt-journal status, open operator confirmations, review questions, and next safe action. It returns no local paths, raw data, code, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "copy_python_exam_human_handoff_packet",
                "label": "Copy the Python Exam Human Handoff Packet for review.",
                "command": "POST /api/unibot/course/python-exam-human-handoff-packet",
                "success_check": "Bundles package id, file hashes, review-console status, A0-A2 profile, review questions, open operator confirmations, notebook checkpoint hash, receipt-journal summary, review-chain status, not_cleared receipt, and next safe action into a compact copy/export view. It returns no local paths, raw data, code, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_full_local_rehearsal_pack",
                "label": "Review the full local Python exam rehearsal pack.",
                "command": "POST /api/unibot/course/python-exam-full-local-rehearsal-pack",
                "success_check": "Compacts the selected Python skill into one full local dry-run review: skill selection, Source-Card anchors, Local Cycle Readiness Review, Handoff, Operator Workspace Card, Chain Snapshot, Operator Dry-Run, Session Console, Run History, Exam Run Packet, Timeline, Evidence Export Preview, and Human Handoff Packet. It performs no local writes by itself, keeps dry-run and A0-A2 by default, requires explicit operator confirmation for local writes, preserves not_cleared, and returns no raw data, code, local paths, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_rehearsal_playback_gap_coach",
                "label": "Review the Python Exam Rehearsal Playback Gap Coach.",
                "command": "POST /api/unibot/course/python-exam-rehearsal-playback-gap-coach",
                "success_check": "Replays the latest Full Local Rehearsal Pack for one selected Python skill and derives exactly one safe next action: ready_to_rehearse_again, resolve_missing_artifact, resolve_source_gap, review_operator_confirmation, continue_a0_a2_drill, or ready_for_human_review_packet. It summarizes only metadata, Source-Card anchors, checkpoint hashes, A0-A2 profile, confirmations, Evidence Preview status, and Human Handoff status; it performs no writes and returns no raw data, code, local paths, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "run_python_exam_gap_coach_guided_rehearsal_loop",
                "label": "Prepare the next Python Exam Guided Rehearsal Loop step.",
                "command": "POST /api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop",
                "success_check": "Consumes the Gap Coach next_safe_action_key and prepares exactly one dry-run next-step card: missing artifact review, Source-Card/checkpoint review, operator confirmation review, A0-A2 drill, another full rehearsal, or Human Review Packet handoff. It performs no writes, starts no local execution, preserves not_cleared, and returns no raw data, code, local paths, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "review_python_exam_guided_loop_control_surface",
                "label": "Review the Python Exam Guided Loop Control Surface.",
                "command": "POST /api/unibot/course/python-exam-guided-loop-control-surface",
                "success_check": "Renders the current Guided Rehearsal Loop card as a visible next-click control surface: action key, route, endpoint, prefill hash, Source-Card anchors, checkpoint hashes, open operator confirmations, A0-A2 profile, Evidence Preview status, Human Handoff status, and next safe click. It prepares dry-run metadata only, performs no writes, preserves not_cleared, and returns no raw data, code, local paths, values, solutions, grading, proctoring, AI detection, or clearance claims.",
            },
            {
                "step_id": "validate_extraction_deferral",
                "label": "Validate an intentional extraction deferral record when remaining jobs are deliberately postponed.",
                "command": "POST /api/unibot/course/extraction-deferral/validate",
                "success_check": "Deferral is accepted only with scope, reviewer roles, reason, job coverage, no raw-text release, and exam_deployment_status not_cleared.",
            },
            {
                "step_id": "build_extraction_completion_report",
                "label": "Classify extraction completion from reviewed receipts or valid deferral evidence.",
                "command": "POST /api/unibot/course/extraction-completion-report",
                "success_check": "Report is public-safe and says complete only when all jobs are receipted, failed/skipped, absent, or covered by a valid intentional deferral.",
            },
            {
                "step_id": "build_extraction_progress_report",
                "label": "Aggregate extraction receipts into review queue and manifest candidates.",
                "command": "POST /api/unibot/course/extraction-progress-report",
                "success_check": "Report is public-safe and exposes only receipt metadata, review state, and hashes.",
            },
            {
                "step_id": "build_extraction_manifest_update_plan",
                "label": "Plan private manifest metadata updates from reviewed receipts.",
                "command": "POST /api/unibot/course/extraction-manifest-update-plan",
                "success_check": "Plan is public-safe, metadata-only, and exposes tutor-ready private update candidates without writing files.",
            },
            {
                "step_id": "build_tutor_coverage_plan",
                "label": "Forecast course tutor skill coverage after reviewed private manifest updates.",
                "command": "POST /api/unibot/course/tutor-coverage-plan",
                "success_check": "Plan is public-safe, forecast-only, and reports current/projected skill readiness without exposing private text.",
            },
            {
                "step_id": "run_course_material_coverage",
                "label": "Condense real course-material coverage into the next Exam-Workspace start point.",
                "command": "POST /api/unibot/course/material-coverage/run",
                "success_check": "Run reports per-skill tutor anchor readiness, OCR/video gaps, notebook exercise readiness, manifest/index journal summaries, and the next A0-A2 Exam-Workspace start point without raw text, notebook code, local paths, or clearance claims.",
            },
            {
                "step_id": "run_exam_workspace_launch_flow",
                "label": "Launch the selected coverage start point into a preconfigured Exam-Workspace dry-run.",
                "command": "POST /api/unibot/exam-workspace/launch-flow/dry-run",
                "success_check": "Launch returns the A2 query template, notebook cell checkpoint, source-anchor hint, Help-Ledger preview, and export receipt without raw query, notebook code, private text, local paths, writes by default, or clearance claims.",
            },
            {
                "step_id": "build_course_study_session_plan",
                "label": "Generate source-grounded retrieval and notebook practice from reviewed tutor anchors.",
                "command": "POST /api/unibot/course/study-session-plan",
                "success_check": "Plan is public-safe, practice-only, A0-A2 bounded, and includes retrieval, notebook, reflection, and spacing tasks.",
            },
            {
                "step_id": "validate_study_session_receipt",
                "label": "Validate one hash-only evidence receipt per completed study task.",
                "command": "POST /api/unibot/course/study-session-receipt/validate",
                "success_check": "Receipt stores evidence presence, help level, source anchor hash, and text hashes only; A6/final-solution exposure requires repeating the task.",
            },
            {
                "step_id": "build_study_session_review_report",
                "label": "Aggregate study receipts into a human-reviewable learning evidence report.",
                "command": "POST /api/unibot/course/study-session-review-report",
                "success_check": "Report is public-safe, non-grading, and summarizes evidence profiles without raw student text or Eigenleistung percentages.",
            },
            {
                "step_id": "build_stakeholder_submission_bundle",
                "label": "Build the public-safe bundle for the remaining human decisions.",
                "command": "POST /api/unibot/stakeholder/submission-bundle",
                "success_check": "Bundle has extraction and exam decision lanes, is not sent, and keeps exam deployment not_cleared.",
            },
            {
                "step_id": "prepare_stakeholder_decision_request",
                "label": "Prepare one lane-specific manual decision request.",
                "command": "POST /api/unibot/stakeholder/decision-request and POST /api/unibot/stakeholder/decision-request-markdown",
                "success_check": "Request is public-safe, not sent by UniBot, and includes a Markdown review export plus receipt template.",
            },
            {
                "step_id": "validate_stakeholder_decision_request_receipt",
                "label": "Validate a manual request receipt before treating a request as sent.",
                "command": "POST /api/unibot/stakeholder/decision-request/validate-receipt",
                "success_check": "Receipt stores a submission reference hash only and does not change extraction or exam gates.",
            },
            {
                "step_id": "record_stakeholder_decision_journal",
                "label": "Record request and receipt evidence in the local hash-only journal.",
                "command": "POST /api/unibot/stakeholder/decision-journal/append then POST /api/unibot/stakeholder/decision-journal/summary",
                "success_check": "Journal records hashes and statuses only; raw messages and written decision text are not stored.",
            },
            {
                "step_id": "validate_external_decision_state",
                "label": "Validate incoming written responses without raw decision storage.",
                "command": "POST /api/unibot/stakeholder/decision-state",
                "success_check": "State stores hashes, records next gates, and does not silently deploy exam mode.",
            },
            {
                "step_id": "record_external_decision_records",
                "label": "Store validated written decision records as local hash-only evidence.",
                "command": "POST /api/unibot/stakeholder/decision-record-journal/append then POST /api/unibot/stakeholder/decision-record-journal/summary",
                "success_check": "Journal stores accepted record metadata and hashes only; raw decisions are not stored and exam deployment remains not_cleared.",
            },
        ],
        "contributor_rules": [
            "Use synthetic tasks or public source cards only.",
            "Keep course-material work staged until permission and review status are explicit.",
            "Write tests for blocker, privacy, and exam-boundary behavior.",
            "Use public-safe summaries instead of copied personal reports or classroom artifacts.",
            "Treat browser-overlay results as practice evidence only, never as exam security evidence.",
            "Open GitHub issues only after reviewing the generated issue bundle manually.",
        ],
        "release_gates": [
            {
                "gate_id": "public_safety_scan",
                "required": True,
                "evidence": "Public scan reports pass for UniBot docs, code, extension files, and tests.",
            },
            {
                "gate_id": "redteam_smoke",
                "required": True,
                "evidence": "Red-team smoke reports pass for solution leakage, privacy, prompt injection, and exam boundary.",
            },
            {
                "gate_id": "publication_package",
                "required": True,
                "evidence": "Publication package reports public draft ready, not exam release.",
            },
            {
                "gate_id": "readiness_check",
                "required": True,
                "evidence": "Readiness check passes while exam_deployment_status remains not_cleared.",
            },
            {
                "gate_id": "github_issue_manual_review",
                "required": True,
                "evidence": "Issue drafts are reviewed before posting and contain only sanitized metadata.",
            },
            {
                "gate_id": "exam_authority_clearance",
                "required": False,
                "evidence": "Only a future exam release would require written Pruefungsamt, Datenschutz, IT, teaching, and inclusion review.",
            },
        ],
        "api_endpoints": [
            "/api/unibot/health",
            "/api/unibot/prompt-card",
            "/api/unibot/review-output",
            "/api/unibot/practice-flow",
            "/api/unibot/demo-run",
            "/api/unibot/demo-feedback/validate",
            "/api/unibot/demo-feedback/triage",
            "/api/unibot/github-issue-bundle",
            "/api/unibot/course/extraction-decision/local-intake",
            "/api/unibot/course/extraction-decision/local-intake/record",
            "/api/unibot/course/extraction-decision/workspace/prepare",
            "/api/unibot/course/extraction-decision/workspace/record",
            "/api/unibot/course/ocr-first/operator-run",
            "/api/unibot/course/extraction-operator-packet",
            "/api/unibot/course/extraction-batch-plan",
            "/api/unibot/course/extraction-batch-receipt-packet",
            "/api/unibot/course/private-extraction/run-batch",
            "/api/unibot/course/video-transcription/run-batch",
            "/api/unibot/course/extraction-receipt/validate",
            "/api/unibot/course/extraction-receipts/append",
            "/api/unibot/course/extraction-receipts/list",
            "/api/unibot/course/extraction-receipts/summary",
            "/api/unibot/course/extraction-review/validate",
            "/api/unibot/course/extraction-review/apply-plan",
            "/api/unibot/course/extraction-manifest/apply-dry-run",
            "/api/unibot/course/extraction-deferral/validate",
            "/api/unibot/course/extraction-completion-report",
            "/api/unibot/course/extraction-progress-report",
            "/api/unibot/course/extraction-manifest-update-plan",
            "/api/unibot/course/tutor-coverage-plan",
            "/api/unibot/course/study-session-plan",
            "/api/unibot/course/study-session-receipt/validate",
            "/api/unibot/course/study-session-review-report",
            "/api/unibot/institutional-clearance/board",
            "/api/unibot/institutional-clearance/validate",
            "/api/unibot/stakeholder/submission-bundle",
            "/api/unibot/stakeholder/submission-bundle-markdown",
            "/api/unibot/stakeholder/decision-request",
            "/api/unibot/stakeholder/decision-request-markdown",
            "/api/unibot/stakeholder/decision-request/validate-receipt",
            "/api/unibot/stakeholder/decision-journal/append",
            "/api/unibot/stakeholder/decision-journal/append-prepared-request",
            "/api/unibot/stakeholder/decision-journal/list",
            "/api/unibot/stakeholder/decision-journal/summary",
            "/api/unibot/stakeholder/decision-state",
            "/api/unibot/stakeholder/decision-record-journal/append",
            "/api/unibot/stakeholder/decision-record-journal/list",
            "/api/unibot/stakeholder/decision-record-journal/summary",
            "/api/unibot/publication-package",
            "/api/unibot/readiness-check",
            "/api/unibot/release-runbook",
        ],
        "troubleshooting": [
            {
                "symptom": "Local API is offline.",
                "try": "Start the local service and retry the health endpoint before using the side panel.",
            },
            {
                "symptom": "Side panel cannot read the page selection.",
                "try": "Use the copy/paste fallback and paste only public-safe task text.",
            },
            {
                "symptom": "Demo feedback is blocked.",
                "try": "Remove private details, confirm private_data_removed, then validate again.",
            },
            {
                "symptom": "Readiness is blocked.",
                "try": "Open the failed check evidence and fix the public-safety, red-team, or release-gate issue first.",
            },
            {
                "symptom": "A clearance record is blocked.",
                "try": "Check missing reviewer roles, overbroad modes, A6 help, proctoring, KI-detection, grading, or raw-text release clauses.",
            },
            {
                "symptom": "The extraction operator or receipt is blocked.",
                "try": "Provide a valid rights/privacy decision record, remove raw text fields, and verify the receipt decision hash and job metadata.",
            },
            {
                "symptom": "The extraction batch plan is ready but no extraction is complete.",
                "try": "Treat the batch plan as a work queue only; each job still needs local private execution, receipt validation, and human review.",
            },
            {
                "symptom": "The extraction batch receipt packet is ready but no receipts exist.",
                "try": "Use the packet templates for the selected local batch, then validate one metadata-only receipt per job before human review.",
            },
            {
                "symptom": "The private extraction runner is blocked.",
                "try": "Provide a valid local rights/privacy decision record first. The runner supports DOCX, text-PDF, and PPTX containers only and never runs without that gate; image-only PDFs and videos need separate approved local adapters.",
            },
            {
                "symptom": "Validated extraction receipts are lost between runs.",
                "try": "Append accepted receipts to the local extraction receipt journal and point progress, batch, manifest, coverage, or study APIs at receipt_journal_path.",
            },
            {
                "symptom": "Receipts are ready but no private manifest candidates exist.",
                "try": "Use the human-review apply-plan endpoint with hash-only review decisions. It can append reviewed_for_private_tutor receipts and review records, but it still does not write manifests or start tutor indexing.",
            },
            {
                "symptom": "Private manifest candidates are ready but the course tutor still has no new anchors.",
                "try": "Run the private manifest apply dry-run, inspect the delta and ExamScopeMap preview, then rerun with operator_confirmed_manifest_apply true only if the local metadata manifest should be updated. Tutor indexing is still a later explicit step.",
            },
            {
                "symptom": "Extraction completion is still open although the current scope can proceed.",
                "try": "Either add reviewed/failed/skipped receipts for every remaining job or validate a role-reviewed intentional deferral record, then rerun the completion report.",
            },
            {
                "symptom": "The extraction progress report is not ready for tutor indexing.",
                "try": "Fix invalid receipts, add missing receipts, or complete human review before applying private manifest updates.",
            },
            {
                "symptom": "The extraction manifest update plan has no candidates.",
                "try": "Complete human review first; only receipts marked reviewed_for_private_tutor become private manifest update candidates.",
            },
            {
                "symptom": "The tutor coverage plan shows no uplift.",
                "try": "Check whether reviewed candidates have skill tags and source-card metadata; apply private manifest metadata before rebuilding ExamScopeMap.",
            },
            {
                "symptom": "The study session plan has no ready tasks.",
                "try": "Build the course coverage plan, then review or extract at least one source-grounded tutor anchor before generating course-bound practice.",
            },
            {
                "symptom": "A study-session receipt is blocked.",
                "try": "Add the missing prediction, retrieval response, smallest notebook action, source anchor, and reflection; remove final solutions, full code, inserted values, raw course text, local paths, or A6 help.",
            },
            {
                "symptom": "The study review report is only partial.",
                "try": "Validate one hash-only receipt per planned task; repeat tasks where final-solution exposure occurred, and keep the report non-grading.",
            },
            {
                "symptom": "The stakeholder bundle is ready but the project is still not complete.",
                "try": "Treat the bundle as human-review preparation only; technical completion is blocked only by failed or open technical gates, while real exam clearance remains a separate reminder.",
            },
            {
                "symptom": "A stakeholder decision request exists but the gate is still open.",
                "try": "Validate a manual request receipt first, then validate the written decision record itself; the request packet alone never authorizes processing or exam use.",
            },
            {
                "symptom": "The decision journal has entries but extraction is still blocked.",
                "try": "Use the journal only as process evidence; local extraction still needs a valid rights/privacy decision record and extraction receipts.",
            },
            {
                "symptom": "Decision state validates records but completion remains open.",
                "try": "Append valid written decisions to the decision-record journal when available; missing exam clearance is a real-world reminder, while open extraction or receipt work remains the technical backlog.",
            },
            {
                "symptom": "The decision-record journal has accepted entries but the real gate is still not deployed.",
                "try": "That is expected: the journal is hash-only review evidence, not a deployment switch. Use completion audit for gate evidence and require a separate manual deployment decision.",
            },
        ],
        "public_language": [
            "Say public draft or local practice demo.",
            "Say not officially cleared for exam use.",
            "Do not say approved, granted, certified, or exam-secure unless written clearance exists.",
        ],
    }
    runbook["release_evidence_alignment"] = build_release_runbook_evidence_alignment(runbook["release_gates"])
    scan = scan_text(json.dumps(runbook, ensure_ascii=False), "release-runbook")
    runbook["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        runbook["status"] = "blocked"
        runbook["public_safety_findings"] = scan["findings"]
    return runbook


def build_release_runbook_markdown() -> str:
    runbook = build_release_runbook()
    quickstart = "\n".join(
        f"- `{step['step_id']}`: {step['label']} Command: `{step['command']}` Success: {step['success_check']}"
        for step in runbook["quickstart_steps"]
    )
    boundaries = "\n".join(f"- {item}" for item in runbook["boundaries"])
    contributor_rules = "\n".join(f"- {item}" for item in runbook["contributor_rules"])
    release_gates = "\n".join(
        f"- `{gate['gate_id']}`: required={gate['required']}; evidence: {gate['evidence']}"
        for gate in runbook["release_gates"]
    )
    alignment = runbook["release_evidence_alignment"]
    alignment_lines = "\n".join(
        f"- `{gate['gate_id']}`: checks {', '.join(gate['readiness_check_ids'])}; human gates {', '.join(gate['human_gates'])}"
        for gate in alignment["release_gates"]
    )
    review_board_thesis_contract = alignment["review_board_thesis_evaluation_claim_contract"]
    endpoints = "\n".join(f"- `{endpoint}`" for endpoint in runbook["api_endpoints"])
    troubleshooting = "\n".join(
        f"- {item['symptom']} Try: {item['try']}" for item in runbook["troubleshooting"]
    )
    public_language = "\n".join(f"- {item}" for item in runbook["public_language"])
    return (
        "# UniBot Release And Contributor Runbook\n\n"
        f"Status: {runbook['status']}\n\n"
        f"Exam deployment: {runbook['exam_deployment_status']}\n\n"
        f"Manual review required: {runbook['manual_review_required']}\n\n"
        "## Boundaries\n\n"
        f"{boundaries}\n\n"
        "## Quickstart\n\n"
        f"{quickstart}\n\n"
        "## Contributor Rules\n\n"
        f"{contributor_rules}\n\n"
        "## Release Gates\n\n"
        f"{release_gates}\n\n"
        "## Release Evidence Alignment\n\n"
        f"- Status: {alignment['status']}\n"
        f"- Snapshot schema: {alignment['readiness_snapshot_contract']['expected_schema_version']}\n"
        f"- Review-board schema: {alignment['review_board_contract']['expected_schema_version']}\n"
        f"- Review-board thesis/evaluation schema: {review_board_thesis_contract['expected_schema_version']}\n"
        f"- Review-board thesis/evaluation status: {review_board_thesis_contract['required_status']}\n"
        f"- GitHub issue schema: {alignment['github_issue_contract']['expected_schema_version']}\n"
        f"{alignment_lines}\n\n"
        "## API Endpoints\n\n"
        f"{endpoints}\n\n"
        "## Troubleshooting\n\n"
        f"{troubleshooting}\n\n"
        "## Public Language\n\n"
        f"{public_language}\n"
    )
