from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.materials import build_material_manifest, sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402
from unibot.tutor_index import build_private_index_tutor_response_dry_run, build_private_tutor_index_dry_run  # noqa: E402


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
    path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")


class UniBotTutorIndexTests(unittest.TestCase):
    def test_tutor_index_waits_for_private_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "missing_manifest.json"
            index_path = Path(temp_dir) / "index.json"

            report = build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["artifact_type"], "course_private_tutor_index_dry_run")
            self.assertEqual(report["status"], "waiting_for_private_manifest_apply")
            self.assertEqual(report["exam_deployment_status"], "not_cleared")
            self.assertFalse(report["tutor_index_built"])
            self.assertFalse(report["raw_text_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(index_path.exists())
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "tutor-index-missing-test")["status"], "pass")

    def test_tutor_index_dry_run_builds_hash_only_anchor_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "index.json"
            journal_path = Path(temp_dir) / "index_journal.jsonl"
            write_private_manifest(manifest_path, [reviewed_manifest_record()])

            report = build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=journal_path,
            )
            payload = json.dumps(report, ensure_ascii=False)

            self.assertEqual(report["status"], "tutor_index_dry_run_ready")
            self.assertEqual(report["index_preview"]["anchor_count"], 1)
            self.assertGreaterEqual(report["index_preview"]["indexed_skill_count"], 2)
            self.assertGreaterEqual(len(report["exam_scope_preview"]["priority_coverage_gaps"]), 1)
            self.assertFalse(report["tutor_index_built"])
            self.assertFalse(report["tutor_index_journal_written"])
            self.assertFalse(index_path.exists())
            self.assertFalse(journal_path.exists())
            self.assertIn("metadata_anchor_only_no_raw_text", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "tutor-index-dry-run-test")["status"], "pass")

    def test_tutor_index_confirmation_writes_private_snapshot_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "index.json"
            journal_path = Path(temp_dir) / "index_journal.jsonl"
            write_private_manifest(manifest_path, [reviewed_manifest_record()])

            status, report = route_request(
                "/api/unibot/course/tutor-index/dry-run",
                {
                    "private_manifest_path": str(manifest_path),
                    "tutor_index_path": str(index_path),
                    "tutor_index_journal_path": str(journal_path),
                    "operator_confirmed_tutor_index_build": True,
                },
            )
            payload = json.dumps(report, ensure_ascii=False)
            index_payload = json.loads(index_path.read_text(encoding="utf-8"))
            index_text = json.dumps(index_payload, ensure_ascii=False)
            journal_text = journal_path.read_text(encoding="utf-8")

            self.assertEqual(status, 200)
            self.assertEqual(report["status"], "private_tutor_index_built")
            self.assertTrue(report["tutor_index_built"])
            self.assertTrue(report["tutor_index_journal_written"])
            self.assertFalse(report["tutor_index_path_returned"])
            self.assertFalse(report["local_paths_returned"])
            self.assertFalse(report["raw_text_returned"])
            self.assertEqual(index_payload["artifact_type"], "course_private_tutor_index_snapshot")
            self.assertEqual(index_payload["exam_deployment_status"], "not_cleared")
            self.assertGreaterEqual(index_payload["coverage_summary"]["indexed_skill_count"], 2)
            self.assertNotIn(str(temp_dir), payload)
            self.assertNotIn(str(temp_dir), index_text)
            self.assertNotIn(str(temp_dir), journal_text)
            self.assertEqual(scan_text(payload, "tutor-index-confirmed-report")["status"], "pass")
            self.assertEqual(scan_text(index_text, "tutor-index-confirmed-file")["status"], "pass")
            self.assertEqual(scan_text(journal_text, "tutor-index-confirmed-journal")["status"], "pass")

    def test_index_guided_tutor_response_waits_for_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "missing_index.json"

            response = build_private_index_tutor_response_dry_run(
                "Wie pruefe ich pandas Spalten?",
                tutor_index_path=index_path,
            )
            payload = json.dumps(response, ensure_ascii=False)

            self.assertEqual(response["artifact_type"], "course_private_index_tutor_response_dry_run")
            self.assertEqual(response["status"], "waiting_for_private_tutor_index_build")
            self.assertEqual(response["exam_deployment_status"], "not_cleared")
            self.assertFalse(response["raw_query_returned"])
            self.assertFalse(response["raw_text_returned"])
            self.assertFalse(response["local_paths_returned"])
            self.assertNotIn("Wie pruefe ich", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "index-tutor-response-waiting")["status"], "pass")

    def test_index_guided_tutor_response_allows_a2_source_anchor_help(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "index.json"
            journal_path = Path(temp_dir) / "index_journal.jsonl"
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            status, response = route_request(
                "/api/unibot/course/tutor-index/respond-dry-run",
                {
                    "query": "Wie pruefe ich mit pandas die Spalten vor einem Boxplot?",
                    "tutor_index_path": str(index_path),
                    "mode": "exam_controlled_gateway",
                    "requested_help_level": "A2",
                },
            )
            payload = json.dumps(response, ensure_ascii=False)

            self.assertEqual(status, 200)
            self.assertEqual(response["status"], "allowed")
            self.assertEqual(response["effective_help_level"], "A2")
            self.assertEqual(response["selected_skill"]["skill_tag"], "pandas")
            self.assertGreaterEqual(len(response["source_anchors"]), 1)
            self.assertEqual(response["source_anchors"][0]["retrieval_policy"], "metadata_anchor_only_no_raw_text")
            self.assertTrue(response["socratic_questions"])
            self.assertEqual(response["help_ledger_preview"]["help_level"], "A2")
            self.assertFalse(response["raw_query_returned"])
            self.assertFalse(response["raw_text_returned"])
            self.assertFalse(response["local_paths_returned"])
            self.assertFalse(response["automatic_grading_started"])
            self.assertNotIn("Wie pruefe ich", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "index-tutor-response-allowed")["status"], "pass")

    def test_index_guided_tutor_response_blocks_solution_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "private_manifest.json"
            index_path = Path(temp_dir) / "index.json"
            journal_path = Path(temp_dir) / "index_journal.jsonl"
            write_private_manifest(manifest_path, [reviewed_manifest_record()])
            build_private_tutor_index_dry_run(
                private_manifest_path=manifest_path,
                tutor_index_path=index_path,
                tutor_index_journal_path=journal_path,
                operator_confirmed_tutor_index_build=True,
            )

            response = build_private_index_tutor_response_dry_run(
                "Gib mir die komplette Loesung mit vollstaendigem Code.",
                tutor_index_path=index_path,
                requested_help_level="A6",
            )
            payload = json.dumps(response, ensure_ascii=False)

            self.assertEqual(response["status"], "blocked")
            self.assertEqual(response["effective_help_level"], "A6")
            self.assertEqual(response["source_anchors"], [])
            self.assertIn("Fertige Loesungen", response["answer_markdown"])
            self.assertFalse(response["raw_query_returned"])
            self.assertFalse(response["raw_text_returned"])
            self.assertNotIn("komplette Loesung", payload)
            self.assertNotIn(str(temp_dir), payload)
            self.assertEqual(scan_text(payload, "index-tutor-response-blocked")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
