from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .materials import (
    CourseMaterialRecord,
    build_material_manifest,
    normalize_material_record,
    sha256_file,
    sha256_text,
    validate_material_record,
)
from .public_safety import scan_text


COURSE_TUTOR_SCHEMA_VERSION = "unibot-course-tutor-v1"
DEFAULT_COURSE_ID = "introduction-to-python-neuroscience-cologne"
ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "knowledge" / ("private_course" + "_materials")
COURSE_MATERIAL_ROOT_ENV = "UNIBOT_COURSE_MATERIAL_ROOT"
MAX_TEXT_CHARS = 6000


@dataclass(frozen=True)
class SkillProfile:
    skill_tag: str
    title: str
    objective: str
    exam_task_type: str
    keywords: tuple[str, ...]
    source_card_ids: tuple[str, ...]
    allowed_practice_help: tuple[str, ...]
    allowed_exam_help: tuple[str, ...]


SKILL_PROFILES = [
    SkillProfile(
        skill_tag="colab_jupyter",
        title="Jupyter and Colab workflow",
        objective="Notebook cells, runtime state, imports, outputs, and source checks can be explained before execution.",
        exam_task_type="Notebook operation, cell order, and runtime/debugging orientation.",
        keywords=("jupyter", "colab", "notebook", "runtime", "kernel", "zelle", "cell", "import"),
        source_card_ids=("jupyter-ai", "google-colab-gemini", "uoc-ki-faq"),
        allowed_practice_help=("tool walkthrough", "cell-state explanation", "source-card guided practice"),
        allowed_exam_help=("A0 Bedienung", "A1 Toolstelle", "A2 next own check"),
    ),
    SkillProfile(
        skill_tag="python_lists",
        title="Python basics, datatypes, lists, and dictionaries",
        objective="Core Python objects can be read, predicted, and tested in small steps.",
        exam_task_type="Trace an expression or choose a data container without full solution output.",
        keywords=("python", "list", "liste", "dictionary", "dict", "tuple", "string", "datatype", "index", "slice"),
        source_card_ids=("vanlehn-2011", "cs50-ai-2024"),
        allowed_practice_help=("concept explanation", "synthetic micro-example", "gap-based code scaffold"),
        allowed_exam_help=("A1 syntax source", "A2 prediction question"),
    ),
    SkillProfile(
        skill_tag="control_flow",
        title="Control flow, loops, and functions",
        objective="Conditions, loops, function inputs, return values, and side effects are made explicit.",
        exam_task_type="Describe a loop/function contract and predict the next step.",
        keywords=("if", "for", "while", "loop", "schleife", "function", "funktion", "return", "condition"),
        source_card_ids=("vanlehn-2011", "cs50-ai-2024"),
        allowed_practice_help=("pseudocode", "minimal test prompt", "gap-based scaffold"),
        allowed_exam_help=("A1 syntax source", "A2 contract question"),
    ),
    SkillProfile(
        skill_tag="numpy",
        title="NumPy arrays and numerical checks",
        objective="Arrays, shapes, indexing, and simple descriptive operations are separated from interpretation.",
        exam_task_type="Choose an array structure and predict shape/output before running code.",
        keywords=("numpy", "array", "shape", "mean", "std", "matrix", "broadcast", "numerical"),
        source_card_ids=("dfg-gwp", "vanlehn-2011"),
        allowed_practice_help=("shape explanation", "synthetic array example", "debugging question"),
        allowed_exam_help=("A1 source reference", "A2 shape prediction question"),
    ),
    SkillProfile(
        skill_tag="pandas",
        title="pandas DataFrames and CSV inspection",
        objective="Tables are loaded, inspected, and column choices are justified before analysis.",
        exam_task_type="Identify measurement/group columns and inspect data quality.",
        keywords=("pandas", "dataframe", "csv", "read_csv", "columns", "spalte", "groupby", "series"),
        source_card_ids=("dfg-gwp", "vanlehn-2011"),
        allowed_practice_help=("API source", "inspection sequence", "gap-based scaffold"),
        allowed_exam_help=("A1 API/source", "A2 column-choice question"),
    ),
    SkillProfile(
        skill_tag="boxplots",
        title="Matplotlib, seaborn, and boxplots",
        objective="Plots are built from justified data choices; interpretation remains the student's work.",
        exam_task_type="Select measurement, grouping, axis label, and interpretation boundary.",
        keywords=("boxplot", "box plot", "matplotlib", "seaborn", "plot", "visualisierung", "axis", "median"),
        source_card_ids=("dfg-gwp", "vanlehn-2011"),
        allowed_practice_help=("plot anatomy", "synthetic plotting scaffold", "interpretation-boundary prompt"),
        allowed_exam_help=("A1 plotting source", "A2 data/axis question"),
    ),
    SkillProfile(
        skill_tag="statistics_pingouin",
        title="Descriptive statistics and Pingouin/statistical tests",
        objective="Variables, assumptions, calculation, and interpretation are kept separate.",
        exam_task_type="Name hypothesis, variable, precondition, and cautious interpretation boundary.",
        keywords=("statistics", "statistik", "pingouin", "ttest", "anova", "correlation", "pvalue", "effect"),
        source_card_ids=("dfg-gwp", "vanlehn-2011"),
        allowed_practice_help=("term explanation", "assumption checklist", "source-card prompt"),
        allowed_exam_help=("A1 function/source", "A2 hypothesis/variable question"),
    ),
    SkillProfile(
        skill_tag="debugging",
        title="Debugging and traceback reading",
        objective="Error type, line, hypothesis, and smallest next diagnostic test are named before editing code.",
        exam_task_type="Read a traceback and propose the next own check, not a complete fix.",
        keywords=("debug", "debugging", "traceback", "error", "exception", "nameerror", "typeerror", "importerror"),
        source_card_ids=("vanlehn-2011", "cs50-ai-2024"),
        allowed_practice_help=("error explanation", "minimal diagnostic prompt", "source-card guided check"),
        allowed_exam_help=("A1 error type explanation", "A2 smallest-next-test question"),
    ),
    SkillProfile(
        skill_tag="machine_learning",
        title="Machine learning basics and applications",
        objective="Features, target, train/test split, evaluation, and limits are distinguished.",
        exam_task_type="Explain pipeline parts and data leakage risks without model-output overclaiming.",
        keywords=("machine", "learning", "ml", "features", "target", "train", "test", "model", "deep"),
        source_card_ids=("dfg-gwp", "eu-ai-act-2024"),
        allowed_practice_help=("pipeline explanation", "limitation checklist", "source-card guided task"),
        allowed_exam_help=("A1 source/term", "A2 target/feature question"),
    ),
]

