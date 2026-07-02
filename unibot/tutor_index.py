from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import (
    DEFAULT_COURSE_ID,
    FINAL_SOLUTION_REQUEST,
    SKILL_BY_TAG,
    build_course_exam_scope,
    next_task_for_skill,
    normalize_help_level,
    safe_course_id,
    socratic_questions_for_skill,
)
from .extraction_manifest_apply import read_private_manifest, resolve_private_manifest_path
from .materials import normalize_material_record, sha256_text, validate_material_record
from .public_safety import scan_text


ROOT = Path(__file__).resolve().parents[1]
TUTOR_INDEX_SCHEMA_VERSION = "unibot-private-tutor-index-v1"
DEFAULT_TUTOR_INDEX_ROOT = ROOT / "knowledge" / ".unibot_guardian"
DEFAULT_PRIVATE_TUTOR_INDEX_PATH = DEFAULT_TUTOR_INDEX_ROOT / "private_tutor_index.hash_only.json"
DEFAULT_TUTOR_INDEX_JOURNAL_PATH = DEFAULT_TUTOR_INDEX_ROOT / "private_tutor_index_journal.jsonl"
SKILL_TAG_ALIASES = {
    "data_files": "pandas",
    "dataframe": "pandas",
    "dataframes": "pandas",
    "dictionaries": "python_lists",
    "functions": "control_flow",
    "general_python": "python_lists",
    "loops": "control_flow",
    "plotting": "boxplots",
}


def resolve_private_tutor_index_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_PRIVATE_TUTOR_INDEX_PATH")
    if env_path:
        return Path(env_path).expanduser()
    workspace_root = os.environ.get("UNIBOT_EXAM_WORKSPACE_ROOT")
    if workspace_root:
        return Path(workspace_root).expanduser() / ".unibot_guardian" / "private_tutor_index.hash_only.json"
    return DEFAULT_PRIVATE_TUTOR_INDEX_PATH


def resolve_tutor_index_journal_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("UNIBOT_PRIVATE_TUTOR_INDEX_JOURNAL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    workspace_root = os.environ.get("UNIBOT_EXAM_WORKSPACE_ROOT")
    if workspace_root:
        return Path(workspace_root).expanduser() / ".unibot_guardian" / "private_tutor_index_journal.jsonl"
    return DEFAULT_TUTOR_INDEX_JOURNAL_PATH


def read_private_tutor_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "artifact_type": "course_private_tutor_index_snapshot",
            "coverage_summary": {},
            "source_anchors": [],
            "skill_index": [],
            "source_card_index": [],
            "priority_coverage_gaps": [],
            "index_hash": "",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "status": "blocked_unreadable_private_tutor_index",
            "artifact_type": "course_private_tutor_index_snapshot",
            "coverage_summary": {},
            "source_anchors": [],
            "skill_index": [],
            "source_card_index": [],
            "priority_coverage_gaps": [],
            "index_hash": "",
        }
    if not isinstance(payload, dict) or payload.get("artifact_type") != "course_private_tutor_index_snapshot":
        return {
            "status": "blocked_invalid_private_tutor_index",
            "artifact_type": str(payload.get("artifact_type", "")) if isinstance(payload, dict) else "",
            "coverage_summary": {},
            "source_anchors": [],
            "skill_index": [],
            "source_card_index": [],
            "priority_coverage_gaps": [],
            "index_hash": "",
        }
    return {
        "status": "ok",
        "artifact_type": payload.get("artifact_type", ""),
        "schema_version": payload.get("schema_version", ""),
        "course_id": payload.get("course_id", ""),
        "exam_deployment_status": payload.get("exam_deployment_status", "not_cleared"),
        "manifest_hash": payload.get("manifest_hash", ""),
        "coverage_summary": safe_mapping(payload.get("coverage_summary", {})),
        "source_anchors": [safe_anchor_view(anchor) for anchor in payload.get("source_anchors", []) if isinstance(anchor, dict)],
        "skill_index": [safe_skill_index_view(skill) for skill in payload.get("skill_index", []) if isinstance(skill, dict)],
        "source_card_index": [safe_source_card_view(card) for card in payload.get("source_card_index", []) if isinstance(card, dict)],
        "priority_coverage_gaps": [
            safe_gap_view(gap) for gap in payload.get("priority_coverage_gaps", []) if isinstance(gap, dict)
        ],
        "index_hash": payload.get("index_hash", sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))),
    }


