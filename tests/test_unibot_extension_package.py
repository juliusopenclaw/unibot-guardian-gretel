from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from unibot.extension_package import package_extension
from unibot.public_safety import scan_text


class UniBotExtensionPackageTests(unittest.TestCase):
    def test_chrome_canary_harness_uses_isolated_official_chrome_loader(self) -> None:
        root = Path(__file__).resolve().parents[1]
        harness = (root / "tests" / "browser" / "extension-package.mjs").read_text(encoding="utf-8")
        package = (root / "package.json").read_text(encoding="utf-8")
        self.assertIn("Extensions.loadUnpacked", harness)
        self.assertIn("--enable-unsafe-extension-debugging", harness)
        self.assertIn("NativeMessagingHosts", harness)
        self.assertIn("fs.rmSync(chromeUserDataDir", harness)
        self.assertIn('"test:chrome-canary"', package)

    def test_mv3_package_contains_only_public_extension_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = package_extension(Path(temporary) / "unibot-mantle.zip")
            package = Path(temporary) / "unibot-mantle.zip"
            self.assertEqual(result["status"], "written")
            self.assertEqual(result["manifest_version"], 3)
            self.assertEqual(result["exam_deployment_status"], "not_cleared")
            self.assertFalse(result["learner_content_included"])
            self.assertFalse(result["private_project_files_included"])
            self.assertEqual(package.stat().st_mode & 0o077, 0)
            with zipfile.ZipFile(package) as archive:
                names = archive.namelist()
                self.assertIn("manifest.json", names)
                self.assertIn("v2/sidepanel.html", names)
                self.assertNotIn("tests/test_unibot_extension_package.py", names)
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["manifest_version"], 3)
                content = "".join(archive.read(name).decode("utf-8") for name in names)
            self.assertEqual(scan_text(content, "extension-package-test")["status"], "pass")

    def test_mv3_package_is_byte_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = package_extension(Path(temporary) / "first.zip")
            second = package_extension(Path(temporary) / "second.zip")
            first_bytes = (Path(temporary) / "first.zip").read_bytes()
            second_bytes = (Path(temporary) / "second.zip").read_bytes()
            self.assertEqual(first["package_sha256"], second["package_sha256"])
            self.assertEqual(first_bytes, second_bytes)


if __name__ == "__main__":
    unittest.main()
