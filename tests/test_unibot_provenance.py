from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from unibot.provenance import PUBLIC_PROVENANCE_SCHEMA_VERSION, public_source_provenance


class UniBotPublicProvenanceTests(unittest.TestCase):
    def test_current_public_source_is_clean_and_path_free(self) -> None:
        provenance = public_source_provenance(Path(__file__).resolve().parents[1])

        self.assertEqual(provenance["schema_version"], PUBLIC_PROVENANCE_SCHEMA_VERSION)
        self.assertEqual(provenance["status"], "verified")
        self.assertRegex(provenance["commit"], r"^[0-9a-f]{40}$")
        self.assertTrue(provenance["working_tree_clean"])
        self.assertNotIn("/" + "Users/", json.dumps(provenance))

    def test_dirty_source_fails_closed_without_exposing_status_output(self) -> None:
        commit = subprocess.CompletedProcess([], 0, stdout="a" * 40 + "\n", stderr="")
        dirty = subprocess.CompletedProcess([], 0, stdout=" M private-notebook.ipynb\n", stderr="")
        with patch("unibot.provenance.subprocess.run", side_effect=[commit, dirty]):
            provenance = public_source_provenance(Path("/synthetic/repository"))

        self.assertEqual(provenance["status"], "blocked_dirty_worktree")
        self.assertEqual(provenance["commit"], "a" * 40)
        self.assertFalse(provenance["working_tree_clean"])
        self.assertNotIn("private-notebook", json.dumps(provenance))


if __name__ == "__main__":
    unittest.main()
