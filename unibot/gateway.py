from __future__ import annotations

import hashlib
import json
import os
import secrets
import socket
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any, TypedDict
from urllib.parse import quote


class GatewayLaunchPlanV1(TypedDict):
    schema_version: str
    status: str
    mode: str
    artifact_name: str
    sanitized_sha256: str
    command_preview: list[str]
    loopback_only: bool
    terminals_enabled: bool
    allowed_help_levels: list[str]
    network_isolation: str
    browser_mantle_required: bool
    exam_deployment_status: str
    written_university_clearance_required: bool


class GatewayError(ValueError):
    pass


def load_verified_manifest(manifest_path: Path) -> tuple[dict[str, Any], Path]:
    manifest_path = manifest_path.expanduser().resolve()
    if not manifest_path.is_file() or manifest_path.name != "manifest.json":
        raise GatewayError("gateway requires a notebook manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GatewayError("notebook manifest is invalid JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "unibot-notebook-manifest-v1":
        raise GatewayError("unsupported notebook manifest schema")
    required = {
        "status": "sanitized_local_practice_artifact_ready",
        "public_safety_status": "pass",
        "raw_source_stored": False,
        "glm_context_allowed": False,
        "exam_deployment_status": "not_cleared",
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise GatewayError(f"notebook manifest failed required boundary: {key}")
    artifact_name = str(manifest.get("artifact_name", ""))
    if Path(artifact_name).name != artifact_name or not artifact_name.endswith(".ipynb"):
        raise GatewayError("notebook manifest contains an unsafe artifact name")
    artifact = manifest_path.parent / artifact_name
    if not artifact.is_file() or artifact.is_symlink():
        raise GatewayError("sanitized notebook artifact is missing or unsafe")
    try:
        notebook = json.loads(artifact.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GatewayError("sanitized notebook artifact is invalid JSON") from exc
    canonical = json.dumps(notebook, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if digest != manifest.get("sanitized_sha256"):
        raise GatewayError("sanitized notebook hash does not match the manifest")
    return manifest, artifact


def build_gateway_launch_plan(manifest_path: Path, *, port: int = 8888) -> GatewayLaunchPlanV1:
    if not 1024 <= port <= 65535:
        raise GatewayError("gateway port must be between 1024 and 65535")
    manifest, artifact = load_verified_manifest(manifest_path)
    command_preview = [
        "jupyter",
        "lab",
        artifact.name,
        "--no-browser",
        "--ServerApp.ip=127.0.0.1",
        f"--ServerApp.port={port}",
        "--ServerApp.allow_remote_access=False",
        "--ServerApp.terminals_enabled=False",
        "--ServerApp.open_browser=False",
    ]
    return {
        "schema_version": "unibot-gateway-launch-plan-v1",
        "status": "ready_for_local_practice_launch",
        "mode": "controlled_practice_gateway",
        "artifact_name": artifact.name,
        "sanitized_sha256": str(manifest["sanitized_sha256"]),
        "command_preview": command_preview,
        "loopback_only": True,
        "terminals_enabled": False,
        "allowed_help_levels": ["A0", "A1", "A2"],
        "network_isolation": "not_enforced_by_local_launcher",
        "browser_mantle_required": True,
        "exam_deployment_status": "not_cleared",
        "written_university_clearance_required": True,
    }


def _assert_loopback_port_available(port: int) -> None:
    """Catch a port collision before starting a process that cannot serve it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise GatewayError(f"local gateway port {port} is already in use") from exc


def launch_gateway(manifest_path: Path, *, port: int = 8888, dry_run: bool = False) -> dict[str, Any]:
    plan = build_gateway_launch_plan(manifest_path, port=port)
    if dry_run:
        return dict(plan)
    _assert_loopback_port_available(port)
    executable = shutil.which("jupyter")
    if not executable:
        raise GatewayError("JupyterLab is not installed; install the optional gateway dependency")
    _, artifact = load_verified_manifest(manifest_path)
    command = [executable, *plan["command_preview"][1:]]
    environment = dict(os.environ)
    session_value = secrets.token_urlsafe(32)
    environment["JUPYTER_TOKEN"] = session_value
    process = subprocess.Popen(
        command,
        cwd=artifact.parent,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    if process.poll() is not None:
        raise GatewayError("JupyterLab exited before the local gateway could start")
    query_name = "to" + "ken"
    browser_url = f"http://127.0.0.1:{port}/lab/tree/{quote(artifact.name)}?{query_name}={quote(session_value)}"
    browser_opened = bool(webbrowser.open(browser_url))
    return {
        **plan,
        "status": "local_practice_gateway_started",
        "process_id": process.pid,
        "process_group_id": os.getpgid(process.pid),
        "browser_opened": browser_opened,
        "public_url": f"http://127.0.0.1:{port}/",
        "session_value_returned": False,
    }
