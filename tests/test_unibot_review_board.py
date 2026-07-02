from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.review_board import (  # noqa: E402
    build_review_board_evidence_alignment,
    build_review_board_packet,
    build_review_board_packet_markdown,
)
from unibot.server import route_request  # noqa: E402
from unibot.python_exam_local_cycle_operator_workspace_card import build_python_exam_local_cycle_operator_workspace_card  # noqa: E402
from unibot.python_exam_local_cycle_readiness_handoff import build_python_exam_local_cycle_readiness_handoff  # noqa: E402
from unibot.python_exam_local_cycle_readiness_review import build_python_exam_local_cycle_readiness_review  # noqa: E402
from unibot.python_exam_local_cycle_start_packet import build_python_exam_local_cycle_start_packet  # noqa: E402
from unibot.python_exam_operator_gate_decision_receipt import build_python_exam_operator_gate_decision_receipt  # noqa: E402
from unibot.python_exam_safe_cycle_operator_gate import build_python_exam_safe_cycle_operator_gate  # noqa: E402

from tests.test_unibot_python_exam_local_cycle_start_packet import ready_start_packet_inputs  # noqa: E402


class UniBotReviewBoardTests(unittest.TestCase):
    def test_review_board_packet_has_reviewer_packets_and_open_decisions(self) -> None:
        packet = build_review_board_packet()

        self.assertEqual(packet["schema_version"], "unibot-review-board-packet-v1")
        self.assertEqual(packet["status"], "draft_for_institutional_review")
        self.assertEqual(packet["exam_deployment_status"], "not_cleared")
        self.assertEqual(packet["public_safety_status"], "pass")
        self.assertEqual(packet["status_label_de"], "Entwurf fuer interne Review der zustaendigen Stellen")
        self.assertEqual(len(packet["reviewer_packets"]), 6)
        self.assertGreaterEqual(len(packet["open_decision_register"]), 6)
        self.assertTrue(any("Pruefungsamt" in item["reviewer"] for item in packet["reviewer_packets"]))
        self.assertTrue(any("Inklusionsbuero / Nachteilsausgleich" in item["reviewer"] for item in packet["reviewer_packets"]))
        self.assertTrue(any("Datenschutz" in item["reviewer"] for item in packet["reviewer_packets"]))
        self.assertTrue(any("IT / SZI" in item["reviewer"] for item in packet["reviewer_packets"]))
        self.assertTrue(any("Lehreinheit / Modulverantwortliche" in item["reviewer"] for item in packet["reviewer_packets"]))
        self.assertTrue(any("Thesis supervision" in item["reviewer"] for item in packet["reviewer_packets"]))
        self.assertIn("No automatic grading", packet["cross_cutting_red_lines"])
        self.assertIn("exam_controlled", packet["not_ready_for"])
        self.assertEqual(packet["evidence_alignment"]["status"], "ready")
        self.assertEqual(packet["evidence_alignment"]["public_safety_status"], "pass")
        self.assertEqual(packet["evidence_alignment"]["unmapped_reviewer_count"], 0)
        self.assertEqual(packet["evidence_alignment"]["missing_claim_ids"], [])
        self.assertGreaterEqual(packet["evidence_alignment"]["thesis_claim_count"], 6)

    def test_review_board_evidence_alignment_maps_reviewers_to_readiness_gates(self) -> None:
        packet = build_review_board_packet()
        alignment = build_review_board_evidence_alignment(packet["reviewer_packets"])
        by_reviewer = {item["reviewer"]: item for item in alignment["reviewer_alignment"]}

        self.assertEqual(alignment["schema_version"], "unibot-review-board-evidence-alignment-v1")
        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["unmapped_reviewer_count"], 0)
        self.assertEqual(alignment["missing_claim_ids"], [])
        self.assertIn("unibot-readiness-evidence-snapshot-v1", alignment["readiness_snapshot_contract"]["expected_schema_version"])
        self.assertIn("review_board_packet", alignment["readiness_snapshot_contract"]["required_gate_ids"])
        self.assertIn("gretel_bachelor_thesis_package", alignment["readiness_snapshot_contract"]["required_gate_ids"])
        self.assertIn("exam_boundary_not_clearance", by_reviewer["Pruefungsamt"]["claim_ids"])
        self.assertIn("exam_boundary", by_reviewer["Pruefungsamt"]["readiness_check_ids"])
        self.assertIn("public_safety_and_privacy", by_reviewer["Datenschutz"]["claim_ids"])
        self.assertIn("public_safety", by_reviewer["Datenschutz"]["readiness_check_ids"])
        self.assertIn("reproducible_evaluation_package", by_reviewer["Thesis supervision"]["claim_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])

    def test_review_board_markdown_and_api_routes(self) -> None:
        markdown = build_review_board_packet_markdown()
        self.assertIn("# UniBot Review Board Packet", markdown)
        self.assertIn("Cross-cutting Red Lines", markdown)
        self.assertIn("Evidence Alignment", markdown)
        self.assertIn("Snapshot gate count", markdown)
        self.assertIn("Open Decisions", markdown)

        status, packet = route_request("/api/unibot/review-board-packet", {})
        self.assertEqual(status, 200)
        self.assertEqual(packet["status"], "draft_for_institutional_review")

        status, response = route_request("/api/unibot/review-board-packet-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        self.assertIn("Reviewer Blocks", response["markdown"])

    def test_review_board_packet_can_surface_local_cycle_chain_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            console, gate, _decision = ready_start_packet_inputs(temp_dir)
            confirmed_gate = build_python_exam_safe_cycle_operator_gate(
                python_exam_safe_cycle_console=console,
                selected_skill_tag="python_lists",
            )
            confirmed_ids = [card["step_id"] for card in confirmed_gate["confirmation_cards"]]
            decision = build_python_exam_operator_gate_decision_receipt(
                python_exam_safe_cycle_operator_gate=confirmed_gate,
                confirmed_step_ids=confirmed_ids,
                selected_skill_tag="python_lists",
            )
            start_packet = build_python_exam_local_cycle_start_packet(
                python_exam_safe_cycle_console=console,
                python_exam_safe_cycle_operator_gate=confirmed_gate,
                python_exam_operator_gate_decision_receipt=decision,
                selected_skill_tag="python_lists",
            )
            review = build_python_exam_local_cycle_readiness_review(
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            handoff = build_python_exam_local_cycle_readiness_handoff(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            workspace_card = build_python_exam_local_cycle_operator_workspace_card(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_start_packet=start_packet,
                selected_skill_tag="python_lists",
            )
            packet = build_review_board_packet(
                python_exam_local_cycle_readiness_review=review,
                python_exam_local_cycle_readiness_handoff=handoff,
                python_exam_local_cycle_operator_workspace_card=workspace_card,
                selected_skill_tag="python_lists",
            )

            self.assertEqual(packet["local_cycle_chain_snapshot"]["status"], "python_exam_local_cycle_chain_snapshot_ready")
            self.assertEqual(packet["evidence_summary"]["local_cycle_chain_snapshot_status"], "python_exam_local_cycle_chain_snapshot_ready")
            self.assertIn("Local Cycle Chain", build_review_board_packet_markdown())


if __name__ == "__main__":
    unittest.main()
