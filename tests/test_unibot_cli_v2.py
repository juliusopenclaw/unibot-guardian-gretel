from __future__ import annotations

import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from unibot.cli import main, public_repository_safety


class UniBotCliV2Tests(unittest.TestCase):
    def test_autonomy_status_is_machine_readable_and_never_grants_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "provider-state.json"
            with (
                patch.dict(os.environ, {"UNIBOT_PROVIDER_STATE_PATH": str(state_path)}),
                io.StringIO() as output,
                redirect_stdout(output),
            ):
                exit_code = main(["autonomy", "status", "--repo", temporary])
                payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema_version"], "unibot-autonomy-v2")
        self.assertFalse(payload["autonomous_merge"])
        self.assertEqual(payload["rollout"]["phase"], "shadow")
        self.assertEqual(payload["provider"]["status"], "parked_awaiting_zai_balance")
        self.assertFalse(payload["provider"]["provider_call_allowed"])

    def test_parked_provider_run_never_reaches_keychain_sdk_or_network_lane(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "provider-state.json"
            with (
                patch.dict(os.environ, {"UNIBOT_PROVIDER_STATE_PATH": str(state_path)}),
                patch("unibot.cli.keychain_key_available") as keychain,
                patch("unibot.cli.ZaiGLMProvider") as provider,
                io.StringIO() as output,
                redirect_stdout(output),
            ):
                exit_code = main(["autonomy", "run", "--repo", temporary])
                payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "parked_awaiting_zai_balance")
        keychain.assert_not_called()
        provider.assert_not_called()

    def test_provider_park_and_explicit_unpark_are_local_secret_free_and_mode_0600(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "state" / "provider-state.json"
            environment = {"UNIBOT_PROVIDER_STATE_PATH": str(state_path)}
            with patch.dict(os.environ, environment), io.StringIO() as output, redirect_stdout(output):
                self.assertEqual(main(["autonomy", "provider", "park"]), 0)
                parked = json.loads(output.getvalue())
            self.assertEqual(parked["status"], "parked_awaiting_zai_balance")
            self.assertEqual(stat.S_IMODE(state_path.stat().st_mode), 0o600)
            self.assertNotIn("key", state_path.read_text(encoding="utf-8").lower())

            with patch.dict(os.environ, environment), io.StringIO() as output, redirect_stdout(output):
                self.assertEqual(
                    main(["autonomy", "provider", "unpark", "--scope", "public-unibot-only"]),
                    0,
                )
                unparked = json.loads(output.getvalue())
            self.assertEqual(unparked["status"], "unparked_public_unibot_only")
            self.assertTrue(unparked["provider_call_allowed"])
            self.assertEqual(stat.S_IMODE(state_path.stat().st_mode), 0o600)

    def test_provider_unpark_rejects_every_broader_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "provider-state.json"
            with (
                patch.dict(os.environ, {"UNIBOT_PROVIDER_STATE_PATH": str(state_path)}),
                io.StringIO() as output,
                redirect_stdout(output),
            ):
                exit_code = main(["autonomy", "provider", "unpark", "--scope", "all-local-files"])
                payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("public-unibot-only", payload["reason"])
        self.assertFalse(state_path.exists())

    def test_tampered_parked_state_cannot_enable_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "provider-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": "unibot-provider-state-v1",
                        "status": "parked_awaiting_zai_balance",
                        "reason": "tampered",
                        "provider_scope": None,
                        "provider_call_allowed": True,
                    }
                ),
                encoding="utf-8",
            )
            state_path.chmod(0o600)
            with (
                patch.dict(os.environ, {"UNIBOT_PROVIDER_STATE_PATH": str(state_path)}),
                patch("unibot.cli.keychain_key_available") as keychain,
                patch("unibot.cli.ZaiGLMProvider") as provider,
                io.StringIO() as output,
                redirect_stdout(output),
            ):
                exit_code = main(["autonomy", "run", "--repo", temporary])
                payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["reason"], "parked_awaiting_zai_balance")
        self.assertFalse(payload["provider"]["provider_call_allowed"])
        keychain.assert_not_called()
        provider.assert_not_called()

    def test_public_repository_safety_uses_relative_source_names(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        result = public_repository_safety(repo)
        self.assertEqual(result["status"], "pass", result["findings"])
        self.assertTrue(all(not str(item["source"]).startswith("/") for item in result["findings"]))


if __name__ == "__main__":
    unittest.main()
