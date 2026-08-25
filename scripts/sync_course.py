#!/usr/bin/env python3
"""One-command Canvas → snapshot → public site → parity verification workflow."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(script: str, env: dict[str, str] | None = None) -> None:
    print(f"\n=== {script} ===", flush=True)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT,
        check=True,
        env=env,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-token-file",
        type=Path,
        help=(
            "Private Verizon Canvas token file. The token is passed to child "
            "processes through CANVAS_TOKEN and is never printed."
        ),
    )
    args = parser.parse_args()
    env = os.environ.copy()
    if args.source_token_file:
        token_path = args.source_token_file.expanduser()
        token = token_path.read_text(encoding="utf-8").strip()
        if not token:
            raise SystemExit(f"Source token file is empty: {token_path}")
        env["CANVAS_TOKEN"] = token
    run("export_canvas.py", env)
    run("build_site.py", env)
    run("verify_site.py", env)
    run("verify_live.py", env)
    print("\nSYNC PASS: snapshot, generated site, public assets, and live Canvas agree.")


if __name__ == "__main__":
    main()
