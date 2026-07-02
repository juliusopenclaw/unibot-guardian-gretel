from __future__ import annotations

import json
import re
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from .course_tutor import DEFAULT_COURSE_ID, course_material_root, record_from_path, safe_course_id
from .extraction_decision_context import (
    decision_context_authorizes,
    public_decision_context_view,
    resolve_extraction_decision_context,
)
from .extraction import extraction_job, job_type_for_record
from .extraction_receipt_journal import append_extraction_receipt_record
from .materials import sha256_text
from .public_safety import scan_text


PRIVATE_EXTRACTION_RUNNER_SCHEMA_VERSION = "unibot-private-extraction-runner-v1"
SUPPORTED_SUFFIXES = {".docx", ".pdf", ".pptx"}
DEFAULT_PRIVATE_OUTPUT_DIR = Path.home() / ".unibot_guardian" / "private_extractions"


def run_private_extraction_batch(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    decision_record: dict[str, Any] | None = None,
    decision_record_journal_path: str | Path | None = None,
    receipt_journal_path: str | Path | None = None,
    private_output_dir: str | Path | None = None,
    max_jobs: int = 8,
    job_types: list[str] | None = None,
    job_ids: list[str] | None = None,
    human_review_status: str = "pending_review",
    public_safe: bool = True,
) -> dict[str, Any]:
    selected_types = {str(item) for item in (job_types or ["ocr"]) if str(item)}
    validation = resolve_extraction_decision_context(
        decision_record=decision_record,
        decision_record_journal_path=decision_record_journal_path,
        requested_job_types=selected_types,
    )
    authorized = decision_context_authorizes(validation)
    if not authorized:
        report = base_report(
            course_id,
            status="blocked_until_valid_rights_privacy_decision",
            validation=validation,
        )
        attach_public_scan(report, public_safe=public_safe)
        return report

    root = course_material_root(course_id, base_path=base_path)
    jobs = private_extraction_jobs(
        course_id,
        root=root,
        max_files=max_files,
        review_policy=review_policy,
        rights_hash=str(validation.get("rights_decision_reference_hash", "")),
    )
    supported = [
        item for item in jobs
        if item["job"].get("job_type") in selected_types and item["path"].suffix.lower() in SUPPORTED_SUFFIXES
    ]
    selected_job_ids = [str(item) for item in (job_ids or []) if str(item)]
    if selected_job_ids:
        allowed_job_ids = set(selected_job_ids)
        order = {job_id: index for index, job_id in enumerate(selected_job_ids)}
        supported = [item for item in supported if str(item["job"].get("job_id", "")) in allowed_job_ids]
        supported.sort(key=lambda item: order.get(str(item["job"].get("job_id", "")), len(order)))
    selected = supported[: max(0, int(max_jobs or 0))]
    output_dir = Path(private_output_dir).expanduser() if private_output_dir else DEFAULT_PRIVATE_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    receipts: list[dict[str, Any]] = []
    journal_results: list[dict[str, Any]] = []
    artifact_map_rows: list[dict[str, Any]] = []
    adapter_counts: dict[str, int] = {}
    failures: list[dict[str, Any]] = []

    for item in selected:
        path = item["path"]
        job = item["job"]
        adapter = adapter_for_path(path)
        adapter_counts[adapter] = adapter_counts.get(adapter, 0) + 1
        extraction = extract_text_from_supported_file(path)
        artifact_id = sha256_text(f"{job['job_id']}:{path.name}:{datetime.now(timezone.utc).isoformat()}")[:24]
        artifact_path = output_dir / f"{artifact_id}.txt"
        if extraction["status"] == "ok" and extraction["text"]:
            text = normalize_extracted_text(str(extraction["text"]))
            artifact_path.write_text(text, encoding="utf-8")
            raw_text_sha = sha256_text(text)
            receipt = {
                "job_id": job["job_id"],
                "material_id": job["material_id"],
                "job_type": job["job_type"],
                "extraction_status": "extracted_private",
                "raw_text_sha256": raw_text_sha,
                "extracted_text_char_count": len(text),
                "private_artifact_reference": f"local-private-artifact:{artifact_id}",
                "human_review_status": human_review_status,
                "decision_reference_hash": str(validation.get("rights_decision_reference_hash", "")),
            }
            artifact_map_rows.append(
                {
                    "job_id": job["job_id"],
                    "material_id": job["material_id"],
                    "artifact_path": str(artifact_path),
                    "source_path": str(path),
                    "raw_text_sha256": raw_text_sha,
                    "adapter": adapter,
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
                "private_artifact_reference": f"local-private-artifact-failed:{artifact_id}",
                "human_review_status": "pending_review",
                "decision_reference_hash": str(validation.get("rights_decision_reference_hash", "")),
            }
            failures.append(
                {
                    "job_id": job["job_id"],
                    "material_id": job["material_id"],
                    "adapter": adapter,
                    "reason": extraction.get("reason", "unknown"),
                }
            )
        receipts.append(receipt)
        if receipt_journal_path:
            journal_results.append(
                append_extraction_receipt_record(
                    receipt,
                    decision_record=decision_record if validation.get("decision_record_source") == "inline_decision_record" else None,
                    decision_reference_hash=str(validation.get("rights_decision_reference_hash", "")),
                    path=receipt_journal_path,
                )
            )

    map_path = output_dir / "private_artifact_map.jsonl"
    if artifact_map_rows:
        with map_path.open("a", encoding="utf-8") as handle:
            for row in artifact_map_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    stored = [item for item in journal_results if item.get("status") == "stored"]
    blocked_journal = [item for item in journal_results if item.get("status") != "stored"]
    report = {
        "schema_version": PRIVATE_EXTRACTION_RUNNER_SCHEMA_VERSION,
        "artifact_type": "course_private_extraction_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": private_run_status(selected, failures, blocked_journal),
        "exam_deployment_status": "not_cleared",
        "execution_boundary": (
            "Local private extraction runner for text containers only. It writes raw extracted text only to "
            "private local artifacts and returns public-safe receipt metadata, hashes, counts, and adapter status."
        ),
        "decision_validation": public_decision_context_view(validation),
        "decision_record_source": validation.get("decision_record_source", "missing_decision_record"),
        "decision_record_journal_used": validation.get("decision_record_source") == "external_decision_record_journal",
        "raw_decision_record_returned": False,
        "counts": {
            "candidate_job_count": len(jobs),
            "supported_candidate_count": len(supported),
            "job_id_filter_count": len(selected_job_ids),
            "selected_job_count": len(selected),
            "extracted_private_count": len([receipt for receipt in receipts if receipt["extraction_status"] == "extracted_private"]),
            "failed_extraction_count": len(failures),
            "receipt_count": len(receipts),
            "stored_receipt_count": len(stored),
            "blocked_journal_append_count": len(blocked_journal),
            "artifact_map_row_count": len(artifact_map_rows),
        },
        "adapter_counts": dict(sorted(adapter_counts.items())),
        "supported_suffixes": sorted(SUPPORTED_SUFFIXES),
        "receipt_journal_used": bool(receipt_journal_path),
        "private_artifact_map_written": bool(artifact_map_rows),
        "private_artifact_map_hash": sha256_text(str(map_path)) if artifact_map_rows else "",
        "raw_text_returned": False,
        "local_paths_returned": False,
        "receipts": [public_receipt_view(receipt) for receipt in receipts],
        "failures": failures[:20],
        "post_run_handoff": {
            "receipt_journal_ready": bool(stored),
            "human_review_required": True,
            "next_routes": [
                "/api/unibot/course/extraction-review/apply-plan",
                "/api/unibot/course/extraction-progress-report",
                "/api/unibot/course/extraction-manifest-update-plan",
                "/api/unibot/course/tutor-coverage-plan",
            ],
            "public_output_policy": "handoff exposes route names and counts only; receipt journals and private artifact maps stay local",
        },
        "next_actions": private_run_next_actions(receipts, supported, jobs, bool(receipt_journal_path)),
    }
    attach_public_scan(report, public_safe=public_safe)
    return report


def private_extraction_jobs(
    course_id: str,
    *,
    root: Path,
    max_files: int,
    review_policy: str,
    rights_hash: str,
) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    files = sorted(path for path in root.rglob("*") if path.is_file())[: max(1, int(max_files or 1))]
    jobs: list[dict[str, Any]] = []
    for path in files:
        record = record_from_path(path, root=root, course_id=course_id, review_policy=review_policy)
        notes = str(record.get("notes", ""))
        if record.get("review_status") == "blocked" or "quarantined_solution_or_exam" in notes:
            continue
        if record.get("extraction_status") in {"text_extracted", "captions_available"}:
            continue
        job_type = job_type_for_record(record)
        if not job_type:
            continue
        jobs.append(
            {
                "job": extraction_job(record, job_type=job_type, authorized=True, rights_hash=rights_hash),
                "path": path,
            }
        )
    return jobs


def extract_text_from_supported_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".docx":
            return {"status": "ok", "text": extract_docx_text(path)}
        if suffix == ".pdf":
            text = extract_pdf_text(path)
            if text:
                return {"status": "ok", "text": text}
            return {"status": "failed", "reason": "no_text_objects_found_pdf_may_require_ocr"}
        if suffix == ".pptx":
            return {"status": "ok", "text": extract_pptx_text(path)}
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError, zlib.error) as exc:
        return {"status": "failed", "reason": exc.__class__.__name__}
    return {"status": "unsupported", "reason": f"unsupported_suffix:{suffix}"}


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        chunks: list[str] = []
        for name in ["word/document.xml", *sorted(n for n in archive.namelist() if n.startswith("word/header") or n.startswith("word/footer"))]:
            if name not in archive.namelist():
                continue
            chunks.extend(xml_text_nodes(archive.read(name)))
    return "\n".join(chunks)