SKILL_BY_TAG = {profile.skill_tag: profile for profile in SKILL_PROFILES}
SKILL_PITFALLS = {
    "colab_jupyter": (
        "Notebook state from earlier cells is mistaken for a documented result.",
        "Runtime resets are treated as code errors instead of environment state.",
        "External tool output is copied before a source or cell-state check.",
    ),
    "python_lists": (
        "Index positions and list length are mixed up.",
        "A printed representation is mistaken for the underlying datatype.",
        "The next step is coded before the expected output is predicted.",
    ),
    "control_flow": (
        "Loop variables are interpreted after the loop without checking the last iteration.",
        "Return values and printed output are treated as the same artifact.",
        "The condition is changed before the current branch is traced.",
    ),
    "numpy": (
        "Array shape is guessed after execution instead of predicted before it.",
        "Broadcasting creates a result whose dimensions are not justified.",
        "A numeric result is interpreted before the measurement unit is named.",
    ),
    "pandas": (
        "Measurement and grouping columns are selected without a dtypes check.",
        "Missing values are ignored before plotting or statistics.",
        "A DataFrame operation is used before naming the expected row/column change.",
    ),
    "boxplots": (
        "The plotted measurement is not separated from the grouping variable.",
        "The visual summary is over-interpreted as a final statistical conclusion.",
        "Axis labels and units are filled in after the plot rather than justified before it.",
    ),
    "statistics_pingouin": (
        "Hypothesis, variable choice, and function call are collapsed into one step.",
        "A p-value is treated as a full final interpretation.",
        "Assumptions are checked after choosing the result sentence.",
    ),
    "debugging": (
        "The whole code cell is rewritten before the traceback line is identified.",
        "The error type is ignored in favor of a guessed code fix.",
        "A complete fix is requested instead of a smallest diagnostic test.",
    ),
    "machine_learning": (
        "Features and target are not separated before training.",
        "Train/test leakage is checked only after the score is known.",
        "Model output is presented without limitations or data-boundary notes.",
    ),
}
SKILL_PRACTICE_TASKS = {
    "colab_jupyter": (
        "Mark the next cell, predicted output, and one runtime-state risk before running.",
        "Write one source-check sentence before using an external notebook helper.",
    ),
    "python_lists": (
        "Predict len(), first index, and one out-of-range risk for a tiny synthetic list.",
        "Explain one list operation in words before writing the smallest code line.",
    ),
    "control_flow": (
        "Trace two loop iterations by hand and name the variable state after each step.",
        "Write a function contract with input, output, and side effect before coding.",
    ),
    "numpy": (
        "Predict shape and dtype for a tiny synthetic array operation.",
        "Name the measurement dimension before applying a summary operation.",
    ),
    "pandas": (
        "List expected columns, dtypes, and one missing-value check before selecting data.",
        "Describe the row/column effect of a pandas operation before running it.",
    ),
    "boxplots": (
        "Name measurement, group, unit, and interpretation boundary before plotting.",
        "Write one statement the boxplot can support and one it cannot support yet.",
    ),
    "statistics_pingouin": (
        "Separate hypothesis, variable, assumption, function, and interpretation boundary.",
        "Write a cautious source-grounded result template without inserting final values.",
    ),
    "debugging": (
        "Copy only error type, failing line, and smallest diagnostic check.",
        "State one hypothesis about the error before changing code.",
    ),
    "machine_learning": (
        "Name features, target, split, metric, and leakage risk before model fitting.",
        "Describe one limitation of the model output before interpreting a score.",
    ),
}
SOLUTION_MARKERS = re.compile(
    r"(?<![a-z0-9])(solution|loesung|lösung|answer[_ -]?key|musterloesung|musterlösung|exam[_ -]?key)(?![a-z0-9])",
    re.I,
)
FINAL_SOLUTION_REQUEST = re.compile(
    r"\b(fertige|complete|komplette|finale|lösung|loesung|solve|write all|vollständigen? code|debug-fix|werte einsetzen)\b",
    re.I,
)


def course_material_root(course_id: str = DEFAULT_COURSE_ID, base_path: str | None = None) -> Path:
    if base_path:
        return Path(base_path).expanduser()
    configured = str(os.environ.get(COURSE_MATERIAL_ROOT_ENV, "")).strip()
    if configured:
        configured_root = Path(configured).expanduser()
        if configured_root.exists():
            return configured_root
    return PRIVATE_ROOT / safe_course_id(course_id)


