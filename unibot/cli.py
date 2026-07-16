from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

from .autonomy_v3 import (
    AutonomyController,
    AutonomyStore,
    ProviderGate,
    WorkItemV3,
    autonomy_doctor,
    autonomy_loop_status,
    default_test_registry,
    evaluate_three_golden_rules,
    prepare_autonomy_loop,
    request_autonomy_loop_start,
    three_golden_rules_status,
)
from .autonomy_v2 import (
    autonomy_status,
    repository_preflight,
    run_proposal_cycle,
    run_review_cycle,
)
from .companion import DEFAULT_EXTENSION_ID, companion_diagnose, companion_status, install_companion, run_native_host
from .clearance import (
    build_institutional_review_decision_template_markdown,
    build_institutional_presentation_markdown,
    build_institutional_presentation_packet,
    build_regulatory_profile,
    build_institutional_review_decision_template,
    write_institutional_review_bundle,
)
from .gateway import GatewayError, launch_gateway
from .guardian_benchmark import evaluate_guardian_benchmark, guardian_semantic_precision_work_item
from .extension_package import package_extension
from .glm_provider import PROVIDER_SCOPE, ZaiGLMProvider, keychain_key_available
from .notebook_intake import NotebookIntakeError, import_notebook
from .public_safety import scan_text
from .release_candidate import write_release_candidate_bundle
from .release_audit import audit_release_candidate
from .release_pr import write_release_pr_draft
from .release_handoff import write_release_handoff
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

    provider = autonomy_commands.add_parser("provider", help="inspect or explicitly park the v3 provider gate")
    provider_commands = provider.add_subparsers(dest="provider_command", required=True)
    for name in ("status", "park"):
        command = provider_commands.add_parser(name)
        command.add_argument("--state-db", type=Path)
        command.add_argument("--provider-state", type=Path)
    unpark = provider_commands.add_parser("unpark")
    unpark.add_argument("--scope", required=True)
    unpark.add_argument("--state-db", type=Path)
    unpark.add_argument("--provider-state", type=Path)

    rollout = autonomy_commands.add_parser("rollout", help="inspect the offline-first v3 rollout gates")
    rollout_commands = rollout.add_subparsers(dest="rollout_command", required=True)
    for name in ("status", "shadow", "local"):
        command = rollout_commands.add_parser(name)
        command.add_argument("--state-db", type=Path)
        command.add_argument("--repo", type=Path, default=Path.cwd())

    autonomy_doctor_parser = autonomy_commands.add_parser("doctor", help="run local v3 safety diagnostics")
    autonomy_doctor_parser.add_argument("--state-db", type=Path)

    loop = autonomy_commands.add_parser("loop", help="prepare or inspect the disabled local v3 watcher")
    loop_commands = loop.add_subparsers(dest="loop_command", required=True)
    for name in ("install", "start", "status", "tick", "stop"):
        command = loop_commands.add_parser(name)
        command.add_argument("--state-db", type=Path)

    work = autonomy_commands.add_parser("work", help="store a bounded v3 work item locally")
    work_commands = work.add_subparsers(dest="work_command", required=True)
    claim = work_commands.add_parser("claim")
    claim.add_argument("--work-item", type=Path, required=True)
    claim.add_argument("--state-db", type=Path)
    release = work_commands.add_parser("release")
    release.add_argument("--work-id", required=True)
    release.add_argument("--state-db", type=Path)

    audit = autonomy_commands.add_parser("audit", help="read one local v3 run record")
    audit.add_argument("run_id")
    audit.add_argument("--state-db", type=Path)

    evolve = autonomy_commands.add_parser("evolve", help="inspect the review-gated Three Golden Rules ledger")
    evolve_commands = evolve.add_subparsers(dest="evolve_command", required=True)
    evolve_status = evolve_commands.add_parser("status")
    evolve_status.add_argument("--state-db", type=Path)
    evolve_audit = evolve_commands.add_parser("audit")
    evolve_audit.add_argument("pattern_id")
    evolve_audit.add_argument("--state-db", type=Path)

    evaluate = commands.add_parser("evaluate", help="run deterministic local evaluation suites")
    evaluate_commands = evaluate.add_subparsers(dest="evaluate_command", required=True)
    evaluate_guardian = evaluate_commands.add_parser("guardian", help="measure Guardian semantic precision")
    evaluate_guardian.add_argument("--json", action="store_true")
    evaluate_3gr = evaluate_commands.add_parser("3gr", help="validate a Three Golden Rules work contract")
    evaluate_3gr.add_argument("--work-item", type=Path)
    evaluate_3gr.add_argument("--state-db", type=Path)
    evaluate_3gr.add_argument("--json", action="store_true")

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
    companion_diagnose_parser = companion_commands.add_parser("diagnose")
    companion_diagnose_parser.add_argument("--extension-id", default=DEFAULT_EXTENSION_ID)
    companion_commands.add_parser("native-host", help=argparse.SUPPRESS)

    commands.add_parser("public-safety", help="scan public repository artifacts")

    institution = commands.add_parser("institution", help="prepare public-safe institutional review artifacts")
    institution_commands = institution.add_subparsers(dest="institution_command", required=True)
    institution_commands.add_parser("profile", help="show RegulatoryProfileV1")
    presentation = institution_commands.add_parser("presentation", help="show the review meeting packet")
    presentation.add_argument("--markdown", action="store_true")
    decision_template = institution_commands.add_parser(
        "decision-template", help="show the blank human review outcome template"
    )
    decision_template.add_argument("--markdown", action="store_true")
    bundle = institution_commands.add_parser("bundle", help="write the public-safe institutional review handoff")
    bundle.add_argument("--output", type=Path, required=True)

    extension = commands.add_parser("extension", help="package the public Chrome extension")
    extension_commands = extension.add_subparsers(dest="extension_command", required=True)
    extension_package = extension_commands.add_parser("package", help="write a deterministic MV3 ZIP package")
    extension_package.add_argument("--output", type=Path, required=True)

    release = commands.add_parser("release", help="prepare a public-safe human review handoff")
    release_commands = release.add_subparsers(dest="release_command", required=True)
    release_candidate = release_commands.add_parser("candidate", help="write the extension and institutional review bundle")
    release_candidate.add_argument("--output", type=Path, required=True)
    release_audit = release_commands.add_parser("audit", help="verify a release candidate without modifying it")
    release_audit.add_argument("candidate", type=Path)
    release_audit.add_argument("--repo", type=Path, default=Path.cwd())
    release_pr = release_commands.add_parser("pr-draft", help="write a human-gated GitHub PR draft")
    release_pr.add_argument("--candidate", type=Path, required=True)
    release_pr.add_argument("--output", type=Path, required=True)
    release_pr.add_argument("--repo", type=Path, default=Path.cwd())
    release_handoff = release_commands.add_parser(
        "handoff", help="atomically build the candidate, audit, and human PR handoff"
    )
    release_handoff.add_argument("--output", type=Path, required=True)
    release_handoff.add_argument("--repo", type=Path, default=Path.cwd())
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
        if args.command == "autonomy" and args.autonomy_command == "provider":
            store = AutonomyStore(args.state_db)
            try:
                gate = ProviderGate(args.provider_state, store=store)
                if args.provider_command == "status":
                    _print_json(gate.status())
                    return 0
                if args.provider_command == "park":
                    _print_json(gate.park())
                    return 0
                try:
                    _print_json(gate.unpark(args.scope))
                    return 0
                except ValueError as exc:
                    _print_json({"status": "blocked", "reason": str(exc)})
                    return 2
            finally:
                store.close()
        if args.command == "autonomy" and args.autonomy_command == "rollout":
            store = AutonomyStore(args.state_db)
            try:
                recovered = store.recover_interrupted_runs()
                rollout = store.rollout_status()
                if args.rollout_command == "status":
                    _print_json({"status": "ok", "rollout": rollout, "recovered_runs": recovered, "watcher_active": False})
                    return 0
                if args.rollout_command == "shadow":
                    repo = args.repo.resolve()
                    branch = subprocess.run(
                        ["git", "-C", str(repo), "branch", "--show-current"],
                        check=False,
                        capture_output=True,
                        text=True,
                        shell=False,
                    ).stdout.strip()
                    if branch != "main":
                        _print_json(
                            {
                                "status": "blocked",
                                "reason": "official_main_base_required",
                                "requested_lane": "shadow",
                                "rollout": rollout,
                                "provider_calls": 0,
                                "github_actions": 0,
                            }
                        )
                        return 2
                    base_commit = subprocess.run(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"],
                        check=True,
                        capture_output=True,
                        text=True,
                        shell=False,
                    ).stdout.strip()
                    item = guardian_semantic_precision_work_item(base_commit)
                    result = AutonomyController(repo_root=repo, store=store).run_shadow_rollout(
                        item,
                        test_registry_factory=default_test_registry,
                    )
                    _print_json(result)
                    return 0 if result["status"] == "shadow_green" else 2
                _print_json(
                    {
                        "status": "blocked",
                        "reason": "explicit_registered_runner_required",
                        "requested_lane": args.rollout_command,
                        "rollout": rollout,
                        "provider_calls": 0,
                        "github_actions": 0,
                        "watcher_active": False,
                    }
                )
                return 2
            finally:
                store.close()
        if args.command == "autonomy" and args.autonomy_command == "doctor":
            store = AutonomyStore(args.state_db)
            try:
                _print_json({**autonomy_doctor(store), "rollout": store.rollout_status(), "watcher_active": False})
                return 0
            finally:
                store.close()
        if args.command == "autonomy" and args.autonomy_command == "loop":
            store = AutonomyStore(args.state_db)
            try:
                if args.loop_command == "install":
                    _print_json(prepare_autonomy_loop(store))
                    return 0
                if args.loop_command == "status":
                    _print_json(autonomy_loop_status(store))
                    return 0
                if args.loop_command == "start":
                    _print_json(request_autonomy_loop_start(store))
                    return 2
                _print_json(
                    {
                        "status": "idle",
                        "reason": "watcher_remains_disabled_until_rollout_and_human_launchd_gate",
                        "loop": autonomy_loop_status(store)["loop"],
                        "provider_calls": 0,
                        "github_actions": 0,
                    }
                )
                return 0
            finally:
                store.close()
        if args.command == "autonomy" and args.autonomy_command == "work":
            store = AutonomyStore(args.state_db)
            try:
                if args.work_command == "claim":
                    item = WorkItemV3.from_dict(json.loads(args.work_item.read_text(encoding="utf-8")))
                    store.save_work_item(item)
                    evaluation = evaluate_three_golden_rules(item)
                    status = "queued" if evaluation["status"] == "pass" else "gretel_proposed"
                    _print_json(
                        {
                            "status": status,
                            "work_item": item.to_dict(),
                            "three_golden_rules": evaluation,
                            "execution_allowed": status == "queued",
                            "automatic_merge": False,
                        }
                    )
                    return 0 if status == "queued" else 2
                released = store.release_work_item(args.work_id)
                _print_json({"status": "released" if released else "not_found", "work_id": args.work_id})
                return 0 if released else 2
            finally:
                store.close()
        if args.command == "autonomy" and args.autonomy_command == "audit":
            store = AutonomyStore(args.state_db)
            try:
                run = store.get_run(args.run_id)
                _print_json({"status": "ok" if run else "not_found", "run": run, "automatic_merge": False})
                return 0 if run else 2
            finally:
                store.close()
        if args.command == "autonomy" and args.autonomy_command == "evolve":
            store = AutonomyStore(args.state_db)
            try:
                if args.evolve_command == "status":
                    _print_json(three_golden_rules_status(store))
                    return 0
                pattern = store.get_improvement_pattern(args.pattern_id)
                _print_json(
                    {
                        "status": "ok" if pattern else "not_found",
                        "pattern": pattern,
                        "automatic_apply": False,
                        "human_review_required": True,
                    }
                )
                return 0 if pattern else 2
            finally:
                store.close()
        if args.command == "autonomy" and args.autonomy_command == "run":
            if args.provider_go != PROVIDER_SCOPE:
                _print_json({"status": "blocked", "reason": "public-unibot-only provider scope required"})
                return 2
            store = AutonomyStore()
            try:
                provider_gate = ProviderGate(store=store)
                provider_status = provider_gate.status()
            finally:
                store.close()
            if not provider_status["call_allowed"]:
                _print_json({"status": "blocked", "reason": provider_status["reason"], "provider": provider_status})
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
        if args.command == "evaluate" and args.evaluate_command == "guardian":
            payload = evaluate_guardian_benchmark()
            _print_json(payload)
            return 0 if payload["status"] == "pass" else 2
        if args.command == "evaluate" and args.evaluate_command == "3gr":
            if args.work_item:
                item = WorkItemV3.from_dict(json.loads(args.work_item.read_text(encoding="utf-8")))
                payload = evaluate_three_golden_rules(item)
            else:
                store = AutonomyStore(args.state_db)
                try:
                    payload = three_golden_rules_status(store)
                finally:
                    store.close()
            _print_json(payload)
            return 0 if payload["status"] in {"pass", "ok"} else 2
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
        if args.command == "companion" and args.companion_command == "diagnose":
            payload = companion_diagnose(args.extension_id)
            _print_json(payload)
            return 0 if payload["status"] == "ready" else 2
        if args.command == "companion" and args.companion_command == "native-host":
            return run_native_host()
        if args.command == "public-safety":
            payload = public_repository_safety(Path.cwd())
            _print_json(payload)
            return 0 if payload["status"] == "pass" else 2
        if args.command == "institution" and args.institution_command == "profile":
            payload = build_regulatory_profile()
            _print_json(payload)
            return 0 if payload["status"] == "review_preparation" else 2
        if args.command == "institution" and args.institution_command == "presentation":
            payload = build_institutional_presentation_packet()
            if args.markdown:
                print(json.dumps({"status": payload["status"], "markdown": build_institutional_presentation_markdown(payload)}, ensure_ascii=True, indent=2))
            else:
                _print_json(payload)
            return 0 if payload["status"] == "ready_for_human_review" else 2
        if args.command == "institution" and args.institution_command == "decision-template":
            payload = build_institutional_review_decision_template()
            if args.markdown:
                print(json.dumps({"status": payload["status"], "markdown": build_institutional_review_decision_template_markdown(payload)}, ensure_ascii=True, indent=2))
            else:
                _print_json(payload)
            return 0 if payload["status"] == "blank_for_human_completion" else 2
        if args.command == "institution" and args.institution_command == "bundle":
            payload = write_institutional_review_bundle(args.output)
            _print_json(payload)
            return 0 if payload["status"] == "written" else 2
        if args.command == "extension" and args.extension_command == "package":
            payload = package_extension(args.output)
            _print_json(payload)
            return 0 if payload["status"] == "written" else 2
        if args.command == "release" and args.release_command == "candidate":
            payload = write_release_candidate_bundle(args.output)
            _print_json(payload)
            return 0 if payload["status"] == "written" else 2
        if args.command == "release" and args.release_command == "audit":
            payload = audit_release_candidate(args.candidate, repository=args.repo)
            _print_json(payload)
            return 0 if payload["status"] == "pass" else 2
        if args.command == "release" and args.release_command == "pr-draft":
            payload = write_release_pr_draft(args.output, args.candidate, repository=args.repo)
            _print_json(payload)
            return 0 if payload["status"] == "ready_for_human_review" else 2
        if args.command == "release" and args.release_command == "handoff":
            payload = write_release_handoff(args.output, repository=args.repo)
            _print_json(payload)
            return 0 if payload["status"] == "written" else 2
    except (GatewayError, NotebookIntakeError, RuntimeError, ValueError, OSError) as exc:
        _print_json({"status": "blocked", "reason": str(exc)})
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
