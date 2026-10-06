#!/usr/bin/env python3
"""Compile an authored HTML paper note to PDF with a Chromium-compatible browser."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote


def find_browser() -> str | None:
    explicit = __import__("os").environ.get("PAPER_DEEP_DIVE_BROWSER")
    candidates = [explicit] if explicit else []
    candidates += ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "msedge"]
    return next((item for item in candidates if item and shutil.which(item)), None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, required=True)
    parser.add_argument("--html", type=Path, help="Optional HTML source (default: article.html).")
    parser.add_argument("--output", type=Path, help="Optional PDF destination (default: article.pdf).")
    args = parser.parse_args()
    paper_dir = args.paper_dir.expanduser().resolve()
    html = (args.html or paper_dir / "article.html").expanduser().resolve()
    pdf = (args.output or paper_dir / "article.pdf").expanduser().resolve()
    if not html.is_file():
        print(f"missing HTML source: {html}", file=sys.stderr)
        return 2
    browser = find_browser()
    if not browser:
        print("No Chromium-compatible browser found; set PAPER_DEEP_DIVE_BROWSER or install Chromium.", file=sys.stderr)
        return 3
    pdf.parent.mkdir(parents=True, exist_ok=True)
    uri = "file://" + quote(str(html))
    command = [browser, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer", "--allow-file-access-from-files", f"--print-to-pdf={pdf}", uri]
    subprocess.run(command, cwd=paper_dir, check=True)
    print(html)
    print(pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
