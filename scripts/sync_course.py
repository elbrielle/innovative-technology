#!/usr/bin/env python3
"""One-command Canvas → snapshot → public site → parity verification workflow."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    print(f"\n=== {script} ===", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)


def main() -> None:
    run("export_canvas.py")
    run("build_site.py")
    run("verify_site.py")
    run("verify_live.py")
    print("\nSYNC PASS: snapshot, generated site, public assets, and live Canvas agree.")


if __name__ == "__main__":
    main()
