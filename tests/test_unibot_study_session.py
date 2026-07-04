from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.study_session import (  # noqa: E402
    build_course_study_session_plan,
    build_study_session_release_claim_alignment,
    build_study_session_review_report,
    validate_study_session_receipt,
)


def write_study_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "pandas_intro.md").write_text(
        "pandas DataFrame read_csv columns dtypes head groupby boxplot",
        encoding="utf-8",
    )
    (root / "Week 1" / "debugging_notes.md").write_text(
        "debugging traceback NameError TypeError smallest diagnostic check",
        encoding="utf-8",
    )
    (root / "Week 1" / "solution_key.md").write_text("solution key", encoding="utf-8")


def valid_study_receipt(task_id: str = "study-task", skill_tag: str = "pandas") -> dict[str, object]:
    return {
        "task_id": task_id,
        "skill_tag": skill_tag,
        "help_level": "A2",
        "source_anchor_id": "course-anchor-pandas",
        "prediction": "Ich erwarte, dass die Spalte zuerst auf numerische Werte geprueft werden muss.",
        "retrieval_response": "Aus dem Kopf: DataFrames brauchen passende Spalten und Datentypen.",
        "notebook_action": "Ich fuehre nur df.dtypes und df.head aus.",
        "reflection": "Mein Beitrag war die Vorhersage und der kleinste Diagnose-Schritt.",
    }


