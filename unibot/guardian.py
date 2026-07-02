from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


PRACTICE_OVERLAY = "practice_overlay"
SELFTEST_GUARDIAN = "selftest_guardian"
EXAM_CONTROLLED = "exam_controlled"

ALLOWED_MODES = {PRACTICE_OVERLAY, SELFTEST_GUARDIAN, EXAM_CONTROLLED}
FILE_SCHEME_PATTERN = re.escape("file:" + "//")

HELP_LEVEL_DEDUCTIONS = {
    "A0": 0,
    "A1": 0,
    "A2": 5,
    "A3": 12,
    "A4": 25,
    "A5": 40,
    "A6": 100,
}

SKILL_PATTERNS = {
    "python_lists": r"\b(list|listen|append|index|slice|slicing|liste)\b",
    "loops": r"\b(loop|loops|for\s+|while\s+|iteration|schleife)\b",
    "dictionaries": r"\b(dict|dictionary|woerterbuch|keyerror|keys?|values?)\b",
    "functions": r"\b(function|def\s+|return|parameter|argument|funktion)\b",
    "numpy": r"\b(numpy|np\.|array|ndarray)\b",
    "pandas": r"\b(pandas|dataframe|series|df\.|read_csv|csv)\b",
    "boxplots": r"\b(boxplots?|box\s*plots?|median|quartile|iqr|ausreisser)\b",
    "debugging": r"\b(error|traceback|nameerror|typeerror|indexerror|keyerror|debug|fehlermeldung)\b",
    "colab_jupyter": r"\b(colab|jupyter|notebook|runtime|cell|zelle)\b",
}

PRIVACY_CHECKS = [
    ("email", r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}"),
    ("phone", r"(?:\+?\d[\d\s()./-]{7,}\d)"),
    ("matriculation", r"\b(?:matrikel|matrikelnummer|student id|student-id)\b"),
    (
        "health_or_inclusion_data",
        r"\b(?:diagnose|attest|adhs|autismus|depression|angststoerung|angststörung|ptbs|medikation|arztbrief|krankheit|behinderung|nachteilsausgleich)\b",
    ),
    ("local_path", rf"(?:/(?:Users|users)/|C:\\\\(?:Users|users)\\\\|{FILE_SCHEME_PATTERN})"),
    ("secret", r"\b(?:api[_-]?key|token|password|passwd|secret)\b\s*[:=]"),
]

FINAL_SOLUTION_PATTERNS = [
    r"\b(?:fertige|komplette|kompletter|kompletten|vollstaendige|vollständige)\s+(?:loesung|lösung|antwort|code)\b",
    r"\b(?:here is|hier ist)\s+(?:the\s+)?(?:complete|full|final|fertige)\s+(?:code|solution|loesung|lösung)\b",
    r"\b(?:copy|kopiere)\s+(?:this|diesen)\s+(?:code|loesung|lösung)\b",
    r"\b(?:abgabefertig|klausurantwort|final answer|endgueltige antwort|endgültige antwort)\b",
]

CODE_FIX_PATTERNS = [
    r"```(?:python|py)?\s*[\s\S]{30,}```",
    r"\b(?:replace|ersetze)\s+(?:it|das|deinen code)\s+(?:with|durch)\b",
    r"\b(?:use|nutze|verwende)\s+(?:this|diesen)\s+code\b",
    r"\bimport\s+(?:pandas|numpy|matplotlib|seaborn)\b[\s\S]{0,400}\b(?:plt\.|df\.|np\.|sns\.|print\()",
    r"\bdef\s+\w+\([^)]*\):[\s\S]{0,400}\breturn\b",
]

VALUE_INSERTION_PATTERNS = [
    r"\b\w+\s*=\s*\[[0-9.,\s-]{5,}\]",
    r"\b(?:median|mittelwert|mean|iqr|standardabweichung)\s+(?:is|ist|=)\s*[-+]?\d",
    r"\b(?:setze|insert|verwende)\s+(?:die\s+)?(?:werte|values)\b",
]

FINAL_INTERPRETATION_PATTERNS = [
    r"\b(?:therefore|therefor|also|somit|daher)\s+(?:zeigt|means|bedeutet|ist die interpretation)\b",
    r"\b(?:finale|abschliessende|abschließende)\s+interpretation\b",
    r"\b(?:du kannst schreiben|write this in your report|schreibe in die abgabe)\b",
]

