from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Iterable

from .materials import (
    CourseMaterialRecord,
    demo_material_records,
    normalize_material_record,
    validate_material_record,
)
from .public_safety import scan_text


ADAPTIVE_TASK_PLAN_SCHEMA_VERSION = "unibot-adaptive-task-plan-v1"

DEFAULT_SKILL_ORDER = ["python_lists", "debugging", "pandas", "boxplots", "loops"]

SKILL_TASK_TEMPLATES: dict[str, dict[str, Any]] = {
    "python_lists": {
        "micro_goal": "Indexing, length, and append/extend decisions for Python lists.",
        "prompt": "Create a tiny synthetic reaction-time list and explain the next indexing step before writing code.",
        "checks": [
            "Which element do you expect at index 0?",
            "What should len(...) return before and after the update?",
            "Are you adding one item or merging another list?",
        ],
    },
    "loops": {
        "micro_goal": "Loop logic before implementation.",
        "prompt": "Describe a loop over synthetic measurements in pseudocode, then write only the loop header and one check.",
        "checks": [
            "What is the loop variable?",
            "What condition makes one item worth keeping?",
            "What should happen before the next iteration?",
        ],
    },
    "dictionaries": {
        "micro_goal": "Map labels to values without KeyError confusion.",
        "prompt": "Sketch a dictionary for two synthetic groups and predict what happens when a missing key is requested.",
        "checks": [
            "Which keys exist before lookup?",
            "What should a safe lookup return when a key is absent?",
            "How would you test this without changing the whole script?",
        ],
    },
    "functions": {
        "micro_goal": "Function contracts before code.",
        "prompt": "Write a one-sentence contract for a helper function, then list input, output, and one test case.",
        "checks": [
            "What type goes in?",
            "What type should come out?",
            "What is the smallest example that proves the function works?",
        ],
    },
    "numpy": {
        "micro_goal": "Array conversion and descriptive checks.",
        "prompt": "Convert a synthetic list to an array and predict shape, mean, and one possible type issue before running.",
        "checks": [
            "What shape do you expect?",
            "Which values are numeric?",
            "What would make the result surprising?",
        ],
    },
    "pandas": {
        "micro_goal": "DataFrame inspection before analysis.",
        "prompt": "Use a synthetic table and write the inspection sequence before selecting a column.",
        "checks": [
            "Which columns must exist?",
            "Which dtype do you expect?",
            "What missing-value check belongs before plotting?",
        ],
    },
    "boxplots": {
        "micro_goal": "Plot decision before interpretation.",
        "prompt": "Define the measurement, grouping variable, and unit for a synthetic boxplot without interpreting the result.",
        "checks": [
            "What is the measured variable?",
            "What defines the groups?",
            "What can the plot show descriptively, and what can it not prove?",
        ],
    },
    "debugging": {
        "micro_goal": "Traceback reading and smallest next test.",
        "prompt": "Take a short synthetic traceback, identify error type, likely variable, and the smallest diagnostic print/check.",
        "checks": [
            "Which line failed?",
            "Which object has the wrong value or type?",
            "What is the smallest check before editing code?",
        ],
    },
    "colab_jupyter": {
        "micro_goal": "Notebook reflection before another AI hint.",
        "prompt": "Fill Ziel, Vorhersage, eigener Versuch, Fehler, and Reflexion before requesting the next hint.",
        "checks": [
            "What did you try yourself?",
            "What changed after running the cell?",
            "What one question should the next hint answer?",
        ],
    },
    "general_python": {
        "micro_goal": "Smallest own next step.",
        "prompt": "State the smallest Python step you can test without asking for a final answer.",
        "checks": [
            "What do you already know?",
            "What exact value or type do you need to inspect?",
            "What would count as progress without a full solution?",
        ],
    },
}


def generate_adaptive_practice_plan(
    skill_state: dict[str, Any] | None = None,
    material_records: Iterable[dict[str, Any] | CourseMaterialRecord] | None = None,
    max_tasks: int = 3,
    public_safe: bool = True,
) -> dict[str, Any]:
    records = _eligible_materials(material_records if material_records is not None else demo_material_records(), public_safe=public_safe)
    materials_by_skill = _materials_by_skill(records)
    skill_order = _rank_skills(skill_state)
    tasks = []
    for skill_tag in skill_order:
        if len(tasks) >= max(1, max_tasks):
            break
        material = _best_material_for_skill(skill_tag, materials_by_skill)
        tasks.append(_build_task(skill_tag, material, skill_state or {}, public_safe=public_safe))

    plan = {
        "schema_version": ADAPTIVE_TASK_PLAN_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "public_safe": public_safe,
        "task_count": len(tasks),
        "skill_order": skill_order[: len(tasks)],
        "eligible_material_count": len(records),
        "tasks": tasks,
        "storage_policy": "local skill state and material hashes only; no raw private course text or local paths",
        "assessment_policy": "practice-only, private formative use; no grade and no official exam decision",
    }
    scan = scan_text(str(plan), "adaptive-task-plan")
    plan["public_safety_status"] = scan["status"] if public_safe else "local_private_mode"
    if public_safe and scan["status"] != "pass":
        plan["status"] = "blocked"
        plan["public_safety_findings"] = scan["findings"]
    return plan


