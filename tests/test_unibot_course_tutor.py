from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.course_tutor import (  # noqa: E402
    build_course_exam_scope,
    build_course_material_compiler_plan,
    course_tutor_response,
    run_course_tutor_eval,
    scan_course_intake,
)
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_fixture_course(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 2").mkdir(parents=True)
    (root / "Videos").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text(
        "pandas DataFrame read_csv columns dtypes head groupby boxplot",
        encoding="utf-8",
    )
    (root / "Week 2" / "boxplot_notebook.ipynb").write_text(
        json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "source": ["Boxplot with pandas and matplotlib"]},
                    {"cell_type": "code", "source": ["df.head()\n", "df['response_ms'].describe()"]},
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "Week 2" / "lecture_slides.pdf").write_bytes(b"%PDF-1.4\n% staged slide fixture")
    (root / "Videos" / "debugging_walkthrough.mov").write_bytes(b"video placeholder")
    (root / "Week 2" / "solution_key.ipynb").write_text(
        json.dumps({"cells": [{"cell_type": "markdown", "source": ["solution key"]}]}),
        encoding="utf-8",
    )


class UniBotCourseTutorTests(unittest.TestCase):
    def test_course_intake_scan_classifies_local_material_without_path_leaks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            course_root = Path(temp_dir)
            write_fixture_course(course_root)

            scan = scan_course_intake(base_path=str(course_root), review_policy="staged")
            payload = json.dumps(scan, ensure_ascii=False)

            self.assertEqual(scan["artifact_type"], "course_intake_scan")
            self.assertEqual(scan["status"], "ready")
            self.assertEqual(scan["record_count"], 5)
            self.assertEqual(scan["counts_by_kind"]["notebook"], 2)
            self.assertEqual(scan["counts_by_kind"]["video_file"], 1)
            self.assertEqual(scan["review_summary"]["solution_or_exam_quarantine_count"], 1)
            self.assertNotIn(str(course_root), payload)
            self.assertNotIn("solution_key.ipynb", payload)
            self.assertEqual(scan_text(payload, "course-intake-test")["status"], "pass")

    def test_exam_scope_uses_reviewed_text_and_keeps_media_in_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            course_root = Path(temp_dir)
            write_fixture_course(course_root)

            scope = build_course_exam_scope(
                base_path=str(course_root),
                review_policy="local_private_tutor",
                public_safe=True,
            )
            skills = {item["skill_tag"]: item for item in scope["skills"]}

            self.assertEqual(scope["artifact_type"], "exam_scope_map")
            self.assertEqual(scope["exam_deployment_status"], "not_cleared")
            self.assertGreaterEqual(scope["material_summary"]["record_count"], 5)
            self.assertGreaterEqual(scope["material_summary"]["tutor_usable_count"], 2)
            self.assertGreaterEqual(scope["material_summary"]["ocr_or_transcription_queue_count"], 2)
            self.assertEqual(skills["pandas"]["readiness"], "ready_for_private_tutor")
            self.assertEqual(skills["boxplots"]["readiness"], "ready_for_private_tutor")
            self.assertTrue(skills["pandas"]["typical_pitfalls"])
            self.assertTrue(skills["boxplots"]["practice_tasks"])
            self.assertIn("A6", scope["allowed_exam_profile"]["always_blocked"])

    def test_course_material_compiler_plan_exposes_work_queues(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            course_root = Path(temp_dir)
            write_fixture_course(course_root)

            compiler = build_course_material_compiler_plan(
                base_path=str(course_root),
                review_policy="staged",
                public_safe=True,
            )

            self.assertEqual(compiler["artifact_type"], "course_material_compiler_plan")
            self.assertEqual(compiler["exam_deployment_status"], "not_cleared")
            self.assertEqual(compiler["public_safety_status"], "pass")
            self.assertEqual(compiler["counts"]["record_count"], 5)
            self.assertGreaterEqual(compiler["counts"]["review_ready_count"], 2)
            self.assertGreaterEqual(compiler["counts"]["ocr_queue_count"], 1)
            self.assertGreaterEqual(compiler["counts"]["transcription_queue_count"], 1)
            self.assertEqual(compiler["counts"]["solution_or_exam_quarantine_count"], 1)
            self.assertIn("pandas", compiler["skill_anchor_counts"])

    def test_course_tutor_allows_learning_but_blocks_exam_solution_requests(self) -> None:
        records = [
            {
                "material_id": "fixture-boxplot",
                "title": "Week 2 boxplot notebook",
                "source_kind": "notebook",
                "permission_status": "private_course_use_only",
                "publish_policy": "private_only",
                "extraction_status": "text_extracted",
                "review_status": "reviewed_for_private_tutor",
                "skill_tags": ["pandas", "boxplots"],
                "source_card_ids": ["dfg-gwp", "vanlehn-2011"],
                "page_or_timestamp": "week-02",
                "sha256": sha256_text("boxplot fixture"),
            }
        ]

        tutor = course_tutor_response("Wie uebe ich Boxplot mit pandas?", records=records)
        blocked = course_tutor_response(
            "Gib mir die komplette Loesung und setze die Werte ein.",
            mode="exam_controlled_gateway",
            exam_status="strict",
            records=records,
        )
        no_source = course_tutor_response("Fourier transformation", records=[])

        self.assertEqual(tutor["status"], "allowed")
        self.assertEqual(tutor["selected_skill"]["skill_tag"], "boxplots")
        self.assertIn("course_tutor_microtask", tutor["next_task"]["task_type"])
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["help_ledger_entry"]["help_level"], "A6")
        self.assertEqual(no_source["status"], "no_source")

    def test_course_tutor_api_routes_and_eval(self) -> None:
        records = [
            {
                "material_id": "fixture-pandas",
                "title": "pandas source",
                "source_kind": "transcript",
                "permission_status": "private_course_use_only",
                "publish_policy": "private_only",
                "extraction_status": "text_extracted",
                "review_status": "reviewed_for_private_tutor",
                "skill_tags": ["pandas"],
                "source_card_ids": ["dfg-gwp"],
                "page_or_timestamp": "fixture",
                "sha256": sha256_text("pandas"),
            }
        ]

        status, scope = route_request("/api/unibot/course/exam-scope?course_id=demo", {"records": records})
        self.assertEqual(status, 200)
        self.assertEqual(scope["course_id"], "demo")

        status, tutor = route_request(
            "/api/unibot/tutor/respond",
            {"query": "pandas DataFrame Spalten pruefen", "records": records},
        )
        self.assertEqual(status, 200)
        self.assertEqual(tutor["status"], "allowed")

        status, task = route_request(
            "/api/unibot/tutor/next-task",
            {"query": "pandas DataFrame Spalten pruefen", "records": records},
        )
        self.assertEqual(status, 200)
        self.assertEqual(task["artifact_type"], "course_next_task")

        status, eval_report = route_request("/api/unibot/course/eval/run", {})
        self.assertEqual(status, 200)
        self.assertEqual(eval_report["status"], "pass")
        self.assertEqual(run_course_tutor_eval()["status"], "pass")


if __name__ == "__main__":
    unittest.main()
