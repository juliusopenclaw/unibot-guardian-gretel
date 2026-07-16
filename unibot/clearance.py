from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .compliance import build_compliance_matrix
from .materials import sha256_text
from .public_safety import scan_text
from .review_board import build_review_board_packet
from .source_cards import get_source_card


INSTITUTIONAL_CLEARANCE_SCHEMA_VERSION = "unibot-institutional-clearance-v1"
REGULATORY_PROFILE_SCHEMA_VERSION = "RegulatoryProfileV1"
INSTITUTIONAL_PRESENTATION_SCHEMA_VERSION = "InstitutionalPresentationV1"
INSTITUTIONAL_REVIEW_BUNDLE_SCHEMA_VERSION = "InstitutionalReviewBundleV1"
ACCESSIBILITY_REVIEW_SCHEMA_VERSION = "AccessibilityReviewV1"
INSTITUTIONAL_REVIEW_DECISION_TEMPLATE_SCHEMA_VERSION = "InstitutionalReviewDecisionTemplateV1"

ALLOWED_DECISION_STATUSES = {"needs_review", "approved", "rejected"}
STANDARD_HELP_LEVELS = ("A0", "A1", "A2")
PRACTICE_HELP_LEVELS = ("A0", "A1", "A2", "A3", "A4")
CONTROLLED_EXAM_HELP_LEVELS = ("A0", "A1", "A2")
BLOCKED_HELP_LEVELS = {"A5", "A6"}

CLEARANCE_SCOPES: dict[str, dict[str, Any]] = {
    "practice_public_draft": {
        "label": "Public draft and local practice demo",
        "current_status": "ready_for_public_draft_review",
        "exam_deployment_status": "not_cleared",
        "allowed_modes": ["practice_overlay", "selftest_guardian", "course_tutor_mode"],
        "required_reviewer_roles": ["Lehreinheit / Modulverantwortliche"],
        "required_source_card_ids": ["uoc-ki-faq", "uoc-ki-lehre", "dfg-gwp"],
        "decision_needed": "Confirm public wording, local-only practice scope, and source-card boundaries.",
        "does_not_authorize": ["exam deployment", "official grading", "proctoring", "KI detection"],
    },
    "local_private_extraction": {
        "label": "Local private OCR/transcription for course tutor indexing",
        "current_status": "pending_rights_privacy_decision",
        "exam_deployment_status": "not_cleared",
        "allowed_modes": ["course_material_extraction", "course_tutor_mode"],
        "required_reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "required_source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "uoc-ki-lehre", "dfg-gwp"],
        "decision_needed": "Confirm local processing, storage, retention, access roles, and human review before tutor indexing.",
        "does_not_authorize": ["public raw text release", "exam deployment", "cloud processing"],
    },
    "formative_pilot": {
        "label": "Formative pilot or bachelor-thesis study rehearsal",
        "current_status": "pending_ethics_privacy_teaching_review",
        "exam_deployment_status": "not_cleared",
        "allowed_modes": ["practice_overlay", "selftest_guardian", "course_tutor_mode"],
        "required_reviewer_roles": [
            "Datenschutz",
            "Lehreinheit / Modulverantwortliche",
            "Thesis supervision",
        ],
        "required_source_card_ids": ["dfg-gwp", "eu-ai-act-2024", "unesco-genai-2023"],
        "decision_needed": "Confirm participant information, consent boundary, stop rules, and synthetic/practice-only data scope.",
        "does_not_authorize": ["real exam deployment", "official grading", "disciplinary decisions"],
    },
    "exam_controlled_gateway": {
        "label": "Controlled exam gateway / managed notebook",
        "current_status": "real_world_clearance_reminder_not_technical_blocker",
        "exam_deployment_status": "not_cleared",
        "allowed_modes": ["exam_controlled_gateway", "controlled_notebook"],
        "required_reviewer_roles": [
            "Pruefungsamt",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
            "Inklusionsbuero / Nachteilsausgleich",
        ],
        "required_source_card_ids": [
            "hg-nrw-2025",
            "hg-nrw-64",
            "uoc-hilfsmittel",
            "uoc-szi-klausurunterstuetzung-2026",
            "uoc-ki-faq",
            "eu-ai-act-2024",
            "jupyter-ai",
        ],
        "decision_needed": "Confirm written exam scope, controlled channel, A0-A2 help policy, ledger/export evidence, and incident handling.",
        "does_not_authorize": [
            "uncontrolled external generative help",
            "automatic grading",
            "proctoring",
            "KI detection",
            "A6 solution delivery",
        ],
    },
}

REGULATORY_SOURCE_CARD_IDS = [
    "uoc-ki-policy-2026",
    "uoc-ki-pruefungsrecht",
    "uoc-medfak-ki-doku-2026",
    "uoc-medfak-ki-lehre-2026",
    "uoc-ki-lehre",
    "uoc-hilfsmittel",
    "uoc-nachteilsausgleich",
    "uoc-szi-klausurunterstuetzung-2026",
    "uoc-szi-inclusive-teaching-2026",
    "uoc-szi-wegweiser-2026",
    "wcag-22",
    "bgg-nrw-10",
    "bitv-nrw",
    "gdpr-2016-679",
    "dsk-ai-privacy-2024",
    "eu-ai-act-2024",
    "hg-nrw-64",
    "dfg-gwp",
    "jupyter-ai",
]

ACCESSIBILITY_REVIEW_SOURCE_CARD_IDS = [
    "wcag-22",
    "bgg-nrw-10",
    "bitv-nrw",
    "uoc-szi-inclusive-teaching-2026",
    "uoc-nachteilsausgleich",
]


