from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from unibot.autonomy_v3 import (
    AutonomyController,
    AutonomyRunV3,
    AutonomyStore,
    CodexReviewV1,
    GLMReviewV2,
    ProviderGate,
    TestRegistry,
    WorkItemV3,
    default_test_registry,
    derive_implementation_evidence,
    sha256_json,
    validate_glm_proposal,
    work_item_from_issue,
)


class MockGLM:
    model_version = "glm-5.2-mock"

    def propose(self, context: dict, item: WorkItemV3) -> dict:
        return {
            "schema_version": "GLMProposalV1",
            "work_item_hash": item.work_item_hash,
            "base_commit": item.base_commit,
            "problem": "synthetic measurable gap",
            "hypothesis": item.hypothesis,
            "change_outline": ["change one public file"],
            "affected_files": list(item.allowed_files),
            "tests": list(item.test_ids),
            "scientific_sources": ["synthetic-source-card"],
            "risks": ["human review remains required"],
            "uncertainty": "mock proposal for local shadow testing",
            "blocked_reason": "",
        }

    def review(self, context: dict, item: WorkItemV3, evidence, proposal: dict) -> GLMReviewV2:
        return GLMReviewV2(
            run_id=evidence.run_id,
            proposal_hash=sha256_json(proposal),
            diff_hash=evidence.diff_hash,
            evidence_hash=evidence.evidence_hash,
            verdict="approve",
            risks=["synthetic shadow run"],
            uncertainty="mock review is not a release decision",
            call_count=2,
        )


