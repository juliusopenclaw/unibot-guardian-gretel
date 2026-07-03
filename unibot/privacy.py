from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .pilot import build_pilot_protocol
from .public_safety import scan_text
from .source_cards import get_source_card


DATA_PROTECTION_SCHEMA_VERSION = "unibot-data-protection-screening-v1"
DATA_PROTECTION_EVIDENCE_ALIGNMENT_SCHEMA_VERSION = "unibot-data-protection-evidence-alignment-v1"
DATA_PROTECTION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-data-protection-release-review-board-claim-alignment-v1"
)

DATA_PROTECTION_ALIGNMENT_SECTIONS = [
    {
        "section_id": "processing_principles",
        "screening_keys": ["processing_principles"],
        "processing_activity_ids": [],
        "risk_ids": [],
        "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
        "readiness_check_ids": ["data_protection_screening", "compliance_matrix", "source_card_drift_guard"],
        "human_gates": ["datenschutz_review_required_before_real_pilot"],
    },
    {
        "section_id": "pilot_records",
        "screening_keys": ["processing_activities", "pilot_alignment"],
        "processing_activity_ids": ["synthetic_pilot_records"],
        "risk_ids": ["private_data_entry", "external_tool_transfer"],
        "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "unesco-genai-2023"],
        "readiness_check_ids": ["data_protection_screening", "pilot_protocol", "public_safety"],
        "human_gates": [
            "datenschutz_review_required_before_real_pilot",
            "ethics_or_supervisor_review_required_before_real_pilot",
        ],
    },
    {
        "section_id": "access_retention_withdrawal",
        "screening_keys": ["open_decisions_for_datenschutz", "processing_activities"],
        "processing_activity_ids": ["help_ledger", "synthetic_pilot_records"],
        "risk_ids": ["private_data_entry", "public_repository_leak"],
        "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024"],
        "readiness_check_ids": ["data_protection_screening", "pilot_protocol", "review_board_packet"],
        "human_gates": ["datenschutz_review_required_before_real_pilot", "human_review_required"],
    },
    {
        "section_id": "public_repository_boundary",
        "screening_keys": ["risk_register", "review_gates"],
        "processing_activity_ids": ["demo_feedback"],
        "risk_ids": ["public_repository_leak"],
        "source_card_ids": ["gdpr-2016-679", "chrome-limited-use", "uoc-ki-lehre"],
        "readiness_check_ids": ["data_protection_screening", "public_safety", "github_issue_bundle"],
        "human_gates": ["public_safety_required", "human_submission_review_required"],
    },
    {
        "section_id": "exam_and_accommodation_boundary",
        "screening_keys": ["processing_activities", "review_gates", "exam_deployment_status"],
        "processing_activity_ids": ["exam_controlled_mode"],
        "risk_ids": ["score_misuse", "browser_overlay_overclaim"],
        "source_card_ids": ["eu-ai-act-2024", "uoc-ki-lehre", "uoc-nachteilsausgleich"],
        "readiness_check_ids": ["data_protection_screening", "exam_boundary", "release_runbook"],
        "human_gates": [
            "datenschutz_review_required_before_real_pilot",
            "written_university_clearance_required_before_exam_use",
        ],
    },
    {
        "section_id": "pilot_release_review_board_data_boundary",
        "screening_keys": ["pilot_alignment", "processing_activities", "risk_register", "review_gates", "policy"],
        "processing_activity_ids": ["synthetic_pilot_records", "help_ledger", "external_ai_postfilter"],
        "risk_ids": ["private_data_entry", "external_tool_transfer", "score_misuse"],
        "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "dfg-gwp", "unesco-genai-2023"],
        "readiness_check_ids": [
            "data_protection_screening",
            "pilot_protocol",
            "release_runbook",
            "review_board_packet",
            "gretel_bachelor_thesis_package",
            "evaluation_packet",
            "adaptive_task_plan",
            "public_safety",
        ],
        "human_gates": [
            "datenschutz_review_required_before_real_pilot",
            "ethics_or_supervisor_review_required_before_real_pilot",
            "human_submission_review_required",
            "public_safety_required",
            "written_university_clearance_required_before_exam_use",
        ],
    },
]


