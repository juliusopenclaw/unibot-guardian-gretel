from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from .course_tutor import (
    DEFAULT_COURSE_ID,
    COURSE_MATERIAL_ROOT_ENV,
    build_course_exam_scope,
    build_course_material_compiler_plan,
    safe_course_id,
)
from .public_safety import scan_text
from .source_cards import list_source_cards


ORCHESTRATION_SCHEMA_VERSION = "unibot-orchestration-v1"

PROJECT_MANAGEMENT_GOLDEN_RULES = [
    {
        "rule_id": "PM-GR1",
        "name": "Generalisieren",
        "contract": "Every useful case workflow becomes a reusable UniBot capability, not a one-off chat artifact.",
    },
    {
        "rule_id": "PM-GR2",
        "name": "Harness Engineering",
        "contract": "Every important workflow needs a runnable harness, metrics, logs, and regression checks.",
    },
    {
        "rule_id": "PM-GR3",
        "name": "Recursive Self-Improvement",
        "contract": "Recurring mistakes become tests, rubric updates, prompt changes, metrics, or backlog tasks.",
    },
]

SAFETY_GOLDEN_RULES = [
    {
        "rule_id": "GR1",
        "name": "Keine finale Loesung",
        "contract": "Do not pass through final solutions, complete code fixes, inserted values, or final interpretations.",
    },
    {
        "rule_id": "GR2",
        "name": "Keine privaten oder sensiblen Daten",
        "contract": "Block or redact private data, health/accommodation details, local paths, secrets, raw AI transcripts, and private course text.",
    },
    {
        "rule_id": "GR3",
        "name": "Eigenleistung sichtbar halten",
        "contract": "Preserve own attempt, next step, reflection, help level, and source boundary without automatic grading.",
    },
]

ROLE_LANES = [
    {
        "role_id": "policy_basis",
        "label": "Policy and Evidence",
        "mission": "Keep public line, source cards, authority rationale, and non-goals consistent.",
        "done_signal": "source-backed public-safe rationale with no official-clearance claim",
    },
    {
        "role_id": "course_material_pipeline",
        "label": "Course Material Pipeline",
        "mission": "Turn local slides, notebooks, videos, transcripts, and data into reviewed source metadata and queues.",
        "done_signal": "compiler plan, source-card work queue, quarantine list, and exam-scope inputs are updated",
    },
    {
        "role_id": "exam_gateway",
        "label": "Exam Gateway",
        "mission": "Maintain the controlled A0-A2 notebook gateway, ledger, freeze, and export package.",
        "done_signal": "gateway E2E passes and exam deployment remains not_cleared",
    },
    {
        "role_id": "tutor_rag",
        "label": "Tutor/RAG",
        "mission": "Make course-specific tutoring source-grounded, Socratic, and exact to the exam scope.",
        "done_signal": "tutor answers cite reviewed course anchors and refuse unanchored claims",
    },
    {
        "role_id": "ui_gretel_orbit",
        "label": "Gretel Orbit evolved UI",
        "mission": "Deliver a direct workbench UI: notebook main stage, tutor sidecar, ledger/status layer.",
        "done_signal": "desktop/mobile screenshots show no overflow and no landing-page detour",
    },
    {
        "role_id": "qa_redteam",
        "label": "QA and Red-Team",
        "mission": "Run smoke, unit, red-team, loop, public-safety, and regression checks.",
        "done_signal": "pipeline is green with public-safety 0 findings",
    },
    {
        "role_id": "stakeholder_packet",
        "label": "Stakeholder Packet",
        "mission": "Prepare reviewer-specific packets for exam office, inclusion office, privacy, IT/SZI, and module owner.",
        "done_signal": "review-board packet is public-safe and lists open decisions instead of claiming approval",
    },
]

