from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .public_safety import scan_text


GLM_EVOLVE_SCHEMA_VERSION = "unibot-gretel-glm-evolve-v1"
GLM_EVOLVE_MODEL_HINT = "zai/glm-5.2"
GLM_RSI_WORKBOARD_SCHEMA_VERSION = "unibot-gretel-glm-rsi-workboard-v1"


PUBLIC_UNIBOT_DOCS = [
    "README.md",
    "docs/unibot/UNIBOT_GOLDEN_RULES.md",
    "docs/unibot/UNIBOT_PIPELINE.md",
    "docs/unibot/UNIBOT_GRETEL_LOOP_PLAN.md",
    "docs/unibot/UNIBOT_THREAT_MODEL.md",
    "docs/unibot/UNIBOT_COMPLIANCE_MATRIX.md",
    "docs/unibot/UNIBOT_PUBLICATION_PACKAGE.md",
    "docs/unibot/UNIBOT_READINESS_CHECK.md",
    "docs/unibot/UNIBOT_RELEASE_RUNBOOK.md",
    "docs/unibot/UNIBOT_GRETEL_BACHELOR_THESIS_PACKAGE.md",
    "docs/unibot/UNIBOT_SOURCE_CARDS.md",
]


PUBLIC_UNIBOT_CODE_SURFACES = [
    "unibot/guardian.py",
    "unibot/public_safety.py",
    "unibot/source_cards.py",
    "unibot/simulation_loop.py",
    "unibot/loop_lab.py",
    "unibot/evaluation.py",
    "unibot/publication.py",
    "unibot/readiness.py",
    "unibot/server.py",
]


def build_public_knowledge_inventory() -> dict[str, Any]:
    return {
        "status": "ready",
        "scope": "public UniBot Guardian knowledge only",
        "project_summary": (
            "UniBot is a separate Socratic Integrity Layer for coding-practice workflows. "
            "It supports practice overlays, private self-tests, source-grounded tutor drills, "
            "red-team checks, publication packets, and authority-review drafts; it is not "
            "an exam-clearance, grading, proctoring, or KI-detection system."
        ),
        "golden_rules": [
            {
                "rule_id": "GR1",
                "short": "Keine finale Loesung",
                "testable_invariant": "Final answers, complete code fixes, inserted values, and final interpretations are blocked.",
            },
            {
                "rule_id": "GR2",
                "short": "Keine privaten oder sensiblen Daten",
                "testable_invariant": "Public artifacts contain no personal data, private course material, local paths, credentials, or raw model transcripts.",
            },
            {
                "rule_id": "GR3",
                "short": "Eigenleistung sichtbar halten",
                "testable_invariant": "Allowed help preserves the learner attempt, next step, reflection, help level, and source boundary.",
            },
        ],
        "scientific_controls": [
            "source cards with source type, authority type, product rule, risk level, and last-checked date",
            "fixed synthetic scenarios and red-team smoke cases",
            "public-safety scan before publication",
            "readiness check with explicit not-cleared exam boundary",
            "publication package with system card, data card, limitations, compliance, pilot, privacy, and review-board packets",
            "manual-review gates for GitHub issues and public release",
        ],
        "public_docs": PUBLIC_UNIBOT_DOCS,
        "public_code_surfaces": PUBLIC_UNIBOT_CODE_SURFACES,
        "public_test_surfaces": [
            "tests/test_unibot_api_and_public_safety.py",
            "tests/test_unibot_gretel_loop.py",
            "tests/test_unibot_publication.py",
            "tests/test_unibot_readiness.py",
            "tests/test_unibot_redteam.py",
        ],
    }


