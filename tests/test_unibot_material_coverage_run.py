from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.material_coverage_run import build_course_material_coverage_run  # noqa: E402
from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.tutor_index import build_private_tutor_index_dry_run  # noqa: E402


def write_gap_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "pandas_boxplot_slides.pdf").write_bytes(b"%PDF-1.4\nfixture")
    (root / "Videos" / "debugging_walkthrough.mov").write_bytes(b"video")


def write_ready_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text(
        "pandas DataFrame read_csv columns dtypes debugging boxplot",
        encoding="utf-8",
    )


def reviewed_manifest_record() -> dict[str, object]:
    return {
        "material_id": "week-01-pandas-notebook",
        "title": "Week 01 pandas and boxplot notebook",
        "source_kind": "notebook",
        "permission_status": "private_course_use_only",
        "publish_policy": "private_only",
        "extraction_status": "text_extracted",
        "review_status": "reviewed_for_private_tutor",
        "skill_tags": ["pandas", "boxplots", "debugging"],
        "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
        "page_or_timestamp": "week 01",
        "sha256": sha256_text("week 01 pandas notebook reviewed locally"),
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
        "decision_reference": "synthetic material coverage decision",
    }


class UniBotMaterialCoverageRunTests(unittest.TestCase):
    def test_material_coverage_run_shows_ocr_and_video_gaps_without_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            write_gap_fixture(root)
            manifest_path = Path(temp_dir) / "missing_manifest.json"
            index_path = Path(temp_dir) / "missing_index.json"

            report = build_course_material_coverage_run(
                base_path=str(root),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "course_material_coverage_run")
            self.assertEqual(report["status"], "course_material_coverage_needs_extraction_or_transcription")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["extraction_gap_summary"]["ocr_job_count"], 1)
            self.assertEqual(report["extraction_gap_summary"]["transcription_job_count"], 1)
            self.assertEqual(report["private_manifest_summary"]["status"], "missing")
            self.assertEqual(report["private_tutor_index_summary"]["status"], "missing")
            self.assertEqual(report["next_exam_workspace_start_point"]["status"], "not_ready")
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["automatic_grading_started"])
            self.assertFalse(report["proctoring_started"])
            self.assertFalse(report["ai_detection_started"])
            self.assertNotIn(str(temp_dir), payload)
            self.assertNotIn("debugging_walkthrough.mov", payload)
            self.assertEqual(scan_text(payload, "material-coverage-gaps")["status"], "pass")

    def test_material_coverage_run_selects_exam_workspace_start_point_from_private_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            manifest_journal_path = Path(temp_dir) / "manifest_apply.jsonl"
            index_path = Path(temp_dir) / "private_tutor_index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            write_ready_fixture(root)
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            manifest_journal_path.write_text(
                json.dumps(
                    {
                        "status": "accepted",
                        "event": {"event_type": "private_manifest_metadata_applied", "new_manifest_hash": "a" * 64},
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=index_journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            status, report = route_request(
                "/api/unibot/course/material-coverage/run",
                {
                    "base_path": str(root),
                    "review_policy": "local_private_tutor",
                    "decision_record": valid_decision(),
                    "private_manifest_path": str(manifest_path),
                    "manifest_apply_journal_path": str(manifest_journal_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(index_journal_path),
                    "focus_query": "pandas boxplot",
                },
            )
            payload = json.dumps(report, ensure_ascii=False)
            skills = {item["skill_tag"]: item for item in report["skill_coverage"]}

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "course_material_coverage_run")
            self.assertEqual(report["status"], "course_material_coverage_ready_for_exam_workspace")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["private_manifest_summary"]["status"], "ok")
            self.assertEqual(report["private_manifest_summary"]["journal"]["status"], "ok")
            self.assertEqual(report["private_tutor_index_summary"]["status"], "ok")
            self.assertEqual(report["private_tutor_index_summary"]["journal"]["status"], "ok")
            self.assertGreaterEqual(report["coverage_summary"]["exam_workspace_ready_skill_count"], 1)
            self.assertEqual(report["next_exam_workspace_start_point"]["status"], "ready")
            self.assertEqual(report["next_exam_workspace_start_point"]["recommended_endpoint"], "/api/unibot/exam-workspace/run-dry-run")
            self.assertEqual(report["next_exam_workspace_start_point"]["recommended_help_level"], "A2")
            self.assertEqual(skills["pandas"]["exam_workspace_readiness"], "ready_for_exam_workspace_dry_run")
            self.assertGreaterEqual(skills["pandas"]["source_anchor_count"], 1)
            self.assertGreaterEqual(skills["pandas"]["reviewed_notebook_anchor_count"], 1)
            self.assertIn(skills["pandas"]["notebook_exercise"]["status"], {"ready", "ready_from_private_index_anchor"})
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertNotIn(str(temp_dir), payload)
            self.assertNotIn("Week 01 pandas", payload)
            self.assertEqual(scan_text(payload, "material-coverage-ready")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
