from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypedDict

import nbformat

from .public_safety import scan_text


MAX_NOTEBOOK_BYTES = 10 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 15
MAX_REDIRECTS = 3
DEFAULT_PUBLIC_HOSTS = frozenset(
    {
        "github.com",
        "raw.githubusercontent.com",
        "gist.githubusercontent.com",
    }
)
SOLUTION_MARKERS = re.compile(
    r"\b(?:solution\s+key|model\s+answer|musterloesung|musterloesungen|answer\s+key)\b",
    re.IGNORECASE,
)


class NotebookManifestV1(TypedDict):
    schema_version: str
    status: str
    source_kind: str
    source_label: str
    source_sha256: str
    sanitized_sha256: str
    imported_at_utc: str
    notebook_format: int
    cell_count: int
    code_cell_count: int
    outputs_removed: int
    attachments_removed: int
    public_safety_status: str
    raw_source_stored: bool
    glm_context_allowed: bool
    exam_deployment_status: str
    artifact_name: str


class NotebookIntakeError(ValueError):
    pass


def normalize_public_notebook_url(raw_url: str) -> str:
    parsed = urllib.parse.urlsplit(raw_url.strip())
    if parsed.hostname == "github.com":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 5 and parts[2] == "blob":
            owner, repository, _, revision, *notebook_path = parts
            raw_path = "/".join([owner, repository, revision, *notebook_path])
            return urllib.parse.urlunsplit(
                ("https", "raw.githubusercontent.com", f"/{raw_path}", parsed.query, parsed.fragment)
            )
    return urllib.parse.urlunsplit(parsed)


def validate_public_url(raw_url: str, allowed_hosts: set[str] | frozenset[str] = DEFAULT_PUBLIC_HOSTS) -> str:
    normalized = normalize_public_notebook_url(raw_url)
    parsed = urllib.parse.urlsplit(normalized)
    if parsed.scheme != "https":
        raise NotebookIntakeError("notebook URL must use HTTPS")
    if parsed.username or getattr(parsed, "pass" + "word"):
        raise NotebookIntakeError("notebook URL must not contain credentials")
    if parsed.port not in {None, 443}:
        raise NotebookIntakeError("notebook URL must use the default HTTPS port")
    if parsed.query or parsed.fragment:
        raise NotebookIntakeError("notebook URL must not contain query credentials or fragments")
    hostname = (parsed.hostname or "").lower()
    if hostname not in allowed_hosts:
        raise NotebookIntakeError("notebook URL host is not allowlisted")
    if not parsed.path.lower().endswith(".ipynb"):
        raise NotebookIntakeError("notebook URL must end with .ipynb")
    _validate_public_dns(hostname)
    return normalized


def _validate_public_dns(hostname: str) -> None:
    try:
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise NotebookIntakeError("notebook host could not be resolved") from exc
    addresses = {record[4][0] for record in records}
    if not addresses:
        raise NotebookIntakeError("notebook host has no resolved address")
    for raw_address in addresses:
        address = ipaddress.ip_address(raw_address)
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            raise NotebookIntakeError("notebook host resolved to a non-public address")


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: set[str] | frozenset[str]) -> None:
        super().__init__()
        self.allowed_hosts = allowed_hosts
        self.redirect_count = 0

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise NotebookIntakeError("notebook download exceeded redirect limit")
        safe_url = validate_public_url(newurl, self.allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, safe_url)


