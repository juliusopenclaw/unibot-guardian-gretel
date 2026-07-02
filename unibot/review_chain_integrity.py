from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text
from .timeline_export_receipt_journal import summarize_timeline_export_receipt_journal


REVIEW_CHAIN_INTEGRITY_SCHEMA_VERSION = "unibot-review-chain-integrity-v1"
REVIEW_CHAIN_INTEGRITY_ENDPOINT = "/api/unibot/course/review-chain-integrity-check"


def build_review_chain_integrity_check(
    *,
    exam_run_packet: dict[str, Any] | None = None,
    exam_packet_timeline: dict[str, Any] | None = None,
    timeline_export_review_packet: dict[str, Any] | None = None,
    timeline_export_receipt_journal_append: dict[str, Any] | None = None,
    timeline_export_receipt_journal_summary: dict[str, Any] | None = None,
    timeline_export_receipt_journal_path: str | None = None,
    selected_skill_tag: str = "",
    public_safe: bool = True,
) -> dict[str, Any]:
    packet = exam_run_packet if isinstance(exam_run_packet, dict) else {}
    timeline = exam_packet_timeline if isinstance(exam_packet_timeline, dict) else {}
    review = timeline_export_review_packet if isinstance(timeline_export_review_packet, dict) else {}
    journal_append = (
        timeline_export_receipt_journal_append if isinstance(timeline_export_receipt_journal_append, dict) else {}
    )
    journal_summary = (
        timeline_export_receipt_journal_summary
        if isinstance(timeline_export_receipt_journal_summary, dict)
        else summarize_timeline_export_receipt_journal(timeline_export_receipt_journal_path)
    )
    context = chain_context(packet, timeline, review, journal_append, journal_summary, selected_skill_tag)
    findings = integrity_findings(context)
    summary = integrity_summary(context, findings)
    payload = {
        "schema_version": REVIEW_CHAIN_INTEGRITY_SCHEMA_VERSION,
        "artifact_type": "review_chain_integrity_check",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Review Chain Integrity Check. It verifies metadata/hash consistency across Exam Run Packet, "
            "Exam Packet Timeline, Timeline Export Review Packet, and Timeline Export Receipt Journal. It "
            "marks missing, duplicate, or contradictory chain links and returns the next safe action. It never "
            "returns raw queries, course raw text, notebook code, local paths, values, solutions, final "
            "interpretations, proctoring, AI detection, automatic assessment, or exam clearance."
        ),
        "chain_integrity_summary": summary,
        "chain_context": context,
        "findings": findings,
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "next_actions": next_actions(summary),
    }
    attach_public_scan(payload, public_safe=public_safe)
    return payload


