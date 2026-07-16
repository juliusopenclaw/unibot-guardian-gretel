"""Local, review-first orchestration contracts for the UniBot v3 loop.

This module deliberately contains no network client and no shell command input
path. Provider calls, Codex sessions, and GitHub publishing are injected behind
small interfaces so the safety properties can be tested with synthetic data.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Protocol

try:  # macOS and other POSIX systems
    import fcntl
except ImportError:  # pragma: no cover - retained for Windows packaging
    fcntl = None  # type: ignore[assignment]

from .public_safety import scan_text


AUTONOMY_SCHEMA_VERSION = "unibot-autonomy-v3"
GLM_PROPOSAL_SCHEMA_VERSION = "GLMProposalV1"
GLM_REVIEW_SCHEMA_VERSION = "GLMReviewV2"
CODEX_REVIEW_SCHEMA_VERSION = "CodexReviewV1"
EVIDENCE_SCHEMA_VERSION = "ImplementationEvidenceV1"
RUN_SCHEMA_VERSION = "AutonomyRunV3"
EVOLUTION_CHUNK_SCHEMA_VERSION = "EvolutionChunkContractV1"
THREE_GOLDEN_RULES_EVIDENCE_SCHEMA_VERSION = "ThreeGoldenRulesEvidenceV1"
IMPROVEMENT_PATTERN_SCHEMA_VERSION = "ImprovementPatternV1"

PROVIDER_PARKED = "parked_awaiting_zai_balance"
PROVIDER_ENABLED = "enabled_public_unibot_only"
MODEL_VERSION = "glm-5.2"
MAX_FILES = 4
MAX_GLM_CALLS = 2
WARN_USD = 15.0
HARD_STOP_USD = 20.0
ROLLOUT_TARGET = 10
CANARY_MERGE_TARGET = 3
STALE_RUN_SECONDS = 60 * 60

RUN_STATES = (
    "queued",
    "proposed",
    "implementing",
    "deterministic_green",
    "codex_review_green",
    "glm_approved",
    "ci_green",
    "ready_for_human_merge",
    "human_merged",
    "blocked",
    "retryable",
    "gretel_proposed",
)

TRANSITIONS: dict[str, set[str]] = {
    "queued": {"proposed", "gretel_proposed", "blocked", "retryable"},
    "proposed": {"implementing", "blocked", "retryable"},
    "implementing": {"deterministic_green", "blocked", "retryable"},
    "deterministic_green": {"codex_review_green", "blocked", "retryable"},
    "codex_review_green": {"glm_approved", "blocked", "retryable"},
    "glm_approved": {"ci_green", "blocked", "retryable"},
    "ci_green": {"ready_for_human_merge", "blocked", "retryable"},
    "ready_for_human_merge": {"human_merged", "blocked"},
    "human_merged": set(),
    "blocked": set(),
    "retryable": set(),
    "gretel_proposed": set(),
}

SAFE_SOURCES = {"main_commit", "failing_check", "github_issue", "measured_gap", "active_milestone"}
SAFE_RISKS = {"low", "medium", "high", "critical"}
SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
SAFE_GIT_COMMIT = re.compile(r"^[0-9a-fA-F]{7,64}$")
PRIVATE_MARKERS = ("private", "icloud", "fallakte", "mail", "health", "notebook", "solution", "exam")
COMMAND_MARKERS = re.compile(r"(?:\$\(|`|;|&&|\|\||\b(?:bash|sh|zsh|powershell|python)\s+-c\b)")


class AutonomyValidationError(ValueError):
    pass


class LeaseBusy(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def _ensure_private_state_path(path: Path) -> None:
    if path.parent.is_symlink():
        raise AutonomyValidationError("state_parent_symlink_not_allowed")
    if not path.parent.exists():
        path.parent.mkdir(mode=0o700, parents=True)
        os.chmod(path.parent, 0o700)
    parent_stat = path.parent.stat()
    if parent_stat.st_uid != os.getuid() or stat.S_IMODE(parent_stat.st_mode) != 0o700:
        raise AutonomyValidationError("state_parent_must_be_owned_and_0700")
    if path.is_symlink():
        raise AutonomyValidationError("state_symlink_not_allowed")
    if path.exists() and stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise AutonomyValidationError("state_file_permissions_must_be_0600")


def _atomic_write_private_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_private_state_path(path)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def _read_private_json(path: Path, *, schema_version: str) -> dict[str, Any]:
    _ensure_private_state_path(path)
    if not path.exists():
        raise AutonomyValidationError("state_file_missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AutonomyValidationError("state_file_invalid_json") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != schema_version:
        raise AutonomyValidationError("state_file_schema_invalid")
    return payload


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug[:60] or "work"


def _safe_relative_path(raw: str) -> str:
    value = str(raw or "").replace("\\", "/")
    path = Path(value)
    lowered = value.lower()
    if not value or path.is_absolute() or ".." in path.parts or value.startswith("~"):
        raise AutonomyValidationError("path_must_be_relative")
    if any(marker in lowered for marker in PRIVATE_MARKERS):
        raise AutonomyValidationError("private_path_not_allowed")
    if value.startswith(".") or "/." in value:
        raise AutonomyValidationError("hidden_path_not_allowed")
    return value


def _validate_ids(values: Iterable[str], label: str) -> list[str]:
    cleaned = []
    for raw in values:
        value = str(raw)
        if not SAFE_ID.fullmatch(value) or COMMAND_MARKERS.search(value):
            raise AutonomyValidationError(f"invalid_{label}")
        cleaned.append(value)
    return list(dict.fromkeys(cleaned))


@dataclass(frozen=True)
class EvolutionChunkContractV1:
    failure_class: str
    generalized_rule: str
    transfer_targets: tuple[str, ...]
    positive_fixture_ids: tuple[str, ...]
    negative_fixture_ids: tuple[str, ...]
    recurrence_monitor_id: str
    human_gate: str = "required"

    def validate(self) -> list[str]:
        errors: list[str] = []
        try:
            _validate_ids((self.failure_class,), "failure_class")
            transfers = _validate_ids(self.transfer_targets, "transfer_targets")
            positives = _validate_ids(self.positive_fixture_ids, "positive_fixture_ids")
            negatives = _validate_ids(self.negative_fixture_ids, "negative_fixture_ids")
            _validate_ids((self.recurrence_monitor_id,), "recurrence_monitor_id")
        except AutonomyValidationError as error:
            errors.append(str(error))
            transfers, positives, negatives = [], [], []
        if len(transfers) < 2:
            errors.append("two_distinct_transfer_targets_required")
        if not positives or not negatives:
            errors.append("positive_and_negative_fixtures_required")
        if set(positives) & set(negatives):
            errors.append("positive_and_negative_fixtures_must_differ")
        if not self.generalized_rule.strip():
            errors.append("generalized_rule_required")
        elif scan_text(self.generalized_rule, "evolution-generalized-rule")["status"] != "pass":
            errors.append("generalized_rule_public_safety_failed")
        if self.human_gate != "required":
            errors.append("human_gate_must_be_required")
        return list(dict.fromkeys(errors))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": EVOLUTION_CHUNK_SCHEMA_VERSION,
            "failure_class": self.failure_class,
            "generalized_rule": self.generalized_rule,
            "transfer_targets": list(self.transfer_targets),
            "positive_fixture_ids": list(self.positive_fixture_ids),
            "negative_fixture_ids": list(self.negative_fixture_ids),
            "recurrence_monitor_id": self.recurrence_monitor_id,
            "human_gate": self.human_gate,
        }
        if include_hash:
            payload["contract_hash"] = sha256_json(payload)
        return payload

    @property
    def contract_hash(self) -> str:
        return sha256_json(self.to_dict(include_hash=False))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvolutionChunkContractV1":
        if not isinstance(payload, dict):
            raise AutonomyValidationError("evolution_chunk_must_be_object")
        contract = cls(
            failure_class=str(payload.get("failure_class", "")),
            generalized_rule=str(payload.get("generalized_rule", "")),
            transfer_targets=tuple(str(value) for value in payload.get("transfer_targets", [])),
            positive_fixture_ids=tuple(str(value) for value in payload.get("positive_fixture_ids", [])),
            negative_fixture_ids=tuple(str(value) for value in payload.get("negative_fixture_ids", [])),
            recurrence_monitor_id=str(payload.get("recurrence_monitor_id", "")),
            human_gate=str(payload.get("human_gate", "required")),
        )
        errors = contract.validate()
        if errors:
            raise AutonomyValidationError(",".join(errors))
        supplied_hash = payload.get("contract_hash")
        if supplied_hash is not None and supplied_hash != contract.contract_hash:
            raise AutonomyValidationError("evolution_contract_hash_mismatch")
        return contract


@dataclass(frozen=True)
class ThreeGoldenRulesEvidenceV1:
    work_item_hash: str
    contract_hash: str
    test_evidence_hash: str
    test_ids_passed: tuple[str, ...]
    recurrence_count: int
    review_gate: str = "human_required"

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": THREE_GOLDEN_RULES_EVIDENCE_SCHEMA_VERSION,
            "work_item_hash": self.work_item_hash,
            "contract_hash": self.contract_hash,
            "test_evidence_hash": self.test_evidence_hash,
            "test_ids_passed": sorted(self.test_ids_passed),
            "recurrence_count": int(self.recurrence_count),
            "generalization_gate": "pass",
            "harness_gate": "pass",
            "recursive_self_improvement_gate": "review_required",
            "review_gate": self.review_gate,
            "automatic_apply": False,
        }
        if include_hash:
            payload["evidence_hash"] = sha256_json(payload)
        return payload


@dataclass(frozen=True)
class WorkItemV3:
    work_id: str
    source: str
    hypothesis: str
    product_delta: str
    risk: str
    allowed_files: tuple[str, ...]
    test_ids: tuple[str, ...]
    base_commit: str
    issue_number: int | None = None
    labels: tuple[str, ...] = ()
    provider_context_files: tuple[str, ...] = ()
    evolution_chunk: EvolutionChunkContractV1 | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not SAFE_ID.fullmatch(self.work_id):
            errors.append("invalid_work_id")
        if self.source not in SAFE_SOURCES:
            errors.append("invalid_source")
        if not self.hypothesis.strip() or not self.product_delta.strip():
            errors.append("hypothesis_and_product_delta_required")
        if self.risk not in SAFE_RISKS:
            errors.append("invalid_risk")
        if not SAFE_GIT_COMMIT.fullmatch(self.base_commit):
            errors.append("invalid_base_commit")
        if len(self.allowed_files) > MAX_FILES:
            errors.append("too_many_allowed_files")
        try:
            [_safe_relative_path(path) for path in self.allowed_files]
        except AutonomyValidationError as error:
            errors.append(str(error))
        if len(self.provider_context_files) > MAX_FILES:
            errors.append("too_many_provider_context_files")
        try:
            [_safe_relative_path(path) for path in self.provider_context_files]
        except AutonomyValidationError as error:
            errors.append(str(error))
        text_scan = scan_text(f"{self.hypothesis}\n{self.product_delta}", "work-item-metadata")
        if text_scan["status"] != "pass":
            errors.append("work_item_public_safety_failed")
        try:
            _validate_ids(self.test_ids, "test_ids")
        except AutonomyValidationError as error:
            errors.append(str(error))
        if self.issue_number is not None and self.issue_number < 1:
            errors.append("invalid_issue_number")
        if self.evolution_chunk is not None:
            errors.extend(self.evolution_chunk.validate())
        return list(dict.fromkeys(errors))

    def validate_for_execution(self) -> list[str]:
        errors = self.validate()
        if self.evolution_chunk is None:
            errors.append("legacy_missing_3gr_contract")
        return list(dict.fromkeys(errors))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": "WorkItemV3",
            "work_id": self.work_id,
            "source": self.source,
            "hypothesis": self.hypothesis,
            "product_delta": self.product_delta,
            "risk": self.risk,
            "allowed_files": list(self.allowed_files),
            "test_ids": list(self.test_ids),
            "base_commit": self.base_commit,
            "issue_number": self.issue_number,
            "labels": list(self.labels),
            "provider_context_files": list(self.provider_context_files),
            "evolution_chunk": self.evolution_chunk.to_dict() if self.evolution_chunk else None,
        }
        if include_hash:
            payload["work_item_hash"] = sha256_json(payload)
        return payload

    @property
    def work_item_hash(self) -> str:
        return sha256_json(self.to_dict(include_hash=False))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WorkItemV3":
        if not isinstance(payload, dict):
            raise AutonomyValidationError("work_item_must_be_object")
        item = cls(
            work_id=str(payload.get("work_id", "")),
            source=str(payload.get("source", "")),
            hypothesis=str(payload.get("hypothesis", "")),
            product_delta=str(payload.get("product_delta", "")),
            risk=str(payload.get("risk", "")),
            allowed_files=tuple(str(value) for value in payload.get("allowed_files", [])),
            test_ids=tuple(str(value) for value in payload.get("test_ids", [])),
            base_commit=str(payload.get("base_commit", "")),
            issue_number=payload.get("issue_number"),
            labels=tuple(str(value) for value in payload.get("labels", [])),
            provider_context_files=tuple(str(value) for value in payload.get("provider_context_files", [])),
            evolution_chunk=(
                EvolutionChunkContractV1.from_dict(payload["evolution_chunk"])
                if isinstance(payload.get("evolution_chunk"), dict)
                else None
            ),
        )
        errors = item.validate()
        if errors:
            raise AutonomyValidationError(",".join(errors))
        supplied_hash = payload.get("work_item_hash")
        if supplied_hash is not None and supplied_hash != item.work_item_hash:
            legacy_payload = item.to_dict(include_hash=False)
            legacy_payload.pop("evolution_chunk", None)
            if "evolution_chunk" in payload or supplied_hash != sha256_json(legacy_payload):
                raise AutonomyValidationError("work_item_hash_mismatch")
        return item

    @property
    def public_context_files(self) -> tuple[str, ...]:
        return self.provider_context_files or self.allowed_files


@dataclass
class ImplementationEvidenceV1:
    run_id: str
    base_commit: str
    diff_hash: str
    changed_files: list[str]
    test_ids_passed: list[str]
    test_evidence_hash: str
    actual_diff_verified: bool
    evidence_hash: str = ""

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "run_id": self.run_id,
            "base_commit": self.base_commit,
            "diff_hash": self.diff_hash,
            "changed_files": sorted(self.changed_files),
            "test_ids_passed": sorted(self.test_ids_passed),
            "test_evidence_hash": self.test_evidence_hash,
            "actual_diff_verified": self.actual_diff_verified,
        }
        if include_hash:
            payload["evidence_hash"] = sha256_json(payload)
        return payload

    def bind(self) -> None:
        self.evidence_hash = sha256_json(self.to_dict(include_hash=False))


@dataclass
class CodexReviewV1:
    run_id: str
    diff_hash: str
    decision: str
    findings: list[dict[str, Any]] = field(default_factory=list)
    test_gaps: list[str] = field(default_factory=list)
    reviewer: str = "codex-independent"

    def validate(self, expected_diff_hash: str) -> list[str]:
        errors = []
        if self.diff_hash != expected_diff_hash:
            errors.append("diff_hash_mismatch")
        if self.decision not in {"approve", "revise", "block"}:
            errors.append("invalid_codex_decision")
        for finding in self.findings:
            if not isinstance(finding, dict) or finding.get("severity") not in {"info", "low", "medium", "high", "critical"}:
                errors.append("invalid_codex_finding")
        return list(dict.fromkeys(errors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": CODEX_REVIEW_SCHEMA_VERSION,
            "run_id": self.run_id,
            "diff_hash": self.diff_hash,
            "decision": self.decision,
            "findings": self.findings,
            "test_gaps": self.test_gaps,
            "reviewer": self.reviewer,
        }


@dataclass
class GLMReviewV2:
    run_id: str
    proposal_hash: str
    diff_hash: str
    evidence_hash: str
    verdict: str
    risks: list[str] = field(default_factory=list)
    uncertainty: str = ""
    call_count: int = 2

    def validate(self, proposal_hash: str, evidence: ImplementationEvidenceV1) -> list[str]:
        errors = []
        if self.proposal_hash != proposal_hash:
            errors.append("proposal_hash_mismatch")
        if self.diff_hash != evidence.diff_hash:
            errors.append("diff_hash_mismatch")
        if self.evidence_hash != evidence.evidence_hash:
            errors.append("evidence_hash_mismatch")
        if self.verdict not in {"approve", "revise", "block"}:
            errors.append("invalid_glm_verdict")
        if self.call_count > MAX_GLM_CALLS:
            errors.append("too_many_glm_calls")
        return list(dict.fromkeys(errors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": GLM_REVIEW_SCHEMA_VERSION,
            "run_id": self.run_id,
            "proposal_hash": self.proposal_hash,
            "diff_hash": self.diff_hash,
            "evidence_hash": self.evidence_hash,
            "verdict": self.verdict,
            "risks": list(self.risks),
            "uncertainty": self.uncertainty,
            "call_count": self.call_count,
        }


@dataclass
class AutonomyRunV3:
    run_id: str
    work_item_hash: str
    trigger: str
    state: str = "queued"
    created_at_utc: str = field(default_factory=utc_now)
    transitions: list[dict[str, Any]] = field(default_factory=list)
    model_versions: dict[str, str] = field(default_factory=dict)
    cost_usd: float = 0.0
    branch: str = ""
    pr_url: str = ""
    block_reason: str = ""
    merge_gate: str = "human_only"
    public_safety_status: str = "pass"

    def transition(self, next_state: str, *, reason: str = "") -> None:
        if next_state not in RUN_STATES:
            raise AutonomyValidationError("unknown_run_state")
        if next_state not in TRANSITIONS[self.state]:
            raise AutonomyValidationError(f"invalid_transition:{self.state}->{next_state}")
        self.transitions.append({"from": self.state, "to": next_state, "at_utc": utc_now(), "reason": reason})
        self.state = next_state
        if next_state in {"blocked", "retryable", "gretel_proposed"}:
            self.block_reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": RUN_SCHEMA_VERSION,
            "run_id": self.run_id,
            "work_item_hash": self.work_item_hash,
            "trigger": self.trigger,
            "state": self.state,
            "created_at_utc": self.created_at_utc,
            "transitions": list(self.transitions),
            "model_versions": dict(self.model_versions),
            "cost_usd": round(float(self.cost_usd), 6),
            "branch": self.branch,
            "pr_url": self.pr_url,
            "block_reason": self.block_reason,
            "merge_gate": self.merge_gate,
            "public_safety_status": self.public_safety_status,
            "automatic_merge": False,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AutonomyRunV3":
        if not isinstance(payload, dict):
            raise AutonomyValidationError("run_must_be_object")
        fields = {
            "run_id",
            "work_item_hash",
            "trigger",
            "state",
            "created_at_utc",
            "transitions",
            "model_versions",
            "cost_usd",
            "branch",
            "pr_url",
            "block_reason",
            "merge_gate",
            "public_safety_status",
        }
        values = {key: payload[key] for key in fields if key in payload}
        try:
            return cls(**values)
        except TypeError as error:
            raise AutonomyValidationError("invalid_run_payload") from error


def default_support_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / "UniBotAutonomy"


def autonomy_loop_status(store: "AutonomyStore", *, support_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(support_dir).expanduser() if support_dir else default_support_dir()
    state_path = root / "loop-state.json"
    state: dict[str, Any] = {"active": False, "installed": False}
    if state_path.exists() or state_path.is_symlink():
        try:
            candidate = _read_private_json(state_path, schema_version="AutonomyLoopStateV1")
            state.update({key: candidate[key] for key in ("active", "installed", "updated_at_utc") if key in candidate})
        except (AutonomyValidationError, OSError) as error:
            state = {"active": False, "installed": False, "state_error": str(error)}
    return {
        "schema_version": "AutonomyLoopStateV1",
        "status": "ok",
        "loop": {**state, "scheduler": "launchd_not_loaded"},
        "rollout": store.rollout_status(),
        "provider_calls": 0,
        "github_actions": 0,
        "automatic_merge": False,
    }


def prepare_autonomy_loop(store: "AutonomyStore", *, support_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(support_dir).expanduser() if support_dir else default_support_dir()
    state = {
        "schema_version": "AutonomyLoopStateV1",
        "active": False,
        "installed": True,
        "updated_at_utc": utc_now(),
        "human_launchd_load_required": True,
    }
    state_path = root / "loop-state.json"
    _atomic_write_private_json(state_path, state)
    return {**autonomy_loop_status(store, support_dir=root), "prepared": True}


def request_autonomy_loop_start(store: "AutonomyStore") -> dict[str, Any]:
    rollout = store.rollout_status()
    if not rollout["canary_allowed"]:
        reason = "rollout_gates_incomplete"
    elif not rollout["watcher_activation_allowed"]:
        reason = "three_human_canary_merges_required"
    else:
        reason = "human_launchd_load_required"
    return {
        "schema_version": "AutonomyLoopStateV1",
        "status": "blocked",
        "reason": reason,
        "loop": {"active": False, "scheduler": "launchd_not_loaded"},
        "rollout": rollout,
        "provider_calls": 0,
        "github_actions": 0,
        "automatic_merge": False,
    }


class AutonomyStore:
    """Metadata-only local store. It never stores prompts, notebook text, or tokens."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path else default_support_dir() / "autonomy.sqlite3"
        _ensure_private_state_path(self.path)
        if not self.path.exists():
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(descriptor)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS work_items (work_item_hash TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS costs (month TEXT PRIMARY KEY, usd REAL NOT NULL, calls INTEGER NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS rollout (lane TEXT PRIMARY KEY, successful_runs INTEGER NOT NULL, "
            "failed_runs INTEGER NOT NULL, success_streak INTEGER NOT NULL DEFAULT 0, "
            "last_run_id TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        rollout_columns = {
            str(row[1]) for row in self.connection.execute("PRAGMA table_info(rollout)").fetchall()
        }
        if "success_streak" not in rollout_columns:
            self.connection.execute(
                "ALTER TABLE rollout ADD COLUMN success_streak INTEGER NOT NULL DEFAULT 0"
            )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS improvement_patterns (pattern_id TEXT PRIMARY KEY, payload TEXT NOT NULL, "
            "recurrence_count INTEGER NOT NULL, updated_at TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS canary_merge_evidence (run_id TEXT PRIMARY KEY, evidence_hash TEXT NOT NULL, "
            "created_at TEXT NOT NULL)"
        )
        self.connection.commit()
        os.chmod(self.path, 0o600)

    def save_work_item(self, item: WorkItemV3) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO work_items(work_item_hash,payload,created_at) VALUES(?,?,?)",
            (item.work_item_hash, canonical_json(item.to_dict()), utc_now()),
        )
        self.connection.commit()

    def save_run(self, run: AutonomyRunV3) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO runs(run_id,payload,created_at) VALUES(?,?,?)",
            (run.run_id, canonical_json(run.to_dict()), run.created_at_utc),
        )
        self.connection.commit()

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT payload FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT payload FROM runs ORDER BY created_at DESC LIMIT ?", (max(1, min(int(limit), 100)),)
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def list_work_items(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT payload FROM work_items ORDER BY created_at DESC LIMIT ?", (max(1, min(int(limit), 100)),)
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def release_work_item(self, work_id: str) -> bool:
        rows = self.connection.execute("SELECT work_item_hash,payload FROM work_items").fetchall()
        for work_item_hash, payload in rows:
            try:
                item = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if item.get("work_id") == work_id:
                self.connection.execute("DELETE FROM work_items WHERE work_item_hash=?", (work_item_hash,))
                self.connection.commit()
                return True
        return False

    def record_improvement_pattern(
        self,
        contract: EvolutionChunkContractV1,
        *,
        work_item_hash: str,
    ) -> dict[str, Any]:
        errors = contract.validate()
        if errors:
            raise AutonomyValidationError(",".join(errors))
        pattern_id = contract.failure_class
        row = self.connection.execute(
            "SELECT payload,recurrence_count FROM improvement_patterns WHERE pattern_id=?", (pattern_id,)
        ).fetchone()
        if row:
            existing = json.loads(row[0])
            if existing.get("last_work_item_hash") == work_item_hash:
                return existing
        recurrence_count = (int(row[1]) if row else 0) + 1
        payload = {
            "schema_version": IMPROVEMENT_PATTERN_SCHEMA_VERSION,
            "pattern_id": pattern_id,
            "failure_class": contract.failure_class,
            "contract_hash": contract.contract_hash,
            "generalized_rule_hash": sha256_bytes(contract.generalized_rule.encode("utf-8")),
            "transfer_targets": list(contract.transfer_targets),
            "recurrence_monitor_id": contract.recurrence_monitor_id,
            "last_work_item_hash": work_item_hash,
            "recurrence_count": recurrence_count,
            "review_status": "review_required" if recurrence_count > 1 else "observed",
            "automatic_apply": False,
            "updated_at_utc": utc_now(),
        }
        self.connection.execute(
            "INSERT OR REPLACE INTO improvement_patterns(pattern_id,payload,recurrence_count,updated_at) "
            "VALUES(?,?,?,?)",
            (pattern_id, canonical_json(payload), recurrence_count, payload["updated_at_utc"]),
        )
        self.connection.commit()
        return payload

    def get_improvement_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT payload FROM improvement_patterns WHERE pattern_id=?", (pattern_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def list_improvement_patterns(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT payload FROM improvement_patterns ORDER BY updated_at DESC LIMIT ?",
            (max(1, min(int(limit), 100)),),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def record_cost(self, amount_usd: float, *, month: str | None = None) -> dict[str, Any]:
        month = month or datetime.now(timezone.utc).strftime("%Y-%m")
        row = self.connection.execute("SELECT usd,calls FROM costs WHERE month=?", (month,)).fetchone()
        current = float(row[0]) if row else 0.0
        calls = int(row[1]) if row else 0
        next_total = round(current + max(0.0, float(amount_usd)), 6)
        if next_total > HARD_STOP_USD:
            return {"status": "blocked", "reason": "monthly_hard_stop", "month": month, "usd": current, "calls": calls}
        self.connection.execute(
            "INSERT OR REPLACE INTO costs(month,usd,calls) VALUES(?,?,?)", (month, next_total, calls + 1)
        )
        self.connection.commit()
        return {
            "status": "warning" if next_total >= WARN_USD else "ok",
            "month": month,
            "usd": next_total,
            "calls": calls + 1,
            "warn_at_usd": WARN_USD,
            "hard_stop_usd": HARD_STOP_USD,
        }

    def budget_status(self, *, month: str | None = None) -> dict[str, Any]:
        month = month or datetime.now(timezone.utc).strftime("%Y-%m")
        row = self.connection.execute("SELECT usd,calls FROM costs WHERE month=?", (month,)).fetchone()
        usd, calls = (float(row[0]), int(row[1])) if row else (0.0, 0)
        return {
            "month": month,
            "usd": usd,
            "calls": calls,
            "warning": usd >= WARN_USD,
            "hard_stopped": usd >= HARD_STOP_USD,
            "warn_at_usd": WARN_USD,
            "hard_stop_usd": HARD_STOP_USD,
        }

    def record_rollout(self, lane: str, *, run_id: str, success: bool) -> dict[str, Any]:
        if lane not in {"shadow", "local"}:
            raise AutonomyValidationError("invalid_rollout_lane")
        row = self.connection.execute(
            "SELECT successful_runs,failed_runs,success_streak FROM rollout WHERE lane=?", (lane,)
        ).fetchone()
        successful, failed, streak = (int(row[0]), int(row[1]), int(row[2])) if row else (0, 0, 0)
        if success:
            successful += 1
            streak += 1
        else:
            failed += 1
            streak = 0
        self.connection.execute(
            "INSERT OR REPLACE INTO rollout(lane,successful_runs,failed_runs,success_streak,last_run_id,updated_at) "
            "VALUES(?,?,?,?,?,?)",
            (lane, successful, failed, streak, run_id, utc_now()),
        )
        self.connection.commit()
        return self.rollout_status()

    def record_canary_merge(
        self,
        *,
        run_id: str,
        reviewer: str,
        merge_commit: str,
        checks_green: bool,
        approved_after_last_push: bool,
    ) -> dict[str, Any]:
        if not SAFE_ID.fullmatch(run_id) or not reviewer.strip() or not SAFE_GIT_COMMIT.fullmatch(merge_commit):
            raise AutonomyValidationError("invalid_canary_merge_evidence")
        if not checks_green or not approved_after_last_push:
            raise AutonomyValidationError("canary_merge_requires_green_checks_and_fresh_human_approval")
        run = self.get_run(run_id)
        if not run or run.get("state") != "human_merged":
            raise AutonomyValidationError("canary_run_must_be_recorded_as_human_merged")
        existing = self.connection.execute(
            "SELECT evidence_hash FROM canary_merge_evidence WHERE run_id=?", (run_id,)
        ).fetchone()
        if existing:
            return self.rollout_status()
        row = self.connection.execute(
            "SELECT successful_runs,failed_runs,success_streak FROM rollout WHERE lane='canary_merges'"
        ).fetchone()
        successful, failed, streak = (int(row[0]), int(row[1]), int(row[2])) if row else (0, 0, 0)
        successful += 1
        streak += 1
        evidence_id = sha256_json(
            {
                "run_id": run_id,
                "reviewer": reviewer,
                "merge_commit": merge_commit,
                "checks_green": True,
                "approved_after_last_push": True,
            }
        )
        self.connection.execute(
            "INSERT OR REPLACE INTO rollout(lane,successful_runs,failed_runs,success_streak,last_run_id,updated_at) "
            "VALUES('canary_merges',?,?,?,?,?)",
            (successful, failed, streak, evidence_id, utc_now()),
        )
        self.connection.execute(
            "INSERT INTO canary_merge_evidence(run_id,evidence_hash,created_at) VALUES(?,?,?)",
            (run_id, evidence_id, utc_now()),
        )
        self.connection.commit()
        return self.rollout_status()

    def rollout_status(self) -> dict[str, Any]:
        rows = self.connection.execute(
            "SELECT lane,successful_runs,failed_runs,success_streak,last_run_id,updated_at FROM rollout"
        ).fetchall()
        lanes = {
            lane: {
                "successful_runs": int(successful),
                "failed_runs": int(failed),
                "consecutive_successes": int(success_streak),
                "last_run_id": last_run_id,
                "updated_at_utc": updated_at,
                "target": CANARY_MERGE_TARGET if lane == "canary_merges" else ROLLOUT_TARGET,
                "complete": int(success_streak)
                >= (CANARY_MERGE_TARGET if lane == "canary_merges" else ROLLOUT_TARGET)
                and (lane != "canary_merges" or int(failed) == 0),
            }
            for lane, successful, failed, success_streak, last_run_id, updated_at in rows
        }
        for lane in ("shadow", "local", "canary_merges"):
            target = CANARY_MERGE_TARGET if lane == "canary_merges" else ROLLOUT_TARGET
            lanes.setdefault(
                lane,
                {
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "consecutive_successes": 0,
                    "last_run_id": "",
                    "updated_at_utc": "",
                    "target": target,
                    "complete": False,
                },
            )
        return {
            "schema_version": "AutonomyRolloutV3",
            "status": "ok",
            "lanes": lanes,
            "provider_required": False,
            "canary_allowed": lanes["shadow"]["complete"] and lanes["local"]["complete"],
            "watcher_activation_allowed": lanes["canary_merges"]["complete"],
            "three_golden_rules": "separate_per_work_item_gate",
        }

    def recover_interrupted_runs(self, *, stale_after_seconds: int = STALE_RUN_SECONDS) -> list[str]:
        active_states = {
            "queued",
            "proposed",
            "implementing",
            "deterministic_green",
            "codex_review_green",
            "glm_approved",
            "ci_green",
        }
        threshold = datetime.now(timezone.utc).timestamp() - max(1, int(stale_after_seconds))
        recovered: list[str] = []
        for payload in self.list_runs(limit=100):
            if payload.get("state") not in active_states:
                continue
            if (
                payload.get("trigger") == "rollout_shadow" and payload.get("state") == "glm_approved"
            ) or (
                payload.get("trigger") == "rollout_local" and payload.get("state") == "codex_review_green"
            ):
                continue
            try:
                created = datetime.fromisoformat(str(payload["created_at_utc"])).timestamp()
            except (KeyError, TypeError, ValueError):
                created = 0
            if created > threshold:
                continue
            run = AutonomyRunV3.from_dict(payload)
            run.transition("retryable", reason="interrupted_run_recovery")
            self.save_run(run)
            recovered.append(run.run_id)
        return recovered

    def close(self) -> None:
        self.connection.close()


def three_golden_rules_status(store: AutonomyStore) -> dict[str, Any]:
    patterns = store.list_improvement_patterns()
    return {
        "schema_version": "ThreeGoldenRulesStatusV1",
        "status": "ok",
        "rules": {
            "generalize": "turn_a_concrete_failure_into_a_reusable_rule_with_transfer_targets",
            "harness_engineering": "bind_the_rule_to_positive_and_negative_registered_fixtures",
            "recursive_self_improvement": "monitor_recurrence_and_create_review_gated_improvement_work",
        },
        "pattern_count": len(patterns),
        "review_required_count": sum(pattern.get("review_status") == "review_required" for pattern in patterns),
        "patterns": patterns,
        "automatic_apply": False,
        "human_review_required": True,
        "canary_merges_are_a_separate_rollout_gate": True,
    }


def evaluate_three_golden_rules(item: WorkItemV3) -> dict[str, Any]:
    errors = item.validate_for_execution()
    contract = item.evolution_chunk
    gates = {
        "generalize": bool(contract and contract.generalized_rule.strip() and len(contract.transfer_targets) >= 2),
        "harness_engineering": bool(contract and contract.positive_fixture_ids and contract.negative_fixture_ids),
        "recursive_self_improvement": bool(contract and contract.recurrence_monitor_id and contract.human_gate == "required"),
    }
    return {
        "schema_version": "ThreeGoldenRulesEvaluationV1",
        "status": "pass" if not errors and all(gates.values()) else "blocked",
        "work_item_hash": item.work_item_hash,
        "gates": gates,
        "errors": errors,
        "automatic_apply": False,
        "human_review_required": True,
        "canary_merges_evaluated": False,
    }


def bind_three_golden_rules_evidence(
    item: WorkItemV3,
    evidence: ImplementationEvidenceV1,
    store: AutonomyStore,
) -> ThreeGoldenRulesEvidenceV1:
    if item.evolution_chunk is None:
        raise AutonomyValidationError("legacy_missing_3gr_contract")
    pattern = store.record_improvement_pattern(item.evolution_chunk, work_item_hash=item.work_item_hash)
    return ThreeGoldenRulesEvidenceV1(
        work_item_hash=item.work_item_hash,
        contract_hash=item.evolution_chunk.contract_hash,
        test_evidence_hash=evidence.test_evidence_hash,
        test_ids_passed=tuple(evidence.test_ids_passed),
        recurrence_count=int(pattern["recurrence_count"]),
    )


class ProviderGate:
    def __init__(self, state_path: str | Path | None = None, store: AutonomyStore | None = None) -> None:
        self.state_path = Path(state_path).expanduser() if state_path else default_support_dir() / "provider-state.json"
        self.store = store

    def _read(self) -> tuple[str, str]:
        if not self.state_path.exists() and not self.state_path.is_symlink():
            return PROVIDER_PARKED, ""
        try:
            payload = _read_private_json(self.state_path, schema_version="ProviderStateV1")
            state = str(payload.get("state", PROVIDER_PARKED))
        except (AutonomyValidationError, OSError) as error:
            return PROVIDER_PARKED, str(error)
        if state not in {PROVIDER_PARKED, PROVIDER_ENABLED}:
            return PROVIDER_PARKED, "provider_state_invalid_fail_closed"
        return state, ""

    def _write(self, state: str) -> dict[str, Any]:
        if state not in {PROVIDER_PARKED, PROVIDER_ENABLED}:
            raise AutonomyValidationError("invalid_provider_state")
        payload = {"schema_version": "ProviderStateV1", "state": state, "updated_at_utc": utc_now(), "key_stored": False}
        _atomic_write_private_json(self.state_path, payload)
        return self.status()

    def park(self) -> dict[str, Any]:
        return self._write(PROVIDER_PARKED)

    def unpark(self, scope: str) -> dict[str, Any]:
        if scope != "public-unibot-only":
            raise AutonomyValidationError("unpark_requires_scope_public_unibot_only")
        return self._write(PROVIDER_ENABLED)

    def status(self) -> dict[str, Any]:
        state, state_error = self._read()
        budget = self.store.budget_status() if self.store else None
        allowed = state == PROVIDER_ENABLED and not state_error and not bool(budget and budget["hard_stopped"])
        reason = state_error or (
            "parked_before_keychain_sdk_and_network" if state == PROVIDER_PARKED else "public_scope_only"
        )
        return {
            "schema_version": "ProviderStateV1",
            "state": state,
            "model": MODEL_VERSION,
            "call_allowed": allowed,
            "reason": reason,
            "key_stored": False,
            "network_call_executed": False,
            "budget": budget,
        }

    def authorize_call(self, *, estimated_cost_usd: float = 0.0) -> dict[str, Any]:
        status = self.status()
        if not status["call_allowed"]:
            return {"status": "blocked", "reason": status["reason"], "provider": status}
        if self.store and estimated_cost_usd:
            budget = self.store.record_cost(estimated_cost_usd)
            if budget["status"] == "blocked":
                return {"status": "blocked", "reason": "monthly_hard_stop", "provider": status}
        return {"status": "authorized", "provider": status}


class AutonomyLease:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path else default_support_dir() / "autonomy.lock"
        self.handle: Any = None

    def acquire(self) -> None:
        _ensure_private_state_path(self.path)
        flags = os.O_CREAT | os.O_RDWR | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(self.path, flags, 0o600)
        except OSError as error:
            raise AutonomyValidationError("lease_path_open_failed") from error
        os.fchmod(descriptor, 0o600)
        self.handle = os.fdopen(descriptor, "a+", encoding="utf-8")
        if fcntl is None:  # pragma: no cover - package target is macOS
            return
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self.handle.close()
            self.handle = None
            raise LeaseBusy("autonomy_lease_busy") from error

    def release(self) -> None:
        if self.handle is None:
            return
        if fcntl is not None:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()
        self.handle = None

    def __enter__(self) -> "AutonomyLease":
        self.acquire()
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()


class PublicContextBuilder:
    def __init__(self, repo_root: str | Path, *, max_file_bytes: int = 120_000) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.max_file_bytes = max_file_bytes

    def build(self, item: WorkItemV3) -> dict[str, Any]:
        errors = item.validate()
        if errors:
            raise AutonomyValidationError(",".join(errors))
        files = []
        for relative in item.public_context_files:
            safe = _safe_relative_path(relative)
            candidate = self.repo_root / safe
            if candidate.is_symlink():
                raise AutonomyValidationError("context_file_missing_or_symlink")
            path = candidate.resolve()
            try:
                path.relative_to(self.repo_root)
            except ValueError as error:
                raise AutonomyValidationError("context_path_outside_repo") from error
            if not path.is_file():
                raise AutonomyValidationError("context_file_missing_or_symlink")
            content_bytes = path.read_bytes()
            if len(content_bytes) > self.max_file_bytes or b"\0" in content_bytes:
                raise AutonomyValidationError("context_file_too_large_or_binary")
            content = content_bytes.decode("utf-8")
            scan = scan_text(content, safe)
            if scan["status"] != "pass":
                raise AutonomyValidationError("public_context_scan_failed")
            files.append({"path": safe, "content": content})
        context = {
            "schema_version": "PublicGLMContextV1",
            "base_commit": item.base_commit,
            "work_item_hash": item.work_item_hash,
            "files": files,
            "raw_private_context_shared": False,
            "notebook_text_shared": False,
            "local_paths_shared": False,
            "context_hash": "",
        }
        context["context_hash"] = sha256_json({key: value for key, value in context.items() if key != "context_hash"})
        return context


class TestRegistry:
    """Only named, registered tests can be executed by the controller."""

    __test__ = False

    def __init__(self) -> None:
        self._tests: dict[str, Callable[[], bool]] = {}

    def register(self, test_id: str, callback: Callable[[], bool]) -> None:
        _validate_ids([test_id], "test_id")
        self._tests[test_id] = callback

    def run(self, test_ids: Iterable[str]) -> dict[str, Any]:
        passed: list[str] = []
        failed: list[str] = []
        unknown: list[str] = []
        for test_id in test_ids:
            callback = self._tests.get(test_id)
            if callback is None:
                unknown.append(test_id)
                continue
            try:
                (passed if bool(callback()) else failed).append(test_id)
            except Exception:
                failed.append(test_id)
        return {"status": "pass" if not failed and not unknown else "fail", "passed": passed, "failed": failed, "unknown": unknown}

    @property
    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._tests))