def build_accessibility_review_plan(*, public_safe: bool = True) -> dict[str, Any]:
    """Prepare a consent-based accessibility review without diagnosing people."""
    checks = [
        {
            "check_id": "keyboard_core_flow",
            "method": "keyboard_only",
            "pass_condition": "Start, cell selection, help request, report preview, and delete are operable with visible focus.",
            "critical": True,
        },
        {
            "check_id": "screen_reader_status",
            "method": "screen_reader_with_synthetic_notebook",
            "pass_condition": "Controls, selected tab, errors, and live status are announced with meaningful labels.",
            "critical": True,
        },
        {
            "check_id": "zoom_and_reflow",
            "method": "browser_zoom_200_percent_and_280px_panel",
            "pass_condition": "Core flow remains usable without hidden controls or horizontal scrolling.",
            "critical": True,
        },
        {
            "check_id": "contrast_and_focus",
            "method": "human_visual_review",
            "pass_condition": "Text, controls, focus, errors, and disabled states remain distinguishable.",
            "critical": True,
        },
        {
            "check_id": "uncertain_cell_fallback",
            "method": "adapter_uncertainty_fixture",
            "pass_condition": "The product asks for explicit selection and never guesses a cell.",
            "critical": True,
        },
        {
            "check_id": "cognitive_load_and_language",
            "method": "human_task_walkthrough",
            "pass_condition": "The next action, help level, uncertainty, and stop/delete option are understandable without hidden assumptions.",
            "critical": False,
        },
        {
            "check_id": "fallback_without_companion",
            "method": "native_host_offline_fixture",
            "pass_condition": "The learner receives a clear error and can use manual selection or stop without data loss.",
            "critical": True,
        },
        {
            "check_id": "privacy_and_non_disclosure",
            "method": "synthetic_only_review_with_storage_scan",
            "pass_condition": "No diagnosis, accommodation status, raw notebook, or learner transcript is recorded in review evidence.",
            "critical": True,
        },
    ]
    plan: dict[str, Any] = {
        "schema_version": ACCESSIBILITY_REVIEW_SCHEMA_VERSION,
        "artifact_type": "unibot_accessibility_review_plan",
        "status": "ready_for_human_accessibility_review",
        "scope": "local_learning_and_practice_only",
        "standards_target": "WCAG 2.2 AA as a review target; BITV NRW and BGG NRW applicability require institutional determination.",
        "source_card_ids": list(ACCESSIBILITY_REVIEW_SOURCE_CARD_IDS),
        "automated_evidence": {
            "status": "prototype_evidence_only",
            "test_file": "tests/browser/mantle-v2.spec.js",
            "covered": [
                "semantic status regions",
                "keyboard focus",
                "tablist arrow-key navigation",
                "narrow panel",
                "reconnection",
                "manual selection fallback",
            ],
            "does_not_prove": ["WCAG conformance", "BITV NRW conformance", "individual accommodation suitability"],
        },
        "human_review": {
            "required_roles": [
                "Inklusionsbuero / Servicezentrum Inklusion",
                "Pruefungsamt for any exam-related scope",
                "IT / SZI",
                "Lehreinheit / Modulverantwortliche",
            ],
            "participant_rule": "Use synthetic tasks by default; any learner study requires consent, withdrawal, and a separate human study decision.",
            "assistive_technology_rule": "Record only consented test outcome categories and assistive-technology class; never record diagnosis or accommodation status.",
            "signoff_required": True,
        },
        "checks": checks,
        "release_gate": {
            "critical_failure_blocks_scope": True,
            "human_conformance_decision_required": True,
            "no_automatic_accommodation_decision": True,
            "no_exam_clearance": True,
            "no_learner_score": True,
        },
        "data_minimisation": {
            "raw_notebook_or_attempt_in_evidence": False,
            "health_or_disability_details_in_evidence": False,
            "local_paths_or_credentials_in_evidence": False,
            "public_demo_uses_synthetic_notebook": True,
        },
        "limitations": [
            "A browser test is evidence about a prototype, not a certification.",
            "Accessibility is context- and task-dependent; the responsible institution decides the applicable scope.",
            "Accessibility support must remain available without being treated as subject-matter help or a performance score.",
        ],
    }
    scan = scan_text(json.dumps(plan, ensure_ascii=False), "accessibility-review-plan")
    plan["public_safety_status"] = scan["status"] if public_safe else "local_private_mode"
    if plan["public_safety_status"] != "pass" and public_safe:
        plan["status"] = "blocked_public_safety"
        plan["public_safety_findings"] = scan["findings"]
    return plan


def validate_accessibility_review_plan(plan: dict[str, Any] | None) -> dict[str, Any]:
    """Validate the review contract without granting accessibility clearance."""
    payload = dict(plan or {})
    issues: list[str] = []
    if payload.get("schema_version") != ACCESSIBILITY_REVIEW_SCHEMA_VERSION:
        issues.append("schema_version_mismatch")
    if payload.get("status") != "ready_for_human_accessibility_review":
        issues.append("human_review_status_required")
    if payload.get("scope") != "local_learning_and_practice_only":
        issues.append("scope_must_remain_practice_only")
    if set(payload.get("source_card_ids", [])) != set(ACCESSIBILITY_REVIEW_SOURCE_CARD_IDS):
        issues.append("accessibility_source_cards_mismatch")
    if len(payload.get("checks", [])) < 8:
        issues.append("accessibility_check_matrix_incomplete")
    release_gate = payload.get("release_gate", {})
    if not release_gate.get("critical_failure_blocks_scope"):
        issues.append("critical_failures_must_block_scope")
    if not release_gate.get("human_conformance_decision_required"):
        issues.append("human_conformance_decision_required")
    if not payload.get("human_review", {}).get("signoff_required"):
        issues.append("human_signoff_required")
    if payload.get("public_safety_status") not in {"pass", "local_private_mode"}:
        issues.append("public_safety_required")
    summary = {
        "schema_version": ACCESSIBILITY_REVIEW_SCHEMA_VERSION,
        "artifact_type": "accessibility_review_validation",
        "status": "ok" if not issues else "blocked",
        "issues": sorted(set(issues)),
        "conformance_cleared": False,
        "exam_deployment_status": "not_cleared",
        "human_review_required": True,
        "public_safety_status": payload.get("public_safety_status", "missing"),
    }
    scan = scan_text(json.dumps(summary, ensure_ascii=False), "accessibility-review-validation")
    if scan["status"] != "pass":
        summary["status"] = "blocked"
        summary["issues"] = sorted(set(summary["issues"] + ["public_safety_findings"]))
        summary["public_safety_findings"] = scan["findings"]
    return summary


def build_institutional_review_decision_template(*, public_safe: bool = True) -> dict[str, Any]:
    """Prepare a blank, hash-only human meeting outcome template.

    The template records the shape of a later human decision without accepting
    raw minutes, names, diagnoses, or an automatic approval signal.
    """
    lanes = [
        {
            "lane_id": "examination_scope",
            "office": "Pruefungsamt",
            "question": "Welche Regeln gelten für den lokalen Übungszweck, und welcher separate Prüfungsentscheid wäre nötig?",
            "required_evidence": ["uoc-ki-policy-2026", "uoc-ki-pruefungsrecht", "uoc-ki-faq"],
        },
        {
            "lane_id": "accessibility_scope",
            "office": "Inklusionsbuero / Servicezentrum Inklusion",
            "question": "Welche Bedienungs- und Strukturierungshilfen sind im vorgesehenen Lehrformat angemessen?",
            "required_evidence": ["uoc-nachteilsausgleich", "uoc-szi-klausurunterstuetzung-2026", "wcag-22", "bgg-nrw-10", "bitv-nrw"],
        },
        {
            "lane_id": "privacy_and_it_scope",
            "office": "Datenschutz / IT / SZI",
            "question": "Sind Datenfluss, Aufbewahrung, Löschung und Zugriffsschutz für den Übungszweck ausreichend beschrieben?",
            "required_evidence": ["gdpr-2016-679", "dsk-ai-privacy-2024", "eu-ai-act-2024"],
        },
        {
            "lane_id": "governance_scope",
            "office": "KI-Office / CIO-Board",
            "question": "Welche Genehmigungsroute und fachverantwortliche Person gelten für eine mögliche Bereitstellung?",
            "required_evidence": ["uoc-ki-policy-2026", "uoc-medfak-ki-lehre-2026"],
        },
        {
            "lane_id": "teaching_and_research_scope",
            "office": "Lehre / Modulverantwortliche / Bachelorarbeitsbetreuung",
            "question": "Sind Forschungsfrage, Hilfestufen, Quellenbindung und Evaluationsgrenzen für einen Übungspilot angemessen?",
            "required_evidence": ["dfg-gwp", "vanlehn-2011", "kulik-fletcher-2016"],
        },
    ]
    template: dict[str, Any] = {
        "schema_version": INSTITUTIONAL_REVIEW_DECISION_TEMPLATE_SCHEMA_VERSION,
        "artifact_type": "unibot_institutional_review_decision_template",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "blank_for_human_completion",
        "scope": "local_learning_and_practice_only",
        "exam_deployment_status": "not_cleared",
        "decision_status_options": [
            "pending_human_review",
            "practice_scope_supported_with_conditions",
            "needs_revision_before_practice_demo",
            "not_supported_for_requested_scope",
            "exam_scope_requires_separate_written_decision",
        ],
        "required_fields": [
            "meeting_date",
            "reviewer_role_ids",
            "recorded_outcome",
            "condition_ids",
            "open_question_ids",
            "next_review_gate",
            "evidence_hashes",
            "human_signoff_reference_hash",
        ],
        "review_lanes": lanes,
        "data_minimisation": {
            "raw_meeting_text_stored": False,
            "raw_names_or_contact_details_stored": False,
            "health_or_accommodation_details_stored": False,
            "notebook_or_learner_content_stored": False,
            "local_paths_or_credentials_stored": False,
            "allowed_record_values": "Controlled IDs, dates, role IDs, hashes, status values, and the next gate only.",
        },
        "human_boundary": {
            "human_completion_required": True,
            "automatic_approval": False,
            "legal_effect": "none",
            "exam_clearance": "not_granted",
            "institutional_release": "not_granted",
        },
        "authorship": {
            "implementation_and_documentation": "Gretel / Codex",
            "glm_role": "No contribution while GLM is parked.",
            "human_decision_owner": "Julius and the named institutional roles decide outside UniBot.",
        },
    }
    scan = scan_text(json.dumps(template, ensure_ascii=False), "institutional-review-decision-template")
    template["public_safety_status"] = scan["status"] if public_safe else "local_private_mode"
    if template["public_safety_status"] != "pass" and public_safe:
        template["status"] = "blocked_public_safety"
        template["public_safety_findings"] = scan["findings"]
    return template


