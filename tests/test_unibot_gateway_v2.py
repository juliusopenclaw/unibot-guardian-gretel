from __future__ import annotations

import tempfile
import unittest
import socket
from pathlib import Path
from unittest.mock import patch

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

    def test_gateway_rejects_an_occupied_loopback_port_before_start(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            write_notebook(source)
            manifest = import_notebook(str(source), root / "intake")
            manifest_path = root / "intake" / manifest["sanitized_sha256"][:16] / "manifest.json"
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                listener.bind(("127.0.0.1", 0))
                listener.listen(1)
                port = int(listener.getsockname()[1])
                with patch("unibot.gateway.shutil.which", return_value="/usr/bin/jupyter") as which:
                    with self.assertRaisesRegex(GatewayError, "already in use"):
                        launch_gateway(manifest_path, port=port)
                which.assert_not_called()

    def test_gateway_rejects_a_process_that_exits_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            write_notebook(source)
            manifest = import_notebook(str(source), root / "intake")
            manifest_path = root / "intake" / manifest["sanitized_sha256"][:16] / "manifest.json"

            class ExitedProcess:
                pid = 12345

                @staticmethod
                def poll() -> int:
                    return 1

            with (
                patch("unibot.gateway.shutil.which", return_value="/usr/bin/jupyter"),
                patch("unibot.gateway.subprocess.Popen", return_value=ExitedProcess()),
                patch("unibot.gateway.webbrowser.open") as browser_open,
            ):
                with self.assertRaisesRegex(GatewayError, "exited before"):
                    launch_gateway(manifest_path, port=8898)
            browser_open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