SPRINT_SEQUENCE = [
    "P0 Command Center and status board",
    "P0 Safety baseline and public-language lock",
    "P1 Course Material Compiler and ExamScopeMap",
    "P1 Tutor usability with source-grounded microtasks",
    "P1 Exam Gateway API and Help Ledger export",
    "P1 Local Cycle Readiness Review and confirmation routing",
    "P1 Readiness handoff and operator-run prefill",
    "P1 Local Cycle Operator Workspace Card and manual cycle preview",
    "P1 Local Cycle Chain Snapshot and evidence-chain preview",
    "P1 Manual Confirmation Console for local cycle stop-go review",
    "P1 Manual Cycle Launch Receipt for final local-cycle stop-go evidence",
    "P1 Manual Cycle Evidence Binder for hash-only pre/post cycle review",
    "P1 Manual Post-Cycle Receipt Intake for human-run hash evidence",
    "P1 Manual Cycle Closure Ledger for hash-only cycle closure",
    "P1 Manual Cycle Review Timeline for chronological hash review",
    "P1 Manual Cycle Review Packet for compact human review",
    "P1 Manual Review Export Preview without export write",
    "P1 Manual Review Export Authorization Gate before export review",
    "P1 Manual Export Review Queue for hash-only candidate review",
    "P1 Manual Export Reviewer Packet for human review",
    "P1 Manual Archive Decision Draft without archive or submission",
    "P1 Manual Final Review Handoff before any export archive or submission",
    "P1 Manual Final Review Receipt Ledger for chronological hash review",
    "P1 Final Review Ledger Integrity Gate before export archive or submission proximity",
    "P1 Final Manual Review Console for one human-readable hash-only view",
    "P1 Final Manual Review Action Lock before export archive or submission proximity",
    "P1 Locked Final Review Board for one final human hash-only review",
    "P1 Locked Final Review Gap Resolver for one safe human follow-up",
    "P1 Full Local Rehearsal Pack for end-to-end Python exam dry-run review",
    "P1 Rehearsal Playback Gap Coach for safe next-action selection",
    "P1 Gap-Coach Guided Rehearsal Loop for next-step preparation",
    "P1 Guided Loop Control Surface for visible next-click review",
    "P2 Gretel Orbit evolved workbench UI",
    "P2 Stakeholder/authority packet",
    "P3 live integrations after explicit go/no-go gates",
]


