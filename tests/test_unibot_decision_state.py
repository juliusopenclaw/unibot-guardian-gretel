from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.decision_state import build_external_decision_state  # noqa: E402
from unibot.public_safety import scan_text  # noqa: E402
from unibot.server import route_request  # noqa: E402


def valid_extraction_decision() -> dict[str, object]:
    return {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "delete private extraction artifacts after reviewed metadata is accepted",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic written extraction decision",
    }


def valid_exam_clearance() -> dict[str, object]:
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
        "decision_reference": "synthetic written exam clearance",
        "allowed_modes": ["exam_controlled_gateway", "controlled_notebook"],
        "help_levels_allowed": ["A0", "A1", "A2"],
        "no_proctoring": True,
        "no_ai_detection": True,
        "no_automatic_grading": True,
        "human_review_required": True,
        "raw_text_public_release_allowed": False,
    }


class UniBotDecisionStateTests(unittest.TestCase):
    def test_decision_state_defaults_to_pending_without_records(self) -> None:
        state = build_external_decision_state()
        payload = json.dumps(state, ensure_ascii=False)

        self.assertEqual(state["schema_version"], "unibot-external-decision-state-v1")
        self.assertEqual(state["artifact_type"], "unibot_external_decision_state")
        self.assertEqual(state["status"], "pending_external_decisions")
        self.assertEqual(state["exam_deployment_status"], "not_cleared")
        self.assertFalse(state["gate_summary"]["local_extraction_can_start"])
        self.assertFalse(state["gate_summary"]["exam_clearance_record_valid"])
        self.assertEqual(state["public_safety_status"], "pass")
        self.assertEqual(scan_text(payload, "decision-state-default-test")["status"], "pass")

    def test_decision_state_validates_records_without_storing_raw_references(self) -> None:
        state = build_external_decision_state(
            extraction_decision_record=valid_extraction_decision(),
            exam_clearance_record=valid_exam_clearance(),
            deployment_go_reference="synthetic manual go reference",
        )
        payload = json.dumps(state, ensure_ascii=False)

        self.assertEqual(state["status"], "external_decisions_validated_for_next_gates")
        self.assertTrue(state["gate_summary"]["local_extraction_can_start"])
        self.assertTrue(state["gate_summary"]["exam_clearance_record_valid"])
        self.assertTrue(state["gate_summary"]["manual_deployment_go_recorded"])
        self.assertEqual(state["exam_deployment_status"], "not_cleared")
        self.assertEqual(state["local_extraction_decision"]["status"], "ok_authorizes_local_extraction")
        self.assertEqual(state["exam_authority_decision"]["status"], "ok_exam_controlled_gateway_clearance_record")
        self.assertFalse(state["local_extraction_decision"]["raw_decision_reference_stored"])
        self.assertFalse(state["exam_authority_decision"]["raw_decision_reference_stored"])
        self.assertNotIn("synthetic written extraction decision", payload)
        self.assertNotIn("synthetic written exam clearance", payload)
        self.assertNotIn("synthetic manual go reference", payload)
        self.assertEqual(state["public_safety_status"], "pass")

    def test_decision_state_api_route(self) -> None:
        status, state = route_request(
            "/api/unibot/stakeholder/decision-state",
            {
                "extraction_decision_record": valid_extraction_decision(),
                "exam_clearance_record": valid_exam_clearance(),
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(state["artifact_type"], "unibot_external_decision_state")
        self.assertEqual(state["status"], "external_decisions_validated_for_next_gates")
        self.assertEqual(state["exam_deployment_status"], "not_cleared")


if __name__ == "__main__":
    unittest.main()
