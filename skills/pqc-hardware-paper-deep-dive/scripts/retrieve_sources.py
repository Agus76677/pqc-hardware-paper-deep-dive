#!/usr/bin/env python3
"""Resolve paper metadata and maintain sources.yaml plus references.bib."""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from paper_common import bibtex_escape, bibtex_url_escape, read_json_yaml, unique_preserving_order, write_json_yaml


USER_AGENT = "paper-deep-dive-plugin/1.0 (metadata retrieval)"
AUTO_BEGIN = "% BEGIN PAPER-DEEP-DIVE AUTO SOURCES"
AUTO_END = "% END PAPER-DEEP-DIVE AUTO SOURCES"


def fetch_json(url: str, timeout: int) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def fetch_text(url: str, timeout: int) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def normalize_title(value: str) -> str:
    return re.sub(r"\W+", " ", value.lower(), flags=re.UNICODE).strip()


def parse_arxiv_id(value: str) -> str:
    match = re.search(r"(?:arxiv\.org/(?:abs|pdf)/)?([a-z-]+/\d{7}|\d{4}\.\d{4,5})(?:v\d+)?", value, re.I)
    return match.group(1) if match else value.strip()


def arxiv_metadata(arxiv_id: str, timeout: int) -> dict:
    clean_id = parse_arxiv_id(arxiv_id)
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": clean_id})
    root = ET.fromstring(fetch_text(url, timeout))
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    entry = root.find("atom:entry", ns)
    if entry is None:
        raise RuntimeError(f"arXiv returned no entry for {clean_id}")
    title = " ".join((entry.findtext("atom:title", default="", namespaces=ns)).split())
    authors = [
        " ".join((node.findtext("atom:name", default="", namespaces=ns)).split())
        for node in entry.findall("atom:author", ns)
    ]
    published = entry.findtext("atom:published", default="", namespaces=ns)
    doi = entry.findtext("arxiv:doi", default="", namespaces=ns)
    journal_ref = entry.findtext("arxiv:journal_ref", default="", namespaces=ns)
    return {
        "title": title,
        "authors": authors,
        "year": published[:4],
        "venue": journal_ref,
        "arxiv_id": clean_id,
        "doi": doi,
        "url": f"https://arxiv.org/abs/{clean_id}",
        "verified": True,
    }


def crossref_item_to_metadata(item: dict) -> dict:
    title_values = item.get("title") or []
    title = " ".join(title_values[0].split()) if title_values else ""
    authors = []
    for author in item.get("author") or []:
        name = " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part)
        if name:
            authors.append(name)
    date_parts = ((item.get("published-print") or item.get("published-online") or item.get("issued") or {}).get("date-parts") or [[]])[0]
    year = str(date_parts[0]) if date_parts else ""
    containers = item.get("container-title") or []
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": containers[0] if containers else "",
        "doi": item.get("DOI", ""),
        "url": item.get("URL", ""),
        "verified": True,
    }


def crossref_doi_metadata(doi: str, timeout: int) -> dict:
    encoded = urllib.parse.quote(doi.strip(), safe="")
    payload = fetch_json(f"https://api.crossref.org/works/{encoded}", timeout)
    return crossref_item_to_metadata(payload["message"])


def crossref_title_metadata(title: str, timeout: int) -> tuple[dict, float]:
    query = urllib.parse.urlencode({"query.bibliographic": title, "rows": 5, "select": "DOI,title,author,issued,published-print,published-online,container-title,URL"})
    payload = fetch_json(f"https://api.crossref.org/works?{query}", timeout)
    candidates = payload.get("message", {}).get("items", [])
    if not candidates:
        raise RuntimeError(f"Crossref returned no candidates for title: {title}")
    scored = []
    for item in candidates:
        metadata = crossref_item_to_metadata(item)
        score = SequenceMatcher(None, normalize_title(title), normalize_title(metadata["title"])).ratio()
        scored.append((score, metadata))
    score, metadata = max(scored, key=lambda pair: pair[0])
    return metadata, score


def author_surnames(authors: list[str]) -> set[str]:
    return {
        re.sub(r"\W+", "", author.split()[-1].lower(), flags=re.UNICODE)
        for author in authors
        if author.split()
    }


