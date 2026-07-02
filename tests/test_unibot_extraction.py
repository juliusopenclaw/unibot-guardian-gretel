from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction import build_course_extraction_queue, build_extraction_run_manifest  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_extraction_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text("pandas DataFrame boxplot", encoding="utf-8")
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Week 1" / "slides.pptx").write_bytes(b"pptx fixture")
    (root / "Videos" / "lecture.mov").write_bytes(b"video")
    (root / "Week 1" / "solution_key.pdf").write_bytes(b"%PDF-1.4\nsolution")


class UniBotExtractionTests(unittest.TestCase):
    def test_extraction_queue_is_metadata_only_and_rights_gated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_extraction_fixture(fixture_root)

            queue = build_course_extraction_queue(base_path=str(fixture_root), review_policy="local_private_tutor")
            payload = json.dumps(queue, ensure_ascii=False)

            self.assertEqual(queue["artifact_type"], "course_extraction_queue")
            self.assertEqual(queue["status"], "ready_to_run_when_authorized")
            self.assertEqual(queue["exam_deployment_status"], "not_cleared")
            self.assertFalse(queue["rights_gate"]["authorized"])
            self.assertEqual(queue["counts"]["job_count"], 3)
            self.assertEqual(queue["counts"]["ocr_job_count"], 2)
            self.assertEqual(queue["counts"]["transcription_job_count"], 1)
            self.assertEqual(queue["counts"]["quarantine_count"], 1)
            self.assertEqual(queue["counts"]["blocked_until_rights_decision_count"], 3)
            self.assertTrue(all(job["status"] == "blocked_until_rights_decision" for job in queue["jobs"]))
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn("solution_key.pdf", payload)
            self.assertEqual(scan_text(payload, "extraction-queue-test")["status"], "pass")

    def test_extraction_queue_can_be_authorized_without_exposing_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_extraction_fixture(fixture_root)

            queue = build_course_extraction_queue(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                rights_decision_reference="synthetic rights decision fixture",
            )
            payload = json.dumps(queue, ensure_ascii=False)

            self.assertEqual(queue["status"], "authorized_manifest_ready")
            self.assertTrue(queue["rights_gate"]["authorized"])
            self.assertTrue(queue["rights_gate"]["decision_reference_hash"])
            self.assertNotIn("synthetic rights decision fixture", payload)
            self.assertTrue(all(job["status"] == "queued" for job in queue["jobs"]))

    def test_extraction_run_manifest_is_dry_run_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_extraction_fixture(fixture_root)

            blocked = build_extraction_run_manifest(base_path=str(fixture_root))
            ready = build_extraction_run_manifest(
                base_path=str(fixture_root),
                rights_decision_reference="synthetic rights decision fixture",
            )

            self.assertEqual(blocked["status"], "blocked_until_rights_decision")
            self.assertEqual(ready["status"], "dry_run_ready")
            self.assertTrue(ready["dry_run"])
            self.assertIn("human-review extracted text", " ".join(ready["steps"]))
            self.assertEqual(ready["public_safety_status"], "pass")

    def test_extraction_api_routes(self) -> None:
        status, queue = route_request("/api/unibot/course/extraction-queue", {})
        self.assertEqual(status, 200)
        self.assertEqual(queue["artifact_type"], "course_extraction_queue")
        self.assertEqual(queue["exam_deployment_status"], "not_cleared")

        status, manifest = route_request("/api/unibot/course/extraction-run-manifest", {})
        self.assertEqual(status, 200)
        self.assertEqual(manifest["artifact_type"], "course_extraction_run_manifest")
        self.assertEqual(manifest["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
