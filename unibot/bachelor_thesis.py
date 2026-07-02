from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text
from .source_cards import build_source_card_drift_report, get_source_card


BACHELOR_THESIS_SCHEMA_VERSION = "unibot-gretel-bachelor-thesis-package-v1"


def build_bachelor_thesis_evidence_index() -> dict[str, Any]:
    source_drift = build_source_card_drift_report()
    evidence_items = [
        {
            "claim_id": "gretel_authorship_label",
            "claim": "The public UniBot package is labelled as built and documented by Gretel, not Julius.",
            "evidence_type": "package_field_and_test",
            "artifact_refs": ["unibot/bachelor_thesis.py", "tests/test_unibot_bachelor_thesis.py"],
            "readiness_check_ids": ["gretel_bachelor_thesis_package"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_bachelor_thesis.py -q"],
            "source_card_ids": [],
            "human_gate": "human_submission_review_required",
        },
        {
            "claim_id": "glm_52_basis",
            "claim": "GLM-5.2 is the primary public-safe proposal model basis, with provider calls disabled by default.",
            "evidence_type": "source_cards_and_review_gate",
            "artifact_refs": [
                "unibot/bachelor_thesis.py",
                "unibot/gretel_glm_evolve.py",
                "docs/unibot/UNIBOT_GRETEL_GLM_EVOLVE_LANE.md",
            ],
            "readiness_check_ids": ["gretel_glm_evolve_lane", "gretel_bachelor_thesis_package"],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_bachelor_thesis.py tests/test_unibot_gretel_glm_evolve.py -q"
            ],
            "source_card_ids": ["zai-glm-52", "zai-glm-52-migration", "zai-glm-pricing"],
            "human_gate": "provider_call_requires_explicit_go_and_redaction_receipt",
        },
        {
            "claim_id": "source_bound_public_science",
            "claim": "Scientific and university-facing claims are anchored to required public source cards.",
            "evidence_type": "source_card_drift_report",
            "artifact_refs": ["unibot/source_cards.py", "unibot/readiness.py", "docs/unibot/UNIBOT_READINESS_CHECK.md"],
            "readiness_check_ids": ["source_cards", "source_card_drift_guard"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_api_and_public_safety.py tests/test_unibot_readiness.py -q"],
            "source_card_ids": ["dfg-gwp", "eu-ai-act-2024", "gdpr-2016-679", "uoc-ki-faq", "zai-glm-52"],
            "human_gate": "human_submission_review_required",
        },
        {
            "claim_id": "public_safety_and_privacy",
            "claim": "The package stays public-safe and blocks local paths, secrets, raw transcripts, private course material, and personal data.",
            "evidence_type": "public_safety_scan",
            "artifact_refs": ["unibot/public_safety.py", "tests/test_unibot_api_and_public_safety.py"],
            "readiness_check_ids": ["public_safety", "data_protection_screening"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_api_and_public_safety.py tests/test_unibot_privacy.py -q"],
            "source_card_ids": ["gdpr-2016-679", "dsk-ai-privacy-2024", "chrome-limited-use"],
            "human_gate": "public_safety_required",
        },
        {
            "claim_id": "exam_boundary_not_clearance",
            "claim": "UniBot is a practice and review system, not exam clearance, grading, proctoring, or AI-detection evidence.",
            "evidence_type": "readiness_and_publication_gate",
            "artifact_refs": ["unibot/publication.py", "unibot/readiness.py", "unibot/compliance.py"],
            "readiness_check_ids": ["exam_boundary", "publication_package", "compliance_matrix"],
            "acceptance_tests": ["python3 -m pytest tests/test_unibot_publication.py tests/test_unibot_compliance.py -q"],
            "source_card_ids": ["hg-nrw-64", "uoc-hilfsmittel", "uoc-ki-faq", "eu-ai-act-2024"],
            "human_gate": "written_university_clearance_required_before_exam_use",
        },
        {
            "claim_id": "reproducible_evaluation_package",
            "claim": "Synthetic tasks, red-team checks, readiness, and publication gates make the research package reproducible.",
            "evidence_type": "test_and_readiness_suite",
            "artifact_refs": ["unibot/evaluation.py", "unibot/redteam.py", "unibot/readiness.py", "unibot/publication.py"],
            "readiness_check_ids": ["evaluation_packet", "redteam", "publication_package"],
            "acceptance_tests": [
                "python3 -m pytest tests/test_unibot_evaluation.py tests/test_unibot_redteam.py tests/test_unibot_publication.py -q"
            ],
            "source_card_ids": ["openai-evals", "dfg-gwp", "vanlehn-2011", "kulik-fletcher-2016"],
            "human_gate": "human_submission_review_required",
        },
    ]
    index = {
        "schema_version": "unibot-gretel-bachelor-thesis-evidence-index-v1",
        "status": "ready",
        "source_card_drift_status": source_drift["status"],
        "source_card_drift_public_safety_status": source_drift["public_safety_status"],
        "source_card_count": source_drift["card_count"],
        "required_source_card_count": source_drift["required_source_card_count"],
        "claim_count": len(evidence_items),
        "evidence_items": evidence_items,
        "required_readiness_check_ids": sorted(
            {check_id for item in evidence_items for check_id in item["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({item["human_gate"] for item in evidence_items}),
        "policy": (
            "Bachelor-thesis-level claims remain draft claims unless their evidence item has tests, readiness checks, "
            "source-card anchors where applicable, and a human gate for real submission or exam use."
        ),
    }
    scan = scan_text(json.dumps(index, ensure_ascii=False), "unibot-gretel-bachelor-thesis-evidence-index")
    index["public_safety_status"] = scan["status"]
    if scan["status"] != "pass" or source_drift["status"] != "pass":
        index["status"] = "blocked"
    return index


def build_bachelor_thesis_package() -> dict[str, Any]:
    package = {
        "schema_version": BACHELOR_THESIS_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "public_scientific_draft_bachelor_thesis_level_not_real_submission",
        "title": "UniBot Guardian: A Gretel-Built GLM-Ready Socratic Integrity Layer for Coding-Practice Workflows",
        "submission_type": "bachelor_thesis_level_research_package_not_real_university_submission",
        "level_statement": (
            "Bachelor thesis level means academic rigor, transparent method, reproducible documentation, "
            "and reviewability; it does not mean this artifact is a real university thesis submission."
        ),
        "authorship_statement": {
            "builder": "Gretel",
            "documentation_author": "Gretel",
            "programmer_claim": "This public package is labelled as built and documented by Gretel, not by Julius.",
            "human_role": "Julius or another human reviewer remains the review, ethics, legal, and real submission gate.",
            "institutional_status": "not a real thesis submission and not institutionally approved by this artifact",
        },
        "glm_technology_basis": {
            "primary_model_hint": "zai/glm-5.2",
            "provider": "Z.AI",
            "use_mode": "redacted proposal, architecture, harness, and documentation review",
            "provider_call_default": "disabled",
            "reason": "GLM-5.2 is treated as the long-context coding proposal model for public-safe UniBot work packets.",
            "official_source_card_ids": ["zai-glm-52", "zai-glm-52-migration", "zai-glm-pricing"],
            "verified_on": "2026-07-02",
        },
        "research_question": (
            "How can a public, source-bound AI practice layer support coding learners without replacing "
            "their own work, leaking private material, or claiming exam clearance?"
        ),
        "scientific_contribution": [
            "A Socratic integrity layer that blocks final-answer outsourcing while preserving learner reflection.",
            "A public-safety scanner for paths, secrets, personal data, raw AI transcripts, and private course references.",
            "A reproducible publication and readiness package based on synthetic tasks and source cards.",
            "A GLM-5.2-ready proposal lane that turns model ideas into tests, review entries, or blocked reasons.",
            "A clear exam boundary: practice and review are supported; official grading, proctoring, and exam clearance are blocked.",
        ],
        "methodology": [
            "Three Golden Rules define allowed and blocked learning support.",
            "Public source cards anchor legal, institutional, privacy, technical, and educational claims.",
            "Synthetic scenarios and red-team checks test likely failure modes.",
            "Readiness and publication gates require public-safety pass results before public release.",
            "Accepted improvements must be converted into regression tests, red-team cases, documentation, or review-board decisions.",
        ],
        "implementation_scope": {
            "package": "unibot",
            "public_api_root": "/api/unibot",
            "primary_modules": [
                "unibot/guardian.py",
                "unibot/public_safety.py",
                "unibot/gretel_glm_evolve.py",
                "unibot/publication.py",
                "unibot/readiness.py",
                "unibot/bachelor_thesis.py",
            ],
            "public_docs": [
                "docs/unibot/UNIBOT_GOLDEN_RULES.md",
                "docs/unibot/UNIBOT_PIPELINE.md",
                "docs/unibot/UNIBOT_GRETEL_GLM_EVOLVE_LANE.md",
                "docs/unibot/UNIBOT_GRETEL_BACHELOR_THESIS_PACKAGE.md",
                "docs/unibot/UNIBOT_PUBLICATION_PACKAGE.md",
                "docs/unibot/UNIBOT_READINESS_CHECK.md",
            ],
        },
        "deliverables": [
            "Public Python package",
            "Local API",
            "Synthetic evaluation and red-team tests",
            "Publication package",
            "Readiness report",
            "Review-board and authority handoff drafts",
            "Gretel/GLM proposal lane",
            "Bachelor-thesis-style documentation package",
        ],
        "review_gates": {
            "public_safety_required": True,
            "written_university_clearance_required_before_exam_use": True,
            "human_submission_review_required": True,
            "no_autonomous_github_publish": True,
            "no_final_go_by_gretel_or_glm": True,
            "provider_call_requires_explicit_go_and_redaction_receipt": True,
        },
        "release_boundaries": {
            "ready_for": ["public code review", "bachelor-thesis-level supervision discussion", "local practice demo"],
            "not_ready_for": ["real university thesis submission without human review", "exam deployment", "grading", "proctoring", "AI-detection evidence"],
        },
    }
    package["evidence_index"] = build_bachelor_thesis_evidence_index()
    package["source_cards"] = [
        card for card in (get_source_card(source_id) for source_id in package["glm_technology_basis"]["official_source_card_ids"]) if card
    ]
    package["receipt"] = build_bachelor_thesis_receipt(package)
    scan = scan_text(json.dumps(package, ensure_ascii=False), "unibot-gretel-bachelor-thesis-package")
    package["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        package["status"] = "blocked_public_safety"
        package["public_safety_findings"] = scan["findings"]
    return package


def build_bachelor_thesis_receipt(package: dict[str, Any]) -> dict[str, Any]:
    hashed = {key: value for key, value in package.items() if key not in {"generated_at_utc", "receipt"}}
    payload = json.dumps(hashed, sort_keys=True, ensure_ascii=False)
    return {
        "schema_version": "unibot-gretel-bachelor-thesis-receipt-v1",
        "package_hash": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "builder": package["authorship_statement"]["builder"],
        "model_hint": package["glm_technology_basis"]["primary_model_hint"],
        "provider_call_executed": False,
        "public_release_only_after_scan": True,
        "human_review_required": True,
    }


def build_bachelor_thesis_markdown() -> str:
    package = build_bachelor_thesis_package()
    contribution_lines = "\n".join(f"- {item}" for item in package["scientific_contribution"])
    method_lines = "\n".join(f"- {item}" for item in package["methodology"])
    deliverable_lines = "\n".join(f"- {item}" for item in package["deliverables"])
    ready_lines = "\n".join(f"- {item}" for item in package["release_boundaries"]["ready_for"])
    not_ready_lines = "\n".join(f"- {item}" for item in package["release_boundaries"]["not_ready_for"])
    evidence_lines = "\n".join(
        f"- `{item['claim_id']}`: {item['evidence_type']} via {', '.join(item['readiness_check_ids'])}"
        for item in package["evidence_index"]["evidence_items"]
    )
    return (
        "# UniBot Gretel Bachelor-Thesis-Level Package\n\n"
        f"Status: {package['status']}\n\n"
        f"Title: {package['title']}\n\n"
        f"Level statement: {package['level_statement']}\n\n"
        "## Authorship\n\n"
        f"- Builder: {package['authorship_statement']['builder']}\n"
        f"- Documentation author: {package['authorship_statement']['documentation_author']}\n"
        f"- Programmer claim: {package['authorship_statement']['programmer_claim']}\n"
        f"- Human role: {package['authorship_statement']['human_role']}\n\n"
        "## GLM Basis\n\n"
        f"- Model hint: {package['glm_technology_basis']['primary_model_hint']}\n"
        f"- Provider: {package['glm_technology_basis']['provider']}\n"
        f"- Use mode: {package['glm_technology_basis']['use_mode']}\n"
        f"- Provider call default: {package['glm_technology_basis']['provider_call_default']}\n\n"
        "## Research Question\n\n"
        f"{package['research_question']}\n\n"
        "## Scientific Contribution\n\n"
        f"{contribution_lines}\n\n"
        "## Methodology\n\n"
        f"{method_lines}\n\n"
        "## Deliverables\n\n"
        f"{deliverable_lines}\n\n"
        "## Evidence Index\n\n"
        f"- Status: {package['evidence_index']['status']}\n"
        f"- Claims: {package['evidence_index']['claim_count']}\n"
        f"- Source-card drift: {package['evidence_index']['source_card_drift_status']}\n\n"
        f"{evidence_lines}\n\n"
        "## Ready For\n\n"
        f"{ready_lines}\n\n"
        "## Not Ready For\n\n"
        f"{not_ready_lines}\n\n"
        "## Receipt\n\n"
        f"- Package hash: {package['receipt']['package_hash']}\n"
        f"- Public safety: {package['public_safety_status']}\n"
        f"- Human review required: {package['receipt']['human_review_required']}\n"
    )
