from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .autonomy_v2 import (
    autonomy_status,
    repository_preflight,
    run_proposal_cycle,
    run_review_cycle,
)
from .companion import DEFAULT_EXTENSION_ID, companion_status, install_companion, run_native_host
from .gateway import GatewayError, launch_gateway
from .glm_provider import PROVIDER_SCOPE, ZaiGLMProvider, keychain_key_available
from .notebook_intake import NotebookIntakeError, import_notebook
from .public_safety import scan_text
from .server import run as run_server


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))


def public_repository_safety(repo: Path) -> dict[str, Any]:
    roots = [
        repo / "README.md",
        repo / "AUTHORS.md",
        repo / "CONTRIBUTING.md",
        repo / "SECURITY.md",
    ]
    roots.extend(sorted((repo / "docs").glob("**/*.md")))
    roots.extend(sorted((repo / "unibot").glob("*.py")))
    roots.extend(sorted((repo / "unibot" / "browser_extension").glob("**/*")))
    roots.append(repo / "unibot" / "autonomy_work_items.json")
    findings: list[dict[str, Any]] = []
    scanned = 0
    for path in dict.fromkeys(roots):
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".js", ".html", ".json"}:
            continue
        relative = path.relative_to(repo).as_posix()
        scan = scan_text(path.read_text(encoding="utf-8"), relative)
        findings.extend(scan["findings"])
        scanned += 1
    return {
        "schema_version": "unibot-public-repository-safety-v2",
        "status": "pass" if not findings else "blocked",
        "scanned_count": scanned,
        "finding_count": len(findings),
        "findings": findings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="unibot", description="UniBot Guardian public-safe local tools")
    commands = parser.add_subparsers(dest="command", required=True)

    autonomy = commands.add_parser("autonomy", help="inspect or run the bounded Gretel/GLM lane")
    autonomy_commands = autonomy.add_subparsers(dest="autonomy_command", required=True)
    preflight = autonomy_commands.add_parser("preflight")
    preflight.add_argument("--repo", type=Path, default=Path.cwd())
    preflight.add_argument("--work-id", default="")
    preflight.add_argument("--json", action="store_true")
    status = autonomy_commands.add_parser("status")
    status.add_argument("--repo", type=Path, default=Path.cwd())
    run = autonomy_commands.add_parser("run")
    run.add_argument("--repo", type=Path, default=Path.cwd())
    run.add_argument("--work-id", default="")
    run.add_argument("--stage", choices=["proposal", "review"], default="proposal")
    run.add_argument("--run-id", default="")
    run.add_argument("--implementation-summary", type=Path)
    run.add_argument("--provider-go", default="")

    notebook = commands.add_parser("notebook", help="import a sanitized public or local notebook")
    notebook_commands = notebook.add_subparsers(dest="notebook_command", required=True)
    notebook_import = notebook_commands.add_parser("import")
    notebook_import.add_argument("source")
    notebook_import.add_argument("--output-root", type=Path, default=Path.cwd() / ".unibot" / "notebooks")

    serve = commands.add_parser("serve", help="run the paired loopback API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8765, type=int)
    serve.add_argument("--pair", action="store_true")

    gateway = commands.add_parser("gateway", help="launch the local practice-only Jupyter gateway")
    gateway_commands = gateway.add_subparsers(dest="gateway_command", required=True)
    gateway_launch = gateway_commands.add_parser("launch")
    gateway_launch.add_argument("manifest", type=Path)
    gateway_launch.add_argument("--port", type=int, default=8888)
    gateway_launch.add_argument("--dry-run", action="store_true")

    companion = commands.add_parser("companion", help="install or inspect the local Chrome companion")
    companion_commands = companion.add_subparsers(dest="companion_command", required=True)
    companion_install = companion_commands.add_parser("install")
    companion_install.add_argument("--extension-id", default=DEFAULT_EXTENSION_ID)
    companion_status_parser = companion_commands.add_parser("status")
    companion_status_parser.add_argument("--extension-id", default=DEFAULT_EXTENSION_ID)
    companion_commands.add_parser("native-host", help=argparse.SUPPRESS)

    commands.add_parser("public-safety", help="scan public repository artifacts")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "autonomy" and args.autonomy_command == "preflight":
            payload = repository_preflight(args.repo, work_id=args.work_id)
            _print_json(payload)
            return 0 if payload["status"] == "ready" else 2
        if args.command == "autonomy" and args.autonomy_command == "status":
            _print_json(autonomy_status(args.repo))
            return 0
        if args.command == "autonomy" and args.autonomy_command == "run":
            if args.provider_go != PROVIDER_SCOPE:
                _print_json({"status": "blocked", "reason": "public-unibot-only provider scope required"})
                return 2
            if not keychain_key_available():
                _print_json({"status": "blocked", "reason": "configured macOS keychain item is unavailable"})
                return 2
            provider = ZaiGLMProvider(provider_scope=args.provider_go)
            if args.stage == "proposal":
                summary, result = run_proposal_cycle(args.repo, provider, work_id=args.work_id, run_id=args.run_id)
            else:
                if not args.run_id or args.implementation_summary is None:
                    raise ValueError("review stage requires run ID and implementation summary")
                implementation_summary = args.implementation_summary.read_text(encoding="utf-8")
                summary, result = run_review_cycle(
                    args.repo,
                    provider,
                    args.run_id,
                    implementation_summary,
                    work_id=args.work_id,
                )
            _print_json({"summary": summary.__dict__, **result})
            return 0 if not result["validation_errors"] else 2
        if args.command == "notebook" and args.notebook_command == "import":
            _print_json(dict(import_notebook(args.source, args.output_root)))
            return 0
        if args.command == "serve":
            run_server(args.host, args.port, show_pairing_code=True)
            return 0
        if args.command == "gateway" and args.gateway_command == "launch":
            _print_json(launch_gateway(args.manifest, port=args.port, dry_run=args.dry_run))
            return 0
        if args.command == "companion" and args.companion_command == "install":
            _print_json(install_companion(args.extension_id))
            return 0
        if args.command == "companion" and args.companion_command == "status":
            _print_json(companion_status(args.extension_id))
            return 0
        if args.command == "companion" and args.companion_command == "native-host":
            return run_native_host()
        if args.command == "public-safety":
            payload = public_repository_safety(Path.cwd())
            _print_json(payload)
            return 0 if payload["status"] == "pass" else 2
    except (GatewayError, NotebookIntakeError, RuntimeError, ValueError, OSError) as exc:
        _print_json({"status": "blocked", "reason": str(exc)})
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
