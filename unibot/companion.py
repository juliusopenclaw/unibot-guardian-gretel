from __future__ import annotations

import json
import os
import shlex
import socket
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any, BinaryIO, cast

from .gateway import launch_gateway
from .learning_session import HELP_LEVELS_V1, LearningSession
from .notebook_intake import import_notebook
from .socratic_tutor import TutorTurnRequestV1, build_tutor_turn


NATIVE_HOST_NAME = "de.gretel.unibot_companion"
DEFAULT_EXTENSION_ID = "cmbjhndgjhgpopcflkjoalmpfjhoiana"
MAX_NATIVE_MESSAGE_BYTES = 64 * 1024
APPLICATION_SUPPORT = Path.home() / "Library" / "Application Support" / "UniBot Companion"
CHROME_NATIVE_HOSTS = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"
CHROMIUM_NATIVE_HOSTS = Path.home() / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts"
DEFAULT_APP_PATH = Path.home() / "Applications" / "UniBot Companion.app"


class CompanionRuntime:
    def __init__(self, *, storage_root: Path | None = None) -> None:
        self.storage_root = storage_root or APPLICATION_SUPPORT / "sessions"
        self.session: LearningSession | None = None
        self.notebook_manifests: dict[str, Path] = {}

    def handle(self, message: dict[str, Any]) -> dict[str, Any]:
        request_id = str(message.get("request_id", ""))
        message_type = str(message.get("type", ""))
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            return self._response(request_id, "invalid-payload", error="payload must be an object")
        try:
            if message_type == "companion.status":
                return self._response(
                    request_id,
                    "ready",
                    native_transport=True,
                    session_active=bool(self.session and not self.session.stopped),
                    allowed_help_levels=list(HELP_LEVELS_V1),
                    exam_deployment_status="not_cleared",
                )
            if message_type == "session.start":
                self.session = LearningSession.start(payload, storage_root=self.storage_root)
                return self._response(request_id, "active", contract=self.session.contract)
            if message_type == "tutor.turn":
                if self.session is None or self.session.stopped:
                    return self._response(request_id, "session-required", error="Start the learning session first.")
                request = cast(TutorTurnRequestV1, payload)
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
            if message_type == "notebook.import":
                source = str(payload.get("source", "")).strip()
                if not source:
                    source = choose_local_notebook()
                if not source:
                    return self._response(request_id, "cancelled", error="Notebook selection was cancelled.")
                output_root = APPLICATION_SUPPORT / "notebooks"
                manifest = import_notebook(source, output_root)
                notebook_id = str(manifest["sanitized_sha256"])[:16]
                self.notebook_manifests[notebook_id] = output_root / notebook_id / "manifest.json"
                return self._response(request_id, "ok", notebook_id=notebook_id, manifest=dict(manifest))
            if message_type == "gateway.launch":
                notebook_id = str(payload.get("notebook_id", ""))
                manifest_path = self.notebook_manifests.get(notebook_id)
                if manifest_path is None:
                    return self._response(request_id, "notebook-required", error="Import a notebook first.")
                port = int(payload.get("port") or available_loopback_port())
                result = launch_gateway(manifest_path, port=port, dry_run=bool(payload.get("dry_run", False)))
                return self._response(request_id, "ok", gateway=result)
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


def _python_launcher(command: str) -> str:
    python = shlex.quote(sys.executable)
    repo_root = shlex.quote(str(Path(__file__).resolve().parents[1]))
    return f"#!/bin/zsh\nexport PYTHONPATH={repo_root}\nexec {python} -m unibot.companion {command}\n"


def install_native_host(extension_id: str = DEFAULT_EXTENSION_ID) -> dict[str, Any]:
    if len(extension_id) != 32 or any(character not in "abcdefghijklmnop" for character in extension_id):
        raise ValueError("extension ID must be a 32-character Chrome extension ID")
    bin_root = APPLICATION_SUPPORT / "bin"
    bin_root.mkdir(parents=True, exist_ok=True)
    os.chmod(APPLICATION_SUPPORT, 0o700)
    os.chmod(bin_root, 0o700)
    launcher = bin_root / "unibot-native-host"
    launcher.write_text(_python_launcher("native-host"), encoding="utf-8")
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
    }


def install_companion_app(app_path: Path = DEFAULT_APP_PATH) -> dict[str, Any]:
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
    executable.write_text(_python_launcher("menu"), encoding="utf-8")
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
    return {"status": "installed", "app_present": True, "signature_status": signature_status}


def install_companion(extension_id: str = DEFAULT_EXTENSION_ID) -> dict[str, Any]:
    return {
        "schema_version": "unibot-companion-install-v1",
        "status": "installed",
        "native_host": install_native_host(extension_id),
        "app": install_companion_app(),
        "exam_deployment_status": "not_cleared",
    }


def companion_status(extension_id: str = DEFAULT_EXTENSION_ID) -> dict[str, Any]:
    chrome_manifest = CHROME_NATIVE_HOSTS / f"{NATIVE_HOST_NAME}.json"
    chromium_manifest = CHROMIUM_NATIVE_HOSTS / f"{NATIVE_HOST_NAME}.json"
    manifests_ready = chrome_manifest.is_file() and chromium_manifest.is_file()
    return {
        "schema_version": "unibot-companion-status-v1",
        "status": "ready" if manifests_ready and DEFAULT_APP_PATH.is_dir() else "not_installed",
        "native_host_installed": manifests_ready,
        "app_installed": DEFAULT_APP_PATH.is_dir(),
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
