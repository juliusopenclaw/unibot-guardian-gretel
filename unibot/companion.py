from __future__ import annotations

import json
import os
import hashlib
import shlex
import shutil
import signal
import secrets
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, BinaryIO, cast

from .gateway import launch_gateway
from .learning_session import (
    HELP_LEVELS_V1,
    LearningSession,
    SESSION_RETENTION_DAYS,
    active_session_metadata,
    cleanup_expired_sessions,
    delete_session_artifacts,
    register_session_notebook,
    session_notebook_ids,
)
from .notebook_intake import import_notebook
from .socratic_tutor import TutorTurnRequestV1, build_tutor_turn


NATIVE_HOST_NAME = "de.gretel.unibot_companion"
DEFAULT_EXTENSION_ID = "cmbjhndgjhgpopcflkjoalmpfjhoiana"
MAX_NATIVE_MESSAGE_BYTES = 64 * 1024
APPLICATION_SUPPORT = Path.home() / "Library" / "Application Support" / "UniBot Companion"
CHROME_NATIVE_HOSTS = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"
CHROMIUM_NATIVE_HOSTS = Path.home() / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts"
DEFAULT_APP_PATH = Path.home() / "Applications" / "UniBot Companion.app"
NOTEBOOK_RETENTION_HOURS = 24
GATEWAY_STATE_SCHEMA_VERSION = "unibot-gateway-state-v1"
RUNTIME_DIRECTORY_NAME = "runtime"


def cleanup_expired_notebooks(
    notebook_root: Path,
    *,
    retention_hours: int = NOTEBOOK_RETENTION_HOURS,
    active_notebook_ids: set[str] | frozenset[str] = frozenset(),
) -> list[str]:
    """Delete old sanitized notebook directories without following symlinks."""
    if not notebook_root.exists():
        return []
    if notebook_root.is_symlink() or not notebook_root.is_dir():
        raise ValueError("notebook storage root is missing or symlinked")
    cutoff = time.time() - (retention_hours * 60 * 60)
    removed: list[str] = []
    for child in sorted(notebook_root.iterdir()):
        if child.is_symlink() or not child.is_dir():
            continue
        if child.name in active_notebook_ids:
            continue
        manifest = child / "manifest.json"
        if manifest.is_symlink():
            raise ValueError("refusing to clean symlinked notebook manifest")
        if manifest.is_file() and manifest.stat().st_mtime < cutoff:
            shutil.rmtree(child)
            removed.append(child.name)
    return removed


