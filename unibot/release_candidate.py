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
from .public_demo import build_public_demo_evidence, build_public_demo_markdown
from .public_safety import scan_text
from .provenance import public_source_provenance


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


def _review_start_here_markdown(source_commit: str) -> str:
    return "\n".join(
        [
            "# UniBot: Hier anfangen",
            "",
            "**Status: öffentlicher Entwurf für menschliche Prüfung; keine Prüfungs- oder Rechtsfreigabe.**",
            "",
            "Diese Seite ist der kurze Einstieg für Prüfungsamt, Inklusionsbüro, Datenschutz, IT/SZI, Lehre und Thesis-Betreuung.",
            "UniBot ist eine lokale sokratische Lern- und Übungshilfe für Python-Notebooks. Die Implementierung und Dokumentation stammen von Gretel / Codex.",
            "GLM ist in dieser Version geparkt und hatte keinen Anteil.",
            "",
            "## In 15 Minuten zeigen",
            "",
            "1. Öffne `PUBLIC-DEMO.md` und verwende ausschließlich `synthetic_python_practice.ipynb`.",
            "2. Zeige im Chrome-Seitenpanel die Auswahl einer synthetischen Zelle und die Hilfe A0 bis A4.",
            "3. Zeige, dass der Tutor keine fertige Lösung, keinen Endwert und keinen ausgeführten Notebookcode liefert.",
            "4. Öffne danach den `institutional-plain-language-brief.md` und den `institutional-accessibility-walkthrough.md`.",
            "",
            "## Was geprüft werden kann",
            "",
            "- `unibot-mantle.zip`: die öffentliche MV3-Erweiterung für den lokalen Übungsbetrieb.",
            "- `RELEASE-MANIFEST.json`: Commit, Größen und SHA-256-Nachweise aller Dateien.",
            "- `institutional-presentation.md`: Gesamtpaket für die Review-Sitzung.",
            "- `institutional-accessibility-walkthrough.md`: acht menschlich zu bewertende Barrierefreiheitsprüfungen.",
            "- `institutional-review-decision-template.md`: absichtlich leer; es kann keine Freigabe automatisch erzeugen.",
            "",
            "## Drei Golden Rules",
            "",
            "- Keine finale Lösung: vollständiger Aufgabencode, Endwerte und fertige Interpretationen werden blockiert.",
            "- Keine privaten Daten: keine Notebookinhalte, Namen, Gesundheitsdaten, lokalen Pfade, Schlüssel oder Providerdaten im öffentlichen Paket.",
            "- Eigenleistung sichtbar halten: eigene Versuche, Hilfestufe, Quellen und Reflexion bleiben getrennt von einer Bewertung.",
            "",
            "## Inklusion",
            "",
            "Barrierefreie Unterstützung ist score-neutral. UniBot entscheidet keinen Nachteilsausgleich, keine Diagnose und keinen offiziellen Unterstützungsstatus.",
            "Tastaturbedienung, sichtbarer Fokus, Statusansagen, kleine Fenster und 200-Prozent-Zoom sind technisch getestet; eine rechtliche Konformitätsentscheidung bleibt menschlich.",
            "",
            "## Menschliche Entscheidungen",
            "",
            "- Passt der lokale Übungszweck zum konkreten Modul und zur Zielgruppe?",
            "- Welche Daten dürfen lokal verarbeitet und wie lange aufbewahrt werden?",
            "- Welche Zugänglichkeits- und Unterstützungsfunktionen sind institutionell angemessen?",
            "- Welche schriftliche Entscheidung wäre für einen separaten Prüfungseinsatz erforderlich?",
            "- Julius prüft den finalen Diff und entscheidet allein über GitHub-Merge und Veröffentlichung.",
            "",
            "## Unveränderliche Grenze",
            "",
            "`exam_deployment_status = not_cleared`. UniBot ist kein Prüfer, kein Notengeber, kein Proctoring-System, kein KI-Detektor und keine automatische Nachteilsausgleich-Entscheidung.",
            "",
            f"Technische Basis dieses Pakets: `{source_commit}`.",
            "",
        ]
    )


def _git_provenance() -> dict[str, Any]:
    """Bind a release candidate to a clean public source revision."""
    return public_source_provenance()


