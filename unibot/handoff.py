from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .ledger import export_public_ledger_summary
from .materials import sha256_text
from .notebooks import generate_practice_notebook
from .public_safety import scan_text
from .redteam import run_redteam_smoke
from .source_cards import list_source_cards


HANDOFF_SCHEMA_VERSION = "unibot-authority-handoff-v1"
AUTHORITY_HANDOFF_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-authority-handoff-release-review-board-claim-alignment-v1"
)


def build_authority_handoff_release_claim_alignment(
    packet: dict[str, Any],
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sections = [
        {
            "section_id": "authority_status_trace",
            "summary_claim": "authority packet is a draft review artifact, not an approval or request outcome",
            "source_card_ids": ["uoc-ki-lehre", "uoc-hilfsmittel"],
            "readiness_check_ids": [
                "authority_handoff",
                "python_exam_local_cycle_operator_workspace_card",
                "review_board_packet",
                "release_runbook",
            ],
            "human_gates": [
                "human_submission_review_required",
                "written_university_clearance_required_before_exam_use",
            ],
        },
        {
            "section_id": "privacy_boundary_trace",
            "summary_claim": "handoff describes public-safe categories and excludes private course, health, path, email, and raw model text",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
            "readiness_check_ids": ["authority_handoff", "data_protection_screening", "public_safety"],
            "human_gates": ["public_safety_required", "datenschutz_review_required_before_real_pilot"],
        },
        {
            "section_id": "source_card_trace",
            "summary_claim": "university-facing claims stay tied to public source cards and high-risk source review",
            "source_card_ids": ["hg-nrw-2025", "uoc-nachteilsausgleich", "eu-ai-act-2024"],
            "readiness_check_ids": ["source_cards", "source_card_drift_guard", "authority_handoff"],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "evidence_trace",
            "summary_claim": "handoff evidence links red-team, notebook, ledger summary, and compliance status without raw private material",
            "source_card_ids": ["dfg-gwp", "openai-evals"],
            "readiness_check_ids": ["redteam", "notebook_template", "compliance_matrix", "authority_handoff"],
            "human_gates": ["human_submission_review_required"],
        },
        {
            "section_id": "provider_trace",
            "summary_claim": "GLM/provider work remains proposal and redaction gated before any live external call",
            "source_card_ids": ["zai-glm-52", "zai-glm-52-migration", "zai-glm-pricing"],
            "readiness_check_ids": ["gretel_glm_evolve_lane", "authority_handoff", "review_board_packet"],
            "human_gates": ["provider_call_requires_explicit_go_and_redaction_receipt"],
        },
    ]
    source_cards = {card["source_id"]: card for card in packet.get("source_cards", [])}
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if source_id not in source_cards)

    modes_by_id = {mode.get("mode"): mode for mode in packet.get("operating_modes", [])}
    non_goals = set(packet.get("non_goals", []))
    data_categories = packet.get("data_categories", {})
    not_stored = set(data_categories.get("not_stored_by_default", []))
    evidence = packet.get("evidence", {})
    compliance = evidence.get("compliance_matrix", {})
    policy = packet.get("authority_packet_policy", "")
    workspace_card = safe_authority_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_authority_workspace_card()
        if packet.get("status") == "draft_not_officially_cleared"
        else {},
        reviewer_packet_hash=authority_handoff_reviewer_packet_hash(packet),
        public_language_hash=authority_handoff_public_language_hash(packet),
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

    contracts = {
        "draft_status_not_officially_cleared": packet.get("status") == "draft_not_officially_cleared",
        "public_label_non_approval": "nicht offiziell freigegeben" in packet.get("status_label_de", ""),
        "exam_mode_blocked_until_written_clearance": modes_by_id.get("exam_controlled", {}).get("status")
        == "blocked_until_written_clearance",
        "no_proctoring_or_grading_or_detection_claims": {
            "no proctoring",
            "no KI detection as evidence",
            "no automatic grading",
            "no decision on Nachteilsausgleich",
        }.issubset(non_goals),
        "private_and_raw_material_not_stored": {
            "raw external KI output",
            "private course materials",
            "emails",
            "medical or accommodation personal data",
            "local paths",
            "official grades",
        }.issubset(not_stored),
        "redteam_evidence_passes": evidence.get("redteam", {}).get("status") == "pass",
        "notebook_audit_passes": evidence.get("notebook_audit", {}).get("status") == "pass",
        "compliance_ready_for_authority_review": compliance.get("status") == "draft_ready_for_authority_review",
        "compliance_public_safety_passes": compliance.get("public_safety_status") == "pass",
        "policy_is_public_summary_only": "public-safe summary only" in policy and "no official decision language" in policy,
        "workspace_card_authority_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == authority_handoff_reviewer_packet_hash(packet)
        and workspace_card.get("task_hash") == authority_handoff_public_language_hash(packet),
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": ["exam clearance", "official grading", "proctoring", "KI-detection evidence"],
    }
    scan = scan_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), "authority-handoff-release-claim-alignment")
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": AUTHORITY_HANDOFF_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "failed_contract_ids": failed_contract_ids,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "blocked_claims": payload["blocked_claims"],
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_authority_gate_linked": contracts["workspace_card_authority_gate_linked"],
        "public_safety_status": scan["status"],
        "policy": (
            "Authority handoff release claims are source-bound draft-review aids only; they do not authorize "
            "publication, provider calls, real pilots, university submission, grading, proctoring, KI detection, "
            "Nachteilsausgleich decisions, or exam clearance."
        ),
    }