def title_candidate_is_confirmed(existing: dict, candidate: dict, score: float) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    corroborating_fields = 0
    if score < 0.9:
        reasons.append(f"title similarity is only {score:.2f}")
    existing_year = str(existing.get("year") or "")
    candidate_year = str(candidate.get("year") or "")
    if existing_year:
        corroborating_fields += 1
        if not candidate_year or candidate_year != existing_year:
            reasons.append(f"year conflicts: expected {existing_year}, candidate {candidate_year or 'unknown'}")
    existing_authors = existing.get("authors") or []
    if existing_authors:
        corroborating_fields += 1
        if not (author_surnames(existing_authors) & author_surnames(candidate.get("authors") or [])):
            reasons.append("candidate authors do not overlap the known authors")
    if corroborating_fields == 0:
        reasons.append("no known author or year is available to corroborate the title")
    return not reasons, reasons


def merge_metadata(base: dict, incoming: dict) -> dict:
    result = dict(base)
    for key, value in incoming.items():
        if value and (not result.get(key) or key in {"verified"}):
            result[key] = value
    result["authors"] = unique_preserving_order([*(base.get("authors") or []), *(incoming.get("authors") or [])])
    return result


def source_entry(source_id: str, source_type: str, title: str, url: str, version: str = "", verified: bool = False) -> dict:
    return {
        "id": source_id,
        "type": source_type,
        "title": title,
        "url": url,
        "accessed": date.today().isoformat(),
        "version": version,
        "supports": [],
        "verified": verified,
    }


def merge_source(previous: dict | None, current: dict) -> dict:
    if not previous:
        return current
    merged = dict(previous)
    for key, value in current.items():
        if value not in (None, "", []):
            merged[key] = value
    merged["supports"] = unique_preserving_order(
        [*(previous.get("supports") or []), *(current.get("supports") or [])]
    )
    merged["verified"] = bool(previous.get("verified") or current.get("verified"))
    return merged


def bib_entry_for_paper(metadata: dict) -> str:
    fields = [
        f"  title = {{{bibtex_escape(metadata.get('title', 'Primary paper'))}}}",
    ]
    authors = metadata.get("authors") or []
    if authors:
        fields.append(f"  author = {{{bibtex_escape(' and '.join(authors))}}}")
    if metadata.get("year"):
        fields.append(f"  year = {{{bibtex_escape(str(metadata['year']))}}}")
    if metadata.get("venue"):
        fields.append(f"  journaltitle = {{{bibtex_escape(metadata['venue'])}}}")
    if metadata.get("doi"):
        fields.append(f"  doi = {{{bibtex_url_escape(metadata['doi'])}}}")
    if metadata.get("arxiv_id"):
        fields.extend(
            [
                "  archiveprefix = {arXiv}",
                f"  eprint = {{{bibtex_escape(metadata['arxiv_id'])}}}",
                "  eprinttype = {arxiv}",
            ]
        )
    if metadata.get("url"):
        fields.append(f"  url = {{{bibtex_url_escape(metadata['url'])}}}")
        fields.append(f"  urldate = {{{date.today().isoformat()}}}")
    return "@article{paper,\n" + ",\n".join(fields) + "\n}"


def bib_entry_for_source(entry: dict) -> str:
    key = re.sub(r"[^a-zA-Z0-9_-]+", "-", entry["id"]).strip("-") or "source"
    fields = [f"  title = {{{bibtex_escape(entry['title'])}}}"]
    if entry.get("url"):
        fields.append(f"  url = {{{bibtex_url_escape(entry['url'])}}}")
    if entry.get("version"):
        fields.append(f"  version = {{{bibtex_escape(entry['version'])}}}")
    if entry.get("accessed"):
        fields.append(f"  urldate = {{{bibtex_escape(entry['accessed'])}}}")
    return f"@online{{{key},\n" + ",\n".join(fields) + "\n}"