def _run_registered_pytest(repo_root: Path, test_file: str) -> bool:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", test_file],
        cwd=repo_root,
        check=False,
        capture_output=True,
        shell=False,
    )
    return completed.returncode == 0


def default_test_registry(repo_root: str | Path) -> TestRegistry:
    """Return the fixed, non-issue-controlled v3 test catalog."""
    root = Path(repo_root).resolve()
    registry = TestRegistry()
    registry.register(
        "guardian.semantic_precision",
        lambda: _run_registered_pytest(root, "tests/test_unibot_guardian_benchmark.py"),
    )
    registry.register(
        "public.safety",
        lambda: _run_registered_pytest(root, "tests/test_unibot_api_and_public_safety.py"),
    )
    registry.register(
        "autonomy.v3",
        lambda: _run_registered_pytest(root, "tests/test_unibot_autonomy_v3.py"),
    )
    return registry


def _git_output(repo: Path, args: list[str], *, binary: bool = False) -> bytes | str:
    try:
        completed = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, shell=False)
    except (OSError, subprocess.CalledProcessError) as error:
        raise AutonomyValidationError("git_evidence_unavailable") from error
    return completed.stdout if binary else completed.stdout.decode("utf-8", errors="strict")


def derive_implementation_evidence(
    *,
    worktree: str | Path,
    run_id: str,
    base_commit: str,
    allowed_files: Iterable[str],
    test_ids_passed: Iterable[str],
    test_evidence_hash: str,
) -> ImplementationEvidenceV1:
    root = Path(worktree).resolve()
    allowed = {_safe_relative_path(path) for path in allowed_files}
    tracked = set(filter(None, str(_git_output(root, ["diff", "--name-only", base_commit, "--"])).splitlines()))
    untracked = set(filter(None, str(_git_output(root, ["ls-files", "--others", "--exclude-standard"])).splitlines()))
    changed = sorted(tracked | untracked)
    if len(changed) > MAX_FILES:
        raise AutonomyValidationError("actual_diff_exceeds_file_limit")
    if not set(changed).issubset(allowed):
        raise AutonomyValidationError("actual_diff_outside_allowed_files")
    binary_diff = _git_output(root, ["diff", "--binary", base_commit, "--"], binary=True)
    if not isinstance(binary_diff, bytes):  # pragma: no cover - guarded by the binary argument
        raise AutonomyValidationError("git_binary_evidence_invalid")
    digest = bytearray(binary_diff)
    for relative in sorted(untracked):
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise AutonomyValidationError("symlink_or_non_file_change")
        data = path.read_bytes()
        if b"\0" in data:
            raise AutonomyValidationError("binary_change_not_allowed")
        if scan_text(data.decode("utf-8", errors="strict"), relative)["status"] != "pass":
            raise AutonomyValidationError("public_safety_diff_failed")
        digest.extend(relative.encode("utf-8") + b"\0" + data)
    for relative in sorted(tracked):
        path = root / relative
        if path.is_symlink():
            raise AutonomyValidationError("symlink_change_not_allowed")
        if path.is_file():
            data = path.read_bytes()
            if b"\0" in data:
                raise AutonomyValidationError("binary_change_not_allowed")
            if scan_text(data.decode("utf-8", errors="strict"), relative)["status"] != "pass":
                raise AutonomyValidationError("public_safety_diff_failed")
    evidence = ImplementationEvidenceV1(
        run_id=run_id,
        base_commit=base_commit,
        diff_hash=sha256_bytes(bytes(digest)),
        changed_files=changed,
        test_ids_passed=sorted(set(test_ids_passed)),
        test_evidence_hash=test_evidence_hash,
        actual_diff_verified=True,
    )
    evidence.bind()
    return evidence


