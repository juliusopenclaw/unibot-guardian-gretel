from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .handoff import build_authority_handoff_packet
from .pilot import build_pilot_protocol
from .privacy import build_data_protection_screening
from .public_safety import scan_text
from .source_cards import get_source_card
from .python_exam_local_cycle_chain_snapshot import build_python_exam_local_cycle_chain_snapshot


REVIEW_BOARD_SCHEMA_VERSION = "unibot-review-board-packet-v1"


def _build_reviewer_packet(
    reviewer: str,
    mandate: str,
    decisions_needed: list[str],
    required_evidence: list[str],
    required_source_cards: list[str],
    must_not_claim: list[str],
    clearance_text_must_include: list[str],
) -> dict[str, Any]:
    source_cards = []
    for source_id in required_source_cards:
        card = get_source_card(source_id)
        if card:
            source_cards.append(card)
    return {
        "reviewer": reviewer,
        "mandate": mandate,
        "decisions_needed": decisions_needed,
        "required_evidence": required_evidence,
        "required_source_cards": [
            {
                "source_id": card["source_id"],
                "title": card["title"],
                "authority_type": card["authority_type"],
                "product_rule": card["product_rule"],
            }
            for card in source_cards
        ],
        "must_not_claim": must_not_claim,
        "clearance_text_must_include": clearance_text_must_include,
        "current_status": "evidence_ready_pending_clearance",
    }


