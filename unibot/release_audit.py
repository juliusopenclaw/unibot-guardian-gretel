"""Read-only integrity audit for a public UniBot release candidate."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .public_safety import scan_text


RELEASE_AUDIT_SCHEMA_VERSION = "UniBotReleaseAuditV1"
REQUIRED_ARTIFACT_NAMES = frozenset(
    {
        "INSTITUTIONAL-MANIFEST.json",
        "PUBLIC-DEMO.md",
        "REVIEW-START-HERE.md",
        "institutional-accessibility-walkthrough.md",
        "institutional-plain-language-brief.md",
        "institutional-presentation.json",
        "institutional-presentation.md",
        "institutional-review-decision-template.md",
        "review-board-packet.json",
        "review-board-packet.md",
        "synthetic_python_practice.ipynb",
        "unibot-mantle.zip",
    }
)


def _read_json_object(path: Path, issue_id: str, issues: list[str]) -> dict[str, Any]:
    """Read a review artifact without allowing malformed JSON to pass as empty data."""
    if not path.is_file():
        issues.append(f"{issue_id}_missing")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        issues.append(f"{issue_id}_invalid")
        return {}
    if not isinstance(value, dict):
        issues.append(f"{issue_id}_not_object")
        return {}
    return value


def _require_field(
    payload: dict[str, Any],
    path: str,
    expected: Any,
    issue_id: str,
    issues: list[str],
) -> None:
    """Require a stable public review contract field and report drift by field name."""
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            issues.append(f"{issue_id}_missing:{path}")
            return
        current = current[part]
    if current != expected:
        issues.append(f"{issue_id}_mismatch:{path}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _current_commit(repository: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and len(commit) == 40 else None


def _current_worktree_clean(repository: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and not result.stdout.strip()


def audit_release_candidate(candidate_dir: str | Path, *, repository: str | Path | None = None) -> dict[str, Any]:
    """Verify a candidate without modifying it or making external calls."""
    root = Path(candidate_dir).expanduser()
    issues: list[str] = []
    manifest_path = root / "RELEASE-MANIFEST.json"
    manifest: dict[str, Any] = {}
    institutional_manifest: dict[str, Any] = {}
    presentation: dict[str, Any] = {}
    review_board: dict[str, Any] = {}
    if not root.is_dir():
        issues.append("candidate_directory_missing")
    elif not manifest_path.is_file():
        issues.append("release_manifest_missing")
    else:
        try:
            parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                manifest = parsed
            else:
                issues.append("release_manifest_not_object")
        except (OSError, json.JSONDecodeError):
            issues.append("release_manifest_invalid")

    provenance = manifest.get("source_provenance") if isinstance(manifest, dict) else None
    if manifest:
        if manifest.get("schema_version") != "UniBotReleaseCandidateV1":
            issues.append("release_manifest_schema_mismatch")
        if manifest.get("status") != "public_draft_not_exam_release":
            issues.append("candidate_status_not_public_draft")
        if manifest.get("exam_deployment_status") != "not_cleared":
            issues.append("exam_deployment_must_remain_not_cleared")
        for field in ("automatic_merge", "automatic_publication", "learner_content_included", "private_project_files_included"):
            if manifest.get(field) is not False:
                issues.append(f"manifest_{field}_must_be_false")
        if manifest.get("provider_calls") != 0:
            issues.append("provider_calls_must_be_zero")

        provenance = manifest.get("source_provenance")
        if not isinstance(provenance, dict) or provenance.get("status") != "verified":
            issues.append("source_provenance_not_verified")
        if not isinstance(provenance, dict) or provenance.get("working_tree_clean") is not True:
            issues.append("source_worktree_not_clean")

        records = manifest.get("files")
        if not isinstance(records, list):
            issues.append("release_file_records_missing")
            records = []
        record_names: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                issues.append("release_file_record_invalid")
                continue
            name = str(record.get("name", ""))
            record_names.add(name)
            if not name or Path(name).name != name or name.startswith("."):
                issues.append(f"release_file_name_invalid:{name or 'empty'}")
                continue
            path = root / name
            if not path.is_file():
                issues.append(f"release_file_missing:{name}")
                continue
            if record.get("bytes") != path.stat().st_size:
                issues.append(f"release_file_size_mismatch:{name}")
            if record.get("sha256") != _sha256_file(path):
                issues.append(f"release_file_hash_mismatch:{name}")
            if record.get("public_safety_status") != "pass":
                issues.append(f"release_file_safety_not_pass:{name}")
        missing = sorted(REQUIRED_ARTIFACT_NAMES - record_names)
        issues.extend(f"required_artifact_not_recorded:{name}" for name in missing)

        if isinstance(provenance, dict):
            institutional_manifest = _read_json_object(
                root / "INSTITUTIONAL-MANIFEST.json", "institutional_manifest", issues
            )
            if institutional_manifest:
                if institutional_manifest.get("source_commit") != provenance.get("commit"):
                    issues.append("institutional_source_commit_mismatch")
                institutional_provenance = institutional_manifest.get("source_provenance")
                if not isinstance(institutional_provenance, dict):
                    issues.append("institutional_source_provenance_missing")
                else:
                    if institutional_provenance.get("status") != "verified":
                        issues.append("institutional_source_provenance_not_verified")
                    if institutional_provenance.get("commit") != provenance.get("commit"):
                        issues.append("institutional_provenance_commit_mismatch")

            presentation = _read_json_object(
                root / "institutional-presentation.json", "institutional_presentation", issues
            )
            review_board = _read_json_object(root / "review-board-packet.json", "review_board_packet", issues)

    # Hashes prove file identity; these semantic checks prove that the identity
    # still carries the review boundaries the institutions are being shown.
    if manifest and presentation:
        _require_field(
            presentation,
            "schema_version",
            "InstitutionalPresentationV1",
            "institutional_presentation_schema",
            issues,
        )
        _require_field(
            presentation,
            "status",
            "ready_for_human_review",
            "institutional_presentation_status",
            issues,
        )
        _require_field(
            presentation,
            "deployment_status",
            "not_cleared",
            "institutional_presentation_deployment",
            issues,
        )
        _require_field(
            presentation,
            "public_safety_status",
            "pass",
            "institutional_presentation_public_safety",
            issues,
        )
        _require_field(
            presentation,
            "accessibility_review.schema_version",
            "AccessibilityReviewV1",
            "accessibility_review_schema",
            issues,
        )
        _require_field(
            presentation,
            "accessibility_review.scope",
            "local_learning_and_practice_only",
            "accessibility_review_scope",
            issues,
        )
        _require_field(
            presentation,
            "accessibility_review.status",
            "ready_for_human_accessibility_review",
            "accessibility_review_status",
            issues,
        )
        _require_field(
            presentation,
            "accessibility_review_validation.conformance_cleared",
            False,
            "accessibility_conformance_gate",
            issues,
        )
        _require_field(
            presentation,
            "institutional_review_decision_template.status",
            "blank_for_human_completion",
            "decision_template_status",
            issues,
        )
        _require_field(
            presentation,
            "institutional_review_decision_template_validation.automatic_approval",
            False,
            "decision_template_automatic_approval",
            issues,
        )
        _require_field(
            presentation,
            "institutional_review_decision_template_validation.human_completion_required",
            True,
            "decision_template_human_gate",
            issues,
        )

        evidence_hash = presentation.get("evidence_hash")
        if not isinstance(evidence_hash, str) or len(evidence_hash) != 64:
            issues.append("institutional_evidence_hash_invalid")
        else:
            if manifest.get("institutional_evidence_hash") != evidence_hash:
                issues.append("release_institutional_evidence_hash_mismatch")
            if institutional_manifest.get("evidence_hash") != evidence_hash:
                issues.append("institutional_manifest_evidence_hash_mismatch")

    if manifest and review_board:
        _require_field(
            review_board,
            "schema_version",
            "unibot-review-board-packet-v1",
            "review_board_schema",
            issues,
        )
        _require_field(
            review_board,
            "status",
            "draft_for_institutional_review",
            "review_board_status",
            issues,
        )
        _require_field(
            review_board,
            "exam_deployment_status",
            "not_cleared",
            "review_board_exam_deployment",
            issues,
        )
        _require_field(
            review_board,
            "public_safety_status",
            "pass",
            "review_board_public_safety",
            issues,
        )
        reviewer_packets = review_board.get("reviewer_packets")
        if not isinstance(reviewer_packets, list) or len(reviewer_packets) < 6:
            issues.append("review_board_reviewer_packets_incomplete")
        for field in ("evidence_alignment", "thesis_evaluation_claim_alignment", "professor_uni_review_brief"):
            _require_field(review_board, f"{field}.status", "ready", f"review_board_{field}", issues)
        if manifest.get("review_board_status") != review_board.get("status"):
            issues.append("release_review_board_status_mismatch")
        if manifest.get("review_board_public_safety_status") != review_board.get("public_safety_status"):
            issues.append("release_review_board_safety_mismatch")

    source_commit = None
    source_commit_match: bool | None = None
    source_worktree_clean: bool | None = None
    if isinstance(provenance, dict):
        source_commit = provenance.get("commit")
        if repository is not None:
            repository_path = Path(repository).expanduser()
            current_commit = _current_commit(repository_path)
            source_commit_match = bool(current_commit and current_commit == source_commit)
            source_worktree_clean = _current_worktree_clean(repository_path)
            if not source_commit_match:
                issues.append("candidate_source_commit_does_not_match_repository")
            if not source_worktree_clean:
                issues.append("candidate_source_worktree_not_clean")

    safety_status = "missing"
    if root.is_dir():
        safety_targets = [
            root / name
            for name in (
                "institutional-presentation.json",
                "institutional-presentation.md",
                "institutional-accessibility-walkthrough.md",
                "institutional-plain-language-brief.md",
                "institutional-review-decision-template.md",
                "review-board-packet.json",
                "review-board-packet.md",
                "INSTITUTIONAL-MANIFEST.json",
                "PUBLIC-DEMO.md",
                "REVIEW-START-HERE.md",
                "synthetic_python_practice.ipynb",
            )
        ]
        scans = [scan_text(path.read_text(encoding="utf-8"), path.name) for path in safety_targets if path.is_file()]
        safety_status = "pass" if scans and all(scan["status"] == "pass" for scan in scans) else "blocked"
        if safety_status != "pass":
            issues.append("candidate_public_safety_not_pass")

    return {
        "schema_version": RELEASE_AUDIT_SCHEMA_VERSION,
        "artifact_type": "unibot_release_candidate_audit",
        "status": "pass" if not issues else "blocked",
        "candidate_directory_checked": root.is_dir(),
        "release_manifest_sha256": _sha256_file(manifest_path) if manifest_path.is_file() else None,
        "source_commit": source_commit,
        "source_commit_match": source_commit_match,
        "source_worktree_clean": source_worktree_clean,
        "recorded_file_count": len(manifest.get("files", [])) if isinstance(manifest.get("files"), list) else 0,
        "public_safety_status": safety_status,
        "automatic_merge": manifest.get("automatic_merge") if manifest else None,
        "automatic_publication": manifest.get("automatic_publication") if manifest else None,
        "exam_deployment_status": manifest.get("exam_deployment_status", "not_cleared"),
        "provider_calls": manifest.get("provider_calls", 0),
        "issues": sorted(set(issues)),
        "side_effects": {
            "files_written": False,
            "network_called": False,
            "provider_called": False,
            "git_changed": False,
        },
    }
