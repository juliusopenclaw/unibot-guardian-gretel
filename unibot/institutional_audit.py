"""Read-only integrity audit for the public institutional review bundle."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from .public_safety import scan_text
from .release_evidence import REQUIRED_GATE_IDS


INSTITUTIONAL_REVIEW_AUDIT_SCHEMA_VERSION = "InstitutionalReviewAuditV1"
INSTITUTIONAL_REVIEW_MANIFEST_SCHEMA_VERSION = "unibot-institutional-review-bundle-manifest-v1"
RELEASE_EVIDENCE_SCHEMA_VERSION = "UniBotReleaseEvidenceV1"
COLAB_CANARY_SCHEMA_VERSION = "UniBotLiveColabCanaryV1"
JUPYTER_CANARY_SCHEMA_VERSION = "UniBotLiveJupyterCanaryV1"
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_RAW_KEYS = frozenset({"stdout", "stderr", "raw_output", "command", "path", "local_path"})
_BASE_FILES = frozenset(
    {
        "CONTROLLED-EXAM-REHEARSAL-V1.md",
        "PUBLIC-DEMO.md",
        "institutional-accessibility-walkthrough.md",
        "institutional-plain-language-brief.md",
        "institutional-presentation.json",
        "institutional-presentation.md",
        "institutional-review-decision-template.md",
        "synthetic_python_practice.ipynb",
        "unibot-mantle.zip",
    }
)
_OPTIONAL_EVIDENCE_FILES = frozenset({"RELEASE-EVIDENCE.json", "COLAB-CANARY.json", "JUPYTER-CANARY.json"})


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _contains_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        if any(key in _RAW_KEYS for key in value):
            return True
        return any(_contains_raw_key(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_raw_key(child) for child in value)
    return False


def _read_json(path: Path, issues: list[str], issue_prefix: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        issues.append(f"{issue_prefix}_missing_or_symlink")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        issues.append(f"{issue_prefix}_invalid_json")
        return {}
    if not isinstance(payload, dict):
        issues.append(f"{issue_prefix}_not_object")
        return {}
    return payload


def _require(payload: dict[str, Any], field: str, expected: Any, issue: str, issues: list[str]) -> None:
    if payload.get(field) != expected:
        issues.append(issue)


def _audit_extension_zip(path: Path, issues: list[str]) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if not names:
                issues.append("extension_package_empty")
            for info in archive.infolist():
                name = info.filename
                parts = Path(name).parts
                mode = (info.external_attr >> 16) & 0o170000
                if name.startswith("/") or ".." in parts or mode == 0o120000:
                    issues.append("extension_package_member_unsafe")
                    continue
                if info.is_dir():
                    continue
                if Path(name).suffix.lower() not in {".css", ".html", ".js", ".json"}:
                    issues.append("extension_package_member_type_unsupported")
                    continue
                try:
                    content = archive.read(info).decode("utf-8")
                except (UnicodeDecodeError, RuntimeError, zipfile.BadZipFile):
                    issues.append("extension_package_member_unreadable")
                    continue
                if scan_text(content, f"extension:{Path(name).name}")["status"] != "pass":
                    issues.append("extension_package_public_safety_failed")
    except (OSError, zipfile.BadZipFile):
        issues.append("extension_package_invalid")


def _audit_release_evidence(payload: dict[str, Any], source_commit: str, issues: list[str]) -> None:
    _require(payload, "schema_version", RELEASE_EVIDENCE_SCHEMA_VERSION, "release_evidence_schema_mismatch", issues)
    _require(payload, "status", "pass", "release_evidence_status_not_pass", issues)
    _require(payload, "source_commit", source_commit, "release_evidence_source_commit_mismatch", issues)
    _require(payload, "provider_calls", 0, "release_evidence_provider_calls_not_zero", issues)
    _require(payload, "learner_content_included", False, "release_evidence_learner_content_present", issues)
    _require(payload, "private_project_files_included", False, "release_evidence_private_files_present", issues)
    _require(payload, "automatic_publication", False, "release_evidence_automatic_publication", issues)
    _require(payload, "automatic_merge", False, "release_evidence_automatic_merge", issues)
    _require(payload, "exam_deployment_status", "not_cleared", "release_evidence_exam_status_drift", issues)
    if _contains_raw_key(payload):
        issues.append("release_evidence_raw_key_present")
    gates = payload.get("gates")
    if not isinstance(gates, list):
        issues.append("release_evidence_gates_missing")
        return
    by_id = {gate.get("gate_id"): gate for gate in gates if isinstance(gate, dict)}
    for gate_id in REQUIRED_GATE_IDS:
        if by_id.get(gate_id, {}).get("status") != "pass":
            issues.append("release_evidence_gate_not_green")
    recorded_hash = payload.get("evidence_sha256")
    unsigned = {key: value for key, value in payload.items() if key != "evidence_sha256"}
    if not isinstance(recorded_hash, str) or recorded_hash != hashlib.sha256(_canonical_json(unsigned).encode("utf-8")).hexdigest():
        issues.append("release_evidence_hash_invalid")


def _audit_canary(payload: dict[str, Any], source_commit: str, *, jupyter: bool, issues: list[str]) -> None:
    schema = JUPYTER_CANARY_SCHEMA_VERSION if jupyter else COLAB_CANARY_SCHEMA_VERSION
    _require(payload, "schema_version", schema, "canary_schema_mismatch", issues)
    _require(payload, "status", "pass", "canary_status_not_pass", issues)
    _require(payload, "source_commit", source_commit, "canary_source_commit_mismatch", issues)
    _require(payload, "provider_calls", 0, "canary_provider_calls_not_zero", issues)
    _require(payload, "source_text_omitted", True, "canary_source_text_present", issues)
    _require(payload, "raw_cell_text_persisted", False, "canary_raw_cell_text_persisted", issues)
    _require(payload, "notebook_output_read", False, "canary_notebook_output_read", issues)
    if jupyter:
        for field, expected, issue in (
            ("notebook_code_executed", False, "canary_notebook_executed"),
            ("native_transport", True, "canary_native_transport_missing"),
            ("tutor_flow_status", "pass", "canary_tutor_flow_failed"),
            ("session_started", True, "canary_session_not_started"),
            ("session_stopped", True, "canary_session_not_stopped"),
            ("session_deleted", True, "canary_session_not_deleted"),
            ("effective_help_level", "A2", "canary_help_level_drift"),
            ("complete_solution_emitted", False, "canary_complete_solution_emitted"),
            ("hint_text_omitted", True, "canary_hint_text_present"),
            ("local_tutor", "deterministic_source_grounded_v1", "canary_tutor_not_local"),
        ):
            _require(payload, field, expected, issue, issues)
        if not isinstance(payload.get("source_anchor_count"), int) or payload["source_anchor_count"] < 1:
            issues.append("canary_source_anchors_missing")


def audit_institutional_review_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    """Verify a review bundle locally without network access or content export."""
    root = Path(bundle_dir).expanduser()
    issues: list[str] = []
    manifest: dict[str, Any] = {}
    if root.is_symlink() or not root.is_dir():
        issues.append("bundle_directory_missing_or_symlink")
    manifest_path = root / "MANIFEST.json"
    if root.is_dir():
        manifest_text = ""
        if manifest_path.is_symlink() or not manifest_path.is_file():
            issues.append("manifest_missing_or_symlink")
        else:
            try:
                manifest_text = manifest_path.read_text(encoding="utf-8")
                parsed = json.loads(manifest_text)
                if isinstance(parsed, dict):
                    manifest = parsed
                else:
                    issues.append("manifest_not_object")
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                issues.append("manifest_invalid_json")
        if manifest_text and scan_text(manifest_text, "MANIFEST.json")["status"] != "pass":
            issues.append("manifest_public_safety_failed")

    _require(
        manifest,
        "schema_version",
        INSTITUTIONAL_REVIEW_MANIFEST_SCHEMA_VERSION,
        "manifest_schema_mismatch",
        issues,
    )
    _require(manifest, "artifact_type", "unibot_institutional_review_bundle_manifest", "manifest_type_mismatch", issues)
    _require(manifest, "packet_status", "ready_for_human_review", "manifest_packet_not_ready", issues)
    _require(manifest, "exam_deployment_status", "not_cleared", "manifest_exam_status_drift", issues)
    source_commit = manifest.get("source_commit")
    if not isinstance(source_commit, str) or not _COMMIT_PATTERN.fullmatch(source_commit):
        issues.append("manifest_source_commit_invalid")
        source_commit = ""
    source_provenance = manifest.get("source_provenance")
    if not isinstance(source_provenance, dict) or source_provenance.get("status") != "verified":
        issues.append("manifest_source_provenance_not_verified")
    elif source_provenance.get("commit") != source_commit:
        issues.append("manifest_provenance_commit_mismatch")

    records = manifest.get("files")
    record_names: set[str] = set()
    verified_count = 0
    if not isinstance(records, list):
        issues.append("manifest_file_records_missing")
        records = []
    for record in records:
        if not isinstance(record, dict):
            issues.append("file_record_invalid")
            continue
        name = record.get("name")
        if not isinstance(name, str) or not name or Path(name).name != name or name.startswith("."):
            issues.append("file_record_name_invalid")
            continue
        if name in record_names:
            issues.append("file_record_duplicate")
            continue
        record_names.add(name)
        path = root / name
        if path.is_symlink() or not path.is_file():
            issues.append("file_record_missing_or_symlink")
            continue
        try:
            if record.get("bytes") != path.stat().st_size or record.get("sha256") != _sha256_file(path):
                issues.append("file_record_hash_or_size_mismatch")
            elif record.get("public_safety_status") != "pass":
                issues.append("file_record_safety_status_not_pass")
            else:
                if name == "unibot-mantle.zip":
                    _audit_extension_zip(path, issues)
                else:
                    try:
                        text = path.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        issues.append("text_file_unreadable")
                    else:
                        if scan_text(text, name)["status"] != "pass":
                            issues.append("file_public_safety_failed")
                verified_count += 1
        except OSError:
            issues.append("file_record_unreadable")

    actual_names = {
        path.name
        for path in root.iterdir()
        if not path.is_symlink() and path.name != "MANIFEST.json"
    } if root.is_dir() else set()
    if actual_names != record_names:
        issues.append("bundle_file_set_mismatch")
    if not _BASE_FILES.issubset(record_names):
        issues.append("bundle_base_files_missing")

    rehearsal = manifest.get("controlled_rehearsal")
    if not isinstance(rehearsal, dict):
        issues.append("controlled_rehearsal_manifest_missing")
    else:
        _require(
            rehearsal,
            "status",
            "ready_for_institutional_rehearsal_review",
            "controlled_rehearsal_status_mismatch",
            issues,
        )
        _require(
            rehearsal,
            "specification_file",
            "CONTROLLED-EXAM-REHEARSAL-V1.md",
            "controlled_rehearsal_specification_mismatch",
            issues,
        )
        _require(rehearsal, "allowed_help_levels", ["A0", "A1", "A2"], "controlled_rehearsal_help_drift", issues)
        _require(rehearsal, "provider_calls", 0, "controlled_rehearsal_provider_calls_not_zero", issues)
        _require(rehearsal, "automatic_submission", False, "controlled_rehearsal_automatic_submission", issues)
        _require(rehearsal, "automatic_assessment", False, "controlled_rehearsal_automatic_assessment", issues)
        _require(rehearsal, "exam_deployment_status", "not_cleared", "controlled_rehearsal_exam_status_drift", issues)
        demo = manifest.get("demo")
        if not isinstance(demo, dict) or rehearsal.get("fixture_sha256") != demo.get("fixture_sha256"):
            issues.append("controlled_rehearsal_fixture_hash_mismatch")

    presentation = _read_json(root / "institutional-presentation.json", issues, "presentation") if root.is_dir() else {}
    _require(presentation, "schema_version", "InstitutionalPresentationV1", "presentation_schema_mismatch", issues)
    _require(presentation, "status", "ready_for_human_review", "presentation_not_ready", issues)
    _require(presentation, "deployment_status", "not_cleared", "presentation_exam_status_drift", issues)
    accessibility_validation = presentation.get("accessibility_review_validation")
    if not isinstance(accessibility_validation, dict) or accessibility_validation.get("conformance_cleared") is not False:
        issues.append("accessibility_conformance_not_human_gated")
    decision_validation = presentation.get("institutional_review_decision_template_validation")
    if not isinstance(decision_validation, dict) or decision_validation.get("automatic_approval") is not False:
        issues.append("automatic_institutional_approval_not_blocked")

    verification = manifest.get("release_verification")
    release_status = "not_recorded"
    if isinstance(verification, dict):
        release_status = str(verification.get("status", "not_recorded"))
        expected_files = {
            "release_evidence_file": "RELEASE-EVIDENCE.json",
            "colab_canary_file": "COLAB-CANARY.json",
            "jupyter_canary_file": "JUPYTER-CANARY.json",
        }
        for field, expected_name in expected_files.items():
            declared = verification.get(field)
            if declared is not None and declared != expected_name:
                issues.append("release_verification_file_reference_invalid")
        for name, jupyter in (("RELEASE-EVIDENCE.json", None), ("COLAB-CANARY.json", False), ("JUPYTER-CANARY.json", True)):
            if name not in record_names:
                continue
            payload = _read_json(root / name, issues, name.replace(".json", "").lower())
            if name == "RELEASE-EVIDENCE.json":
                _audit_release_evidence(payload, source_commit, issues)
            elif payload:
                _audit_canary(payload, source_commit, jupyter=bool(jupyter), issues=issues)
            recorded_hash = verification.get(
                {"RELEASE-EVIDENCE.json": "release_evidence_sha256", "COLAB-CANARY.json": "colab_canary_sha256", "JUPYTER-CANARY.json": "jupyter_canary_sha256"}[name]
            )
            if recorded_hash != _sha256_file(root / name):
                issues.append("release_verification_hash_mismatch")
        if release_status == "pass" and not _OPTIONAL_EVIDENCE_FILES.issubset(record_names):
            issues.append("release_verification_incomplete")
    elif _OPTIONAL_EVIDENCE_FILES.intersection(record_names):
        issues.append("release_verification_metadata_missing")

    return {
        "schema_version": INSTITUTIONAL_REVIEW_AUDIT_SCHEMA_VERSION,
        "artifact_type": "unibot_institutional_review_audit",
        "status": "pass" if not issues else "blocked",
        "source_commit": source_commit,
        "packet_status": manifest.get("packet_status", "missing"),
        "exam_deployment_status": manifest.get("exam_deployment_status", "not_cleared"),
        "release_verification_status": release_status,
        "file_count": len(record_names) + (1 if manifest_path.is_file() else 0),
        "verified_file_count": verified_count,
        "public_safety_status": "pass" if not issues else "blocked",
        "provider_calls": 0,
        "learner_content_included": False,
        "private_project_files_included": False,
        "read_only": True,
        "external_calls": 0,
        "raw_content_returned": False,
        "issues": issues,
    }


__all__ = ["INSTITUTIONAL_REVIEW_AUDIT_SCHEMA_VERSION", "audit_institutional_review_bundle"]
