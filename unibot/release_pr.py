"""Build a public-safe, human-gated GitHub pull-request draft."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .public_safety import scan_text
from .release_audit import audit_release_candidate


RELEASE_PR_DRAFT_SCHEMA_VERSION = "UniBotReleasePrDraftV1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release_pr_draft(
    candidate_dir: str | Path,
    *,
    repository: str | Path | None = None,
) -> dict[str, Any]:
    """Create PR text only after the candidate's read-only audit passes."""
    candidate = Path(candidate_dir).expanduser()
    repo = Path(repository).expanduser() if repository is not None else Path(__file__).resolve().parents[1]
    audit = audit_release_candidate(candidate, repository=repo)
    if audit["status"] != "pass":
        return {
            "schema_version": RELEASE_PR_DRAFT_SCHEMA_VERSION,
            "artifact_type": "unibot_github_pull_request_draft",
            "status": "blocked",
            "reason": "release_candidate_audit_failed",
            "audit_status": audit["status"],
            "audit_issues": audit["issues"],
            "automatic_publication": False,
            "automatic_merge": False,
            "exam_deployment_status": "not_cleared",
        }

    manifest_path = candidate / "RELEASE-MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "schema_version": RELEASE_PR_DRAFT_SCHEMA_VERSION,
            "artifact_type": "unibot_github_pull_request_draft",
            "status": "blocked",
            "reason": "release_manifest_unreadable",
            "automatic_publication": False,
            "automatic_merge": False,
            "exam_deployment_status": "not_cleared",
        }

    title = "UniBot: public-safe local Socratic Chrome learning companion"
    source_commit = str(manifest.get("source_provenance", {}).get("commit", ""))
    extension_hash = str(manifest.get("extension_package_sha256", ""))
    evidence_hash = str(manifest.get("institutional_evidence_hash", ""))
    manifest_hash = _sha256_file(manifest_path)
    body = "\n".join(
        [
            "## Zweck",
            "",
            "Diese Entwurfs-PR bringt UniBot als lokale, sokratische Lern- und Übungshilfe für Python-Notebooks zur menschlichen öffentlichen Prüfung.",
            "Die Chrome-MV3-Erweiterung arbeitet mit dem lokalen Companion und Native Messaging. Der Tutor führt Notebookcode nicht aus und gibt keine fertige Lösung, Endwerte oder fertige Interpretation aus.",
            "",
            "## Transparente Rollen",
            "",
            "- Implementierung und Dokumentation: Gretel / Codex.",
            "- GLM-5.2: in dieser Version geparkt; 0 Provideraufrufe und 0 Kosten.",
            "- Menschliche Entscheidung: Julius prüft den finalen Diff und entscheidet über Merge und Veröffentlichung.",
            "",
            "## Nachweise",
            "",
            f"- Basis-Commit: `{source_commit}`",
            f"- Release-Manifest-SHA-256: `{manifest_hash}`",
            f"- MV3-Paket-SHA-256: `{extension_hash}`",
            f"- Institutioneller Evidenz-Hash: `{evidence_hash}`",
            "- Public-Safety-Scan: bestanden; keine privaten Dateien, Pfade, Schlüssel oder Lerninhalte enthalten.",
            "- Release-Audit: bestanden; keine Netzwerk-, Provider-, Git- oder automatischen Merge-Effekte.",
            "",
            "## Prüfungen",
            "",
            "- `python3 -m pytest -q`",
            "- `npm run test:browser`",
            "- `npm run test:extension-package`",
            "- `UNIBOT_CHROME_EXECUTABLE=... npm run test:chrome-canary`",
            "- `python3 -m unibot.cli public-safety`",
            "- `unibot release audit ...`",
            "",
            "## Menschliche Gates",
            "",
            "- [ ] GitHub-CI ist nach dem letzten Bot-Push grün.",
            "- [ ] Julius hat den vollständigen Diff geprüft.",
            "- [ ] Diskussionen und Sicherheitsbefunde sind aufgelöst.",
            "- [ ] Institutionelle Prüfung durch Lehre, Inklusion, Datenschutz und IT ist vorbereitet.",
            "- [ ] Prüfungseinsatz bleibt ausdrücklich `not_cleared`.",
            "",
            "## Grenzen",
            "",
            "UniBot ist kein Prüfer, kein Notengeber, kein Proctoring-System, kein KI-Detektor und keine automatische Nachteilsausgleich-Entscheidung. Diese PR beantragt keine Prüfungs- oder Rechtsfreigabe.",
            "",
            "## Merge-Regel",
            "",
            "Kein Bot merged diese PR. Nur die menschliche Projektleitung darf sie nach dem letzten Bot-Push prüfen und zusammenführen.",
        ]
    ) + "\n"
    scan = scan_text(body, "github-pull-request-draft")
    if scan["status"] != "pass":
        return {
            "schema_version": RELEASE_PR_DRAFT_SCHEMA_VERSION,
            "artifact_type": "unibot_github_pull_request_draft",
            "status": "blocked",
            "reason": "pull_request_draft_public_safety_failed",
            "finding_count": len(scan["findings"]),
            "automatic_publication": False,
            "automatic_merge": False,
            "exam_deployment_status": "not_cleared",
        }
    return {
        "schema_version": RELEASE_PR_DRAFT_SCHEMA_VERSION,
        "artifact_type": "unibot_github_pull_request_draft",
        "status": "ready_for_human_review",
        "title": title,
        "labels": ["gretel-review", "draft"],
        "body": body,
        "source_commit": source_commit,
        "release_manifest_sha256": manifest_hash,
        "extension_package_sha256": extension_hash,
        "institutional_evidence_hash": evidence_hash,
        "audit_status": audit["status"],
        "public_safety_status": scan["status"],
        "provider_calls": 0,
        "automatic_publication": False,
        "automatic_merge": False,
        "exam_deployment_status": "not_cleared",
        "human_release_gate": "Julius remains the human merge and publication decision-maker.",
    }


def write_release_pr_draft(
    output_path: str | Path,
    candidate_dir: str | Path,
    *,
    repository: str | Path | None = None,
) -> dict[str, Any]:
    """Write a new, owner-readable PR body without overwriting existing files."""
    output = Path(output_path).expanduser()
    if output.is_symlink() or output.exists():
        raise ValueError("pull request draft output must be a new file")
    draft = build_release_pr_draft(candidate_dir, repository=repository)
    if draft["status"] != "ready_for_human_review":
        return draft
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(draft["body"], encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, output)
        os.chmod(output, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        key: value
        for key, value in {
            **draft,
            "output_file_name": output.name,
            "output_bytes": output.stat().st_size,
            "output_sha256": _sha256_file(output),
        }.items()
        if key != "body"
    }
