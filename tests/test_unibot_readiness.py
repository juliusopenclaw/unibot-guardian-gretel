from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.readiness import (  # noqa: E402
    build_readiness_evidence_snapshot,
    build_readiness_markdown,
    build_readiness_runtime_guard,
    default_public_paths,
    run_readiness_check,
)
from unibot.server import route_request  # noqa: E402


class UniBotReadinessTests(unittest.TestCase):
    def test_default_public_paths_include_core_docs_code_and_tests(self) -> None:
        paths = default_public_paths()
        names = {path.name for path in paths}

        self.assertIn("UNIBOT_PIPELINE.md", names)
        self.assertIn("CONTRIBUTING.md", names)
        self.assertIn("SECURITY.md", names)
        self.assertIn("guardian.py", names)
        self.assertIn("publication.py", names)
        self.assertIn("test_unibot_readiness.py", names)

    def test_readiness_check_passes_for_public_draft(self) -> None:
        report = run_readiness_check()
        check_ids = {check["check_id"] for check in report["checks"]}

        self.assertEqual(report["schema_version"], "unibot-readiness-check-v1")
        self.assertEqual(report["status"], "public_draft_ready")
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(report["passed_count"], report["check_count"])
        self.assertIn("public_safety", check_ids)
        self.assertIn("readiness_runtime_guard", check_ids)
        self.assertIn("redteam", check_ids)
        self.assertIn("publication_package", check_ids)
        self.assertIn("evaluation_packet", check_ids)
        self.assertIn("authority_handoff", check_ids)
        self.assertIn("source_card_drift_guard", check_ids)
        self.assertIn("course_material_policy", check_ids)
        self.assertIn("adaptive_task_plan", check_ids)
        self.assertIn("local_demo_run", check_ids)
        self.assertIn("demo_feedback_contract", check_ids)
        self.assertIn("demo_feedback_triage", check_ids)
        self.assertIn("github_issue_bundle", check_ids)
        self.assertIn("release_runbook", check_ids)
        self.assertIn("compliance_matrix", check_ids)
        self.assertIn("pilot_protocol", check_ids)
        self.assertIn("data_protection_screening", check_ids)
        self.assertIn("review_board_packet", check_ids)
        self.assertIn("gretel_glm_evolve_lane", check_ids)
        self.assertIn("gretel_bachelor_thesis_package", check_ids)
        self.assertIn("gretel_autonomous_research_loop", check_ids)
        self.assertIn("exam_boundary", check_ids)
        self.assertIn("public draft review", report["ready_for"])
        self.assertIn("exam deployment", report["not_ready_for"])
        self.assertEqual(report["runtime_guard"]["status"], "budget_guard_ready")
        self.assertEqual(report["runtime_guard"]["routine_budget"]["default_execution_mode"], "focused_readiness")
        self.assertIs(report["runtime_guard"]["routine_budget"]["full_suite_required_by_default"], False)
        self.assertIs(report["runtime_guard"]["routine_budget"]["provider_calls_allowed_by_default"], False)
        self.assertIs(report["runtime_guard"]["routine_budget"]["external_actions_allowed_by_default"], False)
        self.assertEqual(report["source_card_drift"]["status"], "pass")
        self.assertEqual(report["source_card_drift"]["missing_required_source_card_ids"], [])
        self.assertEqual(report["source_card_drift"]["unlisted_high_risk_source_card_ids"], [])
        self.assertEqual(report["evidence_snapshot"]["status"], "ready")
        self.assertEqual(report["evidence_snapshot"]["public_safety_status"], "pass")
        self.assertEqual(report["evidence_snapshot"]["failed_check_ids"], [])
        self.assertEqual(report["evidence_snapshot"]["scientific_gate_passed_count"], report["evidence_snapshot"]["scientific_gate_count"])
        self.assertIn("gretel_bachelor_thesis_package", [gate["check_id"] for gate in report["evidence_snapshot"]["scientific_gates"]])

    def test_readiness_runtime_guard_keeps_recurring_runs_lightweight(self) -> None:
        guard = build_readiness_runtime_guard(public_file_count=123)

        self.assertEqual(guard["status"], "budget_guard_ready")
        self.assertEqual(guard["public_safety_status"], "pass")
        self.assertEqual(guard["routine_budget"]["default_reasoning_effort"], "low")
        self.assertEqual(guard["routine_budget"]["max_active_work_items_per_run"], 1)
        self.assertIs(guard["routine_budget"]["full_suite_required_by_default"], False)
        self.assertIs(guard["routine_budget"]["provider_calls_allowed_by_default"], False)
        self.assertIs(guard["routine_budget"]["external_actions_allowed_by_default"], False)
        self.assertIn("python3 -m pytest tests/test_unibot_readiness.py -q", guard["routine_commands"])
        self.assertIn("full pytest suite", guard["expensive_or_escalated_by_default"])
        self.assertEqual(guard["current_public_file_scan_count"], 123)

    def test_readiness_evidence_snapshot_is_compact_public_safe_and_stable(self) -> None:
        report = run_readiness_check()
        snapshot = report["evidence_snapshot"]
        rebuilt = build_readiness_evidence_snapshot(report)

        self.assertEqual(snapshot["schema_version"], "unibot-readiness-evidence-snapshot-v1")
        self.assertEqual(snapshot["status"], "ready")
        self.assertEqual(snapshot["public_safety_status"], "pass")
        self.assertEqual(snapshot["readiness_status"], "public_draft_ready")
        self.assertEqual(snapshot["exam_deployment_status"], "not_cleared")
        self.assertEqual(snapshot["snapshot_hash"], rebuilt["snapshot_hash"])
        self.assertGreaterEqual(snapshot["scientific_gate_count"], 10)
        self.assertEqual(snapshot["scientific_gate_passed_count"], snapshot["scientific_gate_count"])
        self.assertEqual(snapshot["failed_check_ids"], [])
        self.assertLess(len(json.dumps(snapshot, ensure_ascii=False)), 6000)
        self.assertIn("not exam clearance", snapshot["human_gate_reminder"])

    def test_readiness_check_blocks_when_public_scan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            risky = Path(tmp) / "risky.md"
            risky.write_text("api" + "_key = sk-test\n", encoding="utf-8")
            report = run_readiness_check([risky])

        self.assertEqual(report["status"], "blocked")
        self.assertGreater(report["failed_count"], 0)
        public_check = next(check for check in report["checks"] if check["check_id"] == "public_safety")
        self.assertFalse(public_check["passed"])

    def test_readiness_markdown_and_api_routes(self) -> None:
        markdown = build_readiness_markdown()
        self.assertIn("# UniBot Readiness Check", markdown)
        self.assertIn("public_draft_ready", markdown)
        self.assertIn("Exam deployment: not_cleared", markdown)
        self.assertIn("Runtime guard: budget_guard_ready", markdown)
        self.assertIn("Source-card drift: pass", markdown)
        self.assertIn("Evidence snapshot: ready", markdown)
        self.assertIn("`readiness_runtime_guard`: pass", markdown)
        self.assertIn("`source_card_drift_guard`: pass", markdown)

        status, report = route_request("/api/unibot/readiness-check", {})
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "public_draft_ready")

        status, response = route_request("/api/unibot/readiness-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Policy:", response["markdown"])

    def test_readiness_report_is_public_safe(self) -> None:
        payload = json.dumps(run_readiness_check(), ensure_ascii=False)

        self.assertNotIn("raw_external_ai_output", payload)
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("official_grade", payload)
        self.assertIn("not exam clearance", payload)


if __name__ == "__main__":
    unittest.main()
