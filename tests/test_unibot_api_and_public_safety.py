from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unibot.public_safety import scan_public_files, scan_text  # noqa: E402
from unibot.server import create_server, route_request  # noqa: E402
from unibot.source_cards import (  # noqa: E402
    build_source_card_drift_report,
    get_source_card,
    list_source_cards,
    required_source_card_ids,
)


class UniBotApiAndPublicSafetyTests(unittest.TestCase):
    def test_local_api_health_and_prompt_card(self) -> None:
        status, health = route_request("/api/unibot/health", method="GET")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["raw_output_policy"], "hash-only by default")

        status, card = route_request(
            "/api/unibot/prompt-card",
            {"task": "Python Listen und Boxplots in Colab", "source_card_ids": ["google-colab-gemini"]},
        )
        self.assertEqual(status, 200)
        self.assertIn("keine finale Loesung", card["copyable_prompt"])
        self.assertIn("python_lists", card["skill_tags"])
        self.assertIn("boxplots", card["skill_tags"])

    def test_local_api_review_and_practice_flow_do_not_return_raw_output(self) -> None:
        raw_output = "Hier ist der komplette Code: import pandas as pd\nwerte = [1, 2, 3]\nplt.boxplot(werte)"
        status, review = route_request(
            "/api/unibot/review-output",
            {"external_output": raw_output, "requested_help_level": "A4"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(review["status"], "blocked")
        self.assertIn("final_solution", review["categories"])
        self.assertNotIn(raw_output, json.dumps(review, ensure_ascii=False))

        status, flow = route_request(
            "/api/unibot/practice-flow",
            {
                "task": "Boxplot Debugging in Colab",
                "external_output": "Welche Spalte ist dein Messwert?",
                "requested_help_level": "A2",
                "student_reflection": "Ich pruefe df.dtypes.",
            },
        )
        self.assertEqual(status, 200)
        self.assertFalse(flow["raw_output_stored"])
        self.assertEqual(flow["postfilter"]["status"], "allowed")
        self.assertNotIn("Welche Spalte ist dein Messwert?", json.dumps(flow["guardian_event"], ensure_ascii=False))

    def test_public_safety_scan_blocks_obvious_leaks(self) -> None:
        risky = "\n".join(
            [
                f"Contact: {'student'}@example.invalid",
                "api" + "_key = sk-test",
                "RAW_EXTERNAL" + "_AI_OUTPUT: here is the complete answer",
                "knowledge/private_course" + "_materials/course.pdf",
                "knowledge/exam" + "_workspace/private-run",
                "Ver-" + "Sacrum private marker",
                "/" + "Users/student/private/notebook.ipynb",
                "/" + "home/student/private/notebook.ipynb",
                "/" + "private/va" + "r/folders/zz/private-notebook.ipynb",
                "/" + "va" + "r/folders/zz/private-notebook.ipynb",
                "C:" + "\\Users\\student\\private\\notebook.ipynb",
                "Dia" + "gnose: private detail",
            ]
        )
        scan = scan_text(risky, "fixture")
        finding_types = {finding["type"] for finding in scan["findings"]}

        self.assertEqual(scan["status"], "blocked")
        self.assertIn("email_address", finding_types)
        self.assertIn("secret_assignment", finding_types)
        self.assertIn("raw_external_ai_transcript", finding_types)
        self.assertIn("private_course_material_reference", finding_types)
        self.assertIn("private_project_marker", finding_types)
        self.assertIn("local_path", finding_types)
        self.assertIn("personal_health_or_accommodation_record", finding_types)

    def test_public_safety_scan_passes_unibot_public_files(self) -> None:
        files = [
            *sorted((ROOT / "docs" / "unibot").glob("*.md")),
            *sorted((ROOT / "unibot").glob("*.py")),
            *sorted(path for path in (ROOT / "unibot" / "browser_extension").glob("**/*") if path.is_file()),
        ]
        scan = scan_public_files(files)
        self.assertEqual(scan["status"], "pass", scan["findings"])
        self.assertGreaterEqual(scan["scanned_count"], 8)

    def test_unknown_api_path_returns_404(self) -> None:
        status, response = route_request("/api/unibot/nope", {})
        self.assertEqual(status, 404)
        self.assertEqual(response["status"], "not-found")

    def test_source_cards_are_machine_readable(self) -> None:
        cards = list_source_cards()
        ids = {card["source_id"] for card in cards}

        for required_id in required_source_card_ids():
            self.assertIn(required_id, ids)
        self.assertEqual(get_source_card("eu-ai-act-2024")["risk_level"], "high")
        self.assertEqual(get_source_card("hg-nrw-64")["authority_type"], "state-law")
        self.assertEqual(get_source_card("chrome-limited-use")["source_kind"], "technical-doc")
        self.assertEqual(get_source_card("oecd-digital-education-2026")["authority_type"], "international-organisation")
        self.assertIn("zai-glm-52", ids)
        self.assertIn("zai-glm-pricing", required_source_card_ids())
        self.assertTrue(all(card["url"].startswith("https://") for card in cards))

        status, response = route_request("/api/unibot/source-cards", {"source_kind": "paper"})
        self.assertEqual(status, 200)
        self.assertGreaterEqual(response["count"], 3)
        self.assertTrue(all(card["source_kind"] == "paper" for card in response["source_cards"]))

        status, response = route_request("/api/unibot/source-card", {"source_id": "hg-nrw-2025"})
        self.assertEqual(status, 200)
        self.assertEqual(response["source_card"]["authority_type"], "state-law")

    def test_source_card_drift_report_keeps_scientific_sources_current(self) -> None:
        report = build_source_card_drift_report(as_of="2026-07-02")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["public_safety_status"], "pass")
        self.assertGreaterEqual(report["card_count"], 25)
        self.assertEqual(report["missing_required_source_card_ids"], [])
        self.assertEqual(report["unlisted_high_risk_source_card_ids"], [])
        self.assertEqual(report["duplicate_source_ids"], [])
        self.assertEqual(report["invalid_https_source_ids"], [])
        self.assertEqual(report["stale_source_card_ids"], [])

        stale_report = build_source_card_drift_report(as_of="2027-01-01", max_age_days=120)
        self.assertEqual(stale_report["status"], "blocked")
        self.assertTrue(stale_report["stale_source_card_ids"])

        status, response = route_request("/api/unibot/source-card-drift-report", {})
        self.assertEqual(status, 200)
        self.assertIn(response["status"], {"pass", "blocked"})
        self.assertEqual(response["public_safety_status"], "pass")

    def test_http_handler_roundtrip(self) -> None:
        server = create_server("127.0.0.1", 0, session_token="synthetic-session-token")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            url = f"http://{host}:{port}/api/unibot/review-output"
            body = json.dumps(
                {
                    "external_output": "Hier ist der komplette Code: import pandas as pd",
                    "requested_help_level": "A4",
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                url,
                data=body,
                headers={
                    "content-type": "application/json",
                    "x-unibot-token": "synthetic-session-token",
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual(payload["status"], "blocked")
            self.assertIn("final_solution", payload["categories"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
