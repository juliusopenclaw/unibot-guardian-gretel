from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import nbformat

from unibot.gateway import GatewayError, build_gateway_launch_plan, launch_gateway
from unibot.notebook_intake import import_notebook


def write_notebook(path: Path) -> None:
    payload = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("value = 1")])
    path.write_text(nbformat.writes(payload), encoding="utf-8")


class GatewayV2Tests(unittest.TestCase):
    def test_gateway_plan_is_loopback_terminal_free_and_not_exam_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            write_notebook(source)
            manifest = import_notebook(str(source), root / "intake")
            manifest_path = root / "intake" / manifest["sanitized_sha256"][:16] / "manifest.json"
            plan = build_gateway_launch_plan(manifest_path, port=8899)

        self.assertTrue(plan["loopback_only"])
        self.assertFalse(plan["terminals_enabled"])
        self.assertEqual(plan["allowed_help_levels"], ["A0", "A1", "A2"])
        self.assertEqual(plan["network_isolation"], "not_enforced_by_local_launcher")
        self.assertEqual(plan["exam_deployment_status"], "not_cleared")
        self.assertIn("--ServerApp.terminals_enabled=False", plan["command_preview"])

    def test_gateway_rejects_tampered_notebook(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            write_notebook(source)
            manifest = import_notebook(str(source), root / "intake")
            artifact_dir = root / "intake" / manifest["sanitized_sha256"][:16]
            (artifact_dir / manifest["artifact_name"]).write_text("{}", encoding="utf-8")
            with self.assertRaises(GatewayError):
                build_gateway_launch_plan(artifact_dir / "manifest.json")

    def test_dry_run_never_starts_a_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            write_notebook(source)
            manifest = import_notebook(str(source), root / "intake")
            manifest_path = root / "intake" / manifest["sanitized_sha256"][:16] / "manifest.json"
            result = launch_gateway(manifest_path, dry_run=True)
        self.assertEqual(result["status"], "ready_for_local_practice_launch")
        self.assertNotIn("process_id", result)


if __name__ == "__main__":
    unittest.main()
