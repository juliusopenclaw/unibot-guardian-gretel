from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.exam_skill_drilldown import build_exam_skill_drilldown  # noqa: E402
from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.tutor_index import build_private_tutor_index_dry_run  # noqa: E402


def write_ready_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True, exist_ok=True)
    (root / "Week 1" / "lists_intro.md").write_text(
        "Python lists dictionary tuple index slice loop function notebook",
        encoding="utf-8",
    )


def write_gap_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True, exist_ok=True)
    (root / "Videos").mkdir(parents=True, exist_ok=True)
    (root / "Week 1" / "stats_slides.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "debugging_walkthrough.mov").write_bytes(b"video")


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
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic drilldown decision",
    }


class UniBotExamSkillDrilldownTests(unittest.TestCase):
    def test_drilldown_selects_ready_python_skill_and_prepares_operator_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            status, report = route_request(
                "/api/unibot/course/exam-skill-drilldown",
                {
                    "base_path": str(root),
                    "review_policy": "local_private_tutor",
                    "decision_record": valid_decision(),
                    "private_manifest_path": str(manifest_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(index_journal_path),
                    "focus_query": "private prompt must not be echoed",
                    "selected_skill_tag": "python_lists",
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "exam_skill_drilldown")
            self.assertEqual(report["status"], "exam_skill_drilldown_ready_for_workspace")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["selected_skill"]["skill_tag"], "python_lists")
            self.assertTrue(report["selected_skill"]["selected"])
            self.assertTrue(report["selected_skill"]["start_button_enabled"])
            self.assertEqual(report["workspace_start_action"]["status"], "ready")
            self.assertEqual(report["workspace_start_action"]["endpoint"], "/api/unibot/exam-workspace/operator-run")
            self.assertTrue(report["workspace_start_action"]["dry_run_default"])
            self.assertEqual(report["operator_payload_template"]["focus_query"], "python_lists")
            self.assertEqual(report["operator_payload_template"]["query"], "python_lists")
            self.assertEqual(report["operator_payload_template"]["selected_skill_tag"], "python_lists")
            self.assertEqual(report["operator_payload_template"]["source_anchor_count"], report["selected_skill"]["source_anchor_count"])
            self.assertTrue(report["operator_payload_template"]["source_card_ids"])
            self.assertFalse(report["operator_payload_template"]["raw_source_text_included"])
            self.assertFalse(report["operator_payload_template"]["notebook_code_included"])
            self.assertEqual(report["operator_payload_template"]["operator_confirmations_default"], "all_false_dry_run")
            self.assertEqual(report["notebook_checkpoint_template"]["status"], "template_ready")
            self.assertEqual(report["notebook_checkpoint_template"]["skill_tag"], "python_lists")
            self.assertFalse(report["notebook_checkpoint_template"]["raw_cell_template_returned"])
            self.assertFalse(report["notebook_checkpoint_template"]["notebook_code_returned"])
            self.assertEqual(report["help_ledger_preview_template"]["status"], "template_ready")
            self.assertEqual(report["help_ledger_preview_template"]["help_level"], "A2")
            self.assertFalse(report["help_ledger_preview_template"]["raw_help_text_returned"])
            self.assertEqual(report["skill_to_workspace_live_flow"]["status"], "ready_to_execute_operator_dry_run")
            self.assertEqual(report["skill_to_workspace_live_flow"]["operator_endpoint"], "/api/unibot/exam-workspace/operator-run")
            self.assertGreaterEqual(report["coverage_summary"]["exam_workspace_ready_skill_count"], 1)
            self.assertIn("python_lists", report["coverage_summary"]["ready_skill_tags"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["automatic_grading_started"])
            self.assertFalse(report["proctoring_started"])
            self.assertFalse(report["ai_detection_started"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertNotIn("private prompt", payload)
            self.assertNotIn("Week 01 Python", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "exam-skill-drilldown-ready")["status"], "pass")

    def test_drilldown_blocks_workspace_action_until_selected_skill_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            write_gap_fixture(root)

            report = build_exam_skill_drilldown(
                base_path=str(root),
                selected_skill_tag="debugging",
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "exam_skill_drilldown")
            self.assertEqual(report["status"], "exam_skill_drilldown_needs_material_work")
            self.assertEqual(report["selected_skill"]["skill_tag"], "debugging")
            self.assertFalse(report["selected_skill"]["start_button_enabled"])
            self.assertEqual(report["workspace_start_action"]["status"], "not_ready")
            self.assertEqual(report["workspace_start_action"]["endpoint"], "")
            self.assertEqual(report["operator_payload_template"]["status"], "blocked_until_skill_ready")
            self.assertEqual(report["notebook_checkpoint_template"]["status"], "blocked_until_skill_ready")
            self.assertEqual(report["help_ledger_preview_template"]["status"], "blocked_until_skill_ready")
            self.assertEqual(report["skill_to_workspace_live_flow"]["status"], "waiting_for_skill_material_readiness")
            self.assertTrue(report["material_gap_queue"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertNotIn(str(temp_dir), payload)
            self.assertNotIn("debugging_walkthrough.mov", payload)
            self.assertEqual(scan_text(payload, "exam-skill-drilldown-gap")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
