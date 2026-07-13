from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from datetime import date
from typing import Any

from .public_safety import scan_text


LAST_CHECKED = "2026-06-13"
SOURCE_CARD_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-source-card-release-review-board-claim-alignment-v1"
)

SOURCE_CARD_RELEASE_REVIEW_BOARD_READINESS_CHECK_IDS = [
    "source_cards",
    "source_card_drift_guard",
    "redteam",
    "notebook_template",
    "publication_package",
    "release_runbook",
    "review_board_packet",
    "gretel_bachelor_thesis_package",
    "public_safety",
    "python_exam_local_cycle_operator_workspace_card",
]

SOURCE_CARD_RELEASE_REVIEW_BOARD_HUMAN_GATES = [
    "human_submission_review_required",
    "public_safety_required",
    "written_university_clearance_required_before_exam_use",
]


@dataclass(frozen=True)
class SourceCard:
    source_id: str
    title: str
    url: str
    source_kind: str
    authority_type: str
    product_rule: str
    risk_level: str = "medium"
    public_status: str = "public-link-only"
    last_checked: str = LAST_CHECKED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SOURCE_CARDS = [
    SourceCard(
        source_id="hg-nrw-2025",
        title="Hochschulgesetz Nordrhein-Westfalen, current 2025 version",
        url="https://recht.nrw.de/lrgv/gesetz/07052025-gesetz-ueber-die-hochschulen-des-landes-nordrhein-westfalen-hochschulgesetz-hg/",
        source_kind="law",
        authority_type="state-law",
        product_rule="Exam and accommodation use must remain tied to the applicable university authority and exam regulation.",
        risk_level="high",
    ),
    SourceCard(
        source_id="hg-nrw-62b",
        title="Hochschulgesetz Nordrhein-Westfalen section 62b",
        url="https://recht.nrw.de/lrgv/gesetz/07052025-gesetz-ueber-die-hochschulen-des-landes-nordrhein-westfalen-hochschulgesetz-hg/",
        source_kind="law",
        authority_type="state-law",
        product_rule="Accommodation interests stay in the institutional inclusion process; UniBot may document support categories but not decide them.",
        risk_level="high",
    ),
    SourceCard(
        source_id="hg-nrw-64",
        title="Hochschulgesetz Nordrhein-Westfalen section 64",
        url="https://recht.nrw.de/lrgv/gesetz/07052025-gesetz-ueber-die-hochschulen-des-landes-nordrhein-westfalen-hochschulgesetz-hg/",
        source_kind="law",
        authority_type="state-law",
        product_rule="Exam procedures, aids, breaches, and online-exam privacy must fit the applicable exam regulation before any exam mode.",
        risk_level="high",
    ),
    SourceCard(
        source_id="uoc-ki-lehre",
        title="University of Cologne guidance on generative AI in teaching",
        url="https://uni-koeln.de/studium-lehre/lehrende/ki-in-der-bildung/wie-kann-ich-generative-ki-im-kontext-von-lehre-und-lernen-produktiv-anwenden",
        source_kind="university-policy",
        authority_type="university",
        product_rule="AI use must be transparent and exam-rule aware.",
        risk_level="high",
    ),
    SourceCard(
        source_id="uoc-hilfsmittel",
        title="University of Cologne WiSo aids in exams",
        url="https://wiso.uni-koeln.de/de/fakultaet/dekanat/zentrale-fakultaetsverwaltung/pruefungsamt/rund-um-pruefungen/hilfsmittel",
        source_kind="university-policy",
        authority_type="university-exam-office",
        product_rule="UniBot must not describe an aid as cleared without written exam-authority clearance.",
        risk_level="high",
    ),
    SourceCard(
        source_id="uoc-ki-faq",
        title="University of Cologne FAQ on artificial intelligence",
        url="https://verwaltung.uni-koeln.de/stabsstelle02.1/content/faq/data/kuenstliche_intelligenz/index_ger.html",
        source_kind="university-policy",
        authority_type="university",
        product_rule="Exam mode must block external KI unless the applicable rule explicitly allows it.",
        risk_level="high",
    ),
    SourceCard(
        source_id="uoc-nachteilsausgleich",
        title="University of Cologne Nachteilsausgleich information",
        url="https://hf-studium.uni-koeln.de/studienorganisation/nachteilsausgleich",
        source_kind="university-policy",
        authority_type="university-inclusion-process",
        product_rule="Accessibility support stays score-neutral and non-decisional.",
        risk_level="high",
    ),
    SourceCard(
        source_id="gdpr-2016-679",
        title="General Data Protection Regulation",
        url="https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng",
        source_kind="law",
        authority_type="eu-law",
        product_rule="Apply lawfulness, transparency, purpose limitation, minimisation, security, and accountability.",
        risk_level="high",
    ),
    SourceCard(
        source_id="dsk-ai-privacy-2024",
        title="Datenschutzkonferenz guidance on AI and data protection",
        url="https://www.datenschutzkonferenz-online.de/media/oh/20240506_DSK_Orientierungshilfe_KI_und_Datenschutz.pdf",
        source_kind="authority-guidance",
        authority_type="data-protection-authority",
        product_rule="Prefer controlled systems, avoid unnecessary prompt histories, and validate outputs.",
        risk_level="high",
    ),
    SourceCard(
        source_id="eu-ai-act-2024",
        title="EU AI Act 2024/1689",
        url="https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng",
        source_kind="law",
        authority_type="eu-law",
        product_rule="Education assessment and test-behaviour monitoring can become high-risk; keep scores private and avoid proctoring.",
        risk_level="high",
    ),
    SourceCard(
        source_id="dfg-gwp",
        title="DFG good research practice",
        url="https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/gwp",
        source_kind="research-integrity",
        authority_type="research-funder",
        product_rule="Document methods, versions, limitations, and reproducible evidence.",
    ),
    SourceCard(
        source_id="google-colab-gemini",
        title="Google Colab Gemini code assistance",
        url="https://docs.cloud.google.com/colab/docs/use-code-completion",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="Require validation; do not pass model output through unreviewed.",
    ),
    SourceCard(
        source_id="gemini-code-assist-validation",
        title="Gemini Code Assist overview and validation guidance",
        url="https://developers.google.com/gemini-code-assist/docs/overview",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="Model output can be plausible but wrong; the simulation loop must validate and filter before use.",
    ),
    SourceCard(
        source_id="openai-evals",
        title="OpenAI Evals guidance",
        url="https://developers.openai.com/api/docs/guides/evals",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="Use fixed scenarios, clear graders, and repeatable reports to test model-system behaviour.",
    ),
    SourceCard(
        source_id="deepseek-chat-completion-api",
        title="DeepSeek Chat Completion API",
        url="https://api-docs.deepseek.com/api/create-chat-completion",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="DeepSeek-compatible integration stays mock-first; live calls require explicit opt-in and redacted synthetic inputs.",
        risk_level="high",
    ),
    SourceCard(
        source_id="zai-glm-52",
        title="Z.AI GLM-5.2 model documentation",
        url="https://docs.z.ai/guides/llm/glm-5.2",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="GLM-5.2 may be used only through redacted proposal and independent-review packets with no tools, apply, push, merge, or Final-Go authority.",
        risk_level="high",
        last_checked="2026-07-11",
    ),
    SourceCard(
        source_id="zai-glm-52-migration",
        title="Z.AI migration guide to GLM-5.2",
        url="https://docs.z.ai/guides/overview/migrate-to-glm-new",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="Model-specific parameters and migration behavior must be documented before any live provider call.",
        risk_level="high",
        last_checked="2026-07-11",
    ),
    SourceCard(
        source_id="zai-glm-pricing",
        title="Z.AI model pricing documentation",
        url="https://docs.z.ai/guides/overview/pricing",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="Public-only provider calls require explicit scope, a fresh price check, and the 20 USD monthly budget guard.",
        risk_level="high",
        last_checked="2026-07-11",
    ),
    SourceCard(
        source_id="chrome-content-scripts",
        title="Chrome extension content scripts",
        url="https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="A browser overlay can support practice UX by reading and modifying page DOM.",
    ),
    SourceCard(
        source_id="chrome-webrequest-mv3",
        title="Chrome webRequest in Manifest V3",
        url="https://developer.chrome.com/docs/extensions/reference/api/webRequest",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="Normal MV3 extensions must not be treated as hard response interception or exam security.",
        risk_level="high",
    ),
    SourceCard(
        source_id="chrome-limited-use",
        title="Chrome Web Store Limited Use policy",
        url="https://developer.chrome.com/docs/webstore/program-policies/limited-use",
        source_kind="technical-doc",
        authority_type="vendor",
        product_rule="Browser extension data collection must be visible, limited to the stated purpose, and not over-collected.",
        risk_level="medium",
    ),
    SourceCard(
        source_id="jupyter-ai",
        title="Jupyter AI",
        url="https://github.com/jupyterlab/jupyter-ai",
        source_kind="technical-doc",
        authority_type="open-source-project",
        product_rule="A local or managed Jupyter route is a plausible controlled-channel path.",
    ),
    SourceCard(
        source_id="cs50-ai-2024",
        title="Teaching CS50 with AI",
        url="https://dl.acm.org/doi/10.1145/3626252.3630938",
        source_kind="paper",
        authority_type="research-publication",
        product_rule="Course-specific AI support should be constrained by teaching policy and human oversight.",
    ),
    SourceCard(
        source_id="vanlehn-2011",
        title="Relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems",
        url="https://www.tandfonline.com/doi/abs/10.1080/00461520.2011.611369",
        source_kind="paper",
        authority_type="research-publication",
        product_rule="Scaffold steps and feedback instead of giving final answers.",
    ),
    SourceCard(
        source_id="kulik-fletcher-2016",
        title="Effectiveness of intelligent tutoring systems",
        url="https://journals.sagepub.com/doi/10.3102/0034654315581420",
        source_kind="paper",
        authority_type="research-publication",
        product_rule="Evaluate learning-process outcomes, not only generated-output quality.",
    ),
    SourceCard(
        source_id="unesco-genai-2023",
        title="UNESCO guidance for generative AI in education and research",
        url="https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research",
        source_kind="international-guidance",
        authority_type="international-organisation",
        product_rule="Protect privacy, human agency, and pedagogical validation.",
    ),
    SourceCard(
        source_id="oecd-digital-education-2026",
        title="OECD Digital Education Outlook 2026",
        url="https://www.oecd.org/en/publications/oecd-digital-education-outlook-2026_062a7394-en.html",
        source_kind="international-guidance",
        authority_type="international-organisation",
        product_rule="Avoid false mastery by preserving learner cognitive work when external AI scaffolds practice.",
    ),
]


