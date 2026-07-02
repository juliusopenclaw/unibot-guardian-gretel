from __future__ import annotations

import copy
import json
import tempfile
import unittest

from unibot.python_exam_confirmed_local_export_draft import build_python_exam_confirmed_local_export_draft
from unibot.python_exam_draft_package_review_console import build_python_exam_draft_package_review_console
from unibot.python_exam_human_handoff_packet import build_python_exam_human_handoff_packet
from unibot.server import route_request

from tests.test_unibot_python_exam_confirmed_local_export_draft import ready_preview


def handoff_inputs() -> dict[str, dict]:
    preview = ready_preview()
    draft = build_python_exam_confirmed_local_export_draft(
        python_exam_evidence_export_preview=preview,
        operator_confirmed_local_export_draft_write=False,
    )
    console = build_python_exam_draft_package_review_console(
        python_exam_confirmed_local_export_draft=draft,
        python_exam_evidence_export_preview=preview,
    )
    return {"preview": preview, "draft": draft, "console": console}


class UniBotPythonExamHumanHandoffPacketTests(unittest.TestCase):
    def test_human_handoff_packet_builds_copy_ready_metadata(self) -> None:
        inputs = handoff_inputs()
        report = build_python_exam_human_handoff_packet(
            python_exam_draft_package_review_console=inputs["console"],
            python_exam_evidence_export_preview=inputs["preview"],
            python_exam_confirmed_local_export_draft=inputs["draft"],
        )
        summary = report["handoff_summary"]
        packet = report["handoff_packet"]
        copy_view = report["copy_export_view"]

        self.assertEqual(report["artifact_type"], "python_exam_human_handoff_packet")
        self.assertEqual(report["status"], "python_exam_human_handoff_packet_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(summary["review_console_status"], "python_exam_draft_package_review_console_ready")
        self.assertEqual(summary["file_hash_integrity_status"], "file_hash_integrity_pass")
        self.assertEqual(summary["help_status"], "a0_a2_only")
        self.assertEqual(summary["review_chain_status"], "review_chain_integrity_pass")
        self.assertTrue(summary["notebook_checkpoint_hash_present"])
        self.assertEqual(summary["receipt_journal_accepted_record_count"], 1)
        self.assertGreaterEqual(summary["open_operator_confirmation_count"], 1)
        self.assertGreater(summary["review_question_count"], 0)
        self.assertTrue(packet["not_cleared_receipt"]["not_cleared_receipt"])
        self.assertEqual(copy_view["status"], "copy_ready")
        self.assertIn("# Python Exam Human Handoff Packet", copy_view["markdown"])
        self.assertIn("Exam deployment: not_cleared", copy_view["markdown"])
        self.assertFalse(copy_view["local_paths_included"])
        self.assertFalse(copy_view["raw_text_included"])
        self.assertFalse(copy_view["notebook_code_included"])
        self.assertFalse(report["local_paths_returned"])
        self.assertFalse(report["raw_query_returned"])
        self.assertFalse(report["raw_text_returned"])
        self.assertFalse(report["notebook_code_returned"])
        self.assertFalse(report["values_returned"])
        self.assertFalse(report["solutions_returned"])
        self.assertFalse(report["final_interpretations_returned"])
        self.assertFalse(report["automatic_grading_started"])
        self.assertFalse(report["proctoring_started"])
        self.assertFalse(report["ai_detection_started"])
        self.assertFalse(report["exam_clearance_claimed"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_human_handoff_packet_marks_attention_from_console(self) -> None:
        inputs = handoff_inputs()
        broken_console = copy.deepcopy(inputs["console"])
        broken_console["status"] = "python_exam_draft_package_review_console_attention"
        broken_console["package_integrity"]["status"] = "file_hash_integrity_attention"
        report = build_python_exam_human_handoff_packet(
            python_exam_draft_package_review_console=broken_console,
            python_exam_evidence_export_preview=inputs["preview"],
            python_exam_confirmed_local_export_draft=inputs["draft"],
        )

        self.assertEqual(report["status"], "python_exam_human_handoff_packet_attention")
        self.assertIn("Resolve", report["handoff_summary"]["next_safe_action"])
        self.assertEqual(report["public_safety_status"], "pass")

    def test_human_handoff_packet_api_route(self) -> None:
        inputs = handoff_inputs()
        status, report = route_request(
            "/api/unibot/course/python-exam-human-handoff-packet",
            payload={
                "python_exam_draft_package_review_console": inputs["console"],
                "python_exam_evidence_export_preview": inputs["preview"],
                "python_exam_confirmed_local_export_draft": inputs["draft"],
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "python_exam_human_handoff_packet_ready")
        self.assertEqual(report["public_safety_status"], "pass")

    def test_human_handoff_packet_does_not_leak_temp_path(self) -> None:
        preview = ready_preview()
        with tempfile.TemporaryDirectory() as temp_dir:
            draft = build_python_exam_confirmed_local_export_draft(
                python_exam_evidence_export_preview=preview,
                export_draft_dir=temp_dir,
                operator_confirmed_local_export_draft_write=True,
            )
            console = build_python_exam_draft_package_review_console(
                python_exam_confirmed_local_export_draft=draft,
                python_exam_evidence_export_preview=preview,
            )
            report = build_python_exam_human_handoff_packet(
                python_exam_draft_package_review_console=console,
                python_exam_evidence_export_preview=preview,
                python_exam_confirmed_local_export_draft=draft,
            )

        payload = json.dumps(report, ensure_ascii=False)
        self.assertNotIn(temp_dir, payload)
        self.assertEqual(report["public_safety_status"], "pass")


if __name__ == "__main__":
    unittest.main()
