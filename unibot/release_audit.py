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
        "institutional-plain-language-brief.md",
        "institutional-presentation.json",
        "institutional-presentation.md",
        "institutional-review-decision-template.md",
        "synthetic_python_practice.ipynb",
        "unibot-mantle.zip",
    }
)


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

    source_commit = None
    source_commit_match: bool | None = None
    source_worktree_clean: bool | None = None
    provenance = manifest.get("source_provenance") if isinstance(manifest, dict) else None
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
                "institutional-plain-language-brief.md",
                "institutional-review-decision-template.md",
                "INSTITUTIONAL-MANIFEST.json",
                "PUBLIC-DEMO.md",
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
