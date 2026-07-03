from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .adaptive_tasks import generate_adaptive_practice_plan
from .autonomous_research_loop import build_autonomous_research_loop
from .bachelor_thesis import build_bachelor_thesis_package
from .compliance import build_compliance_matrix
from .demo import build_local_demo_run
from .evaluation import build_evaluation_packet
from .feedback import demo_feedback_template, export_public_demo_feedback_summary, validate_demo_feedback
from .github_issues import build_github_issue_bundle
from .gretel_glm_evolve import build_glm_evolve_work_packet, build_glm_rsi_workboard
from .handoff import build_authority_handoff_packet
from .materials import build_demo_material_manifest, build_public_material_summary
from .paperclip_evaluation_bridge import build_paperclip_evaluation_request
from .pilot import build_pilot_protocol
from .privacy import build_data_protection_screening
from .review_board import build_review_board_packet
from .redteam import run_redteam_smoke
from .release_runbook import build_release_runbook
from .public_safety import scan_text
from .source_cards import get_source_card, list_source_cards
from .triage import build_feedback_triage


PUBLICATION_SCHEMA_VERSION = "unibot-publication-package-v1"
PUBLICATION_REPRODUCIBILITY_ALIGNMENT_SCHEMA_VERSION = "unibot-publication-reproducibility-alignment-v1"
PUBLICATION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION = (
    "unibot-publication-release-review-board-claim-alignment-v1"
)

PUBLICATION_ALIGNMENT_SECTIONS = [
    {
        "section_id": "public_reproduction_bundle",
        "artifact_ids": ["system_card", "data_card", "limitations", "source_cards", "synthetic_tasks", "codebook"],
        "release_gate_ids": ["release_ready", "public_safety_required", "redteam_status", "evaluation_status"],
        "policy_keys": ["collaboration_note"],
        "source_card_ids": ["dfg-gwp", "openai-evals", "unesco-genai-2023"],
        "readiness_check_ids": ["publication_package", "evaluation_packet", "redteam", "source_card_drift_guard"],
        "human_gates": ["human_submission_review_required"],
    },
    {
        "section_id": "manual_release_boundary",
        "artifact_ids": ["release_runbook", "github_issue_bundle", "review_board_packet"],
        "release_gate_ids": ["release_runbook_ready", "review_board_packet_ready", "demo_feedback_contract_ready"],
        "policy_keys": ["release_runbook_policy", "github_issue_policy", "review_board_policy"],
        "source_card_ids": ["dfg-gwp", "uoc-ki-lehre", "gdpr-2016-679"],
        "readiness_check_ids": ["publication_package", "release_runbook", "github_issue_bundle", "review_board_packet"],
        "human_gates": ["human_review_required", "human_submission_review_required"],
    },
    {
        "section_id": "authority_and_compliance_bundle",
        "artifact_ids": ["compliance_matrix", "pilot_protocol", "data_protection_screening", "authority_handoff_summary"],
        "release_gate_ids": [
            "compliance_matrix_ready",
            "pilot_protocol_ready",
            "data_protection_screening_ready",
            "authority_packet_status",
        ],
        "policy_keys": ["compliance_matrix_policy", "pilot_protocol_policy", "data_protection_policy"],
        "source_card_ids": ["gdpr-2016-679", "eu-ai-act-2024", "uoc-ki-lehre", "uoc-nachteilsausgleich"],
        "readiness_check_ids": ["publication_package", "compliance_matrix", "pilot_protocol", "data_protection_screening"],
        "human_gates": [
            "datenschutz_review_required_before_real_pilot",
            "ethics_or_supervisor_review_required_before_real_pilot",
            "written_university_clearance_required_before_exam_use",
        ],
    },
    {
        "section_id": "release_review_board_claim_bundle",
        "artifact_ids": [
            "release_runbook",
            "review_board_packet",
            "pilot_protocol",
            "data_protection_screening",
            "compliance_matrix",
            "gretel_bachelor_thesis_package",
            "adaptive_task_plan_demo",
        ],
        "release_gate_ids": [
            "release_runbook_ready",
            "review_board_packet_ready",
            "pilot_protocol_ready",
            "data_protection_screening_ready",
            "compliance_matrix_ready",
            "gretel_bachelor_thesis_package_ready",
            "adaptive_task_plan_ready",
            "public_safety_required",
        ],
        "policy_keys": [
            "release_runbook_policy",
            "review_board_policy",
            "pilot_protocol_policy",
            "data_protection_policy",
            "compliance_matrix_policy",
            "gretel_bachelor_thesis_policy",
        ],
        "source_card_ids": ["dfg-gwp", "gdpr-2016-679", "dsk-ai-privacy-2024", "unesco-genai-2023"],
        "readiness_check_ids": [
            "publication_package",
            "release_runbook",
            "review_board_packet",
            "pilot_protocol",
            "data_protection_screening",
            "compliance_matrix",
            "gretel_bachelor_thesis_package",
            "evaluation_packet",
            "adaptive_task_plan",
            "public_safety",
        ],
        "human_gates": [
            "datenschutz_review_required_before_real_pilot",
            "ethics_or_supervisor_review_required_before_real_pilot",
            "human_submission_review_required",
            "public_safety_required",
            "written_university_clearance_required_before_exam_use",
        ],
    },
    {
        "section_id": "gretel_glm_thesis_bundle",
        "artifact_ids": ["gretel_glm_evolve_lane", "gretel_glm_rsi_workboard", "gretel_bachelor_thesis_package"],
        "release_gate_ids": [
            "gretel_glm_evolve_lane_ready",
            "gretel_glm_rsi_workboard_ready",
            "gretel_bachelor_thesis_package_ready",
        ],
        "policy_keys": ["gretel_glm_evolve_policy", "gretel_glm_rsi_visibility_policy", "gretel_bachelor_thesis_policy"],
        "source_card_ids": ["zai-glm-52", "zai-glm-52-migration", "zai-glm-pricing", "dfg-gwp"],
        "readiness_check_ids": ["publication_package", "gretel_glm_evolve_lane", "gretel_glm_rsi_visibility_workboard"],
        "human_gates": ["provider_call_requires_explicit_go_and_redaction_receipt", "human_submission_review_required"],
    },
    {
        "section_id": "budgeted_autonomy_boundary",
        "artifact_ids": ["gretel_autonomous_research_loop", "paperclip_evaluation_bridge"],
        "release_gate_ids": ["gretel_autonomous_research_loop_ready", "paperclip_evaluation_bridge_ready"],
        "policy_keys": ["gretel_autonomy_policy", "paperclip_policy"],
        "source_card_ids": ["dfg-gwp", "zai-glm-52"],
        "readiness_check_ids": ["publication_package", "gretel_autonomous_research_loop"],
        "human_gates": ["human_review_required", "public_safety_required"],
    },
]


