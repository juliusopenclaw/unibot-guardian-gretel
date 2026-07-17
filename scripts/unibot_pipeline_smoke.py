#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import re
import shutil
import subprocess
import tempfile
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from unibot.readiness import run_readiness_check
from unibot.redteam import run_redteam_smoke
from unibot.server import route_request
from unibot.loop_lab import run_loop_lab
from unibot.simulation_loop import run_gretel_unibot_loop


@dataclass
class Check:
    name: str
    passed: bool
    details: str


def _check(condition: bool, name: str, details: str) -> Check:
    return Check(name=name, passed=bool(condition), details=details)


def write_private_extraction_smoke_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    docx_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Python notebook setup and pandas source checks</w:t></w:r></w:p></w:body></w:document>"
    )
    pptx_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Loops lists numpy dataframe practice</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
    )
    pdf_stream = zlib.compress(b"BT /F1 12 Tf 72 720 Td (PDF text extraction for course practice) Tj ET")
    with zipfile.ZipFile(root / "setup.docx", "w") as archive:
        archive.writestr("word/document.xml", docx_xml)
    (root / "lecture.pdf").write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        + f"5 0 obj << /Length {len(pdf_stream)} /Filter /FlateDecode >> stream\n".encode("ascii")
        + pdf_stream
        + b"\nendstream endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"
    )
    with zipfile.ZipFile(root / "slides.pptx", "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", pptx_xml)


def write_video_transcription_smoke_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "python_intro.mov").write_bytes(b"synthetic video placeholder")
    (root / "python_intro.vtt").write_text(
        "\n".join(
            [
                "WEBVTT",
                "",
                "00:00:00.000 --> 00:00:03.000",
                "Notebook state and variables matter.",
                "",
                "00:00:03.000 --> 00:00:06.000",
                "Predict the next cell output before running.",
            ]
        ),
        encoding="utf-8",
    )


def _initialize_isolated_git_repository(root: Path) -> tuple[bool, str]:
    """Give the throwaway test copy provenance without copying the real .git directory."""
    init = subprocess.run(
        ["git", "init", "-q"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    if init.returncode != 0:
        return False, "git_init_failed"
    add = subprocess.run(
        ["git", "add", "--all"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    if add.returncode != 0:
        return False, "git_add_failed"
    commit = subprocess.run(
        [
            "git",
            "-c",
            "user.name=UniBot Pipeline Smoke",
            "-c",
            "user.email=unibot-pipeline-smoke@example.invalid",
            "commit",
            "-q",
            "-m",
            "isolated smoke fixture",
        ],
        capture_output=True,
        text=True,
        cwd=root,
    )
    if commit.returncode != 0:
        return False, "git_commit_failed"
    return True, "verified"


def run_unit_tests() -> dict[str, Any]:
    test_files = sorted(str(item.relative_to(ROOT)) for item in ROOT.glob("tests/test_unibot_*.py"))
    if not test_files:
        return {
            "status": "blocked",
            "check_count": 0,
            "passed_count": 0,
            "failed_count": 0,
            "details": "No matching unibot test files found.",
        }

    command = [sys.executable, "-m", "pytest", "-q", "-k", "not http_handler_roundtrip", *test_files]
    unit_test_env = dict(os.environ)
    for key in (
        "UNIBOT_EXAM_WORKSPACE_ROOT",
        "UNIBOT_COURSE_MATERIAL_ROOT",
        "UNIBOT_PRIVATE_TUTOR_INDEX_PATH",
        "UNIBOT_PRIVATE_TUTOR_INDEX_JOURNAL_PATH",
        "UNIBOT_GUARDIAN_ROOT",
    ):
        unit_test_env.pop(key, None)
    with tempfile.TemporaryDirectory() as temp_dir:
        isolated_root = Path(temp_dir) / "unibot-unit-tests"
        tracked = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        tracked_files = [line.strip() for line in (tracked.stdout or "").splitlines() if line.strip()]
        if tracked.returncode == 0 and tracked_files:
            for relative_path in tracked_files:
                source = ROOT / relative_path
                target = isolated_root / relative_path
                if source.is_dir():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        else:
            shutil.copytree(ROOT, isolated_root, ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__"))
        provenance_ready, provenance_reason = _initialize_isolated_git_repository(isolated_root)
        if not provenance_ready:
            return {
                "status": "fail",
                "command": "isolated git provenance setup",
                "return_code": 1,
                "check_count": len(test_files),
                "passed_count": 0,
                "failed_count": len(test_files),
                "xfailed": 0,
                "skipped": 0,
                "summary_line": provenance_reason,
            }
        proc = subprocess.run(command, capture_output=True, text=True, cwd=isolated_root, env=unit_test_env)
    output = (proc.stdout or "") + (proc.stderr or "")
    passed_matches = re.findall(r"(?P<passed>\d+) passed", output)
    failed_matches = re.findall(r"(?P<failed>\d+) failed", output)
    xfailed_matches = re.findall(r"(?P<xfail>\d+) xfailed", output)
    skipped_matches = re.findall(r"(?P<skipped>\d+) skipped", output)

    return {
        "status": "pass" if proc.returncode == 0 else "fail",
        "command": " ".join(command),
        "return_code": proc.returncode,
        "check_count": len(test_files),
        "passed_count": int(passed_matches[-1]) if passed_matches else 0,
        "failed_count": int(failed_matches[-1]) if failed_matches else 0,
        "xfailed": int(xfailed_matches[-1]) if xfailed_matches else 0,
        "skipped": int(skipped_matches[-1]) if skipped_matches else 0,
        "summary_line": output.strip().splitlines()[-1] if output.strip() else "",
    }


def run_smoke_suite() -> dict[str, Any]:
    checks: list[Check] = []

    health_status, health = route_request("/api/unibot/health", method="GET")
    checks.append(_check(
        health_status == 200 and health.get("service") == "unibot-guardian-local",
        "api_health",
        f"GET /api/unibot/health -> {health_status} {health.get('status')}",
    ))

    prompt_card_status, prompt_card = route_request(
        "/api/unibot/prompt-card",
        payload={"task": "Python Listen indexieren", "mode": "practice_overlay", "tool": "colab_gemini"},
    )
    checks.append(
        _check(
            prompt_card_status == 200
            and bool(prompt_card.get("copyable_prompt"))
            and prompt_card.get("mode") == "practice_overlay",
            "prompt_card_generation",
            f"status={prompt_card_status}, has_prompt={bool(prompt_card.get('copyable_prompt'))}",
        )
    )

    review_status, review = route_request(
        "/api/unibot/review-output",
        payload={
            "external_output": "Hier ist die komplette Loesung: import pandas as pd\nplt.boxplot([1, 2, 3, 4])",
            "requested_help_level": "A5",
            "mode": "practice_overlay",
            "task": "Python",
        },
    )
    checks.append(
        _check(
            review_status == 200 and review.get("status") == "blocked" and "final_solution" in review.get("categories", []),
            "postfilter_blocks_solution_like_output",
            f"status={review_status}, categories={review.get('categories')}",
        )
    )

    exam_review_status, exam_review = route_request(
        "/api/unibot/review-output",
        payload={
            "external_output": "Welche Loesung empfiehlst du?",
            "requested_help_level": "A2",
            "mode": "exam_controlled",
        },
    )
    checks.append(
        _check(
            exam_review_status == 200
            and exam_review.get("status") == "blocked"
            and "exam_controlled_requires_written_approval" in exam_review.get("categories", []),
            "exam_mode_requires_approval_block",
            f"status={exam_review_status}, categories={exam_review.get('categories')}",
        )
    )

    flow_status, flow = route_request(
        "/api/unibot/practice-flow",
        payload={
            "task": "Warum ist mein Index falsch?",
            "external_output": "Welche Laenge hat deine Liste direkt vor dem Zugriff?",
            "requested_help_level": "A2",
            "mode": "practice_overlay",
            "tool": "colab_gemini",
            "source_card_ids": ["vanlehn-2011"],
            "student_reflection": "Ich pruefe zuerst len(meine_liste).",
        },
    )
    checks.append(
        _check(
            flow_status == 200
            and flow.get("artifact_type") == "unibot_guardian_practice_flow"
            and flow.get("postfilter", {}).get("status") in {"allowed", "blocked"}
            and isinstance(flow.get("formative_score", {}).get("score"), int),
            "practice_flow_end_to_end",
            f"status={flow_status}, artifact={flow.get('artifact_type')}",
        )
    )

    notebook_status, notebook = route_request(
        "/api/unibot/notebook-template",
        payload={"task": "Python Listen üben", "mode": "practice_overlay"},
    )
    checks.append(_check(notebook_status == 200 and "notebook" in notebook and "audit" in notebook, f"notebook_template", f"status={notebook_status}"))

    audit_status, audit = route_request(
        "/api/unibot/notebook/audit",
        payload={"notebook": notebook.get("notebook", {})},
    )
    checks.append(
        _check(audit_status == 200 and audit.get("status") == "pass", "notebook_audit", f"status={audit_status}, audit={audit.get('status')}")
    )

    source_cards_status, source_cards = route_request("/api/unibot/source-cards", payload={"source_kind": None})
    checks.append(
        _check(
            source_cards_status == 200 and source_cards.get("count", 0) >= 10,
            "source_cards_catalog",
            f"status={source_cards_status}, count={source_cards.get('count')}",
        )
    )

    course_eval_status, course_eval = route_request("/api/unibot/course/eval/run", payload={})
    checks.append(
        _check(
            course_eval_status == 200
            and course_eval.get("status") == "pass"
            and course_eval.get("exam_deployment_status") == "not_cleared",
            "course_tutor_eval",
            f"status={course_eval_status}, result={course_eval.get('status')}, failed={course_eval.get('failed_count')}",
        )
    )

    compiler_status, compiler = route_request("/api/unibot/course/compiler-plan", payload={})
    checks.append(
        _check(
            compiler_status == 200
            and compiler.get("artifact_type") == "course_material_compiler_plan"
            and compiler.get("exam_deployment_status") == "not_cleared"
            and compiler.get("public_safety_status") == "pass",
            "course_material_compiler_plan",
            (
                f"status={compiler_status}, result={compiler.get('status')}, "
                f"records={compiler.get('counts', {}).get('record_count')}, exam={compiler.get('exam_deployment_status')}"
            ),
        )
    )

    extraction_status, extraction = route_request("/api/unibot/course/extraction-queue", payload={})
    checks.append(
        _check(
            extraction_status == 200
            and extraction.get("artifact_type") == "course_extraction_queue"
            and extraction.get("exam_deployment_status") == "not_cleared"
            and extraction.get("public_safety_status") == "pass"
            and extraction.get("rights_gate", {}).get("required_before_processing") is True,
            "course_extraction_queue",
            (
                f"status={extraction_status}, result={extraction.get('status')}, "
                f"jobs={extraction.get('counts', {}).get('job_count')}, rights={extraction.get('rights_gate', {}).get('authorized')}"
            ),
        )
    )

    decision_packet_status, decision_packet = route_request("/api/unibot/course/extraction-decision-packet", payload={})
    checks.append(
        _check(
            decision_packet_status == 200
            and decision_packet.get("artifact_type") == "course_extraction_rights_privacy_decision_packet"
            and decision_packet.get("public_safety_status") == "pass"
            and decision_packet.get("exam_deployment_status") == "not_cleared",
            "course_extraction_decision_packet",
            (
                f"status={decision_packet_status}, result={decision_packet.get('status')}, "
                f"reviewers={len(decision_packet.get('required_reviewer_roles', []))}"
            ),
        )
    )

    decision_validation_status, decision_validation = route_request(
        "/api/unibot/course/extraction-decision/validate",
        payload={
            "decision": {
                "decision_status": "approved_for_local_extraction",
                "scope": "local_private_course_extraction",
                "allowed_job_types": ["ocr", "transcription"],
                "storage_policy": "local_private_only",
                "cloud_processing_allowed": False,
                "raw_text_public_release_allowed": False,
                "human_review_before_tutor_index": True,
                "retention_decision": "synthetic retention fixture",
                "access_roles": ["project_owner", "approved_reviewer"],
                "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
                "decision_reference": "synthetic local extraction decision fixture",
            }
        },
    )
    checks.append(
        _check(
            decision_validation_status == 200
            and decision_validation.get("status") == "ok_authorizes_local_extraction"
            and decision_validation.get("approved_for_local_extraction") is True
            and decision_validation.get("public_safety_status") == "pass"
            and decision_validation.get("raw_decision_reference_stored") is False,
            "course_extraction_decision_validation",
            (
                f"status={decision_validation_status}, result={decision_validation.get('status')}, "
                f"issues={decision_validation.get('issues')}"
            ),
        )
    )

    operator_decision = {
        "decision_status": "approved_for_local_extraction",
        "scope": "local_private_course_extraction",
        "allowed_job_types": ["ocr", "transcription"],
        "storage_policy": "local_private_only",
        "cloud_processing_allowed": False,
        "raw_text_public_release_allowed": False,
        "human_review_before_tutor_index": True,
        "retention_decision": "synthetic retention fixture",
        "access_roles": ["project_owner", "approved_reviewer"],
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic local extraction operator decision fixture",
    }
    operator_status, operator_packet = route_request(
        "/api/unibot/course/extraction-operator-packet",
        payload={"decision_record": operator_decision, "job_limit": 3},
    )
    checks.append(
        _check(
            operator_status == 200
            and operator_packet.get("artifact_type") == "course_extraction_operator_packet"
            and operator_packet.get("exam_deployment_status") == "not_cleared"
            and operator_packet.get("public_safety_status") == "pass"
            and "receipt_contract" in operator_packet,
            "course_extraction_operator_packet",
            (
                f"status={operator_status}, result={operator_packet.get('status')}, "
                f"jobs={operator_packet.get('queue_summary', {}).get('job_count')}, "
                f"decision={operator_packet.get('decision_validation', {}).get('status')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as private_run_temp_dir:
        private_run_root = Path(private_run_temp_dir) / "materials"
        private_output_dir = Path(private_run_temp_dir) / "private"
        private_receipt_journal = Path(private_run_temp_dir) / "private_receipts.jsonl"
        write_private_extraction_smoke_fixture(private_run_root)
        private_run_status, private_run = route_request(
            "/api/unibot/course/private-extraction/run-batch",
            payload={
                "base_path": str(private_run_root),
                "decision_record": operator_decision,
                "receipt_journal_path": str(private_receipt_journal),
                "private_output_dir": str(private_output_dir),
                "max_jobs": 4,
            },
        )
    checks.append(
        _check(
            private_run_status == 200
            and private_run.get("artifact_type") == "course_private_extraction_run"
            and private_run.get("status") == "private_extraction_receipts_ready_for_human_review"
            and private_run.get("public_safety_status") == "pass"
            and private_run.get("counts", {}).get("extracted_private_count") == 3
            and private_run.get("counts", {}).get("stored_receipt_count") == 3
            and private_run.get("raw_text_returned") is False
            and private_run.get("local_paths_returned") is False,
            "private_extraction_run_batch",
            (
                f"status={private_run_status}, result={private_run.get('status')}, "
                f"extracted={private_run.get('counts', {}).get('extracted_private_count')}, "
                f"stored={private_run.get('counts', {}).get('stored_receipt_count')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as private_ocr_temp_dir:
        private_ocr_root = Path(private_ocr_temp_dir) / "materials"
        private_ocr_output_dir = Path(private_ocr_temp_dir) / "private"
        private_ocr_receipt_journal = Path(private_ocr_temp_dir) / "private_ocr_receipts.jsonl"
        write_private_extraction_smoke_fixture(private_ocr_root)
        private_ocr_status, private_ocr = route_request(
            "/api/unibot/course/private-extraction/run-batch",
            payload={
                "base_path": str(private_ocr_root),
                "decision_record": operator_decision,
                "receipt_journal_path": str(private_ocr_receipt_journal),
                "private_output_dir": str(private_ocr_output_dir),
                "max_jobs": 12,
                "job_types": ["ocr"],
            },
        )
    checks.append(
        _check(
            private_ocr_status == 200
            and private_ocr.get("artifact_type") == "course_private_extraction_run"
            and private_ocr.get("status") == "private_extraction_receipts_ready_for_human_review"
            and private_ocr.get("public_safety_status") == "pass"
            and private_ocr.get("counts", {}).get("extracted_private_count") == 3
            and private_ocr.get("counts", {}).get("stored_receipt_count") == 3
            and private_ocr.get("raw_text_returned") is False
            and private_ocr.get("local_paths_returned") is False,
            "private_extraction_run_ocr_filter",
            (
                f"status={private_ocr_status}, result={private_ocr.get('status')}, "
                f"extracted={private_ocr.get('counts', {}).get('extracted_private_count')}, "
                f"stored={private_ocr.get('counts', {}).get('stored_receipt_count')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as private_ocr_bridge_temp_dir:
        private_ocr_bridge_root = Path(private_ocr_bridge_temp_dir) / "materials"
        private_ocr_bridge_output_dir = Path(private_ocr_bridge_temp_dir) / "private"
        private_ocr_bridge_receipt_journal = Path(private_ocr_bridge_temp_dir) / "private_ocr_bridge_receipts.jsonl"
        private_ocr_bridge_decision_journal = Path(private_ocr_bridge_temp_dir) / "decision_records.jsonl"
        write_private_extraction_smoke_fixture(private_ocr_bridge_root)
        bridge_decision_status, bridge_decision = route_request(
            "/api/unibot/stakeholder/decision-record-journal/append",
            payload={
                "record_type": "local_extraction_decision",
                "record": operator_decision,
                "decision_record_journal_path": str(private_ocr_bridge_decision_journal),
            },
        )
        private_ocr_bridge_status, private_ocr_bridge = route_request(
            "/api/unibot/course/private-extraction/run-batch",
            payload={
                "base_path": str(private_ocr_bridge_root),
                "decision_record_journal_path": str(private_ocr_bridge_decision_journal),
                "receipt_journal_path": str(private_ocr_bridge_receipt_journal),
                "private_output_dir": str(private_ocr_bridge_output_dir),
                "max_jobs": 12,
                "job_types": ["ocr"],
            },
        )
    checks.append(
        _check(
            bridge_decision_status == 200
            and bridge_decision.get("status") == "stored"
            and private_ocr_bridge_status == 200
            and private_ocr_bridge.get("artifact_type") == "course_private_extraction_run"
            and private_ocr_bridge.get("status") == "private_extraction_receipts_ready_for_human_review"
            and private_ocr_bridge.get("decision_record_source") == "external_decision_record_journal"
            and private_ocr_bridge.get("decision_record_journal_used") is True
            and private_ocr_bridge.get("raw_decision_record_returned") is False
            and private_ocr_bridge.get("public_safety_status") == "pass"
            and private_ocr_bridge.get("counts", {}).get("extracted_private_count") == 3
            and private_ocr_bridge.get("counts", {}).get("stored_receipt_count") == 3
            and private_ocr_bridge.get("raw_text_returned") is False
            and private_ocr_bridge.get("local_paths_returned") is False,
            "private_extraction_run_ocr_journal_bridge",
            (
                f"decision={bridge_decision.get('status')}, status={private_ocr_bridge_status}, "
                f"result={private_ocr_bridge.get('status')}, "
                f"source={private_ocr_bridge.get('decision_record_source')}, "
                f"extracted={private_ocr_bridge.get('counts', {}).get('extracted_private_count')}, "
                f"stored={private_ocr_bridge.get('counts', {}).get('stored_receipt_count')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as local_intake_temp_dir:
        local_intake_root = Path(local_intake_temp_dir) / "materials"
        local_intake_decision_journal = Path(local_intake_temp_dir) / "decision_records.jsonl"
        local_intake_receipt_journal = Path(local_intake_temp_dir) / "receipts.jsonl"
        local_intake_output_dir = Path(local_intake_temp_dir) / "private"
        write_private_extraction_smoke_fixture(local_intake_root)
        local_intake_waiting_status, local_intake_waiting = route_request(
            "/api/unibot/course/extraction-decision/local-intake",
            payload={
                "base_path": str(local_intake_root),
                "decision_record_journal_path": str(local_intake_decision_journal),
                "receipt_journal_path": str(local_intake_receipt_journal),
                "job_types": ["ocr"],
            },
        )
        local_intake_record_status, local_intake_record = route_request(
            "/api/unibot/course/extraction-decision/local-intake/record",
            payload={
                "base_path": str(local_intake_root),
                "decision_record": operator_decision,
                "decision_record_journal_path": str(local_intake_decision_journal),
                "receipt_journal_path": str(local_intake_receipt_journal),
                "job_types": ["ocr"],
            },
        )
        local_intake_run_status, local_intake_run = route_request(
            "/api/unibot/course/private-extraction/run-batch",
            payload={
                "base_path": str(local_intake_root),
                "decision_record_journal_path": str(local_intake_decision_journal),
                "receipt_journal_path": str(local_intake_receipt_journal),
                "private_output_dir": str(local_intake_output_dir),
                "max_jobs": 12,
                "job_types": ["ocr"],
            },
        )
        local_intake_progress_status, local_intake_progress = route_request(
            "/api/unibot/course/extraction-progress-report",
            payload={
                "base_path": str(local_intake_root),
                "decision_record_journal_path": str(local_intake_decision_journal),
                "receipt_journal_path": str(local_intake_receipt_journal),
            },
        )
        local_intake_manifest_status, local_intake_manifest = route_request(
            "/api/unibot/course/extraction-manifest-update-plan",
            payload={
                "base_path": str(local_intake_root),
                "decision_record_journal_path": str(local_intake_decision_journal),
                "receipt_journal_path": str(local_intake_receipt_journal),
            },
        )
        local_intake_coverage_status, local_intake_coverage = route_request(
            "/api/unibot/course/tutor-coverage-plan",
            payload={
                "base_path": str(local_intake_root),
                "decision_record_journal_path": str(local_intake_decision_journal),
                "receipt_journal_path": str(local_intake_receipt_journal),
            },
        )
    checks.append(
        _check(
            local_intake_waiting_status == 200
            and local_intake_waiting.get("artifact_type") == "course_local_extraction_decision_intake_packet"
            and local_intake_waiting.get("status") == "waiting_for_local_rights_privacy_decision_record"
            and local_intake_waiting.get("public_safety_status") == "pass"
            and local_intake_waiting.get("raw_decision_record_returned") is False
            and local_intake_waiting.get("raw_text_returned") is False
            and local_intake_waiting.get("local_paths_returned") is False,
            "local_extraction_decision_intake_waiting",
            (
                f"status={local_intake_waiting_status}, result={local_intake_waiting.get('status')}, "
                f"ocr_jobs={local_intake_waiting.get('ocr_first_readiness', {}).get('job_count')}"
            ),
        )
    )
    checks.append(
        _check(
            local_intake_record_status == 200
            and local_intake_record.get("artifact_type") == "course_local_extraction_decision_record_result"
            and local_intake_record.get("status") == "decision_record_stored_hash_only"
            and local_intake_record.get("public_safety_status") == "pass"
            and local_intake_record.get("journal_event", {}).get("accepted_for_gate") is True
            and local_intake_record.get("raw_decision_record_returned") is False
            and local_intake_record.get("intake_packet", {}).get("decision_validation", {}).get("decision_record_source") == "external_decision_record_journal"
            and local_intake_record.get("intake_packet", {}).get("ocr_first_readiness", {}).get("status") == "ready_for_local_private_execution",
            "local_extraction_decision_intake_record",
            (
                f"status={local_intake_record_status}, result={local_intake_record.get('status')}, "
                f"source={local_intake_record.get('intake_packet', {}).get('decision_validation', {}).get('decision_record_source')}, "
                f"ocr={local_intake_record.get('intake_packet', {}).get('ocr_first_readiness', {}).get('job_count')}"
            ),
        )
    )
    checks.append(
        _check(
            local_intake_run_status == 200
            and local_intake_run.get("status") == "private_extraction_receipts_ready_for_human_review"
            and local_intake_progress_status == 200
            and local_intake_progress.get("status") == "receipts_ready_for_human_review"
            and local_intake_progress.get("decision_validation", {}).get("decision_record_source") == "external_decision_record_journal"
            and local_intake_manifest_status == 200
            and local_intake_manifest.get("status") == "waiting_for_reviewed_receipts"
            and local_intake_coverage_status == 200
            and local_intake_coverage.get("status") == "waiting_for_reviewed_manifest_candidates"
            and local_intake_progress.get("public_safety_status") == "pass"
            and local_intake_manifest.get("public_safety_status") == "pass"
            and local_intake_coverage.get("public_safety_status") == "pass",
            "local_extraction_decision_intake_post_run_reports",
            (
                f"run={local_intake_run.get('status')}, progress={local_intake_progress.get('status')}, "
                f"manifest={local_intake_manifest.get('status')}, coverage={local_intake_coverage.get('status')}, "
                f"review={local_intake_progress.get('receipt_summary', {}).get('ready_for_human_review_count')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as workspace_temp_dir:
        workspace_root = Path(workspace_temp_dir) / "materials"
        workspace_dir = Path(workspace_temp_dir) / "decision_workspace"
        workspace_decision_journal = Path(workspace_temp_dir) / "decision_records.jsonl"
        workspace_receipt_journal = Path(workspace_temp_dir) / "receipts.jsonl"
        workspace_review_journal = Path(workspace_temp_dir) / "reviews.jsonl"
        workspace_private_manifest = Path(workspace_temp_dir) / "private_manifest.json"
        workspace_manifest_apply_journal = Path(workspace_temp_dir) / "manifest_apply.jsonl"
        workspace_tutor_index = Path(workspace_temp_dir) / "private_tutor_index.hash_only.json"
        workspace_tutor_index_journal = Path(workspace_temp_dir) / "private_tutor_index_journal.jsonl"
        workspace_help_ledger = Path(workspace_temp_dir) / "help_ledger.jsonl"
        workspace_checkpoint_journal = Path(workspace_temp_dir) / "notebook_checkpoints.jsonl"
        workspace_timeline_export_receipt_journal = Path(workspace_temp_dir) / "timeline_export_receipts.jsonl"
        workspace_drill_loop_progress_journal = Path(workspace_temp_dir) / "drill_loop_progress.jsonl"
        workspace_private_output = Path(workspace_temp_dir) / "private"
        workspace_cell_source = "own_values = []\n# smallest local checkpoint\n"
        write_private_extraction_smoke_fixture(workspace_root)
        workspace_prepare_status, workspace_prepare = route_request(
            "/api/unibot/course/extraction-decision/workspace/prepare",
            payload={
                "base_path": str(workspace_root),
                "workspace_dir": str(workspace_dir),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_output_dir": str(workspace_private_output),
                "job_types": ["ocr"],
            },
        )
        workspace_record_status, workspace_record = route_request(
            "/api/unibot/course/extraction-decision/workspace/record",
            payload={
                "base_path": str(workspace_root),
                "decision_record": operator_decision,
                "workspace_dir": str(workspace_dir),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_output_dir": str(workspace_private_output),
                "job_types": ["ocr"],
            },
        )
        ocr_operator_wait_status, ocr_operator_wait = route_request(
            "/api/unibot/course/ocr-first/operator-run",
            payload={
                "base_path": str(workspace_root),
                "workspace_dir": str(workspace_dir),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_output_dir": str(workspace_private_output),
                "operator_confirmed_dry_run": False,
            },
        )
        ocr_operator_run_status, ocr_operator_run = route_request(
            "/api/unibot/course/ocr-first/operator-run",
            payload={
                "base_path": str(workspace_root),
                "workspace_dir": str(workspace_dir),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_output_dir": str(workspace_private_output),
                "operator_confirmed_dry_run": True,
            },
        )
        review_list_status, review_list = route_request(
            "/api/unibot/course/extraction-receipts/list",
            payload={"receipt_journal_path": str(workspace_receipt_journal)},
        )
        review_decisions = [
            {
                "job_id": str(receipt.get("job_id", "")),
                "review_decision": "accepted_for_private_tutor",
                "reviewer_roles": ["approved_reviewer"],
                "review_reference": f"synthetic smoke human review reference {index}",
                "review_notes": f"synthetic smoke human review note {index}",
                "raw_text_reviewed_locally": True,
                "source_card_ids": ["dfg-gwp"],
            }
            for index, receipt in enumerate(review_list.get("receipts_for_progress", []), start=1)
            if receipt.get("job_id")
        ]
        ocr_review_apply_status, ocr_review_apply = route_request(
            "/api/unibot/course/extraction-review/apply-plan",
            payload={
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "review_journal_path": str(workspace_review_journal),
                "review_decisions": review_decisions,
            },
        )
        manifest_apply_dry_status, manifest_apply_dry = route_request(
            "/api/unibot/course/extraction-manifest/apply-dry-run",
            payload={
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "operator_confirmed_manifest_apply": False,
            },
        )
        manifest_apply_confirmed_status, manifest_apply_confirmed = route_request(
            "/api/unibot/course/extraction-manifest/apply-dry-run",
            payload={
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "operator_confirmed_manifest_apply": True,
            },
        )
        tutor_index_dry_status, tutor_index_dry = route_request(
            "/api/unibot/course/tutor-index/dry-run",
            payload={
                "private_manifest_path": str(workspace_private_manifest),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "operator_confirmed_tutor_index_build": False,
            },
        )
        tutor_index_confirmed_status, tutor_index_confirmed = route_request(
            "/api/unibot/course/tutor-index/dry-run",
            payload={
                "private_manifest_path": str(workspace_private_manifest),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "operator_confirmed_tutor_index_build": True,
            },
        )
        tutor_index_response_status, tutor_index_response = route_request(
            "/api/unibot/course/tutor-index/respond-dry-run",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "tutor_index_path": str(workspace_tutor_index),
                "mode": "exam_controlled_gateway",
                "requested_help_level": "A2",
            },
        )
        private_tutor_flow_status, private_tutor_flow = route_request(
            "/api/unibot/course/private-tutor-use-flow/dry-run",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "operator_confirmed_manifest_apply": True,
                "operator_confirmed_tutor_index_build": True,
                "operator_confirmed_help_ledger_append": True,
                "requested_help_level": "A2",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        notebook_checkpoint_status, notebook_checkpoint = route_request(
            "/api/unibot/exam-workspace/notebook-checkpoint/adapt",
            payload={
                "task_id": "smoke-cell-list-check",
                "skill_tag": "python_lists",
                "source_card_ids": ["dfg-gwp"],
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "requested_help_level": "A2",
                "prediction_present": True,
                "retrieval_response_present": True,
                "notebook_action_present": True,
                "reflection_present": True,
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "operator_confirmed_checkpoint_store": False,
            },
        )
        workspace_exam_course_id = "smoke-exam-workspace"
        shutil.rmtree(ROOT / "unibot" / "knowledge" / "exam_workspace" / workspace_exam_course_id, ignore_errors=True)
        exam_workspace_run_status, exam_workspace_run = route_request(
            "/api/unibot/exam-workspace/run-dry-run",
            payload={
                "course_id": workspace_exam_course_id,
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "operator_confirmed_exam_workspace_run": True,
                "operator_confirmed_manifest_apply": False,
                "operator_confirmed_tutor_index_build": False,
                "operator_confirmed_help_ledger_append": False,
                "operator_confirmed_exam_ledger_append": True,
                "requested_help_level": "A2",
                "cell_index": 0,
                "cell_id": "smoke-cell-list-check",
                "cell_type": "code",
                "cell_source": workspace_cell_source,
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        material_coverage_run_status, material_coverage_run = route_request(
            "/api/unibot/course/material-coverage/run",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "focus_query": "Python Listen",
            },
        )
        exam_skill_drilldown_status, exam_skill_drilldown = route_request(
            "/api/unibot/course/exam-skill-drilldown",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "focus_query": "Python Listen",
                "selected_skill_tag": "python_lists",
            },
        )
        skill_to_workspace_status, skill_to_workspace = route_request(
            "/api/unibot/course/skill-to-workspace-live-flow",
            payload={
                "course_id": workspace_exam_course_id,
                "query": "Diese private Startfrage darf nicht im Report stehen.",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "focus_query": "Python Listen",
                "selected_skill_tag": "python_lists",
                "requested_help_level": "A5",
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        exam_workspace_launch_status, exam_workspace_launch = route_request(
            "/api/unibot/exam-workspace/launch-flow/dry-run",
            payload={
                "course_id": workspace_exam_course_id,
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "focus_query": "Python Listen",
                "requested_help_level": "A2",
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        exam_workspace_operator_status, exam_workspace_operator = route_request(
            "/api/unibot/exam-workspace/operator-run",
            payload={
                "course_id": workspace_exam_course_id,
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "focus_query": "Python Listen",
                "requested_help_level": "A2",
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        exam_session_console_status, exam_session_console = route_request(
            "/api/unibot/exam-workspace/session-console",
            payload={
                "course_id": workspace_exam_course_id,
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "selected_skill_tag": "python_lists",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "focus_query": "python_lists",
                "requested_help_level": "A2",
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "repeat_run_index": 1,
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        exam_run_history_status, exam_run_history = route_request(
            "/api/unibot/exam-workspace/run-history-export-review",
            payload={
                "console_reports": [exam_session_console],
                "console_receipts": [exam_session_console.get("session_console_receipt", {})],
                "build_current_console": False,
            },
        )
        course_exam_dashboard_status, course_exam_dashboard = route_request(
            "/api/unibot/course/exam-coverage-dashboard",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "focus_query": "Python Listen",
                "selected_skill_tag": "python_lists",
                "console_reports": [exam_session_console],
                "console_receipts": [exam_session_console.get("session_console_receipt", {})],
                "build_current_console": False,
            },
        )
        per_skill_router_status, per_skill_router = route_request(
            "/api/unibot/course/per-skill-action-router",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "focus_query": "Python Listen",
                "selected_skill_tag": "python_lists",
                "dashboard_report": course_exam_dashboard,
                "console_reports": [exam_session_console],
                "console_receipts": [exam_session_console.get("session_console_receipt", {})],
                "build_current_console": False,
            },
        )
        routed_executor_status, routed_executor = route_request(
            "/api/unibot/course/routed-action-executor",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "focus_query": "Python Listen",
                "selected_skill_tag": "python_lists",
                "router_report": per_skill_router,
                "selected_route": per_skill_router.get("selected_route", {}),
                "console_reports": [exam_session_console],
                "console_receipts": [exam_session_console.get("session_console_receipt", {})],
                "requested_help_level": "A2",
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "operator_confirmed_checkpoint_store": False,
                "operator_confirmed_exam_workspace_run": False,
                "operator_confirmed_manifest_apply": False,
                "operator_confirmed_tutor_index_build": False,
                "operator_confirmed_help_ledger_append": False,
                "operator_confirmed_exam_ledger_append": False,
                "operator_confirmed_private_extraction_run": False,
                "operator_confirmed_video_transcription_run": False,
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        exam_run_packet_status, exam_run_packet = route_request(
            "/api/unibot/course/exam-run-packet",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "focus_query": "Python Listen",
                "selected_skill_tag": "python_lists",
                "dashboard_report": course_exam_dashboard,
                "router_report": per_skill_router,
                "executor_report": routed_executor,
                "console_reports": [exam_session_console],
                "console_receipts": [exam_session_console.get("session_console_receipt", {})],
                "requested_help_level": "A2",
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        exam_packet_timeline_status, exam_packet_timeline = route_request(
            "/api/unibot/course/exam-packet-timeline",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "focus_query": "Python Listen",
                "selected_skill_tag": "python_lists",
                "dashboard_report": course_exam_dashboard,
                "router_report": per_skill_router,
                "executor_report": routed_executor,
                "exam_run_packets": [exam_run_packet],
                "exam_run_packet": exam_run_packet,
                "console_reports": [exam_session_console],
                "console_receipts": [exam_session_console.get("session_console_receipt", {})],
                "requested_help_level": "A2",
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        timeline_export_review_status, timeline_export_review = route_request(
            "/api/unibot/course/timeline-export-review-packet",
            payload={
                "query": "Wie pruefe ich Python Listen fuer den naechsten eigenen Check?",
                "base_path": str(workspace_root),
                "decision_record_journal_path": str(workspace_decision_journal),
                "receipt_journal_path": str(workspace_receipt_journal),
                "private_manifest_path": str(workspace_private_manifest),
                "manifest_apply_journal_path": str(workspace_manifest_apply_journal),
                "tutor_index_path": str(workspace_tutor_index),
                "tutor_index_journal_path": str(workspace_tutor_index_journal),
                "ledger_path": str(workspace_help_ledger),
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "focus_query": "Python Listen",
                "selected_skill_tag": "python_lists",
                "dashboard_report": course_exam_dashboard,
                "router_report": per_skill_router,
                "executor_report": routed_executor,
                "exam_run_packets": [exam_run_packet],
                "exam_run_packet": exam_run_packet,
                "exam_packet_timelines": [exam_packet_timeline],
                "exam_packet_timeline": exam_packet_timeline,
                "console_reports": [exam_session_console],
                "console_receipts": [exam_session_console.get("session_console_receipt", {})],
                "requested_help_level": "A2",
                "student_reflection": "Ich pruefe zuerst die erwartete Struktur selbst.",
                "cell_source": workspace_cell_source,
                "cell_index": 0,
                "cell_type": "code",
                "operator_confirmed_local_export_receipt": False,
                "study_receipt": {
                    "prediction_present": True,
                    "notebook_action_present": True,
                    "reflection_present": True,
                },
            },
        )
        timeline_export_receipt_preview_status, timeline_export_receipt_preview = route_request(
            "/api/unibot/course/timeline-export-receipt-journal/append",
            payload={
                "timeline_export_receipt_journal_path": str(workspace_timeline_export_receipt_journal),
                "review_packet": timeline_export_review,
                "operator_confirmed_timeline_export_receipt_journal_append": False,
            },
        )
        timeline_export_receipt_append_status, timeline_export_receipt_append = route_request(
            "/api/unibot/course/timeline-export-receipt-journal/append",
            payload={
                "timeline_export_receipt_journal_path": str(workspace_timeline_export_receipt_journal),
                "review_packet": timeline_export_review,
                "operator_confirmed_timeline_export_receipt_journal_append": True,
            },
        )
        timeline_export_receipt_summary_status, timeline_export_receipt_summary = route_request(
            "/api/unibot/course/timeline-export-receipt-journal/summary",
            payload={
                "timeline_export_receipt_journal_path": str(workspace_timeline_export_receipt_journal),
            },
        )
        review_chain_integrity_status, review_chain_integrity = route_request(
            "/api/unibot/course/review-chain-integrity-check",
            payload={
                "selected_skill_tag": "python_lists",
                "exam_run_packet": exam_run_packet,
                "exam_packet_timeline": exam_packet_timeline,
                "timeline_export_review_packet": timeline_export_review,
                "timeline_export_receipt_journal_append": timeline_export_receipt_append,
                "timeline_export_receipt_journal_summary": timeline_export_receipt_summary,
                "timeline_export_receipt_journal_path": str(workspace_timeline_export_receipt_journal),
            },
        )
        skill_to_workspace_carryover_status, skill_to_workspace_carryover = route_request(
            "/api/unibot/course/skill-to-workspace-session-carryover",
            payload={
                "skill_to_workspace_live_flow": skill_to_workspace,
                "review_chain_integrity_check": review_chain_integrity,
                "timeline_export_review_packet": timeline_export_review,
                "timeline_export_receipt_journal_summary": timeline_export_receipt_summary,
                "repeat_run_index": 1,
            },
        )
        python_exam_tutor_drill_pack_status, python_exam_tutor_drill_pack = route_request(
            "/api/unibot/course/python-exam-source-grounded-tutor-drill-pack",
            payload={
                "selected_skill_tag": "python_lists",
                "course_exam_coverage_dashboard": course_exam_dashboard,
                "exam_skill_drilldown": exam_skill_drilldown,
                "skill_to_workspace_session_carryover": skill_to_workspace_carryover,
                "max_drills": 1,
            },
        )
        python_exam_drill_session_runner_status, python_exam_drill_session_runner = route_request(
            "/api/unibot/course/python-exam-drill-session-runner",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_tutor_drill_pack": python_exam_tutor_drill_pack,
                "skill_to_workspace_session_carryover": skill_to_workspace_carryover,
                "cell_source": "runner_private_attempt = []\n# local only\n",
                "student_reflection": "Ich habe den Microtask zuerst vorhergesagt und dann lokal geprueft.",
                "checkpoint_journal_path": str(workspace_checkpoint_journal),
                "operator_confirmed_checkpoint_store": False,
            },
        )
        python_exam_drill_session_review_loop_status, python_exam_drill_session_review_loop = route_request(
            "/api/unibot/course/python-exam-drill-session-review-loop",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_drill_session_runner": python_exam_drill_session_runner,
                "python_exam_tutor_drill_pack": python_exam_tutor_drill_pack,
                "previous_review_loops": [],
            },
        )
        python_exam_drill_loop_control_panel_status, python_exam_drill_loop_control_panel = route_request(
            "/api/unibot/course/python-exam-drill-loop-control-panel",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_tutor_drill_pack": python_exam_tutor_drill_pack,
                "skill_to_workspace_session_carryover": skill_to_workspace_carryover,
                "python_exam_drill_session_runner": python_exam_drill_session_runner,
                "python_exam_drill_session_review_loop": python_exam_drill_session_review_loop,
                "previous_review_loops": [],
            },
        )
        python_exam_drill_loop_progress_journal_status, python_exam_drill_loop_progress_journal = route_request(
            "/api/unibot/course/python-exam-drill-loop-progress-journal",
            payload={
                "python_exam_drill_loop_control_panel": python_exam_drill_loop_control_panel,
                "progress_journal_path": str(workspace_drill_loop_progress_journal),
                "operator_confirmed_progress_journal_append": False,
            },
        )
        python_exam_resume_launcher_status, python_exam_resume_launcher = route_request(
            "/api/unibot/course/python-exam-resume-launcher",
            payload={
                "python_exam_drill_loop_progress_journal": python_exam_drill_loop_progress_journal,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_active_study_loop_dashboard_status, python_exam_active_study_loop_dashboard = route_request(
            "/api/unibot/course/python-exam-active-study-loop-dashboard",
            payload={
                "course_exam_coverage_dashboard": course_exam_dashboard,
                "python_exam_tutor_drill_pack": python_exam_tutor_drill_pack,
                "python_exam_drill_loop_control_panel": python_exam_drill_loop_control_panel,
                "python_exam_drill_loop_progress_journal": python_exam_drill_loop_progress_journal,
                "python_exam_resume_launcher": python_exam_resume_launcher,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_active_study_guided_runner_status, python_exam_active_study_guided_runner = route_request(
            "/api/unibot/course/python-exam-active-study-guided-runner",
            payload={
                "python_exam_active_study_loop_dashboard": python_exam_active_study_loop_dashboard,
                "python_exam_resume_launcher": python_exam_resume_launcher,
                "python_exam_drill_loop_control_panel": python_exam_drill_loop_control_panel,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_guided_action_execution_bridge_status, python_exam_guided_action_execution_bridge = route_request(
            "/api/unibot/course/python-exam-guided-action-execution-bridge",
            payload={
                "python_exam_active_study_guided_runner": python_exam_active_study_guided_runner,
                "python_exam_drill_loop_control_panel": python_exam_drill_loop_control_panel,
                "python_exam_drill_loop_progress_journal": python_exam_drill_loop_progress_journal,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_safe_cycle_console_status, python_exam_safe_cycle_console = route_request(
            "/api/unibot/course/python-exam-safe-cycle-console",
            payload={
                "python_exam_active_study_loop_dashboard": python_exam_active_study_loop_dashboard,
                "python_exam_active_study_guided_runner": python_exam_active_study_guided_runner,
                "python_exam_guided_action_execution_bridge": python_exam_guided_action_execution_bridge,
                "python_exam_drill_loop_control_panel": python_exam_drill_loop_control_panel,
                "python_exam_drill_loop_progress_journal": python_exam_drill_loop_progress_journal,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_safe_cycle_operator_gate_status, python_exam_safe_cycle_operator_gate = route_request(
            "/api/unibot/course/python-exam-safe-cycle-operator-gate",
            payload={
                "python_exam_safe_cycle_console": python_exam_safe_cycle_console,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_operator_gate_decision_receipt_status, python_exam_operator_gate_decision_receipt = route_request(
            "/api/unibot/course/python-exam-operator-gate-decision-receipt",
            payload={
                "python_exam_safe_cycle_operator_gate": python_exam_safe_cycle_operator_gate,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_local_cycle_start_packet_status, python_exam_local_cycle_start_packet = route_request(
            "/api/unibot/course/python-exam-local-cycle-start-packet",
            payload={
                "python_exam_safe_cycle_console": python_exam_safe_cycle_console,
                "python_exam_safe_cycle_operator_gate": python_exam_safe_cycle_operator_gate,
                "python_exam_operator_gate_decision_receipt": python_exam_operator_gate_decision_receipt,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_local_cycle_readiness_review_status, python_exam_local_cycle_readiness_review = route_request(
            "/api/unibot/course/python-exam-local-cycle-readiness-review",
            payload={
                "python_exam_local_cycle_start_packet": python_exam_local_cycle_start_packet,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_local_cycle_readiness_handoff_status, python_exam_local_cycle_readiness_handoff = route_request(
            "/api/unibot/course/python-exam-local-cycle-readiness-handoff",
            payload={
                "python_exam_local_cycle_readiness_review": python_exam_local_cycle_readiness_review,
                "python_exam_local_cycle_start_packet": python_exam_local_cycle_start_packet,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_local_cycle_workspace_card_status, python_exam_local_cycle_workspace_card = route_request(
            "/api/unibot/course/python-exam-local-cycle-operator-workspace-card",
            payload={
                "python_exam_local_cycle_readiness_review": python_exam_local_cycle_readiness_review,
                "python_exam_local_cycle_readiness_handoff": python_exam_local_cycle_readiness_handoff,
                "python_exam_local_cycle_start_packet": python_exam_local_cycle_start_packet,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_local_cycle_chain_snapshot_status, python_exam_local_cycle_chain_snapshot = route_request(
            "/api/unibot/course/python-exam-local-cycle-chain-snapshot",
            payload={
                "python_exam_local_cycle_readiness_review": python_exam_local_cycle_readiness_review,
                "python_exam_local_cycle_readiness_handoff": python_exam_local_cycle_readiness_handoff,
                "python_exam_local_cycle_operator_workspace_card": python_exam_local_cycle_workspace_card,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_confirmation_console_status, python_exam_manual_confirmation_console = route_request(
            "/api/unibot/course/python-exam-local-cycle-manual-confirmation-console",
            payload={
                "python_exam_local_cycle_readiness_review": python_exam_local_cycle_readiness_review,
                "python_exam_local_cycle_readiness_handoff": python_exam_local_cycle_readiness_handoff,
                "python_exam_local_cycle_operator_workspace_card": python_exam_local_cycle_workspace_card,
                "python_exam_local_cycle_chain_snapshot": python_exam_local_cycle_chain_snapshot,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_cycle_launch_receipt_status, python_exam_manual_cycle_launch_receipt = route_request(
            "/api/unibot/course/python-exam-manual-cycle-launch-receipt",
            payload={
                "python_exam_manual_confirmation_console": python_exam_manual_confirmation_console,
                "python_exam_local_cycle_chain_snapshot": python_exam_local_cycle_chain_snapshot,
                "python_exam_local_cycle_operator_workspace_card": python_exam_local_cycle_workspace_card,
                "python_exam_local_cycle_readiness_handoff": python_exam_local_cycle_readiness_handoff,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_cycle_evidence_binder_status, python_exam_manual_cycle_evidence_binder = route_request(
            "/api/unibot/course/python-exam-manual-cycle-evidence-binder",
            payload={
                "python_exam_manual_cycle_launch_receipt": python_exam_manual_cycle_launch_receipt,
                "python_exam_manual_confirmation_console": python_exam_manual_confirmation_console,
                "python_exam_local_cycle_chain_snapshot": python_exam_local_cycle_chain_snapshot,
                "python_exam_local_cycle_operator_workspace_card": python_exam_local_cycle_workspace_card,
                "python_exam_local_cycle_readiness_review": python_exam_local_cycle_readiness_review,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_post_cycle_receipt_intake_status, python_exam_manual_post_cycle_receipt_intake = route_request(
            "/api/unibot/course/python-exam-manual-post-cycle-receipt-intake",
            payload={
                "python_exam_manual_cycle_evidence_binder": python_exam_manual_cycle_evidence_binder,
                "python_exam_manual_cycle_launch_receipt": python_exam_manual_cycle_launch_receipt,
                "python_exam_manual_confirmation_console": python_exam_manual_confirmation_console,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_cycle_closure_ledger_status, python_exam_manual_cycle_closure_ledger = route_request(
            "/api/unibot/course/python-exam-manual-cycle-closure-ledger",
            payload={
                "python_exam_manual_post_cycle_receipt_intake": python_exam_manual_post_cycle_receipt_intake,
                "python_exam_manual_cycle_evidence_binder": python_exam_manual_cycle_evidence_binder,
                "python_exam_manual_cycle_launch_receipt": python_exam_manual_cycle_launch_receipt,
                "python_exam_manual_confirmation_console": python_exam_manual_confirmation_console,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_cycle_review_timeline_status, python_exam_manual_cycle_review_timeline = route_request(
            "/api/unibot/course/python-exam-manual-cycle-review-timeline",
            payload={
                "python_exam_manual_cycle_closure_ledger": python_exam_manual_cycle_closure_ledger,
                "python_exam_manual_post_cycle_receipt_intake": python_exam_manual_post_cycle_receipt_intake,
                "python_exam_manual_cycle_evidence_binder": python_exam_manual_cycle_evidence_binder,
                "python_exam_manual_cycle_launch_receipt": python_exam_manual_cycle_launch_receipt,
                "python_exam_manual_confirmation_console": python_exam_manual_confirmation_console,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_cycle_review_packet_status, python_exam_manual_cycle_review_packet = route_request(
            "/api/unibot/course/python-exam-manual-cycle-review-packet",
            payload={
                "python_exam_manual_cycle_review_timeline": python_exam_manual_cycle_review_timeline,
                "python_exam_manual_cycle_closure_ledger": python_exam_manual_cycle_closure_ledger,
                "python_exam_manual_post_cycle_receipt_intake": python_exam_manual_post_cycle_receipt_intake,
                "python_exam_manual_cycle_evidence_binder": python_exam_manual_cycle_evidence_binder,
                "python_exam_manual_cycle_launch_receipt": python_exam_manual_cycle_launch_receipt,
                "python_exam_manual_confirmation_console": python_exam_manual_confirmation_console,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_review_export_preview_status, python_exam_manual_review_export_preview = route_request(
            "/api/unibot/course/python-exam-manual-review-export-preview",
            payload={
                "python_exam_manual_cycle_review_packet": python_exam_manual_cycle_review_packet,
                "python_exam_manual_cycle_review_timeline": python_exam_manual_cycle_review_timeline,
                "python_exam_manual_cycle_closure_ledger": python_exam_manual_cycle_closure_ledger,
                "python_exam_manual_post_cycle_receipt_intake": python_exam_manual_post_cycle_receipt_intake,
                "python_exam_manual_cycle_evidence_binder": python_exam_manual_cycle_evidence_binder,
                "python_exam_manual_cycle_launch_receipt": python_exam_manual_cycle_launch_receipt,
                "python_exam_manual_confirmation_console": python_exam_manual_confirmation_console,
                "selected_skill_tag": "python_lists",
            },
        )
        (
            python_exam_manual_review_export_authorization_gate_status,
            python_exam_manual_review_export_authorization_gate,
        ) = route_request(
            "/api/unibot/course/python-exam-manual-review-export-authorization-gate",
            payload={
                "python_exam_manual_review_export_preview": python_exam_manual_review_export_preview,
                "python_exam_manual_cycle_review_packet": python_exam_manual_cycle_review_packet,
                "python_exam_manual_cycle_review_timeline": python_exam_manual_cycle_review_timeline,
                "python_exam_manual_cycle_closure_ledger": python_exam_manual_cycle_closure_ledger,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_export_review_queue_status, python_exam_manual_export_review_queue = route_request(
            "/api/unibot/course/python-exam-manual-export-review-queue",
            payload={
                "python_exam_manual_review_export_authorization_gate": python_exam_manual_review_export_authorization_gate,
                "python_exam_manual_review_export_preview": python_exam_manual_review_export_preview,
                "python_exam_manual_cycle_review_packet": python_exam_manual_cycle_review_packet,
                "python_exam_manual_cycle_review_timeline": python_exam_manual_cycle_review_timeline,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_export_reviewer_packet_status, python_exam_manual_export_reviewer_packet = route_request(
            "/api/unibot/course/python-exam-manual-export-reviewer-packet",
            payload={
                "python_exam_manual_export_review_queue": python_exam_manual_export_review_queue,
                "python_exam_manual_review_export_authorization_gate": python_exam_manual_review_export_authorization_gate,
                "python_exam_manual_review_export_preview": python_exam_manual_review_export_preview,
                "python_exam_manual_cycle_review_packet": python_exam_manual_cycle_review_packet,
                "python_exam_manual_cycle_review_timeline": python_exam_manual_cycle_review_timeline,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_archive_decision_draft_status, python_exam_manual_archive_decision_draft = route_request(
            "/api/unibot/course/python-exam-manual-archive-decision-draft",
            payload={
                "python_exam_manual_export_reviewer_packet": python_exam_manual_export_reviewer_packet,
                "python_exam_manual_export_review_queue": python_exam_manual_export_review_queue,
                "python_exam_manual_review_export_authorization_gate": python_exam_manual_review_export_authorization_gate,
                "python_exam_manual_review_export_preview": python_exam_manual_review_export_preview,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_manual_final_review_handoff_status, python_exam_manual_final_review_handoff = route_request(
            "/api/unibot/course/python-exam-manual-final-review-handoff",
            payload={
                "python_exam_manual_archive_decision_draft": python_exam_manual_archive_decision_draft,
                "python_exam_manual_export_reviewer_packet": python_exam_manual_export_reviewer_packet,
                "python_exam_manual_export_review_queue": python_exam_manual_export_review_queue,
                "python_exam_manual_review_export_authorization_gate": python_exam_manual_review_export_authorization_gate,
                "selected_skill_tag": "python_lists",
            },
        )
        (
            python_exam_manual_final_review_receipt_ledger_status,
            python_exam_manual_final_review_receipt_ledger,
        ) = route_request(
            "/api/unibot/course/python-exam-manual-final-review-receipt-ledger",
            payload={
                "python_exam_manual_final_review_handoff": python_exam_manual_final_review_handoff,
                "python_exam_manual_archive_decision_draft": python_exam_manual_archive_decision_draft,
                "python_exam_manual_export_reviewer_packet": python_exam_manual_export_reviewer_packet,
                "python_exam_manual_export_review_queue": python_exam_manual_export_review_queue,
                "selected_skill_tag": "python_lists",
            },
        )
        (
            python_exam_final_review_ledger_integrity_gate_status,
            python_exam_final_review_ledger_integrity_gate,
        ) = route_request(
            "/api/unibot/course/python-exam-final-review-ledger-integrity-gate",
            payload={
                "python_exam_manual_final_review_receipt_ledger": python_exam_manual_final_review_receipt_ledger,
                "python_exam_manual_final_review_handoff": python_exam_manual_final_review_handoff,
                "python_exam_manual_archive_decision_draft": python_exam_manual_archive_decision_draft,
                "python_exam_manual_export_reviewer_packet": python_exam_manual_export_reviewer_packet,
                "python_exam_manual_export_review_queue": python_exam_manual_export_review_queue,
                "selected_skill_tag": "python_lists",
            },
        )
        (
            python_exam_final_manual_review_console_status,
            python_exam_final_manual_review_console,
        ) = route_request(
            "/api/unibot/course/python-exam-final-manual-review-console",
            payload={
                "python_exam_final_review_ledger_integrity_gate": python_exam_final_review_ledger_integrity_gate,
                "python_exam_manual_final_review_receipt_ledger": python_exam_manual_final_review_receipt_ledger,
                "python_exam_manual_final_review_handoff": python_exam_manual_final_review_handoff,
                "python_exam_manual_archive_decision_draft": python_exam_manual_archive_decision_draft,
                "python_exam_manual_export_reviewer_packet": python_exam_manual_export_reviewer_packet,
                "python_exam_manual_export_review_queue": python_exam_manual_export_review_queue,
                "selected_skill_tag": "python_lists",
            },
        )
        (
            python_exam_final_manual_review_action_lock_status,
            python_exam_final_manual_review_action_lock,
        ) = route_request(
            "/api/unibot/course/python-exam-final-manual-review-action-lock",
            payload={
                "python_exam_final_manual_review_console": python_exam_final_manual_review_console,
                "python_exam_final_review_ledger_integrity_gate": python_exam_final_review_ledger_integrity_gate,
                "python_exam_manual_final_review_receipt_ledger": python_exam_manual_final_review_receipt_ledger,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_readiness_status, python_exam_readiness = route_request(
            "/api/unibot/course/python-exam-readiness-console",
            payload={
                "selected_skill_tag": "python_lists",
                "course_exam_coverage_dashboard": course_exam_dashboard,
                "exam_skill_drilldown": exam_skill_drilldown,
                "review_chain_integrity_check": review_chain_integrity,
                "timeline_export_receipt_journal_summary": timeline_export_receipt_summary,
            },
        )
        python_exam_cockpit_status, python_exam_cockpit = route_request(
            "/api/unibot/course/python-exam-cockpit-flow",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_readiness_console": python_exam_readiness,
                "exam_skill_drilldown": exam_skill_drilldown,
                "exam_workspace_operator_run": exam_workspace_operator,
                "exam_workspace_session_console": exam_session_console,
                "notebook_checkpoint": notebook_checkpoint,
                "review_chain_integrity_check": review_chain_integrity,
                "timeline_export_review_packet": timeline_export_review,
                "timeline_export_receipt_journal_summary": timeline_export_receipt_summary,
            },
        )
        python_exam_live_control_status, python_exam_live_control = route_request(
            "/api/unibot/course/python-exam-live-control-surface",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_cockpit_flow": python_exam_cockpit,
                "python_exam_readiness_console": python_exam_readiness,
                "exam_skill_drilldown": exam_skill_drilldown,
                "exam_workspace_operator_run": exam_workspace_operator,
                "exam_workspace_session_console": exam_session_console,
                "notebook_checkpoint": notebook_checkpoint,
                "review_chain_integrity_check": review_chain_integrity,
                "timeline_export_review_packet": timeline_export_review,
                "timeline_export_receipt_journal_summary": timeline_export_receipt_summary,
            },
        )
        python_exam_evidence_export_preview_status, python_exam_evidence_export_preview = route_request(
            "/api/unibot/course/python-exam-evidence-export-preview",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_live_control_surface": python_exam_live_control,
                "python_exam_cockpit_flow": python_exam_cockpit,
                "python_exam_readiness_console": python_exam_readiness,
                "exam_skill_drilldown": exam_skill_drilldown,
                "exam_workspace_operator_run": exam_workspace_operator,
                "exam_workspace_session_console": exam_session_console,
                "notebook_checkpoint": notebook_checkpoint,
                "review_chain_integrity_check": review_chain_integrity,
                "timeline_export_review_packet": timeline_export_review,
                "timeline_export_receipt_journal_summary": timeline_export_receipt_summary,
            },
        )
        workspace_python_exam_export_draft_dir = Path(workspace_temp_dir) / "python_exam_export_drafts"
        python_exam_local_export_draft_preview_status, python_exam_local_export_draft_preview = route_request(
            "/api/unibot/course/python-exam-confirmed-local-export-draft",
            payload={
                "python_exam_evidence_export_preview": python_exam_evidence_export_preview,
                "export_draft_dir": str(workspace_python_exam_export_draft_dir),
                "operator_confirmed_local_export_draft_write": False,
            },
        )
        python_exam_local_export_draft_confirmed_status, python_exam_local_export_draft_confirmed = route_request(
            "/api/unibot/course/python-exam-confirmed-local-export-draft",
            payload={
                "python_exam_evidence_export_preview": python_exam_evidence_export_preview,
                "export_draft_dir": str(workspace_python_exam_export_draft_dir),
                "operator_confirmed_local_export_draft_write": True,
            },
        )
        local_export_draft_package_dir = (
            workspace_python_exam_export_draft_dir
            / str(python_exam_local_export_draft_confirmed.get("draft_receipt", {}).get("draft_package_id", "missing"))
        )
        local_export_draft_file_names = (
            sorted(path.name for path in local_export_draft_package_dir.iterdir())
            if local_export_draft_package_dir.exists()
            else []
        )
        python_exam_draft_review_console_status, python_exam_draft_review_console = route_request(
            "/api/unibot/course/python-exam-draft-package-review-console",
            payload={
                "python_exam_confirmed_local_export_draft": python_exam_local_export_draft_confirmed,
                "python_exam_evidence_export_preview": python_exam_evidence_export_preview,
            },
        )
        python_exam_human_handoff_status, python_exam_human_handoff = route_request(
            "/api/unibot/course/python-exam-human-handoff-packet",
            payload={
                "python_exam_draft_package_review_console": python_exam_draft_review_console,
                "python_exam_evidence_export_preview": python_exam_evidence_export_preview,
                "python_exam_confirmed_local_export_draft": python_exam_local_export_draft_confirmed,
            },
        )
        python_exam_full_rehearsal_status, python_exam_full_rehearsal = route_request(
            "/api/unibot/course/python-exam-full-local-rehearsal-pack",
            payload={
                "selected_skill_tag": "python_lists",
                "exam_skill_drilldown": exam_skill_drilldown,
                "python_exam_local_cycle_readiness_review": python_exam_local_cycle_readiness_review,
                "python_exam_local_cycle_readiness_handoff": python_exam_local_cycle_readiness_handoff,
                "python_exam_local_cycle_operator_workspace_card": python_exam_local_cycle_workspace_card,
                "python_exam_local_cycle_chain_snapshot": python_exam_local_cycle_chain_snapshot,
                "exam_workspace_operator_run": exam_workspace_operator,
                "exam_workspace_session_console": exam_session_console,
                "exam_workspace_run_history_export_review": exam_run_history,
                "course_exam_coverage_dashboard": course_exam_dashboard,
                "course_per_skill_action_router": per_skill_router,
                "routed_action_executor": routed_executor,
                "exam_run_packet": exam_run_packet,
                "exam_packet_timeline": exam_packet_timeline,
                "timeline_export_review_packet": timeline_export_review,
                "timeline_export_receipt_journal_summary": timeline_export_receipt_summary,
                "review_chain_integrity_check": review_chain_integrity,
                "python_exam_readiness_console": python_exam_readiness,
                "python_exam_cockpit_flow": python_exam_cockpit,
                "python_exam_live_control_surface": python_exam_live_control,
                "python_exam_evidence_export_preview": python_exam_evidence_export_preview,
                "python_exam_confirmed_local_export_draft": python_exam_local_export_draft_preview,
                "python_exam_draft_package_review_console": python_exam_draft_review_console,
                "python_exam_human_handoff_packet": python_exam_human_handoff,
            },
        )
        python_exam_locked_final_review_board_status, python_exam_locked_final_review_board = route_request(
            "/api/unibot/course/python-exam-locked-final-review-board",
            payload={
                "python_exam_final_manual_review_action_lock": python_exam_final_manual_review_action_lock,
                "python_exam_final_manual_review_console": python_exam_final_manual_review_console,
                "python_exam_final_review_ledger_integrity_gate": python_exam_final_review_ledger_integrity_gate,
                "python_exam_manual_final_review_receipt_ledger": python_exam_manual_final_review_receipt_ledger,
                "python_exam_draft_package_review_console": python_exam_draft_review_console,
                "python_exam_human_handoff_packet": python_exam_human_handoff,
                "python_exam_full_local_rehearsal_pack": python_exam_full_rehearsal,
                "selected_skill_tag": "python_lists",
            },
        )
        python_exam_gap_coach_status, python_exam_gap_coach = route_request(
            "/api/unibot/course/python-exam-rehearsal-playback-gap-coach",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_full_local_rehearsal_pack": python_exam_full_rehearsal,
            },
        )
        python_exam_guided_loop_status, python_exam_guided_loop = route_request(
            "/api/unibot/course/python-exam-gap-coach-guided-rehearsal-loop",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_rehearsal_playback_gap_coach": python_exam_gap_coach,
            },
        )
        python_exam_loop_surface_status, python_exam_loop_surface = route_request(
            "/api/unibot/course/python-exam-guided-loop-control-surface",
            payload={
                "selected_skill_tag": "python_lists",
                "python_exam_gap_coach_guided_rehearsal_loop": python_exam_guided_loop,
                "python_exam_rehearsal_playback_gap_coach": python_exam_gap_coach,
            },
        )
        python_exam_locked_final_review_gap_resolver_status, python_exam_locked_final_review_gap_resolver = route_request(
            "/api/unibot/course/python-exam-locked-final-review-gap-resolver",
            payload={
                "python_exam_locked_final_review_board": python_exam_locked_final_review_board,
                "python_exam_final_manual_review_action_lock": python_exam_final_manual_review_action_lock,
                "python_exam_full_local_rehearsal_pack": python_exam_full_rehearsal,
                "python_exam_rehearsal_playback_gap_coach": python_exam_gap_coach,
                "python_exam_guided_loop_control_surface": python_exam_loop_surface,
                "selected_skill_tag": "python_lists",
            },
        )
        shutil.rmtree(ROOT / "unibot" / "knowledge" / "exam_workspace" / workspace_exam_course_id, ignore_errors=True)
        manifest_apply_file_written = workspace_private_manifest.exists()
        manifest_apply_journal_written = workspace_manifest_apply_journal.exists()
        tutor_index_file_written = workspace_tutor_index.exists()
        tutor_index_journal_written = workspace_tutor_index_journal.exists()
        help_ledger_written = workspace_help_ledger.exists()
        checkpoint_journal_written = workspace_checkpoint_journal.exists()
        timeline_export_receipt_journal_written = workspace_timeline_export_receipt_journal.exists()
    checks.append(
        _check(
            workspace_prepare_status == 200
            and workspace_prepare.get("artifact_type") == "course_local_extraction_decision_workspace"
            and workspace_prepare.get("status") == "workspace_waiting_for_local_decision_record"
            and workspace_prepare.get("public_safety_status") == "pass"
            and workspace_prepare.get("workspace_files", {}).get("template", {}).get("status") == "written"
            and workspace_prepare.get("workspace_files", {}).get("manifest", {}).get("status") == "written"
            and workspace_prepare.get("dry_run_receipt", {}).get("real_ocr_started") is False
            and workspace_prepare.get("raw_decision_record_returned") is False
            and workspace_prepare.get("raw_text_returned") is False
            and workspace_prepare.get("local_paths_returned") is False,
            "local_extraction_decision_workspace_prepare",
            (
                f"status={workspace_prepare_status}, result={workspace_prepare.get('status')}, "
                f"dry_run={workspace_prepare.get('dry_run_receipt', {}).get('status')}, "
                f"template={workspace_prepare.get('workspace_files', {}).get('template', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            workspace_record_status == 200
            and workspace_record.get("artifact_type") == "course_local_extraction_decision_workspace_record_result"
            and workspace_record.get("status") == "workspace_decision_record_stored_hash_only"
            and workspace_record.get("public_safety_status") == "pass"
            and workspace_record.get("journal_append_status") == "stored"
            and workspace_record.get("dry_run_receipt", {}).get("status") == "ocr_first_batch_1_start_ready"
            and workspace_record.get("dry_run_receipt", {}).get("ocr_first_batch_1_start_ready") is True
            and workspace_record.get("dry_run_receipt", {}).get("real_ocr_started") is False
            and workspace_record.get("workspace", {}).get("status") == "workspace_ready_for_controlled_ocr_first_batch_1"
            and workspace_record.get("raw_decision_record_returned") is False
            and workspace_record.get("raw_text_returned") is False
            and workspace_record.get("local_paths_returned") is False,
            "local_extraction_decision_workspace_record",
            (
                f"status={workspace_record_status}, result={workspace_record.get('status')}, "
                f"dry_run={workspace_record.get('dry_run_receipt', {}).get('status')}, "
                f"ocr_ready={workspace_record.get('dry_run_receipt', {}).get('ocr_first_batch_1_start_ready')}, "
                f"jobs={workspace_record.get('dry_run_receipt', {}).get('ocr_first_batch_1_job_count')}"
            ),
        )
    )
    checks.append(
        _check(
            ocr_operator_wait_status == 200
            and ocr_operator_wait.get("artifact_type") == "course_ocr_first_batch_1_operator_run"
            and ocr_operator_wait.get("status") == "waiting_for_operator_confirmation_after_dry_run"
            and ocr_operator_wait.get("workspace_dry_run_receipt", {}).get("ocr_first_batch_1_start_ready") is True
            and ocr_operator_wait.get("private_ocr_started") is False
            and ocr_operator_wait.get("real_ocr_started") is False
            and ocr_operator_wait.get("public_safety_status") == "pass",
            "ocr_first_operator_waits_for_confirmation",
            (
                f"status={ocr_operator_wait_status}, result={ocr_operator_wait.get('status')}, "
                f"dry_run={ocr_operator_wait.get('workspace_dry_run_receipt', {}).get('status')}, "
                f"started={ocr_operator_wait.get('real_ocr_started')}"
            ),
        )
    )
    checks.append(
        _check(
            ocr_operator_run_status == 200
            and ocr_operator_run.get("artifact_type") == "course_ocr_first_batch_1_operator_run"
            and ocr_operator_run.get("status") == "ocr_first_batch_1_receipts_ready_for_human_review"
            and ocr_operator_run.get("private_ocr_started") is True
            and ocr_operator_run.get("real_ocr_started") is True
            and ocr_operator_run.get("private_run_summary", {}).get("selected_job_count") == 3
            and ocr_operator_run.get("private_run_summary", {}).get("stored_receipt_count") == 3
            and ocr_operator_run.get("post_run_reports", {}).get("progress", {}).get("status") == "receipts_ready_for_human_review"
            and ocr_operator_run.get("post_run_reports", {}).get("progress", {}).get("ready_for_human_review_count") == 3
            and ocr_operator_run.get("post_run_reports", {}).get("manifest_update", {}).get("status") == "waiting_for_reviewed_receipts"
            and ocr_operator_run.get("post_run_reports", {}).get("tutor_coverage", {}).get("status") == "waiting_for_reviewed_manifest_candidates"
            and ocr_operator_run.get("raw_decision_record_returned") is False
            and ocr_operator_run.get("raw_text_returned") is False
            and ocr_operator_run.get("local_paths_returned") is False
            and ocr_operator_run.get("public_safety_status") == "pass",
            "ocr_first_operator_run_reports",
            (
                f"status={ocr_operator_run_status}, result={ocr_operator_run.get('status')}, "
                f"selected={ocr_operator_run.get('private_run_summary', {}).get('selected_job_count')}, "
                f"stored={ocr_operator_run.get('private_run_summary', {}).get('stored_receipt_count')}, "
                f"progress={ocr_operator_run.get('post_run_reports', {}).get('progress', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            review_list_status == 200
            and ocr_review_apply_status == 200
            and ocr_review_apply.get("artifact_type") == "course_extraction_human_review_apply_plan"
            and ocr_review_apply.get("status") == "review_decisions_recorded_manifest_apply_plan_ready"
            and ocr_review_apply.get("review_decision_summary", {}).get("appended_review_receipt_count") == 3
            and ocr_review_apply.get("review_decision_summary", {}).get("appended_review_record_count") == 3
            and ocr_review_apply.get("review_queue_summary", {}).get("pre_review_ready_count") == 3
            and ocr_review_apply.get("review_queue_summary", {}).get("post_review_ready_count") == 0
            and ocr_review_apply.get("post_review_reports", {}).get("manifest_update", {}).get("status") == "ready_for_private_manifest_update"
            and ocr_review_apply.get("post_review_reports", {}).get("manifest_update", {}).get("candidate_count") == 3
            and ocr_review_apply.get("manifest_written") is False
            and ocr_review_apply.get("tutor_indexing_started") is False
            and ocr_review_apply.get("raw_text_returned") is False
            and ocr_review_apply.get("local_paths_returned") is False
            and ocr_review_apply.get("public_safety_status") == "pass",
            "extraction_human_review_apply_plan",
            (
                f"status={ocr_review_apply_status}, result={ocr_review_apply.get('status')}, "
                f"appended={ocr_review_apply.get('review_decision_summary', {}).get('appended_review_receipt_count')}, "
                f"ready_after={ocr_review_apply.get('review_queue_summary', {}).get('post_review_ready_count')}, "
                f"candidates={ocr_review_apply.get('post_review_reports', {}).get('manifest_update', {}).get('candidate_count')}"
            ),
        )
    )
    checks.append(
        _check(
            manifest_apply_dry_status == 200
            and manifest_apply_dry.get("artifact_type") == "course_private_manifest_apply_dry_run"
            and manifest_apply_dry.get("status") == "manifest_apply_dry_run_ready"
            and manifest_apply_dry.get("candidate_summary", {}).get("records_to_apply_count") == 3
            and manifest_apply_dry.get("manifest_written") is False
            and manifest_apply_dry.get("manifest_apply_journal_written") is False
            and manifest_apply_dry.get("tutor_indexing_started") is False
            and manifest_apply_dry.get("raw_text_returned") is False
            and manifest_apply_dry.get("local_paths_returned") is False
            and manifest_apply_dry.get("public_safety_status") == "pass"
            and manifest_apply_confirmed_status == 200
            and manifest_apply_confirmed.get("status") == "private_manifest_applied"
            and manifest_apply_confirmed.get("apply_result", {}).get("applied_count") == 3
            and manifest_apply_confirmed.get("manifest_written") is True
            and manifest_apply_confirmed.get("manifest_apply_journal_written") is True
            and manifest_apply_confirmed.get("tutor_indexing_started") is False
            and manifest_apply_confirmed.get("private_manifest_path_returned") is False
            and manifest_apply_confirmed.get("raw_text_returned") is False
            and manifest_apply_confirmed.get("local_paths_returned") is False
            and manifest_apply_confirmed.get("public_safety_status") == "pass"
            and manifest_apply_file_written
            and manifest_apply_journal_written,
            "private_manifest_apply_dry_run_and_confirmed_apply",
            (
                f"dry={manifest_apply_dry.get('status')}, "
                f"delta={manifest_apply_dry.get('candidate_summary', {}).get('records_to_apply_count')}, "
                f"apply={manifest_apply_confirmed.get('status')}, "
                f"applied={manifest_apply_confirmed.get('apply_result', {}).get('applied_count')}, "
                f"indexing={manifest_apply_confirmed.get('tutor_indexing_started')}"
            ),
        )
    )
    checks.append(
        _check(
            tutor_index_dry_status == 200
            and tutor_index_dry.get("artifact_type") == "course_private_tutor_index_dry_run"
            and tutor_index_dry.get("status") == "tutor_index_dry_run_ready"
            and tutor_index_dry.get("index_preview", {}).get("anchor_count", 0) >= 1
            and tutor_index_dry.get("index_preview", {}).get("indexed_skill_count", 0) >= 1
            and tutor_index_dry.get("tutor_index_built") is False
            and tutor_index_dry.get("raw_text_returned") is False
            and tutor_index_dry.get("local_paths_returned") is False
            and tutor_index_dry.get("public_safety_status") == "pass"
            and tutor_index_confirmed_status == 200
            and tutor_index_confirmed.get("status") == "private_tutor_index_built"
            and tutor_index_confirmed.get("tutor_index_built") is True
            and tutor_index_confirmed.get("tutor_index_journal_written") is True
            and tutor_index_confirmed.get("tutor_index_path_returned") is False
            and tutor_index_confirmed.get("raw_text_returned") is False
            and tutor_index_confirmed.get("local_paths_returned") is False
            and tutor_index_confirmed.get("public_safety_status") == "pass"
            and tutor_index_file_written
            and tutor_index_journal_written,
            "private_tutor_index_dry_run_and_confirmed_build",
            (
                f"dry={tutor_index_dry.get('status')}, "
                f"anchors={tutor_index_dry.get('index_preview', {}).get('anchor_count')}, "
                f"skills={tutor_index_dry.get('index_preview', {}).get('indexed_skill_count')}, "
                f"build={tutor_index_confirmed.get('status')}, "
                f"built={tutor_index_confirmed.get('tutor_index_built')}"
            ),
        )
    )
    checks.append(
        _check(
            tutor_index_response_status == 200
            and tutor_index_response.get("artifact_type") == "course_private_index_tutor_response_dry_run"
            and tutor_index_response.get("status") == "allowed"
            and tutor_index_response.get("effective_help_level") == "A2"
            and tutor_index_response.get("selected_skill", {}).get("anchor_count", 0) >= 1
            and len(tutor_index_response.get("source_anchors", [])) >= 1
            and tutor_index_response.get("help_ledger_preview", {}).get("help_level") == "A2"
            and tutor_index_response.get("raw_query_returned") is False
            and tutor_index_response.get("raw_text_returned") is False
            and tutor_index_response.get("local_paths_returned") is False
            and tutor_index_response.get("automatic_grading_started") is False
            and tutor_index_response.get("proctoring_started") is False
            and tutor_index_response.get("ai_detection_started") is False
            and tutor_index_response.get("public_safety_status") == "pass",
            "private_index_tutor_response_dry_run",
            (
                f"status={tutor_index_response_status}, result={tutor_index_response.get('status')}, "
                f"skill={tutor_index_response.get('selected_skill', {}).get('skill_tag')}, "
                f"anchors={len(tutor_index_response.get('source_anchors', []))}, "
                f"help={tutor_index_response.get('effective_help_level')}, "
                f"raw_query={tutor_index_response.get('raw_query_returned')}"
            ),
        )
    )
    checks.append(
        _check(
            private_tutor_flow_status == 200
            and private_tutor_flow.get("artifact_type") == "course_private_tutor_use_flow_dry_run"
            and private_tutor_flow.get("status") == "private_tutor_use_flow_ready_with_ledger"
            and private_tutor_flow.get("tutor_response_summary", {}).get("status") == "allowed"
            and private_tutor_flow.get("tutor_response_summary", {}).get("effective_help_level") == "A2"
            and private_tutor_flow.get("ledger_append_summary", {}).get("ledger_written") is True
            and private_tutor_flow.get("study_receipt_validation", {}).get("status") == "ok_study_session_receipt"
            and private_tutor_flow.get("raw_query_returned") is False
            and private_tutor_flow.get("raw_text_returned") is False
            and private_tutor_flow.get("local_paths_returned") is False
            and private_tutor_flow.get("ledger_path_returned") is False
            and private_tutor_flow.get("automatic_grading_started") is False
            and private_tutor_flow.get("proctoring_started") is False
            and private_tutor_flow.get("ai_detection_started") is False
            and private_tutor_flow.get("public_safety_status") == "pass"
            and help_ledger_written,
            "private_tutor_use_flow_dry_run",
            (
                f"status={private_tutor_flow_status}, result={private_tutor_flow.get('status')}, "
                f"tutor={private_tutor_flow.get('tutor_response_summary', {}).get('status')}, "
                f"ledger={private_tutor_flow.get('ledger_append_summary', {}).get('ledger_written')}, "
                f"receipt={private_tutor_flow.get('study_receipt_validation', {}).get('status')}, "
                f"raw_query={private_tutor_flow.get('raw_query_returned')}"
            ),
        )
    )
    checks.append(
        _check(
            notebook_checkpoint_status == 200
            and notebook_checkpoint.get("artifact_type") == "exam_notebook_checkpoint_adapter_dry_run"
            and notebook_checkpoint.get("status") == "notebook_checkpoint_ready"
            and notebook_checkpoint.get("exam_deployment_status") == "not_cleared"
            and notebook_checkpoint.get("notebook_checkpoint", {}).get("cell_source_sha256")
            and notebook_checkpoint.get("study_receipt_summary", {}).get("status") == "ok_study_session_receipt"
            and notebook_checkpoint.get("help_ledger_preview", {}).get("help_level") == "A2"
            and notebook_checkpoint.get("help_ledger_preview", {}).get("ledger_written") is False
            and notebook_checkpoint.get("checkpoint_journal_summary", {}).get("checkpoint_journal_written") is False
            and notebook_checkpoint.get("raw_cell_returned") is False
            and notebook_checkpoint.get("raw_text_returned") is False
            and notebook_checkpoint.get("raw_notebook_returned") is False
            and notebook_checkpoint.get("notebook_code_returned") is False
            and notebook_checkpoint.get("local_paths_returned") is False
            and notebook_checkpoint.get("exam_clearance_claimed") is False
            and notebook_checkpoint.get("automatic_grading_started") is False
            and notebook_checkpoint.get("proctoring_started") is False
            and notebook_checkpoint.get("ai_detection_started") is False
            and notebook_checkpoint.get("public_safety_status") == "pass"
            and not checkpoint_journal_written,
            "exam_notebook_checkpoint_adapter",
            (
                f"status={notebook_checkpoint_status}, result={notebook_checkpoint.get('status')}, "
                f"receipt={notebook_checkpoint.get('study_receipt_summary', {}).get('status')}, "
                f"ledger={notebook_checkpoint.get('help_ledger_preview', {}).get('ledger_written')}, "
                f"raw_cell={notebook_checkpoint.get('raw_cell_returned')}"
            ),
        )
    )
    checks.append(
        _check(
            exam_workspace_run_status == 200
            and exam_workspace_run.get("artifact_type") == "exam_workspace_run_dry_run"
            and exam_workspace_run.get("status") == "exam_workspace_ready_with_exam_ledger"
            and exam_workspace_run.get("exam_deployment_status") == "not_cleared"
            and exam_workspace_run.get("session_summary", {}).get("status") == "started"
            and exam_workspace_run.get("material_freeze_summary", {}).get("status") == "frozen"
            and exam_workspace_run.get("notebook_checkpoint", {}).get("run_status") == "kernel-unavailable"
            and exam_workspace_run.get("tutor_sidecar", {}).get("status") == "allowed"
            and exam_workspace_run.get("tutor_sidecar", {}).get("effective_help_level") == "A2"
            and exam_workspace_run.get("private_tutor_use_flow_summary", {}).get("study_receipt_validation", {}).get("status") == "ok_study_session_receipt"
            and exam_workspace_run.get("exam_ledger_append_summary", {}).get("ledger_written") is True
            and exam_workspace_run.get("export_package_summary", {}).get("not_cleared_receipt") is True
            and exam_workspace_run.get("export_package_summary", {}).get("human_reviewable_independence_evidence") is True
            and exam_workspace_run.get("raw_query_returned") is False
            and exam_workspace_run.get("raw_text_returned") is False
            and exam_workspace_run.get("notebook_checkpoint", {}).get("notebook_work_sha256") == notebook_checkpoint.get("notebook_checkpoint", {}).get("notebook_work_sha256")
            and exam_workspace_run.get("raw_notebook_returned") is False
            and exam_workspace_run.get("notebook_code_returned") is False
            and exam_workspace_run.get("local_paths_returned") is False
            and exam_workspace_run.get("exam_clearance_claimed") is False
            and exam_workspace_run.get("automatic_grading_started") is False
            and exam_workspace_run.get("proctoring_started") is False
            and exam_workspace_run.get("ai_detection_started") is False
            and exam_workspace_run.get("public_safety_status") == "pass",
            "exam_workspace_run_dry_run",
            (
                f"status={exam_workspace_run_status}, result={exam_workspace_run.get('status')}, "
                f"session={exam_workspace_run.get('session_summary', {}).get('status')}, "
                f"tutor={exam_workspace_run.get('tutor_sidecar', {}).get('status')}, "
                f"ledger={exam_workspace_run.get('exam_ledger_append_summary', {}).get('ledger_written')}, "
                f"export={exam_workspace_run.get('export_package_summary', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            material_coverage_run_status == 200
            and material_coverage_run.get("artifact_type") == "course_material_coverage_run"
            and material_coverage_run.get("status") == "course_material_coverage_ready_for_exam_workspace"
            and material_coverage_run.get("exam_deployment_status") == "not_cleared"
            and material_coverage_run.get("private_manifest_summary", {}).get("status") == "ok"
            and material_coverage_run.get("private_tutor_index_summary", {}).get("status") == "ok"
            and material_coverage_run.get("coverage_summary", {}).get("exam_workspace_ready_skill_count", 0) >= 1
            and material_coverage_run.get("next_exam_workspace_start_point", {}).get("status") == "ready"
            and material_coverage_run.get("next_exam_workspace_start_point", {}).get("recommended_endpoint") == "/api/unibot/exam-workspace/run-dry-run"
            and material_coverage_run.get("raw_query_returned") is False
            and material_coverage_run.get("raw_text_returned") is False
            and material_coverage_run.get("raw_notebook_returned") is False
            and material_coverage_run.get("notebook_code_returned") is False
            and material_coverage_run.get("local_paths_returned") is False
            and material_coverage_run.get("exam_clearance_claimed") is False
            and material_coverage_run.get("automatic_grading_started") is False
            and material_coverage_run.get("proctoring_started") is False
            and material_coverage_run.get("ai_detection_started") is False
            and material_coverage_run.get("public_safety_status") == "pass",
            "course_material_coverage_run",
            (
                f"status={material_coverage_run_status}, result={material_coverage_run.get('status')}, "
                f"manifest={material_coverage_run.get('private_manifest_summary', {}).get('status')}, "
                f"index={material_coverage_run.get('private_tutor_index_summary', {}).get('status')}, "
                f"ready={material_coverage_run.get('coverage_summary', {}).get('exam_workspace_ready_skill_count')}, "
                f"start={material_coverage_run.get('next_exam_workspace_start_point', {}).get('skill_tag')}"
            ),
        )
    )
    checks.append(
        _check(
            exam_workspace_launch_status == 200
            and exam_workspace_launch.get("artifact_type") == "exam_workspace_launch_flow_dry_run"
            and exam_workspace_launch.get("status") == "exam_workspace_launch_dry_run_ready"
            and exam_workspace_launch.get("exam_deployment_status") == "not_cleared"
            and exam_workspace_launch.get("coverage_summary", {}).get("start_point", {}).get("status") == "ready"
            and exam_workspace_launch.get("coverage_summary", {}).get("start_point", {}).get("recommended_endpoint") == "/api/unibot/exam-workspace/launch-flow/dry-run"
            and exam_workspace_launch.get("launch_configuration", {}).get("workspace_endpoint_used") == "/api/unibot/exam-workspace/run-dry-run"
            and exam_workspace_launch.get("launch_configuration", {}).get("help_level") == "A2"
            and exam_workspace_launch.get("launch_configuration", {}).get("actual_query_returned") is False
            and exam_workspace_launch.get("launch_configuration", {}).get("notebook_cell_checkpoint", {}).get("notebook_code_returned") is False
            and exam_workspace_launch.get("local_notebook_checkpoint", {}).get("status") == "notebook_checkpoint_ready"
            and exam_workspace_launch.get("local_notebook_checkpoint", {}).get("notebook_work_sha256") == notebook_checkpoint.get("notebook_checkpoint", {}).get("notebook_work_sha256")
            and exam_workspace_launch.get("local_notebook_checkpoint", {}).get("raw_cell_returned") is False
            and exam_workspace_launch.get("raw_cell_returned") is False
            and exam_workspace_launch.get("exam_workspace_run_summary", {}).get("status") == "exam_workspace_dry_run_ready"
            and exam_workspace_launch.get("exam_workspace_run_summary", {}).get("tutor_status") == "allowed"
            and exam_workspace_launch.get("exam_workspace_run_summary", {}).get("study_receipt_status") == "ok_study_session_receipt"
            and exam_workspace_launch.get("help_ledger_preview", {}).get("help_level") == "A2"
            and exam_workspace_launch.get("help_ledger_preview", {}).get("exam_ledger_written") is False
            and exam_workspace_launch.get("export_receipt", {}).get("not_cleared_receipt") is True
            and exam_workspace_launch.get("export_receipt", {}).get("human_reviewable_independence_evidence") is True
            and exam_workspace_launch.get("raw_query_returned") is False
            and exam_workspace_launch.get("raw_text_returned") is False
            and exam_workspace_launch.get("raw_notebook_returned") is False
            and exam_workspace_launch.get("notebook_code_returned") is False
            and exam_workspace_launch.get("local_paths_returned") is False
            and exam_workspace_launch.get("exam_clearance_claimed") is False
            and exam_workspace_launch.get("automatic_grading_started") is False
            and exam_workspace_launch.get("proctoring_started") is False
            and exam_workspace_launch.get("ai_detection_started") is False
            and exam_workspace_launch.get("public_safety_status") == "pass",
            "exam_workspace_launch_flow_dry_run",
            (
                f"status={exam_workspace_launch_status}, result={exam_workspace_launch.get('status')}, "
                f"start={exam_workspace_launch.get('coverage_summary', {}).get('start_point', {}).get('skill_tag')}, "
                f"workspace={exam_workspace_launch.get('exam_workspace_run_summary', {}).get('status')}, "
                f"ledger={exam_workspace_launch.get('help_ledger_preview', {}).get('exam_ledger_written')}, "
                f"export={exam_workspace_launch.get('export_receipt', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            exam_skill_drilldown_status == 200
            and exam_skill_drilldown.get("artifact_type") == "exam_skill_drilldown"
            and exam_skill_drilldown.get("status") == "exam_skill_drilldown_ready_for_workspace"
            and exam_skill_drilldown.get("exam_deployment_status") == "not_cleared"
            and exam_skill_drilldown.get("selected_skill", {}).get("skill_tag") == "python_lists"
            and exam_skill_drilldown.get("selected_skill", {}).get("start_button_enabled") is True
            and exam_skill_drilldown.get("workspace_start_action", {}).get("endpoint") == "/api/unibot/exam-workspace/operator-run"
            and exam_skill_drilldown.get("workspace_start_action", {}).get("dry_run_default") is True
            and exam_skill_drilldown.get("operator_payload_template", {}).get("operator_confirmations_default") == "all_false_dry_run"
            and exam_skill_drilldown.get("operator_payload_template", {}).get("selected_skill_tag") == "python_lists"
            and exam_skill_drilldown.get("operator_payload_template", {}).get("query") == "python_lists"
            and exam_skill_drilldown.get("operator_payload_template", {}).get("raw_source_text_included") is False
            and exam_skill_drilldown.get("operator_payload_template", {}).get("notebook_code_included") is False
            and exam_skill_drilldown.get("notebook_checkpoint_template", {}).get("status") == "template_ready"
            and exam_skill_drilldown.get("notebook_checkpoint_template", {}).get("raw_cell_template_returned") is False
            and exam_skill_drilldown.get("help_ledger_preview_template", {}).get("status") == "template_ready"
            and exam_skill_drilldown.get("help_ledger_preview_template", {}).get("raw_help_text_returned") is False
            and exam_skill_drilldown.get("skill_to_workspace_live_flow", {}).get("status") == "ready_to_execute_operator_dry_run"
            and exam_skill_drilldown.get("coverage_summary", {}).get("exam_workspace_ready_skill_count", 0) >= 1
            and exam_skill_drilldown.get("coverage_receipt", {}).get("raw_material_returned") is False
            and exam_skill_drilldown.get("raw_query_returned") is False
            and exam_skill_drilldown.get("raw_text_returned") is False
            and exam_skill_drilldown.get("raw_notebook_returned") is False
            and exam_skill_drilldown.get("notebook_code_returned") is False
            and exam_skill_drilldown.get("local_paths_returned") is False
            and exam_skill_drilldown.get("exam_clearance_claimed") is False
            and exam_skill_drilldown.get("automatic_grading_started") is False
            and exam_skill_drilldown.get("proctoring_started") is False
            and exam_skill_drilldown.get("ai_detection_started") is False
            and exam_skill_drilldown.get("public_safety_status") == "pass",
            "exam_skill_drilldown",
            (
                f"status={exam_skill_drilldown_status}, result={exam_skill_drilldown.get('status')}, "
                f"selected={exam_skill_drilldown.get('selected_skill', {}).get('skill_tag')}, "
                f"action={exam_skill_drilldown.get('workspace_start_action', {}).get('status')}, "
                f"live={exam_skill_drilldown.get('skill_to_workspace_live_flow', {}).get('status')}, "
                f"ready={exam_skill_drilldown.get('coverage_summary', {}).get('exam_workspace_ready_skill_count')}"
            ),
        )
    )
    checks.append(
        _check(
            skill_to_workspace_status == 200
            and skill_to_workspace.get("artifact_type") == "skill_to_workspace_live_flow"
            and skill_to_workspace.get("status") == "skill_to_workspace_live_flow_ready"
            and skill_to_workspace.get("exam_deployment_status") == "not_cleared"
            and skill_to_workspace.get("drilldown_status") == "exam_skill_drilldown_ready_for_workspace"
            and skill_to_workspace.get("operator_run_status") == "exam_workspace_operator_dry_run_ready"
            and skill_to_workspace.get("live_flow_summary", {}).get("selected_skill_tag") == "python_lists"
            and skill_to_workspace.get("live_flow_summary", {}).get("requested_help_level") == "A2"
            and skill_to_workspace.get("live_flow_summary", {}).get("a0_a2_only") is True
            and skill_to_workspace.get("live_flow_summary", {}).get("dry_run_default") is True
            and skill_to_workspace.get("operator_prefill", {}).get("status") == "prefill_ready"
            and skill_to_workspace.get("operator_prefill", {}).get("endpoint") == "/api/unibot/exam-workspace/operator-run"
            and skill_to_workspace.get("operator_prefill", {}).get("selected_skill_tag") == "python_lists"
            and skill_to_workspace.get("operator_prefill", {}).get("requested_help_level") == "A2"
            and skill_to_workspace.get("source_anchor_metadata", {}).get("raw_anchor_text_returned") is False
            and skill_to_workspace.get("notebook_checkpoint_template", {}).get("status") == "template_ready"
            and skill_to_workspace.get("notebook_checkpoint_template", {}).get("notebook_code_returned") is False
            and skill_to_workspace.get("help_ledger_preview_template", {}).get("help_level") == "A2"
            and skill_to_workspace.get("help_ledger_preview_template", {}).get("raw_help_text_returned") is False
            and skill_to_workspace.get("operator_confirmation_matrix", {}).get("status") == "all_steps_dry_run"
            and skill_to_workspace.get("operator_confirmation_matrix", {}).get("confirmed_count") == 0
            and skill_to_workspace.get("operator_confirmation_matrix", {}).get("local_writes_requested") is False
            and skill_to_workspace.get("start_exam_workspace_view", {}).get("title") == "Start Exam Workspace"
            and skill_to_workspace.get("dry_run_receipt", {}).get("not_cleared_receipt") is True
            and skill_to_workspace.get("dry_run_default") is True
            and skill_to_workspace.get("local_writes_requested") is False
            and skill_to_workspace.get("raw_query_returned") is False
            and skill_to_workspace.get("raw_text_returned") is False
            and skill_to_workspace.get("raw_cell_returned") is False
            and skill_to_workspace.get("raw_notebook_returned") is False
            and skill_to_workspace.get("notebook_code_returned") is False
            and skill_to_workspace.get("local_paths_returned") is False
            and skill_to_workspace.get("values_returned") is False
            and skill_to_workspace.get("solutions_returned") is False
            and skill_to_workspace.get("final_interpretations_returned") is False
            and skill_to_workspace.get("automatic_grading_started") is False
            and skill_to_workspace.get("proctoring_started") is False
            and skill_to_workspace.get("ai_detection_started") is False
            and skill_to_workspace.get("exam_clearance_claimed") is False
            and skill_to_workspace.get("public_safety_status") == "pass"
            and "Diese private Startfrage" not in json.dumps(skill_to_workspace, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(skill_to_workspace, ensure_ascii=False),
            "skill_to_workspace_live_flow",
            (
                f"status={skill_to_workspace_status}, result={skill_to_workspace.get('status')}, "
                f"skill={skill_to_workspace.get('live_flow_summary', {}).get('selected_skill_tag')}, "
                f"operator={skill_to_workspace.get('operator_run_status')}, "
                f"confirmations={skill_to_workspace.get('operator_confirmation_matrix', {}).get('confirmed_count')}"
            ),
        )
    )
    checks.append(
        _check(
            skill_to_workspace_carryover_status == 200
            and skill_to_workspace_carryover.get("artifact_type") == "skill_to_workspace_session_carryover"
            and skill_to_workspace_carryover.get("status") == "skill_to_workspace_session_carryover_ready"
            and skill_to_workspace_carryover.get("exam_deployment_status") == "not_cleared"
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("selected_skill_tag") == "python_lists"
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("session_status") == "exam_workspace_session_console_ready"
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("run_history_status") == "exam_workspace_run_history_export_review_ready"
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("evidence_preview_status") == "python_exam_evidence_export_preview_ready"
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("human_handoff_status") == "python_exam_human_handoff_packet_ready"
            and bool(skill_to_workspace_carryover.get("carryover_summary", {}).get("operator_receipt_id"))
            and bool(skill_to_workspace_carryover.get("carryover_summary", {}).get("session_receipt_id"))
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("checkpoint_hash_present") is True
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("help_status") == "a0_a2_only"
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("source_card_count", 0) >= 1
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("source_anchor_count", 0) >= 1
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("open_operator_confirmation_count", 0) >= 1
            and skill_to_workspace_carryover.get("carryover_summary", {}).get("local_writes_requested") is False
            and skill_to_workspace_carryover.get("carryover_packet", {}).get("operator_receipt", {}).get("help_level") == "A2"
            and skill_to_workspace_carryover.get("carryover_packet", {}).get("evidence_preview", {}).get("status") == "python_exam_evidence_export_preview_ready"
            and skill_to_workspace_carryover.get("carryover_packet", {}).get("human_handoff", {}).get("status") == "python_exam_human_handoff_packet_ready"
            and skill_to_workspace_carryover.get("carryover_artifacts", {}).get("session_console", {}).get("artifact_type") == "exam_workspace_session_console"
            and skill_to_workspace_carryover.get("carryover_artifacts", {}).get("run_history_export_review", {}).get("artifact_type") == "exam_workspace_run_history_export_review"
            and skill_to_workspace_carryover.get("carryover_artifacts", {}).get("python_exam_evidence_export_preview", {}).get("artifact_type") == "python_exam_evidence_export_preview"
            and skill_to_workspace_carryover.get("carryover_artifacts", {}).get("python_exam_human_handoff_packet", {}).get("artifact_type") == "python_exam_human_handoff_packet"
            and skill_to_workspace_carryover.get("dry_run_default") is True
            and skill_to_workspace_carryover.get("local_writes_requested") is False
            and skill_to_workspace_carryover.get("raw_query_returned") is False
            and skill_to_workspace_carryover.get("raw_text_returned") is False
            and skill_to_workspace_carryover.get("raw_cell_returned") is False
            and skill_to_workspace_carryover.get("raw_notebook_returned") is False
            and skill_to_workspace_carryover.get("notebook_code_returned") is False
            and skill_to_workspace_carryover.get("local_paths_returned") is False
            and skill_to_workspace_carryover.get("values_returned") is False
            and skill_to_workspace_carryover.get("solutions_returned") is False
            and skill_to_workspace_carryover.get("final_interpretations_returned") is False
            and skill_to_workspace_carryover.get("automatic_grading_started") is False
            and skill_to_workspace_carryover.get("proctoring_started") is False
            and skill_to_workspace_carryover.get("ai_detection_started") is False
            and skill_to_workspace_carryover.get("exam_clearance_claimed") is False
            and skill_to_workspace_carryover.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(skill_to_workspace_carryover, ensure_ascii=False),
            "skill_to_workspace_session_carryover",
            (
                f"status={skill_to_workspace_carryover_status}, result={skill_to_workspace_carryover.get('status')}, "
                f"session={skill_to_workspace_carryover.get('carryover_summary', {}).get('session_status')}, "
                f"evidence={skill_to_workspace_carryover.get('carryover_summary', {}).get('evidence_preview_status')}, "
                f"handoff={skill_to_workspace_carryover.get('carryover_summary', {}).get('human_handoff_status')}"
            ),
        )
    )
    tutor_drill_first = (python_exam_tutor_drill_pack.get("skill_drills", []) or [{}])[0]
    tutor_drill_checkpoint = tutor_drill_first.get("notebook_checkpoint_suggestions", {})
    checks.append(
        _check(
            python_exam_tutor_drill_pack_status == 200
            and python_exam_tutor_drill_pack.get("artifact_type") == "python_exam_source_grounded_tutor_drill_pack"
            and python_exam_tutor_drill_pack.get("status") == "python_exam_source_grounded_tutor_drill_pack_ready"
            and python_exam_tutor_drill_pack.get("exam_deployment_status") == "not_cleared"
            and python_exam_tutor_drill_pack.get("selected_skill_tag") == "python_lists"
            and python_exam_tutor_drill_pack.get("drill_pack_summary", {}).get("selected_skill_tag") == "python_lists"
            and python_exam_tutor_drill_pack.get("drill_pack_summary", {}).get("skill_count") == 1
            and python_exam_tutor_drill_pack.get("drill_pack_summary", {}).get("ready_drill_count") == 1
            and python_exam_tutor_drill_pack.get("drill_pack_summary", {}).get("microtask_count", 0) >= 2
            and python_exam_tutor_drill_pack.get("drill_pack_summary", {}).get("retrieval_question_count", 0) >= 1
            and python_exam_tutor_drill_pack.get("drill_pack_summary", {}).get("checkpoint_template_count", 0) >= 1
            and python_exam_tutor_drill_pack.get("drill_pack_summary", {}).get("help_status") == "a0_a2_only"
            and python_exam_tutor_drill_pack.get("drill_pack_summary", {}).get("carryover_status")
            == "skill_to_workspace_session_carryover_ready"
            and tutor_drill_first.get("skill_tag") == "python_lists"
            and tutor_drill_first.get("status") == "drill_ready"
            and tutor_drill_first.get("source_anchor_metadata", {}).get("source_anchor_count", 0) >= 1
            and len(tutor_drill_first.get("source_anchor_metadata", {}).get("source_card_ids", []) or []) >= 1
            and len(tutor_drill_first.get("microtasks", []) or []) >= 2
            and bool((tutor_drill_first.get("microtasks", []) or [{}])[0].get("task_hash"))
            and (tutor_drill_first.get("microtasks", []) or [{}])[0].get("complete_code_returned") is False
            and (tutor_drill_first.get("microtasks", []) or [{}])[0].get("solution_returned") is False
            and (tutor_drill_first.get("microtasks", []) or [{}])[0].get("values_returned") is False
            and (tutor_drill_first.get("retrieval_questions", []) or [{}])[0].get("raw_query_returned") is False
            and (tutor_drill_first.get("retrieval_questions", []) or [{}])[0].get("raw_source_text_returned") is False
            and tutor_drill_checkpoint.get("checkpoint_template_hash")
            and tutor_drill_checkpoint.get("notebook_code_returned") is False
            and tutor_drill_checkpoint.get("local_paths_returned") is False
            and tutor_drill_first.get("help_ledger_preview", {}).get("help_level") == "A2"
            and tutor_drill_first.get("help_ledger_preview", {}).get("write_default") is False
            and python_exam_tutor_drill_pack.get("pack_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_tutor_drill_pack.get("raw_query_returned") is False
            and python_exam_tutor_drill_pack.get("raw_text_returned") is False
            and python_exam_tutor_drill_pack.get("raw_cell_returned") is False
            and python_exam_tutor_drill_pack.get("raw_notebook_returned") is False
            and python_exam_tutor_drill_pack.get("notebook_code_returned") is False
            and python_exam_tutor_drill_pack.get("local_paths_returned") is False
            and python_exam_tutor_drill_pack.get("values_returned") is False
            and python_exam_tutor_drill_pack.get("solutions_returned") is False
            and python_exam_tutor_drill_pack.get("final_interpretations_returned") is False
            and python_exam_tutor_drill_pack.get("ranking_returned") is False
            and python_exam_tutor_drill_pack.get("automatic_grading_started") is False
            and python_exam_tutor_drill_pack.get("proctoring_started") is False
            and python_exam_tutor_drill_pack.get("ai_detection_started") is False
            and python_exam_tutor_drill_pack.get("exam_clearance_claimed") is False
            and python_exam_tutor_drill_pack.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_tutor_drill_pack, ensure_ascii=False),
            "python_exam_source_grounded_tutor_drill_pack",
            (
                f"status={python_exam_tutor_drill_pack_status}, "
                f"result={python_exam_tutor_drill_pack.get('status')}, "
                f"skill={python_exam_tutor_drill_pack.get('selected_skill_tag')}, "
                f"microtasks={python_exam_tutor_drill_pack.get('drill_pack_summary', {}).get('microtask_count')}, "
                f"drills={python_exam_tutor_drill_pack.get('drill_pack_summary', {}).get('ready_drill_count')}/"
                f"{python_exam_tutor_drill_pack.get('drill_pack_summary', {}).get('skill_count')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_drill_session_runner_status == 200
            and python_exam_drill_session_runner.get("artifact_type") == "python_exam_drill_session_runner"
            and python_exam_drill_session_runner.get("status") == "python_exam_drill_session_runner_ready"
            and python_exam_drill_session_runner.get("exam_deployment_status") == "not_cleared"
            and python_exam_drill_session_runner.get("selected_skill_tag") == "python_lists"
            and python_exam_drill_session_runner.get("drill_session_summary", {}).get("pack_status")
            == "python_exam_source_grounded_tutor_drill_pack_ready"
            and python_exam_drill_session_runner.get("drill_session_summary", {}).get("drill_status") == "drill_ready"
            and python_exam_drill_session_runner.get("drill_session_summary", {}).get("microtask_selected") is True
            and python_exam_drill_session_runner.get("drill_session_summary", {}).get("checkpoint_status")
            == "notebook_checkpoint_ready"
            and python_exam_drill_session_runner.get("drill_session_summary", {}).get("study_receipt_status")
            == "ok_study_session_receipt"
            and python_exam_drill_session_runner.get("drill_session_summary", {}).get("help_status") == "a0_a2_only"
            and python_exam_drill_session_runner.get("drill_session_summary", {}).get("carryover_status")
            == "skill_to_workspace_session_carryover_ready"
            and bool(python_exam_drill_session_runner.get("selected_microtask", {}).get("task_hash"))
            and python_exam_drill_session_runner.get("selected_microtask", {}).get("help_level") == "A2"
            and python_exam_drill_session_runner.get("selected_microtask", {}).get("complete_code_returned") is False
            and python_exam_drill_session_runner.get("selected_microtask", {}).get("solution_returned") is False
            and python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("status")
            == "notebook_checkpoint_ready"
            and python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("study_receipt_status")
            == "ok_study_session_receipt"
            and bool(python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("notebook_work_sha256"))
            and python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("checkpoint_journal_written")
            is False
            and python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("raw_cell_returned")
            is False
            and python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("notebook_code_returned")
            is False
            and python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("local_paths_returned")
            is False
            and python_exam_drill_session_runner.get("help_ledger_preview", {}).get("status") == "preview_ready"
            and bool(python_exam_drill_session_runner.get("help_ledger_preview", {}).get("event_hash"))
            and python_exam_drill_session_runner.get("help_ledger_preview", {}).get("ledger_written") is False
            and python_exam_drill_session_runner.get("carryover_reference", {}).get("session_receipt_id")
            == skill_to_workspace_carryover.get("carryover_summary", {}).get("session_receipt_id")
            and python_exam_drill_session_runner.get("drill_session_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_drill_session_runner.get("dry_run_default") is True
            and python_exam_drill_session_runner.get("local_writes_requested") is False
            and python_exam_drill_session_runner.get("raw_query_returned") is False
            and python_exam_drill_session_runner.get("raw_text_returned") is False
            and python_exam_drill_session_runner.get("raw_cell_returned") is False
            and python_exam_drill_session_runner.get("raw_notebook_returned") is False
            and python_exam_drill_session_runner.get("notebook_code_returned") is False
            and python_exam_drill_session_runner.get("local_paths_returned") is False
            and python_exam_drill_session_runner.get("values_returned") is False
            and python_exam_drill_session_runner.get("solutions_returned") is False
            and python_exam_drill_session_runner.get("final_interpretations_returned") is False
            and python_exam_drill_session_runner.get("ranking_returned") is False
            and python_exam_drill_session_runner.get("automatic_grading_started") is False
            and python_exam_drill_session_runner.get("proctoring_started") is False
            and python_exam_drill_session_runner.get("ai_detection_started") is False
            and python_exam_drill_session_runner.get("exam_clearance_claimed") is False
            and python_exam_drill_session_runner.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_drill_session_runner, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_drill_session_runner, ensure_ascii=False),
            "python_exam_drill_session_runner",
            (
                f"status={python_exam_drill_session_runner_status}, "
                f"result={python_exam_drill_session_runner.get('status')}, "
                f"skill={python_exam_drill_session_runner.get('selected_skill_tag')}, "
                f"checkpoint={python_exam_drill_session_runner.get('drill_session_summary', {}).get('checkpoint_status')}, "
                f"receipt={python_exam_drill_session_runner.get('drill_session_receipt', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_drill_session_review_loop_status == 200
            and python_exam_drill_session_review_loop.get("artifact_type") == "python_exam_drill_session_review_loop"
            and python_exam_drill_session_review_loop.get("status") == "python_exam_drill_session_review_loop_ready"
            and python_exam_drill_session_review_loop.get("exam_deployment_status") == "not_cleared"
            and python_exam_drill_session_review_loop.get("selected_skill_tag") == "python_lists"
            and python_exam_drill_session_review_loop.get("review_loop_summary", {}).get("session_status")
            == "python_exam_drill_session_runner_ready"
            and python_exam_drill_session_review_loop.get("review_loop_summary", {}).get("pack_status")
            == "python_exam_source_grounded_tutor_drill_pack_ready"
            and python_exam_drill_session_review_loop.get("review_loop_summary", {}).get("next_step_status")
            == "next_microtask_ready"
            and python_exam_drill_session_review_loop.get("review_loop_summary", {}).get("next_step_action")
            == "run_next_microtask"
            and python_exam_drill_session_review_loop.get("review_loop_summary", {}).get("no_score_or_grade") is True
            and python_exam_drill_session_review_loop.get("session_evidence_summary", {}).get("microtask_hash")
            == python_exam_drill_session_runner.get("selected_microtask", {}).get("task_hash")
            and python_exam_drill_session_review_loop.get("session_evidence_summary", {}).get("checkpoint_hash")
            == python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("notebook_work_sha256")
            and python_exam_drill_session_review_loop.get("session_evidence_summary", {}).get("not_cleared_receipt") is True
            and len(python_exam_drill_session_review_loop.get("source_anchor_metadata", {}).get("source_card_ids", []) or [])
            >= 1
            and python_exam_drill_session_review_loop.get("help_ledger_preview", {}).get("status") == "preview_ready"
            and bool(python_exam_drill_session_review_loop.get("help_ledger_preview", {}).get("event_hash"))
            and python_exam_drill_session_review_loop.get("carryover_reference", {}).get("session_receipt_id")
            == skill_to_workspace_carryover.get("carryover_summary", {}).get("session_receipt_id")
            and python_exam_drill_session_review_loop.get("reflection_status", {}).get("status")
            == "reflection_metadata_present"
            and python_exam_drill_session_review_loop.get("next_step_recommendation", {}).get("action")
            == "run_next_microtask"
            and python_exam_drill_session_review_loop.get("next_step_recommendation", {}).get("help_level") == "A2"
            and bool(python_exam_drill_session_review_loop.get("next_step_recommendation", {}).get("next_task_hash"))
            and python_exam_drill_session_review_loop.get("review_loop_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_drill_session_review_loop.get("dry_run_default") is True
            and python_exam_drill_session_review_loop.get("local_writes_requested") is False
            and python_exam_drill_session_review_loop.get("raw_query_returned") is False
            and python_exam_drill_session_review_loop.get("raw_text_returned") is False
            and python_exam_drill_session_review_loop.get("raw_cell_returned") is False
            and python_exam_drill_session_review_loop.get("raw_notebook_returned") is False
            and python_exam_drill_session_review_loop.get("notebook_code_returned") is False
            and python_exam_drill_session_review_loop.get("local_paths_returned") is False
            and python_exam_drill_session_review_loop.get("values_returned") is False
            and python_exam_drill_session_review_loop.get("solutions_returned") is False
            and python_exam_drill_session_review_loop.get("final_interpretations_returned") is False
            and python_exam_drill_session_review_loop.get("score_returned") is False
            and python_exam_drill_session_review_loop.get("percentage_returned") is False
            and python_exam_drill_session_review_loop.get("ranking_returned") is False
            and python_exam_drill_session_review_loop.get("grade_returned") is False
            and python_exam_drill_session_review_loop.get("automatic_grading_started") is False
            and python_exam_drill_session_review_loop.get("proctoring_started") is False
            and python_exam_drill_session_review_loop.get("ai_detection_started") is False
            and python_exam_drill_session_review_loop.get("exam_clearance_claimed") is False
            and python_exam_drill_session_review_loop.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_drill_session_review_loop, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_drill_session_review_loop, ensure_ascii=False),
            "python_exam_drill_session_review_loop",
            (
                f"status={python_exam_drill_session_review_loop_status}, "
                f"result={python_exam_drill_session_review_loop.get('status')}, "
                f"skill={python_exam_drill_session_review_loop.get('selected_skill_tag')}, "
                f"next={python_exam_drill_session_review_loop.get('next_step_recommendation', {}).get('action')}, "
                f"receipt={python_exam_drill_session_review_loop.get('review_loop_receipt', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_drill_loop_control_panel_status == 200
            and python_exam_drill_loop_control_panel.get("artifact_type") == "python_exam_drill_loop_control_panel"
            and python_exam_drill_loop_control_panel.get("status") == "python_exam_drill_loop_control_panel_ready"
            and python_exam_drill_loop_control_panel.get("exam_deployment_status") == "not_cleared"
            and python_exam_drill_loop_control_panel.get("selected_skill_tag") == "python_lists"
            and python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("pack_status")
            == "python_exam_source_grounded_tutor_drill_pack_ready"
            and python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("session_status")
            == "python_exam_drill_session_runner_ready"
            and python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("review_loop_status")
            == "python_exam_drill_session_review_loop_ready"
            and python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("next_step_action")
            == "run_next_microtask"
            and python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("next_step_status")
            == "next_microtask_ready"
            and python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("help_status") == "a0_a2_only"
            and bool(python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("current_task_hash"))
            and bool(python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("checkpoint_hash"))
            and len(python_exam_drill_loop_control_panel.get("cycle_cards", []) or []) == 3
            and all(item.get("ready") is True for item in (python_exam_drill_loop_control_panel.get("cycle_cards", []) or []))
            and python_exam_drill_loop_control_panel.get("current_microtask", {}).get("task_hash")
            == python_exam_drill_session_runner.get("selected_microtask", {}).get("task_hash")
            and python_exam_drill_loop_control_panel.get("session_evidence_summary", {}).get("checkpoint_hash")
            == python_exam_drill_session_runner.get("notebook_checkpoint_adapter_summary", {}).get("notebook_work_sha256")
            and len(python_exam_drill_loop_control_panel.get("session_evidence_summary", {}).get("source_card_ids", []) or [])
            >= 1
            and python_exam_drill_loop_control_panel.get("session_evidence_summary", {}).get("help_level") == "A2"
            and python_exam_drill_loop_control_panel.get("next_step_recommendation", {}).get("action")
            == "run_next_microtask"
            and bool(python_exam_drill_loop_control_panel.get("next_step_recommendation", {}).get("next_task_hash"))
            and python_exam_drill_loop_control_panel.get("control_panel_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_drill_loop_control_panel.get("dry_run_default") is True
            and python_exam_drill_loop_control_panel.get("local_writes_requested") is False
            and python_exam_drill_loop_control_panel.get("raw_query_returned") is False
            and python_exam_drill_loop_control_panel.get("raw_text_returned") is False
            and python_exam_drill_loop_control_panel.get("raw_cell_returned") is False
            and python_exam_drill_loop_control_panel.get("raw_notebook_returned") is False
            and python_exam_drill_loop_control_panel.get("notebook_code_returned") is False
            and python_exam_drill_loop_control_panel.get("local_paths_returned") is False
            and python_exam_drill_loop_control_panel.get("values_returned") is False
            and python_exam_drill_loop_control_panel.get("solutions_returned") is False
            and python_exam_drill_loop_control_panel.get("final_interpretations_returned") is False
            and python_exam_drill_loop_control_panel.get("score_returned") is False
            and python_exam_drill_loop_control_panel.get("percentage_returned") is False
            and python_exam_drill_loop_control_panel.get("ranking_returned") is False
            and python_exam_drill_loop_control_panel.get("grade_returned") is False
            and python_exam_drill_loop_control_panel.get("automatic_grading_started") is False
            and python_exam_drill_loop_control_panel.get("proctoring_started") is False
            and python_exam_drill_loop_control_panel.get("ai_detection_started") is False
            and python_exam_drill_loop_control_panel.get("exam_clearance_claimed") is False
            and python_exam_drill_loop_control_panel.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_drill_loop_control_panel, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_drill_loop_control_panel, ensure_ascii=False),
            "python_exam_drill_loop_control_panel",
            (
                f"status={python_exam_drill_loop_control_panel_status}, "
                f"result={python_exam_drill_loop_control_panel.get('status')}, "
                f"skill={python_exam_drill_loop_control_panel.get('selected_skill_tag')}, "
                f"next={python_exam_drill_loop_control_panel.get('next_step_recommendation', {}).get('action')}, "
                f"cards={len(python_exam_drill_loop_control_panel.get('cycle_cards', []) or [])}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_drill_loop_progress_journal_status == 200
            and python_exam_drill_loop_progress_journal.get("artifact_type")
            == "python_exam_drill_loop_progress_journal"
            and python_exam_drill_loop_progress_journal.get("status") == "write_preview_ready"
            and python_exam_drill_loop_progress_journal.get("exam_deployment_status") == "not_cleared"
            and python_exam_drill_loop_progress_journal.get("journal_written") is False
            and python_exam_drill_loop_progress_journal.get("dry_run_default") is True
            and python_exam_drill_loop_progress_journal.get("local_writes_requested") is False
            and not workspace_drill_loop_progress_journal.exists()
            and python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("skill_tag")
            == "python_lists"
            and python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("microtask_hash")
            == python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("current_task_hash")
            and python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("checkpoint_hash")
            == python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("checkpoint_hash")
            and len(
                python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("source_card_ids", [])
                or []
            )
            >= 1
            and python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("help_level") == "A2"
            and bool(
                python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("help_ledger_event_hash")
            )
            and bool(
                python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get(
                    "carryover_session_receipt_id"
                )
            )
            and bool(
                python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("review_loop_receipt_id")
            )
            and python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("next_step_action")
            == "run_next_microtask"
            and python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("not_cleared_receipt")
            is True
            and python_exam_drill_loop_progress_journal.get("resume_state", {}).get("status") == "resume_ready"
            and python_exam_drill_loop_progress_journal.get("resume_state", {}).get("resume_action")
            == "run_next_microtask"
            and python_exam_drill_loop_progress_journal.get("resume_state", {}).get("accepted_record_count") == 1
            and python_exam_drill_loop_progress_journal.get("raw_query_returned") is False
            and python_exam_drill_loop_progress_journal.get("raw_text_returned") is False
            and python_exam_drill_loop_progress_journal.get("raw_cell_returned") is False
            and python_exam_drill_loop_progress_journal.get("raw_notebook_returned") is False
            and python_exam_drill_loop_progress_journal.get("notebook_code_returned") is False
            and python_exam_drill_loop_progress_journal.get("local_paths_returned") is False
            and python_exam_drill_loop_progress_journal.get("values_returned") is False
            and python_exam_drill_loop_progress_journal.get("solutions_returned") is False
            and python_exam_drill_loop_progress_journal.get("final_interpretations_returned") is False
            and python_exam_drill_loop_progress_journal.get("score_returned") is False
            and python_exam_drill_loop_progress_journal.get("percentage_returned") is False
            and python_exam_drill_loop_progress_journal.get("ranking_returned") is False
            and python_exam_drill_loop_progress_journal.get("grade_returned") is False
            and python_exam_drill_loop_progress_journal.get("automatic_grading_started") is False
            and python_exam_drill_loop_progress_journal.get("proctoring_started") is False
            and python_exam_drill_loop_progress_journal.get("ai_detection_started") is False
            and python_exam_drill_loop_progress_journal.get("exam_clearance_claimed") is False
            and python_exam_drill_loop_progress_journal.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_drill_loop_progress_journal, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_drill_loop_progress_journal, ensure_ascii=False),
            "python_exam_drill_loop_progress_journal",
            (
                f"status={python_exam_drill_loop_progress_journal_status}, "
                f"result={python_exam_drill_loop_progress_journal.get('status')}, "
                f"skill={python_exam_drill_loop_progress_journal.get('journal_entry_preview', {}).get('skill_tag')}, "
                f"resume={python_exam_drill_loop_progress_journal.get('resume_state', {}).get('resume_action')}, "
                f"written={python_exam_drill_loop_progress_journal.get('journal_written')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_resume_launcher_status == 200
            and python_exam_resume_launcher.get("artifact_type") == "python_exam_resume_launcher"
            and python_exam_resume_launcher.get("status") == "python_exam_resume_launcher_next_microtask_ready"
            and python_exam_resume_launcher.get("exam_deployment_status") == "not_cleared"
            and python_exam_resume_launcher.get("resume_decision", {}).get("action") == "run_next_microtask"
            and python_exam_resume_launcher.get("resume_decision", {}).get("route") == "control_panel"
            and python_exam_resume_launcher.get("resume_decision", {}).get("selected_skill_tag") == "python_lists"
            and python_exam_resume_launcher.get("resume_decision", {}).get("selected_task_hash")
            == python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("next_task_hash")
            and python_exam_resume_launcher.get("control_panel_prefill", {}).get("endpoint")
            == "/api/unibot/course/python-exam-drill-loop-control-panel"
            and python_exam_resume_launcher.get("control_panel_prefill", {}).get("selected_task_hash")
            == python_exam_resume_launcher.get("resume_decision", {}).get("selected_task_hash")
            and python_exam_resume_launcher.get("control_panel_prefill", {}).get("requested_help_level") == "A2"
            and len(python_exam_resume_launcher.get("control_panel_prefill", {}).get("source_card_ids", []) or []) >= 1
            and bool(python_exam_resume_launcher.get("control_panel_prefill", {}).get("prefill_hash"))
            and python_exam_resume_launcher.get("resume_state", {}).get("resume_action") == "run_next_microtask"
            and python_exam_resume_launcher.get("latest_progress_entry", {}).get("skill_tag") == "python_lists"
            and python_exam_resume_launcher.get("dry_run_default") is True
            and python_exam_resume_launcher.get("local_writes_requested") is False
            and python_exam_resume_launcher.get("raw_query_returned") is False
            and python_exam_resume_launcher.get("raw_text_returned") is False
            and python_exam_resume_launcher.get("raw_cell_returned") is False
            and python_exam_resume_launcher.get("raw_notebook_returned") is False
            and python_exam_resume_launcher.get("notebook_code_returned") is False
            and python_exam_resume_launcher.get("local_paths_returned") is False
            and python_exam_resume_launcher.get("values_returned") is False
            and python_exam_resume_launcher.get("solutions_returned") is False
            and python_exam_resume_launcher.get("final_interpretations_returned") is False
            and python_exam_resume_launcher.get("score_returned") is False
            and python_exam_resume_launcher.get("percentage_returned") is False
            and python_exam_resume_launcher.get("ranking_returned") is False
            and python_exam_resume_launcher.get("grade_returned") is False
            and python_exam_resume_launcher.get("automatic_grading_started") is False
            and python_exam_resume_launcher.get("proctoring_started") is False
            and python_exam_resume_launcher.get("ai_detection_started") is False
            and python_exam_resume_launcher.get("exam_clearance_claimed") is False
            and python_exam_resume_launcher.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_resume_launcher, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_resume_launcher, ensure_ascii=False),
            "python_exam_resume_launcher",
            (
                f"status={python_exam_resume_launcher_status}, "
                f"result={python_exam_resume_launcher.get('status')}, "
                f"action={python_exam_resume_launcher.get('resume_decision', {}).get('action')}, "
                f"skill={python_exam_resume_launcher.get('resume_decision', {}).get('selected_skill_tag')}, "
                f"route={python_exam_resume_launcher.get('resume_decision', {}).get('route')}"
            ),
        )
    )
    active_row = (
        python_exam_active_study_loop_dashboard.get("skill_loop_dashboard", [{}])[0]
        if python_exam_active_study_loop_dashboard.get("skill_loop_dashboard")
        else {}
    )
    checks.append(
        _check(
            python_exam_active_study_loop_dashboard_status == 200
            and python_exam_active_study_loop_dashboard.get("artifact_type")
            == "python_exam_active_study_loop_dashboard"
            and python_exam_active_study_loop_dashboard.get("status")
            == "python_exam_active_study_loop_dashboard_ready"
            and python_exam_active_study_loop_dashboard.get("exam_deployment_status") == "not_cleared"
            and python_exam_active_study_loop_dashboard.get("selected_skill_tag") == "python_lists"
            and python_exam_active_study_loop_dashboard.get("active_study_summary", {}).get("selected_skill_tag")
            == "python_lists"
            and python_exam_active_study_loop_dashboard.get("active_study_summary", {}).get("active_resume_action")
            == "run_next_microtask"
            and python_exam_active_study_loop_dashboard.get("active_study_summary", {}).get("next_safe_action")
            == "run_next_microtask"
            and python_exam_active_study_loop_dashboard.get("active_study_summary", {}).get("skill_count", 0) >= 1
            and python_exam_active_study_loop_dashboard.get("active_study_summary", {}).get("a0_a2_only") is True
            and active_row.get("skill_tag") == "python_lists"
            and active_row.get("workspace_readiness") == "ready_for_exam_workspace_dry_run"
            and active_row.get("drill_status") == "drill_ready"
            and active_row.get("last_safe_microtask_hash")
            == python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("microtask_hash")
            and active_row.get("next_microtask_hash")
            == python_exam_resume_launcher.get("resume_decision", {}).get("selected_task_hash")
            and active_row.get("next_safe_action") == "run_next_microtask"
            and len(active_row.get("source_card_ids", []) or []) >= 1
            and active_row.get("help_level") == "A2"
            and bool(active_row.get("checkpoint_hash"))
            and bool(active_row.get("help_ledger_event_hash"))
            and bool(active_row.get("carryover_session_receipt_id"))
            and bool(active_row.get("review_loop_receipt_id"))
            and bool(active_row.get("control_panel_receipt_id"))
            and bool(active_row.get("prefill_hash"))
            and python_exam_active_study_loop_dashboard.get("dry_run_default") is True
            and python_exam_active_study_loop_dashboard.get("local_writes_requested") is False
            and python_exam_active_study_loop_dashboard.get("raw_query_returned") is False
            and python_exam_active_study_loop_dashboard.get("raw_text_returned") is False
            and python_exam_active_study_loop_dashboard.get("raw_cell_returned") is False
            and python_exam_active_study_loop_dashboard.get("raw_notebook_returned") is False
            and python_exam_active_study_loop_dashboard.get("notebook_code_returned") is False
            and python_exam_active_study_loop_dashboard.get("local_paths_returned") is False
            and python_exam_active_study_loop_dashboard.get("values_returned") is False
            and python_exam_active_study_loop_dashboard.get("solutions_returned") is False
            and python_exam_active_study_loop_dashboard.get("final_interpretations_returned") is False
            and python_exam_active_study_loop_dashboard.get("score_returned") is False
            and python_exam_active_study_loop_dashboard.get("percentage_returned") is False
            and python_exam_active_study_loop_dashboard.get("ranking_returned") is False
            and python_exam_active_study_loop_dashboard.get("grade_returned") is False
            and python_exam_active_study_loop_dashboard.get("automatic_grading_started") is False
            and python_exam_active_study_loop_dashboard.get("proctoring_started") is False
            and python_exam_active_study_loop_dashboard.get("ai_detection_started") is False
            and python_exam_active_study_loop_dashboard.get("exam_clearance_claimed") is False
            and python_exam_active_study_loop_dashboard.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_active_study_loop_dashboard, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_active_study_loop_dashboard, ensure_ascii=False),
            "python_exam_active_study_loop_dashboard",
            (
                f"status={python_exam_active_study_loop_dashboard_status}, "
                f"result={python_exam_active_study_loop_dashboard.get('status')}, "
                f"skill={python_exam_active_study_loop_dashboard.get('selected_skill_tag')}, "
                f"next={python_exam_active_study_loop_dashboard.get('active_study_summary', {}).get('next_safe_action')}, "
                f"rows={len(python_exam_active_study_loop_dashboard.get('skill_loop_dashboard', []) or [])}"
            ),
        )
    )
    guided_card = python_exam_active_study_guided_runner.get("guided_action_card", {})
    guided_prefill = python_exam_active_study_guided_runner.get("control_panel_prefill", {})
    checks.append(
        _check(
            python_exam_active_study_guided_runner_status == 200
            and python_exam_active_study_guided_runner.get("artifact_type") == "python_exam_active_study_guided_runner"
            and python_exam_active_study_guided_runner.get("status") == "python_exam_active_study_guided_runner_ready"
            and python_exam_active_study_guided_runner.get("exam_deployment_status") == "not_cleared"
            and python_exam_active_study_guided_runner.get("selected_skill_tag") == "python_lists"
            and python_exam_active_study_guided_runner.get("guided_runner_summary", {}).get("selected_skill_tag")
            == "python_lists"
            and python_exam_active_study_guided_runner.get("guided_runner_summary", {}).get("action")
            == "run_next_microtask"
            and python_exam_active_study_guided_runner.get("guided_runner_summary", {}).get("route") == "control_panel"
            and python_exam_active_study_guided_runner.get("guided_runner_summary", {}).get("endpoint")
            == "/api/unibot/course/python-exam-drill-loop-control-panel"
            and python_exam_active_study_guided_runner.get("guided_runner_summary", {}).get("a0_a2_only") is True
            and python_exam_active_study_guided_runner.get("guided_runner_summary", {}).get("ready") is True
            and guided_card.get("status") == "guided_action_card_ready"
            and guided_card.get("action") == "run_next_microtask"
            and guided_card.get("selected_task_hash")
            == python_exam_resume_launcher.get("resume_decision", {}).get("selected_task_hash")
            and guided_card.get("checkpoint_hash") == python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("checkpoint_hash")
            and len(guided_card.get("source_card_ids", []) or []) >= 1
            and guided_card.get("help_level") == "A2"
            and guided_card.get("operator_confirmations_default") == "all_false_dry_run"
            and "checkpoint_store" in (guided_card.get("operator_confirmations_required", []) or [])
            and guided_prefill.get("endpoint") == "/api/unibot/course/python-exam-drill-loop-control-panel"
            and guided_prefill.get("selected_task_hash") == guided_card.get("selected_task_hash")
            and bool(guided_prefill.get("prefill_hash"))
            and python_exam_active_study_guided_runner.get("operator_confirmations", {}).get("checkpoint_store") is False
            and python_exam_active_study_guided_runner.get("operator_confirmations", {}).get("progress_journal_append") is False
            and python_exam_active_study_guided_runner.get("dry_run_default") is True
            and python_exam_active_study_guided_runner.get("local_writes_requested") is False
            and python_exam_active_study_guided_runner.get("raw_query_returned") is False
            and python_exam_active_study_guided_runner.get("raw_text_returned") is False
            and python_exam_active_study_guided_runner.get("raw_cell_returned") is False
            and python_exam_active_study_guided_runner.get("raw_notebook_returned") is False
            and python_exam_active_study_guided_runner.get("notebook_code_returned") is False
            and python_exam_active_study_guided_runner.get("local_paths_returned") is False
            and python_exam_active_study_guided_runner.get("values_returned") is False
            and python_exam_active_study_guided_runner.get("solutions_returned") is False
            and python_exam_active_study_guided_runner.get("final_interpretations_returned") is False
            and python_exam_active_study_guided_runner.get("score_returned") is False
            and python_exam_active_study_guided_runner.get("percentage_returned") is False
            and python_exam_active_study_guided_runner.get("ranking_returned") is False
            and python_exam_active_study_guided_runner.get("grade_returned") is False
            and python_exam_active_study_guided_runner.get("automatic_grading_started") is False
            and python_exam_active_study_guided_runner.get("proctoring_started") is False
            and python_exam_active_study_guided_runner.get("ai_detection_started") is False
            and python_exam_active_study_guided_runner.get("exam_clearance_claimed") is False
            and python_exam_active_study_guided_runner.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_active_study_guided_runner, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_active_study_guided_runner, ensure_ascii=False),
            "python_exam_active_study_guided_runner",
            (
                f"status={python_exam_active_study_guided_runner_status}, "
                f"result={python_exam_active_study_guided_runner.get('status')}, "
                f"skill={python_exam_active_study_guided_runner.get('selected_skill_tag')}, "
                f"action={python_exam_active_study_guided_runner.get('guided_runner_summary', {}).get('action')}, "
                f"route={python_exam_active_study_guided_runner.get('guided_runner_summary', {}).get('route')}"
            ),
        )
    )
    bridge_preview = python_exam_guided_action_execution_bridge.get("control_panel_cycle_preview", {})
    bridge_matrix = python_exam_guided_action_execution_bridge.get("operator_confirmation_matrix", {})
    checks.append(
        _check(
            python_exam_guided_action_execution_bridge_status == 200
            and python_exam_guided_action_execution_bridge.get("artifact_type") == "python_exam_guided_action_execution_bridge"
            and python_exam_guided_action_execution_bridge.get("status") == "python_exam_guided_action_execution_bridge_ready"
            and python_exam_guided_action_execution_bridge.get("exam_deployment_status") == "not_cleared"
            and python_exam_guided_action_execution_bridge.get("selected_skill_tag") == "python_lists"
            and python_exam_guided_action_execution_bridge.get("execution_bridge_summary", {}).get("selected_skill_tag")
            == "python_lists"
            and python_exam_guided_action_execution_bridge.get("execution_bridge_summary", {}).get("action")
            == "run_next_microtask"
            and python_exam_guided_action_execution_bridge.get("execution_bridge_summary", {}).get("route")
            == "control_panel"
            and python_exam_guided_action_execution_bridge.get("execution_bridge_summary", {}).get("endpoint")
            == "/api/unibot/course/python-exam-drill-loop-control-panel"
            and python_exam_guided_action_execution_bridge.get("execution_bridge_summary", {}).get("preview_status")
            == "control_panel_execution_preview_ready"
            and python_exam_guided_action_execution_bridge.get("execution_bridge_summary", {}).get("a0_a2_only") is True
            and python_exam_guided_action_execution_bridge.get("execution_bridge_summary", {}).get("ready") is True
            and bridge_preview.get("selected_task_hash") == guided_card.get("selected_task_hash")
            and bridge_preview.get("checkpoint_hash") == guided_card.get("checkpoint_hash")
            and len(bridge_preview.get("source_card_ids", []) or []) >= 1
            and bridge_preview.get("help_level") == "A2"
            and bridge_preview.get("progress_journal_preview_status") == python_exam_drill_loop_progress_journal.get("status")
            and bridge_preview.get("progress_journal_written") is False
            and bool(bridge_preview.get("preview_hash"))
            and bridge_matrix.get("status") == "all_steps_dry_run"
            and bridge_matrix.get("confirmed_count") == 0
            and bridge_matrix.get("local_writes_requested") is False
            and python_exam_guided_action_execution_bridge.get("dry_run_default") is True
            and python_exam_guided_action_execution_bridge.get("local_writes_requested") is False
            and python_exam_guided_action_execution_bridge.get("raw_query_returned") is False
            and python_exam_guided_action_execution_bridge.get("raw_text_returned") is False
            and python_exam_guided_action_execution_bridge.get("raw_cell_returned") is False
            and python_exam_guided_action_execution_bridge.get("raw_notebook_returned") is False
            and python_exam_guided_action_execution_bridge.get("notebook_code_returned") is False
            and python_exam_guided_action_execution_bridge.get("local_paths_returned") is False
            and python_exam_guided_action_execution_bridge.get("values_returned") is False
            and python_exam_guided_action_execution_bridge.get("solutions_returned") is False
            and python_exam_guided_action_execution_bridge.get("final_interpretations_returned") is False
            and python_exam_guided_action_execution_bridge.get("score_returned") is False
            and python_exam_guided_action_execution_bridge.get("percentage_returned") is False
            and python_exam_guided_action_execution_bridge.get("ranking_returned") is False
            and python_exam_guided_action_execution_bridge.get("grade_returned") is False
            and python_exam_guided_action_execution_bridge.get("automatic_grading_started") is False
            and python_exam_guided_action_execution_bridge.get("proctoring_started") is False
            and python_exam_guided_action_execution_bridge.get("ai_detection_started") is False
            and python_exam_guided_action_execution_bridge.get("exam_clearance_claimed") is False
            and python_exam_guided_action_execution_bridge.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_guided_action_execution_bridge, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_guided_action_execution_bridge, ensure_ascii=False),
            "python_exam_guided_action_execution_bridge",
            (
                f"status={python_exam_guided_action_execution_bridge_status}, "
                f"result={python_exam_guided_action_execution_bridge.get('status')}, "
                f"skill={python_exam_guided_action_execution_bridge.get('selected_skill_tag')}, "
                f"action={python_exam_guided_action_execution_bridge.get('execution_bridge_summary', {}).get('action')}, "
                f"preview={python_exam_guided_action_execution_bridge.get('execution_bridge_summary', {}).get('preview_status')}"
            ),
        )
    )
    safe_cycle_summary = python_exam_safe_cycle_console.get("safe_cycle_summary", {})
    safe_cycle_view = python_exam_safe_cycle_console.get("current_cycle_view", {})
    safe_cycle_preview = safe_cycle_view.get("preview", {})
    safe_cycle_receipts = safe_cycle_view.get("receipts", {})
    safe_cycle_matrix = safe_cycle_view.get("operator_confirmation_matrix", {})
    checks.append(
        _check(
            python_exam_safe_cycle_console_status == 200
            and python_exam_safe_cycle_console.get("artifact_type") == "python_exam_safe_cycle_console"
            and python_exam_safe_cycle_console.get("status") == "python_exam_safe_cycle_console_ready"
            and python_exam_safe_cycle_console.get("exam_deployment_status") == "not_cleared"
            and python_exam_safe_cycle_console.get("selected_skill_tag") == "python_lists"
            and safe_cycle_summary.get("selected_skill_tag") == "python_lists"
            and safe_cycle_summary.get("cycle_status") == "safe_cycle_ready_for_operator_review"
            and safe_cycle_summary.get("next_safe_action") == "run_next_microtask"
            and safe_cycle_summary.get("route") == "control_panel"
            and safe_cycle_summary.get("preview_status") == "control_panel_execution_preview_ready"
            and safe_cycle_summary.get("a0_a2_only") is True
            and safe_cycle_summary.get("ready") is True
            and safe_cycle_preview.get("selected_task_hash") == guided_card.get("selected_task_hash")
            and safe_cycle_preview.get("checkpoint_hash") == python_exam_drill_loop_control_panel.get("control_panel_summary", {}).get("checkpoint_hash")
            and len(safe_cycle_preview.get("source_card_ids", []) or []) >= 1
            and safe_cycle_preview.get("help_level") == "A2"
            and safe_cycle_receipts.get("execution_bridge_receipt_id")
            == python_exam_guided_action_execution_bridge.get("execution_bridge_receipt", {}).get("receipt_id")
            and safe_cycle_receipts.get("control_panel_receipt_id")
            == python_exam_drill_loop_control_panel.get("control_panel_receipt", {}).get("receipt_id")
            and safe_cycle_receipts.get("progress_entry_hash")
            == python_exam_drill_loop_progress_journal.get("journal_entry_preview", {}).get("entry_hash")
            and bool(safe_cycle_receipts.get("help_ledger_event_hash"))
            and bool(safe_cycle_receipts.get("review_loop_receipt_id"))
            and safe_cycle_receipts.get("progress_journal_written") is False
            and safe_cycle_matrix.get("status") == "all_steps_dry_run"
            and safe_cycle_matrix.get("confirmed_count") == 0
            and safe_cycle_matrix.get("local_writes_requested") is False
            and python_exam_safe_cycle_console.get("dry_run_default") is True
            and python_exam_safe_cycle_console.get("local_writes_requested") is False
            and python_exam_safe_cycle_console.get("raw_query_returned") is False
            and python_exam_safe_cycle_console.get("raw_text_returned") is False
            and python_exam_safe_cycle_console.get("raw_cell_returned") is False
            and python_exam_safe_cycle_console.get("raw_notebook_returned") is False
            and python_exam_safe_cycle_console.get("notebook_code_returned") is False
            and python_exam_safe_cycle_console.get("local_paths_returned") is False
            and python_exam_safe_cycle_console.get("values_returned") is False
            and python_exam_safe_cycle_console.get("solutions_returned") is False
            and python_exam_safe_cycle_console.get("final_interpretations_returned") is False
            and python_exam_safe_cycle_console.get("score_returned") is False
            and python_exam_safe_cycle_console.get("percentage_returned") is False
            and python_exam_safe_cycle_console.get("ranking_returned") is False
            and python_exam_safe_cycle_console.get("grade_returned") is False
            and python_exam_safe_cycle_console.get("automatic_grading_started") is False
            and python_exam_safe_cycle_console.get("proctoring_started") is False
            and python_exam_safe_cycle_console.get("ai_detection_started") is False
            and python_exam_safe_cycle_console.get("exam_clearance_claimed") is False
            and python_exam_safe_cycle_console.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_safe_cycle_console, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_safe_cycle_console, ensure_ascii=False),
            "python_exam_safe_cycle_console",
            (
                f"status={python_exam_safe_cycle_console_status}, "
                f"result={python_exam_safe_cycle_console.get('status')}, "
                f"skill={python_exam_safe_cycle_console.get('selected_skill_tag')}, "
                f"cycle={safe_cycle_summary.get('cycle_status')}, "
                f"next={safe_cycle_summary.get('next_safe_action')}"
            ),
        )
    )
    gate_summary = python_exam_safe_cycle_operator_gate.get("operator_gate_summary", {})
    gate_cards = python_exam_safe_cycle_operator_gate.get("confirmation_cards", [])
    gate_matrix = python_exam_safe_cycle_operator_gate.get("operator_confirmation_matrix", {})
    checks.append(
        _check(
            python_exam_safe_cycle_operator_gate_status == 200
            and python_exam_safe_cycle_operator_gate.get("artifact_type") == "python_exam_safe_cycle_operator_gate"
            and python_exam_safe_cycle_operator_gate.get("status") == "python_exam_safe_cycle_operator_gate_ready"
            and python_exam_safe_cycle_operator_gate.get("exam_deployment_status") == "not_cleared"
            and python_exam_safe_cycle_operator_gate.get("selected_skill_tag") == "python_lists"
            and gate_summary.get("selected_skill_tag") == "python_lists"
            and gate_summary.get("gate_status") == "operator_gate_ready_for_human_review"
            and gate_summary.get("next_safe_action") == "run_next_microtask"
            and gate_summary.get("confirmation_card_count") == 5
            and gate_summary.get("confirmed_count") == 0
            and gate_summary.get("local_writes_started") is False
            and gate_summary.get("a0_a2_only") is True
            and [card.get("step_id") for card in gate_cards]
            == [
                "open_control_panel",
                "prepare_notebook_checkpoint",
                "use_a0_a2_help",
                "review_help_ledger_preview",
                "prepare_progress_journal_append",
            ]
            and all(card.get("operator_confirmed") is False for card in gate_cards)
            and all(card.get("write_started") is False for card in gate_cards)
            and all(card.get("help_level") == "A2" for card in gate_cards)
            and all(bool(card.get("card_hash")) for card in gate_cards)
            and gate_matrix.get("status") == "all_steps_waiting_for_operator_confirmation"
            and gate_matrix.get("confirmed_count") == 0
            and gate_matrix.get("local_writes_requested") is False
            and python_exam_safe_cycle_operator_gate.get("dry_run_default") is True
            and python_exam_safe_cycle_operator_gate.get("local_writes_requested") is False
            and python_exam_safe_cycle_operator_gate.get("raw_query_returned") is False
            and python_exam_safe_cycle_operator_gate.get("raw_text_returned") is False
            and python_exam_safe_cycle_operator_gate.get("raw_cell_returned") is False
            and python_exam_safe_cycle_operator_gate.get("raw_notebook_returned") is False
            and python_exam_safe_cycle_operator_gate.get("notebook_code_returned") is False
            and python_exam_safe_cycle_operator_gate.get("local_paths_returned") is False
            and python_exam_safe_cycle_operator_gate.get("values_returned") is False
            and python_exam_safe_cycle_operator_gate.get("solutions_returned") is False
            and python_exam_safe_cycle_operator_gate.get("final_interpretations_returned") is False
            and python_exam_safe_cycle_operator_gate.get("score_returned") is False
            and python_exam_safe_cycle_operator_gate.get("percentage_returned") is False
            and python_exam_safe_cycle_operator_gate.get("ranking_returned") is False
            and python_exam_safe_cycle_operator_gate.get("grade_returned") is False
            and python_exam_safe_cycle_operator_gate.get("automatic_grading_started") is False
            and python_exam_safe_cycle_operator_gate.get("proctoring_started") is False
            and python_exam_safe_cycle_operator_gate.get("ai_detection_started") is False
            and python_exam_safe_cycle_operator_gate.get("exam_clearance_claimed") is False
            and python_exam_safe_cycle_operator_gate.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_safe_cycle_operator_gate, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_safe_cycle_operator_gate, ensure_ascii=False),
            "python_exam_safe_cycle_operator_gate",
            (
                f"status={python_exam_safe_cycle_operator_gate_status}, "
                f"result={python_exam_safe_cycle_operator_gate.get('status')}, "
                f"skill={python_exam_safe_cycle_operator_gate.get('selected_skill_tag')}, "
                f"cards={gate_summary.get('confirmation_card_count')}, "
                f"confirmed={gate_summary.get('confirmed_count')}"
            ),
        )
    )
    decision_summary = python_exam_operator_gate_decision_receipt.get("decision_receipt_summary", {})
    decision_next = python_exam_operator_gate_decision_receipt.get("next_allowed_local_action", {})
    checks.append(
        _check(
            python_exam_operator_gate_decision_receipt_status == 200
            and python_exam_operator_gate_decision_receipt.get("artifact_type")
            == "python_exam_operator_gate_decision_receipt"
            and python_exam_operator_gate_decision_receipt.get("status")
            == "python_exam_operator_gate_decision_receipt_ready"
            and python_exam_operator_gate_decision_receipt.get("exam_deployment_status") == "not_cleared"
            and python_exam_operator_gate_decision_receipt.get("selected_skill_tag") == "python_lists"
            and decision_summary.get("selected_skill_tag") == "python_lists"
            and decision_summary.get("decision_status") == "decision_receipt_ready_for_human_review"
            and decision_summary.get("card_count") == 5
            and decision_summary.get("confirmed_count") == 0
            and decision_summary.get("unconfirmed_count") == 5
            and decision_summary.get("next_confirmable_step_id") == "open_control_panel"
            and decision_summary.get("local_action_execution_started") is False
            and decision_summary.get("local_writes_started") is False
            and decision_next.get("step_id") == "open_control_panel"
            and decision_next.get("status") == "awaiting_operator_confirmation"
            and decision_next.get("execution_started") is False
            and len(python_exam_operator_gate_decision_receipt.get("unconfirmed_steps", []) or []) == 5
            and python_exam_operator_gate_decision_receipt.get("confirmed_step_hash_metadata") == []
            and python_exam_operator_gate_decision_receipt.get("dry_run_default") is True
            and python_exam_operator_gate_decision_receipt.get("local_writes_requested") is False
            and python_exam_operator_gate_decision_receipt.get("local_writes_started") is False
            and python_exam_operator_gate_decision_receipt.get("raw_query_returned") is False
            and python_exam_operator_gate_decision_receipt.get("raw_text_returned") is False
            and python_exam_operator_gate_decision_receipt.get("raw_cell_returned") is False
            and python_exam_operator_gate_decision_receipt.get("raw_notebook_returned") is False
            and python_exam_operator_gate_decision_receipt.get("notebook_code_returned") is False
            and python_exam_operator_gate_decision_receipt.get("local_paths_returned") is False
            and python_exam_operator_gate_decision_receipt.get("values_returned") is False
            and python_exam_operator_gate_decision_receipt.get("solutions_returned") is False
            and python_exam_operator_gate_decision_receipt.get("final_interpretations_returned") is False
            and python_exam_operator_gate_decision_receipt.get("score_returned") is False
            and python_exam_operator_gate_decision_receipt.get("percentage_returned") is False
            and python_exam_operator_gate_decision_receipt.get("ranking_returned") is False
            and python_exam_operator_gate_decision_receipt.get("grade_returned") is False
            and python_exam_operator_gate_decision_receipt.get("automatic_grading_started") is False
            and python_exam_operator_gate_decision_receipt.get("proctoring_started") is False
            and python_exam_operator_gate_decision_receipt.get("ai_detection_started") is False
            and python_exam_operator_gate_decision_receipt.get("exam_clearance_claimed") is False
            and python_exam_operator_gate_decision_receipt.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_operator_gate_decision_receipt, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_operator_gate_decision_receipt, ensure_ascii=False),
            "python_exam_operator_gate_decision_receipt",
            (
                f"status={python_exam_operator_gate_decision_receipt_status}, "
                f"result={python_exam_operator_gate_decision_receipt.get('status')}, "
                f"skill={python_exam_operator_gate_decision_receipt.get('selected_skill_tag')}, "
                f"open={decision_summary.get('unconfirmed_count')}, "
                f"next={decision_summary.get('next_confirmable_step_id')}"
            ),
        )
    )
    start_summary = python_exam_local_cycle_start_packet.get("local_cycle_start_summary", {})
    start_packet = python_exam_local_cycle_start_packet.get("start_packet", {})
    readiness_summary = python_exam_local_cycle_readiness_review.get("readiness_review_summary", {})
    checks.append(
        _check(
            python_exam_local_cycle_start_packet_status == 200
            and python_exam_local_cycle_start_packet.get("artifact_type") == "python_exam_local_cycle_start_packet"
            and python_exam_local_cycle_start_packet.get("status") == "python_exam_local_cycle_start_packet_ready"
            and python_exam_local_cycle_start_packet.get("exam_deployment_status") == "not_cleared"
            and python_exam_local_cycle_start_packet.get("selected_skill_tag") == "python_lists"
            and start_summary.get("selected_skill_tag") == "python_lists"
            and start_summary.get("start_status") == "blocked_for_confirmation"
            and start_summary.get("blocked_reason") == "operator_confirmations_open"
            and start_summary.get("next_safe_action") == "run_next_microtask"
            and start_summary.get("next_safe_user_action") == "review_next_operator_confirmation"
            and start_summary.get("open_confirmation_count") == 5
            and start_summary.get("confirmed_count") == 0
            and start_summary.get("local_execution_started") is False
            and start_summary.get("local_writes_requested") is False
            and start_packet.get("task_hash") == safe_cycle_summary.get("selected_task_hash")
            and start_packet.get("checkpoint_hash") == safe_cycle_summary.get("checkpoint_hash")
            and len(start_packet.get("source_card_ids", []) or []) >= 1
            and start_packet.get("help_level") == "A2"
            and start_packet.get("gate_receipt_id") == python_exam_safe_cycle_operator_gate.get("operator_gate_receipt", {}).get("receipt_id")
            and start_packet.get("decision_receipt_id") == python_exam_operator_gate_decision_receipt.get("operator_decision_receipt", {}).get("receipt_id")
            and len(start_packet.get("open_confirmations", []) or []) == 5
            and start_packet.get("confirmed_hash_metadata") == []
            and python_exam_local_cycle_start_packet.get("dry_run_default") is True
            and python_exam_local_cycle_start_packet.get("local_writes_requested") is False
            and python_exam_local_cycle_start_packet.get("local_execution_started") is False
            and python_exam_local_cycle_start_packet.get("raw_query_returned") is False
            and python_exam_local_cycle_start_packet.get("raw_text_returned") is False
            and python_exam_local_cycle_start_packet.get("raw_cell_returned") is False
            and python_exam_local_cycle_start_packet.get("raw_notebook_returned") is False
            and python_exam_local_cycle_start_packet.get("notebook_code_returned") is False
            and python_exam_local_cycle_start_packet.get("local_paths_returned") is False
            and python_exam_local_cycle_start_packet.get("values_returned") is False
            and python_exam_local_cycle_start_packet.get("solutions_returned") is False
            and python_exam_local_cycle_start_packet.get("final_interpretations_returned") is False
            and python_exam_local_cycle_start_packet.get("score_returned") is False
            and python_exam_local_cycle_start_packet.get("percentage_returned") is False
            and python_exam_local_cycle_start_packet.get("ranking_returned") is False
            and python_exam_local_cycle_start_packet.get("grade_returned") is False
            and python_exam_local_cycle_start_packet.get("automatic_grading_started") is False
            and python_exam_local_cycle_start_packet.get("proctoring_started") is False
            and python_exam_local_cycle_start_packet.get("ai_detection_started") is False
            and python_exam_local_cycle_start_packet.get("exam_clearance_claimed") is False
            and python_exam_local_cycle_start_packet.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_local_cycle_start_packet, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_local_cycle_start_packet, ensure_ascii=False),
            "python_exam_local_cycle_start_packet",
            (
                f"status={python_exam_local_cycle_start_packet_status}, "
                f"result={python_exam_local_cycle_start_packet.get('status')}, "
                f"skill={python_exam_local_cycle_start_packet.get('selected_skill_tag')}, "
                f"start={start_summary.get('start_status')}, "
                f"open={start_summary.get('open_confirmation_count')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_local_cycle_readiness_review_status == 200
            and python_exam_local_cycle_readiness_review.get("artifact_type")
            == "python_exam_local_cycle_readiness_review"
            and python_exam_local_cycle_readiness_review.get("status") == "python_exam_local_cycle_readiness_review_ready"
            and python_exam_local_cycle_readiness_review.get("exam_deployment_status") == "not_cleared"
            and python_exam_local_cycle_readiness_review.get("selected_skill_tag") == "python_lists"
            and readiness_summary.get("selected_skill_tag") == "python_lists"
            and readiness_summary.get("start_status") == "blocked_for_confirmation"
            and readiness_summary.get("blocked_for_confirmation") is True
            and readiness_summary.get("request_missing_confirmation_review") is True
            and readiness_summary.get("ready_for_manual_local_cycle_review") is False
            and readiness_summary.get("keep_blocked") is False
            and readiness_summary.get("recommendation") == "request_missing_confirmation_review"
            and readiness_summary.get("recommendation_reason") == "open_confirmations_present"
            and readiness_summary.get("open_confirmation_count") == 5
            and readiness_summary.get("confirmed_count") == 0
            and readiness_summary.get("help_level") == "A2"
            and readiness_summary.get("task_hash") == safe_cycle_summary.get("selected_task_hash")
            and readiness_summary.get("checkpoint_hash") == safe_cycle_summary.get("checkpoint_hash")
            and readiness_summary.get("gate_receipt_hash") == python_exam_safe_cycle_operator_gate.get("operator_gate_receipt", {}).get("receipt_hash")
            and readiness_summary.get("decision_receipt_hash") == python_exam_operator_gate_decision_receipt.get("operator_decision_receipt", {}).get("receipt_hash")
            and readiness_summary.get("start_receipt_hash") == python_exam_local_cycle_start_packet.get("local_cycle_start_receipt", {}).get("receipt_hash")
            and len(readiness_summary.get("source_card_ids", []) or []) >= 1
            and python_exam_local_cycle_readiness_review.get("readiness_review_recommendation") == "request_missing_confirmation_review"
            and python_exam_local_cycle_readiness_review.get("readiness_review_reason") == "open_confirmations_present"
            and python_exam_local_cycle_readiness_review.get("dry_run_default") is True
            and python_exam_local_cycle_readiness_review.get("local_writes_requested") is False
            and python_exam_local_cycle_readiness_review.get("local_execution_started") is False
            and python_exam_local_cycle_readiness_review.get("raw_query_returned") is False
            and python_exam_local_cycle_readiness_review.get("raw_text_returned") is False
            and python_exam_local_cycle_readiness_review.get("raw_cell_returned") is False
            and python_exam_local_cycle_readiness_review.get("raw_notebook_returned") is False
            and python_exam_local_cycle_readiness_review.get("notebook_code_returned") is False
            and python_exam_local_cycle_readiness_review.get("local_paths_returned") is False
            and python_exam_local_cycle_readiness_review.get("values_returned") is False
            and python_exam_local_cycle_readiness_review.get("solutions_returned") is False
            and python_exam_local_cycle_readiness_review.get("final_interpretations_returned") is False
            and python_exam_local_cycle_readiness_review.get("score_returned") is False
            and python_exam_local_cycle_readiness_review.get("percentage_returned") is False
            and python_exam_local_cycle_readiness_review.get("ranking_returned") is False
            and python_exam_local_cycle_readiness_review.get("grade_returned") is False
            and python_exam_local_cycle_readiness_review.get("automatic_grading_started") is False
            and python_exam_local_cycle_readiness_review.get("proctoring_started") is False
            and python_exam_local_cycle_readiness_review.get("ai_detection_started") is False
            and python_exam_local_cycle_readiness_review.get("exam_clearance_claimed") is False
            and python_exam_local_cycle_readiness_review.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_local_cycle_readiness_review, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_local_cycle_readiness_review, ensure_ascii=False),
            "python_exam_local_cycle_readiness_review",
            (
                f"status={python_exam_local_cycle_readiness_review_status}, "
                f"result={python_exam_local_cycle_readiness_review.get('status')}, "
                f"skill={python_exam_local_cycle_readiness_review.get('selected_skill_tag')}, "
                f"recommendation={readiness_summary.get('recommendation')}, "
                f"start={readiness_summary.get('start_status')}"
            ),
        )
    )
    readiness_handoff_summary = python_exam_local_cycle_readiness_handoff.get("handoff_summary", {})
    checks.append(
        _check(
            python_exam_local_cycle_readiness_handoff_status == 200
            and python_exam_local_cycle_readiness_handoff.get("artifact_type")
            == "python_exam_local_cycle_readiness_handoff"
            and python_exam_local_cycle_readiness_handoff.get("status") == "python_exam_local_cycle_readiness_handoff_ready"
            and python_exam_local_cycle_readiness_handoff.get("exam_deployment_status") == "not_cleared"
            and python_exam_local_cycle_readiness_handoff.get("selected_skill_tag") == "python_lists"
            and readiness_handoff_summary.get("selected_skill_tag") == "python_lists"
            and readiness_handoff_summary.get("readiness_review_status") == "python_exam_local_cycle_readiness_review_ready"
            and readiness_handoff_summary.get("start_packet_status") == "python_exam_local_cycle_start_packet_ready"
            and readiness_handoff_summary.get("recommendation") == "request_missing_confirmation_review"
            and readiness_handoff_summary.get("ready_for_operator_prefill") is True
            and readiness_handoff_summary.get("operator_run_endpoint") == "/api/unibot/exam-workspace/operator-run"
            and readiness_handoff_summary.get("operator_run_method") == "POST"
            and readiness_handoff_summary.get("open_confirmation_count") == 5
            and readiness_handoff_summary.get("confirmed_count") == 0
            and readiness_handoff_summary.get("help_level") == "A2"
            and readiness_handoff_summary.get("task_hash") == safe_cycle_summary.get("selected_task_hash")
            and readiness_handoff_summary.get("checkpoint_hash") == safe_cycle_summary.get("checkpoint_hash")
            and len(readiness_handoff_summary.get("source_card_ids", []) or []) >= 1
            and python_exam_local_cycle_readiness_handoff.get("operator_run_prefill", {}).get("status") == "prefill_ready"
            and python_exam_local_cycle_readiness_handoff.get("operator_run_prefill", {}).get("endpoint")
            == "/api/unibot/exam-workspace/operator-run"
            and python_exam_local_cycle_readiness_handoff.get("manual_local_cycle_handoff", {}).get("status")
            == "manual_local_cycle_handoff_ready"
            and python_exam_local_cycle_readiness_handoff.get("handoff_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_local_cycle_readiness_handoff.get("dry_run_default") is True
            and python_exam_local_cycle_readiness_handoff.get("local_writes_requested") is False
            and python_exam_local_cycle_readiness_handoff.get("local_execution_started") is False
            and python_exam_local_cycle_readiness_handoff.get("raw_query_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("raw_text_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("raw_cell_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("raw_notebook_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("notebook_code_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("local_paths_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("values_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("solutions_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("final_interpretations_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("score_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("percentage_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("ranking_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("grade_returned") is False
            and python_exam_local_cycle_readiness_handoff.get("automatic_grading_started") is False
            and python_exam_local_cycle_readiness_handoff.get("proctoring_started") is False
            and python_exam_local_cycle_readiness_handoff.get("ai_detection_started") is False
            and python_exam_local_cycle_readiness_handoff.get("exam_clearance_claimed") is False
            and python_exam_local_cycle_readiness_handoff.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_local_cycle_readiness_handoff, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_local_cycle_readiness_handoff, ensure_ascii=False),
            "python_exam_local_cycle_readiness_handoff",
            (
                f"status={python_exam_local_cycle_readiness_handoff_status}, "
                f"result={python_exam_local_cycle_readiness_handoff.get('status')}, "
                f"skill={python_exam_local_cycle_readiness_handoff.get('selected_skill_tag')}, "
                f"prefill={readiness_handoff_summary.get('ready_for_operator_prefill')}, "
                f"next={readiness_handoff_summary.get('next_safe_action')}"
            ),
        )
    )
    manual_confirmation_summary = python_exam_manual_confirmation_console.get("console_summary", {})
    manual_confirmation_matrix = python_exam_manual_confirmation_console.get("confirmation_matrix", {})
    checks.append(
        _check(
            python_exam_manual_confirmation_console_status == 200
            and python_exam_manual_confirmation_console.get("artifact_type")
            == "python_exam_local_cycle_manual_confirmation_console"
            and python_exam_manual_confirmation_console.get("status")
            == "python_exam_local_cycle_manual_confirmation_console_ready"
            and python_exam_manual_confirmation_console.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_confirmation_console.get("selected_skill_tag") == "python_lists"
            and manual_confirmation_summary.get("selected_skill_tag") == "python_lists"
            and manual_confirmation_summary.get("next_manual_confirmation_action") == "review_missing_confirmation"
            and manual_confirmation_summary.get("open_confirmation_count") == 5
            and manual_confirmation_summary.get("confirmed_count") == 0
            and manual_confirmation_summary.get("help_level") == "A2"
            and manual_confirmation_summary.get("hash_metadata_complete") is True
            and manual_confirmation_summary.get("chain_hash_complete") is True
            and manual_confirmation_matrix.get("open_count") == 5
            and manual_confirmation_matrix.get("confirmed_count") == 0
            and len(python_exam_manual_confirmation_console.get("open_confirmation_cards", []) or []) == 5
            and python_exam_manual_confirmation_console.get("next_manual_confirmation_action") == "review_missing_confirmation"
            and python_exam_manual_confirmation_console.get("manual_confirmation_console_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_manual_confirmation_console.get("dry_run_default") is True
            and python_exam_manual_confirmation_console.get("local_writes_requested") is False
            and python_exam_manual_confirmation_console.get("local_execution_started") is False
            and python_exam_manual_confirmation_console.get("raw_query_returned") is False
            and python_exam_manual_confirmation_console.get("raw_text_returned") is False
            and python_exam_manual_confirmation_console.get("raw_cell_returned") is False
            and python_exam_manual_confirmation_console.get("raw_notebook_returned") is False
            and python_exam_manual_confirmation_console.get("notebook_code_returned") is False
            and python_exam_manual_confirmation_console.get("local_paths_returned") is False
            and python_exam_manual_confirmation_console.get("values_returned") is False
            and python_exam_manual_confirmation_console.get("solutions_returned") is False
            and python_exam_manual_confirmation_console.get("final_interpretations_returned") is False
            and python_exam_manual_confirmation_console.get("score_returned") is False
            and python_exam_manual_confirmation_console.get("percentage_returned") is False
            and python_exam_manual_confirmation_console.get("ranking_returned") is False
            and python_exam_manual_confirmation_console.get("grade_returned") is False
            and python_exam_manual_confirmation_console.get("automatic_grading_started") is False
            and python_exam_manual_confirmation_console.get("proctoring_started") is False
            and python_exam_manual_confirmation_console.get("ai_detection_started") is False
            and python_exam_manual_confirmation_console.get("exam_clearance_claimed") is False
            and python_exam_manual_confirmation_console.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_confirmation_console, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_confirmation_console, ensure_ascii=False),
            "python_exam_local_cycle_manual_confirmation_console",
            (
                f"status={python_exam_manual_confirmation_console_status}, "
                f"result={python_exam_manual_confirmation_console.get('status')}, "
                f"skill={python_exam_manual_confirmation_console.get('selected_skill_tag')}, "
                f"next={manual_confirmation_summary.get('next_manual_confirmation_action')}, "
                f"open={manual_confirmation_matrix.get('open_count')}"
            ),
        )
    )
    manual_launch_summary = python_exam_manual_cycle_launch_receipt.get("launch_receipt_summary", {})
    checks.append(
        _check(
            python_exam_manual_cycle_launch_receipt_status == 200
            and python_exam_manual_cycle_launch_receipt.get("artifact_type") == "python_exam_manual_cycle_launch_receipt"
            and python_exam_manual_cycle_launch_receipt.get("status") == "python_exam_manual_cycle_launch_receipt_ready"
            and python_exam_manual_cycle_launch_receipt.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_cycle_launch_receipt.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_cycle_launch_receipt.get("launch_decision") == "stay_in_confirmation_review"
            and manual_launch_summary.get("launch_decision") == "stay_in_confirmation_review"
            and manual_launch_summary.get("manual_confirmation_action") == "review_missing_confirmation"
            and manual_launch_summary.get("open_confirmation_count") == 5
            and manual_launch_summary.get("confirmed_count") == 0
            and manual_launch_summary.get("operator_run_prefill_hash")
            and manual_launch_summary.get("help_level") == "A2"
            and python_exam_manual_cycle_launch_receipt.get("manual_cycle_launch_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_manual_cycle_launch_receipt.get("dry_run_default") is True
            and python_exam_manual_cycle_launch_receipt.get("local_writes_requested") is False
            and python_exam_manual_cycle_launch_receipt.get("local_execution_started") is False
            and python_exam_manual_cycle_launch_receipt.get("raw_query_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("raw_text_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("raw_cell_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("raw_notebook_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("notebook_code_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("local_paths_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("values_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("solutions_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("final_interpretations_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("score_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("percentage_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("ranking_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("grade_returned") is False
            and python_exam_manual_cycle_launch_receipt.get("automatic_grading_started") is False
            and python_exam_manual_cycle_launch_receipt.get("proctoring_started") is False
            and python_exam_manual_cycle_launch_receipt.get("ai_detection_started") is False
            and python_exam_manual_cycle_launch_receipt.get("exam_clearance_claimed") is False
            and python_exam_manual_cycle_launch_receipt.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_cycle_launch_receipt, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_cycle_launch_receipt, ensure_ascii=False),
            "python_exam_manual_cycle_launch_receipt",
            (
                f"status={python_exam_manual_cycle_launch_receipt_status}, "
                f"result={python_exam_manual_cycle_launch_receipt.get('status')}, "
                f"skill={python_exam_manual_cycle_launch_receipt.get('selected_skill_tag')}, "
                f"decision={manual_launch_summary.get('launch_decision')}, "
                f"open={manual_launch_summary.get('open_confirmation_count')}"
            ),
        )
    )
    manual_binder_summary = python_exam_manual_cycle_evidence_binder.get("binder_summary", {})
    manual_binder_evidence = python_exam_manual_cycle_evidence_binder.get("manual_cycle_evidence", {})
    checks.append(
        _check(
            python_exam_manual_cycle_evidence_binder_status == 200
            and python_exam_manual_cycle_evidence_binder.get("artifact_type") == "python_exam_manual_cycle_evidence_binder"
            and python_exam_manual_cycle_evidence_binder.get("status") == "python_exam_manual_cycle_evidence_binder_ready"
            and python_exam_manual_cycle_evidence_binder.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_cycle_evidence_binder.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_cycle_evidence_binder.get("next_safe_review_action") == "continue_confirmation_review"
            and manual_binder_summary.get("next_safe_review_action") == "continue_confirmation_review"
            and manual_binder_summary.get("launch_decision") == "stay_in_confirmation_review"
            and manual_binder_summary.get("open_confirmation_count") == 5
            and manual_binder_summary.get("confirmed_count") == 0
            and manual_binder_summary.get("help_level") == "A2"
            and manual_binder_evidence.get("launch_receipt_hash")
            and manual_binder_evidence.get("manual_confirmation_console_receipt_hash")
            and manual_binder_evidence.get("chain_snapshot_hash")
            and manual_binder_evidence.get("help_ledger_preview_hash")
            and python_exam_manual_cycle_evidence_binder.get("manual_cycle_evidence_binder_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_manual_cycle_evidence_binder.get("cycle_review_window", {}).get("post_cycle_execution_claimed") is False
            and python_exam_manual_cycle_evidence_binder.get("dry_run_default") is True
            and python_exam_manual_cycle_evidence_binder.get("local_writes_requested") is False
            and python_exam_manual_cycle_evidence_binder.get("local_execution_started") is False
            and python_exam_manual_cycle_evidence_binder.get("raw_query_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("raw_text_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("raw_cell_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("raw_notebook_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("notebook_code_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("local_paths_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("values_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("solutions_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("final_interpretations_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("score_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("percentage_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("ranking_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("grade_returned") is False
            and python_exam_manual_cycle_evidence_binder.get("automatic_grading_started") is False
            and python_exam_manual_cycle_evidence_binder.get("proctoring_started") is False
            and python_exam_manual_cycle_evidence_binder.get("ai_detection_started") is False
            and python_exam_manual_cycle_evidence_binder.get("exam_clearance_claimed") is False
            and python_exam_manual_cycle_evidence_binder.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_cycle_evidence_binder, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_cycle_evidence_binder, ensure_ascii=False),
            "python_exam_manual_cycle_evidence_binder",
            (
                f"status={python_exam_manual_cycle_evidence_binder_status}, "
                f"result={python_exam_manual_cycle_evidence_binder.get('status')}, "
                f"skill={python_exam_manual_cycle_evidence_binder.get('selected_skill_tag')}, "
                f"action={manual_binder_summary.get('next_safe_review_action')}, "
                f"open={manual_binder_summary.get('open_confirmation_count')}"
            ),
        )
    )
    manual_post_cycle_summary = python_exam_manual_post_cycle_receipt_intake.get("post_cycle_intake_summary", {})
    checks.append(
        _check(
            python_exam_manual_post_cycle_receipt_intake_status == 200
            and python_exam_manual_post_cycle_receipt_intake.get("artifact_type")
            == "python_exam_manual_post_cycle_receipt_intake"
            and python_exam_manual_post_cycle_receipt_intake.get("status")
            == "python_exam_manual_post_cycle_receipt_intake_ready"
            and python_exam_manual_post_cycle_receipt_intake.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_post_cycle_receipt_intake.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_post_cycle_receipt_intake.get("post_cycle_review_recommendation")
            == "keep_post_cycle_review_open"
            and manual_post_cycle_summary.get("post_cycle_review_recommendation") == "keep_post_cycle_review_open"
            and manual_post_cycle_summary.get("binder_next_safe_review_action") == "continue_confirmation_review"
            and manual_post_cycle_summary.get("metadata_status") == "post_cycle_hash_metadata_missing"
            and manual_post_cycle_summary.get("help_level") == "A2"
            and python_exam_manual_post_cycle_receipt_intake.get("manual_post_cycle_receipt_intake", {}).get("not_cleared_receipt")
            is True
            and python_exam_manual_post_cycle_receipt_intake.get("dry_run_default") is True
            and python_exam_manual_post_cycle_receipt_intake.get("local_writes_requested") is False
            and python_exam_manual_post_cycle_receipt_intake.get("local_execution_started") is False
            and python_exam_manual_post_cycle_receipt_intake.get("raw_query_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("raw_text_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("raw_cell_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("raw_notebook_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("notebook_code_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("local_paths_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("values_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("solutions_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("final_interpretations_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("score_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("percentage_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("ranking_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("grade_returned") is False
            and python_exam_manual_post_cycle_receipt_intake.get("automatic_grading_started") is False
            and python_exam_manual_post_cycle_receipt_intake.get("proctoring_started") is False
            and python_exam_manual_post_cycle_receipt_intake.get("ai_detection_started") is False
            and python_exam_manual_post_cycle_receipt_intake.get("exam_clearance_claimed") is False
            and python_exam_manual_post_cycle_receipt_intake.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_post_cycle_receipt_intake, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_post_cycle_receipt_intake, ensure_ascii=False),
            "python_exam_manual_post_cycle_receipt_intake",
            (
                f"status={python_exam_manual_post_cycle_receipt_intake_status}, "
                f"result={python_exam_manual_post_cycle_receipt_intake.get('status')}, "
                f"skill={python_exam_manual_post_cycle_receipt_intake.get('selected_skill_tag')}, "
                f"recommendation={manual_post_cycle_summary.get('post_cycle_review_recommendation')}, "
                f"metadata={manual_post_cycle_summary.get('metadata_status')}"
            ),
        )
    )
    manual_closure_summary = python_exam_manual_cycle_closure_ledger.get("closure_summary", {})
    checks.append(
        _check(
            python_exam_manual_cycle_closure_ledger_status == 200
            and python_exam_manual_cycle_closure_ledger.get("artifact_type") == "python_exam_manual_cycle_closure_ledger"
            and python_exam_manual_cycle_closure_ledger.get("status") == "python_exam_manual_cycle_closure_ledger_ready"
            and python_exam_manual_cycle_closure_ledger.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_cycle_closure_ledger.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_cycle_closure_ledger.get("closure_ledger_decision") == "keep_cycle_open"
            and manual_closure_summary.get("closure_ledger_decision") == "keep_cycle_open"
            and manual_closure_summary.get("post_cycle_review_recommendation") == "keep_post_cycle_review_open"
            and manual_closure_summary.get("next_safe_review_action") == "continue_manual_cycle_review"
            and manual_closure_summary.get("help_level") == "A2"
            and python_exam_manual_cycle_closure_ledger.get("manual_cycle_closure_ledger_receipt", {}).get("not_cleared_receipt")
            is True
            and len(python_exam_manual_cycle_closure_ledger.get("closure_ledger_entries", [])) == 4
            and python_exam_manual_cycle_closure_ledger.get("dry_run_default") is True
            and python_exam_manual_cycle_closure_ledger.get("local_writes_requested") is False
            and python_exam_manual_cycle_closure_ledger.get("local_execution_started") is False
            and python_exam_manual_cycle_closure_ledger.get("raw_query_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("raw_text_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("raw_cell_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("raw_notebook_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("notebook_code_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("local_paths_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("values_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("solutions_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("final_interpretations_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("score_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("percentage_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("ranking_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("grade_returned") is False
            and python_exam_manual_cycle_closure_ledger.get("automatic_grading_started") is False
            and python_exam_manual_cycle_closure_ledger.get("proctoring_started") is False
            and python_exam_manual_cycle_closure_ledger.get("ai_detection_started") is False
            and python_exam_manual_cycle_closure_ledger.get("exam_clearance_claimed") is False
            and python_exam_manual_cycle_closure_ledger.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_cycle_closure_ledger, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_cycle_closure_ledger, ensure_ascii=False),
            "python_exam_manual_cycle_closure_ledger",
            (
                f"status={python_exam_manual_cycle_closure_ledger_status}, "
                f"result={python_exam_manual_cycle_closure_ledger.get('status')}, "
                f"skill={python_exam_manual_cycle_closure_ledger.get('selected_skill_tag')}, "
                f"decision={manual_closure_summary.get('closure_ledger_decision')}, "
                f"post={manual_closure_summary.get('post_cycle_review_recommendation')}"
            ),
        )
    )
    manual_timeline_summary = python_exam_manual_cycle_review_timeline.get("timeline_summary", {})
    checks.append(
        _check(
            python_exam_manual_cycle_review_timeline_status == 200
            and python_exam_manual_cycle_review_timeline.get("artifact_type") == "python_exam_manual_cycle_review_timeline"
            and python_exam_manual_cycle_review_timeline.get("status") == "python_exam_manual_cycle_review_timeline_ready"
            and python_exam_manual_cycle_review_timeline.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_cycle_review_timeline.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_cycle_review_timeline.get("timeline_review_recommendation") == "continue_cycle_review"
            and manual_timeline_summary.get("timeline_review_recommendation") == "continue_cycle_review"
            and manual_timeline_summary.get("closure_ledger_decision") == "keep_cycle_open"
            and manual_timeline_summary.get("post_cycle_review_recommendation") == "keep_post_cycle_review_open"
            and manual_timeline_summary.get("timeline_event_count") == 5
            and manual_timeline_summary.get("help_level") == "A2"
            and python_exam_manual_cycle_review_timeline.get("manual_cycle_review_timeline_receipt", {}).get("not_cleared_receipt")
            is True
            and len(python_exam_manual_cycle_review_timeline.get("timeline_events", [])) == 5
            and python_exam_manual_cycle_review_timeline.get("dry_run_default") is True
            and python_exam_manual_cycle_review_timeline.get("local_writes_requested") is False
            and python_exam_manual_cycle_review_timeline.get("local_execution_started") is False
            and python_exam_manual_cycle_review_timeline.get("raw_query_returned") is False
            and python_exam_manual_cycle_review_timeline.get("raw_text_returned") is False
            and python_exam_manual_cycle_review_timeline.get("raw_cell_returned") is False
            and python_exam_manual_cycle_review_timeline.get("raw_notebook_returned") is False
            and python_exam_manual_cycle_review_timeline.get("notebook_code_returned") is False
            and python_exam_manual_cycle_review_timeline.get("local_paths_returned") is False
            and python_exam_manual_cycle_review_timeline.get("values_returned") is False
            and python_exam_manual_cycle_review_timeline.get("solutions_returned") is False
            and python_exam_manual_cycle_review_timeline.get("final_interpretations_returned") is False
            and python_exam_manual_cycle_review_timeline.get("score_returned") is False
            and python_exam_manual_cycle_review_timeline.get("percentage_returned") is False
            and python_exam_manual_cycle_review_timeline.get("ranking_returned") is False
            and python_exam_manual_cycle_review_timeline.get("grade_returned") is False
            and python_exam_manual_cycle_review_timeline.get("automatic_grading_started") is False
            and python_exam_manual_cycle_review_timeline.get("proctoring_started") is False
            and python_exam_manual_cycle_review_timeline.get("ai_detection_started") is False
            and python_exam_manual_cycle_review_timeline.get("exam_clearance_claimed") is False
            and python_exam_manual_cycle_review_timeline.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_cycle_review_timeline, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_cycle_review_timeline, ensure_ascii=False),
            "python_exam_manual_cycle_review_timeline",
            (
                f"status={python_exam_manual_cycle_review_timeline_status}, "
                f"result={python_exam_manual_cycle_review_timeline.get('status')}, "
                f"skill={python_exam_manual_cycle_review_timeline.get('selected_skill_tag')}, "
                f"recommendation={manual_timeline_summary.get('timeline_review_recommendation')}, "
                f"events={manual_timeline_summary.get('timeline_event_count')}"
            ),
        )
    )
    manual_packet_summary = python_exam_manual_cycle_review_packet.get("review_packet_summary", {})
    checks.append(
        _check(
            python_exam_manual_cycle_review_packet_status == 200
            and python_exam_manual_cycle_review_packet.get("artifact_type") == "python_exam_manual_cycle_review_packet"
            and python_exam_manual_cycle_review_packet.get("status") == "python_exam_manual_cycle_review_packet_ready"
            and python_exam_manual_cycle_review_packet.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_cycle_review_packet.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_cycle_review_packet.get("packet_recommendation") == "keep_review_packet_open"
            and manual_packet_summary.get("packet_recommendation") == "keep_review_packet_open"
            and manual_packet_summary.get("timeline_recommendation") == "continue_cycle_review"
            and manual_packet_summary.get("closure_decision") == "keep_cycle_open"
            and manual_packet_summary.get("timeline_event_count") == 5
            and manual_packet_summary.get("help_level") == "A2"
            and python_exam_manual_cycle_review_packet.get("manual_cycle_review_packet_receipt", {}).get("not_cleared_receipt")
            is True
            and python_exam_manual_cycle_review_packet.get("dry_run_default") is True
            and python_exam_manual_cycle_review_packet.get("local_writes_requested") is False
            and python_exam_manual_cycle_review_packet.get("local_execution_started") is False
            and python_exam_manual_cycle_review_packet.get("raw_query_returned") is False
            and python_exam_manual_cycle_review_packet.get("raw_text_returned") is False
            and python_exam_manual_cycle_review_packet.get("raw_cell_returned") is False
            and python_exam_manual_cycle_review_packet.get("raw_notebook_returned") is False
            and python_exam_manual_cycle_review_packet.get("notebook_code_returned") is False
            and python_exam_manual_cycle_review_packet.get("local_paths_returned") is False
            and python_exam_manual_cycle_review_packet.get("values_returned") is False
            and python_exam_manual_cycle_review_packet.get("solutions_returned") is False
            and python_exam_manual_cycle_review_packet.get("final_interpretations_returned") is False
            and python_exam_manual_cycle_review_packet.get("score_returned") is False
            and python_exam_manual_cycle_review_packet.get("percentage_returned") is False
            and python_exam_manual_cycle_review_packet.get("ranking_returned") is False
            and python_exam_manual_cycle_review_packet.get("grade_returned") is False
            and python_exam_manual_cycle_review_packet.get("automatic_grading_started") is False
            and python_exam_manual_cycle_review_packet.get("proctoring_started") is False
            and python_exam_manual_cycle_review_packet.get("ai_detection_started") is False
            and python_exam_manual_cycle_review_packet.get("exam_clearance_claimed") is False
            and python_exam_manual_cycle_review_packet.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_cycle_review_packet, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_cycle_review_packet, ensure_ascii=False),
            "python_exam_manual_cycle_review_packet",
            (
                f"status={python_exam_manual_cycle_review_packet_status}, "
                f"result={python_exam_manual_cycle_review_packet.get('status')}, "
                f"skill={python_exam_manual_cycle_review_packet.get('selected_skill_tag')}, "
                f"recommendation={manual_packet_summary.get('packet_recommendation')}, "
                f"timeline={manual_packet_summary.get('timeline_recommendation')}"
            ),
        )
    )
    manual_export_preview_summary = python_exam_manual_review_export_preview.get("export_preview_summary", {})
    checks.append(
        _check(
            python_exam_manual_review_export_preview_status == 200
            and python_exam_manual_review_export_preview.get("artifact_type") == "python_exam_manual_review_export_preview"
            and python_exam_manual_review_export_preview.get("status") == "python_exam_manual_review_export_preview_ready"
            and python_exam_manual_review_export_preview.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_review_export_preview.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_review_export_preview.get("export_preview_recommendation") == "keep_export_preview_open"
            and manual_export_preview_summary.get("export_preview_recommendation") == "keep_export_preview_open"
            and manual_export_preview_summary.get("packet_recommendation") == "keep_review_packet_open"
            and manual_export_preview_summary.get("timeline_recommendation") == "continue_cycle_review"
            and manual_export_preview_summary.get("export_manifest_hash")
            and manual_export_preview_summary.get("help_level") == "A2"
            and python_exam_manual_review_export_preview.get("export_created") is False
            and python_exam_manual_review_export_preview.get("manual_review_export_preview_receipt", {}).get("not_cleared_receipt")
            is True
            and python_exam_manual_review_export_preview.get("dry_run_default") is True
            and python_exam_manual_review_export_preview.get("local_writes_requested") is False
            and python_exam_manual_review_export_preview.get("local_execution_started") is False
            and python_exam_manual_review_export_preview.get("raw_query_returned") is False
            and python_exam_manual_review_export_preview.get("raw_text_returned") is False
            and python_exam_manual_review_export_preview.get("raw_cell_returned") is False
            and python_exam_manual_review_export_preview.get("raw_notebook_returned") is False
            and python_exam_manual_review_export_preview.get("notebook_code_returned") is False
            and python_exam_manual_review_export_preview.get("local_paths_returned") is False
            and python_exam_manual_review_export_preview.get("values_returned") is False
            and python_exam_manual_review_export_preview.get("solutions_returned") is False
            and python_exam_manual_review_export_preview.get("final_interpretations_returned") is False
            and python_exam_manual_review_export_preview.get("score_returned") is False
            and python_exam_manual_review_export_preview.get("percentage_returned") is False
            and python_exam_manual_review_export_preview.get("ranking_returned") is False
            and python_exam_manual_review_export_preview.get("grade_returned") is False
            and python_exam_manual_review_export_preview.get("automatic_grading_started") is False
            and python_exam_manual_review_export_preview.get("proctoring_started") is False
            and python_exam_manual_review_export_preview.get("ai_detection_started") is False
            and python_exam_manual_review_export_preview.get("exam_clearance_claimed") is False
            and python_exam_manual_review_export_preview.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_review_export_preview, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_review_export_preview, ensure_ascii=False),
            "python_exam_manual_review_export_preview",
            (
                f"status={python_exam_manual_review_export_preview_status}, "
                f"result={python_exam_manual_review_export_preview.get('status')}, "
                f"skill={python_exam_manual_review_export_preview.get('selected_skill_tag')}, "
                f"recommendation={manual_export_preview_summary.get('export_preview_recommendation')}, "
                f"export_created={python_exam_manual_review_export_preview.get('export_created')}"
            ),
        )
    )
    manual_export_authorization_gate_summary = python_exam_manual_review_export_authorization_gate.get(
        "authorization_gate_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_manual_review_export_authorization_gate_status == 200
            and python_exam_manual_review_export_authorization_gate.get("artifact_type")
            == "python_exam_manual_review_export_authorization_gate"
            and python_exam_manual_review_export_authorization_gate.get("status")
            == "python_exam_manual_review_export_authorization_gate_ready"
            and python_exam_manual_review_export_authorization_gate.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_review_export_authorization_gate.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_review_export_authorization_gate.get("authorization_gate_decision")
            == "keep_export_blocked"
            and manual_export_authorization_gate_summary.get("authorization_gate_decision") == "keep_export_blocked"
            and manual_export_authorization_gate_summary.get("export_preview_recommendation") == "keep_export_preview_open"
            and manual_export_authorization_gate_summary.get("packet_recommendation") == "keep_review_packet_open"
            and manual_export_authorization_gate_summary.get("timeline_recommendation") == "continue_cycle_review"
            and manual_export_authorization_gate_summary.get("export_manifest_hash")
            and manual_export_authorization_gate_summary.get("authorization_gate_hash")
            and manual_export_authorization_gate_summary.get("help_level") == "A2"
            and python_exam_manual_review_export_authorization_gate.get("export_created") is False
            and python_exam_manual_review_export_authorization_gate.get("export_authorized") is False
            and python_exam_manual_review_export_authorization_gate.get(
                "manual_review_export_authorization_gate_receipt",
                {},
            ).get("not_cleared_receipt")
            is True
            and python_exam_manual_review_export_authorization_gate.get("dry_run_default") is True
            and python_exam_manual_review_export_authorization_gate.get("local_writes_requested") is False
            and python_exam_manual_review_export_authorization_gate.get("local_execution_started") is False
            and python_exam_manual_review_export_authorization_gate.get("raw_query_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("raw_text_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("raw_cell_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("raw_notebook_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("notebook_code_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("local_paths_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("values_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("solutions_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("final_interpretations_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("score_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("percentage_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("ranking_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("grade_returned") is False
            and python_exam_manual_review_export_authorization_gate.get("automatic_grading_started") is False
            and python_exam_manual_review_export_authorization_gate.get("proctoring_started") is False
            and python_exam_manual_review_export_authorization_gate.get("ai_detection_started") is False
            and python_exam_manual_review_export_authorization_gate.get("exam_clearance_claimed") is False
            and python_exam_manual_review_export_authorization_gate.get("public_safety_status") == "pass"
            and "runner_private_attempt"
            not in json.dumps(python_exam_manual_review_export_authorization_gate, ensure_ascii=False)
            and str(workspace_temp_dir)
            not in json.dumps(python_exam_manual_review_export_authorization_gate, ensure_ascii=False),
            "python_exam_manual_review_export_authorization_gate",
            (
                f"status={python_exam_manual_review_export_authorization_gate_status}, "
                f"result={python_exam_manual_review_export_authorization_gate.get('status')}, "
                f"skill={python_exam_manual_review_export_authorization_gate.get('selected_skill_tag')}, "
                f"decision={manual_export_authorization_gate_summary.get('authorization_gate_decision')}, "
                f"export_created={python_exam_manual_review_export_authorization_gate.get('export_created')}"
            ),
        )
    )
    manual_export_review_queue_summary = python_exam_manual_export_review_queue.get("queue_summary", {})
    manual_export_review_queue_candidates = python_exam_manual_export_review_queue.get("queue_candidates", [])
    manual_export_review_queue_primary = (
        manual_export_review_queue_candidates[0] if manual_export_review_queue_candidates else {}
    )
    checks.append(
        _check(
            python_exam_manual_export_review_queue_status == 200
            and python_exam_manual_export_review_queue.get("artifact_type")
            == "python_exam_manual_export_review_queue"
            and python_exam_manual_export_review_queue.get("status") == "python_exam_manual_export_review_queue_ready"
            and python_exam_manual_export_review_queue.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_export_review_queue.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_export_review_queue.get("queue_recommendation") == "keep_queue_open"
            and manual_export_review_queue_summary.get("queue_recommendation") == "keep_queue_open"
            and manual_export_review_queue_summary.get("queue_hash")
            and manual_export_review_queue_summary.get("candidate_count") == 1
            and manual_export_review_queue_primary.get("queue_entry_recommendation") == "keep_queue_open"
            and manual_export_review_queue_primary.get("authorization_gate_decision") == "keep_export_blocked"
            and manual_export_review_queue_primary.get("export_manifest_hash")
            and manual_export_review_queue_primary.get("authorization_gate_hash")
            and manual_export_review_queue_primary.get("help_level") == "A2"
            and python_exam_manual_export_review_queue.get("export_created") is False
            and python_exam_manual_export_review_queue.get("export_authorized") is False
            and python_exam_manual_export_review_queue.get("manual_export_review_queue_receipt", {}).get("not_cleared_receipt")
            is True
            and python_exam_manual_export_review_queue.get("dry_run_default") is True
            and python_exam_manual_export_review_queue.get("local_writes_requested") is False
            and python_exam_manual_export_review_queue.get("local_execution_started") is False
            and python_exam_manual_export_review_queue.get("raw_query_returned") is False
            and python_exam_manual_export_review_queue.get("raw_text_returned") is False
            and python_exam_manual_export_review_queue.get("raw_cell_returned") is False
            and python_exam_manual_export_review_queue.get("raw_notebook_returned") is False
            and python_exam_manual_export_review_queue.get("notebook_code_returned") is False
            and python_exam_manual_export_review_queue.get("local_paths_returned") is False
            and python_exam_manual_export_review_queue.get("values_returned") is False
            and python_exam_manual_export_review_queue.get("solutions_returned") is False
            and python_exam_manual_export_review_queue.get("final_interpretations_returned") is False
            and python_exam_manual_export_review_queue.get("score_returned") is False
            and python_exam_manual_export_review_queue.get("percentage_returned") is False
            and python_exam_manual_export_review_queue.get("ranking_returned") is False
            and python_exam_manual_export_review_queue.get("grade_returned") is False
            and python_exam_manual_export_review_queue.get("automatic_grading_started") is False
            and python_exam_manual_export_review_queue.get("proctoring_started") is False
            and python_exam_manual_export_review_queue.get("ai_detection_started") is False
            and python_exam_manual_export_review_queue.get("exam_clearance_claimed") is False
            and python_exam_manual_export_review_queue.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_export_review_queue, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_export_review_queue, ensure_ascii=False),
            "python_exam_manual_export_review_queue",
            (
                f"status={python_exam_manual_export_review_queue_status}, "
                f"result={python_exam_manual_export_review_queue.get('status')}, "
                f"skill={python_exam_manual_export_review_queue.get('selected_skill_tag')}, "
                f"recommendation={manual_export_review_queue_summary.get('queue_recommendation')}, "
                f"export_created={python_exam_manual_export_review_queue.get('export_created')}"
            ),
        )
    )
    manual_export_reviewer_packet_summary = python_exam_manual_export_reviewer_packet.get(
        "reviewer_packet_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_manual_export_reviewer_packet_status == 200
            and python_exam_manual_export_reviewer_packet.get("artifact_type")
            == "python_exam_manual_export_reviewer_packet"
            and python_exam_manual_export_reviewer_packet.get("status")
            == "python_exam_manual_export_reviewer_packet_ready"
            and python_exam_manual_export_reviewer_packet.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_export_reviewer_packet.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_export_reviewer_packet.get("reviewer_packet_recommendation")
            == "keep_reviewer_packet_open"
            and manual_export_reviewer_packet_summary.get("reviewer_packet_recommendation")
            == "keep_reviewer_packet_open"
            and manual_export_reviewer_packet_summary.get("queue_recommendation") == "keep_queue_open"
            and manual_export_reviewer_packet_summary.get("queue_hash")
            and manual_export_reviewer_packet_summary.get("candidate_hashes")
            and manual_export_reviewer_packet_summary.get("export_manifest_hash")
            and manual_export_reviewer_packet_summary.get("authorization_gate_hash")
            and manual_export_reviewer_packet_summary.get("reviewer_packet_hash")
            and manual_export_reviewer_packet_summary.get("help_level") == "A2"
            and python_exam_manual_export_reviewer_packet.get("export_created") is False
            and python_exam_manual_export_reviewer_packet.get("export_authorized") is False
            and python_exam_manual_export_reviewer_packet.get("manual_export_reviewer_packet_receipt", {}).get(
                "not_cleared_receipt"
            )
            is True
            and python_exam_manual_export_reviewer_packet.get("dry_run_default") is True
            and python_exam_manual_export_reviewer_packet.get("local_writes_requested") is False
            and python_exam_manual_export_reviewer_packet.get("local_execution_started") is False
            and python_exam_manual_export_reviewer_packet.get("raw_query_returned") is False
            and python_exam_manual_export_reviewer_packet.get("raw_text_returned") is False
            and python_exam_manual_export_reviewer_packet.get("raw_cell_returned") is False
            and python_exam_manual_export_reviewer_packet.get("raw_notebook_returned") is False
            and python_exam_manual_export_reviewer_packet.get("notebook_code_returned") is False
            and python_exam_manual_export_reviewer_packet.get("local_paths_returned") is False
            and python_exam_manual_export_reviewer_packet.get("values_returned") is False
            and python_exam_manual_export_reviewer_packet.get("solutions_returned") is False
            and python_exam_manual_export_reviewer_packet.get("final_interpretations_returned") is False
            and python_exam_manual_export_reviewer_packet.get("score_returned") is False
            and python_exam_manual_export_reviewer_packet.get("percentage_returned") is False
            and python_exam_manual_export_reviewer_packet.get("ranking_returned") is False
            and python_exam_manual_export_reviewer_packet.get("grade_returned") is False
            and python_exam_manual_export_reviewer_packet.get("automatic_grading_started") is False
            and python_exam_manual_export_reviewer_packet.get("proctoring_started") is False
            and python_exam_manual_export_reviewer_packet.get("ai_detection_started") is False
            and python_exam_manual_export_reviewer_packet.get("exam_clearance_claimed") is False
            and python_exam_manual_export_reviewer_packet.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_export_reviewer_packet, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_export_reviewer_packet, ensure_ascii=False),
            "python_exam_manual_export_reviewer_packet",
            (
                f"status={python_exam_manual_export_reviewer_packet_status}, "
                f"result={python_exam_manual_export_reviewer_packet.get('status')}, "
                f"skill={python_exam_manual_export_reviewer_packet.get('selected_skill_tag')}, "
                f"recommendation={manual_export_reviewer_packet_summary.get('reviewer_packet_recommendation')}, "
                f"export_created={python_exam_manual_export_reviewer_packet.get('export_created')}"
            ),
        )
    )
    manual_archive_decision_draft_summary = python_exam_manual_archive_decision_draft.get(
        "archive_decision_draft_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_manual_archive_decision_draft_status == 200
            and python_exam_manual_archive_decision_draft.get("artifact_type")
            == "python_exam_manual_archive_decision_draft"
            and python_exam_manual_archive_decision_draft.get("status")
            == "python_exam_manual_archive_decision_draft_ready"
            and python_exam_manual_archive_decision_draft.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_archive_decision_draft.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_archive_decision_draft.get("archive_decision_draft_recommendation")
            == "keep_archive_decision_draft_open"
            and manual_archive_decision_draft_summary.get("archive_decision_draft_recommendation")
            == "keep_archive_decision_draft_open"
            and manual_archive_decision_draft_summary.get("reviewer_packet_recommendation")
            == "keep_reviewer_packet_open"
            and manual_archive_decision_draft_summary.get("queue_recommendation") == "keep_queue_open"
            and manual_archive_decision_draft_summary.get("reviewer_packet_hash")
            and manual_archive_decision_draft_summary.get("queue_hash")
            and manual_archive_decision_draft_summary.get("export_manifest_hash")
            and manual_archive_decision_draft_summary.get("authorization_gate_hash")
            and manual_archive_decision_draft_summary.get("archive_decision_draft_hash")
            and manual_archive_decision_draft_summary.get("help_level") == "A2"
            and python_exam_manual_archive_decision_draft.get("export_created") is False
            and python_exam_manual_archive_decision_draft.get("export_authorized") is False
            and python_exam_manual_archive_decision_draft.get("archive_created") is False
            and python_exam_manual_archive_decision_draft.get("submission_started") is False
            and python_exam_manual_archive_decision_draft.get("manual_archive_decision_draft_receipt", {}).get(
                "not_cleared_receipt"
            )
            is True
            and python_exam_manual_archive_decision_draft.get("dry_run_default") is True
            and python_exam_manual_archive_decision_draft.get("local_writes_requested") is False
            and python_exam_manual_archive_decision_draft.get("local_execution_started") is False
            and python_exam_manual_archive_decision_draft.get("raw_query_returned") is False
            and python_exam_manual_archive_decision_draft.get("raw_text_returned") is False
            and python_exam_manual_archive_decision_draft.get("raw_cell_returned") is False
            and python_exam_manual_archive_decision_draft.get("raw_notebook_returned") is False
            and python_exam_manual_archive_decision_draft.get("notebook_code_returned") is False
            and python_exam_manual_archive_decision_draft.get("local_paths_returned") is False
            and python_exam_manual_archive_decision_draft.get("values_returned") is False
            and python_exam_manual_archive_decision_draft.get("solutions_returned") is False
            and python_exam_manual_archive_decision_draft.get("final_interpretations_returned") is False
            and python_exam_manual_archive_decision_draft.get("score_returned") is False
            and python_exam_manual_archive_decision_draft.get("percentage_returned") is False
            and python_exam_manual_archive_decision_draft.get("ranking_returned") is False
            and python_exam_manual_archive_decision_draft.get("grade_returned") is False
            and python_exam_manual_archive_decision_draft.get("automatic_grading_started") is False
            and python_exam_manual_archive_decision_draft.get("proctoring_started") is False
            and python_exam_manual_archive_decision_draft.get("ai_detection_started") is False
            and python_exam_manual_archive_decision_draft.get("exam_clearance_claimed") is False
            and python_exam_manual_archive_decision_draft.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_archive_decision_draft, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_archive_decision_draft, ensure_ascii=False),
            "python_exam_manual_archive_decision_draft",
            (
                f"status={python_exam_manual_archive_decision_draft_status}, "
                f"result={python_exam_manual_archive_decision_draft.get('status')}, "
                f"skill={python_exam_manual_archive_decision_draft.get('selected_skill_tag')}, "
                f"recommendation={manual_archive_decision_draft_summary.get('archive_decision_draft_recommendation')}, "
                f"archive_created={python_exam_manual_archive_decision_draft.get('archive_created')}"
            ),
        )
    )
    manual_final_review_handoff_summary = python_exam_manual_final_review_handoff.get(
        "final_review_handoff_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_manual_final_review_handoff_status == 200
            and python_exam_manual_final_review_handoff.get("artifact_type")
            == "python_exam_manual_final_review_handoff"
            and python_exam_manual_final_review_handoff.get("status")
            == "python_exam_manual_final_review_handoff_ready"
            and python_exam_manual_final_review_handoff.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_final_review_handoff.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_final_review_handoff.get("final_review_handoff_recommendation")
            == "keep_final_handoff_open"
            and manual_final_review_handoff_summary.get("final_review_handoff_recommendation")
            == "keep_final_handoff_open"
            and manual_final_review_handoff_summary.get("archive_decision_draft_recommendation")
            == "keep_archive_decision_draft_open"
            and manual_final_review_handoff_summary.get("reviewer_packet_recommendation")
            == "keep_reviewer_packet_open"
            and manual_final_review_handoff_summary.get("queue_recommendation") == "keep_queue_open"
            and manual_final_review_handoff_summary.get("archive_decision_draft_hash")
            and manual_final_review_handoff_summary.get("reviewer_packet_hash")
            and manual_final_review_handoff_summary.get("queue_hash")
            and manual_final_review_handoff_summary.get("export_manifest_hash")
            and manual_final_review_handoff_summary.get("authorization_gate_hash")
            and manual_final_review_handoff_summary.get("final_review_handoff_hash")
            and manual_final_review_handoff_summary.get("help_level") == "A2"
            and python_exam_manual_final_review_handoff.get("export_created") is False
            and python_exam_manual_final_review_handoff.get("export_authorized") is False
            and python_exam_manual_final_review_handoff.get("archive_created") is False
            and python_exam_manual_final_review_handoff.get("submission_started") is False
            and python_exam_manual_final_review_handoff.get("manual_final_review_handoff_receipt", {}).get(
                "not_cleared_receipt"
            )
            is True
            and python_exam_manual_final_review_handoff.get("dry_run_default") is True
            and python_exam_manual_final_review_handoff.get("local_writes_requested") is False
            and python_exam_manual_final_review_handoff.get("local_execution_started") is False
            and python_exam_manual_final_review_handoff.get("raw_query_returned") is False
            and python_exam_manual_final_review_handoff.get("raw_text_returned") is False
            and python_exam_manual_final_review_handoff.get("raw_cell_returned") is False
            and python_exam_manual_final_review_handoff.get("raw_notebook_returned") is False
            and python_exam_manual_final_review_handoff.get("notebook_code_returned") is False
            and python_exam_manual_final_review_handoff.get("local_paths_returned") is False
            and python_exam_manual_final_review_handoff.get("values_returned") is False
            and python_exam_manual_final_review_handoff.get("solutions_returned") is False
            and python_exam_manual_final_review_handoff.get("final_interpretations_returned") is False
            and python_exam_manual_final_review_handoff.get("score_returned") is False
            and python_exam_manual_final_review_handoff.get("percentage_returned") is False
            and python_exam_manual_final_review_handoff.get("ranking_returned") is False
            and python_exam_manual_final_review_handoff.get("grade_returned") is False
            and python_exam_manual_final_review_handoff.get("automatic_grading_started") is False
            and python_exam_manual_final_review_handoff.get("proctoring_started") is False
            and python_exam_manual_final_review_handoff.get("ai_detection_started") is False
            and python_exam_manual_final_review_handoff.get("exam_clearance_claimed") is False
            and python_exam_manual_final_review_handoff.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(python_exam_manual_final_review_handoff, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(python_exam_manual_final_review_handoff, ensure_ascii=False),
            "python_exam_manual_final_review_handoff",
            (
                f"status={python_exam_manual_final_review_handoff_status}, "
                f"result={python_exam_manual_final_review_handoff.get('status')}, "
                f"skill={python_exam_manual_final_review_handoff.get('selected_skill_tag')}, "
                f"recommendation={manual_final_review_handoff_summary.get('final_review_handoff_recommendation')}, "
                f"archive_created={python_exam_manual_final_review_handoff.get('archive_created')}"
            ),
        )
    )
    manual_final_review_receipt_ledger_summary = python_exam_manual_final_review_receipt_ledger.get(
        "final_review_receipt_ledger_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_manual_final_review_receipt_ledger_status == 200
            and python_exam_manual_final_review_receipt_ledger.get("artifact_type")
            == "python_exam_manual_final_review_receipt_ledger"
            and python_exam_manual_final_review_receipt_ledger.get("status")
            == "python_exam_manual_final_review_receipt_ledger_ready"
            and python_exam_manual_final_review_receipt_ledger.get("exam_deployment_status") == "not_cleared"
            and python_exam_manual_final_review_receipt_ledger.get("selected_skill_tag") == "python_lists"
            and python_exam_manual_final_review_receipt_ledger.get("final_review_receipt_ledger_recommendation")
            == "keep_final_ledger_open"
            and manual_final_review_receipt_ledger_summary.get("final_review_receipt_ledger_recommendation")
            == "keep_final_ledger_open"
            and manual_final_review_receipt_ledger_summary.get("final_review_handoff_recommendation")
            == "keep_final_handoff_open"
            and manual_final_review_receipt_ledger_summary.get("archive_decision_draft_recommendation")
            == "keep_archive_decision_draft_open"
            and manual_final_review_receipt_ledger_summary.get("reviewer_packet_recommendation")
            == "keep_reviewer_packet_open"
            and manual_final_review_receipt_ledger_summary.get("queue_recommendation") == "keep_queue_open"
            and manual_final_review_receipt_ledger_summary.get("final_review_handoff_hash")
            and manual_final_review_receipt_ledger_summary.get("archive_decision_draft_hash")
            and manual_final_review_receipt_ledger_summary.get("reviewer_packet_hash")
            and manual_final_review_receipt_ledger_summary.get("queue_hash")
            and manual_final_review_receipt_ledger_summary.get("export_manifest_hash")
            and manual_final_review_receipt_ledger_summary.get("authorization_gate_hash")
            and manual_final_review_receipt_ledger_summary.get("final_review_receipt_ledger_hash")
            and manual_final_review_receipt_ledger_summary.get("ledger_event_count") == 5
            and len(manual_final_review_receipt_ledger_summary.get("ledger_event_hashes", [])) == 5
            and manual_final_review_receipt_ledger_summary.get("help_level") == "A2"
            and python_exam_manual_final_review_receipt_ledger.get("export_created") is False
            and python_exam_manual_final_review_receipt_ledger.get("export_authorized") is False
            and python_exam_manual_final_review_receipt_ledger.get("archive_created") is False
            and python_exam_manual_final_review_receipt_ledger.get("submission_started") is False
            and python_exam_manual_final_review_receipt_ledger.get(
                "manual_final_review_receipt_ledger_receipt",
                {},
            ).get("not_cleared_receipt")
            is True
            and python_exam_manual_final_review_receipt_ledger.get("dry_run_default") is True
            and python_exam_manual_final_review_receipt_ledger.get("local_writes_requested") is False
            and python_exam_manual_final_review_receipt_ledger.get("local_execution_started") is False
            and python_exam_manual_final_review_receipt_ledger.get("raw_query_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("raw_text_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("raw_cell_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("raw_notebook_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("notebook_code_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("local_paths_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("values_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("solutions_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("final_interpretations_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("score_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("percentage_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("ranking_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("grade_returned") is False
            and python_exam_manual_final_review_receipt_ledger.get("automatic_grading_started") is False
            and python_exam_manual_final_review_receipt_ledger.get("proctoring_started") is False
            and python_exam_manual_final_review_receipt_ledger.get("ai_detection_started") is False
            and python_exam_manual_final_review_receipt_ledger.get("exam_clearance_claimed") is False
            and python_exam_manual_final_review_receipt_ledger.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(
                python_exam_manual_final_review_receipt_ledger,
                ensure_ascii=False,
            )
            and str(workspace_temp_dir)
            not in json.dumps(python_exam_manual_final_review_receipt_ledger, ensure_ascii=False),
            "python_exam_manual_final_review_receipt_ledger",
            (
                f"status={python_exam_manual_final_review_receipt_ledger_status}, "
                f"result={python_exam_manual_final_review_receipt_ledger.get('status')}, "
                f"skill={python_exam_manual_final_review_receipt_ledger.get('selected_skill_tag')}, "
                f"recommendation={manual_final_review_receipt_ledger_summary.get('final_review_receipt_ledger_recommendation')}, "
                f"events={manual_final_review_receipt_ledger_summary.get('ledger_event_count')}, "
                f"archive_created={python_exam_manual_final_review_receipt_ledger.get('archive_created')}"
            ),
        )
    )
    final_review_ledger_integrity_gate_summary = python_exam_final_review_ledger_integrity_gate.get(
        "final_review_ledger_integrity_gate_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_final_review_ledger_integrity_gate_status == 200
            and python_exam_final_review_ledger_integrity_gate.get("artifact_type")
            == "python_exam_final_review_ledger_integrity_gate"
            and python_exam_final_review_ledger_integrity_gate.get("status")
            == "python_exam_final_review_ledger_integrity_gate_ready"
            and python_exam_final_review_ledger_integrity_gate.get("exam_deployment_status") == "not_cleared"
            and python_exam_final_review_ledger_integrity_gate.get("selected_skill_tag") == "python_lists"
            and python_exam_final_review_ledger_integrity_gate.get("final_review_ledger_integrity_gate_recommendation")
            == "keep_integrity_gate_open"
            and final_review_ledger_integrity_gate_summary.get("final_review_ledger_integrity_gate_recommendation")
            == "keep_integrity_gate_open"
            and final_review_ledger_integrity_gate_summary.get("final_review_receipt_ledger_recommendation")
            == "keep_final_ledger_open"
            and final_review_ledger_integrity_gate_summary.get("final_review_handoff_recommendation")
            == "keep_final_handoff_open"
            and final_review_ledger_integrity_gate_summary.get("archive_decision_draft_recommendation")
            == "keep_archive_decision_draft_open"
            and final_review_ledger_integrity_gate_summary.get("reviewer_packet_recommendation")
            == "keep_reviewer_packet_open"
            and final_review_ledger_integrity_gate_summary.get("queue_recommendation") == "keep_queue_open"
            and final_review_ledger_integrity_gate_summary.get("source_hashes", {}).get("final_review_handoff_hash")
            and final_review_ledger_integrity_gate_summary.get("source_hashes", {}).get("archive_decision_draft_hash")
            and final_review_ledger_integrity_gate_summary.get("source_hashes", {}).get("reviewer_packet_hash")
            and final_review_ledger_integrity_gate_summary.get("source_hashes", {}).get("queue_hash")
            and final_review_ledger_integrity_gate_summary.get("ledger_hashes", {}).get("final_review_handoff_hash")
            and final_review_ledger_integrity_gate_summary.get("ledger_hashes", {}).get("archive_decision_draft_hash")
            and final_review_ledger_integrity_gate_summary.get("ledger_hashes", {}).get("reviewer_packet_hash")
            and final_review_ledger_integrity_gate_summary.get("ledger_hashes", {}).get("queue_hash")
            and final_review_ledger_integrity_gate_summary.get("mismatched_hashes") == []
            and final_review_ledger_integrity_gate_summary.get("chain_issue_count", 0) >= 1
            and final_review_ledger_integrity_gate_summary.get("ledger_event_count") == 5
            and len(final_review_ledger_integrity_gate_summary.get("ledger_event_hashes", [])) == 5
            and final_review_ledger_integrity_gate_summary.get("help_level") == "A2"
            and final_review_ledger_integrity_gate_summary.get("help_level_consistent") is True
            and final_review_ledger_integrity_gate_summary.get("skill_tag_consistent") is True
            and final_review_ledger_integrity_gate_summary.get("final_review_ledger_integrity_gate_hash")
            and python_exam_final_review_ledger_integrity_gate.get("export_created") is False
            and python_exam_final_review_ledger_integrity_gate.get("export_authorized") is False
            and python_exam_final_review_ledger_integrity_gate.get("archive_created") is False
            and python_exam_final_review_ledger_integrity_gate.get("submission_started") is False
            and python_exam_final_review_ledger_integrity_gate.get("final_review_ledger_integrity_gate_receipt", {}).get(
                "not_cleared_receipt"
            )
            is True
            and python_exam_final_review_ledger_integrity_gate.get("dry_run_default") is True
            and python_exam_final_review_ledger_integrity_gate.get("local_writes_requested") is False
            and python_exam_final_review_ledger_integrity_gate.get("local_execution_started") is False
            and python_exam_final_review_ledger_integrity_gate.get("raw_query_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("raw_text_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("raw_cell_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("raw_notebook_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("notebook_code_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("local_paths_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("values_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("solutions_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("final_interpretations_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("score_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("percentage_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("ranking_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("grade_returned") is False
            and python_exam_final_review_ledger_integrity_gate.get("automatic_grading_started") is False
            and python_exam_final_review_ledger_integrity_gate.get("proctoring_started") is False
            and python_exam_final_review_ledger_integrity_gate.get("ai_detection_started") is False
            and python_exam_final_review_ledger_integrity_gate.get("exam_clearance_claimed") is False
            and python_exam_final_review_ledger_integrity_gate.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(
                python_exam_final_review_ledger_integrity_gate,
                ensure_ascii=False,
            )
            and str(workspace_temp_dir)
            not in json.dumps(python_exam_final_review_ledger_integrity_gate, ensure_ascii=False),
            "python_exam_final_review_ledger_integrity_gate",
            (
                f"status={python_exam_final_review_ledger_integrity_gate_status}, "
                f"result={python_exam_final_review_ledger_integrity_gate.get('status')}, "
                f"skill={python_exam_final_review_ledger_integrity_gate.get('selected_skill_tag')}, "
                f"recommendation={final_review_ledger_integrity_gate_summary.get('final_review_ledger_integrity_gate_recommendation')}, "
                f"issues={final_review_ledger_integrity_gate_summary.get('chain_issue_count')}, "
                f"archive_created={python_exam_final_review_ledger_integrity_gate.get('archive_created')}"
            ),
        )
    )
    final_manual_review_console_summary = python_exam_final_manual_review_console.get(
        "final_manual_review_console_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_final_manual_review_console_status == 200
            and python_exam_final_manual_review_console.get("artifact_type")
            == "python_exam_final_manual_review_console"
            and python_exam_final_manual_review_console.get("status")
            == "python_exam_final_manual_review_console_ready"
            and python_exam_final_manual_review_console.get("exam_deployment_status") == "not_cleared"
            and python_exam_final_manual_review_console.get("selected_skill_tag") == "python_lists"
            and python_exam_final_manual_review_console.get("final_manual_review_console_recommendation")
            == "keep_final_console_open"
            and final_manual_review_console_summary.get("final_manual_review_console_recommendation")
            == "keep_final_console_open"
            and final_manual_review_console_summary.get("final_review_ledger_integrity_gate_recommendation")
            == "keep_integrity_gate_open"
            and final_manual_review_console_summary.get("final_review_receipt_ledger_recommendation")
            == "keep_final_ledger_open"
            and final_manual_review_console_summary.get("final_review_handoff_recommendation")
            == "keep_final_handoff_open"
            and final_manual_review_console_summary.get("archive_decision_draft_recommendation")
            == "keep_archive_decision_draft_open"
            and final_manual_review_console_summary.get("reviewer_packet_recommendation")
            == "keep_reviewer_packet_open"
            and final_manual_review_console_summary.get("queue_recommendation") == "keep_queue_open"
            and final_manual_review_console_summary.get("integrity_issue_count", 0) >= 1
            and "notebook_checkpoint_hash"
            in (final_manual_review_console_summary.get("missing_required_hashes", []) or [])
            and final_manual_review_console_summary.get("mismatched_hashes") == []
            and final_manual_review_console_summary.get("help_level") == "A2"
            and final_manual_review_console_summary.get("ledger_event_count") == 5
            and final_manual_review_console_summary.get("final_manual_review_console_hash")
            and python_exam_final_manual_review_console.get("final_manual_review_console_receipt", {}).get(
                "not_cleared_receipt"
            )
            is True
            and python_exam_final_manual_review_console.get("dry_run_default") is True
            and python_exam_final_manual_review_console.get("export_created") is False
            and python_exam_final_manual_review_console.get("export_authorized") is False
            and python_exam_final_manual_review_console.get("archive_created") is False
            and python_exam_final_manual_review_console.get("submission_started") is False
            and python_exam_final_manual_review_console.get("local_writes_requested") is False
            and python_exam_final_manual_review_console.get("local_execution_started") is False
            and python_exam_final_manual_review_console.get("raw_query_returned") is False
            and python_exam_final_manual_review_console.get("raw_text_returned") is False
            and python_exam_final_manual_review_console.get("raw_cell_returned") is False
            and python_exam_final_manual_review_console.get("raw_notebook_returned") is False
            and python_exam_final_manual_review_console.get("notebook_code_returned") is False
            and python_exam_final_manual_review_console.get("local_paths_returned") is False
            and python_exam_final_manual_review_console.get("values_returned") is False
            and python_exam_final_manual_review_console.get("solutions_returned") is False
            and python_exam_final_manual_review_console.get("final_interpretations_returned") is False
            and python_exam_final_manual_review_console.get("score_returned") is False
            and python_exam_final_manual_review_console.get("percentage_returned") is False
            and python_exam_final_manual_review_console.get("ranking_returned") is False
            and python_exam_final_manual_review_console.get("grade_returned") is False
            and python_exam_final_manual_review_console.get("automatic_grading_started") is False
            and python_exam_final_manual_review_console.get("proctoring_started") is False
            and python_exam_final_manual_review_console.get("ai_detection_started") is False
            and python_exam_final_manual_review_console.get("exam_clearance_claimed") is False
            and python_exam_final_manual_review_console.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(
                python_exam_final_manual_review_console,
                ensure_ascii=False,
            )
            and str(workspace_temp_dir)
            not in json.dumps(python_exam_final_manual_review_console, ensure_ascii=False),
            "python_exam_final_manual_review_console",
            (
                f"status={python_exam_final_manual_review_console_status}, "
                f"result={python_exam_final_manual_review_console.get('status')}, "
                f"skill={python_exam_final_manual_review_console.get('selected_skill_tag')}, "
                f"recommendation={final_manual_review_console_summary.get('final_manual_review_console_recommendation')}, "
                f"issues={final_manual_review_console_summary.get('integrity_issue_count')}, "
                f"archive_created={python_exam_final_manual_review_console.get('archive_created')}"
            ),
        )
    )
    final_manual_review_action_lock_summary = python_exam_final_manual_review_action_lock.get(
        "final_manual_review_action_lock_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_final_manual_review_action_lock_status == 200
            and python_exam_final_manual_review_action_lock.get("artifact_type")
            == "python_exam_final_manual_review_action_lock"
            and python_exam_final_manual_review_action_lock.get("status")
            == "python_exam_final_manual_review_action_lock_ready"
            and python_exam_final_manual_review_action_lock.get("exam_deployment_status") == "not_cleared"
            and python_exam_final_manual_review_action_lock.get("selected_skill_tag") == "python_lists"
            and python_exam_final_manual_review_action_lock.get("final_manual_review_action_lock_recommendation")
            == "keep_action_locked"
            and final_manual_review_action_lock_summary.get("final_manual_review_action_lock_recommendation")
            == "keep_action_locked"
            and final_manual_review_action_lock_summary.get("final_manual_review_console_recommendation")
            == "keep_final_console_open"
            and final_manual_review_action_lock_summary.get("final_review_ledger_integrity_gate_recommendation")
            == "keep_integrity_gate_open"
            and final_manual_review_action_lock_summary.get("final_review_receipt_ledger_recommendation")
            == "keep_final_ledger_open"
            and final_manual_review_action_lock_summary.get("integrity_issue_count", 0) >= 1
            and "notebook_checkpoint_hash"
            in (final_manual_review_action_lock_summary.get("missing_required_hashes", []) or [])
            and final_manual_review_action_lock_summary.get("mismatched_hashes") == []
            and final_manual_review_action_lock_summary.get("help_level") == "A2"
            and final_manual_review_action_lock_summary.get("ledger_event_count") == 5
            and final_manual_review_action_lock_summary.get("final_manual_review_action_lock_hash")
            and final_manual_review_action_lock_summary.get("final_manual_review_console_hash")
            and final_manual_review_action_lock_summary.get("final_review_ledger_integrity_gate_hash")
            and final_manual_review_action_lock_summary.get("final_review_receipt_ledger_hash")
            and python_exam_final_manual_review_action_lock.get("final_manual_review_action_lock_receipt", {}).get(
                "not_cleared_receipt"
            )
            is True
            and python_exam_final_manual_review_action_lock.get("dry_run_default") is True
            and python_exam_final_manual_review_action_lock.get("export_created") is False
            and python_exam_final_manual_review_action_lock.get("export_authorized") is False
            and python_exam_final_manual_review_action_lock.get("archive_created") is False
            and python_exam_final_manual_review_action_lock.get("submission_started") is False
            and python_exam_final_manual_review_action_lock.get("local_writes_requested") is False
            and python_exam_final_manual_review_action_lock.get("local_execution_started") is False
            and python_exam_final_manual_review_action_lock.get("raw_query_returned") is False
            and python_exam_final_manual_review_action_lock.get("raw_text_returned") is False
            and python_exam_final_manual_review_action_lock.get("raw_cell_returned") is False
            and python_exam_final_manual_review_action_lock.get("raw_notebook_returned") is False
            and python_exam_final_manual_review_action_lock.get("notebook_code_returned") is False
            and python_exam_final_manual_review_action_lock.get("local_paths_returned") is False
            and python_exam_final_manual_review_action_lock.get("values_returned") is False
            and python_exam_final_manual_review_action_lock.get("solutions_returned") is False
            and python_exam_final_manual_review_action_lock.get("final_interpretations_returned") is False
            and python_exam_final_manual_review_action_lock.get("score_returned") is False
            and python_exam_final_manual_review_action_lock.get("percentage_returned") is False
            and python_exam_final_manual_review_action_lock.get("ranking_returned") is False
            and python_exam_final_manual_review_action_lock.get("grade_returned") is False
            and python_exam_final_manual_review_action_lock.get("automatic_grading_started") is False
            and python_exam_final_manual_review_action_lock.get("proctoring_started") is False
            and python_exam_final_manual_review_action_lock.get("ai_detection_started") is False
            and python_exam_final_manual_review_action_lock.get("exam_clearance_claimed") is False
            and python_exam_final_manual_review_action_lock.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(
                python_exam_final_manual_review_action_lock,
                ensure_ascii=False,
            )
            and str(workspace_temp_dir)
            not in json.dumps(python_exam_final_manual_review_action_lock, ensure_ascii=False),
            "python_exam_final_manual_review_action_lock",
            (
                f"status={python_exam_final_manual_review_action_lock_status}, "
                f"result={python_exam_final_manual_review_action_lock.get('status')}, "
                f"skill={python_exam_final_manual_review_action_lock.get('selected_skill_tag')}, "
                f"recommendation={final_manual_review_action_lock_summary.get('final_manual_review_action_lock_recommendation')}, "
                f"issues={final_manual_review_action_lock_summary.get('integrity_issue_count')}, "
                f"archive_created={python_exam_final_manual_review_action_lock.get('archive_created')}"
            ),
        )
    )
    checks.append(
        _check(
            exam_workspace_operator_status == 200
            and exam_workspace_operator.get("artifact_type") == "exam_workspace_operator_run_dry_run"
            and exam_workspace_operator.get("status") == "exam_workspace_operator_dry_run_ready"
            and exam_workspace_operator.get("exam_deployment_status") == "not_cleared"
            and exam_workspace_operator.get("start_exam_workspace_view", {}).get("title") == "Start Exam Workspace"
            and exam_workspace_operator.get("start_exam_workspace_view", {}).get("status") == "ready_to_start_dry_run"
            and "Start Exam Workspace" in str(exam_workspace_operator.get("start_exam_workspace_markdown", ""))
            and exam_workspace_operator.get("operator_confirmation_matrix", {}).get("status") == "all_steps_dry_run"
            and exam_workspace_operator.get("operator_confirmation_matrix", {}).get("confirmed_count") == 0
            and exam_workspace_operator.get("operator_confirmation_matrix", {}).get("local_writes_requested") is False
            and exam_workspace_operator.get("dry_run_receipt", {}).get("status") == "ready_for_human_review_not_exam_clearance"
            and exam_workspace_operator.get("dry_run_receipt", {}).get("not_cleared_receipt") is True
            and exam_workspace_operator.get("dry_run_receipt", {}).get("notebook_work_sha256") == notebook_checkpoint.get("notebook_checkpoint", {}).get("notebook_work_sha256")
            and exam_workspace_operator.get("coverage_summary", {}).get("start_point", {}).get("status") == "ready"
            and exam_workspace_operator.get("local_notebook_checkpoint", {}).get("status") == "notebook_checkpoint_ready"
            and exam_workspace_operator.get("exam_workspace_run_summary", {}).get("status") == "exam_workspace_dry_run_ready"
            and exam_workspace_operator.get("help_ledger_preview", {}).get("help_level") == "A2"
            and exam_workspace_operator.get("export_receipt", {}).get("not_cleared_receipt") is True
            and exam_workspace_operator.get("raw_query_returned") is False
            and exam_workspace_operator.get("raw_cell_returned") is False
            and exam_workspace_operator.get("raw_text_returned") is False
            and exam_workspace_operator.get("raw_notebook_returned") is False
            and exam_workspace_operator.get("notebook_code_returned") is False
            and exam_workspace_operator.get("local_paths_returned") is False
            and exam_workspace_operator.get("exam_clearance_claimed") is False
            and exam_workspace_operator.get("automatic_grading_started") is False
            and exam_workspace_operator.get("proctoring_started") is False
            and exam_workspace_operator.get("ai_detection_started") is False
            and exam_workspace_operator.get("public_safety_status") == "pass",
            "exam_workspace_operator_run",
            (
                f"status={exam_workspace_operator_status}, result={exam_workspace_operator.get('status')}, "
                f"view={exam_workspace_operator.get('start_exam_workspace_view', {}).get('status')}, "
                f"confirmations={exam_workspace_operator.get('operator_confirmation_matrix', {}).get('confirmed_count')}, "
                f"receipt={exam_workspace_operator.get('dry_run_receipt', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            exam_session_console_status == 200
            and exam_session_console.get("artifact_type") == "exam_workspace_session_console"
            and exam_session_console.get("status") == "exam_workspace_session_console_ready"
            and exam_session_console.get("exam_deployment_status") == "not_cleared"
            and exam_session_console.get("session_console", {}).get("title") == "Exam Workspace Session Console"
            and exam_session_console.get("session_console", {}).get("status") == "ready_dry_run"
            and exam_session_console.get("session_console", {}).get("selected_skill", {}).get("skill_tag") == "python_lists"
            and exam_session_console.get("session_console", {}).get("workspace_status", {}).get("workspace_run_status") == "exam_workspace_dry_run_ready"
            and exam_session_console.get("session_console", {}).get("notebook_checkpoint", {}).get("notebook_work_sha256") == notebook_checkpoint.get("notebook_checkpoint", {}).get("notebook_work_sha256")
            and exam_session_console.get("session_console", {}).get("tutor_state", {}).get("effective_help_level") == "A2"
            and exam_session_console.get("session_console", {}).get("help_ledger_preview", {}).get("help_level") == "A2"
            and exam_session_console.get("session_console", {}).get("export_receipt", {}).get("not_cleared_receipt") is True
            and exam_session_console.get("session_console", {}).get("operator_confirmations", {}).get("confirmed_count") == 0
            and exam_session_console.get("session_console", {}).get("repeat_dry_run", {}).get("supported") is True
            and exam_session_console.get("session_console_receipt", {}).get("status") == "session_console_receipt_ready_not_exam_clearance"
            and exam_session_console.get("session_console_receipt", {}).get("repeat_run_index") == 1
            and "Exam Workspace Session Console" in str(exam_session_console.get("session_console_markdown", ""))
            and exam_session_console.get("raw_query_returned") is False
            and exam_session_console.get("raw_cell_returned") is False
            and exam_session_console.get("raw_text_returned") is False
            and exam_session_console.get("raw_notebook_returned") is False
            and exam_session_console.get("notebook_code_returned") is False
            and exam_session_console.get("local_paths_returned") is False
            and exam_session_console.get("exam_clearance_claimed") is False
            and exam_session_console.get("automatic_grading_started") is False
            and exam_session_console.get("proctoring_started") is False
            and exam_session_console.get("ai_detection_started") is False
            and exam_session_console.get("public_safety_status") == "pass",
            "exam_workspace_session_console",
            (
                f"status={exam_session_console_status}, result={exam_session_console.get('status')}, "
                f"view={exam_session_console.get('session_console', {}).get('status')}, "
                f"skill={exam_session_console.get('session_console', {}).get('selected_skill', {}).get('skill_tag')}, "
                f"repeat={exam_session_console.get('session_console_receipt', {}).get('repeat_run_index')}"
            ),
        )
    )
    checks.append(
        _check(
            exam_run_history_status == 200
            and exam_run_history.get("artifact_type") == "exam_workspace_run_history_export_review"
            and exam_run_history.get("status") == "exam_workspace_run_history_export_review_ready"
            and exam_run_history.get("exam_deployment_status") == "not_cleared"
            and exam_run_history.get("history_summary", {}).get("run_count", 0) >= 1
            and "python_lists" in (exam_run_history.get("history_summary", {}).get("skill_tags", []) or [])
            and exam_run_history.get("history_summary", {}).get("checkpoint_hash_count", 0) >= 1
            and exam_run_history.get("history_summary", {}).get("help_level_profile", {}).get("A2", 0) >= 1
            and exam_run_history.get("export_review_package", {}).get("status") == "export_review_ready"
            and exam_run_history.get("export_review_package", {}).get("human_reviewable_independence_evidence") is True
            and exam_run_history.get("export_review_receipt", {}).get("status") == "export_review_receipt_ready_not_exam_clearance"
            and exam_run_history.get("export_review_receipt", {}).get("not_cleared_receipt") is True
            and exam_run_history.get("raw_query_returned") is False
            and exam_run_history.get("raw_cell_returned") is False
            and exam_run_history.get("raw_text_returned") is False
            and exam_run_history.get("raw_notebook_returned") is False
            and exam_run_history.get("notebook_code_returned") is False
            and exam_run_history.get("local_paths_returned") is False
            and exam_run_history.get("exam_clearance_claimed") is False
            and exam_run_history.get("automatic_grading_started") is False
            and exam_run_history.get("proctoring_started") is False
            and exam_run_history.get("ai_detection_started") is False
            and exam_run_history.get("public_safety_status") == "pass",
            "exam_workspace_run_history_export_review",
            (
                f"status={exam_run_history_status}, result={exam_run_history.get('status')}, "
                f"runs={exam_run_history.get('history_summary', {}).get('run_count')}, "
                f"skills={','.join(exam_run_history.get('history_summary', {}).get('skill_tags', []) or [])}, "
                f"export={exam_run_history.get('export_review_package', {}).get('status')}"
            ),
        )
    )
    dashboard_python_lists = next(
        (
            item
            for item in course_exam_dashboard.get("skill_dashboard", []) or []
            if isinstance(item, dict) and item.get("skill_tag") == "python_lists"
        ),
        {},
    )
    checks.append(
        _check(
            course_exam_dashboard_status == 200
            and course_exam_dashboard.get("artifact_type") == "course_exam_coverage_dashboard"
            and course_exam_dashboard.get("status") == "course_exam_coverage_dashboard_ready"
            and course_exam_dashboard.get("exam_deployment_status") == "not_cleared"
            and course_exam_dashboard.get("dashboard_summary", {}).get("skill_count", 0) >= 1
            and course_exam_dashboard.get("dashboard_summary", {}).get("workspace_ready_skill_count", 0) >= 1
            and course_exam_dashboard.get("dashboard_summary", {}).get("skills_with_history_count", 0) >= 1
            and course_exam_dashboard.get("dashboard_summary", {}).get("checkpoint_hash_count", 0) >= 1
            and course_exam_dashboard.get("dashboard_summary", {}).get("help_level_profile", {}).get("A2", 0) >= 1
            and course_exam_dashboard.get("dashboard_summary", {}).get("open_operator_confirmation_count", 0) >= 1
            and dashboard_python_lists.get("workspace_readiness") == "ready_for_exam_workspace_dry_run"
            and dashboard_python_lists.get("checkpoint_hash_count", 0) >= 1
            and dashboard_python_lists.get("help_level_profile", {}).get("A2", 0) >= 1
            and dashboard_python_lists.get("open_operator_confirmation_count", 0) >= 1
            and course_exam_dashboard.get("coverage_receipt", {}).get("status") == "dashboard_receipt_ready_not_exam_clearance"
            and course_exam_dashboard.get("coverage_receipt", {}).get("not_cleared_receipt") is True
            and course_exam_dashboard.get("raw_query_returned") is False
            and course_exam_dashboard.get("raw_cell_returned") is False
            and course_exam_dashboard.get("raw_text_returned") is False
            and course_exam_dashboard.get("raw_notebook_returned") is False
            and course_exam_dashboard.get("notebook_code_returned") is False
            and course_exam_dashboard.get("local_paths_returned") is False
            and course_exam_dashboard.get("exam_clearance_claimed") is False
            and course_exam_dashboard.get("automatic_grading_started") is False
            and course_exam_dashboard.get("proctoring_started") is False
            and course_exam_dashboard.get("ai_detection_started") is False
            and course_exam_dashboard.get("public_safety_status") == "pass",
            "course_exam_coverage_dashboard",
            (
                f"status={course_exam_dashboard_status}, result={course_exam_dashboard.get('status')}, "
                f"skills={course_exam_dashboard.get('dashboard_summary', {}).get('skill_count')}, "
                f"ready={course_exam_dashboard.get('dashboard_summary', {}).get('workspace_ready_skill_count')}, "
                f"history={course_exam_dashboard.get('dashboard_summary', {}).get('skills_with_history_count')}"
            ),
        )
    )
    checks.append(
        _check(
            per_skill_router_status == 200
            and per_skill_router.get("artifact_type") == "course_per_skill_action_router"
            and per_skill_router.get("status") == "course_per_skill_action_router_ready"
            and per_skill_router.get("exam_deployment_status") == "not_cleared"
            and per_skill_router.get("selected_skill", {}).get("skill_tag") == "python_lists"
            and per_skill_router.get("selected_route", {}).get("route_id") == "review_open_operator_confirmations"
            and per_skill_router.get("selected_route", {}).get("endpoint") == "/api/unibot/exam-workspace/run-history-export-review"
            and per_skill_router.get("selected_route", {}).get("dry_run_by_default") is True
            and per_skill_router.get("selected_route", {}).get("requested_help_level") == "A2"
            and per_skill_router.get("selected_route", {}).get("open_operator_confirmation_count", 0) >= 1
            and per_skill_router.get("selected_route", {}).get("safety_contract", {}).get("a0_a2_only") is True
            and per_skill_router.get("router_summary", {}).get("open_operator_confirmation_route_count", 0) >= 1
            and per_skill_router.get("router_receipt", {}).get("status") == "router_receipt_ready_not_exam_clearance"
            and per_skill_router.get("router_receipt", {}).get("not_cleared_receipt") is True
            and per_skill_router.get("raw_query_returned") is False
            and per_skill_router.get("raw_cell_returned") is False
            and per_skill_router.get("raw_text_returned") is False
            and per_skill_router.get("raw_notebook_returned") is False
            and per_skill_router.get("notebook_code_returned") is False
            and per_skill_router.get("local_paths_returned") is False
            and per_skill_router.get("exam_clearance_claimed") is False
            and per_skill_router.get("automatic_grading_started") is False
            and per_skill_router.get("proctoring_started") is False
            and per_skill_router.get("ai_detection_started") is False
            and per_skill_router.get("public_safety_status") == "pass",
            "course_per_skill_action_router",
            (
                f"status={per_skill_router_status}, result={per_skill_router.get('status')}, "
                f"skill={per_skill_router.get('selected_skill', {}).get('skill_tag')}, "
                f"route={per_skill_router.get('selected_route', {}).get('route_id')}, "
                f"endpoint={per_skill_router.get('selected_route', {}).get('endpoint')}"
            ),
        )
    )
    checks.append(
        _check(
            routed_executor_status == 200
            and routed_executor.get("artifact_type") == "routed_action_executor"
            and routed_executor.get("status") == "routed_action_executor_ready"
            and routed_executor.get("exam_deployment_status") == "not_cleared"
            and routed_executor.get("selected_skill", {}).get("skill_tag") == "python_lists"
            and routed_executor.get("selected_route", {}).get("route_id") == "review_open_operator_confirmations"
            and routed_executor.get("executed_endpoint") == "/api/unibot/exam-workspace/run-history-export-review"
            and routed_executor.get("execution_result_summary", {}).get("artifact_type") == "exam_workspace_run_history_export_review"
            and routed_executor.get("execution_result_summary", {}).get("status") == "exam_workspace_run_history_export_review_ready"
            and routed_executor.get("execution_result_summary", {}).get("local_write_started") is False
            and routed_executor.get("execution_result_summary", {}).get("receipt", {}).get("not_cleared_receipt") is True
            and routed_executor.get("executor_receipt", {}).get("status") == "executor_receipt_ready_not_exam_clearance"
            and routed_executor.get("executor_receipt", {}).get("not_cleared_receipt") is True
            and routed_executor.get("operator_confirmation_summary", {}).get("dry_run_by_default") is True
            and routed_executor.get("operator_confirmation_summary", {}).get("confirmed_count") == 0
            and routed_executor.get("raw_query_returned") is False
            and routed_executor.get("raw_cell_returned") is False
            and routed_executor.get("raw_text_returned") is False
            and routed_executor.get("raw_notebook_returned") is False
            and routed_executor.get("notebook_code_returned") is False
            and routed_executor.get("local_paths_returned") is False
            and routed_executor.get("exam_clearance_claimed") is False
            and routed_executor.get("automatic_grading_started") is False
            and routed_executor.get("proctoring_started") is False
            and routed_executor.get("ai_detection_started") is False
            and routed_executor.get("public_safety_status") == "pass",
            "routed_action_executor",
            (
                f"status={routed_executor_status}, result={routed_executor.get('status')}, "
                f"route={routed_executor.get('selected_route', {}).get('route_id')}, "
                f"executed={routed_executor.get('execution_result_summary', {}).get('artifact_type')}, "
                f"receipt={routed_executor.get('executor_receipt', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            exam_run_packet_status == 200
            and exam_run_packet.get("artifact_type") == "exam_run_packet"
            and exam_run_packet.get("status") == "exam_run_packet_ready"
            and exam_run_packet.get("exam_deployment_status") == "not_cleared"
            and exam_run_packet.get("selected_skill_packet", {}).get("skill_tag") == "python_lists"
            and exam_run_packet.get("selected_skill_packet", {}).get("selected_route", {}).get("route_id")
            == "review_open_operator_confirmations"
            and exam_run_packet.get("selected_skill_packet", {}).get("executed_dry_run", {}).get("artifact_type")
            == "exam_workspace_run_history_export_review"
            and exam_run_packet.get("selected_skill_packet", {}).get("executed_dry_run", {}).get("local_write_started") is False
            and len(exam_run_packet.get("selected_skill_packet", {}).get("latest_checkpoint_hashes", []) or []) >= 1
            and exam_run_packet.get("selected_skill_packet", {}).get("help_level_profile", {}).get("A2", 0) >= 1
            and exam_run_packet.get("selected_skill_packet", {}).get("open_operator_confirmation_count", 0) >= 1
            and exam_run_packet.get("human_reviewable_independence_trace", {}).get("trace_status")
            == "human_reviewable_independence_trace_ready"
            and exam_run_packet.get("human_reviewable_independence_trace", {}).get("no_percentage_claimed") is True
            and exam_run_packet.get("packet_receipt", {}).get("status") == "exam_run_packet_receipt_ready_not_exam_clearance"
            and exam_run_packet.get("packet_receipt", {}).get("not_cleared_receipt") is True
            and exam_run_packet.get("raw_query_returned") is False
            and exam_run_packet.get("raw_cell_returned") is False
            and exam_run_packet.get("raw_text_returned") is False
            and exam_run_packet.get("raw_notebook_returned") is False
            and exam_run_packet.get("notebook_code_returned") is False
            and exam_run_packet.get("local_paths_returned") is False
            and exam_run_packet.get("exam_clearance_claimed") is False
            and exam_run_packet.get("automatic_grading_started") is False
            and exam_run_packet.get("proctoring_started") is False
            and exam_run_packet.get("ai_detection_started") is False
            and exam_run_packet.get("public_safety_status") == "pass",
            "exam_run_packet",
            (
                f"status={exam_run_packet_status}, result={exam_run_packet.get('status')}, "
                f"skill={exam_run_packet.get('selected_skill_packet', {}).get('skill_tag')}, "
                f"route={exam_run_packet.get('selected_skill_packet', {}).get('selected_route', {}).get('route_id')}, "
                f"receipt={exam_run_packet.get('packet_receipt', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            exam_packet_timeline_status == 200
            and exam_packet_timeline.get("artifact_type") == "exam_packet_timeline"
            and exam_packet_timeline.get("status") == "exam_packet_timeline_ready"
            and exam_packet_timeline.get("exam_deployment_status") == "not_cleared"
            and exam_packet_timeline.get("timeline_summary", {}).get("event_count", 0) >= 1
            and "python_lists" in (exam_packet_timeline.get("timeline_summary", {}).get("skill_tags", []) or [])
            and exam_packet_timeline.get("timeline_events", [{}])[0].get("route_id") == "review_open_operator_confirmations"
            and exam_packet_timeline.get("timeline_events", [{}])[0].get("executed_artifact_type")
            == "exam_workspace_run_history_export_review"
            and exam_packet_timeline.get("timeline_summary", {}).get("checkpoint_hash_count", 0) >= 1
            and exam_packet_timeline.get("timeline_summary", {}).get("help_level_profile", {}).get("A2", 0) >= 1
            and exam_packet_timeline.get("timeline_summary", {}).get("open_operator_confirmation_count", 0) >= 1
            and exam_packet_timeline.get("export_review_preview", {}).get("status") == "timeline_export_review_ready"
            and exam_packet_timeline.get("timeline_receipt", {}).get("status")
            == "exam_packet_timeline_receipt_ready_not_exam_clearance"
            and exam_packet_timeline.get("raw_query_returned") is False
            and exam_packet_timeline.get("raw_cell_returned") is False
            and exam_packet_timeline.get("raw_text_returned") is False
            and exam_packet_timeline.get("raw_notebook_returned") is False
            and exam_packet_timeline.get("notebook_code_returned") is False
            and exam_packet_timeline.get("local_paths_returned") is False
            and exam_packet_timeline.get("exam_clearance_claimed") is False
            and exam_packet_timeline.get("automatic_grading_started") is False
            and exam_packet_timeline.get("proctoring_started") is False
            and exam_packet_timeline.get("ai_detection_started") is False
            and exam_packet_timeline.get("public_safety_status") == "pass",
            "exam_packet_timeline",
            (
                f"status={exam_packet_timeline_status}, result={exam_packet_timeline.get('status')}, "
                f"skill={(exam_packet_timeline.get('timeline_summary', {}).get('skill_tags', []) or [''])[0]}, "
                f"events={exam_packet_timeline.get('timeline_summary', {}).get('event_count')}, "
                f"receipt={exam_packet_timeline.get('timeline_receipt', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            timeline_export_review_status == 200
            and timeline_export_review.get("artifact_type") == "timeline_export_review_packet"
            and timeline_export_review.get("status") == "timeline_export_review_packet_ready"
            and timeline_export_review.get("exam_deployment_status") == "not_cleared"
            and timeline_export_review.get("export_review_summary", {}).get("event_count", 0) >= 1
            and "python_lists" in (timeline_export_review.get("export_review_summary", {}).get("skill_tags", []) or [])
            and timeline_export_review.get("export_review_summary", {}).get("checkpoint_hash_count", 0) >= 1
            and timeline_export_review.get("export_review_summary", {}).get("help_level_profile", {}).get("A2", 0) >= 1
            and timeline_export_review.get("export_review_summary", {}).get("open_operator_confirmation_count", 0) >= 1
            and timeline_export_review.get("export_review_summary", {}).get("reviewer_question_count", 0) >= 5
            and timeline_export_review.get("skill_review_packets", [{}])[0].get("status") == "ready_for_human_review"
            and "review_open_operator_confirmations"
            in (timeline_export_review.get("skill_review_packets", [{}])[0].get("route_ids", []) or [])
            and "exam_workspace_run_history_export_review"
            in (timeline_export_review.get("skill_review_packets", [{}])[0].get("executed_artifacts", []) or [])
            and timeline_export_review.get("local_export_receipt", {}).get("status")
            == "timeline_export_review_packet_receipt_ready_not_exam_clearance"
            and timeline_export_review.get("local_export_receipt", {}).get("local_write_started") is False
            and timeline_export_review.get("raw_query_returned") is False
            and timeline_export_review.get("raw_cell_returned") is False
            and timeline_export_review.get("raw_text_returned") is False
            and timeline_export_review.get("raw_notebook_returned") is False
            and timeline_export_review.get("notebook_code_returned") is False
            and timeline_export_review.get("local_paths_returned") is False
            and timeline_export_review.get("exam_clearance_claimed") is False
            and timeline_export_review.get("automatic_grading_started") is False
            and timeline_export_review.get("proctoring_started") is False
            and timeline_export_review.get("ai_detection_started") is False
            and timeline_export_review.get("public_safety_status") == "pass",
            "timeline_export_review_packet",
            (
                f"status={timeline_export_review_status}, result={timeline_export_review.get('status')}, "
                f"skill={(timeline_export_review.get('export_review_summary', {}).get('skill_tags', []) or [''])[0]}, "
                f"events={timeline_export_review.get('export_review_summary', {}).get('event_count')}, "
                f"receipt={timeline_export_review.get('local_export_receipt', {}).get('status')}"
            ),
        )
    )
    checks.append(
        _check(
            timeline_export_receipt_preview_status == 200
            and timeline_export_receipt_preview.get("artifact_type") == "timeline_export_receipt_journal_append"
            and timeline_export_receipt_preview.get("status") == "write_preview_ready"
            and timeline_export_receipt_preview.get("journal_written") is False
            and timeline_export_receipt_preview.get("write_preview", {}).get("would_append") is True
            and timeline_export_receipt_preview.get("write_preview", {}).get("skill_tags") == ["python_lists"]
            and timeline_export_receipt_append_status == 200
            and timeline_export_receipt_append.get("status") == "stored"
            and timeline_export_receipt_append.get("journal_written") is True
            and timeline_export_receipt_journal_written is True
            and timeline_export_receipt_summary_status == 200
            and timeline_export_receipt_summary.get("artifact_type") == "timeline_export_receipt_journal_summary"
            and timeline_export_receipt_summary.get("record_count") == 1
            and timeline_export_receipt_summary.get("accepted_record_count") == 1
            and "python_lists" in (timeline_export_receipt_summary.get("skill_tags", []) or [])
            and timeline_export_receipt_summary.get("event_count", 0) >= 1
            and timeline_export_receipt_summary.get("checkpoint_hash_count", 0) >= 1
            and timeline_export_receipt_summary.get("reviewer_question_count", 0) >= 5
            and timeline_export_receipt_summary.get("help_level_profile", {}).get("A2", 0) >= 1
            and timeline_export_receipt_summary.get("open_operator_confirmation_count", 0) >= 1
            and timeline_export_receipt_summary.get("exam_deployment_status") == "not_cleared"
            and timeline_export_receipt_preview.get("local_paths_returned") is False
            and timeline_export_receipt_append.get("local_paths_returned") is False
            and timeline_export_receipt_summary.get("local_paths_returned") is False
            and timeline_export_receipt_preview.get("raw_text_returned") is False
            and timeline_export_receipt_append.get("notebook_code_returned") is False
            and timeline_export_receipt_summary.get("exam_clearance_claimed") is False
            and timeline_export_receipt_preview.get("public_safety_status") == "pass"
            and timeline_export_receipt_append.get("public_safety_status") == "pass"
            and timeline_export_receipt_summary.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(timeline_export_receipt_preview, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(timeline_export_receipt_append, ensure_ascii=False)
            and str(workspace_temp_dir) not in json.dumps(timeline_export_receipt_summary, ensure_ascii=False),
            "timeline_export_receipt_journal",
            (
                f"preview={timeline_export_receipt_preview.get('status')}, "
                f"append={timeline_export_receipt_append.get('status')}, "
                f"summary_records={timeline_export_receipt_summary.get('record_count')}, "
                f"skill={(timeline_export_receipt_summary.get('skill_tags', []) or [''])[0]}"
            ),
        )
    )
    checks.append(
        _check(
            review_chain_integrity_status == 200
            and review_chain_integrity.get("artifact_type") == "review_chain_integrity_check"
            and review_chain_integrity.get("status") == "review_chain_integrity_pass"
            and review_chain_integrity.get("exam_deployment_status") == "not_cleared"
            and review_chain_integrity.get("chain_integrity_summary", {}).get("issue_count") == 0
            and review_chain_integrity.get("chain_integrity_summary", {}).get("checked_link_count") == 4
            and "python_lists" in (review_chain_integrity.get("chain_integrity_summary", {}).get("skill_tags", []) or [])
            and review_chain_integrity.get("chain_integrity_summary", {}).get("receipt_ids", {}).get("packet_receipt_id")
            and review_chain_integrity.get("chain_integrity_summary", {}).get("receipt_ids", {}).get("timeline_receipt_id")
            and review_chain_integrity.get("chain_integrity_summary", {}).get("receipt_ids", {}).get("review_receipt_id")
            and review_chain_integrity.get("chain_integrity_summary", {}).get("receipt_ids", {}).get("journal_receipt_id")
            and review_chain_integrity.get("chain_integrity_summary", {}).get("counts", {}).get("timeline_event_count", 0) >= 1
            and review_chain_integrity.get("chain_integrity_summary", {}).get("counts", {}).get("review_event_count", 0) >= 1
            and review_chain_integrity.get("chain_integrity_summary", {}).get("counts", {}).get("journal_event_count", 0) >= 1
            and review_chain_integrity.get("chain_integrity_summary", {}).get("counts", {}).get("timeline_checkpoint_hash_count", 0) >= 1
            and review_chain_integrity.get("chain_integrity_summary", {}).get("counts", {}).get("reviewer_question_count", 0) >= 5
            and review_chain_integrity.get("raw_query_returned") is False
            and review_chain_integrity.get("raw_text_returned") is False
            and review_chain_integrity.get("raw_cell_returned") is False
            and review_chain_integrity.get("raw_notebook_returned") is False
            and review_chain_integrity.get("notebook_code_returned") is False
            and review_chain_integrity.get("local_paths_returned") is False
            and review_chain_integrity.get("automatic_grading_started") is False
            and review_chain_integrity.get("proctoring_started") is False
            and review_chain_integrity.get("ai_detection_started") is False
            and review_chain_integrity.get("exam_clearance_claimed") is False
            and review_chain_integrity.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(review_chain_integrity, ensure_ascii=False),
            "review_chain_integrity",
            (
                f"status={review_chain_integrity_status}, result={review_chain_integrity.get('status')}, "
                f"issues={review_chain_integrity.get('chain_integrity_summary', {}).get('issue_count')}, "
                f"next={review_chain_integrity.get('chain_integrity_summary', {}).get('next_safe_action')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_readiness_status == 200
            and python_exam_readiness.get("artifact_type") == "python_exam_readiness_console"
            and python_exam_readiness.get("status") == "python_exam_readiness_console_ready"
            and python_exam_readiness.get("exam_deployment_status") == "not_cleared"
            and python_exam_readiness.get("readiness_summary", {}).get("selected_skill_tag") == "python_lists"
            and python_exam_readiness.get("readiness_summary", {}).get("skill_ready_for_workspace") is True
            and python_exam_readiness.get("readiness_summary", {}).get("source_anchored") is True
            and python_exam_readiness.get("readiness_summary", {}).get("review_chain_pass") is True
            and python_exam_readiness.get("readiness_summary", {}).get("receipt_journal_ready") is True
            and python_exam_readiness.get("readiness_summary", {}).get("latest_notebook_checkpoint_hash")
            and python_exam_readiness.get("a0_a2_help_status", {}).get("status") == "a0_a2_only"
            and python_exam_readiness.get("a0_a2_help_status", {}).get("nonstandard_help_event_count") == 0
            and python_exam_readiness.get("operator_confirmation_status", {}).get("open_operator_confirmation_count", 0) >= 1
            and python_exam_readiness.get("review_chain_status", {}).get("issue_count") == 0
            and python_exam_readiness.get("receipt_journal_status", {}).get("accepted_record_count") == 1
            and python_exam_readiness.get("raw_query_returned") is False
            and python_exam_readiness.get("raw_text_returned") is False
            and python_exam_readiness.get("raw_cell_returned") is False
            and python_exam_readiness.get("raw_notebook_returned") is False
            and python_exam_readiness.get("notebook_code_returned") is False
            and python_exam_readiness.get("local_paths_returned") is False
            and python_exam_readiness.get("values_returned") is False
            and python_exam_readiness.get("solutions_returned") is False
            and python_exam_readiness.get("final_interpretations_returned") is False
            and python_exam_readiness.get("automatic_grading_started") is False
            and python_exam_readiness.get("proctoring_started") is False
            and python_exam_readiness.get("ai_detection_started") is False
            and python_exam_readiness.get("exam_clearance_claimed") is False
            and python_exam_readiness.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_readiness, ensure_ascii=False),
            "python_exam_readiness_console",
            (
                f"status={python_exam_readiness_status}, result={python_exam_readiness.get('status')}, "
                f"skill={python_exam_readiness.get('readiness_summary', {}).get('selected_skill_tag')}, "
                f"chain={python_exam_readiness.get('review_chain_status', {}).get('status')}, "
                f"next={python_exam_readiness.get('readiness_summary', {}).get('next_safe_action')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_cockpit_status == 200
            and python_exam_cockpit.get("artifact_type") == "python_exam_cockpit_flow"
            and python_exam_cockpit.get("status") == "python_exam_cockpit_flow_ready"
            and python_exam_cockpit.get("exam_deployment_status") == "not_cleared"
            and python_exam_cockpit.get("selected_skill_tag") == "python_lists"
            and python_exam_cockpit.get("cockpit_summary", {}).get("step_count") == 9
            and python_exam_cockpit.get("cockpit_summary", {}).get("complete_step_count") == 9
            and python_exam_cockpit.get("cockpit_summary", {}).get("attention_step_count") == 0
            and python_exam_cockpit.get("cockpit_summary", {}).get("dry_run_default") is True
            and python_exam_cockpit.get("local_writes_executed_by_cockpit") is False
            and python_exam_cockpit.get("operator_confirmation_status", {}).get("local_writes_require_confirmation") is True
            and python_exam_cockpit.get("operator_confirmation_status", {}).get("confirmed_local_write_step_count") == 0
            and python_exam_cockpit.get("evidence_receipts", {}).get("operator_receipt_id")
            and python_exam_cockpit.get("evidence_receipts", {}).get("session_receipt_id")
            and python_exam_cockpit.get("evidence_receipts", {}).get("notebook_checkpoint_hash")
            and python_exam_cockpit.get("evidence_receipts", {}).get("review_chain_status") == "review_chain_integrity_pass"
            and python_exam_cockpit.get("evidence_receipts", {}).get("receipt_journal_accepted_record_count") == 1
            and [item.get("step_id") for item in python_exam_cockpit.get("step_bar", [])]
            == [
                "select_skill",
                "readiness_check",
                "start_exam_workspace_operator_dry_run",
                "session_console",
                "notebook_checkpoint",
                "a0_a2_tutor_sidecar",
                "help_exam_ledger_preview",
                "review_chain_integrity",
                "export_receipt_summary",
            ]
            and python_exam_cockpit.get("raw_query_returned") is False
            and python_exam_cockpit.get("raw_text_returned") is False
            and python_exam_cockpit.get("raw_cell_returned") is False
            and python_exam_cockpit.get("raw_notebook_returned") is False
            and python_exam_cockpit.get("notebook_code_returned") is False
            and python_exam_cockpit.get("local_paths_returned") is False
            and python_exam_cockpit.get("values_returned") is False
            and python_exam_cockpit.get("solutions_returned") is False
            and python_exam_cockpit.get("final_interpretations_returned") is False
            and python_exam_cockpit.get("automatic_grading_started") is False
            and python_exam_cockpit.get("proctoring_started") is False
            and python_exam_cockpit.get("ai_detection_started") is False
            and python_exam_cockpit.get("exam_clearance_claimed") is False
            and python_exam_cockpit.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_cockpit, ensure_ascii=False),
            "python_exam_cockpit_flow",
            (
                f"status={python_exam_cockpit_status}, result={python_exam_cockpit.get('status')}, "
                f"steps={python_exam_cockpit.get('cockpit_summary', {}).get('complete_step_count')}/"
                f"{python_exam_cockpit.get('cockpit_summary', {}).get('step_count')}, "
                f"next={python_exam_cockpit.get('next_safe_action')}"
            ),
        )
    )
    live_control_endpoints = {
        item.get("safe_action_id"): item.get("endpoint")
        for item in python_exam_live_control.get("control_actions", [])
        if isinstance(item, dict)
    }
    checks.append(
        _check(
            python_exam_live_control_status == 200
            and python_exam_live_control.get("artifact_type") == "python_exam_live_control_surface"
            and python_exam_live_control.get("status") == "python_exam_live_control_surface_ready"
            and python_exam_live_control.get("exam_deployment_status") == "not_cleared"
            and python_exam_live_control.get("sidepanel_first") is True
            and python_exam_live_control.get("selected_skill_tag") == "python_lists"
            and python_exam_live_control.get("control_summary", {}).get("action_count") == 9
            and python_exam_live_control.get("control_summary", {}).get("enabled_action_count") == 9
            and python_exam_live_control.get("control_summary", {}).get("current_step_id") == "export_receipt_summary"
            and python_exam_live_control.get("control_summary", {}).get("dry_run_default") is True
            and python_exam_live_control.get("status_lights", {}).get("overall") == "green"
            and python_exam_live_control.get("status_lights", {}).get("a0_a2") == "green"
            and python_exam_live_control.get("status_lights", {}).get("review_chain") == "green"
            and python_exam_live_control.get("status_lights", {}).get("receipt_journal") == "green"
            and live_control_endpoints.get("readiness_refresh") == "/api/unibot/course/python-exam-readiness-console"
            and live_control_endpoints.get("operator_dry_run") == "/api/unibot/exam-workspace/operator-run"
            and live_control_endpoints.get("session_console_refresh") == "/api/unibot/exam-workspace/session-console"
            and live_control_endpoints.get("notebook_checkpoint_hash") == "/api/unibot/exam-workspace/notebook-checkpoint/adapt"
            and live_control_endpoints.get("ledger_preview_check") == "/api/unibot/exam-workspace/session-console"
            and live_control_endpoints.get("review_chain_check") == "/api/unibot/course/review-chain-integrity-check"
            and live_control_endpoints.get("receipt_summary_refresh") == "/api/unibot/course/timeline-export-receipt-journal/summary"
            and python_exam_live_control.get("operator_confirmation_status", {}).get("local_writes_require_confirmation") is True
            and python_exam_live_control.get("operator_confirmation_status", {}).get("open_operator_confirmation_count", 0) >= 1
            and python_exam_live_control.get("evidence_receipts", {}).get("operator_receipt_id")
            and python_exam_live_control.get("evidence_receipts", {}).get("session_receipt_id")
            and python_exam_live_control.get("evidence_receipts", {}).get("notebook_checkpoint_hash")
            and python_exam_live_control.get("evidence_receipts", {}).get("review_chain_status") == "review_chain_integrity_pass"
            and python_exam_live_control.get("evidence_receipts", {}).get("receipt_journal_accepted_record_count") == 1
            and python_exam_live_control.get("local_writes_executed_by_surface") is False
            and python_exam_live_control.get("raw_query_returned") is False
            and python_exam_live_control.get("raw_text_returned") is False
            and python_exam_live_control.get("raw_cell_returned") is False
            and python_exam_live_control.get("raw_notebook_returned") is False
            and python_exam_live_control.get("notebook_code_returned") is False
            and python_exam_live_control.get("local_paths_returned") is False
            and python_exam_live_control.get("values_returned") is False
            and python_exam_live_control.get("solutions_returned") is False
            and python_exam_live_control.get("final_interpretations_returned") is False
            and python_exam_live_control.get("automatic_grading_started") is False
            and python_exam_live_control.get("proctoring_started") is False
            and python_exam_live_control.get("ai_detection_started") is False
            and python_exam_live_control.get("exam_clearance_claimed") is False
            and python_exam_live_control.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_live_control, ensure_ascii=False),
            "python_exam_live_control_surface",
            (
                f"status={python_exam_live_control_status}, result={python_exam_live_control.get('status')}, "
                f"actions={python_exam_live_control.get('control_summary', {}).get('enabled_action_count')}/"
                f"{python_exam_live_control.get('control_summary', {}).get('action_count')}, "
                f"next={python_exam_live_control.get('next_safe_action')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_evidence_export_preview_status == 200
            and python_exam_evidence_export_preview.get("artifact_type") == "python_exam_evidence_export_preview"
            and python_exam_evidence_export_preview.get("status") == "python_exam_evidence_export_preview_ready"
            and python_exam_evidence_export_preview.get("exam_deployment_status") == "not_cleared"
            and python_exam_evidence_export_preview.get("selected_skill_tag") == "python_lists"
            and python_exam_evidence_export_preview.get("preview_summary", {}).get("cockpit_step_count") == 9
            and python_exam_evidence_export_preview.get("preview_summary", {}).get("live_control_action_count") == 9
            and python_exam_evidence_export_preview.get("preview_summary", {}).get("help_status") == "a0_a2_only"
            and python_exam_evidence_export_preview.get("preview_summary", {}).get("review_chain_status") == "review_chain_integrity_pass"
            and python_exam_evidence_export_preview.get("preview_summary", {}).get("notebook_checkpoint_hash_present") is True
            and python_exam_evidence_export_preview.get("preview_summary", {}).get("receipt_journal_accepted_record_count") == 1
            and python_exam_evidence_export_preview.get("preview_manifest", {}).get("notebook_checkpoint", {}).get("notebook_checkpoint_hash")
            and python_exam_evidence_export_preview.get("preview_manifest", {}).get("operator_confirmation_profile", {}).get("open_operator_confirmation_count", 0) >= 1
            and python_exam_evidence_export_preview.get("human_review_packet", {}).get("status") == "ready_for_human_review"
            and python_exam_evidence_export_preview.get("preview_receipt", {}).get("status") == "python_exam_evidence_export_preview_receipt_ready_not_exam_clearance"
            and python_exam_evidence_export_preview.get("preview_receipt", {}).get("receipt_id")
            and python_exam_evidence_export_preview.get("dry_run_default") is True
            and python_exam_evidence_export_preview.get("export_preview_only") is True
            and python_exam_evidence_export_preview.get("local_export_package_written") is False
            and python_exam_evidence_export_preview.get("operator_confirmation_required_for_export_write") is True
            and python_exam_evidence_export_preview.get("operator_confirmed_export_write") is False
            and python_exam_evidence_export_preview.get("raw_query_returned") is False
            and python_exam_evidence_export_preview.get("raw_text_returned") is False
            and python_exam_evidence_export_preview.get("raw_cell_returned") is False
            and python_exam_evidence_export_preview.get("raw_notebook_returned") is False
            and python_exam_evidence_export_preview.get("notebook_code_returned") is False
            and python_exam_evidence_export_preview.get("local_paths_returned") is False
            and python_exam_evidence_export_preview.get("values_returned") is False
            and python_exam_evidence_export_preview.get("solutions_returned") is False
            and python_exam_evidence_export_preview.get("final_interpretations_returned") is False
            and python_exam_evidence_export_preview.get("automatic_grading_started") is False
            and python_exam_evidence_export_preview.get("proctoring_started") is False
            and python_exam_evidence_export_preview.get("ai_detection_started") is False
            and python_exam_evidence_export_preview.get("exam_clearance_claimed") is False
            and python_exam_evidence_export_preview.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_evidence_export_preview, ensure_ascii=False),
            "python_exam_evidence_export_preview",
            (
                f"status={python_exam_evidence_export_preview_status}, "
                f"result={python_exam_evidence_export_preview.get('status')}, "
                f"steps={python_exam_evidence_export_preview.get('preview_summary', {}).get('cockpit_step_count')}, "
                f"actions={python_exam_evidence_export_preview.get('preview_summary', {}).get('live_control_action_count')}, "
                f"next={python_exam_evidence_export_preview.get('preview_summary', {}).get('next_safe_action')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_local_export_draft_preview_status == 200
            and python_exam_local_export_draft_preview.get("artifact_type") == "python_exam_confirmed_local_export_draft"
            and python_exam_local_export_draft_preview.get("status") == "python_exam_confirmed_local_export_draft_preview_ready"
            and python_exam_local_export_draft_preview.get("exam_deployment_status") == "not_cleared"
            and python_exam_local_export_draft_preview.get("operator_confirmed_local_export_draft_write") is False
            and python_exam_local_export_draft_preview.get("operator_confirmation_required_for_local_write") is True
            and python_exam_local_export_draft_preview.get("local_export_draft_written") is False
            and python_exam_local_export_draft_preview.get("local_export_package_written") is False
            and python_exam_local_export_draft_preview.get("draft_file_count") == 3
            and len(python_exam_local_export_draft_preview.get("draft_file_manifest", [])) == 3
            and python_exam_local_export_draft_preview.get("draft_receipt", {}).get("status") == "local_export_draft_receipt_ready_not_exam_clearance"
            and python_exam_local_export_draft_preview.get("draft_receipt", {}).get("draft_package_id")
            and python_exam_local_export_draft_preview.get("dry_run_default") is True
            and python_exam_local_export_draft_preview.get("local_paths_returned") is False
            and python_exam_local_export_draft_preview.get("export_draft_dir_returned") is False
            and python_exam_local_export_draft_preview.get("raw_query_returned") is False
            and python_exam_local_export_draft_preview.get("raw_text_returned") is False
            and python_exam_local_export_draft_preview.get("raw_cell_returned") is False
            and python_exam_local_export_draft_preview.get("raw_notebook_returned") is False
            and python_exam_local_export_draft_preview.get("notebook_code_returned") is False
            and python_exam_local_export_draft_preview.get("values_returned") is False
            and python_exam_local_export_draft_preview.get("solutions_returned") is False
            and python_exam_local_export_draft_preview.get("final_interpretations_returned") is False
            and python_exam_local_export_draft_preview.get("automatic_grading_started") is False
            and python_exam_local_export_draft_preview.get("proctoring_started") is False
            and python_exam_local_export_draft_preview.get("ai_detection_started") is False
            and python_exam_local_export_draft_preview.get("exam_clearance_claimed") is False
            and python_exam_local_export_draft_preview.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_local_export_draft_preview, ensure_ascii=False),
            "python_exam_confirmed_local_export_draft_preview",
            (
                f"status={python_exam_local_export_draft_preview_status}, "
                f"result={python_exam_local_export_draft_preview.get('status')}, "
                f"files={python_exam_local_export_draft_preview.get('draft_file_count')}, "
                f"written={python_exam_local_export_draft_preview.get('local_export_draft_written')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_local_export_draft_confirmed_status == 200
            and python_exam_local_export_draft_confirmed.get("artifact_type") == "python_exam_confirmed_local_export_draft"
            and python_exam_local_export_draft_confirmed.get("status") == "python_exam_confirmed_local_export_draft_written"
            and python_exam_local_export_draft_confirmed.get("exam_deployment_status") == "not_cleared"
            and python_exam_local_export_draft_confirmed.get("operator_confirmed_local_export_draft_write") is True
            and python_exam_local_export_draft_confirmed.get("operator_confirmation_required_for_local_write") is True
            and python_exam_local_export_draft_confirmed.get("local_export_draft_written") is True
            and python_exam_local_export_draft_confirmed.get("local_export_package_written") is True
            and python_exam_local_export_draft_confirmed.get("draft_file_count") == 3
            and local_export_draft_file_names
            == ["draft_receipt.json", "manifest.json", "not_cleared_receipt.json", "process_log.json"]
            and python_exam_local_export_draft_confirmed.get("draft_receipt", {}).get("draft_package_id")
            and python_exam_local_export_draft_confirmed.get("draft_receipt", {}).get("draft_package_hash")
            and python_exam_local_export_draft_confirmed.get("draft_summary", {}).get("write_result_status") == "local_export_draft_written"
            and python_exam_local_export_draft_confirmed.get("local_paths_returned") is False
            and python_exam_local_export_draft_confirmed.get("export_draft_dir_returned") is False
            and python_exam_local_export_draft_confirmed.get("raw_query_returned") is False
            and python_exam_local_export_draft_confirmed.get("raw_text_returned") is False
            and python_exam_local_export_draft_confirmed.get("raw_cell_returned") is False
            and python_exam_local_export_draft_confirmed.get("raw_notebook_returned") is False
            and python_exam_local_export_draft_confirmed.get("notebook_code_returned") is False
            and python_exam_local_export_draft_confirmed.get("values_returned") is False
            and python_exam_local_export_draft_confirmed.get("solutions_returned") is False
            and python_exam_local_export_draft_confirmed.get("final_interpretations_returned") is False
            and python_exam_local_export_draft_confirmed.get("automatic_grading_started") is False
            and python_exam_local_export_draft_confirmed.get("proctoring_started") is False
            and python_exam_local_export_draft_confirmed.get("ai_detection_started") is False
            and python_exam_local_export_draft_confirmed.get("exam_clearance_claimed") is False
            and python_exam_local_export_draft_confirmed.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_local_export_draft_confirmed, ensure_ascii=False),
            "python_exam_confirmed_local_export_draft_write",
            (
                f"status={python_exam_local_export_draft_confirmed_status}, "
                f"result={python_exam_local_export_draft_confirmed.get('status')}, "
                f"files={len(local_export_draft_file_names)}, "
                f"written={python_exam_local_export_draft_confirmed.get('local_export_draft_written')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_draft_review_console_status == 200
            and python_exam_draft_review_console.get("artifact_type") == "python_exam_draft_package_review_console"
            and python_exam_draft_review_console.get("status") == "python_exam_draft_package_review_console_ready"
            and python_exam_draft_review_console.get("exam_deployment_status") == "not_cleared"
            and python_exam_draft_review_console.get("review_summary", {}).get("draft_present_status") == "written"
            and python_exam_draft_review_console.get("review_summary", {}).get("file_hash_integrity_status") == "file_hash_integrity_pass"
            and python_exam_draft_review_console.get("review_summary", {}).get("manifest_status") == "manifest_present"
            and python_exam_draft_review_console.get("review_summary", {}).get("not_cleared_receipt_status") == "not_cleared_receipt_present"
            and python_exam_draft_review_console.get("review_summary", {}).get("process_log_status") == "process_log_present"
            and python_exam_draft_review_console.get("review_summary", {}).get("help_status") == "a0_a2_only"
            and python_exam_draft_review_console.get("review_summary", {}).get("review_chain_status") == "review_chain_integrity_pass"
            and python_exam_draft_review_console.get("package_integrity", {}).get("file_count") == 3
            and python_exam_draft_review_console.get("package_integrity", {}).get("mismatched_file_hashes") == []
            and python_exam_draft_review_console.get("receipt_journal_status", {}).get("accepted_record_count") == 1
            and python_exam_draft_review_console.get("operator_confirmation_status", {}).get("local_export_draft_written") is True
            and len(python_exam_draft_review_console.get("review_questions", [])) >= 1
            and python_exam_draft_review_console.get("local_paths_returned") is False
            and python_exam_draft_review_console.get("export_draft_dir_returned") is False
            and python_exam_draft_review_console.get("raw_query_returned") is False
            and python_exam_draft_review_console.get("raw_text_returned") is False
            and python_exam_draft_review_console.get("raw_cell_returned") is False
            and python_exam_draft_review_console.get("raw_notebook_returned") is False
            and python_exam_draft_review_console.get("notebook_code_returned") is False
            and python_exam_draft_review_console.get("values_returned") is False
            and python_exam_draft_review_console.get("solutions_returned") is False
            and python_exam_draft_review_console.get("final_interpretations_returned") is False
            and python_exam_draft_review_console.get("automatic_grading_started") is False
            and python_exam_draft_review_console.get("proctoring_started") is False
            and python_exam_draft_review_console.get("ai_detection_started") is False
            and python_exam_draft_review_console.get("exam_clearance_claimed") is False
            and python_exam_draft_review_console.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_draft_review_console, ensure_ascii=False),
            "python_exam_draft_package_review_console",
            (
                f"status={python_exam_draft_review_console_status}, "
                f"result={python_exam_draft_review_console.get('status')}, "
                f"integrity={python_exam_draft_review_console.get('package_integrity', {}).get('status')}, "
                f"draft={python_exam_draft_review_console.get('review_summary', {}).get('draft_present_status')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_full_rehearsal_status == 200
            and python_exam_full_rehearsal.get("artifact_type") == "python_exam_full_local_rehearsal_pack"
            and python_exam_full_rehearsal.get("status") == "python_exam_full_local_rehearsal_pack_ready"
            and python_exam_full_rehearsal.get("exam_deployment_status") == "not_cleared"
            and python_exam_full_rehearsal.get("selected_skill_tag") == "python_lists"
            and python_exam_full_rehearsal.get("rehearsal_summary", {}).get("step_count") == 12
            and python_exam_full_rehearsal.get("rehearsal_summary", {}).get("ready_step_count") == 12
            and python_exam_full_rehearsal.get("rehearsal_summary", {}).get("attention_step_count") == 0
            and python_exam_full_rehearsal.get("rehearsal_summary", {}).get("missing_step_count") == 0
            and python_exam_full_rehearsal.get("rehearsal_summary", {}).get("local_cycle_chain_snapshot_hash")
            and python_exam_full_rehearsal.get("source_anchor_metadata", {}).get("source_anchor_count", 0) >= 1
            and python_exam_full_rehearsal.get("a0_a2_help_status", {}).get("status") == "a0_a2_only"
            and python_exam_full_rehearsal.get("operator_confirmation_status", {}).get("local_writes_require_confirmation") is True
            and python_exam_full_rehearsal.get("evidence_chain", {}).get("exam_run_packet_receipt_id")
            and python_exam_full_rehearsal.get("evidence_chain", {}).get("exam_packet_timeline_receipt_id")
            and python_exam_full_rehearsal.get("evidence_chain", {}).get("evidence_preview_receipt_id")
            and python_exam_full_rehearsal.get("evidence_chain", {}).get("human_handoff_markdown_hash")
            and python_exam_full_rehearsal.get("dry_run_default") is True
            and python_exam_full_rehearsal.get("local_writes_executed_by_rehearsal_pack") is False
            and python_exam_full_rehearsal.get("raw_query_returned") is False
            and python_exam_full_rehearsal.get("raw_text_returned") is False
            and python_exam_full_rehearsal.get("raw_cell_returned") is False
            and python_exam_full_rehearsal.get("raw_notebook_returned") is False
            and python_exam_full_rehearsal.get("notebook_code_returned") is False
            and python_exam_full_rehearsal.get("local_paths_returned") is False
            and python_exam_full_rehearsal.get("values_returned") is False
            and python_exam_full_rehearsal.get("solutions_returned") is False
            and python_exam_full_rehearsal.get("final_interpretations_returned") is False
            and python_exam_full_rehearsal.get("automatic_grading_started") is False
            and python_exam_full_rehearsal.get("proctoring_started") is False
            and python_exam_full_rehearsal.get("ai_detection_started") is False
            and python_exam_full_rehearsal.get("exam_clearance_claimed") is False
            and python_exam_full_rehearsal.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_full_rehearsal, ensure_ascii=False),
            "python_exam_full_local_rehearsal_pack",
            (
                f"status={python_exam_full_rehearsal_status}, "
                f"result={python_exam_full_rehearsal.get('status')}, "
                f"steps={python_exam_full_rehearsal.get('rehearsal_summary', {}).get('ready_step_count')}/"
                f"{python_exam_full_rehearsal.get('rehearsal_summary', {}).get('step_count')}, "
                f"handoff={python_exam_full_rehearsal.get('rehearsal_summary', {}).get('human_handoff_status')}"
            ),
        )
    )
    locked_final_review_board_summary = python_exam_locked_final_review_board.get(
        "locked_final_review_board_summary",
        {},
    )
    checks.append(
        _check(
            python_exam_locked_final_review_board_status == 200
            and python_exam_locked_final_review_board.get("artifact_type") == "python_exam_locked_final_review_board"
            and python_exam_locked_final_review_board.get("status") == "python_exam_locked_final_review_board_ready"
            and python_exam_locked_final_review_board.get("exam_deployment_status") == "not_cleared"
            and python_exam_locked_final_review_board.get("selected_skill_tag") == "python_lists"
            and python_exam_locked_final_review_board.get("locked_final_review_board_recommendation")
            == "keep_final_board_open"
            and locked_final_review_board_summary.get("locked_final_review_board_recommendation")
            == "keep_final_board_open"
            and locked_final_review_board_summary.get("final_manual_review_action_lock_recommendation")
            == "keep_action_locked"
            and locked_final_review_board_summary.get("final_manual_review_console_recommendation")
            == "keep_final_console_open"
            and locked_final_review_board_summary.get("final_review_ledger_integrity_gate_recommendation")
            == "keep_integrity_gate_open"
            and locked_final_review_board_summary.get("final_review_receipt_ledger_recommendation")
            == "keep_final_ledger_open"
            and locked_final_review_board_summary.get("draft_review_status")
            == "python_exam_draft_package_review_console_ready"
            and locked_final_review_board_summary.get("human_handoff_status")
            == "python_exam_human_handoff_packet_ready"
            and locked_final_review_board_summary.get("full_local_rehearsal_status")
            == "python_exam_full_local_rehearsal_pack_ready"
            and locked_final_review_board_summary.get("integrity_issue_count", 0) >= 1
            and "notebook_checkpoint_hash"
            in (locked_final_review_board_summary.get("missing_required_hashes", []) or [])
            and locked_final_review_board_summary.get("mismatched_hashes") == []
            and locked_final_review_board_summary.get("help_level") == "A2"
            and locked_final_review_board_summary.get("ledger_event_count") == 5
            and locked_final_review_board_summary.get("locked_final_review_board_hash")
            and locked_final_review_board_summary.get("final_manual_review_action_lock_hash")
            and locked_final_review_board_summary.get("final_manual_review_console_hash")
            and locked_final_review_board_summary.get("final_review_ledger_integrity_gate_hash")
            and locked_final_review_board_summary.get("final_review_receipt_ledger_hash")
            and locked_final_review_board_summary.get("human_handoff_markdown_hash")
            and python_exam_locked_final_review_board.get("locked_final_review_board_receipt", {}).get(
                "not_cleared_receipt"
            )
            is True
            and python_exam_locked_final_review_board.get("dry_run_default") is True
            and python_exam_locked_final_review_board.get("export_created") is False
            and python_exam_locked_final_review_board.get("export_authorized") is False
            and python_exam_locked_final_review_board.get("archive_created") is False
            and python_exam_locked_final_review_board.get("submission_started") is False
            and python_exam_locked_final_review_board.get("local_writes_requested") is False
            and python_exam_locked_final_review_board.get("local_execution_started") is False
            and python_exam_locked_final_review_board.get("raw_query_returned") is False
            and python_exam_locked_final_review_board.get("raw_text_returned") is False
            and python_exam_locked_final_review_board.get("raw_cell_returned") is False
            and python_exam_locked_final_review_board.get("raw_notebook_returned") is False
            and python_exam_locked_final_review_board.get("notebook_code_returned") is False
            and python_exam_locked_final_review_board.get("local_paths_returned") is False
            and python_exam_locked_final_review_board.get("values_returned") is False
            and python_exam_locked_final_review_board.get("solutions_returned") is False
            and python_exam_locked_final_review_board.get("final_interpretations_returned") is False
            and python_exam_locked_final_review_board.get("score_returned") is False
            and python_exam_locked_final_review_board.get("percentage_returned") is False
            and python_exam_locked_final_review_board.get("ranking_returned") is False
            and python_exam_locked_final_review_board.get("grade_returned") is False
            and python_exam_locked_final_review_board.get("automatic_grading_started") is False
            and python_exam_locked_final_review_board.get("proctoring_started") is False
            and python_exam_locked_final_review_board.get("ai_detection_started") is False
            and python_exam_locked_final_review_board.get("exam_clearance_claimed") is False
            and python_exam_locked_final_review_board.get("public_safety_status") == "pass"
            and "runner_private_attempt" not in json.dumps(
                python_exam_locked_final_review_board,
                ensure_ascii=False,
            )
            and str(workspace_temp_dir)
            not in json.dumps(python_exam_locked_final_review_board, ensure_ascii=False),
            "python_exam_locked_final_review_board",
            (
                f"status={python_exam_locked_final_review_board_status}, "
                f"result={python_exam_locked_final_review_board.get('status')}, "
                f"skill={python_exam_locked_final_review_board.get('selected_skill_tag')}, "
                f"recommendation={locked_final_review_board_summary.get('locked_final_review_board_recommendation')}, "
                f"issues={locked_final_review_board_summary.get('integrity_issue_count')}, "
                f"archive_created={python_exam_locked_final_review_board.get('archive_created')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_gap_coach_status == 200
            and python_exam_gap_coach.get("artifact_type") == "python_exam_rehearsal_playback_gap_coach"
            and python_exam_gap_coach.get("status") == "python_exam_rehearsal_playback_gap_coach_ready"
            and python_exam_gap_coach.get("exam_deployment_status") == "not_cleared"
            and python_exam_gap_coach.get("selected_skill_tag") == "python_lists"
            and python_exam_gap_coach.get("next_safe_action_key")
            in {
                "ready_to_rehearse_again",
                "resolve_missing_artifact",
                "resolve_source_gap",
                "review_operator_confirmation",
                "continue_a0_a2_drill",
                "ready_for_human_review_packet",
            }
            and python_exam_gap_coach.get("next_safe_action_key") == "review_operator_confirmation"
            and python_exam_gap_coach.get("gap_profile", {}).get("operator_confirmation_gap") is True
            and python_exam_gap_coach.get("source_anchor_metadata", {}).get("source_anchor_count", 0) >= 1
            and python_exam_gap_coach.get("a0_a2_help_status", {}).get("status") == "a0_a2_only"
            and python_exam_gap_coach.get("notebook_checkpoint_metadata", {}).get("checkpoint_hash_count", 0) >= 1
            and python_exam_gap_coach.get("operator_confirmation_status", {}).get("local_writes_require_confirmation") is True
            and python_exam_gap_coach.get("evidence_playback", {}).get("evidence_preview_receipt_id")
            and python_exam_gap_coach.get("evidence_playback", {}).get("human_handoff_markdown_hash")
            and python_exam_gap_coach.get("playback_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_gap_coach.get("dry_run_default") is True
            and python_exam_gap_coach.get("local_writes_executed_by_gap_coach") is False
            and python_exam_gap_coach.get("raw_query_returned") is False
            and python_exam_gap_coach.get("raw_text_returned") is False
            and python_exam_gap_coach.get("raw_cell_returned") is False
            and python_exam_gap_coach.get("raw_notebook_returned") is False
            and python_exam_gap_coach.get("notebook_code_returned") is False
            and python_exam_gap_coach.get("local_paths_returned") is False
            and python_exam_gap_coach.get("values_returned") is False
            and python_exam_gap_coach.get("solutions_returned") is False
            and python_exam_gap_coach.get("final_interpretations_returned") is False
            and python_exam_gap_coach.get("score_returned") is False
            and python_exam_gap_coach.get("percentage_returned") is False
            and python_exam_gap_coach.get("ranking_returned") is False
            and python_exam_gap_coach.get("grade_returned") is False
            and python_exam_gap_coach.get("automatic_grading_started") is False
            and python_exam_gap_coach.get("proctoring_started") is False
            and python_exam_gap_coach.get("ai_detection_started") is False
            and python_exam_gap_coach.get("exam_clearance_claimed") is False
            and python_exam_gap_coach.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_gap_coach, ensure_ascii=False),
            "python_exam_rehearsal_playback_gap_coach",
            (
                f"status={python_exam_gap_coach_status}, "
                f"result={python_exam_gap_coach.get('status')}, "
                f"action={python_exam_gap_coach.get('next_safe_action_key')}, "
                f"checkpoint={python_exam_gap_coach.get('notebook_checkpoint_metadata', {}).get('checkpoint_hash_count')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_guided_loop_status == 200
            and python_exam_guided_loop.get("artifact_type") == "python_exam_gap_coach_guided_rehearsal_loop"
            and python_exam_guided_loop.get("status") == "python_exam_gap_coach_guided_rehearsal_loop_ready"
            and python_exam_guided_loop.get("exam_deployment_status") == "not_cleared"
            and python_exam_guided_loop.get("selected_skill_tag") == "python_lists"
            and python_exam_guided_loop.get("requested_action_key") == "review_operator_confirmation"
            and python_exam_guided_loop.get("guided_loop_summary", {}).get("route") == "operator_confirmation_review"
            and python_exam_guided_loop.get("guided_step", {}).get("endpoint")
            == "/api/unibot/course/python-exam-local-cycle-operator-workspace-card"
            and python_exam_guided_loop.get("safe_prefill", {}).get("prefill_hash")
            and len(python_exam_guided_loop.get("operator_confirmation_review_cards", []) or []) >= 1
            and python_exam_guided_loop.get("guided_loop_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_guided_loop.get("dry_run_default") is True
            and python_exam_guided_loop.get("local_writes_requested") is False
            and python_exam_guided_loop.get("local_execution_started") is False
            and python_exam_guided_loop.get("raw_query_returned") is False
            and python_exam_guided_loop.get("raw_text_returned") is False
            and python_exam_guided_loop.get("raw_cell_returned") is False
            and python_exam_guided_loop.get("raw_notebook_returned") is False
            and python_exam_guided_loop.get("notebook_code_returned") is False
            and python_exam_guided_loop.get("local_paths_returned") is False
            and python_exam_guided_loop.get("values_returned") is False
            and python_exam_guided_loop.get("solutions_returned") is False
            and python_exam_guided_loop.get("final_interpretations_returned") is False
            and python_exam_guided_loop.get("score_returned") is False
            and python_exam_guided_loop.get("percentage_returned") is False
            and python_exam_guided_loop.get("ranking_returned") is False
            and python_exam_guided_loop.get("grade_returned") is False
            and python_exam_guided_loop.get("automatic_grading_started") is False
            and python_exam_guided_loop.get("proctoring_started") is False
            and python_exam_guided_loop.get("ai_detection_started") is False
            and python_exam_guided_loop.get("exam_clearance_claimed") is False
            and python_exam_guided_loop.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_guided_loop, ensure_ascii=False),
            "python_exam_gap_coach_guided_rehearsal_loop",
            (
                f"status={python_exam_guided_loop_status}, "
                f"result={python_exam_guided_loop.get('status')}, "
                f"action={python_exam_guided_loop.get('requested_action_key')}, "
                f"route={python_exam_guided_loop.get('guided_loop_summary', {}).get('route')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_loop_surface_status == 200
            and python_exam_loop_surface.get("artifact_type") == "python_exam_guided_loop_control_surface"
            and python_exam_loop_surface.get("status") == "python_exam_guided_loop_control_surface_ready"
            and python_exam_loop_surface.get("exam_deployment_status") == "not_cleared"
            and python_exam_loop_surface.get("selected_skill_tag") == "python_lists"
            and python_exam_loop_surface.get("control_summary", {}).get("action_key") == "review_operator_confirmation"
            and python_exam_loop_surface.get("control_summary", {}).get("next_safe_click")
            == "review_operator_confirmation_cards"
            and python_exam_loop_surface.get("current_guided_step_card", {}).get("prefill_hash")
            and python_exam_loop_surface.get("source_anchor_status", {}).get("source_anchor_count", 0) >= 1
            and python_exam_loop_surface.get("notebook_checkpoint_status", {}).get("checkpoint_hash_count", 0) >= 1
            and python_exam_loop_surface.get("operator_confirmation_status", {}).get("open_operator_confirmation_count", 0) >= 1
            and python_exam_loop_surface.get("a0_a2_help_status", {}).get("allowed_help_boundary") == "A0-A2"
            and python_exam_loop_surface.get("evidence_status", {}).get("evidence_preview_receipt_id")
            and python_exam_loop_surface.get("surface_receipt", {}).get("not_cleared_receipt") is True
            and python_exam_loop_surface.get("dry_run_default") is True
            and python_exam_loop_surface.get("dry_run_request_prepared") is True
            and python_exam_loop_surface.get("dry_run_request_executed_by_surface") is False
            and python_exam_loop_surface.get("local_writes_requested") is False
            and python_exam_loop_surface.get("local_execution_started") is False
            and python_exam_loop_surface.get("raw_query_returned") is False
            and python_exam_loop_surface.get("raw_text_returned") is False
            and python_exam_loop_surface.get("raw_cell_returned") is False
            and python_exam_loop_surface.get("raw_notebook_returned") is False
            and python_exam_loop_surface.get("notebook_code_returned") is False
            and python_exam_loop_surface.get("local_paths_returned") is False
            and python_exam_loop_surface.get("values_returned") is False
            and python_exam_loop_surface.get("solutions_returned") is False
            and python_exam_loop_surface.get("final_interpretations_returned") is False
            and python_exam_loop_surface.get("score_returned") is False
            and python_exam_loop_surface.get("percentage_returned") is False
            and python_exam_loop_surface.get("ranking_returned") is False
            and python_exam_loop_surface.get("grade_returned") is False
            and python_exam_loop_surface.get("automatic_grading_started") is False
            and python_exam_loop_surface.get("proctoring_started") is False
            and python_exam_loop_surface.get("ai_detection_started") is False
            and python_exam_loop_surface.get("exam_clearance_claimed") is False
            and python_exam_loop_surface.get("public_safety_status") == "pass"
            and str(workspace_temp_dir) not in json.dumps(python_exam_loop_surface, ensure_ascii=False),
            "python_exam_guided_loop_control_surface",
            (
                f"status={python_exam_loop_surface_status}, "
                f"result={python_exam_loop_surface.get('status')}, "
                f"click={python_exam_loop_surface.get('control_summary', {}).get('next_safe_click')}, "
                f"route={python_exam_loop_surface.get('control_summary', {}).get('route')}"
            ),
        )
    )
    checks.append(
        _check(
            python_exam_locked_final_review_gap_resolver_status == 200
            and python_exam_locked_final_review_gap_resolver.get("artifact_type")
            == "python_exam_locked_final_review_gap_resolver"
            and python_exam_locked_final_review_gap_resolver.get("status")
            == "python_exam_locked_final_review_gap_resolver_ready"
            and python_exam_locked_final_review_gap_resolver.get("exam_deployment_status") == "not_cleared"
            and python_exam_locked_final_review_gap_resolver.get("selected_skill_tag") == "python_lists"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_recommendation"
            )
            == "keep_gap_resolver_open"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("locked_final_review_gap_resolver_recommendation")
            == "keep_gap_resolver_open"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("locked_final_review_board_recommendation")
            == "keep_final_board_open"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("final_manual_review_action_lock_recommendation")
            == "keep_action_locked"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("full_local_rehearsal_status")
            == "python_exam_full_local_rehearsal_pack_ready"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("gap_coach_status")
            == "python_exam_rehearsal_playback_gap_coach_ready"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("guided_loop_control_status")
            == "python_exam_guided_loop_control_surface_ready"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("gap_coach_next_safe_action_key")
            == "review_operator_confirmation"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("affected_review_layer")
            == "notebook_checkpoint_hash"
            and python_exam_locked_final_review_gap_resolver.get("prioritized_repair_card", {}).get("repair_action")
            == "review_notebook_checkpoint_hash_chain"
            and "notebook_checkpoint_hash"
            in python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("missing_required_hashes", [])
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("mismatched_hashes")
            == []
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("help_level")
            == "A2"
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("ledger_event_count")
            == 5
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("locked_final_review_gap_resolver_hash")
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("locked_final_review_board_hash")
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_summary", {}
            ).get("final_manual_review_action_lock_hash")
            and python_exam_locked_final_review_gap_resolver.get(
                "locked_final_review_gap_resolver_receipt", {}
            ).get("not_cleared_receipt")
            is True
            and python_exam_locked_final_review_gap_resolver.get("dry_run_default") is True
            and python_exam_locked_final_review_gap_resolver.get("export_created") is False
            and python_exam_locked_final_review_gap_resolver.get("archive_created") is False
            and python_exam_locked_final_review_gap_resolver.get("submission_started") is False
            and python_exam_locked_final_review_gap_resolver.get("local_writes_requested") is False
            and python_exam_locked_final_review_gap_resolver.get("local_execution_started") is False
            and python_exam_locked_final_review_gap_resolver.get("raw_query_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("raw_text_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("raw_cell_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("raw_notebook_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("notebook_code_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("local_paths_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("values_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("solutions_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("final_interpretations_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("score_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("percentage_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("ranking_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("grade_returned") is False
            and python_exam_locked_final_review_gap_resolver.get("automatic_grading_started") is False
            and python_exam_locked_final_review_gap_resolver.get("proctoring_started") is False
            and python_exam_locked_final_review_gap_resolver.get("ai_detection_started") is False
            and python_exam_locked_final_review_gap_resolver.get("exam_clearance_claimed") is False
            and python_exam_locked_final_review_gap_resolver.get("public_safety_status") == "pass"
            and str(workspace_temp_dir)
            not in json.dumps(python_exam_locked_final_review_gap_resolver, ensure_ascii=False),
            "python_exam_locked_final_review_gap_resolver",
            (
                f"status={python_exam_locked_final_review_gap_resolver_status}, "
                f"result={python_exam_locked_final_review_gap_resolver.get('status')}, "
                f"skill={python_exam_locked_final_review_gap_resolver.get('selected_skill_tag')}, "
                f"recommendation={python_exam_locked_final_review_gap_resolver.get('locked_final_review_gap_resolver_recommendation')}, "
                f"layer={python_exam_locked_final_review_gap_resolver.get('locked_final_review_gap_resolver_summary', {}).get('affected_review_layer')}, "
                f"archive_created={python_exam_locked_final_review_gap_resolver.get('archive_created')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as video_run_temp_dir:
        video_run_root = Path(video_run_temp_dir) / "materials"
        video_output_dir = Path(video_run_temp_dir) / "private"
        video_receipt_journal = Path(video_run_temp_dir) / "video_receipts.jsonl"
        write_video_transcription_smoke_fixture(video_run_root)
        video_run_status, video_run = route_request(
            "/api/unibot/course/video-transcription/run-batch",
            payload={
                "base_path": str(video_run_root),
                "decision_record": operator_decision,
                "receipt_journal_path": str(video_receipt_journal),
                "private_output_dir": str(video_output_dir),
                "max_jobs": 2,
            },
        )
    checks.append(
        _check(
            video_run_status == 200
            and video_run.get("artifact_type") == "course_video_transcription_run"
            and video_run.get("status") == "sidecar_transcripts_ready_for_human_review"
            and video_run.get("public_safety_status") == "pass"
            and video_run.get("counts", {}).get("transcribed_private_count") == 1
            and video_run.get("counts", {}).get("stored_receipt_count") == 1
            and video_run.get("raw_text_returned") is False
            and video_run.get("local_paths_returned") is False,
            "video_transcription_run_batch",
            (
                f"status={video_run_status}, result={video_run.get('status')}, "
                f"transcribed={video_run.get('counts', {}).get('transcribed_private_count')}, "
                f"stored={video_run.get('counts', {}).get('stored_receipt_count')}"
            ),
        )
    )

    extraction_receipt_payload = {
        "job_id": "smoke-job",
        "material_id": "smoke-material",
        "job_type": "ocr",
        "extraction_status": "extracted_private",
        "raw_text_sha256": "b" * 64,
        "extracted_text_char_count": 420,
        "private_artifact_reference": "synthetic private extraction artifact ref",
        "human_review_status": "pending_review",
        "decision_reference_hash": operator_packet.get("decision_validation", {}).get("rights_decision_reference_hash"),
    }
    receipt_status, receipt_validation = route_request(
        "/api/unibot/course/extraction-receipt/validate",
        payload={
            "decision_record": operator_decision,
            "receipt": extraction_receipt_payload,
        },
    )
    checks.append(
        _check(
            receipt_status == 200
            and receipt_validation.get("status") == "ok_private_extraction_receipt"
            and receipt_validation.get("ready_for_human_review_queue") is True
            and receipt_validation.get("public_safety_status") == "pass"
            and receipt_validation.get("raw_text_stored_in_receipt") is False,
            "course_extraction_receipt_validation",
            (
                f"status={receipt_status}, result={receipt_validation.get('status')}, "
                f"issues={receipt_validation.get('issues')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as receipt_temp_dir:
        receipt_journal_path = str(Path(receipt_temp_dir) / "extraction_receipts.jsonl")
        receipt_append_status, receipt_append = route_request(
            "/api/unibot/course/extraction-receipts/append",
            payload={
                "decision_record": operator_decision,
                "receipt": extraction_receipt_payload,
                "receipt_journal_path": receipt_journal_path,
            },
        )
        receipt_summary_status, receipt_summary = route_request(
            "/api/unibot/course/extraction-receipts/summary",
            payload={"receipt_journal_path": receipt_journal_path},
        )
        journal_progress_status, journal_progress = route_request(
            "/api/unibot/course/extraction-progress-report",
            payload={
                "decision_record": operator_decision,
                "receipt_journal_path": receipt_journal_path,
            },
        )
    checks.append(
        _check(
            receipt_append_status == 200
            and receipt_append.get("status") == "stored"
            and receipt_summary_status == 200
            and receipt_summary.get("artifact_type") == "course_extraction_receipt_journal_summary"
            and receipt_summary.get("public_safety_status") == "pass"
            and receipt_summary.get("progress_receipt_count") == 1
            and journal_progress_status == 200
            and journal_progress.get("receipt_summary", {}).get("ready_for_human_review_count") == 1,
            "course_extraction_receipt_journal",
            (
                f"append={receipt_append.get('status')}, records={receipt_summary.get('record_count')}, "
                f"progress={receipt_summary.get('progress_receipt_count')}, "
                f"review={journal_progress.get('receipt_summary', {}).get('ready_for_human_review_count')}"
            ),
        )
    )

    extraction_deferral_record = {
        "deferral_scope": "course_material_extraction",
        "decision_status": "approved_deferral",
        "deferred_job_types": ["ocr", "transcription"],
        "deferral_reason": "synthetic smoke deferral for current public draft scope",
        "reviewer_roles": ["Datenschutz", "Lehreinheit / Modulverantwortliche", "IT / SZI"],
        "decision_reference": "synthetic extraction deferral smoke fixture",
        "human_review_before_future_tutor_use": True,
        "raw_text_public_release_allowed": False,
        "exam_deployment_status": "not_cleared",
    }
    deferral_status, deferral = route_request(
        "/api/unibot/course/extraction-deferral/validate",
        payload={"deferral_record": extraction_deferral_record},
    )
    with tempfile.TemporaryDirectory() as completion_temp_dir:
        completion_fixture_root = Path(completion_temp_dir)
        (completion_fixture_root / "Week 1").mkdir(parents=True)
        (completion_fixture_root / "Videos").mkdir(parents=True)
        (completion_fixture_root / "Week 1" / "lecture.pdf").write_bytes(b"%PDF-1.4\nfixture")
        (completion_fixture_root / "Videos" / "lecture.mov").write_bytes(b"video")
        completion_status, completion_report = route_request(
            "/api/unibot/course/extraction-completion-report",
            payload={
                "base_path": str(completion_fixture_root),
                "decision_record": operator_decision,
                "deferral_record": extraction_deferral_record,
            },
        )
    checks.append(
        _check(
            deferral_status == 200
            and deferral.get("status") == "ok_extraction_deferral_record"
            and deferral.get("public_safety_status") == "pass"
            and deferral.get("raw_decision_reference_stored") is False
            and completion_status == 200
            and completion_report.get("artifact_type") == "course_extraction_completion_report"
            and completion_report.get("status") == "complete_intentionally_deferred"
            and completion_report.get("exam_deployment_status") == "not_cleared"
            and completion_report.get("public_safety_status") == "pass",
            "course_extraction_completion_report",
            (
                f"deferral={deferral.get('status')}, completion={completion_report.get('status')}, "
                f"deferred={completion_report.get('job_summary', {}).get('deferred_job_count')}, "
                f"missing={completion_report.get('job_summary', {}).get('missing_job_count')}"
            ),
        )
    )

    progress_status, progress = route_request(
        "/api/unibot/course/extraction-progress-report",
        payload={
            "decision_record": operator_decision,
            "receipts": [extraction_receipt_payload],
        },
    )
    checks.append(
        _check(
            progress_status == 200
            and progress.get("artifact_type") == "course_extraction_progress_report"
            and progress.get("exam_deployment_status") == "not_cleared"
            and progress.get("public_safety_status") == "pass"
            and progress.get("receipt_summary", {}).get("ready_for_human_review_count") == 1,
            "course_extraction_progress_report",
            (
                f"status={progress_status}, result={progress.get('status')}, "
                f"receipts={progress.get('receipt_summary', {}).get('receipt_count')}, "
                f"review={progress.get('receipt_summary', {}).get('ready_for_human_review_count')}"
            ),
        )
    )

    batch_plan_status, batch_plan = route_request(
        "/api/unibot/course/extraction-batch-plan",
        payload={"decision_record": operator_decision, "batch_size": 12},
    )
    checks.append(
        _check(
            batch_plan_status == 200
            and batch_plan.get("artifact_type") == "course_extraction_batch_plan"
            and batch_plan.get("exam_deployment_status") == "not_cleared"
            and batch_plan.get("public_safety_status") == "pass"
            and "receipt_backlog" in batch_plan,
            "course_extraction_batch_plan",
            (
                f"status={batch_plan_status}, result={batch_plan.get('status')}, "
                f"jobs={batch_plan.get('coverage', {}).get('job_count')}, "
                f"batches={batch_plan.get('coverage', {}).get('batch_count')}"
            ),
        )
    )

    batch_plan_ocr_status, batch_plan_ocr = route_request(
        "/api/unibot/course/extraction-batch-plan",
        payload={"decision_record": operator_decision, "batch_size": 12, "job_types": ["ocr"]},
    )
    checks.append(
        _check(
            batch_plan_ocr_status == 200
            and batch_plan_ocr.get("artifact_type") == "course_extraction_batch_plan"
            and batch_plan_ocr.get("public_safety_status") == "pass"
            and batch_plan_ocr.get("coverage", {}).get("job_type_filter") == ["ocr"]
            and batch_plan_ocr.get("coverage", {}).get("transcription_job_count") == 0,
            "course_extraction_batch_plan_ocr_filter",
            (
                f"status={batch_plan_ocr_status}, filter={batch_plan_ocr.get('coverage', {}).get('job_type_filter')}, "
                f"ocr={batch_plan_ocr.get('coverage', {}).get('ocr_job_count')}, "
                f"transcription={batch_plan_ocr.get('coverage', {}).get('transcription_job_count')}"
            ),
        )
    )

    batch_receipt_status, batch_receipt = route_request(
        "/api/unibot/course/extraction-batch-receipt-packet",
        payload={"decision_record": operator_decision, "batch_size": 12, "batch_index": 1},
    )
    checks.append(
        _check(
            batch_receipt_status == 200
            and batch_receipt.get("artifact_type") == "course_extraction_batch_receipt_packet"
            and batch_receipt.get("exam_deployment_status") == "not_cleared"
            and batch_receipt.get("public_safety_status") == "pass"
            and "receipt_contract" in batch_receipt,
            "course_extraction_batch_receipt_packet",
            (
                f"status={batch_receipt_status}, result={batch_receipt.get('status')}, "
                f"batch={batch_receipt.get('selected_batch', {}).get('batch_index')}, "
                f"templates={len(batch_receipt.get('receipt_templates', []))}"
            ),
        )
    )

    manifest_update_status, manifest_update = route_request(
        "/api/unibot/course/extraction-manifest-update-plan",
        payload={
            "decision_record": operator_decision,
            "receipts": [
                {
                    "job_id": "smoke-job",
                    "material_id": "smoke-material",
                    "job_type": "ocr",
                    "extraction_status": "extracted_private",
                    "raw_text_sha256": "b" * 64,
                    "extracted_text_char_count": 420,
                    "private_artifact_reference": "synthetic private extraction artifact ref",
                    "human_review_status": "reviewed_for_private_tutor",
                    "decision_reference_hash": operator_packet.get("decision_validation", {}).get("rights_decision_reference_hash"),
                }
            ],
        },
    )
    checks.append(
        _check(
            manifest_update_status == 200
            and manifest_update.get("artifact_type") == "course_extraction_manifest_update_plan"
            and manifest_update.get("exam_deployment_status") == "not_cleared"
            and manifest_update.get("public_safety_status") == "pass"
            and manifest_update.get("candidate_summary", {}).get("ready_to_apply_private_count") == 1,
            "course_extraction_manifest_update_plan",
            (
                f"status={manifest_update_status}, result={manifest_update.get('status')}, "
                f"candidates={manifest_update.get('candidate_summary', {}).get('candidate_count')}, "
                f"ready={manifest_update.get('candidate_summary', {}).get('ready_to_apply_private_count')}"
            ),
        )
    )

    coverage_status, coverage = route_request(
        "/api/unibot/course/tutor-coverage-plan",
        payload={
            "decision_record": operator_decision,
            "receipts": [
                {
                    "job_id": "smoke-job",
                    "material_id": "smoke-material",
                    "job_type": "ocr",
                    "extraction_status": "extracted_private",
                    "raw_text_sha256": "b" * 64,
                    "extracted_text_char_count": 420,
                    "private_artifact_reference": "synthetic private extraction artifact ref",
                    "human_review_status": "reviewed_for_private_tutor",
                    "decision_reference_hash": operator_packet.get("decision_validation", {}).get("rights_decision_reference_hash"),
                }
            ],
        },
    )
    checks.append(
        _check(
            coverage_status == 200
            and coverage.get("artifact_type") == "course_tutor_coverage_plan"
            and coverage.get("exam_deployment_status") == "not_cleared"
            and coverage.get("public_safety_status") == "pass"
            and "skill_coverage" in coverage,
            "course_tutor_coverage_plan",
            (
                f"status={coverage_status}, result={coverage.get('status')}, "
                f"current={coverage.get('current_scope_summary', {}).get('ready_skill_count')}, "
                f"projected={coverage.get('projected_scope_summary', {}).get('ready_skill_count')}, "
                f"candidates={coverage.get('projected_scope_summary', {}).get('candidate_material_count')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as study_temp_dir:
        study_fixture_root = Path(study_temp_dir)
        (study_fixture_root / "Week 1").mkdir(parents=True)
        (study_fixture_root / "Week 1" / "pandas_intro.md").write_text(
            "pandas DataFrame read_csv columns dtypes debugging boxplot",
            encoding="utf-8",
        )
        study_status, study = route_request(
            "/api/unibot/course/study-session-plan",
            payload={
                "base_path": str(study_fixture_root),
                "review_policy": "local_private_tutor",
                "focus_query": "pandas boxplot debugging",
                "max_items": 3,
            },
        )
        study_task = (study.get("tasks") or [{"task_id": "smoke-study-task", "skill_tag": "pandas"}])[0]
        study_receipt_payload = {
            "task_id": study_task.get("task_id", "smoke-study-task"),
            "skill_tag": study_task.get("skill_tag", "pandas"),
            "help_level": "A2",
            "source_anchor_id": "smoke-course-anchor",
            "prediction": "Ich pruefe zuerst die erwartete Spalte und den Datentyp.",
            "retrieval_response": "Aus dem Kopf: pandas-Fehler beginnen oft bei Spaltennamen oder dtypes.",
            "notebook_action": "Ich fuehre nur df.head und df.dtypes als Diagnose aus.",
            "reflection": "Mein Beitrag war Vorhersage, Quellenanker und kleinster Diagnose-Schritt.",
        }
        study_receipt_status, study_receipt = route_request(
            "/api/unibot/course/study-session-receipt/validate",
            payload={
                "receipt": study_receipt_payload,
                "expected_task_ids": [study_task.get("task_id", "smoke-study-task")],
            },
        )
        study_review_status, study_review = route_request(
            "/api/unibot/course/study-session-review-report",
            payload={
                "base_path": str(study_fixture_root),
                "review_policy": "local_private_tutor",
                "focus_query": "pandas boxplot debugging",
                "max_items": 1,
                "study_receipts": [study_receipt_payload],
            },
        )
    checks.append(
        _check(
            study_status == 200
            and study.get("artifact_type") == "course_study_session_plan"
            and study.get("exam_deployment_status") == "not_cleared"
            and study.get("public_safety_status") == "pass"
            and "session_contract" in study,
            "course_study_session_plan",
            (
                f"status={study_status}, result={study.get('status')}, "
                f"tasks={study.get('task_count')}, ready={study.get('ready_task_count')}"
            ),
        )
    )
    checks.append(
        _check(
            study_receipt_status == 200
            and study_receipt.get("artifact_type") == "course_study_session_receipt_validation"
            and study_receipt.get("status") == "ok_study_session_receipt"
            and study_receipt.get("exam_deployment_status") == "not_cleared"
            and study_receipt.get("public_safety_status") == "pass"
            and study_receipt.get("raw_text_stored") is False,
            "course_study_session_receipt_validation",
            (
                f"status={study_receipt_status}, result={study_receipt.get('status')}, "
                f"raw_text={study_receipt.get('raw_text_stored')}, issues={study_receipt.get('issues')}"
            ),
        )
    )
    checks.append(
        _check(
            study_review_status == 200
            and study_review.get("artifact_type") == "course_study_session_review_report"
            and study_review.get("exam_deployment_status") == "not_cleared"
            and study_review.get("public_safety_status") == "pass"
            and study_review.get("receipt_summary", {}).get("valid_receipt_count") == 1
            and "percentage" in study_review.get("review_policy", {}).get("eigenleistung_claim", ""),
            "course_study_session_review_report",
            (
                f"status={study_review_status}, result={study_review.get('status')}, "
                f"valid={study_review.get('receipt_summary', {}).get('valid_receipt_count')}, "
                f"missing={study_review.get('receipt_summary', {}).get('missing_planned_receipt_count')}"
            ),
        )
    )

    clearance_board_status, clearance_board = route_request("/api/unibot/institutional-clearance/board", payload={})
    checks.append(
        _check(
            clearance_board_status == 200
            and clearance_board.get("artifact_type") == "unibot_institutional_clearance_board"
            and clearance_board.get("exam_deployment_status") == "not_cleared"
            and clearance_board.get("public_safety_status") == "pass"
            and len(clearance_board.get("scope_lanes", [])) >= 4,
            "institutional_clearance_board",
            (
                f"status={clearance_board_status}, result={clearance_board.get('status')}, "
                f"scopes={len(clearance_board.get('scope_lanes', []))}, exam={clearance_board.get('exam_deployment_status')}"
            ),
        )
    )

    exam_clearance_record = {
        "clearance_scope": "exam_controlled_gateway",
        "decision_status": "approved",
        "reviewer_roles": [
            "Pruefungsamt",
            "Datenschutz",
            "IT / SZI",
            "Lehreinheit / Modulverantwortliche",
            "Inklusionsbuero / Nachteilsausgleich",
        ],
        "decision_reference": "synthetic exam gateway clearance fixture",
        "allowed_modes": ["exam_controlled_gateway", "controlled_notebook"],
        "help_levels_allowed": ["A0", "A1", "A2"],
        "no_proctoring": True,
        "no_ai_detection": True,
        "no_automatic_grading": True,
        "human_review_required": True,
        "raw_text_public_release_allowed": False,
    }
    clearance_validation_status, clearance_validation = route_request(
        "/api/unibot/institutional-clearance/validate",
        payload={"record": exam_clearance_record},
    )
    checks.append(
        _check(
            clearance_validation_status == 200
            and clearance_validation.get("status") == "ok_exam_controlled_gateway_clearance_record"
            and clearance_validation.get("cleared_scope_by_record") is True
            and clearance_validation.get("exam_deployment_status") == "not_cleared"
            and clearance_validation.get("public_safety_status") == "pass"
            and clearance_validation.get("raw_decision_reference_stored") is False,
            "institutional_clearance_validation",
            (
                f"status={clearance_validation_status}, result={clearance_validation.get('status')}, "
                f"issues={clearance_validation.get('issues')}, exam={clearance_validation.get('exam_deployment_status')}"
            ),
        )
    )

    submission_status, submission = route_request("/api/unibot/stakeholder/submission-bundle", payload={})
    lane_ids = {lane.get("lane_id") for lane in submission.get("decision_lanes", [])} if isinstance(submission, dict) else set()
    checks.append(
        _check(
            submission_status == 200
            and submission.get("artifact_type") == "unibot_stakeholder_submission_bundle"
            and submission.get("status") == "ready_for_human_submission_not_sent"
            and submission.get("exam_deployment_status") == "not_cleared"
            and submission.get("public_safety_status") == "pass"
            and {"rights_privacy_local_extraction", "exam_gateway_authority_clearance"}.issubset(lane_ids),
            "stakeholder_submission_bundle",
            (
                f"status={submission_status}, result={submission.get('status')}, "
                f"lanes={len(submission.get('decision_lanes', []))}, exam={submission.get('exam_deployment_status')}"
            ),
        )
    )

    decision_request_status, decision_request = route_request(
        "/api/unibot/stakeholder/decision-request",
        payload={"lane_id": "rights_privacy_local_extraction"},
    )
    checks.append(
        _check(
            decision_request_status == 200
            and decision_request.get("artifact_type") == "unibot_stakeholder_decision_request"
            and decision_request.get("status") == "ready_for_manual_review_not_sent"
            and decision_request.get("lane_id") == "rights_privacy_local_extraction"
            and decision_request.get("exam_deployment_status") == "not_cleared"
            and decision_request.get("public_safety_status") == "pass"
            and decision_request.get("receipt_template", {}).get("tool_sent_message") is False,
            "stakeholder_decision_request",
            (
                f"status={decision_request_status}, result={decision_request.get('status')}, "
                f"lane={decision_request.get('lane_id')}, receipt={decision_request.get('receipt_template', {}).get('manual_submission_status')}"
            ),
        )
    )

    decision_request_markdown_status, decision_request_markdown = route_request(
        "/api/unibot/stakeholder/decision-request-markdown",
        payload={"lane_id": "rights_privacy_local_extraction"},
    )
    checks.append(
        _check(
            decision_request_markdown_status == 200
            and decision_request_markdown.get("status") == "ok"
            and "# UniBot Stakeholder Decision Request" in decision_request_markdown.get("markdown", "")
            and "Exam deployment: `not_cleared`" in decision_request_markdown.get("markdown", "")
            and "Manual Receipt Template" in decision_request_markdown.get("markdown", ""),
            "stakeholder_decision_request_markdown",
            (
                f"status={decision_request_markdown_status}, result={decision_request_markdown.get('status')}, "
                f"chars={len(decision_request_markdown.get('markdown', ''))}"
            ),
        )
    )

    receipt = dict(decision_request.get("receipt_template", {}))
    receipt.update(
        {
            "manual_submission_status": "sent_for_human_review",
            "channel": "synthetic manual review channel",
            "submission_reference": "synthetic manual decision request receipt fixture",
        }
    )
    request_receipt_status, request_receipt = route_request(
        "/api/unibot/stakeholder/decision-request/validate-receipt",
        payload={"receipt": receipt},
    )
    checks.append(
        _check(
            request_receipt_status == 200
            and request_receipt.get("artifact_type") == "unibot_stakeholder_decision_request_receipt_validation"
            and request_receipt.get("status") == "ok_manual_request_receipt"
            and request_receipt.get("public_safety_status") == "pass"
            and request_receipt.get("raw_submission_reference_stored") is False,
            "stakeholder_decision_request_receipt",
            (
                f"status={request_receipt_status}, result={request_receipt.get('status')}, "
                f"lane={request_receipt.get('lane_id')}, issues={request_receipt.get('issues')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        journal_path = str(Path(temp_dir) / "decision_journal.jsonl")
        journal_prepared_status, journal_prepared = route_request(
            "/api/unibot/stakeholder/decision-journal/append-prepared-request",
            payload={
                "lane_id": "rights_privacy_local_extraction",
                "markdown": decision_request_markdown.get("markdown", ""),
                "journal_path": journal_path,
            },
        )
        journal_receipt_status, journal_receipt = route_request(
            "/api/unibot/stakeholder/decision-journal/append",
            payload={
                "journal_path": journal_path,
                "event": {
                    "event_type": "decision_request_receipt_validated",
                    "receipt": receipt,
                },
            },
        )
        journal_summary_status, journal_summary = route_request(
            "/api/unibot/stakeholder/decision-journal/summary",
            payload={"journal_path": journal_path},
        )
    checks.append(
        _check(
            journal_prepared_status == 200
            and journal_prepared.get("status") == "stored"
            and journal_receipt_status == 200
            and journal_receipt.get("status") == "stored"
            and journal_summary_status == 200
            and journal_summary.get("event_count") == 2
            and journal_summary.get("sent_receipt_count") == 1
            and "do not authorize" in journal_summary.get("gate_policy", ""),
            "stakeholder_decision_journal",
            (
                f"prepared={journal_prepared.get('status')}, receipt={journal_receipt.get('status')}, "
                f"events={journal_summary.get('event_count')}, sent={journal_summary.get('sent_receipt_count')}"
            ),
        )
    )

    decision_state_status, decision_state = route_request(
        "/api/unibot/stakeholder/decision-state",
        payload={
            "extraction_decision_record": operator_decision,
            "exam_clearance_record": exam_clearance_record,
            "deployment_go_reference": "synthetic manual deployment go fixture",
        },
    )
    checks.append(
        _check(
            decision_state_status == 200
            and decision_state.get("artifact_type") == "unibot_external_decision_state"
            and decision_state.get("status") == "external_decisions_validated_for_next_gates"
            and decision_state.get("exam_deployment_status") == "not_cleared"
            and decision_state.get("public_safety_status") == "pass"
            and decision_state.get("gate_summary", {}).get("local_extraction_can_start") is True
            and decision_state.get("gate_summary", {}).get("exam_clearance_record_valid") is True,
            "external_decision_state",
            (
                f"status={decision_state_status}, result={decision_state.get('status')}, "
                f"exam={decision_state.get('exam_deployment_status')}, "
                f"deployment_go={decision_state.get('gate_summary', {}).get('manual_deployment_go_recorded')}"
            ),
        )
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        decision_record_journal_path = str(Path(temp_dir) / "decision_records.jsonl")
        decision_record_exam_status, decision_record_exam = route_request(
            "/api/unibot/stakeholder/decision-record-journal/append",
            payload={
                "record_type": "exam_clearance",
                "record": exam_clearance_record,
                "decision_record_journal_path": decision_record_journal_path,
            },
        )
        decision_record_deferral_status, decision_record_deferral = route_request(
            "/api/unibot/stakeholder/decision-record-journal/append",
            payload={
                "record_type": "extraction_deferral",
                "record": extraction_deferral_record,
                "decision_record_journal_path": decision_record_journal_path,
            },
        )
        decision_record_summary_status, decision_record_summary = route_request(
            "/api/unibot/stakeholder/decision-record-journal/summary",
            payload={"decision_record_journal_path": decision_record_journal_path},
        )
        decision_record_completion_status, decision_record_completion = route_request(
            "/api/unibot/completion-audit",
            payload={"decision_record_journal_path": decision_record_journal_path},
        )
    checks.append(
        _check(
            decision_record_exam_status == 200
            and decision_record_exam.get("status") == "stored"
            and decision_record_deferral_status == 200
            and decision_record_deferral.get("status") == "stored"
            and decision_record_summary_status == 200
            and decision_record_summary.get("accepted_record_count") == 2
            and decision_record_summary.get("gate_summary", {}).get("exam_clearance_record_valid") is True
            and decision_record_summary.get("gate_summary", {}).get("extraction_deferral_record_valid") is True
            and decision_record_summary.get("gate_summary", {}).get("exam_deployment_status") == "not_cleared"
            and decision_record_completion_status == 200
            and decision_record_completion.get("exam_deployment_status") == "not_cleared",
            "external_decision_record_journal",
            (
                f"exam={decision_record_exam.get('status')}, deferral={decision_record_deferral.get('status')}, "
                f"accepted={decision_record_summary.get('accepted_record_count')}, "
                f"audit={decision_record_completion.get('status')}, "
                f"exam_deployment={decision_record_summary.get('gate_summary', {}).get('exam_deployment_status')}"
            ),
        )
    )

    course_scope_status, course_scope = route_request(
        "/api/unibot/course/exam-scope",
        payload={
            "records": [
                {
                    "material_id": "smoke-pandas",
                    "title": "pandas smoke source",
                    "source_kind": "transcript",
                    "permission_status": "private_course_use_only",
                    "publish_policy": "private_only",
                    "extraction_status": "text_extracted",
                    "review_status": "reviewed_for_private_tutor",
                    "skill_tags": ["pandas", "boxplots"],
                    "source_card_ids": ["dfg-gwp"],
                    "page_or_timestamp": "smoke",
                    "sha256": "2b54676db8d3f0971a0a6d07e92df1661fe7aee6d401de4c76da183c87490864",
                }
            ]
        },
    )
    checks.append(
        _check(
            course_scope_status == 200
            and course_scope.get("artifact_type") == "exam_scope_map"
            and course_scope.get("exam_deployment_status") == "not_cleared"
            and course_scope.get("public_safety_status") == "pass",
            "course_scope_map",
            f"status={course_scope_status}, materials={course_scope.get('material_summary', {}).get('record_count')}",
        )
    )

    orchestration_status, orchestration = route_request("/api/unibot/orchestration/command-center", payload={})
    checks.append(
        _check(
            orchestration_status == 200
            and orchestration.get("artifact_type") == "unibot_orchestration_command_center"
            and orchestration.get("status") == "ready_to_orchestrate"
            and orchestration.get("deployment_line", {}).get("exam_deployment_status") == "not_cleared"
            and orchestration.get("public_safety_status") == "pass"
            and len(orchestration.get("role_lanes", [])) >= 7,
            "orchestration_command_center",
            (
                f"status={orchestration_status}, roles={len(orchestration.get('role_lanes', []))}, "
                f"exam={orchestration.get('deployment_line', {}).get('exam_deployment_status')}"
            ),
        )
    )

    handoff_status, handoff = route_request(
        "/api/unibot/orchestration/handoff/validate",
        payload={
            "handoff": {
                "role_id": "qa_redteam",
                "goal": "Run pipeline smoke.",
                "changed_files": ["scripts/unibot_pipeline_smoke.py"],
                "tests": ["python3 scripts/unibot_pipeline_smoke.py --json"],
                "risks": ["real exam use remains not cleared"],
                "evidence": ["orchestration command center"],
                "next_step": "continue only after green smoke",
            }
        },
    )
    checks.append(
        _check(
            handoff_status == 200 and handoff.get("status") == "ok" and handoff.get("public_safety_status") == "pass",
            "orchestration_handoff_contract",
            f"status={handoff_status}, result={handoff.get('status')}, issues={handoff.get('issues')}",
        )
    )

    readiness_status, readiness = route_request("/api/unibot/readiness-check", payload={})
    checks.append(
        _check(
            readiness_status == 200
            and readiness.get("status") == "public_draft_ready"
            and readiness.get("failed_count", 1) == 0,
            "readiness_check_public_draft",
            f"status={readiness_status}, result={readiness.get('status')}, failed={readiness.get('failed_count')}",
        )
    )

    completion_status, completion = route_request("/api/unibot/completion-audit", payload={})
    checks.append(
        _check(
            completion_status == 200
            and completion.get("artifact_type") == "unibot_project_completion_audit"
            and completion.get("public_draft_ready") is True
            and completion.get("exam_deployment_status") == "not_cleared"
            and completion.get("public_safety_status") == "pass"
            and completion.get("goal_complete") is True
            and completion.get("open_count", 1) == 0
            and completion.get("reminder_count", 0) >= 1
            and completion.get("external_real_world_reminders"),
            "completion_audit_public_draft_technical_complete_with_reminder",
            (
                f"status={completion_status}, audit={completion.get('status')}, "
                f"open={completion.get('open_count')}, reminders={completion.get('reminder_count')}, "
                f"complete={completion.get('goal_complete')}"
            ),
        )
    )

    redteam = run_redteam_smoke()
    checks.append(
        _check(
            redteam.get("status") == "pass" and redteam.get("failed_count", 0) == 0,
            "redteam_smoke",
            f"status={redteam.get('status')}, pass={redteam.get('passed_count')}, fail={redteam.get('failed_count')}",
        )
    )

    gretel_loop = run_gretel_unibot_loop()
    checks.append(
        _check(
            gretel_loop.get("status") == "pass"
            and gretel_loop.get("artifact_type") == "unibot_gretel_exam_loop_report"
            and gretel_loop.get("public_safety", {}).get("status") == "pass",
            "gretel_unibot_loop_smoke",
            (
                f"status={gretel_loop.get('status')}, scenarios={gretel_loop.get('scenario_count')}, "
                f"blocked={gretel_loop.get('summary', {}).get('blocked_outputs')}"
            ),
        )
    )

    glm_packet_status, glm_packet = route_request("/api/unibot/gretel-glm-evolve/work-packet", payload={})
    glm_validation_status, glm_validation = route_request(
        "/api/unibot/gretel-glm-evolve/validate-proposal",
        payload={
            "proposal": {
                "recommendation": "Keep UniBot proposal-only and source-grounded.",
                "patch_outline": ["Add a regression fixture before changing behavior."],
                "test_plan": ["Run focused UniBot tests and public-safety scan."],
                "risk_flags": ["Exam deployment remains not cleared."],
                "confidence": "medium",
            }
        },
    )
    checks.append(
        _check(
            glm_packet_status == 200
            and glm_packet.get("status") == "prepared_no_provider_call"
            and glm_packet.get("public_safety_status") == "pass"
            and glm_packet.get("provider_call_executed") is False
            and glm_packet.get("raw_private_context_shared") is False
            and glm_packet.get("autonomous_apply") is False
            and glm_validation_status == 200
            and glm_validation.get("status") == "ok",
            "gretel_glm_evolve_lane_smoke",
            (
                f"packet={glm_packet.get('status')}, model={glm_packet.get('model_hint')}, "
                f"provider={glm_packet.get('provider_call_executed')}, validation={glm_validation.get('status')}"
            ),
        )
    )

    loop_lab = run_loop_lab(compare_previous=False)
    checks.append(
        _check(
            loop_lab.get("status") == "pass"
            and loop_lab.get("artifact_type") == "unibot_loop_lab_report_v2"
            and loop_lab.get("scenario_count") == 25
            and loop_lab.get("public_safety", {}).get("status") == "pass",
            "loop_lab_v2_smoke",
            (
                f"status={loop_lab.get('status')}, scenarios={loop_lab.get('scenario_count')}, "
                f"backlog={len(loop_lab.get('backlog_items', []))}"
            ),
        )
    )

    publication_status, publication = route_request("/api/unibot/publication-package", payload={})
    checks.append(
        _check(
            publication_status == 200
            and publication.get("status") == "public_draft_not_exam_release"
            and publication.get("release_gates", {}).get("release_ready") is True,
            "publication_package_ready",
            f"status={publication_status}, gates={publication.get('release_gates', {}).get('release_ready')}",
        )
    )

    review_board_status, review_board = route_request("/api/unibot/review-board-packet", payload={})
    reviewer_count = len(review_board.get("reviewer_packets", [])) if isinstance(review_board, dict) else 0
    open_decision_count = len(review_board.get("open_decision_register", [])) if isinstance(review_board, dict) else 0
    checks.append(
        _check(
            review_board_status == 200
            and review_board.get("status") == "draft_for_institutional_review",
            "review_board_packet_ready",
            (
                f"status={review_board_status}, reviewers={reviewer_count}, "
                f"open_decisions={open_decision_count}, exam={review_board.get('exam_deployment_status')}"
            ),
        )
    )

    failed = [check for check in checks if not check.passed]
    passed_count = len(checks) - len(failed)
    return {
        "status": "pass" if not failed else "fail",
        "check_count": len(checks),
        "passed_count": passed_count,
        "failed_count": len(failed),
        "checks": [
            {"name": check.name, "passed": check.passed, "details": check.details}
            for check in checks
        ],
        "failed_checks": [
            {"name": check.name, "details": check.details}
            for check in failed
        ],
        "readiness_summary": readiness,
        "redteam_summary": redteam,
        "public_draft_status": readiness.get("status") if readiness_status == 200 else "unavailable",
    }


def run_full_suite(run_unit_tests_flag: bool) -> dict[str, Any]:
    report = run_smoke_suite()
    if not run_unit_tests_flag:
        return report

    unit_report = run_unit_tests()
    unit_passed = unit_report.get("status") == "pass"
    report["checks"].append(
        {
            "name": "unit_test_suite",
            "passed": unit_passed,
            "details": (
                f"pytest exit={unit_report['return_code']}, passed={unit_report['passed_count']}, "
                f"failed={unit_report['failed_count']}, xfailed={unit_report['xfailed']}, skipped={unit_report['skipped']}"
            ),
        }
    )
    report["check_count"] += 1
    if unit_passed:
        report["passed_count"] += 1
    else:
        report["failed_count"] += 1
    if report["failed_count"]:
        report["status"] = "fail"
    else:
        report["status"] = "pass"
    report["unit_tests"] = unit_report
    return report


def _print_summary(payload: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    width = 70
    print("UniBot Pipeline Smoke")
    print("-" * width)
    for check in payload["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"[{status}] {check['name']}: {check['details']}")
    print("-" * width)
    print(
        f"Result: {payload['status'].upper()} | passed={payload['passed_count']} "
        f"failed={payload['failed_count']} total={payload['check_count']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the UniBot separate track pipeline smoke suite.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    parser.add_argument("--run-tests", action="store_true", help="Run all tests/test_unibot_*.py in addition to API smoke.")
    args = parser.parse_args()

    report = run_full_suite(run_unit_tests_flag=args.run_tests)
    _print_summary(report, json_output=args.json)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
