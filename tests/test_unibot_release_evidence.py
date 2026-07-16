from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from unibot.release_evidence import (
    REQUIRED_GATE_IDS,
    RELEASE_EVIDENCE_SCHEMA_VERSION,
    validate_release_evidence,
    write_release_evidence,
)


def _evidence_hash(payload: dict[str, object]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "evidence_sha256"}
    return hashlib.sha256(
        json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _valid_payload(commit: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": RELEASE_EVIDENCE_SCHEMA_VERSION,
        "artifact_type": "unibot_release_verification_evidence",
        "source_commit": commit,
        "source_worktree_clean": True,
        "provider_calls": 0,
        "learner_content_included": False,
        "private_project_files_included": False,
        "automatic_publication": False,
        "automatic_merge": False,
        "exam_deployment_status": "not_cleared",
        "status": "pass",
        "generated_at_utc": "2026-07-17T12:00:00+00:00",
        "gate_count": len(REQUIRED_GATE_IDS),
        "gates": [
            {
                "gate_id": gate_id,
                "command_id": f"synthetic_{gate_id}",
                "status": "pass",
                "exit_code": 0,
                "duration_ms": 1,
                "output_sha256": "a" * 64,
                "metrics": {"passed_count": 1},
            }
            for gate_id in REQUIRED_GATE_IDS
        ],
    }
    payload["evidence_sha256"] = _evidence_hash(payload)
    return payload


class UniBotReleaseEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[1]
        self.commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repository,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def test_valid_evidence_is_bound_to_clean_current_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "RELEASE-EVIDENCE.json"
            path.write_text(json.dumps(_valid_payload(self.commit)), encoding="utf-8")

            result = validate_release_evidence(path, repository=self.repository)

            self.assertEqual(result["status"], "pass", result["issues"])
            self.assertEqual(result["source_commit"], self.commit)
            self.assertEqual(result["gate_ids"], list(REQUIRED_GATE_IDS))

    def test_tampered_hash_and_raw_output_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "RELEASE-EVIDENCE.json"
            payload = _valid_payload(self.commit)
            gates = payload["gates"]
            assert isinstance(gates, list)
            gates[0]["raw_output"] = "synthetic raw log"
            payload["evidence_sha256"] = _evidence_hash(payload)
            path.write_text(json.dumps(payload), encoding="utf-8")

            result = validate_release_evidence(path, repository=self.repository)

            self.assertEqual(result["status"], "blocked")
            self.assertIn("raw_output_or_path_present", result["issues"])

    def test_missing_green_gate_is_blocked_even_when_overall_status_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "RELEASE-EVIDENCE.json"
            payload = _valid_payload(self.commit)
            gates = payload["gates"]
            assert isinstance(gates, list)
            gates.pop()
            payload["evidence_sha256"] = _evidence_hash(payload)
            path.write_text(json.dumps(payload), encoding="utf-8")

            result = validate_release_evidence(path, repository=self.repository)

            self.assertEqual(result["status"], "blocked")
            self.assertIn("gate_not_green:source_card_drift", result["issues"])

    def test_writer_records_only_aggregate_gate_data(self) -> None:
        def fake_gate(gate_id: str, *_args: object, **_kwargs: object) -> dict[str, object]:
            return {
                "gate_id": gate_id,
                "command_id": "synthetic_gate",
                "status": "pass",
                "exit_code": 0,
                "duration_ms": 1,
                "output_sha256": "b" * 64,
                "metrics": {"passed_count": 1},
            }

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "RELEASE-EVIDENCE.json"
            with (
                patch("unibot.release_evidence._git_value", return_value="b" * 40),
                patch("unibot.release_evidence._worktree_clean", return_value=True),
                patch("unibot.release_evidence._run_gate", side_effect=fake_gate),
                patch(
                    "unibot.release_evidence._source_card_gate",
                    return_value=fake_gate("source_card_drift"),
                ),
            ):
                result = write_release_evidence(path, repository=self.repository)

            self.assertEqual(result["status"], "pass")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("stdout", json.dumps(payload))
            self.assertNotIn("stderr", json.dumps(payload))
            self.assertNotIn("/" + "Users/", json.dumps(payload))
            self.assertEqual(path.stat().st_mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
