from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .adaptive_tasks import generate_adaptive_practice_plan
from .autonomous_research_loop import build_autonomous_research_loop
from .bachelor_thesis import build_bachelor_thesis_package
from .compliance import build_compliance_matrix
from .demo import build_local_demo_run
from .decision_request import build_stakeholder_decision_request
from .decision_journal import build_decision_journal_release_claim_alignment
from .decision_state import build_external_decision_state_release_claim_alignment
from .evaluation import build_evaluation_packet
from .course_exam_coverage_dashboard import (
    build_course_exam_coverage_dashboard_workspace_card_alignment,
    synthetic_course_exam_coverage_dashboard_inputs,
)
from .material_coverage_run import (
    build_material_coverage_run_workspace_card_alignment,
    synthetic_material_coverage_run_inputs,
)
from .course_per_skill_action_router import (
    build_course_per_skill_action_router_workspace_card_alignment,
    synthetic_course_per_skill_action_router_inputs,
)
from .external_decision_journal import build_external_decision_record_journal_release_claim_alignment
from .exam_packet_timeline import (
    build_exam_packet_timeline_workspace_card_alignment,
    synthetic_exam_packet_timeline_inputs,
)
from .exam_run_packet_builder import (
    build_exam_run_packet_workspace_card_alignment,
    synthetic_exam_run_packet_inputs,
)
from .routed_action_executor import (
    build_routed_action_executor_workspace_card_alignment,
    synthetic_routed_action_executor_inputs,
)
from .exam_notebook_checkpoint import (
    build_notebook_checkpoint_release_claim_alignment,
    build_notebook_checkpoint_workspace_card_receipt_alignment,
)
from .exam_workspace_launch_flow import (
    build_exam_workspace_launch_release_claim_alignment,
    build_exam_workspace_launch_workspace_card_receipt_alignment,
)
from .exam_workspace_operator_run import build_exam_workspace_operator_run_release_claim_alignment
from .exam_workspace_run import (
    build_exam_workspace_run_release_claim_alignment,
    build_exam_workspace_run_workspace_card_receipt_alignment,
)
from .exam_workspace_run_history import (
    build_exam_workspace_run_history_release_claim_alignment,
    build_exam_workspace_run_history_workspace_card_receipt_alignment,
)
from .exam_workspace_session_console import build_exam_workspace_session_console_release_claim_alignment
from .extraction_completion import build_extraction_completion_release_claim_alignment
from .extraction_human_review import build_extraction_human_review_release_claim_alignment
from .extraction_manifest_apply import build_private_manifest_apply_release_claim_alignment
from .extraction_manifest_update import build_extraction_manifest_update_release_claim_alignment
from .extraction_progress import build_extraction_progress_release_claim_alignment
from .extraction_receipt_journal import build_extraction_receipt_journal_release_claim_alignment
from .feedback import demo_feedback_template, export_public_demo_feedback_summary, validate_demo_feedback
from .github_issues import build_github_issue_bundle
from .gretel_glm_evolve import (
    build_glm_evolve_work_packet,
    build_glm_provider_redaction_alignment,
    build_glm_rsi_workboard,
)
from .handoff import build_authority_handoff_packet
from .materials import build_demo_material_manifest, build_public_material_summary
from .notebooks import generate_practice_notebook
from .orchestration import build_unibot_command_center, validate_chat_handoff
from .paperclip_evaluation_bridge import (
    build_paperclip_evaluation_request,
    build_paperclip_workspace_card_control_alignment,
    paperclip_status,
)
from .pilot import build_pilot_protocol
from .privacy import build_data_protection_screening
from .private_tutor_use_flow import (
    build_private_tutor_use_flow_release_claim_alignment,
    build_private_tutor_use_flow_workspace_card_alignment,
    synthetic_private_tutor_use_flow_inputs,
)
from .python_exam_local_cycle_operator_workspace_card import (
    build_python_exam_local_cycle_operator_workspace_card_release_claim_alignment,
)
from .python_exam_local_cycle_readiness_handoff import (
    build_python_exam_local_cycle_readiness_handoff_release_claim_alignment,
)
from .python_exam_local_cycle_readiness_review import (
    build_python_exam_local_cycle_readiness_review_release_claim_alignment,
)
from .python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet_release_claim_alignment
from .publication import build_publication_package
from .public_safety import scan_public_files, scan_text
from .redteam import build_threat_model_release_review_board_claim_alignment, run_redteam_smoke
from .release_runbook import build_release_runbook
from .review_chain_integrity import build_review_chain_integrity_check, synthetic_review_chain_inputs
from .source_cards import (
    build_source_card_drift_report,
    build_source_card_release_review_board_claim_alignment,
    list_source_cards,
)
from .submission import build_stakeholder_submission_bundle
from .study_session import (
    build_study_session_release_claim_alignment,
    build_study_session_workspace_card_alignment,
    synthetic_study_session_inputs,
)
from .timeline_export_receipt_journal import (
    build_timeline_export_receipt_journal_workspace_card_alignment,
    synthetic_timeline_export_receipt_journal_inputs,
)
from .timeline_export_review_packet import (
    build_timeline_export_review_packet_workspace_card_alignment,
    synthetic_timeline_export_review_packet_inputs,
)
from .triage import build_feedback_triage
from .review_board import build_review_board_packet


READINESS_SCHEMA_VERSION = "unibot-readiness-check-v1"
ROOT = Path(__file__).resolve().parents[1]


def default_public_paths(include_tests: bool = True) -> list[Path]:
    paths = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        ROOT / "CODE_OF_CONDUCT.md",
        ROOT / "LICENSE",
        ROOT / "pyproject.toml",
        *sorted((ROOT / "docs" / "unibot").glob("*.md")),
        *sorted((ROOT / "unibot").glob("*.py")),
        *sorted(path for path in (ROOT / "unibot" / "browser_extension").glob("*") if path.is_file()),
    ]
    if include_tests:
        paths.extend(sorted((ROOT / "tests").glob("test_unibot_*.py")))
    return paths


def build_readiness_runtime_guard(public_file_count: int | None = None) -> dict[str, Any]:
    guard = {
        "schema_version": "unibot-readiness-runtime-guard-v1",
        "status": "budget_guard_ready",
        "purpose": (
            "Keep recurring Gretel readiness runs focused, public-safe, and low-budget; "
            "broader suites remain explicit escalation work."
        ),
        "routine_budget": {
            "default_execution_mode": "focused_readiness",
            "default_reasoning_effort": "low",
            "max_active_work_items_per_run": 1,
            "full_suite_required_by_default": False,
            "provider_calls_allowed_by_default": False,
            "external_actions_allowed_by_default": False,
        },
        "routine_commands": [
            "python3 -m pytest tests/test_unibot_readiness.py -q",
            "python3 -m pytest tests/test_unibot_autonomous_research_loop.py -q",
            "python3 scripts/unibot_pipeline_smoke.py --json",
        ],
        "expensive_or_escalated_by_default": [
            "full pytest suite",
            "browser/e2e automation",
            "provider-backed GLM/Z.AI/OpenAI calls",
            "large generated artifact rebuilds",
            "public push or release",
        ],
        "escalate_only_when": [
            "a focused gate fails and a bounded local fix is identified",
            "an API, publication, release, or university-submission contract changes",
            "a human explicitly requests a broader verification run",
        ],
        "current_public_file_scan_count": public_file_count,
    }
    scan = scan_text(json.dumps(guard, ensure_ascii=False), "unibot-readiness-runtime-guard")
    guard["public_safety_status"] = scan["status"]
    return guard


def build_autonomous_loop_docs_traceability(
    autonomous_research_loop: dict[str, Any],
    autonomous_loop_doc_text: str,
    readiness_doc_text: str,
) -> dict[str, Any]:
    promotion_blocker_phrase = (
        "candidate lanes are not runnable work; promotion requires a new closed-harnessed "
        "receipt or an explicit ready item with bounded scope and tests"
    )
    autonomous_loop_doc_lower = " ".join(autonomous_loop_doc_text.lower().split())
    readiness_doc_lower = " ".join(readiness_doc_text.lower().split())
    traceability = {
        "schema_version": "unibot-autonomous-loop-docs-traceability-v1",
        "status": "ready",
        "current_candidate_documented": autonomous_research_loop["next_recommended_work_id"]
        in autonomous_loop_doc_text,
        "previous_closure_documented": (
            autonomous_research_loop["candidate_rotation_receipt"]["previous_closed_work_id"]
            in autonomous_loop_doc_text
            and autonomous_research_loop["candidate_rotation_receipt"]["previous_closed_commit"]
            in autonomous_loop_doc_text
        ),
        "readiness_gate_match_rule_documented": "review gate matching the current candidate receipt"
        in readiness_doc_text,
        "promotion_blocker_documented": promotion_blocker_phrase in autonomous_loop_doc_lower
        and promotion_blocker_phrase in readiness_doc_lower,
        "raw_private_context_returned": False,
    }
    traceability["failed_contract_ids"] = sorted(
        contract_id
        for contract_id, passed in {
            "current_candidate_documented": traceability["current_candidate_documented"],
            "previous_closure_documented": traceability["previous_closure_documented"],
            "readiness_gate_match_rule_documented": traceability["readiness_gate_match_rule_documented"],
            "promotion_blocker_documented": traceability["promotion_blocker_documented"],
            "raw_private_context_not_returned": not traceability["raw_private_context_returned"],
        }.items()
        if not passed
    )
    scan = scan_text(
        json.dumps(traceability, ensure_ascii=False),
        "unibot-gretel-autonomous-loop-docs-traceability-readiness",
    )
    traceability["public_safety_status"] = scan["status"]
    if traceability["public_safety_status"] != "pass" or traceability["failed_contract_ids"]:
        traceability["status"] = "blocked"
    return traceability


