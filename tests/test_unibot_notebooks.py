from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.notebooks import REQUIRED_NOTEBOOK_SECTIONS, audit_practice_notebook, generate_practice_notebook  # noqa: E402
from unibot.server import route_request  # noqa: E402


class UniBotNotebookTests(unittest.TestCase):
    def test_generate_practice_notebook_contains_required_sections(self) -> None:
        artifact = generate_practice_notebook(
            "Ich will Python Listen und Boxplots in Colab ueben.",
            source_card_ids=["google-colab-gemini", "uoc-ki-lehre", "vanlehn-2011"],
        )
        notebook = artifact["notebook"]
        text = json.dumps(notebook, ensure_ascii=False)

        self.assertEqual(artifact["artifact_type"], "unibot_practice_notebook")
        self.assertEqual(notebook["nbformat"], 4)
        self.assertEqual(artifact["audit"]["status"], "pass")
        self.assertEqual(set(artifact["audit"]["sections_present"]), set(REQUIRED_NOTEBOOK_SECTIONS))
        self.assertIn("keine finale Loesung", text)
        self.assertIn("UniBot Postfilter", text)
        self.assertNotIn("solution_key", text)
        self.assertNotIn("RAW_EXTERNAL_AI_OUTPUT", text)
        self.assertNotIn("official_grade", text)
        self.assertTrue(artifact["source_cards"])

    def test_generated_notebook_code_cells_are_output_stripped(self) -> None:
        artifact = generate_practice_notebook("pandas DataFrame Debugging")
        code_cells = [cell for cell in artifact["notebook"]["cells"] if cell["cell_type"] == "code"]

        self.assertGreaterEqual(len(code_cells), 2)
        for cell in code_cells:
            self.assertEqual(cell["outputs"], [])
            self.assertIsNone(cell["execution_count"])
            self.assertEqual(cell["metadata"]["unibot_guardian"]["outputs_policy"], "strip_outputs")

    def test_exam_controlled_notebook_is_clearly_not_approved(self) -> None:
        artifact = generate_practice_notebook("Notebook pruefen", mode="exam_controlled")
        text = json.dumps(artifact["notebook"], ensure_ascii=False)

        self.assertEqual(artifact["mode"], "exam_controlled")
        self.assertIn("ohne schriftliche Pruefungsfreigabe gesperrt", text)
        self.assertTrue(artifact["prompt_card"]["blocked_in_exam_without_approval"])

    def test_notebook_audit_blocks_outputs_and_forbidden_markers(self) -> None:
        artifact = generate_practice_notebook("Listen")
        notebook = artifact["notebook"]
        notebook["cells"][3]["outputs"] = [{"output_type": "stream", "text": ["bad"]}]
        notebook["cells"][0]["source"].append("solution_key\n")

        audit = audit_practice_notebook(notebook)
        self.assertEqual(audit["status"], "blocked")
        self.assertIn(3, audit["code_cells_with_outputs"])
        self.assertIn("solution_key", audit["forbidden_markers"])

    def test_notebook_api_routes(self) -> None:
        status, artifact = route_request(
            "/api/unibot/notebook-template",
            {
                "task": "Boxplot mit pandas in Colab",
                "source_card_ids": ["google-colab-gemini"],
                "title": "Boxplot Practice",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(artifact["title"], "Boxplot Practice")
        self.assertEqual(artifact["audit"]["status"], "pass")

        status, audit = route_request("/api/unibot/notebook/audit", {"notebook": artifact["notebook"]})
        self.assertEqual(status, 200)
        self.assertEqual(audit["status"], "pass")

        status, invalid = route_request("/api/unibot/notebook/audit", {"notebook": "not-a-dict"})
        self.assertEqual(status, 400)
        self.assertEqual(invalid["status"], "invalid-notebook")


if __name__ == "__main__":
    unittest.main()
