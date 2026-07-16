"""Atomically assemble the human-facing UniBot release handoff."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .public_safety import scan_text
from .release_audit import audit_release_candidate
from .release_candidate import write_release_candidate_bundle
from .release_pr import write_release_pr_draft


RELEASE_HANDOFF_SCHEMA_VERSION = "UniBotReleaseHandoffV1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _blocked(reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "schema_version": RELEASE_HANDOFF_SCHEMA_VERSION,
        "artifact_type": "unibot_release_handoff",
        "status": "blocked",
        "reason": reason,
        "automatic_publication": False,
        "automatic_merge": False,
        "provider_calls": 0,
        "exam_deployment_status": "not_cleared",
        **extra,
    }


def write_release_handoff(
    output_dir: str | Path,
    *,
    repository: str | Path | None = None,
) -> dict[str, Any]:
    """Build candidate, audit, and PR draft as one atomic local handoff."""
    root = Path(output_dir).expanduser()
    if root.is_symlink() or root.exists():
        raise ValueError("release handoff output must be a new directory")
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.", dir=root.parent))
    os.chmod(staging, 0o700)
    repo = Path(repository).expanduser() if repository is not None else Path(__file__).resolve().parents[1]
    try:
        candidate_dir = staging / "candidate"
        candidate = write_release_candidate_bundle(candidate_dir)
        if candidate.get("status") != "written":
            return _blocked("release_candidate_blocked", candidate=candidate)

        audit = audit_release_candidate(candidate_dir, repository=repo)
        if audit.get("status") != "pass":
            return _blocked("release_candidate_audit_failed", audit=audit)

        pr_path = staging / "UNIBOT-PR-DRAFT.md"
        pr = write_release_pr_draft(pr_path, candidate_dir, repository=repo)
        if pr.get("status") != "ready_for_human_review":
            return _blocked("release_pr_draft_blocked", pr_draft=pr)

        candidate_manifest = candidate_dir / "RELEASE-MANIFEST.json"
        handoff_manifest = {
            "schema_version": RELEASE_HANDOFF_SCHEMA_VERSION,
            "artifact_type": "unibot_release_handoff_manifest",
            "status": "public_draft_ready_for_human_review",
            "exam_deployment_status": "not_cleared",
            "source_commit": candidate["source_commit"],
            "candidate_manifest_sha256": _sha256_file(candidate_manifest),
            "candidate_file_count": candidate["file_count"],
            "demo_fixture_sha256": candidate.get("demo_fixture_sha256"),
            "public_demo_markdown_sha256": candidate.get("public_demo_markdown_sha256"),
            "candidate_public_safety_status": audit["public_safety_status"],
            "candidate_audit_status": audit["status"],
            "pr_draft_sha256": _sha256_file(pr_path),
            "pr_draft_public_safety_status": pr["public_safety_status"],
            "provider_calls": 0,
            "learner_content_included": False,
            "private_project_files_included": False,
            "automatic_publication": False,
            "automatic_merge": False,
            "human_gates": [
                "human GitHub draft PR creation",
                "human review after the last bot push",
                "institutional review by teaching, inclusion, privacy, IT/SZI, and examination roles",
            ],
            "authorship": {
                "implementation_and_documentation": "Gretel / Codex",
                "glm_role": "No contribution while GLM is parked.",
                "human_gate": "Julius remains human project lead and merge/release decision-maker.",
            },
        }
        manifest_text = json.dumps(handoff_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        safety = scan_text(manifest_text, "HANDOFF-MANIFEST.json")
        if safety["status"] != "pass":
            return _blocked("handoff_manifest_public_safety_failed", finding_count=len(safety["findings"]))
        manifest_path = staging / "HANDOFF-MANIFEST.json"
        manifest_path.write_text(manifest_text, encoding="utf-8")
        os.chmod(manifest_path, 0o600)

        os.replace(staging, root)
        return {
            "schema_version": RELEASE_HANDOFF_SCHEMA_VERSION,
            "artifact_type": "unibot_release_handoff",
            "status": "written",
            "output_file_names": ["HANDOFF-MANIFEST.json", "UNIBOT-PR-DRAFT.md", "candidate/"],
            "candidate_file_count": candidate["file_count"],
            "demo_fixture_sha256": candidate.get("demo_fixture_sha256"),
            "public_demo_markdown_sha256": candidate.get("public_demo_markdown_sha256"),
            "candidate_manifest_sha256": _sha256_file(root / "candidate" / "RELEASE-MANIFEST.json"),
            "pr_draft_sha256": _sha256_file(root / "UNIBOT-PR-DRAFT.md"),
            "source_commit": candidate["source_commit"],
            "public_safety_status": "pass",
            "provider_calls": 0,
            "learner_content_included": False,
            "private_project_files_included": False,
            "automatic_publication": False,
            "automatic_merge": False,
            "exam_deployment_status": "not_cleared",
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging)
