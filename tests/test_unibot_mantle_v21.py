from __future__ import annotations

import io
import base64
import hashlib
import os
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nbformat

from unibot.companion import CompanionRuntime, read_native_message, write_native_message
from unibot.learning_session import HELP_COSTS_V1, LearningSession, create_session_contract
from unibot.socratic_tutor import _source_anchors, analyze_cell, build_tutor_turn


class UniBotMantleV21Tests(unittest.TestCase):
    def test_contract_is_hash_bound_and_rejects_invalid_fixed_boundary(self) -> None:
        contract = create_session_contract(
            {
                "pseudonym": "Synthetic Learner",
                "course_id": "python-test",
                "assistance_mode": "adaptive",
                "max_help_level": "A4",
            }
        )
        self.assertEqual(contract["schema_version"], "unibot-session-contract-v1")
        self.assertEqual(contract["help_costs"], HELP_COSTS_V1)
        self.assertEqual(len(contract["contract_hash"]), 64)
        self.assertEqual(contract["exam_deployment_status"], "not_cleared")
        self.assertEqual(contract["practice_scope"], "practice_only")
        with self.assertRaises(ValueError):
            create_session_contract({"fixed_help_level": "A4", "max_help_level": "A2"})

    def test_adaptive_help_increases_one_level_and_requires_new_attempt(self) -> None:
        session = LearningSession.start({"assistance_mode": "adaptive", "max_help_level": "A4"})
        first = build_tutor_turn(
            session,
            {
                "task": "Warum entsteht bei meiner Liste ein IndexError?",
                "learner_attempt": "Ich pruefe die Listenlaenge.",
                "cell_context": "values = [1, 2, 3]\nprint(values[3])",
                "requested_help_level": "A4",
                "confirm_escalation": True,
            },
        )
        self.assertEqual(first["effective_help_level"], "A1")
        self.assertIn("adaptive_mode_allows_one_level_per_turn", first["blocked_reasons"])
        second = build_tutor_turn(
            session,
            {
                "task": "Warum entsteht bei meiner Liste ein IndexError?",
                "learner_attempt": "Ich pruefe die Listenlaenge.",
                "cell_context": "values = [1, 2, 3]\nprint(values[3])",
                "requested_help_level": "A2",
                "confirm_escalation": True,
            },
        )
        self.assertEqual(second["effective_help_level"], "A1")
        self.assertIn("new_own_attempt_required_before_escalation", second["blocked_reasons"])
        third = build_tutor_turn(
            session,
            {
                "task": "Warum entsteht bei meiner Liste ein IndexError?",
                "learner_attempt": "Die Liste hat drei Werte und Index 3 liegt ausserhalb.",
                "cell_context": "values = [1, 2, 3]\nprint(values[3])",
                "requested_help_level": "A2",
                "confirm_escalation": True,
            },
        )
        self.assertEqual(third["effective_help_level"], "A2")
        self.assertEqual(third["assistance_points_delta"], 5)

    def test_a3_formula_and_a4_scaffold_never_return_complete_solution(self) -> None:
        formula = analyze_cell("Wie berechne ich den z-Wert?", "")
        self.assertEqual(formula.formula_card["id"], "formula-z-score-v1")  # type: ignore[index]
        session = LearningSession.start(
            {
                "assistance_mode": "fixed",
                "fixed_help_level": "A4",
                "max_help_level": "A4",
            }
        )
        turn = build_tutor_turn(
            session,
            {
                "task": "Wie strukturiere ich den z-Wert?",
                "learner_attempt": "Ich kenne Beobachtung und Mittelwert, aber nicht den Nenner.",
                "requested_help_level": "A4",
                "confirm_escalation": True,
            },
        )
        self.assertEqual(turn["effective_help_level"], "A4")
        self.assertIn("___", turn["hint_markdown"])
        self.assertNotIn("```", turn["hint_markdown"])
        self.assertEqual(turn["assistance_points_for_task"], 25)

        mean_turn = build_tutor_turn(
            LearningSession.start(
                {"assistance_mode": "fixed", "fixed_help_level": "A4", "max_help_level": "A4"}
            ),
            {
                "task": "Wie strukturiere ich den Mittelwert?",
                "learner_attempt": "Ich kenne die Werte und ihre Anzahl.",
                "requested_help_level": "A4",
            },
        )
        self.assertIn("Summe", mean_turn["hint_markdown"])
        self.assertNotIn("(___ - ___) / ___", mean_turn["hint_markdown"])

    def test_accessibility_support_is_explicit_and_cost_neutral(self) -> None:
        session = LearningSession.start(
            {"assistance_mode": "fixed", "fixed_help_level": "A2", "max_help_level": "A2"}
        )
        turn = build_tutor_turn(
            session,
            {
                "task": "Warum entsteht ein IndexError?",
                "learner_attempt": "Ich pruefe zuerst die Listenlaenge.",
                "cell_context": "values = [1, 2, 3]\nprint(values[3])",
                "requested_help_level": "A2",
                "accessibility_used": True,
            },
        )
        self.assertTrue(turn["accessibility_used"])
        self.assertEqual(turn["assistance_points_delta"], 5)
        self.assertTrue(turn["help_event"]["accessibility_used"])
        self.assertTrue(turn["help_event"]["accessibility_neutral"])
        report = session.report()
        self.assertEqual(report["accessibility_support_event_count"], 1)
        self.assertEqual(report["accessibility_policy"], "optional_user_declared_score_neutral_no_diagnosis")
        self.assertEqual(report["assistance_points_used"], 5)

    def test_rule_pack_binds_ast_traceback_and_source_boundary(self) -> None:
        numpy = analyze_cell("Pruefe die Array-Form.", "import numpy as np\nvalues = np.array([1, 2, 3])")
        self.assertEqual(numpy.rule_id, "numpy.arrays")
        self.assertEqual(numpy.knowledge_boundary, "source_bound")
        self.assertIn("numpy", numpy.skill_tags)

        traceback = analyze_cell("Warum scheitert die Zelle?", "NameError: missing_value")
        self.assertEqual(traceback.rule_id, "python.debugging")
        self.assertIn("python-tutorial-errors", [item["id"] for item in _source_anchors(traceback)])

    def test_unknown_topic_returns_no_reliable_source_without_generic_claim(self) -> None:
        session = LearningSession.start({"assistance_mode": "fixed", "fixed_help_level": "A2", "max_help_level": "A4"})
        turn = build_tutor_turn(
            session,
            {
                "task": "Erklaere mir ein synthetisches Fachgebiet ohne Kursanker.",
                "learner_attempt": "Ich habe zuerst die Begriffe abgegrenzt.",
                "requested_help_level": "A2",
            },
        )
        self.assertEqual(turn["status"], "no_reliable_source")
        self.assertEqual(turn["source_anchor_ids"], [])
        self.assertEqual(turn["assistance_points_delta"], 0)
        self.assertIn("no_reliable_source", turn["blocked_reasons"])

    def test_private_input_is_blocked_and_never_written_to_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = LearningSession.start({}, storage_root=Path(temporary))
            turn = build_tutor_turn(
                session,
                {
                    "task": "Bitte pruefe " + "api" + "_key=synthetic-secret",
                    "learner_attempt": "Ich habe einen eigenen Versuch.",
                    "requested_help_level": "A2",
                },
            )
            report = session.report()
            stored = next(Path(temporary).glob("*.jsonl")).read_text(encoding="utf-8")
        self.assertEqual(turn["status"], "blocked")
        self.assertFalse(report["raw_cell_text_included"])
        self.assertFalse(report["raw_attempt_text_included"])
        self.assertNotIn("synthetic-secret", stored)

    def test_companion_protocol_is_local_and_returns_metadata_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            storage_root = Path(temporary)
            runtime = CompanionRuntime(storage_root=storage_root)
            started = runtime.handle(
                {
                    "request_id": "1",
                    "type": "session.start",
                    "payload": {
                        "assistance_mode": "fixed",
                        "fixed_help_level": "A2",
                        "max_help_level": "A4",
                        "practice_scope": "practice_only",
                        "practice_scope_confirmed": True,
                    },
                }
            )
            self.assertEqual(started["status"], "active")
            session_id = started["contract"]["session_id"]
            turn = runtime.handle(
                {
                    "request_id": "2",
                    "type": "tutor.turn",
                    "payload": {
                        "session_id": session_id,
                        "task": "Wie pruefe ich eine Python-Liste?",
                        "learner_attempt": "Ich beginne mit len(values).",
                        "cell_context": "values = [1, 2, 3]",
                        "requested_help_level": "A2",
                    },
                }
            )
            report = runtime.handle({"request_id": "3", "type": "session.report", "payload": {}})
        self.assertEqual(turn["status"], "ok")
        self.assertEqual(report["report"]["event_count"], 1)
        self.assertFalse(report["report"]["raw_cell_text_included"])

    def test_optional_transfer_task_is_stop_only_hash_only_and_not_assessed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            storage_root = Path(temporary)
            runtime = CompanionRuntime(storage_root=storage_root)
            started = runtime.handle(
                {
                    "request_id": "transfer-1",
                    "type": "session.start",
                    "payload": {"practice_scope": "practice_only", "practice_scope_confirmed": True},
                }
            )
            before_stop = runtime.handle(
                {"request_id": "transfer-2", "type": "session.transfer.prompt", "payload": {}}
            )
            stopped = runtime.handle({"request_id": "transfer-3", "type": "session.stop", "payload": {}})
            prompt = runtime.handle({"request_id": "transfer-4", "type": "session.transfer.prompt", "payload": {}})
            answer = "Ich pruefe zuerst die Laenge und danach die Anzahl der Werte."
            recorded = runtime.handle(
                {
                    "request_id": "transfer-5",
                    "type": "session.transfer.record",
                    "payload": {"task_id": prompt["transfer"]["task_id"], "answer": answer},
                }
            )
            stored = "".join(path.read_text(encoding="utf-8") for path in storage_root.glob("*"))

        self.assertEqual(started["status"], "active")
        self.assertEqual(before_stop["status"], "blocked")
        self.assertEqual(before_stop["error"], "transfer_available_after_session_stop")
        self.assertEqual(stopped["report"]["transfer_tasks"][0]["status"], "not_started")
        self.assertIn("ohne UniBot-Hilfe", prompt["transfer"]["prompt"])
        self.assertFalse(prompt["transfer"]["help_allowed"])
        self.assertFalse(prompt["transfer"]["raw_prompt_stored"])
        self.assertEqual(recorded["status"], "ok")
        transfer = recorded["transfer"]
        self.assertEqual(transfer["status"], "recorded")
        self.assertTrue(transfer["attempt_present"])
        self.assertEqual(transfer["attempt_hash"], hashlib.sha256(answer.encode("utf-8")).hexdigest())
        self.assertFalse(recorded["report"]["transfer_tasks"][0]["raw_attempt_included"])
        self.assertEqual(recorded["report"]["transfer_tasks"][0]["assessment_status"], "not_assessed")
        self.assertNotIn(answer, stored)
        self.assertNotIn("Neue synthetische Python-Aufgabe", stored)

    def test_transfer_task_rejects_private_attempt_without_persisting_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = CompanionRuntime(storage_root=root)
            runtime.handle(
                {
                    "request_id": "transfer-private-1",
                    "type": "session.start",
                    "payload": {"practice_scope": "practice_only", "practice_scope_confirmed": True},
                }
            )
            runtime.handle({"request_id": "transfer-private-2", "type": "session.stop", "payload": {}})
            prompt = runtime.handle(
                {"request_id": "transfer-private-3", "type": "session.transfer.prompt", "payload": {}}
            )
            private_value = "api" + "_key=synthetic-secret"
            rejected = runtime.handle(
                {
                    "request_id": "transfer-private-4",
                    "type": "session.transfer.record",
                    "payload": {"task_id": prompt["transfer"]["task_id"], "answer": private_value},
                }
            )
            stored = "".join(path.read_text(encoding="utf-8") for path in root.glob("*"))

        self.assertEqual(rejected["status"], "blocked")
        self.assertEqual(rejected["error"], "transfer_attempt_contains_private_data")
        self.assertNotIn(private_value, stored)

    def test_companion_resumes_metadata_only_session_after_runtime_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            storage_root = Path(temporary)
            runtime = CompanionRuntime(storage_root=storage_root)
            started = runtime.handle(
                {
                    "request_id": "resume-1",
                    "type": "session.start",
                    "payload": {
                        "assistance_mode": "fixed",
                        "fixed_help_level": "A1",
                        "max_help_level": "A2",
                        "practice_scope": "practice_only",
                        "practice_scope_confirmed": True,
                    },
                }
            )
            session_id = started["contract"]["session_id"]
            runtime.handle(
                {
                    "request_id": "resume-2",
                    "type": "tutor.turn",
                    "payload": {
                        "session_id": session_id,
                        "task": "Wie pruefe ich eine Liste?",
                        "learner_attempt": "Ich pruefe zuerst len.",
                        "cell_context": "values = [1, 2, 3]",
                        "task_id": "sichtbarer-aufgabentext-darf-nicht-persistieren",
                        "requested_help_level": "A1",
                    },
                }
            )
            restarted = CompanionRuntime(storage_root=storage_root)
            status = restarted.handle({"request_id": "resume-3", "type": "companion.status", "payload": {}})
            resumed = restarted.handle(
                {"request_id": "resume-4", "type": "session.resume", "payload": {"session_id": session_id}}
            )
            stored = "\n".join(path.read_text(encoding="utf-8") for path in storage_root.glob("*.jsonl"))

        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["local_practice_status"], "ready_for_local_practice")
        self.assertEqual(status["distribution_status"], "blocked_human_release_gates")
        self.assertTrue(status["resume_available"])
        self.assertEqual(status["active_session_metadata"]["session_id"], session_id)
        self.assertEqual(resumed["status"], "active")
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["report"]["event_count"], 1)
        self.assertNotIn("sichtbarer-aufgabentext", stored)
        self.assertNotIn("Ich pruefe zuerst", stored)

    def test_companion_rejects_stale_or_missing_tutor_session_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runtime = CompanionRuntime(storage_root=Path(temporary))
            missing_scope = runtime.handle({"request_id": "binding-0", "type": "session.start", "payload": {}})
            started = runtime.handle(
                {
                    "request_id": "binding-1",
                    "type": "session.start",
                    "payload": {"practice_scope": "practice_only", "practice_scope_confirmed": True},
                }
            )
            base_payload = {
                "task": "Wie pruefe ich eine Python-Liste?",
                "learner_attempt": "Ich pruefe zuerst len(values).",
                "requested_help_level": "A1",
            }
            missing = runtime.handle({"request_id": "binding-2", "type": "tutor.turn", "payload": base_payload})
            stale = runtime.handle(
                {
                    "request_id": "binding-3",
                    "type": "tutor.turn",
                    "payload": {**base_payload, "session_id": "stale-session"},
                }
            )
            valid = runtime.handle(
                {
                    "request_id": "binding-4",
                    "type": "tutor.turn",
                    "payload": {**base_payload, "session_id": started["contract"]["session_id"]},
                }
            )

        self.assertEqual(missing["status"], "blocked")
        self.assertEqual(missing["error"], "session_id_required")
        self.assertEqual(stale["status"], "blocked")
        self.assertEqual(stale["error"], "session_id_mismatch")
        self.assertEqual(valid["status"], "ok")
        self.assertEqual(missing_scope["status"], "blocked")
        self.assertEqual(missing_scope["error"], "practice_scope_confirmation_required")

    def test_companion_session_delete_removes_contract_state_and_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            storage_root = Path(temporary)
            runtime = CompanionRuntime(storage_root=storage_root)
            started = runtime.handle(
                {
                    "request_id": "delete-1",
                    "type": "session.start",
                    "payload": {"practice_scope": "practice_only", "practice_scope_confirmed": True},
                }
            )
            deleted = runtime.handle(
                {
                    "request_id": "delete-2",
                    "type": "session.delete",
                    "payload": {"session_id": started["contract"]["session_id"]},
                }
            )
            status = runtime.handle({"request_id": "delete-3", "type": "companion.status", "payload": {}})

        self.assertEqual(deleted["status"], "deleted")
        self.assertFalse(status["resume_available"])
        self.assertEqual(list(storage_root.glob("*")), [])

    def test_companion_delete_removes_linked_notebook_after_runtime_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("values = [1, 2, 3]")])
            nbformat.write(notebook, source)
            runtime = CompanionRuntime(storage_root=root / "sessions")
            started = runtime.handle(
                {
                    "request_id": "linked-1",
                    "type": "session.start",
                    "payload": {"practice_scope": "practice_only", "practice_scope_confirmed": True},
                }
            )
            imported = runtime.handle(
                {
                    "request_id": "linked-2",
                    "type": "notebook.import",
                    "payload": {"source": str(source)},
                }
            )
            notebook_path = root / "notebooks" / imported["notebook_id"]
            self.assertTrue(notebook_path.is_dir())

            restarted = CompanionRuntime(storage_root=root / "sessions")
            restarted.handle(
                {
                    "request_id": "linked-3",
                    "type": "session.resume",
                    "payload": {"session_id": started["contract"]["session_id"]},
                }
            )
            deleted = restarted.handle(
                {
                    "request_id": "linked-4",
                    "type": "session.delete",
                    "payload": {"session_id": started["contract"]["session_id"]},
                }
            )

        self.assertEqual(deleted["status"], "deleted")
        self.assertFalse(notebook_path.exists())

    def test_companion_gateway_status_and_stop_persist_no_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("values = [1, 2, 3]")])
            nbformat.write(notebook, source)
            process = subprocess.Popen(["sleep", "30"], start_new_session=True)
            try:
                runtime = CompanionRuntime(storage_root=root / "sessions")
                runtime.handle(
                    {
                        "request_id": "gateway-1",
                        "type": "session.start",
                        "payload": {"practice_scope": "practice_only", "practice_scope_confirmed": True},
                    }
                )
                imported = runtime.handle(
                    {
                        "request_id": "gateway-2",
                        "type": "notebook.import",
                        "payload": {"source": str(source)},
                    }
                )
                notebook_id = imported["notebook_id"]
                with patch(
                    "unibot.companion.launch_gateway",
                    return_value={
                        "status": "local_practice_gateway_started",
                        "artifact_name": f"{notebook_id}.ipynb",
                        "process_id": process.pid,
                        "process_group_id": os.getpgid(process.pid),
                    },
                ):
                    launched = runtime.handle(
                        {
                            "request_id": "gateway-3",
                            "type": "gateway.launch",
                            "payload": {"notebook_id": notebook_id},
                        }
                    )
                    status = runtime.handle({"request_id": "gateway-4", "type": "gateway.status", "payload": {}})
                    stopped = runtime.handle({"request_id": "gateway-5", "type": "gateway.stop", "payload": {}})
                state_text = "".join(path.read_text(encoding="utf-8") for path in (root / "sessions").glob("*"))
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=3)

        self.assertEqual(launched["status"], "ok")
        self.assertEqual(status["status"], "active")
        self.assertEqual(stopped["status"], "stopped")
        self.assertIsNotNone(process.poll())
        self.assertNotIn("JUPYTER_TOKEN", state_text)
        self.assertFalse((root / "sessions" / "gateway.state.json").exists())

    def test_companion_imports_local_notebook_by_id_and_builds_gateway_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("values = [1, 2, 3]")])
            nbformat.write(notebook, source)
            with patch("unibot.companion.APPLICATION_SUPPORT", root / "support"):
                runtime = CompanionRuntime(storage_root=root / "sessions")
                imported = runtime.handle(
                    {
                        "request_id": "notebook-1",
                        "type": "notebook.import",
                        "payload": {"source": str(source)},
                    }
                )
                launched = runtime.handle(
                    {
                        "request_id": "gateway-1",
                        "type": "gateway.launch",
                        "payload": {"notebook_id": imported["notebook_id"], "dry_run": True},
                    }
                )
        self.assertEqual(imported["status"], "ok")
        self.assertNotIn("manifest_path", imported)
        self.assertEqual(launched["status"], "ok")
        self.assertTrue(launched["gateway"]["loopback_only"])
        self.assertFalse(launched["gateway"]["terminals_enabled"])

    def test_native_message_framing_has_size_boundaries(self) -> None:
        output = io.BytesIO()
        write_native_message(output, {"type": "companion.status", "request_id": "synthetic"})
        output.seek(0)
        decoded = read_native_message(output)
        self.assertEqual(decoded["request_id"], "synthetic")  # type: ignore[index]
        oversized = io.BytesIO(struct.pack("<I", 100_000))
        with self.assertRaises(ValueError):
            read_native_message(oversized)

    def test_companion_accepts_chunked_browser_notebook_without_persisting_path_or_raw_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = nbformat.writes(
                nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("values = [1, 2, 3]")])
            ).encode("utf-8")
            runtime = CompanionRuntime(storage_root=root / "sessions")
            upload_id = "a" * 32
            started = runtime.handle(
                {
                    "request_id": "upload-1",
                    "type": "notebook.upload.start",
                    "payload": {
                        "upload_id": upload_id,
                        "source_label": "browser-practice.ipynb",
                        "source_sha256": hashlib.sha256(raw).hexdigest(),
                        "total_bytes": len(raw),
                        "total_chunks": 1,
                    },
                }
            )
            chunk = runtime.handle(
                {
                    "request_id": "upload-2",
                    "type": "notebook.upload.chunk",
                    "payload": {
                        "upload_id": upload_id,
                        "chunk_index": 0,
                        "data": base64.b64encode(raw).decode("ascii"),
                    },
                }
            )
            finished = runtime.handle(
                {
                    "request_id": "upload-3",
                    "type": "notebook.upload.finish",
                    "payload": {"upload_id": upload_id},
                }
            )
            stored = "".join(path.read_text(encoding="utf-8") for path in (root / "sessions").glob("*"))

        self.assertEqual(started["status"], "uploading")
        self.assertEqual(chunk["status"], "uploading")
        self.assertEqual(finished["status"], "ok")
        self.assertEqual(finished["manifest"]["source_label"], "browser-practice.ipynb")
        self.assertNotIn(str(root), stored)
        self.assertNotIn(raw.decode("utf-8"), stored)

    def test_companion_rejects_incomplete_or_tampered_notebook_upload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = b'{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}'
            runtime = CompanionRuntime(storage_root=root / "sessions")
            upload_id = "b" * 32
            runtime.handle(
                {
                    "request_id": "upload-bad-1",
                    "type": "notebook.upload.start",
                    "payload": {
                        "upload_id": upload_id,
                        "source_label": "practice.ipynb",
                        "source_sha256": hashlib.sha256(b"different").hexdigest(),
                        "total_bytes": len(raw),
                        "total_chunks": 1,
                    },
                }
            )
            finished = runtime.handle(
                {"request_id": "upload-bad-2", "type": "notebook.upload.finish", "payload": {"upload_id": upload_id}}
            )
            self.assertEqual(finished["status"], "blocked")
            self.assertEqual(runtime.notebook_uploads, {})


if __name__ == "__main__":
    unittest.main()