def validate_institutional_review_decision_template(template: dict[str, Any] | None) -> dict[str, Any]:
    """Validate the meeting form while keeping all approval decisions human."""
    payload = dict(template or {})
    issues: list[str] = []
    if payload.get("schema_version") != INSTITUTIONAL_REVIEW_DECISION_TEMPLATE_SCHEMA_VERSION:
        issues.append("schema_version_mismatch")
    if payload.get("status") != "blank_for_human_completion":
        issues.append("template_must_remain_blank_for_human_completion")
    if payload.get("scope") != "local_learning_and_practice_only":
        issues.append("scope_must_remain_practice_only")
    if payload.get("exam_deployment_status") != "not_cleared":
        issues.append("exam_deployment_must_remain_not_cleared")
    required_statuses = {
        "pending_human_review",
        "practice_scope_supported_with_conditions",
        "needs_revision_before_practice_demo",
        "not_supported_for_requested_scope",
        "exam_scope_requires_separate_written_decision",
    }
    if set(payload.get("decision_status_options", [])) != required_statuses:
        issues.append("decision_status_options_mismatch")
    if len(payload.get("required_fields", [])) < 8:
        issues.append("required_fields_incomplete")
    if len(payload.get("review_lanes", [])) != 5:
        issues.append("review_lane_matrix_incomplete")
    minimisation = payload.get("data_minimisation", {})
    for field in (
        "raw_meeting_text_stored",
        "raw_names_or_contact_details_stored",
        "health_or_accommodation_details_stored",
        "notebook_or_learner_content_stored",
        "local_paths_or_credentials_stored",
    ):
        if minimisation.get(field) is not False:
            issues.append(f"{field}_must_be_false")
    boundary = payload.get("human_boundary", {})
    if boundary.get("human_completion_required") is not True:
        issues.append("human_completion_required")
    if boundary.get("automatic_approval") is not False:
        issues.append("automatic_approval_must_remain_false")
    if boundary.get("legal_effect") != "none":
        issues.append("legal_effect_must_remain_none")
    if boundary.get("exam_clearance") != "not_granted":
        issues.append("exam_clearance_must_remain_not_granted")
    if payload.get("public_safety_status") not in {"pass", "local_private_mode"}:
        issues.append("public_safety_required")
    summary = {
        "schema_version": INSTITUTIONAL_REVIEW_DECISION_TEMPLATE_SCHEMA_VERSION,
        "artifact_type": "institutional_review_decision_template_validation",
        "status": "ok" if not issues else "blocked",
        "issues": sorted(set(issues)),
        "human_completion_required": True,
        "automatic_approval": False,
        "legal_effect": "none",
        "exam_deployment_status": "not_cleared",
        "public_safety_status": payload.get("public_safety_status", "missing"),
    }
    scan = scan_text(json.dumps(summary, ensure_ascii=False), "institutional-review-decision-template-validation")
    if scan["status"] != "pass":
        summary["status"] = "blocked"
        summary["issues"] = sorted(set(summary["issues"] + ["public_safety_findings"]))
        summary["public_safety_findings"] = scan["findings"]
    return summary


def build_institutional_review_decision_template_markdown(
    template: dict[str, Any] | None = None,
) -> str:
    """Render a printable human form without creating a decision."""
    template = template or build_institutional_review_decision_template()
    lines = [
        "# UniBot: Ergebnisprotokoll der menschlichen Prüfung",
        "",
        f"**Vertrag:** `{template['schema_version']}`",
        "**Status:** Leeres Formular; keine Freigabe und keine Rechtswirkung",
        "**Geltungsbereich:** lokale Lern- und Übungsversion; Prüfungseinsatz bleibt `not_cleared`.",
        "",
        "Dieses Formular hält nur kontrollierte IDs, Rollen, Hashes und den nächsten Prüfschritt fest. Keine Gesprächsnotizen, Namen, Diagnosen, Nachteilsausgleichdaten, Notebookinhalte oder Lernendentexte eintragen.",
        "",
        "## Ergebnis",
        "- Datum: ______________________________",
        "- Rollen-IDs: _________________________",
        "- Ergebnis-ID: ________________________",
        "- Bedingungen-IDs: ____________________",
        "- Offene-Fragen-IDs: ___________________",
        "- Nächster Prüfschritt: _________________",
        "- Evidenz-Hashes: ______________________",
        "- Signoff-Referenz-Hash: _______________",
        "",
        "## Zulässige Ergebnis-IDs",
        *[f"- `{status}`" for status in template["decision_status_options"]],
        "",
        "## Prüflanes",
        *[f"- **{lane['office']}:** {lane['question']}" for lane in template["review_lanes"]],
        "",
        "## Harte Grenzen",
        "- Dieses Formular erteilt keine Prüfungs-, Datenschutz-, Inklusions- oder Rechtsfreigabe.",
        "- Eine eventuelle Prüfungsentscheidung muss separat schriftlich durch die zuständigen Stellen erfolgen.",
        "- Eine menschliche Person muss das Ergebnis außerhalb von UniBot prüfen und verantworten.",
        "",
        "## Autorenschaft",
        "- Implementierung und Dokumentation: **Gretel / Codex**.",
        "- GLM: in dieser geparkten Etappe kein Beitrag.",
        "- Menschliche Entscheidung: Julius und die zuständigen institutionellen Rollen.",
        "",
        "**Technische Prüfung:** Template-Validierung und Public-Safety-Scan sind Nachweise über die Form, nicht über die institutionelle Entscheidung.",
    ]
    return "\n".join(lines) + "\n"


