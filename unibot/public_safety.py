from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable


FILE_SCHEME_PATTERN = re.escape("file:" + "//")
PRIVATE_COURSE_PATH_PATTERN = "|".join(
    re.escape(path)
    for path in [
        "knowledge/private_course" + "_materials/",
        "private_course" + "_materials/",
        "shared_uni" + "_folder/",
    ]
)

PRIVATE_PROJECT_MARKER_PATTERN = "|".join(
    re.escape(marker)
    for marker in [
        "F" + "M",
        "Ver-" + "Sacrum",
        "Ver " + "Sacrum",
        "knowledge/exam" + "_workspace",
        "knowledge\\exam" + "_workspace",
    ]
)

PUBLIC_SAFETY_PATTERNS = [
    ("email_address", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("phone_number", r"\b(?:tel|phone|telefon|mobil|mobile)\s*[:=]?\s*(?:\+?\d[\d\s()./-]{7,}\d)"),
    ("local_path", rf"(?:/(?:Users|users)/|[A-Za-z]:\\(?:Users|users)\\|{FILE_SCHEME_PATTERN})"),
    ("secret_assignment", r"\b(?:api[_-]?key|token|password|passwd|secret)\b\s*[:=]\s*[^\s]+"),
    ("private_course_material_reference", rf"\b(?:{PRIVATE_COURSE_PATH_PATTERN})"),
    ("private_project_marker", rf"\b(?:{PRIVATE_PROJECT_MARKER_PATTERN})\b"),
    ("raw_external_ai_transcript", r"\b(?:RAW_EXTERNAL_AI_OUTPUT|raw_external_ai_output|gemini_raw_response)\b\s*[:=]"),
    (
        "personal_health_or_accommodation_record",
        r"\b(?:meine|my|diagnose|attest|medikation|arztbrief|nachteilsausgleich)\b\s*[:=]\s*[^\n]+",
    ),
]


def scan_text(text: str, source_name: str = "inline") -> dict[str, Any]:
    findings = []
    payload = text or ""
    for finding_type, pattern in PUBLIC_SAFETY_PATTERNS:
        for match in re.finditer(pattern, payload, re.IGNORECASE):
            findings.append(
                {
                    "source": source_name,
                    "type": finding_type,
                    "start": match.start(),
                    "end": match.end(),
                    "preview": redact_preview(match.group(0)),
                }
            )
    return {
        "status": "blocked" if findings else "pass",
        "finding_count": len(findings),
        "findings": findings,
        "policy": "public release must not include private data, raw AI transcripts, local paths, or private course material references",
    }


def scan_public_files(paths: Iterable[str | Path]) -> dict[str, Any]:
    all_findings = []
    scanned = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            all_findings.append(
                {
                    "source": str(path),
                    "type": "missing_file",
                    "start": 0,
                    "end": 0,
                    "preview": "missing",
                }
            )
            continue
        text = path.read_text(encoding="utf-8")
        scanned.append(str(path))
        result = scan_text(text, str(path))
        all_findings.extend(result["findings"])
    return {
        "status": "blocked" if all_findings else "pass",
        "scanned_count": len(scanned),
        "finding_count": len(all_findings),
        "findings": all_findings,
    }


def redact_preview(value: str) -> str:
    stripped = value.strip().replace("\n", " ")
    if len(stripped) <= 8:
        return "***"
    return f"{stripped[:3]}***{stripped[-3:]}"
