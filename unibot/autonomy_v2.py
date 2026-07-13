from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Protocol, TypedDict

from .public_safety import scan_text


AUTONOMY_V2_SCHEMA_VERSION = "unibot-autonomy-v2"
WORK_QUEUE_PATH = Path(__file__).with_name("autonomy_work_items.json")
VALID_STATUSES = {"candidate", "ready", "in_progress", "blocked", "done"}
VALID_WORK_KINDS = {"product", "research", "security"}
MAX_FILES_PER_RUN = 4
MAX_MODEL_CALLS_PER_RUN = 2
MAX_TOTAL_INPUT_TOKENS = 60_000
MAX_TOTAL_OUTPUT_TOKENS = 8_192
MAX_RUN_SECONDS = 45 * 60
MONTHLY_BUDGET_USD = 20.0
INPUT_USD_PER_MILLION = 1.40
OUTPUT_USD_PER_MILLION = 4.40
PRICING_CHECKED_ON = date(2026, 7, 11)
PRICING_SOURCE = "https://docs.z.ai/guides/overview/pricing"
BLOCKED_CONTEXT_PREFIXES = (".git/", ".unibot/", "knowledge/", "tmp/")
ROLLOUT_PHASES = {"shadow", "local_implementation", "draft_pr"}


class WorkItemV2(TypedDict):
    work_id: str
    priority: int
    status: str
    work_kind: str
    source: str
    goal: str
    hypothesis: str
    product_delta: str
    allowed_files: list[str]
    acceptance_tests: list[str]
    risk: str
    sources: list[str]


class GLMProposalV1(TypedDict):
    schema_version: str
    work_id: str
    problem: str
    hypothesis: str
    patch_outline: list[str]
    files: list[str]
    tests: list[str]
    scientific_sources: list[str]
    risks: list[str]
    confidence: float
    blocked_reason: str
    private_context_requested: bool


class GLMReviewV1(TypedDict):
    schema_version: str
    work_id: str
    verdict: str
    findings: list[str]
    test_gaps: list[str]
    claim_check: str
    confidence: float
    private_context_requested: bool


class Provider(Protocol):
    model: str

    def propose(self, work_item: WorkItemV2, context: str) -> ModelResult: ...

    def review(self, work_item: WorkItemV2, context: str, implementation_summary: str) -> ModelResult: ...


@dataclass(frozen=True)
class ModelResult:
    payload: dict[str, Any]
    input_tokens: int
    output_tokens: int
    model: str


@dataclass(frozen=True)
class PublicContext:
    text: str
    files: tuple[str, ...]
    estimated_input_tokens: int
    packet_hash: str


@dataclass(frozen=True)
class RunSummaryV2:
    schema_version: str
    run_id: str
    stage: str
    status: str
    work_id: str
    model: str
    context_hash: str
    result_hash: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    public_safety_status: str
    autonomous_apply: bool
    autonomous_merge: bool
    human_review_required: bool
    created_at_utc: str


def load_work_queue(path: Path | None = None) -> dict[str, Any]:
    queue_path = path or WORK_QUEUE_PATH
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("invalid autonomy work queue")
    return payload


