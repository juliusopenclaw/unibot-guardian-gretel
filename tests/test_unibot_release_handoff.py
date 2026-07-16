from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from unibot.release_handoff import write_release_handoff
from unibot.public_safety import scan_text


class UniBotReleaseHandoffTests(unittest.TestCase):
    def test_handoff_is_atomic_hash_bound_and_contains_candidate_and_pr(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "handoff"
            result = write_release_handoff(output, repository=repository)

            self.assertEqual(result["status"], "written")
            self.assertEqual(result["candidate_file_count"], 6)
            self.assertEqual(result["provider_calls"], 0)
            self.assertFalse(result["automatic_publication"])
            self.assertFalse(result["automatic_merge"])
            self.assertFalse(result["private_project_files_included"])
            self.assertEqual(result["exam_deployment_status"], "not_cleared")
            self.assertEqual(output.stat().st_mode & 0o077, 0)
            self.assertTrue((output / "candidate" / "RELEASE-MANIFEST.json").is_file())
            self.assertTrue((output / "candidate" / "unibot-mantle.zip").is_file())
            self.assertTrue((output / "UNIBOT-PR-DRAFT.md").is_file())
            self.assertTrue((output / "HANDOFF-MANIFEST.json").is_file())

            manifest = json.loads((output / "HANDOFF-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "public_draft_ready_for_human_review")
            self.assertEqual(manifest["source_commit"], result["source_commit"])
            self.assertFalse(manifest["automatic_merge"])
            self.assertNotIn("/" + "Users/", json.dumps(manifest))
            self.assertEqual(
                scan_text((output / "HANDOFF-MANIFEST.json").read_text(encoding="utf-8"), "handoff-manifest")["status"],
                "pass",
            )
            self.assertEqual(
                scan_text((output / "UNIBOT-PR-DRAFT.md").read_text(encoding="utf-8"), "handoff-pr")["status"],
                "pass",
            )

    def test_handoff_refuses_dirty_source_without_creating_output(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "handoff"
            with patch(
                "unibot.release_candidate._git_provenance",
                return_value={"status": "blocked_dirty_worktree", "commit": "a" * 40, "working_tree_clean": False},
            ):
                result = write_release_handoff(output, repository=repository)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "release_candidate_blocked")
            self.assertFalse(output.exists())

    def test_handoff_does_not_overwrite_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "handoff"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                write_release_handoff(output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