def build_unibot_command_center(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    review_policy: str | None = None,
    public_safe: bool = True,
) -> dict[str, Any]:
    effective_review_policy = resolve_review_policy(base_path=base_path, review_policy=review_policy)
    compiler = build_course_material_compiler_plan(
        course_id,
        base_path=base_path,
        review_policy=effective_review_policy,
        public_safe=public_safe,
    )
    scope = build_course_exam_scope(
        course_id,
        base_path=base_path,
        review_policy=effective_review_policy,
        public_safe=public_safe,
    )
    source_cards = list_source_cards()
    high_risk_cards = [card for card in source_cards if card.get("risk_level") == "high"]
    ready_skill_count = len([skill for skill in scope.get("skills", []) if skill.get("readiness") == "ready_for_private_tutor"])
    needs_review_skill_count = len([skill for skill in scope.get("skills", []) if skill.get("readiness") == "needs_review"])

    packet = {
        "schema_version": ORCHESTRATION_SCHEMA_VERSION,
        "artifact_type": "unibot_orchestration_command_center",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready_to_orchestrate",
        "course_id": safe_course_id(course_id),
        "canonical_hub": {
            "label": "local UniBot project root",
            "rule": "older chats and workbench artifacts are evidence inputs; implementation merges through this hub only",
            "public_path_policy": "do not expose local absolute paths in public packets",
        },
        "deployment_line": {
            "public_draft_status": "public_draft_ready",
            "exam_deployment_status": "not_cleared",
            "real_exam_use": "real_world_clearance_reminder_not_technical_blocker",
            "legal_line": "planning draft, not legal advice and not official clearance",
        },
        "golden_rules": {
            "project_management": PROJECT_MANAGEMENT_GOLDEN_RULES,
            "safety": SAFETY_GOLDEN_RULES,
        },
        "role_lanes": ROLE_LANES,
        "handoff_contract": handoff_contract(),
        "workflow_cycle": [
            "Context Packet",
            "small implementation slice",
            "runnable harness",
            "review and public-safety scan",
            "recursive self-improvement backlog item for recurring failures",
        ],
        "active_harnesses": [
            {
                "harness_id": "course_extraction_batch_receipts",
                "purpose": "plan queued OCR/transcription jobs, prepare selected-batch receipt templates, and aggregate review evidence",
                "sequence": [
                    "POST /api/unibot/course/extraction-batch-plan",
                    "POST /api/unibot/course/extraction-batch-receipt-packet",
                    "POST /api/unibot/course/private-extraction/run-batch",
                    "POST /api/unibot/course/video-transcription/run-batch",
                    "POST /api/unibot/course/extraction-receipt/validate",
                    "POST /api/unibot/course/extraction-receipts/append",
                    "POST /api/unibot/course/extraction-receipts/summary",
                    "POST /api/unibot/course/extraction-deferral/validate",
                    "POST /api/unibot/course/extraction-completion-report",
                    "POST /api/unibot/course/extraction-progress-report",
                    "POST /api/unibot/course/extraction-manifest-update-plan",
                    "POST /api/unibot/course/tutor-coverage-plan",
                    "POST /api/unibot/course/study-session-plan",
                    "POST /api/unibot/course/study-session-receipt/validate",
                    "POST /api/unibot/course/study-session-review-report",
                ],
                "boundary": "metadata-only public packets; local private text/video extraction requires written rights/privacy decision; study receipts store hashes and evidence flags only",
            },
            {
                "harness_id": "external_decision_record_journal",
                "purpose": "validate incoming written authority records into local hash-only evidence for human review gates",
                "sequence": [
                    "POST /api/unibot/stakeholder/decision-state",
                    "POST /api/unibot/stakeholder/decision-record-journal/append",
                    "POST /api/unibot/stakeholder/decision-record-journal/list",
                    "POST /api/unibot/stakeholder/decision-record-journal/summary",
                    "POST /api/unibot/completion-audit",
                ],
                "boundary": "stores scope metadata, hashes, statuses, and gate evidence only; no raw written decisions, no sending, and no exam deployment switch",
            },
            {
                "harness_id": "exam_workspace_run",
                "purpose": "connect controlled notebook work, private tutor sidecar, Help-Ledger evidence, study receipt, and export receipt",
                "sequence": [
                    "POST /api/unibot/course/extraction-manifest/apply-dry-run",
                    "POST /api/unibot/course/tutor-index/dry-run",
                    "POST /api/unibot/course/private-tutor-use-flow/dry-run",
                    "POST /api/unibot/course/material-coverage/run",
                    "POST /api/unibot/course/exam-skill-drilldown",
                    "POST /api/unibot/course/skill-to-workspace-live-flow",
                    "POST /api/unibot/course/skill-to-workspace-session-carryover",
                    "POST /api/unibot/course/python-exam-source-grounded-tutor-drill-pack",
                    "POST /api/unibot/course/python-exam-drill-session-runner",
                    "POST /api/unibot/course/python-exam-drill-session-review-loop",
                    "POST /api/unibot/course/python-exam-drill-loop-control-panel",
                    "POST /api/unibot/course/python-exam-drill-loop-progress-journal",
                    "POST /api/unibot/course/python-exam-resume-launcher",
                    "POST /api/unibot/course/python-exam-active-study-loop-dashboard",
                    "POST /api/unibot/course/python-exam-active-study-guided-runner",
                    "POST /api/unibot/course/python-exam-guided-action-execution-bridge",
                    "POST /api/unibot/course/python-exam-safe-cycle-console",
                    "POST /api/unibot/course/python-exam-safe-cycle-operator-gate",
                    "POST /api/unibot/course/python-exam-operator-gate-decision-receipt",
                    "POST /api/unibot/course/python-exam-local-cycle-start-packet",
                    "POST /api/unibot/course/python-exam-local-cycle-readiness-review",
                    "POST /api/unibot/course/python-exam-local-cycle-readiness-handoff",
                    "POST /api/unibot/course/python-exam-local-cycle-operator-workspace-card",
                    "POST /api/unibot/course/python-exam-local-cycle-chain-snapshot",
                    "POST /api/unibot/course/python-exam-local-cycle-manual-confirmation-console",
                    "POST /api/unibot/course/python-exam-manual-cycle-launch-receipt",
                    "POST /api/unibot/course/python-exam-manual-cycle-evidence-binder",
                    "POST /api/unibot/course/python-exam-manual-post-cycle-receipt-intake",
                    "POST /api/unibot/course/python-exam-manual-cycle-closure-ledger",
                    "POST /api/unibot/course/python-exam-manual-cycle-review-timeline",
                    "POST /api/unibot/course/python-exam-manual-cycle-review-packet",
                    "POST /api/unibot/course/python-exam-manual-review-export-preview",
                    "POST /api/unibot/course/python-exam-manual-review-export-authorization-gate",
                    "POST /api/unibot/course/python-exam-manual-export-review-queue",
                    "POST /api/unibot/course/python-exam-manual-export-reviewer-packet",
                    "POST /api/unibot/course/python-exam-manual-archive-decision-draft",
                    "POST /api/unibot/course/python-exam-manual-final-review-handoff",
                    "POST /api/unibot/course/python-exam-manual-final-review-receipt-ledger",
                    "POST /api/unibot/course/python-exam-final-review-ledger-integrity-gate",
                    "POST /api/unibot/course/python-exam-final-manual-review-console",
                    "POST /api/unibot/course/python-exam-final-manual-review-action-lock",
                    "POST /api/unibot/course/python-exam-locked-final-review-board",
                    "POST /api/unibot/course/python-exam-locked-final-review-gap-resolver",
                    "POST /api/unibot/exam-workspace/notebook-checkpoint/adapt",
                    "POST /api/unibot/exam-workspace/launch-flow/dry-run",
                    "POST /api/unibot/exam-workspace/operator-run",
                    "POST /api/unibot/exam-workspace/session-console",
                    "POST /api/unibot/exam-workspace/run-history-export-review",
                    "POST /api/unibot/course/exam-coverage-dashboard",
                    "POST /api/unibot/course/per-skill-action-router",
                    "POST /api/unibot/course/routed-action-executor",
                    "POST /api/unibot/course/exam-run-packet",
                    "POST /api/unibot/course/exam-packet-timeline",
                    "POST /api/unibot/course/timeline-export-review-packet",
                    "POST /api/unibot/course/timeline-export-receipt-journal/append",
                    "POST /api/unibot/course/timeline-export-receipt-journal/summary",
                    "POST /api/unibot/course/review-chain-integrity-check",
                    "POST /api/unibot/course/python-exam-readiness-console",
                    "POST /api/unibot/course/python-exam-cockpit-flow",
                    "POST /api/unibot/course/python-exam-live-control-surface",
                    "POST /api/unibot/course/python-exam-evidence-export-preview",
                    "POST /api/unibot/course/python-exam-confirmed-local-export-draft",
                    "POST /api/unibot/course/python-exam-draft-package-review-console",
                    "POST /api/unibot/course/python-exam-human-handoff-packet",
                    "POST /api/unibot/course/python-exam-full-local-rehearsal-pack",
                    "POST /api/unibot/course/python-exam-rehearsal-playback-gap-coach",
                    "POST /api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop",
                    "POST /api/unibot/course/python-exam-guided-loop-control-surface",
                    "POST /api/unibot/exam-workspace/run-dry-run",
                ],
                "boundary": "Skill-to-Workspace Live Flow, Skill-to-Workspace Session Carryover, Python Exam Source-Grounded Tutor Drill Pack, Python Exam Drill Session Runner, Python Exam Drill Session Review Loop, Python Exam Drill Loop Control Panel, Python Exam Drill Loop Progress Journal, Python Exam Resume Launcher, Python Exam Active Study Loop Dashboard, Python Exam Active Study Guided Runner, Python Exam Guided Action Execution Bridge, Python Exam Safe Cycle Console, Python Exam Safe Cycle Operator Gate, Python Exam Operator Gate Decision Receipt, Python Exam Local Cycle Start Packet, Python Exam Local Cycle Readiness Review, Python Exam Local Cycle Readiness Handoff, Python Exam Local Cycle Operator Workspace Card, Python Exam Local Cycle Chain Snapshot, Python Exam Manual Confirmation Console, Python Exam Manual Cycle Launch Receipt, Python Exam Manual Cycle Evidence Binder, Python Exam Manual Post-Cycle Receipt Intake, Python Exam Manual Cycle Closure Ledger, Python Exam Manual Cycle Review Timeline, Python Exam Manual Cycle Review Packet, Python Exam Manual Review Export Preview, Python Exam Manual Review Export Authorization Gate, Python Exam Manual Export Review Queue, Python Exam Manual Export Reviewer Packet, Python Exam Manual Archive Decision Draft, Python Exam Manual Final Review Handoff, Python Exam Manual Final Review Receipt Ledger, Python Exam Final Review Ledger Integrity Gate, Python Exam Final Manual Review Console, Python Exam Final Manual Review Action Lock, Python Exam Locked Final Review Board, Python Exam Locked Final Review Gap Resolver, Start Exam Workspace operator run, Session Console, Run-History Export Review, Course Exam Coverage Dashboard, Per-Skill Action Router, Routed Action Executor, Exam Run Packet, Exam Packet Timeline Viewer, Timeline Export Review Packet, Timeline Export Receipt Journal, Review Chain Integrity Check, Python Exam Readiness Console, Python Exam Cockpit Flow, Python Exam Live Control Surface, Python Exam Evidence Export Preview, Python Exam Confirmed Local Export Draft, Python Exam Draft Package Review Console, Python Exam Human Handoff Packet, Python Exam Full Local Rehearsal Pack, Python Exam Rehearsal Playback Gap Coach, Python Exam Gap-Coach Guided Rehearsal Loop, and Python Exam Guided Loop Control Surface are dry-run/metadata-only by default; local notebook cells become hashes only; repeated dry-runs use hash-only receipts; timeline, export-review, progress-journal, resume-launcher, active-study-dashboard, active-study-guided-runner, guided-action-execution-bridge, safe-cycle-console, safe-cycle-operator-gate, operator-gate-decision-receipt, local-cycle-start-packet, local-cycle-readiness-review, local-cycle-readiness-handoff, local-cycle-operator-workspace-card, local-cycle-chain-snapshot, manual-confirmation-console, manual-cycle-launch-receipt, manual-cycle-evidence-binder, manual-post-cycle-receipt-intake, manual-cycle-closure-ledger, manual-cycle-review-timeline, manual-cycle-review-packet, manual-review-export-preview, manual-review-export-authorization-gate, manual-export-review-queue, manual-export-reviewer-packet, manual-archive-decision-draft, manual-final-review-handoff, manual-final-review-receipt-ledger, final-review-ledger-integrity-gate, final-manual-review-console, final-manual-review-action-lock, locked-final-review-board, locked-final-review-gap-resolver, journal, chain-integrity, readiness, cockpit, live-control, evidence-export-preview, tutor-drill-pack, drill-session-runner, drill-session-review-loop, drill-loop-control-panel, local-export-draft, draft-review-console, skill-to-workspace, session-carryover, human-handoff, full-local-rehearsal, playback-gap-coach, guided-rehearsal-loop, and guided-loop-control-surface public outputs are metadata-only; local writes need individual operator confirmations; no raw query, notebook code, private text, local paths, scoring, grading, proctoring, AI detection, or exam clearance",
            }
        ],
        "workstream_sequence": SPRINT_SEQUENCE,
        "material_status": compiler.get("counts", {}),
        "scope_status": {
            "status": scope.get("status"),
            "ready_skill_count": ready_skill_count,
            "needs_review_skill_count": needs_review_skill_count,
            "exam_deployment_status": scope.get("exam_deployment_status"),
        },
        "source_evidence": {
            "source_card_count": len(source_cards),
            "high_risk_source_card_count": len(high_risk_cards),
            "net_check_basis": [
                "uoc-ki-faq",
                "eu-ai-act-2024",
                "jupyter-ai",
                "google-colab-gemini",
                "dfg-gwp",
                "vanlehn-2011",
            ],
        },
        "acceptance_gates": [
            "pipeline smoke passes",
            "unit tests pass before milestone handoff",
            "public-safety scan has zero findings for public artifacts",
            "red-team, loop lab, and gateway E2E stay green",
            "exam_deployment_status remains not_cleared while real-world clearance is tracked as a reminder",
        ],
        "next_sprint": next_sprint(compiler, scope),
    }
    attach_public_scan(packet, public_safe=public_safe, source_name="unibot-command-center")
    return packet


