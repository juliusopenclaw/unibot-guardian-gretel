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
from unibot.exam_run_packet_builder import build_exam_run_packet  # noqa: E402
from unibot.exam_workspace_session_console import build_exam_workspace_session_console  # noqa: E402
from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.routed_action_executor import build_routed_action_executor  # noqa: E402
from unibot.python_exam_local_cycle_operator_workspace_card import build_python_exam_local_cycle_operator_workspace_card  # noqa: E402
from unibot.python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff  # noqa: E402
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review  # noqa: E402
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet  # noqa: E402
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt  # noqa: E402
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.tutor_index import build_private_tutor_index_dry_run  # noqa: E402
from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs  # noqa: E402


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
        "retention_decision": "synthetic exam run packet decision",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic exam run packet decision",
    }


class UniBotExamRunPacketTests(unittest.TestCase):
    def test_packet_joins_dashboard_router_executor_and_history_without_raw_data(self) -> None:
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
            local_cycle_console, local_cycle_gate, local_cycle_decision = ready_start_packet_inputs(temp_dir)
            local_cycle_confirmed_gate = build_python_exam_safe_cycle_operator_gate(
                python_exam_safe_cycle_console=local_cycle_console,
                selected_skill_tag="python_lists",
            )
            local_cycle_confirmed_ids = [card["step_id"] for card in local_cycle_confirmed_gate["confirmation_cards"]]
            local_cycle_decision = build_python_exam_operator_gate_decision_receipt(
                python_exam_safe_cycle_operator_gate=local_cycle_confirmed_gate,
                confirmed_step_ids=local_cycle_confirmed_ids,
                selected_skill_tag="python_lists",
            )
            local_cycle_start_packet = build_python_exam_local_cycle_start_packet(
                python_exam_safe_cycle_console=local_cycle_console,
                python_exam_safe_cycle_operator_gate=local_cycle_confirmed_gate,
                python_exam_operator_gate_decision_receipt=local_cycle_decision,
                selected_skill_tag="python_lists",
            )
            local_cycle_review = build_python_exam_local_cycle_readiness_review(
                python_exam_local_cycle_start_packet=local_cycle_start_packet,
                selected_skill_tag="python_lists",
            )
            local_cycle_handoff = build_python_exam_local_cycle_readiness_handoff(
                python_exam_local_cycle_readiness_review=local_cycle_review,
                python_exam_local_cycle_start_packet=local_cycle_start_packet,
                selected_skill_tag="python_lists",
            )
            local_cycle_workspace_card = build_python_exam_local_cycle_operator_workspace_card(
                python_exam_local_cycle_readiness_review=local_cycle_review,
                python_exam_local_cycle_readiness_handoff=local_cycle_handoff,
                python_exam_local_cycle_start_packet=local_cycle_start_packet,
                selected_skill_tag="python_lists",
            )
            packet = build_exam_run_packet(
                dashboard_report=dashboard,
                router_report=router,
                executor_report=executor,
                selected_skill_tag="python_lists",
                console_reports=[console],
                console_receipts=[console["session_console_receipt"]],
                python_exam_local_cycle_readiness_review=local_cycle_review,
                python_exam_local_cycle_readiness_handoff=local_cycle_handoff,
                python_exam_local_cycle_operator_workspace_card=local_cycle_workspace_card,
                public_safe=True,
            )
            payload = json.dumps(packet, ensure_ascii=False)

            self.assertEqual(packet["artifact_type"], "exam_run_packet")
            self.assertEqual(packet["status"], "exam_run_packet_ready")
            self.assertEqual(packet["exam_deployment_status"], "not_cleared")
            self.assertEqual(packet["public_safety_status"], "pass")
            self.assertEqual(packet["selected_skill_packet"]["skill_tag"], "python_lists")
            self.assertEqual(packet["selected_skill_packet"]["selected_route"]["route_id"], "review_open_operator_confirmations")
            self.assertEqual(
                packet["selected_skill_packet"]["executed_dry_run"]["artifact_type"],
                "exam_workspace_run_history_export_review",
            )
            self.assertFalse(packet["selected_skill_packet"]["executed_dry_run"]["local_write_started"])
            self.assertGreaterEqual(len(packet["selected_skill_packet"]["latest_checkpoint_hashes"]), 1)
            self.assertEqual(packet["selected_skill_packet"]["help_level_profile"]["A2"], 1)
            self.assertGreaterEqual(packet["selected_skill_packet"]["open_operator_confirmation_count"], 1)
            self.assertEqual(
                packet["human_reviewable_independence_trace"]["trace_status"],
                "human_reviewable_independence_trace_ready",
            )
            self.assertTrue(packet["human_reviewable_independence_trace"]["no_percentage_claimed"])
            self.assertTrue(packet["packet_receipt"]["not_cleared_receipt"])
            self.assertEqual(packet["local_cycle_chain_snapshot"]["status"], "python_exam_local_cycle_chain_snapshot_ready")
            self.assertEqual(packet["packet_summary"]["local_cycle_chain_snapshot_status"], "python_exam_local_cycle_chain_snapshot_ready")
            self.assertFalse(packet["raw_query_returned"])
            self.assertFalse(packet["raw_cell_returned"])
            self.assertFalse(packet["raw_text_returned"])
            self.assertFalse(packet["raw_notebook_returned"])
            self.assertFalse(packet["notebook_code_returned"])
            self.assertFalse(packet["local_paths_returned"])
            self.assertFalse(packet["automatic_grading_started"])
            self.assertFalse(packet["proctoring_started"])
            self.assertFalse(packet["ai_detection_started"])
            self.assertFalse(packet["exam_clearance_claimed"])
            self.assertNotIn("own_checkpoint", payload)
            self.assertNotIn("Week 01 Python", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "exam-run-packet")["status"], "pass")

    def test_packet_api_route_builds_from_inputs(self) -> None:
        status, packet = route_request(
            "/api/unibot/course/exam-run-packet",
            {
                "selected_skill_tag": "python_lists",
                "focus_query": "Python Listen",
                "public_safe": True,
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(packet["artifact_type"], "exam_run_packet")
        self.assertEqual(packet["status"], "exam_run_packet_ready")
        self.assertEqual(packet["exam_deployment_status"], "not_cleared")
        self.assertFalse(packet["raw_text_returned"])
        self.assertFalse(packet["local_paths_returned"])


if __name__ == "__main__":
    unittest.main()
