#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from unibot.simulation_loop import report_to_markdown, run_gretel_unibot_loop  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the UniBot-Gretel public-safe exam loop smoke.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    parser.add_argument("--gretel-url", default=None, help="Optional live Gretel base URL, e.g. http://127.0.0.1:4173.")
    parser.add_argument("--unibot-url", default=None, help="Optional live UniBot base URL, e.g. http://127.0.0.1:8765.")
    parser.add_argument("--deepseek-live", action="store_true", help="Use live DeepSeek only when DEEPSEEK_API_KEY is set.")
    args = parser.parse_args()

    report = run_gretel_unibot_loop(
        gretel_url=args.gretel_url,
        unibot_url=args.unibot_url,
        deepseek_live=args.deepseek_live,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report_to_markdown(report), end="")
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
