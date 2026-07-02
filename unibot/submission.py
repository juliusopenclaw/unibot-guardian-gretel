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


STAKEHOLDER_SUBMISSION_SCHEMA_VERSION = "unibot-stakeholder-submission-v1"


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
    return (
        "# UniBot Stakeholder Submission Bundle\n\n"
        f"Status: {bundle['status_label_de']}\n\n"
        f"Exam deployment: {bundle['exam_deployment_status']}\n\n"
        f"Boundary: {bundle['submission_boundary']}\n\n"
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
