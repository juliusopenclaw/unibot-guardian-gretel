from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .evaluation import build_evaluation_packet
from .materials import sha256_text
from .public_safety import scan_text
from .redteam import run_redteam_smoke
from .source_cards import get_source_card


PILOT_PROTOCOL_SCHEMA_VERSION = "unibot-pilot-protocol-v1"
PILOT_EVIDENCE_ALIGNMENT_SCHEMA_VERSION = "unibot-pilot-evidence-alignment-v1"
PILOT_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-pilot-release-review-board-claim-alignment-v1"
)
CONTROLLED_PILOT_LAUNCH_GATE_SCHEMA_VERSION = "unibot-controlled-pilot-launch-gate-v1"

CONTROLLED_PILOT_REQUIRED_CLEARANCE_ITEMS = [
    {
        "item_id": "voluntary_participation_confirmed",
        "label": "voluntary participation and withdrawal remain explicit",
        "human_gate": "ethics_or_supervisor_review_required_before_real_pilot",
    },
    {
        "item_id": "transparent_information_sheet_confirmed",
        "label": "participant information sheet is approved and plain-language",
        "human_gate": "human_submission_review_required",
    },
    {
        "item_id": "no_grade_or_exam_effect_confirmed",
        "label": "pilot has no grade, exam, support-decision, or disciplinary effect",
        "human_gate": "written_university_clearance_required_before_exam_use",
    },
    {
        "item_id": "synthetic_tasks_only_confirmed",
        "label": "pilot uses frozen synthetic tasks and no real graded work",
        "human_gate": "human_submission_review_required",
    },
    {
        "item_id": "datenschutz_review_documented",
        "label": "Datenschutz has reviewed storage, retention, access, and minimisation",
        "human_gate": "datenschutz_review_required_before_real_pilot",
    },
    {
        "item_id": "ethics_or_supervisor_review_documented",
        "label": "ethics or thesis supervision review decision is documented",
        "human_gate": "ethics_or_supervisor_review_required_before_real_pilot",
    },
    {
        "item_id": "withdrawal_redaction_process_tested",
        "label": "withdrawal and redaction process has been tested",
        "human_gate": "datenschutz_review_required_before_real_pilot",
    },
    {
        "item_id": "authority_boundary_review_documented",
        "label": "responsible university authority boundary review is documented",
        "human_gate": "written_university_clearance_required_before_exam_use",
    },
    {
        "item_id": "public_safety_review_passed",
        "label": "public-safety review passed before any participant-facing material",
        "human_gate": "public_safety_required",
    },
]

HIGH_STAKES_PILOT_CLAIM_TERMS = [
    "exam clearance",
    "exam deployment",
    "official grading",
    "grading",
    "grade effect",
    "proctoring",
    "ki-detection",
    "ai-detection",
    "misconduct detection",
    "disciplinary",
]

