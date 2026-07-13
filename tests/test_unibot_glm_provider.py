from __future__ import annotations

import unittest

from unibot.glm_provider import provider_failure_reason


class UniBotGlmProviderTests(unittest.TestCase):
    def test_insufficient_balance_is_non_retryable_and_sanitized(self) -> None:
        reason = provider_failure_reason(
            RuntimeError("429 business code 1113 Insufficient balance " + "api" + "_key=secret")
        )
        self.assertIn("insufficient balance", reason)
        self.assertIn("no retry", reason)
        self.assertNotIn("secret", reason)

    def test_transport_failures_are_fail_closed(self) -> None:
        self.assertIn("rate limited", provider_failure_reason(RuntimeError("HTTP 429 rate limit")))
        self.assertIn("timed out", provider_failure_reason(TimeoutError("timed out")))
        self.assertIn("failed closed", provider_failure_reason(RuntimeError("unknown SDK failure")))


if __name__ == "__main__":
    unittest.main()
