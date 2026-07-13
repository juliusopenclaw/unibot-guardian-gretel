from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .evaluation import build_evaluation_packet
from .public_safety import scan_text
from .source_cards import build_source_card_drift_report, get_source_card


BACHELOR_THESIS_SCHEMA_VERSION = "unibot-gretel-bachelor-thesis-package-v1"
BACHELOR_THESIS_EVALUATION_CLAIM_ALIGNMENT_SCHEMA_VERSION = "unibot-gretel-thesis-evaluation-claim-alignment-v1"


def build_bachelor_thesis_evidence_index() -> dict[str, Any]:
    source_drift = build_source_card_drift_report()
    evidence_items = [
        {
            "claim_id": "gretel_authorship_label",
            "claim": "The public UniBot package is labelled as built and documented by Gretel, not Julius.",
            "evidence_type": "package_field_and_test",
            "artifact_refs": ["unibot/bachelor_thesis.py", "tests/test_unibot_bachelor_thesis.py"],
            "readiness_check_ids": ["gretel_bachelor_thesis_package"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_bachelor_thesis.py -q"],
            "source_card_ids": [],
            "human_gate": "human_submission_review_required",
        },
        {
            "claim_id": "glm_52_basis",
            "claim": "GLM-5.2 is the primary public-safe proposal model basis, with provider calls disabled by default.",
            "evidence_type": "source_cards_and_review_gate",
            "artifact_refs": [
                "unibot/bachelor_thesis.py",
                "unibot/gretel_glm_evolve.py",
                "docs/unibot/UNIBOT_GRETEL_GLM_EVOLVE_LANE.md",
            ],
            "readiness_check_ids": ["gretel_glm_evolve_lane", "gretel_bachelor_thesis_package"],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_bachelor_thesis.py tests/test_unibot_gretel_glm_evolve.py -q"
            ],
            "source_card_ids": ["zai-glm-52", "zai-glm-52-migration", "zai-glm-pricing"],
            "human_gate": "provider_call_requires_explicit_go_and_redaction_receipt",
        },
        {
            "claim_id": "source_bound_public_science",
            "claim": "Scientific and university-facing claims are anchored to required public source cards.",
            "evidence_type": "source_card_drift_report",
            "artifact_refs": ["unibot/source_cards.py", "unibot/readiness.py", "docs/unibot/UNIBOT_READINESS_CHECK.md"],
            "readiness_check_ids": ["source_cards", "source_card_drift_guard"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_api_and_public_safety.py tests/test_unibot_readiness.py -q"],
            "source_card_ids": ["dfg-gwp", "eu-ai-act-2024", "gdpr-2016-679", "uoc-ki-faq", "zai-glm-52"],
            "human_gate": "human_submission_review_required",
        },
        {
            "claim_id": "public_safety_and_privacy",
            "claim": "The package stays public-safe and blocks local paths, secrets, raw transcripts, private course material, and personal data.",
            "evidence_type": "public_safety_scan",
            "artifact_refs": ["unibot/public_safety.py", "tests/test_unibot_api_and_public_safety.py"],
            "readiness_check_ids": ["public_safety", "data_protection_screening"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_api_and_public_safety.py tests/test_unibot_privacy.py -q"],
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "chrome-limited-use"],
            "human_gate": "public_safety_required",
        },
        {
            "claim_id": "exam_boundary_not_clearance",
            "claim": "UniBot is a practice and review system, not exam clearance, grading, proctoring, or AI-detection evidence.",
            "evidence_type": "readiness_and_publication_gate",
            "artifact_refs": ["unibot/publication.py", "unibot/readiness.py", "unibot/compliance.py"],
            "readiness_check_ids": ["exam_boundary", "publication_package", "compliance_matrix"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_publication.py tests/test_unibot_compliance.py -q"],
            "source_card_ids": ["hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq", "eu-ai-act-2024"],
            "human_gate": "written_university_clearance_required_before_exam_use",
        },
        {
            "claim_id": "reproducible_evaluation_package",
            "claim": "Synthetic tasks, red-team checks, readiness, and publication gates make the research package reproducible.",
            "evidence_type": "test_and_readiness_suite",
            "artifact_refs": ["unibot/evaluation.py", "unibot/redteam.py", "unibot/readiness.py", "unibot/publication.py"],
            "readiness_check_ids": ["evaluation_packet", "redteam", "publication_package"],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_evaluation.py tests/test_unibot_redteam.py tests/test_unibot_publication.py -q"
            ],
            "source_card_ids": ["openai-evals", "dfg-gwp", "vanlehn-2011", "kulik-fletcher-2016"],
            "human_gate": "human_submission_review_required",
        },
        {
            "claim_id": "evaluation_learner_agency_boundary",
            "claim": (
                "Bachelor-thesis claims about learner agency are backed by evaluation and adaptive-task boundary "
                "alignment, not by broad performance, grading, or exam-readiness claims."
            ),
            "evidence_type": "evaluation_and_adaptive_boundary_alignment",
            "artifact_refs": [
                "unibot/evaluation.py",
                "unibot/adaptive_tasks.py",
                "docs/unibot/UNIBOT_DEMO_TEST_PLAN.md",
                "docs/unibot/UNIBOT_ADAPTIVE_TASKS.md",
            ],
            "readiness_check_ids": ["evaluation_packet", "adaptive_task_plan", "gretel_bachelor_thesis_package"],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_evaluation.py tests/test_unibot_adaptive_tasks.py tests/test_unibot_bachelor_thesis.py -q"
            ],
            "source_card_ids": ["dfg-gwp", "unesco-genai-2023", "vanlehn-2011"],
            "human_gate": "human_submission_review_required",
        },
        {
            "claim_id": "workspace_card_thesis_glm_link",
            "claim": (
                "Gretel bachelor-thesis authorship/evidence and GLM-method metadata are linked to the "
                "local-cycle operator workspace-card readiness gate by hashes, without returning raw workspace data."
            ),
            "evidence_type": "hash_linked_workspace_card_gate",
            "artifact_refs": ["unibot/bachelor_thesis.py", "unibot/python_exam_local_cycle_operator_workspace_card.py"],
            "readiness_check_ids": ["gretel_bachelor_thesis_package", "python_exam_local_cycle_operator_workspace_card"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_bachelor_thesis.py tests/test_unibot_readiness.py -q"],
            "source_card_ids": ["dfg-gwp", "zai-glm-52"],
            "human_gate": "human_submission_review_required",
        },
        {
            "claim_id": "complete_gretel_thesis_manuscript",
            "claim": (
                "The public package includes a chaptered Gretel-authored manuscript covering research question, "
                "related work, method, system, evaluation, results, limitations, ethics, privacy, and reproducibility."
            ),
            "evidence_type": "public_manuscript_and_test",
            "artifact_refs": [
                "docs/thesis/UNIBOT_GRETEL_BACHELOR_THESIS_MANUSCRIPT.md",
                "unibot/bachelor_thesis.py",
                "tests/test_unibot_bachelor_thesis.py",
            ],
            "readiness_check_ids": ["gretel_bachelor_thesis_package"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_bachelor_thesis.py -q"],
            "source_card_ids": ["dfg-gwp", "vanlehn-2011", "gdpr-2016-679", "zai-glm-52"],
            "human_gate": "human_submission_review_required",
        },
    ]
    index = {
        "schema_version": "unibot-gretel-bachelor-thesis-evidence-index-v1",
        "status": "ready",
        "source_card_drift_status": source_drift["status"],
        "source_card_drift_public_safety_status": source_drift["public_safety_status"],
        "source_card_count": source_drift["card_count"],
        "required_source_card_count": source_drift["required_source_card_count"],
        "claim_count": len(evidence_items),
        "evidence_items": evidence_items,
        "required_readiness_check_ids": sorted(
            {check_id for item in evidence_items for check_id in item["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({item["human_gate"] for item in evidence_items}),
        "policy": (
            "Bachelor-thesis-level claims remain draft claims unless their evidence item has tests, readiness checks, "
            "source-card anchors where applicable, and a human gate for real submission or exam use."
        ),
    }
    scan = scan_text(json.dumps(index, ensure_ascii=False), "unibot-gretel-bachelor-thesis-evidence-index")
    index["public_safety_status"] = scan["status"]
    if scan["status"] != "pass" or source_drift["status"] != "pass":
        index["status"] = "blocked"
    return index


def build_bachelor_thesis_evaluation_claim_alignment(
    evidence_index: dict[str, Any] | None = None,
    evaluation_packet: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    thesis_package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if evidence_index is None:
        evidence_index = build_bachelor_thesis_evidence_index()
    if evaluation_packet is None:
        evaluation_packet = build_evaluation_packet()
    thesis_hash_basis = thesis_package if isinstance(thesis_package, dict) else default_bachelor_thesis_hash_basis(evidence_index)
    thesis_evidence_hash = bachelor_thesis_authorship_evidence_hash(thesis_hash_basis)
    glm_method_hash = bachelor_thesis_glm_method_hash(thesis_hash_basis)
    workspace_card = safe_bachelor_thesis_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_bachelor_thesis_workspace_card(),
        thesis_evidence_hash=thesis_evidence_hash,
        glm_method_hash=glm_method_hash,
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

    evidence_items = {item["claim_id"]: item for item in evidence_index.get("evidence_items", [])}
    evaluation_alignment = evaluation_packet.get("learner_agency_boundary_alignment", {})
    required_source_card_ids = sorted(
        {
            source_id
            for item in evidence_index.get("evidence_items", [])
            for source_id in item.get("source_card_ids", [])
        }
        | {"dfg-gwp", "unesco-genai-2023", "vanlehn-2011", "kulik-fletcher-2016"}
    )
    sections = [
        {
            "section_id": "learner_agency_claim_trace",
            "claim_ids": ["evaluation_learner_agency_boundary", "reproducible_evaluation_package"],
            "evaluation_alignment_status": evaluation_alignment.get("status", ""),
            "readiness_check_ids": ["evaluation_packet", "adaptive_task_plan", "gretel_bachelor_thesis_package"],
            "source_card_ids": ["unesco-genai-2023", "vanlehn-2011"],
            "human_gates": ["human_submission_review_required"],
            "boundary": "thesis learner-agency claims must trace to synthetic evaluation and adaptive practice safeguards",
        },
        {
            "section_id": "no_high_stakes_claim",
            "claim_ids": ["exam_boundary_not_clearance", "evaluation_learner_agency_boundary"],
            "evaluation_boundaries": evaluation_packet.get("boundaries", []),
            "excluded_measures": evaluation_packet.get("measurement_plan", {}).get("excluded_measures", []),
            "readiness_check_ids": ["exam_boundary", "evaluation_packet", "compliance_matrix"],
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "uoc-ki-faq"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "human_submission_review_required"],
            "boundary": "learner-agency evidence cannot be promoted into grades, exam clearance, proctoring, or AI-detection evidence",
        },
        {
            "section_id": "source_card_claim_trace",
            "claim_ids": ["source_bound_public_science", "evaluation_learner_agency_boundary"],
            "source_card_ids": required_source_card_ids,
            "readiness_check_ids": ["source_cards", "source_card_drift_guard", "gretel_bachelor_thesis_package"],
            "human_gates": ["human_submission_review_required"],
            "boundary": "external claims remain anchored to public source cards and drift checks",
        },
        {
            "section_id": "submission_review_trace",
            "claim_ids": ["gretel_authorship_label", "evaluation_learner_agency_boundary"],
            "readiness_check_ids": ["gretel_bachelor_thesis_package", "review_board_packet"],
            "source_card_ids": [],
            "human_gates": sorted(evidence_index.get("required_human_gates", [])),
            "boundary": "Gretel authorship and thesis-level rigor remain human-reviewed draft claims, not real submission authority",
        },
        {
            "section_id": "workspace_card_thesis_glm_trace",
            "claim_ids": ["workspace_card_thesis_glm_link", "glm_52_basis", "gretel_authorship_label"],
            "readiness_check_ids": ["gretel_bachelor_thesis_package", "python_exam_local_cycle_operator_workspace_card"],
            "source_card_ids": ["dfg-gwp", "zai-glm-52"],
            "human_gates": ["human_submission_review_required", "written_university_clearance_required_before_exam_use"],
            "boundary": (
                "workspace-card prefill evidence may link thesis and GLM metadata by hash only; it is not "
                "university submission, exam clearance, grading, proctoring, or AI-detection evidence"
            ),
        },
    ]
    payload = json.dumps(
        {"evidence_index": evidence_index, "evaluation_alignment": evaluation_alignment, "sections": sections},
        ensure_ascii=False,
        sort_keys=True,
    )
    payload_scan = scan_text(payload, "gretel-thesis-evaluation-claim-alignment")
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    contracts = {
        "evaluation_claim_exists": "evaluation_learner_agency_boundary" in evidence_items,
        "evaluation_alignment_ready": evaluation_alignment.get("status") == "ready"
        and evaluation_alignment.get("public_safety_status") == "pass",
        "adaptive_trace_in_evaluation_ready": evaluation_alignment.get("contracts", {}).get("adaptive_plan_boundary_ready") is True,
        "high_stakes_claims_excluded": {
            "official grades",
            "real exam performance",
            "disciplinary KI detection",
        }.issubset(set(evaluation_packet.get("measurement_plan", {}).get("excluded_measures", []))),
        "thesis_human_gated": "human_submission_review_required" in evidence_index.get("required_human_gates", [])
        and "written_university_clearance_required_before_exam_use" in evidence_index.get("required_human_gates", []),
        "workspace_card_bachelor_thesis_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == thesis_evidence_hash
        and workspace_card.get("task_hash") == glm_method_hash,
        "payload_public_safe": payload_scan["status"] == "pass",
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    status = "ready" if not missing_source_card_ids and not failed_contract_ids else "needs_review"
    return {
        "schema_version": BACHELOR_THESIS_EVALUATION_CLAIM_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "contracts": contracts,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_bachelor_thesis_gate_linked": contracts["workspace_card_bachelor_thesis_gate_linked"],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in sorted({check_id for section in sections for check_id in section["readiness_check_ids"]}),
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "thesis_evidence_hash": thesis_evidence_hash,
        "glm_method_hash": glm_method_hash,
        "public_safety_status": payload_scan["status"],
        "policy": (
            "Bachelor-thesis evaluation claim alignment is a public review aid only; it does not authorize "
            "real submission, grading, exam clearance, proctoring, KI-detection evidence, provider calls, "
            "private course text, local paths, or student data."
        ),
    }


def default_bachelor_thesis_hash_basis(evidence_index: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "public_scientific_draft_bachelor_thesis_level_not_real_submission",
        "submission_type": "bachelor_thesis_level_research_package_not_real_university_submission",
        "authorship_statement": {
            "builder": "Gretel",
            "documentation_author": "Gretel",
            "builder_identity": "AI implementation and documentation agent",
            "orchestration_surface": "Codex local automation",
            "programmer_claim": "This public package is labelled as built and documented by Gretel, not by Julius.",
            "institutional_status": "not a real thesis submission and not institutionally approved by this artifact",
        },
        "glm_technology_basis": {
            "primary_model_hint": "zai/glm-5.2",
            "provider": "Z.AI",
            "provider_call_default": "disabled",
            "provider_scope_when_enabled": "public-unibot-only",
            "model_permissions": "proposal and independent review only; no tools, apply, push, merge, or Final-Go",
            "official_source_card_ids": ["zai-glm-52", "zai-glm-52-migration", "zai-glm-pricing"],
        },
        "research_question": (
            "How can a public, source-bound AI practice layer support coding learners without replacing "
            "their own work, leaking private material, or claiming exam clearance?"
        ),
        "scientific_contribution": [
            "A Socratic integrity layer that blocks final-answer outsourcing while preserving learner reflection.",
            "A public-safety scanner for paths, secrets, personal data, raw AI transcripts, and private course references.",
            "A reproducible publication and readiness package based on synthetic tasks and source cards.",
            "A GLM-5.2-ready proposal lane that turns model ideas into tests, review entries, or blocked reasons.",
            "A clear exam boundary: practice and review are supported; official grading, proctoring, and exam clearance are blocked.",
        ],
        "methodology": [
            "Three Golden Rules define allowed and blocked learning support.",
            "Public source cards anchor legal, institutional, privacy, technical, and educational claims.",
            "Synthetic scenarios and red-team checks test likely failure modes.",
            "Readiness and publication gates require public-safety pass results before public release.",
            "Accepted improvements must be converted into regression tests, red-team cases, documentation, or review-board decisions.",
        ],
        "review_gates": {
            "public_safety_required": True,
            "written_university_clearance_required_before_exam_use": True,
            "human_submission_review_required": True,
            "no_autonomous_github_publish": True,
            "no_final_go_by_gretel_or_glm": True,
            "provider_call_requires_explicit_go_and_redaction_receipt": True,
        },
        "evidence_index": evidence_index,
    }


def bachelor_thesis_authorship_evidence_hash(package: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "status": package.get("status", ""),
                "submission_type": package.get("submission_type", ""),
                "authorship_statement": package.get("authorship_statement", {}),
                "review_gates": package.get("review_gates", {}),
                "evidence_index": package.get("evidence_index", {}),
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def bachelor_thesis_glm_method_hash(package: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "glm_technology_basis": package.get("glm_technology_basis", {}),
                "research_question": package.get("research_question", ""),
                "scientific_contribution": package.get("scientific_contribution", []),
                "methodology": package.get("methodology", []),
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def synthetic_bachelor_thesis_workspace_card() -> dict[str, Any]:
    preview_hash = hashlib.sha256(b"synthetic bachelor thesis workspace card").hexdigest()
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic bachelor-thesis package prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_bachelor_thesis_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_bachelor_thesis_package_before_manual_submission_discussion",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__BACHELOR_THESIS_GLM_METHOD_HASH__",
            "checkpoint_hash": "__BACHELOR_THESIS_EVIDENCE_HASH__",
            "source_card_ids": ["dfg-gwp", "zai-glm-52"],
            "source_anchor_count": 2,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_bachelor_thesis_workspace_card(
    workspace_card: dict[str, Any],
    *,
    thesis_evidence_hash: str = "",
    glm_method_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if thesis_evidence_hash and checkpoint_hash == "__BACHELOR_THESIS_EVIDENCE_HASH__":
        checkpoint_hash = thesis_evidence_hash
    if glm_method_hash and task_hash == "__BACHELOR_THESIS_GLM_METHOD_HASH__":
        task_hash = glm_method_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_bachelor_thesis_package")),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", "")),
        "operator_run_method": str(summary.get("operator_run_method", "POST")),
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


def build_bachelor_thesis_package() -> dict[str, Any]:
    package = {
        "schema_version": BACHELOR_THESIS_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "public_scientific_draft_bachelor_thesis_level_not_real_submission",
        "title": "UniBot Guardian: A Gretel-Built GLM-Ready Socratic Integrity Layer for Coding-Practice Workflows",
        "submission_type": "bachelor_thesis_level_research_package_not_real_university_submission",
        "level_statement": (
            "Bachelor thesis level means academic rigor, transparent method, reproducible documentation, "
            "and reviewability; it does not mean this artifact is a real university thesis submission."
        ),
        "authorship_statement": {
            "builder": "Gretel",
            "documentation_author": "Gretel",
            "builder_identity": "AI implementation and documentation agent",
            "orchestration_surface": "Codex local automation",
            "programmer_claim": "This public package is labelled as built and documented by Gretel, not by Julius.",
            "human_role": "Julius or another human reviewer remains the review, ethics, legal, and real submission gate.",
            "institutional_status": "not a real thesis submission and not institutionally approved by this artifact",
        },
        "glm_technology_basis": {
            "primary_model_hint": "zai/glm-5.2",
            "provider": "Z.AI",
            "use_mode": "redacted proposal, architecture, harness, and documentation review",
            "provider_call_default": "disabled",
            "provider_scope_when_enabled": "public-unibot-only",
            "model_permissions": "proposal and independent review only; no tools, apply, push, merge, or Final-Go",
            "reason": "GLM-5.2 is treated as the long-context coding proposal model for public-safe UniBot work packets.",
            "official_source_card_ids": ["zai-glm-52", "zai-glm-52-migration", "zai-glm-pricing"],
            "verified_on": "2026-07-11",
        },
        "research_question": (
            "How can a public, source-bound AI practice layer support coding learners without replacing "
            "their own work, leaking private material, or claiming exam clearance?"
        ),
        "scientific_contribution": [
            "A Socratic integrity layer that blocks final-answer outsourcing while preserving learner reflection.",
            "A public-safety scanner for paths, secrets, personal data, raw AI transcripts, and private course references.",
            "A reproducible publication and readiness package based on synthetic tasks and source cards.",
            "A GLM-5.2-ready proposal lane that turns model ideas into tests, review entries, or blocked reasons.",
            "A clear exam boundary: practice and review are supported; official grading, proctoring, and exam clearance are blocked.",
        ],
        "methodology": [
            "Three Golden Rules define allowed and blocked learning support.",
            "Public source cards anchor legal, institutional, privacy, technical, and educational claims.",
            "Synthetic scenarios and red-team checks test likely failure modes.",
            "Readiness and publication gates require public-safety pass results before public release.",
            "Accepted improvements must be converted into regression tests, red-team cases, documentation, or review-board decisions.",
        ],
        "implementation_scope": {
            "package": "unibot",
            "public_api_root": "/api/unibot",
            "primary_modules": [
                "unibot/guardian.py",
                "unibot/public_safety.py",
                "unibot/gretel_glm_evolve.py",
                "unibot/publication.py",
                "unibot/readiness.py",
                "unibot/bachelor_thesis.py",
            ],
            "public_docs": [
                "docs/unibot/UNIBOT_GOLDEN_RULES.md",
                "docs/unibot/UNIBOT_PIPELINE.md",
                "docs/unibot/UNIBOT_GRETEL_GLM_EVOLVE_LANE.md",
                "docs/unibot/UNIBOT_GRETEL_BACHELOR_THESIS_PACKAGE.md",
                "docs/unibot/UNIBOT_PUBLICATION_PACKAGE.md",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
                "docs/thesis/UNIBOT_GRETEL_BACHELOR_THESIS_MANUSCRIPT.md",
            ],
        },
        "manuscript": {
            "status": "complete_public_draft_requires_human_supervision_review",
            "path": "docs/thesis/UNIBOT_GRETEL_BACHELOR_THESIS_MANUSCRIPT.md",
            "language": "German",
            "chapter_count": 12,
            "contains_empirical_student_study": False,
            "contains_exam_security_proof": False,
            "legal_submission_by_gretel": False,
        },
        "deliverables": [
            "Public Python package",
            "Local API",
            "Synthetic evaluation and red-team tests",
            "Publication package",
            "Readiness report",
            "Review-board and authority handoff drafts",
            "Gretel/GLM proposal lane",
            "Bachelor-thesis-style documentation package",
            "Chaptered Gretel-authored bachelor-thesis-level manuscript",
        ],
        "review_gates": {
            "public_safety_required": True,
            "written_university_clearance_required_before_exam_use": True,
            "human_submission_review_required": True,
            "no_autonomous_github_publish": True,
            "draft_pull_request_allowed_after_rollout_gates": True,
            "autonomous_merge": False,
            "no_final_go_by_gretel_or_glm": True,
            "provider_call_requires_explicit_go_and_redaction_receipt": True,
        },
        "release_boundaries": {
            "ready_for": ["public code review", "bachelor-thesis-level supervision discussion", "local practice demo"],
            "not_ready_for": ["real university thesis submission without human review", "exam deployment", "grading", "proctoring", "AI-detection evidence"],
        },
    }
    package["evidence_index"] = build_bachelor_thesis_evidence_index()
    package["evaluation_claim_alignment"] = build_bachelor_thesis_evaluation_claim_alignment(
        package["evidence_index"],
        thesis_package=package,
    )
    package["source_cards"] = [
        card for card in (get_source_card(source_id) for source_id in package["glm_technology_basis"]["official_source_card_ids"]) if card
    ]
    package["receipt"] = build_bachelor_thesis_receipt(package)
    scan = scan_text(json.dumps(package, ensure_ascii=False), "unibot-gretel-bachelor-thesis-package")
    package["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        package["status"] = "blocked_public_safety"
        package["public_safety_findings"] = scan["findings"]
    return package


def build_bachelor_thesis_receipt(package: dict[str, Any]) -> dict[str, Any]:
    hashed = {key: value for key, value in package.items() if key not in {"generated_at_utc", "receipt"}}
    payload = json.dumps(hashed, sort_keys=True, ensure_ascii=False)
    return {
        "schema_version": "unibot-gretel-bachelor-thesis-receipt-v1",
        "package_hash": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "builder": package["authorship_statement"]["builder"],
        "model_hint": package["glm_technology_basis"]["primary_model_hint"],
        "provider_call_executed": False,
        "public_release_only_after_scan": True,
        "human_review_required": True,
    }


def build_bachelor_thesis_markdown() -> str:
    package = build_bachelor_thesis_package()
    contribution_lines = "\n".join(f"- {item}" for item in package["scientific_contribution"])
    method_lines = "\n".join(f"- {item}" for item in package["methodology"])
    deliverable_lines = "\n".join(f"- {item}" for item in package["deliverables"])
    ready_lines = "\n".join(f"- {item}" for item in package["release_boundaries"]["ready_for"])
    not_ready_lines = "\n".join(f"- {item}" for item in package["release_boundaries"]["not_ready_for"])
    evidence_lines = "\n".join(
        f"- `{item['claim_id']}`: {item['evidence_type']} via {', '.join(item['readiness_check_ids'])}"
        for item in package["evidence_index"]["evidence_items"]
    )
    evaluation_alignment_lines = "\n".join(
        f"- `{section['section_id']}`: {section['boundary']}"
        for section in package["evaluation_claim_alignment"]["sections"]
    )
    return (
        "# UniBot Gretel Bachelor-Thesis-Level Package\n\n"
        f"Status: {package['status']}\n\n"
        f"Title: {package['title']}\n\n"
        f"Level statement: {package['level_statement']}\n\n"
        "## Authorship\n\n"
        f"- Builder: {package['authorship_statement']['builder']}\n"
        f"- Documentation author: {package['authorship_statement']['documentation_author']}\n"
        f"- Programmer claim: {package['authorship_statement']['programmer_claim']}\n"
        f"- Human role: {package['authorship_statement']['human_role']}\n\n"
        "## GLM Basis\n\n"
        f"- Model hint: {package['glm_technology_basis']['primary_model_hint']}\n"
        f"- Provider: {package['glm_technology_basis']['provider']}\n"
        f"- Use mode: {package['glm_technology_basis']['use_mode']}\n"
        f"- Provider call default: {package['glm_technology_basis']['provider_call_default']}\n\n"
        "## Research Question\n\n"
        f"{package['research_question']}\n\n"
        "## Scientific Contribution\n\n"
        f"{contribution_lines}\n\n"
        "## Methodology\n\n"
        f"{method_lines}\n\n"
        "## Deliverables\n\n"
        f"{deliverable_lines}\n\n"
        "## Evidence Index\n\n"
        f"- Status: {package['evidence_index']['status']}\n"
        f"- Claims: {package['evidence_index']['claim_count']}\n"
        f"- Source-card drift: {package['evidence_index']['source_card_drift_status']}\n\n"
        f"{evidence_lines}\n\n"
        "## Evaluation Claim Alignment\n\n"
        f"- Status: {package['evaluation_claim_alignment']['status']}\n"
        f"- Public safety: {package['evaluation_claim_alignment']['public_safety_status']}\n\n"
        f"{evaluation_alignment_lines}\n\n"
        "## Ready For\n\n"
        f"{ready_lines}\n\n"
        "## Not Ready For\n\n"
        f"{not_ready_lines}\n\n"
        "## Receipt\n\n"
        f"- Package hash: {package['receipt']['package_hash']}\n"
        f"- Public safety: {package['public_safety_status']}\n"
        f"- Human review required: {package['receipt']['human_review_required']}\n"
    )
