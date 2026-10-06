#!/usr/bin/env python3
"""Create a self-contained output directory for one paper."""

from __future__ import annotations

import argparse
import json
from html import escape
from datetime import date
from pathlib import Path

from paper_common import bibtex_escape, bibtex_url_escape, fail, skill_root, slugify


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    parser.add_argument("--name", help="User-selected output directory name (highest priority).")
    parser.add_argument("--abbreviation", help="Official paper abbreviation.")
    parser.add_argument("--title", required=True, help="Original paper title.")
    parser.add_argument("--article-title", help="Chinese deep-dive title.")
    parser.add_argument("--author", default="Paper Deep Dive", help="Deep-dive author.")
    parser.add_argument("--paper-author", action="append", default=[])
    parser.add_argument("--year", default="")
    parser.add_argument("--venue", default="")
    parser.add_argument("--arxiv-id", default="")
    parser.add_argument("--doi", default="")
    parser.add_argument("--paper-url", default="")
    parser.add_argument("--code-url", default="")
    parser.add_argument("--project-url", default="")
    parser.add_argument("--dataset-url", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Create only missing files when the target directory already exists.",
    )
    return parser.parse_args()


def replace_template(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def write_if_allowed(path: Path, content: str, resume: bool) -> None:
    if path.exists():
        if resume:
            return
        fail(f"Refusing to overwrite existing file: {path}")
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    directory_seed = args.name or args.abbreviation or args.title
    paper_name = slugify(directory_seed)
    target = args.output_root.expanduser().resolve() / paper_name
    if target.exists() and any(target.iterdir()) and not args.resume:
        fail(f"Target is not empty: {target}. Use --resume to preserve existing files.")

    target.mkdir(parents=True, exist_ok=True)
    (target / "figures").mkdir(exist_ok=True)
    (target / "tables").mkdir(exist_ok=True)
    (target / "build").mkdir(exist_ok=True)

    today = date.today().isoformat()
    article_title = args.article_title or f"{args.title} 论文深度解读"
    tags = ["paper deep dive", "post-quantum cryptography hardware", *args.tag]
    paper_authors = ", ".join(args.paper_author)
    values = {
        "ARTICLE_TITLE_HTML": escape(article_title),
        "PAPER_TITLE_HTML": escape(args.title),
        "AUTHOR_HTML": escape(args.author),
        "DATE_HTML": escape(today),
        "PAPER_AUTHORS_HTML": escape(paper_authors or "Unknown"),
        "YEAR_HTML": escape(args.year),
        "PAPER_URL_HTML": escape(args.paper_url),
        "CODE_URL_HTML": escape(args.code_url),
        "PROJECT_URL_HTML": escape(args.project_url),
        "DATASET_URL_HTML": escape(args.dataset_url),
        "TAGS_HTML": escape(", ".join(tags)),
        "TAGS_INLINE_HTML": escape(" · ".join(tags)),
        "PAPER_LINK_HTML": f'<a href="{escape(args.paper_url)}">{escape(args.paper_url)}</a>' if args.paper_url else "未提供",
        "LINKS_HTML": " · ".join(f'<a href="{escape(url)}">{label}</a>' for label, url in (("Code", args.code_url), ("Project", args.project_url), ("Dataset", args.dataset_url)) if url) or "未提供",
        "PAPER_TITLE_BIB": bibtex_escape(args.title),
        "PAPER_AUTHORS_BIB": bibtex_escape(" and ".join(args.paper_author)),
        "YEAR_BIB": bibtex_escape(args.year),
        "PAPER_URL_BIB": bibtex_url_escape(args.paper_url),
        "ACCESS_DATE_BIB": today,
    }

    assets = skill_root() / "assets"
    for source, destination in (
        (assets / "templates" / "article.html", target / "article.html"),
        (assets / "templates" / "references.bib", target / "references.bib"),
    ):
        rendered = replace_template(source.read_text(encoding="utf-8"), values)
        write_if_allowed(destination, rendered, args.resume)

    source_entries = []
    for source_id, source_type, title, url in (
        ("paper", "paper", args.title, args.paper_url),
        ("code", "code", "Official code repository", args.code_url),
        ("project", "project", "Official project page", args.project_url),
        ("dataset", "dataset", "Official dataset", args.dataset_url),
    ):
        if url or source_id == "paper":
            source_entries.append(
                {
                    "id": source_id,
                    "type": source_type,
                    "title": title,
                    "url": url,
                    "accessed": today,
                    "version": "",
                    "supports": ["metadata"],
                    "verified": False,
                }
            )
    sources = {
        "schema_version": 1,
        "generated_at": today,
        "paper": {
            "title": args.title,
            "authors": args.paper_author,
            "year": args.year,
            "venue": args.venue,
            "arxiv_id": args.arxiv_id,
            "doi": args.doi,
            "url": args.paper_url,
        },
        "sources": source_entries,
        "figures": [],
    }
    sources_path = target / "sources.yaml"
    if not sources_path.exists() or not args.resume:
        write_if_allowed(
            sources_path,
            json.dumps(sources, ensure_ascii=False, indent=2) + "\n",
            args.resume,
        )

    theme = assets / "html-theme" / "theme.css"
    if theme.is_file() and not (target / "theme.css").exists():
        (target / "theme.css").write_text(theme.read_text(encoding="utf-8"), encoding="utf-8")

    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