def build_data_protection_screening() -> dict[str, Any]:
    source_ids = [
        "gdpr-2016-679",
        "dsk-ai-privacy-2024",
        "eu-ai-act-2024",
        "chrome-limited-use",
        "dfg-gwp",
        "unesco-genai-2023",
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
    screening["data_protection_evidence_alignment"] = build_data_protection_evidence_alignment(screening)
    scan = scan_text(json.dumps(screening, ensure_ascii=False), "data-protection-screening")
    screening["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        screening["status"] = "blocked_public_safety"
        screening["public_safety_findings"] = scan["findings"]
    return screening


def build_data_protection_evidence_alignment(screening: dict[str, Any] | None = None) -> dict[str, Any]:
    data_protection = screening or build_data_protection_screening()
    activity_ids = {item["activity_id"] for item in data_protection.get("processing_activities", [])}
    risk_ids = {item["risk_id"] for item in data_protection.get("risk_register", [])}
    alignment_rows = []
    for section in DATA_PROTECTION_ALIGNMENT_SECTIONS:
        missing_screening_keys = sorted(key for key in section["screening_keys"] if key not in data_protection)
        missing_activity_ids = sorted(
            activity_id for activity_id in section["processing_activity_ids"] if activity_id not in activity_ids
        )
        missing_risk_ids = sorted(risk_id for risk_id in section["risk_ids"] if risk_id not in risk_ids)
        missing_source_card_ids = sorted(
            source_id for source_id in section["source_card_ids"] if get_source_card(source_id) is None
        )
        alignment_rows.append(
            {
                "section_id": section["section_id"],
                "screening_keys": list(section["screening_keys"]),
                "processing_activity_ids": list(section["processing_activity_ids"]),
                "risk_ids": list(section["risk_ids"]),
                "source_card_ids": list(section["source_card_ids"]),
                "readiness_check_ids": list(section["readiness_check_ids"]),
                "human_gates": list(section["human_gates"]),
                "missing_screening_keys": missing_screening_keys,
                "missing_processing_activity_ids": missing_activity_ids,
                "missing_risk_ids": missing_risk_ids,
                "missing_source_card_ids": missing_source_card_ids,
            }
        )
    alignment = {
        "schema_version": DATA_PROTECTION_EVIDENCE_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "section_count": len(alignment_rows),
        "sections": alignment_rows,
        "missing_screening_keys": sorted(
            {key for row in alignment_rows for key in row["missing_screening_keys"]}
        ),
        "missing_processing_activity_ids": sorted(
            {activity_id for row in alignment_rows for activity_id in row["missing_processing_activity_ids"]}
        ),
        "missing_risk_ids": sorted({risk_id for row in alignment_rows for risk_id in row["missing_risk_ids"]}),
        "missing_source_card_ids": sorted(
            {source_id for row in alignment_rows for source_id in row["missing_source_card_ids"]}
        ),
        "required_readiness_check_ids": sorted(
            {check_id for row in alignment_rows for check_id in row["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for row in alignment_rows for gate in row["human_gates"]}),
        "pilot_contract": {
            "expected_check_id": "pilot_protocol",
            "expected_alignment_status": "ready",
        },
        "source_card_drift_contract": {
            "expected_check_id": "source_card_drift_guard",
            "required_status": "pass",
        },
        "review_board_contract": {
            "expected_check_id": "review_board_packet",
            "required_status": "draft_for_institutional_review",
        },
        "release_boundary_contract": {
            "exam_deployment_status": "not_cleared",
            "real_pilot_status": "blocked_until_datenschutz_ethics_and_authority_review",
        },
        "data_protection_release_review_board_claim_contract": {
            "expected_schema_version": DATA_PROTECTION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
            "required_pilot_release_review_board_schema_version": (
                "unibot-pilot-release-review-board-claim-alignment-v1"
            ),
            "required_review_board_thesis_evaluation_schema_version": (
                "unibot-review-board-thesis-evaluation-claim-alignment-v1"
            ),
            "required_readiness_check_ids": [
                "pilot_protocol",
                "release_runbook",
                "review_board_packet",
                "gretel_bachelor_thesis_package",
                "evaluation_packet",
                "adaptive_task_plan",
                "public_safety",
            ],
            "required_human_gates": [
                "datenschutz_review_required_before_real_pilot",
                "ethics_or_supervisor_review_required_before_real_pilot",
                "human_submission_review_required",
                "public_safety_required",
                "written_university_clearance_required_before_exam_use",
            ],
            "use": "Data-protection language must keep pilot learner-agency evidence synthetic, minimised, review-gated, and not Datenschutz, participant recruitment, cloud-storage, or exam clearance.",
        },
        "policy": (
            "Data-protection evidence alignment is a review aid only; it is not legal advice, "
            "Datenschutz approval, participant recruitment approval, cloud-storage approval, or exam clearance."
        ),
    }
    if (
        alignment["missing_screening_keys"]
        or alignment["missing_processing_activity_ids"]
        or alignment["missing_risk_ids"]
        or alignment["missing_source_card_ids"]
    ):
        alignment["status"] = "blocked"
    required_check_ids = set(
        alignment["data_protection_release_review_board_claim_contract"]["required_readiness_check_ids"]
    )
    present_check_ids = set(alignment["required_readiness_check_ids"])
    alignment["missing_release_review_board_claim_check_ids"] = sorted(required_check_ids - present_check_ids)
    required_human_gates = set(
        alignment["data_protection_release_review_board_claim_contract"]["required_human_gates"]
    )
    present_human_gates = set(alignment["required_human_gates"])
    alignment["missing_release_review_board_claim_human_gates"] = sorted(required_human_gates - present_human_gates)
    if (
        alignment["missing_release_review_board_claim_check_ids"]
        or alignment["missing_release_review_board_claim_human_gates"]
    ):
        alignment["status"] = "blocked"
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "data-protection-evidence-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked_public_safety"
    return alignment


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
    alignment = screening["data_protection_evidence_alignment"]
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
        "## Evidence Alignment\n\n"
        f"- Alignment: {alignment['status']}\n"
        f"- Sections: {alignment['section_count']}\n"
        f"- Release review-board claim alignment: {alignment['data_protection_release_review_board_claim_contract']['expected_schema_version']}\n"
        f"- Human gates: {', '.join(alignment['required_human_gates'])}\n\n"
        "## Source Cards\n\n"
        f"{source_lines}\n\n"
        f"Policy: {screening['policy']}\n"
    )