def build_private_index_tutor_response_dry_run(
    query: str,
    *,
    course_id: str = DEFAULT_COURSE_ID,
    tutor_index_path: str | Path | None = None,
    mode: str = "exam_controlled_gateway",
    requested_help_level: str = "A2",
    exam_status: str = "strict",
    public_safe: bool = True,
) -> dict[str, Any]:
    index_path = resolve_private_tutor_index_path(tutor_index_path)
    index_payload = read_private_tutor_index(index_path)
    query_text = str(query or "").strip()
    query_hash = sha256_text(query_text)
    requested = normalize_help_level(requested_help_level)
    strict = mode == "exam_controlled_gateway" or exam_status in {"closed", "strict", "exam"}
    dangerous = bool(FINAL_SOLUTION_REQUEST.search(query_text))
    selected = select_index_skill(index_payload.get("skill_index", []), query_text)
    anchors = anchors_for_selected_skill(index_payload, selected)
    status = tutor_response_status(
        index_payload=index_payload,
        selected=selected,
        anchors=anchors,
        requested_help_level=requested,
        dangerous=dangerous,
    )
    if status != "allowed":
        anchors = []
    help_level = "A2" if status == "allowed" else "A6" if status == "blocked" else requested
    message = index_tutor_message(
        status=status,
        selected=selected,
        anchors=anchors,
        requested_help_level=requested,
    )
    source_card_ids = sorted(
        {
            str(card_id)
            for anchor in anchors
            for card_id in anchor.get("source_card_ids", []) or []
        }
    )[:8] or list(selected.get("source_card_ids", []) or [])[:8]
    source_anchor_ids = [anchor.get("anchor_id", "") for anchor in anchors[:4]]
    response = {
        "schema_version": TUTOR_INDEX_SCHEMA_VERSION,
        "artifact_type": "course_private_index_tutor_response_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": status,
        "mode": mode,
        "strict_exam_boundary": strict,
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Index-guided private tutor response dry-run. It reads only the hash-only tutor index, returns "
            "A0-A2 Socratic guidance and source-anchor metadata, never raw course text, never local paths, "
            "never complete code, values, final interpretation, grading, proctoring, AI detection, or exam clearance."
        ),
        "query_hash": query_hash,
        "raw_query_returned": False,
        "requested_help_level": requested,
        "effective_help_level": help_level,
        "allowed_help_levels": ["A0", "A1", "A2"],
        "blocked_help": ["A3-A6 without explicit written decision", "complete code", "inserted values", "final interpretation"],
        "selected_skill": {
            "skill_tag": selected.get("skill_tag", ""),
            "title": selected.get("title", ""),
            "readiness": selected.get("readiness", "unknown"),
            "anchor_count": selected.get("anchor_count", 0),
        },
        "answer_markdown": message,
        "socratic_questions": socratic_questions_for_skill(selected, strict=True) if status == "allowed" else [],
        "next_task": next_task_for_skill(selected, strict=True) if status == "allowed" else {},
        "source_anchors": anchors[:4],
        "source_card_ids": source_card_ids,
        "index_summary": {
            "status": index_payload.get("status", "missing"),
            "index_hash": index_payload.get("index_hash", ""),
            "manifest_hash": index_payload.get("manifest_hash", ""),
            "anchor_count": index_payload.get("coverage_summary", {}).get("anchor_count", 0),
            "indexed_skill_count": index_payload.get("coverage_summary", {}).get("indexed_skill_count", 0),
            "missing_skill_count": index_payload.get("coverage_summary", {}).get("missing_skill_count", 0),
            "tutor_index_path_returned": False,
        },
        "priority_coverage_gaps": list(index_payload.get("priority_coverage_gaps", []) or [])[:5],
        "help_ledger_preview": {
            "course_id": safe_course_id(course_id),
            "query_hash": query_hash,
            "help_level": help_level,
            "help_kind": "blocked final-solution request" if status == "blocked" else "private-index Socratic tutor dry-run",
            "source_anchor_ids": source_anchor_ids,
            "source_card_ids": source_card_ids,
            "raw_response_hash": sha256_text(message),
            "accessibility_neutral": requested == "A0",
            "human_review_required": True,
            "exam_deployment_status": "not_cleared",
        },
        "raw_text_returned": False,
        "local_paths_returned": False,
        "tutor_index_path_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "next_actions": index_tutor_response_next_actions(status, index_payload, selected),
    }
    attach_public_scan(response, public_safe=public_safe)
    return response


