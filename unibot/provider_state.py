from __future__ import annotations

import json
import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .glm_provider import PROVIDER_SCOPE


PROVIDER_STATE_SCHEMA = "unibot-provider-state-v1"
PARKED_STATUS = "parked_awaiting_zai_balance"
UNPARKED_STATUS = "unparked_public_unibot_only"
PROVIDER_STATE_ENV = "UNIBOT_PROVIDER_STATE_PATH"


def provider_state_path() -> Path:
    override = os.environ.get(PROVIDER_STATE_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / "Library" / "Application Support" / "UniBot Guardian" / "provider-state.json"


def _default_parked_state(reason: str = "awaiting_zai_balance") -> dict[str, Any]:
    return {
        "schema_version": PROVIDER_STATE_SCHEMA,
        "status": PARKED_STATUS,
        "reason": reason,
        "provider_scope": None,
        "provider_call_allowed": False,
        "contains_secret": False,
    }


def _blocked_state(status: str, reason: str) -> dict[str, Any]:
    state = _default_parked_state(reason)
    state["status"] = status
    return state


def provider_status() -> dict[str, Any]:
    path = provider_state_path()
    if not path.exists():
        return _default_parked_state()
    if path.is_symlink():
        return _blocked_state("parked_invalid_local_state", "provider state must not be a symbolic link")
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        return _blocked_state("parked_insecure_state_permissions", "provider state file must have mode 0600")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _blocked_state("parked_invalid_local_state", "provider state is unreadable or invalid")
    if not isinstance(payload, dict) or payload.get("schema_version") != PROVIDER_STATE_SCHEMA:
        return _blocked_state("parked_invalid_local_state", "provider state schema is invalid")
    status = payload.get("status")
    scope = payload.get("provider_scope")
    if status == PARKED_STATUS and scope is None:
        return {
            **_default_parked_state(str(payload.get("reason") or "awaiting_zai_balance")),
            "updated_at_utc": payload.get("updated_at_utc", ""),
        }
    if status == UNPARKED_STATUS and scope == PROVIDER_SCOPE:
        return {
            "schema_version": PROVIDER_STATE_SCHEMA,
            "status": UNPARKED_STATUS,
            "reason": "explicit_public_unibot_only_scope",
            "provider_scope": PROVIDER_SCOPE,
            "provider_call_allowed": True,
            "contains_secret": False,
            "updated_at_utc": payload.get("updated_at_utc", ""),
        }
    return _blocked_state("parked_invalid_local_state", "provider state values are invalid")


def _write_state(state: dict[str, Any]) -> dict[str, Any]:
    path = provider_state_path()
    parent_existed = path.parent.exists()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not parent_existed or PROVIDER_STATE_ENV not in os.environ:
        os.chmod(path.parent, 0o700)
    state = {**state, "updated_at_utc": datetime.now(timezone.utc).isoformat()}
    descriptor, temporary_name = tempfile.mkstemp(prefix=".provider-state-", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=True, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
        os.chmod(path, 0o600)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary_path.unlink(missing_ok=True)
        raise
    return provider_status()


def park_provider() -> dict[str, Any]:
    return _write_state(_default_parked_state())


def unpark_provider(scope: str) -> dict[str, Any]:
    if scope != PROVIDER_SCOPE:
        raise ValueError("provider scope must be public-unibot-only")
    return _write_state(
        {
            "schema_version": PROVIDER_STATE_SCHEMA,
            "status": UNPARKED_STATUS,
            "reason": "explicit_public_unibot_only_scope",
            "provider_scope": PROVIDER_SCOPE,
            "provider_call_allowed": True,
            "contains_secret": False,
        }
    )
