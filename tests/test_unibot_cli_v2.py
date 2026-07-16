from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from unibot.cli import main, public_repository_safety


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


if __name__ == "__main__":
    unittest.main()