def chain_context(
    packet: dict[str, Any],
    timeline: dict[str, Any],
    review: dict[str, Any],
    journal_append: dict[str, Any],
    journal_summary: dict[str, Any],
    selected_skill_tag: str,
) -> dict[str, Any]:
    packet_skill = packet.get("selected_skill_packet", {}) if isinstance(packet.get("selected_skill_packet"), dict) else {}
    packet_receipt = packet.get("packet_receipt", {}) if isinstance(packet.get("packet_receipt"), dict) else {}
    timeline_summary = timeline.get("timeline_summary", {}) if isinstance(timeline.get("timeline_summary"), dict) else {}
    timeline_receipt = timeline.get("timeline_receipt", {}) if isinstance(timeline.get("timeline_receipt"), dict) else {}
    timeline_events = [event for event in timeline.get("timeline_events", []) if isinstance(event, dict)]
    review_summary = review.get("export_review_summary", {}) if isinstance(review.get("export_review_summary"), dict) else {}
    review_receipt = review.get("local_export_receipt", {}) if isinstance(review.get("local_export_receipt"), dict) else {}
    review_skill_packets = [
        item for item in review.get("skill_review_packets", []) if isinstance(item, dict)
    ]
    journal_record = {}
    for key in ("stored_record", "preview_record"):
        if isinstance(journal_append.get(key), dict):
            journal_record = journal_append[key]
            break
    journal_event = journal_record.get("event", {}) if isinstance(journal_record.get("event"), dict) else {}
    raw_skill_tags = [
        selected_skill_tag,
        packet_skill.get("skill_tag", ""),
        *(timeline_summary.get("skill_tags", []) or []),
        *(review_summary.get("skill_tags", []) or []),
        *(journal_summary.get("skill_tags", []) or []),
    ]
    skill_tags = unique_values(raw_skill_tags)
    return {
        "expected_skill_tags": skill_tags,
        "duplicate_skill_tags": unique_values(
            duplicate_values([str(item) for item in (timeline_summary.get("skill_tags", []) or []) if str(item)])
            + duplicate_values([str(item) for item in (review_summary.get("skill_tags", []) or []) if str(item)])
            + duplicate_values([str(item) for item in (journal_summary.get("skill_tags", []) or []) if str(item)])
        ),
        "artifacts_present": {
            "exam_run_packet": packet.get("artifact_type") == "exam_run_packet",
            "exam_packet_timeline": timeline.get("artifact_type") == "exam_packet_timeline",
            "timeline_export_review_packet": review.get("artifact_type") == "timeline_export_review_packet",
            "timeline_export_receipt_journal_summary": journal_summary.get("artifact_type")
            == "timeline_export_receipt_journal_summary",
        },
        "exam_deployment_statuses": {
            "exam_run_packet": packet.get("exam_deployment_status", ""),
            "exam_packet_timeline": timeline.get("exam_deployment_status", ""),
            "timeline_export_review_packet": review.get("exam_deployment_status", ""),
            "timeline_export_receipt_journal_summary": journal_summary.get("exam_deployment_status", ""),
        },
        "receipt_ids": {
            "packet_receipt_id": packet_receipt.get("receipt_id", ""),
            "timeline_receipt_id": timeline_receipt.get("receipt_id", ""),
            "review_receipt_id": review_receipt.get("receipt_id", ""),
            "journal_receipt_id": journal_event.get("receipt_id", ""),
        },
        "receipt_hashes_present": {
            "packet_receipt_hash": bool(packet_receipt.get("receipt_hash")),
            "timeline_receipt_hash": bool(timeline_receipt.get("receipt_hash")),
            "review_receipt_hash": bool(review_receipt.get("receipt_hash")),
            "journal_receipt_hash": bool(journal_event.get("receipt_hash")),
        },
        "counts": {
            "timeline_event_count": int(timeline_summary.get("event_count", 0) or 0),
            "actual_timeline_event_count": len(timeline_events),
            "review_event_count": int(review_summary.get("event_count", 0) or 0),
            "journal_event_count": int(journal_summary.get("event_count", 0) or 0),
            "timeline_checkpoint_hash_count": int(timeline_summary.get("checkpoint_hash_count", 0) or 0),
            "review_checkpoint_hash_count": int(review_summary.get("checkpoint_hash_count", 0) or 0),
            "journal_checkpoint_hash_count": int(journal_summary.get("checkpoint_hash_count", 0) or 0),
            "reviewer_question_count": int(review_summary.get("reviewer_question_count", 0) or 0),
            "journal_reviewer_question_count": int(journal_summary.get("reviewer_question_count", 0) or 0),
        },
        "help_level_profiles": {
            "packet": dict(packet_skill.get("help_level_profile", {}) or {}),
            "timeline": dict(timeline_summary.get("help_level_profile", {}) or {}),
            "review": dict(review_summary.get("help_level_profile", {}) or {}),
            "journal": dict(journal_summary.get("help_level_profile", {}) or {}),
        },
        "open_operator_confirmation_counts": {
            "packet": int(packet_skill.get("open_operator_confirmation_count", 0) or 0),
            "timeline": int(timeline_summary.get("open_operator_confirmation_count", 0) or 0),
            "review": int(review_summary.get("open_operator_confirmation_count", 0) or 0),
            "journal": int(journal_summary.get("open_operator_confirmation_count", 0) or 0),
        },
        "reflection_statuses": {
            "timeline": list(timeline_summary.get("reflection_statuses", []) or []),
            "review": list(review_summary.get("reflection_statuses", []) or []),
            "journal": list(journal_summary.get("reflection_statuses", []) or []),
        },
        "journal_status": {
            "summary_status": journal_summary.get("status", "missing"),
            "record_count": int(journal_summary.get("record_count", 0) or 0),
            "accepted_record_count": int(journal_summary.get("accepted_record_count", 0) or 0),
            "blocked_record_count": int(journal_summary.get("blocked_record_count", 0) or 0),
            "append_status": journal_append.get("status", "missing") if journal_append else "missing",
        },
        "timeline_packet_receipt_ids": unique_values(
            event.get("packet_receipt_id", "") for event in timeline_events if isinstance(event, dict)
        ),
        "review_packet_receipt_ids": unique_values(
            receipt for item in review_skill_packets for receipt in (item.get("packet_receipts", []) or [])
        ),
        "safety_flags": {
            "raw_query_returned": any_flag_true(packet, timeline, review, journal_summary, "raw_query_returned"),
            "raw_text_returned": any_flag_true(packet, timeline, review, journal_summary, "raw_text_returned"),
            "raw_cell_returned": any_flag_true(packet, timeline, review, journal_summary, "raw_cell_returned"),
            "raw_notebook_returned": any_flag_true(packet, timeline, review, journal_summary, "raw_notebook_returned"),
            "notebook_code_returned": any_flag_true(packet, timeline, review, journal_summary, "notebook_code_returned"),
            "local_paths_returned": any_flag_true(packet, timeline, review, journal_summary, "local_paths_returned"),
            "automatic_grading_started": any_flag_true(packet, timeline, review, journal_summary, "automatic_grading_started"),
            "proctoring_started": any_flag_true(packet, timeline, review, journal_summary, "proctoring_started"),
            "ai_detection_started": any_flag_true(packet, timeline, review, journal_summary, "ai_detection_started"),
            "exam_clearance_claimed": any_flag_true(packet, timeline, review, journal_summary, "exam_clearance_claimed"),
        },
    }


