from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction_completion import build_extraction_completion_report  # noqa: E402
from unibot.extraction_receipt_journal import read_extraction_receipt_journal  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.video_transcription_runner import run_video_transcription_batch  # noqa: E402


def valid_extraction_decision() -> dict[str, object]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic video transcription runner decision",
    }


def write_video_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "python_intro.mov").write_bytes(b"synthetic local video placeholder")
    (root / "Week 1" / "python_intro.vtt").write_text(
        "\n".join(
            [
                "WEBVTT",
                "",
                "00:00:00.000 --> 00:00:04.000",
                "Welcome to Python notebooks and variables.",
                "",
                "00:00:04.000 --> 00:00:08.000",
                "Check the cell state before interpreting output.",
            ]
        ),
        encoding="utf-8",
    )


class UniBotVideoTranscriptionRunnerTests(unittest.TestCase):
    def test_runner_blocks_without_valid_decision_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            output_dir = Path(temp_dir) / "private"
            root.mkdir()
            write_video_fixture(root)

            report = run_video_transcription_batch(
                base_path=str(root),
                private_output_dir=output_dir,
            )

            self.assertEqual(report["artifact_type"], "course_video_transcription_run")
            self.assertEqual(report["status"], "blocked_until_valid_rights_privacy_decision")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertFalse(output_dir.exists())

    def test_runner_ingests_sidecar_transcript_and_stores_hash_only_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            output_dir = Path(temp_dir) / "private"
            journal_path = Path(temp_dir) / "receipts.jsonl"
            root.mkdir()
            write_video_fixture(root)

            report = run_video_transcription_batch(
                base_path=str(root),
                decision_record=valid_extraction_decision(),
                receipt_journal_path=journal_path,
                private_output_dir=output_dir,
                max_jobs=2,
            )
            payload = json.dumps(report, ensure_ascii=False)
            journal = read_extraction_receipt_journal(journal_path)

            self.assertEqual(report["status"], "sidecar_transcripts_ready_for_human_review")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["counts"]["candidate_video_job_count"], 1)
            self.assertEqual(report["counts"]["sidecar_candidate_count"], 1)
            self.assertEqual(report["counts"]["transcribed_private_count"], 1)
            self.assertEqual(report["counts"]["stored_receipt_count"], 1)
            self.assertTrue(report["private_artifact_map_written"])
            self.assertTrue(report["adapter_capabilities"]["sidecar_transcript"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertEqual(journal["count"], 1)
            self.assertEqual(len(journal["receipts_for_progress"]), 1)
            self.assertNotIn(str(root), payload)
            self.assertNotIn(str(output_dir), payload)
            self.assertNotIn("Welcome to Python notebooks and variables", payload)
            self.assertNotIn("Check the cell state before interpreting output", payload)
            self.assertEqual(scan_text(payload, "video-transcription-runner-test")["status"], "pass")

    def test_api_route_and_reviewed_receipt_can_feed_completion_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            output_dir = Path(temp_dir) / "private"
            journal_path = Path(temp_dir) / "receipts.jsonl"
            root.mkdir()
            write_video_fixture(root)

            status, report = route_request(
                "/api/unibot/course/video-transcription/run-batch",
                {
                    "base_path": str(root),
                    "decision_record": valid_extraction_decision(),
                    "receipt_journal_path": str(journal_path),
                    "private_output_dir": str(output_dir),
                    "human_review_status": "reviewed_for_private_tutor",
                    "max_jobs": 2,
                },
            )
            receipts = read_extraction_receipt_journal(journal_path)["receipts_for_progress"]
            completion = build_extraction_completion_report(
                base_path=str(root),
                decision_record=valid_extraction_decision(),
                receipts=receipts,
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "sidecar_transcripts_ready_for_human_review")
            self.assertEqual(report["counts"]["stored_receipt_count"], 1)
            self.assertEqual(completion["status"], "complete_by_reviewed_receipts")
            self.assertEqual(completion["job_summary"]["completed_by_reviewed_receipt_count"], 1)


if __name__ == "__main__":
    unittest.main()