PILOT_ALIGNMENT_SECTIONS = [
    {
        "section_id": "consent_boundary",
        "protocol_keys": ["consent_items", "participant_information", "participant_scope"],
        "source_card_ids": ["dfg-gwp", "unesco-genai-2023", "uoc-ki-lehre"],
        "readiness_check_ids": ["pilot_protocol", "evaluation_packet", "review_board_packet"],
        "human_gates": ["ethics_or_supervisor_review_required_before_real_pilot", "human_review_required"],
    },
    {
        "section_id": "ethics_review_trigger",
        "protocol_keys": ["ethics_review_triggers", "stop_rules"],
        "source_card_ids": ["dfg-gwp", "eu-ai-act-2024", "uoc-ki-lehre"],
        "readiness_check_ids": ["pilot_protocol", "compliance_matrix", "review_board_packet"],
        "human_gates": ["ethics_or_supervisor_review_required_before_real_pilot", "human_submission_review_required"],
    },
    {
        "section_id": "data_management",
        "protocol_keys": ["data_management_plan", "participant_scope"],
        "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "chrome-limited-use"],
        "readiness_check_ids": ["pilot_protocol", "data_protection_screening", "public_safety"],
        "human_gates": ["datenschutz_review_required_before_real_pilot", "public_safety_required"],
    },
    {
        "section_id": "session_flow_and_measures",
        "protocol_keys": ["session_flow", "readiness_gates"],
        "source_card_ids": ["vanlehn-2011", "kulik-fletcher-2016", "cs50-ai-2024"],
        "readiness_check_ids": ["pilot_protocol", "evaluation_packet", "redteam"],
        "human_gates": ["human_review_required", "human_submission_review_required"],
    },
    {
        "section_id": "real_pilot_release_boundary",
        "protocol_keys": ["readiness_gates", "exam_deployment_status", "policy"],
        "source_card_ids": ["uoc-ki-lehre", "uoc-hilfsmittel", "eu-ai-act-2024"],
        "readiness_check_ids": ["pilot_protocol", "compliance_matrix", "release_runbook"],
        "human_gates": [
            "written_university_clearance_required_before_exam_use",
            "ethics_or_supervisor_review_required_before_real_pilot",
            "datenschutz_review_required_before_real_pilot",
        ],
    },
    {
        "section_id": "review_board_thesis_evaluation_pilot_boundary",
        "protocol_keys": ["purpose", "participant_information", "readiness_gates", "policy"],
        "source_card_ids": ["dfg-gwp", "unesco-genai-2023", "vanlehn-2011"],
        "readiness_check_ids": [
            "pilot_protocol",
            "release_runbook",
            "review_board_packet",
            "gretel_bachelor_thesis_package",
            "evaluation_packet",
            "adaptive_task_plan",
            "public_safety",
        ],
        "human_gates": [
            "ethics_or_supervisor_review_required_before_real_pilot",
            "human_submission_review_required",
            "public_safety_required",
            "written_university_clearance_required_before_exam_use",
        ],
    },
]


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
    protocol["pilot_evidence_alignment"] = build_pilot_evidence_alignment(protocol)
    protocol["controlled_pilot_launch_gate"] = build_controlled_pilot_launch_gate(protocol)
    scan = scan_text(json.dumps(protocol, ensure_ascii=False), "pilot-protocol")
    protocol["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        protocol["status"] = "blocked_public_safety"
        protocol["public_safety_findings"] = scan["findings"]
    return protocol


def build_controlled_pilot_launch_gate(
    protocol: dict[str, Any] | None = None,
    clearance_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pilot = protocol or build_pilot_protocol()
    receipt = clearance_receipt if isinstance(clearance_receipt, dict) else {}
    receipt_payload = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    receipt_scan = scan_text(receipt_payload, "controlled-pilot-clearance-receipt")
    receipt_text = receipt_payload.lower()
    high_stakes_terms_found = sorted(term for term in HIGH_STAKES_PILOT_CLAIM_TERMS if term in receipt_text)
    clearance_items = []
    for item in CONTROLLED_PILOT_REQUIRED_CLEARANCE_ITEMS:
        confirmed = receipt.get(item["item_id"]) is True
        clearance_items.append(
            {
                "item_id": item["item_id"],
                "label": item["label"],
                "human_gate": item["human_gate"],
                "status": "confirmed" if confirmed else "missing",
            }
        )
    missing_clearance_item_ids = sorted(
        item["item_id"] for item in clearance_items if item["status"] != "confirmed"
    )
    required_human_gates = sorted({item["human_gate"] for item in CONTROLLED_PILOT_REQUIRED_CLEARANCE_ITEMS})
    protection_contracts = {
        "protocol_draft_ready": pilot.get("status") == "draft_not_ethics_or_authority_cleared",
        "protocol_public_safe": pilot.get("public_safety_status", "pass") == "pass",
        "exam_deployment_not_cleared": pilot.get("exam_deployment_status") == "not_cleared",
        "real_pilot_not_started": True,
        "ai_does_not_authorize_pilot": True,
        "high_stakes_modes_not_claimed": high_stakes_terms_found == [],
        "receipt_public_safe": receipt_scan["status"] == "pass",
        "raw_receipt_not_returned": True,
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in protection_contracts.items() if not passed)
    if receipt_scan["status"] != "pass":
        status = "blocked_receipt_public_safety"
    elif high_stakes_terms_found:
        status = "blocked_claim_boundary"
    elif failed_contract_ids:
        status = "blocked_protocol_boundary"
    elif missing_clearance_item_ids:
        status = "blocked_pending_human_clearance"
    else:
        status = "ready_for_manual_pilot_go_review_not_started"
    gate_payload = {
        "schema_version": CONTROLLED_PILOT_LAUNCH_GATE_SCHEMA_VERSION,
        "status": status,
        "clearance_items": clearance_items,
        "missing_clearance_item_ids": missing_clearance_item_ids,
        "required_human_gates": required_human_gates,
        "failed_contract_ids": failed_contract_ids,
        "high_stakes_terms_found": high_stakes_terms_found,
        "receipt_hash_present": bool(receipt),
        "receipt_hash": sha256_text(receipt_payload) if receipt else "",
        "protocol_status": pilot.get("status", ""),
        "exam_deployment_status": pilot.get("exam_deployment_status", ""),
    }
    gate_scan = scan_text(
        json.dumps(gate_payload, ensure_ascii=False, sort_keys=True),
        "controlled-pilot-launch-gate",
    )
    if gate_scan["status"] != "pass" and status != "blocked_receipt_public_safety":
        status = "blocked_gate_public_safety"
        gate_payload["status"] = status
    return {
        "schema_version": CONTROLLED_PILOT_LAUNCH_GATE_SCHEMA_VERSION,
        "status": status,
        "status_label_de": "Kontrollierter Pilot bleibt ohne menschliche Freigaben blockiert",
        "pilot_mode": "voluntary_transparent_formative_synthetic_only",
        "clearance_items": clearance_items,
        "missing_clearance_item_ids": missing_clearance_item_ids,
        "missing_clearance_count": len(missing_clearance_item_ids),
        "required_human_gates": required_human_gates,
        "protection_contracts": protection_contracts,
        "failed_contract_ids": failed_contract_ids,
        "high_stakes_terms_found": high_stakes_terms_found,
        "receipt_hash_present": bool(receipt),
        "receipt_hash": gate_payload["receipt_hash"],
        "clearance_receipt_public_safety_status": receipt_scan["status"],
        "public_safety_status": gate_scan["status"],
        "real_pilot_started": False,
        "real_pilot_allowed_by_ai": False,
        "raw_receipt_returned": False,
        "ready_for": ["manual review of a clearance receipt"]
        if status == "ready_for_manual_pilot_go_review_not_started"
        else [],
        "not_ready_for": ["real pilot start by AI", "exam deployment", "grading", "proctoring", "KI-detection"],
        "policy": (
            "The controlled pilot launch gate classifies clearance receipts without returning raw receipt text. "
            "It never starts a real pilot and never grants AI authority for pilot launch, grading, proctoring, "
            "KI detection, or exam deployment."
        ),
    }


def build_pilot_evidence_alignment(protocol: dict[str, Any] | None = None) -> dict[str, Any]:
    pilot = protocol or build_pilot_protocol()
    alignment_rows = []
    for section in PILOT_ALIGNMENT_SECTIONS:
        missing_protocol_keys = sorted(key for key in section["protocol_keys"] if key not in pilot)
        missing_source_card_ids = sorted(
            source_id for source_id in section["source_card_ids"] if get_source_card(source_id) is None
        )
        alignment_rows.append(
            {
                "section_id": section["section_id"],
                "protocol_keys": list(section["protocol_keys"]),
                "missing_protocol_keys": missing_protocol_keys,
                "source_card_ids": list(section["source_card_ids"]),
                "missing_source_card_ids": missing_source_card_ids,
                "readiness_check_ids": list(section["readiness_check_ids"]),
                "human_gates": list(section["human_gates"]),
            }
        )
    alignment = {
        "schema_version": PILOT_EVIDENCE_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "section_count": len(alignment_rows),
        "sections": alignment_rows,
        "missing_protocol_keys": sorted(
            {key for row in alignment_rows for key in row["missing_protocol_keys"]}
        ),
        "missing_source_card_ids": sorted(
            {source_id for row in alignment_rows for source_id in row["missing_source_card_ids"]}
        ),
        "required_readiness_check_ids": sorted(
            {check_id for row in alignment_rows for check_id in row["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for row in alignment_rows for gate in row["human_gates"]}),
        "source_card_drift_contract": {
            "expected_check_id": "source_card_drift_guard",
            "required_status": "pass",
        },
        "data_protection_contract": {
            "expected_check_id": "data_protection_screening",
            "required_review_gate": "datenschutz_review_required_before_real_pilot",
        },
        "review_board_contract": {
            "expected_check_id": "review_board_packet",
            "required_status": "draft_for_institutional_review",
        },
        "release_boundary_contract": {
            "expected_check_id": "release_runbook",
            "real_pilot_release_status": "blocked_until_ethics_datenschutz_and_authority_review",
        },
        "pilot_release_review_board_claim_contract": {
            "expected_schema_version": PILOT_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
            "required_release_runbook_schema_version": "unibot-release-runbook-evidence-alignment-v1",
            "required_review_board_thesis_evaluation_schema_version": (
                "unibot-review-board-thesis-evaluation-claim-alignment-v1"
            ),
            "required_readiness_check_ids": [
                "release_runbook",
                "review_board_packet",
                "gretel_bachelor_thesis_package",
                "evaluation_packet",
                "adaptive_task_plan",
                "data_protection_screening",
                "public_safety",
            ],
            "required_human_gates": [
                "ethics_or_supervisor_review_required_before_real_pilot",
                "datenschutz_review_required_before_real_pilot",
                "human_submission_review_required",
                "public_safety_required",
                "written_university_clearance_required_before_exam_use",
            ],
            "use": "Pilot language must keep learner-agency evidence synthetic, formative, human-gated, and not participant recruitment, ethics, Datenschutz, or exam clearance.",
        },
        "policy": (
            "Pilot evidence alignment is a review aid only; it is not ethics clearance, "
            "data-protection approval, participant recruitment approval, or exam clearance."
        ),
    }
    if alignment["missing_protocol_keys"] or alignment["missing_source_card_ids"]:
        alignment["status"] = "blocked"
    required_check_ids = set(alignment["pilot_release_review_board_claim_contract"]["required_readiness_check_ids"])
    present_check_ids = set(alignment["required_readiness_check_ids"])
    alignment["missing_release_review_board_claim_check_ids"] = sorted(required_check_ids - present_check_ids)
    required_human_gates = set(alignment["pilot_release_review_board_claim_contract"]["required_human_gates"])
    present_human_gates = set(alignment["required_human_gates"])
    alignment["missing_release_review_board_claim_human_gates"] = sorted(required_human_gates - present_human_gates)
    if (
        alignment["missing_release_review_board_claim_check_ids"]
        or alignment["missing_release_review_board_claim_human_gates"]
    ):
        alignment["status"] = "blocked"
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "pilot-evidence-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked_public_safety"
    return alignment


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
    alignment = protocol["pilot_evidence_alignment"]
    launch_gate = protocol["controlled_pilot_launch_gate"]
    launch_gate_items = "\n".join(
        f"- `{item['item_id']}`: {item['status']} ({item['human_gate']})" for item in launch_gate["clearance_items"]
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
        "## Evidence Alignment\n\n"
        f"- Alignment: {alignment['status']}\n"
        f"- Sections: {alignment['section_count']}\n"
        f"- Release review-board claim alignment: {alignment['pilot_release_review_board_claim_contract']['expected_schema_version']}\n"
        f"- Human gates: {', '.join(alignment['required_human_gates'])}\n\n"
        "## Controlled Pilot Launch Gate\n\n"
        f"- Status: {launch_gate['status']}\n"
        f"- Public safety: {launch_gate['public_safety_status']}\n"
        f"- Receipt public safety: {launch_gate['clearance_receipt_public_safety_status']}\n"
        f"- Real pilot started: {launch_gate['real_pilot_started']}\n"
        f"- Real pilot allowed by AI: {launch_gate['real_pilot_allowed_by_ai']}\n"
        f"- Missing clearance count: {launch_gate['missing_clearance_count']}\n"
        f"{launch_gate_items}\n\n"
        "## Source Cards\n\n"
        f"{source_lines}\n\n"
        f"Policy: {protocol['policy']}\n"
    )
