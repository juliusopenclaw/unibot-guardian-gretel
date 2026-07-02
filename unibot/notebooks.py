from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .guardian import ALLOWED_MODES, EXAM_CONTROLLED, PRACTICE_OVERLAY, generate_socratic_prompt_card
from .source_cards import get_source_card


REQUIRED_NOTEBOOK_SECTIONS = [
    "Ziel",
    "Vorhersage",
    "Eigener Versuch",
    "Fehler",
    "Quellencheck",
    "Gemini/Colab Promptkarte",
    "UniBot Postfilter",
    "Reflexion",
    "Help-Ledger",
]


def markdown_cell(source: str, section: str) -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {
            "unibot_guardian": {
                "section": section,
                "public_safe": True,
            }
        },
        "source": source.splitlines(keepends=True),
    }


def code_cell(source: str, section: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {
            "unibot_guardian": {
                "section": section,
                "public_safe": True,
                "outputs_policy": "strip_outputs",
            }
        },
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def generate_practice_notebook(
    task: str,
    mode: str = PRACTICE_OVERLAY,
    source_card_ids: list[str] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    mode = mode if mode in ALLOWED_MODES else PRACTICE_OVERLAY
    source_card_ids = source_card_ids or ["google-colab-gemini", "uoc-ki-lehre", "vanlehn-2011"]
    prompt_card = generate_socratic_prompt_card(
        task=task,
        tool="colab_gemini",
        mode=mode,
        source_card_ids=source_card_ids,
    )
    resolved_source_cards = [card for source_id in source_card_ids if (card := get_source_card(source_id))]
    title = title or "UniBot Guardian Practice Notebook"
    exam_note = (
        "Dieser Modus ist ohne schriftliche Pruefungsfreigabe gesperrt. Nutze das Notebook nur als lokalen A0-A2-Reflexionsrahmen."
        if mode == EXAM_CONTROLLED
        else "Practice-Modus: Dieses Notebook ist fuer Uebung und privaten Selbsttest, nicht fuer offizielle Bewertung."
    )
    source_lines = "\n".join(
        f"- `{card['source_id']}`: {card['title']} ({card['product_rule']})" for card in resolved_source_cards
    )
    if not source_lines:
        source_lines = "- Keine Source Card aufgeloest. Pruefe die IDs vor Verwendung."

    cells = [
        markdown_cell(
            f"# {title}\n\n"
            f"{exam_note}\n\n"
            "Grenze: Keine finale Loesung, kein vollstaendiger Code-Fix, keine konkreten Werte einsetzen, "
            "keine privaten Daten und keine abgabefertige Interpretation uebernehmen.\n",
            "Intro",
        ),
        markdown_cell(
            "## Ziel\n\n"
            "Formuliere in einem Satz, welchen fachlichen oder Python-Schritt du gerade verstehen willst.\n\n"
            "- Ziel:\n",
            "Ziel",
        ),
        markdown_cell(
            "## Vorhersage\n\n"
            "Was erwartest du vor dem Ausfuehren: Ausgabe, Tabelle, Plot, Fehlermeldung oder Datentyp?\n\n"
            "- Erwartung:\n",
            "Vorhersage",
        ),
        code_cell(
            "# Eigener Versuch\n"
            "# Schreibe hier nur den kleinsten selbst begruendbaren Schritt.\n"
            "# Nutze Platzhalter, bis Werte oder Spalten aus der Aufgabe geprueft sind.\n",
            "Eigener Versuch",
        ),
        markdown_cell(
            "## Fehler\n\n"
            "Wenn etwas nicht klappt: Kopiere nicht die ganze Loesung. Notiere nur Fehlertyp, betroffene Variable/Zelle und deinen kleinsten Test.\n\n"
            "- Fehlertyp:\n"
            "- Betroffene Stelle:\n"
            "- Kleinster Test:\n",
            "Fehler",
        ),
        markdown_cell(
            "## Quellencheck\n\n"
            "Nutze nur gepruefte Kursquellen, offizielle Dokumentation oder diese Source Cards:\n\n"
            f"{source_lines}\n",
            "Quellencheck",
        ),
        markdown_cell(
            "## Gemini/Colab Promptkarte\n\n"
            "Kopiere nur diese Promptkarte in Gemini/Colab. Fuege keine privaten Daten ein.\n\n"
            "```text\n"
            f"{prompt_card['copyable_prompt']}\n"
            "```\n",
            "Gemini/Colab Promptkarte",
        ),
        markdown_cell(
            "## UniBot Postfilter\n\n"
            "Fuege externe KI-Antworten zuerst im UniBot Guardian ein. Uebernimm nur den gefilterten sokratischen Hinweis. "
            "Rohantworten bleiben ausserhalb des Notebooks und werden im Ledger nur als Hash dokumentiert.\n",
            "UniBot Postfilter",
        ),
        markdown_cell(
            "## Reflexion\n\n"
            "Was bleibt dein eigener naechster Schritt? Schreibe ohne Namen, IDs, Diagnosen, lokale Pfade oder andere private Daten.\n\n"
            "- Eigener naechster Schritt:\n"
            "- Genutzte Hilfestufe A0-A6:\n",
            "Reflexion",
        ),
        markdown_cell(
            "## Help-Ledger\n\n"
            "Speichere die Hilfen lokal ueber UniBot. Das Ledger dokumentiert Hilfestufe, Klassifikation, Hash und Reflexion, aber keine rohe externe KI-Antwort.\n",
            "Help-Ledger",
        ),
        code_cell(
            "help_ledger_hint = {\n"
            '    "policy": "local-only; raw external AI output is hash-only",\n'
            '    "store_with": "python3 -m unibot.server and /api/unibot/ledger/append",\n'
            '    "assessment": "private formative selftest only, no grade",\n'
            "}\n"
            "help_ledger_hint\n",
            "Help-Ledger",
        ),
    ]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            "unibot_guardian": {
                "artifact_type": "practice_notebook",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
                "source_card_ids": source_card_ids,
                "raw_output_policy": "do_not_store_raw_external_ai_output",
                "assessment_policy": "private formative selftest only, no grade",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    audit = audit_practice_notebook(notebook)
    return {
        "artifact_type": "unibot_practice_notebook",
        "title": title,
        "mode": mode,
        "notebook": notebook,
        "prompt_card": prompt_card,
        "source_cards": resolved_source_cards,
        "audit": audit,
    }


def audit_practice_notebook(notebook: dict[str, Any]) -> dict[str, Any]:
    cells = notebook.get("cells", [])
    text = "\n".join("".join(cell.get("source", [])) for cell in cells)
    sections_present = [section for section in REQUIRED_NOTEBOOK_SECTIONS if section in text]
    code_cells_with_outputs = [
        index for index, cell in enumerate(cells) if cell.get("cell_type") == "code" and cell.get("outputs")
    ]
    forbidden_markers = [
        marker
        for marker in ["solution_key", "RAW_EXTERNAL_AI_OUTPUT", "gemini_raw_response", "official_grade"]
        if marker in text
    ]
    status = "pass"
    if len(sections_present) != len(REQUIRED_NOTEBOOK_SECTIONS) or code_cells_with_outputs or forbidden_markers:
        status = "blocked"
    return {
        "status": status,
        "required_sections": REQUIRED_NOTEBOOK_SECTIONS,
        "sections_present": sections_present,
        "missing_sections": [section for section in REQUIRED_NOTEBOOK_SECTIONS if section not in sections_present],
        "code_cells_with_outputs": code_cells_with_outputs,
        "forbidden_markers": forbidden_markers,
        "cell_count": len(cells),
    }
