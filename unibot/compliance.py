from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text
from .source_cards import get_source_card


COMPLIANCE_MATRIX_SCHEMA_VERSION = "unibot-compliance-matrix-v1"

DOMAIN_ALIGNMENT = {
    "exam_authority": {
        "readiness_check_ids": ["exam_boundary", "review_board_packet", "release_runbook"],
        "human_gates": ["written_university_clearance_required_before_exam_use"],
    },
    "inclusion": {
        "readiness_check_ids": ["authority_handoff", "review_board_packet"],
        "human_gates": ["human_submission_review_required"],
    },
    "privacy": {
        "readiness_check_ids": ["public_safety", "data_protection_screening"],
        "human_gates": ["public_safety_required"],
    },
    "ai_governance": {
        "readiness_check_ids": ["exam_boundary", "gretel_bachelor_thesis_package"],
        "human_gates": ["written_university_clearance_required_before_exam_use"],
    },
    "research_integrity": {
        "readiness_check_ids": ["source_card_drift_guard", "evaluation_packet", "gretel_bachelor_thesis_package"],
        "human_gates": ["human_submission_review_required"],
    },
    "pedagogy": {
        "readiness_check_ids": ["evaluation_packet", "redteam", "adaptive_task_plan"],
        "human_gates": ["human_submission_review_required"],
    },
    "external_tool_use": {
        "readiness_check_ids": ["public_safety", "notebook_template"],
        "human_gates": ["provider_call_requires_explicit_go_and_redaction_receipt"],
    },
    "technical_boundary": {
        "readiness_check_ids": ["public_safety", "review_board_packet", "release_runbook"],
        "human_gates": ["human_review_required"],
    },
    "future_exam_architecture": {
        "readiness_check_ids": ["exam_boundary", "authority_handoff", "review_board_packet"],
        "human_gates": ["written_university_clearance_required_before_exam_use"],
    },
}


@dataclass(frozen=True)
class ComplianceRequirement:
    requirement_id: str
    domain: str
    risk_level: str
    authority_reviewers: tuple[str, ...]
    source_card_ids: tuple[str, ...]
    product_rule: str
    implemented_controls: tuple[str, ...]
    verification_evidence: tuple[str, ...]
    blocked_use: tuple[str, ...]
    status: str = "draft_control_ready"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["authority_reviewers"] = list(self.authority_reviewers)
        payload["source_card_ids"] = list(self.source_card_ids)
        payload["implemented_controls"] = list(self.implemented_controls)
        payload["verification_evidence"] = list(self.verification_evidence)
        payload["blocked_use"] = list(self.blocked_use)
        return payload