def list_source_cards(source_kind: str | None = None) -> list[dict[str, Any]]:
    cards = SOURCE_CARDS
    if source_kind:
        cards = [card for card in cards if card.source_kind == source_kind]
    return [card.to_dict() for card in cards]


def get_source_card(source_id: str) -> dict[str, Any] | None:
    for card in SOURCE_CARDS:
        if card.source_id == source_id:
            return card.to_dict()
    return None


def required_source_card_ids() -> list[str]:
    return [
        "hg-nrw-2025",
        "hg-nrw-62b",
        "hg-nrw-64",
        "uoc-ki-lehre",
        "uoc-hilfsmittel",
        "uoc-ki-faq",
        "uoc-nachteilsausgleich",
        "gdpr-2016-679",
        "dsk-ai-privacy-2024",
        "eu-ai-act-2024",
        "dfg-gwp",
        "google-colab-gemini",
        "gemini-code-assist-validation",
        "openai-evals",
        "deepseek-chat-completion-api",
        "zai-glm-52",
        "zai-glm-52-migration",
        "zai-glm-pricing",
        "chrome-content-scripts",
        "chrome-webrequest-mv3",
        "chrome-limited-use",
        "jupyter-ai",
        "cs50-ai-2024",
        "vanlehn-2011",
        "kulik-fletcher-2016",
        "unesco-genai-2023",
        "oecd-digital-education-2026",
    ]