def _write_gateway_state(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_gateway_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
        raise ValueError("gateway state permissions are invalid")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != GATEWAY_STATE_SCHEMA_VERSION:
        raise ValueError("unsupported gateway state")
    return payload


class CompanionRuntime:
    def __init__(self, *, storage_root: Path | None = None) -> None:
        configured_storage_root = storage_root or APPLICATION_SUPPORT / "sessions"
        self.storage_root = configured_storage_root.expanduser()
        if self.storage_root.is_symlink():
            raise ValueError("session storage root must not be a symlink")
        self.storage_root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.storage_root, 0o700)
        self.expired_sessions = cleanup_expired_sessions(self.storage_root, retention_days=SESSION_RETENTION_DAYS)
        self.gateway_state_path = self.storage_root / "gateway.state.json"
        self.notebook_root = (
            APPLICATION_SUPPORT / "notebooks"
            if storage_root is None
            else self.storage_root.parent / "notebooks"
        ).expanduser()
        self.notebook_root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.notebook_root, 0o700)
        active_gateway = self._reconcile_gateway_state()
        self.expired_notebooks = cleanup_expired_notebooks(
            self.notebook_root,
            active_notebook_ids={str(active_gateway["notebook_id"])} if active_gateway else frozenset(),
        )
        self.session: LearningSession | None = None
        self.notebook_manifests: dict[str, Path] = {}

    @staticmethod
    def _process_alive(state: dict[str, Any]) -> bool:
        try:
            process_id = int(state["process_id"])
            process_group_id = int(state["process_group_id"])
            if process_id <= 0 or process_group_id <= 0 or process_group_id == os.getpgrp():
                return False
            if os.getpgid(process_id) != process_group_id:
                return False
            os.kill(process_id, 0)
        except (KeyError, OSError, TypeError, ValueError):
            return False
        return True

    def _mark_gateway_ended(self, state: dict[str, Any]) -> None:
        notebook_id = str(state.get("notebook_id", ""))
        if len(notebook_id) != 16 or any(character not in "0123456789abcdef" for character in notebook_id):
            return
        manifest = self.notebook_root / notebook_id / "manifest.json"
        if manifest.is_symlink():
            raise ValueError("refusing to touch symlinked notebook manifest")
        if manifest.is_file():
            os.utime(manifest, None)

    def _reconcile_gateway_state(self) -> dict[str, Any] | None:
        state = _read_gateway_state(self.gateway_state_path)
        if state is None:
            return None
        if self._process_alive(state):
            return state
        self._mark_gateway_ended(state)
        self.gateway_state_path.unlink(missing_ok=True)
        return None

    def _stop_gateway_state(self, state: dict[str, Any]) -> bool:
        stopped = False
        if self._process_alive(state):
            process_group_id = int(state["process_group_id"])
            os.killpg(process_group_id, signal.SIGTERM)
            deadline = time.time() + 2
            while time.time() < deadline and self._process_alive(state):
                time.sleep(0.05)
            if self._process_alive(state):
                os.killpg(process_group_id, signal.SIGKILL)
            stopped = True
        self._mark_gateway_ended(state)
        self.gateway_state_path.unlink(missing_ok=True)
        return stopped

    def handle(self, message: dict[str, Any]) -> dict[str, Any]:
        request_id = str(message.get("request_id", ""))
        message_type = str(message.get("type", ""))
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            return self._response(request_id, "invalid-payload", error="payload must be an object")
        try:
            if message_type == "companion.status":
                active = active_session_metadata(self.storage_root)
                if len(active) > 1:
                    return self._response(
                        request_id,
                        "blocked",
                        error="Multiple active sessions require an explicit session_id.",
                        resume_available=False,
                        active_session_count=len(active),
                    )
                return self._response(
                    request_id,
                    "ready",
                    native_transport=True,
                    session_active=bool(self.session and not self.session.stopped) or bool(active),
                    resume_available=bool(active),
                    active_session_metadata=active[0] if active else None,
                    allowed_help_levels=list(HELP_LEVELS_V1),
                    exam_deployment_status="not_cleared",
                )
            if message_type == "gateway.status":
                gateway = self._reconcile_gateway_state()
                return self._response(
                    request_id,
                    "active" if gateway else "stopped",
                    gateway={
                        "notebook_id": str(gateway["notebook_id"]),
                        "process_id": int(gateway["process_id"]),
                        "port": int(gateway["port"]),
                    }
                    if gateway
                    else None,
                )
            if message_type == "session.start":
                if active_session_metadata(self.storage_root):
                    return self._response(
                        request_id,
                        "session-exists",
                        error="An active learning session exists; resume or delete it first.",
                    )
                self.session = LearningSession.start(payload, storage_root=self.storage_root)
                for notebook_id in self.notebook_manifests:
                    register_session_notebook(self.storage_root, self.session.contract["session_id"], notebook_id)
                return self._response(request_id, "active", contract=self.session.contract)
            if message_type == "session.resume":
                session_id = str(payload.get("session_id", "")).strip() or None
                self.session = LearningSession.resume(self.storage_root, session_id=session_id)
                return self._response(
                    request_id,
                    "active",
                    resumed=True,
                    contract=self.session.contract,
                    report=self.session.report(),
                )
            if message_type == "tutor.turn":
                if self.session is None or self.session.stopped:
                    return self._response(request_id, "session-required", error="Start the learning session first.")
                request_payload = dict(payload)
                explicit_task_id = str(request_payload.get("task_id", "")).strip()
                if explicit_task_id:
                    request_payload["task_id"] = hashlib.sha256(explicit_task_id.encode("utf-8")).hexdigest()[:16]
                request = cast(TutorTurnRequestV1, request_payload)
                return self._response(request_id, "ok", turn=build_tutor_turn(self.session, request))
            if message_type == "session.report":
                if self.session is None:
                    return self._response(request_id, "session-required", error="Start the learning session first.")
                return self._response(request_id, "ok", report=self.session.report())
            if message_type == "session.stop":
                if self.session is None:
                    return self._response(request_id, "session-required", error="Start the learning session first.")
                stopped = self.session.stop()
                return self._response(
                    request_id,
                    "stopped",
                    session_id=stopped["session_id"],
                    report=stopped["report"],
                )
            if message_type == "session.delete":
                session_id = str(payload.get("session_id", "")).strip()
                if not session_id and self.session is not None:
                    session_id = self.session.contract["session_id"]
                if not session_id:
                    return self._response(request_id, "not-found", error="No learning session is selected.")
                notebook_ids = session_notebook_ids(self.storage_root, session_id)
                gateway = self._reconcile_gateway_state()
                if gateway and str(gateway.get("notebook_id")) in notebook_ids:
                    self._stop_gateway_state(gateway)
                deleted = delete_session_artifacts(self.storage_root, session_id)
                for notebook_id in notebook_ids:
                    notebook_path = (self.notebook_root / notebook_id).resolve()
                    if notebook_path.parent != self.notebook_root.resolve():
                        raise ValueError("notebook path escaped local storage")
                    if notebook_path.is_symlink():
                        raise ValueError("refusing to delete symlinked notebook artifact")
                    if notebook_path.is_dir():
                        shutil.rmtree(notebook_path)
                self.notebook_manifests.clear()
                if self.session is not None and self.session.contract["session_id"] == session_id:
                    self.session = None
                return self._response(request_id, "deleted" if deleted else "not-found", session_id=session_id)
            if message_type == "notebook.import":
                source = str(payload.get("source", "")).strip()
                if not source:
                    source = choose_local_notebook()
                if not source:
                    return self._response(request_id, "cancelled", error="Notebook selection was cancelled.")
                manifest = import_notebook(source, self.notebook_root)
                notebook_id = str(manifest["sanitized_sha256"])[:16]
                self.notebook_manifests[notebook_id] = self.notebook_root / notebook_id / "manifest.json"
                if self.session is not None and not self.session.stopped:
                    register_session_notebook(self.storage_root, self.session.contract["session_id"], notebook_id)
                return self._response(request_id, "ok", notebook_id=notebook_id, manifest=dict(manifest))
            if message_type == "gateway.launch":
                notebook_id = str(payload.get("notebook_id", ""))
                manifest_path = self.notebook_manifests.get(notebook_id)
                if manifest_path is None:
                    return self._response(request_id, "notebook-required", error="Import a notebook first.")
                if self.session is not None and not self.session.stopped:
                    register_session_notebook(self.storage_root, self.session.contract["session_id"], notebook_id)
                port = int(payload.get("port") or available_loopback_port())
                existing_gateway = self._reconcile_gateway_state()
                if existing_gateway:
                    return self._response(
                        request_id,
                        "gateway-exists",
                        error="A local Jupyter gateway is already active; stop it first.",
                    )
                result = launch_gateway(manifest_path, port=port, dry_run=bool(payload.get("dry_run", False)))
                if not bool(payload.get("dry_run", False)):
                    process_id = int(result.get("process_id", 0))
                    _write_gateway_state(
                        self.gateway_state_path,
                        {
                            "schema_version": GATEWAY_STATE_SCHEMA_VERSION,
                            "notebook_id": notebook_id,
                            "process_id": process_id,
                            "process_group_id": int(result.get("process_group_id", process_id)),
                            "port": port,
                            "started_at_utc": time.time(),
                        },
                    )
                return self._response(request_id, "ok", gateway=result)
            if message_type == "gateway.stop":
                gateway = self._reconcile_gateway_state()
                if gateway is None:
                    return self._response(request_id, "not-found", error="Kein lokales Jupyter-Gateway aktiv.")
                stopped = self._stop_gateway_state(gateway)
                return self._response(request_id, "stopped", process_was_running=stopped)
            return self._response(request_id, "unknown-message", error="Unsupported companion message type.")
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return self._response(request_id, "blocked", error=str(exc))

    @staticmethod
    def _response(request_id: str, status: str, **payload: Any) -> dict[str, Any]:
        return {
            "schema_version": "unibot-companion-message-v1",
            "request_id": request_id,
            "status": status,
            **payload,
        }


