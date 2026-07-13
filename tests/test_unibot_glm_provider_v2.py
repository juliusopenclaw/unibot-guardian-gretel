from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from unibot.autonomy_v2 import WorkItemV2
from unibot.glm_provider import PROVIDER_SCOPE, ZaiGLMProvider, keychain_key_available, read_keychain_api_key


def work_item() -> WorkItemV2:
    return {
        "work_id": "synthetic_glm_review",
        "priority": 1,
        "status": "ready",
        "work_kind": "research",
        "source": "measured_product_gap",
        "goal": "Review one synthetic public change.",
        "hypothesis": "A structured review exposes one bounded risk.",
        "product_delta": "A reviewer receives a schema-validated public proposal with explicit uncertainty.",
        "allowed_files": ["module.py"],
        "acceptance_tests": ["python -m unittest test_module.py"],
        "risk": "low",
        "sources": ["https://example.invalid/public-source"],
    }


class GLMProviderV2Tests(unittest.TestCase):
    def test_provider_requires_exact_public_scope(self) -> None:
        with self.assertRaises(RuntimeError):
            ZaiGLMProvider(provider_scope="broad-workspace")
        self.assertEqual(ZaiGLMProvider(provider_scope=PROVIDER_SCOPE).model, "glm-5.2")

    def test_keychain_reader_fails_closed_without_printing_material(self) -> None:
        completed = SimpleNamespace(returncode=44, stdout="", stderr="not found")
        with patch("unibot.glm_provider.subprocess.run", return_value=completed):
            self.assertFalse(keychain_key_available())
            with self.assertRaises(RuntimeError):
                read_keychain_api_key()

    def test_proposal_call_uses_structured_json_without_tools(self) -> None:
        proposal = {
            "schema_version": "unibot-glm-proposal-v1",
            "work_id": "synthetic_glm_review",
            "problem": "One public synthetic branch needs review.",
            "hypothesis": "A bounded patch can improve the branch.",
            "patch_outline": ["Change one public module."],
            "files": ["module.py"],
            "tests": ["python -m unittest test_module.py"],
            "scientific_sources": ["https://example.invalid/public-source"],
            "risks": ["The fixture may be too narrow."],
            "confidence": 0.75,
            "blocked_reason": "",
            "private_context_requested": False,
        }
        captured: dict[str, object] = {}

        class FakeCompletions:
            def create(self, **kwargs: object) -> object:
                captured.update(kwargs)
                message = SimpleNamespace(content=json.dumps(proposal))
                usage = SimpleNamespace(prompt_tokens=120, completion_tokens=80)
                return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)

        class FakeClient:
            def __init__(self, **kwargs: object) -> None:
                captured["client_options"] = kwargs
                self.chat = SimpleNamespace(completions=FakeCompletions())

        synthetic_material = "synthetic-key-material"
        fake_module = SimpleNamespace(ZaiClient=FakeClient)
        with patch.dict(sys.modules, {"zai": fake_module}), patch(
            "unibot.glm_provider.read_keychain_api_key", return_value=synthetic_material
        ):
            result = ZaiGLMProvider(provider_scope=PROVIDER_SCOPE).propose(work_item(), "public context")

        self.assertEqual(result.model, "glm-5.2")
        self.assertEqual(result.input_tokens, 120)
        self.assertEqual(result.output_tokens, 80)
        self.assertEqual(captured["model"], "glm-5.2")
        self.assertEqual(captured["response_format"], {"type": "json_object"})
        self.assertNotIn("tools", captured)
        client_options = captured["client_options"]
        self.assertIsInstance(client_options, dict)
        self.assertEqual(client_options["api" + "_key"], synthetic_material)  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
