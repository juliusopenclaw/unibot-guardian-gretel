from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .course_tutor import DEFAULT_COURSE_ID, course_material_root, safe_course_id
from .extraction_decision import validate_extraction_decision_record
from .extraction_receipt_journal import append_extraction_receipt_record
from .materials import sha256_text
from .private_extraction_runner import private_extraction_jobs, public_receipt_view
from .public_safety import scan_text


VIDEO_TRANSCRIPTION_RUNNER_SCHEMA_VERSION = "unibot-video-transcription-runner-v1"
VIDEO_SUFFIXES = {".mov", ".mp4", ".m4v", ".webm"}
SIDECAR_SUFFIXES = {".vtt", ".srt", ".txt", ".md"}
DEFAULT_PRIVATE_TRANSCRIPT_DIR = Path.home() / ".unibot_guardian" / "private_video_transcripts"


def run_video_transcription_batch(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    receipt_journal_path: str | Path | None = None,
    private_output_dir: str | Path | None = None,
    max_jobs: int = 8,
    human_review_status: str = "pending_review",
    public_safe: bool = True,
) -> dict[str, Any]:
    validation = validate_extraction_decision_record(decision_record or {})
    capabilities = video_transcription_capabilities()
    authorized = validation.get("status") == "ok_authorizes_local_extraction"
    if not authorized:
        report = base_video_report(
            course_id,
            status="blocked_until_valid_rights_privacy_decision",
            validation=validation,
            capabilities=capabilities,
        )
        attach_public_scan(report, public_safe=public_safe)
        return report

    root = course_material_root(course_id, base_path=base_path)
    jobs = [
        item for item in private_extraction_jobs(
            course_id,
            root=root,
            max_files=max_files,
            review_policy=review_policy,
            rights_hash=str(validation.get("rights_decision_reference_hash", "")),
        )
        if item["job"].get("job_type") == "transcription" and item["path"].suffix.lower() in VIDEO_SUFFIXES
    ]
    sidecar_jobs = []
    unsupported_jobs = []
    for item in jobs:
        sidecar = find_sidecar_transcript(item["path"])
        if sidecar:
            sidecar_jobs.append({**item, "sidecar_path": sidecar})
        else:
            unsupported_jobs.append(item)

    selected = sidecar_jobs[: max(0, int(max_jobs or 0))]
    output_dir = Path(private_output_dir).expanduser() if private_output_dir else DEFAULT_PRIVATE_TRANSCRIPT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    receipts: list[dict[str, Any]] = []
    journal_results: list[dict[str, Any]] = []
    artifact_map_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for item in selected:
        job = item["job"]
        sidecar_path = item["sidecar_path"]
        parsed = parse_sidecar_transcript(sidecar_path)
        artifact_id = sha256_text(f"{job['job_id']}:{sidecar_path.name}:{datetime.now(timezone.utc).isoformat()}")[:24]
        artifact_path = output_dir / f"{artifact_id}.txt"
        if parsed["status"] == "ok" and parsed["text"]:
            text = normalize_transcript_text(str(parsed["text"]))
            artifact_path.write_text(text, encoding="utf-8")
            raw_text_sha = sha256_text(text)
            receipt = {
                "job_id": job["job_id"],
                "material_id": job["material_id"],
                "job_type": job["job_type"],
                "extraction_status": "extracted_private",
                "raw_text_sha256": raw_text_sha,
                "extracted_text_char_count": len(text),
                "private_artifact_reference": f"local-private-video-transcript:{artifact_id}",
                "human_review_status": human_review_status,
                "decision_reference_hash": str(validation.get("rights_decision_reference_hash", "")),
            }
            artifact_map_rows.append(
                {
                    "job_id": job["job_id"],
                    "material_id": job["material_id"],
                    "artifact_path": str(artifact_path),
                    "video_source_path": str(item["path"]),
                    "sidecar_source_path": str(sidecar_path),
                    "raw_text_sha256": raw_text_sha,
                    "adapter": "sidecar_transcript",
                }
            )
        else:
            receipt = {
                "job_id": job["job_id"],
                "material_id": job["material_id"],
                "job_type": job["job_type"],
                "extraction_status": "failed",
                "raw_text_sha256": "",
                "extracted_text_char_count": 0,
                "private_artifact_reference": f"local-private-video-transcript-failed:{artifact_id}",
                "human_review_status": "pending_review",
                "decision_reference_hash": str(validation.get("rights_decision_reference_hash", "")),
            }
            failures.append(
                {
                    "job_id": job["job_id"],
                    "material_id": job["material_id"],
                    "adapter": "sidecar_transcript",
                    "reason": parsed.get("reason", "unknown"),
                }
            )
        receipts.append(receipt)
        if receipt_journal_path:
            journal_results.append(
                append_extraction_receipt_record(
                    receipt,
                    decision_record=decision_record,
                    path=receipt_journal_path,
                )
            )

    map_path = output_dir / "private_video_transcript_map.jsonl"
    if artifact_map_rows:
        with map_path.open("a", encoding="utf-8") as handle:
            for row in artifact_map_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    stored = [item for item in journal_results if item.get("status") == "stored"]
    blocked_journal = [item for item in journal_results if item.get("status") != "stored"]
    report = {
        "schema_version": VIDEO_TRANSCRIPTION_RUNNER_SCHEMA_VERSION,
        "artifact_type": "course_video_transcription_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": video_run_status(selected, failures, blocked_journal, unsupported_jobs, capabilities),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Local private video transcription harness. Current safe adapter ingests sidecar captions/transcripts only; "
            "full ASR stays blocked until an approved local adapter is available and a valid rights/privacy decision exists."
        ),
        "decision_validation": {
            "status": validation.get("status"),
            "rights_decision_reference_hash": validation.get("rights_decision_reference_hash", ""),
            "raw_decision_reference_stored": False,
        },
        "counts": {
            "candidate_video_job_count": len(jobs),
            "sidecar_candidate_count": len(sidecar_jobs),
            "selected_job_count": len(selected),
            "transcribed_private_count": len([receipt for receipt in receipts if receipt["extraction_status"] == "extracted_private"]),
            "failed_transcription_count": len(failures),
            "missing_adapter_count": len(unsupported_jobs),
            "receipt_count": len(receipts),
            "stored_receipt_count": len(stored),
            "blocked_journal_append_count": len(blocked_journal),
            "artifact_map_row_count": len(artifact_map_rows),
        },
        "adapter_capabilities": capabilities,
        "supported_video_suffixes": sorted(VIDEO_SUFFIXES),
        "supported_sidecar_suffixes": sorted(SIDECAR_SUFFIXES),
        "receipt_journal_used": bool(receipt_journal_path),
        "private_artifact_map_written": bool(artifact_map_rows),
        "private_artifact_map_hash": sha256_text(str(map_path)) if artifact_map_rows else "",
        "raw_text_returned": False,
        "local_paths_returned": False,
        "receipts": [public_receipt_view(receipt) for receipt in receipts],
        "failures": failures[:20],
        "next_actions": video_run_next_actions(
            receipts=receipts,
            sidecar_jobs=sidecar_jobs,
            unsupported_jobs=unsupported_jobs,
            capabilities=capabilities,
            journal_used=bool(receipt_journal_path),
        ),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def video_transcription_capabilities() -> dict[str, bool]:
    return {
        "sidecar_transcript": True,
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "whisper": bool(shutil.which("whisper")),
        "whisper_cpp": bool(shutil.which("whisper.cpp")),
        "mlx_whisper": bool(shutil.which("mlx_whisper")),
    }


