from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .adaptive_tasks import generate_adaptive_practice_plan
from .guardian import classify_external_ai_output, generate_socratic_prompt_card, guardian_practice_flow
from .notebooks import generate_practice_notebook
from .public_safety import scan_text
from .redteam import run_redteam_smoke


DEMO_RUN_SCHEMA_VERSION = "unibot-demo-run-v1"


def build_local_demo_run() -> dict[str, Any]:
    prompt_card = generate_socratic_prompt_card(
        "Python Listen in Colab ueben: append, Index und kleiner Boxplot-Kontext",
        source_card_ids=["google-colab-gemini", "vanlehn-2011"],
    )
    blocked_review = classify_external_ai_output(
        "Hier ist der komplette Code: import pandas as pd\nwerte = [1, 2, 3, 4]\nplt.boxplot(werte)",
        requested_help_level="A5",
    )
    allowed_flow = guardian_practice_flow(
        task="Python Listen debuggen: Warum ist mein Index falsch?",
        external_output="Welche Laenge hat deine Liste direkt vor dem Zugriff?",
        requested_help_level="A2",
        source_card_ids=["vanlehn-2011"],
        student_reflection="Ich pruefe zuerst len(meine_liste).",
    )
    adaptive_plan = generate_adaptive_practice_plan(
        skill_state={"python_lists": {"signals": 4, "high_help_events": 1}},
        max_tasks=2,
        public_safe=True,
    )
    notebook = generate_practice_notebook(
        "Python Listen und Colab/Gemini Practice",
        source_card_ids=["google-colab-gemini", "uoc-ki-lehre", "vanlehn-2011"],
    )
    redteam = run_redteam_smoke()

    scenarios = [
        {
            "scenario_id": "demo_setup",
            "title": "Local API and browser mantle",
            "user_action": "Start `python3 -m unibot.server`, load the unpacked browser extension, and open Colab or a local Jupyter page.",
            "expected_result": "Health endpoint returns ok; the page shows the practice overlay banner; side panel opens.",
            "success_evidence": ["health_status_ok", "visible_practice_banner", "sidepanel_available"],
        },
        {
            "scenario_id": "demo_prompt_card",
            "title": "Socratic Prompt Card",
            "user_action": "Enter a Python-list task and click Promptkarte erzeugen.",
            "expected_result": "A prompt is copied that asks for questions and blocks final solutions.",
            "success_evidence": prompt_card["skill_tags"],
        },
        {
            "scenario_id": "demo_block_solution",
            "title": "Postfilter blocks solution-like AI output",
            "user_action": "Paste a complete code answer into Externe KI-Antwort and click Antwort pruefen.",
            "expected_result": "Status is blocked and the shown hint asks for the learner's next own step.",
            "success_evidence": blocked_review["categories"],
        },
        {
            "scenario_id": "demo_allowed_flow_and_ledger",
            "title": "Allowed Socratic hint and local ledger",
            "user_action": "Paste a low-level question, add a reflection, and click Flow pruefen und Ledger speichern.",
            "expected_result": "Status is allowed; score remains private/formative; raw external output is not stored.",
            "success_evidence": [
                allowed_flow["postfilter"]["status"],
                allowed_flow["formative_score"]["status"],
                f"raw_output_stored={allowed_flow['raw_output_stored']}",
            ],
        },
        {
            "scenario_id": "demo_adaptive_tasks",
            "title": "Adaptive follow-up tasks",
            "user_action": "Click Uebungsaufgaben erzeugen after using A4-A5 help on a list problem.",
            "expected_result": "A practice-only plan recommends targeted Python-list tasks with Socratic checks.",
            "success_evidence": [task["skill_tag"] for task in adaptive_plan["tasks"]],
        },
        {
            "scenario_id": "demo_notebook_template",
            "title": "Notebook handoff",
            "user_action": "Click Notebook-Vorlage kopieren and save the JSON as an `.ipynb` file.",
            "expected_result": "Notebook audit passes and required reflection cells are present.",
            "success_evidence": [
                notebook["audit"]["status"],
                f"cell_count={notebook['audit']['cell_count']}",
            ],
        },
        {
            "scenario_id": "demo_redteam_smoke",
            "title": "Safety smoke before sharing",
            "user_action": "Run the red-team endpoint or readiness check before a public demo.",
            "expected_result": "Red-team status is pass; exam use remains not cleared.",
            "success_evidence": [redteam["status"], f"scenarios={redteam['scenario_count']}"],
        },
    ]

    bug_report_template = {
        "what_i_tried": "",
        "expected": "",
        "what_happened": "",
        "which_button_or_endpoint": "",
        "screenshot_or_copied_public_safe_text": "",
        "private_data_removed": True,
    }
    report = {
        "schema_version": DEMO_RUN_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "practice_demo_ready_not_exam",
        "mode": "practice_overlay",
        "not_ready_for": ["exam deployment", "official grading", "proctoring", "KI-detection use"],
        "setup": {
            "local_api": "python3 -m unibot.server",
            "browser_extension": "load unpacked folder unibot/browser_extension",
            "recommended_first_page": "Colab or local Jupyter practice notebook with synthetic data",
            "feedback_endpoint": "POST /api/unibot/demo-feedback/validate before sharing; append only after public-safe validation",
        },
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "bug_report_template": bug_report_template,
        "public_safety_policy": "Do not paste private data, real exam work, emails, health/accommodation details, local paths, or raw private course text into public reports.",
    }
    scan = scan_text(json.dumps(report, ensure_ascii=False), "unibot-demo-run")
    report["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        report["status"] = "blocked"
        report["public_safety_findings"] = scan["findings"]
    return report


def build_local_demo_markdown() -> str:
    report = build_local_demo_run()
    scenario_lines = []
    for scenario in report["scenarios"]:
        scenario_lines.extend(
            [
                f"## {scenario['title']}",
                "",
                f"Action: {scenario['user_action']}",
                "",
                f"Expected: {scenario['expected_result']}",
                "",
            ]
        )
    return (
        "# UniBot Local Demo Test Plan\n\n"
        f"Status: {report['status']}\n\n"
        "Boundary: practice demo only, not exam clearance or official grading.\n\n"
        "## Setup\n\n"
        f"- Local API: `{report['setup']['local_api']}`\n"
        f"- Browser extension: {report['setup']['browser_extension']}\n"
        f"- First page: {report['setup']['recommended_first_page']}\n\n"
        f"- Feedback: {report['setup']['feedback_endpoint']}\n\n"
        + "\n".join(scenario_lines)
        + "## Bug Report Template\n\n"
        "- What I tried:\n"
        "- Expected:\n"
        "- What happened:\n"
        "- Button or endpoint:\n"
        "- Public-safe screenshot/text:\n"
        "- Private data removed: yes\n"
    )
