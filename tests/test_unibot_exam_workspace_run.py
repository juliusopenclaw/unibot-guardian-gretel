from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.exam_workspace_run import build_exam_workspace_run_dry_run  # noqa: E402
from unibot.extraction import build_course_extraction_queue  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def write_exam_workspace_fixture(root: Path) -> None:
    (root / "Week 1").mkdir(parents=True)
    (root / "Week 1" / "python_lists_and_loops.pdf").write_bytes(b"%PDF-1.4\nfixture")


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
        "decision_reference": "synthetic exam workspace decision",
    }


def reviewed_receipt_for_job(job: dict[str, object]) -> dict[str, object]:
    return {
        "job_id": job["job_id"],
        "material_id": job["material_id"],
        "job_type": job["job_type"],
        "extraction_status": "extracted_private",
        "raw_text_sha256": "f" * 64,
        "extracted_text_char_count": 1400,
        "private_artifact_reference": "private exam workspace artifact ref",
        "human_review_status": "reviewed_for_private_tutor",
        "decision_reference_hash": sha256_text(str(valid_decision()["decision_reference"])),
    }


def notebook_fixture() -> dict[str, object]:
    return {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# Controlled exam workspace\n"]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["values = [1, 2, 3]\n"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


class UniBotExamWorkspaceRunTests(unittest.TestCase):
    def test_exam_workspace_run_waits_without_private_manifest_or_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "index.json"
            write_exam_workspace_fixture(root)

            report = build_exam_workspace_run_dry_run(
                "Wie pruefe ich Listen vor dem naechsten Notebook-Schritt?",
                base_path=str(root),
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                notebook=notebook_fixture(),
                cell_index=1,
                student_reflection="Ich pruefe zuerst meine eigene Vorhersage.",
                public_safe=True,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "exam_workspace_run_dry_run")
            self.assertEqual(report["status"], "exam_workspace_waiting_for_tutor_flow")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["session_summary"]["status"], "dry_run_not_started")
            self.assertEqual(report["material_freeze_summary"]["status"], "dry_run_not_frozen")
            self.assertEqual(report["notebook_checkpoint"]["run_status"], "dry_run_not_executed")
            self.assertFalse(report["exam_ledger_append_summary"]["ledger_written"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(manifest_path.exists())
            self.assertFalse(index_path.exists())
            self.assertNotIn("Wie pruefe ich", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "exam-workspace-waiting")["status"], "pass")

    def test_exam_workspace_run_connects_notebook_tutor_ledger_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            course_id = f"exam-workspace-{uuid.uuid4().hex[:10]}"
            self.addCleanup(lambda: shutil.rmtree(ROOT / "unibot" / "knowledge" / "exam_workspace" / course_id, ignore_errors=True))
            root = Path(temp_dir) / "materials"
            manifest_path = Path(temp_dir) / "private_manifest.json"
            manifest_journal_path = Path(temp_dir) / "manifest_apply.jsonl"
            index_path = Path(temp_dir) / "index.json"
            index_journal_path = Path(temp_dir) / "index_journal.jsonl"
            help_ledger_path = Path(temp_dir) / "help_ledger.jsonl"
            write_exam_workspace_fixture(root)
            queue = build_course_extraction_queue(
                base_path=str(root),
                rights_decision_reference=str(valid_decision()["decision_reference"]),
            )
            receipt = reviewed_receipt_for_job(queue["jobs"][0])

            status, report = route_request(
                "/api/unibot/exam-workspace/run-dry-run",
                {
                    "course_id": course_id,
                    "query": "Wie pruefe ich Python Listen vor dem naechsten eigenen Check?",
                    "base_path": str(root),
                    "decision_record": valid_decision(),
                    "receipts": [receipt],
                    "private_manifest_path": str(manifest_path),
                    "manifest_apply_journal_path": str(manifest_journal_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(index_journal_path),
                    "ledger_path": str(help_ledger_path),
                    "notebook": notebook_fixture(),
                    "cell_index": 1,
                    "cell_id": "cell-list-check",
                    "cell_type": "code",
                    "student_reflection": "Ich pruefe zuerst die erwartete Laenge selbst.",
                    "operator_confirmed_exam_workspace_run": True,
                    "operator_confirmed_manifest_apply": True,
                    "operator_confirmed_tutor_index_build": True,
                    "operator_confirmed_help_ledger_append": True,
                    "operator_confirmed_exam_ledger_append": True,
                    "requested_help_level": "A2",
                    "study_receipt": {
                        "prediction_present": True,
                        "notebook_action_present": True,
                        "reflection_present": True,
                    },
                },
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(report["artifact_type"], "exam_workspace_run_dry_run")
            self.assertEqual(report["status"], "exam_workspace_ready_with_exam_ledger")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertEqual(report["session_summary"]["status"], "started")
            self.assertEqual(report["material_freeze_summary"]["status"], "frozen")
            self.assertEqual(report["notebook_checkpoint"]["run_status"], "kernel-unavailable")
            self.assertEqual(report["tutor_sidecar"]["status"], "allowed")
            self.assertEqual(report["tutor_sidecar"]["effective_help_level"], "A2")
            self.assertEqual(
                report["private_tutor_use_flow_summary"]["study_receipt_validation"]["status"],
                "ok_study_session_receipt",
            )
            self.assertTrue(report["exam_ledger_append_summary"]["ledger_written"])
            self.assertTrue(report["export_package_summary"]["not_cleared_receipt"])
            self.assertTrue(report["export_package_summary"]["human_reviewable_independence_evidence"])
            self.assertFalse(report["export_package_summary"]["raw_transcripts_included"])
            self.assertFalse(report["export_package_summary"]["automatic_grading_included"])
            self.assertFalse(report["export_package_summary"]["proctoring_included"])
            self.assertFalse(report["export_package_summary"]["ai_detection_included"])
            self.assertFalse(report["raw_query_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["raw_notebook_returned"])
            self.assertFalse(report["notebook_code_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["exam_clearance_claimed"])
            self.assertTrue(manifest_path.exists())
            self.assertTrue(index_path.exists())
            self.assertTrue(help_ledger_path.exists())
            self.assertNotIn("Wie pruefe ich", payload)
            self.assertNotIn("values = [1, 2, 3]", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertNotIn("private exam workspace artifact ref", payload)
            self.assertEqual(scan_text(payload, "exam-workspace-ready")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
