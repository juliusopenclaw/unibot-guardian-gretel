from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import nbformat

import unibot.rehearsal as rehearsal_module
from unibot.cli import build_parser, main as cli_main
from unibot.learning_session import LearningSession
from unibot.notebook_intake import import_notebook
from unibot.rehearsal import (
    MACOS_SANDBOX_PROFILE,
    REHEARSAL_ALLOWED_HELP_LEVELS,
    SYNTHETIC_REHEARSAL_FIXTURE_SHA256,
    SYNTHETIC_REHEARSAL_SANITIZED_SHA256,
    RehearsalError,
    delete_rehearsal,
    finish_rehearsal,
    load_rehearsal_contract,
    network_isolation_preflight,
    prepare_rehearsal,
    rehearsal_status,
    run_network_monitor,
    start_rehearsal,
    verify_rehearsal_export,
)


REPOSITORY = Path(__file__).resolve().parents[1]
FIXTURE = REPOSITORY / "fixtures" / "public" / "synthetic_python_practice.ipynb"


def prepare_fixture(root: Path) -> tuple[dict[str, object], Path, Path, Path]:
    sessions = root / "sessions"
    rehearsals = root / "rehearsals"
    intake = root / "intake"
    manifest = import_notebook(str(FIXTURE), intake)
    manifest_path = intake / manifest["sanitized_sha256"][:16] / "manifest.json"
    session = LearningSession.start(
        {"session_scope": "synthetic_exam_rehearsal"},
        storage_root=sessions,
    )
    contract = prepare_rehearsal(manifest_path, dict(session.contract), state_root=rehearsals)
    return dict(contract), rehearsals, sessions, manifest_path


def make_state_active(root: Path, rehearsal_id: str) -> None:
    with rehearsal_module._state_lock(root, rehearsal_id):
        state = rehearsal_module._state(root, rehearsal_id)
        state.update(
            {
                "status": "active",
                "process_id": 0,
                "process_group_id": 0,
                "monitor_process_id": 0,
                "port": 8888,
                "network_isolation_evidence_hash": "a" * 64,
            }
        )
        rehearsal_module._write_state(root, rehearsal_id, state)


def make_state_frozen(root: Path, rehearsal_id: str) -> None:
    evidence_without_hash = {
        "schema_version": "unibot-network-isolation-evidence-v1",
        "status": "ready",
        "provider_id": "macos-sandbox-exec-loopback-host-offline-v1",
        "platform": "macos",
        "sandbox_exec_available": True,
        "external_default_route_present": False,
        "host_offline": True,
        "loopback_only_gateway": True,
        "sandbox_profile_sha256": rehearsal_module.hashlib.sha256(MACOS_SANDBOX_PROFILE.encode("utf-8")).hexdigest(),
        "checked_at_utc": "2026-01-01T00:00:00+00:00",
    }
    evidence = {
        **evidence_without_hash,
        "evidence_hash": rehearsal_module._canonical_hash(evidence_without_hash),
    }
    directory = root / rehearsal_id
    rehearsal_module._write_private_json(directory / "network-evidence.json", evidence)
    with rehearsal_module._state_lock(root, rehearsal_id):
        state = rehearsal_module._state(root, rehearsal_id)
        state.update(
            {
                "status": "frozen",
                "process_id": 0,
                "process_group_id": 0,
                "monitor_process_id": 0,
                "port": 0,
                "network_isolation_evidence_hash": evidence["evidence_hash"],
            }
        )
        rehearsal_module._write_state(root, rehearsal_id, state)


