from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from unibot.companion import install_native_host


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


if __name__ == "__main__":
    unittest.main()
