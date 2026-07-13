from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from unibot.autonomy_v2 import (
    ModelResult,
    WorkItemV2,
    autonomy_status,
    build_public_context,
    load_work_queue,
    read_usage,
    repository_preflight,
    record_rollout_outcome,
    rollout_status,
    run_proposal_cycle,
    run_review_cycle,
    select_ready_work_item,
    validate_glm_proposal,
    validate_work_item,
    validated_work_items,
)


def work_item() -> WorkItemV2:
    return {
        "work_id": "synthetic_product_delta",
        "priority": 1,
        "status": "ready",
        "work_kind": "product",
        "source": "measured_product_gap",
        "goal": "Improve one public synthetic learner workflow.",
        "hypothesis": "A bounded implementation makes the selected workflow observable and testable.",
        "product_delta": "A learner can complete the synthetic workflow with one fewer ambiguous step.",
        "allowed_files": ["module.py"],
        "acceptance_tests": ["python -m unittest test_module.py"],
        "risk": "low",
        "sources": ["https://example.invalid/public-source"],
    }


class FakeProvider:
    model = "glm-5.2-test-double"

    def propose(self, item: WorkItemV2, context: str) -> ModelResult:
        self.last_context = context
        return ModelResult(
            payload={
                "schema_version": "unibot-glm-proposal-v1",
                "work_id": item["work_id"],
                "problem": "The synthetic flow has one ambiguous step.",
                "hypothesis": item["hypothesis"],
                "patch_outline": ["Clarify the bounded public flow."],
                "files": ["module.py"],
                "tests": item["acceptance_tests"],
                "scientific_sources": item["sources"],
                "risks": ["A clarification could overfit one fixture."],
                "confidence": 0.8,
                "blocked_reason": "",
                "private_context_requested": False,
            },
            input_tokens=100,
            output_tokens=50,
            model=self.model,
        )

    def review(self, item: WorkItemV2, context: str, implementation_summary: str) -> ModelResult:
        self.last_review = (context, implementation_summary)
        return ModelResult(
            payload={
                "schema_version": "unibot-glm-review-v1",
                "work_id": item["work_id"],
                "verdict": "approve",
                "findings": [],
                "test_gaps": [],
                "claim_check": "Practice-only and human-review boundaries remain visible.",
                "confidence": 0.82,
                "private_context_requested": False,
            },
            input_tokens=120,
            output_tokens=40,
            model=self.model,
        )