def find_sidecar_transcript(video_path: Path) -> Path | None:
    candidates: list[Path] = []
    for suffix in SIDECAR_SUFFIXES:
        candidates.append(video_path.with_suffix(suffix))
    for folder_name in ("captions", "transcripts", "Transcripts", "Untertitel"):
        folder = video_path.parent / folder_name
        for suffix in SIDECAR_SUFFIXES:
            candidates.append(folder / f"{video_path.stem}{suffix}")
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def parse_sidecar_transcript(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"status": "failed", "reason": exc.__class__.__name__}
    suffix = path.suffix.lower()
    if suffix == ".vtt":
        text = parse_vtt(raw)
    elif suffix == ".srt":
        text = parse_srt(raw)
    elif suffix in {".txt", ".md"}:
        text = raw
    else:
        return {"status": "unsupported", "reason": f"unsupported_sidecar_suffix:{suffix}"}
    normalized = normalize_transcript_text(text)
    if not normalized:
        return {"status": "failed", "reason": "empty_sidecar_transcript"}
    return {"status": "ok", "text": normalized}


def parse_vtt(raw: str) -> str:
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.upper() == "WEBVTT" or stripped.startswith("NOTE"):
            continue
        if "-->" in stripped or re.fullmatch(r"\d+", stripped):
            continue
        lines.append(strip_caption_tags(stripped))
    return "\n".join(lines)


