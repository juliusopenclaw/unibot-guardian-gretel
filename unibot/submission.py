from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .clearance import build_institutional_clearance_board
from .compliance import build_compliance_matrix
from .course_tutor import DEFAULT_COURSE_ID, safe_course_id
from .extraction import build_course_extraction_queue
from .extraction_decision import build_extraction_decision_packet
from .extraction_operator import build_extraction_operator_packet
from .handoff import build_authority_handoff_packet
from .privacy import build_data_protection_screening
from .public_safety import scan_text
from .review_board import build_review_board_packet
from .source_cards import get_source_card


STAKEHOLDER_SUBMISSION_SCHEMA_VERSION = "unibot-stakeholder-submission-v1"
STAKEHOLDER_SUBMISSION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-stakeholder-submission-release-review-board-claim-alignment-v1"
)


def build_stakeholder_submission_release_claim_alignment(bundle: dict[str, Any]) -> dict[str, Any]:
    sections = [
        {
            "section_id": "submission_boundary_trace",
            "summary_claim": "stakeholder bundle is a human-review draft and never an automatic send, approval, or exam clearance",
            "source_card_ids": ["uoc-ki-lehre", "dfg-gwp"],
            "readiness_check_ids": [
                "stakeholder_submission_bundle",
                "review_board_packet",
                "authority_handoff",
                "release_runbook",
                "public_safety",
            ],
            "human_gates": ["human_submission_review_required", "public_safety_required"],
        },
        {
            "section_id": "local_extraction_decision_trace",
            "summary_claim": "local OCR/transcription lane remains rights/privacy gated and excludes public raw text or cloud processing claims",
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "dfg-gwp"],
            "readiness_check_ids": [
                "stakeholder_submission_bundle",
                "data_protection_screening",
                "course_material_policy",
                "public_safety",
            ],
            "human_gates": ["datenschutz_review_required_before_real_pilot", "human_submission_review_required"],
        },
        {
            "section_id": "exam_gateway_decision_trace",
            "summary_claim": "exam gateway lane remains not cleared and asks only for written authority review of a possible controlled A0-A2 scope",
            "source_card_ids": ["hg-nrw-2025", "hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq", "eu-ai-act-2024"],
            "readiness_check_ids": [
                "stakeholder_submission_bundle",
                "authority_handoff",
                "compliance_matrix",
                "review_board_packet",
                "exam_boundary",
            ],
            "human_gates": [
                "written_university_clearance_required_before_exam_use",
                "human_submission_review_required",
            ],
        },
        {
            "section_id": "evidence_chain_trace",
            "summary_claim": "bundle evidence links extraction queue, operator packet, clearance board, review board, compliance, privacy, and authority handoff statuses",
            "source_card_ids": [],
            "readiness_check_ids": [
                "stakeholder_submission_bundle",
                "source_card_drift_guard",
                "review_board_packet",
                "authority_handoff",
                "data_protection_screening",
            ],
            "human_gates": ["human_submission_review_required"],
        },
    ]
    required_source_card_ids = sorted({source_id for section in sections for source_id in section["source_card_ids"]})
    missing_source_card_ids = sorted(source_id for source_id in required_source_card_ids if get_source_card(source_id) is None)

    lanes = {lane.get("lane_id"): lane for lane in bundle.get("decision_lanes", [])}
    extraction = lanes.get("rights_privacy_local_extraction", {})
    exam = lanes.get("exam_gateway_authority_clearance", {})
    summary = bundle.get("combined_evidence_summary", {})
    public_safety_statuses = summary.get("public_safety_statuses", {})
    do_not_include = set(bundle.get("do_not_include_in_submission", []))
    open_gates = set(bundle.get("open_external_gates", []))

    contracts = {
        "bundle_prepares_human_submission_not_sent": bundle.get("status") == "ready_for_human_submission_not_sent",
        "exam_deployment_not_cleared": bundle.get("exam_deployment_status") == "not_cleared",
        "submission_boundary_blocks_send_approval_legal_exam": all(
            phrase in bundle.get("submission_boundary", "")
            for phrase in ["does not send messages", "does not claim approval", "does not provide legal advice", "does not clear exam deployment"]
        ),
        "open_external_gates_explicit": {
            "rights/privacy decision before local OCR/transcription",
            "written exam authority clearance before any real exam use",
        }.issubset(open_gates),
        "exactly_two_decision_lanes": set(lanes) == {"rights_privacy_local_extraction", "exam_gateway_authority_clearance"},
        "local_extraction_lane_is_rights_privacy_gated": extraction.get("validator_endpoint")
        == "/api/unibot/course/extraction-decision/validate"
        and extraction.get("minimum_record_template", {}).get("cloud_processing_allowed") is False
        and extraction.get("minimum_record_template", {}).get("raw_text_public_release_allowed") is False
        and "Datenschutz" in extraction.get("reviewer_roles", []),
        "exam_gateway_lane_requires_written_clearance": exam.get("validator_endpoint") == "/api/unibot/institutional-clearance/validate"
        and exam.get("exam_deployment_status") == "not_cleared"
        and exam.get("minimum_record_template", {}).get("help_levels_allowed") == ["A0", "A1", "A2"]
        and "Pruefungsamt" in exam.get("reviewer_roles", []),
        "combined_evidence_links_review_privacy_compliance_authority": summary.get("review_board_status")
        == "draft_for_institutional_review"
        and summary.get("clearance_board_status") == "pending_written_clearance"
        and summary.get("compliance_status") == "draft_ready_for_authority_review"
        and summary.get("privacy_status") == "draft_for_datenschutz_review"
        and summary.get("authority_handoff_status") == "draft_not_officially_cleared",
        "public_safety_evidence_passes": all(
            public_safety_statuses.get(key) == "pass"
            for key in ["extraction_queue", "extraction_decision", "operator_packet", "clearance_board", "privacy", "compliance", "review_board"]
        ),
        "submission_excludes_private_raw_and_high_stakes_claims": {
            "raw private course text",
            "local absolute paths",
            "raw external KI outputs",
            "student personal data",
            "health or accommodation records",
            "official-grade language",
            "claims that the exam gateway is already cleared",
        }.issubset(do_not_include),
    }
    failed_contract_ids = sorted(contract_id for contract_id, passed in contracts.items() if not passed)
    payload = {
        "sections": sections,
        "contracts": contracts,
        "missing_source_card_ids": missing_source_card_ids,
        "blocked_claims": [
            "automatic submission",
            "exam clearance",
            "official grading",
            "proctoring",
            "KI-detection evidence",
            "Datenschutz approval",
            "cloud processing approval",
            "public raw course text release",
        ],
    }
    scan = scan_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "stakeholder-submission-release-claim-alignment",
    )
    status = "ready" if not missing_source_card_ids and not failed_contract_ids and scan["status"] == "pass" else "needs_review"
    return {
        "schema_version": STAKEHOLDER_SUBMISSION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
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
        "public_safety_status": scan["status"],
        "policy": (
            "Stakeholder submission release claims are draft-review aids only; they do not send messages, "
            "approve processing, clear exam use, authorize public raw material release, grade, proctor, "
            "detect KI, or replace written human decisions."
        ),
    }


