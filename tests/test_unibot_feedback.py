from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.feedback import (  # noqa: E402
    append_demo_feedback,
    demo_feedback_template,
    export_public_demo_feedback_summary,
    read_demo_feedback,
    summarize_demo_feedback,
    validate_demo_feedback,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def good_feedback() -> dict[str, object]:
    return {
        "scenario_id": "demo_prompt_card",
        "outcome": "fail",
        "severity": "minor",
        "what_i_tried": "Clicked prompt card after entering a synthetic Python-list task.",
        "expected": "Clipboard contains a Socratic prompt.",
        "what_happened": "Clipboard stayed empty.",
        "button_or_endpoint": "Promptkarte erzeugen",
        "public_safe_text": "No private data included.",
        "private_data_removed": True,
    }


class UniBotFeedbackTests(unittest.TestCase):
    def test_feedback_template_is_public_safe(self) -> None:
        template = demo_feedback_template()
        payload = json.dumps(template, ensure_ascii=False)

        self.assertEqual(template["schema_version"], "unibot-demo-feedback-v1")
        self.assertEqual(template["status"], "template")
        self.assertIn("demo_prompt_card", template["allowed_scenario_ids"])
        self.assertIn("what_i_tried", template["required_fields"])
        self.assertEqual(scan_text(payload, "feedback-template")["status"], "pass")

    def test_validate_good_feedback_returns_public_record_without_free_text(self) -> None:
        validation = validate_demo_feedback(good_feedback())
        payload = json.dumps(validation, ensure_ascii=False)

        self.assertEqual(validation["status"], "ok")
        self.assertEqual(validation["issues"], [])
        self.assertIn("feedback_id", validation["public_record"])
        self.assertIn("text_hash", validation["public_record"])
        self.assertNotIn("Clipboard stayed empty", payload)
        self.assertNotIn("Clicked prompt card", payload)

    def test_validate_blocks_private_or_incomplete_feedback(self) -> None:
        unsafe = good_feedback()
        unsafe["public_safe_text"] = f"Contact {'student'}@example.invalid and inspect /" + "Users/student/private.ipynb"
        unsafe["private_data_removed"] = False
        validation = validate_demo_feedback(unsafe)

        self.assertEqual(validation["status"], "blocked")
        self.assertIn("private_data_not_confirmed_removed", validation["issues"])
        self.assertIn("feedback_not_public_safe", validation["issues"])

        missing = validate_demo_feedback({"scenario_id": "demo_prompt_card", "private_data_removed": True})
        self.assertEqual(missing["status"], "blocked")
        self.assertIn("missing_what_i_tried", missing["issues"])

    def test_append_read_and_public_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feedback_path = Path(tmp) / "demo_feedback.jsonl"
            stored = append_demo_feedback(good_feedback(), path=feedback_path)
            self.assertEqual(stored["status"], "stored")
            self.assertTrue(feedback_path.exists())

            listed = read_demo_feedback(feedback_path)
            self.assertEqual(listed["count"], 1)
            summary = summarize_demo_feedback(feedback_path)
            self.assertEqual(summary["feedback_count"], 1)
            self.assertEqual(summary["needs_follow_up_count"], 1)
            self.assertEqual(summary["by_scenario"]["demo_prompt_card"], 1)

            public_summary = export_public_demo_feedback_summary(feedback_path)
            public_payload = json.dumps(public_summary, ensure_ascii=False)
            self.assertEqual(public_summary["feedback_count"], 1)
            self.assertNotIn("what_happened", public_payload)
            self.assertEqual(scan_text(public_payload, "feedback-summary")["status"], "pass")

    def test_blocked_feedback_is_not_stored_and_api_routes_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feedback_path = str(Path(tmp) / "demo_feedback.jsonl")

            status, template = route_request("/api/unibot/demo-feedback/template", {})
            self.assertEqual(status, 200)
            self.assertEqual(template["status"], "template")

            status, validation = route_request("/api/unibot/demo-feedback/validate", {"feedback": good_feedback()})
            self.assertEqual(status, 200)
            self.assertEqual(validation["status"], "ok")

            status, stored = route_request(
                "/api/unibot/demo-feedback/append",
                {"feedback": good_feedback(), "feedback_path": feedback_path},
            )
            self.assertEqual(status, 200)
            self.assertEqual(stored["status"], "stored")

            unsafe = good_feedback()
            unsafe["public_safe_text"] = "api" + "_key = sk-test"
            status, blocked = route_request(
                "/api/unibot/demo-feedback/append",
                {"feedback": unsafe, "feedback_path": feedback_path},
            )
            self.assertEqual(status, 200)
            self.assertEqual(blocked["status"], "blocked_not_stored")

            status, listed = route_request("/api/unibot/demo-feedback/list", {"feedback_path": feedback_path})
            self.assertEqual(status, 200)
            self.assertEqual(listed["count"], 1)

            status, summary = route_request("/api/unibot/demo-feedback/public-summary", {"feedback_path": feedback_path})
            self.assertEqual(status, 200)
            self.assertEqual(summary["feedback_count"], 1)

            status, invalid = route_request("/api/unibot/demo-feedback/append", {"feedback": "not-feedback"})
            self.assertEqual(status, 400)
            self.assertEqual(invalid["status"], "invalid-feedback")


if __name__ == "__main__":
    unittest.main()