SOURCE_RISK_PATTERNS = [
    r"\b(?:fake|erfinde|invent)\s+(?:quelle|source|citation|literatur)\b",
    r"\b(?:quelle unbekannt|no source|ohne quelle|citation needed)\b",
    r"\b(?:laut studie|according to a study)\b(?![\s\S]{0,160}(?:doi|https?://|isbn|pmid))",
]

PROMPT_INJECTION_PATTERNS = [
    r"\b(?:ignore|ignoriere|vergiss)\s+(?:alle\s+)?(?:previous|vorherigen|bisherigen)\s+(?:instructions|anweisungen|regeln)\b",
    r"\b(?:system prompt|developer message|hidden instructions|versteckte anweisungen)\b",
    r"\b(?:bypass|umgehe|override|jailbreak)\s+(?:the\s+)?(?:guard|filter|policy|regeln|schutz)\b",
    r"\b(?:do not tell|sag nicht|verschweige)\s+(?:the\s+)?(?:teacher|pruefer|prüfer|aufsicht)\b",
]


@dataclass(frozen=True)
class GuardianEvent:
    mode: str
    tool: str
    task_id: str
    skill_tags: list[str]
    raw_output_hash: str
    classification: list[str]
    allowed_hint: str
    help_level: str
    privacy_flags: list[str] = field(default_factory=list)
    source_card_ids: list[str] = field(default_factory=list)
    student_reflection: str = ""
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_public_dict(self) -> dict[str, Any]:
        """Return a ledger-safe representation without raw external AI output."""
        return asdict(self)


def stable_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def normalize_help_level(help_level: str | None) -> str:
    candidate = str(help_level or "A2").upper().strip()
    return candidate if candidate in HELP_LEVEL_DEDUCTIONS else "A2"


def detect_skill_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags = [tag for tag, pattern in SKILL_PATTERNS.items() if re.search(pattern, lowered, re.IGNORECASE)]
    return tags or ["general_python"]


def detect_privacy_flags(text: str) -> list[str]:
    lowered = text.lower()
    flags = [label for label, pattern in PRIVACY_CHECKS if re.search(pattern, lowered, re.IGNORECASE)]
    return sorted(set(flags))


def _matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def classify_external_ai_output(
    external_output: str,
    requested_help_level: str | None = "A2",
    mode: str = PRACTICE_OVERLAY,
    approval_reference: str | None = None,
) -> dict[str, Any]:
    """Classify external AI help before it reaches the learner.

    The function intentionally returns a filtered hint and a raw-output hash,
    never a raw-output transcript.
    """
    mode = mode if mode in ALLOWED_MODES else PRACTICE_OVERLAY
    help_level = normalize_help_level(requested_help_level)
    text = external_output or ""
    privacy_flags = detect_privacy_flags(text)
    categories: list[str] = []

    if mode == EXAM_CONTROLLED and not approval_reference:
        categories.append("exam_controlled_requires_written_approval")
    if privacy_flags:
        categories.append("private_or_sensitive_data")
    if _matches_any(FINAL_SOLUTION_PATTERNS, text):
        categories.append("final_solution")
    if _matches_any(CODE_FIX_PATTERNS, text):
        categories.append("code_fix_or_complete_code")
    if _matches_any(VALUE_INSERTION_PATTERNS, text):
        categories.append("values_inserted")
    if _matches_any(FINAL_INTERPRETATION_PATTERNS, text):
        categories.append("final_interpretation")
    if _matches_any(SOURCE_RISK_PATTERNS, text):
        categories.append("source_or_citation_risk")
    if _matches_any(PROMPT_INJECTION_PATTERNS, text):
        categories.append("prompt_injection_or_policy_evasion")

    blocked = bool(categories)
    allowed_hint = socratic_hint_from_review(text, categories, help_level)
    return {
        "status": "blocked" if blocked else "allowed",
        "blocked": blocked,
        "requested_help_level": help_level,
        "mode": mode,
        "categories": categories,
        "privacy_flags": privacy_flags,
        "raw_output_hash": stable_hash(text),
        "allowed_socratic_hint": allowed_hint,
        "public_safe": not privacy_flags and not blocked,
        "ledger_policy": "raw external AI output is hashed only; do not store transcript by default",
    }


