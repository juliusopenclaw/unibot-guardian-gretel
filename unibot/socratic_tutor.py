from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass
from typing import Any, TypedDict, cast

from .guardian import classify_external_ai_output, detect_privacy_flags, detect_skill_tags
from .learning_session import HELP_COSTS_V1, HELP_LEVELS_V1, HelpEventV2, LearningSession


MAX_CELL_CHARACTERS = 12_000
MAX_TASK_CHARACTERS = 4_000
MAX_ATTEMPT_CHARACTERS = 4_000
TUTOR_RULE_PACK_SCHEMA_VERSION = "TutorRulePackV2"

SOURCE_ANCHORS = {
    "general_python": {
        "id": "python-tutorial-controlflow",
        "label": "Python Tutorial: More Control Flow Tools",
        "url": "https://docs.python.org/3/tutorial/controlflow.html",
    },
    "python_lists": {
        "id": "python-tutorial-datastructures",
        "label": "Python Tutorial: Data Structures",
        "url": "https://docs.python.org/3/tutorial/datastructures.html",
    },
    "loops": {
        "id": "python-tutorial-controlflow",
        "label": "Python Tutorial: More Control Flow Tools",
        "url": "https://docs.python.org/3/tutorial/controlflow.html",
    },
    "dictionaries": {
        "id": "python-tutorial-datastructures",
        "label": "Python Tutorial: Data Structures",
        "url": "https://docs.python.org/3/tutorial/datastructures.html",
    },
    "functions": {
        "id": "python-tutorial-functions",
        "label": "Python Tutorial: Defining Functions",
        "url": "https://docs.python.org/3/tutorial/controlflow.html#defining-functions",
    },
    "debugging": {
        "id": "python-tutorial-errors",
        "label": "Python Tutorial: Errors and Exceptions",
        "url": "https://docs.python.org/3/tutorial/errors.html",
    },
    "numpy": {
        "id": "numpy-absolute-beginners",
        "label": "NumPy: Absolute Beginner's Guide",
        "url": "https://numpy.org/doc/stable/user/absolute_beginners.html",
    },
    "pandas": {
        "id": "pandas-getting-started",
        "label": "pandas: Getting Started",
        "url": "https://pandas.pydata.org/docs/getting_started/index.html",
    },
    "boxplots": {
        "id": "matplotlib-boxplot",
        "label": "Matplotlib: boxplot",
        "url": "https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.boxplot.html",
    },
    "colab_jupyter": {
        "id": "jupyter-notebook-docs",
        "label": "Jupyter Notebook Documentation",
        "url": "https://jupyter-notebook.readthedocs.io/en/stable/",
    },
}

FORMULA_CARDS = {
    "mean": {
        "terms": ("mittelwert", "mean", "durchschnitt"),
        "id": "formula-arithmetic-mean-v1",
        "structure": "Mittelwert = Summe der beobachteten Werte / Anzahl der beobachteten Werte.",
        "scaffold": "Mittelwert = Summe(___, ..., ___) / ___.",
        "question": "Welche Werte gehoeren fachlich in die Summe, und ist ihre Anzahl wirklich der passende Nenner?",
    },
    "standard_deviation": {
        "terms": ("standardabweichung", "standard deviation", "std"),
        "id": "formula-standard-deviation-v1",
        "structure": "Standardabweichung: Abweichungen vom Mittelwert quadrieren, mitteln und daraus die Wurzel ziehen.",
        "scaffold": "Standardabweichung = Wurzel aus [Summe von (___ - ___)^2 / ___].",
        "question": "Berechnest du eine Stichprobe oder eine Grundgesamtheit, und welcher Nenner folgt daraus?",
    },
    "z_score": {
        "terms": ("z-score", "z score", "z-wert", "z wert"),
        "id": "formula-z-score-v1",
        "structure": "z-Wert = (Beobachtung - Mittelwert) / Standardabweichung.",
        "scaffold": "z-Wert = (___ - ___) / ___.",
        "question": "Welche Referenzverteilung liefert Mittelwert und Standardabweichung?",
    },
    "correlation": {
        "terms": ("korrelation", "correlation", "pearson"),
        "id": "formula-pearson-correlation-v1",
        "structure": "Pearson-Korrelation: gemeinsame standardisierte Abweichung beider Variablen relativ zu ihren Streuungen.",
        "scaffold": "Korrelation = gemeinsame Abweichung von ___ und ___ / Produkt ihrer ___.",
        "question": "Sind die Beobachtungspaare korrekt zugeordnet, und rechtfertigen Datenform und Ausreisser Pearson?",
    },
}

