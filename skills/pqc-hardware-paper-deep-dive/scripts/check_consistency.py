#!/usr/bin/env python3
"""Backward-compatible HTML consistency preflight."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, required=True)
    args = parser.parse_args()
    validator = Path(__file__).with_name("validate_output.py")
    return subprocess.run([sys.executable, str(validator), "--paper-dir", str(args.paper_dir), "--allow-missing-pdf"]).returncode

if __name__ == "__main__": raise SystemExit(main())