def validate_glm_proposal(proposal: dict[str, Any], item: WorkItemV3) -> dict[str, Any]:
    blockers: list[str] = []
    if not isinstance(proposal, dict):
        return {"status": "blocked", "blockers": ["invalid_json_object"]}
    required = {
        "schema_version",
        "work_item_hash",
        "base_commit",
        "problem",
        "hypothesis",
        "change_outline",
        "affected_files",
        "tests",
        "scientific_sources",
        "risks",
        "uncertainty",
        "blocked_reason",
    }
    blockers.extend(f"missing:{key}" for key in sorted(required - set(proposal)))
    if proposal.get("schema_version") != GLM_PROPOSAL_SCHEMA_VERSION:
        blockers.append("invalid_schema_version")
    if proposal.get("work_item_hash") != item.work_item_hash:
        blockers.append("work_item_hash_mismatch")
    if proposal.get("base_commit") != item.base_commit:
        blockers.append("base_commit_mismatch")
    affected = proposal.get("affected_files", [])
    if not isinstance(affected, list):
        blockers.append("affected_files_must_be_list")
        affected = []
    else:
        try:
            affected = [_safe_relative_path(path) for path in affected]
        except AutonomyValidationError as error:
            blockers.append(str(error))
        if len(affected) > MAX_FILES or not set(affected).issubset(set(item.allowed_files)):
            blockers.append("affected_files_outside_work_item")
    tests = proposal.get("tests", [])
    if not isinstance(tests, list):
        blockers.append("tests_must_be_list")
        tests = []
    else:
        try:
            _validate_ids(tests, "proposal_tests")
        except AutonomyValidationError as error:
            blockers.append(str(error))
        if not set(tests).issubset(set(item.test_ids)):
            blockers.append("proposal_test_outside_registry")
    forbidden_keys = {"autonomous_apply", "final_go", "publish", "merge", "external_actions", "write_access", "private_context"}
    blockers.extend(f"forbidden:{key}" for key in sorted(forbidden_keys & set(proposal)))
    scan = scan_text(canonical_json(proposal), "glm-proposal")
    if scan["status"] != "pass":
        blockers.append("public_safety_scan_failed")
    return {
        "schema_version": "GLMProposalValidationV1",
        "status": "blocked" if blockers else "ok",
        "blockers": list(dict.fromkeys(blockers)),
        "proposal_hash": sha256_json(proposal) if not blockers else "",
        "affected_files": affected,
        "public_safety_status": scan["status"],
        "provider_call_executed": False,
    }