def safe_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_anchor_view(anchor: dict[str, Any]) -> dict[str, Any]:
    return {
        "anchor_id": str(anchor.get("anchor_id", "")),
        "retrieval_anchor_hash": str(anchor.get("retrieval_anchor_hash", "")),
        "material_id": str(anchor.get("material_id", "")),
        "title": str(anchor.get("title", "")),
        "source_kind": str(anchor.get("source_kind", "")),
        "skill_tags": list(anchor.get("skill_tags", []) or [])[:8],
        "source_card_ids": list(anchor.get("source_card_ids", []) or [])[:8],
        "page_or_timestamp": str(anchor.get("page_or_timestamp", "")),
        "sha256": str(anchor.get("sha256", "")),
        "review_status": str(anchor.get("review_status", "")),
        "extraction_status": str(anchor.get("extraction_status", "")),
        "retrieval_policy": str(anchor.get("retrieval_policy", "metadata_anchor_only_no_raw_text")),
        "raw_text_stored": False,
        "local_path_stored": False,
    }


def safe_skill_index_view(skill: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": str(skill.get("skill_tag", "")),
        "title": str(skill.get("title", "")),
        "readiness": str(skill.get("readiness", "unknown")),
        "anchor_count": int(skill.get("anchor_count", 0) or 0),
        "material_count": int(skill.get("material_count", 0) or 0),
        "tutor_usable_count": int(skill.get("tutor_usable_count", 0) or 0),
        "source_anchor_ids": list(skill.get("source_anchor_ids", []) or [])[:8],
        "source_card_ids": list(skill.get("source_card_ids", []) or [])[:8],
        "allowed_exam_help": list(skill.get("allowed_exam_help", []) or [])[:8],
        "blocked_exam_help": list(skill.get("blocked_exam_help", []) or [])[:8],
    }


def safe_source_card_view(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_card_id": str(card.get("source_card_id", "")),
        "anchor_count": int(card.get("anchor_count", 0) or 0),
        "source_anchor_ids": list(card.get("source_anchor_ids", []) or [])[:8],
    }


def safe_gap_view(gap: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_tag": str(gap.get("skill_tag", "")),
        "title": str(gap.get("title", "")),
        "priority": str(gap.get("priority", "medium")),
        "current_readiness": str(gap.get("current_readiness", "unknown")),
        "next_review_need": str(gap.get("next_review_need", "")),
    }


