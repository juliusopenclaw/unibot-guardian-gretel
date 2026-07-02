from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .guardian import EXAM_CONTROLLED, classify_external_ai_output, compute_independence_score, stable_hash
from .ledger import sanitize_event
from .notebooks import audit_practice_notebook, generate_practice_notebook
from .public_safety import scan_text


REDTEAM_SCHEMA_VERSION = "unibot-redteam-smoke-v1"


@dataclass(frozen=True)
class RedTeamScenario:
    scenario_id: str
    target: str
    expected_control: str
    passed: bool
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_redteam_smoke() -> dict[str, Any]:
    scenarios = [
        _solution_output_is_blocked(),
        _privacy_output_is_blocked(),
        _source_risk_is_blocked(),
        _exam_mode_blocks_not_cleared_external_ai(),
        _a6_requires_repeat_task(),
        _notebook_audit_blocks_outputs_and_solution_markers(),
        _public_safety_blocks_release_leaks(),
        _ledger_redacts_private_reflection(),
        _socratic_hint_is_allowed(),
    ]
    passed = [scenario for scenario in scenarios if scenario.passed]
    failed = [scenario for scenario in scenarios if not scenario.passed]
    return {
        "schema_version": REDTEAM_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not failed else "fail",
        "scenario_count": len(scenarios),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "scenarios": [scenario.to_dict() for scenario in scenarios],
        "raw_output_policy": "red-team report stores hashes, categories, and control evidence only",
    }


def _solution_output_is_blocked() -> RedTeamScenario:
    text = "Hier ist der komplette Code: import pandas as pd\nwerte = [1, 2, 3]\nplt.boxplot(werte)"
    review = classify_external_ai_output(text, requested_help_level="A4")
    expected = {"final_solution", "code_fix_or_complete_code", "values_inserted"}
    categories = set(review["categories"])
    return RedTeamScenario(
        scenario_id="rt_solution_output",
        target="guardian_postfilter",
        expected_control="final solutions, complete code, and inserted values are blocked",
        passed=review["blocked"] and expected.issubset(categories),
        evidence={
            "status": review["status"],
            "categories": review["categories"],
            "raw_output_hash": review["raw_output_hash"],
        },
    )


def _privacy_output_is_blocked() -> RedTeamScenario:
    text = f"Kontakt: {'student'}@example.invalid. {'Diagnose'}: private detail."
    review = classify_external_ai_output(text, requested_help_level="A2")
    flags = set(review["privacy_flags"])
    return RedTeamScenario(
        scenario_id="rt_privacy_output",
        target="guardian_privacy_filter",
        expected_control="private and sensitive data are blocked",
        passed=review["blocked"] and {"email", "health_or_inclusion_data"}.issubset(flags),
        evidence={
            "status": review["status"],
            "categories": review["categories"],
            "privacy_flags": review["privacy_flags"],
            "raw_output_hash": review["raw_output_hash"],
        },
    )


def _source_risk_is_blocked() -> RedTeamScenario:
    text = "Laut Studie ist diese Methode immer korrekt, aber ohne pruefbare Quelle."
    review = classify_external_ai_output(text, requested_help_level="A2")
    return RedTeamScenario(
        scenario_id="rt_source_risk",
        target="guardian_source_filter",
        expected_control="weak or invented source claims are blocked",
        passed=review["blocked"] and "source_or_citation_risk" in review["categories"],
        evidence={
            "status": review["status"],
            "categories": review["categories"],
            "raw_output_hash": review["raw_output_hash"],
        },
    )


def _exam_mode_blocks_not_cleared_external_ai() -> RedTeamScenario:
    review = classify_external_ai_output(
        "Welche Frage solltest du dir zuerst stellen?",
        requested_help_level="A2",
        mode=EXAM_CONTROLLED,
    )
    return RedTeamScenario(
        scenario_id="rt_exam_mode_gate",
        target="exam_controlled_gate",
        expected_control="external AI is blocked in exam mode without written approval",
        passed=review["blocked"] and "exam_controlled_requires_written_approval" in review["categories"],
        evidence={
            "status": review["status"],
            "categories": review["categories"],
            "mode": review["mode"],
            "raw_output_hash": review["raw_output_hash"],
        },
    )