def extract_pptx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        names = [
            name for name in sorted(archive.namelist())
            if (name.startswith("ppt/slides/slide") or name.startswith("ppt/notesSlides/notesSlide"))
            and name.endswith(".xml")
        ]
        chunks: list[str] = []
        for name in names:
            chunks.extend(xml_text_nodes(archive.read(name)))
    return "\n".join(chunks)


def extract_pdf_text(path: Path) -> str:
    data = path.read_bytes()
    chunks: list[str] = []
    for stream in pdf_stream_payloads(data):
        chunks.extend(pdf_text_operands(stream))
    if not chunks:
        chunks.extend(pdf_literal_strings(data[:2_000_000]))
    return "\n".join(chunks)


def pdf_stream_payloads(data: bytes) -> list[bytes]:
    payloads: list[bytes] = []
    for match in re.finditer(rb"<<(?P<dict>.*?)>>\s*stream\r?\n(?P<body>.*?)\r?\nendstream", data, re.S):
        stream_dict = match.group("dict")
        body = match.group("body")
        if b"FlateDecode" in stream_dict:
            try:
                payloads.append(zlib.decompress(body))
            except zlib.error:
                payloads.append(body)
        else:
            payloads.append(body)
    return payloads


def pdf_text_operands(stream: bytes) -> list[str]:
    text_segments: list[str] = []
    for literal in re.findall(rb"(\((?:\\.|[^\\)])*\))\s*(?:Tj|')", stream):
        segment = decode_pdf_literal(literal[1:-1])
        if usable_text_segment(segment):
            text_segments.append(segment)
    for array_body in re.findall(rb"\[(.*?)\]\s*TJ", stream, re.S):
        parts = [decode_pdf_literal(item[1:-1]) for item in re.findall(rb"\((?:\\.|[^\\)])*\)", array_body)]
        segment = "".join(parts)
        if usable_text_segment(segment):
            text_segments.append(segment)
    for hex_text in re.findall(rb"<([0-9A-Fa-f\s]{4,})>\s*Tj", stream):
        segment = decode_pdf_hex(hex_text)
        if usable_text_segment(segment):
            text_segments.append(segment)
    return text_segments


