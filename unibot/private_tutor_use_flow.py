from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction import build_course_extraction_queue
from .extraction_manifest_apply import build_private_manifest_apply_dry_run
from .ledger import append_ledger_event
from .materials import sha256_text
from .public_safety import scan_text
from .source_cards import get_source_card
from .study_session import validate_study_session_receipt
from .tutor_index import build_private_index_tutor_response_dry_run, build_private_tutor_index_dry_run


PRIVATE_TUTOR_USE_FLOW_SCHEMA_VERSION = "unibot-private-tutor-use-flow-v1"
PRIVATE_TUTOR_USE_FLOW_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-private-tutor-use-flow-release-review-board-claim-alignment-v1"
)


def build_private_tutor_use_flow_dry_run(
    query: str,
    *,
    course_id: str = DEFAULT_COURSE_ID,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipts: list[dict[str, Any]] | None = None,
    receipt_journal_path: str | Path | None = None,
    private_manifest_path: str | Path | None = None,
    manifest_apply_journal_path: str | Path | None = None,
    tutor_index_path: str | Path | None = None,
    tutor_index_journal_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
    requested_help_level: str = "A2",
    mode: str = "exam_controlled_gateway",
    exam_status: str = "strict",
    operator_confirmed_manifest_apply: bool = False,
    operator_confirmed_tutor_index_build: bool = False,
    operator_confirmed_help_ledger_append: bool = False,
    study_receipt: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    workspace_card_source = (
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else {}
    )
    manifest_apply = build_private_manifest_apply_dry_run(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        receipts=receipts,
        receipt_journal_path=receipt_journal_path,
        private_manifest_path=private_manifest_path,
        manifest_apply_journal_path=manifest_apply_journal_path,
        operator_confirmed_manifest_apply=operator_confirmed_manifest_apply,
        public_safe=public_safe,
    )
    tutor_index = build_private_tutor_index_dry_run(
        course_id,
        private_manifest_path=private_manifest_path,
        tutor_index_path=tutor_index_path,
        tutor_index_journal_path=tutor_index_journal_path,
        operator_confirmed_tutor_index_build=operator_confirmed_tutor_index_build,
        public_safe=public_safe,
    )
    tutor_response = build_private_index_tutor_response_dry_run(
        query,
        course_id=course_id,
        tutor_index_path=tutor_index_path,
        mode=mode,
        requested_help_level=requested_help_level,
        exam_status=exam_status,
        public_safe=public_safe,
    )
    ledger_append = maybe_append_help_ledger(
        tutor_response,
        operator_confirmed=operator_confirmed_help_ledger_append,
        ledger_path=ledger_path,
    )
    local_cycle_workspace_card = safe_local_cycle_workspace_card(
        workspace_card_source,
        ledger_event_hash=str(ledger_append.get("event_hash", "")),
    )
    receipt_validation = validate_study_session_receipt(
        flow_study_receipt(tutor_response, study_receipt),
        public_safe=public_safe,
    )
    report = {
        "schema_version": PRIVATE_TUTOR_USE_FLOW_SCHEMA_VERSION,
        "artifact_type": "course_private_tutor_use_flow_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": private_tutor_use_flow_status(
            manifest_apply=manifest_apply,
            tutor_index=tutor_index,
            tutor_response=tutor_response,
            ledger_append=ledger_append,
            receipt_validation=receipt_validation,
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "End-to-end private tutor use flow. Standard is dry-run. It can apply reviewed private manifest "
            "metadata, build a hash-only tutor index, produce A0-A2 index-guided tutor help, append a Help-Ledger "
            "event only with operator confirmation, and validate a hash-only study receipt. It never returns raw "
            "course text, raw queries, local paths, complete code, inserted values, final interpretation, grading, "
            "proctoring, AI detection, or exam clearance."
        ),
        "flow_steps": [
            manifest_step_summary(manifest_apply),
            tutor_index_step_summary(tutor_index),
            tutor_response_step_summary(tutor_response),
            ledger_step_summary(ledger_append),
            study_receipt_step_summary(receipt_validation),
        ],
        "manifest_apply_summary": manifest_step_summary(manifest_apply),
        "tutor_index_summary": tutor_index_step_summary(tutor_index),
        "tutor_response_summary": tutor_response_step_summary(tutor_response),
        "ledger_append_summary": ledger_step_summary(ledger_append),
        "study_receipt_validation": receipt_validation,
        "local_cycle_operator_workspace_card": local_cycle_workspace_card,
        "operator_confirmed_manifest_apply": operator_confirmed_manifest_apply,
        "operator_confirmed_tutor_index_build": operator_confirmed_tutor_index_build,
        "operator_confirmed_help_ledger_append": operator_confirmed_help_ledger_append,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "private_manifest_path_returned": False,
        "tutor_index_path_returned": False,
        "ledger_path_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "next_actions": private_tutor_use_flow_next_actions(
            manifest_apply=manifest_apply,
            tutor_index=tutor_index,
            tutor_response=tutor_response,
            ledger_append=ledger_append,
            receipt_validation=receipt_validation,
        ),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def build_private_tutor_use_flow_release_claim_alignment(
    flow_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if flow_report is None:
        decision_record = synthetic_private_tutor_flow_decision_record()
        with tempfile.TemporaryDirectory(prefix="unibot_private_tutor_flow_alignment_") as temp_dir:
            fixture_root = Path(temp_dir) / "materials"
            (fixture_root / "Week 1").mkdir(parents=True)
            (fixture_root / "Week 1" / "pandas_boxplot_slides.pdf").write_bytes(b"%PDF-1.4\nfixture")
            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                rights_decision_reference=str(decision_record["decision_reference"]),
            )
            receipts = [
                synthetic_private_tutor_flow_reviewed_receipt(
                    queue["jobs"][0],
                    decision_reference_hash=sha256_text(str(decision_record["decision_reference"])),
                )
            ]
            flow_report = build_private_tutor_use_flow_dry_run(
                "How do I check pandas columns before plotting?",
                base_path=str(fixture_root),
                decision_record=decision_record,
                receipts=receipts,
                private_manifest_path=Path(temp_dir) / "private_manifest.json",
                manifest_apply_journal_path=Path(temp_dir) / "private_manifest_apply.jsonl",
                tutor_index_path=Path(temp_dir) / "private_tutor_index.json",
                tutor_index_journal_path=Path(temp_dir) / "private_tutor_index.jsonl",
                ledger_path=Path(temp_dir) / "help_ledger.jsonl",
                operator_confirmed_manifest_apply=True,
                operator_confirmed_tutor_index_build=True,
                operator_confirmed_help_ledger_append=True,
                requested_help_level="A2",
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                python_exam_local_cycle_operator_workspace_card=synthetic_private_tutor_flow_workspace_card(),
            )

    sections = [
        {
            "section_id": "reviewed_private_manifest_evidence_trace",
            "summary_claim": "private tutor use starts from reviewed private manifest evidence and operator-confirmed local apply",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "dfg-gwp"],
            "readiness_check_ids": ["private_tutor_use_flow", "extraction_human_review", "extraction_manifest_apply"],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "hash_only_tutor_index_trace",
            "summary_claim": "the tutor index is hash-only and local, with no returned paths or raw course text",
            "source_card_ids": ["dsk-ai-privacy-2024", "dfg-gwp"],
            "readiness_check_ids": ["private_tutor_use_flow", "extraction_manifest_apply", "extraction_completion"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "learner_agency_trace",
            "summary_claim": "private tutor responses stay within A0-A2 source-anchored Socratic help and validate study receipts",
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "private_tutor_use_flow",
                "python_exam_local_cycle_operator_workspace_card",
                "evaluation_packet",
                "review_board_packet",
            ],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
        },
        {
            "section_id": "not_authorized_trace",
            "summary_claim": "private tutor use does not clear public release, cloud processing, official grading, proctoring, KI-detection evidence, or exam deployment",
            "source_card_ids": ["eu-ai-act-2024", "uoc-ki-faq", "uoc-hilfsmittel"],
            "readiness_check_ids": ["private_tutor_use_flow", "external_decision_state", "exam_boundary"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    manifest_apply = flow_report.get("manifest_apply_summary", {})
    tutor_index = flow_report.get("tutor_index_summary", {})
    tutor_response = flow_report.get("tutor_response_summary", {})
    ledger = flow_report.get("ledger_append_summary", {})
    study_receipt = flow_report.get("study_receipt_validation", {})
    workspace_card = (
        flow_report.get("local_cycle_operator_workspace_card", {})
        if isinstance(flow_report.get("local_cycle_operator_workspace_card"), dict)
        else {}
    )
    blocked_claims = [
        "raw query returned",
        "raw extracted course text returned",
        "local path returned",
        "private manifest path returned",
        "tutor index path returned",
        "ledger path returned",
        "private manifest apply without operator confirmation",
        "private tutor index build without operator confirmation",
        "help ledger append without operator confirmation",
        "complete code or final-answer tutoring",
        "public raw course text release",
        "cloud processing",
        "exam deployment",
        "official grading",
        "proctoring",
        "KI-detection evidence",
    ]
    boundary = str(flow_report.get("execution_boundary", ""))
    allowed_help_levels = {"A0", "A1", "A2"}
    workspace_card_readiness_gate_linked = any(
        "python_exam_local_cycle_operator_workspace_card" in section["readiness_check_ids"] for section in sections
    )
    contracts = {
        "flow_public_safe": flow_report.get("public_safety_status") == "pass",
        "reviewed_private_manifest_evidence_operator_confirmed": manifest_apply.get("status") == "private_manifest_applied"
        and manifest_apply.get("manifest_written") is True
        and flow_report.get("operator_confirmed_manifest_apply") is True
        and manifest_apply.get("path_returned") is False,
        "hash_only_tutor_index_operator_confirmed": tutor_index.get("status") == "private_tutor_index_built"
        and tutor_index.get("tutor_index_built") is True
        and flow_report.get("operator_confirmed_tutor_index_build") is True
        and tutor_index.get("path_returned") is False
        and tutor_index.get("anchor_count", 0) >= 1,
        "learner_agency_a0_a2_source_anchored": tutor_response.get("status") == "allowed"
        and tutor_response.get("effective_help_level") in allowed_help_levels
        and tutor_response.get("source_anchor_count", 0) >= 1
        and tutor_response.get("raw_query_returned") is False
        and study_receipt.get("status") == "ok_study_session_receipt",
        "help_ledger_operator_confirmed_hash_only": ledger.get("status") == "stored"
        and ledger.get("ledger_written") is True
        and flow_report.get("operator_confirmed_help_ledger_append") is True
        and ledger.get("path_returned") is False
        and bool(ledger.get("event_hash")),
        "workspace_card_help_ledger_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") == ledger.get("event_hash")
        and workspace_card.get("checkpoint_hash") == ledger.get("event_hash")
        and workspace_card.get("selected_skill_tag") == study_receipt.get("skill_tag")
        and workspace_card.get("help_level") == tutor_response.get("effective_help_level")
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False,
        "public_outputs_hide_private_data": flow_report.get("raw_query_returned") is False
        and flow_report.get("raw_text_returned") is False
        and flow_report.get("local_paths_returned") is False
        and flow_report.get("private_manifest_path_returned") is False
        and flow_report.get("tutor_index_path_returned") is False
        and flow_report.get("ledger_path_returned") is False
        and "never returns raw course text" in boundary
        and "raw queries" in boundary
        and "local paths" in boundary,
        "high_stakes_actions_not_started": flow_report.get("exam_deployment_status") == "not_cleared"
        and flow_report.get("automatic_grading_started") is False
        and flow_report.get("proctoring_started") is False
        and flow_report.get("ai_detection_started") is False,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": blocked_claims,
        "flow_status": flow_report.get("status"),
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "private-tutor-use-flow-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": PRIVATE_TUTOR_USE_FLOW_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "flow_status": flow_report.get("status"),
        "flow_public_safety_status": flow_report.get("public_safety_status"),
        "exam_deployment_status": flow_report.get("exam_deployment_status"),
        "manifest_apply_status": manifest_apply.get("status"),
        "manifest_written": bool(manifest_apply.get("manifest_written", False)),
        "tutor_index_status": tutor_index.get("status"),
        "tutor_index_built": bool(tutor_index.get("tutor_index_built", False)),
        "tutor_index_anchor_count": tutor_index.get("anchor_count", 0),
        "tutor_response_status": tutor_response.get("status"),
        "effective_help_level": tutor_response.get("effective_help_level", ""),
        "source_anchor_count": tutor_response.get("source_anchor_count", 0),
        "ledger_status": ledger.get("status"),
        "ledger_written": bool(ledger.get("ledger_written", False)),
        "workspace_card_status": workspace_card.get("status"),
        "workspace_card_selected_skill_tag": workspace_card.get("selected_skill_tag"),
        "workspace_card_ready_for_operator_prefill": bool(workspace_card.get("ready_for_operator_prefill", False)),
        "workspace_card_help_ledger_status": workspace_card.get("help_ledger_preview_status"),
        "workspace_card_help_ledger_hash_present": bool(workspace_card.get("help_ledger_preview_hash")),
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_help_ledger_gate_linked": contracts["workspace_card_help_ledger_gate_linked"],
        "study_receipt_status": study_receipt.get("status"),
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "blocked_claims": blocked_claims,
        "public_safety_status": scan["status"],
        "policy": (
            "Private tutor use is a local, operator-confirmed learning flow. It may apply reviewed private "
            "manifest metadata, build a hash-only local tutor index, produce A0-A2 source-anchored help, "
            "and store hash-only Help-Ledger evidence, but it does not expose raw text or paths, approve "
            "public release, approve cloud processing, grade, proctor, detect AI use, or clear exams."
        ),
    }


def maybe_append_help_ledger(
    tutor_response: dict[str, Any],
    *,
    operator_confirmed: bool,
    ledger_path: str | Path | None,
) -> dict[str, Any]:
    event = ledger_event_from_tutor_response(tutor_response)
    if tutor_response.get("status") != "allowed":
        return {
            "status": "not_applicable_tutor_response_not_allowed",
            "ledger_written": False,
            "path_returned": False,
            "event_hash": sha256_text(json.dumps(event, sort_keys=True, ensure_ascii=False)),
        }
    if not operator_confirmed:
        return {
            "status": "dry_run_not_written",
            "ledger_written": False,
            "path_returned": False,
            "event_hash": sha256_text(json.dumps(event, sort_keys=True, ensure_ascii=False)),
        }
    stored = append_ledger_event(event, path=ledger_path)
    return {
        "status": stored.get("status", "stored"),
        "ledger_written": stored.get("status") == "stored",
        "path_returned": False,
        "event_hash": sha256_text(json.dumps(stored.get("record", {}), sort_keys=True, ensure_ascii=False)),
        "record_schema_version": stored.get("record", {}).get("schema_version", ""),
    }


def ledger_event_from_tutor_response(tutor_response: dict[str, Any]) -> dict[str, Any]:
    selected = tutor_response.get("selected_skill", {}) if isinstance(tutor_response.get("selected_skill"), dict) else {}
    ledger = tutor_response.get("help_ledger_preview", {}) if isinstance(tutor_response.get("help_ledger_preview"), dict) else {}
    classification = [] if tutor_response.get("status") == "allowed" else [str(tutor_response.get("status", "blocked"))]
    return {
        "mode": tutor_response.get("mode", "exam_controlled_gateway"),
        "tool": "unibot_private_index_tutor",
        "task_id": f"idx-flow-{str(tutor_response.get('query_hash', ''))[:12]}",
        "skill_tags": [selected.get("skill_tag", "general_python")],
        "raw_output_hash": ledger.get("raw_response_hash", sha256_text(str(tutor_response.get("answer_markdown", "")))),
        "classification": classification,
        "allowed_hint": str(tutor_response.get("answer_markdown", ""))[:500],
        "help_level": tutor_response.get("effective_help_level", "A2"),
        "privacy_flags": [],
        "source_card_ids": list(tutor_response.get("source_card_ids", []) or [])[:8],
        "student_reflection": "",
    }


def flow_study_receipt(tutor_response: dict[str, Any], study_receipt: dict[str, Any] | None) -> dict[str, Any]:
    selected = tutor_response.get("selected_skill", {}) if isinstance(tutor_response.get("selected_skill"), dict) else {}
    anchors = tutor_response.get("source_anchors", []) if isinstance(tutor_response.get("source_anchors"), list) else []
    first_anchor = anchors[0] if anchors and isinstance(anchors[0], dict) else {}
    base = {
        "task_id": f"idx-flow-{str(tutor_response.get('query_hash', ''))[:12]}",
        "skill_tag": selected.get("skill_tag", "general_python"),
        "help_level": tutor_response.get("effective_help_level", "A2"),
        "source_anchor_id": first_anchor.get("anchor_id", ""),
        "retrieval_response_present": tutor_response.get("status") == "allowed",
    }
    if study_receipt:
        base.update({key: value for key, value in study_receipt.items() if key not in {"solution", "final_answer", "raw_private_text"}})
    return base


def private_tutor_use_flow_status(
    *,
    manifest_apply: dict[str, Any],
    tutor_index: dict[str, Any],
    tutor_response: dict[str, Any],
    ledger_append: dict[str, Any],
    receipt_validation: dict[str, Any],
) -> str:
    if manifest_apply.get("status") == "blocked_public_safety" or tutor_index.get("status") == "blocked_public_safety":
        return "blocked_public_safety"
    if manifest_apply.get("status") == "blocked_until_valid_rights_privacy_decision":
        return "waiting_for_manifest_apply_rights_decision"
    if manifest_apply.get("status") in {"blocked_candidate_metadata", "waiting_for_reviewed_receipts"}:
        return str(manifest_apply.get("status"))
    if tutor_index.get("status") in {"waiting_for_private_manifest_apply", "waiting_for_tutor_usable_manifest_records"}:
        return str(tutor_index.get("status"))
    if tutor_response.get("status") != "allowed":
        return f"tutor_response_{tutor_response.get('status', 'blocked')}"
    if receipt_validation.get("status") == "repeat_task_required":
        return "repeat_task_required"
    if receipt_validation.get("status") == "blocked":
        return "study_receipt_needs_evidence"
    if ledger_append.get("ledger_written"):
        return "private_tutor_use_flow_ready_with_ledger"
    return "private_tutor_use_flow_dry_run_ready"


def manifest_step_summary(manifest_apply: dict[str, Any]) -> dict[str, Any]:
    candidates = manifest_apply.get("candidate_summary", {}) if isinstance(manifest_apply.get("candidate_summary"), dict) else {}
    return {
        "step_id": "private_manifest_apply",
        "status": manifest_apply.get("status", "unknown"),
        "candidate_count": candidates.get("candidate_count", 0),
        "records_to_apply_count": candidates.get("records_to_apply_count", 0),
        "manifest_written": bool(manifest_apply.get("manifest_written", False)),
        "path_returned": False,
    }


def tutor_index_step_summary(tutor_index: dict[str, Any]) -> dict[str, Any]:
    preview = tutor_index.get("index_preview", {}) if isinstance(tutor_index.get("index_preview"), dict) else {}
    return {
        "step_id": "private_tutor_index",
        "status": tutor_index.get("status", "unknown"),
        "anchor_count": preview.get("anchor_count", 0),
        "indexed_skill_count": preview.get("indexed_skill_count", 0),
        "tutor_index_built": bool(tutor_index.get("tutor_index_built", False)),
        "path_returned": False,
    }


def tutor_response_step_summary(tutor_response: dict[str, Any]) -> dict[str, Any]:
    selected = tutor_response.get("selected_skill", {}) if isinstance(tutor_response.get("selected_skill"), dict) else {}
    return {
        "step_id": "private_index_tutor_response",
        "status": tutor_response.get("status", "unknown"),
        "skill_tag": selected.get("skill_tag", ""),
        "source_anchor_count": len(tutor_response.get("source_anchors", []) or []),
        "effective_help_level": tutor_response.get("effective_help_level", "A2"),
        "raw_query_returned": False,
    }


def ledger_step_summary(ledger_append: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": "help_ledger_append",
        "status": ledger_append.get("status", "unknown"),
        "ledger_written": bool(ledger_append.get("ledger_written", False)),
        "event_hash": ledger_append.get("event_hash", ""),
        "path_returned": False,
    }


def synthetic_private_tutor_flow_workspace_card() -> dict[str, Any]:
    preview_hash = "__LEDGER_EVENT_HASH__"
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic private tutor Help-Ledger prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_private_tutor_help_ledger_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_help_ledger_receipt_before_any_local_write",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": sha256_text("synthetic private tutor flow workspace card"),
            "checkpoint_hash": preview_hash,
            "source_card_ids": ["dfg-gwp", "uoc-ki-faq"],
            "source_anchor_count": 2,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_local_cycle_workspace_card(workspace_card: dict[str, Any], *, ledger_event_hash: str = "") -> dict[str, Any]:
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
    help_ledger_preview_hash = str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", "")))
    if ledger_event_hash and checkpoint_hash == "__LEDGER_EVENT_HASH__":
        checkpoint_hash = ledger_event_hash
    if ledger_event_hash and help_ledger_preview_hash == "__LEDGER_EVENT_HASH__":
        help_ledger_preview_hash = ledger_event_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_help_ledger_receipt"))
        ),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", review.get("next_safe_action", ""))),
        "next_safe_user_action": str(summary.get("next_safe_user_action", review.get("next_safe_user_action", ""))),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", handoff.get("operator_run_endpoint", ""))),
        "operator_run_method": str(summary.get("operator_run_method", handoff.get("operator_run_method", "POST"))),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": str(summary.get("task_hash", "")),
        "checkpoint_hash": checkpoint_hash,
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": help_ledger_preview_hash,
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }


