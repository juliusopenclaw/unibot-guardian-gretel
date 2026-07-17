from __future__ import annotations

import hashlib
import json
import os
import stat
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Any, Literal, TypedDict, cast


HELP_COSTS_V1 = {"A0": 0, "A1": 0, "A2": 5, "A3": 12, "A4": 25}
HELP_LEVELS_V1 = tuple(HELP_COSTS_V1)
COST_POLICY_VERSION = "unibot-help-cost-v1"
SESSION_STATE_SCHEMA_VERSION = "unibot-session-state-v1"
LOCAL_LEARNING_RECORD_SCHEMA_VERSION = "unibot-local-learning-record-v2"
SESSION_RETENTION_DAYS = 7
TRANSFER_TASK_SCHEMA_VERSION = "unibot-transfer-task-v1"
TRANSFER_TASK_ID = "synthetic-python-transfer-v1"
TRANSFER_TASK_PROMPT = (
    "Neue synthetische Python-Aufgabe: Beschreibe ohne UniBot-Hilfe die zwei kleinsten "
    "Prüfschritte, bevor du aus einer Liste unbekannter Länge einen Mittelwert berechnest."
)
TRANSFER_MAX_ANSWER_CHARACTERS = 4_000
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


class SessionContractV1(TypedDict):
    schema_version: str
    session_id: str
    pseudonym: str
    course_id: str
    assistance_mode: Literal["fixed", "adaptive"]
    fixed_help_level: str
    max_help_level: str
    planned_task_count: int
    cost_policy_version: str
    help_costs: dict[str, int]
    sharing_policy: str
    practice_scope: Literal["practice_only", "synthetic_exam_rehearsal"]
    exam_deployment_status: str
    created_at_utc: str
    contract_hash: str


class HelpEventV2(TypedDict):
    schema_version: str
    session_id: str
    task_id: str
    timestamp_utc: str
    requested_help_level: str
    effective_help_level: str
    assistance_points_delta: int
    assistance_points_for_task: int
    attempt_hash: str
    cell_hash: str
    source_anchor_ids: list[str]
    status: str
    own_attempt_present: bool
    revision_number: int
    accessibility_used: bool
    accessibility_neutral: bool


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _new_transfer_state() -> dict[str, Any]:
    return {
        "schema_version": TRANSFER_TASK_SCHEMA_VERSION,
        "task_id": TRANSFER_TASK_ID,
        "prompt_hash": _canonical_hash({"task_id": TRANSFER_TASK_ID, "prompt": TRANSFER_TASK_PROMPT}),
        "status": "not_started",
        "attempt_hash": "",
        "attempt_present": False,
        "answer_character_count": 0,
        "recorded_at_utc": "",
    }