def update_bibliography(path: Path, metadata: dict, entries: list[dict]) -> None:
    generated = [bib_entry_for_paper(metadata)]
    generated.extend(bib_entry_for_source(entry) for entry in entries if entry.get("id") != "paper")
    block = AUTO_BEGIN + "\n\n" + "\n\n".join(generated) + "\n\n" + AUTO_END
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(re.escape(AUTO_BEGIN) + r".*?" + re.escape(AUTO_END), re.S)
    if pattern.search(existing):
        rendered = pattern.sub(block, existing)
    else:
        rendered = (existing.rstrip() + "\n\n" + block + "\n").lstrip()
    path.write_text(rendered, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, required=True)
    identity = parser.add_mutually_exclusive_group()
    identity.add_argument("--arxiv-id")
    identity.add_argument("--doi")
    identity.add_argument("--title")
    parser.add_argument("--accept-best", action="store_true", help="Accept a low-confidence title match.")
    parser.add_argument("--code-url")
    parser.add_argument("--code-version", default="")
    parser.add_argument("--project-url")
    parser.add_argument("--dataset-url")
    parser.add_argument(
        "--document",
        action="append",
        default=[],
        metavar="TITLE=URL",
        help="Add another official or reliable source.",
    )
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paper_dir = args.paper_dir.expanduser().resolve()
    paper_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = paper_dir / "sources.yaml"
    manifest = read_json_yaml(manifest_path)
    metadata = manifest.get("paper") or {}
    confidence = None

    try:
        if args.arxiv_id:
            metadata = merge_metadata(metadata, arxiv_metadata(args.arxiv_id, args.timeout))
        elif args.doi:
            metadata = merge_metadata(metadata, crossref_doi_metadata(args.doi, args.timeout))
        elif args.title:
            resolved, confidence = crossref_title_metadata(args.title, args.timeout)
            confirmed, reasons = title_candidate_is_confirmed(metadata, resolved, confidence)
            if not confirmed and not args.accept_best:
                print("title search found a candidate but could not verify paper identity:")
                print(json.dumps(resolved, ensure_ascii=False, indent=2))
                for reason in reasons:
                    print(f"- {reason}")
                print("Provide arXiv/DOI/PDF, or verify this candidate and re-run with --accept-best.")
                return 1
            resolved["verified"] = bool(confirmed or args.accept_best)
            metadata = merge_metadata(metadata, resolved)
    except (urllib.error.URLError, TimeoutError, ET.ParseError, KeyError, RuntimeError) as exc:
        print(f"metadata retrieval failed: {exc}")
        print("No uncertain metadata was written. Provide a PDF, arXiv ID, DOI, or verified links.")
        return 1

    existing = {entry.get("id"): entry for entry in manifest.get("sources", []) if entry.get("id")}
    paper_url = metadata.get("url", "")
    existing["paper"] = merge_source(
        existing.get("paper"),
        source_entry(
            "paper",
            "paper",
            metadata.get("title", "Primary paper"),
            paper_url,
            verified=bool(metadata.get("verified")),
        ),
    )
    extras = [
        ("code", "code", "Official code repository", args.code_url, args.code_version),
        ("project", "project", "Official project page", args.project_url, ""),
        ("dataset", "dataset", "Official dataset", args.dataset_url, ""),
    ]
    for source_id, source_type, title, url, version in extras:
        if url:
            existing[source_id] = merge_source(
                existing.get(source_id), source_entry(source_id, source_type, title, url, version, False)
            )
    for index, item in enumerate(args.document, start=1):
        if "=" not in item:
            print(f"invalid --document value: {item!r}; expected TITLE=URL")
            return 2
        title, url = item.split("=", 1)
        source_id = f"document-{index}"
        existing[source_id] = merge_source(
            existing.get(source_id),
            source_entry(source_id, "documentation", title.strip(), url.strip(), verified=False),
        )

    entries = list(existing.values())
    manifest.update(
        {
            "schema_version": 1,
            "generated_at": date.today().isoformat(),
            "paper": metadata,
            "sources": entries,
            "figures": manifest.get("figures", []),
        }
    )
    write_json_yaml(manifest_path, manifest)
    update_bibliography(paper_dir / "references.bib", metadata, entries)
    print(f"updated: {manifest_path}")
    print(f"updated: {paper_dir / 'references.bib'}")
    if confidence is not None:
        print(f"title match confidence: {confidence:.2f}")
    unverified = [entry["id"] for entry in entries if not entry.get("verified")]
    if unverified:
        print("review and verify these source entries before finalizing: " + ", ".join(unverified))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
