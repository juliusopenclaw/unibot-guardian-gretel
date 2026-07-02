from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.guardian import (  # noqa: E402
    EXAM_CONTROLLED,
    GuardianEvent,
    classify_external_ai_output,
    compute_independence_score,
    generate_socratic_prompt_card,
    guardian_practice_flow,
    recommend_next_tasks,
    update_local_skill_state,
)


class UniBotGuardianTests(unittest.TestCase):
    def test_prompt_card_is_socratic_and_separate(self) -> None:
        card = generate_socratic_prompt_card(
            "Ich verstehe Python Listen und Boxplots in Colab nicht.",
            source_card_ids=["uoc-ki-lehre", "google-colab-gemini"],
        )

        self.assertEqual(card["mode"], "practice_overlay")
        self.assertIn("keine finale Loesung", card["copyable_prompt"])
        self.assertIn("python_lists", card["skill_tags"])
        self.assertIn("boxplots", card["skill_tags"])
        self.assertEqual(card["source_card_ids"], ["uoc-ki-lehre", "google-colab-gemini"])

    def test_postfilter_blocks_solution_code_values_and_privacy(self) -> None:
        review = classify_external_ai_output(
            "Hier ist der komplette Code: import pandas as pd\nwerte = [1, 2, 3]\nplt.boxplot(werte)\n"
            f"Frag {'max'}@example.invalid nach dem Attest.",
            requested_help_level="A4",
        )

        self.assertTrue(review["blocked"])
        self.assertEqual(review["status"], "blocked")
        self.assertIn("final_solution", review["categories"])
        self.assertIn("code_fix_or_complete_code", review["categories"])
        self.assertIn("values_inserted", review["categories"])
        self.assertIn("private_or_sensitive_data", review["categories"])
        self.assertIn("email", review["privacy_flags"])
        self.assertIn("health_or_inclusion_data", review["privacy_flags"])
        self.assertNotIn("komplette Code", json.dumps(review, ensure_ascii=False))

    def test_allowed_socratic_help_passes_without_raw_storage(self) -> None:
        review = classify_external_ai_output(
            "Welche Spalte ist dein Messwert, und welche Gruppe willst du vergleichen?",
            requested_help_level="A2",
        )

        self.assertFalse(review["blocked"])
        self.assertTrue(review["public_safe"])
        self.assertEqual(review["requested_help_level"], "A2")
        self.assertIn("raw_output_hash", review)

    def test_independence_score_matrix_and_accessibility(self) -> None:
        a0 = compute_independence_score("A0", accessibility_used=True)
        a4 = compute_independence_score([{"help_level": "A2"}, {"help_level": "A4"}])
        a6 = compute_independence_score("A6")

        self.assertEqual(a0["score"], 100)
        self.assertTrue(a0["accessibility_neutral"])
        self.assertEqual(a4["deduction"], 25)
        self.assertLess(a4["score"], 100)
        self.assertEqual(a6["status"], "repeat_task")
        self.assertEqual(a6["score"], 0)

    def test_skill_state_recommends_targeted_tasks(self) -> None:
        state = update_local_skill_state(
            [
                {"text": "list append IndexError", "help_level": "A4"},
                {"text": "pandas DataFrame df.dtypes", "help_level": "A2"},
            ]
        )
        recommendations = recommend_next_tasks(state)
        payload = json.dumps(recommendations, ensure_ascii=False)

        self.assertIn("python_lists", state)
        self.assertIn("pandas", state)
        self.assertIn("practice-only", payload)
        self.assertGreaterEqual(len(recommendations["tasks"]), 2)

    def test_exam_controlled_blocks_without_approval(self) -> None:
        review = classify_external_ai_output(
            "Welche Frage solltest du dir zuerst stellen?",
            requested_help_level="A2",
            mode=EXAM_CONTROLLED,
        )

        self.assertTrue(review["blocked"])
        self.assertIn("exam_controlled_requires_written_approval", review["categories"])

    def test_guardian_event_and_flow_are_public_safe(self) -> None:
        flow = guardian_practice_flow(
            task="Python Listen in Colab debuggen",
            external_output="Stelle zuerst fest, welche Liste leer ist.",
            requested_help_level="A2",
            source_card_ids=["vanlehn-2011"],
            student_reflection="Ich pruefe zuerst len(meine_liste).",
        )

        self.assertEqual(flow["artifact_type"], "unibot_guardian_practice_flow")
        self.assertFalse(flow["raw_output_stored"])
        self.assertEqual(flow["postfilter"]["status"], "allowed")
        self.assertEqual(flow["guardian_event"]["source_card_ids"], ["vanlehn-2011"])
        self.assertIn("raw_output_hash", flow["guardian_event"])
        self.assertNotIn("Stelle zuerst fest", json.dumps(flow["guardian_event"], ensure_ascii=False))

        event = GuardianEvent(
            mode="practice_overlay",
            tool="colab_gemini",
            task_id="task",
            skill_tags=["debugging"],
            raw_output_hash="abc",
            classification=[],
            allowed_hint="Pruefe die Fehlermeldung.",
            help_level="A2",
        )
        self.assertEqual(event.to_public_dict()["raw_output_hash"], "abc")

    def test_docs_and_extension_files_exist(self) -> None:
        required = [
            ROOT / "docs" / "unibot" / "UNIBOT_PIPELINE.md",
            ROOT / "docs" / "unibot" / "UNIBOT_SOURCE_CARDS.md",
            ROOT / "docs" / "unibot" / "UNIBOT_THREAT_MODEL.md",
            ROOT / "docs" / "unibot" / "UNIBOT_MASTER_THESIS_STRATEGY.md",
            ROOT / "docs" / "unibot" / "UNIBOT_ADAPTIVE_TASKS.md",
            ROOT / "docs" / "unibot" / "UNIBOT_DEMO_TEST_PLAN.md",
            ROOT / "docs" / "unibot" / "UNIBOT_DEMO_FEEDBACK.md",
            ROOT / "docs" / "unibot" / "UNIBOT_FEEDBACK_TRIAGE.md",
            ROOT / "docs" / "unibot" / "UNIBOT_GITHUB_ISSUE_BUNDLE.md",
            ROOT / "docs" / "unibot" / "UNIBOT_RELEASE_RUNBOOK.md",
            ROOT / "docs" / "unibot" / "UNIBOT_COMPLIANCE_MATRIX.md",
            ROOT / "docs" / "unibot" / "UNIBOT_PILOT_PROTOCOL.md",
            ROOT / "docs" / "unibot" / "UNIBOT_DATA_PROTECTION_SCREENING.md",
            ROOT / "unibot" / "browser_extension" / "manifest.json",
            ROOT / "unibot" / "browser_extension" / "background.js",
            ROOT / "unibot" / "browser_extension" / "content.js",
            ROOT / "unibot" / "browser_extension" / "sidepanel.html",
            ROOT / "unibot" / "browser_extension" / "sidepanel.js",
        ]
        for path in required:
            self.assertTrue(path.exists(), path)

        manifest = json.loads((ROOT / "unibot" / "browser_extension" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifest_version"], 3)
        self.assertIn("sidePanel", manifest["permissions"])