def integrity_findings(context: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for artifact, present in context.get("artifacts_present", {}).items():
        add_finding(findings, present, "missing", artifact, f"{artifact} present")
    for artifact, status in context.get("exam_deployment_statuses", {}).items():
        add_finding(
            findings,
            status == "not_cleared",
            "contradiction",
            f"{artifact}.exam_deployment_status",
            "exam_deployment_status must remain not_cleared",
        )
    for receipt_name, receipt_id in context.get("receipt_ids", {}).items():
        if receipt_name == "journal_receipt_id" and not receipt_id:
            add_finding(findings, False, "missing", receipt_name, "journal receipt id missing from append/preview")
        else:
            add_finding(findings, bool(receipt_id), "missing", receipt_name, "receipt id present")
    for receipt_hash_name, present in context.get("receipt_hashes_present", {}).items():
        if receipt_hash_name == "journal_receipt_hash" and not present:
            add_finding(findings, False, "missing", receipt_hash_name, "journal receipt hash missing from append/preview")
        else:
            add_finding(findings, bool(present), "missing", receipt_hash_name, "receipt hash present")

    receipt_ids = context.get("receipt_ids", {})
    packet_id = receipt_ids.get("packet_receipt_id", "")
    if packet_id:
        add_finding(
            findings,
            packet_id in (context.get("timeline_packet_receipt_ids", []) or []),
            "contradiction",
            "timeline_packet_receipt_ids",
            "timeline must reference the Exam Run Packet receipt id",
        )
        add_finding(
            findings,
            packet_id in (context.get("review_packet_receipt_ids", []) or []),
            "contradiction",
            "review_packet_receipt_ids",
            "review packet must reference the Exam Run Packet receipt id",
        )
    review_id = receipt_ids.get("review_receipt_id", "")
    journal_id = receipt_ids.get("journal_receipt_id", "")
    add_finding(
        findings,
        bool(review_id and journal_id and review_id == journal_id),
        "contradiction",
        "journal_review_receipt_id",
        "journal receipt must match Timeline Export Review Packet receipt id",
    )

    counts = context.get("counts", {})
    add_finding(
        findings,
        counts.get("timeline_event_count") == counts.get("actual_timeline_event_count") and counts.get("timeline_event_count", 0) > 0,
        "contradiction",
        "timeline_event_count",
        "timeline summary event count must match visible timeline events",
    )
    for left, right, name in [
        ("timeline_event_count", "review_event_count", "timeline_to_review_event_count"),
        ("review_event_count", "journal_event_count", "review_to_journal_event_count"),
        ("timeline_checkpoint_hash_count", "review_checkpoint_hash_count", "timeline_to_review_checkpoint_count"),
        ("review_checkpoint_hash_count", "journal_checkpoint_hash_count", "review_to_journal_checkpoint_count"),
        ("reviewer_question_count", "journal_reviewer_question_count", "review_to_journal_question_count"),
    ]:
        add_finding(
            findings,
            int(counts.get(right, 0) or 0) >= int(counts.get(left, 0) or 0) and int(counts.get(left, 0) or 0) > 0,
            "contradiction",
            name,
            f"{right} must cover {left}",
        )
    add_profile_findings(findings, context.get("help_level_profiles", {}))
    add_count_findings(findings, context.get("open_operator_confirmation_counts", {}), "open_operator_confirmation_count")
    add_reflection_findings(findings, context.get("reflection_statuses", {}))
    add_skill_tag_findings(
        findings,
        context.get("expected_skill_tags", []),
        context.get("duplicate_skill_tags", []),
    )
    journal = context.get("journal_status", {})
    add_finding(findings, int(journal.get("record_count", 0) or 0) >= 1, "missing", "journal_record_count", "journal must contain at least one record")
    add_finding(
        findings,
        int(journal.get("accepted_record_count", 0) or 0) >= 1,
        "missing",
        "journal_accepted_record_count",
        "journal must contain at least one accepted record",
    )
    for flag, value in context.get("safety_flags", {}).items():
        add_finding(findings, value is False, "contradiction", flag, f"{flag} must be false")
    return findings


def add_profile_findings(findings: list[dict[str, Any]], profiles: dict[str, dict[str, int]]) -> None:
    expected = profiles.get("packet") or profiles.get("timeline") or profiles.get("review") or {}
    for source in ("timeline", "review", "journal"):
        profile = profiles.get(source, {})
        for level, count in expected.items():
            add_finding(
                findings,
                int(profile.get(level, 0) or 0) >= int(count or 0),
                "contradiction",
                f"{source}.help_level_profile.{level}",
                f"{source} help profile must cover packet help profile",
            )
        for level, count in profile.items():
            if level not in {"A0", "A1", "A2"} and int(count or 0) > 0:
                add_finding(
                    findings,
                    False,
                    "contradiction",
                    f"{source}.help_level_profile.{level}",
                    "higher help level requires explicit non-standard exception",
                )


def add_count_findings(findings: list[dict[str, Any]], counts: dict[str, int], item_name: str) -> None:
    packet_count = int(counts.get("packet", 0) or 0)
    for source in ("timeline", "review", "journal"):
        add_finding(
            findings,
            int(counts.get(source, 0) or 0) >= packet_count,
            "contradiction",
            f"{source}.{item_name}",
            f"{source} {item_name} must cover packet count",
        )


def add_reflection_findings(findings: list[dict[str, Any]], statuses: dict[str, list[str]]) -> None:
    expected = set(statuses.get("timeline", []) or statuses.get("review", []) or [])
    for source in ("review", "journal"):
        source_statuses = set(statuses.get(source, []) or [])
        add_finding(
            findings,
            expected.issubset(source_statuses),
            "contradiction",
            f"{source}.reflection_statuses",
            f"{source} reflection statuses must cover earlier chain reflection statuses",
        )


def add_skill_tag_findings(findings: list[dict[str, Any]], skill_tags: list[str], duplicates: list[str]) -> None:
    add_finding(findings, bool(skill_tags), "missing", "skill_tags", "at least one skill tag present")
    add_finding(findings, not duplicates, "duplicate", "skill_tags", "skill tags should be normalized without duplicates")


def add_finding(findings: list[dict[str, Any]], condition: bool, finding_type: str, item: str, detail: str) -> None:
    findings.append(
        {
            "item": item,
            "finding_type": finding_type,
            "status": "pass" if condition else "attention_required",
            "severity": "none" if condition else ("warning" if finding_type == "duplicate" else "error"),
            "detail": detail,
        }
    )


def integrity_summary(context: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    attention = [item for item in findings if item.get("status") != "pass"]
    missing = [item for item in attention if item.get("finding_type") == "missing"]
    contradictions = [item for item in attention if item.get("finding_type") == "contradiction"]
    duplicates = [item for item in attention if item.get("finding_type") == "duplicate"]
    status = "review_chain_integrity_pass" if not attention else "review_chain_integrity_attention_required"
    return {
        "status": status,
        "checked_link_count": 4,
        "finding_count": len(findings),
        "issue_count": len(attention),
        "missing_count": len(missing),
        "contradiction_count": len(contradictions),
        "duplicate_count": len(duplicates),
        "skill_tags": context.get("expected_skill_tags", []),
        "receipt_ids": dict(context.get("receipt_ids", {}) or {}),
        "counts": dict(context.get("counts", {}) or {}),
        "help_level_profiles": dict(context.get("help_level_profiles", {}) or {}),
        "open_operator_confirmation_counts": dict(context.get("open_operator_confirmation_counts", {}) or {}),
        "reflection_statuses": dict(context.get("reflection_statuses", {}) or {}),
        "journal_status": dict(context.get("journal_status", {}) or {}),
        "exam_deployment_status": "not_cleared",
        "next_safe_action": next_safe_action(status, attention),
    }


def next_safe_action(status: str, attention: list[dict[str, Any]]) -> str:
    if status == "review_chain_integrity_pass":
        return "Proceed to human review using the metadata-only chain; keep exam_deployment_status not_cleared."
    first = attention[0] if attention else {}
    return f"Resolve {first.get('item', 'the first integrity finding')} before relying on the review chain."


def next_actions(summary: dict[str, Any]) -> list[str]:
    return [
        summary.get("next_safe_action", "Review chain findings."),
        "Keep all local write steps behind operator confirmation.",
        "Keep real-world exam clearance outside UniBot; this check remains not_cleared.",
    ]


def any_flag_true(*payloads_and_flag: Any) -> bool:
    if not payloads_and_flag:
        return False
    *payloads, flag = payloads_and_flag
    return any(isinstance(payload, dict) and payload.get(flag) is True for payload in payloads)


def unique_values(values: Any) -> list[str]:
    result = []
    for value in values:
        text = str(value)
        if text and text not in result:
            result.append(text)
    return result


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "review-chain-integrity-check")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