def build_institutional_clearance_board(*, public_safe: bool = True) -> dict[str, Any]:
    review_board = build_review_board_packet()
    compliance = build_compliance_matrix()
    regulatory_profile = build_regulatory_profile(public_safe=public_safe)
    lanes = [clearance_lane(scope_id, scope) for scope_id, scope in CLEARANCE_SCOPES.items()]
    board = {
        "schema_version": INSTITUTIONAL_CLEARANCE_SCHEMA_VERSION,
        "artifact_type": "unibot_institutional_clearance_board",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pending_written_clearance",
        "status_label_de": "Institutionelles Clearance-Board: Entscheidungen vorbereitet, nicht erteilt",
        "exam_deployment_status": "not_cleared",
        "regulatory_profile": regulatory_profile,
        "decision_boundary": (
            "This board prepares human authority decisions. It is not approval, legal advice, "
            "Datenschutz approval, exam clearance, or a deployment switch."
        ),
        "golden_rule_alignment": {
            "pm_gr1_generalize": "One clearance schema covers public draft, extraction, pilot, and exam gateway scopes.",
            "pm_gr2_harness_engineering": "Each written record can be validated before any mode changes.",
            "pm_gr3_recursive_self_improvement": "Missing roles, unsafe clauses, or overbroad modes become regression checks.",
        },
        "strict_non_goals": [
            "no proctoring",
            "no KI detection as evidence",
            "no automatic grading",
            "no accommodation decision by UniBot",
            "no real exam deployment without written authority clearance",
            "no public release of raw private course text",
        ],
        "default_help_policy": {
            "standard_allowed": list(STANDARD_HELP_LEVELS),
            "non_standard_visible_exception": ["A3", "A4"],
            "always_blocked": ["A5", "A6"],
            "eigenleistung_claim": "Use help-level profile, blocks, checkpoints, source links, and reflection; never claim a percentage.",
        },
        "scope_lanes": lanes,
        "required_record_fields": [
            "clearance_scope",
            "decision_status",
            "reviewer_roles",
            "decision_reference",
            "allowed_modes",
            "help_levels_allowed",
            "no_proctoring",
            "no_ai_detection",
            "no_automatic_grading",
            "human_review_required",
            "raw_text_public_release_allowed",
        ],
        "evidence_summary": {
            "review_board_status": review_board.get("status"),
            "reviewer_packet_count": len(review_board.get("reviewer_packets", [])),
            "compliance_matrix_status": compliance.get("status"),
            "high_risk_requirement_count": compliance.get("high_risk_requirement_count"),
            "source_card_count": compliance.get("source_card_count"),
        },
        "ready_for": ["public draft review", "local practice demo", "stakeholder decision preparation"],
        "not_ready_for": ["exam deployment", "official grading", "automatic support claims", "exam_controlled_gateway"],
        "next_actions": [
            "Collect written records per scope with the required reviewer roles.",
            "Validate records with the clearance validator before changing any local gate.",
            "Keep real exam deployment not_cleared until the responsible authorities have issued written clearance.",
        ],
    }
    attach_public_scan(board, public_safe=public_safe, source_name="institutional-clearance-board")
    return board


def build_regulatory_profile(*, public_safe: bool = True) -> dict[str, Any]:
    """Build the public-safe institutional profile for human review.

    This is a structured preparation artifact, not a legal opinion or a
    deployment switch. It deliberately contains policy boundaries and data
    categories, never notebook content, case material, credentials, or paths.
    """
    source_cards = []
    missing_source_card_ids = []
    for source_id in REGULATORY_SOURCE_CARD_IDS:
        card = get_source_card(source_id)
        if card is None:
            missing_source_card_ids.append(source_id)
            continue
        source_cards.append(
            {
                "source_id": card["source_id"],
                "title": card["title"],
                "url": card["url"],
                "authority_type": card["authority_type"],
                "last_checked": card["last_checked"],
            }
        )

    profile = {
        "schema_version": REGULATORY_PROFILE_SCHEMA_VERSION,
        "artifact_type": "unibot_regulatory_profile",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "review_preparation",
        "deployment_status": "not_cleared",
        "purpose": "Prepare a transparent human review of a local learning and practice tool.",
        "intended_use": "local_learning_and_practice",
        "institutional_reference": (
            "Universitaet zu Koeln; applicable module, faculty, examination, inclusion, and IT rules take precedence."
        ),
        "human_authority_required": [
            "KI-Office / CIO-Board",
            "Namentlich benannte fachverantwortliche Person",
            "Pruefungsamt",
            "Inklusionsbuero / Nachteilsausgleich",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
            "Thesis supervision",
        ],
        "data_flow": {
            "cell_and_attempt_text": "Ephemeral local processing only; never persisted in the public profile, GitHub, iCloud, or a model provider.",
            "tutor_output": "Deterministic local rule result; filtered before display and not used as a grade.",
            "persisted_metadata": [
                "session contract hash",
                "help level and source identifiers",
                "attempt and event hashes",
                "timestamps and cost metadata",
                "deletion and export receipts",
            ],
            "provider": "No provider is used by the local tutor; GLM development calls remain separately scoped and receive no learner content.",
            "public_repository": "Only synthetic tests, public source references, redacted summaries, and code are eligible for release.",
        },
        "retention_boundary": {
            "active_session": "Local session metadata only; raw cell text, attempt text, transcript, and notebook token are not persisted.",
            "ended_session": "Delete local session metadata after the configured retention period; provide immediate user deletion.",
            "export": "Voluntary preview first; export contains pseudonymous metadata and source identifiers, not notebook content.",
            "institutional_decision_needed": "Retention, access roles, deletion proof, and any pilot storage require written human review.",
        },
        "accessibility_commitments": [
            "Full keyboard operation with visible focus.",
            "Status announcements through an accessible live region.",
            "Readable contrast and layout at 200 percent zoom.",
            "Side panel remains usable from 280 pixels width.",
            "Manual cell selection and a non-AI fallback remain available when detection is uncertain.",
            "Accessibility support is cost-neutral and is never converted into a score or automatic accommodation decision.",
        ],
        "excluded_functions": [
            "automatic grading",
            "admissions or eligibility decisions",
            "proctoring or surveillance",
            "AI-use detection or disciplinary evidence",
            "automatic accommodation or Nachteilsausgleich decisions",
            "final-answer delivery",
            "exam authorization or legal clearance",
        ],
        "review_questions": [
            "Benötigt der vorgesehene Hochschulzweck eine KI-Office- oder CIO-Board-Entscheidung beziehungsweise eine Aufnahme in eine Positivliste?",
            "Wer wird für den konkreten Einsatz als fachverantwortliche Person mit menschlicher Letztverantwortung benannt?",
            "Which concrete local learning mode is acceptable for the named module and learner group?",
            "Which data categories, retention period, access roles, and deletion evidence are approved?",
            "Which accessibility functions are permitted without changing assessment criteria?",
            "Which help levels and source rules are acceptable for practice, if any?",
            "Which incident, outage, and manual fallback procedure is required?",
            "Which written authority decision would be required before any controlled exam track?",
        ],
        "open_gates": [
            "KI-Office / CIO-Board scope review and named human responsibility",
            "written university and module decision",
            "Datenschutz review of the concrete data flow",
            "IT / SZI security review of the local gateway and extension",
            "Inklusionsbuero review of accessibility and support boundaries",
            "human pilot protocol and consent decision",
            "separate exam-track approval; current status remains not_cleared",
        ],
        "source_card_ids": list(REGULATORY_SOURCE_CARD_IDS),
        "source_cards": source_cards,
        "missing_source_card_ids": missing_source_card_ids,
        "authorship": {
            "implementation_and_documentation": "Gretel / Codex",
            "glm_role": "proposal and independent review only when explicitly enabled; no contribution to this parked local profile",
            "human_responsibility": "Julius remains human project lead and merge/release decision-maker.",
        },
        "university_ai_governance": {
            "source_card_ids": ["uoc-ki-policy-2026", "uoc-medfak-ki-lehre-2026"],
            "review_roles": ["KI-Office", "CIO-Board", "fachverantwortliche Person"],
            "required_action": "Determine the applicable institutional scope, approval route, and named human responsibility before university deployment.",
            "status": "human_scope_review_required",
            "legal_effect": "none",
        },
        "legal_boundary": (
            "Planning and review artifact only. It is not legal advice, Datenschutz approval, examination clearance, inclusion approval, or a deployment authorization."
        ),
        "public_boundary": {
            "allowed": ["code", "synthetic tests", "aggregated metrics", "public source-card metadata", "redacted review summaries"],
            "blocked": ["raw notebook text", "learner attempts", "health or accommodation records", "credentials", "local paths", "private course material"],
        },
    }
    if missing_source_card_ids:
        profile["status"] = "blocked_missing_source_cards"
    attach_public_scan(profile, public_safe=public_safe, source_name="regulatory-profile-v1")
    return profile