def next_sprint(compiler: dict[str, Any], scope: dict[str, Any]) -> dict[str, Any]:
    counts = compiler.get("counts", {})
    queue_total = int(counts.get("review_ready_count", 0) or 0) + int(counts.get("ocr_queue_count", 0) or 0) + int(
        counts.get("transcription_queue_count", 0) or 0
    )
    if queue_total:
        focus = "Course Material Compiler"
        outcome = "increase reviewed source anchors without exposing private course text"
    elif scope.get("status") == "needs_materials":
        focus = "Course Material Intake"
        outcome = "provide a local course-material base path and rerun the compiler plan"
    else:
        focus = "Tutor and Gateway UX"
        outcome = "connect source-grounded tutor, notebook sidecar, and Help Ledger into the workbench"
    return {
        "focus": focus,
        "outcome": outcome,
        "timebox": "one small slice, then smoke + targeted tests",
        "definition_of_done": [
            "one public-safe artifact or API response exists",
            "one test or smoke check proves the behavior",
            "handoff packet records changed surface, tests, risks, and next step",
        ],
    }


def resolve_review_policy(*, base_path: str | None = None, review_policy: str | None = None) -> str:
    policy = str(review_policy or "").strip()
    if policy and policy != "auto":
        return policy
    configured_root = str(os.environ.get(COURSE_MATERIAL_ROOT_ENV, "")).strip()
    if base_path or configured_root:
        return "local_private_tutor"
    return "staged"