# The rule pack is deliberately deterministic. It selects a bounded learning
# move from syntax, AST features, traceback type, and reviewed source anchors.
TUTOR_RULES_V2 = {
    "python.syntax": {
        "source_anchor_ids": ("python-tutorial-controlflow",),
        "trigger": "syntax_error",
        "hint_kind": "diagnostic_location",
    },
    "python.debugging": {
        "source_anchor_ids": ("python-tutorial-errors",),
        "trigger": "traceback_type",
        "hint_kind": "diagnostic_error",
    },
    "python.control_flow": {
        "source_anchor_ids": ("python-tutorial-controlflow",),
        "trigger": "loops",
        "hint_kind": "control_flow_check",
    },
    "python.collections": {
        "source_anchor_ids": ("python-tutorial-datastructures",),
        "trigger": "collections",
        "hint_kind": "collection_check",
    },
    "python.functions": {
        "source_anchor_ids": ("python-tutorial-functions",),
        "trigger": "functions",
        "hint_kind": "function_contract_check",
    },
    "numpy.arrays": {
        "source_anchor_ids": ("numpy-absolute-beginners",),
        "trigger": "numpy",
        "hint_kind": "array_shape_check",
    },
    "pandas.dataframes": {
        "source_anchor_ids": ("pandas-getting-started",),
        "trigger": "pandas",
        "hint_kind": "dataframe_check",
    },
    "visualization.boxplots": {
        "source_anchor_ids": ("matplotlib-boxplot",),
        "trigger": "boxplots",
        "hint_kind": "visualization_check",
    },
    "statistics.formula": {
        "source_anchor_ids": (),
        "trigger": "formula_card",
        "hint_kind": "formula_structure",
    },
    "notebook.state": {
        "source_anchor_ids": ("jupyter-notebook-docs",),
        "trigger": "colab_jupyter",
        "hint_kind": "notebook_state_check",
    },
    "python.ast_basics": {
        "source_anchor_ids": ("python-tutorial-controlflow",),
        "trigger": "ast_features",
        "hint_kind": "ast_structure_check",
    },
}


class TutorTurnRequestV1(TypedDict, total=False):
    session_id: str
    task_id: str
    task: str
    learner_attempt: str
    student_reflection: str
    cell_context: str
    cell_type: str
    cell_index: int
    adapter: str
    requested_help_level: str
    help_level: str
    confirm_escalation: bool
    accessibility_used: bool


class TutorTurnV1(TypedDict):
    schema_version: str
    status: str
    task_id: str
    requested_help_level: str
    effective_help_level: str
    hint_kind: str
    hint_markdown: str
    source_anchors: list[dict[str, str]]
    source_anchor_ids: list[str]
    confidence: str
    assistance_points_delta: int
    assistance_points_for_task: int
    next_allowed_help_level: str
    blocked_reasons: list[str]
    attempt_hash: str
    cell_hash: str
    own_attempt_present: bool
    raw_cell_stored: bool
    raw_attempt_stored: bool
    local_realizer: str
    rule_pack_version: str
    rule_id: str
    knowledge_boundary: str
    exam_deployment_status: str
    help_event: HelpEventV2


@dataclass(frozen=True)
class CellAnalysis:
    syntax_status: str
    syntax_detail: str
    traceback_type: str
    skill_tags: list[str]
    formula_card: dict[str, Any] | None
    ast_features: tuple[str, ...]
    rule_id: str
    knowledge_boundary: str


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_level(value: Any, fallback: str = "A2") -> str:
    candidate = str(value or fallback).strip().upper()
    return candidate if candidate in HELP_COSTS_V1 else fallback


def _next_level(level: str, maximum: str) -> str:
    current_index = HELP_LEVELS_V1.index(level)
    maximum_index = HELP_LEVELS_V1.index(maximum)
    return HELP_LEVELS_V1[min(current_index + 1, maximum_index)]


def _ast_features(cell: str) -> tuple[str, ...]:
    if not cell.strip():
        return ()
    try:
        tree = ast.parse(cell)
    except SyntaxError:
        return ()
    features: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While, ast.If)):
            features.add("control_flow")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            features.add("function_definition")
        if isinstance(node, ast.Subscript):
            features.add("subscript")
        if isinstance(node, ast.Assign):
            features.add("assignment")
        if isinstance(node, ast.Import):
            names = {alias.name.split(".", 1)[0] for alias in node.names}
            if "numpy" in names:
                features.add("numpy_import")
            if "pandas" in names:
                features.add("pandas_import")
        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root == "numpy":
                features.add("numpy_import")
            if root == "pandas":
                features.add("pandas_import")
    return tuple(sorted(features))


