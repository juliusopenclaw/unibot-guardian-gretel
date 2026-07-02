from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.extraction_decision import (  # noqa: E402
    build_extraction_decision_packet,
    validate_extraction_decision_record,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_decision_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "lecture.mov").write_bytes(b"video")


def valid_decision() -> dict:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete local raw extraction artifacts after reviewed source-card metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic signed decision fixture",
    }


class UniBotExtractionDecisionTests(unittest.TestCase):
    def test_decision_packet_is_public_safe_and_not_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_decision_fixture(fixture_root)

            packet = build_extraction_decision_packet(base_path=str(fixture_root))
            payload = json.dumps(packet, ensure_ascii=False)

            self.assertEqual(packet["artifact_type"], "course_extraction_rights_privacy_decision_packet")
            self.assertEqual(packet["status"], "draft_ready_for_rights_privacy_review")
            self.assertEqual(packet["exam_deployment_status"], "not_cleared")
            self.assertEqual(packet["public_safety_status"], "pass")
            self.assertIn("Datenschutz", packet["required_reviewer_roles"])
            self.assertFalse(packet["minimum_decision_record"]["cloud_processing_allowed"])
            self.assertFalse(packet["minimum_decision_record"]["raw_text_public_release_allowed"])
            self.assertIn("not approval", packet["decision_boundary"])
            self.assertNotIn(str(fixture_root), payload)
            self.assertEqual(scan_text(payload, "decision-packet-test")["status"], "pass")

    def test_valid_decision_record_hashes_reference_and_authorizes_local_only(self) -> None:
        validation = validate_extraction_decision_record(valid_decision())
        payload = json.dumps(validation, ensure_ascii=False)

        self.assertEqual(validation["status"], "ok_authorizes_local_extraction")
        self.assertTrue(validation["approved_for_local_extraction"])
        self.assertTrue(validation["rights_decision_reference_hash"])
        self.assertFalse(validation["raw_decision_reference_stored"])
        self.assertNotIn("synthetic signed decision fixture", payload)
        self.assertEqual(validation["public_safety_status"], "pass")

    def test_invalid_decision_record_is_blocked(self) -> None:
        invalid = valid_decision()
        invalid["cloud_processing_allowed"] = True
        invalid["reviewer_roles"] = ["Datenschutz"]
        invalid["human_review_before_tutor_index"] = False

        validation = validate_extraction_decision_record(invalid)

        self.assertEqual(validation["status"], "blocked")
        self.assertFalse(validation["approved_for_local_extraction"])
        self.assertIn("cloud_processing_must_remain_false_for_this_gate", validation["issues"])
        self.assertIn("missing_required_reviewer_roles", validation["issues"])
        self.assertIn("human_review_before_tutor_index_required", validation["issues"])

    def test_decision_api_routes(self) -> None:
        status, packet = route_request("/api/unibot/course/extraction-decision-packet", {})
        self.assertEqual(status, 200)
        self.assertEqual(packet["artifact_type"], "course_extraction_rights_privacy_decision_packet")

        status, validation = route_request(
            "/api/unibot/course/extraction-decision/validate",
            {"decision": valid_decision()},
        )
        self.assertEqual(status, 200)
        self.assertEqual(validation["status"], "ok_authorizes_local_extraction")


if __name__ == "__main__":
    unittest.main()