def socratic_hint_from_review(text: str, categories: list[str], help_level: str) -> str:
    skill_tags = detect_skill_tags(text)
    if "exam_controlled_requires_written_approval" in categories:
        return (
            "Dieser KI-Pfad ist im Pruefungsmodus ohne schriftliche Freigabe gesperrt. "
            "Formuliere stattdessen den kleinsten lokalen A0-A2-Schritt, den du selbst pruefen kannst."
        )
    if "private_or_sensitive_data" in categories:
        return (
            "Entferne zuerst private oder sensible Angaben. Danach darf nur eine abstrakte Frage "
            "ohne Namen, IDs, Diagnosen, lokale Pfade oder Geheimnisse weiterverarbeitet werden."
        )
    if any(category in categories for category in ["final_solution", "code_fix_or_complete_code", "values_inserted", "final_interpretation"]):
        return (
            "Die externe Hilfe war zu loesungsnah. Nutze nur diese Rueckfrage: "
            "Welcher Teil ist dein eigener naechster Schritt, und welche Variable, Spalte oder Fehlermeldung musst du selbst begruenden?"
        )
    if "source_or_citation_risk" in categories:
        return "Markiere die Aussage als ungeprueft und suche eine echte Kursquelle oder offizielle Dokumentation."
    if "prompt_injection_or_policy_evasion" in categories:
        return "Ignoriere Umgehungsanweisungen. Nutze nur die sichtbare Kursregel und formuliere den naechsten eigenen A0-A2-Schritt."
    if "python_lists" in skill_tags:
        return "Pruefe bei der Liste zuerst: Index, Laenge, append/extend und erwarteter Datentyp."
    if "pandas" in skill_tags:
        return "Pruefe zuerst Spaltennamen, Datentypen und fehlende Werte, bevor du pandas-Code ergaenzt."
    if "boxplots" in skill_tags:
        return "Klaere zuerst Messwert, Gruppe, Einheit und was der Boxplot nur deskriptiv zeigen darf."
    if help_level in {"A0", "A1", "A2"}:
        return "Stelle eine Rueckfrage, die den naechsten eigenen Denkschritt ausloest, ohne Code oder Ergebnis vorzugeben."
    return "Reduziere die Hilfe auf eine Frage und einen Hinweis auf das relevante Konzept."


def generate_socratic_prompt_card(
    task: str,
    tool: str = "colab_gemini",
    mode: str = PRACTICE_OVERLAY,
    source_card_ids: list[str] | None = None,
) -> dict[str, Any]:
    mode = mode if mode in ALLOWED_MODES else PRACTICE_OVERLAY
    source_card_ids = source_card_ids or []
    skill_tags = detect_skill_tags(task)
    blocked = mode == EXAM_CONTROLLED
    copyable_prompt = (
        "Du bist ein sokratischer Python-Neuro-Tutor. Gib keine finale Loesung, "
        "keinen vollstaendigen Code, keine konkreten Werte und keine abgabefertige Interpretation. "
        "Stelle zuerst 1-3 Rueckfragen, dann maximal einen kleinen Konzept-Hinweis. "
        "Markiere Unsicherheit und nenne, welche Kursquelle oder offizielle Dokumentation geprueft werden sollte.\n\n"
        f"Aufgabe/Problem: {task.strip()}\n"
        f"Skill-Fokus: {', '.join(skill_tags)}"
    )
    return {
        "mode": mode,
        "tool": tool,
        "blocked_in_exam_without_approval": blocked,
        "source_card_ids": source_card_ids,
        "skill_tags": skill_tags,
        "copyable_prompt": copyable_prompt,
        "student_checklist": [
            "eigener Versuch vor externer KI",
            "keine privaten Daten",
            "keine finale Loesung uebernehmen",
            "Gretel/UniBot-Filter vor Nutzung der Antwort",
            "Reflexion im Help-Ledger",
        ],
    }


def compute_independence_score(
    help_events: list[dict[str, Any]] | str | None = None,
    accessibility_used: bool = False,
) -> dict[str, Any]:
    if isinstance(help_events, str) or help_events is None:
        events = [{"help_level": normalize_help_level(help_events)}]
    else:
        events = list(help_events)

    levels = [normalize_help_level(event.get("help_level")) for event in events]
    deduction = max((HELP_LEVEL_DEDUCTIONS[level] for level in levels), default=0)
    if any(level == "A6" for level in levels):
        status = "repeat_task"
        score = 0
    else:
        status = "selftest-only"
        score = max(0, 100 - deduction)
    return {
        "status": status,
        "score": score,
        "deduction": deduction,
        "help_levels": levels,
        "accessibility_neutral": bool(accessibility_used),
        "note": "Privater Lernspiegel, keine Note und kein offizielles Pruefungsurteil.",
    }


