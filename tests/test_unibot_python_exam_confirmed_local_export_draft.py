from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from unibot.python_exam_confirmed_local_export_draft import build_python_exam_confirmed_local_export_draft
from unibot.server import route_request

from tests.test_unibot_python_exam_evidence_export_preview import preview_inputs
from unibot.python_exam_evidence_export_preview import build_python_exam_evidence_export_preview


def ready_preview() -> dict:
    inputs = preview_inputs()
    return build_python_exam_evidence_export_preview(
        python_exam_live_control_surface=inputs["live_control"],
        python_exam_cockpit_flow=inputs["cockpit"],
        python_exam_readiness_console=inputs["readiness"],
        exam_skill_drilldown=inputs["drilldown"],
        exam_workspace_operator_run=inputs["operator"],
        exam_workspace_session_console=inputs["session"],
        review_chain_integrity_check=inputs["chain"],
        timeline_export_review_packet=inputs["review"],
        timeline_export_receipt_journal_summary=inputs["journal"],
        selected_skill_tag="python_lists",
    )


class UniBotPythonExamConfirmedLocalExportDraftTests(unittest.TestCase):
    def test_confirmed_local_export_draft_defaults_to_write_preview(self) -> None:
        preview = ready_preview()
        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_python_exam_confirmed_local_export_draft(
                python_exam_evidence_export_preview=preview,
                export_draft_dir=temp_dir,
                operator_confirmed_local_export_draft_write=False,
            )

            self.assertEqual(report["artifact_type"], "python_exam_confirmed_local_export_draft")
            self.assertEqual(report["status"], "python_exam_confirmed_local_export_draft_preview_ready")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertFalse(report["operator_confirmed_local_export_draft_write"])
            self.assertTrue(report["operator_confirmation_required_for_local_write"])
            self.assertTrue(report["dry_run_default"])
            self.assertFalse(report["local_export_draft_written"])
            self.assertFalse(report["local_export_package_written"])
            self.assertEqual(report["write_preview"]["status"], "ready_to_write_with_operator_confirmation")
            self.assertEqual(report["draft_file_count"], 3)
            self.assertEqual(len(report["draft_file_manifest"]), 3)
            self.assertTrue(report["draft_receipt"]["draft_package_id"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["export_draft_dir_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["values_returned"])
            self.assertFalse(report["solutions_returned"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(list(Path(temp_dir).glob("*")), [])

    def test_confirmed_local_export_draft_writes_hash_only_package_when_confirmed(self) -> None:
        preview = ready_preview()
        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_python_exam_confirmed_local_export_draft(
                python_exam_evidence_export_preview=preview,
                export_draft_dir=temp_dir,
                operator_confirmed_local_export_draft_write=True,
            )
            package_id = report["draft_receipt"]["draft_package_id"]
            package_dir = Path(temp_dir) / package_id
            files = sorted(path.name for path in package_dir.iterdir())

            self.assertEqual(report["status"], "python_exam_confirmed_local_export_draft_written")
            self.assertTrue(report["operator_confirmed_local_export_draft_write"])
            self.assertTrue(report["local_export_draft_written"])
            self.assertTrue(report["local_export_package_written"])
            self.assertEqual(report["draft_summary"]["write_result_status"], "local_export_draft_written")
            self.assertEqual(files, ["draft_receipt.json", "manifest.json", "not_cleared_receipt.json", "process_log.json"])
            for path in package_dir.iterdir():
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(payload.get("exam_deployment_status"), "not_cleared")
                self.assertFalse(payload.get("raw_text_included", False))
                self.assertFalse(payload.get("notebook_code_included", False))
                self.assertFalse(payload.get("local_paths_included", False))
            self.assertFalse(report["local_paths_returned"])
            self.assertNotIn(temp_dir, json.dumps(report, ensure_ascii=False))
            self.assertEqual(report["public_safety_status"], "pass")

    def test_confirmed_local_export_draft_blocks_write_when_preview_not_ready(self) -> None:
        preview = copy.deepcopy(ready_preview())
        preview["status"] = "python_exam_evidence_export_preview_attention"
        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_python_exam_confirmed_local_export_draft(
                python_exam_evidence_export_preview=preview,
                export_draft_dir=temp_dir,
                operator_confirmed_local_export_draft_write=True,
            )

            self.assertEqual(report["status"], "python_exam_confirmed_local_export_draft_blocked_preview_not_ready")
            self.assertTrue(report["operator_confirmed_local_export_draft_write"])
            self.assertFalse(report["local_export_draft_written"])
            self.assertEqual(list(Path(temp_dir).glob("*")), [])
            self.assertEqual(report["public_safety_status"], "pass")

    def test_confirmed_local_export_draft_api_route(self) -> None:
        preview = ready_preview()
        with tempfile.TemporaryDirectory() as temp_dir:
            status, report = route_request(
                "/api/unibot/course/python-exam-confirmed-local-export-draft",
                payload={
                    "python_exam_evidence_export_preview": preview,
                    "export_draft_dir": temp_dir,
                    "operator_confirmed_local_export_draft_write": True,
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "python_exam_confirmed_local_export_draft_written")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertFalse(report["local_paths_returned"])
            self.assertNotIn(temp_dir, json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
