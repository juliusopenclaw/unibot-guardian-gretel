from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.source_cards import (  # noqa: E402
    SOURCE_CARD_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
    build_source_card_drift_report,
    build_source_card_release_review_board_claim_alignment,
    get_source_card,
    list_source_cards,
    required_source_card_ids,
    source_card_corpus_hash,
    source_card_drift_report_hash,
    synthetic_source_card_workspace_card,
)
from unibot.public_safety import scan_text  # noqa: E402


class UniBotSourceCardTests(unittest.TestCase):
    def test_source_card_drift_report_passes_public_required_cards(self) -> None:
        report = build_source_card_drift_report(as_of="2026-07-03")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["public_safety_status"], "pass")
        self.assertGreaterEqual(report["card_count"], report["required_source_card_count"])
        self.assertEqual(report["missing_required_source_card_ids"], [])
        self.assertEqual(report["unlisted_high_risk_source_card_ids"], [])
        self.assertEqual(report["duplicate_source_ids"], [])
        self.assertEqual(report["stale_source_card_ids"], [])
        self.assertIsNotNone(get_source_card("dfg-gwp"))
        self.assertIsNotNone(get_source_card("uoc-szi-assistenzstelle-2026"))
        self.assertIn("zai-glm-52", required_source_card_ids())

    def test_high_risk_university_cards_preserve_authority_boundaries(self) -> None:
        self.assertIn("exam-specific ban", get_source_card("uoc-ki-pruefungsrecht")["product_rule"])
        self.assertIn("assistive technology", get_source_card("uoc-szi-klausurunterstuetzung-2026")["product_rule"])

    def test_source_card_claim_alignment_links_release_review_board_chain(self) -> None:
        drift = build_source_card_drift_report(as_of="2026-07-03")
        alignment = build_source_card_release_review_board_claim_alignment(drift)

        self.assertEqual(alignment["status"], "ready")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertTrue(alignment["public_link_only"])
        self.assertTrue(alignment["all_cards_have_product_rules"])
        self.assertGreaterEqual(alignment["source_card_count"], alignment["required_source_card_count"])
        self.assertEqual(
            alignment["manual_publication_claim_contract"]["expected_schema_version"],
            SOURCE_CARD_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
        )
        self.assertIn("source_cards", alignment["unique_readiness_check_ids"])
        self.assertIn("source_card_drift_guard", alignment["unique_readiness_check_ids"])
        self.assertIn("python_exam_local_cycle_operator_workspace_card", alignment["unique_readiness_check_ids"])
        self.assertIn("redteam", alignment["unique_readiness_check_ids"])
        self.assertIn("notebook_template", alignment["unique_readiness_check_ids"])
        self.assertIn("publication_package", alignment["unique_readiness_check_ids"])
        self.assertIn("review_board_packet", alignment["unique_readiness_check_ids"])
        self.assertIn("human_submission_review_required", alignment["required_human_gates"])
        self.assertIn("written_university_clearance_required_before_exam_use", alignment["required_human_gates"])
        self.assertEqual(alignment["missing_release_review_board_claim_check_ids"], [])
        self.assertEqual(alignment["missing_release_review_board_claim_human_gates"], [])
        self.assertEqual(alignment["failed_contract_ids"], [])
        self.assertTrue(alignment["contracts"]["workspace_card_source_gate_linked"])
        self.assertEqual(alignment["workspace_card_status"], "python_exam_local_cycle_operator_workspace_card_ready")
        self.assertEqual(alignment["workspace_card_selected_skill_tag"], "pandas")
        self.assertTrue(alignment["workspace_card_ready_for_operator_prefill"])
        self.assertEqual(alignment["workspace_card_help_ledger_status"], "help_ledger_preview_ready")
        self.assertTrue(alignment["workspace_card_help_ledger_hash_present"])
        self.assertTrue(alignment["workspace_card_readiness_gate_linked"])
        self.assertTrue(alignment["workspace_card_source_gate_linked"])
        self.assertTrue(alignment["workspace_card_readiness_gate_claim_linked"])
        self.assertFalse(alignment["raw_workspace_card_returned"])
        self.assertEqual(alignment["source_card_corpus_hash"], source_card_corpus_hash())
        self.assertEqual(alignment["source_card_drift_hash"], source_card_drift_report_hash(drift))
        self.assertIn("exam clearance", alignment["blocked_claims"])
        self.assertEqual(scan_text(json.dumps(alignment, ensure_ascii=False), "source-card-alignment")["status"], "pass")

    def test_source_card_hash_helpers_link_corpus_and_drift_report(self) -> None:
        drift = build_source_card_drift_report(as_of="2026-07-03")

        self.assertTrue(source_card_corpus_hash())
        self.assertTrue(source_card_drift_report_hash(drift))
        self.assertNotEqual(source_card_corpus_hash(), source_card_drift_report_hash(drift))

    def test_source_card_claim_alignment_rejects_unlinked_workspace_card_hashes(self) -> None:
        drift = build_source_card_drift_report(as_of="2026-07-03")
        card = synthetic_source_card_workspace_card()
        card["workspace_card_summary"]["checkpoint_hash"] = "wrong-source-card-corpus-hash"
        card["workspace_card_summary"]["task_hash"] = "wrong-source-card-drift-hash"

        alignment = build_source_card_release_review_board_claim_alignment(drift, card)

        self.assertEqual(alignment["status"], "blocked")
        self.assertFalse(alignment["workspace_card_source_gate_linked"])
        self.assertIn("workspace_card_source_gate_linked", alignment["failed_contract_ids"])

    def test_source_card_claim_alignment_blocks_failed_drift_report(self) -> None:
        drift = build_source_card_drift_report(as_of="2026-07-03")
        drift["status"] = "blocked"
        drift["missing_required_source_card_ids"] = ["dfg-gwp"]
        alignment = build_source_card_release_review_board_claim_alignment(drift)

        self.assertEqual(alignment["status"], "blocked")
        self.assertEqual(alignment["public_safety_status"], "pass")
        self.assertEqual(alignment["drift_status"], "blocked")

    def test_source_cards_do_not_contain_private_material(self) -> None:
        payload = json.dumps(list_source_cards(), ensure_ascii=False)

        self.assertEqual(scan_text(payload, "source-cards")["status"], "pass")
        self.assertNotIn("private_course", payload)
        self.assertNotIn("/" + "Users/", payload)

    def test_public_source_cards_document_every_required_card(self) -> None:
        documentation = (ROOT / "docs" / "unibot" / "UNIBOT_SOURCE_CARDS.md").read_text(encoding="utf-8")
        missing = [source_id for source_id in required_source_card_ids() if f"`{source_id}`" not in documentation]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
