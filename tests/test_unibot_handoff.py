from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.guardian import guardian_practice_flow  # noqa: E402
from unibot.handoff import build_authority_handoff_markdown, build_authority_handoff_packet  # noqa: E402
from unibot.ledger import append_ledger_event  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotHandoffTests(unittest.TestCase):
    def test_authority_packet_contains_required_review_sections(self) -> None:
        packet = build_authority_handoff_packet()
        payload = json.dumps(packet, ensure_ascii=False)

        self.assertEqual(packet["schema_version"], "unibot-authority-handoff-v1")
        self.assertEqual(packet["status"], "draft_not_officially_cleared")
        self.assertIn("nicht offiziell freigegeben", packet["status_label_de"])
        self.assertIn("Pruefungsamt", packet["intended_reviewers"])
        self.assertIn("Inklusionsbuero / Nachteilsausgleich-Stelle", packet["intended_reviewers"])
        self.assertIn("Datenschutz", packet["intended_reviewers"])
        self.assertEqual(packet["evidence"]["redteam"]["status"], "pass")
        self.assertEqual(packet["evidence"]["notebook_audit"]["status"], "pass")
        self.assertEqual(packet["evidence"]["compliance_matrix"]["status"], "draft_ready_for_authority_review")
        self.assertEqual(packet["evidence"]["compliance_matrix"]["public_safety_status"], "pass")
        self.assertGreaterEqual(packet["evidence"]["source_card_count"], 10)
        self.assertIn("exam_controlled", payload)
        self.assertIn("no proctoring", payload)
        self.assertIn("no automatic grading", payload)

    def test_authority_packet_is_public_safe_and_no_raw_ai_output(self) -> None:
        packet_text = json.dumps(build_authority_handoff_packet(), ensure_ascii=False)

        self.assertNotIn("werte = [1, 2, 3]", packet_text)
        self.assertNotIn("raw_external_ai_output", packet_text)
        self.assertNotIn("solution_key", packet_text)
        self.assertNotIn("official_grade", packet_text)
        self.assertNotIn("health details", packet_text.lower())
        self.assertIn("raw external KI outputs", packet_text)

    def test_authority_packet_uses_ledger_public_summary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "help_ledger.jsonl"
            flow = guardian_practice_flow(
                task="Python Listen in Colab",
                external_output="Welche Spalte ist dein Messwert?",
                requested_help_level="A2",
                student_reflection="Ich pruefe zuerst df.dtypes.",
            )
            append_ledger_event(flow["guardian_event"], ledger_path)

            packet = build_authority_handoff_packet(str(ledger_path))
            summary = packet["evidence"]["ledger_public_summary"]

            self.assertEqual(summary["event_count"], 1)
            self.assertNotIn("student_reflection", json.dumps(summary, ensure_ascii=False))
            self.assertNotIn("Ich pruefe zuerst", json.dumps(packet, ensure_ascii=False))

    def test_authority_packet_markdown_and_api_routes(self) -> None:
        markdown = build_authority_handoff_markdown()
        self.assertIn("# UniBot Guardian Handoff Packet", markdown)
        self.assertIn("Status: Entwurf", markdown)
        self.assertIn("Red-Team: pass", markdown)
        self.assertIn("Compliance Matrix", markdown)

        status, packet = route_request("/api/unibot/authority-packet", {})
        self.assertEqual(status, 200)
        self.assertEqual(packet["status"], "draft_not_officially_cleared")

        status, response = route_request("/api/unibot/authority-packet-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("## Betriebsmodi", response["markdown"])


if __name__ == "__main__":
    unittest.main()