def pdf_literal_strings(data: bytes) -> list[str]:
    segments: list[str] = []
    for literal in re.findall(rb"\((?:\\.|[^\\)]){4,}\)", data):
        segment = decode_pdf_literal(literal[1:-1])
        if usable_text_segment(segment):
            segments.append(segment)
    return segments[:200]


def decode_pdf_literal(raw: bytes) -> str:
    replacements = {
        b"\\n": b"\n",
        b"\\r": b"\r",
        b"\\t": b"\t",
        b"\\b": b"\b",
        b"\\f": b"\f",
        b"\\(": b"(",
        b"\\)": b")",
        b"\\\\": b"\\",
    }
    value = raw
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(rb"\\([0-7]{1,3})", lambda m: bytes([int(m.group(1), 8) & 0xFF]), value)
    return value.decode("utf-8", errors="replace")


def decode_pdf_hex(raw: bytes) -> str:
    cleaned = re.sub(rb"\s+", b"", raw)
    if len(cleaned) % 2:
        cleaned += b"0"
    try:
        data = bytes.fromhex(cleaned.decode("ascii"))
    except ValueError:
        return ""
    for encoding in ("utf-16-be", "utf-8", "latin-1"):
        text = data.decode(encoding, errors="replace").strip("\ufeff")
        if usable_text_segment(text):
            return text
    return ""