def safe_course_id(course_id: str | None) -> str:
    raw = str(course_id or DEFAULT_COURSE_ID).strip() or DEFAULT_COURSE_ID
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", raw)[:120] or DEFAULT_COURSE_ID


def scan_course_intake(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    public_safe: bool = True,
) -> dict[str, Any]:
    root = course_material_root(course_id, base_path=base_path)
    generated_at = datetime.now(timezone.utc).isoformat()
    if not root.exists():
        return {
            "schema_version": COURSE_TUTOR_SCHEMA_VERSION,
            "artifact_type": "course_intake_scan",
            "generated_at_utc": generated_at,
            "course_id": safe_course_id(course_id),
            "status": "missing",
            "record_count": 0,
            "records": [],
            "root_policy": "local private course-material root is not returned",
            "next_safe_steps": ["add local course files", "review permission status", "build exam-scope map"],
        }

    files = sorted(path for path in root.rglob("*") if path.is_file())
    limited = files[: max(1, int(max_files or 1))]
    records = [
        record_from_path(path, root=root, course_id=course_id, review_policy=review_policy)
        for path in limited
    ]
    manifest = build_material_manifest(records)
    counts_by_kind: dict[str, int] = {}
    counts_by_status: dict[str, int] = {}
    solution_quarantine = 0
    for record in manifest["records"]:
        counts_by_kind[record["source_kind"]] = counts_by_kind.get(record["source_kind"], 0) + 1
        counts_by_status[record["extraction_status"]] = counts_by_status.get(record["extraction_status"], 0) + 1
        if "quarantined_solution_or_exam" in record.get("notes", ""):
            solution_quarantine += 1

    scan = {
        "schema_version": COURSE_TUTOR_SCHEMA_VERSION,
        "artifact_type": "course_intake_scan",
        "generated_at_utc": generated_at,
        "course_id": safe_course_id(course_id),
        "status": "ready" if records else "empty",
        "record_count": len(records),
        "total_file_count": len(files),
        "truncated": len(files) > len(limited),
        "counts_by_kind": counts_by_kind,
        "counts_by_extraction_status": counts_by_status,
        "review_policy": review_policy,
        "review_summary": {
            "tutor_usable_count": manifest["tutor_usable_count"],
            "public_release_allowed_count": manifest["public_release_allowed_count"],
            "blocked_count": manifest["blocked_count"],
            "solution_or_exam_quarantine_count": solution_quarantine,
        },
        "records": [public_record_view(record, public_safe=public_safe) for record in manifest["records"]],
        "root_policy": "local private course-material root is not returned",
        "content_policy": "metadata, source labels, hashes, and tiny generated snippets only; no raw private course text by default",
        "next_safe_steps": [
            "review permission status for slides, videos, notebooks, and exercises",
            "transcribe videos locally only after rights/privacy decision",
            "mark usable records as reviewed_for_private_tutor before retrieval tutoring",
            "keep exam mode on frozen A0-A2 material only",
        ],
    }
    attach_public_scan(scan, public_safe=public_safe, source_name="course-intake-scan")
    return scan


def record_from_path(
    path: Path,
    *,
    root: Path,
    course_id: str,
    review_policy: str = "staged",
) -> dict[str, Any]:
    relative_parts = path.relative_to(root).parts
    filename = path.name
    text_sample = extract_text_sample(path)
    haystack = f"{filename} {' '.join(relative_parts)} {text_sample}".lower()
    source_kind = source_kind_for_path(path)
    extraction_status = extraction_status_for_path(path, text_sample=text_sample)
    quarantined = bool(SOLUTION_MARKERS.search(haystack))
    review_status = "blocked" if quarantined else review_status_for_policy(review_policy, extraction_status)
    permission_status = "private_course_use_only"
    publish_policy = "private_only"
    sha = ""
    if review_status in {"reviewed_for_private_tutor", "reviewed_public_safe"}:
        sha = safe_file_hash(path)
    elif text_sample:
        sha = sha256_text(f"{safe_course_id(course_id)}:{filename}:{text_sample[:500]}")
    skill_tags = infer_skill_tags(haystack)
    source_card_ids = infer_source_card_ids(skill_tags, quarantined=quarantined)
    material_id = material_id_for_path(path, root=root, course_id=course_id)
    record = {
        "material_id": material_id,
        "title": title_for_path(path),
        "source_kind": source_kind,
        "permission_status": permission_status,
        "publish_policy": publish_policy,
        "extraction_status": extraction_status,
        "review_status": review_status,
        "skill_tags": skill_tags,
        "source_card_ids": source_card_ids,
        "page_or_timestamp": page_or_timestamp_for_path(path, relative_parts),
        "sha256": sha,
        "notes": "quarantined_solution_or_exam" if quarantined else notes_for_source_kind(source_kind, extraction_status),
        "source_label": safe_source_label(path, relative_parts),
        "course_id": safe_course_id(course_id),
    }
    return record


def source_kind_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".ipynb":
        return "notebook"
    if suffix in {".mov", ".mp4", ".m4v", ".webm"}:
        return "video_file"
    if suffix in {".srt", ".vtt"}:
        return "video_caption"
    if suffix in {".pptx", ".ppt"}:
        return "slide_deck"
    if suffix == ".pdf":
        return "slide_pdf"
    if suffix in {".md", ".txt"}:
        return "transcript"
    if suffix == ".py":
        return "python_file"
    if suffix == ".csv":
        return "data_file"
    if suffix in {".docx", ".doc"}:
        return "document"
    if suffix in {".json", ".yml", ".yaml"}:
        return "course_manifest"
    return "other_staged"


