from __future__ import annotations

import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from unibot.public_safety import scan_text
from unibot.release_candidate import write_release_candidate_bundle


class UniBotReleaseCandidateTests(unittest.TestCase):
    def test_dirty_source_is_blocked_before_any_artifact_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate"
            with patch(
                "unibot.release_candidate._git_provenance",
                return_value={
                    "status": "blocked_dirty_worktree",
                    "commit": "a" * 40,
                    "working_tree_clean": False,
                },
            ):
                result = write_release_candidate_bundle(output)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "blocked_dirty_worktree")
            self.assertFalse(output.exists())

    def test_bundle_contains_only_public_extension_and_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "unibot-review-candidate"
            result = write_release_candidate_bundle(output)

            self.assertEqual(result["status"], "written")
            self.assertEqual(result["file_count"], 5)
            self.assertEqual(result["exam_deployment_status"], "not_cleared")
            self.assertEqual(result["provider_calls"], 0)
            self.assertFalse(result["learner_content_included"])
            self.assertFalse(result["private_project_files_included"])
            self.assertEqual(output.stat().st_mode & 0o077, 0)
            self.assertEqual(
                sorted(path.name for path in output.iterdir()),
                [
                    "INSTITUTIONAL-MANIFEST.json",
                    "RELEASE-MANIFEST.json",
                    "institutional-presentation.json",
                    "institutional-presentation.md",
                    "unibot-mantle.zip",
                ],
            )

            manifest = json.loads((output / "RELEASE-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "public_draft_not_exam_release")
            self.assertEqual(manifest["exam_deployment_status"], "not_cleared")
            self.assertFalse(manifest["automatic_publication"])
            self.assertFalse(manifest["automatic_merge"])
            self.assertEqual(manifest["source_provenance"]["status"], "verified")
            self.assertTrue(manifest["source_provenance"]["working_tree_clean"])
            self.assertRegex(manifest["source_provenance"]["commit"], re.fullmatch(r"[0-9a-f]{40}").pattern)
            self.assertEqual(manifest["authorship"]["implementation_and_documentation"], "Gretel / Codex")
            self.assertNotIn("/" + "Users/", json.dumps(manifest))

            with zipfile.ZipFile(output / "unibot-mantle.zip") as archive:
                self.assertIn("manifest.json", archive.namelist())
                self.assertNotIn("tests/test_unibot_release_candidate.py", archive.namelist())

            for path in output.glob("*.json"):
                self.assertEqual(scan_text(path.read_text(encoding="utf-8"), path.name)["status"], "pass")
            self.assertEqual(scan_text((output / "institutional-presentation.md").read_text(encoding="utf-8"), "presentation")["status"], "pass")

    def test_existing_output_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate"
            output.mkdir()
            marker = output / "do-not-delete.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                write_release_candidate_bundle(output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
