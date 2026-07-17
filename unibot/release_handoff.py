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
from .release_evidence import validate_release_evidence
from .release_pr import write_release_pr_draft


RELEASE_HANDOFF_SCHEMA_VERSION = "UniBotReleaseHandoffV1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_colab_canary(path: Path, source_commit: str) -> dict[str, Any]:
    """Accept only metadata-only live-Colab evidence bound to this source commit."""
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
        return {"status": "blocked", "reason": "colab_canary_permissions_or_path_invalid"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"status": "blocked", "reason": "colab_canary_not_valid_json"}
    if not isinstance(payload, dict):
        return {"status": "blocked", "reason": "colab_canary_not_object"}
    required = {
        "schema_version": "UniBotLiveColabCanaryV1",
        "status": "pass",
        "source_commit": source_commit,
        "provider_calls": 0,
        "source_text_omitted": True,
        "raw_cell_text_persisted": False,
        "notebook_output_read": False,
    }
    if any(payload.get(key) != expected for key, expected in required.items()):
        return {"status": "blocked", "reason": "colab_canary_contract_mismatch"}
    safety = scan_text(path.read_text(encoding="utf-8"), "COLAB-CANARY.json")
    if safety["status"] != "pass":
        return {"status": "blocked", "reason": "colab_canary_public_safety_failed"}
    return {"status": "pass", "payload": payload}


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
    evidence: str | Path | None = None,
    colab_canary: str | Path | None = None,
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
        verification = None
        if evidence is not None:
            verification = validate_release_evidence(evidence, repository=repo)
            if verification["status"] != "pass":
                return _blocked(
                    "release_evidence_blocked",
                    verification_evidence_status=verification["status"],
                    verification_evidence_issues=verification["issues"],
                )
        candidate_dir = staging / "candidate"
        candidate = write_release_candidate_bundle(candidate_dir)
        if candidate.get("status") != "written":
            return _blocked("release_candidate_blocked", candidate=candidate)

        canary_source = Path(colab_canary).expanduser() if colab_canary is not None else None
        canary = {"status": "not_recorded"}
        canary_path = None
        if canary_source is not None:
            canary = _validate_colab_canary(canary_source, str(candidate["source_commit"]))
            if canary["status"] != "pass":
                return _blocked("colab_canary_blocked", colab_canary=canary)
            canary_path = staging / "COLAB-CANARY.json"
            shutil.copyfile(canary_source, canary_path)
            os.chmod(canary_path, 0o600)

        audit = audit_release_candidate(candidate_dir, repository=repo)
        if audit.get("status") != "pass":
            return _blocked("release_candidate_audit_failed", audit=audit)

        pr_path = staging / "UNIBOT-PR-DRAFT.md"
        pr = write_release_pr_draft(pr_path, candidate_dir, repository=repo, evidence=evidence)
        if pr.get("status") != "ready_for_human_review":
            return _blocked("release_pr_draft_blocked", pr_draft=pr)

        evidence_path = None
        if evidence is not None:
            evidence_path = staging / "RELEASE-EVIDENCE.json"
            shutil.copyfile(Path(evidence).expanduser(), evidence_path)
            os.chmod(evidence_path, 0o600)
            evidence_scan = scan_text(evidence_path.read_text(encoding="utf-8"), "RELEASE-EVIDENCE.json")
            if evidence_scan["status"] != "pass":
                return _blocked("release_evidence_public_safety_failed", finding_count=len(evidence_scan["findings"]))

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
            "verification_evidence_status": pr.get("verification_evidence_status", "not_recorded"),
            "verification_evidence_sha256": pr.get("release_evidence_sha256", ""),
            "verification_gate_ids": pr.get("verification_gate_ids", []),
            "verification_evidence_file": "RELEASE-EVIDENCE.json" if evidence_path else None,
            "colab_canary_file": "COLAB-CANARY.json" if canary_path else None,
            "colab_canary_sha256": _sha256_file(canary_path) if canary_path else None,
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
        output_file_names = ["HANDOFF-MANIFEST.json", "UNIBOT-PR-DRAFT.md", "candidate/"]
        if evidence_path:
            output_file_names.append("RELEASE-EVIDENCE.json")
        if canary_path:
            output_file_names.append("COLAB-CANARY.json")
        return {
            "schema_version": RELEASE_HANDOFF_SCHEMA_VERSION,
            "artifact_type": "unibot_release_handoff",
            "status": "written",
            "output_file_names": output_file_names,
            "candidate_file_count": candidate["file_count"],
            "demo_fixture_sha256": candidate.get("demo_fixture_sha256"),
            "public_demo_markdown_sha256": candidate.get("public_demo_markdown_sha256"),
            "candidate_manifest_sha256": _sha256_file(root / "candidate" / "RELEASE-MANIFEST.json"),
            "pr_draft_sha256": _sha256_file(root / "UNIBOT-PR-DRAFT.md"),
            "verification_evidence_status": pr.get("verification_evidence_status", "not_recorded"),
            "verification_evidence_sha256": pr.get("release_evidence_sha256", ""),
            "verification_gate_ids": pr.get("verification_gate_ids", []),
            "colab_canary_sha256": _sha256_file(root / "COLAB-CANARY.json") if canary_path else None,
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
