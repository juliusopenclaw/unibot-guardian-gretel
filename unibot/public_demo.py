"""Reproducible, synthetic end-to-end demonstration of the local tutor."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .guardian import classify_external_ai_output
from .learning_session import LearningSession
from .notebook_intake import sanitize_notebook
from .public_safety import scan_text
from .socratic_tutor import TutorTurnRequestV1, build_tutor_turn


PUBLIC_DEMO_SCHEMA_VERSION = "UniBotPublicDemoV1"
PUBLIC_DEMO_FIXTURE_NAME = "synthetic_python_practice.ipynb"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "public" / PUBLIC_DEMO_FIXTURE_NAME


def _public_turn(turn: dict[str, Any]) -> dict[str, Any]:
    """Keep the demonstration report free of task, cell, and attempt text."""
    return {
        "requested_help_level": turn["requested_help_level"],
        "effective_help_level": turn["effective_help_level"],
        "status": turn["status"],
        "hint_kind": turn["hint_kind"],
        "hint_markdown": turn["hint_markdown"],
        "source_anchor_ids": list(turn["source_anchor_ids"]),
        "confidence": turn["confidence"],
        "assistance_points_delta": turn["assistance_points_delta"],
        "assistance_points_for_task": turn["assistance_points_for_task"],
        "blocked_reasons": list(turn["blocked_reasons"]),
        "attempt_hash": turn["attempt_hash"],
        "cell_hash": turn["cell_hash"],
        "own_attempt_present": turn["own_attempt_present"],
        "raw_cell_stored": turn["raw_cell_stored"],
        "raw_attempt_stored": turn["raw_attempt_stored"],
        "rule_pack_version": turn["rule_pack_version"],
        "rule_id": turn["rule_id"],
        "knowledge_boundary": turn["knowledge_boundary"],
    }


def build_public_demo_evidence() -> dict[str, Any]:
    """Run the public synthetic notebook through the real local tutor in memory.

    The fixture is parsed and sanitized, but never executed. The session has no
    storage root, so the demo cannot write learner content or a tutor transcript.
    """
    fixture = _fixture_path()
    if fixture.is_symlink() or not fixture.is_file():
        return {
            "schema_version": PUBLIC_DEMO_SCHEMA_VERSION,
            "status": "blocked",
            "reason": "public_demo_fixture_missing_or_unsafe",
            "fixture_name": PUBLIC_DEMO_FIXTURE_NAME,
            "exam_deployment_status": "not_cleared",
        }

    try:
        raw_bytes = fixture.read_bytes()
        sanitized, counts = sanitize_notebook(raw_bytes)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return {
            "schema_version": PUBLIC_DEMO_SCHEMA_VERSION,
            "status": "blocked",
            "reason": "public_demo_fixture_invalid",
            "fixture_name": PUBLIC_DEMO_FIXTURE_NAME,
            "error_type": type(exc).__name__,
            "exam_deployment_status": "not_cleared",
        }

    code_cells = [cell for cell in sanitized.get("cells", []) if cell.get("cell_type") == "code"]
    if len(code_cells) != 1:
        return {
            "schema_version": PUBLIC_DEMO_SCHEMA_VERSION,
            "status": "blocked",
            "reason": "public_demo_requires_one_code_cell",
            "fixture_name": PUBLIC_DEMO_FIXTURE_NAME,
            "exam_deployment_status": "not_cleared",
        }
    code_cell = code_cells[0]
    cell_source = str(code_cell.get("source", ""))
    task = "Untersuche die Liste und berechne den Mittelwert. Welche kleinste Pruefung machst du zuerst?"
    session = LearningSession.start(
        {
            "assistance_mode": "adaptive",
            "max_help_level": "A4",
            "planned_task_count": 1,
            "course_id": "public-synthetic-python-practice",
        }
    )
    requests: tuple[TutorTurnRequestV1, ...] = (
        {
            "task_id": "public-demo-mean",
            "task": task,
            "learner_attempt": "Ich beschreibe zuerst Eingabe und erwartete Ausgabe.",
            "cell_context": cell_source,
            "requested_help_level": "A0",
            "cell_type": "code",
            "cell_index": 1,
            "adapter": "public-synthetic-fixture",
        },
        {
            "task_id": "public-demo-mean",
            "task": task,
            "learner_attempt": "Ich pruefe jetzt Laenge und Nenner der Liste.",
            "cell_context": cell_source,
            "requested_help_level": "A1",
            "cell_type": "code",
            "cell_index": 1,
            "adapter": "public-synthetic-fixture",
            "confirm_escalation": True,
        },
        {
            "task_id": "public-demo-mean",
            "task": task,
            "learner_attempt": "Ich vergleiche die verwendeten Namen und pruefe die Formelstruktur.",
            "cell_context": cell_source,
            "requested_help_level": "A2",
            "cell_type": "code",
            "cell_index": 1,
            "adapter": "public-synthetic-fixture",
            "confirm_escalation": True,
        },
    )
    turns = [_public_turn(build_tutor_turn(session, request)) for request in requests]
    output_reviews = [
        classify_external_ai_output(
            turn["hint_markdown"], requested_help_level=turn["effective_help_level"], mode="practice_overlay"
        )
        for turn in turns
    ]
    output_filter_pass = all(
        review["status"] == "allowed"
        and not any(
            category
            in {
                "final_solution",
                "code_fix_or_complete_code",
                "values_inserted",
                "final_interpretation",
                "source_or_citation_risk",
            }
            for category in review["categories"]
        )
        for review in output_reviews
    )
    source_binding_pass = all(
        turn["source_anchor_ids"] and turn["knowledge_boundary"] == "source_bound" for turn in turns
    )
    blocked_solution_review = classify_external_ai_output(
        "Here is the " + "complete code and final answer for this synthetic task.",
        requested_help_level="A4",
        mode="practice_overlay",
    )
    complete_solution_block_pass = (
        blocked_solution_review["status"] == "blocked"
        and "final_solution" in blocked_solution_review["categories"]
    )
    report = {
        "schema_version": PUBLIC_DEMO_SCHEMA_VERSION,
        "status": "ready_for_human_demo"
        if output_filter_pass and source_binding_pass and complete_solution_block_pass
        else "blocked",
        "mode": "public_synthetic_practice_only",
        "fixture_name": PUBLIC_DEMO_FIXTURE_NAME,
        "fixture_sha256": _sha256(raw_bytes),
        "sanitized_notebook_sha256": _sha256(
            json.dumps(sanitized, ensure_ascii=True, sort_keys=True).encode("utf-8")
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "notebook": {
            "nbformat": int(sanitized.get("nbformat", 0)),
            "cell_count": len(sanitized.get("cells", [])),
            "code_cell_count": len(code_cells),
            "outputs_removed": int(counts["outputs_removed"]),
            "attachments_removed": int(counts["attachments_removed"]),
            "execution_counts_cleared": all(cell.get("execution_count") is None for cell in code_cells),
        },
        "tutor": {
            "rule_pack_version": "TutorRulePackV2",
            "local_realizer": "deterministic_source_grounded_v1",
            "help_levels_demonstrated": [turn["effective_help_level"] for turn in turns],
            "turns": turns,
            "source_binding_pass": source_binding_pass,
            "output_filter_pass": output_filter_pass,
            "complete_solution_block_pass": complete_solution_block_pass,
            "complete_solution_block_categories": list(blocked_solution_review["categories"]),
            "complete_solution_probe_hash": blocked_solution_review["raw_output_hash"],
            "raw_cell_stored": any(turn["raw_cell_stored"] for turn in turns),
            "raw_attempt_stored": any(turn["raw_attempt_stored"] for turn in turns),
        },
        "safety": {
            "notebook_code_executed": False,
            "provider_calls": 0,
            "provider_context_included": False,
            "learner_content_included": False,
            "private_project_files_included": False,
            "automatic_merge": False,
            "automatic_publication": False,
        },
        "exam_deployment_status": "not_cleared",
        "human_demo_gates": [
            "show_only_the_public_synthetic_fixture",
            "explain_local_processing_and_retention",
            "invite_inclusion_and_teaching_review",
            "do_not_present_this_as_exam_clearance",
        ],
    }
    scan = scan_text(json.dumps(report, ensure_ascii=False), "public-demo-evidence")
    report["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        report["status"] = "blocked"
        report["public_safety_findings"] = scan["findings"]
    return report


def build_public_demo_markdown(report: dict[str, Any] | None = None) -> str:
    """Render a short meeting script without exposing notebook source."""
    report = report or build_public_demo_evidence()
    lines = [
        "# UniBot Oeffentliche Demo",
        "",
        f"Status: {report['status']}",
        "",
        "Nur synthetische Uebungsdaten; keine Pruefungs- oder Hochschulfreigabe.",
        "",
        f"Fixture: `{report.get('fixture_name', PUBLIC_DEMO_FIXTURE_NAME)}`",
        f"Notebook-Code ausgefuehrt: {'ja' if report.get('safety', {}).get('notebook_code_executed') else 'nein'}",
        f"Provideraufrufe: {report.get('safety', {}).get('provider_calls', 0)}",
        f"Quellenbindung: {'bestanden' if report.get('tutor', {}).get('source_binding_pass') else 'blockiert'}",
        f"Ausgabefilter: {'bestanden' if report.get('tutor', {}).get('output_filter_pass') else 'blockiert'}",
        "",
        "## Vorfuehrung",
        "",
        "1. Das synthetische Notebook oeffnen und die fehlerhafte eigene Zeile zeigen.",
        "2. Die Zelle ausdruecklich auswaehlen und den eigenen Versuch formulieren.",
        "3. A0, A1 und A2 nacheinander anfordern; jede Stufe bleibt quellengebunden.",
        "4. Den Rueckblick mit Hilfestufen und Hashes zeigen; keine Rohzelle wird gespeichert.",
        "5. Mit den zustaendigen Stellen Zweck, Barrierefreiheit, Datenschutz und Grenzen besprechen.",
        "6. Eine synthetische fertige Antwort einspeisen; der Guardian blockiert sie und zeigt nur eine Rueckfrage.",
        "",
        "## Grenze",
        "",
        "UniBot benotet nicht, ueberwacht nicht, erkennt keine KI-Nutzung und erteilt keine Pruefungsfreigabe.",
    ]
    return "\n".join(lines) + "\n"
