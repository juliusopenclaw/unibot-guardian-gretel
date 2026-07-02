from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.clearance import build_institutional_clearance_board, validate_clearance_record  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def valid_exam_clearance_record() -> dict[str, object]:
    return {
        "clearance_scope": "exam_controlled_gateway",
        "decision_status": "approved",
        "reviewer_roles": [
            "Pruefungsamt",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
            "Inklusionsbuero / Nachteilsausgleich",
        ],
        "decision_reference": "synthetic exam gateway written clearance fixture",
        "allowed_modes": ["exam_controlled_gateway", "controlled_notebook"],
        "help_levels_allowed": ["A0", "A1", "A2"],
        "no_proctoring": True,
        "no_ai_detection": True,
        "no_automatic_grading": True,
        "human_review_required": True,
        "raw_text_public_release_allowed": False,
    }


class UniBotInstitutionalClearanceTests(unittest.TestCase):
    def test_clearance_board_is_public_safe_and_not_exam_clearance(self) -> None:
        board = build_institutional_clearance_board()
        payload = json.dumps(board, ensure_ascii=False)

        self.assertEqual(board["schema_version"], "unibot-institutional-clearance-v1")
        self.assertEqual(board["artifact_type"], "unibot_institutional_clearance_board")
        self.assertEqual(board["status"], "pending_written_clearance")
        self.assertEqual(board["exam_deployment_status"], "not_cleared")
        self.assertEqual(board["public_safety_status"], "pass")
        self.assertEqual(len(board["scope_lanes"]), 4)
        self.assertIn("exam_controlled_gateway", board["not_ready_for"])
        self.assertIn("not approval", board["decision_boundary"])
        self.assertEqual(scan_text(payload, "clearance-board-test")["status"], "pass")

    def test_valid_exam_clearance_record_hashes_reference_and_stays_scope_bound(self) -> None:
        validation = validate_clearance_record(valid_exam_clearance_record())
        payload = json.dumps(validation, ensure_ascii=False)

        self.assertEqual(validation["status"], "ok_exam_controlled_gateway_clearance_record")
        self.assertTrue(validation["cleared_scope_by_record"])
        self.assertEqual(validation["exam_deployment_status"], "not_cleared")
        self.assertEqual(validation["public_safety_status"], "pass")
        self.assertFalse(validation["raw_decision_reference_stored"])
        self.assertTrue(validation["decision_reference_hash"])
        self.assertNotIn("synthetic exam gateway written clearance fixture", payload)
        self.assertIn("validator_checks_record_shape_only", " ".join(validation["warnings"]))

    def test_clearance_record_blocks_missing_roles_and_forbidden_clauses(self) -> None:
        invalid = valid_exam_clearance_record()
        invalid["reviewer_roles"] = ["Pruefungsamt"]
        invalid["no_proctoring"] = False
        invalid["help_levels_allowed"] = ["A0", "A6"]
        invalid["raw_text_public_release_allowed"] = True

        validation = validate_clearance_record(invalid)

        self.assertEqual(validation["status"], "blocked")
        self.assertFalse(validation["cleared_scope_by_record"])
        self.assertIn("missing_required_reviewer_roles", validation["issues"])
        self.assertIn("no_proctoring_clause_required", validation["issues"])
        self.assertIn("a6_must_always_be_blocked", validation["issues"])
        self.assertIn("raw_text_public_release_must_remain_false", validation["issues"])

    def test_clearance_api_routes(self) -> None:
        status, board = route_request("/api/unibot/institutional-clearance/board", {})
        self.assertEqual(status, 200)
        self.assertEqual(board["artifact_type"], "unibot_institutional_clearance_board")

        status, validation = route_request(
            "/api/unibot/institutional-clearance/validate",
            {"record": valid_exam_clearance_record()},
        )
        self.assertEqual(status, 200)
        self.assertEqual(validation["status"], "ok_exam_controlled_gateway_clearance_record")


if __name__ == "__main__":
    unittest.main()