def validate_regulatory_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    """Validate the profile contract without granting any real-world clearance."""
    payload = dict(profile or {})
    issues: list[str] = []
    required_exclusions = {
        "automatic grading",
        "proctoring or surveillance",
        "AI-use detection or disciplinary evidence",
        "automatic accommodation or Nachteilsausgleich decisions",
        "exam authorization or legal clearance",
    }
    if payload.get("schema_version") != REGULATORY_PROFILE_SCHEMA_VERSION:
        issues.append("schema_version_mismatch")
    if payload.get("deployment_status") != "not_cleared":
        issues.append("deployment_must_remain_not_cleared")
    if payload.get("intended_use") != "local_learning_and_practice":
        issues.append("intended_use_must_remain_local_learning_and_practice")
    if not payload.get("human_authority_required"):
        issues.append("human_authority_required")
    if not required_exclusions.issubset(set(payload.get("excluded_functions", []))):
        issues.append("strict_exclusions_incomplete")
    if "not legal advice" not in str(payload.get("legal_boundary", "")).lower():
        issues.append("legal_boundary_required")
    if payload.get("missing_source_card_ids"):
        issues.append("source_cards_missing")
    if payload.get("public_safety_status") not in {"pass", "local_private_mode"}:
        issues.append("public_safety_required")
    summary = {
        "schema_version": REGULATORY_PROFILE_SCHEMA_VERSION,
        "artifact_type": "regulatory_profile_validation",
        "status": "ok" if not issues else "blocked",
        "issues": sorted(set(issues)),
        "deployment_status": "not_cleared",
        "cleared_scope_by_profile": False,
        "legal_effect": "none",
        "human_review_required": True,
        "source_card_count": len(payload.get("source_cards", [])),
        "public_safety_status": payload.get("public_safety_status", "missing"),
    }
    scan = scan_text(json.dumps(summary, ensure_ascii=False), "regulatory-profile-validation")
    if scan["status"] != "pass":
        summary["status"] = "blocked"
        summary["issues"] = sorted(set(summary["issues"] + ["public_safety_findings"]))
        summary["public_safety_findings"] = scan["findings"]
    return summary