def validate_work_item(raw_item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_strings = ["work_id", "status", "work_kind", "source", "goal", "hypothesis", "product_delta", "risk"]
    for key in required_strings:
        if not isinstance(raw_item.get(key), str) or not str(raw_item.get(key, "")).strip():
            errors.append(f"missing_or_invalid:{key}")
    if raw_item.get("status") not in VALID_STATUSES:
        errors.append("invalid:status")
    if raw_item.get("work_kind") not in VALID_WORK_KINDS:
        errors.append("invalid:work_kind")
    if not isinstance(raw_item.get("priority"), int) or int(raw_item.get("priority", 0)) < 1:
        errors.append("invalid:priority")
    files = raw_item.get("allowed_files")
    if not isinstance(files, list) or not files or len(files) > MAX_FILES_PER_RUN:
        errors.append("invalid:allowed_files")
    elif any(not isinstance(item, str) or item.startswith(("/", "../")) for item in files):
        errors.append("unsafe:allowed_files")
    tests = raw_item.get("acceptance_tests")
    if not isinstance(tests, list) or not tests or any(not isinstance(item, str) or not item.strip() for item in tests):
        errors.append("invalid:acceptance_tests")
    sources = raw_item.get("sources")
    if not isinstance(sources, list) or any(not isinstance(item, str) or not item.startswith("https://") for item in sources):
        errors.append("invalid:sources")
    product_delta = str(raw_item.get("product_delta", ""))
    if len(product_delta.strip()) < 24:
        errors.append("invalid:product_delta")
    if raw_item.get("source") != "failing_gate":
        receipt_words = {"receipt", "hash alignment", "readiness tail", "gate receipt"}
        combined = " ".join(str(raw_item.get(key, "")) for key in ("work_id", "goal", "product_delta")).lower()
        if any(marker in combined for marker in receipt_words):
            errors.append("receipt_only_work_blocked")
    return sorted(set(errors))


def validated_work_items(path: Path | None = None) -> tuple[list[WorkItemV2], dict[str, list[str]]]:
    queue = load_work_queue(path)
    valid: list[WorkItemV2] = []
    invalid: dict[str, list[str]] = {}
    for raw in queue["items"]:
        if not isinstance(raw, dict):
            invalid["non_object"] = ["invalid:item"]
            continue
        errors = validate_work_item(raw)
        work_id = str(raw.get("work_id", "missing"))
        if errors:
            invalid[work_id] = errors
        else:
            valid.append(raw)  # type: ignore[arg-type]
    return sorted(valid, key=lambda item: (item["priority"], item["work_id"])), invalid


def select_ready_work_item(path: Path | None = None, work_id: str = "") -> WorkItemV2 | None:
    items, invalid = validated_work_items(path)
    if invalid:
        return None
    candidates = [item for item in items if item["status"] == "ready"]
    if work_id:
        candidates = [item for item in candidates if item["work_id"] == work_id]
    return candidates[0] if candidates else None


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.stdout.strip()


def repository_preflight(repo: Path, work_id: str = "") -> dict[str, Any]:
    root = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    branch = _git(root, "branch", "--show-current")
    changes = [line for line in _git(root, "status", "--porcelain").splitlines() if line.strip()]
    item = select_ready_work_item(work_id=work_id)
    _, invalid = validated_work_items()
    failed: list[str] = []
    if changes:
        failed.append("worktree_not_clean")
    if invalid:
        failed.append("invalid_work_queue")
    if item is None:
        failed.append("no_ready_product_work")
    if (date.today() - PRICING_CHECKED_ON).days > 45:
        failed.append("glm_pricing_source_stale")
    rollout = rollout_status(root)
    implementation_allowed = branch not in {"", "main", "master"} and rollout["phase"] in {
        "local_implementation",
        "draft_pr",
    }
    return {
        "schema_version": "unibot-autonomy-preflight-v2",
        "status": "ready" if not failed else "blocked",
        "failed_checks": failed,
        "branch": branch,
        "ready_for_shadow": not failed,
        "ready_for_implementation": not failed and implementation_allowed,
        "direct_main_change_blocked": not implementation_allowed,
        "rollout_phase": rollout["phase"],
        "draft_pr_allowed": bool(rollout["draft_pr_allowed"]),
        "selected_work_id": item["work_id"] if item else "",
        "max_files_per_run": MAX_FILES_PER_RUN,
        "max_model_calls_per_run": MAX_MODEL_CALLS_PER_RUN,
        "max_run_seconds": MAX_RUN_SECONDS,
        "monthly_budget_usd": MONTHLY_BUDGET_USD,
        "pricing_source": PRICING_SOURCE,
        "provider_call_executed": False,
    }


def _tracked_files(repo: Path) -> set[str]:
    output = _git(repo, "ls-files", "-z")
    return {item for item in output.split("\0") if item}


def build_public_context(repo: Path, work_item: WorkItemV2) -> PublicContext:
    repo = repo.resolve()
    tracked = _tracked_files(repo)
    requested = ["README.md", "AUTHORS.md", "docs/unibot/UNIBOT_AUTONOMY_V2.md", *work_item["allowed_files"]]
    selected: list[str] = []
    sections: list[str] = []
    for relative in dict.fromkeys(requested):
        if relative.startswith(BLOCKED_CONTEXT_PREFIXES) or relative not in tracked:
            continue
        path = (repo / relative).resolve()
        if repo not in path.parents or path.is_symlink() or not path.is_file() or path.stat().st_size > 250_000:
            continue
        text = path.read_text(encoding="utf-8")
        scan = scan_text(text, relative)
        if scan["status"] != "pass":
            raise ValueError(f"public safety blocked context file: {relative}")
        selected.append(relative)
        sections.append(f"--- {relative} ---\n{text}")
    item_text = json.dumps(work_item, ensure_ascii=True, sort_keys=True)
    context = f"WORK ITEM\n{item_text}\n\nPUBLIC TRACKED CONTEXT\n" + "\n\n".join(sections)
    estimated_tokens = max(1, (len(context) + 3) // 4)
    if estimated_tokens > MAX_TOTAL_INPUT_TOKENS:
        raise ValueError("public context exceeds token budget")
    scan = scan_text(context, "autonomy-v2-context")
    if scan["status"] != "pass":
        raise ValueError("public safety blocked assembled context")
    packet_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
    return PublicContext(context, tuple(selected), estimated_tokens, packet_hash)


def validate_glm_proposal(payload: dict[str, Any], work_item: WorkItemV2) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "work_id",
        "problem",
        "hypothesis",
        "patch_outline",
        "files",
        "tests",
        "scientific_sources",
        "risks",
        "confidence",
        "blocked_reason",
        "private_context_requested",
    }
    if set(payload) != required:
        errors.append("invalid_schema_fields")
    if payload.get("schema_version") != "unibot-glm-proposal-v1":
        errors.append("invalid_schema_version")
    if payload.get("work_id") != work_item["work_id"]:
        errors.append("work_id_mismatch")
    for key in ("patch_outline", "files", "tests", "scientific_sources", "risks"):
        value = payload.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"invalid:{key}")
    files = payload.get("files", [])
    if isinstance(files, list) and (len(files) > MAX_FILES_PER_RUN or not set(files).issubset(set(work_item["allowed_files"]))):
        errors.append("files_outside_work_item")
    if payload.get("private_context_requested") is not False:
        errors.append("private_context_request_blocked")
    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append("invalid:confidence")
    if scan_text(json.dumps(payload, ensure_ascii=False), "glm-proposal")["status"] != "pass":
        errors.append("public_safety_blocked")
    return sorted(set(errors))