def compliance_requirements() -> list[ComplianceRequirement]:
    return [
        ComplianceRequirement(
            requirement_id="exam-clearance-boundary",
            domain="exam_authority",
            risk_level="high",
            authority_reviewers=("Pruefungsamt", "Lehreinheit / Modulverantwortliche"),
            source_card_ids=("hg-nrw-2025", "hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq"),
            product_rule="Exam-controlled use stays blocked until written authority clearance exists.",
            implemented_controls=(
                "exam_controlled blocks external KI without approval_reference",
                "public language uses not officially cleared / requested instead of approved",
                "publication and readiness status stay not exam release",
            ),
            verification_evidence=(
                "tests/test_unibot_guardian.py",
                "tests/test_unibot_readiness.py",
                "tests/test_unibot_publication.py",
            ),
            blocked_use=("exam deployment", "official grading", "hidden external KI help"),
        ),
        ComplianceRequirement(
            requirement_id="accessibility-neutrality",
            domain="inclusion",
            risk_level="high",
            authority_reviewers=("Inklusionsbuero / Nachteilsausgleich-Stelle", "Pruefungsamt"),
            source_card_ids=("hg-nrw-62b", "uoc-nachteilsausgleich"),
            product_rule="Accessibility support is documented separately and never lowers the private score.",
            implemented_controls=(
                "compute_independence_score keeps accessibility_used neutral",
                "selftest score is private and formative only",
                "UniBot does not decide accommodation status",
            ),
            verification_evidence=("tests/test_unibot_guardian.py", "tests/test_unibot_handoff.py"),
            blocked_use=("accommodation decision", "accessibility penalty", "official support status decision"),
        ),
        ComplianceRequirement(
            requirement_id="data-minimisation-and-public-safety",
            domain="privacy",
            risk_level="high",
            authority_reviewers=("Datenschutz", "IT / SZI"),
            source_card_ids=("gdpr-2016-679", "dsk-ai-privacy-2024", "chrome-limited-use"),
            product_rule="Store minimal local metadata and block private material from public artifacts.",
            implemented_controls=(
                "raw external KI output is stored as hash by default",
                "public-safety scanner blocks private identifiers, local paths, secrets, and private course references",
                "ledger public summary excludes raw external KI output and student reflections",
            ),
            verification_evidence=(
                "tests/test_unibot_api_and_public_safety.py",
                "tests/test_unibot_ledger.py",
                "tests/test_unibot_readiness.py",
            ),
            blocked_use=("public leakage", "unnecessary prompt history storage", "secret or local path publication"),
        ),
        ComplianceRequirement(
            requirement_id="ai-act-high-risk-avoidance",
            domain="ai_governance",
            risk_level="high",
            authority_reviewers=("Datenschutz", "Pruefungsamt", "Lehreinheit / Modulverantwortliche"),
            source_card_ids=("eu-ai-act-2024",),
            product_rule="Keep UniBot as practice support; avoid official assessment, proctoring, and test-behaviour monitoring.",
            implemented_controls=(
                "Independence Score is private and formative",
                "non-goals state no proctoring, no KI detection, and no automatic grading",
                "exam_controlled is blocked until controlled-channel review",
            ),
            verification_evidence=("tests/test_unibot_publication.py", "tests/test_unibot_readiness.py"),
            blocked_use=("official assessment automation", "proctoring", "disciplinary KI detection"),
        ),
        ComplianceRequirement(
            requirement_id="research-integrity-and-reproducibility",
            domain="research_integrity",
            risk_level="medium",
            authority_reviewers=("Thesis supervision", "Lehreinheit / Modulverantwortliche"),
            source_card_ids=("dfg-gwp",),
            product_rule="Document methods, sources, versions, limitations, evaluation boundaries, and reproducible checks.",
            implemented_controls=(
                "source cards include product rules and last_checked metadata",
                "evaluation packet uses synthetic tasks and a codebook",
                "publication package exposes system card, data card, limitations, and release gates",
            ),
            verification_evidence=(
                "tests/test_unibot_evaluation.py",
                "tests/test_unibot_publication.py",
                "tests/test_unibot_release_runbook.py",
            ),
            blocked_use=("unreviewed thesis claims", "unversioned evidence", "private data in reproduction package"),
        ),
        ComplianceRequirement(
            requirement_id="socratic-pedagogy-and-learning-evidence",
            domain="pedagogy",
            risk_level="medium",
            authority_reviewers=("Lehreinheit / Modulverantwortliche", "Thesis supervision"),
            source_card_ids=(
                "cs50-ai-2024",
                "vanlehn-2011",
                "kulik-fletcher-2016",
                "unesco-genai-2023",
                "oecd-digital-education-2026",
            ),
            product_rule="External AI help is transformed into next-step scaffolding rather than final answers.",
            implemented_controls=(
                "Prompt Cards ask for Socratic hints and uncertainty markers",
                "postfilter blocks complete solutions, code fixes, inserted values, and final interpretations",
                "adaptive tasks target local skill gaps without publishing private course material",
            ),
            verification_evidence=(
                "tests/test_unibot_guardian.py",
                "tests/test_unibot_adaptive_tasks.py",
                "tests/test_unibot_redteam.py",
            ),
            blocked_use=("answer delivery", "false mastery", "learning evidence based only on generated output"),
        ),
        ComplianceRequirement(
            requirement_id="colab-gemini-output-validation",
            domain="external_tool_use",
            risk_level="medium",
            authority_reviewers=("IT / SZI", "Lehreinheit / Modulverantwortliche"),
            source_card_ids=("google-colab-gemini",),
            product_rule="Colab/Gemini output is never accepted unfiltered; the learner must validate and reflect.",
            implemented_controls=(
                "practice flow requires postfilter review of pasted external KI output",
                "notebook template includes prediction, own attempt, source check, reflection, and Help Ledger cells",
                "blocked output never exposes raw text in public events",
            ),
            verification_evidence=("tests/test_unibot_notebooks.py", "tests/test_unibot_api_and_public_safety.py"),
            blocked_use=("unfiltered model output", "hidden solution handoff", "source-free final interpretation"),
        ),
        ComplianceRequirement(
            requirement_id="browser-overlay-limit",
            domain="technical_boundary",
            risk_level="high",
            authority_reviewers=("IT / SZI", "Pruefungsamt"),
            source_card_ids=("chrome-content-scripts", "chrome-webrequest-mv3"),
            product_rule="A normal browser overlay is practice UX, not hard exam security.",
            implemented_controls=(
                "side panel offers visible copy/paste fallback",
                "threat model states that extension interception is not exam security",
                "exam-grade variant is deferred to controlled gateway or managed notebook environment",
            ),
            verification_evidence=("tests/test_unibot_browser_extension.py", "tests/test_unibot_release_runbook.py"),
            blocked_use=("hard exam-security claim", "silent interception claim", "network-level enforcement claim"),
        ),
        ComplianceRequirement(
            requirement_id="controlled-notebook-route",
            domain="future_exam_architecture",
            risk_level="high",
            authority_reviewers=("Pruefungsamt", "Datenschutz", "IT / SZI", "Lehreinheit / Modulverantwortliche"),
            source_card_ids=("jupyter-ai",),
            product_rule="Future exam work should prefer a controlled local or managed notebook channel over a generic browser overlay.",
            implemented_controls=(
                "exam_controlled remains blocked in the MVP",
                "notebook generator is public-safe and output-free",
                "authority handoff asks which controlled channel could be reviewed",
            ),
            verification_evidence=("tests/test_unibot_handoff.py", "tests/test_unibot_notebooks.py"),
            blocked_use=("generic browser-only exam control", "unreviewed model gateway", "raw model output before filtering"),
        ),
    ]