def build_institutional_presentation_packet(*, public_safe: bool = True) -> dict[str, Any]:
    """Build a compact, source-bound packet for institutional human review."""
    from .readiness import run_readiness_check
    from .release_runbook import build_release_runbook

    profile = build_regulatory_profile(public_safe=public_safe)
    profile_validation = validate_regulatory_profile(profile)
    accessibility_review = build_accessibility_review_plan(public_safe=public_safe)
    accessibility_validation = validate_accessibility_review_plan(accessibility_review)
    decision_template = build_institutional_review_decision_template(public_safe=public_safe)
    decision_template_validation = validate_institutional_review_decision_template(decision_template)
    board = build_institutional_clearance_board(public_safe=public_safe)
    runbook = build_release_runbook()
    readiness = run_readiness_check()
    evidence = {
        "regulatory_profile": {
            "schema_version": profile["schema_version"],
            "status": profile["status"],
            "validation_status": profile_validation["status"],
            "source_card_count": len(profile["source_cards"]),
            "public_safety_status": profile["public_safety_status"],
            "human_authority_required": list(profile["human_authority_required"]),
        },
        "institutional_clearance_board": {
            "status": board["status"],
            "public_safety_status": board["public_safety_status"],
            "exam_deployment_status": board["exam_deployment_status"],
            "scope_count": len(board["scope_lanes"]),
        },
        "readiness": {
            "status": readiness["status"],
            "passed_count": readiness["passed_count"],
            "check_count": readiness["check_count"],
            "evidence_snapshot_status": readiness["evidence_snapshot"]["status"],
        },
        "release_runbook": {
            "status": runbook["status"],
            "evidence_alignment_status": runbook["release_evidence_alignment"]["status"],
            "public_safety_status": runbook["public_safety_status"],
            "manual_review_required": runbook["manual_review_required"],
            "exam_deployment_status": runbook["exam_deployment_status"],
        },
        "browser_mantle": {
            "interface": "Chrome MV3 side panel with local companion/native messaging.",
            "supported_contexts": ["local Jupyter practice", "Colab practice surface", "manual text selection"],
            "uncertain_selection": "Ask the learner to select a cell; never guess.",
            "outputs": "Notebook outputs are not automatically captured.",
            "notebook_import": {
                "accepted_sources": ["allowlisted public HTTPS URL", "local .ipynb file picker"],
                "local_path_forwarded": False,
                "raw_source_stored": False,
                "sanitized_practice_copy_only": True,
                "demo_boundary": "Use only a public synthetic notebook for institutional demonstration.",
            },
            "practice_help_levels": list(PRACTICE_HELP_LEVELS),
            "controlled_exam_candidate_help_levels": list(CONTROLLED_EXAM_HELP_LEVELS),
            "controlled_exam_candidate_status": "requires_written_authority_decision",
            "manual_live_canary": "Required before any real institutional pilot.",
            "accessibility_evidence": {
                "status": "browser_tested_human_review_required",
                "automated_checks": [
                    "semantic status/live regions",
                    "tab-panel relationships",
                    "visible keyboard focus",
                    "tablist arrow-key, Home, and End navigation",
                    "280px minimum layout without horizontal overflow",
                ],
                "test_file": "tests/browser/mantle-v2.spec.js",
                "claim_boundary": "Automated evidence does not equal WCAG certification; institutional accessibility review remains open.",
                "review_plan_schema_version": accessibility_review["schema_version"],
                "review_plan_status": accessibility_review["status"],
                "review_plan_validation_status": accessibility_validation["status"],
                "standards_source_card_ids": list(ACCESSIBILITY_REVIEW_SOURCE_CARD_IDS),
            },
        },
        "accessibility_review": accessibility_review,
        "accessibility_review_validation": accessibility_validation,
        "institutional_review_decision_template": {
            "schema_version": decision_template["schema_version"],
            "status": decision_template["status"],
            "validation_status": decision_template_validation["status"],
            "public_safety_status": decision_template["public_safety_status"],
            "review_lane_count": len(decision_template["review_lanes"]),
            "automatic_approval": decision_template_validation["automatic_approval"],
        },
    }
    evidence_core = json.dumps(evidence, ensure_ascii=False, sort_keys=True)
    packet = {
        "schema_version": INSTITUTIONAL_PRESENTATION_SCHEMA_VERSION,
        "artifact_type": "unibot_institutional_presentation_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready_for_human_review",
        "review_status_label_de": "Vorlage für menschliche Prüfung; keine Freigabe",
        "deployment_status": "not_cleared",
        "audience": [
            "KI-Office / CIO-Board",
            "fachverantwortliche Person",
            "Pruefungsamt",
            "Inklusionsbuero / Nachteilsausgleich",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
            "Thesis supervision",
        ],
        "research_artifact": {
            "level": "bachelor_thesis_level",
            "label_de": "Gretel-gebaute und Gretel-dokumentierte Bachelorarbeitsfassung",
            "submission_status": "public scientific draft; not a submitted university thesis",
            "human_boundary": "Julius remains responsible for institutional review, submission, and release decisions.",
        },
        "university_ai_governance": profile["university_ai_governance"],
        "one_page_summary": {
            "product": "Lokale sokratische Lern- und Übungshilfe für Python-Notebooks.",
            "learner_flow": [
                "Öffentliche oder lokale .ipynb-Datei sicher bereinigen und in lokaler Jupyter-Umgebung öffnen; Colab bleibt eine Übungsoberfläche.",
                "Eine Zelle ausdrücklich auswählen und den eigenen nächsten Schritt formulieren.",
                "Im Übungsbetrieb A0 bis A4 als begrenzte, quellengebundene Hilfe erhalten; ein möglicher Prüfungstrack bleibt auf A0 bis A2 und schriftliche Entscheidung beschränkt.",
                "Hilfenutzung und eigene Versuche als datensparsame Metadaten rückblicken.",
                "Exportvorschau prüfen und nur freiwillig teilen.",
            ],
            "scientific_claim": "Messbare Sicherheits- und Quellenbindung; keine automatische Lernwirksamkeits- oder Notenbehauptung.",
            "inclusion_claim": "Bedienungshilfen bleiben zugänglich und kostenneutral; UniBot entscheidet keinen Nachteilsausgleich und automatisierte Evidenz ist keine WCAG-Zertifizierung.",
            "privacy_claim": "Lokaler Tutor ohne Provider; öffentliche Artefakte enthalten nur Code, Quellen und synthetische Evidenz.",
        },
        "demo_protocol": {
            "data": "Nur ein öffentliches, synthetisches Notebook verwenden.",
            "notebook_fixture": "fixtures/public/synthetic_python_practice.ipynb",
            "steps": [
                "Tutor und Gateway lokal starten und die öffentliche Synthetic-Fixture importieren.",
                "Synthetische Notebook-Zelle manuell auswählen.",
                "A0-, A1- und A2-Hinweis mit Quellenanker zeigen.",
                "Komplettlösung, Endwert und fertige Interpretation als blockiert zeigen.",
                "Rückblick, Exportvorschau und sofortige Löschung demonstrieren.",
            ],
            "expected_observation": "Die lernende Person bleibt handelnde Autorin; der Bot liefert gestufte Fragen und überprüfbare Anker.",
            "forbidden_demo_content": ["private course material", "health or accommodation records", "real examination task", "real learner transcript"],
        },
        "review_session": {
            "status": "human_review_meeting_ready",
            "suggested_duration_minutes": 25,
            "format": "public synthetic notebook demo followed by lane-specific review",
            "requested_outcome": "Written scope, conditions, responsible role, and next review gate; no automatic approval.",
            "sequence": [
                "State purpose, authorship, local-only data boundary, and not_cleared status.",
                "Run the synthetic notebook demo with A0-A2 help and show a blocked complete solution.",
                "Show keyboard, focus, zoom, uncertain-selection fallback, export preview, and deletion.",
                "Review each institutional lane and record open conditions without storing raw meeting text.",
            ],
            "office_lanes": [
                {
                    "office": "Pruefungsamt",
                    "question": "Ist der lokale Übungszweck mit den konkreten Modul- und Prüfungsregeln vereinbar, und welche separate Entscheidung wäre für einen Prüfungstrack nötig?",
                    "evidence": ["uoc-ki-policy-2026", "uoc-ki-pruefungsrecht", "uoc-ki-faq"],
                    "decision_boundary": "No exam clearance, grading, or permitted-aid decision is requested from this packet.",
                },
                {
                    "office": "Inklusionsbüro / Servicezentrum Inklusion",
                    "question": "Sind die kostenneutralen Bedienungs- und Strukturierungshilfen im vorgesehenen Lernformat zugänglich, ohne einen Nachteilsausgleich automatisch zu bestimmen?",
                    "evidence": [
                        "uoc-nachteilsausgleich",
                        "uoc-szi-klausurunterstuetzung-2026",
                        "uoc-szi-wegweiser-2026",
                        "wcag-22",
                        "bgg-nrw-10",
                        "bitv-nrw",
                    ],
                    "decision_boundary": "Accessibility evidence is a prototype claim; it is not a WCAG certification or an individual accommodation decision.",
                },
                {
                    "office": "Datenschutz / IT / SZI",
                    "question": "Sind lokaler Datenfluss, Speicherfristen, Löschung, Zugriffsschutz, Companion und Gateway für den vorgesehenen Übungszweck ausreichend beschrieben?",
                    "evidence": ["gdpr-2016-679", "dsk-ai-privacy-2024", "eu-ai-act-2024"],
                    "decision_boundary": "No private notebook, health, accommodation, credential, or local-path data is needed for the public demo.",
                },
                {
                    "office": "KI-Office / CIO-Board",
                    "question": "Welche Genehmigungsroute und welche namentlich benannte fachverantwortliche Person gelten für eine mögliche universitäre Bereitstellung?",
                    "evidence": ["uoc-ki-policy-2026", "uoc-medfak-ki-lehre-2026"],
                    "decision_boundary": "This packet does not request whitelist admission or institutional deployment approval.",
                },
                {
                    "office": "Lehre / Modulverantwortliche / Bachelorarbeitsbetreuung",
                    "question": "Sind Forschungsfrage, Hilfestufen, Quellenbindung, Lernendenautonomie und Evaluationsgrenzen für einen freiwilligen Übungspilot wissenschaftlich angemessen?",
                    "evidence": ["dfg-gwp", "vanlehn-2011", "kulik-fletcher-2016"],
                    "decision_boundary": "The artifact is a Gretel-built bachelor-thesis-level draft, not a submitted thesis or learning-effectiveness claim.",
                },
            ],
        },
        "human_decisions_needed": [
            "Welche institutionelle Genehmigungsroute gilt für den vorgesehenen Hochschulzweck: KI-Office, CIO-Board oder eine andere zuständige Stelle?",
            "Wer wird als fachverantwortliche Person mit menschlicher Letztverantwortung benannt?",
            "Ist der lokale Übungszweck für das konkrete Modul und die Zielgruppe pädagogisch geeignet?",
            "Welche Datenarten, Aufbewahrungsfristen, Rollen und Löschbelege sind institutionell zulässig?",
            "Welche Bedienungs- und Assistenzfunktionen sind im jeweiligen Lehrformat angemessen?",
            "Welche Quellen- und Hilfestufen sollen im Übungsbetrieb gelten?",
            "Welche separate schriftliche Entscheidung wäre für einen Prüfungstrack erforderlich?",
        ],
        "accessibility_review": accessibility_review,
        "accessibility_review_validation": accessibility_validation,
        "institutional_review_decision_template": decision_template,
        "institutional_review_decision_template_validation": decision_template_validation,
        "evidence": evidence,
        "evidence_hash": sha256_text(evidence_core),
        "strict_non_goals": [
            "no automatic grading",
            "no admissions or eligibility decisions",
            "no proctoring or surveillance",
            "no AI-use detection or disciplinary evidence",
            "no automatic accommodation decision",
            "no final-answer delivery",
            "no exam authorization or legal approval",
        ],
        "authorship": {
            "implementation_and_documentation": "Gretel / Codex",
            "glm_role": "No contribution while GLM is parked; later only proposal and counter-review.",
            "human_gate": "Julius remains human project lead and merge/release decision-maker.",
        },
        "legal_boundary": "Review preparation only; not legal advice, institutional approval, or examination clearance.",
    }
    attach_public_scan(packet, public_safe=public_safe, source_name="institutional-presentation-packet")
    if packet["public_safety_status"] != "pass":
        packet["status"] = "blocked_public_safety"
    if profile_validation["status"] != "ok":
        packet["status"] = "blocked_profile_validation"
    if accessibility_validation["status"] != "ok":
        packet["status"] = "blocked_accessibility_review_contract"
    if decision_template_validation["status"] != "ok":
        packet["status"] = "blocked_institutional_decision_template"
    if readiness["status"] != "public_draft_ready":
        packet["status"] = "blocked_readiness"
    if runbook["release_evidence_alignment"]["status"] != "ready":
        packet["status"] = "blocked_release_evidence"
    return packet


