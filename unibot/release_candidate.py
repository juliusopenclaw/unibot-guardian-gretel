from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .clearance import write_institutional_review_bundle
from .extension_package import package_extension
from .public_safety import scan_text


RELEASE_CANDIDATE_SCHEMA_VERSION = "UniBotReleaseCandidateV1"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_record(path: Path, name: str, *, public_safety_status: str) -> dict[str, Any]:
    return {
        "name": name,
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "public_safety_status": public_safety_status,
    }


def _scan_text_file(path: Path, name: str) -> str:
    return _scan_text_file_from_content(path.read_text(encoding="utf-8"), name)


def write_release_candidate_bundle(output_dir: str | Path) -> dict[str, Any]:
    """Write a public-safe review handoff without the repository checkout."""
    root = Path(output_dir).expanduser()
    if root.is_symlink() or root.exists():
        raise ValueError("release candidate output must be a new directory")
    root.parent.mkdir(parents=True, exist_ok=True)

    staging = Path(tempfile.mkdtemp(prefix=f".{root.name}.", dir=root.parent))
    os.chmod(staging, 0o700)
    try:
        with tempfile.TemporaryDirectory(prefix="unibot-release-build-") as build_dir_name:
            build_dir = Path(build_dir_name)
            extension_result = package_extension(build_dir / "unibot-mantle.zip")
            if extension_result.get("status") != "written":
                return {
                    "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                    "artifact_type": "unibot_release_candidate_bundle",
                    "status": "blocked",
                    "reason": "extension_package_blocked",
                    "exam_deployment_status": "not_cleared",
                }

            institutional_result = write_institutional_review_bundle(build_dir / "institutional")
            if institutional_result.get("status") != "written":
                return {
                    "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                    "artifact_type": "unibot_release_candidate_bundle",
                    "status": "blocked",
                    "reason": "institutional_review_bundle_blocked",
                    "exam_deployment_status": "not_cleared",
                }

            extension_path = staging / "unibot-mantle.zip"
            shutil.copy2(build_dir / "unibot-mantle.zip", extension_path)
            os.chmod(extension_path, 0o600)
            records = [
                _file_record(
                    extension_path,
                    "unibot-mantle.zip",
                    public_safety_status=str(extension_result["public_safety_status"]),
                )
            ]

            institutional_names = {
                "institutional-presentation.json": "institutional-presentation.json",
                "institutional-presentation.md": "institutional-presentation.md",
                "MANIFEST.json": "INSTITUTIONAL-MANIFEST.json",
            }
            for source_name, target_name in institutional_names.items():
                source = build_dir / "institutional" / source_name
                target = staging / target_name
                shutil.copy2(source, target)
                os.chmod(target, 0o600)
                safety_status = _scan_text_file(target, target_name)
                if safety_status != "pass":
                    return {
                        "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                        "artifact_type": "unibot_release_candidate_bundle",
                        "status": "blocked",
                        "reason": "institutional_artifact_public_safety_failed",
                        "exam_deployment_status": "not_cleared",
                    }
                records.append(_file_record(target, target_name, public_safety_status=safety_status))

        manifest = {
            "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
            "artifact_type": "unibot_release_candidate_bundle_manifest",
            "status": "public_draft_not_exam_release",
            "exam_deployment_status": "not_cleared",
            "files": sorted(records, key=lambda record: str(record["name"])),
            "extension_package_sha256": extension_result["package_sha256"],
            "institutional_evidence_hash": institutional_result["evidence_hash"],
            "public_safety_status": "pass",
            "provider_calls": 0,
            "learner_content_included": False,
            "private_project_files_included": False,
            "automatic_publication": False,
            "automatic_merge": False,
            "human_release_gates": [
                "human publication review",
                "Google Chrome canary with a synthetic notebook",
                "Developer ID signature and Apple notarization for general Mac distribution",
                "institutional review by teaching, inclusion, privacy, IT/SZI, and examination roles",
            ],
            "authorship": {
                "implementation_and_documentation": "Gretel / Codex",
                "glm_role": "No contribution while GLM is parked.",
                "human_gate": "Julius remains human project lead and merge/release decision-maker.",
            },
        }
        manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if _scan_text_file_from_content(manifest_text, "RELEASE-MANIFEST.json") != "pass":
            return {
                "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                "artifact_type": "unibot_release_candidate_bundle",
                "status": "blocked",
                "reason": "release_manifest_public_safety_failed",
                "exam_deployment_status": "not_cleared",
            }
        manifest_path = staging / "RELEASE-MANIFEST.json"
        manifest_path.write_text(manifest_text, encoding="utf-8")
        os.chmod(manifest_path, 0o600)
        records.append(_file_record(manifest_path, "RELEASE-MANIFEST.json", public_safety_status="pass"))

        os.replace(staging, root)
        return {
            "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
            "artifact_type": "unibot_release_candidate_bundle",
            "status": "written",
            "output_file_names": sorted(record["name"] for record in records),
            "file_count": len(records),
            "manifest_sha256": _sha256_file(root / "RELEASE-MANIFEST.json"),
            "extension_package_sha256": extension_result["package_sha256"],
            "institutional_evidence_hash": institutional_result["evidence_hash"],
            "public_safety_status": "pass",
            "provider_calls": 0,
            "learner_content_included": False,
            "private_project_files_included": False,
            "exam_deployment_status": "not_cleared",
            "automatic_publication": False,
            "automatic_merge": False,
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _scan_text_file_from_content(content: str, name: str) -> str:
    scan = scan_text(content, name)
    return str(scan["status"])