def build_compliance_matrix() -> dict[str, Any]:
    requirements = [requirement.to_dict() for requirement in compliance_requirements()]
    all_source_ids = sorted({source_id for item in requirements for source_id in item["source_card_ids"]})
    missing_source_card_ids = [source_id for source_id in all_source_ids if get_source_card(source_id) is None]
    high_risk_count = len([item for item in requirements if item["risk_level"] == "high"])
    matrix = {
        "schema_version": COMPLIANCE_MATRIX_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "draft_ready_for_authority_review",
        "exam_deployment_status": "not_cleared",
        "requirement_count": len(requirements),
        "high_risk_requirement_count": high_risk_count,
        "source_card_count": len(all_source_ids),
        "missing_source_card_ids": missing_source_card_ids,
        "requirements": requirements,
        "compliance_drift_alignment": build_compliance_drift_alignment(requirements),
        "reviewer_groups": sorted({reviewer for item in requirements for reviewer in item["authority_reviewers"]}),
        "policy": "Authority review matrix only; not legal advice, not exam clearance, and not a substitute for written university approval.",
    }
    if missing_source_card_ids:
        matrix["status"] = "blocked_missing_source_cards"
    scan = scan_text(json.dumps(matrix, ensure_ascii=False), "compliance-matrix")
    matrix["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        matrix["status"] = "blocked_public_safety"
        matrix["public_safety_findings"] = scan["findings"]
    return matrix


def build_compliance_drift_alignment(requirements: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    requirement_rows = list(requirements) if requirements is not None else [item.to_dict() for item in compliance_requirements()]
    alignment_rows = []
    for requirement in requirement_rows:
        mapping = DOMAIN_ALIGNMENT.get(requirement["domain"], {"readiness_check_ids": [], "human_gates": []})
        alignment_rows.append(
            {
                "requirement_id": requirement["requirement_id"],
                "domain": requirement["domain"],
                "risk_level": requirement["risk_level"],
                "source_card_ids": list(requirement["source_card_ids"]),
                "readiness_check_ids": list(mapping["readiness_check_ids"]),
                "human_gates": list(mapping["human_gates"]),
                "verification_evidence_count": len(requirement["verification_evidence"]),
                "blocked_use_count": len(requirement["blocked_use"]),
            }
        )
    alignment = {
        "schema_version": "unibot-compliance-drift-alignment-v1",
        "status": "ready",
        "requirement_count": len(alignment_rows),
        "high_risk_requirement_count": len([row for row in alignment_rows if row["risk_level"] == "high"]),
        "requirements": alignment_rows,
        "source_card_drift_contract": {
            "expected_check_id": "source_card_drift_guard",
            "required_status": "pass",
        },
        "readiness_snapshot_contract": {
            "expected_schema_version": "unibot-readiness-evidence-snapshot-v1",
            "required_status": "ready",
        },
        "review_board_contract": {
            "expected_schema_version": "unibot-review-board-evidence-alignment-v1",
            "required_status": "ready",
        },
        "unmapped_requirement_ids": sorted(row["requirement_id"] for row in alignment_rows if not row["readiness_check_ids"]),
        "requirements_without_human_gates": sorted(row["requirement_id"] for row in alignment_rows if not row["human_gates"]),
        "unique_readiness_check_ids": sorted({check_id for row in alignment_rows for check_id in row["readiness_check_ids"]}),
        "unique_source_card_ids": sorted({source_id for row in alignment_rows for source_id in row["source_card_ids"]}),
        "required_human_gates": sorted({gate for row in alignment_rows for gate in row["human_gates"]}),
        "human_gate_reminder": "Compliance alignment is review preparation only; it is not legal advice, exam clearance, provider approval, or thesis submission approval.",
    }
    if alignment["unmapped_requirement_ids"] or alignment["requirements_without_human_gates"]:
        alignment["status"] = "blocked"
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "compliance-drift-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked_public_safety"
    return alignment


def build_compliance_matrix_markdown() -> str:
    matrix = build_compliance_matrix()
    requirement_lines = []
    for item in matrix["requirements"]:
        sources = ", ".join(f"`{source_id}`" for source_id in item["source_card_ids"])
        controls = "; ".join(item["implemented_controls"])
        evidence = ", ".join(f"`{path}`" for path in item["verification_evidence"])
        requirement_lines.extend(
            [
                f"## {item['requirement_id']}",
                "",
                f"- Domain: {item['domain']}",
                f"- Risk: {item['risk_level']}",
                f"- Reviewers: {', '.join(item['authority_reviewers'])}",
                f"- Sources: {sources}",
                f"- Product rule: {item['product_rule']}",
                f"- Controls: {controls}",
                f"- Evidence: {evidence}",
                f"- Blocked use: {', '.join(item['blocked_use'])}",
                "",
            ]
        )
    return (
        "# UniBot Compliance Matrix\n\n"
        f"Status: {matrix['status']}\n\n"
        f"Exam deployment: {matrix['exam_deployment_status']}\n\n"
        f"Requirements: {matrix['requirement_count']}\n\n"
        f"High-risk requirements: {matrix['high_risk_requirement_count']}\n\n"
        f"Missing source cards: {', '.join(matrix['missing_source_card_ids']) or 'none'}\n\n"
        f"Compliance drift alignment: {matrix['compliance_drift_alignment']['status']}\n\n"
        f"Alignment readiness checks: {', '.join(matrix['compliance_drift_alignment']['unique_readiness_check_ids'])}\n\n"
        "Boundary: authority review matrix only, not legal advice or exam clearance.\n\n"
        + "\n".join(requirement_lines)
    ).rstrip() + "\n"
