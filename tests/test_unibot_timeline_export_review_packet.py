from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.course_exam_coverage_dashboard import build_course_exam_coverage_dashboard  # noqa: E402
from unibot.course_per_skill_action_router import build_course_per_skill_action_router  # noqa: E402
from unibot.exam_packet_timeline import build_exam_packet_timeline  # noqa: E402
from unibot.exam_run_packet_builder import build_exam_run_packet  # noqa: E402
from unibot.exam_workspace_session_console import build_exam_workspace_session_console  # noqa: E402
from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.routed_action_executor import build_routed_action_executor  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.timeline_export_review_packet import build_timeline_export_review_packet  # noqa: E402
from unibot.tutor_index import build_private_tutor_index_dry_run  # noqa: E402


def write_ready_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "lists_intro.md").write_text(
        "Python lists dictionary tuple index slice loop function notebook",
        encoding="utf-8",
    )


def reviewed_manifest_record() -> dict[str, object]:
    return {
        "material_id": "week-01-python-lists-notebook",
        "title": "Week 01 Python lists notebook",
        "source_kind": "notebook",
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": "text_extracted",
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": ["python_lists", "control_flow", "debugging"],
        "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
        "page_or_timestamp": "week 01",
        "sha256": sha256_text("week 01 python lists notebook reviewed locally"),
    }


def write_private_manifest(path: Path, records: list[dict[str, object]]) -> None:
    manifest = build_material_manifest(records)
    manifest["artifact_type"] = "course_private_material_manifest"
    manifest["exam_deployment_status"] = "not_cleared"
    manifest["storage_policy"] = "hash-only private material metadata; no raw text or local paths"
    path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")


def valid_decision() -> dict[str, object]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "synthetic timeline export review decision",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic timeline export review decision",
    }


class UniBotTimelineExportReviewPacketTests(unittest.TestCase):
    def test_export_review_packet_bundles_timeline_without_raw_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                operator_confirmed_tutor_index_build=True,
            )
            console = build_exam_workspace_session_console(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                selected_skill_tag="python_lists",
                cell_source="own_checkpoint = []\n",
                repeat_run_index=1,
                study_receipt={
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
                public_safe=True,
            )
            dashboard = build_course_exam_coverage_dashboard(
                base_path=str(root),
                review_policy="local_private_tutor",
                decision_record=valid_decision(),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                selected_skill_tag="python_lists",
                console_reports=[console],
                console_receipts=[console["session_console_receipt"]],
                public_safe=True,
            )
            router = build_course_per_skill_action_router(
                dashboard_report=dashboard,
                selected_skill_tag="python_lists",
                console_reports=[console],
                console_receipts=[console["session_console_receipt"]],
                public_safe=True,
            )
            executor = build_routed_action_executor(
                router_report=router,
                selected_route=router["selected_route"],
                selected_skill_tag="python_lists",
                console_reports=[console],
                console_receipts=[console["session_console_receipt"]],
                public_safe=True,
            )
            packet = build_exam_run_packet(
                dashboard_report=dashboard,
                router_report=router,
                executor_report=executor,
                selected_skill_tag="python_lists",
                console_reports=[console],
                console_receipts=[console["session_console_receipt"]],
                public_safe=True,
            )
            timeline = build_exam_packet_timeline(
                exam_run_packets=[packet],
                selected_skill_tag="python_lists",
                public_safe=True,
            )
            review_packet = build_timeline_export_review_packet(
                exam_packet_timeline=timeline,
                selected_skill_tag="python_lists",
                public_safe=True,
            )
            payload = json.dumps(review_packet, ensure_ascii=False)
            skill_packet = review_packet["skill_review_packets"][0]

            self.assertEqual(review_packet["artifact_type"], "timeline_export_review_packet")
            self.assertEqual(review_packet["status"], "timeline_export_review_packet_ready")
            self.assertEqual(review_packet["exam_deployment_status"], "not_cleared")
            self.assertEqual(review_packet["public_safety_status"], "pass")
            self.assertEqual(review_packet["export_review_summary"]["event_count"], 1)
            self.assertIn("python_lists", review_packet["export_review_summary"]["skill_tags"])
            self.assertEqual(skill_packet["skill_tag"], "python_lists")
            self.assertEqual(skill_packet["status"], "ready_for_human_review")
            self.assertGreaterEqual(len(skill_packet["packet_receipts"]), 1)
            self.assertIn("review_open_operator_confirmations", skill_packet["route_ids"])
            self.assertIn("exam_workspace_run_history_export_review", skill_packet["executed_artifacts"])
            self.assertGreaterEqual(skill_packet["checkpoint_hash_count"], 1)
            self.assertEqual(skill_packet["help_level_profile"]["A2"], 1)
            self.assertGreaterEqual(skill_packet["open_operator_confirmation_count"], 1)
            self.assertIn("reflection_evidence_present", skill_packet["reflection_statuses"])
            self.assertGreaterEqual(len(skill_packet["human_reviewer_questions"]), 5)
            self.assertEqual(
                review_packet["local_export_receipt"]["status"],
                "timeline_export_review_packet_receipt_ready_not_exam_clearance",
            )
            self.assertFalse(review_packet["local_export_receipt"]["local_write_started"])
            self.assertFalse(review_packet["raw_query_returned"])
            self.assertFalse(review_packet["raw_cell_returned"])
            self.assertFalse(review_packet["raw_text_returned"])
            self.assertFalse(review_packet["raw_notebook_returned"])
            self.assertFalse(review_packet["notebook_code_returned"])
            self.assertFalse(review_packet["local_paths_returned"])
            self.assertFalse(review_packet["automatic_grading_started"])
            self.assertFalse(review_packet["proctoring_started"])
            self.assertFalse(review_packet["ai_detection_started"])
            self.assertFalse(review_packet["exam_clearance_claimed"])
            self.assertNotIn("own_checkpoint", payload)
            self.assertNotIn("Week 01 Python", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "timeline-export-review-packet")["status"], "pass")

    def test_export_review_api_route_builds_from_minimal_inputs(self) -> None:
        status, review_packet = route_request(
            "/api/unibot/course/timeline-export-review-packet",
            {
                "selected_skill_tag": "python_lists",
                "focus_query": "Python Listen",
                "public_safe": True,
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(review_packet["artifact_type"], "timeline_export_review_packet")
        self.assertEqual(review_packet["status"], "timeline_export_review_packet_ready")
        self.assertEqual(review_packet["exam_deployment_status"], "not_cleared")
        self.assertFalse(review_packet["raw_text_returned"])
        self.assertFalse(review_packet["local_paths_returned"])


if __name__ == "__main__":
    unittest.main()
