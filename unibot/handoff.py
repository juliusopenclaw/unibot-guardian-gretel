from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .compliance import build_compliance_matrix
from .ledger import export_public_ledger_summary
from .notebooks import generate_practice_notebook
from .redteam import run_redteam_smoke
from .source_cards import list_source_cards


HANDOFF_SCHEMA_VERSION = "unibot-authority-handoff-v1"


def build_authority_handoff_packet(ledger_path: str | None = None) -> dict[str, Any]:
    redteam = run_redteam_smoke()
    notebook_artifact = generate_practice_notebook(
        "Python-Neuro Practice: Listen, pandas, Boxplot und Debugging in Colab",
        source_card_ids=["hg-nrw-2025", "uoc-ki-lehre", "uoc-hilfsmittel", "uoc-nachteilsausgleich", "google-colab-gemini", "vanlehn-2011"],
        title="UniBot Guardian Practice Demo",
    )
    ledger_summary = export_public_ledger_summary(ledger_path)
    source_cards = list_source_cards()
    high_risk_cards = [card for card in source_cards if card["risk_level"] == "high"]
    compliance = build_compliance_matrix()

    return {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "draft_not_officially_cleared",
        "status_label_de": "Entwurf: nicht offiziell freigegeben / beantragt",
        "project": {
            "name": "UniBot Guardian",
            "one_sentence": (
                "Ein separater sokratischer Guardian-Mantel fuer Colab/Gemini, Jupyter und Coding-Hilfen, "
                "der externe KI-Antworten filtert, Hilfestufen dokumentiert und Eigenleistung schuetzt."
            ),
            "separation": "Separate UniBot track; not main Gretel/Badgyal pipeline.",
            "current_use": "practice and private selftest only",
        },
        "intended_reviewers": [
            "Pruefungsamt",
            "Inklusionsbuero / Nachteilsausgleich-Stelle",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
        ],
        "operating_modes": [
            {
                "mode": "practice_overlay",
                "status": "implemented_mvp",
                "rule": "Visible practice filter for external KI help; not exam security.",
            },
            {
                "mode": "selftest_guardian",
                "status": "implemented_mvp",
                "rule": "Private Independence Score only; no grade and no official assessment.",
            },
            {
                "mode": "exam_controlled",
                "status": "blocked_until_written_clearance",
                "rule": "Requires written exam-authority clearance and a controlled KI channel or managed environment.",
            },
        ],
        "non_goals": [
            "no proctoring",
            "no KI detection as evidence",
            "no automatic grading",
            "no decision on Nachteilsausgleich",
            "no processing of medical or accommodation personal data without a clear legal and privacy basis",
            "no public release of private course materials, emails, local paths, or raw external KI outputs",
        ],
        "data_flow": [
            "Student formulates task and own attempt locally.",
            "UniBot generates a Socratic Prompt Card.",
            "Student may ask an external tool in practice mode.",
            "External output is pasted into UniBot for filtering.",
            "UniBot returns only an allowed Socratic hint and a private formative score.",
            "Ledger stores hash, categories, help level, source card IDs, and redacted reflection only.",
            "Public summaries exclude raw external KI output and student reflections.",
        ],
        "data_categories": {
            "stored_by_default": ["hashes", "classification categories", "help levels", "skill tags", "source card IDs", "redacted reflections"],
            "not_stored_by_default": ["raw external KI output", "private course materials", "emails", "medical or accommodation personal data", "local paths", "official grades"],
            "local_storage_default": "~/.unibot_guardian/help_ledger.jsonl",
        },
        "review_questions": [
            "Welche Hilfsmittelregel gilt fuer einen freiwilligen Practice- oder Selftest-Einsatz?",
            "Welche Stelle muesste einen spaeteren exam_controlled-Modus schriftlich freigeben?",
            "Welche Daten duerfen fuer Help-Ledger und Evaluation gespeichert werden, und wie lange?",
            "Welche Accessibility-Hilfen sind punkteneutral zu dokumentieren?",
            "Welche Formulierungen muessen im UI stehen, damit keine Scheinfreigabe entsteht?",
            "Waere fuer eine Pilotstudie eine Ethik-/Datenschutzpruefung noetig?",
        ],
        "evidence": {
            "redteam": {
                "status": redteam["status"],
                "scenario_count": redteam["scenario_count"],
                "passed_count": redteam["passed_count"],
                "failed_count": redteam["failed_count"],
                "scenario_ids": [scenario["scenario_id"] for scenario in redteam["scenarios"]],
            },
            "notebook_audit": notebook_artifact["audit"],
            "ledger_public_summary": ledger_summary,
            "source_card_count": len(source_cards),
            "high_risk_source_card_ids": [card["source_id"] for card in high_risk_cards],
            "compliance_matrix": {
                "status": compliance["status"],
                "requirement_count": compliance["requirement_count"],
                "high_risk_requirement_count": compliance["high_risk_requirement_count"],
                "missing_source_card_ids": compliance["missing_source_card_ids"],
                "public_safety_status": compliance["public_safety_status"],
            },
        },
        "source_cards": [
            {
                "source_id": card["source_id"],
                "title": card["title"],
                "url": card["url"],
                "source_kind": card["source_kind"],
                "authority_type": card["authority_type"],
                "product_rule": card["product_rule"],
                "risk_level": card["risk_level"],
                "last_checked": card["last_checked"],
            }
            for card in source_cards
        ],
        "authority_packet_policy": "public-safe summary only; no raw external KI outputs, no private course material, no health data, no official decision language",
    }


def build_authority_handoff_markdown(ledger_path: str | None = None) -> str:
    packet = build_authority_handoff_packet(ledger_path)
    mode_lines = "\n".join(f"- `{mode['mode']}`: {mode['rule']}" for mode in packet["operating_modes"])
    non_goal_lines = "\n".join(f"- {item}" for item in packet["non_goals"])
    review_lines = "\n".join(f"- {item}" for item in packet["review_questions"])
    evidence = packet["evidence"]
    source_lines = "\n".join(
        f"- `{card['source_id']}` ({card['source_kind']}): {card['product_rule']}"
        for card in packet["source_cards"]
    )
    return (
        "# UniBot Guardian Handoff Packet\n\n"
        f"Status: {packet['status_label_de']}\n\n"
        f"Projekt: {packet['project']['one_sentence']}\n\n"
        "## Betriebsmodi\n\n"
        f"{mode_lines}\n\n"
        "## Nicht-Ziele\n\n"
        f"{non_goal_lines}\n\n"
        "## Datenfluss\n\n"
        + "\n".join(f"- {step}" for step in packet["data_flow"])
        + "\n\n"
        "## Offene Review-Fragen\n\n"
        f"{review_lines}\n\n"
        "## Evidenzstatus\n\n"
        f"- Red-Team: {evidence['redteam']['status']} ({evidence['redteam']['passed_count']}/{evidence['redteam']['scenario_count']})\n"
        f"- Notebook-Audit: {evidence['notebook_audit']['status']}\n"
        f"- Source Cards: {evidence['source_card_count']}\n"
        f"- Compliance Matrix: {evidence['compliance_matrix']['status']} ({evidence['compliance_matrix']['requirement_count']} requirements)\n"
        f"- Ledger Public Summary Events: {evidence['ledger_public_summary']['event_count']}\n\n"
        "## Source Cards\n\n"
        f"{source_lines}\n\n"
        "Policy: public-safe summary only; no raw external KI outputs, no private course material, no health data, no official decision language.\n"
    )
