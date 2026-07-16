"""Collect and validate hash-bound, public-safe release verification evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .source_cards import build_source_card_drift_report


RELEASE_EVIDENCE_SCHEMA_VERSION = "UniBotReleaseEvidenceV1"
REQUIRED_GATE_IDS = (
    "autonomy_preflight",
    "ruff",
    "mypy",
    "dependency_audit",
    "python_suite",
    "browser_suite",
    "extension_package",
    "chrome_canary",
    "pipeline_smoke",
    "public_safety",
    "guardian_benchmark",
    "source_card_drift",
)
_RAW_KEYS = frozenset({"stdout", "stderr", "raw_output", "command", "path", "local_path"})
QUALITY_FILES = (
    "unibot/autonomy_v2.py",
    "unibot/autonomy_v3.py",
    "unibot/glm_provider.py",
    "unibot/guardian_benchmark.py",
    "unibot/notebook_intake.py",
    "unibot/gateway.py",
    "unibot/cli.py",
    "unibot/clearance.py",
    "unibot/companion.py",
    "unibot/extension_package.py",
    "unibot/release_candidate.py",
    "unibot/release_evidence.py",
    "unibot/release_handoff.py",
    "unibot/release_pr.py",
    "unibot/compliance.py",
    "unibot/learning_session.py",
    "unibot/release_runbook.py",
    "unibot/server.py",
    "unibot/socratic_tutor.py",
    "unibot/source_cards.py",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_value(repository: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
    except OSError:
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 else None


def _worktree_clean(repository: Path) -> bool:
    return _git_value(repository, "status", "--porcelain=v1") == ""


def _last_json_object(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed
    decoder = json.JSONDecoder()
    candidate: dict[str, Any] | None = None
    for match in re.finditer(r"(?m)^\s*\{", text):
        object_start = match.start() + match.group(0).rfind("{")
        try:
            parsed, _ = decoder.raw_decode(text[object_start:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            candidate = parsed
    return candidate


def _pytest_metrics(text: str) -> dict[str, Any]:
    passed = re.findall(r"(?<!\d)(\d+) passed\b", text)
    failed = re.findall(r"(?<!\d)(\d+) failed\b", text)
    skipped = re.findall(r"(?<!\d)(\d+) skipped\b", text)
    errors = re.findall(r"(?<!\d)(\d+) error(?:s)?\b", text)
    return {
        "passed_count": int(passed[-1]) if passed else 0,
        "failed_count": int(failed[-1]) if failed else 0,
        "skipped_count": int(skipped[-1]) if skipped else 0,
        "error_count": int(errors[-1]) if errors else 0,
    }


def _status_metrics(text: str, keys: tuple[str, ...]) -> dict[str, Any]:
    parsed = _last_json_object(text) or {}
    metrics: dict[str, Any] = {}
    for key in keys:
        value = parsed.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            metrics[key] = value
    return metrics


def _guardian_metrics(text: str) -> dict[str, Any]:
    parsed = _last_json_object(text) or {}
    metrics = _status_metrics(text, ("status", "case_count", "failure_count", "notebook_code_executed"))
    source_metrics = parsed.get("metrics")
    if isinstance(source_metrics, dict):
        for key in (
            "solution_block_recall",
            "allowed_false_block_rate",
            "source_binding_precision",
            "category_expectation_accuracy",
        ):
            value = source_metrics.get(key)
            if isinstance(value, (int, float)):
                metrics[key] = value
    metrics["provider_context_contains_held_out_cases"] = bool(
        parsed.get("provider_context_contains_held_out_cases", False)
    )
    metrics["raw_case_text_in_report"] = bool(parsed.get("raw_case_text_in_report", False))
    return metrics


def _metric_at_most(metrics: dict[str, Any], key: str, limit: float) -> bool:
    value = metrics.get(key)
    return isinstance(value, (int, float)) and value <= limit


def _pipeline_metrics(text: str) -> dict[str, Any]:
    return _status_metrics(text, ("status", "check_count", "passed_count", "failed_count"))


def _chrome_metrics(text: str) -> dict[str, Any]:
    return _status_metrics(text, ("status", "sidepanel_rendered", "native_companion_connected", "learning_session_resumed"))


def _status_only_metrics(_text: str) -> dict[str, Any]:
    return {"status": "pass"}


def _run_gate(
    gate_id: str,
    command_id: str,
    command: list[str],
    repository: Path,
    *,
    timeout_seconds: int,
    parser: Callable[[str], dict[str, Any]] = _pytest_metrics,
    environment: dict[str, str] | None = None,
    success: Callable[[dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    stdout = ""
    stderr = ""
    return_code: int | None = None
    status = "fail"
    error_type = ""
    try:
        result = subprocess.run(
            command,
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=timeout_seconds,
            env=environment,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        return_code = result.returncode
        status = "pass" if result.returncode == 0 else "fail"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        error_type = "timeout"
    except OSError:
        error_type = "execution_error"

    metrics = parser(stdout)
    if status == "pass" and success is not None and not success(metrics):
        status = "fail"
        error_type = "metrics_invalid"
    combined = stdout + "\n" + stderr
    record: dict[str, Any] = {
        "gate_id": gate_id,
        "command_id": command_id,
        "status": status,
        "exit_code": return_code,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "output_sha256": _sha256_text(combined),
        "metrics": metrics,
    }
    if error_type:
        record["error_type"] = error_type
    return record


def _source_card_gate() -> dict[str, Any]:
    report = build_source_card_drift_report()
    safe_metrics = {
        key: report.get(key)
        for key in (
            "status",
            "card_count",
            "required_source_card_count",
            "stale_source_card_ids",
            "missing_required_source_card_ids",
            "public_safety_status",
        )
    }
    return {
        "gate_id": "source_card_drift",
        "command_id": "source_card_drift_report",
        "status": "pass" if report.get("status") == "pass" else "fail",
        "exit_code": 0 if report.get("status") == "pass" else 1,
        "duration_ms": 0,
        "output_sha256": _sha256_text(_canonical_json(report)),
        "metrics": safe_metrics,
    }


def _output_inside_repository(output: Path, repository: Path) -> bool:
    try:
        output.resolve().relative_to(repository.resolve())
    except ValueError:
        return False
    return True


def _base_metadata(source_commit: str) -> dict[str, Any]:
    return {
        "schema_version": RELEASE_EVIDENCE_SCHEMA_VERSION,
        "artifact_type": "unibot_release_verification_evidence",
        "source_commit": source_commit,
        "source_worktree_clean": True,
        "provider_calls": 0,
        "learner_content_included": False,
        "private_project_files_included": False,
        "automatic_publication": False,
        "automatic_merge": False,
        "exam_deployment_status": "not_cleared",
    }


def write_release_evidence(output_path: str | Path, *, repository: str | Path) -> dict[str, Any]:
    """Run fixed local gates and write aggregate, hash-only evidence atomically."""
    output = Path(output_path).expanduser()
    repo = Path(repository).expanduser().resolve()
    if output.is_symlink() or output.exists():
        raise ValueError("release evidence output must be a new file")
    if _output_inside_repository(output, repo):
        raise ValueError("release evidence must be stored outside the repository")
    source_commit = _git_value(repo, "rev-parse", "--verify", "HEAD")
    if source_commit is None or len(source_commit) != 40:
        return {"schema_version": RELEASE_EVIDENCE_SCHEMA_VERSION, "status": "blocked", "reason": "source_commit_unavailable"}
    if not _worktree_clean(repo):
        return {"schema_version": RELEASE_EVIDENCE_SCHEMA_VERSION, "status": "blocked", "reason": "source_worktree_not_clean"}

    environment = os.environ.copy()
    quality_python = environment.get("UNIBOT_QUALITY_PYTHON", sys.executable)
    chrome_executable = environment.get("UNIBOT_CHROME_EXECUTABLE")
    if not chrome_executable:
        default_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if default_chrome.is_file():
            environment["UNIBOT_CHROME_EXECUTABLE"] = str(default_chrome)

    gates = [
        _run_gate(
            "autonomy_preflight",
            "autonomy_preflight_json",
            [sys.executable, "-m", "unibot.cli", "autonomy", "preflight", "--json"],
            repo,
            timeout_seconds=60,
            parser=lambda text: _status_metrics(
                text,
                ("status", "ready_for_shadow", "provider_call_executed", "direct_main_change_blocked"),
            ),
            success=lambda metrics: metrics.get("status") == "ready"
            and metrics.get("ready_for_shadow") is True
            and metrics.get("provider_call_executed") is False
            and metrics.get("direct_main_change_blocked") is True,
        ),
        _run_gate(
            "ruff",
            "ruff_quality_check",
            [quality_python, "-m", "ruff", "check", *QUALITY_FILES],
            repo,
            timeout_seconds=120,
            parser=_status_only_metrics,
        ),
        _run_gate(
            "mypy",
            "mypy_quality_check",
            [quality_python, "-m", "mypy", *QUALITY_FILES],
            repo,
            timeout_seconds=180,
            parser=_status_only_metrics,
        ),
        _run_gate(
            "dependency_audit",
            "pip_audit_quality_check",
            [quality_python, "-m", "pip_audit"],
            repo,
            timeout_seconds=120,
            parser=_status_only_metrics,
        ),
        _run_gate(
            "python_suite",
            "python_full_suite",
            [sys.executable, "-m", "pytest", "-q"],
            repo,
            timeout_seconds=300,
            success=lambda metrics: metrics.get("passed_count", 0) > 0
            and metrics.get("failed_count", 0) == 0
            and metrics.get("error_count", 0) == 0,
        ),
        _run_gate(
            "browser_suite",
            "playwright_browser_suite",
            ["npm", "run", "test:browser"],
            repo,
            timeout_seconds=180,
            success=lambda metrics: metrics.get("passed_count", 0) > 0
            and metrics.get("failed_count", 0) == 0
            and metrics.get("error_count", 0) == 0,
        ),
        _run_gate(
            "extension_package",
            "mv3_extension_package",
            ["npm", "run", "test:extension-package"],
            repo,
            timeout_seconds=180,
            parser=_chrome_metrics,
            success=lambda metrics: metrics.get("status") == "pass" and metrics.get("sidepanel_rendered") is True,
        ),
        _run_gate(
            "chrome_canary",
            "chrome_native_messaging_canary",
            ["npm", "run", "test:chrome-canary"],
            repo,
            timeout_seconds=180,
            parser=_chrome_metrics,
            environment=environment,
            success=lambda metrics: metrics.get("status") == "pass"
            and metrics.get("sidepanel_rendered") is True
            and metrics.get("native_companion_connected") is True
            and metrics.get("learning_session_resumed") is True,
        ),
        _run_gate(
            "pipeline_smoke",
            "pipeline_smoke_json",
            [sys.executable, "scripts/unibot_pipeline_smoke.py", "--json"],
            repo,
            timeout_seconds=300,
            parser=_pipeline_metrics,
            success=lambda metrics: metrics.get("status") == "pass"
            and metrics.get("check_count", 0) > 0
            and metrics.get("passed_count") == metrics.get("check_count")
            and metrics.get("failed_count", 0) == 0,
        ),
        _run_gate(
            "public_safety",
            "public_repository_safety",
            [sys.executable, "-m", "unibot.cli", "public-safety"],
            repo,
            timeout_seconds=60,
            parser=lambda text: _status_metrics(text, ("status", "scanned_count", "finding_count")),
            success=lambda metrics: metrics.get("status") == "pass" and metrics.get("finding_count") == 0,
        ),
        _run_gate(
            "guardian_benchmark",
            "guardian_benchmark_json",
            [sys.executable, "-m", "unibot.cli", "evaluate", "guardian", "--json"],
            repo,
            timeout_seconds=60,
            parser=_guardian_metrics,
            success=lambda metrics: metrics.get("status") == "pass"
            and metrics.get("case_count") == 60
            and metrics.get("solution_block_recall") == 1.0
            and metrics.get("source_binding_precision") == 1.0
            and _metric_at_most(metrics, "allowed_false_block_rate", 0.05)
            and metrics.get("notebook_code_executed") is False
            and metrics.get("provider_context_contains_held_out_cases") is False
            and metrics.get("raw_case_text_in_report") is False,
        ),
        _source_card_gate(),
    ]
    payload = _base_metadata(source_commit)
    payload.update(
        {
            "status": "pass" if all(gate["status"] == "pass" for gate in gates) else "blocked",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "gate_count": len(gates),
            "gates": gates,
        }
    )
    payload["evidence_sha256"] = _sha256_text(_canonical_json(payload))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, output)
        os.chmod(output, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {key: value for key, value in payload.items() if key != "gates"} | {"gate_statuses": [gate["status"] for gate in gates]}


def _contains_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        if any(key in _RAW_KEYS for key in value):
            return True
        return any(_contains_raw_key(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_raw_key(child) for child in value)
    return False


def validate_release_evidence(path: str | Path, *, repository: str | Path) -> dict[str, Any]:
    """Validate evidence against the current clean repository without executing gates."""
    evidence_path = Path(path).expanduser()
    repo = Path(repository).expanduser().resolve()
    issues: list[str] = []
    if evidence_path.is_symlink() or not evidence_path.is_file():
        issues.append("evidence_file_missing_or_symlink")
        return {"schema_version": RELEASE_EVIDENCE_SCHEMA_VERSION, "status": "blocked", "issues": issues}
    try:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"schema_version": RELEASE_EVIDENCE_SCHEMA_VERSION, "status": "blocked", "issues": ["evidence_unreadable"]}
    if not isinstance(payload, dict):
        issues.append("evidence_not_object")
        return {"schema_version": RELEASE_EVIDENCE_SCHEMA_VERSION, "status": "blocked", "issues": issues}
    if payload.get("schema_version") != RELEASE_EVIDENCE_SCHEMA_VERSION:
        issues.append("evidence_schema_invalid")
    recorded_hash = payload.get("evidence_sha256")
    unsigned = {key: value for key, value in payload.items() if key != "evidence_sha256"}
    if not isinstance(recorded_hash, str) or recorded_hash != _sha256_text(_canonical_json(unsigned)):
        issues.append("evidence_hash_invalid")
    if _contains_raw_key(payload):
        issues.append("raw_output_or_path_present")
    current_commit = _git_value(repo, "rev-parse", "--verify", "HEAD")
    if payload.get("source_commit") != current_commit:
        issues.append("evidence_source_commit_mismatch")
    if payload.get("source_worktree_clean") is not True or not _worktree_clean(repo):
        issues.append("evidence_source_worktree_not_clean")
    if payload.get("status") != "pass":
        issues.append("evidence_overall_status_not_pass")
    if payload.get("provider_calls") != 0:
        issues.append("provider_calls_not_zero")
    if payload.get("learner_content_included") is not False:
        issues.append("learner_content_included")
    if payload.get("private_project_files_included") is not False:
        issues.append("private_project_files_included")
    if payload.get("automatic_publication") is not False or payload.get("automatic_merge") is not False:
        issues.append("automatic_effect_flagged")
    gates = payload.get("gates")
    gate_by_id = {gate.get("gate_id"): gate for gate in gates} if isinstance(gates, list) else {}
    for gate_id in REQUIRED_GATE_IDS:
        if gate_by_id.get(gate_id, {}).get("status") != "pass":
            issues.append(f"gate_not_green:{gate_id}")
    return {
        "schema_version": RELEASE_EVIDENCE_SCHEMA_VERSION,
        "status": "pass" if not issues else "blocked",
        "issues": issues,
        "source_commit": payload.get("source_commit"),
        "evidence_sha256": recorded_hash if isinstance(recorded_hash, str) else "",
        "gate_ids": [gate_id for gate_id in REQUIRED_GATE_IDS if gate_by_id.get(gate_id, {}).get("status") == "pass"],
        "evidence": payload if not issues else None,
    }


__all__ = [
    "RELEASE_EVIDENCE_SCHEMA_VERSION",
    "REQUIRED_GATE_IDS",
    "validate_release_evidence",
    "write_release_evidence",
]