def build_system_card() -> dict[str, Any]:
    return {
        "name": "UniBot Guardian",
        "status": "public practice MVP; not officially cleared for exam use",
        "purpose": "Socratic filtering layer for Colab/Gemini, Jupyter, and coding AI practice workflows.",
        "intended_users": ["students in voluntary practice", "teaching staff reviewing a prototype", "research collaborators"],
        "supported_modes": ["practice_overlay", "selftest_guardian"],
        "blocked_or_not_cleared_modes": ["exam_controlled"],
        "core_capabilities": [
            "generate Socratic Prompt Cards",
            "classify external AI output",
            "block final solutions and sensitive data",
            "produce private formative help-level summaries",
            "generate public-safe practice notebooks",
            "summarize course-material staging without publishing private files",
            "generate adaptive practice plans from skill tags and reviewed material metadata",
            "run red-team smokes",
            "prepare redacted Gretel/GLM proposal packets for reviewed self-improvement",
            "run a budgeted Gretel autonomous research loop for local, public-safe improvement candidates",
            "prepare optional Paperclip control-plane evaluation receipts without making Paperclip a runtime dependency",
        ],
        "non_goals": [
            "no proctoring",
            "no KI detection as evidence",
            "no automatic grading",
            "no decision on accommodation",
            "no exam-security guarantee through a normal browser extension",
        ],
    }


def build_data_card() -> dict[str, Any]:
    return {
        "data_principle": "local-first, minimal, public-safe by default",
        "stored_by_default": ["hashes", "classification categories", "help levels", "skill tags", "source card IDs", "redacted reflections"],
        "not_stored_by_default": ["raw external KI output", "student reflections in public summaries", "private course materials", "emails", "local paths"],
        "public_release_allowed": [
            "source cards",
            "synthetic tasks",
            "codebook",
            "red-team status",
            "system card",
            "data card",
            "limitations",
            "public-safe documentation",
            "course-material public summaries",
            "adaptive practice plan demo",
            "local demo test plan",
            "demo feedback template and public summary contract",
            "demo feedback triage contract",
            "GitHub issue bundle draft",
            "release and contributor runbook",
            "compliance matrix",
            "pilot protocol",
            "data-protection screening",
            "Gretel autonomous research loop",
        ],
        "public_release_excluded": [
            "private course materials",
            "emails",
            "local filesystem paths",
            "raw external KI transcripts",
            "medical or accommodation personal data",
            "real exam performance",
            "grades",
        ],
        "retention": "To be defined with Datenschutz before any real pilot.",
    }


