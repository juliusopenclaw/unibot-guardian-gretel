from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.feedback import append_demo_feedback  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.triage import build_feedback_triage, build_feedback_triage_markdown  # noqa: E402


def public_record(
    scenario_id: str = "demo_prompt_card",
    outcome: str = "fail",
    severity: str = "minor",
) -> dict[str, object]:
    return {
        "feedback_id": f"{scenario_id}-{outcome}-{severity}",
        "scenario_id": scenario_id,
        "outcome": outcome,
        "severity": severity,
        "button_or_endpoint": "Promptkarte erzeugen",
        "private_data_removed": True,
        "has_public_safe_text": False,
        "has_follow_up_note": False,
    }


class UniBotTriageTests(unittest.TestCase):
    def test_triage_prioritizes_feedback_and_builds_issue_drafts(self) -> None:
        triage = build_feedback_triage(
            records=[
                public_record("demo_adaptive_tasks", "confusing", "minor"),
                public_record("demo_block_solution", "blocked", "minor"),
                public_record("demo_prompt_card", "fail", "major"),
                public_record("demo_setup", "pass", "info"),
            ]
        )
        payload = json.dumps(triage, ensure_ascii=False)

        self.assertEqual(triage["schema_version"], "unibot-feedback-triage-v1")
        self.assertEqual(triage["status"], "ready")
        self.assertEqual(triage["public_safety_status"], "pass")
        self.assertEqual(triage["feedback_count"], 4)
        self.assertEqual(triage["triage_count"], 3)
        self.assertEqual(triage["items"][0]["priority"], "P0")
        self.assertEqual(triage["items"][0]["component"], "postfilter")
        self.assertIn("issue_draft", triage["items"][0])
        self.assertIn("publication_package", triage["items"][0]["readiness_check_ids"])
        self.assertIn("release_runbook", triage["items"][0]["readiness_check_ids"])
        self.assertIn("review_board_packet", triage["items"][0]["readiness_check_ids"])
        self.assertIn("human_review_before_github_create", triage["items"][0]["human_gates"])
        self.assertIn("human_submission_review_required", triage["items"][0]["human_gates"])
        self.assertTrue(triage["items"][0]["manual_publish_only"])
        claim_alignment = triage["claim_alignment"]
        self.assertEqual(claim_alignment["status"], "ready")
        self.assertEqual(claim_alignment["public_safety_status"], "pass")
        self.assertEqual(
            claim_alignment["manual_publication_claim_contract"]["expected_schema_version"],
            "unibot-feedback-triage-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            claim_alignment["manual_publication_claim_contract"]["required_github_issue_claim_schema_version"],
            "unibot-github-issue-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            claim_alignment["manual_publication_claim_contract"][
                "required_publication_release_review_board_schema_version"
            ],
            "unibot-publication-release-review-board-claim-alignment-v1",
        )
        self.assertTrue(claim_alignment["manual_publication_claim_contract"]["manual_publish_only"])
        self.assertIn("github_issue_bundle", claim_alignment["unique_readiness_check_ids"])
        self.assertIn("human_submission_review_required", claim_alignment["required_human_gates"])
        self.assertEqual(claim_alignment["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(claim_alignment["missing_release_review_board_claim_human_gates"], [])
        self.assertNotIn("Promptkarte erzeugen", payload)
        self.assertEqual(scan_text(payload, "triage")["status"], "pass")

    def test_triage_empty_when_no_follow_up_needed(self) -> None:
        triage = build_feedback_triage(records=[public_record("demo_setup", "pass", "info")])

        self.assertEqual(triage["status"], "empty")
        self.assertEqual(triage["triage_count"], 0)
        self.assertEqual(triage["public_safety_status"], "pass")

    def test_triage_from_stored_feedback_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feedback_path = Path(tmp) / "demo_feedback.jsonl"
            stored = append_demo_feedback(
                {
                    "scenario_id": "demo_notebook_template",
                    "outcome": "fail",
                    "severity": "minor",
                    "what_i_tried": "Clicked notebook template with synthetic task.",
                    "expected": "Notebook JSON is copied.",
                    "what_happened": "Nothing appeared in clipboard.",
                    "button_or_endpoint": "Notebook-Vorlage kopieren",
                    "public_safe_text": "No private data included.",
                    "private_data_removed": True,
                },
                path=feedback_path,
            )
            self.assertEqual(stored["status"], "stored")

            triage = build_feedback_triage(path=feedback_path)
            markdown = build_feedback_triage_markdown(path=feedback_path)

            self.assertEqual(triage["status"], "ready")
            self.assertEqual(triage["items"][0]["component"], "notebooks")
            self.assertIn("# UniBot Demo Feedback Triage", markdown)
            self.assertIn("demo_notebook_template", markdown)
            self.assertNotIn("Nothing appeared", markdown)

    def test_triage_api_routes(self) -> None:
        status, triage = route_request(
            "/api/unibot/demo-feedback/triage",
            {"records": [public_record("demo_redteam_smoke", "blocked", "critical")]},
        )

        self.assertEqual(status, 200)
        self.assertEqual(triage["status"], "ready")
        self.assertEqual(triage["items"][0]["priority"], "P0")

        status, response = route_request(
            "/api/unibot/demo-feedback/triage-markdown",
            {"records": [public_record("demo_allowed_flow_and_ledger", "fail", "minor")]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("ledger_and_scoring", response["markdown"])

        status, invalid = route_request("/api/unibot/demo-feedback/triage", {"records": "not-records"})
        self.assertEqual(status, 400)
        self.assertEqual(invalid["status"], "invalid-records")


if __name__ == "__main__":
    unittest.main()
