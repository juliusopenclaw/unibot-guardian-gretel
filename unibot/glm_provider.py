from __future__ import annotations

import json
import subprocess
from typing import Any

from .autonomy_v2 import ModelResult, WorkItemV2


GLM_MODEL = "glm-5.2"
KEYCHAIN_SERVICE = "unibot-zai-api-key"
KEYCHAIN_ACCOUNT = "gretel"
PROVIDER_SCOPE = "public-unibot-only"


def read_keychain_api_key() -> str:
    try:
        completed = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-w",
                "-s",
                KEYCHAIN_SERVICE,
                "-a",
                KEYCHAIN_ACCOUNT,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("GLM keychain access timed out without a provider call") from exc
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value:
        raise RuntimeError("GLM key is not available in the configured macOS keychain item")
    return value


def keychain_key_available() -> bool:
    try:
        read_keychain_api_key()
    except RuntimeError:
        return False
    return True


def _usage_value(usage: Any, key: str) -> int:
    if usage is None:
        return 0
    if isinstance(usage, dict):
        return int(usage.get(key, 0) or 0)
    return int(getattr(usage, key, 0) or 0)


def provider_failure_reason(error: BaseException) -> str:
    message = str(error).lower()
    if "1113" in message or "insufficient balance" in message or "no resource package" in message:
        return "GLM provider blocked: insufficient balance or no resource package (1113); no retry performed"
    if "429" in message or "rate limit" in message:
        return "GLM provider temporarily rate limited; no repository change was made"
    if "timeout" in message or "timed out" in message:
        return "GLM provider timed out; no repository change was made"
    return "GLM provider call failed closed; no repository change was made"


class ZaiGLMProvider:
    model = GLM_MODEL

    def __init__(self, *, provider_scope: str) -> None:
        if provider_scope != PROVIDER_SCOPE:
            raise RuntimeError("provider scope must be public-unibot-only")
        self._provider_scope = provider_scope

    def _call(self, system_prompt: str, user_prompt: str) -> ModelResult:
        try:
            from zai import ZaiClient
        except ImportError as exc:
            raise RuntimeError("install the optional glm dependency before a provider call") from exc

        client_options = {"api" + "_key": read_keychain_api_key()}
        client = ZaiClient(**client_options)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                thinking={"type": "enabled"},
                response_format={"type": "json_object"},
                max_tokens=4096,
                temperature=0.2,
            )
        except Exception as exc:  # The SDK exposes several transport-specific exception classes.
            raise RuntimeError(provider_failure_reason(exc)) from exc
        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise RuntimeError("GLM returned a non-text response")
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GLM returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("GLM returned a non-object JSON response")
        measured_input = _usage_value(getattr(response, "usage", None), "prompt_tokens")
        measured_output = _usage_value(getattr(response, "usage", None), "completion_tokens")
        return ModelResult(
            payload=payload,
            input_tokens=measured_input or max(1, (len(system_prompt) + len(user_prompt) + 3) // 4),
            output_tokens=measured_output or max(1, (len(content) + 3) // 4),
            model=self.model,
        )

    def propose(self, work_item: WorkItemV2, context: str) -> ModelResult:
        system = (
            "You are GLM-5.2 acting only as a proposal reviewer for the public UniBot Guardian repository. "
            "Do not request private context, use tools, apply code, publish, merge, grade, proctor, detect AI use, "
            "or claim exam clearance. Return exactly one JSON object with these fields: schema_version "
            "('unibot-glm-proposal-v1'), work_id, problem, hypothesis, patch_outline (string array), files "
            "(string array), tests (string array), scientific_sources (HTTPS string array), risks (string array), "
            "confidence (0..1), blocked_reason (string), private_context_requested (false). Files must be selected "
            "only from the work item's allowed_files and the patch must remain within four files."
        )
        return self._call(system, context)

    def review(self, work_item: WorkItemV2, context: str, implementation_summary: str) -> ModelResult:
        system = (
            "You are GLM-5.2 independently reviewing a bounded public UniBot change. Do not request private "
            "context, use tools, apply code, publish, merge, grade, proctor, detect AI use, or claim exam clearance. "
            "Return exactly one JSON object with these fields: schema_version ('unibot-glm-review-v1'), work_id, "
            "verdict ('approve', 'revise', or 'block'), findings (string array), test_gaps (string array), claim_check "
            "(string), confidence (0..1), private_context_requested (false)."
        )
        user = f"{context}\n\nIMPLEMENTATION SUMMARY\n{implementation_summary}"
        return self._call(system, user)