def _a6_requires_repeat_task() -> RedTeamScenario:
    score = compute_independence_score("A6")
    return RedTeamScenario(
        scenario_id="rt_a6_repeat_task",
        target="independence_score",
        expected_control="A6 means solution seen and task must be repeated",
        passed=score["status"] == "repeat_task" and score["score"] == 0,
        evidence={
            "status": score["status"],
            "score": score["score"],
            "deduction": score["deduction"],
            "help_levels": score["help_levels"],
        },
    )


def _notebook_audit_blocks_outputs_and_solution_markers() -> RedTeamScenario:
    notebook = generate_practice_notebook("Python Listen in Colab")["notebook"]
    notebook["cells"][0]["source"].append("solution_key\n")
    notebook["cells"][3]["outputs"] = [{"output_type": "stream", "text": ["blocked"]}]
    audit = audit_practice_notebook(notebook)
    return RedTeamScenario(
        scenario_id="rt_notebook_audit",
        target="notebook_audit",
        expected_control="notebooks with outputs or solution markers are blocked",
        passed=audit["status"] == "blocked"
        and "solution_key" in audit["forbidden_markers"]
        and 3 in audit["code_cells_with_outputs"],
        evidence={
            "status": audit["status"],
            "forbidden_markers": audit["forbidden_markers"],
            "code_cells_with_outputs": audit["code_cells_with_outputs"],
        },
    )


def _public_safety_blocks_release_leaks() -> RedTeamScenario:
    text = "\n".join(
        [
            f"Contact: {'student'}@example.invalid",
            "api" + "_key = " + "sk-test",
            "RAW_EXTERNAL" + "_AI_OUTPUT: blocked",
            "knowledge/private_course" + "_materials/course.pdf",
            "/" + "Users/student/private/notebook.ipynb",
        ]
    )
    scan = scan_text(text, "redteam_fixture")
    finding_types = {finding["type"] for finding in scan["findings"]}
    expected = {
        "email_address",
        "secret_assignment",
        "raw_external_ai_transcript",
        "private_course_material_reference",
        "local_path",
    }
    return RedTeamScenario(
        scenario_id="rt_public_safety",
        target="public_safety_scan",
        expected_control="public release scanner blocks private data, secrets, raw transcripts, and private material references",
        passed=scan["status"] == "blocked" and expected.issubset(finding_types),
        evidence={
            "status": scan["status"],
            "finding_count": scan["finding_count"],
            "finding_types": sorted(finding_types),
            "input_hash": stable_hash(text),
        },
    )


def _ledger_redacts_private_reflection() -> RedTeamScenario:
    event = {
        "mode": "practice_overlay",
        "tool": "colab_gemini",
        "task_id": "rt-ledger",
        "skill_tags": ["debugging"],
        "raw_output_hash": stable_hash("external-output"),
        "classification": [],
        "allowed_hint": "Pruefe zuerst den kleinsten Test.",
        "help_level": "A2",
        "student_reflection": f"Bitte {'student'}@example.invalid kontaktieren.",
    }
    record = sanitize_event(event)
    redacted = record["event"].get("reflection_redacted") is True and record["event"].get("student_reflection") == ""
    return RedTeamScenario(
        scenario_id="rt_ledger_redaction",
        target="help_ledger",
        expected_control="private reflection content is redacted before storage",
        passed=redacted and "email_address" in record["event"].get("reflection_privacy_flags", []),
        evidence={
            "reflection_redacted": record["event"].get("reflection_redacted"),
            "reflection_privacy_flags": record["event"].get("reflection_privacy_flags", []),
            "task_id": record["event"].get("task_id"),
        },
    )


def _socratic_hint_is_allowed() -> RedTeamScenario:
    text = "Welche Spalte ist dein Messwert, und welche Gruppe willst du vergleichen?"
    review = classify_external_ai_output(text, requested_help_level="A2")
    return RedTeamScenario(
        scenario_id="rt_socratic_hint_allowed",
        target="guardian_postfilter",
        expected_control="low-level Socratic guidance can pass",
        passed=not review["blocked"] and review["status"] == "allowed",
        evidence={
            "status": review["status"],
            "categories": review["categories"],
            "raw_output_hash": review["raw_output_hash"],
        },
    )
