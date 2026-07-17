from __future__ import annotations

import json
import unittest
from pathlib import Path

from unibot.cli import public_repository_safety
from unibot.public_safety import scan_text


class UniBotPublicDemoFixtureTests(unittest.TestCase):
    def test_public_synthetic_notebook_is_reproducible_and_contains_no_outputs(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        fixture = repository / "fixtures" / "public" / "synthetic_python_practice.ipynb"
        payload = json.loads(fixture.read_text(encoding="utf-8"))

        self.assertEqual(payload["nbformat"], 4)
        self.assertEqual(payload["metadata"]["kernelspec"]["name"], "python3")
        self.assertEqual(len(payload["cells"]), 2)
        code_cells = [cell for cell in payload["cells"] if cell["cell_type"] == "code"]
        self.assertEqual(len(code_cells), 1)
        self.assertEqual(code_cells[0]["outputs"], [])
        self.assertIsNone(code_cells[0]["execution_count"])
        self.assertIn("len(value)", "".join(code_cells[0]["source"]))
        self.assertNotIn("/" + "Users/", fixture.read_text(encoding="utf-8"))
        self.assertEqual(scan_text(fixture.read_text(encoding="utf-8"), "public-demo-fixture")["status"], "pass")

    def test_public_repository_safety_scans_the_notebook_fixture(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        result = public_repository_safety(repository)
        self.assertEqual(result["status"], "pass", result["findings"])
        self.assertGreaterEqual(result["scanned_count"], 186)


if __name__ == "__main__":
    unittest.main()
