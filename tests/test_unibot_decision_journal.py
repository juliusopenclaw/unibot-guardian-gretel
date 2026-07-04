from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.decision_journal import (  # noqa: E402
    append_decision_request_journal_event,
    append_prepared_request_to_journal,
    build_decision_journal_release_claim_alignment,
    decision_journal_hash,
    decision_request_journal_hash,
    read_decision_journal,
    sanitize_decision_journal_event,
    summarize_decision_journal,
    synthetic_decision_journal_workspace_card,
)
from unibot.decision_request import build_stakeholder_decision_request, build_stakeholder_decision_request_markdown  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotDecisionJournalTests(unittest.TestCase):
    def test_prepared_request_event_is_hash_only_and_public_safe(self) -> None:
        request = build_stakeholder_decision_request()
        markdown = build_stakeholder_decision_request_markdown()

        record = sanitize_decision_journal_event(
            {
                "event_type": "decision_request_prepared",
                "request": request,
                "markdown": markdown,
            }
        )
        payload = json.dumps(record, ensure_ascii=False)

        self.assertEqual(record["schema_version"], "unibot-stakeholder-decision-journal-v1")
        self.assertEqual(record["artifact_type"], "unibot_stakeholder_decision_journal_record")
        self.assertEqual(record["status"], "accepted")
        self.assertEqual(record["public_safety_status"], "pass")
        self.assertEqual(record["event"]["event_type"], "decision_request_prepared")
        self.assertTrue(record["event"]["request_hash"])
        self.assertTrue(record["event"]["markdown_hash"])
        self.assertFalse(record["event"]["raw_text_stored"])
        self.assertFalse(record["event"]["tool_sent_message"])
        self.assertNotIn(markdown, payload)
        self.assertEqual(scan_text(payload, "decision-journal-prepared-test")["status"], "pass")

    def test_decision_journal_release_claim_alignment_is_hash_only_and_gate_bound(self) -> None:
        alignment = build_decision_journal_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-stakeholder-decision-journal-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertIn("decision_request_prepared", alignment["event_types"])
        self.assertIn("decision_request_receipt_validated", alignment["event_types"])
        self.assertIn("stakeholder_decision_journal", alignment["required_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["required_readiness_check_ids"])
        self.assertIn("stakeholder_decision_request", alignment["required_readiness_check_ids"])
        self.assertIn("stakeholder_submission_bundle", alignment["required_readiness_check_ids"])
        self.assertIn("data_protection_screening", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["workspace_card_decision_journal_gate_linked"])
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "pandas")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_decision_journal_gate_linked"])
        self.assertIn("raw written decision storage", alignment["blocked_claims"])
        self.assertIn("tool-sent stakeholder message", alignment["blocked_claims"])
        self.assertIn("automatic gate change", alignment["blocked_claims"])

    def test_decision_journal_hash_helpers_link_records_and_request_receipts(self) -> None:
        request = build_stakeholder_decision_request()
        record = sanitize_decision_journal_event(
            {
                "event_type": "decision_request_prepared",
                "request": request,
            }
        )
        events = [record["event"]]

        self.assertTrue(decision_journal_hash([record]))
        self.assertTrue(decision_request_journal_hash(events))
        self.assertNotEqual(decision_journal_hash([record]), decision_request_journal_hash(events))

    def test_decision_journal_release_claim_alignment_rejects_unlinked_workspace_card_hashes(self) -> None:
        request = build_stakeholder_decision_request()
        receipt = dict(request["receipt_template"])
        receipt.update(
            {
                "manual_submission_status": "sent_for_human_review",
                "channel": "synthetic manual review channel",
                "submission_reference": "synthetic hash-only journal reference",
            }
        )
        records = [
            sanitize_decision_journal_event(
                {
                    "event_type": "decision_request_prepared",
                    "request": request,
                }
            ),
            sanitize_decision_journal_event(
                {
                    "event_type": "decision_request_receipt_validated",
                    "receipt": receipt,
                }
            ),
        ]
        card = synthetic_decision_journal_workspace_card()
        card["workspace_card_summary"]["checkpoint_hash"] = "x"
        card["workspace_card_summary"]["task_hash"] = "x"

        alignment = build_decision_journal_release_claim_alignment(
            records,
            python_exam_local_cycle_operator_workspace_card=card,
        )

        self.assertEqual(alignment["status"], "needs_review")
        self.assertFalse(alignment["workspace_card_decision_journal_gate_linked"])
        self.assertIn("workspace_card_decision_journal_gate_linked", alignment["failed_contract_ids"])

    def test_decision_journal_release_claim_alignment_blocks_raw_or_tool_sent_records(self) -> None:
        request = build_stakeholder_decision_request()
        record = sanitize_decision_journal_event(
            {
                "event_type": "decision_request_prepared",
                "request": request,
                "tool_sent_message": True,
            }
        )

        alignment = build_decision_journal_release_claim_alignment([record])

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("all_records_accepted_and_public_safe", alignment["failed_contract_ids"])
        self.assertIn("records_store_no_raw_text_or_tool_send", alignment["failed_contract_ids"])
        self.assertIn("receipt_event_hash_only_no_gate_change", alignment["failed_contract_ids"])
        self.assertIn("prepared_and_receipt_events_present", alignment["failed_contract_ids"])

    def test_receipt_event_accepts_manual_receipt_and_blocks_tool_send(self) -> None:
        request = build_stakeholder_decision_request()
        receipt = dict(request["receipt_template"])
        receipt.update(
            {
                "manual_submission_status": "sent_for_human_review",
                "channel": "manual review channel",
                "submission_reference": "synthetic manual request journal reference",
            }
        )

        record = sanitize_decision_journal_event(
            {
                "event_type": "decision_request_receipt_validated",
                "receipt": receipt,
            }
        )
        payload = json.dumps(record, ensure_ascii=False)

        self.assertEqual(record["status"], "accepted")
        self.assertEqual(record["event"]["receipt_validation_status"], "ok_manual_request_receipt")
        self.assertTrue(record["event"]["submission_reference_hash"])
        self.assertFalse(record["event"]["raw_submission_reference_stored"])
        self.assertNotIn("synthetic manual request journal reference", payload)

        invalid = dict(receipt)
        invalid["tool_sent_message"] = True
        blocked = sanitize_decision_journal_event(
            {
                "event_type": "decision_request_receipt_validated",
                "receipt": invalid,
            }
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("receipt_validation_blocked", blocked["event"]["issues"])

    def test_journal_append_read_and_summary(self) -> None:
        request = build_stakeholder_decision_request()
        markdown = build_stakeholder_decision_request_markdown()
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_path = Path(temp_dir) / "decision_journal.jsonl"
            stored = append_decision_request_journal_event(
                {
                    "event_type": "decision_request_prepared",
                    "request": request,
                    "markdown": markdown,
                },
                path=journal_path,
            )

            self.assertEqual(stored["status"], "stored")
            self.assertTrue(journal_path.exists())
            listed = read_decision_journal(journal_path)
            self.assertEqual(listed["count"], 1)
            summary = summarize_decision_journal(journal_path)
            self.assertEqual(summary["event_count"], 1)
            self.assertEqual(summary["by_event_type"]["decision_request_prepared"], 1)
            self.assertEqual(summary["by_lane"]["rights_privacy_local_extraction"], 1)
            self.assertIn("do not authorize", summary["gate_policy"])

    def test_append_prepared_request_and_api_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_path = str(Path(temp_dir) / "decision_journal.jsonl")
            markdown = build_stakeholder_decision_request_markdown()

            stored = append_prepared_request_to_journal(markdown=markdown, path=journal_path)
            self.assertEqual(stored["status"], "stored")

            status, listed = route_request(
                "/api/unibot/stakeholder/decision-journal/list",
                {"journal_path": journal_path},
            )
            self.assertEqual(status, 200)
            self.assertEqual(listed["count"], 1)

            status, summary = route_request(
                "/api/unibot/stakeholder/decision-journal/summary",
                {"journal_path": journal_path},
            )
            self.assertEqual(status, 200)
            self.assertEqual(summary["event_count"], 1)

            receipt = dict(build_stakeholder_decision_request()["receipt_template"])
            receipt.update(
                {
                    "manual_submission_status": "sent_for_human_review",
                    "channel": "manual review channel",
                    "submission_reference": "synthetic api receipt",
                }
            )
            status, stored_receipt = route_request(
                "/api/unibot/stakeholder/decision-journal/append",
                {
                    "journal_path": journal_path,
                    "event": {
                        "event_type": "decision_request_receipt_validated",
                        "receipt": receipt,
                    },
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(stored_receipt["status"], "stored")

            status, summary = route_request(
                "/api/unibot/stakeholder/decision-journal/summary",
                {"journal_path": journal_path},
            )
            self.assertEqual(status, 200)
            self.assertEqual(summary["event_count"], 2)
            self.assertEqual(summary["sent_receipt_count"], 1)


if __name__ == "__main__":
    unittest.main()
