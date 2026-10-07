#!/usr/bin/env python3
"""Compatibility alias for structural preflight; does not verify paper semantics."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, required=True)
    parser.add_argument("--allow-no-figures", action="store_true")
    args = parser.parse_args()
    validator = Path(__file__).with_name("validate_output.py")
    command = [sys.executable, str(validator), "--paper-dir", str(args.paper_dir), "--allow-missing-pdf"]
    if args.allow_no_figures: command.append("--allow-no-figures")
    return subprocess.run(command).returncode

if __name__ == "__main__": raise SystemExit(main())
