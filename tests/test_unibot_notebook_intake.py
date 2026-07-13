from __future__ import annotations

import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nbformat

from unibot.notebook_intake import (
    NotebookIntakeError,
    import_notebook,
    normalize_public_notebook_url,
    sanitize_notebook,
    validate_public_url,
)


def notebook_bytes(*, with_output: bool = True, source: str = "value = 1") -> bytes:
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("# Public synthetic practice task"),
            nbformat.v4.new_code_cell(
                source,
                execution_count=2 if with_output else None,
                outputs=[nbformat.v4.new_output("stream", name="stdout", text="1\n")] if with_output else [],
            ),
        ]
    )
    return nbformat.writes(notebook).encode("utf-8")


class NotebookIntakeTests(unittest.TestCase):
    def test_github_blob_url_is_normalized_to_raw_host(self) -> None:
        normalized = normalize_public_notebook_url(
            "https://github.com/example/project/blob/main/practice/task.ipynb"
        )
        self.assertEqual(
            normalized,
            "https://raw.githubusercontent.com/example/project/main/practice/task.ipynb",
        )

    @patch("unibot.notebook_intake.socket.getaddrinfo")
    def test_public_url_validation_blocks_private_resolution_and_query(self, resolver: object) -> None:
        resolver.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]  # type: ignore[attr-defined]
        with self.assertRaises(NotebookIntakeError):
            validate_public_url("https://raw.githubusercontent.com/example/project/main/task.ipynb")

        resolver.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]  # type: ignore[attr-defined]
        with self.assertRaises(NotebookIntakeError):
            validate_public_url("https://raw.githubusercontent.com/example/project/main/task.ipynb?access=hidden")

    def test_sanitizer_removes_outputs_and_execution_count(self) -> None:
        sanitized, counts = sanitize_notebook(notebook_bytes())
        code = sanitized["cells"][1]
        self.assertEqual(code["outputs"], [])
        self.assertIsNone(code["execution_count"])
        self.assertEqual(counts["outputs_removed"], 1)
        self.assertFalse(sanitized["metadata"]["unibot_guardian"]["glm_context_allowed"])

    def test_sanitizer_blocks_solution_key_and_private_source(self) -> None:
        with self.assertRaises(NotebookIntakeError):
            sanitize_notebook(notebook_bytes(source="# model answer\nvalue = 1"))
        with self.assertRaises(NotebookIntakeError):
            synthetic_contact = "learner" + "@" + "example.invalid"
            sanitize_notebook(notebook_bytes(source=f"contact = '{synthetic_contact}'"))

    def test_local_import_writes_only_sanitized_notebook_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "practice.ipynb"
            source.write_bytes(notebook_bytes())
            output = root / "output"
            manifest = import_notebook(str(source), output)

            self.assertEqual(manifest["schema_version"], "unibot-notebook-manifest-v1")
            self.assertFalse(manifest["raw_source_stored"])
            self.assertEqual(manifest["exam_deployment_status"], "not_cleared")
            artifact_dir = output / manifest["sanitized_sha256"][:16]
            saved = json.loads((artifact_dir / manifest["artifact_name"]).read_text(encoding="utf-8"))
            self.assertEqual(saved["cells"][1]["outputs"], [])
            self.assertTrue((artifact_dir / "manifest.json").is_file())

    def test_public_import_uses_injected_downloader_and_does_not_store_raw_source(self) -> None:
        def fake_download(source: str, **_: object) -> tuple[bytes, str]:
            self.assertTrue(source.startswith("https://"))
            return notebook_bytes(), "https://raw.githubusercontent.com/example/project/main/task.ipynb"

        with tempfile.TemporaryDirectory() as temporary:
            manifest = import_notebook(
                "https://raw.githubusercontent.com/example/project/main/task.ipynb",
                Path(temporary),
                downloader=fake_download,
            )
        self.assertEqual(manifest["source_kind"], "public_https_url")
        self.assertFalse(manifest["raw_source_stored"])
        self.assertFalse(manifest["glm_context_allowed"])


if __name__ == "__main__":
    unittest.main()
