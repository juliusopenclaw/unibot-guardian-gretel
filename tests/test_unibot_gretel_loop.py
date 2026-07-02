from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.simulation_loop import (  # noqa: E402
    default_scenarios,
    load_golden_rules,
    mock_deepseek_student,
    parse_deepseek_student_payload,
    run_gretel_unibot_loop,
)


SCRIPT = ROOT / "scripts" / "unibot_gretel_loop_smoke.py"


class UniBotGretelLoopTests(unittest.TestCase):
    def test_mock_deepseek_student_is_stable_and_compatible(self) -> None:
        scenario = default_scenarios()[0]
        first = mock_deepseek_student(scenario)
        second = mock_deepseek_student(scenario)

        self.assertEqual(first, second)
        self.assertEqual(first["object"], "chat.completion")
        payload = parse_deepseek_student_payload(first, scenario)
        self.assertTrue(payload["raw_output_omitted"])
        self.assertIn("external_ai_output_hash", payload)
        self.assertNotIn(
            "Welche Laenge hat deine Liste",
            json.dumps({"payload": {k: v for k, v in payload.items() if k != "external_ai_output"}}, ensure_ascii=False),
        )

    def test_golden_rules_are_loaded_from_policy_file(self) -> None:
        rules = load_golden_rules()

        self.assertEqual(rules["status"], "pass")
        self.assertEqual(rules["rule_ids"], ["GR1", "GR2", "GR3"])
        self.assertIn("UNIBOT_GOLDEN_RULES.md", rules["source"])

    def test_missing_golden_rules_blocks_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = run_gretel_unibot_loop(golden_rules_path=Path(tmp) / "missing.md")

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["golden_rules"]["reason"], "golden_rules_missing")

    def test_loop_report_blocks_risky_student_behaviour_without_raw_output(self) -> None:
        report = run_gretel_unibot_loop()
        payload = json.dumps(report, ensure_ascii=False)
        by_id = {item["scenario_id"]: item for item in report["scenarios"]}

        self.assertEqual(report["artifact_type"], "unibot_gretel_exam_loop_report")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["public_safety"]["status"], "pass")
        self.assertEqual(report["summary"]["raw_outputs_stored"], 0)
        self.assertEqual(report["scenario_count"], len(default_scenarios()))

        solution = by_id["deepseek_solution_leak"]
        self.assertEqual(solution["status"], "pass")
        self.assertTrue(solution["unibot"]["blocked"])
        self.assertIn("final_solution", solution["unibot"]["categories"])
        self.assertEqual(solution["unibot"]["independence_score"]["status"], "repeat_task")

        privacy = by_id["privacy_slip"]
        self.assertTrue(privacy["unibot"]["blocked"])
        self.assertIn("private_or_sensitive_data", privacy["unibot"]["categories"])
        self.assertIn("email", privacy["unibot"]["privacy_flags"])

        exam = by_id["exam_controlled_no_approval"]
        self.assertTrue(exam["unibot"]["blocked"])
        self.assertIn("exam_controlled_requires_written_approval", exam["unibot"]["categories"])

        self.assertNotIn("Hier ist die komplette Loesung", payload)
        self.assertNotIn("learner" + "@" + "example.invalid", payload)
        self.assertNotIn("Meine Diagnose", payload)
        self.assertNotIn("```python", payload)

    def test_loop_api_route_returns_report(self) -> None:
        from unibot.server import route_request

        status, report = route_request("/api/unibot/gretel-loop/run", payload={})

        self.assertEqual(status, 200)
        self.assertEqual(report["artifact_type"], "unibot_gretel_exam_loop_report")
        self.assertEqual(report["status"], "pass")

    def test_smoke_script_emits_valid_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["artifact_type"], "unibot_gretel_exam_loop_report")
        self.assertEqual(report["public_safety"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
