from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .bachelor_thesis import build_bachelor_thesis_evidence_index, build_bachelor_thesis_evaluation_claim_alignment
from .handoff import build_authority_handoff_packet
from .pilot import build_pilot_protocol
from .privacy import build_data_protection_screening
from .public_safety import scan_text
from .source_cards import get_source_card
from .python_exam_local_cycle_chain_snapshot import build_python_exam_local_cycle_chain_snapshot


REVIEW_BOARD_SCHEMA_VERSION = "unibot-review-board-packet-v1"
REVIEW_BOARD_THESIS_EVALUATION_ALIGNMENT_SCHEMA_VERSION = "unibot-review-board-thesis-evaluation-claim-alignment-v1"


def build_review_board_evidence_alignment(reviewers: list[dict[str, Any]]) -> dict[str, Any]:
    thesis_evidence = build_bachelor_thesis_evidence_index()
    claim_by_id = {item["claim_id"]: item for item in thesis_evidence["evidence_items"]}
    reviewer_claim_map = {
        "Pruefungsamt": ["exam_boundary_not_clearance", "source_bound_public_science"],
        "Inklusionsbuero / Nachteilsausgleich": ["exam_boundary_not_clearance", "public_safety_and_privacy"],
        "Datenschutz": ["public_safety_and_privacy", "source_bound_public_science"],
        "IT / SZI": ["glm_52_basis", "public_safety_and_privacy"],
        "Lehreinheit / Modulverantwortliche": [
            "reproducible_evaluation_package",
            "evaluation_learner_agency_boundary",
            "source_bound_public_science",
        ],
        "Thesis supervision": [
            "gretel_authorship_label",
            "glm_52_basis",
            "reproducible_evaluation_package",
            "evaluation_learner_agency_boundary",
        ],
    }
    reviewer_rows = []
    for reviewer in reviewers:
        claim_ids = reviewer_claim_map.get(reviewer["reviewer"], [])
        mapped_claims = [claim_by_id[claim_id] for claim_id in claim_ids if claim_id in claim_by_id]
        reviewer_rows.append(
            {
                "reviewer": reviewer["reviewer"],
                "claim_ids": claim_ids,
                "readiness_check_ids": sorted(
                    {check_id for claim in mapped_claims for check_id in claim["readiness_check_ids"]}
                ),
                "source_card_ids": sorted({source_id for claim in mapped_claims for source_id in claim["source_card_ids"]}),
                "human_gates": sorted({claim["human_gate"] for claim in mapped_claims}),
                "missing_claim_ids": sorted(set(claim_ids) - set(claim_by_id)),
            }
        )

    required_snapshot_gate_ids = sorted(
        {
            "public_safety",
            "readiness_runtime_guard",
            "source_card_drift_guard",
            "evaluation_packet",
            "redteam",
            "publication_package",
            "review_board_packet",
            "gretel_glm_evolve_lane",
            "gretel_bachelor_thesis_package",
            "gretel_autonomous_research_loop",
            "exam_boundary",
        }
    )
    alignment = {
        "schema_version": "unibot-review-board-evidence-alignment-v1",
        "status": "ready",
        "thesis_evidence_index_status": thesis_evidence["status"],
        "thesis_claim_count": thesis_evidence["claim_count"],
        "readiness_snapshot_contract": {
            "expected_schema_version": "unibot-readiness-evidence-snapshot-v1",
            "required_status": "ready",
            "required_gate_ids": required_snapshot_gate_ids,
            "use": "Compare recurring Gretel readiness snapshots before human review, not as approval.",
        },
        "reviewer_alignment": reviewer_rows,
        "unmapped_reviewer_count": len([row for row in reviewer_rows if not row["claim_ids"]]),
        "missing_claim_ids": sorted({claim_id for row in reviewer_rows for claim_id in row["missing_claim_ids"]}),
        "required_human_gates": thesis_evidence["required_human_gates"],
        "human_gate_reminder": "Review-board alignment prepares human audit; it is not exam clearance, legal approval, provider approval, or thesis submission approval.",
    }
    if (
        thesis_evidence["status"] != "ready"
        or alignment["unmapped_reviewer_count"] != 0
        or alignment["missing_claim_ids"]
    ):
        alignment["status"] = "blocked"
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "unibot-review-board-evidence-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
    return alignment