def build_stakeholder_submission_bundle(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    review_policy: str = "staged",
    public_safe: bool = True,
) -> dict[str, Any]:
    extraction_queue = build_course_extraction_queue(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    extraction_decision = build_extraction_decision_packet(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    operator_packet = build_extraction_operator_packet(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    clearance_board = build_institutional_clearance_board(public_safe=public_safe)
    review_board = build_review_board_packet()
    compliance = build_compliance_matrix()
    privacy = build_data_protection_screening()
    authority_handoff = build_authority_handoff_packet()

    lanes = [
        local_extraction_lane(extraction_queue, extraction_decision, operator_packet, privacy),
        exam_gateway_lane(clearance_board, review_board, compliance, authority_handoff),
    ]
    bundle = {
        "schema_version": STAKEHOLDER_SUBMISSION_SCHEMA_VERSION,
        "artifact_type": "unibot_stakeholder_submission_bundle",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "ready_for_human_submission_not_sent",
        "status_label_de": "Einreichungspaket vorbereitet, keine Freigabe erteilt und nichts versendet",
        "exam_deployment_status": "not_cleared",
        "submission_boundary": (
            "This bundle prepares written human decisions. It does not send messages, "
            "does not claim approval, does not provide legal advice, and does not clear exam deployment."
        ),
        "golden_rule_alignment": {
            "pm_gr1_generalize": "Both remaining external gates use reusable decision lanes and record templates.",
            "pm_gr2_harness_engineering": "Every lane points to validator endpoints, evidence artifacts, and regression checks.",
            "pm_gr3_recursive_self_improvement": "Missing decisions remain explicit open gates instead of becoming vague project risk.",
        },
        "open_external_gates": [
            "rights/privacy decision before local OCR/transcription",
            "written exam authority clearance before any real exam use",
        ],
        "decision_lanes": lanes,
        "combined_evidence_summary": {
            "extraction_job_count": extraction_queue.get("counts", {}).get("job_count", 0),
            "ocr_job_count": extraction_queue.get("counts", {}).get("ocr_job_count", 0),
            "transcription_job_count": extraction_queue.get("counts", {}).get("transcription_job_count", 0),
            "review_board_status": review_board.get("status"),
            "clearance_board_status": clearance_board.get("status"),
            "compliance_status": compliance.get("status"),
            "privacy_status": privacy.get("status"),
            "authority_handoff_status": authority_handoff.get("status"),
            "public_safety_statuses": {
                "extraction_queue": extraction_queue.get("public_safety_status"),
                "extraction_decision": extraction_decision.get("public_safety_status"),
                "operator_packet": operator_packet.get("public_safety_status"),
                "clearance_board": clearance_board.get("public_safety_status"),
                "privacy": privacy.get("public_safety_status"),
                "compliance": compliance.get("public_safety_status"),
                "review_board": review_board.get("public_safety_status"),
            },
        },
        "do_not_include_in_submission": [
            "raw private course text",
            "local absolute paths",
            "raw external KI outputs",
            "student personal data",
            "health or accommodation records",
            "official-grade language",
            "claims that the exam gateway is already cleared",
        ],
        "next_actions": [
            "Review the two decision lanes and choose which human reviewer group to approach first.",
            "Use the lane message template as a draft only; manually review before any real submission.",
            "Validate any written decision record before changing extraction or exam gates.",
            "Keep exam_deployment_status not_cleared unless the responsible authorities issue written clearance.",
        ],
    }
    bundle["release_claim_alignment"] = build_stakeholder_submission_release_claim_alignment(bundle)
    attach_public_scan(bundle, public_safe=public_safe, source_name="stakeholder-submission-bundle")
    return bundle


def local_extraction_lane(
    extraction_queue: dict[str, Any],
    extraction_decision: dict[str, Any],
    operator_packet: dict[str, Any],
    privacy: dict[str, Any],
) -> dict[str, Any]:
    queue_counts = extraction_queue.get("counts", {})
    return {
        "lane_id": "rights_privacy_local_extraction",
        "title": "Local OCR/transcription decision for course tutor preparation",
        "status": "ready_to_request_written_decision",
        "decision_type": "rights_privacy_local_extraction",
        "reviewer_roles": extraction_decision.get("required_reviewer_roles", []),
        "decision_request": (
            "May UniBot process the listed course files locally and privately for OCR/transcription, "
            "with human review before any private tutor index is updated?"
        ),
        "current_evidence": {
            "job_count": queue_counts.get("job_count", 0),
            "ocr_job_count": queue_counts.get("ocr_job_count", 0),
            "transcription_job_count": queue_counts.get("transcription_job_count", 0),
            "quarantine_count": queue_counts.get("quarantine_count", 0),
            "operator_packet_status": operator_packet.get("status"),
            "privacy_status": privacy.get("status"),
        },
        "validator_endpoint": "/api/unibot/course/extraction-decision/validate",
        "follow_up_endpoint_if_valid": "/api/unibot/course/extraction-operator-packet",
        "minimum_record_template": extraction_decision.get("minimum_decision_record", {}),
        "approval_effect_if_valid": extraction_decision.get("approval_effect_if_valid", {}),
        "submission_message_template": (
            "Bitte pruefen Sie, ob eine lokale private OCR/Transkription der im UniBot-Metadatenpaket "
            "gelisteten Kursmaterialien fuer einen kursgenauen Tutor vorbereitet werden darf. "
            "Das Paket enthaelt keine Rohtexte und keine lokalen Pfade; Rohartefakte blieben lokal privat, "
            "Cloud-Verarbeitung ist in diesem Gate deaktiviert, und Tutor-Nutzung erfolgt erst nach menschlicher Review."
        ),
        "must_not_claim": [
            "Datenschutz approval already exists",
            "public raw text release is allowed",
            "exam deployment is authorized",
            "cloud processing is allowed",
        ],
    }


def exam_gateway_lane(
    clearance_board: dict[str, Any],
    review_board: dict[str, Any],
    compliance: dict[str, Any],
    authority_handoff: dict[str, Any],
) -> dict[str, Any]:
    exam_lane = next(
        (lane for lane in clearance_board.get("scope_lanes", []) if lane.get("clearance_scope") == "exam_controlled_gateway"),
        {},
    )
    return {
        "lane_id": "exam_gateway_authority_clearance",
        "title": "Controlled A0-A2 exam gateway / notebook-mode decision",
        "status": "ready_to_request_decision_not_deployable",
        "decision_type": "exam_controlled_gateway",
        "exam_deployment_status": "not_cleared",
        "reviewer_roles": exam_lane.get("required_reviewer_roles", []),
        "decision_request": (
            "Could a future controlled notebook gateway be reviewed for this module/exam scope, "
            "limited to A0-A2 help, with Help Ledger evidence and no proctoring, no KI detection, and no automatic grading?"
        ),
        "current_evidence": {
            "review_board_status": review_board.get("status"),
            "clearance_board_status": clearance_board.get("status"),
            "compliance_status": compliance.get("status"),
            "authority_handoff_status": authority_handoff.get("status"),
            "reviewer_packet_count": len(review_board.get("reviewer_packets", [])),
            "high_risk_requirement_count": compliance.get("high_risk_requirement_count", 0),
        },
        "validator_endpoint": "/api/unibot/institutional-clearance/validate",
        "minimum_record_template": exam_lane.get("minimum_record_template", {}),
        "submission_message_template": (
            "Bitte pruefen Sie nur den Entscheidungsrahmen fuer einen moeglichen spaeteren kontrollierten "
            "Notebook-Gateway-Modus. Der aktuelle Stand ist nicht fuer echte Pruefungen freigegeben. "
            "Der Standardmodus waere auf A0-A2-Hilfe begrenzt, blockiert Loesungen/A6, erzeugt ein Help Ledger "
            "fuer menschliche Review, und vermeidet Proctoring, KI-Detektion und automatische Bewertung."
        ),
        "must_not_claim": [
            "exam use is already cleared",
            "UniBot grades or detects KI",
            "browser overlay is hard exam security",
            "A3-A6 help is standard for real exams",
        ],
    }


def build_stakeholder_submission_markdown(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    review_policy: str = "staged",
) -> str:
    bundle = build_stakeholder_submission_bundle(
        course_id,
        base_path=base_path,
        review_policy=review_policy,
    )
    lane_blocks = []
    for lane in bundle["decision_lanes"]:
        reviewers = ", ".join(lane.get("reviewer_roles", [])) or "to be assigned"
        evidence = "; ".join(f"{key}: {value}" for key, value in lane.get("current_evidence", {}).items())
        must_not = "\n".join(f"- {item}" for item in lane.get("must_not_claim", []))
        lane_blocks.append(
            f"## {lane['title']}\n\n"
            f"Status: {lane['status']}\n\n"
            f"Reviewers: {reviewers}\n\n"
            f"Decision request: {lane['decision_request']}\n\n"
            f"Validator: `{lane['validator_endpoint']}`\n\n"
            f"Evidence: {evidence}\n\n"
            f"Draft message: {lane['submission_message_template']}\n\n"
            f"Must not claim:\n{must_not}\n"
        )
    release_alignment = bundle["release_claim_alignment"]
    return (
        "# UniBot Stakeholder Submission Bundle\n\n"
        f"Status: {bundle['status_label_de']}\n\n"
        f"Exam deployment: {bundle['exam_deployment_status']}\n\n"
        f"Boundary: {bundle['submission_boundary']}\n\n"
        "## Release Claim Alignment\n\n"
        f"- Status: {release_alignment['status']}\n"
        f"- Public Safety: {release_alignment['public_safety_status']}\n"
        f"- Human Gates: {', '.join(release_alignment['required_human_gates'])}\n"
        f"- Blocked Claims: {', '.join(release_alignment['blocked_claims'])}\n\n"
        "## Open External Gates\n\n"
        + "\n".join(f"- {item}" for item in bundle["open_external_gates"])
        + "\n\n"
        + "\n\n".join(lane_blocks)
        + "\n\n## Next Actions\n\n"
        + "\n".join(f"- {item}" for item in bundle["next_actions"])
        + "\n"
    )


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
