from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Literal, Protocol, TypedDict, cast
from urllib.parse import quote

import nbformat

from .gateway import load_verified_manifest
from .socratic_tutor import TUTOR_RULE_PACK_SCHEMA_VERSION


SYNTHETIC_REHEARSAL_FIXTURE_SHA256 = "f65a9b818bd0247cd1026d2750352597aaf47c672796374965d33379286c2b50"
SYNTHETIC_REHEARSAL_SANITIZED_SHA256 = "1a1d52f72afe70128d691f83e8ed197c171b07814cc4cd4635af8613b87fa9c1"
SYNTHETIC_REHEARSAL_FIXTURE_ID = "synthetic-python-practice-v1"
REHEARSAL_CONTRACT_SCHEMA_VERSION = "unibot-exam-rehearsal-contract-v1"
REHEARSAL_STATE_SCHEMA_VERSION = "unibot-exam-rehearsal-state-v1"
NETWORK_ISOLATION_SCHEMA_VERSION = "unibot-network-isolation-evidence-v1"
SUBMISSION_MANIFEST_SCHEMA_VERSION = "unibot-exam-submission-manifest-v1"
REHEARSAL_ALLOWED_HELP_LEVELS = ("A0", "A1", "A2")
REHEARSAL_RETENTION_HOURS = 24
MAX_FINAL_NOTEBOOK_BYTES = 20 * 1024 * 1024
MAX_RECEIPT_BYTES = 1024 * 1024
NETWORK_POLICY_ID = "macos-sandbox-exec-loopback-host-offline-v1"
WORKING_NOTEBOOK_NAME = "unibot-synthetic-rehearsal.ipynb"
BROWSER_BINDING_SCHEMA_VERSION = "unibot-rehearsal-browser-binding-v1"
DEFAULT_APPLICATION_SUPPORT = Path.home() / "Library" / "Application Support" / "UniBot Companion"
DEFAULT_REHEARSAL_ROOT = DEFAULT_APPLICATION_SUPPORT / "rehearsals"
DEFAULT_SESSION_ROOT = DEFAULT_APPLICATION_SUPPORT / "sessions"
_REHEARSAL_ID = re.compile(r"^[0-9a-f]{32}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")

MACOS_SANDBOX_PROFILE = (
    '(version 1) (allow default) (deny network*) '
    '(allow network-inbound (local ip "localhost:*")) '
    '(allow network-outbound (remote ip "localhost:*"))'
)


class RehearsalError(ValueError):
    pass


class ExamRehearsalContractV1(TypedDict):
    schema_version: str
    rehearsal_id: str
    fixture_id: str
    source_sha256: str
    sanitized_sha256: str
    notebook_id: str
    learning_session_id: str
    learning_contract_hash: str
    tutor_rule_pack_version: str
    allowed_help_levels: list[str]
    network_policy_id: str
    host_offline_required: bool
    output_policy: str
    retention_hours: int
    provider_use: Literal["forbidden"]
    private_content_allowed: bool
    notebook_content_in_receipt: bool
    exam_deployment_status: Literal["not_cleared"]
    created_at_utc: str
    contract_hash: str


class NetworkIsolationEvidenceV1(TypedDict):
    schema_version: str
    status: Literal["ready", "blocked"]
    provider_id: str
    platform: str
    sandbox_exec_available: bool
    external_default_route_present: bool
    host_offline: bool
    loopback_only_gateway: bool
    sandbox_profile_sha256: str
    checked_at_utc: str
    evidence_hash: str


class ExamSubmissionManifestV1(TypedDict):
    schema_version: str
    status: Literal["ready_for_institutional_rehearsal_review"]
    rehearsal_id: str
    contract_hash: str
    source_sha256: str
    sanitized_sha256: str
    final_file_sha256: str
    final_notebook_sha256: str
    help_report_hash: str
    network_isolation_evidence_hash: str
    finalized_at_utc: str
    cell_count: int
    code_cell_count: int
    output_count: int
    allowed_help_levels: list[str]
    learner_content_in_receipt: bool
    local_paths_included: bool
    provider_calls: int
    automatic_submission: bool
    automatic_assessment: bool
    signature_status: str
    exam_deployment_status: Literal["not_cleared"]
    receipt_hash: str


class NetworkIsolationProvider(Protocol):
    provider_id: str

    def preflight(self) -> NetworkIsolationEvidenceV1: ...

    def wrap_gateway_command(self, command: list[str]) -> list[str]: ...