def build_glm_evolve_work_packet(
    *,
    work_id: str = "unibot-open-science-gretel-glm-evolve-v1",
    task_kind: str = "architecture_and_harness_proposal",
    model_hint: str = GLM_EVOLVE_MODEL_HINT,
) -> dict[str, Any]:
    packet = {
        "schema_version": GLM_EVOLVE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "work_id": work_id,
        "domain": "unibot_guardian_open_science",
        "task_kind": task_kind,
        "status": "prepared_no_provider_call",
        "route": "proposal_only_requires_codex_and_human_review",
        "model_hint": model_hint,
        "provider_call_executed": False,
        "raw_private_context_shared": False,
        "autonomous_apply": False,
        "external_actions_allowed": [],
        "redaction_level": "public_safe_metadata_and_small_non_private_snippets_only",
        "allowed_context": [
            "public UniBot docs",
            "public-safe module and test names",
            "synthetic scenarios",
            "source-card identifiers and URLs",
            "aggregate test status",
            "non-private patch outlines",
        ],
        "blocked_context": [
            "private course files",
            "mailbox exports",
            "real exam notebooks or solution keys",
            "personal data",
            "health or accommodation records",
            "local filesystem details",
            "credentials",
            "raw model transcripts",
            "confidential Gretel or FM case material",
        ],
        "knowledge_inventory": build_public_knowledge_inventory(),
        "request_to_gretel_glm": {
            "role": "proposal reviewer only",
            "ask": (
                "Propose the smallest safe code and documentation improvements that make UniBot easier "
                "for scientists to reproduce, audit, test, and extend on GitHub while preserving the three Golden Rules."
            ),
            "required_output_fields": [
                "problem_understanding",
                "patch_outline",
                "test_plan",
                "risk_flags",
                "scientific_rigor_notes",
                "generalization_rule",
                "confidence",
                "blocked_reason_if_any",
            ],
            "must_not": [
                "apply code",
                "send messages",
                "publish to GitHub",
                "claim exam clearance",
                "request private context",
                "include raw private content",
            ],
        },
        "next_safe_chunks": [
            {
                "chunk_id": "public_repo_governance",
                "goal": "Add license, contribution, security, and public-science collaboration docs.",
                "acceptance": "Docs explain public-only collaboration, manual review, no exam clearance, and leak boundaries.",
            },
            {
                "chunk_id": "glm_proposal_lane",
                "goal": "Keep GLM as a redacted proposal lane that emits plans, tests, risks, and confidence only.",
                "acceptance": "No provider call is performed by default; proposals are blocked if they request apply/send/final decisions.",
            },
            {
                "chunk_id": "harness_generalization",
                "goal": "Turn every accepted or rejected model idea into a regression fixture or a documented blocked reason.",
                "acceptance": "Readiness includes the lane and public-safety scan still passes.",
            },
            {
                "chunk_id": "open_science_evidence",
                "goal": "Expose source-tiering, reproducibility, limitations, and evaluation design for outside scientists.",
                "acceptance": "Publication package includes the open-science evolve lane without private data.",
            },
        ],
    }
    packet["receipt"] = build_glm_evolve_receipt(packet)
    scan = scan_text(json.dumps(packet, ensure_ascii=False), "unibot-gretel-glm-evolve-work-packet")
    packet["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        packet["status"] = "blocked_public_safety"
        packet["public_safety_findings"] = scan["findings"]
    return packet


def build_glm_evolve_receipt(packet: dict[str, Any], *, outcome: str = "prepared_no_provider_call") -> dict[str, Any]:
    hashed_packet = {key: value for key, value in packet.items() if key not in {"generated_at_utc", "receipt"}}
    payload = json.dumps(hashed_packet, sort_keys=True, ensure_ascii=False)
    return {
        "schema_version": "unibot-gretel-glm-evolve-receipt-v1",
        "work_id": str(packet.get("work_id", "")),
        "packet_hash": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "model_hint": str(packet.get("model_hint", GLM_EVOLVE_MODEL_HINT)),
        "provider_call_executed": bool(packet.get("provider_call_executed", False)),
        "raw_private_context_shared": bool(packet.get("raw_private_context_shared", False)),
        "autonomous_apply": bool(packet.get("autonomous_apply", False)),
        "outcome": outcome,
        "next_local_action": "codex_review_then_tests_before_any_provider_call_or_patch_application",
    }


def validate_glm_evolve_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proposal, dict):
        return {"status": "blocked", "blocked_reason": "invalid_proposal_type"}
    blockers = []
    if proposal.get("autonomous_apply") is True:
        blockers.append("autonomous_apply_requested")
    if proposal.get("raw_private_context_shared") is True:
        blockers.append("raw_private_context_requested_or_shared")
    if proposal.get("final_go") is True:
        blockers.append("final_go_requested")
    requested_actions = proposal.get("external_actions", [])
    if requested_actions and not isinstance(requested_actions, list):
        blockers.append("invalid_external_actions")
    elif requested_actions:
        blockers.append("external_actions_requested")
    text_scan = scan_text(json.dumps(proposal, ensure_ascii=False), "unibot-gretel-glm-evolve-proposal")
    if text_scan["status"] != "pass":
        blockers.append("public_safety_scan_failed")
    required = {"recommendation", "patch_outline", "test_plan", "risk_flags", "confidence"}
    missing = sorted(required - set(proposal.keys()))
    if missing:
        blockers.append("missing_required_fields")
    return {
        "schema_version": "unibot-gretel-glm-evolve-proposal-validation-v1",
        "status": "blocked" if blockers else "ok",
        "blockers": blockers,
        "missing_fields": missing,
        "public_safety_status": text_scan["status"],
        "public_safety_findings": text_scan.get("findings", []),
        "review_policy": "proposal_only_codex_and_human_review_required",
    }


