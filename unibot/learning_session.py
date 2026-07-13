from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict, cast


HELP_COSTS_V1 = {"A0": 0, "A1": 0, "A2": 5, "A3": 12, "A4": 25}
HELP_LEVELS_V1 = tuple(HELP_COSTS_V1)
COST_POLICY_VERSION = "unibot-help-cost-v1"


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
    accessibility_neutral: bool


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _safe_label(value: Any, *, fallback: str, maximum: int = 80) -> str:
    candidate = " ".join(str(value or "").strip().split())[:maximum]
    if not candidate:
        return fallback
    return "".join(character for character in candidate if character.isalnum() or character in " ._-" ).strip() or fallback


def _help_level(value: Any, *, fallback: str = "A2") -> str:
    candidate = str(value or fallback).strip().upper()
    return candidate if candidate in HELP_COSTS_V1 else fallback


def create_session_contract(payload: dict[str, Any] | None = None) -> SessionContractV1:
    payload = payload or {}
    assistance_mode = str(payload.get("assistance_mode", "fixed")).strip().lower()
    if assistance_mode not in {"fixed", "adaptive"}:
        raise ValueError("assistance_mode must be fixed or adaptive")
    max_help_level = _help_level(payload.get("max_help_level"), fallback="A4")
    fixed_help_level = _help_level(payload.get("fixed_help_level"), fallback="A2")
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
        "pseudonym": _safe_label(payload.get("pseudonym"), fallback="Lernende Person"),
        "course_id": _safe_label(payload.get("course_id"), fallback="python-practice"),
        "assistance_mode": assistance_mode,
        "fixed_help_level": fixed_help_level,
        "max_help_level": max_help_level,
        "planned_task_count": planned_task_count,
        "cost_policy_version": COST_POLICY_VERSION,
        "help_costs": dict(HELP_COSTS_V1),
        "sharing_policy": "voluntary_metadata_preview_before_export",
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
    events: list[HelpEventV2] = field(default_factory=list)
    stopped: bool = False

    @classmethod
    def start(
        cls,
        payload: dict[str, Any] | None = None,
        *,
        storage_root: Path | None = None,
    ) -> "LearningSession":
        contract = create_session_contract(payload)
        storage_path = None
        if storage_root is not None:
            storage_root.mkdir(parents=True, exist_ok=True)
            os.chmod(storage_root, 0o700)
            storage_path = storage_root / f"{contract['session_id']}.jsonl"
        return cls(contract=contract, storage_path=storage_path)

    def task_events(self, task_id: str) -> list[HelpEventV2]:
        return [event for event in self.events if event["task_id"] == task_id]

    def current_level(self, task_id: str) -> str:
        events = self.task_events(task_id)
        if not events:
            return "A0"
        return max((event["effective_help_level"] for event in events), key=lambda level: HELP_COSTS_V1[level])

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
            accessibility_neutral=True,
        )
        self.events.append(event)
        self._append_local(event)
        return event

    def _append_local(self, event: HelpEventV2) -> None:
        if self.storage_path is None:
            return
        record = {
            "schema_version": "unibot-local-learning-record-v1",
            "event": event,
            "storage_policy": "local metadata and hashes only; no cell, task, attempt, or transcript text",
        }
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        descriptor = os.open(self.storage_path, flags, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")

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
            **summary,
            "transfer_tasks": [],
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
        return {"status": "stopped", "session_id": self.contract["session_id"], "report": self.report()}