def read_native_message(stream: BinaryIO) -> dict[str, Any] | None:
    raw_length = stream.read(4)
    if not raw_length:
        return None
    if len(raw_length) != 4:
        raise ValueError("invalid native message length prefix")
    length = struct.unpack("<I", raw_length)[0]
    if length <= 0 or length > MAX_NATIVE_MESSAGE_BYTES:
        raise ValueError("native message exceeds size boundary")
    raw_message = stream.read(length)
    if len(raw_message) != length:
        raise ValueError("incomplete native message")
    payload = json.loads(raw_message.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("native message must be a JSON object")
    return payload


def write_native_message(stream: BinaryIO, payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_NATIVE_MESSAGE_BYTES:
        encoded = json.dumps(
            {
                "schema_version": "unibot-companion-message-v1",
                "status": "blocked",
                "error": "native response exceeds size boundary",
            },
            separators=(",", ":"),
        ).encode("utf-8")
    stream.write(struct.pack("<I", len(encoded)))
    stream.write(encoded)
    stream.flush()


def choose_local_notebook() -> str:
    script = 'POSIX path of (choose file with prompt "Python-Notebook auswaehlen")'
    result = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def available_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def run_native_host(stdin: BinaryIO | None = None, stdout: BinaryIO | None = None) -> int:
    input_stream = stdin or sys.stdin.buffer
    output_stream = stdout or sys.stdout.buffer
    runtime = CompanionRuntime()
    while True:
        try:
            message = read_native_message(input_stream)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            write_native_message(output_stream, {"status": "blocked", "error": str(exc)})
            return 2
        if message is None:
            return 0
        write_native_message(output_stream, runtime.handle(message))


def _runtime_root() -> Path:
    return APPLICATION_SUPPORT / RUNTIME_DIRECTORY_NAME


def _reject_runtime_symlinks(source_root: Path) -> None:
    if source_root.is_symlink():
        raise ValueError("UniBot runtime source must not be a symlink")
    for path in source_root.rglob("*"):
        if path.is_symlink():
            raise ValueError("UniBot runtime source contains a symlink")


def _set_runtime_permissions(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            raise ValueError("installed UniBot runtime contains a symlink")
        if path.is_dir():
            os.chmod(path, 0o700)
        else:
            os.chmod(path, 0o600)
    os.chmod(root, 0o700)


def install_runtime(runtime_root: Path | None = None) -> Path:
    """Copy the public UniBot package into a source-independent local runtime."""
    target = (runtime_root or _runtime_root()).expanduser()
    source_root = Path(__file__).resolve().parents[1] / "unibot"
    source_exam_mode = source_root.parent / "exam_mode.py"
    if not source_root.is_dir():
        raise ValueError("UniBot runtime source package is missing")
    if not source_exam_mode.is_file() or source_exam_mode.is_symlink():
        raise ValueError("UniBot runtime exam-mode module is missing or unsafe")
    _reject_runtime_symlinks(source_root)
    if target.exists() and target.is_symlink():
        raise ValueError("installed UniBot runtime must not be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(target.parent, 0o700)
    staging = target.parent / f".{target.name}.staging-{os.getpid()}-{secrets.token_hex(6)}"
    backup = target.parent / f".{target.name}.previous-{os.getpid()}-{secrets.token_hex(6)}"
    try:
        shutil.copytree(
            source_root,
            staging / "unibot",
            symlinks=False,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        shutil.copy2(source_exam_mode, staging / "exam_mode.py")
        _set_runtime_permissions(staging)
        if target.exists():
            os.replace(target, backup)
        os.replace(staging, target)
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists():
            shutil.rmtree(backup)
    return target


def _python_launcher(command: str, runtime_root: Path | None = None) -> str:
    python = shlex.quote(sys.executable)
    package_root = shlex.quote(str(runtime_root or _runtime_root()))
    return f"#!/bin/zsh\nexport PYTHONPATH={package_root}\nexec {python} -m unibot.companion {command}\n"


def install_native_host(
    extension_id: str = DEFAULT_EXTENSION_ID,
    *,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    if len(extension_id) != 32 or any(character not in "abcdefghijklmnop" for character in extension_id):
        raise ValueError("extension ID must be a 32-character Chrome extension ID")
    installed_runtime = install_runtime(runtime_root)
    bin_root = APPLICATION_SUPPORT / "bin"
    bin_root.mkdir(parents=True, exist_ok=True)
    os.chmod(APPLICATION_SUPPORT, 0o700)
    os.chmod(bin_root, 0o700)
    launcher = bin_root / "unibot-native-host"
    launcher.write_text(_python_launcher("native-host", installed_runtime), encoding="utf-8")
    os.chmod(launcher, 0o700)
    manifest = {
        "name": NATIVE_HOST_NAME,
        "description": "Local-only UniBot Socratic tutor companion",
        "path": str(launcher),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id}/"],
    }
    for host_root in (CHROME_NATIVE_HOSTS, CHROMIUM_NATIVE_HOSTS):
        host_root.mkdir(parents=True, exist_ok=True)
        manifest_path = host_root / f"{NATIVE_HOST_NAME}.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        os.chmod(manifest_path, 0o600)
    return {
        "status": "installed",
        "native_host_name": NATIVE_HOST_NAME,
        "extension_id": extension_id,
        "manifest_present": True,
        "browser_manifests": ["Google Chrome", "Chromium"],
        "launcher_present": True,
        "runtime_package_copied": True,
    }


def install_companion_app(
    app_path: Path = DEFAULT_APP_PATH,
    *,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    installed_runtime = install_runtime(runtime_root)
    executable_root = app_path / "Contents" / "MacOS"
    executable_root.mkdir(parents=True, exist_ok=True)
    info_plist = app_path / "Contents" / "Info.plist"
    info_plist.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleDisplayName</key><string>UniBot Companion</string>
<key>CFBundleExecutable</key><string>UniBot Companion</string>
<key>CFBundleIdentifier</key><string>de.gretel.unibot-companion</string>
<key>CFBundleName</key><string>UniBot Companion</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.3.0</string>
<key>LSMinimumSystemVersion</key><string>13.0</string>
</dict></plist>
""",
        encoding="utf-8",
    )
    executable = executable_root / "UniBot Companion"
    executable.write_text(_python_launcher("menu", installed_runtime), encoding="utf-8")
    os.chmod(executable, 0o700)
    signature_status = "unsigned"
    codesign = subprocess.run(
        ["/usr/bin/codesign", "--force", "--deep", "--sign", "-", str(app_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if codesign.returncode == 0:
        signature_status = "ad_hoc_signed"
    return {
        "status": "installed",
        "app_present": True,
        "signature_status": signature_status,
        "runtime_package_copied": True,
    }


def install_companion(extension_id: str = DEFAULT_EXTENSION_ID) -> dict[str, Any]:
    installed_runtime = install_runtime()
    return {
        "schema_version": "unibot-companion-install-v1",
        "status": "installed",
        "native_host": install_native_host(extension_id, runtime_root=installed_runtime),
        "app": install_companion_app(runtime_root=installed_runtime),
        "runtime_mode": "source_independent_package_copy_current_interpreter",
        "exam_deployment_status": "not_cleared",
    }


def companion_status(extension_id: str = DEFAULT_EXTENSION_ID) -> dict[str, Any]:
    chrome_manifest = CHROME_NATIVE_HOSTS / f"{NATIVE_HOST_NAME}.json"
    chromium_manifest = CHROMIUM_NATIVE_HOSTS / f"{NATIVE_HOST_NAME}.json"
    manifests_ready = chrome_manifest.is_file() and chromium_manifest.is_file()
    runtime_ready = (_runtime_root() / "unibot" / "companion.py").is_file()
    return {
        "schema_version": "unibot-companion-status-v1",
        "status": "ready" if manifests_ready and DEFAULT_APP_PATH.is_dir() and runtime_ready else "not_installed",
        "native_host_installed": manifests_ready,
        "app_installed": DEFAULT_APP_PATH.is_dir(),
        "runtime_package_copied": runtime_ready,
        "extension_id": extension_id,
        "allowed_help_levels": list(HELP_LEVELS_V1),
        "exam_deployment_status": "not_cleared",
    }


def run_menu() -> int:
    install_companion()
    script = '''
set choices to {"Chrome oeffnen", "Diagnose anzeigen", "Bridge neu installieren", "Beenden"}
set selectedItem to choose from list choices with title "UniBot Companion" with prompt "Aktion waehlen" default items {"Chrome oeffnen"}
if selectedItem is false then return "Beenden"
return item 1 of selectedItem
'''
    result = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True, check=False)
    choice = result.stdout.strip()
    if choice == "Chrome oeffnen":
        subprocess.run(["/usr/bin/open", "-a", "Google Chrome"], check=False)
    elif choice == "Diagnose anzeigen":
        message = "UniBot Companion ist lokal bereit. Pruefungseinsatz ist nicht freigegeben."
        subprocess.run(["/usr/bin/osascript", "-e", f'display dialog "{message}" buttons {{"OK"}}'], check=False)
    elif choice == "Bridge neu installieren":
        install_native_host()
    return 0


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    if command == "native-host":
        return run_native_host()
    if command == "install":
        print(json.dumps(install_companion(), ensure_ascii=True, indent=2))
        return 0
    if command == "menu":
        return run_menu()
    print(json.dumps(companion_status(), ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
