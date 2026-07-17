from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from unibot.autonomy_v3 import (
    AutonomyController,
    AutonomyLease,
    AutonomyRunV3,
    AutonomyStore,
    CodexReviewV1,
    EvolutionChunkContractV1,
    GLMReviewV2,
    ProviderGate,
    TestRegistry,
    WorkItemV3,
    default_test_registry,
    derive_implementation_evidence,
    evaluate_three_golden_rules,
    prepare_autonomy_loop,
    request_autonomy_loop_start,
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
    def evolution(self, failure_class: str = "test.autonomy") -> EvolutionChunkContractV1:
        return EvolutionChunkContractV1(
            failure_class=failure_class,
            generalized_rule="Every bounded change needs reusable transfer and regression evidence.",
            transfer_targets=("guardian.policy", "tutor.output"),
            positive_fixture_ids=("test.allowed",),
            negative_fixture_ids=("test.blocked",),
            recurrence_monitor_id="test.autonomy.recurrence",
        )

    def make_git_repo(self) -> tuple[tempfile.TemporaryDirectory, Path, str]:
        holder = tempfile.TemporaryDirectory()
        root = Path(holder.name)
        (root / "public.py").write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "init", "-q", "--initial-branch=main"], check=True)
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
            evolution_chunk=self.evolution(),
        )
        self.assertEqual(item.validate(), [])
        self.assertEqual(item.to_dict()["work_item_hash"], item.work_item_hash)
        bad = WorkItemV3(**{**item.__dict__, "allowed_files": ("private-notebook.ipynb",)})
        self.assertIn("private_path_not_allowed", bad.validate())

    def test_work_item_requires_bounded_files_and_registered_tests(self) -> None:
        item = WorkItemV3(
            work_id="bounded-contract",
            source="measured_gap",
            hypothesis="A bounded contract is measurable.",
            product_delta="Keep the work item executable and reviewable.",
            risk="low",
            allowed_files=("public.py",),
            test_ids=("test.guardian",),
            base_commit="abcdef1",
            evolution_chunk=self.evolution("test.bounded_contract"),
        )
        self.assertIn("allowed_files_required", replace(item, allowed_files=()).validate())
        self.assertIn("test_ids_required", replace(item, test_ids=()).validate())
        self.assertIn("allowed_files_must_be_unique", replace(item, allowed_files=("public.py", "public.py")).validate())
        self.assertIn("test_ids_must_be_unique", replace(item, test_ids=("test.guardian", "test.guardian")).validate())

    def test_unexpected_implementation_failure_is_blocked_without_exception_text(self) -> None:
        holder, root, base = self.make_git_repo()
        try:
            item = WorkItemV3(
                work_id="runtime-failure",
                source="measured_gap",
                hypothesis="An implementation crash must become a bounded run result.",
                product_delta="Keep private exception text out of run metadata.",
                risk="medium",
                allowed_files=("public.py",),
                test_ids=("test.guardian",),
                base_commit=base,
                evolution_chunk=self.evolution("test.runtime_failure"),
            )
            with tempfile.TemporaryDirectory() as state_dir:
                store = AutonomyStore(Path(state_dir) / "state.sqlite3")
                gate = ProviderGate(Path(state_dir) / "provider.json", store=store)
                gate.unpark("public-unibot-only")
                controller = AutonomyController(
                    repo_root=root,
                    store=store,
                    provider_gate=gate,
                    lease=AutonomyLease(Path(state_dir) / "run.lock"),
                )
                tests = TestRegistry()
                tests.register("test.guardian", lambda: True)

                def broken_implementer(*_: object) -> None:
                    raise RuntimeError("/private/learner/notebook.ipynb")

                result = controller.execute(
                    item,
                    glm=MockGLM(),
                    implementer=broken_implementer,
                    reviewer=lambda evidence, work_item: CodexReviewV1(
                        run_id=evidence.run_id,
                        diff_hash=evidence.diff_hash,
                        decision="approve",
                    ),
                    tests=tests,
                    ci_green=True,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason"], "unexpected_runtime_failure")
                self.assertEqual(result["run"]["state"], "blocked")
                self.assertNotIn("/private/learner", str(result))
                store.close()
        finally:
            holder.cleanup()

    def test_gitlink_changes_are_rejected_from_implementation_evidence(self) -> None:
        holder, root, base = self.make_git_repo()
        try:
            subprocess.run(
                ["git", "-C", str(root), "update-index", "--add", "--cacheinfo", "160000", "a" * 40, "vendor/module"],
                check=True,
            )
            with self.assertRaisesRegex(ValueError, "submodule_change_not_allowed"):
                derive_implementation_evidence(
                    worktree=root,
                    run_id="gitlink-evidence",
                    base_commit=base,
                    allowed_files=("vendor/module",),
                    test_ids_passed=["test.guardian"],
                    test_evidence_hash="a" * 64,
                )
        finally:
            holder.cleanup()

    def test_human_merge_evidence_rejects_bot_identity_and_short_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AutonomyStore(Path(tmp) / "state.sqlite3")
            run = AutonomyRunV3(
                run_id="human-gate",
                work_item_hash="a" * 64,
                trigger="canary",
                state="ready_for_human_merge",
            )
            store.save_run(run)
            controller = AutonomyController(repo_root=Path(tmp), store=store)
            self.assertEqual(
                controller.record_human_merge("human-gate", reviewer="Codex", merge_commit="a" * 40)["reason"],
                "non_human_reviewer_not_allowed",
            )
            self.assertEqual(
                controller.record_human_merge("human-gate", reviewer="Julius", merge_commit="abcdef1")["reason"],
                "full_merge_commit_required",
            )
            self.assertEqual(
                controller.record_human_merge("human-gate", reviewer="Julius", merge_commit="a" * 40)["status"],
                "human_merged",
            )
            store.close()

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

    def test_provider_state_and_store_reject_unsafe_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = AutonomyStore(root / "state.sqlite3")
            gate = ProviderGate(root / "provider.json", store=store)
            gate.unpark("public-unibot-only")
            os.chmod(root / "provider.json", 0o644)
            status = gate.status()
            self.assertFalse(status["call_allowed"])
            self.assertEqual(status["state"], "parked_awaiting_zai_balance")
            self.assertEqual(status["reason"], "state_file_permissions_must_be_0600")
            store.close()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.sqlite3"
            target.write_bytes(b"")
            os.chmod(target, 0o600)
            (root / "state.sqlite3").symlink_to(target)
            with self.assertRaises(ValueError):
                AutonomyStore(root / "state.sqlite3")

    def test_private_loop_state_is_atomic_and_permission_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = AutonomyStore(root / "state.sqlite3")
            result = prepare_autonomy_loop(store, support_dir=root / "support")
            state_path = root / "support" / "loop-state.json"
            self.assertTrue(result["prepared"])
            self.assertEqual(os.stat(state_path).st_mode & 0o777, 0o600)
            self.assertEqual(os.stat(state_path.parent).st_mode & 0o777, 0o700)
            store.close()

    def test_three_golden_rules_are_distinct_from_three_canary_merges(self) -> None:
        legacy = WorkItemV3(
            work_id="legacy",
            source="measured_gap",
            hypothesis="safe",
            product_delta="safe",
            risk="low",
            allowed_files=("public.py",),
            test_ids=("test.guardian",),
            base_commit="abcdef1",
        )
        evaluation = evaluate_three_golden_rules(legacy)
        self.assertEqual(evaluation["status"], "blocked")
        self.assertIn("legacy_missing_3gr_contract", evaluation["errors"])

        with tempfile.TemporaryDirectory() as tmp:
            store = AutonomyStore(Path(tmp) / "state.sqlite3")
            rollout = store.rollout_status()
            self.assertEqual(rollout["three_golden_rules"], "separate_per_work_item_gate")
            self.assertFalse(rollout["watcher_activation_allowed"])
            self.assertEqual(request_autonomy_loop_start(store)["reason"], "rollout_gates_incomplete")
            for index in range(10):
                store.record_rollout("shadow", run_id=f"shadow-{index}", success=True)
                store.record_rollout("local", run_id=f"local-{index}", success=True)
            self.assertEqual(
                request_autonomy_loop_start(store)["reason"],
                "three_human_canary_merges_required",
            )
            for index in range(3):
                run = AutonomyRunV3(
                    run_id=f"canary-{index}",
                    work_item_hash="a" * 64,
                    trigger="canary",
                    state="human_merged",
                )
                store.save_run(run)
                rollout = store.record_canary_merge(
                    run_id=run.run_id,
                    reviewer="Julius",
                    merge_commit=f"{index + 1:040x}",
                    checks_green=True,
                    approved_after_last_push=True,
                )
            self.assertTrue(rollout["watcher_activation_allowed"])
            self.assertEqual(store.record_canary_merge(
                run_id="canary-2",
                reviewer="Julius",
                merge_commit=f"{3:040x}",
                checks_green=True,
                approved_after_last_push=True,
            )["lanes"]["canary_merges"]["successful_runs"], 3)
            store.close()

    def test_budget_warns_at_fifteen_and_stops_above_twenty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AutonomyStore(Path(tmp) / "state.sqlite3")
            self.assertEqual(store.record_cost(15, month="2099-01")["status"], "warning")
            self.assertEqual(store.record_cost(5, month="2099-01")["status"], "warning")
            self.assertEqual(store.record_cost(0.01, month="2099-01")["reason"], "monthly_hard_stop")
            store.close()

    def test_rollout_gate_requires_ten_consecutive_green_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AutonomyStore(Path(tmp) / "state.sqlite3")
            for index in range(9):
                status = store.record_rollout("shadow", run_id=f"shadow-green-{index}", success=True)
            self.assertFalse(status["lanes"]["shadow"]["complete"])
            self.assertEqual(status["lanes"]["shadow"]["consecutive_successes"], 9)

            status = store.record_rollout("shadow", run_id="shadow-red", success=False)
            self.assertFalse(status["lanes"]["shadow"]["complete"])
            self.assertEqual(status["lanes"]["shadow"]["successful_runs"], 9)
            self.assertEqual(status["lanes"]["shadow"]["failed_runs"], 1)
            self.assertEqual(status["lanes"]["shadow"]["consecutive_successes"], 0)

            for index in range(10):
                status = store.record_rollout("shadow", run_id=f"shadow-recovered-{index}", success=True)
            self.assertTrue(status["lanes"]["shadow"]["complete"])
            self.assertEqual(status["lanes"]["shadow"]["consecutive_successes"], 10)
            self.assertEqual(status["lanes"]["shadow"]["successful_runs"], 19)
            self.assertEqual(status["lanes"]["shadow"]["failed_runs"], 1)
            self.assertTrue(status["canary_allowed"] is False)
            store.close()

    def test_rollout_recording_is_idempotent_for_replayed_run_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AutonomyStore(Path(tmp) / "state.sqlite3")
            first = store.record_rollout("local", run_id="replayed-run", success=True)
            second = store.record_rollout("local", run_id="replayed-run", success=True)
            self.assertEqual(first["lanes"]["local"]["successful_runs"], 1)
            self.assertEqual(second["lanes"]["local"]["successful_runs"], 1)
            self.assertEqual(second["lanes"]["local"]["consecutive_successes"], 1)
            self.assertEqual(second["lanes"]["local"]["failed_runs"], 0)
            store.close()

    def test_old_rollout_schema_migrates_with_a_closed_success_streak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.sqlite3"
            import sqlite3

            connection = sqlite3.connect(path)
            connection.execute(
                "CREATE TABLE rollout (lane TEXT PRIMARY KEY, successful_runs INTEGER NOT NULL, "
                "failed_runs INTEGER NOT NULL, last_run_id TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT INTO rollout VALUES('shadow', 10, 0, 'old-run', '2026-01-01T00:00:00+00:00')"
            )
            connection.commit()
            connection.close()
            path.chmod(0o600)

            store = AutonomyStore(path)
            shadow = store.rollout_status()["lanes"]["shadow"]
            self.assertFalse(shadow["complete"])
            self.assertEqual(shadow["consecutive_successes"], 0)
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
                evolution_chunk=self.evolution("test.actual_diff"),
            )
            with tempfile.TemporaryDirectory() as state_dir:
                store = AutonomyStore(Path(state_dir) / "state.sqlite3")
                gate = ProviderGate(Path(state_dir) / "provider.json", store=store)
                gate.unpark("public-unibot-only")
                controller = AutonomyController(
                    repo_root=root,
                    store=store,
                    provider_gate=gate,
                    lease=AutonomyLease(Path(state_dir) / "run.lock"),
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
                evolution_chunk=self.evolution("test.provider_park"),
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
                evolution_chunk=self.evolution("test.main_protection"),
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
            evolution_chunk=self.evolution("test.proposal_binding"),
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
                evolution_chunk=self.evolution("test.local_rollout"),
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
                self.assertEqual(result["three_golden_rules_evidence"]["generalization_gate"], "pass")
                self.assertFalse(result["three_golden_rules_evidence"]["automatic_apply"])
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
