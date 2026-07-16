from __future__ import annotations

import json
import unittest

from unibot.cli import main
from unibot.public_demo import build_public_demo_evidence, build_public_demo_markdown
from unibot.public_safety import scan_text


class UniBotPublicDemoTests(unittest.TestCase):
    def test_public_demo_runs_real_tutor_without_executing_notebook(self) -> None:
        report = build_public_demo_evidence()

        self.assertEqual(report["schema_version"], "UniBotPublicDemoV1")
        self.assertEqual(report["status"], "ready_for_human_demo")
        self.assertEqual(report["fixture_name"], "synthetic_python_practice.ipynb")
        self.assertEqual(report["notebook"]["code_cell_count"], 1)
        self.assertTrue(report["notebook"]["execution_counts_cleared"])
        self.assertEqual(report["tutor"]["help_levels_demonstrated"], ["A0", "A1", "A2"])
        self.assertTrue(report["tutor"]["source_binding_pass"])
        self.assertTrue(report["tutor"]["output_filter_pass"])
        self.assertFalse(report["tutor"]["raw_cell_stored"])
        self.assertFalse(report["tutor"]["raw_attempt_stored"])
        self.assertFalse(report["safety"]["notebook_code_executed"])
        self.assertEqual(report["safety"]["provider_calls"], 0)
        self.assertEqual(report["exam_deployment_status"], "not_cleared")
        self.assertEqual(scan_text(json.dumps(report, ensure_ascii=False), "public-demo-test")["status"], "pass")

    def test_public_demo_markdown_is_a_short_meeting_script(self) -> None:
        markdown = build_public_demo_markdown(build_public_demo_evidence())

        self.assertIn("# UniBot Oeffentliche Demo", markdown)
        self.assertIn("A0, A1 und A2", markdown)
        self.assertIn("keine Pruefungs- oder Hochschulfreigabe", markdown)
        self.assertNotIn("values = [2, 4, 6]", markdown)
        self.assertEqual(scan_text(markdown, "public-demo-markdown")["status"], "pass")

    def test_cli_runs_public_demo_without_provider_or_write_work(self) -> None:
        self.assertEqual(main(["demo", "--markdown"]), 0)


if __name__ == "__main__":
    unittest.main()
