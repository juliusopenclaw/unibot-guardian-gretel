from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text
from .source_cards import get_source_card


BACHELOR_THESIS_SCHEMA_VERSION = "unibot-gretel-bachelor-thesis-package-v1"


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
        "## Ready For\n\n"
        f"{ready_lines}\n\n"
        "## Not Ready For\n\n"
        f"{not_ready_lines}\n\n"
        "## Receipt\n\n"
        f"- Package hash: {package['receipt']['package_hash']}\n"
        f"- Public safety: {package['public_safety_status']}\n"
        f"- Human review required: {package['receipt']['human_review_required']}\n"
    )
