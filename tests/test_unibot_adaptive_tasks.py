from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.adaptive_tasks import generate_adaptive_practice_plan  # noqa: E402
from unibot.materials import sha256_text  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotAdaptiveTasksTests(unittest.TestCase):
    def test_public_plan_prioritizes_high_help_skill_and_uses_public_material(self) -> None:
        plan = generate_adaptive_practice_plan(
            skill_state={
                "python_lists": {"signals": 4, "high_help_events": 2},
                "pandas": {"signals": 2, "high_help_events": 0},
            },
            max_tasks=3,
            public_safe=True,
        )

        self.assertEqual(plan["schema_version"], "unibot-adaptive-task-plan-v1")
        self.assertEqual(plan["status"], "ok")
        self.assertEqual(plan["public_safety_status"], "pass")
        self.assertEqual(plan["tasks"][0]["skill_tag"], "python_lists")
        self.assertEqual(plan["tasks"][0]["difficulty"], "guided_repair")
        self.assertEqual(plan["tasks"][0]["source_reference"]["material_id"], "python-lists-demo")
        self.assertIn("socratic_checks", plan["tasks"][0])
        self.assertIn("practice-only", json.dumps(plan, ensure_ascii=False))

    def test_public_plan_excludes_private_tutor_material(self) -> None:
        records = [
            {
                "material_id": "private-pandas-week",
                "title": "Private pandas week",
                "source_kind": "slide_pdf",
                "permission_status": "private_course_use_only",
                "publish_policy": "private_only",
                "extraction_status": "text_extracted",
                "review_status": "reviewed_for_private_tutor",
                "skill_tags": ["pandas"],
                "source_card_ids": ["dfg-gwp"],
                "page_or_timestamp": "week-04",
                "sha256": sha256_text("private pandas staged text"),
                "local_path": "/" + "Users/student/private/pandas.pdf",
            }
        ]
        public_plan = generate_adaptive_practice_plan(
            skill_state={"pandas": {"signals": 5, "high_help_events": 2}},
            material_records=records,
            public_safe=True,
        )
        local_plan = generate_adaptive_practice_plan(
            skill_state={"pandas": {"signals": 5, "high_help_events": 2}},
            material_records=records,
            public_safe=False,
        )
        public_payload = json.dumps(public_plan, ensure_ascii=False)
        local_payload = json.dumps(local_plan, ensure_ascii=False)

        self.assertEqual(public_plan["eligible_material_count"], 0)
        self.assertIn("synthetic-fallback", public_payload)
        self.assertNotIn("private-pandas-week", public_payload)
        self.assertEqual(local_plan["eligible_material_count"], 1)
        self.assertIn("private-pandas-week", local_payload)
        self.assertNotIn("/" + "Users/student", local_payload)
        self.assertNotIn("private pandas staged text", local_payload)

    def test_public_plan_blocks_if_generated_payload_is_not_public_safe(self) -> None:
        records = [
            {
                "material_id": "unsafe-demo",
                "title": "Unsafe demo",
                "source_kind": "synthetic_demo",
                "permission_status": "synthetic",
                "publish_policy": "synthetic_public",
                "extraction_status": "text_extracted",
                "review_status": "reviewed_public_safe",
                "skill_tags": ["debugging"],
                "sha256": sha256_text("unsafe"),
                "public_excerpt": f"Contact: {'student'}@example.invalid",
            }
        ]
        plan = generate_adaptive_practice_plan(
            skill_state={"debugging": {"signals": 1, "high_help_events": 1}},
            material_records=records,
            public_safe=True,
        )
        payload = json.dumps(plan, ensure_ascii=False)

        self.assertEqual(plan["status"], "ok")
        self.assertEqual(plan["eligible_material_count"], 0)
        self.assertNotIn("student" + "@example.invalid", payload)
        self.assertEqual(scan_text(payload, "adaptive-plan")["status"], "pass")

    def test_api_route_returns_plan_and_rejects_invalid_payloads(self) -> None:
        status, plan = route_request(
            "/api/unibot/tasks/adaptive-plan",
            {"skill_state": {"boxplots": {"signals": 3, "high_help_events": 1}}, "max_tasks": 2},
        )

        self.assertEqual(status, 200)
        self.assertEqual(plan["task_count"], 2)
        self.assertEqual(plan["tasks"][0]["skill_tag"], "boxplots")

        status, response = route_request("/api/unibot/tasks/adaptive-plan", {"skill_state": "not-state"})
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-skill-state")

        status, response = route_request("/api/unibot/tasks/adaptive-plan", {"records": "not-records"})
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-records")

        status, response = route_request("/api/unibot/tasks/adaptive-plan", {"max_tasks": "many"})
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "invalid-max-tasks")


if __name__ == "__main__":
    unittest.main()