def study_receipt_step_summary(receipt_validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": "study_receipt_validation",
        "status": receipt_validation.get("status", "unknown"),
        "skill_tag": receipt_validation.get("skill_tag", ""),
        "help_level": receipt_validation.get("help_level", "A0"),
        "repeat_task_required": bool(receipt_validation.get("repeat_task_required", False)),
        "raw_text_stored": False,
    }


def private_tutor_use_flow_next_actions(
    *,
    manifest_apply: dict[str, Any],
    tutor_index: dict[str, Any],
    tutor_response: dict[str, Any],
    ledger_append: dict[str, Any],
    receipt_validation: dict[str, Any],
) -> list[str]:
    if manifest_apply.get("status") == "blocked_until_valid_rights_privacy_decision":
        return ["Record or reference a valid local rights/privacy decision before applying private manifest metadata."]
    if tutor_index.get("status") in {"waiting_for_private_manifest_apply", "waiting_for_tutor_usable_manifest_records"}:
        return ["Apply reviewed private manifest metadata, then build the hash-only tutor index."]
    if tutor_response.get("status") != "allowed":
        return ["Use an A0-A2 request with an indexed source anchor; do not ask for code, inserted values, or final interpretation."]
    if receipt_validation.get("status") == "blocked":
        return ["Provide hash-only study evidence: prediction, notebook action, source anchor, and reflection."]
    if not ledger_append.get("ledger_written"):
        return ["Review the dry-run, then set operator_confirmed_help_ledger_append only if this help should be stored locally."]
    return [
        "Use the validated receipt as a human-reviewable learning evidence checkpoint.",
        "Keep expanding course coverage through manifest apply and tutor-index rebuilds.",
        "Reminder: real exam authority clearance remains a real-world follow-up; UniBot stays not_cleared.",
    ]


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "private-tutor-use-flow")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]


def synthetic_private_tutor_flow_decision_record() -> dict[str, Any]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic private tutor use flow release alignment decision",
    }


def synthetic_private_tutor_flow_reviewed_receipt(
    job: dict[str, Any],
    *,
    decision_reference_hash: str,
) -> dict[str, Any]:
    return {
        "job_id": job.get("job_id", "synthetic-private-tutor-flow-job"),
        "material_id": job.get("material_id", "synthetic-private-tutor-flow-material"),
        "job_type": job.get("job_type", "ocr"),
        "extraction_status": "extracted_private",
        "raw_text_sha256": "c" * 64,
        "extracted_text_char_count": 1200,
        "private_artifact_reference": "synthetic local private tutor flow artifact reference",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": decision_reference_hash,
    }