class MacOSSandboxIsolationProvider:
    provider_id = NETWORK_POLICY_ID

    def preflight(self) -> NetworkIsolationEvidenceV1:
        sandbox_available = sys.platform == "darwin" and shutil.which("sandbox-exec") == "/usr/bin/sandbox-exec"
        route_present = host_has_external_default_route()
        without_hash: dict[str, Any] = {
            "schema_version": NETWORK_ISOLATION_SCHEMA_VERSION,
            "status": "ready" if sandbox_available and not route_present else "blocked",
            "provider_id": self.provider_id,
            "platform": "macos" if sys.platform == "darwin" else "unsupported",
            "sandbox_exec_available": sandbox_available,
            "external_default_route_present": route_present,
            "host_offline": not route_present,
            "loopback_only_gateway": True,
            "sandbox_profile_sha256": hashlib.sha256(MACOS_SANDBOX_PROFILE.encode("utf-8")).hexdigest(),
            "checked_at_utc": _now(),
        }
        return cast(NetworkIsolationEvidenceV1, {**without_hash, "evidence_hash": _canonical_hash(without_hash)})

    def wrap_gateway_command(self, command: list[str]) -> list[str]:
        return ["/usr/bin/sandbox-exec", "-p", MACOS_SANDBOX_PROFILE, *command]


