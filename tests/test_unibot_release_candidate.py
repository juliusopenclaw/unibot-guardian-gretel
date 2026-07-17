from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from unibot.public_safety import scan_text
from unibot.release_audit import audit_release_candidate
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
            self.assertEqual(result["file_count"], 13)
            self.assertEqual(result["exam_deployment_status"], "not_cleared")
            self.assertEqual(result["provider_calls"], 0)
            self.assertFalse(result["learner_content_included"])
            self.assertFalse(result["private_project_files_included"])
            self.assertEqual(output.stat().st_mode & 0o077, 0)
            self.assertEqual(
                sorted(path.name for path in output.iterdir()),
                [
                    "INSTITUTIONAL-MANIFEST.json",
                    "PUBLIC-DEMO.md",
                    "RELEASE-MANIFEST.json",
                    "REVIEW-START-HERE.md",
                    "institutional-accessibility-walkthrough.md",
                    "institutional-plain-language-brief.md",
                    "institutional-presentation.json",
                    "institutional-presentation.md",
                    "institutional-review-decision-template.md",
                    "review-board-packet.json",
                    "review-board-packet.md",
                    "synthetic_python_practice.ipynb",
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
            self.assertRegex(manifest["source_provenance"]["commit"], r"^[0-9a-f]{40}$")
            institutional_manifest = json.loads((output / "INSTITUTIONAL-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(institutional_manifest["source_commit"], manifest["source_provenance"]["commit"])
            self.assertEqual(institutional_manifest["source_provenance"]["status"], "verified")
            self.assertRegex(manifest["demo_fixture_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(manifest["public_demo_markdown_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(manifest["authorship"]["implementation_and_documentation"], "Gretel / Codex")
            self.assertNotIn("/" + "Users/", json.dumps(manifest))

            with zipfile.ZipFile(output / "unibot-mantle.zip") as archive:
                self.assertIn("manifest.json", archive.namelist())
                self.assertNotIn("tests/test_unibot_release_candidate.py", archive.namelist())

            self.assertEqual(
                scan_text(
                    (output / "synthetic_python_practice.ipynb").read_text(encoding="utf-8"),
                    "synthetic_python_practice.ipynb",
                )["status"],
                "pass",
            )
            self.assertEqual(scan_text((output / "PUBLIC-DEMO.md").read_text(encoding="utf-8"), "PUBLIC-DEMO.md")["status"], "pass")
            self.assertIn(
                "Nutzung wird weder im Sitzungsjournal noch im freiwilligen Export protokolliert",
                (output / "REVIEW-START-HERE.md").read_text(encoding="utf-8"),
            )
            review_start = (output / "REVIEW-START-HERE.md").read_text(encoding="utf-8")
            self.assertIn("Hier anfangen", review_start)
            self.assertIn("Hilfe A0 bis A4", review_start)
            self.assertIn("15-Minuten-Demo; vollständige Review etwa 25 Minuten", review_start)
            self.assertIn("Die 15 Minuten sind nur der kurze Produkt-Demo-Teil", review_start)
            self.assertIn("practice_only", review_start)
            self.assertIn("freiwillige Übung, kein Prüfungseinsatz", review_start)
            self.assertIn("Keine finale Lösung", review_start)
            self.assertIn("Screenreader, 200-Prozent-Zoom/Reflow", review_start)
            self.assertNotIn("200-Prozent-Zoom sind technisch getestet", review_start)
            self.assertEqual(
                scan_text((output / "REVIEW-START-HERE.md").read_text(encoding="utf-8"), "REVIEW-START-HERE.md")["status"],
                "pass",
            )
            public_demo = (output / "PUBLIC-DEMO.md").read_text(encoding="utf-8")
            self.assertIn("practice_only", public_demo)
            self.assertIn("Ohne ausdrückliche Bestätigung", public_demo)

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

    def test_release_audit_verifies_hashes_and_source_commit_without_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate"
            result = write_release_candidate_bundle(output)
            self.assertEqual(result["status"], "written")

            audit = audit_release_candidate(output, repository=Path(__file__).resolve().parents[1])

            self.assertEqual(audit["status"], "pass", audit["issues"])
            self.assertTrue(audit["candidate_directory_checked"])
            self.assertTrue(audit["source_commit_match"])
            self.assertNotIn("institutional_source_commit_mismatch", audit["issues"])
            self.assertEqual(audit["recorded_file_count"], 12)
            self.assertEqual(audit["public_safety_status"], "pass")
            self.assertFalse(audit["side_effects"]["files_written"])
            self.assertFalse(audit["side_effects"]["network_called"])
            self.assertFalse(audit["side_effects"]["git_changed"])

    def test_release_audit_blocks_tampered_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate"
            result = write_release_candidate_bundle(output)
            self.assertEqual(result["status"], "written")
            (output / "institutional-presentation.md").write_text("tampered", encoding="utf-8")

            audit = audit_release_candidate(output)

            self.assertEqual(audit["status"], "blocked")
            self.assertIn("release_file_hash_mismatch:institutional-presentation.md", audit["issues"])

    def test_release_audit_blocks_institutional_exam_status_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate"
            result = write_release_candidate_bundle(output)
            self.assertEqual(result["status"], "written")

            presentation_path = output / "institutional-presentation.json"
            presentation = json.loads(presentation_path.read_text(encoding="utf-8"))
            presentation["deployment_status"] = "approved"
            presentation_path.write_text(json.dumps(presentation), encoding="utf-8")

            audit = audit_release_candidate(output)

            self.assertEqual(audit["status"], "blocked")
            self.assertIn("release_file_hash_mismatch:institutional-presentation.json", audit["issues"])
            self.assertIn("institutional_presentation_deployment_mismatch:deployment_status", audit["issues"])

    def test_release_audit_blocks_institutional_evidence_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate"
            result = write_release_candidate_bundle(output)
            self.assertEqual(result["status"], "written")

            presentation_path = output / "institutional-presentation.json"
            presentation = json.loads(presentation_path.read_text(encoding="utf-8"))
            presentation["evidence_hash"] = "0" * 64
            presentation_path.write_text(json.dumps(presentation), encoding="utf-8")

            audit = audit_release_candidate(output)

            self.assertEqual(audit["status"], "blocked")
            self.assertIn("release_file_hash_mismatch:institutional-presentation.json", audit["issues"])
            self.assertIn("release_institutional_evidence_hash_mismatch", audit["issues"])
            self.assertIn("institutional_manifest_evidence_hash_mismatch", audit["issues"])


if __name__ == "__main__":
    unittest.main()