def build_glm_rsi_workboard(
    *,
    work_id: str = "unibot-glm-rsi-open-science-workboard-v1",
    include_blocked_fixture: bool = True,
) -> dict[str, Any]:
    base_packet = build_glm_evolve_work_packet(work_id=work_id)
    items = [
        {
            "work_id_hash": hashlib.sha256(work_id.encode("utf-8")).hexdigest()[:16],
            "domain": "unibot_guardian_open_science",
            "task_kind": "unibot_open_science_harness",
            "status": "waiting_julius_go",
            "model_hint": GLM_EVOLVE_MODEL_HINT,
            "why_glm_needed": "long-horizon architecture, harness and documentation proposal for public scientific collaboration",
            "redaction_level": "public_safe_metadata_only",
            "standards_gates": ["3gr", "fa_level", "netcheck", "open_science", "local_first", "redaction", "harness", "codex_review", "julius_go_required", "no_final_go"],
            "harness_refs": ["tests/test_unibot_gretel_glm_evolve.py"],
            "review_decision": "waiting_explicit_julius_go_for_provider_call",
            "visible_status": "UniBot GLM-RSI work packet is prepared; no provider call has run.",
            "next_local_action": "Codex reviews proposal packet, then focused tests before any implementation or provider call.",
            "harvest_category": "review_board_entry",
            "provider_call_executed": False,
            "provider_call_allowed_now": False,
            "raw_content_shared": False,
            "autonomous_apply": False,
            "final_go": False,
        },
        {
            "work_id_hash": hashlib.sha256(b"unibot-routine-local-first").hexdigest()[:16],
            "domain": "unibot_guardian_open_science",
            "task_kind": "routine_status",
            "status": "local_analysis_first",
            "model_hint": "local_deterministic_first",
            "why_glm_needed": "not_needed_for_routine_status",
            "redaction_level": "metadata_only",
            "standards_gates": ["local_first", "redaction", "harness"],
            "harness_refs": [],
            "review_decision": "not_needed",
            "visible_status": "Routine UniBot status stays local-first.",
            "next_local_action": "Use public-safe local tests and docs checks.",
            "harvest_category": "",
            "provider_call_executed": False,
            "provider_call_allowed_now": False,
            "raw_content_shared": False,
            "autonomous_apply": False,
            "final_go": False,
        },
    ]
    if include_blocked_fixture:
        items.append(
            {
                "work_id_hash": hashlib.sha256(b"unibot-unsafe-context-fixture").hexdigest()[:16],
                "domain": "unibot_guardian_open_science",
                "task_kind": "unsafe_context_fixture",
                "status": "blocked",
                "model_hint": GLM_EVOLVE_MODEL_HINT,
                "why_glm_needed": "blocked until private or raw context is replaced by public-safe hashes and labels",
                "redaction_level": "metadata_only",
                "standards_gates": ["redaction", "harness", "codex_review", "no_final_go"],
                "harness_refs": ["tests/test_unibot_gretel_glm_evolve.py"],
                "review_decision": "blocked_by_redaction_policy",
                "visible_status": "Blocked fixture: unsafe raw context must never enter a GLM prompt.",
                "next_local_action": "Prepare a public-safe replacement packet if this case becomes real.",
                "harvest_category": "documented_blocker",
                "provider_call_executed": False,
                "provider_call_allowed_now": False,
                "raw_content_shared": False,
                "autonomous_apply": False,
                "final_go": False,
            }
        )
    counts: dict[str, int] = {}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    payload = {
        "schema_version": GLM_RSI_WORKBOARD_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "visible",
        "active_item_count": len([item for item in items if item["status"] not in {"closed_harnessed", "rejected_with_reason"}]),
        "blocked_item_count": counts.get("blocked", 0),
        "closed_harnessed_count": counts.get("closed_harnessed", 0),
        "status_counts": counts,
        "items": items,
        "source_packet_hash": base_packet["receipt"]["packet_hash"],
        "policy": "GLM may propose only; Codex and human review remain apply, send, publish and release gates.",
        "visibility_surfaces": {
            "api": "/api/unibot/gretel-glm-evolve/workboard",
            "markdown": "/api/unibot/gretel-glm-evolve/markdown",
            "chrome_extension_dependency": False,
        },
        "privacy": {
            "raw_text_stored": False,
            "raw_chat_id_stored": False,
            "tokens_stored": False,
            "private_paths_stored": False,
            "raw_model_transcripts_stored": False,
        },
        "safety": {
            "provider_call_executed": False,
            "provider_call_allowed_now": False,
            "autonomous_apply": False,
            "external_actions": [],
            "github_publish": False,
            "final_go": False,
        },
    }
    scan = scan_text(json.dumps(payload, ensure_ascii=False), "unibot-gretel-glm-rsi-workboard")
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["status"] = "blocked_public_safety"
        payload["public_safety_findings"] = scan.get("findings", [])
    return payload


