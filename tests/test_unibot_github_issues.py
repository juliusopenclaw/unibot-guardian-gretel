from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.github_issues import (  # noqa: E402
    build_github_issue_bundle,
    build_github_issue_bundle_markdown,
    build_issue_evidence_traceability,
    build_issue_review_contract,
)
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
        self.assertIn("review_contract", bundle)
        self.assertIn("evidence_traceability", bundle)
        self.assertEqual(bundle["evidence_traceability"]["status"], "ready")
        self.assertEqual(bundle["evidence_traceability"]["public_safety_status"], "pass")
        self.assertTrue(bundle["evidence_traceability"]["manual_publish_only"])
        self.assertIn("title", issue)
        self.assertIn("labels", issue)
        self.assertIn("body", issue)
        self.assertIn("review_checklist", issue)
        self.assertIn("evidence_requirements", issue)
        self.assertEqual(issue["publication_gate"], "human_review_before_github_create")
        self.assertTrue(issue["manual_publish_only"])
        self.assertIn("evaluation_packet", issue["readiness_check_ids"])
        self.assertIn("source_card_drift_guard", issue["readiness_check_ids"])
        self.assertIn("publication_package", issue["readiness_check_ids"])
        self.assertIn("release_runbook", issue["readiness_check_ids"])
        self.assertIn("review_board_packet", issue["readiness_check_ids"])
        self.assertIn("vanlehn-2011", issue["source_card_ids"])
        self.assertIn("human_review_before_github_create", issue["human_gates"])
        self.assertIn("human_submission_review_required", issue["human_gates"])
        self.assertIn("guardian_prompt_cards", issue["labels"])
        self.assertIn("manual", bundle["publishing_note"].lower())
        self.assertNotIn("Promptkarte erzeugen", payload)
        self.assertEqual(scan_text(payload, "github-issue-bundle")["status"], "pass")

    def test_issue_evidence_traceability_maps_issues_to_manual_gates(self) -> None:
        bundle = build_github_issue_bundle(records=[feedback_record()])
        traceability = build_issue_evidence_traceability(bundle["issues"])

        self.assertEqual(traceability["schema_version"], "unibot-github-issue-evidence-traceability-v1")
        self.assertEqual(traceability["status"], "ready")
        self.assertEqual(traceability["public_safety_status"], "pass")
        self.assertEqual(traceability["issue_count"], 1)
        self.assertTrue(traceability["manual_publish_only"])
        self.assertEqual(traceability["publication_gate"], "human_review_before_github_create")
        self.assertIn("unibot-readiness-evidence-snapshot-v1", traceability["readiness_snapshot_contract"]["expected_schema_version"])
        self.assertIn("evaluation_packet", traceability["unique_readiness_check_ids"])
        self.assertIn("source_card_drift_guard", traceability["unique_readiness_check_ids"])
        self.assertIn("publication_package", traceability["unique_readiness_check_ids"])
        self.assertIn("release_runbook", traceability["unique_readiness_check_ids"])
        self.assertIn("review_board_packet", traceability["unique_readiness_check_ids"])
        self.assertIn("vanlehn-2011", traceability["unique_source_card_ids"])
        self.assertIn("public_safety_required", traceability["required_human_gates"])
        self.assertIn("human_submission_review_required", traceability["required_human_gates"])
        claim_contract = traceability["manual_publication_claim_contract"]
        self.assertEqual(
            claim_contract["expected_schema_version"],
            "unibot-github-issue-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            claim_contract["required_publication_release_review_board_schema_version"],
            "unibot-publication-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(
            claim_contract["required_review_board_thesis_evaluation_schema_version"],
            "unibot-review-board-thesis-evaluation-claim-alignment-v1",
        )
        self.assertTrue(claim_contract["manual_publish_only"])
        self.assertEqual(traceability["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(traceability["missing_release_review_board_claim_human_gates"], [])

    def test_issue_review_contract_blocks_auto_publish_and_high_stakes_claims(self) -> None:
        contract = build_issue_review_contract()
        payload = json.dumps(contract, ensure_ascii=False)

        self.assertEqual(contract["schema_version"], "unibot-github-issue-review-contract-v1")
        self.assertTrue(contract["manual_publish_only"])
        self.assertEqual(contract["publication_gate"], "human_review_before_github_create")
        self.assertIn("suggested focused test", " ".join(contract["evidence_requirements"]))
        self.assertIn("does not claim exam clearance", " ".join(contract["review_checklist"]))
        self.assertEqual(scan_text(payload, "github-issue-review-contract")["status"], "pass")

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
        self.assertIn("Review checklist", markdown)
        self.assertIn("Evidence requirements", markdown)
        self.assertIn("Manual publish only: True", markdown)
        self.assertIn("Readiness checks:", markdown)
        self.assertIn("Source cards:", markdown)
        self.assertIn("Human gates:", markdown)
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