def build_review_board_thesis_evaluation_claim_alignment(review_board: dict[str, Any] | None = None) -> dict[str, Any]:
    if review_board is None:
        review_board = build_review_board_packet()
    thesis_evidence = build_bachelor_thesis_evidence_index()
    thesis_evaluation_alignment = build_bachelor_thesis_evaluation_claim_alignment(thesis_evidence)
    reviewer_alignment = review_board.get("evidence_alignment", {}).get("reviewer_alignment", [])
    reviewer_by_name = {row.get("reviewer", ""): row for row in reviewer_alignment}
    required_reviewers = ["Lehreinheit / Modulverantwortliche", "Thesis supervision"]
    reviewer_rows = []
    for reviewer in required_reviewers:
        row = reviewer_by_name.get(reviewer, {})
        reviewer_rows.append(
            {
                "reviewer": reviewer,
                "has_evaluation_claim": "evaluation_learner_agency_boundary" in row.get("claim_ids", []),
                "claim_ids": row.get("claim_ids", []),
                "readiness_check_ids": row.get("readiness_check_ids", []),
                "source_card_ids": row.get("source_card_ids", []),
                "human_gates": row.get("human_gates", []),
            }
        )
    sections = [
        {
            "section_id": "teaching_review_trace",
            "reviewers": ["Lehreinheit / Modulverantwortliche"],
            "claim_ids": ["evaluation_learner_agency_boundary", "reproducible_evaluation_package"],
            "readiness_check_ids": ["evaluation_packet", "adaptive_task_plan", "review_board_packet"],
            "source_card_ids": ["vanlehn-2011", "unesco-genai-2023"],
            "human_gates": ["human_submission_review_required"],
            "boundary": "teaching review sees learner-agency evidence as synthetic formative practice, not answer replacement",
        },
        {
            "section_id": "thesis_supervision_trace",
            "reviewers": ["Thesis supervision"],
            "claim_ids": ["gretel_authorship_label", "evaluation_learner_agency_boundary"],
            "readiness_check_ids": ["gretel_bachelor_thesis_package", "evaluation_packet", "review_board_packet"],
            "source_card_ids": ["dfg-gwp", "unesco-genai-2023", "vanlehn-2011"],
            "human_gates": ["human_submission_review_required"],
            "boundary": "thesis supervision sees Gretel-authored claims tied to evaluation evidence and human review gates",
        },
        {
            "section_id": "high_stakes_review_trace",
            "reviewers": ["Pruefungsamt", "Datenschutz"],
            "claim_ids": ["exam_boundary_not_clearance", "evaluation_learner_agency_boundary"],
            "readiness_check_ids": ["exam_boundary", "data_protection_screening", "compliance_matrix"],
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "uoc-ki-faq"],
            "human_gates": ["written_university_clearance_required_before_exam_use", "datenschutz_review_required_before_real_pilot"],
            "boundary": "review board keeps learner-agency evidence out of grading, proctoring, KI detection, and exam clearance",
        },
        {
            "section_id": "public_language_trace",
            "reviewers": required_reviewers,
            "claim_ids": ["evaluation_learner_agency_boundary"],
            "readiness_check_ids": ["review_board_packet", "public_safety"],
            "source_card_ids": [],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
            "boundary": "public language remains draft/review wording until human reviewers approve real submission language",
        },
    ]
    payload = json.dumps(
        {
            "reviewer_rows": reviewer_rows,
            "thesis_evaluation_alignment": thesis_evaluation_alignment,
            "sections": sections,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    payload_scan = scan_text(payload, "review-board-thesis-evaluation-claim-alignment")
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)
    failed_reviewer_ids = sorted(row["reviewer"] for row in reviewer_rows if row["has_evaluation_claim"] is not True)
    contracts = {
        "thesis_evaluation_alignment_ready": thesis_evaluation_alignment["status"] == "ready"
        and thesis_evaluation_alignment["public_safety_status"] == "pass",
        "required_reviewers_have_evaluation_claim": failed_reviewer_ids == [],
        "review_board_evidence_alignment_ready": review_board.get("evidence_alignment", {}).get("status") == "ready"
        and review_board.get("evidence_alignment", {}).get("public_safety_status") == "pass",
        "high_stakes_red_lines_present": "No automatic grading" in review_board.get("cross_cutting_red_lines", [])
        and "No disciplinary KI-detection output" in review_board.get("cross_cutting_red_lines", []),
        "exam_deployment_not_cleared": review_board.get("exam_deployment_status") == "not_cleared",
        "payload_public_safe": payload_scan["status"] == "pass",
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    status = "ready" if not missing_source_card_ids and not failed_reviewer_ids and not failed_contract_ids else "needs_review"
    return {
        "schema_version": REVIEW_BOARD_THESIS_EVALUATION_ALIGNMENT_SCHEMA_VERSION,
        "status": status,
        "section_count": len(sections),
        "sections": sections,
        "reviewer_alignment": reviewer_rows,
        "missing_source_card_ids": missing_source_card_ids,
        "failed_reviewer_ids": failed_reviewer_ids,
        "failed_contract_ids": failed_contract_ids,
        "contracts": contracts,
        "required_readiness_check_ids": sorted(
            {check_id for section in sections for check_id in section["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for section in sections for gate in section["human_gates"]}),
        "public_safety_status": payload_scan["status"],
        "policy": (
            "Review-board thesis-evaluation alignment is a public review aid only; it does not authorize "
            "real submission, grading, exam clearance, proctoring, KI-detection evidence, provider calls, "
            "private course text, local paths, or student data."
        ),
    }


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
    evidence_alignment = build_review_board_evidence_alignment(reviewers)

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
            "evidence_alignment_status": evidence_alignment["status"],
            "evidence_alignment_public_safety_status": evidence_alignment["public_safety_status"],
            "evidence_alignment_reviewer_count": len(evidence_alignment["reviewer_alignment"]),
            "local_cycle_chain_snapshot_status": local_cycle_chain_snapshot.get("status", "missing"),
            "local_cycle_chain_snapshot_hash": local_cycle_chain_snapshot.get("chain_snapshot_summary", {}).get("snapshot_hash", "")
            if isinstance(local_cycle_chain_snapshot.get("chain_snapshot_summary"), dict)
            else "",
        },
        "evidence_alignment": evidence_alignment,
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
    review_board["thesis_evaluation_claim_alignment"] = build_review_board_thesis_evaluation_claim_alignment(review_board)
    review_board["evidence_summary"]["thesis_evaluation_claim_alignment_status"] = review_board[
        "thesis_evaluation_claim_alignment"
    ]["status"]
    review_board["evidence_summary"]["thesis_evaluation_claim_alignment_public_safety_status"] = review_board[
        "thesis_evaluation_claim_alignment"
    ]["public_safety_status"]
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
    alignment = packet["evidence_alignment"]
    thesis_evaluation_alignment = packet["thesis_evaluation_claim_alignment"]
    alignment_lines = "\n".join(
        f"- {item['reviewer']}: claims {', '.join(item['claim_ids'])}; checks {', '.join(item['readiness_check_ids'])}"
        for item in alignment["reviewer_alignment"]
    )
    thesis_evaluation_lines = "\n".join(
        f"- {section['section_id']}: {section['boundary']}" for section in thesis_evaluation_alignment["sections"]
    )
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
        "## Evidence Alignment\n\n"
        f"- Status: {alignment['status']}\n"
        f"- Thesis claims: {alignment['thesis_claim_count']}\n"
        f"- Snapshot schema: {alignment['readiness_snapshot_contract']['expected_schema_version']}\n"
        f"- Snapshot gate count: {len(alignment['readiness_snapshot_contract']['required_gate_ids'])}\n"
        f"{alignment_lines}\n\n"
        "## Thesis Evaluation Claim Alignment\n\n"
        f"- Status: {thesis_evaluation_alignment['status']}\n"
        f"- Public safety: {thesis_evaluation_alignment['public_safety_status']}\n"
        f"{thesis_evaluation_lines}\n\n"
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
