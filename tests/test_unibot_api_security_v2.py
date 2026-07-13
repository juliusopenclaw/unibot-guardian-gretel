from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request

from unibot.server import create_server


EXTENSION_ORIGIN = "chrome-extension://" + "a" * 32


class UniBotApiSecurityV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = create_server(
            "127.0.0.1",
            0,
            session_token=f"synthetic-session-{self._testMethodName}",
            pairing_code="12345678",
        )
        if self.server.session_ledger_path.exists():
            self.server.session_ledger_path.unlink()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(
        self,
        path: str,
        *,
        payload: dict[str, object] | None = None,
        origin: str = "",
        session_value: str = "",
        host: str = "",
    ) -> tuple[int, dict[str, object], dict[str, str]]:
        headers = {"content-type": "application/json"}
        if origin:
            headers["Origin"] = origin
        if session_value:
            headers["X-UniBot-Token"] = session_value
        if host:
            headers["Host"] = host
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method="POST" if payload is not None else "GET",
        )
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            body = json.loads(error.read().decode("utf-8"))
            return error.code, body, dict(error.headers.items())
        with response:
            body = json.loads(response.read().decode("utf-8"))
            return response.status, body, dict(response.headers.items())

    def pair(self) -> str:
        status, body, headers = self.request(
            "/api/v2/pair",
            payload={"pairing_code": "12345678"},
            origin=EXTENSION_ORIGIN,
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "paired")
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), EXTENSION_ORIGIN)
        return str(body["session_token"])

    def test_health_is_public_but_never_uses_wildcard_cors(self) -> None:
        status, body, headers = self.request("/api/v2/health", origin="https://unrelated.example")
        self.assertEqual(status, 200)
        self.assertEqual(body["authentication"], "one-time pairing and session token")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_protected_route_requires_pairing_token(self) -> None:
        status, body, _ = self.request(
            "/api/v2/socratic/help",
            payload={"task": "synthetic list practice", "help_level": "A2"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(body["status"], "session-token-required")

    def test_pairing_pins_extension_origin_and_rejects_other_origins(self) -> None:
        session_value = self.pair()
        status, body, headers = self.request(
            "/api/v2/socratic/help",
            payload={"task": "synthetic list practice", "help_level": "A2"},
            origin=EXTENSION_ORIGIN,
            session_value=session_value,
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), EXTENSION_ORIGIN)
        self.assertNotEqual(body.get("status"), "session-token-required")

        status, summary, _ = self.request(
            "/api/v2/session/export",
            origin=EXTENSION_ORIGIN,
            session_value=session_value,
        )
        self.assertEqual(status, 200)
        self.assertEqual(summary["event_count"], 1)
        self.assertNotIn("path", summary)

        status, body, _ = self.request(
            "/api/v2/socratic/help",
            payload={"task": "synthetic list practice", "help_level": "A2"},
            origin="https://unrelated.example",
            session_value=session_value,
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["status"], "blocked-origin")

    def test_high_help_level_and_untrusted_host_are_blocked(self) -> None:
        session_value = self.pair()
        status, body, _ = self.request(
            "/api/v2/socratic/help",
            payload={"task": "synthetic list practice", "help_level": "A4"},
            origin=EXTENSION_ORIGIN,
            session_value=session_value,
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["allowed_help_levels"], ["A0", "A1", "A2"])

        status, body, _ = self.request("/api/v2/health", host="unrelated.example")
        self.assertEqual(status, 403)
        self.assertEqual(body["status"], "blocked-host")

    def test_learning_contract_enables_a0_a4_tutor_and_metadata_report(self) -> None:
        session_value = self.pair()
        status, contract_response, _ = self.request(
            "/api/v2/session/contracts",
            payload={
                "assistance_mode": "fixed",
                "fixed_help_level": "A4",
                "max_help_level": "A4",
                "pseudonym": "Synthetic Learner",
            },
            origin=EXTENSION_ORIGIN,
            session_value=session_value,
        )
        self.assertEqual(status, 201)
        self.assertEqual(contract_response["contract"]["max_help_level"], "A4")

        status, turn, _ = self.request(
            "/api/v2/socratic/help",
            payload={
                "task": "Wie strukturiere ich einen z-Wert?",
                "learner_attempt": "Ich kenne Beobachtung und Mittelwert.",
                "requested_help_level": "A4",
                "confirm_escalation": True,
            },
            origin=EXTENSION_ORIGIN,
            session_value=session_value,
        )
        self.assertEqual(status, 200)
        self.assertEqual(turn["effective_help_level"], "A4")
        self.assertFalse(turn["raw_cell_stored"])

        status, report, _ = self.request(
            "/api/v2/session/export",
            payload={},
            origin=EXTENSION_ORIGIN,
            session_value=session_value,
        )
        self.assertEqual(status, 200)
        self.assertEqual(report["schema_version"], "unibot-independence-report-v1")
        self.assertFalse(report["raw_attempt_text_included"])

    def test_pairing_attempt_limit_is_enforced(self) -> None:
        for _ in range(5):
            status, _, _ = self.request(
                "/api/v2/pair",
                payload={"pairing_code": "00000000"},
                origin=EXTENSION_ORIGIN,
            )
            self.assertEqual(status, 401)
        status, body, _ = self.request(
            "/api/v2/pair",
            payload={"pairing_code": "12345678"},
            origin=EXTENSION_ORIGIN,
        )
        self.assertEqual(status, 429)
        self.assertEqual(body["status"], "pairing-attempt-limit")


if __name__ == "__main__":
    unittest.main()