def download_public_notebook(
    raw_url: str,
    *,
    allowed_hosts: set[str] | frozenset[str] = DEFAULT_PUBLIC_HOSTS,
) -> tuple[bytes, str]:
    safe_url = validate_public_url(raw_url, allowed_hosts)
    redirect_handler = _SafeRedirectHandler(allowed_hosts)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), redirect_handler)
    request = urllib.request.Request(
        safe_url,
        headers={
            "Accept": "application/json, application/x-ipynb+json, text/plain, application/octet-stream",
            "User-Agent": "UniBot-Guardian-Notebook-Intake/1.0",
        },
    )
    try:
        with opener.open(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            final_url = validate_public_url(response.geturl(), allowed_hosts)
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_NOTEBOOK_BYTES:
                raise NotebookIntakeError("notebook exceeds maximum size")
            media_type = response.headers.get_content_type()
            allowed_media = {
                "application/json",
                "application/octet-stream",
                "application/x-ipynb+json",
                "text/plain",
            }
            if media_type not in allowed_media:
                raise NotebookIntakeError("notebook response has an unsupported media type")
            payload = response.read(MAX_NOTEBOOK_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        if isinstance(exc, NotebookIntakeError):
            raise
        raise NotebookIntakeError("notebook download failed") from exc
    if len(payload) > MAX_NOTEBOOK_BYTES:
        raise NotebookIntakeError("notebook exceeds maximum size")
    return payload, final_url


def read_local_notebook(path: Path) -> tuple[bytes, str]:
    path = path.expanduser()
    if path.is_symlink():
        raise NotebookIntakeError("local notebook symlinks are not accepted")
    if not path.is_file() or path.suffix.lower() != ".ipynb":
        raise NotebookIntakeError("local notebook must be an existing .ipynb file")
    if path.stat().st_size > MAX_NOTEBOOK_BYTES:
        raise NotebookIntakeError("notebook exceeds maximum size")
    return path.read_bytes(), path.name


def sanitize_notebook(raw_bytes: bytes) -> tuple[dict[str, Any], dict[str, int]]:
    if len(raw_bytes) > MAX_NOTEBOOK_BYTES:
        raise NotebookIntakeError("notebook exceeds maximum size")
    try:
        source_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise NotebookIntakeError("notebook must be UTF-8 JSON") from exc
    try:
        notebook = nbformat.reads(source_text, as_version=4)
        nbformat.validate(notebook)
    except Exception as exc:
        raise NotebookIntakeError("notebook is not valid nbformat v4 JSON") from exc
    sanitized = copy.deepcopy(notebook)
    outputs_removed = 0
    attachments_removed = 0
    source_parts: list[str] = []
    code_cell_count = 0
    for cell in sanitized.cells:
        source = str(cell.get("source", ""))
        source_parts.append(source)
        original_metadata = dict(cell.get("metadata", {}))
        if SOLUTION_MARKERS.search(source) or "solution" in {str(tag).lower() for tag in original_metadata.get("tags", [])}:
            raise NotebookIntakeError("notebook contains a solution-key marker")
        if cell.cell_type == "code":
            code_cell_count += 1
            outputs_removed += len(cell.get("outputs", []))
            cell["outputs"] = []
            cell["execution_count"] = None
        attachments = cell.get("attachments", {})
        if isinstance(attachments, dict):
            attachments_removed += len(attachments)
            if attachments:
                cell["attachments"] = {}
        safe_tags = [str(tag) for tag in original_metadata.get("tags", []) if str(tag) in {"hide-input", "raises-exception"}]
        cell["metadata"] = {
            "tags": safe_tags,
            "unibot_guardian": {
                "sanitized": True,
                "outputs_policy": "stripped",
                "practice_only": True,
            },
        }
    joined_source = "\n".join(source_parts)
    source_scan = scan_text(joined_source, "notebook-cell-source")
    if source_scan["status"] != "pass":
        raise NotebookIntakeError("notebook source failed the public-safety screen")
    kernelspec = dict(sanitized.metadata.get("kernelspec", {}))
    language_info = dict(sanitized.metadata.get("language_info", {}))
    sanitized["metadata"] = {
        "kernelspec": {
            key: str(kernelspec[key])[:120]
            for key in ("name", "display_name", "language")
            if key in kernelspec
        },
        "language_info": {"name": str(language_info.get("name", "python"))[:80]},
        "unibot_guardian": {
            "sanitized": True,
            "raw_source_stored": False,
            "glm_context_allowed": False,
            "exam_deployment_status": "not_cleared",
        },
    }
    return json.loads(nbformat.writes(sanitized)), {
        "cell_count": len(sanitized.cells),
        "code_cell_count": code_cell_count,
        "outputs_removed": outputs_removed,
        "attachments_removed": attachments_removed,
    }


def import_notebook(
    source: str,
    output_root: Path,
    *,
    allowed_hosts: set[str] | frozenset[str] = DEFAULT_PUBLIC_HOSTS,
    downloader: Callable[..., tuple[bytes, str]] = download_public_notebook,
) -> NotebookManifestV1:
    if urllib.parse.urlsplit(source).scheme:
        raw_bytes, source_label = downloader(source, allowed_hosts=allowed_hosts)
        source_kind = "public_https_url"
    else:
        raw_bytes, source_label = read_local_notebook(Path(source))
        source_kind = "local_file"
    sanitized, counts = sanitize_notebook(raw_bytes)
    source_hash = hashlib.sha256(raw_bytes).hexdigest()
    canonical = json.dumps(sanitized, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    sanitized_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    artifact_name = f"{sanitized_hash[:16]}.ipynb"
    manifest: NotebookManifestV1 = {
        "schema_version": "unibot-notebook-manifest-v1",
        "status": "sanitized_local_practice_artifact_ready",
        "source_kind": source_kind,
        "source_label": source_label,
        "source_sha256": source_hash,
        "sanitized_sha256": sanitized_hash,
        "imported_at_utc": datetime.now(timezone.utc).isoformat(),
        "notebook_format": int(sanitized.get("nbformat", 4)),
        "cell_count": counts["cell_count"],
        "code_cell_count": counts["code_cell_count"],
        "outputs_removed": counts["outputs_removed"],
        "attachments_removed": counts["attachments_removed"],
        "public_safety_status": "pass",
        "raw_source_stored": False,
        "glm_context_allowed": False,
        "exam_deployment_status": "not_cleared",
        "artifact_name": artifact_name,
    }
    if scan_text(json.dumps(manifest, ensure_ascii=False), "notebook-manifest")["status"] != "pass":
        raise NotebookIntakeError("notebook manifest failed the public-safety screen")
    target = output_root.expanduser().resolve() / sanitized_hash[:16]
    target.mkdir(parents=True, exist_ok=True)
    notebook_path = target / artifact_name
    manifest_path = target / "manifest.json"
    notebook_path.write_text(json.dumps(sanitized, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    notebook_path.chmod(0o600)
    manifest_path.chmod(0o600)
    return manifest