def _validated_transfer_state(value: Any) -> dict[str, Any]:
    if value is None:
        return _new_transfer_state()
    if not isinstance(value, dict):
        raise ValueError("transfer state is invalid")
    expected = _new_transfer_state()
    if value.get("schema_version") != TRANSFER_TASK_SCHEMA_VERSION or value.get("task_id") != TRANSFER_TASK_ID:
        raise ValueError("transfer state schema is invalid")
    if value.get("prompt_hash") != expected["prompt_hash"]:
        raise ValueError("transfer prompt hash mismatch")
    status = str(value.get("status", "not_started"))
    if status not in {"not_started", "recorded"}:
        raise ValueError("transfer state status is invalid")
    attempt_hash = str(value.get("attempt_hash", ""))
    if attempt_hash and not re.fullmatch(r"[0-9a-f]{64}", attempt_hash):
        raise ValueError("transfer attempt hash is invalid")
    try:
        answer_character_count = int(value.get("answer_character_count", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("transfer answer length is invalid") from exc
    if not 0 <= answer_character_count <= TRANSFER_MAX_ANSWER_CHARACTERS:
        raise ValueError("transfer answer length is invalid")
    attempt_present = bool(value.get("attempt_present", False))
    if status == "recorded" and (not attempt_hash or not attempt_present or answer_character_count <= 0):
        raise ValueError("recorded transfer state is incomplete")
    if status == "not_started" and (attempt_hash or attempt_present or answer_character_count):
        raise ValueError("unstarted transfer state contains an attempt")
    return {
        **expected,
        "status": status,
        "attempt_hash": attempt_hash,
        "attempt_present": attempt_present,
        "answer_character_count": answer_character_count,
        "recorded_at_utc": str(value.get("recorded_at_utc", "")),
    }


def _safe_label(value: Any, *, fallback: str, maximum: int = 80) -> str:
    candidate = " ".join(str(value or "").strip().split())[:maximum]
    if not candidate:
        return fallback
    return "".join(character for character in candidate if character.isalnum() or character in " ._-" ).strip() or fallback


def _help_level(value: Any, *, fallback: str = "A2") -> str:
    candidate = str(value or fallback).strip().upper()
    return candidate if candidate in HELP_COSTS_V1 else fallback


def require_practice_boundary_confirmation(payload: dict[str, Any] | None) -> None:
    """Require an explicit learner acknowledgement on every public transport."""
    if not isinstance(payload, dict):
        raise ValueError("practice_scope_confirmation_required")
    if payload.get("practice_scope") != "practice_only" or payload.get("practice_scope_confirmed") is not True:
        raise ValueError("practice_scope_confirmation_required")


def _session_id(value: Any) -> str:
    candidate = str(value or "").strip()
    if not _SESSION_ID_PATTERN.fullmatch(candidate):
        raise ValueError("session_id is invalid")
    return candidate


def _notebook_id(value: Any) -> str:
    candidate = str(value or "").strip()
    if not re.fullmatch(r"[0-9a-f]{16}", candidate):
        raise ValueError("notebook_id is invalid")
    return candidate


def _session_paths(storage_root: Path, session_id: str) -> tuple[Path, Path, Path]:
    safe_id = _session_id(session_id)
    return (
        storage_root / f"{safe_id}.contract.json",
        storage_root / f"{safe_id}.state.json",
        storage_root / f"{safe_id}.jsonl",
    )


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
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


def _persisted_event(event: HelpEventV2 | dict[str, Any]) -> dict[str, Any]:
    """Remove the optional accessibility preference before local persistence."""
    persisted = dict(event)
    persisted.pop("accessibility_used", None)
    return persisted


def _local_learning_record(event: HelpEventV2 | dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": LOCAL_LEARNING_RECORD_SCHEMA_VERSION,
        "event": _persisted_event(event),
        "storage_policy": (
            "local metadata and hashes only; no cell, task, attempt, transcript, "
            "or accessibility-preference usage signal"
        ),
    }


def _rewrite_private_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_private_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("session metadata file is missing or symlinked")
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError("session metadata file permissions must be 0600")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("session metadata must be an object")
    return payload


def _state_record(
    session_id: str,
    status: str,
    *,
    contract_hash: str,
    notebook_ids: list[str] | tuple[str, ...] = (),
    transfer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in {"active", "stopped"}:
        raise ValueError("unsupported session state")
    return {
        "schema_version": SESSION_STATE_SCHEMA_VERSION,
        "session_id": _session_id(session_id),
        "status": status,
        "contract_hash": str(contract_hash),
        "notebook_ids": sorted({_notebook_id(item) for item in notebook_ids if str(item)}),
        "transfer": _validated_transfer_state(transfer),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _validated_contract(storage_root: Path, session_id: str) -> dict[str, Any]:
    contract_path, _, _ = _session_paths(storage_root, session_id)
    contract = _read_private_json(contract_path)
    contract_hash = str(contract.get("contract_hash", ""))
    without_hash = dict(contract)
    without_hash.pop("contract_hash", None)
    if not contract_hash or _canonical_hash(without_hash) != contract_hash:
        raise ValueError("session contract hash mismatch")
    if str(contract.get("session_id", "")) != session_id:
        raise ValueError("session contract id mismatch")
    return contract


def session_notebook_ids(storage_root: Path, session_id: str) -> list[str]:
    """Return only the sanitized notebook identifiers linked to a session."""
    safe_id = _session_id(session_id)
    _, state_path, _ = _session_paths(storage_root, safe_id)
    state = _read_private_json(state_path)
    if state.get("schema_version") != SESSION_STATE_SCHEMA_VERSION:
        raise ValueError("unsupported session state schema")
    if state.get("contract_hash") != _validated_contract(storage_root, safe_id).get("contract_hash"):
        raise ValueError("session state contract binding mismatch")
    notebook_ids = state.get("notebook_ids", [])
    if not isinstance(notebook_ids, list) or not all(isinstance(item, str) for item in notebook_ids):
        raise ValueError("session notebook metadata is invalid")
    return sorted({_notebook_id(item) for item in notebook_ids})


def register_session_notebook(storage_root: Path, session_id: str, notebook_id: str) -> None:
    """Bind a sanitized notebook identifier to the active session metadata."""
    safe_id = _session_id(session_id)
    safe_notebook_id = _notebook_id(notebook_id)
    _, state_path, _ = _session_paths(storage_root, safe_id)
    state = _read_private_json(state_path)
    if state.get("status") != "active":
        raise ValueError("only active sessions can register notebooks")
    existing = session_notebook_ids(storage_root, safe_id)
    _write_private_json(
        state_path,
        _state_record(
            safe_id,
            "active",
            contract_hash=str(state.get("contract_hash", "")),
            notebook_ids=[*existing, safe_notebook_id],
            transfer=state.get("transfer"),
        ),
    )


def active_session_metadata(storage_root: Path) -> list[dict[str, str]]:
    """Return only resumable session metadata, never notebook or learner text."""
    if not storage_root.exists():
        return []
    if storage_root.is_symlink() or not storage_root.is_dir():
        raise ValueError("session storage root is missing or symlinked")
    if stat.S_IMODE(storage_root.stat().st_mode) != 0o700:
        raise ValueError("session storage root permissions must be 0700")
    active: list[dict[str, str]] = []
    for state_path in sorted(storage_root.glob("*.state.json")):
        state = _read_private_json(state_path)
        if state.get("schema_version") != SESSION_STATE_SCHEMA_VERSION:
            raise ValueError("unsupported session state schema")
        session_id = _session_id(state.get("session_id"))
        if state.get("status") != "active":
            continue
        contract = _validated_contract(storage_root, session_id)
        if state.get("contract_hash") != contract.get("contract_hash"):
            raise ValueError("session state contract binding mismatch")
        active.append(
            {
                "session_id": session_id,
                "contract_hash": str(contract.get("contract_hash", "")),
                "course_id": str(contract.get("course_id", "")),
                "updated_at_utc": str(state.get("updated_at_utc", "")),
            }
        )
    return active


def delete_session_artifacts(storage_root: Path, session_id: str) -> bool:
    """Delete one session's metadata and event journal without following links."""
    if storage_root.is_symlink() or not storage_root.is_dir():
        raise ValueError("session storage root is missing or symlinked")
    paths = _session_paths(storage_root, session_id)
    present = False
    for path in paths:
        if path.exists() or path.is_symlink():
            if path.is_symlink():
                raise ValueError("refusing to delete symlinked session metadata")
            if not path.is_file():
                raise ValueError("session metadata path is not a file")
            path.unlink()
            present = True
    return present


def cleanup_expired_sessions(storage_root: Path, *, retention_days: int = SESSION_RETENTION_DAYS) -> list[str]:
    """Remove ended sessions after the declared retention window."""
    if not storage_root.exists():
        return []
    if storage_root.is_symlink() or not storage_root.is_dir():
        raise ValueError("session storage root is missing or symlinked")
    if stat.S_IMODE(storage_root.stat().st_mode) != 0o700:
        raise ValueError("session storage root permissions must be 0700")
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    removed: list[str] = []
    for state_path in sorted(storage_root.glob("*.state.json")):
        state = _read_private_json(state_path)
        if state.get("schema_version") != SESSION_STATE_SCHEMA_VERSION or state.get("status") != "stopped":
            continue
        try:
            updated = datetime.fromisoformat(str(state.get("updated_at_utc", "")))
        except ValueError:
            continue
        if updated.tzinfo is None or updated >= cutoff:
            continue
        session_id = _session_id(state.get("session_id"))
        if delete_session_artifacts(storage_root, session_id):
            removed.append(session_id)
    return removed


def create_session_contract(payload: dict[str, Any] | None = None) -> SessionContractV1:
    payload = payload or {}
    session_scope = str(payload.get("session_scope", "practice_only")).strip()
    if session_scope not in {"practice_only", "synthetic_exam_rehearsal"}:
        raise ValueError("session_scope is invalid")
    assistance_mode = str(payload.get("assistance_mode", "fixed")).strip().lower()
    if assistance_mode not in {"fixed", "adaptive"}:
        raise ValueError("assistance_mode must be fixed or adaptive")
    max_help_level = _help_level(payload.get("max_help_level"), fallback="A4")
    fixed_help_level = _help_level(payload.get("fixed_help_level"), fallback="A2")
    if session_scope == "synthetic_exam_rehearsal":
        assistance_mode = "adaptive"
        max_help_level = "A2"
        fixed_help_level = "A0"
    if HELP_COSTS_V1[fixed_help_level] > HELP_COSTS_V1[max_help_level]:
        raise ValueError("fixed_help_level must not exceed max_help_level")
    try:
        planned_task_count = int(payload.get("planned_task_count", 1))
    except (TypeError, ValueError) as exc:
        raise ValueError("planned_task_count must be an integer") from exc
    if not 1 <= planned_task_count <= 200:
        raise ValueError("planned_task_count must be between 1 and 200")
    created_at = datetime.now(timezone.utc).isoformat()
    contract_without_hash: dict[str, Any] = {
        "schema_version": "unibot-session-contract-v1",
        "session_id": secrets.token_urlsafe(18),
        "pseudonym": (
            "Synthetic Learner"
            if session_scope == "synthetic_exam_rehearsal"
            else _safe_label(payload.get("pseudonym"), fallback="Lernende Person")
        ),
        "course_id": (
            "synthetic-python-rehearsal-v1"
            if session_scope == "synthetic_exam_rehearsal"
            else _safe_label(payload.get("course_id"), fallback="python-practice")
        ),
        "assistance_mode": assistance_mode,
        "fixed_help_level": fixed_help_level,
        "max_help_level": max_help_level,
        "planned_task_count": planned_task_count,
        "cost_policy_version": COST_POLICY_VERSION,
        "help_costs": dict(HELP_COSTS_V1),
        "sharing_policy": (
            "local_hash_receipt_only_no_automatic_submission"
            if session_scope == "synthetic_exam_rehearsal"
            else "voluntary_metadata_preview_before_export"
        ),
        "practice_scope": session_scope,
        "exam_deployment_status": "not_cleared",
        "created_at_utc": created_at,
    }
    return cast(
        SessionContractV1,
        {**contract_without_hash, "contract_hash": _canonical_hash(contract_without_hash)},
    )


@dataclass
class LearningSession:
    contract: SessionContractV1
    storage_path: Path | None = None
    contract_path: Path | None = None
    state_path: Path | None = None
    events: list[HelpEventV2] = field(default_factory=list)
    stopped: bool = False
    transfer: dict[str, Any] = field(default_factory=_new_transfer_state)

    @classmethod
    def start(
        cls,
        payload: dict[str, Any] | None = None,
        *,
        storage_root: Path | None = None,
    ) -> "LearningSession":
        contract = create_session_contract(payload)
        storage_path = None
        contract_path = None
        state_path = None
        if storage_root is not None:
            if storage_root.exists() and storage_root.is_symlink():
                raise ValueError("session storage root must not be a symlink")
            storage_root.mkdir(parents=True, exist_ok=True)
            os.chmod(storage_root, 0o700)
            contract_path, state_path, storage_path = _session_paths(storage_root, contract["session_id"])
        session = cls(
            contract=contract,
            storage_path=storage_path,
            contract_path=contract_path,
            state_path=state_path,
        )
        if contract_path is not None and state_path is not None:
            _write_private_json(contract_path, dict(contract))
            _write_private_json(
                state_path,
                _state_record(contract["session_id"], "active", contract_hash=contract["contract_hash"]),
            )
        return session

    @classmethod
    def resume(cls, storage_root: Path, session_id: str | None = None) -> "LearningSession":
        active = active_session_metadata(storage_root)
        if session_id:
            safe_id = _session_id(session_id)
        elif len(active) == 1:
            safe_id = active[0]["session_id"]
        elif not active:
            raise ValueError("no active learning session to resume")
        else:
            raise ValueError("multiple active learning sessions require an explicit session_id")
        contract_path, state_path, storage_path = _session_paths(storage_root, safe_id)
        state = _read_private_json(state_path)
        if state.get("schema_version") != SESSION_STATE_SCHEMA_VERSION or state.get("status") != "active":
            raise ValueError("learning session is not resumable")
        contract_payload = _validated_contract(storage_root, safe_id)
        if state.get("contract_hash") != contract_payload.get("contract_hash"):
            raise ValueError("session state contract binding mismatch")
        events: list[HelpEventV2] = []
        persisted_records: list[dict[str, Any]] = []
        needs_event_migration = False
        if storage_path.exists():
            if storage_path.is_symlink() or stat.S_IMODE(storage_path.stat().st_mode) != 0o600:
                raise ValueError("session event journal permissions are invalid")
            for line in storage_path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if not isinstance(record, dict) or record.get("schema_version") not in {
                    "unibot-local-learning-record-v1",
                    LOCAL_LEARNING_RECORD_SCHEMA_VERSION,
                }:
                    raise ValueError("unsupported session event record")
                event = record.get("event")
                if not isinstance(event, dict) or event.get("session_id") != safe_id:
                    raise ValueError("session event binding mismatch")
                sanitized_event = _persisted_event(event)
                needs_event_migration = needs_event_migration or (
                    record.get("schema_version") != LOCAL_LEARNING_RECORD_SCHEMA_VERSION
                    or sanitized_event != event
                )
                events.append(cast(HelpEventV2, sanitized_event))
                persisted_records.append(_local_learning_record(sanitized_event))
            if needs_event_migration:
                _rewrite_private_jsonl(storage_path, persisted_records)
        return cls(
            contract=cast(SessionContractV1, contract_payload),
            storage_path=storage_path,
            contract_path=contract_path,
            state_path=state_path,
            events=events,
            transfer=_validated_transfer_state(state.get("transfer")),
        )

    def task_events(self, task_id: str) -> list[HelpEventV2]:
        return [event for event in self.events if event["task_id"] == task_id]

    def current_level(self, task_id: str) -> str:
        events = self.task_events(task_id)
        if not events:
            return "A0"
        # A0 and A1 are intentionally both cost-free; progression is ordered by
        # pedagogical level, not by the assistance budget.
        return max((event["effective_help_level"] for event in events), key=HELP_LEVELS_V1.index)

    def last_attempt_hash(self, task_id: str) -> str:
        events = self.task_events(task_id)
        return events[-1]["attempt_hash"] if events else ""

    def record_turn(self, turn: dict[str, Any]) -> HelpEventV2:
        if self.stopped:
            raise ValueError("learning session is stopped")
        task_id = str(turn["task_id"])
        prior = self.task_events(task_id)
        event = HelpEventV2(
            schema_version="unibot-help-event-v2",
            session_id=self.contract["session_id"],
            task_id=task_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            requested_help_level=str(turn["requested_help_level"]),
            effective_help_level=str(turn["effective_help_level"]),
            assistance_points_delta=int(turn["assistance_points_delta"]),
            assistance_points_for_task=int(turn["assistance_points_for_task"]),
            attempt_hash=str(turn["attempt_hash"]),
            cell_hash=str(turn["cell_hash"]),
            source_anchor_ids=list(turn.get("source_anchor_ids", [])),
            status=str(turn["status"]),
            own_attempt_present=bool(turn.get("own_attempt_present", False)),
            revision_number=len({item["attempt_hash"] for item in prior if item["attempt_hash"]}),
            accessibility_used=bool(turn.get("accessibility_used", False)),
            accessibility_neutral=True,
        )
        self.events.append(event)
        self._append_local(event)
        return event

    def _append_local(self, event: HelpEventV2) -> None:
        if self.storage_path is None:
            return
        record = _local_learning_record(event)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        descriptor = os.open(self.storage_path, flags, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(self.storage_path, 0o600)

    def summary(self) -> dict[str, Any]:
        by_level: dict[str, int] = {}
        task_points: dict[str, int] = {}
        attempts: set[str] = set()
        source_ids: set[str] = set()
        blocked_count = 0
        for event in self.events:
            level = event["effective_help_level"]
            by_level[level] = by_level.get(level, 0) + 1
            task_points[event["task_id"]] = max(task_points.get(event["task_id"], 0), event["assistance_points_for_task"])
            if event["attempt_hash"]:
                attempts.add(event["attempt_hash"])
            source_ids.update(event["source_anchor_ids"])
            if event["status"] not in {"allowed", "downgraded"}:
                blocked_count += 1
        return {
            "event_count": len(self.events),
            "blocked_or_flagged_count": blocked_count,
            "by_help_level": by_level,
            "assistance_points_by_task": task_points,
            "assistance_points_used": sum(task_points.values()),
            "own_attempt_count": len(attempts),
            "source_anchor_ids": sorted(source_ids),
        }

    def _persist_state(self, status: str) -> None:
        if self.state_path is None:
            return
        current_state = _read_private_json(self.state_path)
        _write_private_json(
            self.state_path,
            _state_record(
                self.contract["session_id"],
                status,
                contract_hash=self.contract["contract_hash"],
                notebook_ids=current_state.get("notebook_ids", []),
                transfer=self.transfer,
            ),
        )

    def _transfer_report(self) -> dict[str, Any]:
        state = _validated_transfer_state(self.transfer)
        status = state["status"] if self.stopped else "locked_until_session_stop"
        return {
            "schema_version": TRANSFER_TASK_SCHEMA_VERSION,
            "task_id": TRANSFER_TASK_ID,
            "status": status,
            "prompt_hash": state["prompt_hash"],
            "attempt_present": bool(state["attempt_present"]),
            "attempt_hash": state["attempt_hash"],
            "answer_character_count": int(state["answer_character_count"]),
            "recorded_at_utc": state["recorded_at_utc"],
            "help_allowed": False,
            "assessment_status": "not_assessed",
            "raw_prompt_included": False,
            "raw_attempt_included": False,
        }

    def transfer_prompt(self) -> dict[str, Any]:
        if not self.stopped:
            raise ValueError("transfer_available_after_session_stop")
        return {
            "schema_version": TRANSFER_TASK_SCHEMA_VERSION,
            "task_id": TRANSFER_TASK_ID,
            "prompt": TRANSFER_TASK_PROMPT,
            "prompt_hash": self.transfer["prompt_hash"],
            "status": self.transfer["status"],
            "help_allowed": False,
            "raw_prompt_stored": False,
            "exam_deployment_status": "not_cleared",
        }

    def record_transfer_attempt(self, task_id: str, answer: str) -> dict[str, Any]:
        if not self.stopped:
            raise ValueError("transfer_available_after_session_stop")
        if str(task_id).strip() != TRANSFER_TASK_ID:
            raise ValueError("transfer task id mismatch")
        normalized = str(answer).strip()[:TRANSFER_MAX_ANSWER_CHARACTERS]
        if not normalized:
            raise ValueError("transfer_attempt_required")
        from .guardian import detect_privacy_flags

        if detect_privacy_flags(normalized):
            raise ValueError("transfer_attempt_contains_private_data")
        self.transfer = {
            **_new_transfer_state(),
            "status": "recorded",
            "attempt_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "attempt_present": True,
            "answer_character_count": len(normalized),
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        self._persist_state("stopped")
        return self._transfer_report()

    def report(self) -> dict[str, Any]:
        summary = self.summary()
        report_without_hash = {
            "schema_version": "unibot-independence-report-v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "session_id": self.contract["session_id"],
            "pseudonym": self.contract["pseudonym"],
            "course_id": self.contract["course_id"],
            "contract_hash": self.contract["contract_hash"],
            "cost_policy_version": self.contract["cost_policy_version"],
            "accessibility_policy": "optional_local_display_score_neutral_no_usage_metadata",
            "accessibility_usage_metadata_collected": False,
            **summary,
            "transfer_tasks": [self._transfer_report()],
            "uncertainty": "Help exposure and documented attempts do not prove authorship or learning outcome.",
            "assessment_policy": "Voluntary learning report; no automatic grade, proctoring, or AI detection.",
            "raw_cell_text_included": False,
            "raw_attempt_text_included": False,
            "local_paths_included": False,
            "exam_deployment_status": "not_cleared",
        }
        return {**report_without_hash, "report_hash": _canonical_hash(report_without_hash)}

    def stop(self) -> dict[str, Any]:
        self.stopped = True
        self._persist_state("stopped")
        return {"status": "stopped", "session_id": self.contract["session_id"], "report": self.report()}