class UniBotStudySessionTests(unittest.TestCase):
    def test_study_session_generates_course_bound_retrieval_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_study_fixture(fixture_root)

            plan = build_course_study_session_plan(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                focus_query="pandas boxplot",
                max_items=3,
            )
            payload = json.dumps(plan, ensure_ascii=False)

            self.assertEqual(plan["artifact_type"], "course_study_session_plan")
            self.assertEqual(plan["status"], "ready_for_course_bound_practice")
            self.assertEqual(plan["exam_deployment_status"], "not_cleared")
            self.assertEqual(plan["public_safety_status"], "pass")
            self.assertGreaterEqual(plan["ready_task_count"], 1)
            self.assertEqual(plan["tasks"][0]["readiness"], "ready_for_private_tutor")
            self.assertIn("A0-A2", json.dumps(plan["session_contract"], ensure_ascii=False))
            self.assertEqual(len(plan["spacing_plan"]), plan["task_count"])
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn("solution_key.md", payload)
            self.assertEqual(scan_text(payload, "study-session-ready-test")["status"], "pass")

    def test_study_session_needs_materials_without_course_anchors(self) -> None:
        plan = build_course_study_session_plan(base_path="/private/tmp/definitely-missing-unibot-course-root")

        self.assertEqual(plan["status"], "needs_course_materials")
        self.assertEqual(plan["task_count"], 0)
        self.assertEqual(plan["public_safety_status"], "pass")

    def test_study_session_receipt_hashes_evidence_without_raw_text(self) -> None:
        validation = validate_study_session_receipt(
            valid_study_receipt(),
            expected_task_ids={"study-task"},
        )
        payload = json.dumps(validation, ensure_ascii=False)

        self.assertEqual(validation["artifact_type"], "course_study_session_receipt_validation")
        self.assertEqual(validation["status"], "ok_study_session_receipt")
        self.assertEqual(validation["public_safety_status"], "pass")
        self.assertFalse(validation["raw_text_stored"])
        self.assertFalse(validation["reflection_stored"])
        self.assertTrue(validation["evidence"]["prediction_present"])
        self.assertTrue(validation["evidence"]["reflection_present"])
        self.assertEqual(len(validation["evidence"]["prediction_hash"]), 64)
        self.assertNotIn("DataFrames brauchen passende Spalten", payload)
        self.assertEqual(scan_text(payload, "study-receipt-valid-test")["status"], "pass")

    def test_study_session_receipt_repeats_after_a6_or_final_solution(self) -> None:
        receipt = valid_study_receipt()
        receipt.update({"help_level": "A6", "final_solution_seen": True})

        validation = validate_study_session_receipt(receipt, expected_task_ids={"study-task"})

        self.assertEqual(validation["status"], "repeat_task_required")
        self.assertTrue(validation["repeat_task_required"])
        self.assertIn("a6_or_final_solution_seen_repeat_task_required", validation["issues"])
        self.assertEqual(validation["exam_deployment_status"], "not_cleared")

    def test_study_session_receipt_blocks_missing_learning_evidence(self) -> None:
        validation = validate_study_session_receipt(
            {
                "task_id": "study-task",
                "skill_tag": "pandas",
                "help_level": "A1",
                "source_anchor_id": "course-anchor-pandas",
            },
            expected_task_ids={"study-task"},
        )

        self.assertEqual(validation["status"], "blocked")
        self.assertIn("required_learning_evidence_missing", validation["issues"])
        self.assertFalse(validation["evidence"]["prediction_present"])

    def test_study_session_review_report_aggregates_receipts_without_grading(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_study_fixture(fixture_root)
            plan = build_course_study_session_plan(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                focus_query="pandas",
                max_items=1,
            )
            task = plan["tasks"][0]
            receipt = valid_study_receipt(task_id=task["task_id"], skill_tag=task["skill_tag"])

            report = build_study_session_review_report(
                base_path=str(fixture_root),
                review_policy="local_private_tutor",
                study_receipts=[receipt],
                focus_query="pandas",
                max_items=1,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "course_study_session_review_report")
            self.assertEqual(report["status"], "study_session_evidence_ready_for_human_review")
            self.assertEqual(report["public_safety_status"], "pass")
            self.assertEqual(report["receipt_summary"]["valid_receipt_count"], 1)
            self.assertEqual(report["evidence_profile"]["by_help_level"]["A2"], 1)
            self.assertIn("never claim a percentage", report["review_policy"]["eigenleistung_claim"])
            self.assertNotIn(str(fixture_root), payload)
            self.assertNotIn("DataFrames brauchen passende Spalten", payload)
            self.assertEqual(scan_text(payload, "study-review-report-test")["status"], "pass")

    def test_study_session_release_claim_alignment_links_receipts_reflection_and_boundaries(self) -> None:
        alignment = build_study_session_release_claim_alignment()

        self.assertEqual(
            alignment["schema_version"],
            "unibot-study-session-release-review-board-claim-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["review_public_safety_status"], "pass")
        self.assertEqual(alignment["review_status"], "study_session_evidence_ready_for_human_review")
        self.assertEqual(alignment["study_session_status"], "ready_for_course_bound_practice")
        self.assertEqual(alignment["exam_deployment_status"], "not_cleared")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertGreaterEqual(alignment["planned_task_count"], 1)
        self.assertGreaterEqual(alignment["valid_receipt_count"], 1)
        self.assertEqual(alignment["blocked_receipt_count"], 0)
        self.assertEqual(alignment["repeat_task_required_count"], 0)
        self.assertEqual(alignment["missing_planned_receipt_count"], 0)
        self.assertEqual(alignment["repeat_validation_status"], "repeat_task_required")
        self.assertTrue(alignment["repeat_task_required"])
        self.assertEqual(alignment["repeat_validation_public_safety_status"], "pass")
        self.assertIn("study_session", alignment["required_readiness_check_ids"])
        self.assertIn("private_tutor_use_flow", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["required_readiness_check_ids"])
        self.assertIn("exam_boundary", alignment["required_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertTrue(alignment["contracts"]["study_plan_ready_for_course_bound_practice"])
        self.assertTrue(alignment["contracts"]["hash_only_receipts_with_required_evidence"])
        self.assertTrue(alignment["contracts"]["learner_agency_profile_complete"])
        self.assertTrue(alignment["contracts"]["a6_or_final_solution_forces_repeat"])
        self.assertTrue(alignment["contracts"]["non_grading_human_review_only"])
        self.assertIn("raw reflection storage", alignment["blocked_claims"])
        self.assertIn("final solution acceptance", alignment["blocked_claims"])
        self.assertIn("Eigenleistung percentage claim", alignment["blocked_claims"])
        self.assertIn("automatic grading", alignment["blocked_claims"])
        self.assertIn("exam deployment", alignment["blocked_claims"])

    def test_study_session_release_claim_alignment_blocks_grading_or_final_solution_claims(self) -> None:
        report = build_study_session_review_report(study_receipts=[valid_study_receipt()])
        report["status"] = "study_session_evidence_ready_for_human_review"
        report["study_session_status"] = "ready_for_course_bound_practice"
        report["exam_deployment_status"] = "cleared"
        report["execution_boundary"] = "This review grades students and stores raw student text."
        report["receipt_summary"]["valid_receipt_count"] = 0
        report["receipt_summary"]["blocked_receipt_count"] = 1
        report["review_policy"]["eigenleistung_claim"] = "Claim 90 percent Eigenleistung."
        report["review_policy"]["not_allowed"] = []
        report["validated_receipts"] = [
            {
                "status": "ok_study_session_receipt",
                "raw_text_stored": True,
                "reflection_stored": True,
                "evidence": {},
            }
        ]
        repeat = validate_study_session_receipt(valid_study_receipt(), expected_task_ids={"study-task"})

        alignment = build_study_session_release_claim_alignment(report, repeat)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("hash_only_receipts_with_required_evidence", alignment["failed_contract_ids"])
        self.assertIn("a6_or_final_solution_forces_repeat", alignment["failed_contract_ids"])
        self.assertIn("non_grading_human_review_only", alignment["failed_contract_ids"])

    def test_study_session_api_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            write_study_fixture(fixture_root)
            status, plan = route_request(
                "/api/unibot/course/study-session-plan",
                {
                    "base_path": str(fixture_root),
                    "review_policy": "local_private_tutor",
                    "focus_query": "pandas",
                    "max_items": 1,
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(plan["artifact_type"], "course_study_session_plan")
            self.assertEqual(plan["exam_deployment_status"], "not_cleared")
            self.assertEqual(plan["public_safety_status"], "pass")

            task = plan["tasks"][0]
            receipt = valid_study_receipt(task_id=task["task_id"], skill_tag=task["skill_tag"])
            status, validation = route_request(
                "/api/unibot/course/study-session-receipt/validate",
                {"receipt": receipt, "expected_task_ids": [task["task_id"]]},
            )
            self.assertEqual(status, 200)
            self.assertEqual(validation["status"], "ok_study_session_receipt")

            status, report = route_request(
                "/api/unibot/course/study-session-review-report",
                {
                    "base_path": str(fixture_root),
                    "review_policy": "local_private_tutor",
                    "focus_query": "pandas",
                    "max_items": 1,
                    "study_receipts": [receipt],
                },
            )
            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "course_study_session_review_report")
            self.assertEqual(report["receipt_summary"]["valid_receipt_count"], 1)

        status, response = route_request("/api/unibot/course/study-session-plan", {"max_items": "many"})
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-limit")

        status, response = route_request("/api/unibot/course/study-session-receipt/validate", {"receipt": []})
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-receipt")

        status, response = route_request(
            "/api/unibot/course/study-session-review-report",
            {"study_receipts": "not-a-list"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-study-receipts")


if __name__ == "__main__":
    unittest.main()