def validate_glm_review(payload: dict[str, Any], work_item: WorkItemV2) -> list[str]:
    required = {
        "schema_version",
        "work_id",
        "verdict",
        "findings",
        "test_gaps",
        "claim_check",
        "confidence",
        "private_context_requested",
    }
    errors: list[str] = []
    if set(payload) != required:
        errors.append("invalid_schema_fields")
    if payload.get("schema_version") != "unibot-glm-review-v1":
        errors.append("invalid_schema_version")
    if payload.get("work_id") != work_item["work_id"]:
        errors.append("work_id_mismatch")
    if payload.get("verdict") not in {"approve", "revise", "block"}:
        errors.append("invalid:verdict")
    if payload.get("private_context_requested") is not False:
        errors.append("private_context_request_blocked")
    for key in ("findings", "test_gaps"):
        value = payload.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"invalid:{key}")
    if scan_text(json.dumps(payload, ensure_ascii=False), "glm-review")["status"] != "pass":
        errors.append("public_safety_blocked")
    return sorted(set(errors))


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return round(
        input_tokens * INPUT_USD_PER_MILLION / 1_000_000
        + output_tokens * OUTPUT_USD_PER_MILLION / 1_000_000,
        6,
    )


def state_dir(repo: Path) -> Path:
    configured = os.environ.get("UNIBOT_STATE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return repo.resolve() / ".unibot"


def rollout_status(repo: Path) -> dict[str, Any]:
    path = state_dir(repo) / "rollout.json"
    if not path.exists():
        return {
            "schema_version": "unibot-autonomy-rollout-v1",
            "phase": "shadow",
            "shadow_green_runs": 0,
            "local_green_runs": 0,
            "leak_findings": 0,
            "total_leak_findings": 0,
            "draft_pr_allowed": False,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "schema_version": "unibot-autonomy-rollout-v1",
            "phase": "shadow",
            "shadow_green_runs": 0,
            "local_green_runs": 0,
            "leak_findings": 1,
            "total_leak_findings": 1,
            "draft_pr_allowed": False,
        }
    if not isinstance(payload, dict) or payload.get("phase") not in ROLLOUT_PHASES:
        raise RuntimeError("invalid autonomy rollout state")
    return payload


def record_rollout_outcome(repo: Path, *, stage: str, green: bool, leak_findings: int = 0) -> dict[str, Any]:
    current = dict(rollout_status(repo))
    new_leaks = max(0, leak_findings)
    current["leak_findings"] = int(current.get("leak_findings", 0)) + new_leaks
    current["total_leak_findings"] = int(current.get("total_leak_findings", 0)) + new_leaks
    if leak_findings or not green:
        current["phase"] = "shadow"
        current["shadow_green_runs"] = 0
        current["local_green_runs"] = 0
    elif current["phase"] == "shadow" and stage == "proposal":
        if int(current.get("shadow_green_runs", 0)) == 0:
            current["leak_findings"] = 0
        current["shadow_green_runs"] = int(current.get("shadow_green_runs", 0)) + 1
        if current["shadow_green_runs"] >= 10:
            current["phase"] = "local_implementation"
    elif current["phase"] == "local_implementation" and stage == "review":
        current["local_green_runs"] = int(current.get("local_green_runs", 0)) + 1
        if current["local_green_runs"] >= 10:
            current["phase"] = "draft_pr"
    current["draft_pr_allowed"] = current["phase"] == "draft_pr" and current["leak_findings"] == 0
    directory = state_dir(repo)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "rollout.json"
    temporary = directory / "rollout.json.tmp"
    temporary.write_text(json.dumps(current, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return current


def read_usage(repo: Path) -> list[dict[str, Any]]:
    path = state_dir(repo) / "usage.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def monthly_spend_usd(repo: Path, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    prefix = now.strftime("%Y-%m")
    return round(
        sum(float(item.get("estimated_cost_usd", 0.0)) for item in read_usage(repo) if str(item.get("created_at_utc", "")).startswith(prefix)),
        6,
    )


def _append_usage(repo: Path, summary: RunSummaryV2) -> None:
    directory = state_dir(repo)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "usage.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(summary), ensure_ascii=True, sort_keys=True) + "\n")


def _write_summary(repo: Path, summary: RunSummaryV2) -> None:
    directory = state_dir(repo) / "runs"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{summary.run_id}-{summary.stage}.json").write_text(
        json.dumps(asdict(summary), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _calls_for_run(repo: Path, run_id: str) -> list[dict[str, Any]]:
    return [item for item in read_usage(repo) if item.get("run_id") == run_id]


def _assert_budget(repo: Path, run_id: str, estimated_input_tokens: int) -> None:
    calls = _calls_for_run(repo, run_id)
    if len(calls) >= MAX_MODEL_CALLS_PER_RUN:
        raise RuntimeError("model call limit reached for run")
    used_input = sum(int(item.get("input_tokens", 0)) for item in calls)
    used_output = sum(int(item.get("output_tokens", 0)) for item in calls)
    if used_input + estimated_input_tokens > MAX_TOTAL_INPUT_TOKENS:
        raise RuntimeError("input token limit reached for run")
    if used_output + 4096 > MAX_TOTAL_OUTPUT_TOKENS:
        raise RuntimeError("output token limit reached for run")
    worst_case_cost = estimate_cost_usd(estimated_input_tokens, 4096)
    if monthly_spend_usd(repo) + worst_case_cost > MONTHLY_BUDGET_USD:
        raise RuntimeError("monthly GLM budget reached")


def _build_summary(
    *,
    run_id: str,
    stage: str,
    status: str,
    work_id: str,
    context_hash: str,
    result: ModelResult,
) -> RunSummaryV2:
    result_text = json.dumps(result.payload, ensure_ascii=True, sort_keys=True)
    scan = scan_text(result_text, f"autonomy-v2-{stage}")
    return RunSummaryV2(
        schema_version="unibot-run-summary-v2",
        run_id=run_id,
        stage=stage,
        status=status,
        work_id=work_id,
        model=result.model,
        context_hash=context_hash,
        result_hash=hashlib.sha256(result_text.encode("utf-8")).hexdigest(),
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        estimated_cost_usd=estimate_cost_usd(result.input_tokens, result.output_tokens),
        public_safety_status=scan["status"],
        autonomous_apply=False,
        autonomous_merge=False,
        human_review_required=True,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
    )


def run_proposal_cycle(repo: Path, provider: Provider, work_id: str = "", run_id: str = "") -> tuple[RunSummaryV2, dict[str, Any]]:
    item = select_ready_work_item(work_id=work_id)
    if item is None:
        raise RuntimeError("no ready product work item")
    context = build_public_context(repo, item)
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    _assert_budget(repo, run_id, context.estimated_input_tokens)
    result = provider.propose(item, context.text)
    errors = validate_glm_proposal(result.payload, item)
    status = "shadow_proposal_ready" if not errors else "blocked_invalid_proposal"
    summary = _build_summary(
        run_id=run_id,
        stage="proposal",
        status=status,
        work_id=item["work_id"],
        context_hash=context.packet_hash,
        result=result,
    )
    _append_usage(repo, summary)
    _write_summary(repo, summary)
    record_rollout_outcome(
        repo,
        stage="proposal",
        green=not errors and summary.public_safety_status == "pass",
        leak_findings=0 if summary.public_safety_status == "pass" else 1,
    )
    return summary, {"proposal": result.payload if not errors else {}, "validation_errors": errors}


def run_review_cycle(
    repo: Path,
    provider: Provider,
    run_id: str,
    implementation_summary: str,
    work_id: str = "",
) -> tuple[RunSummaryV2, dict[str, Any]]:
    item = select_ready_work_item(work_id=work_id)
    if item is None:
        raise RuntimeError("no ready product work item")
    if len(implementation_summary) > 20_000:
        raise ValueError("implementation summary too large")
    if scan_text(implementation_summary, "implementation-summary")["status"] != "pass":
        raise ValueError("implementation summary blocked by public safety")
    context = build_public_context(repo, item)
    estimated_review_tokens = context.estimated_input_tokens + max(1, len(implementation_summary) // 4)
    _assert_budget(repo, run_id, estimated_review_tokens)
    result = provider.review(item, context.text, implementation_summary)
    errors = validate_glm_review(result.payload, item)
    status = "review_ready" if not errors else "blocked_invalid_review"
    summary = _build_summary(
        run_id=run_id,
        stage="review",
        status=status,
        work_id=item["work_id"],
        context_hash=context.packet_hash,
        result=result,
    )
    _append_usage(repo, summary)
    _write_summary(repo, summary)
    verdict = str(result.payload.get("verdict", ""))
    record_rollout_outcome(
        repo,
        stage="review",
        green=not errors and verdict == "approve" and summary.public_safety_status == "pass",
        leak_findings=0 if summary.public_safety_status == "pass" else 1,
    )
    return summary, {"review": result.payload if not errors else {}, "validation_errors": errors}


def autonomy_status(repo: Path) -> dict[str, Any]:
    items, invalid = validated_work_items()
    counts = {status: len([item for item in items if item["status"] == status]) for status in sorted(VALID_STATUSES)}
    next_item = select_ready_work_item()
    rollout = rollout_status(repo)
    return {
        "schema_version": AUTONOMY_V2_SCHEMA_VERSION,
        "status": "ready" if not invalid else "blocked",
        "queue_counts": counts,
        "invalid_items": invalid,
        "next_work_id": next_item["work_id"] if next_item else "",
        "monthly_spend_usd": monthly_spend_usd(repo),
        "monthly_budget_usd": MONTHLY_BUDGET_USD,
        "provider_call_default": "disabled_without_public_unibot_scope",
        "rollout": rollout,
        "draft_pr_allowed": bool(rollout["draft_pr_allowed"]),
        "autonomous_apply": False,
        "autonomous_merge": False,
    }