class GLMAdapter(Protocol):
    model_version: str

    def propose(self, context: dict[str, Any], item: WorkItemV3) -> dict[str, Any]: ...

    def review(self, context: dict[str, Any], item: WorkItemV3, evidence: ImplementationEvidenceV1, proposal: dict[str, Any]) -> GLMReviewV2: ...


class NoNetworkGLMAdapter:
    model_version = MODEL_VERSION

    def propose(self, context: dict[str, Any], item: WorkItemV3) -> dict[str, Any]:
        raise AutonomyValidationError("glm_provider_not_called_without_explicit_adapter")

    def review(self, context: dict[str, Any], item: WorkItemV3, evidence: ImplementationEvidenceV1, proposal: dict[str, Any]) -> GLMReviewV2:
        raise AutonomyValidationError("glm_provider_not_called_without_explicit_adapter")


class DeterministicShadowGLM:
    """A no-network stand-in used only for the pre-provider shadow rollout."""

    model_version = "glm-5.2-mock-shadow"

    def propose(self, context: dict[str, Any], item: WorkItemV3) -> dict[str, Any]:
        return {
            "schema_version": GLM_PROPOSAL_SCHEMA_VERSION,
            "work_item_hash": item.work_item_hash,
            "base_commit": item.base_commit,
            "problem": "deterministic no-change shadow rehearsal",
            "hypothesis": item.hypothesis,
            "change_outline": ["validate the proposal and review chain without a code change"],
            "affected_files": list(item.allowed_files),
            "tests": list(item.test_ids),
            "scientific_sources": ["synthetic-local-shadow"],
            "risks": ["no provider, GitHub, CI, or merge action is available"],
            "uncertainty": "This response is a local deterministic mock, not a GLM provider call.",
            "blocked_reason": "",
        }

    def review(self, context: dict[str, Any], item: WorkItemV3, evidence: ImplementationEvidenceV1, proposal: dict[str, Any]) -> GLMReviewV2:
        return GLMReviewV2(
            run_id=evidence.run_id,
            proposal_hash=sha256_json(proposal),
            diff_hash=evidence.diff_hash,
            evidence_hash=evidence.evidence_hash,
            verdict="approve",
            risks=["deterministic shadow only"],
            uncertainty="No provider call was made.",
            call_count=0,
        )