def _rule_for_analysis(
    *,
    syntax_status: str,
    traceback_type: str,
    skill_tags: list[str],
    formula_card: dict[str, Any] | None,
    ast_features: tuple[str, ...],
) -> str:
    if traceback_type:
        return "python.debugging"
    if syntax_status == "syntax_error":
        return "python.syntax"
    if formula_card:
        return "statistics.formula"
    skill_rules = {
        "colab_jupyter": "notebook.state",
        "numpy": "numpy.arrays",
        "pandas": "pandas.dataframes",
        "boxplots": "visualization.boxplots",
        "loops": "python.control_flow",
        "dictionaries": "python.collections",
        "python_lists": "python.collections",
        "functions": "python.functions",
    }
    for skill in (
        "colab_jupyter",
        "numpy",
        "pandas",
        "boxplots",
        "loops",
        "functions",
        "dictionaries",
        "python_lists",
    ):
        if skill not in skill_tags:
            continue
        if skill in skill_rules:
            return skill_rules[skill]
    if ast_features:
        return "python.ast_basics"
    return ""


def analyze_cell(task: str, cell: str) -> CellAnalysis:
    syntax_status = "not_checked"
    syntax_detail = ""
    if cell.strip():
        if len(cell) > MAX_CELL_CHARACTERS:
            syntax_status = "too_large"
            syntax_detail = "Die Zelle ist fuer eine einzelne Hilfsanfrage zu gross."
        else:
            try:
                ast.parse(cell)
                syntax_status = "valid_python"
            except SyntaxError as exc:
                syntax_status = "syntax_error"
                syntax_detail = f"Syntaxfehler in Zeile {exc.lineno or '?'} bei Spalte {exc.offset or '?'}: {exc.msg}."
    combined = f"{task}\n{cell}"
    traceback_match = re.search(r"(?m)^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)):\s*(.+)$", combined)
    traceback_type = traceback_match.group(1) if traceback_match else ""
    formula = None
    lowered = combined.lower()
    for card in FORMULA_CARDS.values():
        if any(term in lowered for term in card["terms"]):
            formula = card
            break
    ast_features = _ast_features(cell) if syntax_status != "too_large" else ()
    detected_tags = [tag for tag in detect_skill_tags(combined) if tag != "general_python"]
    skill_tags = detected_tags or (["general_python"] if ast_features else [])
    rule_id = _rule_for_analysis(
        syntax_status=syntax_status,
        traceback_type=traceback_type,
        skill_tags=skill_tags,
        formula_card=formula,
        ast_features=ast_features,
    )
    return CellAnalysis(
        syntax_status=syntax_status,
        syntax_detail=syntax_detail,
        traceback_type=traceback_type,
        skill_tags=skill_tags,
        formula_card=formula,
        ast_features=ast_features,
        rule_id=rule_id,
        knowledge_boundary="source_bound" if rule_id else "no_reliable_source",
    )


def _source_anchors(analysis: CellAnalysis) -> list[dict[str, str]]:
    anchors: list[dict[str, str]] = []
    rule = TUTOR_RULES_V2.get(analysis.rule_id)
    source_ids = rule.get("source_anchor_ids", ()) if rule else ()
    for source_id in source_ids:
        for candidate in SOURCE_ANCHORS.values():
            if candidate["id"] == source_id and candidate not in anchors:
                anchors.append(dict(candidate))
    for skill in analysis.skill_tags:
        anchor = SOURCE_ANCHORS.get(skill)
        if anchor and anchor not in anchors:
            anchors.append(dict(anchor))
    if not anchors and analysis.knowledge_boundary == "source_bound":
        anchors.append(dict(SOURCE_ANCHORS["general_python"]))
    if analysis.formula_card:
        anchors.append(
            {
                "id": str(analysis.formula_card["id"]),
                "label": "Versionierte lokale Formelkarte",
                "url": "",
            }
        )
    return anchors[:4]


