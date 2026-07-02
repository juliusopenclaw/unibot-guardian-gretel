from __future__ import annotations

import copy
import unittest

from unibot.review_chain_integrity import build_review_chain_integrity_check
from unibot.server import route_request


def synthetic_chain() -> dict[str, dict]:
    packet = {
        "artifact_type": "exam_run_packet",
        "status": "exam_run_packet_ready",
        "exam_deployment_status": "not_cleared",
        "selected_skill_packet": {
            "skill_tag": "python_lists",
            "help_level_profile": {"A2": 1},
            "open_operator_confirmation_count": 2,
        },
        "packet_receipt": {
            "receipt_id": "packet-1",
            "receipt_hash": "p" * 64,
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "public_safety_status": "pass",
    }
    timeline = {
        "artifact_type": "exam_packet_timeline",
        "status": "exam_packet_timeline_ready",
        "exam_deployment_status": "not_cleared",
        "timeline_summary": {
            "event_count": 1,
            "skill_tags": ["python_lists"],
            "checkpoint_hash_count": 1,
            "help_level_profile": {"A2": 1},
            "open_operator_confirmation_count": 2,
            "reflection_statuses": ["reflection_evidence_present"],
        },
        "timeline_events": [
            {
                "packet_receipt_id": "packet-1",
                "route_id": "review_open_operator_confirmations",
                "executed_artifact_type": "exam_workspace_run_history_export_review",
                "checkpoint_hashes": ["c" * 64],
            }
        ],
        "timeline_receipt": {
            "receipt_id": "timeline-1",
            "receipt_hash": "t" * 64,
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "public_safety_status": "pass",
    }
    review = {
        "artifact_type": "timeline_export_review_packet",
        "status": "timeline_export_review_packet_ready",
        "exam_deployment_status": "not_cleared",
        "export_review_summary": {
            "event_count": 1,
            "skill_tags": ["python_lists"],
            "checkpoint_hash_count": 1,
            "help_level_profile": {"A2": 1},
            "open_operator_confirmation_count": 2,
            "reflection_statuses": ["reflection_evidence_present"],
            "reviewer_question_count": 6,
        },
        "skill_review_packets": [
            {
                "status": "ready_for_human_review",
                "skill_tag": "python_lists",
                "packet_receipts": ["packet-1"],
                "route_ids": ["review_open_operator_confirmations"],
                "executed_artifacts": ["exam_workspace_run_history_export_review"],
            }
        ],
        "local_export_receipt": {
            "receipt_id": "review-1",
            "receipt_hash": "r" * 64,
        },
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
        "public_safety_status": "pass",
    }
    journal_append = {
        "artifact_type": "timeline_export_receipt_journal_append",
        "status": "stored",
        "stored_record": {
            "status": "accepted",
            "event": {
                "receipt_id": "review-1",
                "receipt_hash": "r" * 64,
                "skill_tags": ["python_lists"],
                "event_count": 1,
                "checkpoint_hash_count": 1,
                "reviewer_question_count": 6,
                "help_level_profile": {"A2": 1},
                "open_operator_confirmation_count": 2,
                "reflection_statuses": ["reflection_evidence_present"],
                "exam_deployment_status": "not_cleared",
            },
        },
    }
    journal_summary = {
        "artifact_type": "timeline_export_receipt_journal_summary",
        "status": "ok",
        "record_count": 1,
        "accepted_record_count": 1,
        "blocked_record_count": 0,
        "skill_tags": ["python_lists"],
        "event_count": 1,
        "checkpoint_hash_count": 1,
        "reviewer_question_count": 6,
        "help_level_profile": {"A2": 1},
        "open_operator_confirmation_count": 2,
        "reflection_statuses": ["reflection_evidence_present"],
        "exam_deployment_status": "not_cleared",
        "raw_query_returned": False,
        "raw_text_returned": False,
        "raw_cell_returned": False,
        "raw_notebook_returned": False,
        "notebook_code_returned": False,
        "local_paths_returned": False,
        "automatic_grading_started": False,
        "proctoring_started": False,
        "ai_detection_started": False,
        "exam_clearance_claimed": False,
    }
    return {
        "packet": packet,
        "timeline": timeline,
        "review": review,
        "journal_append": journal_append,
        "journal_summary": journal_summary,
    }


class UniBotReviewChainIntegrityTests(unittest.TestCase):
    def test_review_chain_integrity_passes_metadata_only_chain(self) -> None:
        chain = synthetic_chain()
        report = build_review_chain_integrity_check(
            exam_run_packet=chain["packet"],
            exam_packet_timeline=chain["timeline"],
            timeline_export_review_packet=chain["review"],
            timeline_export_receipt_journal_append=chain["journal_append"],
            timeline_export_receipt_journal_summary=chain["journal_summary"],
            selected_skill_tag="python_lists",
        )
        summary = report["chain_integrity_summary"]
        self.assertEqual(report["artifact_type"], "review_chain_integrity_check")
        self.assertEqual(report["status"], "review_chain_integrity_pass")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(summary["issue_count"], 0)
        self.assertEqual(summary["checked_link_count"], 4)
        self.assertIn("python_lists", summary["skill_tags"])
        self.assertEqual(summary["receipt_ids"]["journal_receipt_id"], "review-1")
        self.assertFalse(report["raw_query_returned"])
        self.assertFalse(report["raw_text_returned"])
        self.assertFalse(report["notebook_code_returned"])
        self.assertFalse(report["local_paths_returned"])
        self.assertFalse(report["exam_clearance_claimed"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_review_chain_integrity_marks_contradictory_journal_receipt(self) -> None:
        chain = synthetic_chain()
        broken_append = copy.deepcopy(chain["journal_append"])
        broken_append["stored_record"]["event"]["receipt_id"] = "different-review-receipt"
        report = build_review_chain_integrity_check(
            exam_run_packet=chain["packet"],
            exam_packet_timeline=chain["timeline"],
            timeline_export_review_packet=chain["review"],
            timeline_export_receipt_journal_append=broken_append,
            timeline_export_receipt_journal_summary=chain["journal_summary"],
            selected_skill_tag="python_lists",
        )
        summary = report["chain_integrity_summary"]
        self.assertEqual(report["status"], "review_chain_integrity_attention_required")
        self.assertGreaterEqual(summary["contradiction_count"], 1)
        self.assertTrue(
            any(item["item"] == "journal_review_receipt_id" for item in report["findings"] if item["status"] != "pass")
        )
        self.assertEqual(report["public_safety_status"], "pass")

    def test_review_chain_integrity_api_route(self) -> None:
        chain = synthetic_chain()
        status, report = route_request(
            "/api/unibot/course/review-chain-integrity-check",
            payload={
                "exam_run_packet": chain["packet"],
                "exam_packet_timeline": chain["timeline"],
                "timeline_export_review_packet": chain["review"],
                "timeline_export_receipt_journal_append": chain["journal_append"],
                "timeline_export_receipt_journal_summary": chain["journal_summary"],
                "selected_skill_tag": "python_lists",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "review_chain_integrity_pass")
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