def handoff_contract() -> dict[str, Any]:
    return {
        "required_fields": ["role_id", "goal", "changed_files", "tests", "risks", "evidence", "next_step"],
        "role_ids": [role["role_id"] for role in ROLE_LANES],
        "rules": [
            "no raw private course text",
            "no local absolute paths in public text",
            "no raw external AI transcripts",
            "no official approval or legal-advice claim",
            "external live actions require explicit Julius-Go or Final-Go",
        ],
    }


def build_context_packet(role_id: str, course_id: str = DEFAULT_COURSE_ID) -> dict[str, Any]:
    role = next((item for item in ROLE_LANES if item["role_id"] == role_id), None)
    if role is None:
        role = {
            "role_id": "unknown",
            "label": "Unknown role",
            "mission": "Use the command center to choose a valid role lane before implementation.",
            "done_signal": "valid role selected",
        }
    packet = {
        "schema_version": ORCHESTRATION_SCHEMA_VERSION,
        "artifact_type": "unibot_context_packet",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "course_id": safe_course_id(course_id),
        "role": role,
        "source_of_truth": "local UniBot hub only; older chats are evidence inputs",
        "non_goals": ["proctoring", "AI detection as evidence", "automatic grading", "official accommodation decision"],
        "mode_gates": {
            "practice_overlay": "allowed for demos and private practice",
            "course_tutor_mode": "allowed for reviewed local course anchors",
            "exam_controlled_gateway": "not_cleared; real-world authority clearance is a reminder, not a technical delivery blocker",
        },
        "handoff_contract": handoff_contract(),
        "required_harness": "add or update a runnable test, smoke check, or public-safety validation for every implementation slice",
    }
    attach_public_scan(packet, public_safe=True, source_name="unibot-context-packet")
    return packet


