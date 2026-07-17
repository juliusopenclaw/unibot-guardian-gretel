from __future__ import annotations

import re
from collections import OrderedDict
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable


FILE_SCHEME_PATTERN = re.escape("file:" + "//")
LOCAL_PATH_PATTERN = "|".join(
    [
        r"/(?:Users|users)/",
        r"/home/[A-Za-z0-9._-]+/",
        r"/(?:private/)?var/folders/[A-Za-z0-9._/-]+",
        r"[A-Za-z]:\\(?:Users|users)\\",
        FILE_SCHEME_PATTERN,
    ]
)
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
    ("local_path", rf"(?:{LOCAL_PATH_PATTERN})"),
    ("secret_assignment", r"\b(?:api[_-]?key|token|password|passwd|secret)\b\s*[:=]\s*[^\s]+"),
    ("private_course_material_reference", rf"\b(?:{PRIVATE_COURSE_PATH_PATTERN})"),
    ("private_project_marker", rf"\b(?:{PRIVATE_PROJECT_MARKER_PATTERN})\b"),
    ("raw_external_ai_transcript", r"\b(?:RAW_EXTERNAL_AI_OUTPUT|raw_external_ai_output|gemini_raw_response)\b\s*[:=]"),
    (
        "personal_health_or_accommodation_record",
        r"\b(?:meine|my|diagnose|attest|medikation|arztbrief|nachteilsausgleich)\b\s*[:=]\s*[^\n]+",
    ),
]

_COMPILED_PUBLIC_SAFETY_PATTERNS = tuple(
    (finding_type, re.compile(pattern, re.IGNORECASE))
    for finding_type, pattern in PUBLIC_SAFETY_PATTERNS
)
# These are necessary markers, not heuristic exclusions: a pattern is skipped
# only when its own syntax cannot possibly match the payload.
_PUBLIC_SAFETY_PREFILTERS = (
    ("@",),
    ("tel", "phone", "telefon", "mobil", "mobile"),
    ("/", "\\", "file:"),
    ("api", "key", "token", "password", "passwd", "secret"),
    ("private_course", "course_materials", "shared_uni"),
    ("f" + "m", "ver" + "-sacrum", "ver" + " sacrum", "exam" + "_workspace"),
    ("raw_external_ai_output", "gemini_raw_response"),
    ("meine", "my", "diagnose", "attest", "medikation", "arztbrief", "nachteilsausgleich"),
)
_SCAN_CACHE_MAX_ENTRIES = 512
_SCAN_CACHE_MAX_TEXT_CHARS = 1_048_576
_SCAN_CACHE: OrderedDict[tuple[int, bytes], tuple[tuple[str, int, int, str], ...]] = OrderedDict()


def scan_text(text: str, source_name: str = "inline") -> dict[str, Any]:
    payload = text or ""
    cache_key = (len(payload), sha256(payload.encode("utf-8")).digest())
    cached_findings = _SCAN_CACHE.get(cache_key) if len(payload) <= _SCAN_CACHE_MAX_TEXT_CHARS else None
    if cached_findings is None:
        findings_without_source: list[tuple[str, int, int, str]] = []
        folded_payload = payload.casefold()
        for (finding_type, pattern), prefilter_tokens in zip(
            _COMPILED_PUBLIC_SAFETY_PATTERNS,
            _PUBLIC_SAFETY_PREFILTERS,
        ):
            if not any(token in folded_payload for token in prefilter_tokens):
                continue
            for match in pattern.finditer(payload):
                findings_without_source.append(
                    (
                        finding_type,
                        match.start(),
                        match.end(),
                        redact_preview(match.group(0)),
                    )
                )
        cached_findings = tuple(findings_without_source)
        if len(payload) <= _SCAN_CACHE_MAX_TEXT_CHARS:
            _SCAN_CACHE[cache_key] = cached_findings
            _SCAN_CACHE.move_to_end(cache_key)
            if len(_SCAN_CACHE) > _SCAN_CACHE_MAX_ENTRIES:
                _SCAN_CACHE.popitem(last=False)
    findings = [
        {
            "source": source_name,
            "type": finding_type,
            "start": start,
            "end": end,
            "preview": preview,
        }
        for finding_type, start, end, preview in cached_findings
    ]
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
