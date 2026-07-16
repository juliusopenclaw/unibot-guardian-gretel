from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from unibot.companion import CompanionRuntime, companion_diagnose, install_native_host


class UniBotCompanionInstallTests(unittest.TestCase):
    def test_native_host_uses_source_independent_runtime_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            support = root / "support"
            chrome_hosts = root / "chrome-hosts"
            chromium_hosts = root / "chromium-hosts"
            with (
                patch("unibot.companion.APPLICATION_SUPPORT", support),
                patch("unibot.companion.CHROME_NATIVE_HOSTS", chrome_hosts),
                patch("unibot.companion.CHROMIUM_NATIVE_HOSTS", chromium_hosts),
            ):
                result = install_native_host("a" * 32)

            runtime_root = support / "runtime"
            launcher = support / "bin" / "unibot-native-host"
            manifest = json.loads((chrome_hosts / "de.gretel.unibot_companion.json").read_text(encoding="utf-8"))
            launcher_text = launcher.read_text(encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-c", "import unibot; print(unibot.__file__)"],
                cwd=root,
                env={**os.environ, "PYTHONPATH": str(runtime_root)},
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(result["status"], "installed")
            self.assertTrue(result["runtime_package_copied"])
            self.assertTrue((runtime_root / "unibot" / "companion.py").is_file())
            self.assertTrue((runtime_root / "exam_mode.py").is_file())
            self.assertEqual(manifest["path"], str(launcher))
            self.assertIn(str(runtime_root), launcher_text)
            self.assertNotIn(str(Path(__file__).resolve().parents[1]), launcher_text)
            self.assertTrue(completed.stdout.strip().startswith(str(runtime_root)))

    def test_diagnosis_is_structured_and_does_not_return_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            support = root / "support"
            chrome_hosts = root / "chrome-hosts"
            chromium_hosts = root / "chromium-hosts"
            app_path = root / "UniBot Companion.app"
            with (
                patch("unibot.companion.APPLICATION_SUPPORT", support),
                patch("unibot.companion.CHROME_NATIVE_HOSTS", chrome_hosts),
                patch("unibot.companion.CHROMIUM_NATIVE_HOSTS", chromium_hosts),
                patch("unibot.companion.DEFAULT_APP_PATH", app_path),
            ):
                install_native_host("a" * 32)
                app_path.mkdir(parents=True)
                diagnosis = companion_diagnose("a" * 32)
                native_response = CompanionRuntime(storage_root=support / "sessions").handle(
                    {
                        "request_id": "diagnose-1",
                        "type": "companion.diagnose",
                        "payload": {"extension_id": "a" * 32},
                    }
                )

            self.assertEqual(diagnosis["schema_version"], "unibot-companion-diagnosis-v1")
            self.assertEqual(diagnosis["status"], "ready")
            self.assertEqual(diagnosis["local_practice_status"], "ready_for_local_practice")
            self.assertEqual(diagnosis["distribution_status"], "blocked_human_release_gates")
            self.assertTrue(diagnosis["checks"]["runtime_package"])
            self.assertTrue(diagnosis["checks"]["chrome_manifest"])
            self.assertEqual(native_response["status"], "ok")
            self.assertEqual(native_response["diagnosis"]["schema_version"], "unibot-companion-diagnosis-v1")
            self.assertFalse(diagnosis["bundled_developer_id_interpreter"])
            self.assertFalse(diagnosis["notarized"])
            self.assertNotIn(str(root), json.dumps(diagnosis))


if __name__ == "__main__":
    unittest.main()