def build_authority_handoff_packet(ledger_path: str | None = None) -> dict[str, Any]:
    redteam = run_redteam_smoke()
    notebook_artifact = generate_practice_notebook(
        "Python-Neuro Practice: Listen, pandas, Boxplot und Debugging in Colab",
        source_card_ids=["hg-nrw-2025", "uoc-ki-lehre", "uoc-hilfsmittel", "uoc-nachteilsausgleich", "google-colab-gemini", "vanlehn-2011"],
        title="UniBot Guardian Practice Demo",
    )
    ledger_summary = export_public_ledger_summary(ledger_path)
    source_cards = list_source_cards()
    high_risk_cards = [card for card in source_cards if card["risk_level"] == "high"]
    compliance = build_compliance_matrix()

    packet = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "draft_not_officially_cleared",
        "status_label_de": "Entwurf: nicht offiziell freigegeben / beantragt",
        "project": {
            "name": "UniBot Guardian",
            "one_sentence": (
                "Ein separater sokratischer Guardian-Mantel fuer Colab/Gemini, Jupyter und Coding-Hilfen, "
                "der externe KI-Antworten filtert, Hilfestufen dokumentiert und Eigenleistung schuetzt."
            ),
            "separation": "Separate UniBot track; not main Gretel/Badgyal pipeline.",
            "current_use": "practice and private selftest only",
        },
        "intended_reviewers": [
            "Pruefungsamt",
            "Inklusionsbuero / Nachteilsausgleich-Stelle",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
        ],
        "operating_modes": [
            {
                "mode": "practice_overlay",
                "status": "implemented_mvp",
                "rule": "Visible practice filter for external KI help; not exam security.",
            },
            {
                "mode": "selftest_guardian",
                "status": "implemented_mvp",
                "rule": "Private Independence Score only; no grade and no official assessment.",
            },
            {
                "mode": "exam_controlled",
                "status": "blocked_until_written_clearance",
                "rule": "Requires written exam-authority clearance and a controlled KI channel or managed environment.",
            },
        ],
        "non_goals": [
            "no proctoring",
            "no KI detection as evidence",
            "no automatic grading",
            "no decision on Nachteilsausgleich",
            "no processing of medical or accommodation personal data without a clear legal and privacy basis",
            "no public release of private course materials, emails, local paths, or raw external KI outputs",
        ],
        "data_flow": [
            "Student formulates task and own attempt locally.",
            "UniBot generates a Socratic Prompt Card.",
            "Student may ask an external tool in practice mode.",
            "External output is pasted into UniBot for filtering.",
            "UniBot returns only an allowed Socratic hint and a private formative score.",
            "Ledger stores hash, categories, help level, source card IDs, and redacted reflection only.",
            "Public summaries exclude raw external KI output and student reflections.",
        ],
        "data_categories": {
            "stored_by_default": ["hashes", "classification categories", "help levels", "skill tags", "source card IDs", "redacted reflections"],
            "not_stored_by_default": ["raw external KI output", "private course materials", "emails", "medical or accommodation personal data", "local paths", "official grades"],
            "local_storage_default": "~/.unibot_guardian/help_ledger.jsonl",
        },
        "review_questions": [
            "Welche Hilfsmittelregel gilt fuer einen freiwilligen Practice- oder Selftest-Einsatz?",
            "Welche Stelle muesste einen spaeteren exam_controlled-Modus schriftlich freigeben?",
            "Welche Daten duerfen fuer Help-Ledger und Evaluation gespeichert werden, und wie lange?",
            "Welche Accessibility-Hilfen sind punkteneutral zu dokumentieren?",
            "Welche Formulierungen muessen im UI stehen, damit keine Scheinfreigabe entsteht?",
            "Waere fuer eine Pilotstudie eine Ethik-/Datenschutzpruefung noetig?",
        ],
        "evidence": {
            "redteam": {
                "status": redteam["status"],
                "scenario_count": redteam["scenario_count"],
                "passed_count": redteam["passed_count"],
                "failed_count": redteam["failed_count"],
                "scenario_ids": [scenario["scenario_id"] for scenario in redteam["scenarios"]],
            },
            "notebook_audit": notebook_artifact["audit"],
            "ledger_public_summary": ledger_summary,
            "source_card_count": len(source_cards),
            "high_risk_source_card_ids": [card["source_id"] for card in high_risk_cards],
            "compliance_matrix": {
                "status": compliance["status"],
                "requirement_count": compliance["requirement_count"],
                "high_risk_requirement_count": compliance["high_risk_requirement_count"],
                "missing_source_card_ids": compliance["missing_source_card_ids"],
                "public_safety_status": compliance["public_safety_status"],
            },
        },
        "source_cards": [
            {
                "source_id": card["source_id"],
                "title": card["title"],
                "url": card["url"],
                "source_kind": card["source_kind"],
                "authority_type": card["authority_type"],
                "product_rule": card["product_rule"],
                "risk_level": card["risk_level"],
                "last_checked": card["last_checked"],
            }
            for card in source_cards
        ],
        "authority_packet_policy": "public-safe summary only; no raw external KI outputs, no private course material, no health data, no official decision language",
    }
    packet["release_claim_alignment"] = build_authority_handoff_release_claim_alignment(packet)
    return packet


