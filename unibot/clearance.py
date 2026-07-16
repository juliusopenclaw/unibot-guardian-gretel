from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .materials import sha256_text
from .public_safety import scan_text
from .review_board import build_review_board_packet
from .source_cards import get_source_card


INSTITUTIONAL_CLEARANCE_SCHEMA_VERSION = "unibot-institutional-clearance-v1"
REGULATORY_PROFILE_SCHEMA_VERSION = "RegulatoryProfileV1"
INSTITUTIONAL_PRESENTATION_SCHEMA_VERSION = "InstitutionalPresentationV1"

ALLOWED_DECISION_STATUSES = {"needs_review", "approved", "rejected"}
STANDARD_HELP_LEVELS = {"A0", "A1", "A2"}
BLOCKED_HELP_LEVELS = {"A6"}

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
        "label": "Formative pilot or master-thesis study rehearsal",
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
    "uoc-ki-lehre",
    "uoc-hilfsmittel",
    "uoc-nachteilsausgleich",
    "gdpr-2016-679",
    "dsk-ai-privacy-2024",
    "eu-ai-act-2024",
    "hg-nrw-64",
    "dfg-gwp",
    "jupyter-ai",
]


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
            "standard_allowed": ["A0", "A1", "A2"],
            "non_standard_visible_exception": ["A3", "A4", "A5"],
            "always_blocked": ["A6"],
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
            "Which concrete local learning mode is acceptable for the named module and learner group?",
            "Which data categories, retention period, access roles, and deletion evidence are approved?",
            "Which accessibility functions are permitted without changing assessment criteria?",
            "Which help levels and source rules are acceptable for practice, if any?",
            "Which incident, outage, and manual fallback procedure is required?",
            "Which written authority decision would be required before any controlled exam track?",
        ],
        "open_gates": [
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
            "supported_contexts": ["synthetic Jupyter", "synthetic Colab fixture", "manual text selection"],
            "uncertain_selection": "Ask the learner to select a cell; never guess.",
            "outputs": "Notebook outputs are not automatically captured.",
            "manual_live_canary": "Required before any real institutional pilot.",
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
            "Pruefungsamt",
            "Inklusionsbuero / Nachteilsausgleich",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
            "Thesis supervision",
        ],
        "one_page_summary": {
            "product": "Lokale sokratische Lern- und Übungshilfe für Python-Notebooks.",
            "learner_flow": [
                "Notebook in lokaler Jupyter-Umgebung oder synthetischer Browser-Fixture öffnen.",
                "Eine Zelle ausdrücklich auswählen und den eigenen nächsten Schritt formulieren.",
                "A0 bis A2 als begrenzte, quellengebundene Hilfe erhalten.",
                "Hilfenutzung und eigene Versuche als datensparsame Metadaten rückblicken.",
                "Exportvorschau prüfen und nur freiwillig teilen.",
            ],
            "scientific_claim": "Messbare Sicherheits- und Quellenbindung; keine automatische Lernwirksamkeits- oder Notenbehauptung.",
            "inclusion_claim": "Bedienungshilfen bleiben zugänglich und kostenneutral; UniBot entscheidet keinen Nachteilsausgleich.",
            "privacy_claim": "Lokaler Tutor ohne Provider; öffentliche Artefakte enthalten nur Code, Quellen und synthetische Evidenz.",
        },
        "demo_protocol": {
            "data": "Nur ein öffentliches, synthetisches Notebook verwenden.",
            "steps": [
                "Tutor und Gateway lokal starten.",
                "Synthetische Notebook-Zelle manuell auswählen.",
                "A0-, A1- und A2-Hinweis mit Quellenanker zeigen.",
                "Komplettlösung, Endwert und fertige Interpretation als blockiert zeigen.",
                "Rückblick, Exportvorschau und sofortige Löschung demonstrieren.",
            ],
            "expected_observation": "Die lernende Person bleibt handelnde Autorin; der Bot liefert gestufte Fragen und überprüfbare Anker.",
            "forbidden_demo_content": ["private course material", "health or accommodation records", "real examination task", "real learner transcript"],
        },
        "human_decisions_needed": [
            "Ist der lokale Übungszweck für das konkrete Modul und die Zielgruppe pädagogisch geeignet?",
            "Welche Datenarten, Aufbewahrungsfristen, Rollen und Löschbelege sind institutionell zulässig?",
            "Welche Bedienungs- und Assistenzfunktionen sind im jeweiligen Lehrformat angemessen?",
            "Welche Quellen- und Hilfestufen sollen im Übungsbetrieb gelten?",
            "Welche separate schriftliche Entscheidung wäre für einen Prüfungstrack erforderlich?",
        ],
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
        f"Status: {packet['status']}",
        f"Einsatzstatus: {packet['deployment_status']}",
        f"Für: {', '.join(packet['audience'])}",
        "",
        "## Zweck",
        summary["product"],
        "",
        "## Ablauf",
        *[f"- {item}" for item in summary["learner_flow"]],
        "",
        "## Nachweise",
        f"- RegulatoryProfileV1: {evidence['regulatory_profile']['validation_status']}",
        f"- Readiness: {evidence['readiness']['status']} ({evidence['readiness']['passed_count']}/{evidence['readiness']['check_count']})",
        f"- Release-Runbook: {evidence['release_runbook']['evidence_alignment_status']}",
        f"- Browsermantel: {evidence['browser_mantle']['interface']}",
        "",
        "## Menschliche Entscheidungen",
        *[f"- {item}" for item in packet["human_decisions_needed"]],
        "",
        "## Grenzen",
        *[f"- {item}" for item in packet["strict_non_goals"]],
        "",
        "## Autorenschaft",
        f"- Implementierung und Dokumentation: {packet['authorship']['implementation_and_documentation']}",
        f"- Menschlicher Gate: {packet['authorship']['human_gate']}",
        "",
        packet["legal_boundary"],
    ]
    return "\n".join(lines) + "\n"


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
