from __future__ import annotations

import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from unibot.cli import main
from unibot.public_safety import scan_text
from unibot.release_candidate import write_release_candidate_bundle
from unibot.release_pr import build_release_pr_draft, write_release_pr_draft


class UniBotReleasePrDraftTests(unittest.TestCase):
    def test_pr_draft_is_hash_bound_public_safe_and_human_gated(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate"
            candidate_result = write_release_candidate_bundle(candidate)
            self.assertEqual(candidate_result["status"], "written")

            draft = build_release_pr_draft(candidate, repository=repository)

            self.assertEqual(draft["schema_version"], "UniBotReleasePrDraftV1")
            self.assertEqual(draft["status"], "ready_for_human_review")
            self.assertFalse(draft["automatic_publication"])
            self.assertFalse(draft["automatic_merge"])
            self.assertEqual(draft["provider_calls"], 0)
            self.assertEqual(draft["exam_deployment_status"], "not_cleared")
            self.assertIn("Julius", draft["body"])
            self.assertIn("Gretel / Codex", draft["body"])
            self.assertIn("Institutionelle Prüfung", draft["body"])
            self.assertIn("Öffentliche Demo-Fixture-SHA-256", draft["body"])
            self.assertIn("Öffentlicher Demo-Ablauf-SHA-256", draft["body"])
            self.assertIn("Einfache institutionelle Kurzinfo-SHA-256", draft["body"])
            self.assertIn("Drei Golden Rules (3GR)", draft["body"])
            self.assertIn("Gitleaks v3", draft["body"])
            self.assertRegex(draft["demo_fixture_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(draft["public_demo_markdown_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(draft["institutional_plain_language_brief_sha256"], r"^[0-9a-f]{64}$")
            self.assertNotIn("/" + "Users/", draft["body"])
            self.assertEqual(scan_text(draft["body"], "pr-draft-test")["status"], "pass")

            output = Path(temporary) / "UNIBOT-PR-DRAFT.md"
            written = write_release_pr_draft(output, candidate, repository=repository)
            self.assertEqual(written["status"], "ready_for_human_review")
            self.assertTrue(output.is_file())
            self.assertEqual(output.stat().st_mode & 0o077, 0)
            self.assertEqual(written["output_bytes"], output.stat().st_size)

    def test_pr_draft_blocks_when_source_worktree_is_dirty(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate"
            result = write_release_candidate_bundle(candidate)
            self.assertEqual(result["status"], "written")
            with patch("unibot.release_audit._current_worktree_clean", return_value=False):
                draft = build_release_pr_draft(candidate, repository=repository)
            self.assertEqual(draft["status"], "blocked")
            self.assertIn("candidate_source_worktree_not_clean", draft["audit_issues"])

    def test_cli_writes_pr_draft_without_network_or_publication(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate"
            result = write_release_candidate_bundle(candidate)
            self.assertEqual(result["status"], "written")
            output = Path(temporary) / "pr.md"
            with io.StringIO() as stdout, redirect_stdout(stdout):
                exit_code = main(
                    [
                        "release",
                        "pr-draft",
                        "--candidate",
                        str(candidate),
                        "--output",
                        str(output),
                        "--repo",
                        str(repository),
                    ]
                )
                raw_stdout = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            payload = json.loads(raw_stdout)
            self.assertEqual(payload["status"], "ready_for_human_review")
            self.assertIn("UniBot", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