def build_review_board_packet(
    *,
    python_exam_local_cycle_readiness_review: dict[str, Any] | None = None,
    python_exam_local_cycle_readiness_handoff: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
    selected_skill_tag: str = "",
) -> dict[str, Any]:
    handoff = build_authority_handoff_packet()
    compliance = build_compliance_matrix()
    pilot = build_pilot_protocol()
    privacy = build_data_protection_screening()
    local_cycle_chain_snapshot = build_python_exam_local_cycle_chain_snapshot(
        python_exam_local_cycle_readiness_review=python_exam_local_cycle_readiness_review,
        python_exam_local_cycle_readiness_handoff=python_exam_local_cycle_readiness_handoff,
        python_exam_local_cycle_operator_workspace_card=python_exam_local_cycle_operator_workspace_card,
        selected_skill_tag=selected_skill_tag,
        public_safe=True,
    )

    reviewers = [
        _build_reviewer_packet(
            reviewer="Pruefungsamt",
            mandate="Validate whether and how external KI support can be used in regulated exam contexts.",
            decisions_needed=[
                "written approval scope for the module and exam format",
                "whether exam_controlled remains blocked in the local mode",
                "allowed AI workflow by task type and assessment phase",
                "required evidence package for pilot or deployment",
            ],
            required_evidence=[
                "authority handoff packet",
                "compliance matrix",
                "pilot readiness gates",
                "privacy decisions",
            ],
            required_source_cards=["hg-nrw-2025", "hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq"],
            must_not_claim=[
                "no hidden or silent AI grading",
                "no automatic assessment",
                "no AI as proctoring substitute",
            ],
            clearance_text_must_include=[
                "nicht offiziell freigegeben",
                "nur beantragt",
            ],
        ),
        _build_reviewer_packet(
            reviewer="Inklusionsbuero / Nachteilsausgleich",
            mandate="Check that accessibility support is documented, neutral for scoring, and not confused with official decisions.",
            decisions_needed=[
                "whether the current accessibility path is sufficient for this use case",
                "whether additional support documents are needed",
                "how and where accommodation docs are stored in an institutionally compliant process",
            ],
            required_evidence=[
                "pilot protocol",
                "pilot consent boundary",
                "help-level neutrality checks",
            ],
            required_source_cards=["hg-nrw-62b", "uoc-nachteilsausgleich", "eu-ai-act-2024"],
            must_not_claim=[
                "no individual accommodation decision by UniBot",
                "no grade effect for accessibility options",
            ],
            clearance_text_must_include=[
                "Nutzerleistung bleibt erforderlich",
                "keine Entscheidung durch KI",
            ],
        ),
        _build_reviewer_packet(
            reviewer="Datenschutz",
            mandate="Validate lawful legal basis, minimisation, retention, local storage, and deletion behavior.",
            decisions_needed=[
                "storage purpose and lawful basis for any real pilot records",
                "retention schedule and withdrawal workflow",
                "access model and role boundaries",
                "cloud usage and location model",
            ],
            required_evidence=[
                "data-protection screening",
                "pilot data-management plan",
                "public-safety scan log",
                "red-team evidence for private markers",
            ],
            required_source_cards=["gdpr-2016-679", "dsk-ai-privacy-2024", "eu-ai-act-2024"],
            must_not_claim=[
                "collect raw external answers in public artifacts",
                "store private course material paths",
                "store health or accommodation details without governance",
            ],
            clearance_text_must_include=[
                "schriftlich mit Datenschutz abgesprochen",
                "Datenentfernung bei Rueckzug",
            ],
        ),
        _build_reviewer_packet(
            reviewer="IT / SZI",
            mandate="Review technical boundary of the browser mantling model and define a future controlled AI channel.",
            decisions_needed=[
                "allowed extension deployment model in the institution",
                "whether a managed notebook or gateway is required",
                "allowed local storage paths and audit logging policy",
                "incident handling and fail-open/closed behavior",
            ],
            required_evidence=[
                "browser mantle implementation",
                "notebook template audit",
                "threat model source",
            ],
            required_source_cards=["chrome-content-scripts", "chrome-webrequest-mv3", "jupyter-ai", "google-colab-gemini"],
            must_not_claim=[
                "hard exam security from MV3 interception",
                "silent network level enforcement without explicit architecture",
            ],
            clearance_text_must_include=[
                "Overlay ist Praxisfilter",
                "Exam-Kanal nur kontrolliert",
            ],
        ),
        _build_reviewer_packet(
            reviewer="Lehreinheit / Modulverantwortliche",
            mandate="Check pedagogical fit, task mapping, and alignment with official course learning outcomes.",
            decisions_needed=[
                "whether synthetic demo tasks still match course outcomes",
                "whether source card constraints fit current teaching materials",
                "whether reporting language is teachable and understandable",
            ],
            required_evidence=[
                "course-material manifest and permissions",
                "adaptive task planning",
                "pilot session flow and measures",
            ],
            required_source_cards=["cs50-ai-2024", "vanlehn-2011", "kulik-fletcher-2016", "uoc-ki-lehre"],
            must_not_claim=[
                "replace explanation quality with answer snippets",
                "remove requirement of student's own reasoning step",
            ],
            clearance_text_must_include=[
                "Sokratischer Support als Lernfilter",
                "keine Vollloesung durch KI",
            ],
        ),
        _build_reviewer_packet(
            reviewer="Thesis supervision",
            mandate="Validate master-thesis quality, reproducibility, method transparency, and claim boundaries.",
            decisions_needed=[
                "hypotheses and measures for final study design",
                "limitations wording for official thesis claim",
                "data-quality and replication plan before real participant recruitment",
            ],
            required_evidence=[
                "publication package",
                "evaluation packet",
                "codebook and source cards",
            ],
            required_source_cards=[
                "dfg-gwp",
                "unesco-genai-2023",
                "oecd-digital-education-2026",
            ],
            must_not_claim=[
                "causal claims from synthetic-only pilot evidence",
                "overclaim beyond evidence",
            ],
            clearance_text_must_include=[
                "pilot-only",
                "synthetic tasks only",
                "design-boundaries documented",
            ],
        ),
    ]

    review_board = {
        "schema_version": REVIEW_BOARD_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "draft_for_institutional_review",
        "status_label_de": "Entwurf fuer interne Review der zustaendigen Stellen",
        "exam_deployment_status": "not_cleared",
        "public_safety_status": "pass",
        "reviewer_packets": reviewers,
        "evidence_summary": {
            "authority_handoff_status": handoff["status"],
            "compliance_matrix_status": compliance["status"],
            "pilot_protocol_status": pilot["status"],
            "privacy_status": privacy["status"],
            "compliance_source_cards": compliance["source_card_count"],
            "redteam_status": handoff["evidence"]["redteam"]["status"],
            "local_cycle_chain_snapshot_status": local_cycle_chain_snapshot.get("status", "missing"),
            "local_cycle_chain_snapshot_hash": local_cycle_chain_snapshot.get("chain_snapshot_summary", {}).get("snapshot_hash", "")
            if isinstance(local_cycle_chain_snapshot.get("chain_snapshot_summary"), dict)
            else "",
        },
        "local_cycle_chain_snapshot": local_cycle_chain_snapshot,
        "cross_cutting_red_lines": [
            "No proctoring and no hidden monitoring claims",
            "No automatic grading",
            "No disciplinary KI-detection output",
            "No official exam use without written clearance",
            "No private course files in public repository",
            "No personal health or accommodation data in public artifacts",
        ],
        "clearance_requirements": {
            "practice_mode": {
                "status": "ready",
                "required_clearance": [],
                "notes": "Local practice and selftest flow is available as MVP and public-safe.",
            },
            "pilot_mode": {
                "status": "pending_clearance",
                "required_clearance": [
                    "written ethics/data protection check",
                    "formal consent and withdrawal process",
                    "authority acknowledgment",
                ],
            },
            "exam_controlled": {
                "status": "blocked",
                "required_clearance": [
                    "written Pruefungsamt approval",
                    "controlled channel architecture",
                    "documented data governance and incident response",
                ],
                "blocked_reason": "not_cleared",
            },
        },
        "open_decision_register": [
            {
                "reviewer": reviewer["reviewer"],
                "question": "Welche Bedingung muss dokumentiert werden, bevor dieser Block freigegeben werden kann?",
                "current_state": reviewer["current_status"],
                "priority": "high",
            }
            for reviewer in reviewers
        ],
        "public_language": {
            "default": "beantragt / nicht offiziell freigegeben",
            "no_approved_claims": ["approved", "officially approved", "freigegeben als exam use"],
            "approved_in_public": "never",
        },
        "ready_for": ["public draft review", "local practice demo"],
        "not_ready_for": ["exam deployment", "official grading", "automatic support claims", "exam_controlled"],
    }
    scan = scan_text(json.dumps(review_board, ensure_ascii=False), "unibot-review-board-packet")
    review_board["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        review_board["status"] = "blocked_public_safety"
        review_board["public_safety_findings"] = scan["findings"]
    return review_board


def build_review_board_packet_markdown() -> str:
    packet = build_review_board_packet()
    reviewer_lines = "\n".join(
        f"- **{item['reviewer']}**: {item['mandate']}"
        for item in packet["reviewer_packets"]
    )
    decision_lines = "\n".join(
        f"- {item['reviewer']}: {item['question']} ({item['priority']})"
        for item in packet["open_decision_register"]
    )
    redline_lines = "\n".join(f"- {line}" for line in packet["cross_cutting_red_lines"])
    clearance_lines = "\n".join(
        f"- {name}: {details['status']}"
        + (
            f" ({', '.join(details.get('required_clearance', []))})"
            if details.get("required_clearance")
            else ""
        )
        for name, details in packet["clearance_requirements"].items()
    )
    evidence = packet["evidence_summary"]
    chain = packet.get("local_cycle_chain_snapshot", {})
    chain_summary = chain.get("chain_snapshot_summary", {}) if isinstance(chain.get("chain_snapshot_summary"), dict) else {}
    chain_step_lines = "\n".join(
        f"- {item.get('step_id', '')}: {item.get('status', 'unknown')} / {item.get('step_hash', '')}"
        for item in (chain.get("chain_steps", []) or [])
        if isinstance(item, dict)
    )
    return (
        "# UniBot Review Board Packet\n\n"
        f"Status: {packet['status_label_de']}\n\n"
        f"Exam deployment: {packet['exam_deployment_status']}\n\n"
        "## Reviewer Blocks\n\n"
        f"{reviewer_lines}\n\n"
        "## Cross-cutting Red Lines\n\n"
        f"{redline_lines}\n\n"
        "## Clearance Matrix\n\n"
        f"{clearance_lines}\n\n"
        "## Open Decisions\n\n"
        f"{decision_lines}\n\n"
        "## Evidence Summary\n\n"
        f"- Authority handoff: {evidence['authority_handoff_status']}\n"
        f"- Compliance matrix: {evidence['compliance_matrix_status']}\n"
        f"- Pilot protocol: {evidence['pilot_protocol_status']}\n"
        f"- Privacy screening: {evidence['privacy_status']}\n"
        f"- Red-team: {evidence['redteam_status']}\n\n"
        "## Local Cycle Chain\n\n"
        f"- Status: {chain.get('status', 'missing')}\n"
        f"- Snapshot hash: {chain_summary.get('snapshot_hash', '')}\n"
        f"- Review recommendation: {chain_summary.get('review_recommendation', 'keep_blocked')}\n"
        f"- Handoff status: {chain_summary.get('handoff_status', 'missing')}\n"
        f"- Workspace card status: {chain_summary.get('workspace_card_status', 'missing')}\n"
        f"{chain_step_lines}\n\n"
        f"Public language rule: {packet['public_language']['default']}\n"
        f"Policy: {', '.join(packet['ready_for'])}. Not ready for: {', '.join(packet['not_ready_for'])}.\n"
    )
