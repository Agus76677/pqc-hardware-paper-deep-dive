#!/usr/bin/env python3
"""Build the PDF from the authored HTML source."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--allow-no-figures", action="store_true")
    parser.add_argument("--keep-going", action="store_true", help="Retained for CLI compatibility; HTML is the only pipeline.")
    args = parser.parse_args()
    script = Path(__file__).with_name("build_html.py")
    command = [sys.executable, str(script), "--paper-dir", str(args.paper_dir), "--timeout", str(args.timeout)]
    if args.allow_no_figures:
        command.append("--allow-no-figures")
    result = subprocess.run(command)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