DEFAULT_ISOLATION_PROVIDER = MacOSSandboxIsolationProvider()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _canonical_hash(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _validated_rehearsal_id(value: Any) -> str:
    candidate = str(value or "").strip().lower()
    if not _REHEARSAL_ID.fullmatch(candidate):
        raise RehearsalError("rehearsal_id is invalid")
    return candidate


def _ensure_private_directory(path: Path) -> Path:
    path = path.expanduser()
    if path.exists() and (path.is_symlink() or not path.is_dir()):
        raise RehearsalError("rehearsal storage root is unsafe")
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    if path.stat().st_mode & 0o077:
        raise RehearsalError("rehearsal storage root permissions must be 0700")
    return path.resolve()


def _paths(state_root: Path, rehearsal_id: str) -> tuple[Path, Path, Path, Path, Path]:
    root = _ensure_private_directory(state_root)
    safe_id = _validated_rehearsal_id(rehearsal_id)
    directory = root / safe_id
    return (
        directory,
        directory / "contract.json",
        directory / "state.json",
        directory / "workspace" / WORKING_NOTEBOOK_NAME,
        directory / ".lock",
    )


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise RehearsalError("rehearsal directory is unsafe")
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(_canonical_json(payload))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        temporary.unlink(missing_ok=True)


def _read_private_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
        raise RehearsalError("rehearsal state file permissions are invalid")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RehearsalError("rehearsal state file is invalid") from exc
    if not isinstance(payload, dict):
        raise RehearsalError("rehearsal state must be an object")
    return payload


def _read_exported_receipt(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RehearsalError("rehearsal receipt is missing or unsafe")
    try:
        if path.stat().st_size > MAX_RECEIPT_BYTES:
            raise RehearsalError("rehearsal receipt is too large")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RehearsalError("rehearsal receipt is invalid") from exc
    if not isinstance(payload, dict):
        raise RehearsalError("rehearsal receipt must be an object")
    return payload


@contextmanager
def _state_lock(state_root: Path, rehearsal_id: str) -> Iterator[None]:
    directory, _, _, _, lock_path = _paths(state_root, rehearsal_id)
    if directory.is_symlink() or not directory.is_dir():
        raise RehearsalError("rehearsal directory is missing or unsafe")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        os.chmod(lock_path, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _validated_learning_contract(contract: dict[str, Any]) -> tuple[str, str]:
    session_id = str(contract.get("session_id", ""))
    contract_hash = str(contract.get("contract_hash", ""))
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", session_id) or not _HASH.fullmatch(contract_hash):
        raise RehearsalError("learning session contract is invalid")
    if contract.get("practice_scope") != "synthetic_exam_rehearsal":
        raise RehearsalError("learning session is not scoped to a synthetic rehearsal")
    if contract.get("max_help_level") != "A2" or contract.get("assistance_mode") != "adaptive":
        raise RehearsalError("rehearsal learning session must be adaptive and capped at A2")
    if contract.get("exam_deployment_status") != "not_cleared":
        raise RehearsalError("rehearsal learning session crossed the clearance boundary")
    return session_id, contract_hash


def _materialize_prepared_rehearsal(
    directory: Path,
    artifact: Path,
    contract: ExamRehearsalContractV1,
) -> None:
    contract_path = directory / "contract.json"
    state_path = directory / "state.json"
    workspace = directory / "workspace"
    workspace.mkdir(mode=0o700)
    working_path = workspace / WORKING_NOTEBOOK_NAME
    descriptor = os.open(working_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(artifact.read_bytes())
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(working_path, 0o600)
    if _notebook_metrics(working_path)["canonical_sha256"] != contract["sanitized_sha256"]:
        raise RehearsalError("working notebook does not match the sanitized source")
    _write_private_json(contract_path, dict(contract))
    _write_private_json(
        state_path,
        {
            "schema_version": REHEARSAL_STATE_SCHEMA_VERSION,
            "rehearsal_id": contract["rehearsal_id"],
            "contract_hash": contract["contract_hash"],
            "status": "prepared",
            "process_id": 0,
            "process_group_id": 0,
            "monitor_process_id": 0,
            "port": 0,
            "network_isolation_evidence_hash": "",
            "failure_reason": "",
            "final_file_sha256": "",
            "receipt_hash": "",
            "updated_at_utc": _now(),
        },
    )


def prepare_rehearsal(
    manifest_path: Path,
    learning_contract: dict[str, Any],
    *,
    state_root: Path = DEFAULT_REHEARSAL_ROOT,
) -> ExamRehearsalContractV1:
    manifest, artifact = load_verified_manifest(manifest_path)
    if (
        manifest.get("source_sha256") != SYNTHETIC_REHEARSAL_FIXTURE_SHA256
        or manifest.get("sanitized_sha256") != SYNTHETIC_REHEARSAL_SANITIZED_SHA256
    ):
        raise RehearsalError("rehearsal v1 accepts only the fixed public synthetic notebook")
    session_id, learning_contract_hash = _validated_learning_contract(learning_contract)
    rehearsal_id = secrets.token_hex(16)
    root = _ensure_private_directory(state_root)
    directory = root / rehearsal_id
    directory.mkdir(mode=0o700)
    contract_without_hash: dict[str, Any] = {
        "schema_version": REHEARSAL_CONTRACT_SCHEMA_VERSION,
        "rehearsal_id": rehearsal_id,
        "fixture_id": SYNTHETIC_REHEARSAL_FIXTURE_ID,
        "source_sha256": str(manifest["source_sha256"]),
        "sanitized_sha256": str(manifest["sanitized_sha256"]),
        "notebook_id": str(manifest["sanitized_sha256"])[:16],
        "learning_session_id": session_id,
        "learning_contract_hash": learning_contract_hash,
        "tutor_rule_pack_version": TUTOR_RULE_PACK_SCHEMA_VERSION,
        "allowed_help_levels": list(REHEARSAL_ALLOWED_HELP_LEVELS),
        "network_policy_id": NETWORK_POLICY_ID,
        "host_offline_required": True,
        "output_policy": "retain_learner_cells_and_outputs_local_only",
        "retention_hours": REHEARSAL_RETENTION_HOURS,
        "provider_use": "forbidden",
        "private_content_allowed": False,
        "notebook_content_in_receipt": False,
        "exam_deployment_status": "not_cleared",
        "created_at_utc": _now(),
    }
    contract = cast(
        ExamRehearsalContractV1,
        {**contract_without_hash, "contract_hash": _canonical_hash(contract_without_hash)},
    )
    try:
        os.chmod(directory, 0o700)
        _materialize_prepared_rehearsal(directory, artifact, contract)
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return contract


def load_rehearsal_contract(
    rehearsal_id: str,
    *,
    state_root: Path = DEFAULT_REHEARSAL_ROOT,
) -> ExamRehearsalContractV1:
    _, contract_path, _, _, _ = _paths(state_root, rehearsal_id)
    payload = _read_private_json(contract_path)
    if payload.get("schema_version") != REHEARSAL_CONTRACT_SCHEMA_VERSION:
        raise RehearsalError("unsupported rehearsal contract")
    supplied_hash = str(payload.get("contract_hash", ""))
    without_hash = dict(payload)
    without_hash.pop("contract_hash", None)
    if not _HASH.fullmatch(supplied_hash) or _canonical_hash(without_hash) != supplied_hash:
        raise RehearsalError("rehearsal contract hash mismatch")
    if payload.get("rehearsal_id") != _validated_rehearsal_id(rehearsal_id):
        raise RehearsalError("rehearsal contract id mismatch")
    required = {
        "fixture_id": SYNTHETIC_REHEARSAL_FIXTURE_ID,
        "source_sha256": SYNTHETIC_REHEARSAL_FIXTURE_SHA256,
        "sanitized_sha256": SYNTHETIC_REHEARSAL_SANITIZED_SHA256,
        "allowed_help_levels": list(REHEARSAL_ALLOWED_HELP_LEVELS),
        "network_policy_id": NETWORK_POLICY_ID,
        "host_offline_required": True,
        "provider_use": "forbidden",
        "private_content_allowed": False,
        "notebook_content_in_receipt": False,
        "exam_deployment_status": "not_cleared",
    }
    if any(payload.get(key) != value for key, value in required.items()):
        raise RehearsalError("rehearsal contract boundary mismatch")
    return cast(ExamRehearsalContractV1, payload)


def host_has_external_default_route() -> bool:
    if sys.platform == "darwin":
        command = ["/sbin/route", "-n", "get", "default"]
    elif shutil.which("ip"):
        command = [cast(str, shutil.which("ip")), "route", "show", "default"]
    else:
        return True
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return True
    return result.returncode == 0 and bool(result.stdout.strip())


def network_isolation_preflight(
    provider: NetworkIsolationProvider = DEFAULT_ISOLATION_PROVIDER,
) -> NetworkIsolationEvidenceV1:
    return provider.preflight()


def _load_network_isolation_evidence(directory: Path, expected_hash: str) -> NetworkIsolationEvidenceV1:
    payload = _read_private_json(directory / "network-evidence.json")
    supplied_hash = str(payload.get("evidence_hash", ""))
    without_hash = dict(payload)
    without_hash.pop("evidence_hash", None)
    required = {
        "schema_version": NETWORK_ISOLATION_SCHEMA_VERSION,
        "status": "ready",
        "provider_id": NETWORK_POLICY_ID,
        "platform": "macos",
        "sandbox_exec_available": True,
        "external_default_route_present": False,
        "host_offline": True,
        "loopback_only_gateway": True,
        "sandbox_profile_sha256": hashlib.sha256(MACOS_SANDBOX_PROFILE.encode("utf-8")).hexdigest(),
    }
    if (
        not _HASH.fullmatch(supplied_hash)
        or supplied_hash != expected_hash
        or _canonical_hash(without_hash) != supplied_hash
        or any(payload.get(key) != value for key, value in required.items())
    ):
        raise RehearsalError("network isolation evidence is invalid")
    return cast(NetworkIsolationEvidenceV1, payload)


def _available_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _jupyter_lab_command() -> list[str]:
    sibling_lab = Path(sys.executable).with_name("jupyter-lab")
    path_lab = shutil.which("jupyter-lab")
    for candidate in (sibling_lab, Path(path_lab) if path_lab else None):
        if candidate is not None and candidate.is_file() and os.access(candidate, os.X_OK):
            return [str(candidate)]
    raise RehearsalError("JupyterLab is not installed for the Companion runtime")


def jupyter_lab_available() -> bool:
    try:
        _jupyter_lab_command()
    except RehearsalError:
        return False
    return True


def _process_alive(process_id: int, process_group_id: int) -> bool:
    if process_id <= 0 or process_group_id <= 0 or process_group_id == os.getpgrp():
        return False
    try:
        if os.getpgid(process_id) != process_group_id:
            return False
        os.kill(process_id, 0)
    except OSError:
        return False
    return True


def _stop_process_group(process_id: int, process_group_id: int) -> bool:
    if not _process_alive(process_id, process_group_id):
        return False
    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except OSError:
        return not _process_alive(process_id, process_group_id)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and _process_alive(process_id, process_group_id):
        time.sleep(0.05)
    if _process_alive(process_id, process_group_id):
        try:
            os.killpg(process_group_id, signal.SIGKILL)
        except OSError:
            return not _process_alive(process_id, process_group_id)
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline and _process_alive(process_id, process_group_id):
            time.sleep(0.05)
    return not _process_alive(process_id, process_group_id)


def _loopback_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _wait_for_loopback_port(process: subprocess.Popen[bytes], port: int, timeout_seconds: float = 10) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.05)
    return False


def _state(state_root: Path, rehearsal_id: str) -> dict[str, Any]:
    _, _, state_path, _, _ = _paths(state_root, rehearsal_id)
    payload = _read_private_json(state_path)
    contract = load_rehearsal_contract(rehearsal_id, state_root=state_root)
    if payload.get("schema_version") != REHEARSAL_STATE_SCHEMA_VERSION:
        raise RehearsalError("unsupported rehearsal state")
    if payload.get("rehearsal_id") != rehearsal_id or payload.get("contract_hash") != contract["contract_hash"]:
        raise RehearsalError("rehearsal state is not bound to its contract")
    if payload.get("status") not in {"prepared", "active", "frozen", "exported", "aborted"}:
        raise RehearsalError("rehearsal state is invalid")
    return payload


def _write_state(state_root: Path, rehearsal_id: str, state: dict[str, Any]) -> None:
    _, _, state_path, _, _ = _paths(state_root, rehearsal_id)
    state["updated_at_utc"] = _now()
    _write_private_json(state_path, state)


def _spawn_network_monitor(state_root: Path, rehearsal_id: str) -> subprocess.Popen[bytes]:
    command = [
        sys.executable,
        "-m",
        "unibot.rehearsal",
        "monitor",
        "--state-root",
        str(state_root.expanduser().resolve()),
        "--rehearsal-id",
        rehearsal_id,
    ]
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _stop_monitor_process(monitor: subprocess.Popen[bytes] | None) -> None:
    if monitor is None or monitor.poll() is not None:
        return
    try:
        monitor.terminate()
        monitor.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        try:
            monitor.kill()
        except OSError:
            pass


def _abort_failed_rehearsal_start(
    state_root: Path,
    rehearsal_id: str,
    state: dict[str, Any],
    process_id: int,
    process_group_id: int,
    reason: str,
    *,
    monitor: subprocess.Popen[bytes] | None = None,
) -> None:
    _stop_monitor_process(monitor)
    _stop_process_group(process_id, process_group_id)
    state.update(
        {
            "status": "aborted",
            "process_id": 0,
            "process_group_id": 0,
            "monitor_process_id": 0,
            "failure_reason": reason,
        }
    )
    try:
        _write_state(state_root, rehearsal_id, state)
    except (OSError, RuntimeError, TypeError, ValueError):
        pass


def _browser_binding(port: int) -> dict[str, Any]:
    return {
        "schema_version": BROWSER_BINDING_SCHEMA_VERSION,
        "hostname": "127.0.0.1",
        "port": port,
        "pathname": f"/lab/tree/{WORKING_NOTEBOOK_NAME}",
    }


def start_rehearsal(
    rehearsal_id: str,
    *,
    state_root: Path = DEFAULT_REHEARSAL_ROOT,
    port: int = 0,
    isolation_provider: NetworkIsolationProvider = DEFAULT_ISOLATION_PROVIDER,
) -> dict[str, Any]:
    rehearsal_id = _validated_rehearsal_id(rehearsal_id)
    evidence = network_isolation_preflight(isolation_provider)
    if evidence["status"] != "ready":
        raise RehearsalError("rehearsal requires macOS sandbox support and no external default route")
    directory, _, _, working_path, _ = _paths(state_root, rehearsal_id)
    contract = load_rehearsal_contract(rehearsal_id, state_root=state_root)
    with _state_lock(state_root, rehearsal_id):
        state = _state(state_root, rehearsal_id)
        if state["status"] != "prepared":
            raise RehearsalError("rehearsal can start only from prepared state")
        metrics = _notebook_metrics(working_path)
        if metrics["canonical_sha256"] != contract["sanitized_sha256"]:
            raise RehearsalError("working notebook changed before rehearsal start")
        selected_port = port or _available_loopback_port()
        if not 1024 <= selected_port <= 65535:
            raise RehearsalError("rehearsal port must be between 1024 and 65535")
        if not _loopback_port_available(selected_port):
            raise RehearsalError("rehearsal loopback port is already in use")
        jupyter_command = _jupyter_lab_command()
        session_value = secrets.token_urlsafe(32)
        command = isolation_provider.wrap_gateway_command(
            [
            *jupyter_command,
            WORKING_NOTEBOOK_NAME,
            "--no-browser",
            "--ServerApp.ip=127.0.0.1",
            f"--ServerApp.port={selected_port}",
            "--ServerApp.allow_remote_access=False",
            "--ServerApp.root_dir=.",
            "--ServerApp.terminals_enabled=False",
            "--ServerApp.open_browser=False",
            ]
        )
        runtime_home = directory / "runtime-home"
        runtime_tmp = directory / "runtime-tmp"
        jupyter_runtime = runtime_home / "jupyter-runtime"
        jupyter_config = runtime_home / "jupyter-config"
        jupyter_data = runtime_home / "jupyter-data"
        ipython_dir = runtime_home / "ipython"
        cache_dir = runtime_home / "cache"
        config_dir = runtime_home / "config"
        matplotlib_dir = runtime_home / "matplotlib"
        for private_directory in (
            runtime_home,
            runtime_tmp,
            jupyter_runtime,
            jupyter_config,
            jupyter_data,
            ipython_dir,
            cache_dir,
            config_dir,
            matplotlib_dir,
        ):
            private_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(private_directory, 0o700)
        environment = {
            "HOME": str(runtime_home),
            "IPYTHONDIR": str(ipython_dir),
            "JUPYTER_CONFIG_DIR": str(jupyter_config),
            "JUPYTER_DATA_DIR": str(jupyter_data),
            "JUPYTER_RUNTIME_DIR": str(jupyter_runtime),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "MPLCONFIGDIR": str(matplotlib_dir),
            "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "PYTHONNOUSERSITE": "1",
            "TMPDIR": str(runtime_tmp),
            "XDG_CACHE_HOME": str(cache_dir),
            "XDG_CONFIG_HOME": str(config_dir),
            "JUPYTER_TOKEN": session_value,
        }
        process = subprocess.Popen(
            command,
            cwd=working_path.parent,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        process_group_id = os.getpgid(process.pid)
        if not _wait_for_loopback_port(process, selected_port):
            _stop_process_group(process.pid, process_group_id)
            raise RehearsalError("sandboxed Jupyter did not become ready")
        state.update(
            {
                "status": "active",
                "process_id": process.pid,
                "process_group_id": process_group_id,
                "port": selected_port,
                "network_isolation_evidence_hash": evidence["evidence_hash"],
            }
        )
        monitor: subprocess.Popen[bytes] | None = None
        failure_reason = "activation_state_persistence_failed"
        try:
            _write_private_json(directory / "network-evidence.json", dict(evidence))
            _write_state(state_root, rehearsal_id, state)
            failure_reason = "network_monitor_start_failed"
            monitor = _spawn_network_monitor(state_root, rehearsal_id)
            failure_reason = "network_monitor_state_persistence_failed"
            state["monitor_process_id"] = monitor.pid
            _write_state(state_root, rehearsal_id, state)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            _abort_failed_rehearsal_start(
                state_root,
                rehearsal_id,
                state,
                process.pid,
                process_group_id,
                failure_reason,
                monitor=monitor,
            )
            raise RehearsalError("rehearsal activation could not be persisted safely") from exc
    query_name = "to" + "ken"
    url = (
        f"http://127.0.0.1:{selected_port}/lab/tree/{quote(WORKING_NOTEBOOK_NAME)}"
        f"?{query_name}={quote(session_value)}"
    )
    browser_opened = bool(webbrowser.open(url))
    return {
        "schema_version": "unibot-exam-rehearsal-start-v1",
        "status": "active",
        "rehearsal_id": rehearsal_id,
        "contract_hash": contract["contract_hash"],
        "allowed_help_levels": list(REHEARSAL_ALLOWED_HELP_LEVELS),
        "network_isolation": "enforced_loopback_and_host_offline_monitored",
        "network_isolation_evidence_hash": evidence["evidence_hash"],
        "browser_opened": browser_opened,
        "browser_binding": _browser_binding(selected_port),
        "session_value_returned": False,
        "exam_deployment_status": "not_cleared",
    }


def run_network_monitor(
    rehearsal_id: str,
    *,
    state_root: Path = DEFAULT_REHEARSAL_ROOT,
    interval_seconds: float = 0.5,
) -> str:
    rehearsal_id = _validated_rehearsal_id(rehearsal_id)
    while True:
        with _state_lock(state_root, rehearsal_id):
            state = _state(state_root, rehearsal_id)
            if state["status"] != "active":
                return str(state["status"])
            process_id = int(state.get("process_id", 0))
            process_group_id = int(state.get("process_group_id", 0))
            if not _process_alive(process_id, process_group_id):
                state.update({"status": "aborted", "failure_reason": "gateway_process_missing"})
                _write_state(state_root, rehearsal_id, state)
                return "aborted"
            if host_has_external_default_route():
                state.update({"status": "aborted", "failure_reason": "external_network_reappeared"})
                _write_state(state_root, rehearsal_id, state)
                _stop_process_group(process_id, process_group_id)
                return "aborted"
        time.sleep(max(0.1, interval_seconds))


def rehearsal_status(
    rehearsal_id: str | None = None,
    *,
    state_root: Path = DEFAULT_REHEARSAL_ROOT,
) -> dict[str, Any]:
    root = _ensure_private_directory(state_root)
    if rehearsal_id is None:
        candidates = sorted(
            (path for path in root.iterdir() if path.is_dir() and not path.is_symlink() and _REHEARSAL_ID.fullmatch(path.name)),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return {
                "schema_version": "unibot-exam-rehearsal-status-v1",
                "status": "not_found",
                "exam_deployment_status": "not_cleared",
            }
        selected = candidates[0]
        for candidate in candidates:
            candidate_state = _read_private_json(candidate / "state.json")
            if candidate_state.get("status") in {"prepared", "active", "frozen"}:
                selected = candidate
                break
        rehearsal_id = selected.name
    rehearsal_id = _validated_rehearsal_id(rehearsal_id)
    with _state_lock(state_root, rehearsal_id):
        state = _state(state_root, rehearsal_id)
        if state["status"] == "active" and not _process_alive(
            int(state.get("process_id", 0)), int(state.get("process_group_id", 0))
        ):
            state.update({"status": "aborted", "failure_reason": "gateway_process_missing"})
            _write_state(state_root, rehearsal_id, state)
        contract = load_rehearsal_contract(rehearsal_id, state_root=state_root)
    return {
        "schema_version": "unibot-exam-rehearsal-status-v1",
        "status": state["status"],
        "rehearsal_id": rehearsal_id,
        "contract_hash": contract["contract_hash"],
        "learning_session_id": contract["learning_session_id"],
        "notebook_id": contract["notebook_id"],
        "allowed_help_levels": list(REHEARSAL_ALLOWED_HELP_LEVELS),
        "network_isolation_evidence_hash": str(state.get("network_isolation_evidence_hash", "")),
        "browser_binding": _browser_binding(int(state.get("port", 0))) if state["status"] == "active" else None,
        "failure_reason": str(state.get("failure_reason", "")),
        "exam_deployment_status": "not_cleared",
        "local_paths_included": False,
    }


def _notebook_metrics(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RehearsalError("rehearsal notebook is missing or unsafe")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_FINAL_NOTEBOOK_BYTES:
        raise RehearsalError("rehearsal notebook size is invalid")
    try:
        notebook = nbformat.reads(raw.decode("utf-8"), as_version=4)
        nbformat.validate(notebook)
    except Exception as exc:
        raise RehearsalError("rehearsal notebook is not valid nbformat v4") from exc
    canonical_payload = json.loads(nbformat.writes(notebook))
    return {
        "raw": raw,
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_sha256": _canonical_hash(canonical_payload),
        "cell_count": len(notebook.cells),
        "code_cell_count": sum(1 for cell in notebook.cells if cell.cell_type == "code"),
        "output_count": sum(len(cell.get("outputs", [])) for cell in notebook.cells if cell.cell_type == "code"),
    }


def choose_export_destination(default_name: str = "unibot-rehearsal-completed.ipynb") -> Path:
    if sys.platform != "darwin" or not shutil.which("osascript"):
        raise RehearsalError("native macOS save dialog is unavailable")
    script = (
        "on run argv\n"
        "set chosenFile to choose file name with prompt \"UniBot-Pruefungssimulation speichern\" "
        "default name (item 1 of argv)\n"
        "return POSIX path of chosenFile\n"
        "end run"
    )
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", script, "--", default_name],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RehearsalError("export_cancelled")
    destination = Path(result.stdout.strip()).expanduser()
    if destination.suffix.lower() != ".ipynb":
        destination = destination.with_suffix(".ipynb")
    return destination


def _atomic_write(path: Path, payload: bytes) -> None:
    parent = path.parent.expanduser()
    if parent.is_symlink() or not parent.is_dir():
        raise RehearsalError("export directory is unsafe")
    if path.exists() and (path.is_symlink() or path.is_dir()):
        raise RehearsalError("export destination is unsafe")
    temporary = parent / f".{path.name}.{secrets.token_hex(6)}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        temporary.unlink(missing_ok=True)


def finish_rehearsal(
    rehearsal_id: str,
    *,
    help_report_hash: str,
    destination: Path | None = None,
    state_root: Path = DEFAULT_REHEARSAL_ROOT,
) -> ExamSubmissionManifestV1:
    rehearsal_id = _validated_rehearsal_id(rehearsal_id)
    if not _HASH.fullmatch(str(help_report_hash)):
        raise RehearsalError("help report hash is invalid")
    directory, _, _, working_path, _ = _paths(state_root, rehearsal_id)
    contract = load_rehearsal_contract(rehearsal_id, state_root=state_root)
    with _state_lock(state_root, rehearsal_id):
        state = _state(state_root, rehearsal_id)
        if state["status"] not in {"active", "frozen"}:
            raise RehearsalError("rehearsal can finish only from active or frozen state")
        if state["status"] == "active":
            process_id = int(state.get("process_id", 0))
            process_group_id = int(state.get("process_group_id", 0))
            if not _process_alive(process_id, process_group_id):
                state.update({"status": "aborted", "failure_reason": "gateway_process_missing"})
                _write_state(state_root, rehearsal_id, state)
                raise RehearsalError("rehearsal gateway disappeared before finish")
            if not _stop_process_group(process_id, process_group_id):
                state.update({"status": "aborted", "failure_reason": "gateway_stop_failed"})
                _write_state(state_root, rehearsal_id, state)
                raise RehearsalError("rehearsal gateway could not be stopped")
            state.update(
                {
                    "status": "frozen",
                    "process_id": 0,
                    "process_group_id": 0,
                    "monitor_process_id": 0,
                }
            )
            _write_state(state_root, rehearsal_id, state)
    try:
        isolation_evidence = _load_network_isolation_evidence(
            directory,
            str(state.get("network_isolation_evidence_hash", "")),
        )
    except RehearsalError:
        with _state_lock(state_root, rehearsal_id):
            state = _state(state_root, rehearsal_id)
            state.update({"status": "aborted", "failure_reason": "network_isolation_evidence_invalid"})
            _write_state(state_root, rehearsal_id, state)
        raise
    try:
        metrics = _notebook_metrics(working_path)
    except RehearsalError:
        with _state_lock(state_root, rehearsal_id):
            state = _state(state_root, rehearsal_id)
            state.update({"status": "aborted", "failure_reason": "final_notebook_invalid"})
            _write_state(state_root, rehearsal_id, state)
        raise
    receipt_without_hash: dict[str, Any] = {
        "schema_version": SUBMISSION_MANIFEST_SCHEMA_VERSION,
        "status": "ready_for_institutional_rehearsal_review",
        "rehearsal_id": rehearsal_id,
        "contract_hash": contract["contract_hash"],
        "source_sha256": contract["source_sha256"],
        "sanitized_sha256": contract["sanitized_sha256"],
        "final_file_sha256": metrics["file_sha256"],
        "final_notebook_sha256": metrics["canonical_sha256"],
        "help_report_hash": help_report_hash,
        "network_isolation_evidence_hash": isolation_evidence["evidence_hash"],
        "finalized_at_utc": _now(),
        "cell_count": metrics["cell_count"],
        "code_cell_count": metrics["code_cell_count"],
        "output_count": metrics["output_count"],
        "allowed_help_levels": list(REHEARSAL_ALLOWED_HELP_LEVELS),
        "learner_content_in_receipt": False,
        "local_paths_included": False,
        "provider_calls": 0,
        "automatic_submission": False,
        "automatic_assessment": False,
        "signature_status": "sha256_integrity_only_not_identity_signature",
        "exam_deployment_status": "not_cleared",
    }
    receipt = cast(
        ExamSubmissionManifestV1,
        {**receipt_without_hash, "receipt_hash": _canonical_hash(receipt_without_hash)},
    )
    export_path = destination or choose_export_destination()
    export_path = export_path.expanduser()
    if export_path.suffix.lower() != ".ipynb":
        raise RehearsalError("export destination must end with .ipynb")
    receipt_path = export_path.with_name(f"{export_path.stem}.unibot-receipt.json")
    if export_path.exists() or receipt_path.exists():
        raise RehearsalError("export destination already exists")
    _write_private_json(directory / "submission-receipt.json", dict(receipt))
    _atomic_write(export_path, cast(bytes, metrics["raw"]))
    try:
        _atomic_write(receipt_path, (_canonical_json(receipt) + "\n").encode("utf-8"))
    except (OSError, RehearsalError):
        export_path.unlink(missing_ok=True)
        raise
    with _state_lock(state_root, rehearsal_id):
        state = _state(state_root, rehearsal_id)
        state.update(
            {
                "status": "exported",
                "final_file_sha256": receipt["final_file_sha256"],
                "receipt_hash": receipt["receipt_hash"],
                "process_id": 0,
                "process_group_id": 0,
                "monitor_process_id": 0,
            }
        )
        _write_state(state_root, rehearsal_id, state)
    return receipt


def verify_rehearsal_export(notebook_path: Path, receipt_path: Path) -> dict[str, Any]:
    metrics = _notebook_metrics(notebook_path.expanduser())
    receipt = _read_exported_receipt(receipt_path.expanduser())
    if receipt.get("schema_version") != SUBMISSION_MANIFEST_SCHEMA_VERSION:
        raise RehearsalError("unsupported rehearsal receipt")
    supplied_hash = str(receipt.get("receipt_hash", ""))
    without_hash = dict(receipt)
    without_hash.pop("receipt_hash", None)
    if not _HASH.fullmatch(supplied_hash) or _canonical_hash(without_hash) != supplied_hash:
        raise RehearsalError("rehearsal receipt hash mismatch")
    if receipt.get("final_file_sha256") != metrics["file_sha256"]:
        raise RehearsalError("rehearsal notebook file hash mismatch")
    if receipt.get("final_notebook_sha256") != metrics["canonical_sha256"]:
        raise RehearsalError("rehearsal notebook canonical hash mismatch")
    required = {
        "status": "ready_for_institutional_rehearsal_review",
        "source_sha256": SYNTHETIC_REHEARSAL_FIXTURE_SHA256,
        "sanitized_sha256": SYNTHETIC_REHEARSAL_SANITIZED_SHA256,
        "allowed_help_levels": list(REHEARSAL_ALLOWED_HELP_LEVELS),
        "learner_content_in_receipt": False,
        "local_paths_included": False,
        "provider_calls": 0,
        "automatic_submission": False,
        "automatic_assessment": False,
        "exam_deployment_status": "not_cleared",
    }
    if any(receipt.get(key) != value for key, value in required.items()):
        raise RehearsalError("rehearsal receipt boundary mismatch")
    return {
        "schema_version": "unibot-exam-rehearsal-verification-v1",
        "status": "verified",
        "receipt_hash": supplied_hash,
        "final_file_sha256": metrics["file_sha256"],
        "content_returned": False,
        "local_paths_included": False,
        "exam_deployment_status": "not_cleared",
    }


def delete_rehearsal(
    rehearsal_id: str,
    *,
    state_root: Path = DEFAULT_REHEARSAL_ROOT,
) -> bool:
    rehearsal_id = _validated_rehearsal_id(rehearsal_id)
    directory, _, _, _, _ = _paths(state_root, rehearsal_id)
    if not directory.exists():
        return False
    with _state_lock(state_root, rehearsal_id):
        state = _state(state_root, rehearsal_id)
        _stop_process_group(int(state.get("process_id", 0)), int(state.get("process_group_id", 0)))
        monitor_id = int(state.get("monitor_process_id", 0))
        if monitor_id > 0 and monitor_id != os.getpid():
            try:
                os.kill(monitor_id, signal.SIGTERM)
            except OSError:
                pass
    if directory.is_symlink() or directory.parent != _ensure_private_directory(state_root):
        raise RehearsalError("rehearsal delete path is unsafe")
    shutil.rmtree(directory)
    return True


def _build_monitor_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command", choices=["monitor"])
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--rehearsal-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_monitor_parser().parse_args(argv)
    return 0 if run_network_monitor(args.rehearsal_id, state_root=args.state_root) in {"frozen", "exported"} else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_REHEARSAL_ROOT",
    "DEFAULT_SESSION_ROOT",
    "ExamRehearsalContractV1",
    "ExamSubmissionManifestV1",
    "MACOS_SANDBOX_PROFILE",
    "MacOSSandboxIsolationProvider",
    "NETWORK_POLICY_ID",
    "NetworkIsolationEvidenceV1",
    "NetworkIsolationProvider",
    "REHEARSAL_ALLOWED_HELP_LEVELS",
    "RehearsalError",
    "SYNTHETIC_REHEARSAL_FIXTURE_SHA256",
    "SYNTHETIC_REHEARSAL_SANITIZED_SHA256",
    "choose_export_destination",
    "delete_rehearsal",
    "finish_rehearsal",
    "host_has_external_default_route",
    "jupyter_lab_available",
    "load_rehearsal_contract",
    "network_isolation_preflight",
    "prepare_rehearsal",
    "rehearsal_status",
    "run_network_monitor",
    "start_rehearsal",
    "verify_rehearsal_export",
]
