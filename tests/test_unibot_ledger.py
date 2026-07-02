from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.guardian import guardian_practice_flow  # noqa: E402
from unibot.ledger import (  # noqa: E402
    append_ledger_event,
    export_public_ledger_summary,
    read_ledger,
    sanitize_event,
    summarize_ledger,
)
from unibot.server import route_request  # noqa: E402


class UniBotLedgerTests(unittest.TestCase):
    def test_sanitize_event_keeps_public_safe_keys_only(self) -> None:
        event = {
            "mode": "practice_overlay",
            "tool": "colab_gemini",
            "task_id": "task-1",
            "skill_tags": ["python_lists"],
            "raw_output_hash": "abc123",
            "classification": ["final_solution"],
            "allowed_hint": "Pruefe den naechsten eigenen Schritt.",
            "help_level": "A4",
            "privacy_flags": [],
            "source_card_ids": ["google-colab-gemini"],
            "student_reflection": "Ich pruefe zuerst den Index.",
            "raw_external_ai_output": "THIS MUST NOT BE STORED",
        }
        record = sanitize_event(event)
        payload = json.dumps(record, ensure_ascii=False)

        self.assertEqual(record["schema_version"], "unibot-guardian-ledger-v1")
        self.assertEqual(record["event"]["help_level"], "A4")
        self.assertFalse(record["event"]["reflection_redacted"])
        self.assertNotIn("THIS MUST NOT BE STORED", payload)
        self.assertNotIn("raw_external_ai_output", payload)

    def test_reflection_privacy_is_redacted(self) -> None:
        record = sanitize_event(
            {
                "help_level": "A2",
                "student_reflection": f"Bitte an {'student'}@example.invalid schreiben.",
            }
        )

        self.assertTrue(record["event"]["reflection_redacted"])
        self.assertEqual(record["event"]["student_reflection"], "")
        self.assertIn("email_address", record["event"]["reflection_privacy_flags"])

    def test_append_read_summary_and_public_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "help_ledger.jsonl"
            flow = guardian_practice_flow(
                task="Python Listen in Colab",
                external_output="Hier ist der komplette Code: import pandas as pd",
                requested_help_level="A4",
                source_card_ids=["google-colab-gemini"],
                student_reflection="Ich schreibe erst den naechsten Test.",
            )
            stored = append_ledger_event(flow["guardian_event"], path=ledger_path)
            self.assertEqual(stored["status"], "stored")
            self.assertTrue(ledger_path.exists())

            rows = read_ledger(ledger_path)
            self.assertEqual(rows["count"], 1)
            self.assertEqual(rows["events"][0]["event"]["help_level"], "A4")
            self.assertNotIn("Hier ist der komplette Code", json.dumps(rows, ensure_ascii=False))

            summary = summarize_ledger(ledger_path)
            self.assertEqual(summary["event_count"], 1)
            self.assertEqual(summary["by_help_level"]["A4"], 1)
            self.assertGreater(summary["blocked_or_flagged_count"], 0)

            public_summary = export_public_ledger_summary(ledger_path)
            self.assertEqual(public_summary["event_count"], 1)
            self.assertNotIn("student_reflection", json.dumps(public_summary, ensure_ascii=False))

    def test_ledger_api_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = str(Path(tmp) / "help_ledger.jsonl")
            flow = guardian_practice_flow(
                task="Boxplot pandas Debugging",
                external_output="Welche Spalte ist dein Messwert?",
                requested_help_level="A2",
                student_reflection="Ich pruefe df.dtypes.",
            )
            status, stored = route_request(
                "/api/unibot/ledger/append",
                {"event": flow["guardian_event"], "ledger_path": ledger_path},
            )
            self.assertEqual(status, 200)
            self.assertEqual(stored["status"], "stored")

            status, listed = route_request("/api/unibot/ledger/list", {"ledger_path": ledger_path})
            self.assertEqual(status, 200)
            self.assertEqual(listed["count"], 1)

            status, summary = route_request("/api/unibot/ledger/public-summary", {"ledger_path": ledger_path})
            self.assertEqual(status, 200)
            self.assertEqual(summary["schema_version"], "unibot-guardian-ledger-summary-v1")

            status, invalid = route_request("/api/unibot/ledger/append", {"event": "not-a-dict"})
            self.assertEqual(status, 400)
            self.assertEqual(invalid["status"], "invalid-event")


if __name__ == "__main__":
    unittest.main()
