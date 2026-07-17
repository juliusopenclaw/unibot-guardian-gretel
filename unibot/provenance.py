"""Public-safe source provenance for reproducible human review artifacts."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


PUBLIC_PROVENANCE_SCHEMA_VERSION = "UniBotPublicSourceProvenanceV1"


def public_source_provenance(repository_root: Path | None = None) -> dict[str, Any]:
    """Return commit and cleanliness evidence without returning local paths."""
    root = repository_root or Path(__file__).resolve().parents[1]
    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        status_result = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return {
            "schema_version": PUBLIC_PROVENANCE_SCHEMA_VERSION,
            "status": "blocked_source_provenance_unavailable",
            "commit": None,
            "working_tree_clean": False,
        }

    commit = commit_result.stdout.strip()
    clean = status_result.returncode == 0 and not status_result.stdout.strip()
    if commit_result.returncode != 0 or len(commit) != 40:
        return {
            "schema_version": PUBLIC_PROVENANCE_SCHEMA_VERSION,
            "status": "blocked_source_provenance_unavailable",
            "commit": None,
            "working_tree_clean": clean,
        }
    if not clean:
        return {
            "schema_version": PUBLIC_PROVENANCE_SCHEMA_VERSION,
            "status": "blocked_dirty_worktree",
            "commit": commit,
            "working_tree_clean": False,
        }
    return {
        "schema_version": PUBLIC_PROVENANCE_SCHEMA_VERSION,
        "status": "verified",
        "commit": commit,
        "working_tree_clean": True,
        "implementation_and_documentation": "Gretel / Codex",
        "human_gate": "Julius remains human project lead and merge/release decision-maker.",
    }