def usable_text_segment(text: str) -> bool:
    stripped = re.sub(r"\s+", " ", text).strip()
    if len(stripped) < 3:
        return False
    printable = sum(1 for char in stripped if char.isprintable())
    alpha = sum(1 for char in stripped if char.isalpha())
    return printable / max(1, len(stripped)) > 0.75 and alpha >= 2


def xml_text_nodes(raw_xml: bytes) -> list[str]:
    root = ElementTree.fromstring(raw_xml)
    texts = []
    for node in root.iter():
        if node.tag.endswith("}t") and node.text:
            texts.append(node.text)
    return texts


def normalize_extracted_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def adapter_for_path(path: Path) -> str:
    suffix = path.suffix.lower().strip(".") or "unknown"
    return f"zip_xml_{suffix}"


def public_receipt_view(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": receipt.get("job_id", ""),
        "material_id": receipt.get("material_id", ""),
        "job_type": receipt.get("job_type", ""),
        "extraction_status": receipt.get("extraction_status", ""),
        "human_review_status": receipt.get("human_review_status", ""),
        "raw_text_sha256": receipt.get("raw_text_sha256", ""),
        "extracted_text_char_count": receipt.get("extracted_text_char_count", 0),
        "decision_reference_hash": receipt.get("decision_reference_hash", ""),
        "raw_text_stored": False,
        "local_path_stored": False,
    }


def private_run_status(
    selected: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    blocked_journal: list[dict[str, Any]],
) -> str:
    if not selected:
        return "no_supported_private_extraction_jobs"
    if blocked_journal:
        return "blocked_receipt_journal_append"
    if failures:
        return "partial_private_extraction_run"
    return "private_extraction_receipts_ready_for_human_review"


def private_run_next_actions(
    receipts: list[dict[str, Any]],
    supported: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
    journal_used: bool,
) -> list[str]:
    if not jobs:
        return ["No extraction jobs are currently queued."]
    if not supported:
        return ["No DOCX/PDF/PPTX text-container jobs are supported by this local runner; use manual OCR/transcription or another approved local adapter."]
    actions = []
    if receipts and journal_used:
        actions.append("Open the private artifact map locally and perform human review before marking receipts reviewed_for_private_tutor.")
    elif receipts:
        actions.append("Append generated receipts to the extraction receipt journal before running progress and completion reports.")
    actions.extend(
        [
            "Keep raw extracted text local; use only hashes/counts in public reports.",
            "Use a separate approved local adapter for image-only PDFs and videos.",
        ]
    )
    return actions


def base_report(course_id: str, *, status: str, validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": PRIVATE_EXTRACTION_RUNNER_SCHEMA_VERSION,
        "artifact_type": "course_private_extraction_run",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": status,
        "exam_deployment_status": "not_cleared",
        "decision_validation": public_decision_context_view(validation),
        "decision_record_source": validation.get("decision_record_source", "missing_decision_record"),
        "decision_record_journal_used": validation.get("decision_record_source") == "external_decision_record_journal",
        "raw_decision_record_returned": False,
        "counts": {
            "candidate_job_count": 0,
            "supported_candidate_count": 0,
            "selected_job_count": 0,
            "extracted_private_count": 0,
            "receipt_count": 0,
            "stored_receipt_count": 0,
        },
        "raw_text_returned": False,
        "local_paths_returned": False,
        "next_actions": ["Provide a valid local extraction decision record before running private extraction."],
    }


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "private-extraction-run")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan["findings"]
