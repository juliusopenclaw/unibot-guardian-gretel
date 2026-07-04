from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.guardian import guardian_practice_flow  # noqa: E402
from unibot.handoff import (  # noqa: E402
    build_authority_handoff_markdown,
    build_authority_handoff_packet,
    build_authority_handoff_release_claim_alignment,
)
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
        self.assertEqual(packet["release_claim_alignment"]["status"], "ready")
        self.assertEqual(packet["release_claim_alignment"]["public_safety_status"], "pass")
        self.assertIn("exam_controlled", payload)
        self.assertIn("no proctoring", payload)
        self.assertIn("no automatic grading", payload)

    def test_authority_handoff_release_claim_alignment_links_review_board_chain(self) -> None:
        packet = build_authority_handoff_packet()
        alignment = packet["release_claim_alignment"]

        self.assertEqual(
            alignment["schema_version"],
            "unibot-authority-handoff-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("authority_handoff", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("source_card_drift_guard", alignment["required_readiness_check_ids"])
        self.assertIn("redteam", alignment["required_readiness_check_ids"])
        self.assertIn("notebook_template", alignment["required_readiness_check_ids"])
        self.assertIn("compliance_matrix", alignment["required_readiness_check_ids"])
        self.assertIn("public_safety", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("public_safety_required", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("provider_call_requires_explicit_go_and_redaction_receipt", alignment["required_human_gates"])
        self.assertIn("exam clearance", alignment["blocked_claims"])
        self.assertIn("KI detection", alignment["policy"])

    def test_authority_handoff_release_claim_alignment_blocks_approval_language(self) -> None:
        packet = build_authority_handoff_packet()
        packet["status"] = "officially_cleared"
        packet["status_label_de"] = "Freigegeben"
        packet["operating_modes"] = [
            {
                "mode": "exam_controlled",
                "status": "approved",
                "rule": "Incorrect approval claim.",
            }
        ]

        alignment = build_authority_handoff_release_claim_alignment(packet)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("draft_status_not_officially_cleared", alignment["failed_contract_ids"])
        self.assertIn("public_label_non_approval", alignment["failed_contract_ids"])
        self.assertIn("exam_mode_blocked_until_written_clearance", alignment["failed_contract_ids"])

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
        self.assertIn("## Release Claim Alignment", markdown)
        self.assertIn("Status: ready", markdown)

        status, packet = route_request("/api/unibot/authority-packet", {})
        self.assertEqual(status, 200)
        self.assertEqual(packet["status"], "draft_not_officially_cleared")
        self.assertEqual(packet["release_claim_alignment"]["status"], "ready")

        status, response = route_request("/api/unibot/authority-packet-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("## Betriebsmodi", response["markdown"])


if __name__ == "__main__":
    unittest.main()
