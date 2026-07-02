from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.github_issues import build_github_issue_bundle, build_github_issue_bundle_markdown  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def feedback_record() -> dict[str, object]:
    return {
        "feedback_id": "feedback-demo-1",
        "scenario_id": "demo_prompt_card",
        "outcome": "fail",
        "severity": "minor",
        "button_or_endpoint": "Promptkarte erzeugen",
        "private_data_removed": True,
        "has_public_safe_text": False,
        "has_follow_up_note": False,
    }


class UniBotGithubIssueBundleTests(unittest.TestCase):
    def test_issue_bundle_builds_public_safe_github_drafts(self) -> None:
        bundle = build_github_issue_bundle(records=[feedback_record()])
        payload = json.dumps(bundle, ensure_ascii=False)
        issue = bundle["issues"][0]

        self.assertEqual(bundle["schema_version"], "unibot-github-issue-bundle-v1")
        self.assertEqual(bundle["status"], "ready")
        self.assertEqual(bundle["public_safety_status"], "pass")
        self.assertEqual(bundle["issue_count"], 1)
        self.assertIn("title", issue)
        self.assertIn("labels", issue)
        self.assertIn("body", issue)
        self.assertIn("guardian_prompt_cards", issue["labels"])
        self.assertIn("manual", bundle["publishing_note"].lower())
        self.assertNotIn("Promptkarte erzeugen", payload)
        self.assertEqual(scan_text(payload, "github-issue-bundle")["status"], "pass")

    def test_issue_bundle_empty_when_triage_empty(self) -> None:
        bundle = build_github_issue_bundle(
            records=[
                {
                    "feedback_id": "feedback-pass",
                    "scenario_id": "demo_setup",
                    "outcome": "pass",
                    "severity": "info",
                    "button_or_endpoint": "setup",
                }
            ]
        )

        self.assertEqual(bundle["status"], "empty")
        self.assertEqual(bundle["issue_count"], 0)
        self.assertEqual(bundle["public_safety_status"], "pass")

    def test_issue_bundle_markdown_and_api_routes(self) -> None:
        markdown = build_github_issue_bundle_markdown(records=[feedback_record()])

        self.assertIn("# UniBot GitHub Issue Bundle", markdown)
        self.assertIn("demo_prompt_card", markdown)
        self.assertIn("guardian_prompt_cards", markdown)
        self.assertNotIn("Promptkarte erzeugen", markdown)

        status, bundle = route_request("/api/unibot/github-issue-bundle", {"records": [feedback_record()]})
        self.assertEqual(status, 200)
        self.assertEqual(bundle["status"], "ready")

        status, response = route_request("/api/unibot/github-issue-bundle-markdown", {"records": [feedback_record()]})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Public-safe", response["markdown"])

        status, invalid = route_request("/api/unibot/github-issue-bundle", {"records": "not-records"})
        self.assertEqual(status, 400)
        self.assertEqual(invalid["status"], "invalid-records")


if __name__ == "__main__":
    unittest.main()
