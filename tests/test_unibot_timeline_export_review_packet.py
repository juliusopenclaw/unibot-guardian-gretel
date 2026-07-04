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
from unibot.timeline_export_review_packet import (  # noqa: E402
    build_timeline_export_review_packet,
    build_timeline_export_review_packet_workspace_card_alignment,
    synthetic_timeline_export_review_packet_workspace_card,
    timeline_export_review_packet_hash,
    timeline_export_review_packet_receipt_hash,
)
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
            alignment = review_packet["workspace_card_review_alignment"]
            self.assertEqual(
                alignment["schema_version"],
                "unibot-timeline-export-review-packet-workspace-card-review-alignment-v1",
            )
            self.assertEqual(alignment["status"], "ready")
            self.assertEqual(alignment["alignment_public_safety_status"], "pass")
            self.assertEqual(alignment["timeline_export_review_packet_hash"], timeline_export_review_packet_hash(review_packet))
            self.assertEqual(
                alignment["timeline_export_review_packet_receipt_hash"],
                timeline_export_review_packet_receipt_hash(review_packet),
            )
            self.assertEqual(alignment["failed_contract_ids"], [])
            self.assertFalse(alignment["local_write_started"])
            self.assertTrue(alignment["operator_confirmation_required_for_write"])
            self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
            self.assertTrue(alignment["workspace_card_timeline_review_packet_gate_linked"])
            self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
            self.assertFalse(alignment["raw_workspace_card_returned"])

    def test_workspace_card_alignment_blocks_broken_hash_link(self) -> None:
        review_packet = build_timeline_export_review_packet(
            selected_skill_tag="python_lists",
            focus_query="Python Listen",
            public_safe=True,
        )
        card = synthetic_timeline_export_review_packet_workspace_card()
        card["workspace_card_summary"]["checkpoint_hash"] = "broken-review-hash"
        card["workspace_card_summary"]["task_hash"] = "broken-receipt-hash"
        alignment = build_timeline_export_review_packet_workspace_card_alignment(
            review_packet,
            python_exam_local_cycle_operator_workspace_card=card,
        )

        self.assertEqual(alignment["status"], "blocked")
        self.assertEqual(alignment["alignment_public_safety_status"], "pass")
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertFalse(alignment["workspace_card_timeline_review_packet_gate_linked"])
        self.assertIn("workspace_card_timeline_review_packet_gate_linked", alignment["failed_contract_ids"])
        self.assertFalse(alignment["raw_workspace_card_returned"])

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
        self.assertEqual(review_packet["workspace_card_review_alignment"]["status"], "ready")
        self.assertTrue(
            review_packet["workspace_card_review_alignment"]["workspace_card_timeline_review_packet_gate_linked"]
        )


if __name__ == "__main__":
    unittest.main()
