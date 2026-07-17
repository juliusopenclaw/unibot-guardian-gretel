from __future__ import annotations

import json
import tempfile
import unittest
import hashlib
from pathlib import Path
from unittest.mock import patch

from unibot.release_handoff import write_release_handoff
from unibot.public_safety import scan_text
from unibot.provenance import public_source_provenance


class UniBotReleaseHandoffTests(unittest.TestCase):
    def test_handoff_is_atomic_hash_bound_and_contains_candidate_and_pr(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "handoff"
            result = write_release_handoff(output, repository=repository)

            self.assertEqual(result["status"], "written")
            self.assertEqual(result["candidate_file_count"], 13)
            self.assertEqual(result["provider_calls"], 0)
            self.assertFalse(result["automatic_publication"])
            self.assertFalse(result["automatic_merge"])
            self.assertFalse(result["private_project_files_included"])
            self.assertEqual(result["exam_deployment_status"], "not_cleared")
            self.assertEqual(output.stat().st_mode & 0o077, 0)
            self.assertTrue((output / "candidate" / "RELEASE-MANIFEST.json").is_file())
            self.assertTrue((output / "candidate" / "unibot-mantle.zip").is_file())
            self.assertTrue((output / "candidate" / "synthetic_python_practice.ipynb").is_file())
            self.assertTrue((output / "candidate" / "PUBLIC-DEMO.md").is_file())
            self.assertTrue((output / "candidate" / "REVIEW-START-HERE.md").is_file())
            self.assertTrue((output / "candidate" / "review-board-packet.json").is_file())
            self.assertTrue((output / "candidate" / "review-board-packet.md").is_file())
            self.assertTrue((output / "UNIBOT-PR-DRAFT.md").is_file())
            self.assertTrue((output / "HANDOFF-MANIFEST.json").is_file())

            manifest = json.loads((output / "HANDOFF-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "public_draft_ready_for_human_review")
            self.assertEqual(manifest["source_commit"], result["source_commit"])
            self.assertRegex(manifest["demo_fixture_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(manifest["public_demo_markdown_sha256"], r"^[0-9a-f]{64}$")
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

    def test_handoff_binds_metadata_only_colab_canary_to_source_commit(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canary = root / "colab-canary.json"
            source_commit = str(public_source_provenance(repository)["commit"])
            canary.write_text(
                json.dumps(
                    {
                        "schema_version": "UniBotLiveColabCanaryV1",
                        "status": "pass",
                        "source_commit": source_commit,
                        "provider_calls": 0,
                        "source_text_omitted": True,
                        "raw_cell_text_persisted": False,
                        "notebook_output_read": False,
                        "capture_status": "manual_selection_required",
                        "adapter": "manual_selection",
                        "confidence": "low",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            canary.chmod(0o600)
            output = root / "handoff"
            result = write_release_handoff(output, repository=repository, colab_canary=canary)

            self.assertEqual(result["status"], "written")
            self.assertIn("COLAB-CANARY.json", result["output_file_names"])
            self.assertEqual(
                result["colab_canary_sha256"], hashlib.sha256((output / "COLAB-CANARY.json").read_bytes()).hexdigest()
            )
            manifest = json.loads((output / "HANDOFF-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["colab_canary_file"], "COLAB-CANARY.json")
            self.assertEqual(manifest["source_commit"], source_commit)
            self.assertFalse(manifest["private_project_files_included"])

    def test_handoff_rejects_colab_canary_from_another_commit(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canary = root / "colab-canary.json"
            canary.write_text(
                json.dumps(
                    {
                        "schema_version": "UniBotLiveColabCanaryV1",
                        "status": "pass",
                        "source_commit": "0" * 40,
                        "provider_calls": 0,
                        "source_text_omitted": True,
                        "raw_cell_text_persisted": False,
                        "notebook_output_read": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            canary.chmod(0o600)
            output = root / "handoff"
            result = write_release_handoff(output, repository=repository, colab_canary=canary)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "colab_canary_blocked")
            self.assertFalse(output.exists())

    def test_handoff_binds_metadata_only_jupyter_canary_to_source_commit(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canary = root / "jupyter-canary.json"
            source_commit = str(public_source_provenance(repository)["commit"])
            canary.write_text(
                json.dumps(
                    {
                        "schema_version": "UniBotLiveJupyterCanaryV1",
                        "status": "pass",
                        "source_commit": source_commit,
                        "provider_calls": 0,
                        "source_text_omitted": True,
                        "raw_cell_text_persisted": False,
                        "notebook_output_read": False,
                        "notebook_code_executed": False,
                        "adapter": "jupyterlab",
                        "adapter_version": "jupyterlab-v1",
                        "confidence": "high",
                        "source_url_kind": "local_synthetic_jupyterlab",
                        "capture_status": "adapter_metadata_available",
                        "cell_type": "markdown",
                        "cell_index": 0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            canary.chmod(0o600)
            output = root / "handoff"
            result = write_release_handoff(output, repository=repository, jupyter_canary=canary)

            self.assertEqual(result["status"], "written")
            self.assertIn("JUPYTER-CANARY.json", result["output_file_names"])
            self.assertEqual(
                result["jupyter_canary_sha256"],
                hashlib.sha256((output / "JUPYTER-CANARY.json").read_bytes()).hexdigest(),
            )
            manifest = json.loads((output / "HANDOFF-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["jupyter_canary_file"], "JUPYTER-CANARY.json")
            self.assertEqual(manifest["jupyter_canary_sha256"], result["jupyter_canary_sha256"])
            self.assertEqual(manifest["source_commit"], source_commit)
            self.assertFalse(manifest["private_project_files_included"])

    def test_handoff_rejects_jupyter_canary_from_another_commit(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canary = root / "jupyter-canary.json"
            canary.write_text(
                json.dumps(
                    {
                        "schema_version": "UniBotLiveJupyterCanaryV1",
                        "status": "pass",
                        "source_commit": "0" * 40,
                        "provider_calls": 0,
                        "source_text_omitted": True,
                        "raw_cell_text_persisted": False,
                        "notebook_output_read": False,
                        "notebook_code_executed": False,
                        "adapter": "jupyterlab",
                        "adapter_version": "jupyterlab-v1",
                        "confidence": "high",
                        "source_url_kind": "local_synthetic_jupyterlab",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            canary.chmod(0o600)
            output = root / "handoff"
            result = write_release_handoff(output, repository=repository, jupyter_canary=canary)

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "jupyter_canary_blocked")
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
