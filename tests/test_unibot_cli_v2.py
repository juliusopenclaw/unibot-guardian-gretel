from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from unibot.cli import main, public_repository_safety
from unibot.release_candidate import write_release_candidate_bundle


class UniBotCliV2Tests(unittest.TestCase):
    def test_guardian_evaluation_command_reports_only_safe_aggregate_metrics(self) -> None:
        with io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["evaluate", "guardian", "--json"])
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema_version"], "GuardianBenchmarkV1")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["case_count"], 60)
        self.assertEqual(payload["metrics"]["solution_block_recall"], 1.0)
        self.assertEqual(payload["metrics"]["source_binding_precision"], 1.0)
        self.assertEqual(payload["metrics"]["allowed_false_block_rate"], 0.0)
        self.assertFalse(payload["notebook_code_executed"])
        self.assertFalse(payload["raw_case_text_in_report"])
        self.assertFalse(payload["provider_context_contains_held_out_cases"])

    def test_3gr_evaluation_command_runs_public_synthetic_self_check(self) -> None:
        with io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["evaluate", "3gr", "--json"])
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["mode"], "public_synthetic_self_check")
        self.assertTrue(all(payload["gates"].values()))
        self.assertFalse(payload["automatic_apply"])
        self.assertTrue(payload["human_review_required"])
        self.assertFalse(payload["canary_merges_evaluated"])

    def test_autonomy_status_is_machine_readable_and_never_grants_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["autonomy", "status", "--repo", temporary])
            payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema_version"], "unibot-autonomy-v2")
        self.assertFalse(payload["autonomous_merge"])
        self.assertEqual(payload["rollout"]["phase"], "shadow")

    def test_provider_run_without_exact_scope_fails_before_keychain_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["autonomy", "run", "--repo", temporary])
            payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("public-unibot-only", payload["reason"])

    def test_v3_provider_and_rollout_commands_start_local_and_parked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, io.StringIO() as output, redirect_stdout(output):
            state = Path(temporary) / "state.sqlite3"
            provider = Path(temporary) / "provider.json"
            exit_code = main(
                [
                    "autonomy",
                    "provider",
                    "status",
                    "--state-db",
                    str(state),
                    "--provider-state",
                    str(provider),
                ]
            )
            payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["state"], "parked_awaiting_zai_balance")
        self.assertFalse(payload["call_allowed"])
        self.assertFalse(payload["network_call_executed"])

        with tempfile.TemporaryDirectory() as temporary, io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["autonomy", "rollout", "status", "--state-db", str(Path(temporary) / "state.sqlite3")])
            payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["rollout"]["lanes"]["shadow"]["successful_runs"], 0)
        self.assertFalse(payload["watcher_active"])

        with tempfile.TemporaryDirectory() as temporary, io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["autonomy", "loop", "start", "--state-db", str(Path(temporary) / "state.sqlite3")])
            payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["reason"], "rollout_gates_incomplete")
        self.assertFalse(payload["loop"]["active"])

    def test_local_rollout_command_uses_disposable_actual_diff_and_no_provider(self) -> None:
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            subprocess.run(
                ["git", "clone", "--no-local", "--no-checkout", str(source), str(repo)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(["git", "-C", str(repo), "checkout", "-qb", "main", "HEAD"], check=True)
            state = Path(temporary) / "state.sqlite3"
            with io.StringIO() as output, redirect_stdout(output):
                exit_code = main(
                    [
                        "autonomy",
                        "rollout",
                        "local",
                        "--repo",
                        str(repo),
                        "--state-db",
                        str(state),
                    ]
                )
                payload = json.loads(output.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "local_green")
            self.assertEqual(payload["runner"], "deterministic_local_codex_rehearsal")
            self.assertEqual(payload["provider_calls"], 0)
            self.assertFalse(payload["automatic_merge"])
            self.assertEqual(payload["evidence"]["changed_files"], ["docs/unibot/UNIBOT_GUARDIAN_BENCHMARK.md"])
            clean = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(clean.stdout, "")

    def test_public_repository_safety_uses_relative_source_names(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        result = public_repository_safety(repo)
        self.assertEqual(result["status"], "pass", result["findings"])
        self.assertTrue(all(not str(item["source"]).startswith("/") for item in result["findings"]))

    def test_institutional_presentation_cli_stays_human_gated(self) -> None:
        with io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["institution", "presentation"])
            payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema_version"], "InstitutionalPresentationV1")
        self.assertEqual(payload["status"], "ready_for_human_review")
        self.assertEqual(payload["deployment_status"], "not_cleared")
        self.assertEqual(payload["evidence"]["readiness"]["status"], "public_draft_ready")

        with io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["institution", "presentation", "--markdown"])
            markdown_payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(markdown_payload["status"], "ready_for_human_review")
        self.assertIn("UniBot Institutional Presentation", markdown_payload["markdown"])
        self.assertIn("not_cleared", markdown_payload["markdown"])

        with io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["institution", "brief", "--markdown"])
            brief_payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(brief_payload["artifact_type"], "unibot_institutional_plain_language_brief")
        self.assertIn("Kurzinfo", brief_payload["markdown"])
        self.assertEqual(brief_payload["deployment_status"], "not_cleared")

        with io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["institution", "accessibility-walkthrough", "--markdown"])
            accessibility_payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            accessibility_payload["artifact_type"], "unibot_institutional_accessibility_walkthrough"
        )
        self.assertIn("Accessibility-Walkthrough", accessibility_payload["markdown"])
        self.assertIn("not_tested", accessibility_payload["markdown"])

        with io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["institution", "decision-template"])
            template_payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(template_payload["schema_version"], "InstitutionalReviewDecisionTemplateV1")
        self.assertEqual(template_payload["status"], "blank_for_human_completion")
        self.assertFalse(template_payload["human_boundary"]["automatic_approval"])

        with io.StringIO() as output, redirect_stdout(output):
            exit_code = main(["institution", "decision-template", "--markdown"])
            template_markdown = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertIn("InstitutionalReviewDecisionTemplateV1", template_markdown["markdown"])
        self.assertIn("keine Freigabe", template_markdown["markdown"])

    def test_release_audit_cli_is_read_only_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate"
            result = write_release_candidate_bundle(candidate)
            self.assertEqual(result["status"], "written")
            with io.StringIO() as output, redirect_stdout(output):
                exit_code = main(["release", "audit", str(candidate), "--repo", str(Path(__file__).resolve().parents[1])])
                payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema_version"], "UniBotReleaseAuditV1")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["source_commit_match"])
        self.assertFalse(payload["side_effects"]["files_written"])
        self.assertFalse(payload["side_effects"]["network_called"])


if __name__ == "__main__":
    unittest.main()