def _hint_for_level(level: str, analysis: CellAnalysis, task: str) -> tuple[str, str]:
    primary_skill = analysis.skill_tags[0] if analysis.skill_tags else "general_python"
    if level == "A0":
        return "orientation_question", "Formuliere in einem Satz: Welche Eingabe hast du, und welche Ausgabe erwartest du als naechstes?"
    if level == "A1":
        if analysis.syntax_detail:
            return "diagnostic_location", f"{analysis.syntax_detail} Welche kleinste Stelle unmittelbar davor kannst du selbst pruefen?"
        if analysis.traceback_type:
            return "diagnostic_error", f"Der sichtbare Fehlertyp ist {analysis.traceback_type}. Welche Variable in der letzten eigenen Codezeile hat nicht den erwarteten Zustand?"
        return "diagnostic_question", "Trenne die Aufgabe in Eingabe, Verarbeitung und Ausgabe. In welchem dieser drei Teile entsteht die erste Unsicherheit?"
    if level == "A2":
        concept = {
            "python_lists": "Pruefe Laenge, Indexgrenzen und den Unterschied zwischen append und extend.",
            "loops": "Pruefe Startmenge, Schleifenvariable und Abbruch- oder Iterationsbedingung getrennt.",
            "dictionaries": "Pruefe zuerst vorhandene Schluessel und den erwarteten Werttyp.",
            "functions": "Benenne Parameter, Rueckgabewert und Seiteneffekt getrennt.",
            "numpy": "Pruefe zuerst Datentyp und Shape des Arrays.",
            "pandas": "Pruefe zuerst Spaltennamen, dtypes und fehlende Werte.",
            "boxplots": "Benenne Messwert, Gruppierung, Einheit und die Grenze der deskriptiven Aussage.",
            "debugging": "Lies den Traceback von unten nach oben und isoliere die zuerst eigene fehlerhafte Zeile.",
            "colab_jupyter": "Pruefe, welche Zelle den benoetigten Zustand erzeugt und ob sie bereits ausgefuehrt wurde.",
        }.get(primary_skill, "Pruefe Datentyp, Form und erwartetes Zwischenergebnis vor dem naechsten Schritt.")
        return "concept_and_source", f"Konzept-Hinweis: {concept} Welcher kleine Test wuerde diese Annahme bestaetigen oder widerlegen?"
    if level == "A3":
        if analysis.formula_card:
            return "formula_structure", f"Formelstruktur: {analysis.formula_card['structure']} {analysis.formula_card['question']}"
        return "pseudocode_structure", "Pseudocode: 1. Eingabe pruefen. 2. Eine einzelne Transformation anwenden. 3. Form oder Typ des Zwischenergebnisses pruefen. Welche konkrete Pruefung setzt du in Schritt 1 ein?"
    if analysis.formula_card:
        return "incomplete_formula_scaffold", f"Teilgeruest: {analysis.formula_card['scaffold']} Ordne zuerst Bedeutung und Einheit jeder Luecke zu. {analysis.formula_card['question']}"
    return (
        "incomplete_code_scaffold",
        "Teilgeruest mit absichtlichen Luecken: Daten = ___; gepruefte_Daten = ___; Ergebnis = ___(gepruefte_Daten). Fuell zuerst nur die Pruefung aus und begruende ihren erwarteten Typ.",
    )


def _effective_level(
    session: LearningSession,
    task_id: str,
    requested: str,
    attempt_hash: str,
    confirmed: bool,
) -> tuple[str, list[str]]:
    contract = session.contract
    maximum = contract["max_help_level"]
    if HELP_COSTS_V1[requested] > HELP_COSTS_V1[maximum]:
        return maximum, ["requested_level_exceeds_session_contract"]
    if contract["assistance_mode"] == "fixed":
        return contract["fixed_help_level"], []
    current = session.current_level(task_id)
    maximum_next = _next_level(current, maximum)
    if HELP_COSTS_V1[requested] > HELP_COSTS_V1[maximum_next]:
        return maximum_next, ["adaptive_mode_allows_one_level_per_turn"]
    if HELP_COSTS_V1[requested] > HELP_COSTS_V1[current]:
        if not confirmed:
            return current, ["escalation_confirmation_required"]
        previous_attempt = session.last_attempt_hash(task_id)
        if previous_attempt and previous_attempt == attempt_hash:
            return current, ["new_own_attempt_required_before_escalation"]
    return requested, []