class UniBotControlledExamRehearsalTests(unittest.TestCase):
    def test_contract_accepts_only_fixed_public_fixture_and_is_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            loaded = load_rehearsal_contract(str(contract["rehearsal_id"]), state_root=rehearsals)

        self.assertEqual(loaded["source_sha256"], SYNTHETIC_REHEARSAL_FIXTURE_SHA256)
        self.assertEqual(loaded["sanitized_sha256"], SYNTHETIC_REHEARSAL_SANITIZED_SHA256)
        self.assertEqual(loaded["allowed_help_levels"], list(REHEARSAL_ALLOWED_HELP_LEVELS))
        self.assertEqual(loaded["provider_use"], "forbidden")
        self.assertEqual(loaded["exam_deployment_status"], "not_cleared")
        self.assertEqual(loaded["private_content_allowed"], False)

    def test_contract_rejects_any_other_notebook(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "other.ipynb"
            source.write_text(
                nbformat.writes(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("value = 1")])),
                encoding="utf-8",
            )
            manifest = import_notebook(str(source), root / "intake")
            manifest_path = root / "intake" / manifest["sanitized_sha256"][:16] / "manifest.json"
            session = LearningSession.start(
                {"session_scope": "synthetic_exam_rehearsal"},
                storage_root=root / "sessions",
            )
            with self.assertRaisesRegex(RehearsalError, "fixed public synthetic notebook"):
                prepare_rehearsal(manifest_path, dict(session.contract), state_root=root / "rehearsals")

    def test_contract_rejects_manifest_with_forged_fixture_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "other.ipynb"
            source.write_text(
                nbformat.writes(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("value = 99")])),
                encoding="utf-8",
            )
            manifest = import_notebook(str(source), root / "intake")
            manifest_path = root / "intake" / manifest["sanitized_sha256"][:16] / "manifest.json"
            forged_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            forged_manifest["source_sha256"] = SYNTHETIC_REHEARSAL_FIXTURE_SHA256
            manifest_path.write_text(json.dumps(forged_manifest), encoding="utf-8")
            session = LearningSession.start(
                {"session_scope": "synthetic_exam_rehearsal"},
                storage_root=root / "sessions",
            )

            with self.assertRaisesRegex(RehearsalError, "fixed public synthetic notebook"):
                prepare_rehearsal(manifest_path, dict(session.contract), state_root=root / "rehearsals")

    def test_prepare_removes_partial_directory_when_persistence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            intake = root / "intake"
            rehearsals = root / "rehearsals"
            manifest = import_notebook(str(FIXTURE), intake)
            manifest_path = intake / manifest["sanitized_sha256"][:16] / "manifest.json"
            session = LearningSession.start(
                {"session_scope": "synthetic_exam_rehearsal"},
                storage_root=root / "sessions",
            )
            original_write = rehearsal_module._write_private_json

            def fail_contract_write(path: Path, payload: dict[str, object]) -> None:
                if path.name == "contract.json":
                    raise OSError("synthetic persistence failure")
                original_write(path, payload)

            with patch("unibot.rehearsal._write_private_json", side_effect=fail_contract_write):
                with self.assertRaisesRegex(OSError, "synthetic persistence failure"):
                    prepare_rehearsal(manifest_path, dict(session.contract), state_root=rehearsals)

            self.assertEqual(list(rehearsals.iterdir()), [])

    def test_tampered_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            contract_path = rehearsals / str(contract["rehearsal_id"]) / "contract.json"
            payload = json.loads(contract_path.read_text(encoding="utf-8"))
            payload["allowed_help_levels"] = ["A0", "A1", "A2", "A3"]
            contract_path.write_text(json.dumps(payload), encoding="utf-8")
            contract_path.chmod(0o600)
            with self.assertRaisesRegex(RehearsalError, "hash mismatch"):
                load_rehearsal_contract(str(contract["rehearsal_id"]), state_root=rehearsals)

    def test_synthetic_learning_contract_is_separate_and_capped_at_a2(self) -> None:
        session = LearningSession.start(
            {
                "session_scope": "synthetic_exam_rehearsal",
                "assistance_mode": "fixed",
                "fixed_help_level": "A4",
                "max_help_level": "A4",
                "pseudonym": "ignored",
            }
        )
        self.assertEqual(session.contract["practice_scope"], "synthetic_exam_rehearsal")
        self.assertEqual(session.contract["assistance_mode"], "adaptive")
        self.assertEqual(session.contract["max_help_level"], "A2")
        self.assertEqual(session.contract["fixed_help_level"], "A0")
        self.assertEqual(session.contract["pseudonym"], "Synthetic Learner")

    def test_network_preflight_fails_closed_on_route_or_missing_sandbox(self) -> None:
        with (
            patch.object(rehearsal_module.sys, "platform", "darwin"),
            patch("unibot.rehearsal.shutil.which", return_value="/usr/bin/sandbox-exec"),
            patch("unibot.rehearsal.host_has_external_default_route", return_value=True),
        ):
            online = network_isolation_preflight()
        self.assertEqual(online["status"], "blocked")
        self.assertFalse(online["host_offline"])

        with (
            patch.object(rehearsal_module.sys, "platform", "linux"),
            patch("unibot.rehearsal.host_has_external_default_route", return_value=False),
        ):
            unsupported = network_isolation_preflight()
        self.assertEqual(unsupported["status"], "blocked")
        self.assertFalse(unsupported["sandbox_exec_available"])

    @unittest.skipUnless(sys.platform == "darwin", "macOS sandbox evidence")
    def test_macos_sandbox_profile_denies_external_socket(self) -> None:
        command = [
            "/usr/bin/sandbox-exec",
            "-p",
            MACOS_SANDBOX_PROFILE,
            sys.executable,
            "-c",
            "import socket; socket.create_connection(('1.1.1.1', 443), timeout=1)",
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Operation not permitted", result.stderr)

        https = subprocess.run(
            [
                "/usr/bin/sandbox-exec",
                "-p",
                MACOS_SANDBOX_PROFILE,
                sys.executable,
                "-c",
                "import urllib.request; urllib.request.urlopen('https://example.com', timeout=1)",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertNotEqual(https.returncode, 0)

        dns = subprocess.run(
            [
                "/usr/bin/sandbox-exec",
                "-p",
                MACOS_SANDBOX_PROFILE,
                sys.executable,
                "-c",
                "import socket; socket.getaddrinfo('example.com', 443)",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertNotEqual(dns.returncode, 0)

    @unittest.skipUnless(sys.platform == "darwin", "macOS sandbox evidence")
    def test_macos_sandbox_profile_keeps_loopback_available(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = int(server.getsockname()[1])
            received: list[bytes] = []

            def accept_once() -> None:
                connection, _ = server.accept()
                with connection:
                    received.append(connection.recv(16))

            worker = threading.Thread(target=accept_once, daemon=True)
            worker.start()
            result = subprocess.run(
                [
                    "/usr/bin/sandbox-exec",
                    "-p",
                    MACOS_SANDBOX_PROFILE,
                    sys.executable,
                    "-c",
                    f"import socket; s=socket.create_connection(('127.0.0.1', {port}), timeout=2); s.sendall(b'loopback')",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            worker.join(timeout=2)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(received, [b"loopback"])

    def test_start_uses_sandbox_and_returns_no_session_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            gateway = Mock(pid=43210)
            gateway.poll.return_value = None
            monitor = Mock(pid=43211)
            ready = {
                "schema_version": "unibot-network-isolation-evidence-v1",
                "status": "ready",
                "provider_id": "macos-sandbox-exec-loopback-host-offline-v1",
                "platform": "macos",
                "sandbox_exec_available": True,
                "external_default_route_present": False,
                "host_offline": True,
                "loopback_only_gateway": True,
                "sandbox_profile_sha256": "b" * 64,
                "checked_at_utc": "2026-01-01T00:00:00+00:00",
                "evidence_hash": "c" * 64,
            }
            with (
                patch("unibot.rehearsal.network_isolation_preflight", return_value=ready),
                patch("unibot.rehearsal._jupyter_lab_command", return_value=["/usr/local/bin/jupyter", "lab"]),
                patch("unibot.rehearsal.subprocess.Popen", return_value=gateway) as popen,
                patch("unibot.rehearsal.os.getpgid", return_value=43210),
                patch("unibot.rehearsal._loopback_port_available", return_value=True),
                patch("unibot.rehearsal._wait_for_loopback_port", return_value=True),
                patch("unibot.rehearsal._spawn_network_monitor", return_value=monitor),
                patch("unibot.rehearsal.webbrowser.open", return_value=True),
            ):
                result = start_rehearsal(str(contract["rehearsal_id"]), state_root=rehearsals, port=8899)

        command = popen.call_args.args[0]
        self.assertEqual(command[:3], ["/usr/bin/sandbox-exec", "-p", MACOS_SANDBOX_PROFILE])
        self.assertIn("--ServerApp.terminals_enabled=False", command)
        self.assertIn("--ServerApp.root_dir=.", command)
        launch_environment = popen.call_args.kwargs["env"]
        self.assertNotIn("ZAI_API_KEY", launch_environment)
        self.assertNotIn("OPENAI_API_KEY", launch_environment)
        self.assertEqual(set(launch_environment), {
            "HOME",
            "IPYTHONDIR",
            "JUPYTER_CONFIG_DIR",
            "JUPYTER_DATA_DIR",
            "JUPYTER_RUNTIME_DIR",
            "JUPYTER_TOKEN",
            "LANG",
            "MPLCONFIGDIR",
            "PATH",
            "PYTHONNOUSERSITE",
            "TMPDIR",
            "XDG_CACHE_HOME",
            "XDG_CONFIG_HOME",
        })
        self.assertEqual(popen.call_args.kwargs["cwd"].name, "workspace")
        self.assertEqual(result["network_isolation"], "enforced_loopback_and_host_offline_monitored")
        self.assertFalse(result["session_value_returned"])
        self.assertNotIn("token", json.dumps(result).lower())

    def test_start_stops_jupyter_when_activation_state_cannot_be_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            gateway = Mock(pid=43210)
            gateway.poll.return_value = None
            ready = {
                "schema_version": "unibot-network-isolation-evidence-v1",
                "status": "ready",
                "provider_id": "macos-sandbox-exec-loopback-host-offline-v1",
                "platform": "macos",
                "sandbox_exec_available": True,
                "external_default_route_present": False,
                "host_offline": True,
                "loopback_only_gateway": True,
                "sandbox_profile_sha256": "b" * 64,
                "checked_at_utc": "2026-01-01T00:00:00+00:00",
                "evidence_hash": "c" * 64,
            }
            original_write = rehearsal_module._write_private_json

            def fail_evidence_write(path: Path, payload: dict[str, object]) -> None:
                if path.name == "network-evidence.json":
                    raise OSError("synthetic evidence failure")
                original_write(path, payload)

            with (
                patch("unibot.rehearsal.network_isolation_preflight", return_value=ready),
                patch("unibot.rehearsal._jupyter_lab_command", return_value=["/usr/local/bin/jupyter", "lab"]),
                patch("unibot.rehearsal.subprocess.Popen", return_value=gateway),
                patch("unibot.rehearsal.os.getpgid", return_value=43210),
                patch("unibot.rehearsal._loopback_port_available", return_value=True),
                patch("unibot.rehearsal._wait_for_loopback_port", return_value=True),
                patch("unibot.rehearsal._write_private_json", side_effect=fail_evidence_write),
                patch("unibot.rehearsal._stop_process_group") as stop_process,
                patch("unibot.rehearsal._spawn_network_monitor") as spawn_monitor,
            ):
                with self.assertRaisesRegex(RehearsalError, "could not be persisted safely"):
                    start_rehearsal(str(contract["rehearsal_id"]), state_root=rehearsals, port=8899)

            stop_process.assert_called_once_with(43210, 43210)
            spawn_monitor.assert_not_called()
            status = rehearsal_status(str(contract["rehearsal_id"]), state_root=rehearsals)
            self.assertEqual(status["status"], "aborted")
            self.assertEqual(status["failure_reason"], "activation_state_persistence_failed")

    def test_start_rejects_an_occupied_loopback_port_before_spawning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            ready = {
                "schema_version": "unibot-network-isolation-evidence-v1",
                "status": "ready",
                "provider_id": "macos-sandbox-exec-loopback-host-offline-v1",
                "platform": "macos",
                "sandbox_exec_available": True,
                "external_default_route_present": False,
                "host_offline": True,
                "loopback_only_gateway": True,
                "sandbox_profile_sha256": "b" * 64,
                "checked_at_utc": "2026-01-01T00:00:00+00:00",
                "evidence_hash": "c" * 64,
            }
            with (
                patch("unibot.rehearsal.network_isolation_preflight", return_value=ready),
                patch("unibot.rehearsal._loopback_port_available", return_value=False),
                patch("unibot.rehearsal.subprocess.Popen") as popen,
            ):
                with self.assertRaisesRegex(RehearsalError, "already in use"):
                    start_rehearsal(str(contract["rehearsal_id"]), state_root=rehearsals, port=8899)
        popen.assert_not_called()

    def test_network_monitor_aborts_and_stops_gateway_when_route_returns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            make_state_active(rehearsals, rehearsal_id)
            with (
                patch("unibot.rehearsal._process_alive", return_value=True),
                patch("unibot.rehearsal.host_has_external_default_route", return_value=True),
                patch("unibot.rehearsal._stop_process_group", return_value=True) as stop,
            ):
                status = run_network_monitor(rehearsal_id, state_root=rehearsals, interval_seconds=0.1)
            state = rehearsal_module._state(rehearsals, rehearsal_id)

        self.assertEqual(status, "aborted")
        self.assertEqual(state["failure_reason"], "external_network_reappeared")
        stop.assert_called_once()

    def test_finish_exports_valid_notebook_and_hash_only_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            make_state_frozen(rehearsals, rehearsal_id)
            working = rehearsals / rehearsal_id / "workspace" / "unibot-synthetic-rehearsal.ipynb"
            notebook = nbformat.read(working, as_version=4)
            notebook.cells[1]["source"] = "values = [2, 4, 6]\nmean = sum(values) / len(values)\nmean"
            notebook.cells[1]["outputs"] = [nbformat.v4.new_output("execute_result", data={"text/plain": "4.0"})]
            working.write_text(nbformat.writes(notebook), encoding="utf-8")
            working.chmod(0o600)
            destination = root / "completed.ipynb"
            receipt = finish_rehearsal(
                rehearsal_id,
                help_report_hash="d" * 64,
                destination=destination,
                state_root=rehearsals,
            )
            receipt_path = root / "completed.unibot-receipt.json"
            verification = verify_rehearsal_export(destination, receipt_path)
            receipt_path.chmod(0o644)
            shared_verification = verify_rehearsal_export(destination, receipt_path)
            receipt_text = receipt_path.read_text(encoding="utf-8")

        self.assertEqual(receipt["status"], "ready_for_institutional_rehearsal_review")
        self.assertEqual(receipt["output_count"], 1)
        self.assertEqual(receipt["provider_calls"], 0)
        self.assertFalse(receipt["learner_content_in_receipt"])
        self.assertFalse(receipt["automatic_submission"])
        self.assertEqual(receipt["exam_deployment_status"], "not_cleared")
        self.assertEqual(verification["status"], "verified")
        self.assertEqual(shared_verification["status"], "verified")
        self.assertNotIn("values =", receipt_text)
        self.assertNotIn(str(root), receipt_text)

    def test_verify_rejects_modified_notebook(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            make_state_frozen(rehearsals, rehearsal_id)
            destination = root / "completed.ipynb"
            finish_rehearsal(
                rehearsal_id,
                help_report_hash="e" * 64,
                destination=destination,
                state_root=rehearsals,
            )
            destination.write_text(destination.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RehearsalError, "file hash mismatch"):
                verify_rehearsal_export(destination, root / "completed.unibot-receipt.json")

    def test_verify_rejects_a_rehashed_receipt_that_crosses_the_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            make_state_frozen(rehearsals, rehearsal_id)
            destination = root / "completed.ipynb"
            finish_rehearsal(
                rehearsal_id,
                help_report_hash="e" * 64,
                destination=destination,
                state_root=rehearsals,
            )
            receipt_path = root / "completed.unibot-receipt.json"
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            payload["provider_calls"] = 1
            unsigned = dict(payload)
            unsigned.pop("receipt_hash")
            payload["receipt_hash"] = rehearsal_module._canonical_hash(unsigned)
            receipt_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RehearsalError, "boundary mismatch"):
                verify_rehearsal_export(destination, receipt_path)

    def test_finish_never_overwrites_an_existing_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            make_state_frozen(rehearsals, rehearsal_id)
            destination = root / "completed.ipynb"
            destination.write_text("keep-existing", encoding="utf-8")
            with self.assertRaisesRegex(RehearsalError, "already exists"):
                finish_rehearsal(
                    rehearsal_id,
                    help_report_hash="f" * 64,
                    destination=destination,
                    state_root=rehearsals,
                )
            self.assertEqual(destination.read_text(encoding="utf-8"), "keep-existing")
            self.assertFalse((root / "completed.unibot-receipt.json").exists())

    def test_finish_aborts_if_the_gateway_disappeared(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            make_state_active(rehearsals, rehearsal_id)
            with self.assertRaisesRegex(RehearsalError, "disappeared"):
                finish_rehearsal(
                    rehearsal_id,
                    help_report_hash="f" * 64,
                    destination=root / "completed.ipynb",
                    state_root=rehearsals,
                )
            status = rehearsal_status(rehearsal_id, state_root=rehearsals)
            self.assertEqual(status["status"], "aborted")
            self.assertEqual(status["failure_reason"], "gateway_process_missing")
            self.assertFalse((root / "completed.ipynb").exists())

    def test_tampered_network_evidence_aborts_before_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            make_state_frozen(rehearsals, rehearsal_id)
            evidence_path = rehearsals / rehearsal_id / "network-evidence.json"
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["host_offline"] = False
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            evidence_path.chmod(0o600)
            with self.assertRaisesRegex(RehearsalError, "network isolation evidence"):
                finish_rehearsal(
                    rehearsal_id,
                    help_report_hash="f" * 64,
                    destination=root / "completed.ipynb",
                    state_root=rehearsals,
                )
            status = rehearsal_status(rehearsal_id, state_root=rehearsals)
            self.assertEqual(status["status"], "aborted")
            self.assertEqual(status["failure_reason"], "network_isolation_evidence_invalid")
            self.assertFalse((root / "completed.ipynb").exists())

    def test_invalid_final_notebook_aborts_instead_of_exporting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            make_state_frozen(rehearsals, rehearsal_id)
            working = rehearsals / rehearsal_id / "workspace" / "unibot-synthetic-rehearsal.ipynb"
            working.write_text("not a notebook", encoding="utf-8")
            with self.assertRaisesRegex(RehearsalError, "not valid"):
                finish_rehearsal(
                    rehearsal_id,
                    help_report_hash="f" * 64,
                    destination=root / "completed.ipynb",
                    state_root=rehearsals,
                )
            status = rehearsal_status(rehearsal_id, state_root=rehearsals)
            self.assertEqual(status["status"], "aborted")
            self.assertEqual(status["failure_reason"], "final_notebook_invalid")
            self.assertFalse((root / "completed.ipynb").exists())

    def test_latest_open_rehearsal_is_not_hidden_by_a_newer_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, rehearsals, _, _ = prepare_fixture(root)
            first_id = str(first["rehearsal_id"])
            make_state_frozen(rehearsals, first_id)
            second, _, _, _ = prepare_fixture(root)
            second_id = str(second["rehearsal_id"])
            make_state_frozen(rehearsals, second_id)
            finish_rehearsal(
                second_id,
                help_report_hash="f" * 64,
                destination=root / "completed.ipynb",
                state_root=rehearsals,
            )
            selected = rehearsal_status(state_root=rehearsals)
            self.assertEqual(selected["rehearsal_id"], first_id)
            self.assertEqual(selected["status"], "frozen")

    def test_delete_removes_local_rehearsal_but_not_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            rehearsal_id = str(contract["rehearsal_id"])
            self.assertTrue(delete_rehearsal(rehearsal_id, state_root=rehearsals))
            self.assertFalse((rehearsals / rehearsal_id).exists())

    def test_status_returns_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract, rehearsals, _, _ = prepare_fixture(root)
            status = rehearsal_status(str(contract["rehearsal_id"]), state_root=rehearsals)
            encoded = json.dumps(status)

        self.assertEqual(status["status"], "prepared")
        self.assertFalse(status["local_paths_included"])
        self.assertNotIn(str(root), encoded)

    def test_cli_exposes_complete_rehearsal_surface(self) -> None:
        parser = build_parser()
        self.assertEqual(parser.parse_args(["rehearsal", "start", "manifest.json"]).rehearsal_command, "start")
        self.assertEqual(parser.parse_args(["rehearsal", "status"]).rehearsal_command, "status")
        self.assertEqual(
            parser.parse_args(["rehearsal", "finish", "a" * 32, "--output", "final.ipynb"]).rehearsal_command,
            "finish",
        )
        self.assertEqual(
            parser.parse_args(["rehearsal", "verify", "final.ipynb", "receipt.json"]).rehearsal_command,
            "verify",
        )
        self.assertEqual(parser.parse_args(["rehearsal", "delete", "a" * 32]).rehearsal_command, "delete")

    def test_cli_start_blocks_before_preflight_when_learning_session_is_active(self) -> None:
        printed = Mock()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                patch("unibot.cli.rehearsal_status", return_value={"status": "not_found"}),
                patch(
                    "unibot.cli.active_session_metadata",
                    return_value=[{"session_id": "synthetic-existing-session"}],
                ),
                patch("unibot.cli.network_isolation_preflight") as preflight,
                patch("unibot.cli._print_json", printed),
            ):
                exit_code = cli_main(
                    [
                        "rehearsal",
                        "start",
                        str(root / "manifest.json"),
                        "--state-root",
                        str(root / "rehearsals"),
                        "--session-root",
                        str(root / "sessions"),
                    ]
                )

        self.assertEqual(exit_code, 2)
        self.assertEqual(printed.call_args.args[0]["reason"], "active_learning_session_must_be_finished_or_deleted")
        preflight.assert_not_called()


if __name__ == "__main__":
    unittest.main()