def parse_srt(raw: str) -> str:
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or re.fullmatch(r"\d+", stripped) or "-->" in stripped:
            continue
        lines.append(strip_caption_tags(stripped))
    return "\n".join(lines)


def strip_caption_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return text


def normalize_transcript_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    deduped: list[str] = []
    previous = ""
    for line in lines:
        if not line or line == previous:
            continue
        deduped.append(line)
        previous = line
    return "\n".join(deduped)


def video_run_status(
    selected: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    blocked_journal: list[dict[str, Any]],
    unsupported_jobs: list[dict[str, Any]],
    capabilities: dict[str, bool],
) -> str:
    adapter_available = any(capabilities.get(name) for name in ("ffmpeg", "whisper", "whisper_cpp", "mlx_whisper"))
    if not selected and unsupported_jobs and not adapter_available:
        return "no_video_transcription_adapter_available"
    if not selected:
        return "no_sidecar_video_transcription_jobs"
    if blocked_journal:
        return "blocked_receipt_journal_append"
    if failures:
        return "partial_video_transcription_run"
    return "sidecar_transcripts_ready_for_human_review"


def video_run_next_actions(
    *,
    receipts: list[dict[str, Any]],
    sidecar_jobs: list[dict[str, Any]],
    unsupported_jobs: list[dict[str, Any]],
    capabilities: dict[str, bool],
    journal_used: bool,
) -> list[str]:
    actions: list[str] = []
    if receipts and journal_used:
        actions.append("Review private transcript artifacts before marking receipts reviewed_for_private_tutor.")
    elif receipts:
        actions.append("Append generated transcript receipts to the extraction receipt journal.")
    if unsupported_jobs:
        if any(capabilities.get(name) for name in ("ffmpeg", "whisper", "whisper_cpp", "mlx_whisper")):
            actions.append("Connect the available local ASR adapter only after an approved adapter-specific runbook exists.")
        else:
            actions.append("Install or approve a local ASR adapter, or provide matching sidecar transcripts, before processing remaining videos.")
    if sidecar_jobs:
        actions.append("Keep sidecar transcript text local and expose only hashes/counts in public reports.")
    if not actions:
        actions.append("No queued video transcription jobs found.")
    return actions


def base_video_report(
    course_id: str,
    *,
    status: str,
    validation: dict[str, Any],
    capabilities: dict[str, bool],
) -> dict[str, Any]:
    return {
        "schema_version": VIDEO_TRANSCRIPTION_RUNNER_SCHEMA_VERSION,
        "artifact_type": "course_video_transcription_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": status,
        "exam_deployment_status": "not_cleared",
        "decision_validation": {
            "status": validation.get("status"),
            "issues": validation.get("issues", []),
            "rights_decision_reference_hash": validation.get("rights_decision_reference_hash", ""),
            "raw_decision_reference_stored": False,
        },
        "counts": {
            "candidate_video_job_count": 0,
            "sidecar_candidate_count": 0,
            "selected_job_count": 0,
            "transcribed_private_count": 0,
            "receipt_count": 0,
            "stored_receipt_count": 0,
        },
        "adapter_capabilities": capabilities,
        "raw_text_returned": False,
        "local_paths_returned": False,
        "next_actions": ["Provide a valid local extraction decision record before running video transcription."],
    }


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "video-transcription-run")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