def build_draft_pr_preview(run: AutonomyRunV3, item: WorkItemV3, evidence: ImplementationEvidenceV1, review: GLMReviewV2) -> dict[str, Any]:
    branch = f"gretel/{safe_slug(item.work_id)}-{run.run_id[:8]}"
    body = (
        "## UniBot Autonomie v3 Entwurfs-PR\n\n"
        "Implementierung und Dokumentation: Gretel/Codex, KI-Agent.\n"
        "GLM-5.2: Vorschlag und Gegenprüfung. Julius: menschlicher Projektverantwortlicher und Freigeber.\n\n"
        f"- WorkItem-Hash: `{item.work_item_hash}`\n"
        f"- Basis-Commit: `{item.base_commit}`\n"
        f"- Diff-Hash: `{evidence.diff_hash}`\n"
        f"- Evidence-Hash: `{evidence.evidence_hash}`\n"
        f"- GLM-Verdict: `{review.verdict}`; Aufrufe: `{review.call_count}`\n"
        f"- Tests: `{', '.join(evidence.test_ids_passed)}`\n\n"
        "Dieser Entwurf hat keine automatische Merge- oder Release-Freigabe. "
        "Die menschliche Prüfung nach dem letzten Bot-Push ist erforderlich."
    )
    preview = {
        "schema_version": "DraftPRPreviewV1",
        "status": "ready_for_human_merge",
        "draft_only": True,
        "external_action_executed": False,
        "automatic_merge": False,
        "branch": branch,
        "title": f"Gretel: {item.product_delta[:100]}",
        "body": body,
        "changed_files": evidence.changed_files,
        "hash_chain": {
            "work_item_hash": item.work_item_hash,
            "diff_hash": evidence.diff_hash,
            "evidence_hash": evidence.evidence_hash,
            "glm_review_hash": sha256_json(review.to_dict()),
        },
    }
    scan = scan_text(canonical_json(preview), "draft-pr-preview")
    preview["public_safety_status"] = scan["status"]
    if scan["status"] != "pass":
        preview["status"] = "blocked"
        preview["public_safety_findings"] = scan["findings"]
    return preview


