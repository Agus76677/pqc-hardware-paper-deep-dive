#!/usr/bin/env python3
"""Validate an HTML paper note, local assets, provenance, bibliography, and PDF."""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from paper_common import read_json_yaml


class HTMLInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: set[str] = set()
        self.citations: set[str] = set()
        self.headings: list[str] = []
        self.title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "img" and values.get("src"):
            self.images.add(values["src"] or "")
        if "data-cite" in values:
            self.citations.update(re.findall(r"[A-Za-z0-9_.:-]+", values["data-cite"] or ""))
        if tag in {"h1", "h2", "h3"}:
            self.headings.append(tag)
        if tag == "title":
            self.title = True


def bib_keys(text: str) -> set[str]:
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", text))


def valid_pdf(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 512 and path.read_bytes()[:5] == b"%PDF-"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, required=True)
    parser.add_argument("--allow-missing-pdf", action="store_true")
    parser.add_argument("--allow-no-figures", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    paper_dir = args.paper_dir.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    required = ["article.html", "references.bib", "sources.yaml"]
    for name in required:
        if not (paper_dir / name).is_file():
            errors.append(f"missing required file: {name}")
    if errors:
        return _emit(args.json, errors, warnings)

    html_text = (paper_dir / "article.html").read_text(encoding="utf-8")
    if "{{" in html_text or "在此准确" in html_text or "删除所有写作提示" in html_text:
        errors.append("unfinished HTML template placeholders remain")
    inventory = HTMLInventory()
    try:
        inventory.feed(html_text)
    except Exception as exc:
        errors.append(f"invalid HTML: {exc}")
    if "<html" not in html_text.lower() or "<body" not in html_text.lower():
        errors.append("article.html must contain html and body elements")
    if not inventory.headings:
        errors.append("article.html has no article headings")
    for marker in ("【Paper】", "【Code】", "【Source】", "【Analysis】"):
        if marker not in html_text:
            warnings.append(f"fact marker is unused: {marker}")

    local_images = {src for src in inventory.images if not src.startswith(("http://", "https://", "data:"))}
    if not local_images and not args.allow_no_figures:
        errors.append("no local paper figures are referenced")
    for src in local_images:
        path = (paper_dir / src).resolve()
        if not path.is_file():
            errors.append(f"referenced image is missing: {src}")

    keys = bib_keys((paper_dir / "references.bib").read_text(encoding="utf-8"))
    missing_keys = inventory.citations - keys
    if missing_keys:
        errors.append("citation keys missing from references.bib: " + ", ".join(sorted(missing_keys)))
    if not keys:
        errors.append("references.bib contains no entries")

    try:
        manifest = read_json_yaml(paper_dir / "sources.yaml")
        if not manifest.get("paper", {}).get("title"):
            errors.append("sources.yaml is missing paper.title")
        if not manifest.get("sources"):
            errors.append("sources.yaml contains no sources")
        registered = {Path(item.get("path", "")).name for item in manifest.get("figures", [])}
        image_names = {Path(src).name for src in local_images}
        if image_names - registered:
            errors.append("figures missing provenance records: " + ", ".join(sorted(image_names - registered)))
        unverified = [item.get("id", "unknown") for item in manifest.get("sources", []) if not item.get("verified")]
        if unverified:
            warnings.append("unverified sources remain: " + ", ".join(unverified))
    except Exception as exc:
        errors.append(f"cannot read sources.yaml: {exc}")

    if not args.allow_missing_pdf and not valid_pdf(paper_dir / "article.pdf"):
        errors.append("missing or invalid PDF: article.pdf")
    return _emit(args.json, errors, warnings)


def _emit(as_json: bool, errors: list[str], warnings: list[str]) -> int:
    result = {"ok": not errors, "errors": errors, "warnings": warnings}
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        print("VALID" if result["ok"] else "INVALID")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
