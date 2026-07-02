from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .pilot import build_pilot_protocol
from .public_safety import scan_text
from .source_cards import get_source_card


DATA_PROTECTION_SCHEMA_VERSION = "unibot-data-protection-screening-v1"


def build_data_protection_screening() -> dict[str, Any]:
    source_ids = [
        "gdpr-2016-679",
        "dsk-ai-privacy-2024",
        "eu-ai-act-2024",
        "chrome-limited-use",
        "uoc-ki-lehre",
        "uoc-nachteilsausgleich",
    ]
    source_cards = [card for source_id in source_ids if (card := get_source_card(source_id))]
    compliance = build_compliance_matrix()
    pilot = build_pilot_protocol()
    screening = {
        "schema_version": DATA_PROTECTION_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "draft_for_datenschutz_review",
        "status_label_de": "Entwurf: Datenschutzpruefung erforderlich vor echtem Pilot",
        "exam_deployment_status": "not_cleared",
        "scope": "local-first practice MVP and synthetic formative pilot planning",
        "non_advice_boundary": "Operational screening draft only; not legal advice and not Datenschutz approval.",
        "processing_principles": [
            {
                "principle_id": "purpose_limitation",
                "product_rule": "Use data only for visible practice filtering, local selftest, public-safe feedback triage, or reviewed pilot analysis.",
                "control": "Each endpoint and artifact declares practice-only or public-draft status.",
            },
            {
                "principle_id": "data_minimisation",
                "product_rule": "Collect the smallest metadata set needed for Socratic filtering and formative evaluation.",
                "control": "Raw external KI answers are represented by hashes by default; public summaries exclude free text.",
            },
            {
                "principle_id": "transparency",
                "product_rule": "Learners and reviewers must see what is stored, excluded, and not approved.",
                "control": "Pilot consent items, release runbook, and system/data cards state boundaries.",
            },
            {
                "principle_id": "storage_limitation",
                "product_rule": "Retention must be defined before a real participant pilot.",
                "control": "Pilot protocol keeps retention_status open for Datenschutz review.",
            },
            {
                "principle_id": "integrity_confidentiality",
                "product_rule": "Public artifacts must not contain private course material, local paths, secrets, contact data, or special-category details.",
                "control": "Public-safety scanner and readiness gate block known public-leak patterns.",
            },
            {
                "principle_id": "accountability",
                "product_rule": "Authority-facing evidence must link sources, rules, controls, tests, and open decisions.",
                "control": "Compliance matrix, readiness report, and publication package provide machine-readable evidence.",
            },
        ],
        "processing_activities": [
            {
                "activity_id": "prompt_card_generation",
                "purpose": "Create a visible Socratic question card for a synthetic or practice task.",
                "data_categories": ["task text", "skill tags", "source card IDs"],
                "storage_default": "not stored unless the user creates a local ledger event",
                "external_transfer": "none by UniBot",
                "risk_level": "low",
                "controls": ["visible prompt", "no private-data requirement", "public-safety scan available"],
            },
            {
                "activity_id": "external_ai_postfilter",
                "purpose": "Classify pasted Colab/Gemini or other KI output before learner use.",
                "data_categories": ["pasted external KI answer", "requested help level", "classification categories"],
                "storage_default": "hash-only by default for raw pasted answer",
                "external_transfer": "none by UniBot; external tool use is initiated by the learner in practice mode",
                "risk_level": "medium",
                "controls": ["solution blocker", "privacy blocker", "raw answer omitted from public events"],
            },
            {
                "activity_id": "help_ledger",
                "purpose": "Document help intensity and private formative independence score locally.",
                "data_categories": ["raw-output hash", "help level", "skill tags", "categories", "redacted reflection status"],
                "storage_default": "local-only JSONL ledger",
                "external_transfer": "none by default",
                "risk_level": "medium",
                "controls": ["redaction", "public summary only", "private score is not a grade"],
            },
            {
                "activity_id": "demo_feedback",
                "purpose": "Collect public-safe bug reports and usability feedback for the prototype.",
                "data_categories": ["scenario ID", "outcome", "severity", "component", "public-safe summary flags"],
                "storage_default": "local feedback records only when validation passes",
                "external_transfer": "manual GitHub issue publication only after review",
                "risk_level": "medium",
                "controls": ["private_data_removed required", "issue bundle manual review", "no copied private free text"],
            },
            {
                "activity_id": "synthetic_pilot_records",
                "purpose": "Evaluate formative learning-process signals in synthetic tasks.",
                "data_categories": pilot["data_management_plan"]["default_data"],
                "storage_default": pilot["data_management_plan"]["storage"],
                "external_transfer": "none until institutional review approves storage, access, and retention",
                "risk_level": "medium",
                "controls": ["voluntary consent", "synthetic tasks only", "withdrawal handling", "public summaries only"],
            },
            {
                "activity_id": "exam_controlled_mode",
                "purpose": "Future controlled exam-like use, not implemented for the public MVP.",
                "data_categories": ["not defined"],
                "storage_default": "blocked",
                "external_transfer": "blocked",
                "risk_level": "high",
                "controls": ["requires written clearance", "requires managed channel", "not part of public practice release"],
                "status": "blocked_until_authority_review",
            },
        ],
        "risk_register": [
            {
                "risk_id": "private_data_entry",
                "risk": "Participant enters private course, contact, local path, or special-category details.",
                "severity": "high",
                "controls": ["participant instruction", "public-safety scan", "stop rule", "redaction"],
                "residual_status": "requires review before real pilot",
            },
            {
                "risk_id": "external_tool_transfer",
                "risk": "Learner sends private text to an external KI tool during practice.",
                "severity": "high",
                "controls": ["Prompt Card warns against private content", "practice-only framing", "copy/paste fallback"],
                "residual_status": "requires training and reviewed participant sheet",
            },
            {
                "risk_id": "score_misuse",
                "risk": "Private formative score is treated as grade, disciplinary evidence, or support decision.",
                "severity": "high",
                "controls": ["no grade boundary", "publication non-goals", "compliance matrix blocked uses"],
                "residual_status": "blocked for official assessment",
            },
            {
                "risk_id": "browser_overlay_overclaim",
                "risk": "Normal browser overlay is mistaken for hard exam security.",
                "severity": "high",
                "controls": ["threat model", "release runbook language", "exam mode blocked"],
                "residual_status": "requires managed environment for any future exam path",
            },
            {
                "risk_id": "public_repository_leak",
                "risk": "Public documentation or issues include private material.",
                "severity": "high",
                "controls": ["public-safety scanner", "GitHub issue bundle manual review", "readiness gate"],
                "residual_status": "controlled for draft artifacts; still needs human review",
            },
        ],
        "open_decisions_for_datenschutz": [
            "Which storage location is approved for any real pilot records?",
            "What retention period applies before and after aggregation?",
            "Who may access non-public pilot records?",
            "Whether a formal Datenschutz-Folgenabschaetzung is required for the reviewed pilot.",
            "Whether any cloud service may be used for external KI or record storage.",
            "Which withdrawal and deletion workflow must be documented before recruitment.",
        ],
        "pilot_alignment": {
            "pilot_status": pilot["status"],
            "consent_item_count": len(pilot["consent_items"]),
            "ethics_trigger_count": len(pilot["ethics_review_triggers"]),
            "compliance_status": compliance["status"],
            "compliance_public_safety_status": compliance["public_safety_status"],
        },
        "review_gates": {
            "public_safety_required": True,
            "datenschutz_review_required_before_real_pilot": True,
            "ethics_or_supervisor_review_required_before_real_pilot": True,
            "authority_review_required_before_exam_context": True,
            "exam_deployment_status": "not_cleared",
        },
        "source_cards": source_cards,
        "policy": "Data-protection screening is a planning artifact only; real pilots require institutional Datenschutz review before recruitment or data collection.",
    }
    scan = scan_text(json.dumps(screening, ensure_ascii=False), "data-protection-screening")
    screening["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        screening["status"] = "blocked_public_safety"
        screening["public_safety_findings"] = scan["findings"]
    return screening


def build_data_protection_screening_markdown() -> str:
    screening = build_data_protection_screening()
    principle_lines = "\n".join(
        f"- `{item['principle_id']}`: {item['product_rule']} Control: {item['control']}"
        for item in screening["processing_principles"]
    )
    activity_lines = "\n".join(
        f"- `{item['activity_id']}`: {item['purpose']} Risk: {item['risk_level']}; storage: {item['storage_default']}"
        for item in screening["processing_activities"]
    )
    risk_lines = "\n".join(
        f"- `{item['risk_id']}`: {item['risk']} Severity: {item['severity']}; residual: {item['residual_status']}"
        for item in screening["risk_register"]
    )
    decision_lines = "\n".join(f"- {item}" for item in screening["open_decisions_for_datenschutz"])
    source_lines = "\n".join(
        f"- `{card['source_id']}`: {card['product_rule']}" for card in screening["source_cards"]
    )
    return (
        "# UniBot Data Protection Screening\n\n"
        f"Status: {screening['status_label_de']}\n\n"
        f"Exam deployment: {screening['exam_deployment_status']}\n\n"
        f"Scope: {screening['scope']}\n\n"
        f"Boundary: {screening['non_advice_boundary']}\n\n"
        "## Processing Principles\n\n"
        f"{principle_lines}\n\n"
        "## Processing Activities\n\n"
        f"{activity_lines}\n\n"
        "## Risk Register\n\n"
        f"{risk_lines}\n\n"
        "## Open Decisions For Datenschutz\n\n"
        f"{decision_lines}\n\n"
        "## Source Cards\n\n"
        f"{source_lines}\n\n"
        f"Policy: {screening['policy']}\n"
    )