def validate_chat_handoff(handoff: dict[str, Any]) -> dict[str, Any]:
    contract = handoff_contract()
    missing = [field for field in contract["required_fields"] if not handoff.get(field)]
    role_id = str(handoff.get("role_id", ""))
    issues = list(missing)
    if role_id and role_id not in contract["role_ids"]:
        issues.append("unknown_role_id")
    if handoff.get("external_live_action") and not (
        handoff.get("julius_go_reference") or handoff.get("final_go_reference")
    ):
        issues.append("external_live_action_requires_explicit_go")
    serialized = json.dumps(handoff, ensure_ascii=False, sort_keys=True)
    safety_scan = scan_text(serialized, "chat-handoff")
    if safety_scan["status"] != "pass":
        issues.extend(f"public_safety:{finding['type']}" for finding in safety_scan["findings"])
    return {
        "schema_version": ORCHESTRATION_SCHEMA_VERSION,
        "artifact_type": "unibot_chat_handoff_validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok" if not issues else "blocked",
        "issues": sorted(set(issues)),
        "accepted_role_id": role_id if role_id in contract["role_ids"] else "",
        "public_safety_status": safety_scan["status"],
        "handoff_contract": contract,
    }


def build_orchestration_markdown(
    course_id: str = DEFAULT_COURSE_ID,
    *,
    base_path: str | None = None,
    review_policy: str | None = None,
) -> str:
    center = build_unibot_command_center(course_id, base_path=base_path, review_policy=review_policy)
    lane_lines = "\n".join(f"- `{lane['role_id']}`: {lane['mission']}" for lane in center["role_lanes"])
    gate_lines = "\n".join(f"- {gate}" for gate in center["acceptance_gates"])
    sprint_lines = "\n".join(f"- {item}" for item in center["workstream_sequence"])
    material = center["material_status"]
    return (
        "# UniBot Command Center\n\n"
        f"Status: {center['status']}\n\n"
        f"Exam deployment: {center['deployment_line']['exam_deployment_status']}\n\n"
        "## Materialstatus\n\n"
        f"- Records: {material.get('record_count', 0)}\n"
        f"- Private tutor index: {material.get('private_tutor_index_count', 0)}\n"
        f"- Review ready: {material.get('review_ready_count', 0)}\n"
        f"- OCR queue: {material.get('ocr_queue_count', 0)}\n"
        f"- Transcription queue: {material.get('transcription_queue_count', 0)}\n"
        f"- Quarantine: {material.get('solution_or_exam_quarantine_count', 0)}\n\n"
        "## Rollen\n\n"
        f"{lane_lines}\n\n"
        "## Sprintfolge\n\n"
        f"{sprint_lines}\n\n"
        "## Gates\n\n"
        f"{gate_lines}\n"
    )


def attach_public_scan(payload: dict[str, Any], *, public_safe: bool, source_name: str) -> None:
    if not public_safe:
        payload["public_safety_status"] = "local_private_mode"
        return
    scan = scan_text(json.dumps(payload, ensure_ascii=False), source_name)
    payload["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        payload["public_safety_findings"] = scan["findings"]