def build_limitations() -> list[dict[str, str]]:
    return [
        {
            "limitation": "Browser overlay is not hard exam security.",
            "mitigation": "Use only for practice unless a controlled channel and written clearance exist.",
        },
        {
            "limitation": "Postfilter rules are heuristic.",
            "mitigation": "Run red-team smokes and human review before demos or pilot use.",
        },
        {
            "limitation": "Evaluation packet is synthetic.",
            "mitigation": "Do not infer real exam outcomes or official learning judgments.",
        },
        {
            "limitation": "Source cards are public pointers, not legal advice.",
            "mitigation": "Use authority handoff for Pruefungsamt, Inklusion, Datenschutz, IT/SZI, and teaching review.",
        },
    ]


def build_publication_reproducibility_alignment(package: dict[str, Any] | None = None) -> dict[str, Any]:
    publication = package or build_publication_package()
    artifact_ids = set(publication.get("included_artifacts", [])) | {
        key for key in publication.keys() if key not in {"generated_at_utc", "publication_reproducibility_alignment"}
    }
    release_gates = publication.get("release_gates", {})
    release_gate_ids = set(release_gates)
    alignment_rows = []
    for section in PUBLICATION_ALIGNMENT_SECTIONS:
        missing_artifact_ids = sorted(artifact_id for artifact_id in section["artifact_ids"] if artifact_id not in artifact_ids)
        missing_release_gate_ids = sorted(
            gate_id for gate_id in section["release_gate_ids"] if gate_id not in release_gate_ids
        )
        missing_policy_keys = sorted(policy_key for policy_key in section["policy_keys"] if policy_key not in publication)
        missing_source_card_ids = sorted(
            source_id for source_id in section["source_card_ids"] if get_source_card(source_id) is None
        )
        alignment_rows.append(
            {
                "section_id": section["section_id"],
                "artifact_ids": list(section["artifact_ids"]),
                "release_gate_ids": list(section["release_gate_ids"]),
                "policy_keys": list(section["policy_keys"]),
                "source_card_ids": list(section["source_card_ids"]),
                "readiness_check_ids": list(section["readiness_check_ids"]),
                "human_gates": list(section["human_gates"]),
                "missing_artifact_ids": missing_artifact_ids,
                "missing_release_gate_ids": missing_release_gate_ids,
                "missing_policy_keys": missing_policy_keys,
                "missing_source_card_ids": missing_source_card_ids,
            }
        )
    contracts = {
        "release_ready_public_draft_only": (
            release_gates.get("release_ready") is True
            and "not as exam deployment" in str(release_gates.get("release_ready_note", ""))
            and publication.get("status") == "public_draft_not_exam_release"
        ),
        "private_groups_excluded": all(
            needle in " ".join(publication.get("excluded_file_groups", [])).lower()
            for needle in ["private", "emails", "local", "exam"]
        ),
        "manual_review_policies_present": all(
            needle in str(publication.get(policy_key, "")).lower()
            for policy_key, needle in [
                ("github_issue_policy", "manual review"),
                ("review_board_policy", "review"),
                ("gretel_autonomy_policy", "human-gated"),
            ]
        ),
        "gretel_thesis_claim_source_bound": (
            publication.get("gretel_bachelor_thesis_package", {})
            .get("evidence_index", {})
            .get("status")
            == "ready"
            and publication.get("gretel_bachelor_thesis_package", {})
            .get("authorship_statement", {})
            .get("builder")
            == "Gretel"
        ),
        "glm_provider_locked": (
            publication.get("gretel_glm_evolve_lane", {}).get("provider_call_executed") is False
            and publication.get("gretel_glm_rsi_workboard", {}).get("safety", {}).get("provider_call_allowed_now") is False
        ),
        "autonomous_release_locked": publication.get("gretel_autonomous_research_loop", {}).get("safety", {}).get(
            "autonomous_github_push"
        )
        is False,
        "pilot_claim_contract_ready": (
            publication.get("pilot_protocol", {})
            .get("pilot_evidence_alignment", {})
            .get("pilot_release_review_board_claim_contract", {})
            .get("expected_schema_version")
            == "unibot-pilot-release-review-board-claim-alignment-v1"
            and publication.get("pilot_protocol", {})
            .get("pilot_evidence_alignment", {})
            .get("missing_release_review_board_claim_check_ids")
            == []
            and publication.get("pilot_protocol", {})
            .get("pilot_evidence_alignment", {})
            .get("missing_release_review_board_claim_human_gates")
            == []
        ),
        "data_protection_claim_contract_ready": (
            publication.get("data_protection_screening", {})
            .get("data_protection_evidence_alignment", {})
            .get("data_protection_release_review_board_claim_contract", {})
            .get("expected_schema_version")
            == "unibot-data-protection-release-review-board-claim-alignment-v1"
            and publication.get("data_protection_screening", {})
            .get("data_protection_evidence_alignment", {})
            .get("missing_release_review_board_claim_check_ids")
            == []
            and publication.get("data_protection_screening", {})
            .get("data_protection_evidence_alignment", {})
            .get("missing_release_review_board_claim_human_gates")
            == []
        ),
        "review_board_thesis_evaluation_claim_ready": (
            publication.get("review_board_packet", {})
            .get("thesis_evaluation_claim_alignment", {})
            .get("status")
            == "ready"
            and publication.get("release_runbook", {})
            .get("release_evidence_alignment", {})
            .get("review_board_thesis_evaluation_claim_contract", {})
            .get("required_status")
            == "ready"
        ),
    }
    alignment = {
        "schema_version": PUBLICATION_REPRODUCIBILITY_ALIGNMENT_SCHEMA_VERSION,
        "status": "ready",
        "section_count": len(alignment_rows),
        "sections": alignment_rows,
        "missing_artifact_ids": sorted({item for row in alignment_rows for item in row["missing_artifact_ids"]}),
        "missing_release_gate_ids": sorted({item for row in alignment_rows for item in row["missing_release_gate_ids"]}),
        "missing_policy_keys": sorted({item for row in alignment_rows for item in row["missing_policy_keys"]}),
        "missing_source_card_ids": sorted({item for row in alignment_rows for item in row["missing_source_card_ids"]}),
        "failed_contract_ids": sorted(contract_id for contract_id, passed in contracts.items() if not passed),
        "contracts": contracts,
        "publication_release_review_board_claim_contract": {
            "expected_schema_version": PUBLICATION_RELEASE_REVIEW_BOARD_ALIGNMENT_SCHEMA_VERSION,
            "required_pilot_release_review_board_schema_version": (
                "unibot-pilot-release-review-board-claim-alignment-v1"
            ),
            "required_data_protection_release_review_board_schema_version": (
                "unibot-data-protection-release-review-board-claim-alignment-v1"
            ),
            "required_review_board_thesis_evaluation_schema_version": (
                "unibot-review-board-thesis-evaluation-claim-alignment-v1"
            ),
            "required_readiness_check_ids": [
                "publication_package",
                "release_runbook",
                "review_board_packet",
                "pilot_protocol",
                "data_protection_screening",
                "compliance_matrix",
                "gretel_bachelor_thesis_package",
                "evaluation_packet",
                "adaptive_task_plan",
                "public_safety",
            ],
            "required_human_gates": [
                "datenschutz_review_required_before_real_pilot",
                "ethics_or_supervisor_review_required_before_real_pilot",
                "human_submission_review_required",
                "public_safety_required",
                "written_university_clearance_required_before_exam_use",
            ],
            "use": "Publication package language must carry pilot/data-protection/review-board thesis-evaluation boundaries without implying GitHub publication approval, university submission, real pilot recruitment, or exam clearance.",
        },
        "required_readiness_check_ids": sorted(
            {check_id for row in alignment_rows for check_id in row["readiness_check_ids"]}
        ),
        "required_human_gates": sorted({gate for row in alignment_rows for gate in row["human_gates"]}),
        "release_boundary": "public_draft_only_not_exam_deployment_not_university_submission",
        "policy": (
            "Publication reproducibility alignment is a review aid for the public package; it is not exam clearance, "
            "legal advice, Datenschutz approval, provider-call approval, or thesis submission approval."
        ),
    }
    if (
        alignment["missing_artifact_ids"]
        or alignment["missing_release_gate_ids"]
        or alignment["missing_policy_keys"]
        or alignment["missing_source_card_ids"]
        or alignment["failed_contract_ids"]
    ):
        alignment["status"] = "blocked"
    required_check_ids = set(
        alignment["publication_release_review_board_claim_contract"]["required_readiness_check_ids"]
    )
    present_check_ids = set(alignment["required_readiness_check_ids"])
    alignment["missing_release_review_board_claim_check_ids"] = sorted(required_check_ids - present_check_ids)
    required_human_gates = set(
        alignment["publication_release_review_board_claim_contract"]["required_human_gates"]
    )
    present_human_gates = set(alignment["required_human_gates"])
    alignment["missing_release_review_board_claim_human_gates"] = sorted(required_human_gates - present_human_gates)
    if (
        alignment["missing_release_review_board_claim_check_ids"]
        or alignment["missing_release_review_board_claim_human_gates"]
    ):
        alignment["status"] = "blocked"
    scan = scan_text(json.dumps(alignment, ensure_ascii=False), "publication-reproducibility-alignment")
    alignment["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        alignment["status"] = "blocked_public_safety"
    return alignment


def build_publication_package() -> dict[str, Any]:
    redteam = run_redteam_smoke()
    evaluation = build_evaluation_packet()
    handoff = build_authority_handoff_packet()
    source_cards = list_source_cards()
    material_manifest = build_demo_material_manifest()
    material_summary = build_public_material_summary(material_manifest["records"])
    adaptive_plan = generate_adaptive_practice_plan(
        skill_state={"python_lists": {"signals": 3, "high_help_events": 1}},
        material_records=material_manifest["records"],
        max_tasks=3,
        public_safe=True,
    )
    demo_run = build_local_demo_run()
    feedback_template = demo_feedback_template()
    feedback_validation = validate_demo_feedback(
        {
            "scenario_id": "demo_prompt_card",
            "outcome": "fail",
            "severity": "minor",
            "what_i_tried": "Clicked prompt card after entering a synthetic Python-list task.",
            "expected": "Clipboard contains a Socratic prompt.",
            "what_happened": "Clipboard stayed empty.",
            "button_or_endpoint": "Promptkarte erzeugen",
            "public_safe_text": "No private data included.",
            "private_data_removed": True,
        }
    )
    feedback_public_summary = export_public_demo_feedback_summary()
    feedback_triage = build_feedback_triage(
        records=[
            {
                "feedback_id": "demo-feedback-1",
                "scenario_id": "demo_prompt_card",
                "outcome": "fail",
                "severity": "minor",
                "button_or_endpoint": "Promptkarte erzeugen",
                "private_data_removed": True,
                "has_public_safe_text": False,
                "has_follow_up_note": False,
            }
        ]
    )
    github_issue_bundle = build_github_issue_bundle(
        records=[
            {
                "feedback_id": "demo-feedback-1",
                "scenario_id": "demo_prompt_card",
                "outcome": "fail",
                "severity": "minor",
                "button_or_endpoint": "Promptkarte erzeugen",
                "private_data_removed": True,
                "has_public_safe_text": False,
                "has_follow_up_note": False,
            }
        ]
    )
    release_runbook = build_release_runbook()
    compliance_matrix = build_compliance_matrix()
    pilot_protocol = build_pilot_protocol()
    data_protection_screening = build_data_protection_screening()
    review_board_packet = build_review_board_packet()
    glm_evolve_packet = build_glm_evolve_work_packet()
    glm_rsi_workboard = build_glm_rsi_workboard()
    bachelor_thesis_package = build_bachelor_thesis_package()
    autonomous_research_loop = build_autonomous_research_loop()
    paperclip_bridge = build_paperclip_evaluation_request()
    material_policy_ready = (
        material_manifest["record_count"] >= 2
        and material_manifest["public_release_allowed_count"] == 1
        and material_summary["public_release_allowed_count"] == 1
    )
    adaptive_plan_ready = adaptive_plan["status"] == "ok" and adaptive_plan["public_safety_status"] == "pass"
    demo_run_ready = demo_run["status"] == "practice_demo_ready_not_exam" and demo_run["public_safety_status"] == "pass"
    feedback_contract_ready = (
        feedback_template["status"] == "template"
        and feedback_validation["status"] == "ok"
        and feedback_triage["status"] == "ready"
        and feedback_triage["public_safety_status"] == "pass"
        and github_issue_bundle["status"] == "ready"
        and github_issue_bundle["public_safety_status"] == "pass"
    )
    release_runbook_ready = (
        release_runbook["status"] == "public_draft_runbook_not_exam_release"
        and release_runbook["public_safety_status"] == "pass"
        and release_runbook["manual_review_required"] is True
        and release_runbook["exam_deployment_status"] == "not_cleared"
    )
    compliance_matrix_ready = (
        compliance_matrix["status"] == "draft_ready_for_authority_review"
        and compliance_matrix["public_safety_status"] == "pass"
        and compliance_matrix["missing_source_card_ids"] == []
        and compliance_matrix["exam_deployment_status"] == "not_cleared"
    )
    pilot_protocol_ready = (
        pilot_protocol["status"] == "draft_not_ethics_or_authority_cleared"
        and pilot_protocol["public_safety_status"] == "pass"
        and pilot_protocol["exam_deployment_status"] == "not_cleared"
        and len(pilot_protocol["consent_items"]) >= 7
    )
    data_protection_ready = (
        data_protection_screening["status"] == "draft_for_datenschutz_review"
        and data_protection_screening["public_safety_status"] == "pass"
        and data_protection_screening["review_gates"]["datenschutz_review_required_before_real_pilot"] is True
        and data_protection_screening["exam_deployment_status"] == "not_cleared"
    )
    review_board_ready = (
        review_board_packet["status"] == "draft_for_institutional_review"
        and review_board_packet["public_safety_status"] == "pass"
        and review_board_packet["exam_deployment_status"] == "not_cleared"
        and len(review_board_packet["reviewer_packets"]) >= 6
    )
    glm_evolve_ready = (
        glm_evolve_packet["status"] == "prepared_no_provider_call"
        and glm_evolve_packet["public_safety_status"] == "pass"
        and glm_evolve_packet["provider_call_executed"] is False
        and glm_evolve_packet["raw_private_context_shared"] is False
        and glm_evolve_packet["autonomous_apply"] is False
    )
    paperclip_bridge_ready = (
        paperclip_bridge["status"] == "needs_codex_review"
        and paperclip_bridge["public_safety_status"] == "pass"
        and paperclip_bridge["critical_path"] is False
        and paperclip_bridge["chrome_extension_dependency"] is False
        and paperclip_bridge["provider_call_executed"] is False
        and paperclip_bridge["paperclip_execution_requested"] is False
        and paperclip_bridge["raw_private_context_shared"] is False
        and paperclip_bridge["autonomous_apply"] is False
        and paperclip_bridge["receipt"]["status"] in {"proposal_ready", "blocked", "needs_codex_review", "discarded"}
    )
    glm_rsi_workboard_ready = (
        glm_rsi_workboard["status"] == "visible"
        and glm_rsi_workboard["public_safety_status"] == "pass"
        and glm_rsi_workboard["safety"]["provider_call_executed"] is False
        and glm_rsi_workboard["safety"]["provider_call_allowed_now"] is False
        and glm_rsi_workboard["safety"]["autonomous_apply"] is False
        and glm_rsi_workboard["safety"]["final_go"] is False
        and glm_rsi_workboard["active_item_count"] >= 1
    )
    bachelor_thesis_ready = (
        bachelor_thesis_package["status"] == "public_scientific_draft_bachelor_thesis_level_not_real_submission"
        and bachelor_thesis_package["public_safety_status"] == "pass"
        and bachelor_thesis_package["authorship_statement"]["builder"] == "Gretel"
        and bachelor_thesis_package["glm_technology_basis"]["primary_model_hint"] == "zai/glm-5.2"
        and bachelor_thesis_package["review_gates"]["no_autonomous_github_publish"] is True
        and bachelor_thesis_package["review_gates"]["no_final_go_by_gretel_or_glm"] is True
    )
    autonomous_loop_ready = (
        autonomous_research_loop["status"] == "ready_for_budgeted_recurring_local_runs"
        and autonomous_research_loop["public_safety_status"] == "pass"
        and autonomous_research_loop["budget_policy"]["token_policy"]["default_reasoning_effort"] == "low"
        and autonomous_research_loop["budget_policy"]["cadence"]["max_active_work_item_per_run"] == 1
        and autonomous_research_loop["safety"]["provider_call_executed"] is False
        and autonomous_research_loop["safety"]["autonomous_github_push"] is False
        and autonomous_research_loop["safety"]["final_go"] is False
    )
    release_gates = {
        "redteam_status": redteam["status"],
        "evaluation_status": evaluation["status"],
        "authority_packet_status": handoff["status"],
        "source_card_count": len(source_cards),
        "course_material_policy_ready": material_policy_ready,
        "adaptive_task_plan_ready": adaptive_plan_ready,
        "local_demo_run_ready": demo_run_ready,
        "demo_feedback_contract_ready": feedback_contract_ready,
        "release_runbook_ready": release_runbook_ready,
        "compliance_matrix_ready": compliance_matrix_ready,
        "pilot_protocol_ready": pilot_protocol_ready,
        "data_protection_screening_ready": data_protection_ready,
        "review_board_packet_ready": review_board_ready,
        "gretel_glm_evolve_lane_ready": glm_evolve_ready,
        "gretel_glm_rsi_workboard_ready": glm_rsi_workboard_ready,
        "gretel_bachelor_thesis_package_ready": bachelor_thesis_ready,
        "gretel_autonomous_research_loop_ready": autonomous_loop_ready,
        "paperclip_evaluation_bridge_ready": paperclip_bridge_ready,
        "public_safety_required": True,
        "release_ready": redteam["status"] == "pass"
        and evaluation["status"] == "draft_not_ethics_or_authority_cleared"
        and handoff["status"] == "draft_not_officially_cleared"
        and len(source_cards) >= 10
        and material_policy_ready
        and adaptive_plan_ready
        and demo_run_ready
        and feedback_contract_ready
        and release_runbook_ready
        and compliance_matrix_ready
        and pilot_protocol_ready
        and data_protection_ready
        and review_board_ready
        and glm_evolve_ready
        and glm_rsi_workboard_ready
        and bachelor_thesis_ready
        and autonomous_loop_ready
        and paperclip_bridge_ready,
        "release_ready_note": "Ready as public-safe draft package, not as exam deployment.",
    }
    package = {
        "schema_version": PUBLICATION_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "public_draft_not_exam_release",
        "system_card": build_system_card(),
        "data_card": build_data_card(),
        "limitations": build_limitations(),
        "release_gates": release_gates,
        "course_material_public_summary": material_summary,
        "adaptive_task_plan_demo": adaptive_plan,
        "local_demo_run": demo_run,
        "demo_feedback_template": feedback_template,
        "demo_feedback_public_summary": feedback_public_summary,
        "demo_feedback_triage": feedback_triage,
        "github_issue_bundle": github_issue_bundle,
        "release_runbook": release_runbook,
        "compliance_matrix": compliance_matrix,
        "pilot_protocol": pilot_protocol,
        "data_protection_screening": data_protection_screening,
        "review_board_packet": review_board_packet,
        "gretel_glm_evolve_lane": glm_evolve_packet,
        "gretel_glm_rsi_workboard": glm_rsi_workboard,
        "gretel_bachelor_thesis_package": bachelor_thesis_package,
        "gretel_autonomous_research_loop": autonomous_research_loop,
        "paperclip_evaluation_bridge": paperclip_bridge,
        "public_file_groups": [
            "unibot/",
            "docs/unibot/",
            "tests/test_unibot_*.py",
        ],
        "excluded_file_groups": [
            "private course-material directory (local-only; exact path omitted from public package)",
            "docs/exports with private review artifacts",
            "local Help Ledger files",
            "emails and mailbox exports",
            "real exam notebooks or solution keys",
        ],
        "included_artifacts": [
            "source_cards",
            "synthetic_tasks",
            "codebook",
            "redteam_summary",
            "authority_handoff_summary",
            "evaluation_packet",
            "course_material_public_summary",
            "adaptive_task_plan_demo",
            "local_demo_run",
            "demo_feedback_template",
            "demo_feedback_public_summary",
            "demo_feedback_triage",
            "github_issue_bundle",
            "release_runbook",
            "compliance_matrix",
            "pilot_protocol",
            "data_protection_screening",
            "review_board_packet",
            "gretel_glm_evolve_lane",
            "gretel_glm_rsi_workboard",
            "gretel_bachelor_thesis_package",
            "gretel_autonomous_research_loop",
            "paperclip_evaluation_bridge",
            "system_card",
            "data_card",
            "limitations",
        ],
        "collaboration_note": "Contributors should work only with synthetic tasks, public source cards, and public-safe tests.",
        "gretel_glm_evolve_policy": "Gretel/GLM may prepare redacted proposals only; Codex and human review remain the apply and release gate.",
        "gretel_glm_rsi_visibility_policy": "Gretel's GLM-RSI workboard must show active, blocked and harnessed proposal work without provider calls or private raw context.",
        "gretel_bachelor_thesis_policy": "The UniBot package is labelled as Gretel-built and Gretel-documented at bachelor-thesis level, GLM-5.2-ready, public-safe, and not a real university submission without human review.",
        "gretel_autonomy_policy": "Gretel may run a budgeted local autonomous research loop for one small public-safe work item at a time; provider calls, external messages, Final-Go and public GitHub pushes remain human-gated.",
        "paperclip_policy": "Paperclip may be evaluated as an optional local control plane only; it is not required by the browser extension and must not apply code or execute provider calls without explicit review.",
        "github_issue_policy": "Issue bundle drafts require manual review before publication and never include private feedback text.",
        "release_runbook_policy": "Runbook status is public draft only and must not be represented as exam clearance.",
        "compliance_matrix_policy": "Compliance matrix links sources to controls for authority review; it is not legal advice or exam clearance.",
        "pilot_protocol_policy": "Pilot protocol is a planning draft only and must be reviewed before any real participant study.",
        "data_protection_policy": "Data-protection screening is a planning draft only and must be reviewed before any real pilot data collection.",
        "review_board_policy": "Review board packet is a planning artifact and is not written institutional approval.",
    }
    package["publication_reproducibility_alignment"] = build_publication_reproducibility_alignment(package)
    return package


def build_publication_markdown() -> str:
    package = build_publication_package()
    system = package["system_card"]
    data = package["data_card"]
    limitation_lines = "\n".join(f"- {item['limitation']} Mitigation: {item['mitigation']}" for item in package["limitations"])
    included_lines = "\n".join(f"- {item}" for item in package["included_artifacts"])
    excluded_lines = "\n".join(f"- {item}" for item in package["excluded_file_groups"])
    alignment = package["publication_reproducibility_alignment"]
    return (
        "# UniBot Public Reproduction Package\n\n"
        f"Status: {package['status']}\n\n"
        "## System Card\n\n"
        f"- Name: {system['name']}\n"
        f"- Purpose: {system['purpose']}\n"
        f"- Modes: {', '.join(system['supported_modes'])}\n"
        f"- Not cleared: {', '.join(system['blocked_or_not_cleared_modes'])}\n\n"
        "## Data Card\n\n"
        f"- Principle: {data['data_principle']}\n"
        f"- Retention: {data['retention']}\n\n"
        "## Included Artifacts\n\n"
        f"{included_lines}\n\n"
        "## Excluded File Groups\n\n"
        f"{excluded_lines}\n\n"
        "## Limitations\n\n"
        f"{limitation_lines}\n\n"
        "## Reproducibility Alignment\n\n"
        f"- Alignment: {alignment['status']}\n"
        f"- Sections: {alignment['section_count']}\n"
        f"- Release review-board claim alignment: {alignment['publication_release_review_board_claim_contract']['expected_schema_version']}\n"
        f"- Release boundary: {alignment['release_boundary']}\n"
        f"- Human gates: {', '.join(alignment['required_human_gates'])}\n\n"
        "## Release Gates\n\n"
        f"- Red-Team: {package['release_gates']['redteam_status']}\n"
        f"- Evaluation: {package['release_gates']['evaluation_status']}\n"
        f"- Authority packet: {package['release_gates']['authority_packet_status']}\n"
        f"- Course-material policy: {package['release_gates']['course_material_policy_ready']}\n"
        f"- Adaptive task plan: {package['release_gates']['adaptive_task_plan_ready']}\n"
        f"- Local demo run: {package['release_gates']['local_demo_run_ready']}\n"
        f"- Demo feedback contract: {package['release_gates']['demo_feedback_contract_ready']}\n"
        f"- Release runbook: {package['release_gates']['release_runbook_ready']}\n"
        f"- Compliance matrix: {package['release_gates']['compliance_matrix_ready']}\n"
        f"- Pilot protocol: {package['release_gates']['pilot_protocol_ready']}\n"
        f"- Data protection screening: {package['release_gates']['data_protection_screening_ready']}\n"
        f"- Review board packet: {package['release_gates']['review_board_packet_ready']}\n"
        f"- Gretel GLM evolve lane: {package['release_gates']['gretel_glm_evolve_lane_ready']}\n"
        f"- Gretel GLM-RSI workboard: {package['release_gates']['gretel_glm_rsi_workboard_ready']}\n"
        f"- Gretel Bachelor thesis package: {package['release_gates']['gretel_bachelor_thesis_package_ready']}\n"
        f"- Gretel autonomous research loop: {package['release_gates']['gretel_autonomous_research_loop_ready']}\n"
        f"- Public draft ready: {package['release_gates']['release_ready']}\n"
    )
