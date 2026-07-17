from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.clearance import (  # noqa: E402
    ACCESSIBILITY_REVIEW_SCHEMA_VERSION,
    ACCESSIBILITY_REVIEW_SOURCE_CARD_IDS,
    INSTITUTIONAL_PRESENTATION_SCHEMA_VERSION,
    INSTITUTIONAL_REVIEW_DECISION_TEMPLATE_SCHEMA_VERSION,
    REGULATORY_PROFILE_SCHEMA_VERSION,
    build_accessibility_review_plan,
    build_institutional_clearance_board,
    build_institutional_review_decision_template,
    build_institutional_review_decision_template_markdown,
    build_institutional_presentation_markdown,
    build_institutional_presentation_packet,
    build_regulatory_profile,
    validate_clearance_record,
    validate_accessibility_review_plan,
    validate_institutional_review_decision_template,
    validate_regulatory_profile,
    write_institutional_review_bundle,
)
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
    def test_human_review_decision_template_is_blank_hash_only_and_not_clearance(self) -> None:
        template = build_institutional_review_decision_template()
        self.assertEqual(template["schema_version"], INSTITUTIONAL_REVIEW_DECISION_TEMPLATE_SCHEMA_VERSION)
        self.assertEqual(template["status"], "blank_for_human_completion")
        self.assertEqual(template["scope"], "local_learning_and_practice_only")
        self.assertEqual(template["exam_deployment_status"], "not_cleared")
        self.assertEqual(len(template["review_lanes"]), 5)
        self.assertFalse(template["data_minimisation"]["raw_meeting_text_stored"])
        self.assertFalse(template["data_minimisation"]["health_or_accommodation_details_stored"])
        self.assertTrue(template["human_boundary"]["human_completion_required"])
        self.assertFalse(template["human_boundary"]["automatic_approval"])
        self.assertEqual(validate_institutional_review_decision_template(template)["status"], "ok")
        markdown = build_institutional_review_decision_template_markdown(template)
        self.assertIn("InstitutionalReviewDecisionTemplateV1", markdown)
        self.assertIn("keine Freigabe", markdown)
        self.assertEqual(scan_text(markdown, "decision-template-test")["status"], "pass")

        tampered = dict(template)
        tampered["human_boundary"] = dict(template["human_boundary"], automatic_approval=True)
        self.assertEqual(validate_institutional_review_decision_template(tampered)["status"], "blocked")

    def test_accessibility_review_is_source_bound_and_human_gated(self) -> None:
        plan = build_accessibility_review_plan()
        self.assertEqual(plan["schema_version"], ACCESSIBILITY_REVIEW_SCHEMA_VERSION)
        self.assertEqual(plan["status"], "ready_for_human_accessibility_review")
        self.assertEqual(plan["scope"], "local_learning_and_practice_only")
        self.assertEqual(set(plan["source_card_ids"]), set(ACCESSIBILITY_REVIEW_SOURCE_CARD_IDS))
        self.assertEqual(len(plan["checks"]), 8)
        self.assertTrue(plan["human_review"]["signoff_required"])
        self.assertTrue(plan["release_gate"]["critical_failure_blocks_scope"])
        self.assertTrue(plan["release_gate"]["no_automatic_accommodation_decision"])
        self.assertEqual(plan["public_safety_status"], "pass")
        validation = validate_accessibility_review_plan(plan)
        self.assertEqual(validation["status"], "ok")
        self.assertFalse(validation["conformance_cleared"])
        self.assertTrue(validation["human_review_required"])

        tampered = dict(plan)
        tampered["source_card_ids"] = ["wcag-22"]
        self.assertEqual(validate_accessibility_review_plan(tampered)["status"], "blocked")

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
        self.assertEqual(board["regulatory_profile"]["deployment_status"], "not_cleared")
        self.assertEqual(scan_text(payload, "clearance-board-test")["status"], "pass")

    def test_regulatory_profile_is_public_safe_and_human_gated(self) -> None:
        profile = build_regulatory_profile()
        payload = json.dumps(profile, ensure_ascii=False)

        self.assertEqual(profile["schema_version"], REGULATORY_PROFILE_SCHEMA_VERSION)
        self.assertEqual(profile["status"], "review_preparation")
        self.assertEqual(profile["deployment_status"], "not_cleared")
        self.assertEqual(profile["intended_use"], "local_learning_and_practice")
        self.assertEqual(profile["missing_source_card_ids"], [])
        self.assertEqual(profile["public_safety_status"], "pass")
        self.assertIn("Pruefungsamt", profile["human_authority_required"])
        self.assertIn("Inklusionsbuero / Nachteilsausgleich", profile["human_authority_required"])
        self.assertEqual(len(profile["human_authority_required"]), len(set(profile["human_authority_required"])))
        self.assertIn("automatic grading", profile["excluded_functions"])
        self.assertIn("AI-use detection or disciplinary evidence", profile["excluded_functions"])
        self.assertNotIn("/" + "Users/", payload)
        self.assertNotIn("raw notebook text:", payload.lower())
        self.assertEqual(scan_text(payload, "regulatory-profile-test")["status"], "pass")

        validation = validate_regulatory_profile(profile)
        self.assertEqual(validation["status"], "ok")
        self.assertFalse(validation["cleared_scope_by_profile"])
        self.assertTrue(validation["human_review_required"])
        self.assertEqual(validation["legal_effect"], "none")

    def test_regulatory_profile_validator_fails_closed(self) -> None:
        profile = build_regulatory_profile()
        profile["deployment_status"] = "approved"
        profile["excluded_functions"] = []
        profile["missing_source_card_ids"] = ["synthetic-missing-card"]

        validation = validate_regulatory_profile(profile)

        self.assertEqual(validation["status"], "blocked")
        self.assertIn("deployment_must_remain_not_cleared", validation["issues"])
        self.assertIn("strict_exclusions_incomplete", validation["issues"])
        self.assertIn("source_cards_missing", validation["issues"])

    def test_institutional_presentation_packet_is_human_review_ready_only(self) -> None:
        packet = build_institutional_presentation_packet()
        payload = json.dumps(packet, ensure_ascii=False)

        self.assertEqual(packet["schema_version"], INSTITUTIONAL_PRESENTATION_SCHEMA_VERSION)
        self.assertEqual(packet["status"], "ready_for_human_review")
        self.assertEqual(packet["deployment_status"], "not_cleared")
        self.assertEqual(packet["evidence"]["readiness"]["status"], "public_draft_ready")
        self.assertEqual(packet["evidence"]["regulatory_profile"]["validation_status"], "ok")
        self.assertEqual(packet["evidence"]["release_runbook"]["evidence_alignment_status"], "ready")
        self.assertEqual(packet["public_safety_status"], "pass")
        self.assertIn("Pruefungsamt", packet["audience"])
        self.assertIn("Inklusionsbuero / Nachteilsausgleich", packet["audience"])
        self.assertIn("KI-Office / CIO-Board", packet["evidence"]["regulatory_profile"].get("human_authority_required", []) or packet.get("human_authority_required", []))
        self.assertEqual(packet["university_ai_governance"]["status"], "human_scope_review_required")
        self.assertIn("no automatic grading", packet["strict_non_goals"])
        self.assertEqual(packet["evidence"]["browser_mantle"]["practice_help_levels"], ["A0", "A1", "A2", "A3", "A4"])
        self.assertEqual(packet["evidence"]["browser_mantle"]["controlled_exam_candidate_help_levels"], ["A0", "A1", "A2"])
        self.assertNotIn("A5", packet["evidence"]["browser_mantle"]["practice_help_levels"])
        self.assertEqual(
            packet["evidence"]["browser_mantle"]["notebook_import"]["accepted_sources"],
            ["allowlisted public HTTPS URL", "local .ipynb file picker"],
        )
        self.assertFalse(packet["evidence"]["browser_mantle"]["notebook_import"]["local_path_forwarded"])
        self.assertEqual(
            packet["evidence"]["browser_mantle"]["controlled_exam_candidate_status"],
            "requires_written_authority_decision",
        )
        self.assertEqual(
            packet["evidence"]["browser_mantle"]["accessibility_evidence"]["status"],
            "browser_tested_human_review_required",
        )
        self.assertEqual(packet["accessibility_review"]["schema_version"], ACCESSIBILITY_REVIEW_SCHEMA_VERSION)
        self.assertEqual(packet["accessibility_review_validation"]["status"], "ok")
        self.assertEqual(
            packet["institutional_review_decision_template"]["schema_version"],
            INSTITUTIONAL_REVIEW_DECISION_TEMPLATE_SCHEMA_VERSION,
        )
        self.assertEqual(packet["institutional_review_decision_template_validation"]["status"], "ok")
        self.assertFalse(packet["institutional_review_decision_template_validation"]["automatic_approval"])
        self.assertEqual(
            packet["evidence"]["browser_mantle"]["accessibility_evidence"]["review_plan_validation_status"],
            "ok",
        )
        self.assertEqual(packet["research_artifact"]["level"], "bachelor_thesis_level")
        self.assertIn("Bachelorarbeitsfassung", packet["research_artifact"]["label_de"])
        self.assertEqual(packet["review_session"]["status"], "human_review_meeting_ready")
        self.assertEqual(len(packet["review_session"]["office_lanes"]), 5)
        self.assertEqual(
            packet["review_session"]["format"],
            "öffentliche synthetische Notebook-Demo, danach rollenbezogene Prüfung",
        )
        self.assertIn("KI-Office / CIO-Board", [lane["office"] for lane in packet["review_session"]["office_lanes"]])
        self.assertIn(
            "unibot demo --markdown",
            packet["demo_protocol"]["steps"][0],
        )
        self.assertNotIn("raw notebook text:", payload.lower())
        self.assertNotIn("/" + "Users/", payload)
        self.assertNotIn("master thesis", payload.lower())
        self.assertNotIn("masterarbeit", payload.lower())

        markdown = build_institutional_presentation_markdown(packet)
        self.assertIn("# UniBot Institutional Presentation", markdown)
        self.assertIn("## Vorlage für Prüfungsamt und Inklusionsbüro", markdown)
        self.assertIn("## Inklusion und Barrierefreiheit", markdown)
        self.assertIn("## Universitäts-Governance", markdown)
        self.assertIn("KI-Office/CIO-Board", markdown)
        self.assertIn("## Vorschlag für den Review-Termin", markdown)
        self.assertIn("Pruefungsamt", markdown)
        self.assertIn("## Datenschutz und Datenfluss", markdown)
        self.assertIn("## Was der Bot ausdrücklich nicht tut", markdown)
        self.assertIn("Vollständiger Aufgabencode", markdown)
        self.assertEqual(markdown.count("- **A3:**"), 1)
        self.assertIn("not_cleared", markdown)
        self.assertIn("RegulatoryProfileV1: ok", markdown)
        self.assertIn("Bachelorarbeitsfassung", markdown)
        self.assertNotIn("Masterarbeit", markdown)
        self.assertIn("Pruefungsamt", markdown)
        self.assertIn("Barrierefreiheit: browser_tested_human_review_required", markdown)
        self.assertIn("Nutzung der Darstellung wird nicht als Unterstützungsereignis gespeichert", markdown)
        self.assertEqual(scan_text(markdown, "institutional-presentation-markdown")['status'], "pass")

        from unibot.clearance import build_institutional_plain_language_brief

        brief = build_institutional_plain_language_brief(packet)
        self.assertIn("# UniBot: Kurzinfo", brief)
        self.assertIn("## Was macht der Bot nicht?", brief)
        self.assertIn("## Inklusion", brief)
        self.assertIn("not_cleared", brief)
        self.assertIn("Gretel / Codex", brief)
        self.assertIn("Nutzung wird weder im Sitzungsjournal noch im freiwilligen Export protokolliert", brief)
        self.assertEqual(scan_text(brief, "institutional-plain-language-brief")['status'], "pass")

        from unibot.clearance import build_accessibility_review_walkthrough

        walkthrough = build_accessibility_review_walkthrough(packet)
        self.assertIn("# UniBot: Accessibility-Walkthrough", walkthrough)
        self.assertIn("## Worum es geht", walkthrough)
        self.assertIn("Tastatur-Grundablauf", walkthrough)
        self.assertIn("Woran erkennen wir es?", walkthrough)
        self.assertIn("`not_tested`", walkthrough)
        self.assertIn("Keine Namen, Diagnosen", walkthrough)
        self.assertIn("die Nutzung der Darstellung", walkthrough)
        self.assertIn("200 percent", packet["evidence"]["browser_mantle"]["accessibility_evidence"]["automated_checks"][-1])
        self.assertEqual(scan_text(walkthrough, "institutional-accessibility-walkthrough")['status'], "pass")

    def test_institutional_review_bundle_is_hash_bound_and_public_safe(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            result = write_institutional_review_bundle(Path(temporary) / "review-bundle")
            bundle_root = Path(temporary) / "review-bundle"
            self.assertEqual(result["status"], "written")
            self.assertEqual(result["file_count"], 6)
            self.assertEqual(result["exam_deployment_status"], "not_cleared")
            self.assertRegex(result["source_commit"], r"^[0-9a-f]{40}$")
            self.assertEqual(result["source_provenance_status"], "verified")
            self.assertFalse(result["raw_learner_content_written"])
            self.assertTrue((bundle_root / "institutional-presentation.json").is_file())
            self.assertTrue((bundle_root / "institutional-presentation.md").is_file())
            self.assertTrue((bundle_root / "institutional-plain-language-brief.md").is_file())
            self.assertTrue((bundle_root / "institutional-accessibility-walkthrough.md").is_file())
            self.assertTrue((bundle_root / "institutional-review-decision-template.md").is_file())
            self.assertTrue((bundle_root / "MANIFEST.json").is_file())
            self.assertEqual((bundle_root / "MANIFEST.json").stat().st_mode & 0o077, 0)
            manifest = json.loads((bundle_root / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_commit"], result["source_commit"])
            self.assertEqual(manifest["source_provenance"]["status"], "verified")
            payload = "".join(path.read_text(encoding="utf-8") for path in bundle_root.iterdir())
            self.assertNotIn("/" + "Users/", payload)
            self.assertNotIn("raw notebook text:", payload.lower())
            self.assertEqual(scan_text(payload, "institutional-review-bundle-test")["status"], "pass")

    def test_institutional_review_bundle_blocks_dirty_source_before_writing(self) -> None:
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "review-bundle"
            with patch(
                "unibot.clearance.public_source_provenance",
                return_value={
                    "schema_version": "UniBotPublicSourceProvenanceV1",
                    "status": "blocked_dirty_worktree",
                    "commit": "a" * 40,
                    "working_tree_clean": False,
                },
            ):
                result = write_institutional_review_bundle(output)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["reason"], "blocked_dirty_worktree")
            self.assertFalse(output.exists())

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

        status, profile = route_request("/api/unibot/institutional/profile", {})
        self.assertEqual(status, 200)
        self.assertEqual(profile["schema_version"], REGULATORY_PROFILE_SCHEMA_VERSION)

        status, presentation = route_request("/api/unibot/institutional/presentation", {})
        self.assertEqual(status, 200)
        self.assertEqual(presentation["status"], "ready_for_human_review")

        status, markdown = route_request("/api/unibot/institutional/presentation-markdown", {})
        self.assertEqual(status, 200)
        self.assertEqual(markdown["status"], "ready_for_human_review")
        self.assertIn("UniBot Institutional Presentation", markdown["markdown"])

        status, decision_template = route_request("/api/unibot/institutional/decision-template", {})
        self.assertEqual(status, 200)
        self.assertEqual(decision_template["schema_version"], INSTITUTIONAL_REVIEW_DECISION_TEMPLATE_SCHEMA_VERSION)
        self.assertEqual(decision_template["status"], "blank_for_human_completion")


if __name__ == "__main__":
    unittest.main()