def write_release_candidate_bundle(output_dir: str | Path) -> dict[str, Any]:
    """Write a public-safe review handoff without the repository checkout."""
    root = Path(output_dir).expanduser()
    if root.is_symlink() or root.exists():
        raise ValueError("release candidate output must be a new directory")
    root.parent.mkdir(parents=True, exist_ok=True)
    provenance = _git_provenance()
    if provenance["status"] != "verified":
        return {
            "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
            "artifact_type": "unibot_release_candidate_bundle",
            "status": "blocked",
            "reason": str(provenance["status"]),
            "source_provenance": provenance,
            "exam_deployment_status": "not_cleared",
        }

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

            repository_root = Path(__file__).resolve().parents[1]
            demo_fixture_source = repository_root / "fixtures" / "public" / "synthetic_python_practice.ipynb"
            if demo_fixture_source.is_symlink() or not demo_fixture_source.is_file():
                return {
                    "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                    "artifact_type": "unibot_release_candidate_bundle",
                    "status": "blocked",
                    "reason": "demo_fixture_missing_or_unsafe",
                    "exam_deployment_status": "not_cleared",
                }
            demo_fixture_path = staging / "synthetic_python_practice.ipynb"
            try:
                shutil.copy2(demo_fixture_source, demo_fixture_path)
                os.chmod(demo_fixture_path, 0o600)
                demo_fixture_safety = _scan_text_file(demo_fixture_path, demo_fixture_path.name)
            except (OSError, UnicodeDecodeError):
                return {
                    "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                    "artifact_type": "unibot_release_candidate_bundle",
                    "status": "blocked",
                    "reason": "demo_fixture_unreadable",
                    "exam_deployment_status": "not_cleared",
                }
            if demo_fixture_safety != "pass":
                return {
                    "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                    "artifact_type": "unibot_release_candidate_bundle",
                    "status": "blocked",
                    "reason": "demo_fixture_public_safety_failed",
                    "exam_deployment_status": "not_cleared",
                }
            records.append(_file_record(demo_fixture_path, demo_fixture_path.name, public_safety_status=demo_fixture_safety))

            demo_result = build_public_demo_evidence()
            if demo_result.get("status") != "ready_for_human_demo" or demo_result.get("public_safety_status") != "pass":
                return {
                    "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                    "artifact_type": "unibot_release_candidate_bundle",
                    "status": "blocked",
                    "reason": "public_demo_evidence_blocked",
                    "exam_deployment_status": "not_cleared",
                }
            demo_path = staging / "PUBLIC-DEMO.md"
            demo_path.write_text(build_public_demo_markdown(demo_result), encoding="utf-8")
            os.chmod(demo_path, 0o600)
            demo_safety = _scan_text_file(demo_path, demo_path.name)
            if demo_safety != "pass":
                return {
                    "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                    "artifact_type": "unibot_release_candidate_bundle",
                    "status": "blocked",
                    "reason": "public_demo_markdown_safety_failed",
                    "exam_deployment_status": "not_cleared",
                }
            records.append(_file_record(demo_path, demo_path.name, public_safety_status=demo_safety))

            review_start_path = staging / "REVIEW-START-HERE.md"
            review_start_path.write_text(
                _review_start_here_markdown(str(provenance["commit"])),
                encoding="utf-8",
            )
            os.chmod(review_start_path, 0o600)
            review_start_safety = _scan_text_file(review_start_path, review_start_path.name)
            if review_start_safety != "pass":
                return {
                    "schema_version": RELEASE_CANDIDATE_SCHEMA_VERSION,
                    "artifact_type": "unibot_release_candidate_bundle",
                    "status": "blocked",
                    "reason": "review_start_here_public_safety_failed",
                    "exam_deployment_status": "not_cleared",
                }
            records.append(_file_record(review_start_path, review_start_path.name, public_safety_status=review_start_safety))

            institutional_names = {
                "institutional-presentation.json": "institutional-presentation.json",
                "institutional-presentation.md": "institutional-presentation.md",
                "institutional-plain-language-brief.md": "institutional-plain-language-brief.md",
                "institutional-accessibility-walkthrough.md": "institutional-accessibility-walkthrough.md",
                "institutional-review-decision-template.md": "institutional-review-decision-template.md",
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
            "demo_fixture_sha256": _sha256_file(demo_fixture_path),
            "public_demo_markdown_sha256": _sha256_file(demo_path),
            "institutional_evidence_hash": institutional_result["evidence_hash"],
            "public_safety_status": "pass",
            "provider_calls": 0,
            "learner_content_included": False,
            "private_project_files_included": False,
            "automatic_publication": False,
            "automatic_merge": False,
            "source_provenance": provenance,
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
            "demo_fixture_sha256": _sha256_file(root / "synthetic_python_practice.ipynb"),
            "public_demo_markdown_sha256": _sha256_file(root / "PUBLIC-DEMO.md"),
            "institutional_evidence_hash": institutional_result["evidence_hash"],
            "public_safety_status": "pass",
            "provider_calls": 0,
            "learner_content_included": False,
            "private_project_files_included": False,
            "exam_deployment_status": "not_cleared",
            "automatic_publication": False,
            "automatic_merge": False,
            "source_commit": provenance["commit"],
            "source_provenance_status": provenance["status"],
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _scan_text_file_from_content(content: str, name: str) -> str:
    scan = scan_text(content, name)
    return str(scan["status"])