def build_source_card_drift_report(*, as_of: str | None = None, max_age_days: int = 120) -> dict[str, Any]:
    cards = list_source_cards()
    required_ids = required_source_card_ids()
    source_ids = [card["source_id"] for card in cards]
    duplicate_ids = sorted({source_id for source_id in source_ids if source_ids.count(source_id) > 1})
    required_id_set = set(required_ids)
    high_risk_ids = sorted(card["source_id"] for card in cards if card["risk_level"] == "high")
    as_of_date = date.fromisoformat(as_of) if as_of else date.today()

    invalid_last_checked: list[str] = []
    stale_source_ids: list[str] = []
    for card in cards:
        try:
            checked_date = date.fromisoformat(card["last_checked"])
        except ValueError:
            invalid_last_checked.append(card["source_id"])
            continue
        if (as_of_date - checked_date).days > max_age_days:
            stale_source_ids.append(card["source_id"])

    report = {
        "schema_version": "unibot-source-card-drift-report-v1",
        "status": "pass",
        "as_of": as_of_date.isoformat(),
        "max_age_days": max_age_days,
        "card_count": len(cards),
        "required_source_card_count": len(required_ids),
        "high_risk_source_card_count": len(high_risk_ids),
        "source_kind_count": len({card["source_kind"] for card in cards}),
        "authority_type_count": len({card["authority_type"] for card in cards}),
        "duplicate_source_ids": duplicate_ids,
        "missing_required_source_card_ids": sorted(required_id_set - set(source_ids)),
        "unlisted_high_risk_source_card_ids": sorted(set(high_risk_ids) - required_id_set),
        "invalid_https_source_ids": sorted(card["source_id"] for card in cards if not card["url"].startswith("https://")),
        "missing_product_rule_source_ids": sorted(card["source_id"] for card in cards if not card["product_rule"].strip()),
        "invalid_risk_level_source_ids": sorted(
            card["source_id"] for card in cards if card["risk_level"] not in {"low", "medium", "high"}
        ),
        "invalid_public_status_source_ids": sorted(
            card["source_id"] for card in cards if card["public_status"] != "public-link-only"
        ),
        "invalid_last_checked_source_ids": sorted(invalid_last_checked),
        "stale_source_card_ids": sorted(stale_source_ids),
        "policy": (
            "Source-bound scientific claims require stable source-card IDs, HTTPS public links, product rules, "
            "known risk levels, required high-risk coverage, and recent review dates."
        ),
    }
    issue_keys = [
        "duplicate_source_ids",
        "missing_required_source_card_ids",
        "unlisted_high_risk_source_card_ids",
        "invalid_https_source_ids",
        "missing_product_rule_source_ids",
        "invalid_risk_level_source_ids",
        "invalid_public_status_source_ids",
        "invalid_last_checked_source_ids",
        "stale_source_card_ids",
    ]
    if any(report[key] for key in issue_keys):
        report["status"] = "blocked"
    scan = scan_text(str(report), "unibot-source-card-drift-report")
    report["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        report["status"] = "blocked"
    return report


def build_source_card_release_review_board_claim_alignment(
    drift_report: dict[str, Any] | None = None,
    python_exam_local_cycle_operator_workspace_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cards = list_source_cards()
    drift_report = drift_report or build_source_card_drift_report()
    corpus_hash = source_card_corpus_hash(cards)
    drift_hash = source_card_drift_report_hash(drift_report)
    workspace_card = safe_source_card_workspace_card(
        python_exam_local_cycle_operator_workspace_card
        if isinstance(python_exam_local_cycle_operator_workspace_card, dict)
        else synthetic_source_card_workspace_card(),
        source_card_corpus_hash=corpus_hash,
        source_card_drift_hash=drift_hash,
    )
    workspace_card_readiness_gate_linked = (
        workspace_card.get("status") == "python_exam_local_cycle_operator_workspace_card_ready"
        and workspace_card.get("ready_for_operator_prefill") is True
        and workspace_card.get("help_ledger_preview_status") == "help_ledger_preview_ready"
        and workspace_card.get("help_ledger_preview_hash") != ""
        and workspace_card.get("exam_deployment_status") == "not_cleared"
        and workspace_card.get("not_cleared_receipt") is True
        and workspace_card.get("raw_workspace_card_returned") is False
    )
    card_rows = [
        {
            "source_id": card["source_id"],
            "source_kind": card["source_kind"],
            "authority_type": card["authority_type"],
            "risk_level": card["risk_level"],
            "public_status": card["public_status"],
            "readiness_check_ids": SOURCE_CARD_RELEASE_REVIEW_BOARD_READINESS_CHECK_IDS,
            "human_gates": SOURCE_CARD_RELEASE_REVIEW_BOARD_HUMAN_GATES,
            "public_link_only": card["public_status"] == "public-link-only",
            "has_product_rule": bool(card["product_rule"].strip()),
        }
        for card in cards
    ]
    required_ids = required_source_card_ids()
    required_id_set = set(required_ids)
    present_ids = {card["source_id"] for card in cards}
    high_risk_ids = {card["source_id"] for card in cards if card["risk_level"] == "high"}
    contracts = {
        "workspace_card_source_gate_linked": workspace_card_readiness_gate_linked
        and workspace_card.get("checkpoint_hash") == corpus_hash
        and workspace_card.get("task_hash") == drift_hash,
    }
    alignment = {
        "schema_version": "unibot-source-card-claim-alignment-v1",
        "status": "ready" if cards and drift_report.get("status") == "pass" else "blocked",
        "source_card_count": len(cards),
        "required_source_card_count": len(required_ids),
        "high_risk_source_card_count": len(high_risk_ids),
        "public_link_only": all(row["public_link_only"] for row in card_rows),
        "all_cards_have_product_rules": all(row["has_product_rule"] for row in card_rows),
        "manual_publication_claim_contract": {
            "expected_schema_version": SOURCE_CARD_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
            "required_redteam_schema_version": "unibot-redteam-release-review-board-claim-alignment-v1",
            "required_notebook_handoff_schema_version": (
                "unibot-notebook-handoff-release-review-board-claim-alignment-v1"
            ),
            "required_publication_schema_version": (
                "unibot-publication-release-review-board-claim-alignment-v1"
            ),
            "required_readiness_check_ids": SOURCE_CARD_RELEASE_REVIEW_BOARD_READINESS_CHECK_IDS,
            "required_human_gates": SOURCE_CARD_RELEASE_REVIEW_BOARD_HUMAN_GATES,
            "use": (
                "Source cards anchor public scientific, legal, privacy, technical, and pedagogical claims; "
                "they do not approve public release, institutional submission, provider calls, or exam use."
            ),
        },
        "card_rows": card_rows,
        "unique_readiness_check_ids": sorted(
            {check_id for row in card_rows for check_id in row["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for row in card_rows for gate in row["human_gates"]}),
        "missing_required_source_card_ids": sorted(required_id_set - present_ids),
        "unlisted_high_risk_source_card_ids": drift_report.get("unlisted_high_risk_source_card_ids", []),
        "drift_status": drift_report.get("status", "unknown"),
        "drift_public_safety_status": drift_report.get("public_safety_status", "unknown"),
        "failed_contract_ids": sorted(contract_id for contract_id, passed in contracts.items() if not passed),
        "contracts": contracts,
        "workspace_card_status": workspace_card["status"],
        "workspace_card_selected_skill_tag": workspace_card["selected_skill_tag"],
        "workspace_card_ready_for_operator_prefill": workspace_card["ready_for_operator_prefill"],
        "workspace_card_help_ledger_status": workspace_card["help_ledger_preview_status"],
        "workspace_card_help_ledger_hash_present": workspace_card["help_ledger_preview_hash"] != "",
        "workspace_card_readiness_gate_linked": workspace_card_readiness_gate_linked,
        "workspace_card_source_gate_linked": contracts["workspace_card_source_gate_linked"],
        "workspace_card_readiness_gate_claim_linked": "python_exam_local_cycle_operator_workspace_card"
        in sorted({check_id for row in card_rows for check_id in row["readiness_check_ids"]}),
        "raw_workspace_card_returned": workspace_card["raw_workspace_card_returned"],
        "source_card_corpus_hash": corpus_hash,
        "source_card_drift_hash": drift_hash,
        "blocked_claims": ["exam clearance", "official grading", "proctoring", "KI-detection evidence"],
        "public_language": "Public claims must cite source-card IDs and keep legal, exam, privacy, and institutional decisions human-reviewed.",
    }
    required_check_ids = set(alignment["manual_publication_claim_contract"]["required_readiness_check_ids"])
    present_check_ids = set(alignment["unique_readiness_check_ids"])
    alignment["missing_release_review_board_claim_check_ids"] = sorted(required_check_ids - present_check_ids)
    required_human_gates = set(alignment["manual_publication_claim_contract"]["required_human_gates"])
    present_human_gates = set(alignment["required_human_gates"])
    alignment["missing_release_review_board_claim_human_gates"] = sorted(required_human_gates - present_human_gates)
    if (
        drift_report.get("status") != "pass"
        or drift_report.get("public_safety_status") != "pass"
        or alignment["missing_required_source_card_ids"]
        or alignment["unlisted_high_risk_source_card_ids"]
        or not alignment["public_link_only"]
        or not alignment["all_cards_have_product_rules"]
        or alignment["missing_release_review_board_claim_check_ids"]
        or alignment["missing_release_review_board_claim_human_gates"]
        or alignment["failed_contract_ids"]
    ):
        alignment["status"] = "blocked"
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "source-card-claim-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked"
        alignment["public_safety_findings"] = scan["findings"]
    return alignment


def source_card_corpus_hash(cards: list[dict[str, Any]] | None = None) -> str:
    public_cards = cards if isinstance(cards, list) else list_source_cards()
    return hashlib.sha256(
        json.dumps(
            {
                "required_source_card_ids": required_source_card_ids(),
                "cards": sorted(public_cards, key=lambda card: str(card.get("source_id", ""))),
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def source_card_drift_report_hash(drift_report: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                key: value
                for key, value in drift_report.items()
                if key not in {"public_safety_findings"}
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def synthetic_source_card_workspace_card() -> dict[str, Any]:
    preview_hash = hashlib.sha256(b"synthetic source card workspace card").hexdigest()
    return {
        "schema_version": "unibot-python-exam-local-cycle-operator-workspace-card-v1",
        "artifact_type": "python_exam_local_cycle_operator_workspace_card",
        "status": "python_exam_local_cycle_operator_workspace_card_ready",
        "selected_skill_tag": "pandas",
        "exam_deployment_status": "not_cleared",
        "not_cleared_receipt": True,
        "workspace_card_summary": {
            "recommendation": "ready_for_operator_prefill",
            "recommendation_reason": "synthetic source-card drift-guard prerequisites are satisfied",
            "ready_for_operator_prefill": True,
            "help_ledger_preview_status": "help_ledger_preview_ready",
            "selected_skill_tag": "pandas",
            "next_safe_action": "review_source_card_hashes_before_workspace_prefill",
            "next_safe_user_action": "review_hash_only_source_card_drift_before_public_claim_use",
            "operator_run_endpoint": "/api/unibot/exam-workspace/operator-run",
            "operator_run_method": "POST",
            "help_level": "A2",
            "task_hash": "__SOURCE_CARD_DRIFT_HASH__",
            "checkpoint_hash": "__SOURCE_CARD_CORPUS_HASH__",
            "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "zai-glm-52"],
            "source_anchor_count": 3,
            "help_ledger_preview_hash": preview_hash,
        },
        "help_ledger_preview": {
            "status": "help_ledger_preview_ready",
            "help_level": "A2",
            "preview_hash": preview_hash,
        },
    }


def safe_source_card_workspace_card(
    workspace_card: dict[str, Any],
    *,
    source_card_corpus_hash: str = "",
    source_card_drift_hash: str = "",
) -> dict[str, Any]:
    summary = workspace_card.get("workspace_card_summary", {}) if isinstance(workspace_card.get("workspace_card_summary"), dict) else {}
    ledger = workspace_card.get("help_ledger_preview", {}) if isinstance(workspace_card.get("help_ledger_preview"), dict) else {}
    if not summary and (
        workspace_card.get("help_ledger_preview_hash") is not None
        or workspace_card.get("ready_for_operator_prefill") is not None
        or workspace_card.get("help_ledger_preview_status") is not None
    ):
        summary = workspace_card
    checkpoint_hash = str(summary.get("checkpoint_hash", ""))
    task_hash = str(summary.get("task_hash", ""))
    if source_card_corpus_hash and checkpoint_hash == "__SOURCE_CARD_CORPUS_HASH__":
        checkpoint_hash = source_card_corpus_hash
    if source_card_drift_hash and task_hash == "__SOURCE_CARD_DRIFT_HASH__":
        task_hash = source_card_drift_hash
    return {
        "status": workspace_card.get("status", "missing"),
        "selected_skill_tag": str(summary.get("selected_skill_tag", workspace_card.get("selected_skill_tag", ""))),
        "recommendation": str(summary.get("recommendation", "keep_blocked")),
        "recommendation_reason": str(summary.get("recommendation_reason", "missing_source_card_drift_guard")),
        "ready_for_operator_prefill": bool(summary.get("ready_for_operator_prefill", False)),
        "help_ledger_preview_status": str(summary.get("help_ledger_preview_status", ledger.get("status", "missing"))),
        "next_safe_action": str(summary.get("next_safe_action", "")),
        "next_safe_user_action": str(summary.get("next_safe_user_action", "")),
        "operator_run_endpoint": str(summary.get("operator_run_endpoint", "")),
        "operator_run_method": str(summary.get("operator_run_method", "POST")),
        "help_level": str(summary.get("help_level", ledger.get("help_level", "A2"))),
        "task_hash": task_hash,
        "checkpoint_hash": checkpoint_hash,
        "source_card_ids": [str(item) for item in (summary.get("source_card_ids", []) or [])][:8],
        "source_anchor_count": int(summary.get("source_anchor_count", 0) or 0),
        "help_ledger_preview_hash": str(summary.get("help_ledger_preview_hash", ledger.get("preview_hash", ""))),
        "not_cleared_receipt": bool(workspace_card.get("not_cleared_receipt", True)),
        "exam_deployment_status": "not_cleared",
        "raw_workspace_card_returned": False,
    }