def build_tutor_turn(session: LearningSession, payload: TutorTurnRequestV1) -> TutorTurnV1:
    task = str(payload.get("task", "")).strip()[:MAX_TASK_CHARACTERS]
    attempt = str(payload.get("learner_attempt", payload.get("student_reflection", ""))).strip()[:MAX_ATTEMPT_CHARACTERS]
    cell = str(payload.get("cell_context", "")).strip()[:MAX_CELL_CHARACTERS]
    task_id = str(payload.get("task_id", "")).strip() or _hash_text(task)[:16]
    requested = _normalize_level(payload.get("requested_help_level", payload.get("help_level", "A2")))
    attempt_hash = _hash_text(attempt) if attempt else ""
    cell_hash = _hash_text(cell) if cell else ""
    blocked_reasons: list[str] = []
    if not task:
        blocked_reasons.append("learning_goal_required")
    if not attempt:
        blocked_reasons.append("own_attempt_required")
    privacy_flags = detect_privacy_flags("\n".join((task, attempt, cell)))
    if privacy_flags:
        blocked_reasons.extend(f"privacy:{flag}" for flag in privacy_flags)
    analysis = analyze_cell(task, cell)
    effective, level_reasons = _effective_level(
        session,
        task_id,
        requested,
        attempt_hash,
        bool(payload.get("confirm_escalation", False)),
    )
    blocked_reasons.extend(level_reasons)
    anchors = _source_anchors(analysis)
    previous_cost = HELP_COSTS_V1[session.current_level(task_id)] if session.task_events(task_id) else 0
    effective_cost = HELP_COSTS_V1[effective]
    delta = max(0, effective_cost - previous_cost)
    if any(reason.startswith("privacy:") for reason in blocked_reasons) or not task or not attempt:
        hint_kind = "blocked"
        hint = "Entferne private Angaben und beschreibe Lernziel sowie eigenen Versuch abstrakt, bevor UniBot Hilfe erzeugt."
        status = "blocked"
        effective = session.current_level(task_id)
        effective_cost = previous_cost
        delta = 0
    elif not anchors:
        effective = session.current_level(task_id)
        effective_cost = previous_cost
        delta = 0
        hint_kind = "no_reliable_source"
        hint = (
            "Ich finde fuer diese Frage keinen belastbaren Regel- oder Quellenanker. "
            "Beschreibe den naechsten eigenen Pruefschritt, ohne eine fachliche Aussage als belegt auszugeben."
        )
        blocked_reasons.append("no_reliable_source")
        status = "no_reliable_source"
    else:
        hint_kind, hint = _hint_for_level(effective, analysis, task)
        status = "allowed" if not level_reasons else "bounded"
        review = classify_external_ai_output(hint, requested_help_level=effective, mode="practice_overlay")
        unsafe_categories = [
            category
            for category in review["categories"]
            if category
            in {
                "final_solution",
                "code_fix_or_complete_code",
                "values_inserted",
                "final_interpretation",
                "source_or_citation_risk",
                "prompt_injection_or_policy_evasion",
            }
        ]
        if unsafe_categories:
            effective = "A1"
            effective_cost = HELP_COSTS_V1[effective]
            delta = max(0, effective_cost - previous_cost)
            hint_kind = "downgraded_diagnostic_question"
            hint = "Die vorbereitete Hilfe war zu loesungsnah. Welche Eingabe, Annahme oder Fehlermeldung kannst du als naechstes selbst pruefen?"
            blocked_reasons.extend(f"output_filter:{category}" for category in unsafe_categories)
            status = "downgraded"
    next_allowed = _next_level(effective, session.contract["max_help_level"])
    turn_without_event: dict[str, Any] = {
        "schema_version": "unibot-tutor-turn-v1",
        "status": status,
        "task_id": task_id,
        "requested_help_level": requested,
        "effective_help_level": effective,
        "hint_kind": hint_kind,
        "hint_markdown": hint,
        "source_anchors": anchors,
        "source_anchor_ids": [anchor["id"] for anchor in anchors],
        "confidence": "high" if analysis.syntax_status in {"valid_python", "syntax_error"} else "bounded",
        "assistance_points_delta": delta,
        "assistance_points_for_task": effective_cost,
        "next_allowed_help_level": next_allowed,
        "blocked_reasons": blocked_reasons,
        "attempt_hash": attempt_hash,
        "cell_hash": cell_hash,
        "own_attempt_present": bool(attempt),
        "raw_cell_stored": False,
        "raw_attempt_stored": False,
        "local_realizer": "deterministic_source_grounded_v1",
        "rule_pack_version": TUTOR_RULE_PACK_SCHEMA_VERSION,
        "rule_id": analysis.rule_id,
        "knowledge_boundary": analysis.knowledge_boundary,
        "exam_deployment_status": "not_cleared",
    }
    event = session.record_turn(turn_without_event)
    return cast(TutorTurnV1, {**turn_without_event, "help_event": event})