def build_institutional_presentation_markdown(
    packet: dict[str, Any] | None = None,
) -> str:
    """Render the compact packet for a human review meeting."""
    packet = packet or build_institutional_presentation_packet()
    summary = packet["one_page_summary"]
    evidence = packet["evidence"]
    lines = [
        "# UniBot Institutional Presentation",
        "",
        "## Vorlage für Prüfungsamt und Inklusionsbüro",
        "",
        f"**Status:** {packet['review_status_label_de']}",
        f"**Einsatzstatus:** `{packet['deployment_status']}`",
        f"**Für:** {', '.join(packet['audience'])}",
        "",
        "## Kurz gesagt",
        summary["product"],
        f"Diese öffentliche Fassung ist ausdrücklich eine **{packet['research_artifact']['label_de']}**; sie ist keine bereits eingereichte Hochschularbeit.",
        "UniBot legt sich als lokaler Chrome-Seitenbereich über ein Python-Notebook.",
        "Die lernende Person wählt eine Zelle, beschreibt ihren eigenen Versuch und erhält eine begrenzte sokratische Hilfe.",
        "Der Bot ersetzt weder die lernende Person noch eine institutionelle Entscheidung.",
        "",
        "## Ablauf im Übungsbetrieb",
        *[f"- {item}" for item in summary["learner_flow"]],
        "",
        "## Hilfestufen",
        "- **A0:** Ziel klären und den nächsten eigenen Schritt formulieren.",
        "- **A1:** Fehlerart oder kleinste Problemstelle eingrenzen.",
        "- **A2:** Konzept, Prüffrage und belastbare Quelle geben.",
        "- **A3:** Formelstruktur, Variablen oder Pseudocode geben.",
        "- **A4:** Nur ein unvollständiges Gerüst oder ein analoges Beispiel geben.",
        "- Vollständiger Aufgabencode, konkrete Endwerte und fertige Interpretation bleiben blockiert.",
        "",
        "## Inklusion und Barrierefreiheit",
        "- Tastaturbedienung, sichtbarer Fokus, Statusansagen und schmale Seitenbereiche sind technisch geprüft.",
        "- Unterstützung bleibt im Hilfebudget kostenneutral; der Bot bewertet keinen Nachteilsausgleich.",
        "- Welche Unterstützung im konkreten Modul angemessen und zulässig ist, entscheidet ausschließlich die zuständige Stelle.",
        "- Automatisierte Browser-Tests sind ein Nachweis für den Prototyp, keine WCAG-Zertifizierung.",
        f"- AccessibilityReviewV1 umfasst {len(packet['accessibility_review']['checks'])} reproduzierbare Prüfungen; kritische Fehler blockieren den jeweiligen Einsatzumfang.",
        "- Screenreader-, Reflow-, Ausfall- und datensparsame Nicht-Offenlegungsprüfungen benötigen menschliche Prüfung und Einwilligung, nicht Diagnosedaten.",
        "",
        "## Universitäts-Governance",
        "- Vor einer universitären Bereitstellung prüfen KI-Office/CIO-Board den konkreten Zweck und die zuständige Genehmigungsroute.",
        "- Eine namentlich benannte fachverantwortliche Person trägt die menschliche Letztverantwortung; UniBot übernimmt keine Entscheidung mit Rechtswirkung.",
        "- Diese Präsentation beantragt keine Aufnahme in eine Positivliste und erteilt keine Prüfungs- oder Inklusionsfreigabe.",
        "",
        "## Vorschlag für den Review-Termin",
        f"- Dauer: etwa **{packet['review_session']['suggested_duration_minutes']} Minuten**; Format: {packet['review_session']['format']}.",
        f"- Gewünschtes Ergebnis: {packet['review_session']['requested_outcome']}",
        *[f"- **{lane['office']}:** {lane['question']} Nachweise: {', '.join(lane['evidence'])}." for lane in packet['review_session']['office_lanes']],
        "",
        "## Datenschutz und Datenfluss",
        "- Zelltext, eigener Versuch, Notebook-Ausgaben und Tutor-Transkript werden nur flüchtig lokal verarbeitet.",
        "- Dauerhaft gespeichert werden ausschließlich Hashes, Hilfestufen, Quellen-IDs, Zeitpunkte und Lösch-/Exportmetadaten.",
        "- Der lokale Tutor nutzt keinen Provider; GLM erhält in dieser Phase keinen Lerninhalt.",
        "- Export und Weitergabe sind freiwillig und zeigen vorab eine Vorschau.",
        "",
        "## Ergebnisprotokoll der menschlichen Prüfung",
        "- Ein leeres `InstitutionalReviewDecisionTemplateV1` liegt dem Paket bei.",
        "- Es werden nur kontrollierte Ergebnis-, Bedingungen-, Fragen- und Evidenz-IDs sowie Hashes vorgesehen.",
        "- Gesprächsnotizen, Namen, Diagnosen, Nachteilsausgleichdaten, Notebookinhalte und Lernendentexte gehören nicht in das öffentliche Paket.",
        "- Das Formular erteilt keine Freigabe; eine mögliche Prüfungsentscheidung bleibt separat schriftlich und menschlich.",
        "",
        "## Wissenschaftliche Nachweise",
        f"- Sicherheits- und Quellenbindung: {summary['scientific_claim']}",
        f"- Inklusionsgrenze: {summary['inclusion_claim']}",
        f"- Datenschutzgrenze: {summary['privacy_claim']}",
        f"- RegulatoryProfileV1: {evidence['regulatory_profile']['validation_status']}",
        f"- Readiness: {evidence['readiness']['status']} ({evidence['readiness']['passed_count']}/{evidence['readiness']['check_count']})",
        f"- Release-Runbook: {evidence['release_runbook']['evidence_alignment_status']}",
        "- Browsermantel: Chrome MV3 mit lokalem Companion und Native Messaging.",
        f"- Barrierefreiheit: {evidence['browser_mantle']['accessibility_evidence']['status']}",
        "",
        "## Was der Bot ausdrücklich nicht tut",
        *[f"- {item}" for item in packet["strict_non_goals"]],
        "",
        "## Fragen an die zuständigen Stellen",
        *[f"- {item}" for item in packet["human_decisions_needed"]],
        "",
        "## Rollen und Autorenschaft",
        f"- Implementierung und Dokumentation: **{packet['authorship']['implementation_and_documentation']}**.",
        f"- GLM-Rolle: **{packet['authorship']['glm_role']}**",
        "- Menschliche Freigabe: Julius entscheidet über Veröffentlichung, Zusammenführung und jeden späteren Prüfungstrack.",
        "",
        f"**Rechtliche Grenze:** {packet['legal_boundary']}",
    ]
    return "\n".join(lines) + "\n"


