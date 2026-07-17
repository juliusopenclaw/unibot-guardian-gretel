from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.clearance import write_institutional_review_bundle  # noqa: E402
from unibot.institutional_audit import audit_institutional_review_bundle  # noqa: E402
from unibot.release_evidence import REQUIRED_GATE_IDS  # noqa: E402


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def _valid_inputs(root: Path, source_commit: str) -> tuple[Path, Path, Path]:
    evidence: dict[str, object] = {
        "schema_version": "UniBotReleaseEvidenceV1",
        "status": "pass",
        "source_commit": source_commit,
        "source_worktree_clean": True,
        "provider_calls": 0,
        "learner_content_included": False,
        "private_project_files_included": False,
        "automatic_publication": False,
        "automatic_merge": False,
        "exam_deployment_status": "not_cleared",
        "gate_count": len(REQUIRED_GATE_IDS),
        "gates": [{"gate_id": gate_id, "status": "pass"} for gate_id in REQUIRED_GATE_IDS],
    }
    evidence["evidence_sha256"] = hashlib.sha256(_canonical_json(evidence).encode("utf-8")).hexdigest()
    colab = {
        "schema_version": "UniBotLiveColabCanaryV1",
        "status": "pass",
        "source_commit": source_commit,
        "provider_calls": 0,
        "source_text_omitted": True,
        "raw_cell_text_persisted": False,
        "notebook_output_read": False,
    }
    jupyter = {
        "schema_version": "UniBotLiveJupyterCanaryV1",
        "status": "pass",
        "source_commit": source_commit,
        "provider_calls": 0,
        "source_text_omitted": True,
        "raw_cell_text_persisted": False,
        "notebook_output_read": False,
        "notebook_code_executed": False,
        "native_transport": True,
        "tutor_flow_status": "pass",
        "session_started": True,
        "session_stopped": True,
        "session_deleted": True,
        "effective_help_level": "A2",
        "source_anchor_count": 1,
        "complete_solution_emitted": False,
        "hint_text_omitted": True,
        "local_tutor": "deterministic_source_grounded_v1",
    }
    paths = (root / "release.json", root / "colab.json", root / "jupyter.json")
    for path, payload in zip(paths, (evidence, colab, jupyter)):
        _write_json(path, payload)
    return paths


def _build_bundle(root: Path) -> Path:
    source_commit = "a" * 40
    release_evidence, colab, jupyter = _valid_inputs(root, source_commit)
    output = root / "bundle"
    with patch(
        "unibot.clearance.public_source_provenance",
        return_value={
            "schema_version": "UniBotPublicSourceProvenanceV1",
            "status": "verified",
            "commit": source_commit,
            "working_tree_clean": True,
        },
    ), patch(
        "unibot.clearance.validate_release_evidence",
        return_value={"status": "pass", "source_commit": source_commit, "issues": []},
    ):
        result = write_institutional_review_bundle(
            output,
            release_evidence=release_evidence,
            colab_canary=colab,
            jupyter_canary=jupyter,
        )
    if result["status"] != "written":
        raise AssertionError(result)
    return output


class UniBotInstitutionalAuditTests(unittest.TestCase):
    def test_audit_accepts_complete_evidence_bound_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = audit_institutional_review_bundle(_build_bundle(Path(temporary)))

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["file_count"], 13)
        self.assertEqual(result["verified_file_count"], 12)
        self.assertEqual(result["release_verification_status"], "pass")
        self.assertEqual(result["provider_calls"], 0)
        self.assertTrue(result["read_only"])
        self.assertFalse(result["raw_content_returned"])
        self.assertEqual(result["issues"], [])

    def test_audit_blocks_tampered_public_file_without_returning_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = _build_bundle(Path(temporary))
            demo = bundle / "PUBLIC-DEMO.md"
            demo.write_text(demo.read_text(encoding="utf-8") + "\nTampered.\n", encoding="utf-8")
            result = audit_institutional_review_bundle(bundle)

        self.assertEqual(result["status"], "blocked")
        self.assertIn("file_record_hash_or_size_mismatch", result["issues"])
        self.assertFalse(result["raw_content_returned"])
        self.assertNotIn("Tampered", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