def build_glm_evolve_markdown() -> str:
    packet = build_glm_evolve_work_packet()
    workboard = build_glm_rsi_workboard()
    chunks = "\n".join(
        f"- `{chunk['chunk_id']}`: {chunk['goal']} Acceptance: {chunk['acceptance']}"
        for chunk in packet["next_safe_chunks"]
    )
    rules = "\n".join(
        f"- `{rule['rule_id']}` {rule['short']}: {rule['testable_invariant']}"
        for rule in packet["knowledge_inventory"]["golden_rules"]
    )
    return (
        "# UniBot Gretel GLM Evolve Lane\n\n"
        f"Status: {packet['status']}\n\n"
        f"Model hint: `{packet['model_hint']}`\n\n"
        f"Provider call executed: {packet['provider_call_executed']}\n\n"
        f"Route: {packet['route']}\n\n"
        "## GLM-RSI Workboard\n\n"
        f"- Status: `{workboard['status']}`\n"
        f"- Active items: `{workboard['active_item_count']}`\n"
        f"- Blocked items: `{workboard['blocked_item_count']}`\n"
        f"- Provider call allowed now: `{workboard['safety']['provider_call_allowed_now']}`\n\n"
        "## Golden Rules\n\n"
        f"{rules}\n\n"
        "## Next Safe Chunks\n\n"
        f"{chunks}\n\n"
        "Policy: GLM may propose plans, tests, risks, and patch outlines only. "
        "Codex and a human reviewer remain the apply and release gate.\n"
    )
