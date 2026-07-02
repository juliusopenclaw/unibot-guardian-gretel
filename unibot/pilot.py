from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .evaluation import build_evaluation_packet
from .public_safety import scan_text
from .redteam import run_redteam_smoke
from .source_cards import get_source_card


PILOT_PROTOCOL_SCHEMA_VERSION = "unibot-pilot-protocol-v1"


def build_pilot_protocol() -> dict[str, Any]:
    source_ids = [
        "dfg-gwp",
        "gdpr-2016-679",
        "dsk-ai-privacy-2024",
        "eu-ai-act-2024",
        "uoc-ki-lehre",
        "uoc-nachteilsausgleich",
        "vanlehn-2011",
        "kulik-fletcher-2016",
        "unesco-genai-2023",
    ]
    source_cards = [card for source_id in source_ids if (card := get_source_card(source_id))]
    evaluation = build_evaluation_packet()
    compliance = build_compliance_matrix()
    redteam = run_redteam_smoke()
    protocol = {
        "schema_version": PILOT_PROTOCOL_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "draft_not_ethics_or_authority_cleared",
        "status_label_de": "Entwurf: noch keine Ethik-, Datenschutz- oder Pruefungsfreigabe",
        "exam_deployment_status": "not_cleared",
        "title": "UniBot Guardian formative pilot protocol",
        "purpose": (
            "Prepare a voluntary, formative, synthetic-task pilot for evaluating whether UniBot preserves "
            "student cognitive work while filtering external KI help into Socratic scaffolding."
        ),
        "participant_scope": {
            "scope": "voluntary formative pilot with synthetic Python-neuroscience practice tasks only",
            "excluded": [
                "real exams",
                "graded assignments",
                "mandatory course participation",
                "minors or vulnerable groups without separate review",
                "medical or accommodation personal data",
                "private course files",
            ],
        },
        "participant_information": {
            "plain_language_summary": (
                "Participants try synthetic programming tasks, may use visible UniBot prompts and filters, "
                "and give feedback on whether the support keeps them thinking instead of receiving final answers."
            ),
            "what_happens": [
                "Briefing on practice-only status and data boundaries.",
                "Synthetic task attempt in a local or demo environment.",
                "Optional external KI answer is pasted into UniBot for filtering.",
                "Participant writes a short reflection on their next own step.",
                "Participant gives public-safe usability feedback.",
                "Debrief explains that UniBot is not exam clearance or an assessment tool.",
            ],
            "risks": [
                "False confidence if KI help is mistaken for understanding.",
                "Privacy risk if private details are entered despite instructions.",
                "Confusion if practice support is mistaken for official exam permission.",
            ],
            "risk_controls": [
                "Synthetic tasks only.",
                "Public-safety scanner and redaction rules.",
                "Clear not-cleared exam language in UI and documents.",
                "Stop rules for private data, discomfort, or real-assessment drift.",
            ],
            "questions_contact_policy": (
                "Use the institutionally reviewed contact route in the approved participant sheet; "
                "do not publish personal contact details in the public repository."
            ),
        },
        "consent_items": [
            {
                "item_id": "voluntary_participation",
                "text": "I understand that participation is voluntary and can stop at any time.",
                "required": True,
            },
            {
                "item_id": "no_grade_or_exam_effect",
                "text": "I understand that the pilot does not affect grades, exam access, or support decisions.",
                "required": True,
            },
            {
                "item_id": "synthetic_tasks_only",
                "text": "I agree to use only synthetic practice tasks, not real exam or graded work.",
                "required": True,
            },
            {
                "item_id": "no_private_data_entry",
                "text": "I agree not to enter private course files, local paths, personal contact data, or health-related details.",
                "required": True,
            },
            {
                "item_id": "local_minimal_metadata",
                "text": "I understand that UniBot stores minimal local metadata by default, not raw external KI answers.",
                "required": True,
            },
            {
                "item_id": "public_summary_only",
                "text": "I understand that public reports use synthetic examples and aggregate or redacted summaries only.",
                "required": True,
            },
            {
                "item_id": "not_exam_security",
                "text": "I understand that the browser overlay is practice support, not exam security.",
                "required": True,
            },
        ],
        "data_management_plan": {
            "default_data": [
                "task IDs",
                "skill tags",
                "help levels",
                "classification categories",
                "raw-output hashes",
                "redacted reflection status",
                "public-safe feedback categories",
            ],
            "excluded_data": [
                "raw external KI answers",
                "private course material",
                "personal contact data",
                "medical or accommodation personal data",
                "real exam work",
                "grades",
                "local filesystem paths",
            ],
            "storage": "local-first until institutional data-management review defines approved storage and retention.",
            "access": "project researcher and approved reviewers only for non-public pilot records.",
            "publication": "public package contains code, synthetic tasks, source cards, codebook, aggregate summaries, and limitations.",
            "withdrawal_handling": "Before aggregation, remove participant-coded local records when withdrawal is requested.",
            "retention_status": "to_be_defined_by_datenschutz_before_real_pilot",
        },
        "ethics_review_triggers": [
            "Any move from synthetic practice to real course or exam work.",
            "Any collection of special-category or accommodation-related personal data.",
            "Any mandatory participation or dependency relationship.",
            "Any publication of participant free text beyond public-safe summaries.",
            "Any cloud storage of non-public pilot records.",
            "Any claim about official learning assessment, exam security, or misconduct detection.",
        ],
        "session_flow": [
            {"phase": "briefing", "artifact": "participant information and consent checklist"},
            {"phase": "synthetic_task", "artifact": "evaluation task set"},
            {"phase": "guardian_use", "artifact": "Prompt Card, Postfilter, Help Ledger summary"},
            {"phase": "reflection", "artifact": "next-own-step response"},
            {"phase": "feedback", "artifact": "public-safe demo feedback form"},
            {"phase": "debrief", "artifact": "limits, no exam clearance, withdrawal reminder"},
        ],
        "stop_rules": evaluation["consent_boundary"]["stop_rules"],
        "readiness_gates": {
            "redteam_status": redteam["status"],
            "evaluation_status": evaluation["status"],
            "compliance_status": compliance["status"],
            "compliance_public_safety_status": compliance["public_safety_status"],
            "required_before_real_pilot": [
                "ethics or supervisor decision on whether review is required",
                "Datenschutz review of storage, retention, and access",
                "authority review if any course or exam context is involved",
                "frozen synthetic tasks and codebook",
                "tested withdrawal and redaction procedure",
            ],
        },
        "source_cards": source_cards,
        "policy": "Pilot protocol is a public-safe planning draft only, not ethics clearance, not data-protection approval, and not exam clearance.",
    }
    scan = scan_text(json.dumps(protocol, ensure_ascii=False), "pilot-protocol")
    protocol["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        protocol["status"] = "blocked_public_safety"
        protocol["public_safety_findings"] = scan["findings"]
    return protocol


def build_pilot_protocol_markdown() -> str:
    protocol = build_pilot_protocol()
    scope = protocol["participant_scope"]
    excluded = "\n".join(f"- {item}" for item in scope["excluded"])
    consent_lines = "\n".join(
        f"- `{item['item_id']}`: {item['text']}" for item in protocol["consent_items"]
    )
    data_excluded = "\n".join(f"- {item}" for item in protocol["data_management_plan"]["excluded_data"])
    trigger_lines = "\n".join(f"- {item}" for item in protocol["ethics_review_triggers"])
    flow_lines = "\n".join(
        f"- {step['phase']}: {step['artifact']}" for step in protocol["session_flow"]
    )
    source_lines = "\n".join(
        f"- `{card['source_id']}`: {card['product_rule']}" for card in protocol["source_cards"]
    )
    return (
        "# UniBot Pilot Protocol\n\n"
        f"Status: {protocol['status_label_de']}\n\n"
        f"Exam deployment: {protocol['exam_deployment_status']}\n\n"
        f"Purpose: {protocol['purpose']}\n\n"
        "## Participant Scope\n\n"
        f"{scope['scope']}\n\n"
        "Excluded:\n\n"
        f"{excluded}\n\n"
        "## Consent Checklist\n\n"
        f"{consent_lines}\n\n"
        "## Data Management\n\n"
        f"Storage: {protocol['data_management_plan']['storage']}\n\n"
        "Excluded data:\n\n"
        f"{data_excluded}\n\n"
        "## Ethics Review Triggers\n\n"
        f"{trigger_lines}\n\n"
        "## Session Flow\n\n"
        f"{flow_lines}\n\n"
        "## Readiness Gates\n\n"
        f"- Red-Team: {protocol['readiness_gates']['redteam_status']}\n"
        f"- Evaluation: {protocol['readiness_gates']['evaluation_status']}\n"
        f"- Compliance: {protocol['readiness_gates']['compliance_status']}\n\n"
        "## Source Cards\n\n"
        f"{source_lines}\n\n"
        f"Policy: {protocol['policy']}\n"
    )