class AutonomyV2Tests(unittest.TestCase):
    def make_repo(self, root: Path) -> tuple[Path, Path]:
        repo = root / "repo"
        repo.mkdir()
        (repo / "README.md").write_text("# Public synthetic repository\n", encoding="utf-8")
        (repo / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        (repo / "untracked-private.txt").write_text("not part of provider context\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Synthetic Test"], cwd=repo, check=True)
        synthetic_email = "synthetic" + "@" + "example.invalid"
        subprocess.run(["git", "config", "user.email", synthetic_email], cwd=repo, check=True)
        subprocess.run(["git", "add", "README.md", "module.py"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "synthetic baseline"], cwd=repo, check=True)
        queue = root / "queue.json"
        queue.write_text(
            json.dumps(
                {
                    "schema_version": "unibot-autonomy-work-queue-v2",
                    "active_milestone": "synthetic",
                    "items": [work_item()],
                }
            ),
            encoding="utf-8",
        )
        return repo, queue

    def test_public_queue_has_exactly_one_ready_product_item(self) -> None:
        queue = load_work_queue()
        items, invalid = validated_work_items()
        ready = [item for item in items if item["status"] == "ready"]
        self.assertEqual(queue["schema_version"], "unibot-autonomy-work-queue-v2")
        self.assertEqual(invalid, {})
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]["work_id"], "guardian_semantic_precision_benchmark")
        self.assertEqual(select_ready_work_item()["work_kind"], "research")  # type: ignore[index]

    def test_receipt_only_work_is_rejected(self) -> None:
        item = dict(work_item())
        item["work_id"] = "readiness_receipt_tail"
        item["goal"] = "Add one more gate receipt for the readiness tail."
        self.assertIn("receipt_only_work_blocked", validate_work_item(item))

    def test_context_contains_only_selected_tracked_public_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, _ = self.make_repo(Path(temporary))
            context = build_public_context(repo, work_item())
        self.assertIn("module.py", context.files)
        self.assertNotIn("untracked-private.txt", context.text)
        self.assertNotIn(str(repo), context.text)
        self.assertLess(context.estimated_input_tokens, 60_000)

    def test_preflight_blocks_direct_implementation_on_default_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, queue = self.make_repo(Path(temporary))
            (repo / "untracked-private.txt").unlink()
            with patch("unibot.autonomy_v2.WORK_QUEUE_PATH", queue):
                result = repository_preflight(repo)
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["ready_for_shadow"])
        self.assertFalse(result["ready_for_implementation"])
        self.assertTrue(result["direct_main_change_blocked"])

    def test_proposal_review_and_call_limit_use_hash_only_run_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, queue = self.make_repo(Path(temporary))
            provider = FakeProvider()
            with patch("unibot.autonomy_v2.WORK_QUEUE_PATH", queue):
                proposal_summary, proposal = run_proposal_cycle(repo, provider, run_id="synthetic-run")
                review_summary, review = run_review_cycle(
                    repo,
                    provider,
                    "synthetic-run",
                    "Changed module.py and the focused synthetic test passed.",
                )
                with self.assertRaises(RuntimeError):
                    run_proposal_cycle(repo, provider, run_id="synthetic-run")

            self.assertEqual(proposal_summary.status, "shadow_proposal_ready")
            self.assertEqual(review_summary.status, "review_ready")
            self.assertEqual(proposal["validation_errors"], [])
            self.assertEqual(review["validation_errors"], [])
            usage = read_usage(repo)
            self.assertEqual(len(usage), 2)
            stored = (repo / ".unibot" / "runs" / "synthetic-run-proposal.json").read_text(encoding="utf-8")
            self.assertNotIn("ambiguous step", stored)
            self.assertIn("result_hash", stored)

    def test_invalid_proposal_cannot_request_private_context_or_extra_files(self) -> None:
        provider = FakeProvider()
        result = provider.propose(work_item(), "public")
        result.payload["private_context_requested"] = True
        result.payload["files"] = ["outside.py"]
        errors = validate_glm_proposal(result.payload, work_item())
        self.assertIn("private_context_request_blocked", errors)
        self.assertIn("files_outside_work_item", errors)

    def test_status_never_grants_apply_or_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status = autonomy_status(Path(temporary))
        self.assertFalse(status["autonomous_apply"])
        self.assertFalse(status["autonomous_merge"])
        self.assertEqual(status["monthly_budget_usd"], 20.0)

    def test_rollout_requires_ten_shadow_and_ten_local_green_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            for _ in range(9):
                state = record_rollout_outcome(repo, stage="proposal", green=True)
            self.assertEqual(state["phase"], "shadow")
            state = record_rollout_outcome(repo, stage="proposal", green=True)
            self.assertEqual(state["phase"], "local_implementation")
            for _ in range(10):
                state = record_rollout_outcome(repo, stage="review", green=True)
            self.assertEqual(state["phase"], "draft_pr")
            self.assertTrue(state["draft_pr_allowed"])

            state = record_rollout_outcome(repo, stage="review", green=False, leak_findings=1)
            self.assertEqual(state["phase"], "shadow")
            self.assertFalse(state["draft_pr_allowed"])
            self.assertEqual(rollout_status(repo)["leak_findings"], 1)

    def test_external_neutral_state_directory_preserves_rollout_outside_clone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            clone = root / "ephemeral-clone"
            clone.mkdir()
            neutral_state = root / "neutral-state"
            with patch.dict("os.environ", {"UNIBOT_STATE_DIR": str(neutral_state)}):
                result = record_rollout_outcome(clone, stage="proposal", green=True)
                self.assertEqual(rollout_status(clone)["shadow_green_runs"], 1)
            self.assertEqual(result["phase"], "shadow")
            self.assertTrue((neutral_state / "rollout.json").is_file())
            self.assertFalse((clone / ".unibot").exists())


if __name__ == "__main__":
    unittest.main()