def update_local_skill_state(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for event in events or []:
        text = str(event.get("text", ""))
        help_level = normalize_help_level(event.get("help_level"))
        for tag in detect_skill_tags(text):
            bucket = state.setdefault(tag, {"signals": 0, "high_help_events": 0, "last_help_level": help_level})
            bucket["signals"] += 1
            bucket["last_help_level"] = help_level
            if HELP_LEVEL_DEDUCTIONS[help_level] >= HELP_LEVEL_DEDUCTIONS["A4"]:
                bucket["high_help_events"] += 1
    return state


def recommend_next_tasks(skill_state: dict[str, Any] | None = None, max_tasks: int = 3) -> dict[str, Any]:
    templates = {
        "python_lists": "Erstelle eine Liste mit Messwerten, greife auf Index 0 und -1 zu, und erklaere den Unterschied zwischen append und extend.",
        "loops": "Schreibe eine for-Schleife, die Messwerte prueft, aber erst als Pseudocode und dann als kleinsten Python-Schritt.",
        "dictionaries": "Ordne zwei Gruppenlabels je einer Messwertliste zu und erklaere, wann ein KeyError entsteht.",
        "functions": "Kapsle einen kleinen Datencheck in eine Funktion und formuliere zuerst Eingabe, Ausgabe und Rueckgabewert.",
        "numpy": "Wandle eine Messwertliste in ein NumPy-Array um und vergleiche mean/std mit deiner Erwartung.",
        "pandas": "Lade eine synthetische Tabelle, pruefe df.head(), df.dtypes und fehlende Werte, bevor du eine Spalte nutzt.",
        "boxplots": "Bestimme Messwert, Gruppe und Einheit fuer einen Boxplot und schreibe nur die Plot-Entscheidung, nicht die Interpretation.",
        "debugging": "Nimm eine Traceback-Zeile, markiere Fehlertyp, betroffene Variable und den kleinsten Test, der den Fehler isoliert.",
        "colab_jupyter": "Beschreibe in einem Notebook Ziel, Vorhersage, eigenen Versuch, Fehler und Reflexion vor dem naechsten KI-Hinweis.",
    }
    ranked = sorted(
        (skill_state or {}).items(),
        key=lambda item: (item[1].get("high_help_events", 0), item[1].get("signals", 0), item[0]),
        reverse=True,
    )
    if not ranked:
        ranked = [("python_lists", {}), ("debugging", {}), ("pandas", {})]
    tasks = [
        {
            "skill_tag": tag,
            "task": templates.get(tag, templates["debugging"]),
            "source_policy": "Use only reviewed course material or synthetic demo data.",
            "assessment_policy": "practice-only, no grade",
        }
        for tag, _ in ranked[:max_tasks]
    ]
    return {"tasks": tasks, "model": "local_skill_state", "storage": "local-only"}


def guardian_practice_flow(
    task: str,
    external_output: str,
    requested_help_level: str = "A2",
    mode: str = PRACTICE_OVERLAY,
    tool: str = "colab_gemini",
    source_card_ids: list[str] | None = None,
    accessibility_used: bool = False,
    approval_reference: str | None = None,
    student_reflection: str = "",
) -> dict[str, Any]:
    source_card_ids = source_card_ids or []
    prompt_card = generate_socratic_prompt_card(task, tool=tool, mode=mode, source_card_ids=source_card_ids)
    review = classify_external_ai_output(
        external_output,
        requested_help_level=requested_help_level,
        mode=mode,
        approval_reference=approval_reference,
    )
    score = compute_independence_score(requested_help_level, accessibility_used=accessibility_used)
    skill_state = update_local_skill_state(
        [
            {"text": task, "help_level": requested_help_level},
            {"text": external_output, "help_level": requested_help_level},
        ]
    )
    event = GuardianEvent(
        mode=mode if mode in ALLOWED_MODES else PRACTICE_OVERLAY,
        tool=tool,
        task_id=stable_hash(task)[:12],
        skill_tags=prompt_card["skill_tags"],
        raw_output_hash=review["raw_output_hash"],
        classification=review["categories"],
        allowed_hint=review["allowed_socratic_hint"],
        help_level=normalize_help_level(requested_help_level),
        privacy_flags=review["privacy_flags"],
        source_card_ids=source_card_ids,
        student_reflection=student_reflection,
    )
    return {
        "artifact_type": "unibot_guardian_practice_flow",
        "mode": mode,
        "prompt_card": prompt_card,
        "postfilter": review,
        "formative_score": score,
        "skill_state": skill_state,
        "next_tasks": recommend_next_tasks(skill_state),
        "guardian_event": event.to_public_dict(),
        "raw_output_stored": False,
    }