def extraction_status_for_path(path: Path, *, text_sample: str) -> str:
    suffix = path.suffix.lower()
    if text_sample and suffix in {".ipynb", ".md", ".txt", ".py", ".csv", ".json"}:
        return "text_extracted"
    if suffix in {".srt", ".vtt"}:
        return "captions_available"
    if suffix in {".mov", ".mp4", ".m4v", ".webm"}:
        return "staged"
    if suffix in {".pdf", ".pptx", ".ppt", ".docx", ".doc"}:
        return "ocr_needed"
    return "staged"


def review_status_for_policy(review_policy: str, extraction_status: str) -> str:
    if review_policy == "local_private_tutor" and extraction_status in {"text_extracted", "captions_available"}:
        return "reviewed_for_private_tutor"
    if review_policy == "public_safe_demo" and extraction_status in {"text_extracted", "captions_available"}:
        return "reviewed_public_safe"
    return "unreviewed"


def safe_file_hash(path: Path) -> str:
    try:
        if path.stat().st_size > 48 * 1024 * 1024:
            return sha256_text(f"{path.name}:{path.stat().st_size}:{int(path.stat().st_mtime)}")
        return sha256_file(path)
    except OSError:
        return ""


def extract_text_sample(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix in {".md", ".txt", ".py", ".srt", ".vtt"}:
            return path.read_text(encoding="utf-8", errors="replace")[:MAX_TEXT_CHARS]
        if suffix == ".csv":
            return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:8])[:MAX_TEXT_CHARS]
        if suffix == ".json":
            return path.read_text(encoding="utf-8", errors="replace")[:MAX_TEXT_CHARS]
        if suffix == ".ipynb":
            return extract_notebook_text(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ""
    return ""


def extract_notebook_text(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    cells = data.get("cells") if isinstance(data, dict) else []
    parts: list[str] = []
    if isinstance(cells, list):
        for cell in cells[:40]:
            if not isinstance(cell, dict):
                continue
            source = cell.get("source", "")
            text = "".join(source) if isinstance(source, list) else str(source)
            parts.append(text)
    return "\n".join(parts)[:MAX_TEXT_CHARS]


def infer_skill_tags(text: str) -> list[str]:
    tags = []
    for profile in SKILL_PROFILES:
        if any(keyword.lower() in text for keyword in profile.keywords):
            tags.append(profile.skill_tag)
    if not tags and any(term in text for term in ["data", "daten", "csv"]):
        tags.append("data_files")
    return tags or ["general_python"]


def infer_source_card_ids(skill_tags: Iterable[str], *, quarantined: bool = False) -> list[str]:
    cards: list[str] = ["dfg-gwp"]
    if quarantined:
        cards.extend(["uoc-ki-faq", "eu-ai-act-2024"])
    for tag in skill_tags:
        profile = SKILL_BY_TAG.get(tag)
        if profile:
            cards.extend(profile.source_card_ids)
    deduped: list[str] = []
    for card in cards:
        if card not in deduped:
            deduped.append(card)
    return deduped[:8]


def material_id_for_path(path: Path, *, root: Path, course_id: str) -> str:
    relative = "/".join(path.relative_to(root).parts)
    return sha256_text(f"{safe_course_id(course_id)}:{relative}")[:20]


def title_for_path(path: Path) -> str:
    title = path.stem.replace("_", " ").replace("-", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return title[:90] or "Course material"


def page_or_timestamp_for_path(path: Path, relative_parts: tuple[str, ...]) -> str:
    label_parts = []
    for part in relative_parts[:-1]:
        clean = part.replace("_", " ").replace("-", " ").strip()
        if re.search(r"\bweek\b|\bday\b|\bwoche\b", clean, re.I):
            label_parts.append(clean)
    if path.suffix.lower() in {".mov", ".mp4", ".m4v", ".webm"}:
        label_parts.append("video staged")
    return " / ".join(label_parts[:3]) or "course-local"


def safe_source_label(path: Path, relative_parts: tuple[str, ...]) -> str:
    context = [part for part in relative_parts[:-1] if re.search(r"\bweek\b|\bday\b|\btools\b|\bexercise\b", part, re.I)]
    stem = path.stem.replace("_", " ").replace("-", " ")
    label = " / ".join([*context[-2:], stem]).strip()
    return re.sub(r"\s+", " ", label)[:120] or title_for_path(path)


def notes_for_source_kind(source_kind: str, extraction_status: str) -> str:
    if source_kind == "video_file":
        return "video_staged_transcription_required"
    if source_kind in {"slide_pdf", "slide_deck", "document"} and extraction_status == "ocr_needed":
        return "text_extraction_or_ocr_required"
    if source_kind == "notebook":
        return "notebook_cells_extracted_outputs_not_used"
    return "local_private_review_required"


def public_record_view(record: dict[str, Any], *, public_safe: bool) -> dict[str, Any]:
    allowed = {
        "material_id",
        "title",
        "source_kind",
        "permission_status",
        "publish_policy",
        "extraction_status",
        "review_status",
        "skill_tags",
        "source_card_ids",
        "page_or_timestamp",
        "sha256",
        "tutor_usable",
        "public_release_allowed",
        "path_policy",
        "validation",
        "notes",
        "source_label",
        "course_id",
    }
    view = {key: value for key, value in record.items() if key in allowed}
    if public_safe:
        view.pop("source_label", None)
    return view


def build_course_exam_scope(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    records: Iterable[dict[str, Any] | CourseMaterialRecord] | None = None,
    base_path: str | None = None,
    review_policy: str = "staged",
    public_safe: bool = True,
) -> dict[str, Any]:
    scan = None
    if records is None:
        scan = scan_course_intake(
            course_id,
            base_path=base_path,
            review_policy=review_policy,
            public_safe=public_safe,
        )
        raw_records = scan.get("records", [])
    else:
        raw_records = list(records)

    normalized = [record if isinstance(record, CourseMaterialRecord) else normalize_material_record(record) for record in raw_records]
    material_views = []
    for record in normalized:
        validation = validate_material_record(record)
        material_views.append(
            {
                "material_id": record.material_id,
                "title": record.title,
                "source_kind": record.source_kind,
                "skill_tags": list(record.skill_tags),
                "source_card_ids": list(record.source_card_ids),
                "page_or_timestamp": record.page_or_timestamp,
                "sha256": record.sha256,
                "review_status": record.review_status,
                "extraction_status": record.extraction_status,
                "tutor_usable": validation["tutor_usable"],
                "public_release_allowed": validation["public_release_allowed"],
                "notes": record.notes,
            }
        )

    skills = []
    for profile in SKILL_PROFILES:
        matched = [material for material in material_views if profile.skill_tag in material["skill_tags"]]
        tutor_usable = [material for material in matched if material["tutor_usable"]]
        candidate = [material for material in matched if material["review_status"] != "blocked"]
        readiness = "ready_for_private_tutor" if tutor_usable else "needs_review" if candidate else "no_course_anchor"
        skills.append(
            {
                "skill_tag": profile.skill_tag,
                "title": profile.title,
                "objective": profile.objective,
                "exam_task_type": profile.exam_task_type,
                "readiness": readiness,
                "material_count": len(matched),
                "tutor_usable_count": len(tutor_usable),
                "source_card_ids": list(profile.source_card_ids),
                "source_refs": [
                    {
                        "material_id": material["material_id"],
                        "title": material["title"],
                        "source_kind": material["source_kind"],
                        "page_or_timestamp": material["page_or_timestamp"],
                        "review_status": material["review_status"],
                        "sha256": material["sha256"],
                    }
                    for material in matched[:6]
                ],
                "allowed_practice_help": list(profile.allowed_practice_help),
                "allowed_exam_help": list(profile.allowed_exam_help),
                "typical_pitfalls": list(SKILL_PITFALLS.get(profile.skill_tag, ()))[:4],
                "practice_tasks": list(SKILL_PRACTICE_TASKS.get(profile.skill_tag, ()))[:4],
                "blocked_exam_help": [
                    "complete code",
                    "inserted values",
                    "final interpretation",
                    "automatic grading",
                    "proctoring",
                    "AI detection",
                ],
            }
        )

    scope = {
        "schema_version": COURSE_TUTOR_SCHEMA_VERSION,
        "artifact_type": "exam_scope_map",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "ok" if any(skill["material_count"] for skill in skills) else "needs_materials",
        "public_safe": public_safe,
        "source_policy": "course materials stay local; source-card IDs, hashes, and reviewed metadata carry tutor evidence",
        "exam_deployment_status": "not_cleared",
        "golden_rules": [
            "generalize reusable course capabilities",
            "validate important workflows with harnesses, metrics, logs, and regression checks",
            "turn recurring failures into tests, rubrics, backlog, and prompt updates",
        ],
        "allowed_exam_profile": {
            "standard": ["A0", "A1", "A2"],
            "not_standard_without_written_decision": ["A3", "A4", "A5"],
            "always_blocked": ["A6"],
            "non_goals": ["automatic grading", "proctoring", "AI detection", "accommodation decision"],
        },
        "material_summary": {
            "record_count": len(material_views),
            "tutor_usable_count": len([material for material in material_views if material["tutor_usable"]]),
            "ocr_or_transcription_queue_count": len(
                [
                    material
                    for material in material_views
                    if material["extraction_status"] in {"ocr_needed", "staged"}
                ]
            ),
        },
        "skills": skills,
        "intake_status": scan.get("status") if isinstance(scan, dict) else "provided_records",
    }
    attach_public_scan(scope, public_safe=public_safe, source_name="exam-scope-map")
    return scope


def build_course_material_compiler_plan(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    max_files: int = 260,
    review_policy: str = "staged",
    public_safe: bool = True,
) -> dict[str, Any]:
    scan = scan_course_intake(
        course_id,
        base_path=base_path,
        max_files=max_files,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    records = list(scan.get("records", []))
    review_ready = [
        brief_material(record)
        for record in records
        if record.get("extraction_status") in {"text_extracted", "captions_available"}
        and record.get("review_status") == "unreviewed"
        and "quarantined_solution_or_exam" not in str(record.get("notes", ""))
    ]
    private_tutor_index = [
        brief_material(record)
        for record in records
        if record.get("review_status") in {"reviewed_for_private_tutor", "reviewed_public_safe"}
        and record.get("extraction_status") in {"text_extracted", "captions_available"}
    ]
    ocr_queue = [
        brief_material(record)
        for record in records
        if record.get("extraction_status") == "ocr_needed"
    ]
    transcription_queue = [
        brief_material(record)
        for record in records
        if record.get("source_kind") == "video_file" and record.get("extraction_status") == "staged"
    ]
    quarantine = [
        brief_material(record)
        for record in records
        if record.get("review_status") == "blocked" or "quarantined_solution_or_exam" in str(record.get("notes", ""))
    ]
    skill_counts: dict[str, int] = {}
    for record in records:
        if record.get("review_status") == "blocked":
            continue
        for tag in record.get("skill_tags", []) or []:
            skill_counts[str(tag)] = skill_counts.get(str(tag), 0) + 1
    source_card_counts: dict[str, int] = {}
    for record in records:
        for source_id in record.get("source_card_ids", []) or []:
            source_card_counts[str(source_id)] = source_card_counts.get(str(source_id), 0) + 1

    plan = {
        "schema_version": COURSE_TUTOR_SCHEMA_VERSION,
        "artifact_type": "course_material_compiler_plan",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "status": "ready" if scan.get("status") in {"ready", "empty"} else scan.get("status", "missing"),
        "exam_deployment_status": "not_cleared",
        "source_policy": "private course files stay local; compiler queues expose metadata, hashes, and review status only",
        "counts": {
            "total_file_count": scan.get("total_file_count", scan.get("record_count", 0)),
            "record_count": scan.get("record_count", 0),
            "review_ready_count": len(review_ready),
            "private_tutor_index_count": len(private_tutor_index),
            "ocr_queue_count": len(ocr_queue),
            "transcription_queue_count": len(transcription_queue),
            "solution_or_exam_quarantine_count": len(quarantine),
        },
        "queues": {
            "review_ready": review_ready[:20],
            "private_tutor_index": private_tutor_index[:20],
            "ocr_queue": ocr_queue[:20],
            "transcription_queue": transcription_queue[:20],
            "solution_or_exam_quarantine": quarantine[:20],
        },
        "skill_anchor_counts": dict(sorted(skill_counts.items())),
        "source_card_counts": dict(sorted(source_card_counts.items())),
        "outputs_to_build": [
            "source cards for reviewed private tutor material",
            "exam scope map with skill objectives, pitfalls, and microtasks",
            "local retrieval index for tutor mode",
            "public-safe material summary without source files, local paths, or raw course text",
        ],
        "next_actions": [
            "review text-extracted notebooks, scripts, captions, and transcripts for private tutor use",
            "run OCR only locally for slides and documents after rights/privacy decision",
            "transcribe video files locally only after rights/privacy decision",
            "keep solution-key or exam-like files quarantined from tutor retrieval",
        ],
        "golden_rules": [
            "generalize reusable material-intake and source-card capabilities",
            "cover compiler queues with harness checks and public-safety scans",
            "turn recurring material-review failures into regression tests and backlog items",
        ],
        "intake_status": scan.get("status", "unknown"),
        "root_policy": scan.get("root_policy", "local private course-material root is not returned"),
    }
    attach_public_scan(plan, public_safe=public_safe, source_name="course-material-compiler-plan")
    return plan


def brief_material(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "material_id": record.get("material_id", ""),
        "title": record.get("title", ""),
        "source_kind": record.get("source_kind", ""),
        "extraction_status": record.get("extraction_status", ""),
        "review_status": record.get("review_status", ""),
        "skill_tags": list(record.get("skill_tags", []) or [])[:6],
        "source_card_ids": list(record.get("source_card_ids", []) or [])[:6],
        "sha256": record.get("sha256", ""),
        "notes": record.get("notes", ""),
    }


def course_tutor_response(
    query: str,
    *,
    course_id: str = DEFAULT_COURSE_ID,
    mode: str = "course_tutor_mode",
    requested_help_level: str = "A2",
    exam_status: str = "practice",
    records: Iterable[dict[str, Any] | CourseMaterialRecord] | None = None,
    base_path: str | None = None,
    review_policy: str = "staged",
    public_safe: bool = True,
) -> dict[str, Any]:
    scope = build_course_exam_scope(
        course_id,
        records=records,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    query_text = str(query or "").strip()
    strict = mode == "exam_controlled_gateway" or exam_status in {"closed", "strict", "exam"}
    selected = select_skill(scope["skills"], query_text)
    dangerous = bool(FINAL_SOLUTION_REQUEST.search(query_text))
    requested = normalize_help_level(requested_help_level)
    source_refs = selected.get("source_refs", [])
    has_reviewed_anchor = selected.get("tutor_usable_count", 0) > 0
    has_any_anchor = selected.get("material_count", 0) > 0

    if strict and (requested not in {"A0", "A1", "A2"} or dangerous):
        return tutor_payload(
            status="blocked",
            query=query_text,
            course_id=course_id,
            mode=mode,
            requested_help_level=requested,
            selected=selected,
            strict=strict,
            message="Im Pruefungsmodus bleibt UniBot bei A0-A2. Fertige Loesungen, Werte, Code-Fixes und finale Interpretation werden blockiert.",
            source_refs=source_refs,
            scope=scope,
        )

    if not has_any_anchor:
        return tutor_payload(
            status="no_source",
            query=query_text,
            course_id=course_id,
            mode=mode,
            requested_help_level=requested,
            selected=selected,
            strict=strict,
            message="Ich finde in der Kurs-Stoffkarte keine belastbare Stelle. Ich kann eine allgemeine Lernfrage formulieren, aber keinen quellenbasierten Kursstoff behaupten.",
            source_refs=[],
            scope=scope,
        )

    if strict and not has_reviewed_anchor:
        return tutor_payload(
            status="needs_review",
            query=query_text,
            course_id=course_id,
            mode=mode,
            requested_help_level=requested,
            selected=selected,
            strict=strict,
            message="Es gibt Kursanker, aber sie sind fuer den strikten Pruefungsmodus noch nicht als reviewed_for_private_tutor markiert.",
            source_refs=source_refs,
            scope=scope,
        )

    message = build_allowed_message(selected, strict=strict)
    return tutor_payload(
        status="allowed",
        query=query_text,
        course_id=course_id,
        mode=mode,
        requested_help_level=requested,
        selected=selected,
        strict=strict,
        message=message,
        source_refs=source_refs,
        scope=scope,
    )


def select_skill(skills: list[dict[str, Any]], query: str) -> dict[str, Any]:
    haystack = query.lower()
    scored = []
    for skill in skills:
        profile = SKILL_BY_TAG.get(skill["skill_tag"])
        keywords = profile.keywords if profile else (skill["skill_tag"],)
        keyword_score = sum(1 for keyword in keywords if keyword.lower() in haystack)
        readiness_score = min(int(skill.get("tutor_usable_count", 0) or 0), 10)
        material_score = min(int(skill.get("material_count", 0) or 0), 10)
        score = keyword_score * 100 + readiness_score * 2 + material_score
        scored.append((score, keyword_score, readiness_score, material_score, skill))
    scored.sort(key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
    return scored[0][4] if scored else fallback_skill()


def fallback_skill() -> dict[str, Any]:
    profile = SKILL_BY_TAG["python_lists"]
    return {
        "skill_tag": profile.skill_tag,
        "title": profile.title,
        "objective": profile.objective,
        "exam_task_type": profile.exam_task_type,
        "readiness": "no_course_anchor",
        "material_count": 0,
        "tutor_usable_count": 0,
        "source_card_ids": list(profile.source_card_ids),
        "source_refs": [],
        "allowed_practice_help": list(profile.allowed_practice_help),
        "allowed_exam_help": list(profile.allowed_exam_help),
        "blocked_exam_help": ["complete solution"],
    }


def normalize_help_level(value: str) -> str:
    match = re.search(r"A[0-6]", str(value or "").upper())
    return match.group(0) if match else "A2"


def build_allowed_message(selected: dict[str, Any], *, strict: bool) -> str:
    if strict:
        return (
            f"Ich arbeite im A0-A2-Gateway zu {selected['title']}. "
            "Ich zeige dir den Quellenanker und stelle die naechste eigene Prueffrage; ich schreibe keinen neuen Loesungscode."
        )
    return (
        f"Ich nutze die Kurs-Stoffkarte zu {selected['title']}. "
        "Im Lernmodus darf ich erklaeren, mit synthetischen Mini-Schritten ueben und dich dann zu einem eigenen Notebook-Schritt fuehren."
    )


def tutor_payload(
    *,
    status: str,
    query: str,
    course_id: str,
    mode: str,
    requested_help_level: str,
    selected: dict[str, Any],
    strict: bool,
    message: str,
    source_refs: list[dict[str, Any]],
    scope: dict[str, Any],
) -> dict[str, Any]:
    help_level = "A2" if strict else requested_help_level if requested_help_level in {"A0", "A1", "A2", "A3", "A4", "A5"} else "A2"
    if status == "blocked":
        help_level = "A6"
    next_task = next_task_for_skill(selected, strict=strict)
    payload = {
        "schema_version": COURSE_TUTOR_SCHEMA_VERSION,
        "artifact_type": "course_tutor_response",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "course_id": safe_course_id(course_id),
        "mode": mode,
        "strict_exam_boundary": strict,
        "exam_deployment_status": "not_cleared",
        "selected_skill": {
            "skill_tag": selected["skill_tag"],
            "title": selected["title"],
            "readiness": selected.get("readiness", "unknown"),
            "material_count": selected.get("material_count", 0),
            "tutor_usable_count": selected.get("tutor_usable_count", 0),
        },
        "answer_markdown": message,
        "socratic_questions": socratic_questions_for_skill(selected, strict=strict),
        "next_task": next_task,
        "source_refs": source_refs[:4],
        "source_card_ids": selected.get("source_card_ids", [])[:8],
        "allowed_help_levels": ["A0", "A1", "A2"] if strict else ["A0", "A1", "A2", "A3", "A4", "A5"],
        "blocked_help": selected.get("blocked_exam_help", []),
        "help_ledger_entry": {
            "course_id": safe_course_id(course_id),
            "help_level": help_level,
            "help_kind": "blocked final solution" if status == "blocked" else "source-card Socratic tutor",
            "source_card_ids": selected.get("source_card_ids", [])[:8],
            "source_ref_ids": [item.get("material_id", "") for item in source_refs[:4]],
            "raw_response_hash": sha256_text(message),
            "accessibility_neutral": True,
            "human_review_required": True,
        },
        "scope_summary": scope.get("material_summary", {}),
        "storage_policy": "hashes and source metadata only by default; no raw private transcript storage",
    }
    attach_public_scan(payload, public_safe=True, source_name="course-tutor-response")
    return payload


def socratic_questions_for_skill(selected: dict[str, Any], *, strict: bool) -> list[str]:
    tag = selected.get("skill_tag", "general_python")
    base = {
        "pandas": [
            "Welche Spalte ist Messwert, welche ist Gruppe oder Bedingung?",
            "Welche Ausgabe erwartest du von head(), columns oder dtypes?",
            "Welche Datenqualitaetspruefung kommt vor Plot oder Statistik?",
        ],
        "boxplots": [
            "Welche Messreihe gehoert fachlich in den Plot?",
            "Welche Einheit und Achsenbeschriftung kannst du selbst begruenden?",
            "Welche Aussage waere nach dem Boxplot noch nicht erlaubt?",
        ],
        "debugging": [
            "Welcher Fehlertyp steht im Traceback?",
            "Welche Zeile ist wirklich fehlgeschlagen?",
            "Was ist der kleinste Test, bevor du Code aenderst?",
        ],
        "numpy": [
            "Welche Shape erwartest du vor dem Ausfuehren?",
            "Welche Zahl oder Dimension repraesentiert welche Messung?",
            "Wann waere ein DataFrame statt Array sinnvoller?",
        ],
        "colab_jupyter": [
            "Welche Zelle erzeugt Zustand, welche dokumentiert nur?",
            "Welche Ausgabe erwartest du vor dem naechsten Run?",
            "Welche Daten duerfen nicht in ein externes Notebook?",
        ],
    }
    questions = base.get(
        tag,
        [
            "Welche Eingabe, Ausgabe und Annahme kannst du selbst benennen?",
            "Welche Quelle oder Kursstelle pruefst du zuerst?",
            "Was ist der kleinste eigene naechste Schritt?",
        ],
    )
    return questions[:2] if strict else questions


def next_task_for_skill(selected: dict[str, Any], *, strict: bool) -> dict[str, Any]:
    tag = selected.get("skill_tag", "general_python")
    prompts = {
        "pandas": "Notiere Spalten, erwartete dtypes und eine Datenqualitaetsfrage, bevor du eine Spalte auswaehlst.",
        "boxplots": "Formuliere Messreihe, Gruppe, Einheit und Aussagegrenze, bevor du einen Plot erzeugst.",
        "debugging": "Schreibe Fehlertyp, betroffene Zeile und kleinsten Diagnoseschritt auf.",
        "numpy": "Sage Shape und Datentyp vorher, dann teste nur diesen Mini-Schritt.",
        "colab_jupyter": "Markiere naechste Zelle, erwartete Ausgabe und Risiko bei Runtime-Neustart.",
    }
    return {
        "task_type": "exam_safe_microtask" if strict else "course_tutor_microtask",
        "skill_tag": tag,
        "prompt": prompts.get(tag, "Formuliere den kleinsten eigenen naechsten Schritt und die Quelle dazu."),
        "expected_artifact": "one prediction, one source anchor, one reflection sentence",
        "assessment_policy": "self-check only; no grade, ranking, proctoring, or AI detection",
    }


def next_course_task(
    query: str = "",
    *,
    course_id: str = DEFAULT_COURSE_ID,
    records: Iterable[dict[str, Any] | CourseMaterialRecord] | None = None,
    base_path: str | None = None,
    review_policy: str = "staged",
    public_safe: bool = True,
) -> dict[str, Any]:
    scope = build_course_exam_scope(
        course_id,
        records=records,
        base_path=base_path,
        review_policy=review_policy,
        public_safe=public_safe,
    )
    selected = select_skill(scope["skills"], query)
    return {
        "schema_version": COURSE_TUTOR_SCHEMA_VERSION,
        "artifact_type": "course_next_task",
        "status": "ok",
        "course_id": safe_course_id(course_id),
        "selected_skill": selected["skill_tag"],
        "next_task": next_task_for_skill(selected, strict=False),
        "source_refs": selected.get("source_refs", [])[:4],
        "source_card_ids": selected.get("source_card_ids", [])[:8],
        "exam_deployment_status": "not_cleared",
    }


def run_course_tutor_eval() -> dict[str, Any]:
    records = [
        {
            "material_id": "fixture-pandas-notebook",
            "title": "Week 1 pandas notebook",
            "source_kind": "notebook",
            "permission_status": "private_course_use_only",
            "publish_policy": "private_only",
            "extraction_status": "text_extracted",
            "review_status": "reviewed_for_private_tutor",
            "skill_tags": ["pandas", "boxplots"],
            "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
            "page_or_timestamp": "fixture",
            "sha256": sha256_text("fixture pandas notebook"),
        }
    ]
    allowed = course_tutor_response(
        "Wie uebe ich einen Boxplot mit pandas?",
        records=records,
        review_policy="local_private_tutor",
        public_safe=True,
    )
    blocked = course_tutor_response(
        "Gib mir die komplette Loesung und setze die Werte ein.",
        mode="exam_controlled_gateway",
        exam_status="strict",
        records=records,
        review_policy="local_private_tutor",
        public_safe=True,
    )
    no_source = course_tutor_response("Fourier transformation proof", records=[], public_safe=True)
    checks = [
        ("allowed_course_tutor", allowed["status"] == "allowed"),
        ("blocked_exam_solution", blocked["status"] == "blocked" and blocked["help_ledger_entry"]["help_level"] == "A6"),
        ("no_source_refusal", no_source["status"] == "no_source"),
        ("no_raw_private_paths", scan_text(json.dumps([allowed, blocked, no_source], ensure_ascii=False), "course-eval")["status"] == "pass"),
    ]
    failed = [name for name, passed in checks if not passed]
    return {
        "schema_version": COURSE_TUTOR_SCHEMA_VERSION,
        "artifact_type": "course_tutor_eval",
        "status": "pass" if not failed else "fail",
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "failed_checks": failed,
        "exam_deployment_status": "not_cleared",
    }


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