class AutonomyController:
    def __init__(
        self,
        *,
        repo_root: str | Path,
        store: AutonomyStore | None = None,
        provider_gate: ProviderGate | None = None,
        lease: AutonomyLease | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.store = store or AutonomyStore()
        self.provider_gate = provider_gate or ProviderGate(store=self.store)
        self.lease = lease or AutonomyLease()

    def _ensure_clean_source_repository(self) -> None:
        if not (self.repo_root / ".git").exists():
            raise AutonomyValidationError("git_source_repository_required")
        inside = str(_git_output(self.repo_root, ["rev-parse", "--is-inside-work-tree"])).strip()
        if inside != "true":
            raise AutonomyValidationError("git_source_repository_required")
        if str(_git_output(self.repo_root, ["status", "--porcelain"])).strip():
            raise AutonomyValidationError("source_repository_must_be_clean")

    def _resolve_base_commit(self, base_commit: str) -> str:
        self._ensure_clean_source_repository()
        return str(_git_output(self.repo_root, ["rev-parse", "--verify", f"{base_commit}^{{commit}}"])).strip()

    @contextmanager
    def _ephemeral_worktree(self, item: WorkItemV3, run_id: str) -> Iterator[tuple[Path, str]]:
        base_commit = self._resolve_base_commit(item.base_commit)
        parent = default_support_dir() / "worktrees"
        parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(parent, 0o700)
        except OSError:
            pass
        worktree = parent / run_id
        if worktree.exists():
            raise AutonomyValidationError("ephemeral_worktree_already_exists")
        try:
            subprocess.run(
                ["git", "clone", "--quiet", "--no-local", "--no-checkout", str(self.repo_root), str(worktree)],
                check=True,
                capture_output=True,
                shell=False,
            )
            subprocess.run(
                ["git", "-C", str(worktree), "checkout", "--quiet", "--detach", base_commit],
                check=True,
                capture_output=True,
                shell=False,
            )
            subprocess.run(
                ["git", "-C", str(worktree), "remote", "remove", "origin"],
                check=True,
                capture_output=True,
                shell=False,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            shutil.rmtree(worktree, ignore_errors=True)
            raise AutonomyValidationError("ephemeral_worktree_creation_failed") from error
        try:
            yield worktree, base_commit
        finally:
            shutil.rmtree(worktree, ignore_errors=True)

    def claim(self, item: WorkItemV3) -> dict[str, Any]:
        errors = item.validate()
        if errors:
            return {"status": "blocked", "reason": "invalid_work_item", "errors": errors}
        self.store.save_work_item(item)
        if item.evolution_chunk is None:
            return {
                "status": "gretel_proposed",
                "reason": "legacy_missing_3gr_contract",
                "execution_allowed": False,
                "work_item": item.to_dict(),
            }
        return {"status": "queued", "execution_allowed": True, "work_item": item.to_dict()}

    def create_run(self, item: WorkItemV3, *, trigger: str) -> AutonomyRunV3:
        run = AutonomyRunV3(run_id=uuid.uuid4().hex, work_item_hash=item.work_item_hash, trigger=trigger)
        self.store.save_run(run)
        return run

    def parked_run(self, item: WorkItemV3, *, trigger: str = "manual") -> dict[str, Any]:
        run = self.create_run(item, trigger=trigger)
        run.transition("blocked", reason="provider_parked_before_keychain_sdk_and_network")
        self.store.save_run(run)
        return {"status": "blocked", "reason": run.block_reason, "run": run.to_dict(), "provider": self.provider_gate.status()}

    def run_local_rollout(
        self,
        item: WorkItemV3,
        *,
        implementer: Callable[[Path, dict[str, Any], WorkItemV3], None],
        reviewer: Callable[[ImplementationEvidenceV1, WorkItemV3], CodexReviewV1],
        tests: TestRegistry | None = None,
        test_registry_factory: Callable[[Path], TestRegistry] | None = None,
        trigger: str = "rollout_local",
    ) -> dict[str, Any]:
        """Run a disposable, no-provider implementation rehearsal.

        This mode is deliberately unable to call GLM, CI, GitHub, or a merge.
        It exists solely for the ten local rollout rehearsals that must precede
        a live provider canary.
        """
        errors = item.validate_for_execution()
        if errors:
            return {"status": "blocked", "reason": "invalid_work_item", "errors": errors}
        self.store.save_work_item(item)
        run = self.create_run(item, trigger=trigger)
        proposal = {
            "schema_version": GLM_PROPOSAL_SCHEMA_VERSION,
            "work_item_hash": item.work_item_hash,
            "base_commit": item.base_commit,
            "problem": "deterministic local rollout rehearsal",
            "hypothesis": item.hypothesis,
            "change_outline": ["local implementation rehearsal only"],
            "affected_files": list(item.allowed_files),
            "tests": list(item.test_ids),
            "scientific_sources": ["local-rollout-no-provider"],
            "risks": ["no provider, GitHub, CI, or merge action is available"],
            "uncertainty": "This is not a GLM proposal or a release decision.",
            "blocked_reason": "",
        }
        with self.lease:
            try:
                proposal_validation = validate_glm_proposal(proposal, item)
                if proposal_validation["status"] != "ok":
                    raise AutonomyValidationError("local_rollout_proposal_invalid")
                run.transition("proposed", reason="local_rollout_synthetic_proposal")
                run.transition("implementing", reason="local_codex_rehearsal_start")
                with self._ephemeral_worktree(item, run.run_id) as (worktree, base_commit):
                    implementer(worktree, proposal, item)
                    test_registry = test_registry_factory(worktree) if test_registry_factory else tests
                    if test_registry is None:
                        raise AutonomyValidationError("registered_test_registry_missing")
                    test_result = test_registry.run(item.test_ids)
                    if test_result["status"] != "pass":
                        run.transition("blocked", reason="deterministic_tests_failed_or_unregistered")
                        self.store.save_run(run)
                        self.store.record_rollout("local", run_id=run.run_id, success=False)
                        return {"status": "blocked", "tests": test_result, "run": run.to_dict()}
                    evidence = derive_implementation_evidence(
                        worktree=worktree,
                        run_id=run.run_id,
                        base_commit=base_commit,
                        allowed_files=item.allowed_files,
                        test_ids_passed=test_result["passed"],
                        test_evidence_hash=sha256_json(test_result),
                    )
                    run.transition("deterministic_green", reason="local_registered_tests_and_actual_diff_green")
                    codex_review = reviewer(evidence, item)
                    review_errors = codex_review.validate(evidence.diff_hash)
                    if review_errors or codex_review.decision != "approve":
                        run.transition("blocked", reason="local_codex_review_not_approved")
                        self.store.save_run(run)
                        self.store.record_rollout("local", run_id=run.run_id, success=False)
                        return {
                            "status": "blocked",
                            "review_errors": review_errors,
                            "codex_review": codex_review.to_dict(),
                            "run": run.to_dict(),
                        }
                    run.transition("codex_review_green", reason="independent_local_codex_review_approved")
                    golden_rules_evidence = bind_three_golden_rules_evidence(item, evidence, self.store)
                    self.store.save_run(run)
                    self.store.record_rollout("local", run_id=run.run_id, success=True)
                    return {
                        "status": "local_green",
                        "run": run.to_dict(),
                        "evidence": evidence.to_dict(),
                        "codex_review": codex_review.to_dict(),
                        "three_golden_rules_evidence": golden_rules_evidence.to_dict(),
                        "provider_calls": 0,
                        "github_actions": 0,
                        "automatic_merge": False,
                    }
            except (AutonomyValidationError, OSError) as error:
                if run.state not in {"blocked", "retryable", "gretel_proposed"}:
                    run.transition("blocked", reason=str(error))
                self.store.save_run(run)
                self.store.record_rollout("local", run_id=run.run_id, success=False)
                return {"status": "blocked", "reason": str(error), "run": run.to_dict()}

    def run_shadow_rollout(
        self,
        item: WorkItemV3,
        *,
        tests: TestRegistry | None = None,
        test_registry_factory: Callable[[Path], TestRegistry] | None = None,
    ) -> dict[str, Any]:
        """Run one real no-change rehearsal without a provider call or a push."""
        def no_change_implementer(worktree: Path, proposal: dict[str, Any], work_item: WorkItemV3) -> None:
            return None

        def approving_reviewer(evidence: ImplementationEvidenceV1, work_item: WorkItemV3) -> CodexReviewV1:
            return CodexReviewV1(run_id=evidence.run_id, diff_hash=evidence.diff_hash, decision="approve")

        return self.execute(
            item,
            trigger="rollout_shadow",
            glm=DeterministicShadowGLM(),
            implementer=no_change_implementer,
            reviewer=approving_reviewer,
            tests=tests,
            test_registry_factory=test_registry_factory,
            shadow=True,
        )

    def execute(
        self,
        item: WorkItemV3,
        *,
        trigger: str = "manual",
        glm: GLMAdapter | None = None,
        implementer: Callable[[Path, dict[str, Any], WorkItemV3], None] | None = None,
        reviewer: Callable[[ImplementationEvidenceV1, WorkItemV3], CodexReviewV1] | None = None,
        repairer: Callable[[Path, list[dict[str, Any]], WorkItemV3], None] | None = None,
        tests: TestRegistry | None = None,
        test_registry_factory: Callable[[Path], TestRegistry] | None = None,
        shadow: bool = False,
        ci_green: bool = False,
        estimated_glm_cost_usd: float = 0.0,
    ) -> dict[str, Any]:
        errors = item.validate_for_execution()
        if errors:
            return {"status": "blocked", "reason": "invalid_work_item", "errors": errors}
        self.store.save_work_item(item)
        run = self.create_run(item, trigger=trigger)
        with self.lease:
            if not shadow:
                authorization = self.provider_gate.authorize_call(estimated_cost_usd=estimated_glm_cost_usd)
                if authorization["status"] != "authorized":
                    run.transition("blocked", reason=authorization["reason"])
                    self.store.save_run(run)
                    return {"status": "blocked", "reason": authorization["reason"], "run": run.to_dict()}
            if glm is None:
                run.transition("blocked", reason="glm_adapter_missing")
                self.store.save_run(run)
                return {"status": "blocked", "reason": run.block_reason, "run": run.to_dict()}
            try:
                with self._ephemeral_worktree(item, run.run_id) as (worktree, base_commit):
                    context = PublicContextBuilder(worktree).build(item)
                    proposal = glm.propose(context, item)
                    proposal_validation = validate_glm_proposal(proposal, item)
                    if proposal_validation["status"] != "ok":
                        run.transition("gretel_proposed", reason="glm_proposal_blocked")
                        self.store.save_run(run)
                        return {"status": "gretel_proposed", "proposal_validation": proposal_validation, "run": run.to_dict()}
                    proposal_hash = proposal_validation["proposal_hash"]
                    run.model_versions["glm"] = getattr(glm, "model_version", MODEL_VERSION)
                    run.transition("proposed", reason="validated_glm_proposal")
                    run.transition("implementing", reason="codex_implementation_start")
                    if implementer is None:
                        raise AutonomyValidationError("codex_implementer_missing")
                    implementer(worktree, proposal, item)
                    test_registry = test_registry_factory(worktree) if test_registry_factory else (tests or TestRegistry())
                    attempts = 0
                    while True:
                        test_result = test_registry.run(item.test_ids)
                        if test_result["status"] != "pass":
                            run.transition("blocked", reason="deterministic_tests_failed_or_unregistered")
                            self.store.save_run(run)
                            return {"status": "blocked", "tests": test_result, "run": run.to_dict()}
                        evidence = derive_implementation_evidence(
                            worktree=worktree,
                            run_id=run.run_id,
                            base_commit=base_commit,
                            allowed_files=item.allowed_files,
                            test_ids_passed=test_result["passed"],
                            test_evidence_hash=sha256_json(test_result),
                        )
                        if shadow and evidence.changed_files:
                            run.transition("blocked", reason="shadow_run_changed_files")
                            self.store.save_run(run)
                            self.store.record_rollout("shadow", run_id=run.run_id, success=False)
                            return {"status": "blocked", "reason": "shadow_run_changed_files", "run": run.to_dict()}
                        run.transition("deterministic_green", reason="registered_tests_and_actual_diff_green")
                        if reviewer is None:
                            raise AutonomyValidationError("independent_codex_reviewer_missing")
                        codex_review = reviewer(evidence, item)
                        review_errors = codex_review.validate(evidence.diff_hash)
                        if review_errors:
                            raise AutonomyValidationError(",".join(review_errors))
                        if codex_review.decision == "approve":
                            run.transition("codex_review_green", reason="independent_codex_review_approved")
                            break
                        if codex_review.decision == "block":
                            run.transition("blocked", reason="codex_review_blocked")
                            self.store.save_run(run)
                            return {"status": "blocked", "codex_review": codex_review.to_dict(), "run": run.to_dict()}
                        if repairer is None or attempts >= 2:
                            run.transition("blocked", reason="codex_review_repair_limit")
                            self.store.save_run(run)
                            return {"status": "blocked", "codex_review": codex_review.to_dict(), "run": run.to_dict()}
                        repairer(worktree, codex_review.findings, item)
                        attempts += 1
                        run.transitions.append({"from": run.state, "to": "implementing", "at_utc": utc_now(), "reason": "codex_review_repair"})
                        run.state = "implementing"
                    glm_review = glm.review(context, item, evidence, proposal)
                    review_errors = glm_review.validate(proposal_hash, evidence)
                    if review_errors:
                        run.transition("blocked", reason="glm_review_hash_or_schema_invalid")
                        self.store.save_run(run)
                        return {"status": "blocked", "glm_review_errors": review_errors, "run": run.to_dict()}
                    if glm_review.verdict != "approve":
                        run.transition("gretel_proposed", reason=f"glm_review_{glm_review.verdict}")
                        self.store.save_run(run)
                        return {"status": "gretel_proposed", "glm_review": glm_review.to_dict(), "run": run.to_dict()}
                    run.transition("glm_approved", reason="glm_review_bound_to_actual_evidence")
                    if shadow:
                        self.store.save_run(run)
                        self.store.record_rollout("shadow", run_id=run.run_id, success=True)
                        return {
                            "status": "shadow_green",
                            "run": run.to_dict(),
                            "evidence": evidence.to_dict(),
                            "codex_review": codex_review.to_dict(),
                            "glm_review": glm_review.to_dict(),
                            "three_golden_rules": evaluate_three_golden_rules(item),
                            "provider_calls": 0,
                            "github_actions": 0,
                            "automatic_merge": False,
                        }
                    golden_rules_evidence = bind_three_golden_rules_evidence(item, evidence, self.store)
                    if not ci_green:
                        run.transition("retryable", reason="github_ci_not_green")
                        self.store.save_run(run)
                        return {
                            "status": "retryable",
                            "run": run.to_dict(),
                            "evidence": evidence.to_dict(),
                            "three_golden_rules_evidence": golden_rules_evidence.to_dict(),
                        }
                    run.transition("ci_green", reason="ci_gate_reported_green")
                    run.transition("ready_for_human_merge", reason="draft_pr_preview_ready")
                    run.branch = f"gretel/{safe_slug(item.work_id)}-{run.run_id[:8]}"
                    self.store.save_run(run)
                    preview = build_draft_pr_preview(run, item, evidence, glm_review)
                    return {
                        "status": preview["status"],
                        "run": run.to_dict(),
                        "evidence": evidence.to_dict(),
                        "codex_review": codex_review.to_dict(),
                        "glm_review": glm_review.to_dict(),
                        "three_golden_rules_evidence": golden_rules_evidence.to_dict(),
                        "draft_pr": preview,
                    }
            except (AutonomyValidationError, OSError) as error:
                if run.state not in {"blocked", "retryable", "gretel_proposed"}:
                    run.transition("blocked", reason=str(error))
                self.store.save_run(run)
                return {"status": "blocked", "reason": str(error), "run": run.to_dict()}

    def record_human_merge(self, run_id: str, *, reviewer: str, merge_commit: str) -> dict[str, Any]:
        run_payload = self.store.get_run(run_id)
        if not run_payload:
            return {"status": "not_found", "run_id": run_id}
        if not reviewer.strip() or not merge_commit.strip():
            return {"status": "blocked", "reason": "human_reviewer_and_merge_commit_required"}
        if run_payload.get("state") != "ready_for_human_merge":
            return {"status": "blocked", "reason": "run_not_ready_for_human_merge", "run": run_payload}
        run = AutonomyRunV3(**{key: value for key, value in run_payload.items() if key in {"run_id", "work_item_hash", "trigger", "state", "created_at_utc", "transitions", "model_versions", "cost_usd", "branch", "pr_url", "block_reason", "merge_gate", "public_safety_status"}})
        run.transition("human_merged", reason=f"human_review:{reviewer}")
        self.store.save_run(run)
        return {"status": "human_merged", "reviewer": reviewer, "merge_commit": merge_commit, "run": run.to_dict(), "automatic_merge": False}


def work_item_from_issue(issue: dict[str, Any]) -> WorkItemV3:
    """Convert issue metadata to an inert work item; issue text is never executed."""
    if not isinstance(issue, dict):
        raise AutonomyValidationError("issue_must_be_object")
    title = str(issue.get("title", "")).strip()
    body = str(issue.get("body", "")).strip()
    if COMMAND_MARKERS.search(body):
        raise AutonomyValidationError("issue_body_contains_command_like_text")
    issue_scan = scan_text(f"{title}\n{body}", "github-issue-metadata")
    if issue_scan["status"] != "pass":
        raise AutonomyValidationError("issue_public_safety_failed")
    labels = tuple(str(label) for label in issue.get("labels", []) if SAFE_ID.fullmatch(str(label)))
    if "gretel-ready" not in labels:
        raise AutonomyValidationError("issue_missing_gretel_ready_label")
    evolution_payload = issue.get("evolution_chunk")
    return WorkItemV3(
        work_id=f"issue-{int(issue.get('number', 0) or 0)}",
        source="github_issue",
        hypothesis=title,
        product_delta=body[:1000],
        risk="medium",
        allowed_files=tuple(str(value) for value in issue.get("allowed_files", [])),
        test_ids=tuple(str(value) for value in issue.get("test_ids", [])),
        base_commit=str(issue.get("base_commit", "")),
        issue_number=int(issue.get("number", 0) or 0),
        labels=labels,
        evolution_chunk=(
            EvolutionChunkContractV1.from_dict(evolution_payload)
            if isinstance(evolution_payload, dict)
            else None
        ),
    )


def autonomy_doctor(store: AutonomyStore | None = None) -> dict[str, Any]:
    store = store or AutonomyStore()
    provider = ProviderGate(store=store)
    checks = [
        {"check_id": "provider_park_gate", "status": "pass", "detail": provider.status()["state"]},
        {"check_id": "automatic_merge", "status": "pass", "detail": "disabled"},
        {"check_id": "private_context", "status": "pass", "detail": "not accepted by public context builder"},
        {"check_id": "shell_input", "status": "pass", "detail": "issue text is inert metadata"},
        {"check_id": "budget", "status": "pass", "detail": store.budget_status()},
    ]
    return {"schema_version": "AutonomyDoctorV1", "status": "pass", "checks": checks}