def build_readiness_evidence_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    checks = list(report["checks"])
    by_id = {check["check_id"]: check for check in checks}
    scientific_gate_ids = [
        "public_safety",
        "readiness_runtime_guard",
        "source_card_drift_guard",
        "evaluation_packet",
        "redteam",
        "publication_package",
        "review_board_packet",
        "stakeholder_submission_bundle",
        "stakeholder_decision_request",
        "stakeholder_decision_journal",
        "external_decision_record_journal",
        "external_decision_state",
        "extraction_receipt_journal",
        "extraction_progress",
        "extraction_manifest_update",
        "extraction_manifest_apply",
        "extraction_completion",
        "extraction_human_review",
        "private_tutor_use_flow",
        "study_session",
        "notebook_checkpoint",
        "exam_workspace_launch",
        "exam_workspace_run",
        "exam_workspace_run_history",
        "exam_workspace_operator_run",
        "exam_workspace_session_console",
        "python_exam_local_cycle_start_packet",
        "python_exam_local_cycle_readiness_review",
        "python_exam_local_cycle_readiness_handoff",
        "python_exam_local_cycle_operator_workspace_card",
        "material_coverage_run",
        "gretel_glm_evolve_lane",
        "gretel_bachelor_thesis_package",
        "gretel_autonomous_research_loop",
        "exam_boundary",
    ]
    gate_rows = [
        {
            "check_id": check_id,
            "passed": bool(by_id[check_id]["passed"]),
            "evidence_key_count": len(by_id[check_id]["evidence"]),
        }
        for check_id in scientific_gate_ids
        if check_id in by_id
    ]
    workspace_card_check = by_id.get("python_exam_local_cycle_operator_workspace_card", {})
    workspace_card_evidence = (
        workspace_card_check.get("evidence", {}) if isinstance(workspace_card_check.get("evidence"), dict) else {}
    )
    status_payload = {
        "readiness_status": report["status"],
        "exam_deployment_status": report["exam_deployment_status"],
        "check_count": report["check_count"],
        "passed_count": report["passed_count"],
        "failed_count": report["failed_count"],
        "failed_check_ids": sorted(check["check_id"] for check in checks if not check["passed"]),
        "scientific_gate_ids": [row["check_id"] for row in gate_rows],
        "scientific_gate_passed_count": len([row for row in gate_rows if row["passed"]]),
        "source_card_drift_status": report["source_card_drift"]["status"],
        "source_card_count": report["source_card_drift"]["card_count"],
        "runtime_guard_status": report["runtime_guard"]["status"],
        "runtime_default_mode": report["runtime_guard"]["routine_budget"]["default_execution_mode"],
    }
    digest = hashlib.sha256(json.dumps(status_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    scientific_gate_hash = hashlib.sha256(
        json.dumps(gate_rows, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    alignment_contracts = {
        "snapshot_ready": report["status"] == "public_draft_ready" and report["failed_count"] == 0,
        "scientific_gate_hash_present": scientific_gate_hash != "",
        "workspace_card_readiness_gate_linked": bool(workspace_card_check.get("passed"))
        and workspace_card_evidence.get("ready_card_status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card_evidence.get("ready_for_operator_prefill") is True
        and workspace_card_evidence.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card_evidence.get("help_ledger_preview_hash_present") is True
        and workspace_card_evidence.get("operator_prefill_hash_present") is True,
        "workspace_card_hash_metadata_preserved": workspace_card_evidence.get("task_hash_present") is True
        and workspace_card_evidence.get("checkpoint_hash_present") is True,
        "workspace_card_public_metadata_only": workspace_card_evidence.get("workspace_card_ready_metadata_only") is True
        and workspace_card_evidence.get("public_outputs_hide_private_workspace_card_data") is True,
        "high_stakes_boundaries_blocked": workspace_card_evidence.get("exam_deployment_status") == "not_cleared"
        and workspace_card_evidence.get("automatic_grading_blocked") is True
        and workspace_card_evidence.get("proctoring_blocked") is True
        and workspace_card_evidence.get("ki_detection_evidence_blocked") is True
        and workspace_card_evidence.get("exam_clearance_blocked") is True,
    }
    alignment_failed_contract_ids = [
        contract_id for contract_id, passed in alignment_contracts.items() if passed is not True
    ]
    workspace_card_snapshot_alignment = {
        "schema_version": "unibot-readiness-evidence-snapshot-workspace-card-link-v1",
        "status": "ready" if alignment_failed_contract_ids == [] else "blocked",
        "snapshot_hash": digest,
        "scientific_gate_hash": scientific_gate_hash,
        "workspace_card_check_id": "python_exam_local_cycle_operator_workspace_card",
        "workspace_card_status": workspace_card_evidence.get("ready_card_status", "missing"),
        "workspace_card_selected_skill_tag": workspace_card_evidence.get("selected_skill_tag", ""),
        "workspace_card_ready_for_operator_prefill": workspace_card_evidence.get("ready_for_operator_prefill") is True,
        "workspace_card_help_ledger_status": workspace_card_evidence.get("help_ledger_preview_status", "missing"),
        "workspace_card_help_ledger_hash_present": workspace_card_evidence.get("help_ledger_preview_hash_present")
        is True,
        "workspace_card_operator_prefill_hash_present": workspace_card_evidence.get("operator_prefill_hash_present")
        is True,
        "raw_workspace_card_returned": False,
        "contracts": alignment_contracts,
        "failed_contract_ids": alignment_failed_contract_ids,
        "blocked_claims": [
            "raw private course text publication",
            "contact data publication",
            "local path publication",
            "provider call",
            "autonomous publication",
            "approval claim",
            "exam clearance",
            "grading",
            "proctoring",
            "KI-detection evidence",
            "exam deployment",
        ],
    }
    snapshot = {
        "schema_version": "unibot-readiness-evidence-snapshot-v1",
        "status": (
            "ready"
            if report["status"] == "public_draft_ready"
            and report["failed_count"] == 0
            and workspace_card_snapshot_alignment["status"] == "ready"
            else "blocked"
        ),
        "snapshot_hash": digest,
        "scientific_gate_hash": scientific_gate_hash,
        "readiness_status": report["status"],
        "exam_deployment_status": report["exam_deployment_status"],
        "check_count": report["check_count"],
        "passed_count": report["passed_count"],
        "failed_count": report["failed_count"],
        "failed_check_ids": status_payload["failed_check_ids"],
        "scientific_gate_count": len(gate_rows),
        "scientific_gate_passed_count": status_payload["scientific_gate_passed_count"],
        "scientific_gates": gate_rows,
        "source_card_drift_status": report["source_card_drift"]["status"],
        "source_card_count": report["source_card_drift"]["card_count"],
        "required_source_card_count": report["source_card_drift"]["required_source_card_count"],
        "runtime_guard_status": report["runtime_guard"]["status"],
        "runtime_default_mode": report["runtime_guard"]["routine_budget"]["default_execution_mode"],
        "workspace_card_snapshot_alignment": workspace_card_snapshot_alignment,
        "human_gate_reminder": "Public draft readiness is not exam clearance, legal approval, provider approval, or real submission approval.",
    }
    scan = scan_text(json.dumps(snapshot, ensure_ascii=False), "unibot-readiness-evidence-snapshot")
    snapshot["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        snapshot["status"] = "blocked"
    return snapshot


def run_readiness_check(paths: Iterable[str | Path] | None = None) -> dict[str, Any]:
    public_paths = list(paths) if paths is not None else default_public_paths()
    public_scan = scan_public_files(public_paths)
    runtime_guard = build_readiness_runtime_guard(public_file_count=len(public_paths))
    redteam = run_redteam_smoke()
    threat_model_text = (ROOT / "docs" / "unibot" / "UNIBOT_THREAT_MODEL.md").read_text(encoding="utf-8")
    threat_model_alignment = build_threat_model_release_review_board_claim_alignment(threat_model_text)
    publication = build_publication_package()
    publication_scan = scan_text(json.dumps(publication, ensure_ascii=False), "unibot-publication-package")
    evaluation = build_evaluation_packet()
    evaluation_learner_agency_alignment = evaluation["learner_agency_boundary_alignment"]
    handoff = build_authority_handoff_packet()
    stakeholder_submission = build_stakeholder_submission_bundle()
    stakeholder_decision_request = build_stakeholder_decision_request()
    stakeholder_decision_journal_alignment = build_decision_journal_release_claim_alignment()
    external_decision_record_journal_alignment = build_external_decision_record_journal_release_claim_alignment()
    external_decision_state_alignment = build_external_decision_state_release_claim_alignment()
    extraction_receipt_journal_alignment = build_extraction_receipt_journal_release_claim_alignment()
    extraction_progress_alignment = build_extraction_progress_release_claim_alignment()
    extraction_manifest_update_alignment = build_extraction_manifest_update_release_claim_alignment()
    extraction_manifest_apply_alignment = build_private_manifest_apply_release_claim_alignment()
    extraction_completion_alignment = build_extraction_completion_release_claim_alignment()
    extraction_human_review_alignment = build_extraction_human_review_release_claim_alignment()
    private_tutor_use_flow_alignment = build_private_tutor_use_flow_release_claim_alignment()
    private_tutor_use_flow_inputs = synthetic_private_tutor_use_flow_inputs()
    private_tutor_use_flow_workspace_alignment = build_private_tutor_use_flow_workspace_card_alignment(
        private_tutor_use_flow_inputs["private_tutor_use_flow"],
    )
    study_session_alignment = build_study_session_release_claim_alignment()
    study_session_inputs = synthetic_study_session_inputs()
    study_session_workspace_alignment = build_study_session_workspace_card_alignment(
        study_session_inputs["study_session_review_report"],
    )
    notebook_checkpoint_alignment = build_notebook_checkpoint_release_claim_alignment()
    notebook_checkpoint_workspace_alignment = build_notebook_checkpoint_workspace_card_receipt_alignment()
    exam_workspace_launch_alignment = build_exam_workspace_launch_release_claim_alignment()
    exam_workspace_launch_workspace_alignment = build_exam_workspace_launch_workspace_card_receipt_alignment()
    exam_workspace_run_alignment = build_exam_workspace_run_release_claim_alignment()
    exam_workspace_run_workspace_alignment = build_exam_workspace_run_workspace_card_receipt_alignment()
    exam_workspace_run_history_alignment = build_exam_workspace_run_history_release_claim_alignment()
    exam_workspace_run_history_workspace_alignment = (
        build_exam_workspace_run_history_workspace_card_receipt_alignment()
    )
    exam_workspace_operator_run_alignment = build_exam_workspace_operator_run_release_claim_alignment()
    exam_workspace_session_console_alignment = build_exam_workspace_session_console_release_claim_alignment()
    python_exam_local_cycle_start_packet_alignment = build_python_exam_local_cycle_start_packet_release_claim_alignment()
    python_exam_local_cycle_readiness_review_alignment = (
        build_python_exam_local_cycle_readiness_review_release_claim_alignment()
    )
    python_exam_local_cycle_readiness_handoff_alignment = (
        build_python_exam_local_cycle_readiness_handoff_release_claim_alignment()
    )
    python_exam_local_cycle_operator_workspace_card_alignment = (
        build_python_exam_local_cycle_operator_workspace_card_release_claim_alignment()
    )
    notebook = generate_practice_notebook("UniBot readiness notebook smoke")
    source_cards = list_source_cards()
    source_card_drift = build_source_card_drift_report()
    source_card_claim_alignment = build_source_card_release_review_board_claim_alignment(source_card_drift)
    material_manifest = build_demo_material_manifest()
    material_summary = build_public_material_summary(material_manifest["records"])
    material_summary_scan = scan_text(json.dumps(material_summary, ensure_ascii=False), "unibot-material-summary")
    material_public_boundary_alignment = material_manifest["material_public_boundary_alignment"]
    adaptive_plan = generate_adaptive_practice_plan(
        skill_state={"python_lists": {"signals": 3, "high_help_events": 1}},
        material_records=material_manifest["records"],
        max_tasks=3,
        public_safe=True,
    )
    adaptive_source_boundary_alignment = adaptive_plan["source_boundary_alignment"]
    demo_run = build_local_demo_run()
    feedback_template = demo_feedback_template()
    browser_sidepanel_text = (ROOT / "unibot" / "browser_extension" / "sidepanel.js").read_text(encoding="utf-8")
    browser_manifest = json.loads((ROOT / "unibot" / "browser_extension" / "manifest.json").read_text(encoding="utf-8"))
    browser_content_text = (ROOT / "unibot" / "browser_extension" / "content.js").read_text(encoding="utf-8")
    feedback_template_scan = scan_text(json.dumps(feedback_template, ensure_ascii=False), "unibot-feedback-template")
    demo_feedback_validation = validate_demo_feedback(
        {
            "scenario_id": "demo_prompt_card",
            "outcome": "fail",
            "severity": "minor",
            "what_i_tried": "Clicked prompt card after entering a synthetic Python-list task.",
            "expected": "Clipboard contains a Socratic prompt.",
            "what_happened": "Clipboard stayed empty.",
            "button_or_endpoint": "Promptkarte erzeugen",
            "public_safe_text": "No private data included.",
            "private_data_removed": True,
        }
    )
    feedback_summary_scan = scan_text(
        json.dumps(export_public_demo_feedback_summary(), ensure_ascii=False),
        "unibot-feedback-public-summary",
    )
    feedback_triage = build_feedback_triage(
        records=[
            {
                "feedback_id": "demo-feedback-1",
                "scenario_id": "demo_prompt_card",
                "outcome": "fail",
                "severity": "minor",
                "button_or_endpoint": "Promptkarte erzeugen",
                "private_data_removed": True,
                "has_public_safe_text": False,
                "has_follow_up_note": False,
            }
        ]
    )
    github_issue_bundle = build_github_issue_bundle(
        records=[
            {
                "feedback_id": "demo-feedback-1",
                "scenario_id": "demo_prompt_card",
                "outcome": "fail",
                "severity": "minor",
                "button_or_endpoint": "Promptkarte erzeugen",
                "private_data_removed": True,
                "has_public_safe_text": False,
                "has_follow_up_note": False,
            }
        ]
    )
    release_runbook = build_release_runbook()
    compliance_matrix = build_compliance_matrix()
    pilot_protocol = build_pilot_protocol()
    data_protection = build_data_protection_screening()
    review_board_packet = build_review_board_packet()
    glm_evolve_packet = build_glm_evolve_work_packet()
    glm_rsi_workboard = build_glm_rsi_workboard()
    glm_provider_redaction_alignment = build_glm_provider_redaction_alignment(glm_evolve_packet, glm_rsi_workboard)
    glm_rsi_workboard_scan = scan_text(json.dumps(glm_rsi_workboard, ensure_ascii=False), "unibot-glm-rsi-workboard-readiness")
    bachelor_thesis_package = build_bachelor_thesis_package()
    bachelor_thesis_scan = scan_text(
        json.dumps(bachelor_thesis_package, ensure_ascii=False),
        "unibot-gretel-bachelor-thesis-readiness",
    )
    autonomous_research_loop = build_autonomous_research_loop()
    autonomous_research_loop_scan = scan_text(
        json.dumps(autonomous_research_loop, ensure_ascii=False),
        "unibot-gretel-autonomous-research-loop-readiness",
    )
    autonomous_loop_doc_text = (
        ROOT / "docs" / "unibot" / "UNIBOT_GRETEL_AUTONOMOUS_RESEARCH_LOOP.md"
    ).read_text(encoding="utf-8")
    readiness_doc_text = (ROOT / "docs" / "unibot" / "UNIBOT_READINESS_CHECK.md").read_text(encoding="utf-8")
    autonomous_loop_docs_traceability = build_autonomous_loop_docs_traceability(
        autonomous_research_loop,
        autonomous_loop_doc_text,
        readiness_doc_text,
    )
    autonomous_candidate_review_hash = hashlib.sha256(
        json.dumps(
            autonomous_research_loop["candidate_review"],
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    autonomous_candidate_rotation_hash = autonomous_research_loop["candidate_rotation_receipt"]["rotation_hash"]
    autonomous_single_candidate_continuity_hash = autonomous_research_loop["single_candidate_continuity_receipt"][
        "continuity_hash"
    ]
    autonomous_docs_traceability_negative_evidence_receipt = (
        autonomous_research_loop.get("docs_traceability_negative_evidence_receipt", {})
        if isinstance(autonomous_research_loop.get("docs_traceability_negative_evidence_receipt"), dict)
        else {}
    )
    paperclip_status_payload = paperclip_status()
    paperclip_bridge = build_paperclip_evaluation_request()
    paperclip_workspace_card_alignment = build_paperclip_workspace_card_control_alignment(
        paperclip_bridge,
        paperclip_status_payload,
    )
    paperclip_bridge_scan = scan_text(json.dumps(paperclip_bridge, ensure_ascii=False), "unibot-paperclip-evaluation-readiness")
    command_center = build_unibot_command_center()
    command_center_scan = scan_text(json.dumps(command_center, ensure_ascii=False), "unibot-command-center-readiness")
    review_chain_inputs = synthetic_review_chain_inputs()
    review_chain_integrity = build_review_chain_integrity_check(
        exam_run_packet=review_chain_inputs["packet"],
        exam_packet_timeline=review_chain_inputs["timeline"],
        timeline_export_review_packet=review_chain_inputs["review"],
        timeline_export_receipt_journal_append=review_chain_inputs["journal_append"],
        timeline_export_receipt_journal_summary=review_chain_inputs["journal_summary"],
        selected_skill_tag="python_lists",
    )
    review_chain_integrity_scan = scan_text(
        json.dumps(review_chain_integrity, ensure_ascii=False),
        "unibot-review-chain-integrity-readiness",
    )
    timeline_receipt_journal_inputs = synthetic_timeline_export_receipt_journal_inputs()
    timeline_receipt_journal_alignment = build_timeline_export_receipt_journal_workspace_card_alignment(
        timeline_export_receipt_journal_append=timeline_receipt_journal_inputs["append"],
        timeline_export_receipt_journal_summary=timeline_receipt_journal_inputs["summary"],
    )
    timeline_review_packet_inputs = synthetic_timeline_export_review_packet_inputs()
    timeline_review_packet_alignment = build_timeline_export_review_packet_workspace_card_alignment(
        timeline_review_packet_inputs["review_packet"],
    )
    material_coverage_run_inputs = synthetic_material_coverage_run_inputs()
    material_coverage_run_alignment = build_material_coverage_run_workspace_card_alignment(
        material_coverage_run_inputs["material_coverage_run"],
    )
    course_exam_coverage_dashboard_inputs = synthetic_course_exam_coverage_dashboard_inputs()
    course_exam_coverage_dashboard_alignment = build_course_exam_coverage_dashboard_workspace_card_alignment(
        course_exam_coverage_dashboard_inputs["course_exam_coverage_dashboard"],
    )
    course_per_skill_action_router_inputs = synthetic_course_per_skill_action_router_inputs()
    course_per_skill_action_router_alignment = build_course_per_skill_action_router_workspace_card_alignment(
        course_per_skill_action_router_inputs["course_per_skill_action_router"],
    )
    routed_action_executor_inputs = synthetic_routed_action_executor_inputs()
    routed_action_executor_alignment = build_routed_action_executor_workspace_card_alignment(
        routed_action_executor_inputs["routed_action_executor"],
    )
    exam_run_packet_inputs = synthetic_exam_run_packet_inputs()
    exam_run_packet_alignment = build_exam_run_packet_workspace_card_alignment(
        exam_run_packet_inputs["exam_run_packet"],
    )
    exam_packet_timeline_inputs = synthetic_exam_packet_timeline_inputs()
    exam_packet_timeline_alignment = build_exam_packet_timeline_workspace_card_alignment(
        exam_packet_timeline_inputs["timeline"],
    )
    handoff_validation = validate_chat_handoff(
        {
            "role_id": "qa_redteam",
            "goal": "Run the UniBot orchestration smoke and report public-safe status.",
            "changed_files": ["unibot/orchestration.py", "tests/test_unibot_orchestration.py"],
            "tests": ["python3 scripts/unibot_pipeline_smoke.py --json"],
            "risks": ["real exam use remains blocked until written authority clearance"],
            "evidence": ["pipeline smoke", "public-safety scan", "red-team smoke"],
            "next_step": "merge only after green smoke and public-safety 0 findings",
        }
    )

    checks = [
        {
            "check_id": "public_safety",
            "passed": public_scan["status"] == "pass",
            "evidence": {
                "status": public_scan["status"],
                "scanned_count": public_scan["scanned_count"],
                "finding_count": public_scan["finding_count"],
            },
        },
        {
            "check_id": "readiness_runtime_guard",
            "passed": runtime_guard["status"] == "budget_guard_ready"
            and runtime_guard["public_safety_status"] == "pass"
            and runtime_guard["routine_budget"]["default_execution_mode"] == "focused_readiness"
            and runtime_guard["routine_budget"]["default_reasoning_effort"] == "low"
            and runtime_guard["routine_budget"]["max_active_work_items_per_run"] == 1
            and runtime_guard["routine_budget"]["full_suite_required_by_default"] is False
            and runtime_guard["routine_budget"]["provider_calls_allowed_by_default"] is False
            and runtime_guard["routine_budget"]["external_actions_allowed_by_default"] is False,
            "evidence": {
                "status": runtime_guard["status"],
                "public_safety_status": runtime_guard["public_safety_status"],
                "default_execution_mode": runtime_guard["routine_budget"]["default_execution_mode"],
                "default_reasoning_effort": runtime_guard["routine_budget"]["default_reasoning_effort"],
                "full_suite_required_by_default": runtime_guard["routine_budget"]["full_suite_required_by_default"],
                "provider_calls_allowed_by_default": runtime_guard["routine_budget"]["provider_calls_allowed_by_default"],
                "current_public_file_scan_count": runtime_guard["current_public_file_scan_count"],
            },
        },
        {
            "check_id": "redteam",
            "passed": redteam["status"] == "pass"
            and redteam["failed_count"] == 0
            and redteam["claim_alignment"]["status"] == "ready"
            and redteam["claim_alignment"]["public_safety_status"] == "pass"
            and redteam["claim_alignment"]["hash_or_category_evidence_only"] is True
            and redteam["claim_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and redteam["claim_alignment"]["missing_release_review_board_claim_human_gates"] == []
            and threat_model_alignment["status"] == "ready"
            and threat_model_alignment["public_safety_status"] == "pass",
            "evidence": {
                "status": redteam["status"],
                "passed_count": redteam["passed_count"],
                "scenario_count": redteam["scenario_count"],
                "claim_alignment_status": redteam["claim_alignment"]["status"],
                "claim_alignment_public_safety_status": redteam["claim_alignment"]["public_safety_status"],
                "manual_publication_claim_contract_status": redteam["claim_alignment"][
                    "manual_publication_claim_contract"
                ]["expected_schema_version"],
                "threat_model_claim_alignment_status": threat_model_alignment["status"],
                "threat_model_claim_contract_status": threat_model_alignment["manual_publication_claim_contract"][
                    "expected_schema_version"
                ],
                "threat_model_missing_required_phrase_count": len(threat_model_alignment["missing_required_phrases"]),
                "hash_or_category_evidence_only": redteam["claim_alignment"]["hash_or_category_evidence_only"],
                "notebook_handoff_claim_linked": (
                    "notebook_template" in redteam["claim_alignment"]["unique_readiness_check_ids"]
                ),
                "browser_handoff_claim_linked": (
                    "browser_extension_demo_handoff" in redteam["claim_alignment"]["unique_readiness_check_ids"]
                ),
                "browser_manifest_boundary_linked": (
                    "browser_manifest_content_boundary" in redteam["claim_alignment"]["unique_readiness_check_ids"]
                ),
                "local_demo_claim_linked": "local_demo_run" in redteam["claim_alignment"]["unique_readiness_check_ids"],
                "publication_claim_linked": "publication_package" in redteam["claim_alignment"]["unique_readiness_check_ids"],
                "review_board_claim_linked": "review_board_packet" in redteam["claim_alignment"]["unique_readiness_check_ids"],
                "threat_model_source_cards_linked": "source_cards" in threat_model_alignment["unique_readiness_check_ids"],
                "threat_model_release_runbook_linked": "release_runbook" in threat_model_alignment["unique_readiness_check_ids"],
                "human_submission_gate_linked": (
                    "human_submission_review_required" in redteam["claim_alignment"]["required_human_gates"]
                    and "human_submission_review_required" in threat_model_alignment["required_human_gates"]
                ),
                "exam_clearance_blocked": "exam clearance" in redteam["claim_alignment"]["blocked_claims"]
                and "exam clearance" in threat_model_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "publication_package",
            "passed": publication["status"] == "public_draft_not_exam_release"
            and publication["release_gates"]["release_ready"] is True
            and publication_scan["status"] == "pass"
            and publication["publication_reproducibility_alignment"]["status"] == "ready"
            and publication["publication_reproducibility_alignment"]["public_safety_status"] == "pass"
            and publication["publication_reproducibility_alignment"]["missing_artifact_ids"] == []
            and publication["publication_reproducibility_alignment"]["missing_release_gate_ids"] == []
            and publication["publication_reproducibility_alignment"]["missing_policy_keys"] == []
            and publication["publication_reproducibility_alignment"]["missing_source_card_ids"] == []
            and publication["publication_reproducibility_alignment"]["failed_contract_ids"] == []
            and publication["publication_reproducibility_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and publication["publication_reproducibility_alignment"][
                "missing_release_review_board_claim_human_gates"
            ]
            == []
            and publication["publication_reproducibility_alignment"]["workspace_card_publication_gate_linked"] is True,
            "evidence": {
                "status": publication["status"],
                "release_ready": publication["release_gates"]["release_ready"],
                "release_ready_note": publication["release_gates"]["release_ready_note"],
                "public_safety_status": publication_scan["status"],
                "reproducibility_alignment_status": publication["publication_reproducibility_alignment"]["status"],
                "publication_release_review_board_claim_contract_status": publication[
                    "publication_reproducibility_alignment"
                ]["publication_release_review_board_claim_contract"]["expected_schema_version"],
                "reproducibility_alignment_section_count": publication["publication_reproducibility_alignment"]["section_count"],
                "workspace_card_status": publication["publication_reproducibility_alignment"]["workspace_card_status"],
                "workspace_card_selected_skill_tag": publication["publication_reproducibility_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": publication["publication_reproducibility_alignment"][
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": publication["publication_reproducibility_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": publication["publication_reproducibility_alignment"][
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": publication["publication_reproducibility_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_publication_gate_linked": publication["publication_reproducibility_alignment"][
                    "workspace_card_publication_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in publication["publication_reproducibility_alignment"]["required_readiness_check_ids"]
                ),
                "reproducibility_alignment_human_gates": publication["publication_reproducibility_alignment"]["required_human_gates"],
            },
        },
        {
            "check_id": "evaluation_packet",
            "passed": evaluation["status"] == "draft_not_ethics_or_authority_cleared"
            and len(evaluation["synthetic_tasks"]) >= 4
            and bool(evaluation["codebook"]["coding_rules"])
            and evaluation_learner_agency_alignment["status"] == "ready"
            and evaluation_learner_agency_alignment["public_safety_status"] == "pass"
            and evaluation_learner_agency_alignment["missing_source_card_ids"] == []
            and evaluation_learner_agency_alignment["failed_contract_ids"] == [],
            "evidence": {
                "status": evaluation["status"],
                "task_count": len(evaluation["synthetic_tasks"]),
                "coding_rule_count": len(evaluation["codebook"]["coding_rules"]),
                "learner_agency_alignment_status": evaluation_learner_agency_alignment["status"],
                "learner_agency_alignment_section_count": evaluation_learner_agency_alignment["section_count"],
                "learner_agency_alignment_human_gates": evaluation_learner_agency_alignment["required_human_gates"],
            },
        },
        {
            "check_id": "authority_handoff",
            "passed": handoff["status"] == "draft_not_officially_cleared"
            and handoff["evidence"]["redteam"]["status"] == "pass"
            and handoff["release_claim_alignment"]["status"] == "ready"
            and handoff["release_claim_alignment"]["public_safety_status"] == "pass"
            and handoff["release_claim_alignment"]["missing_source_card_ids"] == []
            and handoff["release_claim_alignment"]["failed_contract_ids"] == [],
            "evidence": {
                "status": handoff["status"],
                "redteam_status": handoff["evidence"]["redteam"]["status"],
                "reviewer_count": len(handoff["intended_reviewers"]),
                "release_claim_alignment_status": handoff["release_claim_alignment"]["status"],
                "release_claim_alignment_public_safety_status": handoff["release_claim_alignment"][
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": handoff["release_claim_alignment"]["schema_version"],
                "release_claim_alignment_section_count": handoff["release_claim_alignment"]["section_count"],
                "workspace_card_status": handoff["release_claim_alignment"]["workspace_card_status"],
                "workspace_card_selected_skill_tag": handoff["release_claim_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": handoff["release_claim_alignment"][
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": handoff["release_claim_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": handoff["release_claim_alignment"][
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": handoff["release_claim_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_authority_gate_linked": handoff["release_claim_alignment"][
                    "workspace_card_authority_gate_linked"
                ],
                "release_claim_alignment_human_gates": handoff["release_claim_alignment"]["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in handoff["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in handoff["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "source_card_drift_claim_linked": (
                    "source_card_drift_guard" in handoff["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "compliance_claim_linked": (
                    "compliance_matrix" in handoff["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "public_safety_claim_linked": (
                    "public_safety" in handoff["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in handoff["release_claim_alignment"]["required_human_gates"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in handoff["release_claim_alignment"]["required_human_gates"]
                ),
                "exam_clearance_blocked": "exam clearance" in handoff["release_claim_alignment"]["blocked_claims"],
                "workspace_card_authority_gate_contract": handoff["release_claim_alignment"]["contracts"][
                    "workspace_card_authority_gate_linked"
                ],
            },
        },
        {
            "check_id": "stakeholder_submission_bundle",
            "passed": stakeholder_submission["status"] == "ready_for_human_submission_not_sent"
            and stakeholder_submission["exam_deployment_status"] == "not_cleared"
            and stakeholder_submission["public_safety_status"] == "pass"
            and stakeholder_submission["release_claim_alignment"]["status"] == "ready"
            and stakeholder_submission["release_claim_alignment"]["public_safety_status"] == "pass"
            and stakeholder_submission["release_claim_alignment"]["missing_source_card_ids"] == []
            and stakeholder_submission["release_claim_alignment"]["failed_contract_ids"] == [],
            "evidence": {
                "status": stakeholder_submission["status"],
                "exam_deployment_status": stakeholder_submission["exam_deployment_status"],
                "public_safety_status": stakeholder_submission["public_safety_status"],
                "decision_lane_count": len(stakeholder_submission["decision_lanes"]),
                "open_external_gate_count": len(stakeholder_submission["open_external_gates"]),
                "release_claim_alignment_status": stakeholder_submission["release_claim_alignment"]["status"],
                "release_claim_alignment_public_safety_status": stakeholder_submission["release_claim_alignment"][
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": stakeholder_submission["release_claim_alignment"][
                    "schema_version"
                ],
                "release_claim_alignment_section_count": stakeholder_submission["release_claim_alignment"][
                    "section_count"
                ],
                "workspace_card_status": stakeholder_submission["release_claim_alignment"]["workspace_card_status"],
                "workspace_card_selected_skill_tag": stakeholder_submission["release_claim_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": stakeholder_submission["release_claim_alignment"][
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": stakeholder_submission["release_claim_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": stakeholder_submission["release_claim_alignment"][
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": stakeholder_submission["release_claim_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_submission_lane_gate_linked": stakeholder_submission["release_claim_alignment"][
                    "workspace_card_submission_lane_gate_linked"
                ],
                "release_claim_alignment_human_gates": stakeholder_submission["release_claim_alignment"][
                    "required_human_gates"
                ],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in stakeholder_submission["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet"
                    in stakeholder_submission["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "authority_handoff_claim_linked": (
                    "authority_handoff"
                    in stakeholder_submission["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening"
                    in stakeholder_submission["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "source_card_drift_claim_linked": (
                    "source_card_drift_guard"
                    in stakeholder_submission["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required"
                    in stakeholder_submission["release_claim_alignment"]["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in stakeholder_submission["release_claim_alignment"]["required_human_gates"]
                ),
                "exam_clearance_blocked": "exam clearance"
                in stakeholder_submission["release_claim_alignment"]["blocked_claims"],
                "automatic_submission_blocked": "automatic submission"
                in stakeholder_submission["release_claim_alignment"]["blocked_claims"],
                "workspace_card_submission_lane_gate_contract": stakeholder_submission["release_claim_alignment"][
                    "contracts"
                ]["workspace_card_submission_lane_gate_linked"],
            },
        },
        {
            "check_id": "stakeholder_decision_request",
            "passed": stakeholder_decision_request["status"] == "ready_for_manual_review_not_sent"
            and stakeholder_decision_request["exam_deployment_status"] == "not_cleared"
            and stakeholder_decision_request["public_safety_status"] == "pass"
            and stakeholder_decision_request["release_claim_alignment"]["status"] == "ready"
            and stakeholder_decision_request["release_claim_alignment"]["public_safety_status"] == "pass"
            and stakeholder_decision_request["release_claim_alignment"]["missing_source_card_ids"] == []
            and stakeholder_decision_request["release_claim_alignment"]["failed_contract_ids"] == [],
            "evidence": {
                "status": stakeholder_decision_request["status"],
                "lane_id": stakeholder_decision_request["lane_id"],
                "exam_deployment_status": stakeholder_decision_request["exam_deployment_status"],
                "public_safety_status": stakeholder_decision_request["public_safety_status"],
                "evidence_manifest_count": len(stakeholder_decision_request["evidence_manifest"]),
                "receipt_tool_sent_message": stakeholder_decision_request["receipt_template"]["tool_sent_message"],
                "receipt_raw_decision_text_included": stakeholder_decision_request["receipt_template"][
                    "raw_decision_text_included"
                ],
                "release_claim_alignment_status": stakeholder_decision_request["release_claim_alignment"]["status"],
                "release_claim_alignment_public_safety_status": stakeholder_decision_request[
                    "release_claim_alignment"
                ]["public_safety_status"],
                "release_claim_alignment_contract_status": stakeholder_decision_request["release_claim_alignment"][
                    "schema_version"
                ],
                "release_claim_alignment_section_count": stakeholder_decision_request["release_claim_alignment"][
                    "section_count"
                ],
                "workspace_card_status": stakeholder_decision_request["release_claim_alignment"][
                    "workspace_card_status"
                ],
                "workspace_card_selected_skill_tag": stakeholder_decision_request["release_claim_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": stakeholder_decision_request["release_claim_alignment"][
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": stakeholder_decision_request["release_claim_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": stakeholder_decision_request["release_claim_alignment"][
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": stakeholder_decision_request["release_claim_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_decision_request_gate_linked": stakeholder_decision_request["release_claim_alignment"][
                    "workspace_card_decision_request_gate_linked"
                ],
                "release_claim_alignment_human_gates": stakeholder_decision_request["release_claim_alignment"][
                    "required_human_gates"
                ],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in stakeholder_decision_request["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "submission_bundle_claim_linked": (
                    "stakeholder_submission_bundle"
                    in stakeholder_decision_request["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet"
                    in stakeholder_decision_request["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening"
                    in stakeholder_decision_request["release_claim_alignment"]["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required"
                    in stakeholder_decision_request["release_claim_alignment"]["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in stakeholder_decision_request["release_claim_alignment"]["required_human_gates"]
                ),
                "workspace_card_decision_request_gate_contract": stakeholder_decision_request["release_claim_alignment"][
                    "contracts"
                ]["workspace_card_decision_request_gate_linked"],
                "automatic_external_send_blocked": "automatic external send"
                in stakeholder_decision_request["release_claim_alignment"]["blocked_claims"],
                "raw_decision_storage_blocked": "raw written decision storage"
                in stakeholder_decision_request["release_claim_alignment"]["blocked_claims"],
                "exam_clearance_blocked": "exam clearance"
                in stakeholder_decision_request["release_claim_alignment"]["blocked_claims"],
            },
        },
        {
            "check_id": "stakeholder_decision_journal",
            "passed": stakeholder_decision_journal_alignment["status"] == "ready"
            and stakeholder_decision_journal_alignment["public_safety_status"] == "pass"
            and stakeholder_decision_journal_alignment["missing_source_card_ids"] == []
            and stakeholder_decision_journal_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": stakeholder_decision_journal_alignment["status"],
                "release_claim_alignment_public_safety_status": stakeholder_decision_journal_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": stakeholder_decision_journal_alignment["schema_version"],
                "release_claim_alignment_section_count": stakeholder_decision_journal_alignment["section_count"],
                "record_count": stakeholder_decision_journal_alignment["record_count"],
                "event_types": stakeholder_decision_journal_alignment["event_types"],
                "workspace_card_status": stakeholder_decision_journal_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": stakeholder_decision_journal_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": stakeholder_decision_journal_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": stakeholder_decision_journal_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": stakeholder_decision_journal_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": stakeholder_decision_journal_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_decision_journal_gate_linked": stakeholder_decision_journal_alignment[
                    "workspace_card_decision_journal_gate_linked"
                ],
                "release_claim_alignment_human_gates": stakeholder_decision_journal_alignment["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in stakeholder_decision_journal_alignment["required_readiness_check_ids"]
                ),
                "decision_request_claim_linked": (
                    "stakeholder_decision_request"
                    in stakeholder_decision_journal_alignment["required_readiness_check_ids"]
                ),
                "submission_bundle_claim_linked": (
                    "stakeholder_submission_bundle"
                    in stakeholder_decision_journal_alignment["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening"
                    in stakeholder_decision_journal_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in stakeholder_decision_journal_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required"
                    in stakeholder_decision_journal_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in stakeholder_decision_journal_alignment["required_human_gates"]
                ),
                "workspace_card_decision_journal_gate_contract": stakeholder_decision_journal_alignment["contracts"][
                    "workspace_card_decision_journal_gate_linked"
                ],
                "raw_decision_storage_blocked": "raw written decision storage"
                in stakeholder_decision_journal_alignment["blocked_claims"],
                "tool_sent_message_blocked": "tool-sent stakeholder message"
                in stakeholder_decision_journal_alignment["blocked_claims"],
                "automatic_gate_change_blocked": "automatic gate change"
                in stakeholder_decision_journal_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance" in stakeholder_decision_journal_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "external_decision_record_journal",
            "passed": external_decision_record_journal_alignment["status"] == "ready"
            and external_decision_record_journal_alignment["public_safety_status"] == "pass"
            and external_decision_record_journal_alignment["missing_source_card_ids"] == []
            and external_decision_record_journal_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": external_decision_record_journal_alignment["status"],
                "release_claim_alignment_public_safety_status": external_decision_record_journal_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": external_decision_record_journal_alignment["schema_version"],
                "release_claim_alignment_section_count": external_decision_record_journal_alignment["section_count"],
                "record_count": external_decision_record_journal_alignment["record_count"],
                "record_types": external_decision_record_journal_alignment["record_types"],
                "workspace_card_status": external_decision_record_journal_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": external_decision_record_journal_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": external_decision_record_journal_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": external_decision_record_journal_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": external_decision_record_journal_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": external_decision_record_journal_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_decision_record_gate_linked": external_decision_record_journal_alignment[
                    "workspace_card_decision_record_gate_linked"
                ],
                "release_claim_alignment_human_gates": external_decision_record_journal_alignment[
                    "required_human_gates"
                ],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in external_decision_record_journal_alignment["required_readiness_check_ids"]
                ),
                "decision_journal_claim_linked": (
                    "stakeholder_decision_journal"
                    in external_decision_record_journal_alignment["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening"
                    in external_decision_record_journal_alignment["required_readiness_check_ids"]
                ),
                "authority_handoff_claim_linked": (
                    "authority_handoff"
                    in external_decision_record_journal_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in external_decision_record_journal_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required"
                    in external_decision_record_journal_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in external_decision_record_journal_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in external_decision_record_journal_alignment["required_human_gates"]
                ),
                "workspace_card_decision_record_gate_contract": external_decision_record_journal_alignment["contracts"][
                    "workspace_card_decision_record_gate_linked"
                ],
                "raw_decision_storage_blocked": "raw written decision storage"
                in external_decision_record_journal_alignment["blocked_claims"],
                "deployment_switch_blocked": "deployment switch"
                in external_decision_record_journal_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in external_decision_record_journal_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "external_decision_state",
            "passed": external_decision_state_alignment["status"] == "ready"
            and external_decision_state_alignment["public_safety_status"] == "pass"
            and external_decision_state_alignment["missing_source_card_ids"] == []
            and external_decision_state_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": external_decision_state_alignment["status"],
                "release_claim_alignment_public_safety_status": external_decision_state_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": external_decision_state_alignment["schema_version"],
                "release_claim_alignment_section_count": external_decision_state_alignment["section_count"],
                "workspace_card_status": external_decision_state_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": external_decision_state_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": external_decision_state_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": external_decision_state_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": external_decision_state_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": external_decision_state_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_decision_gate_linked": external_decision_state_alignment[
                    "workspace_card_decision_gate_linked"
                ],
                "release_claim_alignment_human_gates": external_decision_state_alignment["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in external_decision_state_alignment["required_readiness_check_ids"]
                ),
                "decision_record_journal_claim_linked": (
                    "external_decision_record_journal"
                    in external_decision_state_alignment["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening" in external_decision_state_alignment["required_readiness_check_ids"]
                ),
                "authority_handoff_claim_linked": (
                    "authority_handoff" in external_decision_state_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in external_decision_state_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in external_decision_state_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in external_decision_state_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in external_decision_state_alignment["required_human_gates"]
                ),
                "workspace_card_decision_gate_contract": external_decision_state_alignment["contracts"][
                    "workspace_card_decision_gate_linked"
                ],
                "raw_decision_storage_blocked": "raw written decision storage"
                in external_decision_state_alignment["blocked_claims"],
                "silent_deployment_switch_blocked": "silent deployment switch"
                in external_decision_state_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in external_decision_state_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "extraction_receipt_journal",
            "passed": extraction_receipt_journal_alignment["status"] == "ready"
            and extraction_receipt_journal_alignment["public_safety_status"] == "pass"
            and extraction_receipt_journal_alignment["summary_public_safety_status"] == "pass"
            and extraction_receipt_journal_alignment["missing_source_card_ids"] == []
            and extraction_receipt_journal_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": extraction_receipt_journal_alignment["status"],
                "release_claim_alignment_public_safety_status": extraction_receipt_journal_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": extraction_receipt_journal_alignment["schema_version"],
                "release_claim_alignment_section_count": extraction_receipt_journal_alignment["section_count"],
                "record_count": extraction_receipt_journal_alignment["record_count"],
                "accepted_record_count": extraction_receipt_journal_alignment["accepted_record_count"],
                "ready_for_human_review_count": extraction_receipt_journal_alignment[
                    "ready_for_human_review_count"
                ],
                "eligible_for_private_tutor_index_count": extraction_receipt_journal_alignment[
                    "eligible_for_private_tutor_index_count"
                ],
                "progress_receipt_count": extraction_receipt_journal_alignment["progress_receipt_count"],
                "workspace_card_status": extraction_receipt_journal_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": extraction_receipt_journal_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": extraction_receipt_journal_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": extraction_receipt_journal_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": extraction_receipt_journal_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": extraction_receipt_journal_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_receipt_journal_gate_linked": extraction_receipt_journal_alignment[
                    "workspace_card_receipt_journal_gate_linked"
                ],
                "release_claim_alignment_human_gates": extraction_receipt_journal_alignment["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in extraction_receipt_journal_alignment["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening"
                    in extraction_receipt_journal_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state" in extraction_receipt_journal_alignment["required_readiness_check_ids"]
                ),
                "course_material_policy_claim_linked": (
                    "course_material_policy" in extraction_receipt_journal_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in extraction_receipt_journal_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in extraction_receipt_journal_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required"
                    in extraction_receipt_journal_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in extraction_receipt_journal_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in extraction_receipt_journal_alignment["required_human_gates"]
                ),
                "hash_only_records": extraction_receipt_journal_alignment["contracts"]["records_hash_only"],
                "workspace_card_receipt_journal_gate_contract": extraction_receipt_journal_alignment["contracts"][
                    "workspace_card_receipt_journal_gate_linked"
                ],
                "raw_text_storage_blocked": "raw extracted text storage"
                in extraction_receipt_journal_alignment["blocked_claims"],
                "local_path_storage_blocked": "local path storage"
                in extraction_receipt_journal_alignment["blocked_claims"],
                "manifest_update_by_receipt_alone_blocked": "tutor manifest update by receipt alone"
                in extraction_receipt_journal_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing"
                in extraction_receipt_journal_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in extraction_receipt_journal_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "extraction_progress",
            "passed": extraction_progress_alignment["status"] == "ready"
            and extraction_progress_alignment["public_safety_status"] == "pass"
            and extraction_progress_alignment["report_public_safety_status"] == "pass"
            and extraction_progress_alignment["exam_deployment_status"] == "not_cleared"
            and extraction_progress_alignment["missing_source_card_ids"] == []
            and extraction_progress_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": extraction_progress_alignment["status"],
                "release_claim_alignment_public_safety_status": extraction_progress_alignment["public_safety_status"],
                "release_claim_alignment_contract_status": extraction_progress_alignment["schema_version"],
                "release_claim_alignment_section_count": extraction_progress_alignment["section_count"],
                "report_status": extraction_progress_alignment["report_status"],
                "report_public_safety_status": extraction_progress_alignment["report_public_safety_status"],
                "exam_deployment_status": extraction_progress_alignment["exam_deployment_status"],
                "valid_receipt_count": extraction_progress_alignment["receipt_summary"]["valid_receipt_count"],
                "ready_for_human_review_count": extraction_progress_alignment["receipt_summary"][
                    "ready_for_human_review_count"
                ],
                "eligible_for_private_tutor_index_count": extraction_progress_alignment["receipt_summary"][
                    "eligible_for_private_tutor_index_count"
                ],
                "review_queue_count": extraction_progress_alignment["review_queue_count"],
                "manifest_update_candidate_count": extraction_progress_alignment["manifest_update_candidate_count"],
                "workspace_card_status": extraction_progress_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": extraction_progress_alignment["workspace_card_selected_skill_tag"],
                "workspace_card_ready_for_operator_prefill": extraction_progress_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": extraction_progress_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": extraction_progress_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": extraction_progress_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_progress_queue_gate_linked": extraction_progress_alignment[
                    "workspace_card_progress_queue_gate_linked"
                ],
                "release_claim_alignment_human_gates": extraction_progress_alignment["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in extraction_progress_alignment["required_readiness_check_ids"]
                ),
                "receipt_journal_claim_linked": (
                    "extraction_receipt_journal" in extraction_progress_alignment["required_readiness_check_ids"]
                ),
                "course_material_policy_claim_linked": (
                    "course_material_policy" in extraction_progress_alignment["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening" in extraction_progress_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state" in extraction_progress_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in extraction_progress_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in extraction_progress_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in extraction_progress_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in extraction_progress_alignment["required_human_gates"]
                ),
                "review_queue_hash_only": extraction_progress_alignment["contracts"]["review_queue_hash_only"],
                "manifest_candidates_private_metadata_only": extraction_progress_alignment["contracts"][
                    "manifest_candidates_private_metadata_only"
                ],
                "workspace_card_progress_queue_gate_contract": extraction_progress_alignment["contracts"][
                    "workspace_card_progress_queue_gate_linked"
                ],
                "raw_text_in_progress_blocked": "raw extracted text in progress report"
                in extraction_progress_alignment["blocked_claims"],
                "local_path_in_progress_blocked": "local path in progress report"
                in extraction_progress_alignment["blocked_claims"],
                "tutor_retrieval_without_manifest_update_blocked": "tutor retrieval without manifest update"
                in extraction_progress_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in extraction_progress_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in extraction_progress_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "extraction_manifest_update",
            "passed": extraction_manifest_update_alignment["status"] == "ready"
            and extraction_manifest_update_alignment["public_safety_status"] == "pass"
            and extraction_manifest_update_alignment["plan_public_safety_status"] == "pass"
            and extraction_manifest_update_alignment["exam_deployment_status"] == "not_cleared"
            and extraction_manifest_update_alignment["missing_source_card_ids"] == []
            and extraction_manifest_update_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": extraction_manifest_update_alignment["status"],
                "release_claim_alignment_public_safety_status": extraction_manifest_update_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": extraction_manifest_update_alignment["schema_version"],
                "release_claim_alignment_section_count": extraction_manifest_update_alignment["section_count"],
                "plan_status": extraction_manifest_update_alignment["plan_status"],
                "plan_public_safety_status": extraction_manifest_update_alignment["plan_public_safety_status"],
                "exam_deployment_status": extraction_manifest_update_alignment["exam_deployment_status"],
                "candidate_count": extraction_manifest_update_alignment["candidate_summary"]["candidate_count"],
                "ready_to_apply_private_count": extraction_manifest_update_alignment["candidate_summary"][
                    "ready_to_apply_private_count"
                ],
                "manifest_update_candidate_count": extraction_manifest_update_alignment[
                    "manifest_update_candidate_count"
                ],
                "workspace_card_status": extraction_manifest_update_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": extraction_manifest_update_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": extraction_manifest_update_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": extraction_manifest_update_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": extraction_manifest_update_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": extraction_manifest_update_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_candidate_gate_linked": extraction_manifest_update_alignment[
                    "workspace_card_candidate_gate_linked"
                ],
                "release_claim_alignment_human_gates": extraction_manifest_update_alignment["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in extraction_manifest_update_alignment["required_readiness_check_ids"]
                ),
                "progress_claim_linked": (
                    "extraction_progress" in extraction_manifest_update_alignment["required_readiness_check_ids"]
                ),
                "receipt_journal_claim_linked": (
                    "extraction_receipt_journal"
                    in extraction_manifest_update_alignment["required_readiness_check_ids"]
                ),
                "course_material_policy_claim_linked": (
                    "course_material_policy" in extraction_manifest_update_alignment["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening"
                    in extraction_manifest_update_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in extraction_manifest_update_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in extraction_manifest_update_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required"
                    in extraction_manifest_update_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in extraction_manifest_update_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in extraction_manifest_update_alignment["required_human_gates"]
                ),
                "execution_boundary_blocks_file_write_raw_and_paths": extraction_manifest_update_alignment[
                    "contracts"
                ]["execution_boundary_blocks_file_write_raw_and_paths"],
                "candidates_private_metadata_only": extraction_manifest_update_alignment["contracts"][
                    "candidates_private_metadata_only"
                ],
                "workspace_card_candidate_gate_linked_contract": extraction_manifest_update_alignment["contracts"][
                    "workspace_card_candidate_gate_linked"
                ],
                "manifest_file_write_by_planning_blocked": "manifest file write by planning"
                in extraction_manifest_update_alignment["blocked_claims"],
                "raw_text_storage_blocked": "raw OCR text storage"
                in extraction_manifest_update_alignment["blocked_claims"],
                "local_source_path_exposure_blocked": "local source path exposure"
                in extraction_manifest_update_alignment["blocked_claims"],
                "public_release_by_plan_blocked": "public release by manifest update plan"
                in extraction_manifest_update_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing"
                in extraction_manifest_update_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in extraction_manifest_update_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "extraction_manifest_apply",
            "passed": extraction_manifest_apply_alignment["status"] == "ready"
            and extraction_manifest_apply_alignment["public_safety_status"] == "pass"
            and extraction_manifest_apply_alignment["dry_run_public_safety_status"] == "pass"
            and extraction_manifest_apply_alignment["confirmed_public_safety_status"] == "pass"
            and extraction_manifest_apply_alignment["missing_source_card_ids"] == []
            and extraction_manifest_apply_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": extraction_manifest_apply_alignment["status"],
                "release_claim_alignment_public_safety_status": extraction_manifest_apply_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": extraction_manifest_apply_alignment["schema_version"],
                "release_claim_alignment_section_count": extraction_manifest_apply_alignment["section_count"],
                "dry_run_status": extraction_manifest_apply_alignment["dry_run_status"],
                "confirmed_status": extraction_manifest_apply_alignment["confirmed_status"],
                "dry_run_public_safety_status": extraction_manifest_apply_alignment["dry_run_public_safety_status"],
                "confirmed_public_safety_status": extraction_manifest_apply_alignment[
                    "confirmed_public_safety_status"
                ],
                "dry_run_records_to_apply_count": extraction_manifest_apply_alignment[
                    "dry_run_records_to_apply_count"
                ],
                "confirmed_applied_count": extraction_manifest_apply_alignment["confirmed_applied_count"],
                "workspace_card_status": extraction_manifest_apply_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": extraction_manifest_apply_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": extraction_manifest_apply_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": extraction_manifest_apply_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": extraction_manifest_apply_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": extraction_manifest_apply_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_manifest_gate_linked": extraction_manifest_apply_alignment[
                    "workspace_card_manifest_gate_linked"
                ],
                "release_claim_alignment_human_gates": extraction_manifest_apply_alignment["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in extraction_manifest_apply_alignment["required_readiness_check_ids"]
                ),
                "manifest_update_claim_linked": (
                    "extraction_manifest_update"
                    in extraction_manifest_apply_alignment["required_readiness_check_ids"]
                ),
                "progress_claim_linked": (
                    "extraction_progress" in extraction_manifest_apply_alignment["required_readiness_check_ids"]
                ),
                "receipt_journal_claim_linked": (
                    "extraction_receipt_journal"
                    in extraction_manifest_apply_alignment["required_readiness_check_ids"]
                ),
                "course_material_policy_claim_linked": (
                    "course_material_policy" in extraction_manifest_apply_alignment["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening"
                    in extraction_manifest_apply_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in extraction_manifest_apply_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in extraction_manifest_apply_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required"
                    in extraction_manifest_apply_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in extraction_manifest_apply_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in extraction_manifest_apply_alignment["required_human_gates"]
                ),
                "dry_run_does_not_write": extraction_manifest_apply_alignment["contracts"]["dry_run_does_not_write"],
                "confirmed_write_requires_operator_confirmation": extraction_manifest_apply_alignment["contracts"][
                    "confirmed_write_requires_operator_confirmation"
                ],
                "workspace_card_manifest_gate_linked_contract": extraction_manifest_apply_alignment["contracts"][
                    "workspace_card_manifest_gate_linked"
                ],
                "public_outputs_hide_paths_and_raw_text": extraction_manifest_apply_alignment["contracts"][
                    "public_outputs_hide_paths_and_raw_text"
                ],
                "tutor_indexing_never_started": extraction_manifest_apply_alignment["contracts"][
                    "tutor_indexing_never_started"
                ],
                "raw_text_returned_blocked": "raw extracted text returned"
                in extraction_manifest_apply_alignment["blocked_claims"],
                "local_path_returned_blocked": "local path returned"
                in extraction_manifest_apply_alignment["blocked_claims"],
                "private_manifest_path_returned_blocked": "private manifest path returned"
                in extraction_manifest_apply_alignment["blocked_claims"],
                "tutor_indexing_started_blocked": "tutor indexing started by apply"
                in extraction_manifest_apply_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing"
                in extraction_manifest_apply_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in extraction_manifest_apply_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "extraction_completion",
            "passed": extraction_completion_alignment["status"] == "ready"
            and extraction_completion_alignment["public_safety_status"] == "pass"
            and extraction_completion_alignment["receipt_completion_public_safety_status"] == "pass"
            and extraction_completion_alignment["deferral_completion_public_safety_status"] == "pass"
            and extraction_completion_alignment["missing_source_card_ids"] == []
            and extraction_completion_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": extraction_completion_alignment["status"],
                "release_claim_alignment_public_safety_status": extraction_completion_alignment["public_safety_status"],
                "release_claim_alignment_contract_status": extraction_completion_alignment["schema_version"],
                "release_claim_alignment_section_count": extraction_completion_alignment["section_count"],
                "receipt_completion_status": extraction_completion_alignment["receipt_completion_status"],
                "deferral_completion_status": extraction_completion_alignment["deferral_completion_status"],
                "receipt_completion_public_safety_status": extraction_completion_alignment[
                    "receipt_completion_public_safety_status"
                ],
                "deferral_completion_public_safety_status": extraction_completion_alignment[
                    "deferral_completion_public_safety_status"
                ],
                "receipt_open_job_count": extraction_completion_alignment["receipt_open_job_count"],
                "receipt_completed_job_count": extraction_completion_alignment["receipt_completed_job_count"],
                "deferral_open_job_count": extraction_completion_alignment["deferral_open_job_count"],
                "deferral_deferred_job_count": extraction_completion_alignment["deferral_deferred_job_count"],
                "release_claim_alignment_human_gates": extraction_completion_alignment["required_human_gates"],
                "receipt_journal_claim_linked": (
                    "extraction_receipt_journal"
                    in extraction_completion_alignment["required_readiness_check_ids"]
                ),
                "progress_claim_linked": (
                    "extraction_progress" in extraction_completion_alignment["required_readiness_check_ids"]
                ),
                "manifest_update_claim_linked": (
                    "extraction_manifest_update"
                    in extraction_completion_alignment["required_readiness_check_ids"]
                ),
                "manifest_apply_claim_linked": (
                    "extraction_manifest_apply"
                    in extraction_completion_alignment["required_readiness_check_ids"]
                ),
                "data_protection_claim_linked": (
                    "data_protection_screening"
                    in extraction_completion_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state" in extraction_completion_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in extraction_completion_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in extraction_completion_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in extraction_completion_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in extraction_completion_alignment["required_human_gates"]
                ),
                "receipt_completion_covers_all_jobs": extraction_completion_alignment["contracts"][
                    "receipt_completion_covers_all_jobs"
                ],
                "deferral_completion_covers_all_jobs_hash_only": extraction_completion_alignment["contracts"][
                    "deferral_completion_covers_all_jobs_hash_only"
                ],
                "completion_boundaries_block_execution_manifest_and_exam": extraction_completion_alignment[
                    "contracts"
                ]["completion_boundaries_block_execution_manifest_and_exam"],
                "raw_deferral_reason_storage_blocked": "raw deferral reason storage"
                in extraction_completion_alignment["blocked_claims"],
                "manifest_update_by_completion_report_blocked": "manifest update by completion report"
                in extraction_completion_alignment["blocked_claims"],
                "tutor_indexing_by_completion_report_blocked": "tutor indexing by completion report"
                in extraction_completion_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in extraction_completion_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in extraction_completion_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "extraction_human_review",
            "passed": extraction_human_review_alignment["status"] == "ready"
            and extraction_human_review_alignment["public_safety_status"] == "pass"
            and extraction_human_review_alignment["plan_public_safety_status"] == "pass"
            and extraction_human_review_alignment["exam_deployment_status"] == "not_cleared"
            and extraction_human_review_alignment["missing_source_card_ids"] == []
            and extraction_human_review_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": extraction_human_review_alignment["status"],
                "release_claim_alignment_public_safety_status": extraction_human_review_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": extraction_human_review_alignment["schema_version"],
                "release_claim_alignment_section_count": extraction_human_review_alignment["section_count"],
                "plan_status": extraction_human_review_alignment["plan_status"],
                "plan_public_safety_status": extraction_human_review_alignment["plan_public_safety_status"],
                "exam_deployment_status": extraction_human_review_alignment["exam_deployment_status"],
                "pre_review_ready_count": extraction_human_review_alignment["pre_review_ready_count"],
                "post_review_ready_count": extraction_human_review_alignment["post_review_ready_count"],
                "post_reviewed_for_private_tutor_count": extraction_human_review_alignment[
                    "post_reviewed_for_private_tutor_count"
                ],
                "stored_review_decision_count": extraction_human_review_alignment["stored_review_decision_count"],
                "invalid_review_decision_count": extraction_human_review_alignment["invalid_review_decision_count"],
                "appended_review_receipt_count": extraction_human_review_alignment["appended_review_receipt_count"],
                "appended_review_record_count": extraction_human_review_alignment["appended_review_record_count"],
                "manifest_candidate_count": extraction_human_review_alignment["manifest_candidate_count"],
                "ready_to_apply_private_count": extraction_human_review_alignment["ready_to_apply_private_count"],
                "release_claim_alignment_human_gates": extraction_human_review_alignment["required_human_gates"],
                "receipt_journal_claim_linked": (
                    "extraction_receipt_journal"
                    in extraction_human_review_alignment["required_readiness_check_ids"]
                ),
                "progress_claim_linked": (
                    "extraction_progress" in extraction_human_review_alignment["required_readiness_check_ids"]
                ),
                "completion_claim_linked": (
                    "extraction_completion" in extraction_human_review_alignment["required_readiness_check_ids"]
                ),
                "manifest_update_claim_linked": (
                    "extraction_manifest_update"
                    in extraction_human_review_alignment["required_readiness_check_ids"]
                ),
                "manifest_apply_claim_linked": (
                    "extraction_manifest_apply"
                    in extraction_human_review_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in extraction_human_review_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in extraction_human_review_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in extraction_human_review_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in extraction_human_review_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in extraction_human_review_alignment["required_human_gates"]
                ),
                "review_decisions_recorded_hash_only": extraction_human_review_alignment["contracts"][
                    "review_decisions_recorded_hash_only"
                ],
                "local_private_artifact_review_required": extraction_human_review_alignment["contracts"][
                    "local_private_artifact_review_required"
                ],
                "private_manifest_plan_only": extraction_human_review_alignment["contracts"][
                    "private_manifest_plan_only"
                ],
                "completion_evidence_linked": extraction_human_review_alignment["contracts"][
                    "completion_evidence_linked"
                ],
                "raw_review_notes_storage_blocked": "raw review notes storage"
                in extraction_human_review_alignment["blocked_claims"],
                "raw_text_returned_blocked": "raw extracted text returned"
                in extraction_human_review_alignment["blocked_claims"],
                "manifest_write_by_human_review_alone_blocked": "manifest write by human review alone"
                in extraction_human_review_alignment["blocked_claims"],
                "tutor_indexing_by_human_review_alone_blocked": "tutor indexing by human review alone"
                in extraction_human_review_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in extraction_human_review_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in extraction_human_review_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "private_tutor_use_flow",
            "passed": private_tutor_use_flow_alignment["status"] == "ready"
            and private_tutor_use_flow_alignment["public_safety_status"] == "pass"
            and private_tutor_use_flow_alignment["flow_public_safety_status"] == "pass"
            and private_tutor_use_flow_alignment["exam_deployment_status"] == "not_cleared"
            and private_tutor_use_flow_alignment["missing_source_card_ids"] == []
            and private_tutor_use_flow_alignment["failed_contract_ids"] == []
            and private_tutor_use_flow_workspace_alignment["status"] == "ready"
            and private_tutor_use_flow_workspace_alignment["alignment_public_safety_status"] == "pass"
            and private_tutor_use_flow_workspace_alignment["failed_contract_ids"] == []
            and private_tutor_use_flow_workspace_alignment["receipt_status"]
            == "private_tutor_use_flow_receipt_ready_not_exam_clearance"
            and private_tutor_use_flow_workspace_alignment["workspace_card_readiness_gate_linked"] is True
            and private_tutor_use_flow_workspace_alignment["workspace_card_private_tutor_flow_gate_linked"] is True
            and private_tutor_use_flow_workspace_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "release_claim_alignment_status": private_tutor_use_flow_alignment["status"],
                "release_claim_alignment_public_safety_status": private_tutor_use_flow_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": private_tutor_use_flow_alignment["schema_version"],
                "workspace_card_private_use_alignment_status": private_tutor_use_flow_workspace_alignment[
                    "status"
                ],
                "workspace_card_private_use_alignment_public_safety_status": private_tutor_use_flow_workspace_alignment[
                    "alignment_public_safety_status"
                ],
                "workspace_card_private_use_alignment_contract_status": private_tutor_use_flow_workspace_alignment[
                    "schema_version"
                ],
                "workspace_card_private_use_receipt_status": private_tutor_use_flow_workspace_alignment[
                    "receipt_status"
                ],
                "release_claim_alignment_section_count": private_tutor_use_flow_alignment["section_count"],
                "flow_status": private_tutor_use_flow_alignment["flow_status"],
                "flow_public_safety_status": private_tutor_use_flow_alignment["flow_public_safety_status"],
                "exam_deployment_status": private_tutor_use_flow_alignment["exam_deployment_status"],
                "manifest_apply_status": private_tutor_use_flow_alignment["manifest_apply_status"],
                "manifest_written": private_tutor_use_flow_alignment["manifest_written"],
                "tutor_index_status": private_tutor_use_flow_alignment["tutor_index_status"],
                "tutor_index_built": private_tutor_use_flow_alignment["tutor_index_built"],
                "tutor_index_anchor_count": private_tutor_use_flow_alignment["tutor_index_anchor_count"],
                "tutor_response_status": private_tutor_use_flow_alignment["tutor_response_status"],
                "effective_help_level": private_tutor_use_flow_alignment["effective_help_level"],
                "source_anchor_count": private_tutor_use_flow_alignment["source_anchor_count"],
                "ledger_status": private_tutor_use_flow_alignment["ledger_status"],
                "ledger_written": private_tutor_use_flow_alignment["ledger_written"],
                "workspace_card_status": private_tutor_use_flow_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": private_tutor_use_flow_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": private_tutor_use_flow_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": private_tutor_use_flow_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": private_tutor_use_flow_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": private_tutor_use_flow_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_help_ledger_gate_linked": private_tutor_use_flow_alignment[
                    "workspace_card_help_ledger_gate_linked"
                ],
                "workspace_card_private_tutor_flow_gate_linked": private_tutor_use_flow_workspace_alignment[
                    "workspace_card_private_tutor_flow_gate_linked"
                ],
                "workspace_card_operator_prefill_hash_present": private_tutor_use_flow_workspace_alignment[
                    "workspace_card_operator_prefill_hash_present"
                ],
                "study_receipt_status": private_tutor_use_flow_alignment["study_receipt_status"],
                "release_claim_alignment_human_gates": private_tutor_use_flow_alignment["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in private_tutor_use_flow_alignment["required_readiness_check_ids"]
                ),
                "human_review_claim_linked": (
                    "extraction_human_review"
                    in private_tutor_use_flow_alignment["required_readiness_check_ids"]
                ),
                "manifest_apply_claim_linked": (
                    "extraction_manifest_apply"
                    in private_tutor_use_flow_alignment["required_readiness_check_ids"]
                ),
                "completion_claim_linked": (
                    "extraction_completion"
                    in private_tutor_use_flow_alignment["required_readiness_check_ids"]
                ),
                "evaluation_claim_linked": (
                    "evaluation_packet"
                    in private_tutor_use_flow_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet"
                    in private_tutor_use_flow_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in private_tutor_use_flow_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in private_tutor_use_flow_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required"
                    in private_tutor_use_flow_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in private_tutor_use_flow_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in private_tutor_use_flow_alignment["required_human_gates"]
                ),
                "reviewed_private_manifest_evidence_operator_confirmed": private_tutor_use_flow_alignment[
                    "contracts"
                ]["reviewed_private_manifest_evidence_operator_confirmed"],
                "hash_only_tutor_index_operator_confirmed": private_tutor_use_flow_alignment["contracts"][
                    "hash_only_tutor_index_operator_confirmed"
                ],
                "learner_agency_a0_a2_source_anchored": private_tutor_use_flow_alignment["contracts"][
                    "learner_agency_a0_a2_source_anchored"
                ],
                "help_ledger_operator_confirmed_hash_only": private_tutor_use_flow_alignment["contracts"][
                    "help_ledger_operator_confirmed_hash_only"
                ],
                "workspace_card_help_ledger_gate_linked_contract": private_tutor_use_flow_alignment["contracts"][
                    "workspace_card_help_ledger_gate_linked"
                ],
                "public_outputs_hide_private_data": private_tutor_use_flow_alignment["contracts"][
                    "public_outputs_hide_private_data"
                ],
                "high_stakes_actions_not_started": private_tutor_use_flow_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "raw_query_returned_blocked": "raw query returned"
                in private_tutor_use_flow_alignment["blocked_claims"],
                "raw_text_returned_blocked": "raw extracted course text returned"
                in private_tutor_use_flow_alignment["blocked_claims"],
                "unconfirmed_manifest_apply_blocked": "private manifest apply without operator confirmation"
                in private_tutor_use_flow_alignment["blocked_claims"],
                "unconfirmed_tutor_index_build_blocked": "private tutor index build without operator confirmation"
                in private_tutor_use_flow_alignment["blocked_claims"],
                "complete_code_or_final_answer_tutoring_blocked": "complete code or final-answer tutoring"
                in private_tutor_use_flow_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing"
                in private_tutor_use_flow_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in private_tutor_use_flow_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "study_session",
            "passed": study_session_alignment["status"] == "ready"
            and study_session_alignment["public_safety_status"] == "pass"
            and study_session_alignment["review_public_safety_status"] == "pass"
            and study_session_alignment["repeat_validation_public_safety_status"] == "pass"
            and study_session_alignment["exam_deployment_status"] == "not_cleared"
            and study_session_alignment["missing_source_card_ids"] == []
            and study_session_alignment["failed_contract_ids"] == []
            and study_session_workspace_alignment["status"] == "ready"
            and study_session_workspace_alignment["alignment_public_safety_status"] == "pass"
            and study_session_workspace_alignment["failed_contract_ids"] == []
            and study_session_workspace_alignment["receipt_status"]
            == "study_session_review_receipt_ready_not_exam_clearance"
            and study_session_workspace_alignment["workspace_card_readiness_gate_linked"] is True
            and study_session_workspace_alignment["workspace_card_study_session_gate_linked"] is True
            and study_session_workspace_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "release_claim_alignment_status": study_session_alignment["status"],
                "release_claim_alignment_public_safety_status": study_session_alignment["public_safety_status"],
                "release_claim_alignment_contract_status": study_session_alignment["schema_version"],
                "workspace_card_study_alignment_status": study_session_workspace_alignment["status"],
                "workspace_card_study_alignment_public_safety_status": study_session_workspace_alignment[
                    "alignment_public_safety_status"
                ],
                "workspace_card_study_alignment_contract_status": study_session_workspace_alignment[
                    "schema_version"
                ],
                "workspace_card_study_receipt_status": study_session_workspace_alignment["receipt_status"],
                "release_claim_alignment_section_count": study_session_alignment["section_count"],
                "review_status": study_session_alignment["review_status"],
                "review_public_safety_status": study_session_alignment["review_public_safety_status"],
                "study_session_status": study_session_alignment["study_session_status"],
                "exam_deployment_status": study_session_alignment["exam_deployment_status"],
                "planned_task_count": study_session_alignment["planned_task_count"],
                "valid_receipt_count": study_session_alignment["valid_receipt_count"],
                "blocked_receipt_count": study_session_alignment["blocked_receipt_count"],
                "repeat_task_required_count": study_session_alignment["repeat_task_required_count"],
                "missing_planned_receipt_count": study_session_alignment["missing_planned_receipt_count"],
                "repeat_validation_status": study_session_alignment["repeat_validation_status"],
                "repeat_validation_public_safety_status": study_session_alignment[
                    "repeat_validation_public_safety_status"
                ],
                "repeat_task_required": study_session_alignment["repeat_task_required"],
                "workspace_card_status": study_session_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": study_session_alignment["workspace_card_selected_skill_tag"],
                "workspace_card_ready_for_operator_prefill": study_session_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": study_session_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": study_session_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": study_session_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_reflection_gate_linked": study_session_alignment[
                    "workspace_card_reflection_gate_linked"
                ],
                "workspace_card_study_session_gate_linked": study_session_workspace_alignment[
                    "workspace_card_study_session_gate_linked"
                ],
                "workspace_card_operator_prefill_hash_present": study_session_workspace_alignment[
                    "workspace_card_operator_prefill_hash_present"
                ],
                "workspace_card_reflection_hash_present": study_session_alignment[
                    "workspace_card_reflection_hash_present"
                ],
                "release_claim_alignment_human_gates": study_session_alignment["required_human_gates"],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in study_session_alignment["required_readiness_check_ids"]
                ),
                "private_tutor_use_flow_claim_linked": (
                    "private_tutor_use_flow" in study_session_alignment["required_readiness_check_ids"]
                ),
                "evaluation_claim_linked": (
                    "evaluation_packet" in study_session_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in study_session_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state" in study_session_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in study_session_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in study_session_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in study_session_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in study_session_alignment["required_human_gates"]
                ),
                "study_plan_ready_for_course_bound_practice": study_session_alignment["contracts"][
                    "study_plan_ready_for_course_bound_practice"
                ],
                "hash_only_receipts_with_required_evidence": study_session_alignment["contracts"][
                    "hash_only_receipts_with_required_evidence"
                ],
                "learner_agency_profile_complete": study_session_alignment["contracts"][
                    "learner_agency_profile_complete"
                ],
                "a6_or_final_solution_forces_repeat": study_session_alignment["contracts"][
                    "a6_or_final_solution_forces_repeat"
                ],
                "workspace_card_reflection_gate_linked_contract": study_session_alignment["contracts"][
                    "workspace_card_reflection_gate_linked"
                ],
                "non_grading_human_review_only": study_session_alignment["contracts"][
                    "non_grading_human_review_only"
                ],
                "raw_reflection_storage_blocked": "raw reflection storage"
                in study_session_alignment["blocked_claims"],
                "final_solution_acceptance_blocked": "final solution acceptance"
                in study_session_alignment["blocked_claims"],
                "eigenleistung_percentage_claim_blocked": "Eigenleistung percentage claim"
                in study_session_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading" in study_session_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring" in study_session_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in study_session_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in study_session_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in study_session_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "notebook_checkpoint",
            "passed": notebook_checkpoint_alignment["status"] == "ready"
            and notebook_checkpoint_alignment["public_safety_status"] == "pass"
            and notebook_checkpoint_alignment["ready_public_safety_status"] == "pass"
            and notebook_checkpoint_alignment["stored_public_safety_status"] == "pass"
            and notebook_checkpoint_alignment["repeat_public_safety_status"] == "pass"
            and notebook_checkpoint_alignment["exam_deployment_status"] == "not_cleared"
            and notebook_checkpoint_alignment["missing_source_card_ids"] == []
            and notebook_checkpoint_alignment["failed_contract_ids"] == []
            and notebook_checkpoint_workspace_alignment["status"] == "ready"
            and notebook_checkpoint_workspace_alignment["public_safety_status"] == "pass"
            and notebook_checkpoint_workspace_alignment["checkpoint_public_safety_status"] == "pass"
            and notebook_checkpoint_workspace_alignment["stored_checkpoint_public_safety_status"] == "pass"
            and notebook_checkpoint_workspace_alignment["exam_deployment_status"] == "not_cleared"
            and notebook_checkpoint_workspace_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": notebook_checkpoint_alignment["status"],
                "release_claim_alignment_public_safety_status": notebook_checkpoint_alignment["public_safety_status"],
                "release_claim_alignment_contract_status": notebook_checkpoint_alignment["schema_version"],
                "release_claim_alignment_section_count": notebook_checkpoint_alignment["section_count"],
                "ready_checkpoint_status": notebook_checkpoint_alignment["ready_checkpoint_status"],
                "ready_public_safety_status": notebook_checkpoint_alignment["ready_public_safety_status"],
                "stored_checkpoint_status": notebook_checkpoint_alignment["stored_checkpoint_status"],
                "stored_public_safety_status": notebook_checkpoint_alignment["stored_public_safety_status"],
                "repeat_checkpoint_status": notebook_checkpoint_alignment["repeat_checkpoint_status"],
                "repeat_public_safety_status": notebook_checkpoint_alignment["repeat_public_safety_status"],
                "exam_deployment_status": notebook_checkpoint_alignment["exam_deployment_status"],
                "study_receipt_status": notebook_checkpoint_alignment["study_receipt_status"],
                "checkpoint_hash_present": notebook_checkpoint_alignment["checkpoint_hash_present"],
                "workspace_card_status": notebook_checkpoint_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": notebook_checkpoint_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": notebook_checkpoint_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": notebook_checkpoint_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": notebook_checkpoint_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": notebook_checkpoint_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_checkpoint_gate_linked": notebook_checkpoint_alignment[
                    "workspace_card_checkpoint_gate_linked"
                ],
                "workspace_card_checkpoint_receipt_alignment_status": notebook_checkpoint_workspace_alignment[
                    "status"
                ],
                "workspace_card_checkpoint_receipt_alignment_public_safety_status": (
                    notebook_checkpoint_workspace_alignment["public_safety_status"]
                ),
                "workspace_card_checkpoint_receipt_alignment_contract_status": (
                    notebook_checkpoint_workspace_alignment["schema_version"]
                ),
                "checkpoint_report_hash_present": bool(
                    notebook_checkpoint_workspace_alignment["checkpoint_report_hash"]
                ),
                "checkpoint_receipt_hash_present": bool(
                    notebook_checkpoint_workspace_alignment["checkpoint_receipt_hash"]
                ),
                "stored_checkpoint_receipt_hash_present": bool(
                    notebook_checkpoint_workspace_alignment["stored_checkpoint_receipt_hash"]
                ),
                "workspace_card_checkpoint_receipt_gate_linked": notebook_checkpoint_workspace_alignment[
                    "workspace_card_checkpoint_receipt_gate_linked"
                ],
                "workspace_card_checkpoint_receipt_gate_linked_contract": (
                    notebook_checkpoint_workspace_alignment["contracts"][
                        "workspace_card_checkpoint_receipt_gate_linked"
                    ]
                ),
                "checkpoint_receipt_study_session_reference_preserved": (
                    notebook_checkpoint_workspace_alignment["contracts"]["study_session_reference_preserved"]
                ),
                "checkpoint_receipt_operator_journal_boundary_preserved": (
                    notebook_checkpoint_workspace_alignment["contracts"][
                        "operator_confirmed_journal_boundary_preserved"
                    ]
                ),
                "checkpoint_receipt_local_write_boundary_not_exam_clearance": (
                    notebook_checkpoint_workspace_alignment["contracts"]["local_write_boundary_not_exam_clearance"]
                ),
                "checkpoint_receipt_hashes_present_contract": notebook_checkpoint_workspace_alignment[
                    "contracts"
                ]["checkpoint_receipt_hashes_present"],
                "checkpoint_journal_status": notebook_checkpoint_alignment["checkpoint_journal_status"],
                "checkpoint_journal_written": notebook_checkpoint_alignment["checkpoint_journal_written"],
                "repeat_receipt_status": notebook_checkpoint_alignment["repeat_receipt_status"],
                "repeat_task_required": notebook_checkpoint_alignment["repeat_task_required"],
                "release_claim_alignment_human_gates": notebook_checkpoint_alignment["required_human_gates"],
                "study_session_claim_linked": (
                    "study_session" in notebook_checkpoint_alignment["required_readiness_check_ids"]
                ),
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in notebook_checkpoint_alignment["required_readiness_check_ids"]
                ),
                "private_tutor_use_flow_claim_linked": (
                    "private_tutor_use_flow" in notebook_checkpoint_alignment["required_readiness_check_ids"]
                ),
                "evaluation_claim_linked": (
                    "evaluation_packet" in notebook_checkpoint_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in notebook_checkpoint_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state" in notebook_checkpoint_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in notebook_checkpoint_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in notebook_checkpoint_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in notebook_checkpoint_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in notebook_checkpoint_alignment["required_human_gates"]
                ),
                "hash_only_checkpoint_ready": notebook_checkpoint_alignment["contracts"][
                    "hash_only_checkpoint_ready"
                ],
                "operator_confirmed_journal_hash_only": notebook_checkpoint_alignment["contracts"][
                    "operator_confirmed_journal_hash_only"
                ],
                "a6_or_final_solution_forces_repeat": notebook_checkpoint_alignment["contracts"][
                    "a6_or_final_solution_forces_repeat"
                ],
                "workspace_card_checkpoint_gate_linked_contract": notebook_checkpoint_alignment["contracts"][
                    "workspace_card_checkpoint_gate_linked"
                ],
                "public_outputs_hide_private_notebook_data": notebook_checkpoint_alignment["contracts"][
                    "public_outputs_hide_private_notebook_data"
                ],
                "high_stakes_actions_not_started": notebook_checkpoint_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in notebook_checkpoint_alignment["blocked_claims"],
                "raw_cell_text_returned_blocked": "raw cell text returned"
                in notebook_checkpoint_alignment["blocked_claims"],
                "unconfirmed_checkpoint_journal_write_blocked": "checkpoint journal write without operator confirmation"
                in notebook_checkpoint_alignment["blocked_claims"],
                "final_solution_acceptance_blocked": "final solution acceptance"
                in notebook_checkpoint_alignment["blocked_claims"],
                "eigenleistung_percentage_claim_blocked": "Eigenleistung percentage claim"
                in notebook_checkpoint_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading" in notebook_checkpoint_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring" in notebook_checkpoint_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in notebook_checkpoint_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in notebook_checkpoint_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in notebook_checkpoint_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "exam_workspace_launch",
            "passed": exam_workspace_launch_alignment["status"] == "ready"
            and exam_workspace_launch_alignment["public_safety_status"] == "pass"
            and exam_workspace_launch_alignment["launch_public_safety_status"] == "pass"
            and exam_workspace_launch_alignment["blocked_public_safety_status"] == "pass"
            and exam_workspace_launch_alignment["exam_deployment_status"] == "not_cleared"
            and exam_workspace_launch_alignment["missing_source_card_ids"] == []
            and exam_workspace_launch_alignment["failed_contract_ids"] == []
            and exam_workspace_launch_workspace_alignment["status"] == "ready"
            and exam_workspace_launch_workspace_alignment["public_safety_status"] == "pass"
            and exam_workspace_launch_workspace_alignment["launch_public_safety_status"] == "pass"
            and exam_workspace_launch_workspace_alignment["blocked_launch_public_safety_status"] == "pass"
            and exam_workspace_launch_workspace_alignment["exam_deployment_status"] == "not_cleared"
            and exam_workspace_launch_workspace_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": exam_workspace_launch_alignment["status"],
                "release_claim_alignment_public_safety_status": exam_workspace_launch_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": exam_workspace_launch_alignment["schema_version"],
                "release_claim_alignment_section_count": exam_workspace_launch_alignment["section_count"],
                "launch_status": exam_workspace_launch_alignment["launch_status"],
                "launch_public_safety_status": exam_workspace_launch_alignment["launch_public_safety_status"],
                "launch_workspace_status": exam_workspace_launch_alignment["launch_workspace_status"],
                "blocked_launch_status": exam_workspace_launch_alignment["blocked_launch_status"],
                "blocked_public_safety_status": exam_workspace_launch_alignment["blocked_public_safety_status"],
                "exam_deployment_status": exam_workspace_launch_alignment["exam_deployment_status"],
                "checkpoint_status": exam_workspace_launch_alignment["checkpoint_status"],
                "checkpoint_hash_present": exam_workspace_launch_alignment["checkpoint_hash_present"],
                "study_receipt_status": exam_workspace_launch_alignment["study_receipt_status"],
                "tutor_status": exam_workspace_launch_alignment["tutor_status"],
                "workspace_card_status": exam_workspace_launch_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": exam_workspace_launch_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": exam_workspace_launch_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": exam_workspace_launch_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": exam_workspace_launch_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": exam_workspace_launch_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_launch_receipt_alignment_status": exam_workspace_launch_workspace_alignment[
                    "status"
                ],
                "workspace_card_launch_receipt_alignment_public_safety_status": (
                    exam_workspace_launch_workspace_alignment["public_safety_status"]
                ),
                "workspace_card_launch_receipt_alignment_contract_status": (
                    exam_workspace_launch_workspace_alignment["schema_version"]
                ),
                "launch_hash_present": bool(exam_workspace_launch_workspace_alignment["launch_hash"]),
                "launch_receipt_hash_present": bool(
                    exam_workspace_launch_workspace_alignment["launch_receipt_hash"]
                ),
                "blocked_launch_receipt_hash_present": bool(
                    exam_workspace_launch_workspace_alignment["blocked_launch_receipt_hash"]
                ),
                "workspace_card_launch_receipt_gate_linked": exam_workspace_launch_workspace_alignment[
                    "workspace_card_launch_receipt_gate_linked"
                ],
                "workspace_card_launch_receipt_gate_linked_contract": (
                    exam_workspace_launch_workspace_alignment["contracts"][
                        "workspace_card_launch_receipt_gate_linked"
                    ]
                ),
                "launch_ready_with_receipt": exam_workspace_launch_workspace_alignment["contracts"][
                    "launch_ready_with_receipt"
                ],
                "launch_coverage_start_point_preserved": exam_workspace_launch_workspace_alignment[
                    "contracts"
                ]["coverage_start_point_preserved"],
                "launch_private_tutor_study_checkpoint_references_preserved": (
                    exam_workspace_launch_workspace_alignment["contracts"][
                        "private_tutor_study_checkpoint_references_preserved"
                    ]
                ),
                "launch_receipt_hashes_present_contract": exam_workspace_launch_workspace_alignment[
                    "contracts"
                ]["launch_receipt_hashes_present"],
                "launch_operator_reviewed_boundary_preserved": exam_workspace_launch_workspace_alignment[
                    "contracts"
                ]["operator_reviewed_launch_boundary_preserved"],
                "help_ledger_preview_status": exam_workspace_launch_alignment["help_ledger_preview_status"],
                "general_help_ledger_written": exam_workspace_launch_alignment["general_help_ledger_written"],
                "exam_ledger_written": exam_workspace_launch_alignment["exam_ledger_written"],
                "repeat_task_required": exam_workspace_launch_alignment["repeat_task_required"],
                "release_claim_alignment_human_gates": exam_workspace_launch_alignment["required_human_gates"],
                "notebook_checkpoint_claim_linked": (
                    "notebook_checkpoint" in exam_workspace_launch_alignment["required_readiness_check_ids"]
                ),
                "study_session_claim_linked": (
                    "study_session" in exam_workspace_launch_alignment["required_readiness_check_ids"]
                ),
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in exam_workspace_launch_alignment["required_readiness_check_ids"]
                ),
                "private_tutor_use_flow_claim_linked": (
                    "private_tutor_use_flow" in exam_workspace_launch_alignment["required_readiness_check_ids"]
                ),
                "evaluation_claim_linked": (
                    "evaluation_packet" in exam_workspace_launch_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in exam_workspace_launch_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state" in exam_workspace_launch_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in exam_workspace_launch_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in exam_workspace_launch_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in exam_workspace_launch_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in exam_workspace_launch_alignment["required_human_gates"]
                ),
                "launch_public_safe": exam_workspace_launch_alignment["contracts"]["launch_public_safe"],
                "blocked_launch_public_safe": exam_workspace_launch_alignment["contracts"]["blocked_launch_public_safe"],
                "notebook_checkpoint_linked_hash_only": exam_workspace_launch_alignment["contracts"][
                    "notebook_checkpoint_linked_hash_only"
                ],
                "private_tutor_use_and_study_receipt_linked": exam_workspace_launch_alignment["contracts"][
                    "private_tutor_use_and_study_receipt_linked"
                ],
                "workspace_card_launch_gate_linked": exam_workspace_launch_alignment["contracts"][
                    "workspace_card_launch_gate_linked"
                ],
                "dry_run_operator_boundaries_hold": exam_workspace_launch_alignment["contracts"][
                    "dry_run_operator_boundaries_hold"
                ],
                "blocked_checkpoint_stops_launch": exam_workspace_launch_alignment["contracts"][
                    "blocked_checkpoint_stops_launch"
                ],
                "public_outputs_hide_private_data": exam_workspace_launch_alignment["contracts"][
                    "public_outputs_hide_private_data"
                ],
                "high_stakes_actions_not_started": exam_workspace_launch_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in exam_workspace_launch_alignment["blocked_claims"],
                "raw_cell_text_returned_blocked": "raw cell text returned"
                in exam_workspace_launch_alignment["blocked_claims"],
                "final_solution_acceptance_blocked": "final solution acceptance"
                in exam_workspace_launch_alignment["blocked_claims"],
                "eigenleistung_percentage_claim_blocked": "Eigenleistung percentage claim"
                in exam_workspace_launch_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading" in exam_workspace_launch_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring" in exam_workspace_launch_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in exam_workspace_launch_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in exam_workspace_launch_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in exam_workspace_launch_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance" in exam_workspace_launch_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "exam_workspace_run",
            "passed": exam_workspace_run_alignment["status"] == "ready"
            and exam_workspace_run_alignment["public_safety_status"] == "pass"
            and exam_workspace_run_alignment["run_public_safety_status"] == "pass"
            and exam_workspace_run_alignment["waiting_public_safety_status"] == "pass"
            and exam_workspace_run_alignment["exam_deployment_status"] == "not_cleared"
            and exam_workspace_run_alignment["missing_source_card_ids"] == []
            and exam_workspace_run_alignment["failed_contract_ids"] == []
            and exam_workspace_run_workspace_alignment["status"] == "ready"
            and exam_workspace_run_workspace_alignment["public_safety_status"] == "pass"
            and exam_workspace_run_workspace_alignment["run_public_safety_status"] == "pass"
            and exam_workspace_run_workspace_alignment["waiting_public_safety_status"] == "pass"
            and exam_workspace_run_workspace_alignment["exam_deployment_status"] == "not_cleared"
            and exam_workspace_run_workspace_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": exam_workspace_run_alignment["status"],
                "release_claim_alignment_public_safety_status": exam_workspace_run_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": exam_workspace_run_alignment["schema_version"],
                "release_claim_alignment_section_count": exam_workspace_run_alignment["section_count"],
                "run_status": exam_workspace_run_alignment["run_status"],
                "run_public_safety_status": exam_workspace_run_alignment["run_public_safety_status"],
                "waiting_status": exam_workspace_run_alignment["waiting_status"],
                "waiting_public_safety_status": exam_workspace_run_alignment["waiting_public_safety_status"],
                "exam_deployment_status": exam_workspace_run_alignment["exam_deployment_status"],
                "session_status": exam_workspace_run_alignment["session_status"],
                "material_freeze_status": exam_workspace_run_alignment["material_freeze_status"],
                "notebook_run_status": exam_workspace_run_alignment["notebook_run_status"],
                "notebook_hash_present": exam_workspace_run_alignment["notebook_hash_present"],
                "notebook_work_hash_present": exam_workspace_run_alignment["notebook_work_hash_present"],
                "tutor_status": exam_workspace_run_alignment["tutor_status"],
                "effective_help_level": exam_workspace_run_alignment["effective_help_level"],
                "source_anchor_count": exam_workspace_run_alignment["source_anchor_count"],
                "workspace_card_status": exam_workspace_run_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": exam_workspace_run_alignment["workspace_card_selected_skill_tag"],
                "workspace_card_ready_for_operator_prefill": exam_workspace_run_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": exam_workspace_run_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": exam_workspace_run_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": exam_workspace_run_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_run_receipt_alignment_status": exam_workspace_run_workspace_alignment["status"],
                "workspace_card_run_receipt_alignment_public_safety_status": (
                    exam_workspace_run_workspace_alignment["public_safety_status"]
                ),
                "workspace_card_run_receipt_alignment_contract_status": (
                    exam_workspace_run_workspace_alignment["schema_version"]
                ),
                "run_hash_present": bool(exam_workspace_run_workspace_alignment["run_hash"]),
                "run_receipt_hash_present": bool(exam_workspace_run_workspace_alignment["run_receipt_hash"]),
                "waiting_run_receipt_hash_present": bool(
                    exam_workspace_run_workspace_alignment["waiting_run_receipt_hash"]
                ),
                "workspace_card_run_receipt_gate_linked": exam_workspace_run_workspace_alignment[
                    "workspace_card_run_receipt_gate_linked"
                ],
                "workspace_card_run_receipt_gate_linked_contract": (
                    exam_workspace_run_workspace_alignment["contracts"]["workspace_card_run_receipt_gate_linked"]
                ),
                "run_ready_with_receipts": exam_workspace_run_workspace_alignment["contracts"][
                    "run_ready_with_receipts"
                ],
                "run_private_tutor_study_ledger_references_preserved": (
                    exam_workspace_run_workspace_alignment["contracts"][
                        "private_tutor_study_ledger_references_preserved"
                    ]
                ),
                "run_notebook_checkpoint_hash_only_preserved": exam_workspace_run_workspace_alignment[
                    "contracts"
                ]["notebook_checkpoint_hash_only_preserved"],
                "run_receipt_hashes_present_contract": exam_workspace_run_workspace_alignment["contracts"][
                    "run_receipt_hashes_present"
                ],
                "run_operator_confirmed_local_write_boundary_preserved": (
                    exam_workspace_run_workspace_alignment["contracts"][
                        "operator_confirmed_local_write_boundary_preserved"
                    ]
                ),
                "run_waiting_mode_no_write_boundary_preserved": exam_workspace_run_workspace_alignment[
                    "contracts"
                ]["waiting_mode_no_write_boundary_preserved"],
                "private_tutor_use_flow_status": exam_workspace_run_alignment["private_tutor_use_flow_status"],
                "study_receipt_status": exam_workspace_run_alignment["study_receipt_status"],
                "general_help_ledger_status": exam_workspace_run_alignment["general_help_ledger_status"],
                "general_help_ledger_written": exam_workspace_run_alignment["general_help_ledger_written"],
                "exam_ledger_status": exam_workspace_run_alignment["exam_ledger_status"],
                "exam_ledger_written": exam_workspace_run_alignment["exam_ledger_written"],
                "export_status": exam_workspace_run_alignment["export_status"],
                "export_not_cleared_receipt": exam_workspace_run_alignment["export_not_cleared_receipt"],
                "human_reviewable_independence_evidence": exam_workspace_run_alignment[
                    "human_reviewable_independence_evidence"
                ],
                "waiting_session_status": exam_workspace_run_alignment["waiting_session_status"],
                "waiting_freeze_written": exam_workspace_run_alignment["waiting_freeze_written"],
                "waiting_exam_ledger_written": exam_workspace_run_alignment["waiting_exam_ledger_written"],
                "release_claim_alignment_human_gates": exam_workspace_run_alignment["required_human_gates"],
                "launch_claim_linked": (
                    "exam_workspace_launch" in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "notebook_checkpoint_claim_linked": (
                    "notebook_checkpoint" in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "study_session_claim_linked": (
                    "study_session" in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "private_tutor_use_flow_claim_linked": (
                    "private_tutor_use_flow" in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "evaluation_claim_linked": (
                    "evaluation_packet" in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state" in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in exam_workspace_run_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in exam_workspace_run_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in exam_workspace_run_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in exam_workspace_run_alignment["required_human_gates"]
                ),
                "run_public_safe": exam_workspace_run_alignment["contracts"]["run_public_safe"],
                "waiting_run_public_safe": exam_workspace_run_alignment["contracts"]["waiting_run_public_safe"],
                "session_material_notebook_checkpoint_hash_only": exam_workspace_run_alignment["contracts"][
                    "session_material_notebook_checkpoint_hash_only"
                ],
                "private_tutor_study_and_ledger_linked": exam_workspace_run_alignment["contracts"][
                    "private_tutor_study_and_ledger_linked"
                ],
                "workspace_card_execution_gate_linked": exam_workspace_run_alignment["contracts"][
                    "workspace_card_execution_gate_linked"
                ],
                "operator_confirmed_local_write_boundaries": exam_workspace_run_alignment["contracts"][
                    "operator_confirmed_local_write_boundaries"
                ],
                "waiting_mode_no_writes_no_paths": exam_workspace_run_alignment["contracts"][
                    "waiting_mode_no_writes_no_paths"
                ],
                "export_receipt_not_exam_clearance": exam_workspace_run_alignment["contracts"][
                    "export_receipt_not_exam_clearance"
                ],
                "public_outputs_hide_private_data": exam_workspace_run_alignment["contracts"][
                    "public_outputs_hide_private_data"
                ],
                "high_stakes_actions_not_started": exam_workspace_run_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "raw_query_returned_blocked": "raw query returned" in exam_workspace_run_alignment["blocked_claims"],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in exam_workspace_run_alignment["blocked_claims"],
                "raw_cell_text_returned_blocked": "raw cell text returned"
                in exam_workspace_run_alignment["blocked_claims"],
                "final_solution_acceptance_blocked": "final solution acceptance"
                in exam_workspace_run_alignment["blocked_claims"],
                "eigenleistung_percentage_claim_blocked": "Eigenleistung percentage claim"
                in exam_workspace_run_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading" in exam_workspace_run_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring" in exam_workspace_run_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in exam_workspace_run_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in exam_workspace_run_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in exam_workspace_run_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance" in exam_workspace_run_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "exam_workspace_run_history",
            "passed": exam_workspace_run_history_alignment["status"] == "ready"
            and exam_workspace_run_history_alignment["public_safety_status"] == "pass"
            and exam_workspace_run_history_alignment["history_public_safety_status"] == "pass"
            and exam_workspace_run_history_alignment["waiting_public_safety_status"] == "pass"
            and exam_workspace_run_history_alignment["exam_deployment_status"] == "not_cleared"
            and exam_workspace_run_history_alignment["missing_source_card_ids"] == []
            and exam_workspace_run_history_alignment["failed_contract_ids"] == []
            and exam_workspace_run_history_workspace_alignment["status"] == "ready"
            and exam_workspace_run_history_workspace_alignment["public_safety_status"] == "pass"
            and exam_workspace_run_history_workspace_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": exam_workspace_run_history_alignment["status"],
                "release_claim_alignment_public_safety_status": exam_workspace_run_history_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": exam_workspace_run_history_alignment["schema_version"],
                "release_claim_alignment_section_count": exam_workspace_run_history_alignment["section_count"],
                "history_status": exam_workspace_run_history_alignment["history_status"],
                "history_public_safety_status": exam_workspace_run_history_alignment["history_public_safety_status"],
                "waiting_status": exam_workspace_run_history_alignment["waiting_status"],
                "waiting_public_safety_status": exam_workspace_run_history_alignment["waiting_public_safety_status"],
                "exam_deployment_status": exam_workspace_run_history_alignment["exam_deployment_status"],
                "run_count": exam_workspace_run_history_alignment["run_count"],
                "checkpoint_hash_count": exam_workspace_run_history_alignment["checkpoint_hash_count"],
                "skill_tags": exam_workspace_run_history_alignment["skill_tags"],
                "help_level_profile": exam_workspace_run_history_alignment["help_level_profile"],
                "blocker_profile": exam_workspace_run_history_alignment["blocker_profile"],
                "open_operator_step_count": exam_workspace_run_history_alignment["open_operator_step_count"],
                "workspace_card_profile": exam_workspace_run_history_alignment["workspace_card_profile"],
                "workspace_card_ready_entry_count": exam_workspace_run_history_alignment[
                    "workspace_card_ready_entry_count"
                ],
                "workspace_card_help_ledger_hash_count": exam_workspace_run_history_alignment[
                    "workspace_card_help_ledger_hash_count"
                ],
                "workspace_card_readiness_gate_linked": exam_workspace_run_history_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_history_receipt_alignment_status": exam_workspace_run_history_workspace_alignment[
                    "status"
                ],
                "workspace_card_history_receipt_alignment_public_safety_status": (
                    exam_workspace_run_history_workspace_alignment["public_safety_status"]
                ),
                "workspace_card_history_receipt_alignment_contract_status": (
                    exam_workspace_run_history_workspace_alignment["schema_version"]
                ),
                "history_hash_present": bool(exam_workspace_run_history_workspace_alignment["history_hash"]),
                "history_receipt_hash_present": bool(
                    exam_workspace_run_history_workspace_alignment["history_receipt_hash"]
                ),
                "waiting_history_receipt_hash_present": bool(
                    exam_workspace_run_history_workspace_alignment["waiting_history_receipt_hash"]
                ),
                "workspace_card_history_receipt_gate_linked": (
                    exam_workspace_run_history_workspace_alignment["workspace_card_history_receipt_gate_linked"]
                ),
                "workspace_card_history_receipt_gate_linked_contract": (
                    exam_workspace_run_history_workspace_alignment["contracts"][
                        "workspace_card_history_receipt_gate_linked"
                    ]
                ),
                "history_export_review_ready": exam_workspace_run_history_workspace_alignment["contracts"][
                    "history_export_review_ready"
                ],
                "session_console_receipts_preserved": exam_workspace_run_history_workspace_alignment["contracts"][
                    "session_console_receipts_preserved"
                ],
                "checkpoint_hashes_and_help_profile_preserved": (
                    exam_workspace_run_history_workspace_alignment["contracts"][
                        "checkpoint_hashes_and_help_profile_preserved"
                    ]
                ),
                "reflection_review_status_preserved": exam_workspace_run_history_workspace_alignment["contracts"][
                    "reflection_review_status_preserved"
                ],
                "export_receipt_reference_preserved": exam_workspace_run_history_workspace_alignment["contracts"][
                    "export_receipt_reference_preserved"
                ],
                "operator_confirmation_boundary_preserved": (
                    exam_workspace_run_history_workspace_alignment["contracts"][
                        "operator_confirmation_boundary_preserved"
                    ]
                ),
                "history_receipt_hashes_present_contract": exam_workspace_run_history_workspace_alignment[
                    "contracts"
                ]["history_receipt_hashes_present"],
                "history_waiting_mode_no_reviewable_export": exam_workspace_run_history_workspace_alignment[
                    "contracts"
                ]["waiting_mode_no_reviewable_export"],
                "export_review_status": exam_workspace_run_history_alignment["export_review_status"],
                "human_reviewable_independence_evidence": exam_workspace_run_history_alignment[
                    "human_reviewable_independence_evidence"
                ],
                "reflection_evidence_present": exam_workspace_run_history_alignment["reflection_evidence_present"],
                "export_receipt_status": exam_workspace_run_history_alignment["export_receipt_status"],
                "export_receipt_not_cleared": exam_workspace_run_history_alignment["export_receipt_not_cleared"],
                "waiting_run_count": exam_workspace_run_history_alignment["waiting_run_count"],
                "waiting_export_status": exam_workspace_run_history_alignment["waiting_export_status"],
                "release_claim_alignment_human_gates": exam_workspace_run_history_alignment["required_human_gates"],
                "run_claim_linked": (
                    "exam_workspace_run" in exam_workspace_run_history_alignment["required_readiness_check_ids"]
                ),
                "launch_claim_linked": (
                    "exam_workspace_launch" in exam_workspace_run_history_alignment["required_readiness_check_ids"]
                ),
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in exam_workspace_run_history_alignment["required_readiness_check_ids"]
                ),
                "study_session_claim_linked": (
                    "study_session" in exam_workspace_run_history_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in exam_workspace_run_history_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in exam_workspace_run_history_alignment["required_readiness_check_ids"]
                ),
                "evaluation_claim_linked": (
                    "evaluation_packet" in exam_workspace_run_history_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in exam_workspace_run_history_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in exam_workspace_run_history_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in exam_workspace_run_history_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in exam_workspace_run_history_alignment["required_human_gates"]
                ),
                "history_public_safe": exam_workspace_run_history_alignment["contracts"]["history_public_safe"],
                "waiting_history_public_safe": exam_workspace_run_history_alignment["contracts"][
                    "waiting_history_public_safe"
                ],
                "run_history_hash_only_ready": exam_workspace_run_history_alignment["contracts"][
                    "run_history_hash_only_ready"
                ],
                "operator_reflection_and_blockers_preserved": exam_workspace_run_history_alignment["contracts"][
                    "operator_reflection_and_blockers_preserved"
                ],
                "workspace_card_review_gate_linked": exam_workspace_run_history_alignment["contracts"][
                    "workspace_card_review_gate_linked"
                ],
                "export_review_package_human_reviewable": exam_workspace_run_history_alignment["contracts"][
                    "export_review_package_human_reviewable"
                ],
                "export_review_receipt_not_exam_clearance": exam_workspace_run_history_alignment["contracts"][
                    "export_review_receipt_not_exam_clearance"
                ],
                "waiting_history_has_no_reviewable_export": exam_workspace_run_history_alignment["contracts"][
                    "waiting_history_has_no_reviewable_export"
                ],
                "public_outputs_hide_private_history_data": exam_workspace_run_history_alignment["contracts"][
                    "public_outputs_hide_private_history_data"
                ],
                "high_stakes_actions_not_started": exam_workspace_run_history_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "raw_query_returned_blocked": "raw query returned"
                in exam_workspace_run_history_alignment["blocked_claims"],
                "raw_history_returned_blocked": "raw history returned"
                in exam_workspace_run_history_alignment["blocked_claims"],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in exam_workspace_run_history_alignment["blocked_claims"],
                "raw_cell_text_returned_blocked": "raw cell text returned"
                in exam_workspace_run_history_alignment["blocked_claims"],
                "final_solution_acceptance_blocked": "final solution acceptance"
                in exam_workspace_run_history_alignment["blocked_claims"],
                "eigenleistung_percentage_claim_blocked": "Eigenleistung percentage claim"
                in exam_workspace_run_history_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading"
                in exam_workspace_run_history_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring" in exam_workspace_run_history_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in exam_workspace_run_history_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in exam_workspace_run_history_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in exam_workspace_run_history_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance" in exam_workspace_run_history_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "exam_workspace_operator_run",
            "passed": exam_workspace_operator_run_alignment["status"] == "ready"
            and exam_workspace_operator_run_alignment["public_safety_status"] == "pass"
            and exam_workspace_operator_run_alignment["operator_public_safety_status"] == "pass"
            and exam_workspace_operator_run_alignment["repeat_public_safety_status"] == "pass"
            and exam_workspace_operator_run_alignment["exam_deployment_status"] == "not_cleared"
            and exam_workspace_operator_run_alignment["missing_source_card_ids"] == []
            and exam_workspace_operator_run_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": exam_workspace_operator_run_alignment["status"],
                "release_claim_alignment_public_safety_status": exam_workspace_operator_run_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": exam_workspace_operator_run_alignment["schema_version"],
                "release_claim_alignment_section_count": exam_workspace_operator_run_alignment["section_count"],
                "operator_status": exam_workspace_operator_run_alignment["operator_status"],
                "operator_public_safety_status": exam_workspace_operator_run_alignment["operator_public_safety_status"],
                "repeat_status": exam_workspace_operator_run_alignment["repeat_status"],
                "repeat_public_safety_status": exam_workspace_operator_run_alignment["repeat_public_safety_status"],
                "exam_deployment_status": exam_workspace_operator_run_alignment["exam_deployment_status"],
                "view_status": exam_workspace_operator_run_alignment["view_status"],
                "receipt_status": exam_workspace_operator_run_alignment["receipt_status"],
                "receipt_not_cleared": exam_workspace_operator_run_alignment["receipt_not_cleared"],
                "confirmation_status": exam_workspace_operator_run_alignment["confirmation_status"],
                "confirmed_count": exam_workspace_operator_run_alignment["confirmed_count"],
                "write_step_count": exam_workspace_operator_run_alignment["write_step_count"],
                "local_writes_requested": exam_workspace_operator_run_alignment["local_writes_requested"],
                "checkpoint_status": exam_workspace_operator_run_alignment["checkpoint_status"],
                "checkpoint_hash_present": exam_workspace_operator_run_alignment["checkpoint_hash_present"],
                "workspace_status": exam_workspace_operator_run_alignment["workspace_status"],
                "tutor_status": exam_workspace_operator_run_alignment["tutor_status"],
                "study_receipt_status": exam_workspace_operator_run_alignment["study_receipt_status"],
                "workspace_card_status": exam_workspace_operator_run_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": exam_workspace_operator_run_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": exam_workspace_operator_run_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": exam_workspace_operator_run_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": exam_workspace_operator_run_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": exam_workspace_operator_run_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "help_ledger_preview_status": exam_workspace_operator_run_alignment["help_ledger_preview_status"],
                "general_help_ledger_written": exam_workspace_operator_run_alignment["general_help_ledger_written"],
                "exam_ledger_written": exam_workspace_operator_run_alignment["exam_ledger_written"],
                "export_status": exam_workspace_operator_run_alignment["export_status"],
                "export_not_cleared_receipt": exam_workspace_operator_run_alignment["export_not_cleared_receipt"],
                "repeat_checkpoint_status": exam_workspace_operator_run_alignment["repeat_checkpoint_status"],
                "release_claim_alignment_human_gates": exam_workspace_operator_run_alignment["required_human_gates"],
                "launch_claim_linked": (
                    "exam_workspace_launch" in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "run_claim_linked": (
                    "exam_workspace_run" in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "history_claim_linked": (
                    "exam_workspace_run_history"
                    in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "notebook_checkpoint_claim_linked": (
                    "notebook_checkpoint" in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "study_session_claim_linked": (
                    "study_session" in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in exam_workspace_operator_run_alignment["required_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in exam_workspace_operator_run_alignment["required_human_gates"]
                ),
                "datenschutz_gate_linked": (
                    "datenschutz_review_required_before_real_pilot"
                    in exam_workspace_operator_run_alignment["required_human_gates"]
                ),
                "written_clearance_gate_linked": (
                    "written_university_clearance_required_before_exam_use"
                    in exam_workspace_operator_run_alignment["required_human_gates"]
                ),
                "operator_ready_public_safe": exam_workspace_operator_run_alignment["contracts"][
                    "operator_ready_public_safe"
                ],
                "repeat_boundary_public_safe": exam_workspace_operator_run_alignment["contracts"][
                    "repeat_boundary_public_safe"
                ],
                "start_view_hash_only_ready": exam_workspace_operator_run_alignment["contracts"][
                    "start_view_hash_only_ready"
                ],
                "workspace_card_start_view_gate_linked": exam_workspace_operator_run_alignment["contracts"][
                    "workspace_card_start_view_gate_linked"
                ],
                "individual_confirmations_default_to_dry_run": exam_workspace_operator_run_alignment["contracts"][
                    "individual_confirmations_default_to_dry_run"
                ],
                "receipt_and_export_not_exam_clearance": exam_workspace_operator_run_alignment["contracts"][
                    "receipt_and_export_not_exam_clearance"
                ],
                "help_ledger_preview_not_written": exam_workspace_operator_run_alignment["contracts"][
                    "help_ledger_preview_not_written"
                ],
                "repeat_task_stops_operator_start": exam_workspace_operator_run_alignment["contracts"][
                    "repeat_task_stops_operator_start"
                ],
                "markdown_boundary_mentions_no_high_stakes_claims": exam_workspace_operator_run_alignment[
                    "contracts"
                ]["markdown_boundary_mentions_no_high_stakes_claims"],
                "public_outputs_hide_private_operator_data": exam_workspace_operator_run_alignment["contracts"][
                    "public_outputs_hide_private_operator_data"
                ],
                "high_stakes_actions_not_started": exam_workspace_operator_run_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "raw_query_returned_blocked": "raw query returned"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "raw_confirmation_text_returned_blocked": "raw confirmation text returned"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "unconfirmed_local_write_blocked": "unconfirmed local write"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "raw_cell_text_returned_blocked": "raw cell text returned"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "final_solution_acceptance_blocked": "final solution acceptance"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "eigenleistung_percentage_claim_blocked": "Eigenleistung percentage claim"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring" in exam_workspace_operator_run_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in exam_workspace_operator_run_alignment["blocked_claims"],
                "cloud_processing_blocked": "cloud processing" in exam_workspace_operator_run_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment" in exam_workspace_operator_run_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance" in exam_workspace_operator_run_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "exam_workspace_session_console",
            "passed": exam_workspace_session_console_alignment["status"] == "ready"
            and exam_workspace_session_console_alignment["public_safety_status"] == "pass"
            and exam_workspace_session_console_alignment["console_public_safety_status"] == "pass"
            and exam_workspace_session_console_alignment["repeat_public_safety_status"] == "pass"
            and exam_workspace_session_console_alignment["exam_deployment_status"] == "not_cleared"
            and exam_workspace_session_console_alignment["missing_source_card_ids"] == []
            and exam_workspace_session_console_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": exam_workspace_session_console_alignment["status"],
                "release_claim_alignment_public_safety_status": exam_workspace_session_console_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": exam_workspace_session_console_alignment[
                    "schema_version"
                ],
                "release_claim_alignment_section_count": exam_workspace_session_console_alignment["section_count"],
                "console_status": exam_workspace_session_console_alignment["console_status"],
                "console_public_safety_status": exam_workspace_session_console_alignment[
                    "console_public_safety_status"
                ],
                "repeat_status": exam_workspace_session_console_alignment["repeat_status"],
                "repeat_public_safety_status": exam_workspace_session_console_alignment[
                    "repeat_public_safety_status"
                ],
                "exam_deployment_status": exam_workspace_session_console_alignment["exam_deployment_status"],
                "session_console_status": exam_workspace_session_console_alignment["session_console_status"],
                "selected_skill_tag": exam_workspace_session_console_alignment["selected_skill_tag"],
                "workspace_status": exam_workspace_session_console_alignment["workspace_status"],
                "operator_status": exam_workspace_session_console_alignment["operator_status"],
                "operator_receipt_id_present": bool(exam_workspace_session_console_alignment["operator_receipt_id"]),
                "receipt_status": exam_workspace_session_console_alignment["receipt_status"],
                "receipt_not_cleared": exam_workspace_session_console_alignment["receipt_not_cleared"],
                "receipt_hash_present": exam_workspace_session_console_alignment["receipt_hash_present"],
                "checkpoint_status": exam_workspace_session_console_alignment["checkpoint_status"],
                "checkpoint_hash_present": exam_workspace_session_console_alignment["checkpoint_hash_present"],
                "tutor_status": exam_workspace_session_console_alignment["tutor_status"],
                "study_receipt_status": exam_workspace_session_console_alignment["study_receipt_status"],
                "help_ledger_preview_status": exam_workspace_session_console_alignment["help_ledger_preview_status"],
                "export_status": exam_workspace_session_console_alignment["export_status"],
                "export_not_cleared_receipt": exam_workspace_session_console_alignment["export_not_cleared_receipt"],
                "confirmation_status": exam_workspace_session_console_alignment["confirmation_status"],
                "confirmed_count": exam_workspace_session_console_alignment["confirmed_count"],
                "write_step_count": exam_workspace_session_console_alignment["write_step_count"],
                "local_writes_requested": exam_workspace_session_console_alignment["local_writes_requested"],
                "reflection_status": exam_workspace_session_console_alignment["reflection_status"],
                "workspace_card_status": exam_workspace_session_console_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": exam_workspace_session_console_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_help_ledger_status": exam_workspace_session_console_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_ready_for_operator_prefill": exam_workspace_session_console_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_hash_present": exam_workspace_session_console_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": exam_workspace_session_console_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "repeat_checkpoint_status": exam_workspace_session_console_alignment["repeat_checkpoint_status"],
                "release_claim_alignment_human_gates": exam_workspace_session_console_alignment[
                    "required_human_gates"
                ],
                "operator_run_claim_linked": (
                    "exam_workspace_operator_run"
                    in exam_workspace_session_console_alignment["required_readiness_check_ids"]
                ),
                "run_history_claim_linked": (
                    "exam_workspace_run_history"
                    in exam_workspace_session_console_alignment["required_readiness_check_ids"]
                ),
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in exam_workspace_session_console_alignment["required_readiness_check_ids"]
                ),
                "study_session_claim_linked": (
                    "study_session" in exam_workspace_session_console_alignment["required_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in exam_workspace_session_console_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in exam_workspace_session_console_alignment["required_readiness_check_ids"]
                ),
                "evaluation_packet_claim_linked": (
                    "evaluation_packet" in exam_workspace_session_console_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in exam_workspace_session_console_alignment["required_readiness_check_ids"]
                ),
                "console_public_safe": exam_workspace_session_console_alignment["contracts"]["console_public_safe"],
                "repeat_public_safe": exam_workspace_session_console_alignment["contracts"]["repeat_public_safe"],
                "session_console_receipt_hash_only_ready": exam_workspace_session_console_alignment["contracts"][
                    "session_console_receipt_hash_only_ready"
                ],
                "operator_run_receipt_linked": exam_workspace_session_console_alignment["contracts"][
                    "operator_run_receipt_linked"
                ],
                "workspace_card_and_reflection_preserved": exam_workspace_session_console_alignment["contracts"][
                    "workspace_card_and_reflection_preserved"
                ],
                "workspace_card_readiness_gate_contract": exam_workspace_session_console_alignment["contracts"][
                    "workspace_card_readiness_gate_linked"
                ],
                "repeat_task_blocks_console_ready": exam_workspace_session_console_alignment["contracts"][
                    "repeat_task_blocks_console_ready"
                ],
                "public_outputs_hide_private_console_data": exam_workspace_session_console_alignment["contracts"][
                    "public_outputs_hide_private_console_data"
                ],
                "high_stakes_actions_not_started": exam_workspace_session_console_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "not_cleared_receipt_present": exam_workspace_session_console_alignment["contracts"][
                    "not_cleared_receipt_present"
                ],
                "raw_run_history_returned_blocked": "raw run history returned"
                in exam_workspace_session_console_alignment["blocked_claims"],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in exam_workspace_session_console_alignment["blocked_claims"],
                "unconfirmed_local_write_blocked": "unconfirmed local write"
                in exam_workspace_session_console_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading"
                in exam_workspace_session_console_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring" in exam_workspace_session_console_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in exam_workspace_session_console_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in exam_workspace_session_console_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance" in exam_workspace_session_console_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "python_exam_local_cycle_start_packet",
            "passed": python_exam_local_cycle_start_packet_alignment["status"] == "ready"
            and python_exam_local_cycle_start_packet_alignment["public_safety_status"] == "pass"
            and python_exam_local_cycle_start_packet_alignment["open_packet_public_safety_status"] == "pass"
            and python_exam_local_cycle_start_packet_alignment["confirmed_packet_public_safety_status"] == "pass"
            and python_exam_local_cycle_start_packet_alignment["exam_deployment_status"] == "not_cleared"
            and python_exam_local_cycle_start_packet_alignment["missing_source_card_ids"] == []
            and python_exam_local_cycle_start_packet_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": python_exam_local_cycle_start_packet_alignment["status"],
                "release_claim_alignment_public_safety_status": python_exam_local_cycle_start_packet_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": python_exam_local_cycle_start_packet_alignment[
                    "schema_version"
                ],
                "release_claim_alignment_section_count": python_exam_local_cycle_start_packet_alignment[
                    "section_count"
                ],
                "open_packet_status": python_exam_local_cycle_start_packet_alignment["open_packet_status"],
                "open_packet_public_safety_status": python_exam_local_cycle_start_packet_alignment[
                    "open_packet_public_safety_status"
                ],
                "confirmed_packet_status": python_exam_local_cycle_start_packet_alignment["confirmed_packet_status"],
                "confirmed_packet_public_safety_status": python_exam_local_cycle_start_packet_alignment[
                    "confirmed_packet_public_safety_status"
                ],
                "exam_deployment_status": python_exam_local_cycle_start_packet_alignment["exam_deployment_status"],
                "selected_skill_tag": python_exam_local_cycle_start_packet_alignment["selected_skill_tag"],
                "open_start_status": python_exam_local_cycle_start_packet_alignment["open_start_status"],
                "open_blocked_reason": python_exam_local_cycle_start_packet_alignment["open_blocked_reason"],
                "open_confirmation_count": python_exam_local_cycle_start_packet_alignment["open_confirmation_count"],
                "confirmed_start_status": python_exam_local_cycle_start_packet_alignment["confirmed_start_status"],
                "confirmed_count": python_exam_local_cycle_start_packet_alignment["confirmed_count"],
                "task_hash_present": python_exam_local_cycle_start_packet_alignment["task_hash_present"],
                "checkpoint_hash_present": python_exam_local_cycle_start_packet_alignment["checkpoint_hash_present"],
                "source_card_ids": python_exam_local_cycle_start_packet_alignment["source_card_ids"],
                "source_anchor_count": python_exam_local_cycle_start_packet_alignment["source_anchor_count"],
                "help_level": python_exam_local_cycle_start_packet_alignment["help_level"],
                "gate_receipt_id_present": python_exam_local_cycle_start_packet_alignment["gate_receipt_id_present"],
                "decision_receipt_id_present": python_exam_local_cycle_start_packet_alignment[
                    "decision_receipt_id_present"
                ],
                "start_receipt_status": python_exam_local_cycle_start_packet_alignment["start_receipt_status"],
                "start_receipt_hash_present": python_exam_local_cycle_start_packet_alignment[
                    "start_receipt_hash_present"
                ],
                "not_cleared_receipt": python_exam_local_cycle_start_packet_alignment["not_cleared_receipt"],
                "safe_cycle_console_status": python_exam_local_cycle_start_packet_alignment[
                    "safe_cycle_console_status"
                ],
                "operator_gate_status": python_exam_local_cycle_start_packet_alignment["operator_gate_status"],
                "decision_receipt_status": python_exam_local_cycle_start_packet_alignment["decision_receipt_status"],
                "dry_run_default": python_exam_local_cycle_start_packet_alignment["dry_run_default"],
                "local_writes_requested": python_exam_local_cycle_start_packet_alignment["local_writes_requested"],
                "local_execution_started": python_exam_local_cycle_start_packet_alignment["local_execution_started"],
                "release_claim_alignment_human_gates": python_exam_local_cycle_start_packet_alignment[
                    "required_human_gates"
                ],
                "session_console_claim_linked": (
                    "exam_workspace_session_console"
                    in python_exam_local_cycle_start_packet_alignment["required_readiness_check_ids"]
                ),
                "operator_run_claim_linked": (
                    "exam_workspace_operator_run"
                    in python_exam_local_cycle_start_packet_alignment["required_readiness_check_ids"]
                ),
                "study_session_claim_linked": (
                    "study_session"
                    in python_exam_local_cycle_start_packet_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in python_exam_local_cycle_start_packet_alignment["required_readiness_check_ids"]
                ),
                "evaluation_packet_claim_linked": (
                    "evaluation_packet"
                    in python_exam_local_cycle_start_packet_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in python_exam_local_cycle_start_packet_alignment["required_readiness_check_ids"]
                ),
                "open_packet_public_safe": python_exam_local_cycle_start_packet_alignment["contracts"][
                    "open_packet_public_safe"
                ],
                "confirmed_packet_public_safe": python_exam_local_cycle_start_packet_alignment["contracts"][
                    "confirmed_packet_public_safe"
                ],
                "start_packet_metadata_only_ready": python_exam_local_cycle_start_packet_alignment["contracts"][
                    "start_packet_metadata_only_ready"
                ],
                "open_confirmations_block_local_cycle": python_exam_local_cycle_start_packet_alignment["contracts"][
                    "open_confirmations_block_local_cycle"
                ],
                "confirmed_packet_still_no_execution": python_exam_local_cycle_start_packet_alignment["contracts"][
                    "confirmed_packet_still_no_execution"
                ],
                "source_gate_decision_receipts_linked": python_exam_local_cycle_start_packet_alignment["contracts"][
                    "source_gate_decision_receipts_linked"
                ],
                "public_outputs_hide_private_start_packet_data": python_exam_local_cycle_start_packet_alignment[
                    "contracts"
                ]["public_outputs_hide_private_start_packet_data"],
                "high_stakes_actions_not_started": python_exam_local_cycle_start_packet_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "not_cleared_receipt_present": python_exam_local_cycle_start_packet_alignment["contracts"][
                    "not_cleared_receipt_present"
                ],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in python_exam_local_cycle_start_packet_alignment["blocked_claims"],
                "unconfirmed_local_write_blocked": "unconfirmed local write"
                in python_exam_local_cycle_start_packet_alignment["blocked_claims"],
                "local_execution_started_blocked": "local execution started"
                in python_exam_local_cycle_start_packet_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading"
                in python_exam_local_cycle_start_packet_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring" in python_exam_local_cycle_start_packet_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in python_exam_local_cycle_start_packet_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in python_exam_local_cycle_start_packet_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance"
                in python_exam_local_cycle_start_packet_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "python_exam_local_cycle_readiness_review",
            "passed": python_exam_local_cycle_readiness_review_alignment["status"] == "ready"
            and python_exam_local_cycle_readiness_review_alignment["public_safety_status"] == "pass"
            and python_exam_local_cycle_readiness_review_alignment["open_review_public_safety_status"] == "pass"
            and python_exam_local_cycle_readiness_review_alignment["confirmed_review_public_safety_status"] == "pass"
            and python_exam_local_cycle_readiness_review_alignment["missing_review_public_safety_status"] == "pass"
            and python_exam_local_cycle_readiness_review_alignment["exam_deployment_status"] == "not_cleared"
            and python_exam_local_cycle_readiness_review_alignment["missing_source_card_ids"] == []
            and python_exam_local_cycle_readiness_review_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": python_exam_local_cycle_readiness_review_alignment["status"],
                "release_claim_alignment_public_safety_status": python_exam_local_cycle_readiness_review_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": python_exam_local_cycle_readiness_review_alignment[
                    "schema_version"
                ],
                "release_claim_alignment_section_count": python_exam_local_cycle_readiness_review_alignment[
                    "section_count"
                ],
                "open_review_status": python_exam_local_cycle_readiness_review_alignment["open_review_status"],
                "open_review_public_safety_status": python_exam_local_cycle_readiness_review_alignment[
                    "open_review_public_safety_status"
                ],
                "confirmed_review_status": python_exam_local_cycle_readiness_review_alignment[
                    "confirmed_review_status"
                ],
                "confirmed_review_public_safety_status": python_exam_local_cycle_readiness_review_alignment[
                    "confirmed_review_public_safety_status"
                ],
                "missing_review_status": python_exam_local_cycle_readiness_review_alignment["missing_review_status"],
                "missing_review_public_safety_status": python_exam_local_cycle_readiness_review_alignment[
                    "missing_review_public_safety_status"
                ],
                "exam_deployment_status": python_exam_local_cycle_readiness_review_alignment["exam_deployment_status"],
                "selected_skill_tag": python_exam_local_cycle_readiness_review_alignment["selected_skill_tag"],
                "open_recommendation": python_exam_local_cycle_readiness_review_alignment["open_recommendation"],
                "open_recommendation_reason": python_exam_local_cycle_readiness_review_alignment[
                    "open_recommendation_reason"
                ],
                "open_start_status": python_exam_local_cycle_readiness_review_alignment["open_start_status"],
                "open_confirmation_count": python_exam_local_cycle_readiness_review_alignment[
                    "open_confirmation_count"
                ],
                "confirmed_recommendation": python_exam_local_cycle_readiness_review_alignment[
                    "confirmed_recommendation"
                ],
                "confirmed_count": python_exam_local_cycle_readiness_review_alignment["confirmed_count"],
                "missing_recommendation": python_exam_local_cycle_readiness_review_alignment["missing_recommendation"],
                "missing_recommendation_reason": python_exam_local_cycle_readiness_review_alignment[
                    "missing_recommendation_reason"
                ],
                "packet_present": python_exam_local_cycle_readiness_review_alignment["packet_present"],
                "hash_metadata_complete": python_exam_local_cycle_readiness_review_alignment[
                    "hash_metadata_complete"
                ],
                "task_hash_present": python_exam_local_cycle_readiness_review_alignment["task_hash_present"],
                "checkpoint_hash_present": python_exam_local_cycle_readiness_review_alignment[
                    "checkpoint_hash_present"
                ],
                "gate_receipt_hash_present": python_exam_local_cycle_readiness_review_alignment[
                    "gate_receipt_hash_present"
                ],
                "decision_receipt_hash_present": python_exam_local_cycle_readiness_review_alignment[
                    "decision_receipt_hash_present"
                ],
                "start_receipt_hash_present": python_exam_local_cycle_readiness_review_alignment[
                    "start_receipt_hash_present"
                ],
                "review_receipt_hash_present": python_exam_local_cycle_readiness_review_alignment[
                    "review_receipt_hash_present"
                ],
                "source_card_ids": python_exam_local_cycle_readiness_review_alignment["source_card_ids"],
                "source_anchor_count": python_exam_local_cycle_readiness_review_alignment["source_anchor_count"],
                "help_level": python_exam_local_cycle_readiness_review_alignment["help_level"],
                "dry_run_default": python_exam_local_cycle_readiness_review_alignment["dry_run_default"],
                "local_writes_requested": python_exam_local_cycle_readiness_review_alignment[
                    "local_writes_requested"
                ],
                "local_execution_started": python_exam_local_cycle_readiness_review_alignment[
                    "local_execution_started"
                ],
                "not_cleared_receipt": python_exam_local_cycle_readiness_review_alignment[
                    "not_cleared_receipt"
                ],
                "release_claim_alignment_human_gates": python_exam_local_cycle_readiness_review_alignment[
                    "required_human_gates"
                ],
                "start_packet_claim_linked": (
                    "python_exam_local_cycle_start_packet"
                    in python_exam_local_cycle_readiness_review_alignment["required_readiness_check_ids"]
                ),
                "session_console_claim_linked": (
                    "exam_workspace_session_console"
                    in python_exam_local_cycle_readiness_review_alignment["required_readiness_check_ids"]
                ),
                "study_session_claim_linked": (
                    "study_session"
                    in python_exam_local_cycle_readiness_review_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in python_exam_local_cycle_readiness_review_alignment["required_readiness_check_ids"]
                ),
                "evaluation_packet_claim_linked": (
                    "evaluation_packet"
                    in python_exam_local_cycle_readiness_review_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary"
                    in python_exam_local_cycle_readiness_review_alignment["required_readiness_check_ids"]
                ),
                "open_review_public_safe": python_exam_local_cycle_readiness_review_alignment["contracts"][
                    "open_review_public_safe"
                ],
                "confirmed_review_public_safe": python_exam_local_cycle_readiness_review_alignment["contracts"][
                    "confirmed_review_public_safe"
                ],
                "missing_review_public_safe": python_exam_local_cycle_readiness_review_alignment["contracts"][
                    "missing_review_public_safe"
                ],
                "open_confirmation_review_recommendation_ready": python_exam_local_cycle_readiness_review_alignment[
                    "contracts"
                ]["open_confirmation_review_recommendation_ready"],
                "confirmed_review_manual_only_ready": python_exam_local_cycle_readiness_review_alignment["contracts"][
                    "confirmed_review_manual_only_ready"
                ],
                "missing_start_packet_keeps_blocked": python_exam_local_cycle_readiness_review_alignment["contracts"][
                    "missing_start_packet_keeps_blocked"
                ],
                "hash_metadata_and_source_cards_preserved": python_exam_local_cycle_readiness_review_alignment[
                    "contracts"
                ]["hash_metadata_and_source_cards_preserved"],
                "public_outputs_hide_private_review_data": python_exam_local_cycle_readiness_review_alignment[
                    "contracts"
                ]["public_outputs_hide_private_review_data"],
                "high_stakes_actions_not_started": python_exam_local_cycle_readiness_review_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "not_cleared_receipt_present": python_exam_local_cycle_readiness_review_alignment["contracts"][
                    "not_cleared_receipt_present"
                ],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in python_exam_local_cycle_readiness_review_alignment["blocked_claims"],
                "local_write_requested_blocked": "local write requested"
                in python_exam_local_cycle_readiness_review_alignment["blocked_claims"],
                "local_execution_started_blocked": "local execution started"
                in python_exam_local_cycle_readiness_review_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading"
                in python_exam_local_cycle_readiness_review_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring"
                in python_exam_local_cycle_readiness_review_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in python_exam_local_cycle_readiness_review_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in python_exam_local_cycle_readiness_review_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance"
                in python_exam_local_cycle_readiness_review_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "python_exam_local_cycle_readiness_handoff",
            "passed": python_exam_local_cycle_readiness_handoff_alignment["status"] == "ready"
            and python_exam_local_cycle_readiness_handoff_alignment["public_safety_status"] == "pass"
            and python_exam_local_cycle_readiness_handoff_alignment["ready_handoff_public_safety_status"] == "pass"
            and python_exam_local_cycle_readiness_handoff_alignment["attention_handoff_public_safety_status"] == "pass"
            and python_exam_local_cycle_readiness_handoff_alignment["exam_deployment_status"] == "not_cleared"
            and python_exam_local_cycle_readiness_handoff_alignment["missing_source_card_ids"] == []
            and python_exam_local_cycle_readiness_handoff_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": python_exam_local_cycle_readiness_handoff_alignment["status"],
                "release_claim_alignment_public_safety_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "schema_version"
                ],
                "release_claim_alignment_section_count": python_exam_local_cycle_readiness_handoff_alignment[
                    "section_count"
                ],
                "ready_handoff_status": python_exam_local_cycle_readiness_handoff_alignment["ready_handoff_status"],
                "ready_handoff_public_safety_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "ready_handoff_public_safety_status"
                ],
                "attention_handoff_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "attention_handoff_status"
                ],
                "attention_handoff_public_safety_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "attention_handoff_public_safety_status"
                ],
                "exam_deployment_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "exam_deployment_status"
                ],
                "selected_skill_tag": python_exam_local_cycle_readiness_handoff_alignment["selected_skill_tag"],
                "recommendation": python_exam_local_cycle_readiness_handoff_alignment["recommendation"],
                "recommendation_reason": python_exam_local_cycle_readiness_handoff_alignment[
                    "recommendation_reason"
                ],
                "ready_for_operator_prefill": python_exam_local_cycle_readiness_handoff_alignment[
                    "ready_for_operator_prefill"
                ],
                "operator_run_endpoint": python_exam_local_cycle_readiness_handoff_alignment["operator_run_endpoint"],
                "operator_run_method": python_exam_local_cycle_readiness_handoff_alignment["operator_run_method"],
                "operator_prefill_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "operator_prefill_status"
                ],
                "operator_prefill_hash_present": python_exam_local_cycle_readiness_handoff_alignment[
                    "operator_prefill_hash_present"
                ],
                "manual_handoff_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "manual_handoff_status"
                ],
                "manual_next_operator_action": python_exam_local_cycle_readiness_handoff_alignment[
                    "manual_next_operator_action"
                ],
                "attention_prefill_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "attention_prefill_status"
                ],
                "attention_manual_handoff_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "attention_manual_handoff_status"
                ],
                "task_hash_present": python_exam_local_cycle_readiness_handoff_alignment["task_hash_present"],
                "checkpoint_hash_present": python_exam_local_cycle_readiness_handoff_alignment[
                    "checkpoint_hash_present"
                ],
                "source_card_ids": python_exam_local_cycle_readiness_handoff_alignment["source_card_ids"],
                "source_anchor_count": python_exam_local_cycle_readiness_handoff_alignment["source_anchor_count"],
                "help_level": python_exam_local_cycle_readiness_handoff_alignment["help_level"],
                "handoff_receipt_status": python_exam_local_cycle_readiness_handoff_alignment[
                    "handoff_receipt_status"
                ],
                "handoff_receipt_hash_present": python_exam_local_cycle_readiness_handoff_alignment[
                    "handoff_receipt_hash_present"
                ],
                "not_cleared_receipt": python_exam_local_cycle_readiness_handoff_alignment[
                    "not_cleared_receipt"
                ],
                "dry_run_default": python_exam_local_cycle_readiness_handoff_alignment["dry_run_default"],
                "local_writes_requested": python_exam_local_cycle_readiness_handoff_alignment[
                    "local_writes_requested"
                ],
                "local_execution_started": python_exam_local_cycle_readiness_handoff_alignment[
                    "local_execution_started"
                ],
                "release_claim_alignment_human_gates": python_exam_local_cycle_readiness_handoff_alignment[
                    "required_human_gates"
                ],
                "readiness_review_claim_linked": (
                    "python_exam_local_cycle_readiness_review"
                    in python_exam_local_cycle_readiness_handoff_alignment["required_readiness_check_ids"]
                ),
                "start_packet_claim_linked": (
                    "python_exam_local_cycle_start_packet"
                    in python_exam_local_cycle_readiness_handoff_alignment["required_readiness_check_ids"]
                ),
                "operator_run_claim_linked": (
                    "exam_workspace_operator_run"
                    in python_exam_local_cycle_readiness_handoff_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in python_exam_local_cycle_readiness_handoff_alignment["required_readiness_check_ids"]
                ),
                "evaluation_packet_claim_linked": (
                    "evaluation_packet"
                    in python_exam_local_cycle_readiness_handoff_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in python_exam_local_cycle_readiness_handoff_alignment["required_readiness_check_ids"]
                ),
                "ready_handoff_public_safe": python_exam_local_cycle_readiness_handoff_alignment["contracts"][
                    "ready_handoff_public_safe"
                ],
                "attention_handoff_public_safe": python_exam_local_cycle_readiness_handoff_alignment["contracts"][
                    "attention_handoff_public_safe"
                ],
                "operator_prefill_ready_metadata_only": python_exam_local_cycle_readiness_handoff_alignment[
                    "contracts"
                ]["operator_prefill_ready_metadata_only"],
                "manual_handoff_ready_not_execution": python_exam_local_cycle_readiness_handoff_alignment[
                    "contracts"
                ]["manual_handoff_ready_not_execution"],
                "attention_handoff_stays_blocked": python_exam_local_cycle_readiness_handoff_alignment["contracts"][
                    "attention_handoff_stays_blocked"
                ],
                "hash_metadata_and_source_cards_preserved": python_exam_local_cycle_readiness_handoff_alignment[
                    "contracts"
                ]["hash_metadata_and_source_cards_preserved"],
                "public_outputs_hide_private_handoff_data": python_exam_local_cycle_readiness_handoff_alignment[
                    "contracts"
                ]["public_outputs_hide_private_handoff_data"],
                "high_stakes_actions_not_started": python_exam_local_cycle_readiness_handoff_alignment["contracts"][
                    "high_stakes_actions_not_started"
                ],
                "not_cleared_receipt_present": python_exam_local_cycle_readiness_handoff_alignment["contracts"][
                    "not_cleared_receipt_present"
                ],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in python_exam_local_cycle_readiness_handoff_alignment["blocked_claims"],
                "local_write_requested_blocked": "local write requested"
                in python_exam_local_cycle_readiness_handoff_alignment["blocked_claims"],
                "local_execution_started_blocked": "local execution started"
                in python_exam_local_cycle_readiness_handoff_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading"
                in python_exam_local_cycle_readiness_handoff_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring"
                in python_exam_local_cycle_readiness_handoff_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in python_exam_local_cycle_readiness_handoff_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in python_exam_local_cycle_readiness_handoff_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance"
                in python_exam_local_cycle_readiness_handoff_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "python_exam_local_cycle_operator_workspace_card",
            "passed": python_exam_local_cycle_operator_workspace_card_alignment["status"] == "ready"
            and python_exam_local_cycle_operator_workspace_card_alignment["public_safety_status"] == "pass"
            and python_exam_local_cycle_operator_workspace_card_alignment["ready_card_public_safety_status"] == "pass"
            and python_exam_local_cycle_operator_workspace_card_alignment["attention_card_public_safety_status"] == "pass"
            and python_exam_local_cycle_operator_workspace_card_alignment["exam_deployment_status"] == "not_cleared"
            and python_exam_local_cycle_operator_workspace_card_alignment["missing_source_card_ids"] == []
            and python_exam_local_cycle_operator_workspace_card_alignment["failed_contract_ids"] == [],
            "evidence": {
                "release_claim_alignment_status": python_exam_local_cycle_operator_workspace_card_alignment["status"],
                "release_claim_alignment_public_safety_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "public_safety_status"
                ],
                "release_claim_alignment_contract_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "schema_version"
                ],
                "release_claim_alignment_section_count": python_exam_local_cycle_operator_workspace_card_alignment[
                    "section_count"
                ],
                "ready_card_status": python_exam_local_cycle_operator_workspace_card_alignment["ready_card_status"],
                "ready_card_public_safety_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "ready_card_public_safety_status"
                ],
                "attention_card_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "attention_card_status"
                ],
                "attention_card_public_safety_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "attention_card_public_safety_status"
                ],
                "exam_deployment_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "exam_deployment_status"
                ],
                "selected_skill_tag": python_exam_local_cycle_operator_workspace_card_alignment["selected_skill_tag"],
                "recommendation": python_exam_local_cycle_operator_workspace_card_alignment["recommendation"],
                "recommendation_reason": python_exam_local_cycle_operator_workspace_card_alignment[
                    "recommendation_reason"
                ],
                "ready_for_operator_prefill": python_exam_local_cycle_operator_workspace_card_alignment[
                    "ready_for_operator_prefill"
                ],
                "help_ledger_preview_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "help_ledger_preview_status"
                ],
                "help_ledger_preview_hash_present": python_exam_local_cycle_operator_workspace_card_alignment[
                    "help_ledger_preview_hash_present"
                ],
                "operator_prefill_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "operator_prefill_status"
                ],
                "operator_prefill_hash_present": python_exam_local_cycle_operator_workspace_card_alignment[
                    "operator_prefill_hash_present"
                ],
                "manual_handoff_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "manual_handoff_status"
                ],
                "manual_next_operator_action": python_exam_local_cycle_operator_workspace_card_alignment[
                    "manual_next_operator_action"
                ],
                "attention_help_ledger_preview_status": python_exam_local_cycle_operator_workspace_card_alignment[
                    "attention_help_ledger_preview_status"
                ],
                "task_hash_present": python_exam_local_cycle_operator_workspace_card_alignment["task_hash_present"],
                "checkpoint_hash_present": python_exam_local_cycle_operator_workspace_card_alignment[
                    "checkpoint_hash_present"
                ],
                "source_card_ids": python_exam_local_cycle_operator_workspace_card_alignment["source_card_ids"],
                "source_anchor_count": python_exam_local_cycle_operator_workspace_card_alignment["source_anchor_count"],
                "help_level": python_exam_local_cycle_operator_workspace_card_alignment["help_level"],
                "dry_run_default": python_exam_local_cycle_operator_workspace_card_alignment["dry_run_default"],
                "local_writes_requested": python_exam_local_cycle_operator_workspace_card_alignment[
                    "local_writes_requested"
                ],
                "local_execution_started": python_exam_local_cycle_operator_workspace_card_alignment[
                    "local_execution_started"
                ],
                "not_cleared_receipt": python_exam_local_cycle_operator_workspace_card_alignment[
                    "not_cleared_receipt"
                ],
                "release_claim_alignment_human_gates": python_exam_local_cycle_operator_workspace_card_alignment[
                    "required_human_gates"
                ],
                "readiness_handoff_claim_linked": (
                    "python_exam_local_cycle_readiness_handoff"
                    in python_exam_local_cycle_operator_workspace_card_alignment["required_readiness_check_ids"]
                ),
                "readiness_review_claim_linked": (
                    "python_exam_local_cycle_readiness_review"
                    in python_exam_local_cycle_operator_workspace_card_alignment["required_readiness_check_ids"]
                ),
                "start_packet_claim_linked": (
                    "python_exam_local_cycle_start_packet"
                    in python_exam_local_cycle_operator_workspace_card_alignment["required_readiness_check_ids"]
                ),
                "operator_run_claim_linked": (
                    "exam_workspace_operator_run"
                    in python_exam_local_cycle_operator_workspace_card_alignment["required_readiness_check_ids"]
                ),
                "external_decision_state_claim_linked": (
                    "external_decision_state"
                    in python_exam_local_cycle_operator_workspace_card_alignment["required_readiness_check_ids"]
                ),
                "evaluation_packet_claim_linked": (
                    "evaluation_packet"
                    in python_exam_local_cycle_operator_workspace_card_alignment["required_readiness_check_ids"]
                ),
                "exam_boundary_claim_linked": (
                    "exam_boundary" in python_exam_local_cycle_operator_workspace_card_alignment["required_readiness_check_ids"]
                ),
                "ready_card_public_safe": python_exam_local_cycle_operator_workspace_card_alignment["contracts"][
                    "ready_card_public_safe"
                ],
                "attention_card_public_safe": python_exam_local_cycle_operator_workspace_card_alignment["contracts"][
                    "attention_card_public_safe"
                ],
                "workspace_card_ready_metadata_only": python_exam_local_cycle_operator_workspace_card_alignment[
                    "contracts"
                ]["workspace_card_ready_metadata_only"],
                "operator_prefill_and_manual_handoff_linked": python_exam_local_cycle_operator_workspace_card_alignment[
                    "contracts"
                ]["operator_prefill_and_manual_handoff_linked"],
                "attention_card_stays_blocked": python_exam_local_cycle_operator_workspace_card_alignment[
                    "contracts"
                ]["attention_card_stays_blocked"],
                "hash_metadata_and_source_cards_preserved": python_exam_local_cycle_operator_workspace_card_alignment[
                    "contracts"
                ]["hash_metadata_and_source_cards_preserved"],
                "public_outputs_hide_private_workspace_card_data": python_exam_local_cycle_operator_workspace_card_alignment[
                    "contracts"
                ]["public_outputs_hide_private_workspace_card_data"],
                "high_stakes_actions_not_started": python_exam_local_cycle_operator_workspace_card_alignment[
                    "contracts"
                ]["high_stakes_actions_not_started"],
                "not_cleared_receipt_present": python_exam_local_cycle_operator_workspace_card_alignment["contracts"][
                    "not_cleared_receipt_present"
                ],
                "no_local_execution_or_write": python_exam_local_cycle_operator_workspace_card_alignment["contracts"][
                    "no_local_execution_or_write"
                ],
                "raw_notebook_code_returned_blocked": "raw notebook code returned"
                in python_exam_local_cycle_operator_workspace_card_alignment["blocked_claims"],
                "local_write_requested_blocked": "local write requested"
                in python_exam_local_cycle_operator_workspace_card_alignment["blocked_claims"],
                "local_execution_started_blocked": "local execution started"
                in python_exam_local_cycle_operator_workspace_card_alignment["blocked_claims"],
                "automatic_grading_blocked": "automatic grading"
                in python_exam_local_cycle_operator_workspace_card_alignment["blocked_claims"],
                "proctoring_blocked": "proctoring"
                in python_exam_local_cycle_operator_workspace_card_alignment["blocked_claims"],
                "ki_detection_evidence_blocked": "KI-detection evidence"
                in python_exam_local_cycle_operator_workspace_card_alignment["blocked_claims"],
                "exam_deployment_blocked": "exam deployment"
                in python_exam_local_cycle_operator_workspace_card_alignment["blocked_claims"],
                "exam_clearance_blocked": "exam clearance"
                in python_exam_local_cycle_operator_workspace_card_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "notebook_template",
            "passed": notebook["audit"]["status"] == "pass"
            and notebook["handoff_claim_alignment"]["status"] == "ready"
            and notebook["handoff_claim_alignment"]["public_safety_status"] == "pass"
            and notebook["handoff_claim_alignment"]["practice_only"] is True
            and notebook["handoff_claim_alignment"]["local_only"] is True
            and notebook["handoff_claim_alignment"]["public_summary_only"] is True
            and notebook["handoff_claim_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and notebook["handoff_claim_alignment"]["missing_release_review_board_claim_human_gates"] == [],
            "evidence": {
                **notebook["audit"],
                "handoff_claim_alignment_status": notebook["handoff_claim_alignment"]["status"],
                "handoff_claim_alignment_public_safety_status": notebook["handoff_claim_alignment"]["public_safety_status"],
                "manual_publication_claim_contract_status": notebook["handoff_claim_alignment"][
                    "manual_publication_claim_contract"
                ]["expected_schema_version"],
                "practice_only": notebook["handoff_claim_alignment"]["practice_only"],
                "local_only": notebook["handoff_claim_alignment"]["local_only"],
                "public_summary_only": notebook["handoff_claim_alignment"]["public_summary_only"],
                "browser_handoff_claim_linked": (
                    "browser_extension_demo_handoff" in notebook["handoff_claim_alignment"]["unique_readiness_check_ids"]
                ),
                "browser_manifest_boundary_linked": (
                    "browser_manifest_content_boundary"
                    in notebook["handoff_claim_alignment"]["unique_readiness_check_ids"]
                ),
                "local_demo_claim_linked": "local_demo_run" in notebook["handoff_claim_alignment"]["unique_readiness_check_ids"],
                "demo_feedback_claim_linked": (
                    "demo_feedback_contract" in notebook["handoff_claim_alignment"]["unique_readiness_check_ids"]
                ),
                "publication_claim_linked": (
                    "publication_package" in notebook["handoff_claim_alignment"]["unique_readiness_check_ids"]
                ),
                "review_board_claim_linked": (
                    "review_board_packet" in notebook["handoff_claim_alignment"]["unique_readiness_check_ids"]
                ),
                "human_submission_gate_linked": (
                    "human_submission_review_required" in notebook["handoff_claim_alignment"]["required_human_gates"]
                ),
                "exam_clearance_blocked": "exam clearance" in notebook["handoff_claim_alignment"]["blocked_claims"],
            },
        },
        {
            "check_id": "source_cards",
            "passed": len(source_cards) >= 10
            and source_card_claim_alignment["status"] == "ready"
            and source_card_claim_alignment["public_safety_status"] == "pass"
            and source_card_claim_alignment["public_link_only"] is True
            and source_card_claim_alignment["all_cards_have_product_rules"] is True,
            "evidence": {
                "source_card_count": len(source_cards),
                "high_risk_count": len([card for card in source_cards if card["risk_level"] == "high"]),
                "claim_alignment_status": source_card_claim_alignment["status"],
                "claim_alignment_public_safety_status": source_card_claim_alignment["public_safety_status"],
                "manual_publication_claim_contract_status": source_card_claim_alignment[
                    "manual_publication_claim_contract"
                ]["expected_schema_version"],
                "public_link_only": source_card_claim_alignment["public_link_only"],
                "all_cards_have_product_rules": source_card_claim_alignment["all_cards_have_product_rules"],
            },
        },
        {
            "check_id": "source_card_drift_guard",
            "passed": source_card_drift["status"] == "pass"
            and source_card_drift["public_safety_status"] == "pass"
            and source_card_drift["missing_required_source_card_ids"] == []
            and source_card_drift["unlisted_high_risk_source_card_ids"] == []
            and source_card_drift["duplicate_source_ids"] == []
            and source_card_drift["stale_source_card_ids"] == []
            and source_card_claim_alignment["missing_release_review_board_claim_check_ids"] == []
            and source_card_claim_alignment["missing_release_review_board_claim_human_gates"] == []
            and source_card_claim_alignment["failed_contract_ids"] == []
            and source_card_claim_alignment["workspace_card_readiness_gate_linked"] is True
            and source_card_claim_alignment["workspace_card_source_gate_linked"] is True
            and source_card_claim_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "status": source_card_drift["status"],
                "public_safety_status": source_card_drift["public_safety_status"],
                "card_count": source_card_drift["card_count"],
                "required_source_card_count": source_card_drift["required_source_card_count"],
                "high_risk_source_card_count": source_card_drift["high_risk_source_card_count"],
                "source_kind_count": source_card_drift["source_kind_count"],
                "authority_type_count": source_card_drift["authority_type_count"],
                "stale_source_card_count": len(source_card_drift["stale_source_card_ids"]),
                "source_card_claim_alignment_status": source_card_claim_alignment["status"],
                "redteam_claim_linked": "redteam" in source_card_claim_alignment["unique_readiness_check_ids"],
                "notebook_handoff_claim_linked": (
                    "notebook_template" in source_card_claim_alignment["unique_readiness_check_ids"]
                ),
                "publication_claim_linked": "publication_package" in source_card_claim_alignment["unique_readiness_check_ids"],
                "review_board_claim_linked": "review_board_packet" in source_card_claim_alignment["unique_readiness_check_ids"],
                "workspace_card_status": source_card_claim_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": source_card_claim_alignment["workspace_card_selected_skill_tag"],
                "workspace_card_ready_for_operator_prefill": source_card_claim_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": source_card_claim_alignment["workspace_card_help_ledger_status"],
                "workspace_card_help_ledger_hash_present": source_card_claim_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": source_card_claim_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_source_gate_linked": source_card_claim_alignment["workspace_card_source_gate_linked"],
                "workspace_card_readiness_gate_claim_linked": source_card_claim_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": source_card_claim_alignment["raw_workspace_card_returned"],
                "human_submission_gate_linked": (
                    "human_submission_review_required" in source_card_claim_alignment["required_human_gates"]
                ),
                "exam_clearance_blocked": "exam clearance" in source_card_claim_alignment["blocked_claims"],
            },
        },
        {
            "check_id": "course_material_policy",
            "passed": material_manifest["record_count"] >= 2
            and material_manifest["public_release_allowed_count"] == 1
            and material_summary_scan["status"] == "pass"
            and material_public_boundary_alignment["status"] == "ready"
            and material_public_boundary_alignment["public_safety_status"] == "pass"
            and material_public_boundary_alignment["missing_material_ids"] == []
            and material_public_boundary_alignment["missing_summary_material_ids"] == []
            and material_public_boundary_alignment["missing_source_card_ids"] == []
            and material_public_boundary_alignment["failed_contract_ids"] == [],
            "evidence": {
                "record_count": material_manifest["record_count"],
                "tutor_usable_count": material_manifest["tutor_usable_count"],
                "public_release_allowed_count": material_manifest["public_release_allowed_count"],
                "public_summary_scan": material_summary_scan["status"],
                "material_public_boundary_alignment_status": material_public_boundary_alignment["status"],
                "material_public_boundary_alignment_section_count": material_public_boundary_alignment["section_count"],
                "material_public_boundary_alignment_human_gates": material_public_boundary_alignment["required_human_gates"],
            },
        },
        {
            "check_id": "adaptive_task_plan",
            "passed": adaptive_plan["status"] == "ok"
            and adaptive_plan["public_safety_status"] == "pass"
            and adaptive_plan["task_count"] >= 3
            and all(task["public_safe"] for task in adaptive_plan["tasks"])
            and adaptive_source_boundary_alignment["status"] == "ready"
            and adaptive_source_boundary_alignment["public_safety_status"] == "pass"
            and adaptive_source_boundary_alignment["non_public_source_material_ids"] == []
            and adaptive_source_boundary_alignment["missing_source_card_ids"] == []
            and adaptive_source_boundary_alignment["failed_contract_ids"] == [],
            "evidence": {
                "status": adaptive_plan["status"],
                "task_count": adaptive_plan["task_count"],
                "public_safety_status": adaptive_plan["public_safety_status"],
                "eligible_material_count": adaptive_plan["eligible_material_count"],
                "source_boundary_alignment_status": adaptive_source_boundary_alignment["status"],
                "source_boundary_alignment_section_count": adaptive_source_boundary_alignment["section_count"],
                "source_boundary_alignment_human_gates": adaptive_source_boundary_alignment["required_human_gates"],
            },
        },
        {
            "check_id": "local_demo_run",
            "passed": demo_run["status"] == "practice_demo_ready_not_exam"
            and demo_run["public_safety_status"] == "pass"
            and demo_run["scenario_count"] >= 7
            and demo_run["claim_alignment"]["status"] == "ready"
            and demo_run["claim_alignment"]["public_safety_status"] == "pass"
            and demo_run["claim_alignment"]["practice_only"] is True
            and demo_run["claim_alignment"]["local_only"] is True
            and demo_run["claim_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and demo_run["claim_alignment"]["missing_release_review_board_claim_human_gates"] == [],
            "evidence": {
                "status": demo_run["status"],
                "scenario_count": demo_run["scenario_count"],
                "claim_alignment_status": demo_run["claim_alignment"]["status"],
                "claim_alignment_public_safety_status": demo_run["claim_alignment"]["public_safety_status"],
                "practice_only": demo_run["claim_alignment"]["practice_only"],
                "local_only": demo_run["claim_alignment"]["local_only"],
                "manual_publication_claim_contract_status": demo_run["claim_alignment"]["manual_publication_claim_contract"]["expected_schema_version"],
                "public_safety_status": demo_run["public_safety_status"],
            },
        },
        {
            "check_id": "browser_extension_demo_handoff",
            "passed": "browserExtensionReleaseReviewBoardClaimAlignment" in browser_sidepanel_text
            and "unibot-browser-extension-release-review-board-claim-alignment-v1" in browser_sidepanel_text
            and "unibot-local-demo-release-review-board-claim-alignment-v1" in browser_sidepanel_text
            and "unibot-demo-feedback-release-review-board-claim-alignment-v1" in browser_sidepanel_text
            and "unibot-feedback-triage-release-review-board-claim-alignment-v1" in browser_sidepanel_text
            and "unibot-github-issue-release-review-board-claim-alignment-v1" in browser_sidepanel_text
            and "browser_extension_demo_handoff" in browser_sidepanel_text
            and "local_demo_run" in browser_sidepanel_text
            and "demo_feedback_contract" in browser_sidepanel_text
            and "github_issue_bundle" in browser_sidepanel_text
            and "human_submission_review_required" in browser_sidepanel_text
            and "exam clearance" in browser_sidepanel_text
            and "practice-only" in browser_sidepanel_text,
            "evidence": {
                "status": "ready",
                "contract_status": "unibot-browser-extension-release-review-board-claim-alignment-v1",
                "local_demo_claim_linked": "unibot-local-demo-release-review-board-claim-alignment-v1" in browser_sidepanel_text,
                "demo_feedback_claim_linked": "unibot-demo-feedback-release-review-board-claim-alignment-v1" in browser_sidepanel_text,
                "triage_claim_linked": "unibot-feedback-triage-release-review-board-claim-alignment-v1" in browser_sidepanel_text,
                "github_issue_claim_linked": "unibot-github-issue-release-review-board-claim-alignment-v1" in browser_sidepanel_text,
                "human_submission_gate_linked": "human_submission_review_required" in browser_sidepanel_text,
                "exam_clearance_blocked": "exam clearance" in browser_sidepanel_text,
            },
        },
        {
            "check_id": "browser_manifest_content_boundary",
            "passed": browser_manifest["permissions"] == ["activeTab", "storage", "sidePanel"]
            and "<all_urls>" not in json.dumps(browser_manifest, ensure_ascii=False)
            and "https://colab.research.google.com/*" in browser_manifest["host_permissions"]
            and "http://localhost/*" in browser_manifest["host_permissions"]
            and "http://127.0.0.1/*" in browser_manifest["host_permissions"]
            and "contentScriptBoundaryClaimAlignment" in browser_content_text
            and "unibot-browser-manifest-content-boundary-claim-alignment-v1" in browser_content_text
            and "unibot-browser-extension-release-review-board-claim-alignment-v1" in browser_content_text
            and "unibot-local-demo-release-review-board-claim-alignment-v1" in browser_content_text
            and "browser_manifest_content_boundary" in browser_content_text
            and "browser_extension_demo_handoff" in browser_content_text
            and "human_submission_review_required" in browser_content_text
            and "exam clearance" in browser_content_text
            and "never claims exam security" in browser_content_text,
            "evidence": {
                "status": "ready",
                "contract_status": "unibot-browser-manifest-content-boundary-claim-alignment-v1",
                "permission_count": len(browser_manifest["permissions"]),
                "host_permission_count": len(browser_manifest["host_permissions"]),
                "all_urls_requested": "<all_urls>" in json.dumps(browser_manifest, ensure_ascii=False),
                "content_boundary_claim_present": "contentScriptBoundaryClaimAlignment" in browser_content_text,
                "sidepanel_claim_linked": "unibot-browser-extension-release-review-board-claim-alignment-v1" in browser_content_text,
                "local_demo_claim_linked": "unibot-local-demo-release-review-board-claim-alignment-v1" in browser_content_text,
                "human_submission_gate_linked": "human_submission_review_required" in browser_content_text,
                "exam_security_claim_blocked": "never claims exam security" in browser_content_text,
            },
        },
        {
            "check_id": "demo_feedback_contract",
            "passed": feedback_template_scan["status"] == "pass"
            and demo_feedback_validation["status"] == "ok"
            and feedback_summary_scan["status"] == "pass"
            and demo_feedback_validation["claim_alignment"]["status"] == "ready"
            and demo_feedback_validation["claim_alignment"]["public_safety_status"] == "pass"
            and demo_feedback_validation["claim_alignment"]["local_only"] is True
            and demo_feedback_validation["claim_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and demo_feedback_validation["claim_alignment"]["missing_release_review_board_claim_human_gates"] == [],
            "evidence": {
                "claim_alignment_status": demo_feedback_validation["claim_alignment"]["status"],
                "claim_alignment_public_safety_status": demo_feedback_validation["claim_alignment"]["public_safety_status"],
                "local_only": demo_feedback_validation["claim_alignment"]["local_only"],
                "public_summary_only": demo_feedback_validation["claim_alignment"]["public_summary_only"],
                "manual_publication_claim_contract_status": demo_feedback_validation["claim_alignment"]["manual_publication_claim_contract"]["expected_schema_version"],
                "template_status": feedback_template["status"],
                "template_public_safety_status": feedback_template_scan["status"],
                "validation_status": demo_feedback_validation["status"],
                "public_summary_scan": feedback_summary_scan["status"],
            },
        },
        {
            "check_id": "demo_feedback_triage",
            "passed": feedback_triage["status"] == "ready"
            and feedback_triage["public_safety_status"] == "pass"
            and feedback_triage["claim_alignment"]["status"] == "ready"
            and feedback_triage["claim_alignment"]["public_safety_status"] == "pass"
            and feedback_triage["claim_alignment"]["manual_publish_only"] is True
            and feedback_triage["claim_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and feedback_triage["claim_alignment"]["missing_release_review_board_claim_human_gates"] == [],
            "evidence": {
                "triage_status": feedback_triage["status"],
                "triage_count": feedback_triage["triage_count"],
                "public_safety_status": feedback_triage["public_safety_status"],
                "claim_alignment_status": feedback_triage["claim_alignment"]["status"],
                "claim_alignment_public_safety_status": feedback_triage["claim_alignment"]["public_safety_status"],
                "manual_publish_only": feedback_triage["claim_alignment"]["manual_publish_only"],
                "manual_publication_claim_contract_status": feedback_triage["claim_alignment"][
                    "manual_publication_claim_contract"
                ]["expected_schema_version"],
                "claim_alignment_readiness_check_count": len(feedback_triage["claim_alignment"]["unique_readiness_check_ids"]),
            },
        },
        {
            "check_id": "github_issue_bundle",
            "passed": github_issue_bundle["status"] == "ready"
            and github_issue_bundle["public_safety_status"] == "pass"
            and github_issue_bundle["issue_count"] >= 1
            and github_issue_bundle["evidence_traceability"]["status"] == "ready"
            and github_issue_bundle["evidence_traceability"]["public_safety_status"] == "pass"
            and github_issue_bundle["evidence_traceability"]["manual_publish_only"] is True
            and github_issue_bundle["evidence_traceability"]["missing_release_review_board_claim_check_ids"] == []
            and github_issue_bundle["evidence_traceability"]["missing_release_review_board_claim_human_gates"] == [],
            "evidence": {
                "status": github_issue_bundle["status"],
                "issue_count": github_issue_bundle["issue_count"],
                "public_safety_status": github_issue_bundle["public_safety_status"],
                "evidence_traceability_status": github_issue_bundle["evidence_traceability"]["status"],
                "evidence_traceability_public_safety_status": github_issue_bundle["evidence_traceability"]["public_safety_status"],
                "manual_publish_only": github_issue_bundle["evidence_traceability"]["manual_publish_only"],
                "manual_publication_claim_contract_status": github_issue_bundle["evidence_traceability"][
                    "manual_publication_claim_contract"
                ]["expected_schema_version"],
                "readiness_check_count": len(github_issue_bundle["evidence_traceability"]["unique_readiness_check_ids"]),
            },
        },
        {
            "check_id": "release_runbook",
            "passed": release_runbook["status"] == "public_draft_runbook_not_exam_release"
            and release_runbook["public_safety_status"] == "pass"
            and release_runbook["manual_review_required"] is True
            and release_runbook["exam_deployment_status"] == "not_cleared"
            and release_runbook["release_evidence_alignment"]["status"] == "ready"
            and release_runbook["release_evidence_alignment"]["public_safety_status"] == "pass"
            and release_runbook["release_evidence_alignment"]["unmapped_gate_ids"] == []
            and release_runbook["release_evidence_alignment"]["missing_review_board_thesis_evaluation_check_ids"] == []
            and release_runbook["release_evidence_alignment"]["missing_review_board_thesis_evaluation_human_gates"] == []
            and release_runbook["release_evidence_alignment"]["workspace_card_release_runbook_gate_linked"] is True
            and release_runbook["release_evidence_alignment"]["workspace_card_release_runbook_gate_issue"] == "",
            "evidence": {
                "status": release_runbook["status"],
                "public_safety_status": release_runbook["public_safety_status"],
                "manual_review_required": release_runbook["manual_review_required"],
                "exam_deployment_status": release_runbook["exam_deployment_status"],
                "release_evidence_alignment_status": release_runbook["release_evidence_alignment"]["status"],
                "release_gate_count": release_runbook["release_evidence_alignment"]["release_gate_count"],
                "review_board_thesis_evaluation_claim_contract_status": release_runbook["release_evidence_alignment"][
                    "review_board_thesis_evaluation_claim_contract"
                ]["required_status"],
                "workspace_card_status": release_runbook["release_evidence_alignment"]["workspace_card_status"],
                "workspace_card_selected_skill_tag": release_runbook["release_evidence_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": release_runbook["release_evidence_alignment"][
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": release_runbook["release_evidence_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": release_runbook["release_evidence_alignment"][
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": release_runbook["release_evidence_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_release_runbook_gate_linked": release_runbook["release_evidence_alignment"][
                    "workspace_card_release_runbook_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in release_runbook["release_evidence_alignment"]["unique_readiness_check_ids"]
                ),
                "workspace_card_release_runbook_gate_issue": release_runbook["release_evidence_alignment"][
                    "workspace_card_release_runbook_gate_issue"
                ],
                "release_alignment_human_gates": release_runbook["release_evidence_alignment"]["required_human_gates"],
            },
        },
        {
            "check_id": "compliance_matrix",
            "passed": compliance_matrix["status"] == "draft_ready_for_authority_review"
            and compliance_matrix["public_safety_status"] == "pass"
            and compliance_matrix["missing_source_card_ids"] == []
            and compliance_matrix["exam_deployment_status"] == "not_cleared"
            and compliance_matrix["compliance_drift_alignment"]["status"] == "ready"
            and compliance_matrix["compliance_drift_alignment"]["public_safety_status"] == "pass"
            and compliance_matrix["compliance_drift_alignment"]["unmapped_requirement_ids"] == []
            and compliance_matrix["compliance_drift_alignment"]["requirements_without_human_gates"] == []
            and compliance_matrix["compliance_drift_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and compliance_matrix["compliance_drift_alignment"]["missing_release_review_board_claim_human_gates"] == [],
            "evidence": {
                "status": compliance_matrix["status"],
                "requirement_count": compliance_matrix["requirement_count"],
                "high_risk_requirement_count": compliance_matrix["high_risk_requirement_count"],
                "public_safety_status": compliance_matrix["public_safety_status"],
                "missing_source_card_ids": compliance_matrix["missing_source_card_ids"],
                "exam_deployment_status": compliance_matrix["exam_deployment_status"],
                "compliance_drift_alignment_status": compliance_matrix["compliance_drift_alignment"]["status"],
                "release_review_board_claim_contract_status": compliance_matrix["compliance_drift_alignment"][
                    "release_runbook_review_board_claim_contract"
                ]["expected_schema_version"],
                "compliance_alignment_readiness_check_count": len(
                    compliance_matrix["compliance_drift_alignment"]["unique_readiness_check_ids"]
                ),
                "compliance_alignment_human_gates": compliance_matrix["compliance_drift_alignment"]["required_human_gates"],
            },
        },
        {
            "check_id": "pilot_protocol",
            "passed": pilot_protocol["status"] == "draft_not_ethics_or_authority_cleared"
            and pilot_protocol["public_safety_status"] == "pass"
            and pilot_protocol["exam_deployment_status"] == "not_cleared"
            and len(pilot_protocol["consent_items"]) >= 7
            and pilot_protocol["pilot_evidence_alignment"]["status"] == "ready"
            and pilot_protocol["pilot_evidence_alignment"]["public_safety_status"] == "pass"
            and pilot_protocol["pilot_evidence_alignment"]["missing_protocol_keys"] == []
            and pilot_protocol["pilot_evidence_alignment"]["missing_source_card_ids"] == []
            and pilot_protocol["pilot_evidence_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and pilot_protocol["pilot_evidence_alignment"]["missing_release_review_board_claim_human_gates"] == [],
            "evidence": {
                "status": pilot_protocol["status"],
                "public_safety_status": pilot_protocol["public_safety_status"],
                "consent_item_count": len(pilot_protocol["consent_items"]),
                "ethics_trigger_count": len(pilot_protocol["ethics_review_triggers"]),
                "exam_deployment_status": pilot_protocol["exam_deployment_status"],
                "pilot_evidence_alignment_status": pilot_protocol["pilot_evidence_alignment"]["status"],
                "pilot_release_review_board_claim_contract_status": pilot_protocol["pilot_evidence_alignment"][
                    "pilot_release_review_board_claim_contract"
                ]["expected_schema_version"],
                "pilot_alignment_section_count": pilot_protocol["pilot_evidence_alignment"]["section_count"],
                "pilot_alignment_human_gates": pilot_protocol["pilot_evidence_alignment"]["required_human_gates"],
            },
        },
        {
            "check_id": "data_protection_screening",
            "passed": data_protection["status"] == "draft_for_datenschutz_review"
            and data_protection["public_safety_status"] == "pass"
            and data_protection["review_gates"]["datenschutz_review_required_before_real_pilot"] is True
            and data_protection["exam_deployment_status"] == "not_cleared"
            and data_protection["data_protection_evidence_alignment"]["status"] == "ready"
            and data_protection["data_protection_evidence_alignment"]["public_safety_status"] == "pass"
            and data_protection["data_protection_evidence_alignment"]["missing_screening_keys"] == []
            and data_protection["data_protection_evidence_alignment"]["missing_processing_activity_ids"] == []
            and data_protection["data_protection_evidence_alignment"]["missing_risk_ids"] == []
            and data_protection["data_protection_evidence_alignment"]["missing_source_card_ids"] == []
            and data_protection["data_protection_evidence_alignment"]["missing_release_review_board_claim_check_ids"] == []
            and data_protection["data_protection_evidence_alignment"][
                "missing_release_review_board_claim_human_gates"
            ]
            == [],
            "evidence": {
                "status": data_protection["status"],
                "public_safety_status": data_protection["public_safety_status"],
                "processing_activity_count": len(data_protection["processing_activities"]),
                "risk_count": len(data_protection["risk_register"]),
                "datenschutz_review_required": data_protection["review_gates"]["datenschutz_review_required_before_real_pilot"],
                "exam_deployment_status": data_protection["exam_deployment_status"],
                "data_protection_evidence_alignment_status": data_protection["data_protection_evidence_alignment"]["status"],
                "data_protection_release_review_board_claim_contract_status": data_protection[
                    "data_protection_evidence_alignment"
                ]["data_protection_release_review_board_claim_contract"]["expected_schema_version"],
                "data_protection_alignment_section_count": data_protection["data_protection_evidence_alignment"]["section_count"],
                "data_protection_alignment_human_gates": data_protection["data_protection_evidence_alignment"]["required_human_gates"],
            },
        },
        {
            "check_id": "review_board_packet",
            "passed": review_board_packet["status"] == "draft_for_institutional_review"
            and review_board_packet["public_safety_status"] == "pass"
            and review_board_packet["exam_deployment_status"] == "not_cleared"
            and len(review_board_packet["reviewer_packets"]) >= 6
            and len(review_board_packet["open_decision_register"]) >= 6
            and review_board_packet["evidence_alignment"]["status"] == "ready"
            and review_board_packet["evidence_alignment"]["public_safety_status"] == "pass"
            and review_board_packet["evidence_alignment"]["unmapped_reviewer_count"] == 0
            and review_board_packet["evidence_alignment"]["missing_claim_ids"] == []
            and review_board_packet["thesis_evaluation_claim_alignment"]["status"] == "ready"
            and review_board_packet["thesis_evaluation_claim_alignment"]["public_safety_status"] == "pass"
            and review_board_packet["thesis_evaluation_claim_alignment"]["missing_source_card_ids"] == []
            and review_board_packet["thesis_evaluation_claim_alignment"]["failed_reviewer_ids"] == []
            and review_board_packet["thesis_evaluation_claim_alignment"]["failed_contract_ids"] == []
            and review_board_packet["release_claim_summary_alignment"]["status"] == "ready"
            and review_board_packet["release_claim_summary_alignment"]["public_safety_status"] == "pass"
            and review_board_packet["release_claim_summary_alignment"]["missing_source_card_ids"] == []
            and review_board_packet["release_claim_summary_alignment"]["failed_contract_ids"] == [],
            "evidence": {
                "status": review_board_packet["status"],
                "public_safety_status": review_board_packet["public_safety_status"],
                "reviewer_count": len(review_board_packet["reviewer_packets"]),
                "open_decision_count": len(review_board_packet["open_decision_register"]),
                "exam_deployment_status": review_board_packet["exam_deployment_status"],
                "evidence_alignment_status": review_board_packet["evidence_alignment"]["status"],
                "evidence_alignment_reviewer_count": len(review_board_packet["evidence_alignment"]["reviewer_alignment"]),
                "readiness_snapshot_gate_count": len(
                    review_board_packet["evidence_alignment"]["readiness_snapshot_contract"]["required_gate_ids"]
                ),
                "thesis_evaluation_claim_alignment_status": review_board_packet["thesis_evaluation_claim_alignment"]["status"],
                "thesis_evaluation_claim_alignment_section_count": review_board_packet["thesis_evaluation_claim_alignment"]["section_count"],
                "thesis_evaluation_claim_alignment_human_gates": review_board_packet["thesis_evaluation_claim_alignment"]["required_human_gates"],
                "release_claim_summary_alignment_status": review_board_packet["release_claim_summary_alignment"]["status"],
                "release_claim_summary_alignment_public_safety_status": review_board_packet[
                    "release_claim_summary_alignment"
                ]["public_safety_status"],
                "release_claim_summary_alignment_section_count": review_board_packet["release_claim_summary_alignment"][
                    "section_count"
                ],
                "workspace_card_status": review_board_packet["release_claim_summary_alignment"]["workspace_card_status"],
                "workspace_card_selected_skill_tag": review_board_packet["release_claim_summary_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": review_board_packet["release_claim_summary_alignment"][
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": review_board_packet["release_claim_summary_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": review_board_packet["release_claim_summary_alignment"][
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": review_board_packet["release_claim_summary_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_review_board_gate_linked": review_board_packet["release_claim_summary_alignment"][
                    "workspace_card_review_board_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": (
                    "python_exam_local_cycle_operator_workspace_card"
                    in review_board_packet["release_claim_summary_alignment"]["required_readiness_check_ids"]
                ),
                "workspace_card_review_board_gate_contract": review_board_packet["release_claim_summary_alignment"][
                    "contracts"
                ]["workspace_card_review_board_gate_linked"],
            },
        },
        {
            "check_id": "exam_boundary",
            "passed": "exam_controlled" in publication["system_card"]["blocked_or_not_cleared_modes"],
            "evidence": {
                "blocked_or_not_cleared_modes": publication["system_card"]["blocked_or_not_cleared_modes"],
                "exam_deployment_status": "not_cleared",
            },
        },
        {
            "check_id": "orchestration_command_center",
            "passed": command_center["status"] == "ready_to_orchestrate"
            and command_center["deployment_line"]["exam_deployment_status"] == "not_cleared"
            and command_center["public_safety_status"] == "pass"
            and command_center_scan["status"] == "pass"
            and command_center["workspace_card_route_alignment"]["status"] == "ready"
            and command_center["workspace_card_route_alignment"]["alignment_public_safety_status"] == "pass"
            and command_center["workspace_card_route_alignment"]["failed_contract_ids"] == []
            and command_center["workspace_card_route_alignment"]["workspace_card_readiness_gate_linked"] is True
            and command_center["workspace_card_route_alignment"]["workspace_card_command_center_gate_linked"] is True
            and command_center["workspace_card_route_alignment"]["raw_workspace_card_returned"] is False
            and handoff_validation["status"] == "ok",
            "evidence": {
                "status": command_center["status"],
                "role_lane_count": len(command_center["role_lanes"]),
                "public_safety_status": command_center["public_safety_status"],
                "handoff_validation_status": handoff_validation["status"],
                "exam_deployment_status": command_center["deployment_line"]["exam_deployment_status"],
                "workspace_card_route_alignment_status": command_center["workspace_card_route_alignment"]["status"],
                "workspace_card_route_alignment_public_safety_status": command_center[
                    "workspace_card_route_alignment"
                ]["alignment_public_safety_status"],
                "active_harness_count": command_center["workspace_card_route_alignment"]["active_harness_count"],
                "active_route_count": command_center["workspace_card_route_alignment"]["active_route_count"],
                "scope_status": command_center["workspace_card_route_alignment"]["scope_status"],
                "workspace_card_status": command_center["workspace_card_route_alignment"]["workspace_card_status"],
                "workspace_card_selected_skill_tag": command_center["workspace_card_route_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": command_center["workspace_card_route_alignment"][
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": command_center["workspace_card_route_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": command_center["workspace_card_route_alignment"][
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": command_center["workspace_card_route_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_command_center_gate_linked": command_center["workspace_card_route_alignment"][
                    "workspace_card_command_center_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": command_center["workspace_card_route_alignment"][
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": command_center["workspace_card_route_alignment"][
                    "raw_workspace_card_returned"
                ],
            },
        },
        {
            "check_id": "gretel_glm_evolve_lane",
            "passed": glm_evolve_packet["status"] == "prepared_no_provider_call"
            and glm_evolve_packet["public_safety_status"] == "pass"
            and glm_evolve_packet["provider_call_executed"] is False
            and glm_evolve_packet["raw_private_context_shared"] is False
            and glm_evolve_packet["autonomous_apply"] is False
            and glm_evolve_packet["route"] == "proposal_only_requires_codex_and_human_review"
            and glm_provider_redaction_alignment["status"] == "ready"
            and glm_provider_redaction_alignment["public_safety_status"] == "pass"
            and glm_provider_redaction_alignment["failed_contract_ids"] == []
            and glm_provider_redaction_alignment["missing_packet_keys"] == []
            and glm_provider_redaction_alignment["missing_workboard_keys"] == []
            and glm_provider_redaction_alignment["missing_source_card_ids"] == []
            and glm_provider_redaction_alignment["workspace_card_readiness_gate_linked"] is True
            and glm_provider_redaction_alignment["workspace_card_glm_gate_linked"] is True
            and glm_provider_redaction_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "status": glm_evolve_packet["status"],
                "public_safety_status": glm_evolve_packet["public_safety_status"],
                "provider_call_executed": glm_evolve_packet["provider_call_executed"],
                "raw_private_context_shared": glm_evolve_packet["raw_private_context_shared"],
                "autonomous_apply": glm_evolve_packet["autonomous_apply"],
                "route": glm_evolve_packet["route"],
                "model_hint": glm_evolve_packet["model_hint"],
                "provider_redaction_alignment_status": glm_provider_redaction_alignment["status"],
                "provider_redaction_alignment_section_count": glm_provider_redaction_alignment["section_count"],
                "provider_redaction_alignment_human_gates": glm_provider_redaction_alignment["required_human_gates"],
                "workspace_card_status": glm_provider_redaction_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": glm_provider_redaction_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": glm_provider_redaction_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": glm_provider_redaction_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": glm_provider_redaction_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": glm_provider_redaction_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_glm_gate_linked": glm_provider_redaction_alignment[
                    "workspace_card_glm_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": glm_provider_redaction_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": glm_provider_redaction_alignment["raw_workspace_card_returned"],
            },
        },
        {
            "check_id": "gretel_glm_rsi_visibility_workboard",
            "passed": glm_rsi_workboard["status"] == "visible"
            and glm_rsi_workboard["public_safety_status"] == "pass"
            and glm_rsi_workboard_scan["status"] == "pass"
            and glm_rsi_workboard["safety"]["provider_call_executed"] is False
            and glm_rsi_workboard["safety"]["provider_call_allowed_now"] is False
            and glm_rsi_workboard["safety"]["autonomous_apply"] is False
            and glm_rsi_workboard["safety"]["final_go"] is False
            and glm_rsi_workboard["active_item_count"] >= 1,
            "evidence": {
                "status": glm_rsi_workboard["status"],
                "public_safety_status": glm_rsi_workboard["public_safety_status"],
                "scan_status": glm_rsi_workboard_scan["status"],
                "active_item_count": glm_rsi_workboard["active_item_count"],
                "blocked_item_count": glm_rsi_workboard["blocked_item_count"],
                "provider_call_executed": glm_rsi_workboard["safety"]["provider_call_executed"],
                "provider_call_allowed_now": glm_rsi_workboard["safety"]["provider_call_allowed_now"],
                "autonomous_apply": glm_rsi_workboard["safety"]["autonomous_apply"],
            },
        },
        {
            "check_id": "gretel_bachelor_thesis_package",
            "passed": bachelor_thesis_package["status"] == "public_scientific_draft_bachelor_thesis_level_not_real_submission"
            and bachelor_thesis_package["public_safety_status"] == "pass"
            and bachelor_thesis_scan["status"] == "pass"
            and bachelor_thesis_package["authorship_statement"]["builder"] == "Gretel"
            and bachelor_thesis_package["authorship_statement"]["documentation_author"] == "Gretel"
            and bachelor_thesis_package["glm_technology_basis"]["primary_model_hint"] == "zai/glm-5.2"
            and bachelor_thesis_package["review_gates"]["human_submission_review_required"] is True
            and bachelor_thesis_package["review_gates"]["no_autonomous_github_publish"] is True
            and bachelor_thesis_package["review_gates"]["no_final_go_by_gretel_or_glm"] is True
            and bachelor_thesis_package["evidence_index"]["status"] == "ready"
            and bachelor_thesis_package["evidence_index"]["public_safety_status"] == "pass"
            and bachelor_thesis_package["evaluation_claim_alignment"]["status"] == "ready"
            and bachelor_thesis_package["evaluation_claim_alignment"]["public_safety_status"] == "pass"
            and bachelor_thesis_package["evaluation_claim_alignment"]["missing_source_card_ids"] == []
            and bachelor_thesis_package["evaluation_claim_alignment"]["failed_contract_ids"] == []
            and bachelor_thesis_package["evaluation_claim_alignment"]["workspace_card_readiness_gate_linked"] is True
            and bachelor_thesis_package["evaluation_claim_alignment"]["workspace_card_bachelor_thesis_gate_linked"] is True
            and bachelor_thesis_package["evaluation_claim_alignment"]["raw_workspace_card_returned"] is False
            and "source_card_drift_guard" in bachelor_thesis_package["evidence_index"]["required_readiness_check_ids"]
            and "python_exam_local_cycle_operator_workspace_card"
            in bachelor_thesis_package["evaluation_claim_alignment"]["required_readiness_check_ids"]
            and "written_university_clearance_required_before_exam_use"
            in bachelor_thesis_package["evidence_index"]["required_human_gates"],
            "evidence": {
                "status": bachelor_thesis_package["status"],
                "public_safety_status": bachelor_thesis_package["public_safety_status"],
                "scan_status": bachelor_thesis_scan["status"],
                "builder": bachelor_thesis_package["authorship_statement"]["builder"],
                "documentation_author": bachelor_thesis_package["authorship_statement"]["documentation_author"],
                "model_hint": bachelor_thesis_package["glm_technology_basis"]["primary_model_hint"],
                "institutional_status": bachelor_thesis_package["authorship_statement"]["institutional_status"],
                "evidence_index_status": bachelor_thesis_package["evidence_index"]["status"],
                "evidence_claim_count": bachelor_thesis_package["evidence_index"]["claim_count"],
                "evaluation_claim_alignment_status": bachelor_thesis_package["evaluation_claim_alignment"]["status"],
                "evaluation_claim_alignment_section_count": bachelor_thesis_package["evaluation_claim_alignment"]["section_count"],
                "evaluation_claim_alignment_human_gates": bachelor_thesis_package["evaluation_claim_alignment"]["required_human_gates"],
                "workspace_card_status": bachelor_thesis_package["evaluation_claim_alignment"]["workspace_card_status"],
                "workspace_card_selected_skill_tag": bachelor_thesis_package["evaluation_claim_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": bachelor_thesis_package["evaluation_claim_alignment"][
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": bachelor_thesis_package["evaluation_claim_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": bachelor_thesis_package["evaluation_claim_alignment"][
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": bachelor_thesis_package["evaluation_claim_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_bachelor_thesis_gate_linked": bachelor_thesis_package["evaluation_claim_alignment"][
                    "workspace_card_bachelor_thesis_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": bachelor_thesis_package["evaluation_claim_alignment"][
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": bachelor_thesis_package["evaluation_claim_alignment"][
                    "raw_workspace_card_returned"
                ],
                "required_human_gates": bachelor_thesis_package["evidence_index"]["required_human_gates"],
            },
        },
        {
            "check_id": "gretel_autonomous_research_loop",
            "passed": autonomous_research_loop["status"] == "ready_for_budgeted_recurring_local_runs"
            and autonomous_research_loop["public_safety_status"] == "pass"
            and autonomous_research_loop_scan["status"] == "pass"
            and autonomous_research_loop["workspace_card_budget_alignment"]["status"] == "ready"
            and autonomous_research_loop["workspace_card_budget_alignment"]["public_safety_status"] == "pass"
            and autonomous_research_loop["workspace_card_budget_alignment"]["failed_contract_ids"] == []
            and autonomous_research_loop["budget_policy"]["cadence"]["recommended_cron"] == "every_6_hours"
            and autonomous_research_loop["budget_policy"]["token_policy"]["default_reasoning_effort"] == "low"
            and autonomous_research_loop["budget_policy"]["cadence"]["max_active_work_item_per_run"] == 1
            and autonomous_research_loop["safety"]["provider_call_executed"] is False
            and autonomous_research_loop["safety"]["autonomous_github_push"] is False
            and autonomous_research_loop["safety"]["mail_calendar_chat_actions"] is False
            and autonomous_research_loop["safety"]["final_go"] is False
            and autonomous_research_loop["workspace_card_budget_alignment"][
                "workspace_card_readiness_gate_linked"
            ]
            is True
            and autonomous_research_loop["workspace_card_budget_alignment"][
                "workspace_card_autonomous_loop_gate_linked"
            ]
            is True
            and autonomous_research_loop["workspace_card_budget_alignment"]["raw_workspace_card_returned"] is False
            and autonomous_research_loop["candidate_receipt"]["status"] == "candidate_receipt_ready"
            and autonomous_research_loop["candidate_receipt"]["selected_work_id"]
            == autonomous_research_loop["next_recommended_work_id"]
            and autonomous_research_loop["candidate_receipt"]["ready_work_items_remain_zero"] is True
            and autonomous_research_loop["candidate_receipt"]["candidate_is_not_auto_ready"] is True
            and autonomous_research_loop["candidate_receipt"]["allowed_file_count"] <= 4
            and autonomous_research_loop["candidate_receipt"]["public_safety_status"] == "pass"
            and autonomous_research_loop["candidate_review"]["status"] == "candidate_review_ready"
            and autonomous_research_loop["candidate_review"]["public_safety_status"] == "pass"
            and autonomous_research_loop["candidate_review"]["failed_contract_ids"] == []
            and autonomous_research_loop["candidate_review"]["auto_promotion_allowed"] is False
            and autonomous_research_loop["receipt"]["candidate_receipt_status"] == "candidate_receipt_ready"
            and autonomous_research_loop["receipt"]["candidate_receipt_hash"]
            == autonomous_research_loop["candidate_receipt"]["candidate_hash"]
            and autonomous_research_loop["receipt"]["candidate_review_status"] == "candidate_review_ready"
            and autonomous_research_loop["receipt"]["candidate_review_hash"] == autonomous_candidate_review_hash
            and autonomous_research_loop["candidate_rotation_receipt"]["status"] == "candidate_rotation_receipt_ready"
            and autonomous_research_loop["candidate_rotation_receipt"]["public_safety_status"] == "pass"
            and autonomous_research_loop["candidate_rotation_receipt"]["failed_contract_ids"] == []
            and autonomous_research_loop["candidate_rotation_receipt"]["auto_promotion_allowed"] is False
            and autonomous_research_loop["receipt"]["candidate_rotation_status"]
            == "candidate_rotation_receipt_ready"
            and autonomous_research_loop["receipt"]["candidate_rotation_hash"] == autonomous_candidate_rotation_hash
            and autonomous_research_loop["single_candidate_continuity_receipt"]["status"]
            == "single_candidate_continuity_ready"
            and autonomous_research_loop["single_candidate_continuity_receipt"]["public_safety_status"] == "pass"
            and autonomous_research_loop["single_candidate_continuity_receipt"]["selected_status"] == "candidate"
            and autonomous_research_loop["single_candidate_continuity_receipt"]["review_gate"]
            == autonomous_research_loop["candidate_receipt"]["review_gate"]
            and autonomous_research_loop["single_candidate_continuity_receipt"]["ready_work_items"] == 0
            and autonomous_research_loop["single_candidate_continuity_receipt"]["candidate_work_items"] == 1
            and autonomous_research_loop["single_candidate_continuity_receipt"]["failed_contract_ids"] == []
            and autonomous_research_loop["single_candidate_continuity_receipt"]["auto_promotion_allowed"] is False
            and autonomous_research_loop["receipt"]["single_candidate_continuity_status"]
            == "single_candidate_continuity_ready"
            and autonomous_research_loop["receipt"]["single_candidate_continuity_hash"]
            == autonomous_single_candidate_continuity_hash
            and autonomous_docs_traceability_negative_evidence_receipt.get("status")
            == "docs_traceability_negative_evidence_receipt_ready"
            and autonomous_docs_traceability_negative_evidence_receipt.get("public_safety_status") == "pass"
            and autonomous_docs_traceability_negative_evidence_receipt.get("failed_contract_ids") == []
            and autonomous_docs_traceability_negative_evidence_receipt.get("auto_promotion_allowed") is False
            and autonomous_docs_traceability_negative_evidence_receipt.get("provider_call_executed") is False
            and autonomous_docs_traceability_negative_evidence_receipt.get("autonomous_publication_started") is False
            and autonomous_docs_traceability_negative_evidence_receipt.get("final_go") is False
            and autonomous_docs_traceability_negative_evidence_receipt.get("negative_evidence_readiness_commit", "")
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_commit", ""
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_commit", ""
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_commit", ""
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_commit", ""
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_commit", ""
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                "",
            )
            != ""
            and autonomous_docs_traceability_negative_evidence_receipt.get(
                "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                "",
            )
            != ""
            and autonomous_research_loop["receipt"]["docs_traceability_negative_evidence_status"]
            == "docs_traceability_negative_evidence_receipt_ready"
            and autonomous_research_loop["receipt"]["docs_traceability_negative_evidence_hash"]
            == autonomous_docs_traceability_negative_evidence_receipt.get("evidence_hash", "")
            and autonomous_loop_docs_traceability["status"] == "ready"
            and autonomous_loop_docs_traceability["public_safety_status"] == "pass"
            and autonomous_loop_docs_traceability["failed_contract_ids"] == [],
            "evidence": {
                "status": autonomous_research_loop["status"],
                "public_safety_status": autonomous_research_loop["public_safety_status"],
                "scan_status": autonomous_research_loop_scan["status"],
                "workspace_card_budget_alignment_status": autonomous_research_loop[
                    "workspace_card_budget_alignment"
                ]["status"],
                "workspace_card_budget_alignment_public_safety_status": autonomous_research_loop[
                    "workspace_card_budget_alignment"
                ]["public_safety_status"],
                "recommended_cron": autonomous_research_loop["budget_policy"]["cadence"]["recommended_cron"],
                "default_reasoning_effort": autonomous_research_loop["budget_policy"]["token_policy"]["default_reasoning_effort"],
                "ready_work_items": autonomous_research_loop["receipt"]["ready_work_items"],
                "candidate_work_items": autonomous_research_loop["receipt"]["candidate_work_items"],
                "closed_harnessed_work_items": autonomous_research_loop["receipt"]["closed_harnessed_work_items"],
                "candidate_receipt_status": autonomous_research_loop["candidate_receipt"]["status"],
                "candidate_receipt_work_id": autonomous_research_loop["candidate_receipt"]["selected_work_id"],
                "candidate_receipt_hash_present": autonomous_research_loop["candidate_receipt"]["candidate_hash"]
                != "",
                "candidate_receipt_public_safety_status": autonomous_research_loop["candidate_receipt"][
                    "public_safety_status"
                ],
                "candidate_review_status": autonomous_research_loop["candidate_review"]["status"],
                "candidate_review_public_safety_status": autonomous_research_loop["candidate_review"][
                    "public_safety_status"
                ],
                "candidate_review_surface": autonomous_research_loop["candidate_review"][
                    "candidate_review_surface"
                ],
                "candidate_review_hash_present": autonomous_research_loop["candidate_review"][
                    "candidate_receipt_hash"
                ]
                != "",
                "candidate_review_receipt_status": autonomous_research_loop["receipt"]["candidate_review_status"],
                "candidate_review_receipt_hash_present": autonomous_research_loop["receipt"]["candidate_review_hash"]
                != "",
                "candidate_review_receipt_hash_matches_review": autonomous_research_loop["receipt"][
                    "candidate_review_hash"
                ]
                == autonomous_candidate_review_hash,
                "candidate_review_auto_promotion_allowed": autonomous_research_loop["candidate_review"][
                    "auto_promotion_allowed"
                ],
                "candidate_review_promotion_recommendation": autonomous_research_loop["candidate_review"][
                    "promotion_recommendation"
                ],
                "candidate_rotation_status": autonomous_research_loop["candidate_rotation_receipt"]["status"],
                "candidate_rotation_public_safety_status": autonomous_research_loop["candidate_rotation_receipt"][
                    "public_safety_status"
                ],
                "candidate_rotation_previous_closed_work_id": autonomous_research_loop[
                    "candidate_rotation_receipt"
                ]["previous_closed_work_id"],
                "candidate_rotation_previous_closed_commit": autonomous_research_loop[
                    "candidate_rotation_receipt"
                ]["previous_closed_commit"],
                "candidate_rotation_selected_work_id": autonomous_research_loop["candidate_rotation_receipt"][
                    "selected_work_id"
                ],
                "candidate_rotation_hash_present": autonomous_research_loop["candidate_rotation_receipt"][
                    "rotation_hash"
                ]
                != "",
                "candidate_rotation_receipt_status": autonomous_research_loop["receipt"][
                    "candidate_rotation_status"
                ],
                "candidate_rotation_receipt_hash_matches_rotation": autonomous_research_loop["receipt"][
                    "candidate_rotation_hash"
                ]
                == autonomous_candidate_rotation_hash,
                "candidate_rotation_auto_promotion_allowed": autonomous_research_loop[
                    "candidate_rotation_receipt"
                ]["auto_promotion_allowed"],
                "single_candidate_continuity_status": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["status"],
                "single_candidate_continuity_public_safety_status": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["public_safety_status"],
                "single_candidate_continuity_selected_work_id": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["selected_work_id"],
                "single_candidate_continuity_selected_status": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["selected_status"],
                "single_candidate_continuity_review_gate": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["review_gate"],
                "single_candidate_continuity_review_gate_matches_candidate_receipt": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["review_gate"]
                == autonomous_research_loop["candidate_receipt"]["review_gate"],
                "single_candidate_continuity_ready_work_items": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["ready_work_items"],
                "single_candidate_continuity_candidate_work_items": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["candidate_work_items"],
                "single_candidate_continuity_hash_present": autonomous_single_candidate_continuity_hash != "",
                "single_candidate_continuity_receipt_status": autonomous_research_loop["receipt"][
                    "single_candidate_continuity_status"
                ],
                "single_candidate_continuity_receipt_hash_matches_continuity": autonomous_research_loop["receipt"][
                    "single_candidate_continuity_hash"
                ]
                == autonomous_single_candidate_continuity_hash,
                "single_candidate_continuity_auto_promotion_allowed": autonomous_research_loop[
                    "single_candidate_continuity_receipt"
                ]["auto_promotion_allowed"],
                "docs_traceability_status": autonomous_loop_docs_traceability["status"],
                "docs_traceability_public_safety_status": autonomous_loop_docs_traceability["public_safety_status"],
                "docs_traceability_current_candidate_documented": autonomous_loop_docs_traceability[
                    "current_candidate_documented"
                ],
                "docs_traceability_previous_closure_documented": autonomous_loop_docs_traceability[
                    "previous_closure_documented"
                ],
                "docs_traceability_readiness_gate_match_rule_documented": autonomous_loop_docs_traceability[
                    "readiness_gate_match_rule_documented"
                ],
                "docs_traceability_promotion_blocker_documented": autonomous_loop_docs_traceability[
                    "promotion_blocker_documented"
                ],
                "docs_traceability_failed_contract_ids": autonomous_loop_docs_traceability["failed_contract_ids"],
                "docs_traceability_negative_evidence_receipt_status": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "status", "missing"
                ),
                "docs_traceability_negative_evidence_receipt_public_safety_status": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "public_safety_status", "missing"
                ),
                "docs_traceability_negative_evidence_receipt_hash_present": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "evidence_hash", ""
                )
                != "",
                "docs_traceability_negative_evidence_receipt_hash_matches_loop_receipt": autonomous_research_loop[
                    "receipt"
                ]["docs_traceability_negative_evidence_hash"]
                == autonomous_docs_traceability_negative_evidence_receipt.get("evidence_hash", ""),
                "docs_traceability_negative_evidence_receipt_negative_harness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_harness_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_receipt_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_commit", ""
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "negative_evidence_readiness_negative_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_receipt_readiness_commit",
                    "",
                ),
                "docs_traceability_negative_evidence_receipt_selected_work_id": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "selected_work_id", ""
                ),
                "docs_traceability_negative_evidence_receipt_review_gate": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "review_gate", ""
                ),
                "docs_traceability_negative_evidence_receipt_failed_contract_ids": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "failed_contract_ids", ["missing_docs_traceability_negative_evidence_receipt"]
                ),
                "docs_traceability_negative_evidence_receipt_auto_promotion_allowed": autonomous_docs_traceability_negative_evidence_receipt.get(
                    "auto_promotion_allowed", None
                ),
                "autonomous_github_push": autonomous_research_loop["safety"]["autonomous_github_push"],
                "workspace_card_status": autonomous_research_loop["workspace_card_budget_alignment"][
                    "workspace_card_status"
                ],
                "workspace_card_selected_skill_tag": autonomous_research_loop["workspace_card_budget_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": autonomous_research_loop[
                    "workspace_card_budget_alignment"
                ]["workspace_card_ready_for_operator_prefill"],
                "workspace_card_help_ledger_status": autonomous_research_loop["workspace_card_budget_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": autonomous_research_loop[
                    "workspace_card_budget_alignment"
                ]["workspace_card_help_ledger_hash_present"],
                "workspace_card_readiness_gate_linked": autonomous_research_loop[
                    "workspace_card_budget_alignment"
                ]["workspace_card_readiness_gate_linked"],
                "workspace_card_autonomous_loop_gate_linked": autonomous_research_loop[
                    "workspace_card_budget_alignment"
                ]["workspace_card_autonomous_loop_gate_linked"],
                "workspace_card_readiness_gate_claim_linked": autonomous_research_loop[
                    "workspace_card_budget_alignment"
                ]["workspace_card_readiness_gate_claim_linked"],
                "raw_workspace_card_returned": autonomous_research_loop["workspace_card_budget_alignment"][
                    "raw_workspace_card_returned"
                ],
            },
        },
        {
            "check_id": "paperclip_evaluation_bridge",
            "passed": paperclip_status_payload["status"] == "optional_not_active"
            and paperclip_bridge["status"] == "needs_codex_review"
            and paperclip_bridge["public_safety_status"] == "pass"
            and paperclip_bridge_scan["status"] == "pass"
            and paperclip_workspace_card_alignment["status"] == "ready"
            and paperclip_workspace_card_alignment["public_safety_status"] == "pass"
            and paperclip_workspace_card_alignment["failed_contract_ids"] == []
            and paperclip_bridge["critical_path"] is False
            and paperclip_bridge["chrome_extension_dependency"] is False
            and paperclip_bridge["provider_call_executed"] is False
            and paperclip_bridge["paperclip_execution_requested"] is False
            and paperclip_bridge["raw_private_context_shared"] is False
            and paperclip_bridge["autonomous_apply"] is False
            and paperclip_bridge["receipt"]["status"] in {"proposal_ready", "blocked", "needs_codex_review", "discarded"}
            and paperclip_workspace_card_alignment["workspace_card_readiness_gate_linked"] is True
            and paperclip_workspace_card_alignment["workspace_card_paperclip_gate_linked"] is True
            and paperclip_workspace_card_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "status": paperclip_bridge["status"],
                "paperclip_status": paperclip_status_payload["status"],
                "public_safety_status": paperclip_bridge["public_safety_status"],
                "workspace_card_control_alignment_status": paperclip_workspace_card_alignment["status"],
                "workspace_card_control_alignment_public_safety_status": paperclip_workspace_card_alignment[
                    "public_safety_status"
                ],
                "critical_path": paperclip_bridge["critical_path"],
                "chrome_extension_dependency": paperclip_bridge["chrome_extension_dependency"],
                "provider_call_executed": paperclip_bridge["provider_call_executed"],
                "ticket_status": paperclip_bridge["receipt"]["status"],
                "workspace_card_status": paperclip_workspace_card_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": paperclip_workspace_card_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": paperclip_workspace_card_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": paperclip_workspace_card_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": paperclip_workspace_card_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": paperclip_workspace_card_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_paperclip_gate_linked": paperclip_workspace_card_alignment[
                    "workspace_card_paperclip_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": paperclip_workspace_card_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": paperclip_workspace_card_alignment["raw_workspace_card_returned"],
            },
        },
        {
            "check_id": "review_chain_integrity",
            "passed": review_chain_integrity["status"] == "review_chain_integrity_pass"
            and review_chain_integrity["public_safety_status"] == "pass"
            and review_chain_integrity_scan["status"] == "pass"
            and review_chain_integrity["chain_integrity_summary"]["issue_count"] == 0
            and review_chain_integrity["exam_deployment_status"] == "not_cleared"
            and review_chain_integrity["workspace_card_chain_alignment"]["status"] == "ready"
            and review_chain_integrity["workspace_card_chain_alignment"]["alignment_public_safety_status"] == "pass"
            and review_chain_integrity["workspace_card_chain_alignment"]["failed_contract_ids"] == []
            and review_chain_integrity["workspace_card_chain_alignment"]["workspace_card_readiness_gate_linked"] is True
            and review_chain_integrity["workspace_card_chain_alignment"]["workspace_card_review_chain_gate_linked"] is True
            and review_chain_integrity["workspace_card_chain_alignment"]["raw_workspace_card_returned"] is False,
            "evidence": {
                "status": review_chain_integrity["status"],
                "public_safety_status": review_chain_integrity["public_safety_status"],
                "scan_status": review_chain_integrity_scan["status"],
                "issue_count": review_chain_integrity["chain_integrity_summary"]["issue_count"],
                "checked_link_count": review_chain_integrity["chain_integrity_summary"]["checked_link_count"],
                "exam_deployment_status": review_chain_integrity["exam_deployment_status"],
                "workspace_card_chain_alignment_status": review_chain_integrity["workspace_card_chain_alignment"][
                    "status"
                ],
                "workspace_card_chain_alignment_public_safety_status": review_chain_integrity[
                    "workspace_card_chain_alignment"
                ]["alignment_public_safety_status"],
                "workspace_card_status": review_chain_integrity["workspace_card_chain_alignment"][
                    "workspace_card_status"
                ],
                "workspace_card_selected_skill_tag": review_chain_integrity["workspace_card_chain_alignment"][
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": review_chain_integrity[
                    "workspace_card_chain_alignment"
                ]["workspace_card_ready_for_operator_prefill"],
                "workspace_card_help_ledger_status": review_chain_integrity["workspace_card_chain_alignment"][
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": review_chain_integrity[
                    "workspace_card_chain_alignment"
                ]["workspace_card_help_ledger_hash_present"],
                "workspace_card_readiness_gate_linked": review_chain_integrity["workspace_card_chain_alignment"][
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_review_chain_gate_linked": review_chain_integrity["workspace_card_chain_alignment"][
                    "workspace_card_review_chain_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": review_chain_integrity[
                    "workspace_card_chain_alignment"
                ]["workspace_card_readiness_gate_claim_linked"],
                "raw_workspace_card_returned": review_chain_integrity["workspace_card_chain_alignment"][
                    "raw_workspace_card_returned"
                ],
            },
        },
        {
            "check_id": "timeline_export_receipt_journal",
            "passed": timeline_receipt_journal_alignment["status"] == "ready"
            and timeline_receipt_journal_alignment["alignment_public_safety_status"] == "pass"
            and timeline_receipt_journal_alignment["failed_contract_ids"] == []
            and timeline_receipt_journal_alignment["append_status"] == "write_preview_ready"
            and timeline_receipt_journal_alignment["journal_written"] is False
            and timeline_receipt_journal_alignment["accepted_record_count"] >= 1
            and timeline_receipt_journal_alignment["exam_deployment_status"] == "not_cleared"
            and timeline_receipt_journal_alignment["workspace_card_readiness_gate_linked"] is True
            and timeline_receipt_journal_alignment["workspace_card_timeline_receipt_journal_gate_linked"] is True
            and timeline_receipt_journal_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "workspace_card_journal_alignment_status": timeline_receipt_journal_alignment["status"],
                "workspace_card_journal_alignment_public_safety_status": timeline_receipt_journal_alignment[
                    "alignment_public_safety_status"
                ],
                "append_status": timeline_receipt_journal_alignment["append_status"],
                "summary_status": timeline_receipt_journal_alignment["summary_status"],
                "journal_written": timeline_receipt_journal_alignment["journal_written"],
                "operator_confirmed_timeline_export_receipt_journal_append": timeline_receipt_journal_alignment[
                    "operator_confirmed_timeline_export_receipt_journal_append"
                ],
                "record_count": timeline_receipt_journal_alignment["record_count"],
                "accepted_record_count": timeline_receipt_journal_alignment["accepted_record_count"],
                "blocked_record_count": timeline_receipt_journal_alignment["blocked_record_count"],
                "event_count": timeline_receipt_journal_alignment["event_count"],
                "checkpoint_hash_count": timeline_receipt_journal_alignment["checkpoint_hash_count"],
                "reviewer_question_count": timeline_receipt_journal_alignment["reviewer_question_count"],
                "exam_deployment_status": timeline_receipt_journal_alignment["exam_deployment_status"],
                "workspace_card_status": timeline_receipt_journal_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": timeline_receipt_journal_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": timeline_receipt_journal_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": timeline_receipt_journal_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": timeline_receipt_journal_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": timeline_receipt_journal_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_timeline_receipt_journal_gate_linked": timeline_receipt_journal_alignment[
                    "workspace_card_timeline_receipt_journal_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": timeline_receipt_journal_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": timeline_receipt_journal_alignment["raw_workspace_card_returned"],
            },
        },
        {
            "check_id": "timeline_export_review_packet",
            "passed": timeline_review_packet_alignment["status"] == "ready"
            and timeline_review_packet_alignment["alignment_public_safety_status"] == "pass"
            and timeline_review_packet_alignment["failed_contract_ids"] == []
            and timeline_review_packet_alignment["review_packet_status"] == "timeline_export_review_packet_ready"
            and timeline_review_packet_alignment["receipt_status"]
            == "timeline_export_review_packet_receipt_ready_not_exam_clearance"
            and timeline_review_packet_alignment["local_write_started"] is False
            and timeline_review_packet_alignment["event_count"] >= 1
            and timeline_review_packet_alignment["reviewer_question_count"] >= 1
            and timeline_review_packet_alignment["exam_deployment_status"] == "not_cleared"
            and timeline_review_packet_alignment["workspace_card_readiness_gate_linked"] is True
            and timeline_review_packet_alignment["workspace_card_timeline_review_packet_gate_linked"] is True
            and timeline_review_packet_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "workspace_card_review_alignment_status": timeline_review_packet_alignment["status"],
                "workspace_card_review_alignment_public_safety_status": timeline_review_packet_alignment[
                    "alignment_public_safety_status"
                ],
                "review_packet_status": timeline_review_packet_alignment["review_packet_status"],
                "receipt_status": timeline_review_packet_alignment["receipt_status"],
                "local_write_started": timeline_review_packet_alignment["local_write_started"],
                "operator_confirmation_required_for_write": timeline_review_packet_alignment[
                    "operator_confirmation_required_for_write"
                ],
                "event_count": timeline_review_packet_alignment["event_count"],
                "skill_count": timeline_review_packet_alignment["skill_count"],
                "reviewer_question_count": timeline_review_packet_alignment["reviewer_question_count"],
                "checkpoint_hash_count": timeline_review_packet_alignment["checkpoint_hash_count"],
                "open_operator_confirmation_count": timeline_review_packet_alignment[
                    "open_operator_confirmation_count"
                ],
                "exam_deployment_status": timeline_review_packet_alignment["exam_deployment_status"],
                "workspace_card_status": timeline_review_packet_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": timeline_review_packet_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": timeline_review_packet_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": timeline_review_packet_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": timeline_review_packet_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": timeline_review_packet_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_timeline_review_packet_gate_linked": timeline_review_packet_alignment[
                    "workspace_card_timeline_review_packet_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": timeline_review_packet_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": timeline_review_packet_alignment["raw_workspace_card_returned"],
            },
        },
        {
            "check_id": "material_coverage_run",
            "passed": material_coverage_run_alignment["status"] == "ready"
            and material_coverage_run_alignment["alignment_public_safety_status"] == "pass"
            and material_coverage_run_alignment["failed_contract_ids"] == []
            and material_coverage_run_alignment["coverage_status"]
            in {
                "course_material_coverage_needs_materials",
                "course_material_coverage_needs_private_manifest_apply",
                "course_material_coverage_needs_tutor_index_build",
                "course_material_coverage_ready_for_exam_workspace",
                "course_material_coverage_needs_extraction_or_transcription",
                "course_material_coverage_needs_anchor_review",
            }
            and material_coverage_run_alignment["receipt_status"]
            == "material_coverage_receipt_ready_not_exam_clearance"
            and material_coverage_run_alignment["skill_count"] >= 1
            and material_coverage_run_alignment["visible_skill_count"] >= 1
            and material_coverage_run_alignment["source_anchor_count"] >= 0
            and material_coverage_run_alignment["notebook_anchor_count"] >= 0
            and material_coverage_run_alignment["ocr_gap_count"] >= 0
            and material_coverage_run_alignment["video_gap_count"] >= 0
            and material_coverage_run_alignment["exam_deployment_status"] == "not_cleared"
            and material_coverage_run_alignment["workspace_card_readiness_gate_linked"] is True
            and material_coverage_run_alignment["workspace_card_material_coverage_gate_linked"] is True
            and material_coverage_run_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "workspace_card_coverage_alignment_status": material_coverage_run_alignment["status"],
                "workspace_card_coverage_alignment_public_safety_status": material_coverage_run_alignment[
                    "alignment_public_safety_status"
                ],
                "coverage_status": material_coverage_run_alignment["coverage_status"],
                "receipt_status": material_coverage_run_alignment["receipt_status"],
                "skill_count": material_coverage_run_alignment["skill_count"],
                "visible_skill_count": material_coverage_run_alignment["visible_skill_count"],
                "source_anchor_count": material_coverage_run_alignment["source_anchor_count"],
                "notebook_anchor_count": material_coverage_run_alignment["notebook_anchor_count"],
                "ocr_gap_count": material_coverage_run_alignment["ocr_gap_count"],
                "video_gap_count": material_coverage_run_alignment["video_gap_count"],
                "exam_deployment_status": material_coverage_run_alignment["exam_deployment_status"],
                "workspace_card_status": material_coverage_run_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": material_coverage_run_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": material_coverage_run_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": material_coverage_run_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": material_coverage_run_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": material_coverage_run_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_material_coverage_gate_linked": material_coverage_run_alignment[
                    "workspace_card_material_coverage_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": material_coverage_run_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": material_coverage_run_alignment["raw_workspace_card_returned"],
            },
        },
        {
            "check_id": "course_exam_coverage_dashboard",
            "passed": course_exam_coverage_dashboard_alignment["status"] == "ready"
            and course_exam_coverage_dashboard_alignment["alignment_public_safety_status"] == "pass"
            and course_exam_coverage_dashboard_alignment["failed_contract_ids"] == []
            and course_exam_coverage_dashboard_alignment["dashboard_status"]
            == "course_exam_coverage_dashboard_ready"
            and course_exam_coverage_dashboard_alignment["receipt_status"]
            == "dashboard_receipt_ready_not_exam_clearance"
            and course_exam_coverage_dashboard_alignment["skill_count"] >= 1
            and course_exam_coverage_dashboard_alignment["visible_skill_count"] >= 1
            and course_exam_coverage_dashboard_alignment["workspace_ready_skill_count"] >= 0
            and course_exam_coverage_dashboard_alignment["checkpoint_hash_count"] >= 0
            and course_exam_coverage_dashboard_alignment["open_operator_confirmation_count"] >= 0
            and course_exam_coverage_dashboard_alignment["exam_deployment_status"] == "not_cleared"
            and course_exam_coverage_dashboard_alignment["workspace_card_readiness_gate_linked"] is True
            and course_exam_coverage_dashboard_alignment["workspace_card_course_exam_dashboard_gate_linked"] is True
            and course_exam_coverage_dashboard_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "workspace_card_dashboard_alignment_status": course_exam_coverage_dashboard_alignment["status"],
                "workspace_card_dashboard_alignment_public_safety_status": course_exam_coverage_dashboard_alignment[
                    "alignment_public_safety_status"
                ],
                "dashboard_status": course_exam_coverage_dashboard_alignment["dashboard_status"],
                "receipt_status": course_exam_coverage_dashboard_alignment["receipt_status"],
                "skill_count": course_exam_coverage_dashboard_alignment["skill_count"],
                "visible_skill_count": course_exam_coverage_dashboard_alignment["visible_skill_count"],
                "workspace_ready_skill_count": course_exam_coverage_dashboard_alignment[
                    "workspace_ready_skill_count"
                ],
                "checkpoint_hash_count": course_exam_coverage_dashboard_alignment["checkpoint_hash_count"],
                "open_operator_confirmation_count": course_exam_coverage_dashboard_alignment[
                    "open_operator_confirmation_count"
                ],
                "exam_deployment_status": course_exam_coverage_dashboard_alignment["exam_deployment_status"],
                "workspace_card_status": course_exam_coverage_dashboard_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": course_exam_coverage_dashboard_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": course_exam_coverage_dashboard_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": course_exam_coverage_dashboard_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": course_exam_coverage_dashboard_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": course_exam_coverage_dashboard_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_course_exam_dashboard_gate_linked": course_exam_coverage_dashboard_alignment[
                    "workspace_card_course_exam_dashboard_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": course_exam_coverage_dashboard_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": course_exam_coverage_dashboard_alignment[
                    "raw_workspace_card_returned"
                ],
            },
        },
        {
            "check_id": "course_per_skill_action_router",
            "passed": course_per_skill_action_router_alignment["status"] == "ready"
            and course_per_skill_action_router_alignment["alignment_public_safety_status"] == "pass"
            and course_per_skill_action_router_alignment["failed_contract_ids"] == []
            and course_per_skill_action_router_alignment["router_status"] == "course_per_skill_action_router_ready"
            and course_per_skill_action_router_alignment["receipt_status"]
            == "router_receipt_ready_not_exam_clearance"
            and course_per_skill_action_router_alignment["route_id"] != "missing"
            and course_per_skill_action_router_alignment["route_endpoint"] != ""
            and course_per_skill_action_router_alignment["dry_run_by_default"] is True
            and course_per_skill_action_router_alignment["requires_operator_confirmation_for_local_writes"] is True
            and course_per_skill_action_router_alignment["route_count"] >= 1
            and course_per_skill_action_router_alignment["exam_deployment_status"] == "not_cleared"
            and course_per_skill_action_router_alignment["workspace_card_readiness_gate_linked"] is True
            and course_per_skill_action_router_alignment["workspace_card_course_per_skill_router_gate_linked"] is True
            and course_per_skill_action_router_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "workspace_card_route_alignment_status": course_per_skill_action_router_alignment["status"],
                "workspace_card_route_alignment_public_safety_status": course_per_skill_action_router_alignment[
                    "alignment_public_safety_status"
                ],
                "router_status": course_per_skill_action_router_alignment["router_status"],
                "receipt_status": course_per_skill_action_router_alignment["receipt_status"],
                "skill_tag": course_per_skill_action_router_alignment["skill_tag"],
                "route_id": course_per_skill_action_router_alignment["route_id"],
                "route_endpoint": course_per_skill_action_router_alignment["route_endpoint"],
                "dry_run_by_default": course_per_skill_action_router_alignment["dry_run_by_default"],
                "requires_operator_confirmation_for_local_writes": course_per_skill_action_router_alignment[
                    "requires_operator_confirmation_for_local_writes"
                ],
                "open_operator_confirmation_count": course_per_skill_action_router_alignment[
                    "open_operator_confirmation_count"
                ],
                "open_operator_confirmation_route_count": course_per_skill_action_router_alignment[
                    "open_operator_confirmation_route_count"
                ],
                "route_count": course_per_skill_action_router_alignment["route_count"],
                "exam_deployment_status": course_per_skill_action_router_alignment["exam_deployment_status"],
                "workspace_card_status": course_per_skill_action_router_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": course_per_skill_action_router_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": course_per_skill_action_router_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": course_per_skill_action_router_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": course_per_skill_action_router_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": course_per_skill_action_router_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_course_per_skill_router_gate_linked": course_per_skill_action_router_alignment[
                    "workspace_card_course_per_skill_router_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": course_per_skill_action_router_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": course_per_skill_action_router_alignment[
                    "raw_workspace_card_returned"
                ],
            },
        },
        {
            "check_id": "routed_action_executor",
            "passed": routed_action_executor_alignment["status"] == "ready"
            and routed_action_executor_alignment["alignment_public_safety_status"] == "pass"
            and routed_action_executor_alignment["failed_contract_ids"] == []
            and routed_action_executor_alignment["executor_status"] == "routed_action_executor_ready"
            and routed_action_executor_alignment["receipt_status"] == "executor_receipt_ready_not_exam_clearance"
            and routed_action_executor_alignment["route_id"] != "missing"
            and routed_action_executor_alignment["executed_artifact_type"] != "missing"
            and routed_action_executor_alignment["executed_status"] != "missing"
            and routed_action_executor_alignment["executed_result_hash_present"] is True
            and routed_action_executor_alignment["local_write_started"] is False
            and routed_action_executor_alignment["dry_run_by_default"] is True
            and routed_action_executor_alignment["local_write_confirmations_are_explicit"] is True
            and routed_action_executor_alignment["exam_deployment_status"] == "not_cleared"
            and routed_action_executor_alignment["workspace_card_readiness_gate_linked"] is True
            and routed_action_executor_alignment["workspace_card_routed_action_executor_gate_linked"] is True
            and routed_action_executor_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "workspace_card_execution_alignment_status": routed_action_executor_alignment["status"],
                "workspace_card_execution_alignment_public_safety_status": routed_action_executor_alignment[
                    "alignment_public_safety_status"
                ],
                "executor_status": routed_action_executor_alignment["executor_status"],
                "receipt_status": routed_action_executor_alignment["receipt_status"],
                "route_id": routed_action_executor_alignment["route_id"],
                "executed_endpoint": routed_action_executor_alignment["executed_endpoint"],
                "executed_artifact_type": routed_action_executor_alignment["executed_artifact_type"],
                "executed_status": routed_action_executor_alignment["executed_status"],
                "executed_result_hash_present": routed_action_executor_alignment["executed_result_hash_present"],
                "local_write_started": routed_action_executor_alignment["local_write_started"],
                "dry_run_by_default": routed_action_executor_alignment["dry_run_by_default"],
                "local_write_confirmations_are_explicit": routed_action_executor_alignment[
                    "local_write_confirmations_are_explicit"
                ],
                "exam_deployment_status": routed_action_executor_alignment["exam_deployment_status"],
                "workspace_card_status": routed_action_executor_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": routed_action_executor_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": routed_action_executor_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": routed_action_executor_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": routed_action_executor_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": routed_action_executor_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_routed_action_executor_gate_linked": routed_action_executor_alignment[
                    "workspace_card_routed_action_executor_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": routed_action_executor_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": routed_action_executor_alignment["raw_workspace_card_returned"],
            },
        },
        {
            "check_id": "exam_run_packet",
            "passed": exam_run_packet_alignment["status"] == "ready"
            and exam_run_packet_alignment["alignment_public_safety_status"] == "pass"
            and exam_run_packet_alignment["failed_contract_ids"] == []
            and exam_run_packet_alignment["packet_status"] == "exam_run_packet_ready"
            and exam_run_packet_alignment["receipt_status"] == "exam_run_packet_receipt_ready_not_exam_clearance"
            and exam_run_packet_alignment["route_id"] != "missing"
            and exam_run_packet_alignment["executed_artifact_type"] != "missing"
            and exam_run_packet_alignment["executed_status"] != "missing"
            and exam_run_packet_alignment["executed_result_hash_present"] is True
            and exam_run_packet_alignment["local_write_started"] is False
            and exam_run_packet_alignment["local_cycle_chain_snapshot_status"]
            == "python_exam_local_cycle_chain_snapshot_ready"
            and exam_run_packet_alignment["local_cycle_chain_snapshot_hash_present"] is True
            and exam_run_packet_alignment["exam_deployment_status"] == "not_cleared"
            and exam_run_packet_alignment["workspace_card_readiness_gate_linked"] is True
            and exam_run_packet_alignment["workspace_card_exam_run_packet_gate_linked"] is True
            and exam_run_packet_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "workspace_card_packet_alignment_status": exam_run_packet_alignment["status"],
                "workspace_card_packet_alignment_public_safety_status": exam_run_packet_alignment[
                    "alignment_public_safety_status"
                ],
                "packet_status": exam_run_packet_alignment["packet_status"],
                "receipt_status": exam_run_packet_alignment["receipt_status"],
                "route_id": exam_run_packet_alignment["route_id"],
                "executed_artifact_type": exam_run_packet_alignment["executed_artifact_type"],
                "executed_status": exam_run_packet_alignment["executed_status"],
                "executed_result_hash_present": exam_run_packet_alignment["executed_result_hash_present"],
                "local_write_started": exam_run_packet_alignment["local_write_started"],
                "local_cycle_chain_snapshot_status": exam_run_packet_alignment[
                    "local_cycle_chain_snapshot_status"
                ],
                "local_cycle_chain_snapshot_hash_present": exam_run_packet_alignment[
                    "local_cycle_chain_snapshot_hash_present"
                ],
                "exam_deployment_status": exam_run_packet_alignment["exam_deployment_status"],
                "workspace_card_status": exam_run_packet_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": exam_run_packet_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": exam_run_packet_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": exam_run_packet_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": exam_run_packet_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": exam_run_packet_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_exam_run_packet_gate_linked": exam_run_packet_alignment[
                    "workspace_card_exam_run_packet_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": exam_run_packet_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": exam_run_packet_alignment["raw_workspace_card_returned"],
            },
        },
        {
            "check_id": "exam_packet_timeline",
            "passed": exam_packet_timeline_alignment["status"] == "ready"
            and exam_packet_timeline_alignment["alignment_public_safety_status"] == "pass"
            and exam_packet_timeline_alignment["failed_contract_ids"] == []
            and exam_packet_timeline_alignment["timeline_status"] == "exam_packet_timeline_ready"
            and exam_packet_timeline_alignment["receipt_status"] == "exam_packet_timeline_receipt_ready_not_exam_clearance"
            and exam_packet_timeline_alignment["event_count"] >= 1
            and exam_packet_timeline_alignment["visible_event_count"] >= 1
            and exam_packet_timeline_alignment["packet_receipt_count"] >= 1
            and exam_packet_timeline_alignment["export_review_preview_status"] == "timeline_export_review_ready"
            and exam_packet_timeline_alignment["exam_deployment_status"] == "not_cleared"
            and exam_packet_timeline_alignment["workspace_card_readiness_gate_linked"] is True
            and exam_packet_timeline_alignment["workspace_card_exam_packet_timeline_gate_linked"] is True
            and exam_packet_timeline_alignment["raw_workspace_card_returned"] is False,
            "evidence": {
                "workspace_card_timeline_alignment_status": exam_packet_timeline_alignment["status"],
                "workspace_card_timeline_alignment_public_safety_status": exam_packet_timeline_alignment[
                    "alignment_public_safety_status"
                ],
                "timeline_status": exam_packet_timeline_alignment["timeline_status"],
                "receipt_status": exam_packet_timeline_alignment["receipt_status"],
                "event_count": exam_packet_timeline_alignment["event_count"],
                "visible_event_count": exam_packet_timeline_alignment["visible_event_count"],
                "packet_receipt_count": exam_packet_timeline_alignment["packet_receipt_count"],
                "checkpoint_hash_count": exam_packet_timeline_alignment["checkpoint_hash_count"],
                "open_operator_confirmation_count": exam_packet_timeline_alignment[
                    "open_operator_confirmation_count"
                ],
                "export_review_preview_status": exam_packet_timeline_alignment["export_review_preview_status"],
                "exam_deployment_status": exam_packet_timeline_alignment["exam_deployment_status"],
                "workspace_card_status": exam_packet_timeline_alignment["workspace_card_status"],
                "workspace_card_selected_skill_tag": exam_packet_timeline_alignment[
                    "workspace_card_selected_skill_tag"
                ],
                "workspace_card_ready_for_operator_prefill": exam_packet_timeline_alignment[
                    "workspace_card_ready_for_operator_prefill"
                ],
                "workspace_card_help_ledger_status": exam_packet_timeline_alignment[
                    "workspace_card_help_ledger_status"
                ],
                "workspace_card_help_ledger_hash_present": exam_packet_timeline_alignment[
                    "workspace_card_help_ledger_hash_present"
                ],
                "workspace_card_readiness_gate_linked": exam_packet_timeline_alignment[
                    "workspace_card_readiness_gate_linked"
                ],
                "workspace_card_exam_packet_timeline_gate_linked": exam_packet_timeline_alignment[
                    "workspace_card_exam_packet_timeline_gate_linked"
                ],
                "workspace_card_readiness_gate_claim_linked": exam_packet_timeline_alignment[
                    "workspace_card_readiness_gate_claim_linked"
                ],
                "raw_workspace_card_returned": exam_packet_timeline_alignment["raw_workspace_card_returned"],
            },
        },
    ]
    failed = [check for check in checks if not check["passed"]]
    report = {
        "schema_version": READINESS_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "public_draft_ready" if not failed else "blocked",
        "exam_deployment_status": "not_cleared",
        "ready_for": ["public draft review", "local practice demo"] if not failed else [],
        "not_ready_for": ["exam deployment", "official grading", "proctoring", "KI-detection use"],
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "checks": checks,
        "runtime_guard": runtime_guard,
        "source_card_drift": source_card_drift,
        "policy": "Readiness means public-safe draft only, not exam clearance or legal approval.",
    }
    report["evidence_snapshot"] = build_readiness_evidence_snapshot(report)
    return report


def build_readiness_markdown(paths: Iterable[str | Path] | None = None) -> str:
    report = run_readiness_check(paths)
    check_lines = "\n".join(
        f"- `{check['check_id']}`: {'pass' if check['passed'] else 'blocked'}" for check in report["checks"]
    )
    return (
        "# UniBot Readiness Check\n\n"
        f"Status: {report['status']}\n\n"
        f"Exam deployment: {report['exam_deployment_status']}\n\n"
        f"Passed: {report['passed_count']}/{report['check_count']}\n\n"
        f"Runtime guard: {report['runtime_guard']['status']} "
        f"({report['runtime_guard']['routine_budget']['default_execution_mode']}, "
        f"full suite default: {report['runtime_guard']['routine_budget']['full_suite_required_by_default']})\n\n"
        f"Source-card drift: {report['source_card_drift']['status']} "
        f"({report['source_card_drift']['card_count']} cards, "
        f"{report['source_card_drift']['required_source_card_count']} required)\n\n"
        f"Evidence snapshot: {report['evidence_snapshot']['status']} "
        f"({report['evidence_snapshot']['scientific_gate_passed_count']}/"
        f"{report['evidence_snapshot']['scientific_gate_count']} scientific gates)\n\n"
        "## Checks\n\n"
        f"{check_lines}\n\n"
        f"Policy: {report['policy']}\n"
    )