def write_institutional_review_bundle(
    output_dir: str | Path,
    *,
    public_safe: bool = True,
) -> dict[str, Any]:
    """Write a public-safe, hash-bound institutional review handoff locally."""
    if not public_safe:
        raise ValueError("institutional review bundle requires public_safe=True")
    packet = build_institutional_presentation_packet(public_safe=True)
    if packet.get("status") != "ready_for_human_review":
        return {
            "schema_version": INSTITUTIONAL_REVIEW_BUNDLE_SCHEMA_VERSION,
            "artifact_type": "unibot_institutional_review_bundle",
            "status": "blocked",
            "reason": "presentation_packet_not_ready_for_human_review",
            "packet_status": packet.get("status"),
            "exam_deployment_status": "not_cleared",
        }
    markdown = build_institutional_presentation_markdown(packet)
    json_text = json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    contents = {
        "institutional-presentation.json": json_text,
        "institutional-presentation.md": markdown,
        "institutional-review-decision-template.md": build_institutional_review_decision_template_markdown(
            packet["institutional_review_decision_template"]
        ),
    }
    file_records: list[dict[str, Any]] = []
    for name, content in contents.items():
        scan = scan_text(content, name)
        if scan["status"] != "pass":
            return {
                "schema_version": INSTITUTIONAL_REVIEW_BUNDLE_SCHEMA_VERSION,
                "artifact_type": "unibot_institutional_review_bundle",
                "status": "blocked",
                "reason": "bundle_public_safety_scan_failed",
                "finding_count": len(scan["findings"]),
                "exam_deployment_status": "not_cleared",
            }
        file_records.append(
            {
                "name": name,
                "bytes": len(content.encode("utf-8")),
                "sha256": sha256_text(content),
                "public_safety_status": scan["status"],
            }
        )
    manifest = {
        "schema_version": "unibot-institutional-review-bundle-manifest-v1",
        "artifact_type": "unibot_institutional_review_bundle_manifest",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "packet_schema_version": packet["schema_version"],
        "packet_status": packet["status"],
        "exam_deployment_status": "not_cleared",
        "files": file_records,
        "evidence_hash": packet["evidence_hash"],
        "authorship": packet["authorship"],
        "human_release_gate": "Julius remains human project lead and merge/release decision-maker.",
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    contents["MANIFEST.json"] = manifest_text
    root = Path(output_dir).expanduser()
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("institutional review bundle output must be a real directory")
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    for name, content in contents.items():
        target = root / name
        temporary = root / f".{name}.{os.getpid()}.tmp"
        temporary.write_text(content, encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        os.chmod(target, 0o600)
    return {
        "schema_version": INSTITUTIONAL_REVIEW_BUNDLE_SCHEMA_VERSION,
        "artifact_type": "unibot_institutional_review_bundle",
        "status": "written",
        "packet_status": packet["status"],
        "exam_deployment_status": "not_cleared",
        "file_names": sorted(contents),
        "file_count": len(contents),
        "manifest_sha256": sha256_text(manifest_text),
        "evidence_hash": packet["evidence_hash"],
        "public_safety_status": "pass",
        "raw_learner_content_written": False,
        "local_paths_written_to_bundle": False,
    }


def clearance_lane(scope_id: str, scope: dict[str, Any]) -> dict[str, Any]:
    source_cards = [
        {
            "source_id": card["source_id"],
            "title": card["title"],
            "authority_type": card["authority_type"],
            "product_rule": card["product_rule"],
        }
        for source_id in scope["required_source_card_ids"]
        if (card := get_source_card(source_id))
    ]
    return {
        "clearance_scope": scope_id,
        "label": scope["label"],
        "current_status": scope["current_status"],
        "exam_deployment_status": scope["exam_deployment_status"],
        "required_reviewer_roles": scope["required_reviewer_roles"],
        "allowed_modes_if_cleared": scope["allowed_modes"],
        "decision_needed": scope["decision_needed"],
        "does_not_authorize": scope["does_not_authorize"],
        "source_cards": source_cards,
        "minimum_record_template": {
            "clearance_scope": scope_id,
            "decision_status": "needs_review",
            "reviewer_roles": scope["required_reviewer_roles"],
            "decision_reference": "hash-only reference; do not publish the written record text",
            "allowed_modes": scope["allowed_modes"],
            "help_levels_allowed": ["A0", "A1", "A2"],
            "no_proctoring": True,
            "no_ai_detection": True,
            "no_automatic_grading": True,
            "human_review_required": True,
            "raw_text_public_release_allowed": False,
            "notes": "scope-specific written decision required before use",
        },
    }


def validate_clearance_record(record: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(record or {})
    issues: list[str] = []
    warnings: list[str] = []

    scope_id = str(payload.get("clearance_scope", "")).strip()
    scope = CLEARANCE_SCOPES.get(scope_id)
    if scope is None:
        issues.append("unsupported_clearance_scope")

    decision_status = str(payload.get("decision_status", "")).strip()
    if decision_status not in ALLOWED_DECISION_STATUSES:
        issues.append("unsupported_decision_status")

    reviewer_roles = [str(item).strip() for item in payload.get("reviewer_roles", []) if str(item).strip()]
    required_roles = list(scope.get("required_reviewer_roles", [])) if scope else []
    missing_roles = [role for role in required_roles if role not in reviewer_roles]
    if missing_roles:
        issues.append("missing_required_reviewer_roles")

    allowed_modes = [str(item).strip() for item in payload.get("allowed_modes", []) if str(item).strip()]
    if not allowed_modes:
        issues.append("allowed_modes_required")
    if scope:
        unsupported_modes = [mode for mode in allowed_modes if mode not in scope["allowed_modes"]]
        if unsupported_modes:
            issues.append("allowed_modes_outside_clearance_scope")

    help_levels_allowed = [str(item).strip() for item in payload.get("help_levels_allowed", []) if str(item).strip()]
    if not help_levels_allowed:
        issues.append("help_levels_allowed_required")
    if any(level in BLOCKED_HELP_LEVELS for level in help_levels_allowed):
        issues.append("a6_must_always_be_blocked")
    if scope_id == "exam_controlled_gateway":
        outside_standard = [level for level in help_levels_allowed if level not in STANDARD_HELP_LEVELS]
        if outside_standard:
            issues.append("exam_gateway_allows_only_a0_a2_standard_help")

    if not bool(payload.get("no_proctoring", False)):
        issues.append("no_proctoring_clause_required")
    if not bool(payload.get("no_ai_detection", False)):
        issues.append("no_ai_detection_clause_required")
    if not bool(payload.get("no_automatic_grading", False)):
        issues.append("no_automatic_grading_clause_required")
    if not bool(payload.get("human_review_required", False)):
        issues.append("human_review_required")
    if bool(payload.get("raw_text_public_release_allowed", False)):
        issues.append("raw_text_public_release_must_remain_false")

    decision_reference = str(payload.get("decision_reference", "")).strip()
    if not decision_reference:
        issues.append("decision_reference_required")
    decision_reference_hash = sha256_text(decision_reference) if decision_reference else ""

    if decision_status == "approved" and scope_id != "practice_public_draft":
        warnings.append("approval_record_must_stay_scope_bound_and_human_reviewable")
    if scope_id == "exam_controlled_gateway" and decision_status == "approved":
        warnings.append("validator_checks_record_shape_only_not_real_world_authority_or_deployment")

    safe_summary = {
        "schema_version": INSTITUTIONAL_CLEARANCE_SCHEMA_VERSION,
        "artifact_type": "institutional_clearance_record_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": record_status(decision_status, issues, scope_id),
        "clearance_scope": scope_id or "missing",
        "decision_status": decision_status or "missing",
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "required_reviewer_roles": required_roles,
        "reviewer_roles": reviewer_roles,
        "allowed_modes": allowed_modes,
        "help_levels_allowed": help_levels_allowed,
        "cleared_scope_by_record": not issues and decision_status == "approved",
        "exam_deployment_status": "not_cleared",
        "record_effect": record_effect(scope_id, decision_status, issues),
        "decision_reference_hash": decision_reference_hash,
        "raw_decision_reference_stored": False,
        "policy": (
            "A valid record is a human-reviewable clearance artifact for the named scope only. "
            "It does not by itself publish private material, grade students, detect KI use, "
            "or switch the running system into real exam deployment."
        ),
    }
    scan = scan_text(json.dumps(safe_summary, ensure_ascii=False), "institutional-clearance-validation")
    safe_summary["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        safe_summary["status"] = "blocked"
        safe_summary["public_safety_findings"] = scan["findings"]
    return safe_summary


def record_status(decision_status: str, issues: list[str], scope_id: str) -> str:
    if issues:
        return "blocked"
    if decision_status == "approved":
        return f"ok_{scope_id}_clearance_record"
    if decision_status == "rejected":
        return "rejected"
    return "needs_review"


def record_effect(scope_id: str, decision_status: str, issues: list[str]) -> str:
    if issues:
        return "no_effect_blocked_record"
    if decision_status == "approved":
        return f"scope_clearance_record_valid_for_{scope_id}"
    if decision_status == "rejected":
        return "scope_rejected_by_record"
    return "scope_still_needs_human_review"


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