def build_authority_handoff_markdown(ledger_path: str | None = None) -> str:
    packet = build_authority_handoff_packet(ledger_path)
    mode_lines = "\n".join(f"- `{mode['mode']}`: {mode['rule']}" for mode in packet["operating_modes"])
    non_goal_lines = "\n".join(f"- {item}" for item in packet["non_goals"])
    review_lines = "\n".join(f"- {item}" for item in packet["review_questions"])
    evidence = packet["evidence"]
    release_alignment = packet["release_claim_alignment"]
    source_lines = "\n".join(
        f"- `{card['source_id']}` ({card['source_kind']}): {card['product_rule']}"
        for card in packet["source_cards"]
    )
    return (
        "# UniBot Guardian Handoff Packet\n\n"
        f"Status: {packet['status_label_de']}\n\n"
        f"Projekt: {packet['project']['one_sentence']}\n\n"
        "## Betriebsmodi\n\n"
        f"{mode_lines}\n\n"
        "## Nicht-Ziele\n\n"
        f"{non_goal_lines}\n\n"
        "## Datenfluss\n\n"
        + "\n".join(f"- {step}" for step in packet["data_flow"])
        + "\n\n"
        "## Offene Review-Fragen\n\n"
        f"{review_lines}\n\n"
        "## Evidenzstatus\n\n"
        f"- Red-Team: {evidence['redteam']['status']} ({evidence['redteam']['passed_count']}/{evidence['redteam']['scenario_count']})\n"
        f"- Notebook-Audit: {evidence['notebook_audit']['status']}\n"
        f"- Source Cards: {evidence['source_card_count']}\n"
        f"- Compliance Matrix: {evidence['compliance_matrix']['status']} ({evidence['compliance_matrix']['requirement_count']} requirements)\n"
        f"- Ledger Public Summary Events: {evidence['ledger_public_summary']['event_count']}\n\n"
        "## Release Claim Alignment\n\n"
        f"- Status: {release_alignment['status']}\n"
        f"- Public Safety: {release_alignment['public_safety_status']}\n"
        f"- Human Gates: {', '.join(release_alignment['required_human_gates'])}\n"
        f"- Blocked Claims: {', '.join(release_alignment['blocked_claims'])}\n\n"
        "## Source Cards\n\n"
        f"{source_lines}\n\n"
        "Policy: public-safe summary only; no raw external KI outputs, no private course material, no health data, no official decision language.\n"
    )


def synthetic_authority_workspace_card() -> dict[str, Any]:
    preview_hash = sha256_text("synthetic authority handoff workspace card")
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic authority handoff prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_authority_handoff_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_authority_packet_before_manual_submission",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__AUTHORITY_PUBLIC_LANGUAGE_HASH__",
            "checkpoint_hash": "__AUTHORITY_REVIEWER_PACKET_HASH__",
            "source_card_ids": ["uoc-ki-lehre", "uoc-hilfsmittel", "dfg-gwp"],
            "source_anchor_count": 3,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def authority_handoff_reviewer_packet_hash(packet: dict[str, Any]) -> str:
    return sha256_text(
        json.dumps(
            {
                "status": packet.get("status", ""),
                "intended_reviewers": packet.get("intended_reviewers", []),
                "operating_modes": packet.get("operating_modes", []),
                "review_questions": packet.get("review_questions", []),
                "evidence": packet.get("evidence", {}),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def authority_handoff_public_language_hash(packet: dict[str, Any]) -> str:
    return sha256_text(
        json.dumps(
            {
                "status_label_de": packet.get("status_label_de", ""),
                "project": packet.get("project", {}),
                "non_goals": packet.get("non_goals", []),
                "data_flow": packet.get("data_flow", []),
                "data_categories": packet.get("data_categories", {}),
                "authority_packet_policy": packet.get("authority_packet_policy", ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def safe_authority_workspace_card(
    workspace_card: dict[str, Any],
    *,
    reviewer_packet_hash: str = "",
    public_language_hash: str = "",
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
    if reviewer_packet_hash and checkpoint_hash == "__AUTHORITY_REVIEWER_PACKET_HASH__":
        checkpoint_hash = reviewer_packet_hash
    if public_language_hash and task_hash == "__AUTHORITY_PUBLIC_LANGUAGE_HASH__":
        task_hash = public_language_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", review.get("recommendation", "keep_blocked"))),
        "recommendation_reason": str(
            summary.get("recommendation_reason", review.get("recommendation_reason", "missing_authority_handoff"))
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