def select_index_skill(skill_index: list[dict[str, Any]], query: str) -> dict[str, Any]:
    haystack = query.lower()
    scored = []
    for skill in skill_index:
        tag = str(skill.get("skill_tag", ""))
        profile = SKILL_BY_TAG.get(tag)
        keywords = profile.keywords if profile else (tag,)
        keyword_score = sum(1 for keyword in keywords if keyword.lower() in haystack)
        anchor_score = min(int(skill.get("anchor_count", 0) or 0), 10)
        readiness_score = 1 if skill.get("readiness") == "retrieval_anchor_ready" else 0
        score = keyword_score * 100 + anchor_score * 3 + readiness_score
        scored.append((score, keyword_score, anchor_score, readiness_score, skill))
    scored.sort(key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
    if scored:
        return scored[0][4]
    profile = SKILL_BY_TAG["python_lists"]
    return {
        "skill_tag": profile.skill_tag,
        "title": profile.title,
        "readiness": "no_index_loaded",
        "anchor_count": 0,
        "source_anchor_ids": [],
        "source_card_ids": list(profile.source_card_ids),
        "allowed_exam_help": list(profile.allowed_exam_help),
        "blocked_exam_help": ["complete solution"],
    }


def anchors_for_selected_skill(index_payload: dict[str, Any], selected: dict[str, Any]) -> list[dict[str, Any]]:
    wanted_ids = {str(anchor_id) for anchor_id in selected.get("source_anchor_ids", []) or []}
    anchors = [anchor for anchor in index_payload.get("source_anchors", []) if anchor.get("anchor_id") in wanted_ids]
    if anchors:
        return anchors
    tag = str(selected.get("skill_tag", ""))
    return [
        anchor
        for anchor in index_payload.get("source_anchors", [])
        if tag in {str(item) for item in anchor.get("skill_tags", []) or []}
    ][:4]


def tutor_response_status(
    *,
    index_payload: dict[str, Any],
    selected: dict[str, Any],
    anchors: list[dict[str, Any]],
    requested_help_level: str,
    dangerous: bool,
) -> str:
    if requested_help_level not in {"A0", "A1", "A2"} or dangerous:
        return "blocked"
    if index_payload.get("status") == "missing":
        return "waiting_for_private_tutor_index_build"
    if index_payload.get("status") != "ok":
        return str(index_payload.get("status", "blocked_invalid_private_tutor_index"))
    if not anchors or int(selected.get("anchor_count", 0) or 0) <= 0:
        return "no_index_anchor"
    return "allowed"


def index_tutor_message(
    *,
    status: str,
    selected: dict[str, Any],
    anchors: list[dict[str, Any]],
    requested_help_level: str,
) -> str:
    if status == "blocked":
        return (
            "Blockiert: Der index-gestuetzte Tutor bleibt bei A0-A2. "
            "Fertige Loesungen, vollstaendiger Code, eingesetzte Werte und finale Interpretation werden nicht ausgegeben."
        )
    if status == "waiting_for_private_tutor_index_build":
        return "Der private Tutor-Index ist noch nicht gebaut. Fuehre zuerst den hash-only Tutor-Index-Dry-Run mit bestaetigtem Build aus."
    if status != "allowed":
        return "Ich finde im privaten Tutor-Index fuer diesen Skill noch keinen belastbaren Quellenanker."
    anchor_count = len(anchors)
    title = selected.get("title", "diesem Python-Skill")
    return (
        f"Ich nutze {anchor_count} privaten Kursanker zu {title}. "
        f"{requested_help_level}-Hilfe: Pruefe zuerst deine eigene Vorhersage, den passenden Quellenanker "
        "und den kleinsten Notebook-Schritt. Ich gebe keinen Loesungscode, keine eingesetzten Werte und keine finale Interpretation aus."
    )


def index_tutor_response_next_actions(
    status: str,
    index_payload: dict[str, Any],
    selected: dict[str, Any],
) -> list[str]:
    if status == "waiting_for_private_tutor_index_build":
        return ["Build the private hash-only tutor index after reviewing the dry-run anchor preview."]
    if status == "blocked":
        return ["Rephrase as an A0-A2 request: ask for a source anchor, a syntax pointer, or one Socratic next-check question."]
    if status != "allowed":
        gaps = list(index_payload.get("priority_coverage_gaps", []) or [])
        if gaps:
            return [f"Review or extract course material for {gaps[0].get('skill_tag', 'the missing skill')} before using this tutor path."]
        return ["Add reviewed private tutor anchors for the selected skill before using the index-guided response."]
    return [
        "Write one prediction, run the smallest notebook step yourself, then store the Help-Ledger preview if useful.",
        f"Keep expanding coverage for adjacent skill gaps after {selected.get('skill_tag', 'this skill')}.",
        "Reminder: real exam authority clearance remains a real-world follow-up; UniBot stays not_cleared.",
    ]


def build_private_tutor_index_dry_run(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    private_manifest_path: str | Path | None = None,
    tutor_index_path: str | Path | None = None,
    tutor_index_journal_path: str | Path | None = None,
    operator_confirmed_tutor_index_build: bool = False,
    public_safe: bool = True,
) -> dict[str, Any]:
    manifest_path = resolve_private_manifest_path(private_manifest_path)
    index_path = resolve_private_tutor_index_path(tutor_index_path)
    if tutor_index_journal_path is not None:
        journal_path = resolve_tutor_index_journal_path(tutor_index_journal_path)
    else:
        env_journal_path = os.environ.get("UNIBOT_PRIVATE_TUTOR_INDEX_JOURNAL_PATH")
        if env_journal_path or os.environ.get("UNIBOT_EXAM_WORKSPACE_ROOT"):
            journal_path = resolve_tutor_index_journal_path()
        elif tutor_index_path is not None:
            journal_path = Path(index_path).expanduser().with_name("private_tutor_index_journal.jsonl")
        else:
            journal_path = resolve_tutor_index_journal_path()
    manifest_payload = read_private_manifest(manifest_path)
    records = [record for record in manifest_payload.get("records", []) if isinstance(record, dict)]
    tutor_records = tutor_usable_records(records)
    exam_scope = build_course_exam_scope(
        course_id,
        records=records,
        review_policy="local_private_tutor",
        public_safe=public_safe,
    )
    anchors = build_source_anchors(tutor_records)
    skill_index = build_skill_index(exam_scope, anchors)
    source_card_index = build_source_card_index(anchors)
    gaps = priority_coverage_gaps(skill_index)
    snapshot = build_index_snapshot(
        course_id=course_id,
        manifest_payload=manifest_payload,
        anchors=anchors,
        skill_index=skill_index,
        source_card_index=source_card_index,
        coverage_gaps=gaps,
    )

    build_result = {
        "status": "not_requested",
        "index_written": False,
        "journal_written": False,
        "index_hash": snapshot["index_hash"],
    }
    can_build = manifest_payload.get("status") == "ok" and bool(anchors)
    if operator_confirmed_tutor_index_build and can_build:
        build_result = write_private_tutor_index_snapshot(
            snapshot,
            tutor_index_path=index_path,
            journal_path=journal_path,
            public_safe=public_safe,
        )

    report = {
        "schema_version": TUTOR_INDEX_SCHEMA_VERSION,
        "artifact_type": "course_private_tutor_index_dry_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": tutor_index_status(
            manifest_payload=manifest_payload,
            anchor_count=len(anchors),
            confirmed=operator_confirmed_tutor_index_build,
            build_result=build_result,
        ),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Controlled private tutor-index harness. Default is dry-run. Confirmed builds write a local "
            "hash-only source-anchor index, never raw course text, never local paths, never automatic grading, "
            "never proctoring, never AI detection, and never exam deployment clearance."
        ),
        "private_manifest_summary": {
            "status": manifest_payload.get("status", "missing"),
            "record_count": manifest_payload.get("record_count", 0),
            "tutor_usable_record_count": len(tutor_records),
            "manifest_hash": manifest_payload.get("manifest_hash", ""),
            "private_manifest_path_returned": False,
        },
        "index_preview": {
            "anchor_count": len(anchors),
            "source_card_count": len(source_card_index),
            "indexed_skill_count": len([item for item in skill_index if item.get("anchor_count", 0) > 0]),
            "missing_skill_count": len([item for item in skill_index if item.get("anchor_count", 0) == 0]),
            "index_hash": snapshot["index_hash"],
            "anchors": anchors[:20],
            "anchors_truncated": len(anchors) > 20,
        },
        "exam_scope_preview": {
            "status": exam_scope.get("status", "unknown"),
            "material_summary": exam_scope.get("material_summary", {}),
            "skill_index": skill_index,
            "priority_coverage_gaps": gaps[:10],
        },
        "build_result": public_build_result(build_result),
        "operator_confirmed_tutor_index_build": operator_confirmed_tutor_index_build,
        "tutor_index_built": bool(build_result.get("index_written", False)),
        "tutor_index_journal_written": bool(build_result.get("journal_written", False)),
        "raw_text_returned": False,
        "local_paths_returned": False,
        "private_manifest_path_returned": False,
        "tutor_index_path_returned": False,
        "tutor_index_journal_path_returned": False,
        "next_actions": tutor_index_next_actions(
            manifest_payload=manifest_payload,
            anchor_count=len(anchors),
            confirmed=operator_confirmed_tutor_index_build,
            build_result=build_result,
            gaps=gaps,
        ),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def tutor_usable_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    usable = []
    for raw in records:
        record = normalize_material_record(raw)
        validation = validate_material_record(record)
        if validation["tutor_usable"]:
            usable.append(record.to_public_summary_dict())
    return usable


def build_source_anchors(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anchors = []
    for raw in records:
        record = normalize_material_record(raw)
        skill_tags = canonical_skill_tags(list(record.skill_tags))
        seed = {
            "material_id": record.material_id,
            "sha256": record.sha256,
            "skill_tags": skill_tags,
            "source_card_ids": list(record.source_card_ids),
            "page_or_timestamp": record.page_or_timestamp,
        }
        anchor_hash = sha256_text(json.dumps(seed, sort_keys=True, ensure_ascii=False))
        anchors.append(
            {
                "anchor_id": f"src_{anchor_hash[:20]}",
                "retrieval_anchor_hash": anchor_hash,
                "material_id": record.material_id,
                "title": record.title,
                "source_kind": record.source_kind,
                "skill_tags": skill_tags,
                "source_card_ids": list(record.source_card_ids),
                "page_or_timestamp": record.page_or_timestamp,
                "sha256": record.sha256,
                "review_status": record.review_status,
                "extraction_status": record.extraction_status,
                "retrieval_policy": "metadata_anchor_only_no_raw_text",
                "raw_text_stored": False,
                "local_path_stored": False,
            }
        )
    return sorted(anchors, key=lambda item: (item["material_id"], item["anchor_id"]))


def canonical_skill_tags(skill_tags: list[str]) -> list[str]:
    canonical: list[str] = []
    for raw_tag in skill_tags or ["general_python"]:
        tag = str(raw_tag).strip()
        if not tag:
            continue
        for candidate in [tag, SKILL_TAG_ALIASES.get(tag, "")]:
            if candidate and candidate not in canonical:
                canonical.append(candidate)
    return canonical or ["python_lists"]


def build_skill_index(exam_scope: dict[str, Any], anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_skill: dict[str, list[dict[str, Any]]] = {}
    for anchor in anchors:
        for tag in anchor.get("skill_tags", []) or []:
            by_skill.setdefault(str(tag), []).append(anchor)

    skill_index = []
    for skill in exam_scope.get("skills", []):
        if not isinstance(skill, dict):
            continue
        tag = str(skill.get("skill_tag", ""))
        matched = by_skill.get(tag, [])
        readiness = "retrieval_anchor_ready" if matched else (
            "needs_review_or_index_anchor" if skill.get("material_count", 0) else "no_course_anchor"
        )
        skill_index.append(
            {
                "skill_tag": tag,
                "title": skill.get("title", ""),
                "readiness": readiness,
                "anchor_count": len(matched),
                "material_count": skill.get("material_count", 0),
                "tutor_usable_count": skill.get("tutor_usable_count", 0),
                "source_anchor_ids": [anchor["anchor_id"] for anchor in matched[:8]],
                "source_card_ids": sorted(
                    {
                        str(card_id)
                        for anchor in matched
                        for card_id in anchor.get("source_card_ids", []) or []
                    }
                )[:8] or list(skill.get("source_card_ids", []) or [])[:8],
                "allowed_exam_help": list(skill.get("allowed_exam_help", []) or []),
                "blocked_exam_help": list(skill.get("blocked_exam_help", []) or []),
            }
        )
    return skill_index


def build_source_card_index(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_card: dict[str, list[str]] = {}
    for anchor in anchors:
        for card_id in anchor.get("source_card_ids", []) or []:
            by_card.setdefault(str(card_id), []).append(anchor["anchor_id"])
    return [
        {
            "source_card_id": card_id,
            "anchor_count": len(anchor_ids),
            "source_anchor_ids": sorted(anchor_ids)[:8],
        }
        for card_id, anchor_ids in sorted(by_card.items())
    ]


def priority_coverage_gaps(skill_index: list[dict[str, Any]]) -> list[dict[str, Any]]:
    core_priority = {
        "colab_jupyter",
        "python_lists",
        "control_flow",
        "numpy",
        "pandas",
        "boxplots",
        "statistics_pingouin",
        "debugging",
    }
    gaps = []
    for skill in skill_index:
        if skill.get("anchor_count", 0) > 0:
            continue
        tag = str(skill.get("skill_tag", ""))
        gaps.append(
            {
                "skill_tag": tag,
                "title": skill.get("title", ""),
                "priority": "high" if tag in core_priority else "medium",
                "current_readiness": skill.get("readiness", "unknown"),
                "next_review_need": (
                    "review an already extracted course source for this skill"
                    if skill.get("material_count", 0)
                    else "extract or map one approved course source for this skill"
                ),
            }
        )
    return sorted(gaps, key=lambda item: (0 if item["priority"] == "high" else 1, item["skill_tag"]))


def build_index_snapshot(
    *,
    course_id: str,
    manifest_payload: dict[str, Any],
    anchors: list[dict[str, Any]],
    skill_index: list[dict[str, Any]],
    source_card_index: list[dict[str, Any]],
    coverage_gaps: list[dict[str, Any]],
) -> dict[str, Any]:
    snapshot = {
        "schema_version": TUTOR_INDEX_SCHEMA_VERSION,
        "artifact_type": "course_private_tutor_index_snapshot",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "exam_deployment_status": "not_cleared",
        "manifest_hash": manifest_payload.get("manifest_hash", ""),
        "coverage_summary": {
            "anchor_count": len(anchors),
            "skill_count": len(skill_index),
            "indexed_skill_count": len([item for item in skill_index if item.get("anchor_count", 0) > 0]),
            "missing_skill_count": len([item for item in skill_index if item.get("anchor_count", 0) == 0]),
            "source_card_count": len(source_card_index),
        },
        "source_anchors": anchors,
        "skill_index": skill_index,
        "source_card_index": source_card_index,
        "priority_coverage_gaps": coverage_gaps,
        "storage_policy": "hash-only local tutor source-anchor index; no raw text, no local paths, no private artifact references",
    }
    snapshot["index_hash"] = sha256_text(json.dumps(snapshot, sort_keys=True, ensure_ascii=False))
    return snapshot


def write_private_tutor_index_snapshot(
    snapshot: dict[str, Any],
    *,
    tutor_index_path: Path,
    journal_path: Path,
    public_safe: bool,
) -> dict[str, Any]:
    scan = scan_text(json.dumps(snapshot, ensure_ascii=False), "private-tutor-index-snapshot")
    if public_safe and scan["status"] != "pass":
        return {
            "status": "blocked_public_safety",
            "index_written": False,
            "journal_written": False,
            "index_hash": snapshot.get("index_hash", ""),
            "public_safety_findings": scan["findings"],
        }

    tutor_index_path.parent.mkdir(parents=True, exist_ok=True)
    tutor_index_path.write_text(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    journal_record = {
        "schema_version": TUTOR_INDEX_SCHEMA_VERSION,
        "artifact_type": "course_private_tutor_index_journal_record",
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "accepted",
        "event": {
            "event_type": "private_tutor_index_snapshot_built",
            "index_hash": snapshot.get("index_hash", ""),
            "manifest_hash": snapshot.get("manifest_hash", ""),
            "anchor_count": snapshot.get("coverage_summary", {}).get("anchor_count", 0),
            "indexed_skill_count": snapshot.get("coverage_summary", {}).get("indexed_skill_count", 0),
            "exam_deployment_status": "not_cleared",
            "index_path_stored": False,
            "journal_path_stored": False,
            "raw_text_stored": False,
            "local_path_stored": False,
        },
        "storage_policy": "hash-only tutor-index journal; no local paths, raw text, or private artifact references",
    }
    journal_record["event"]["validation_hash"] = sha256_text(
        json.dumps(journal_record["event"], sort_keys=True, ensure_ascii=False)
    )
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(journal_record, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "private_tutor_index_built",
        "index_written": True,
        "journal_written": True,
        "index_hash": snapshot.get("index_hash", ""),
        "anchor_count": snapshot.get("coverage_summary", {}).get("anchor_count", 0),
        "indexed_skill_count": snapshot.get("coverage_summary", {}).get("indexed_skill_count", 0),
        "tutor_index_path_returned": False,
        "journal_path_returned": False,
    }


def tutor_index_status(
    *,
    manifest_payload: dict[str, Any],
    anchor_count: int,
    confirmed: bool,
    build_result: dict[str, Any],
) -> str:
    if confirmed and build_result.get("status") in {"private_tutor_index_built", "blocked_public_safety"}:
        return str(build_result.get("status"))
    if manifest_payload.get("status") == "missing":
        return "waiting_for_private_manifest_apply"
    if manifest_payload.get("status") != "ok":
        return "blocked_unreadable_private_manifest"
    if anchor_count == 0:
        return "waiting_for_tutor_usable_manifest_records"
    return "tutor_index_dry_run_ready"


def public_build_result(build_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": build_result.get("status", "not_requested"),
        "index_written": bool(build_result.get("index_written", False)),
        "journal_written": bool(build_result.get("journal_written", False)),
        "index_hash": build_result.get("index_hash", ""),
        "anchor_count": build_result.get("anchor_count", 0),
        "indexed_skill_count": build_result.get("indexed_skill_count", 0),
        "tutor_index_path_returned": False,
        "journal_path_returned": False,
    }


def tutor_index_next_actions(
    *,
    manifest_payload: dict[str, Any],
    anchor_count: int,
    confirmed: bool,
    build_result: dict[str, Any],
    gaps: list[dict[str, Any]],
) -> list[str]:
    if manifest_payload.get("status") == "missing":
        return [
            "Apply reviewed private material metadata with the private manifest apply harness first.",
            "Keep the default tutor-index step in dry-run until the operator explicitly confirms the build.",
        ]
    if manifest_payload.get("status") != "ok":
        return ["Repair or recreate the private material manifest; no tutor index is built from unreadable metadata."]
    if anchor_count == 0:
        return ["Review at least one extracted/captioned course source for private tutor use before building an index."]
    actions = []
    if not confirmed:
        actions.append("Review the anchor preview and coverage gaps, then set operator_confirmed_tutor_index_build only if the dry-run is acceptable.")
    elif build_result.get("status") == "private_tutor_index_built":
        actions.append("Use the hash-only index snapshot for the next Tutor/RAG dry-run and keep raw course text local.")
    if gaps:
        actions.append(f"Prioritize the next course-material gap: {gaps[0]['skill_tag']} ({gaps[0]['next_review_need']}).")
    actions.append("Reminder: real exam authority clearance stays a real-world follow-up; UniBot remains not_cleared.")
    return actions


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "private-tutor-index-dry-run")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
