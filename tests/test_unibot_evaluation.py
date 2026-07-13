from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.evaluation import (  # noqa: E402
    build_evaluation_markdown,
    build_evaluation_learner_agency_boundary_alignment,
    build_evaluation_packet,
    build_scientific_quality_rubric,
    score_synthetic_decisions,
    synthetic_task_category_counts,
    synthetic_tasks,
)
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotEvaluationTests(unittest.TestCase):
    def test_evaluation_packet_contains_master_thesis_scaffold(self) -> None:
        packet = build_evaluation_packet()

        self.assertEqual(packet["schema_version"], "unibot-evaluation-packet-v1")
        self.assertEqual(packet["status"], "draft_not_ethics_or_authority_cleared")
        self.assertEqual(len(packet["synthetic_tasks"]), 180)
        self.assertIn("codebook", packet)
        self.assertIn("scientific_quality_rubric", packet)
        self.assertIn("measurement_plan", packet)
        self.assertIn("consent_boundary", packet)
        self.assertEqual(packet["learner_agency_boundary_alignment"]["status"], "ready")
        self.assertEqual(packet["learner_agency_boundary_alignment"]["public_safety_status"], "pass")
        self.assertEqual(packet["quality_gates"]["redteam_status"], "pass")
        self.assertEqual(packet["quality_gates"]["authority_packet_status"], "draft_not_officially_cleared")

    def test_learner_agency_boundary_alignment_connects_evaluation_to_adaptive_tasks(self) -> None:
        packet = build_evaluation_packet()
        alignment = build_evaluation_learner_agency_boundary_alignment(packet)

        self.assertEqual(
            alignment["schema_version"],
            "unibot-evaluation-learner-agency-boundary-alignment-v1",
        )
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["missing_source_card_ids"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertTrue(all(alignment["contracts"].values()))
        self.assertIn("adaptive_task_plan", alignment["required_readiness_check_ids"])
        self.assertIn("evaluation_packet", alignment["required_readiness_check_ids"])
        self.assertIn("datenschutz_review_required_before_real_pilot", alignment["required_human_gates"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])

        sections = {section["section_id"]: section for section in alignment["sections"]}
        self.assertIn("synthetic_lists_debugging", sections["synthetic_task_set"]["task_ids"])
        self.assertEqual(sections["adaptive_practice_trace"]["adaptive_alignment_status"], "ready")
        self.assertIn("official grades", sections["high_stakes_exclusion"]["excluded_measures"])

    def test_learner_agency_boundary_alignment_blocks_unready_adaptive_trace(self) -> None:
        packet = build_evaluation_packet()
        adaptive_plan = {
            "status": "ok",
            "public_safe": True,
            "task_count": 3,
            "tasks": [],
            "source_boundary_alignment": {
                "status": "needs_review",
                "non_public_source_material_ids": ["private-week"],
            },
        }
        alignment = build_evaluation_learner_agency_boundary_alignment(packet, adaptive_plan)

        self.assertEqual(alignment["status"], "needs_review")
        self.assertIn("adaptive_plan_boundary_ready", alignment["failed_contract_ids"])

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
        self.assertEqual(len(tasks), 180)
        self.assertEqual(
            synthetic_task_category_counts(),
            {
                "allowed_socratic_hint": 30,
                "assistance_budget": 30,
                "forbidden_final_answer": 30,
                "privacy_boundary": 30,
                "prompt_injection": 30,
                "source_binding": 30,
            },
        )
        self.assertNotIn("solution_key", payload)
        self.assertNotIn("official_grade", payload)
        self.assertNotIn("raw_external_ai_output", payload)

    def test_synthetic_decision_score_reports_false_blocks_and_forbidden_recall(self) -> None:
        observations = [
            {"task_id": task["task_id"], "decision": task["expected_decision"]}
            for task in synthetic_tasks()
        ]
        score = score_synthetic_decisions(observations)
        self.assertEqual(score["status"], "complete")
        self.assertEqual(score["task_count"], 180)
        self.assertEqual(score["forbidden_decision_recall"], 1.0)
        self.assertEqual(score["allowed_help_false_block_rate"], 0.0)
        self.assertIn("no learner grade", score["assessment_boundary"])

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
        self.assertIn("Learner-Agency Boundary Alignment", markdown)
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
        self.assertEqual(len(tasks["tasks"]), 180)


if __name__ == "__main__":
    unittest.main()
