from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.evaluation import (  # noqa: E402
    build_evaluation_markdown,
    build_evaluation_packet,
    build_scientific_quality_rubric,
    synthetic_tasks,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotEvaluationTests(unittest.TestCase):
    def test_evaluation_packet_contains_master_thesis_scaffold(self) -> None:
        packet = build_evaluation_packet()

        self.assertEqual(packet["schema_version"], "unibot-evaluation-packet-v1")
        self.assertEqual(packet["status"], "draft_not_ethics_or_authority_cleared")
        self.assertGreaterEqual(len(packet["synthetic_tasks"]), 4)
        self.assertIn("codebook", packet)
        self.assertIn("scientific_quality_rubric", packet)
        self.assertIn("measurement_plan", packet)
        self.assertIn("consent_boundary", packet)
        self.assertEqual(packet["quality_gates"]["redteam_status"], "pass")
        self.assertEqual(packet["quality_gates"]["authority_packet_status"], "draft_not_officially_cleared")

    def test_scientific_quality_rubric_covers_socratic_sources_refusal_and_privacy(self) -> None:
        rubric = build_scientific_quality_rubric()
        dimension_ids = {dimension["dimension_id"] for dimension in rubric["dimensions"]}
        payload = json.dumps(rubric, ensure_ascii=False)

        self.assertEqual(rubric["schema_version"], "unibot-scientific-quality-rubric-v1")
        self.assertIn("socratic_help_quality", dimension_ids)
        self.assertIn("source_grounding", dimension_ids)
        self.assertIn("refusal_clarity", dimension_ids)
        self.assertIn("privacy_and_publication_safety", dimension_ids)
        self.assertIn("learner_agency_and_fairness", dimension_ids)
        self.assertIn("Do not collapse scores into grades", rubric["aggregation_rule"])
        self.assertEqual(scan_text(payload, "scientific-quality-rubric")["status"], "pass")

    def test_synthetic_tasks_are_public_safe_and_skill_tagged(self) -> None:
        tasks = synthetic_tasks()
        task_ids = {task["task_id"] for task in tasks}
        payload = json.dumps(tasks, ensure_ascii=False)

        self.assertIn("synthetic_lists_debugging", task_ids)
        self.assertIn("synthetic_pandas_boxplot", task_ids)
        self.assertIn("synthetic_source_uncertainty", task_ids)
        self.assertIn("synthetic_accessibility_neutral", task_ids)
        self.assertTrue(all(task["skill_tags"] for task in tasks))
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("official_grade", payload)
        self.assertNotIn("raw_external_ai_output", payload)

    def test_evaluation_boundaries_exclude_high_stakes_use(self) -> None:
        packet_text = json.dumps(build_evaluation_packet(), ensure_ascii=False).lower()

        self.assertIn("no real exam performance", packet_text)
        self.assertIn("no grades", packet_text)
        self.assertIn("no proctoring", packet_text)
        self.assertIn("no ki detection as evidence", packet_text)
        self.assertIn("no accommodation decision", packet_text)
        self.assertIn("no medical or accommodation personal data", packet_text)

    def test_evaluation_markdown_and_api_routes(self) -> None:
        markdown = build_evaluation_markdown()
        self.assertIn("# UniBot Evaluation Packet", markdown)
        self.assertIn("Synthetic Tasks", markdown)
        self.assertIn("Scientific Quality Rubric", markdown)
        self.assertIn("refusal_clarity", markdown)
        self.assertIn("Red-Team: pass", markdown)

        status, packet = route_request("/api/unibot/evaluation-packet", {})
        self.assertEqual(status, 200)
        self.assertEqual(packet["schema_version"], "unibot-evaluation-packet-v1")

        status, response = route_request("/api/unibot/evaluation-packet-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Primary Measures", response["markdown"])

        status, tasks = route_request("/api/unibot/evaluation-tasks", {})
        self.assertEqual(status, 200)
        self.assertEqual(tasks["status"], "ok")
        self.assertGreaterEqual(len(tasks["tasks"]), 4)


if __name__ == "__main__":
    unittest.main()
