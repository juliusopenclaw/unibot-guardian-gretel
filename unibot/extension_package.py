from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path
from typing import Any

from .companion import DEFAULT_EXTENSION_ID
from .public_safety import scan_text


EXTENSION_PACKAGE_SCHEMA_VERSION = "UniBotExtensionPackageV1"
EXTENSION_ROOT = Path(__file__).resolve().parent / "browser_extension"
TEXT_SUFFIXES = {".css", ".html", ".js", ".json"}


def _manifest_files(manifest: dict[str, Any]) -> set[str]:
    required = {"manifest.json"}
    background = manifest.get("background")
    if isinstance(background, dict) and isinstance(background.get("service_worker"), str):
        required.add(background["service_worker"])
    side_panel = manifest.get("side_panel")
    if isinstance(side_panel, dict) and isinstance(side_panel.get("default_path"), str):
        required.add(side_panel["default_path"])
    content_scripts = manifest.get("content_scripts", [])
    if isinstance(content_scripts, list):
        for entry in content_scripts:
            if isinstance(entry, dict) and isinstance(entry.get("js"), list):
                required.update(item for item in entry["js"] if isinstance(item, str))
    return required


def package_extension(
    output_path: str | Path,
    *,
    source_root: str | Path = EXTENSION_ROOT,
) -> dict[str, Any]:
    """Create a deterministic, public-safe MV3 package without private project files."""
    root = Path(source_root).expanduser()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("extension source must be a real directory")
    manifest_path = root / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("extension manifest is missing or unsafe")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("extension manifest is not valid JSON") from error
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 3:
        raise ValueError("only Manifest V3 extensions can be packaged")
    side_panel = manifest.get("side_panel")
    if manifest.get("key") is None or not isinstance(side_panel, dict) or side_panel.get("default_path") is None:
        raise ValueError("fixed public extension identity or side panel is missing")
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("extension source contains a symlink")
        if path.is_file():
            if path.suffix.lower() not in TEXT_SUFFIXES:
                raise ValueError("extension contains an unsupported file type")
            files.append(path)
    relative_names = {path.relative_to(root).as_posix() for path in files}
    missing = sorted(_manifest_files(manifest) - relative_names)
    if missing:
        raise ValueError(f"extension manifest references missing files: {', '.join(missing)}")
    findings: list[dict[str, Any]] = []
    for path in files:
        scan = scan_text(path.read_text(encoding="utf-8"), path.relative_to(root).as_posix())
        findings.extend(scan["findings"])
    if findings:
        return {
            "schema_version": EXTENSION_PACKAGE_SCHEMA_VERSION,
            "artifact_type": "unibot_mv3_extension_package",
            "status": "blocked",
            "reason": "extension_public_safety_scan_failed",
            "finding_count": len(findings),
            "public_safety_status": "blocked",
            "exam_deployment_status": "not_cleared",
        }
    output = Path(output_path).expanduser()
    if output.is_symlink() or (output.exists() and not output.is_file()):
        raise ValueError("extension package output must be a regular file")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                relative_name = path.relative_to(root).as_posix()
                info = zipfile.ZipInfo(relative_name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100600 << 16
                archive.writestr(info, path.read_bytes())
        os.replace(temporary, output)
        os.chmod(output, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()
    package_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    return {
        "schema_version": EXTENSION_PACKAGE_SCHEMA_VERSION,
        "artifact_type": "unibot_mv3_extension_package",
        "status": "written",
        "extension_id": DEFAULT_EXTENSION_ID,
        "manifest_version": 3,
        "file_names": sorted(relative_names),
        "file_count": len(files),
        "package_sha256": package_hash,
        "public_safety_status": "pass",
        "learner_content_included": False,
        "private_project_files_included": False,
        "exam_deployment_status": "not_cleared",
        "human_release_gates": ["Google Chrome canary", "human publication review"],
    }