class AutonomyV3Tests(unittest.TestCase):
    def make_git_repo(self) -> tuple[tempfile.TemporaryDirectory, Path, str]:
        holder = tempfile.TemporaryDirectory()
        root = Path(holder.name)
        (root / "public.py").write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test.example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "UniBot Test"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "public.py"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
        base = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        subprocess.run(["git", "-C", str(root), "checkout", "-qb", "gretel/test-shadow"], check=True)
        return holder, root, base

    def test_work_item_is_hashed_and_private_paths_are_rejected(self) -> None:
        item = WorkItemV3(
            work_id="guardian-benchmark",
            source="measured_gap",
            hypothesis="A measurable synthetic gap can be covered by a fixed test.",
            product_delta="Add one deterministic regression test.",
            risk="low",
            allowed_files=("public.py",),
            test_ids=("test.guardian",),
            base_commit="abcdef1",
        )
        self.assertEqual(item.validate(), [])
        self.assertEqual(item.to_dict()["work_item_hash"], item.work_item_hash)
        bad = WorkItemV3(**{**item.__dict__, "allowed_files": ("private-notebook.ipynb",)})
        self.assertIn("private_path_not_allowed", bad.validate())

    def test_provider_defaults_to_parked_and_scope_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AutonomyStore(Path(tmp) / "state.sqlite3")
            gate = ProviderGate(Path(tmp) / "provider.json", store=store)
            self.assertEqual(gate.status()["state"], "parked_awaiting_zai_balance")
            with self.assertRaises(ValueError):
                gate.unpark("all-repositories")
            enabled = gate.unpark("public-unibot-only")
            self.assertTrue(enabled["call_allowed"])
            self.assertEqual(os.stat(Path(tmp) / "provider.json").st_mode & 0o777, 0o600)
            store.close()

    def test_budget_warns_at_fifteen_and_stops_above_twenty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AutonomyStore(Path(tmp) / "state.sqlite3")
            self.assertEqual(store.record_cost(15, month="2099-01")["status"], "warning")
            self.assertEqual(store.record_cost(5, month="2099-01")["status"], "warning")
            self.assertEqual(store.record_cost(0.01, month="2099-01")["reason"], "monthly_hard_stop")
            store.close()

    def test_actual_diff_is_derived_and_controller_reaches_human_gate(self) -> None:
        holder, root, base = self.make_git_repo()
        try:
            item = WorkItemV3(
                work_id="guardian-benchmark",
                source="measured_gap",
                hypothesis="A fixed benchmark improves measurable guardian coverage.",
                product_delta="Add a synthetic benchmark fixture.",
                risk="medium",
                allowed_files=("public.py",),
                test_ids=("test.guardian",),
                base_commit=base,
            )
            with tempfile.TemporaryDirectory() as state_dir:
                store = AutonomyStore(Path(state_dir) / "state.sqlite3")
                gate = ProviderGate(Path(state_dir) / "provider.json", store=store)
                gate.unpark("public-unibot-only")
                controller = AutonomyController(
                    repo_root=root,
                    store=store,
                    provider_gate=gate,
                    lease=__import__("unibot.autonomy_v3", fromlist=["AutonomyLease"]).AutonomyLease(Path(state_dir) / "run.lock"),
                )
                tests = TestRegistry()
                tests.register("test.guardian", lambda: True)

                seen_worktrees: list[Path] = []

                def implementer(worktree: Path, proposal: dict, work_item: WorkItemV3) -> None:
                    seen_worktrees.append(worktree)
                    (worktree / "public.py").write_text("VALUE = 2\n", encoding="utf-8")

                def reviewer(evidence, work_item):
                    return CodexReviewV1(run_id=evidence.run_id, diff_hash=evidence.diff_hash, decision="approve")

                result = controller.execute(
                    item,
                    glm=MockGLM(),
                    implementer=implementer,
                    reviewer=reviewer,
                    tests=tests,
                    shadow=False,
                    ci_green=True,
                )
                self.assertEqual(result["status"], "ready_for_human_merge")
                self.assertTrue(result["evidence"]["actual_diff_verified"])
                self.assertEqual(result["draft_pr"]["external_action_executed"], False)
                self.assertEqual(result["run"]["state"], "ready_for_human_merge")
                self.assertFalse(result["run"]["automatic_merge"])
                self.assertEqual(result["draft_pr"]["public_safety_status"], "pass")
                self.assertEqual((root / "public.py").read_text(encoding="utf-8"), "VALUE = 1\n")
                self.assertTrue(seen_worktrees)
                self.assertFalse(seen_worktrees[0].exists())
                store.close()
        finally:
            holder.cleanup()

    def test_parked_provider_stops_before_implementation(self) -> None:
        holder, root, base = self.make_git_repo()
        try:
            item = WorkItemV3(
                work_id="parked-check",
                source="active_milestone",
                hypothesis="Provider parking has no side effects.",
                product_delta="No code change is allowed while parked.",
                risk="low",
                allowed_files=("public.py",),
                test_ids=("test.guardian",),
                base_commit=base,
            )
            with tempfile.TemporaryDirectory() as state_dir:
                store = AutonomyStore(Path(state_dir) / "state.sqlite3")
                controller = AutonomyController(
                    repo_root=root,
                    store=store,
                    provider_gate=ProviderGate(Path(state_dir) / "provider.json", store=store),
                )
                called = []
                result = controller.execute(item, glm=MockGLM(), implementer=lambda *_: called.append(True), shadow=False)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason"], "parked_before_keychain_sdk_and_network")
                self.assertEqual(called, [])
                store.close()
        finally:
            holder.cleanup()

    def test_main_is_a_read_only_source_for_a_no_change_shadow_run(self) -> None:
        holder, root, base = self.make_git_repo()
        try:
            subprocess.run(["git", "-C", str(root), "checkout", "-q", "main"], check=True)
            item = WorkItemV3(
                work_id="main-protection",
                source="failing_check",
                hypothesis="main must remain human-controlled.",
                product_delta="No autonomous write may reach main.",
                risk="high",
                allowed_files=("public.py",),
                test_ids=("test.guardian",),
                base_commit=base,
            )
            with tempfile.TemporaryDirectory() as state_dir:
                store = AutonomyStore(Path(state_dir) / "state.sqlite3")
                controller = AutonomyController(
                    repo_root=root,
                    store=store,
                    provider_gate=ProviderGate(Path(state_dir) / "provider.json", store=store),
                )
                tests = TestRegistry()
                tests.register("test.guardian", lambda: True)
                seen_worktrees: list[Path] = []

                def registry_factory(worktree: Path) -> TestRegistry:
                    seen_worktrees.append(worktree)
                    return tests

                result = controller.run_shadow_rollout(item, test_registry_factory=registry_factory)
                self.assertEqual(result["status"], "shadow_green")
                self.assertEqual((root / "public.py").read_text(encoding="utf-8"), "VALUE = 1\n")
                self.assertTrue(seen_worktrees)
                self.assertFalse(seen_worktrees[0].exists())
                self.assertEqual(store.rollout_status()["lanes"]["shadow"]["successful_runs"], 1)
                store.close()
        finally:
            holder.cleanup()

    def test_proposal_binding_and_issue_text_never_becomes_a_command(self) -> None:
        item = WorkItemV3(
            work_id="safe-proposal",
            source="measured_gap",
            hypothesis="safe",
            product_delta="safe",
            risk="low",
            allowed_files=("public.py",),
            test_ids=("test.guardian",),
            base_commit="abc123",
        )
        proposal = MockGLM().propose({}, item)
        proposal["base_commit"] = "other"
        self.assertEqual(validate_glm_proposal(proposal, item)["status"], "blocked")
        with self.assertRaises(ValueError):
            work_item_from_issue({"number": 7, "title": "x", "body": "$(rm -rf /)", "labels": ["gretel-ready"]})

    def test_local_rollout_is_provider_free_and_discards_the_worktree(self) -> None:
        holder, root, base = self.make_git_repo()
        try:
            item = WorkItemV3(
                work_id="local-rollout",
                source="measured_gap",
                hypothesis="A local rehearsal can prove isolation before provider use.",
                product_delta="Change one public fixture only in a disposable worktree.",
                risk="low",
                allowed_files=("public.py",),
                test_ids=("test.guardian",),
                base_commit=base,
            )
            with tempfile.TemporaryDirectory() as state_dir:
                store = AutonomyStore(Path(state_dir) / "state.sqlite3")
                controller = AutonomyController(
                    repo_root=root,
                    store=store,
                    provider_gate=ProviderGate(Path(state_dir) / "provider.json", store=store),
                )
                tests = TestRegistry()
                tests.register("test.guardian", lambda: True)
                seen_worktrees: list[Path] = []

                def implementer(worktree: Path, proposal: dict, work_item: WorkItemV3) -> None:
                    seen_worktrees.append(worktree)
                    (worktree / "public.py").write_text("VALUE = 3\n", encoding="utf-8")

                def reviewer(evidence, work_item):
                    return CodexReviewV1(run_id=evidence.run_id, diff_hash=evidence.diff_hash, decision="approve")

                result = controller.run_local_rollout(item, implementer=implementer, reviewer=reviewer, tests=tests)
                self.assertEqual(result["status"], "local_green")
                self.assertEqual(result["provider_calls"], 0)
                self.assertEqual((root / "public.py").read_text(encoding="utf-8"), "VALUE = 1\n")
                self.assertTrue(seen_worktrees)
                self.assertFalse(seen_worktrees[0].exists())
                self.assertEqual(store.rollout_status()["lanes"]["local"]["successful_runs"], 1)
                store.close()
        finally:
            holder.cleanup()

    def test_registry_is_fixed_and_recovery_marks_only_interrupted_runs_retryable(self) -> None:
        registry = default_test_registry(Path.cwd())
        self.assertEqual(
            registry.registered_ids,
            ("autonomy.v3", "guardian.semantic_precision", "public.safety"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            store = AutonomyStore(Path(temporary) / "state.sqlite3")
            run = AutonomyRunV3(
                run_id="interrupted-run",
                work_item_hash="a" * 64,
                trigger="manual",
                state="implementing",
                created_at_utc="2000-01-01T00:00:00+00:00",
            )
            store.save_run(run)
            self.assertEqual(store.recover_interrupted_runs(stale_after_seconds=1), ["interrupted-run"])
            self.assertEqual(store.get_run("interrupted-run")["state"], "retryable")
            store.close()


if __name__ == "__main__":
    unittest.main()