def _rank_skills(skill_state: dict[str, Any] | None) -> list[str]:
    if not skill_state:
        return DEFAULT_SKILL_ORDER.copy()

    ranked = sorted(
        skill_state.items(),
        key=lambda item: (
            int(item[1].get("high_help_events", 0) or 0),
            int(item[1].get("signals", 0) or 0),
            str(item[0]),
        ),
        reverse=True,
    )
    ordered = [str(skill) for skill, _ in ranked]
    for fallback in DEFAULT_SKILL_ORDER:
        if fallback not in ordered:
            ordered.append(fallback)
    return ordered


def _eligible_materials(
    records: Iterable[dict[str, Any] | CourseMaterialRecord],
    *,
    public_safe: bool,
) -> list[CourseMaterialRecord]:
    eligible = []
    for raw in records:
        record = raw if isinstance(raw, CourseMaterialRecord) else normalize_material_record(raw)
        validation = validate_material_record(record)
        if public_safe and validation["public_release_allowed"]:
            eligible.append(record)
        elif not public_safe and validation["tutor_usable"]:
            eligible.append(record)
    return eligible


def _materials_by_skill(records: list[CourseMaterialRecord]) -> dict[str, list[CourseMaterialRecord]]:
    grouped: dict[str, list[CourseMaterialRecord]] = {}
    for record in records:
        for tag in record.skill_tags:
            grouped.setdefault(tag, []).append(record)
    return grouped


def _best_material_for_skill(
    skill_tag: str,
    materials_by_skill: dict[str, list[CourseMaterialRecord]],
) -> CourseMaterialRecord | None:
    if materials_by_skill.get(skill_tag):
        return materials_by_skill[skill_tag][0]
    for fallback in DEFAULT_SKILL_ORDER:
        if materials_by_skill.get(fallback):
            return materials_by_skill[fallback][0]
    return None


def _build_task(
    skill_tag: str,
    material: CourseMaterialRecord | None,
    skill_state: dict[str, Any],
    *,
    public_safe: bool,
) -> dict[str, Any]:
    template = SKILL_TASK_TEMPLATES.get(skill_tag, SKILL_TASK_TEMPLATES["general_python"])
    signal = skill_state.get(skill_tag, {}) if isinstance(skill_state, dict) else {}
    high_help = int(signal.get("high_help_events", 0) or 0)
    difficulty = "guided_repair" if high_help else "micro_practice"
    task = {
        "task_id": _task_id(skill_tag, material.material_id if material else "synthetic-fallback", difficulty),
        "skill_tag": skill_tag,
        "difficulty": difficulty,
        "micro_goal": template["micro_goal"],
        "task_prompt": template["prompt"],
        "socratic_checks": template["checks"],
        "expected_student_artifacts": [
            "own prediction before code",
            "smallest attempted step",
            "one reflection sentence",
            "help level logged if external AI was used",
        ],
        "help_policy": "Start with A0-A2. A3-A5 lowers only the private selftest score. A6 means repeat with a fresh task.",
        "assessment_policy": "practice-only, no grade",
        "public_safe": public_safe,
    }
    task["source_reference"] = _source_reference(material, public_safe=public_safe)
    return task


def _source_reference(material: CourseMaterialRecord | None, *, public_safe: bool) -> dict[str, Any]:
    if material is None:
        return {
            "material_id": "synthetic-fallback",
            "source_policy": "synthetic fallback task; no course material required",
            "source_card_ids": [],
            "public_release_allowed": True,
        }
    reference: dict[str, Any] = {
        "material_id": material.material_id,
        "source_kind": material.source_kind,
        "page_or_timestamp": material.page_or_timestamp,
        "source_card_ids": list(material.source_card_ids),
        "sha256": material.sha256,
        "review_status": material.review_status,
        "source_policy": "refer to reviewed material metadata only; do not copy raw private course text",
        "public_release_allowed": validate_material_record(material)["public_release_allowed"],
    }
    if public_safe and material.public_excerpt and reference["public_release_allowed"]:
        reference["public_excerpt"] = material.public_excerpt
    return reference


def _task_id(skill_tag: str, material_id: str, difficulty: str) -> str:
    return hashlib.sha256(f"{skill_tag}:{material_id}:{difficulty}".encode("utf-8")).hexdigest()[:16]
