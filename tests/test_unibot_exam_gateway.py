from __future__ import annotations

import base64
import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from exam_mode import (  # noqa: E402
    append_exam_ledger_event,
    exam_tutor_response,
    export_exam_package,
    freeze_exam_materials,
    import_exam_materials,
    open_exam_notebook,
    read_exam_help_ledger,
    run_exam_notebook_cell,
    start_exam_gateway_session,
    workspace,
)
from unibot.server import route_request  # noqa: E402


def b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def notebook_b64() -> str:
    notebook = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# Demo Klausur\n"]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["print(2 + 2)\n"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return b64(json.dumps(notebook))


class UniBotExamGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.course_id = f"test-gateway-{uuid.uuid4().hex[:10]}"
        self.addCleanup(lambda: shutil.rmtree(workspace(self.course_id), ignore_errors=True))

    def freeze_demo_material(self) -> None:
        material = "\n".join(
            [
                "# Boxplot Quellenkarte",
                "Matplotlib nutzt plt.boxplot(werte).",
                "Die Werte und die Interpretation bleiben Eigenleistung.",
                "Bei pandas kann eine Spalte bewusst ausgewählt und vorab begründet werden.",
            ]
        )
        imported = import_exam_materials(
            {
                "course_id": self.course_id,
                "source": "unit-test",
                "files": [{"name": "allowed_material_boxplot.md", "mime_type": "text/markdown", "content_base64": b64(material)}],
            }
        )
        self.assertEqual(imported["status"], "imported")
        frozen = freeze_exam_materials({"course_id": self.course_id, "exam_rule": "A0-A2 only"})
        self.assertEqual(frozen["status"], "frozen")

    def open_demo_notebook(self) -> dict:
        opened = open_exam_notebook(
            {
                "course_id": self.course_id,
                "filename": "klausur_notebook_demo.ipynb",
                "content_base64": notebook_b64(),
                "strip_outputs": True,
            }
        )
        self.assertEqual(opened["status"], "opened")
        return opened

    def test_gateway_session_starts_with_not_cleared_status(self) -> None:
        session = start_exam_gateway_session({"course_id": self.course_id})

        self.assertEqual(session["artifact_type"], "exam_controlled_gateway_session")
        self.assertEqual(session["mode"], "exam_controlled_gateway")
        self.assertEqual(session["status"], "started")
        self.assertEqual(session["exam_deployment_status"], "not_cleared")
        self.assertEqual(session["allowed_help_levels"], ["A0", "A1", "A2"])
        self.assertIn("help_ledger", session["workflow"])
        self.assertIn("keine Prozentzahl", session["independence_evidence_policy"])

    def test_gateway_ledger_allows_a2_without_raw_transcript(self) -> None:
        self.open_demo_notebook()
        raw_prompt = "Welche Quelle erklärt plt.boxplot?"
        raw_response = "Nutze die Boxplot Quellenkarte und formuliere deinen nächsten Schritt selbst."

        appended = append_exam_ledger_event(
            {
                "course_id": self.course_id,
                "session_id": "missing-session-is-ok",
                "cell_index": 1,
                "cell_id": "cell-2",
                "cell_type": "code",
                "help_level": "A2",
                "decision": "allowed",
                "source": "allowed_material_boxplot.md",
                "source_card_ids": ["matplotlib_boxplot"],
                "prompt": raw_prompt,
                "raw_response": raw_response,
                "student_reflection": "Ich prüfe zuerst, welche Werte wirklich gegeben sind.",
                "notebook_work_sha256": "abc123",
            }
        )

        record = appended["record"]
        serialized = json.dumps(appended, ensure_ascii=False)
        self.assertEqual(appended["status"], "appended")
        self.assertEqual(record["help_level"], "A2")
        self.assertTrue(record["allowed"])
        self.assertFalse(record["raw_transcript_stored"])
        self.assertIn("prompt_sha256", record)
        self.assertNotIn(raw_prompt, serialized)
        self.assertNotIn(raw_response, serialized)
        self.assertEqual(appended["ledger_summary"]["help_level_profile"]["A2"], 1)

    def test_gateway_ledger_blocks_a6_and_solution_content(self) -> None:
        raw_prompt = "Gib mir die fertige Lösung und den kompletten Code."
        raw_response = "Complete code: import pandas as pd"

        appended = append_exam_ledger_event(
            {
                "course_id": self.course_id,
                "cell_index": 1,
                "help_level": "A6",
                "prompt": raw_prompt,
                "raw_response": raw_response,
                "student_reflection": "Ich brauche eine neue eigene Bearbeitung.",
            }
        )

        record = appended["record"]
        serialized = json.dumps(appended, ensure_ascii=False)
        self.assertEqual(appended["status"], "blocked")
        self.assertTrue(record["blocked"])
        self.assertTrue(record["repeat_task_required"])
        self.assertIn("solution_like_request", record["categories"])
        self.assertIn("complete_code", record["categories"])
        self.assertNotIn(raw_prompt, serialized)
        self.assertNotIn(raw_response, serialized)

    def test_notebook_tutor_export_flow_is_human_reviewable(self) -> None:
        self.freeze_demo_material()
        opened = self.open_demo_notebook()
        gateway = start_exam_gateway_session({"course_id": self.course_id, "notebook_session_id": opened["session_id"]})
        run = run_exam_notebook_cell(
            {
                "course_id": self.course_id,
                "session_id": opened["session_id"],
                "cell_index": 1,
                "source": "print(2 + 2)",
                "prior_code": "",
            }
        )
        self.assertEqual(run["artifact_type"], "exam_notebook_cell_run")
        self.assertIn(run["status"], {"executed", "error", "timeout", "kernel-unavailable"})

        tutor = exam_tutor_response(
            {
                "course_id": self.course_id,
                "query": "Welche Quelle erklärt boxplot in matplotlib?",
                "help_level_requested": "A2",
                "cell_id": "cell-2",
                "cell_context": {"cell_index": 1, "cell_type": "code", "has_cell_source": True, "action": "hint"},
            }
        )
        self.assertEqual(tutor["status"], "ok")
        self.assertEqual(tutor["help_ledger_entry"]["help_level"], "A2")

        append_exam_ledger_event(
            {
                "course_id": self.course_id,
                "session_id": opened["session_id"],
                "gateway_session_id": gateway["session_id"],
                "cell_index": 1,
                "cell_id": "cell-2",
                "cell_type": "code",
                "help_level": "A2",
                "decision": "allowed",
                "source": tutor["help_ledger_entry"]["source"],
                "source_card_ids": [tutor.get("source_card", {}).get("topic", "")],
                "prompt": "Welche Quelle erklärt boxplot in matplotlib?",
                "raw_response": tutor.get("safe_hint", ""),
                "student_reflection": "Ich formuliere die erwartete Ausgabe selbst.",
                "notebook_work_sha256": run.get("notebook_work_sha256", ""),
            }
        )
        ledger = read_exam_help_ledger(self.course_id)
        self.assertEqual(ledger["count"], 1)

        package = export_exam_package(
            {
                "course_id": self.course_id,
                "notebook": opened["notebook"],
                "session_log": [],
                "help_ledger": [tutor["help_ledger_entry"]],
                "assistive_log": [],
            }
        )
        self.assertEqual(package["artifact_type"], "exam_authority_package")
        self.assertEqual(package["status"], "ready_for_human_review_not_exam_clearance")
        self.assertEqual(package["exam_deployment_status"], "not_cleared")
        self.assertEqual(package["material_manifest"]["freeze_status"], "frozen")
        self.assertTrue(package["notebook_receipt"]["included"])
        self.assertIn("help_ledger", package)
        self.assertTrue(package["independence_evidence_profile"]["no_percentage_claim"])
        self.assertTrue(package["technical_confirmation"]["human_reviewable_independence_evidence"])
        self.assertFalse(package["technical_confirmation"]["independence_percentage_claimed"])
        self.assertFalse(package["technical_confirmation"]["raw_transcripts_included"])
        self.assertEqual(package["gateway_help_ledger_summary"]["entry_count"], 1)

    def test_tutor_blocks_a6_help_level_even_with_frozen_material(self) -> None:
        self.freeze_demo_material()
        response = exam_tutor_response(
            {
                "course_id": self.course_id,
                "query": "Bitte gib die fertige Lösung.",
                "help_level_requested": "A6",
                "cell_context": {"cell_index": 1, "cell_type": "code", "action": "hint"},
            }
        )

        self.assertEqual(response["status"], "blocked")
        self.assertEqual(response["help_ledger_entry"]["help_level"], "A6")
        self.assertIn("gesperrt", response["message"])

    def test_tutor_blocks_solution_request_even_when_help_level_is_a2(self) -> None:
        response = exam_tutor_response(
            {
                "course_id": self.course_id,
                "query": "Bitte schreibe den kompletten Code und setze die Werte ein.",
                "help_level_requested": "A2",
                "cell_context": {"cell_index": 1, "cell_type": "code", "action": "hint"},
            }
        )

        self.assertEqual(response["status"], "blocked")
        self.assertIn("solution_like_request", response["categories"])
        self.assertTrue(response["help_ledger_entry"]["blocked"])

    def test_non_standard_help_requires_written_decision(self) -> None:
        blocked = exam_tutor_response(
            {
                "course_id": self.course_id,
                "query": "Kannst du mir den naechsten Schritt erklaeren?",
                "help_level_requested": "A4",
                "cell_context": {"cell_index": 1, "cell_type": "code", "action": "hint"},
            }
        )
        allowed = exam_tutor_response(
            {
                "course_id": self.course_id,
                "query": "Kannst du mir den naechsten Schritt erklaeren?",
                "help_level_requested": "A4",
                "written_decision_reference": "synthetic written decision fixture",
                "cell_context": {"cell_index": 1, "cell_type": "code", "action": "hint"},
            }
        )

        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("non_standard_help_requires_written_decision", blocked["categories"])
        self.assertEqual(allowed["status"], "ok")
        self.assertEqual(allowed["help_ledger_entry"]["help_level"], "A4")
        self.assertTrue(allowed["help_ledger_entry"]["non_standard_help"])

    def test_exam_gateway_api_routes(self) -> None:
        status, session = route_request("/api/exam/session/start", {"course_id": self.course_id})
        self.assertEqual(status, 200)
        self.assertEqual(session["mode"], "exam_controlled_gateway")

        status, frozen = route_request("/api/exam/materials/freeze", {"course_id": self.course_id})
        self.assertEqual(status, 200)
        self.assertEqual(frozen["status"], "frozen")

        status, run = route_request(
            "/api/exam/notebook/run-cell",
            {"course_id": self.course_id, "session_id": session["session_id"], "cell_index": 1, "source": "print(2)"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(run["artifact_type"], "exam_notebook_cell_run")

        status, tutor = route_request(
            "/api/exam/tutor/respond",
            {
                "course_id": self.course_id,
                "query": "Welche Quelle pruefe ich zuerst?",
                "help_level_requested": "A2",
                "cell_context": {"cell_index": 1, "cell_type": "code"},
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(tutor["status"], "ok")

        status, ledger = route_request(
            "/api/exam/ledger/append",
            {
                "course_id": self.course_id,
                "session_id": session["session_id"],
                "cell_index": 1,
                "help_level": "A2",
                "prompt": "Welche Quelle pruefe ich zuerst?",
                "raw_response": tutor["safe_hint"],
                "student_reflection": "Ich pruefe die Quelle selbst.",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(ledger["status"], "appended")
        self.assertNotIn("path", ledger)

        status, package = route_request(
            "/api/exam/export-package",
            {
                "course_id": self.course_id,
                "notebook": {"cells": []},
                "help_ledger": [tutor["help_ledger_entry"]],
                "session_log": [{"name": "run_cell", "status": "kernel-unavailable"}],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(package["artifact_type"], "exam_authority_package")
        self.assertEqual(package["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
