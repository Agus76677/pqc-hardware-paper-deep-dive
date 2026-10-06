#!/usr/bin/env python3
"""Download, inventory, render, crop, register, and verify paper figures."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tarfile
import tempfile
import urllib.request
from datetime import date
from pathlib import Path

from paper_common import executable, fail, read_json_yaml, run, slugify, write_json_yaml


IMAGE_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".webp", ".eps", ".svg")
INCLUDE_RE = re.compile(r"\\includegraphics(?:\[([^\]]*)\])?\{([^}]+)\}")
CAPTION_START_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\{")


def request_download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "paper-deep-dive-plugin/1.0"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def safe_extract_tar(bundle: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(bundle, "r:*") as archive:
        for member in archive.getmembers():
            if member.issym() or member.islnk():
                continue
            target = (destination / member.name).resolve()
            if root not in target.parents and target != root:
                raise RuntimeError(f"Unsafe archive path: {member.name}")
            archive.extract(member, destination)


def resolve_figure(tex_file: Path, source_dir: Path, requested: str) -> Path | None:
    roots = [tex_file.parent, source_dir]
    for root in roots:
        direct = (root / requested).resolve()
        if direct.is_file():
            return direct
        if direct.suffix:
            continue
        for extension in IMAGE_EXTENSIONS:
            candidate = direct.with_suffix(extension)
            if candidate.is_file():
                return candidate
    return None


def balanced_content(text: str, opening_brace: int) -> str:
    depth = 0
    escaped = False
    for index in range(opening_brace, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[opening_brace + 1 : index]
    return ""


def clean_caption(value: str) -> str:
    value = re.sub(r"\\label\{[^{}]*\}", "", value)
    for _ in range(4):
        value = re.sub(r"\\(?:textbf|textit|emph|small|footnotesize)\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", "", value)
    value = value.replace("{", "").replace("}", "").replace("~", " ")
    return " ".join(value.split())


def nearby_caption(text: str, match: re.Match[str]) -> str:
    forward_start = match.end()
    forward = CAPTION_START_RE.search(text, forward_start, min(len(text), forward_start + 5000))
    caption_match = forward
    if not caption_match:
        backward_start = max(0, match.start() - 2500)
        candidates = list(CAPTION_START_RE.finditer(text, backward_start, match.start()))
        caption_match = candidates[-1] if candidates else None
    if not caption_match:
        return ""
    return clean_caption(balanced_content(text, caption_match.end() - 1))


def inventory_source(source_dir: Path) -> list[dict]:
    inventory: list[dict] = []
    for tex_file in sorted(source_dir.rglob("*.tex")):
        try:
            text = tex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for index, match in enumerate(INCLUDE_RE.finditer(text), start=1):
            requested = match.group(2).strip()
            resolved = resolve_figure(tex_file, source_dir, requested)
            inventory.append(
                {
                    "id": f"{tex_file.stem}-{index}",
                    "tex_file": str(tex_file.relative_to(source_dir)),
                    "requested_path": requested,
                    "resolved_path": str(resolved.relative_to(source_dir)) if resolved and source_dir in resolved.parents else "",
                    "options": (match.group(1) or "").strip(),
                    "caption": nearby_caption(text, match),
                }
            )
    return inventory


def render_pdf(input_path: Path, output_path: Path, page: int, dpi: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stem = output_path.with_suffix("")
    renderer = executable("pdftocairo", "pdftoppm")
    if not renderer:
        fail("pdftocairo/pdftoppm is required; run install_dependencies.py first")
    if Path(renderer).name.lower().startswith("pdftocairo"):
        command = [renderer, "-f", str(page), "-l", str(page), "-singlefile", "-png", "-r", str(dpi), str(input_path), str(stem)]
    else:
        command = [renderer, "-f", str(page), "-l", str(page), "-singlefile", "-r", str(dpi), "-png", str(input_path), str(stem)]
    run(command)
    generated = stem.with_suffix(".png")
    if generated != output_path:
        generated.replace(output_path)


def crop_image(input_path: Path, output_path: Path, x: int, y: int, width: int, height: int) -> None:
    image_tool = executable("magick", "convert")
    if not image_tool:
        fail("ImageMagick is required; run install_dependencies.py first")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run([image_tool, str(input_path), "-crop", f"{width}x{height}+{x}+{y}", "+repage", str(output_path)])


def autocrop_image(input_path: Path, output_path: Path, fuzz: float, border: int) -> None:
    """Remove uniform white/near-white margins left by PDF or raster rendering."""
    image_tool = executable("magick", "convert")
    if not image_tool:
        fail("ImageMagick is required; run install_dependencies.py first")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run([image_tool, str(input_path), "-fuzz", f"{fuzz:g}%", "-trim", "+repage", "-bordercolor", "white", "-border", str(max(0, border)), str(output_path)])


def register_figure(args: argparse.Namespace) -> None:
    paper_dir = args.paper_dir.expanduser().resolve()
    figure_path = args.file.expanduser().resolve()
    try:
        relative = figure_path.relative_to(paper_dir)
    except ValueError:
        fail("Registered figure must be inside --paper-dir")
    if not figure_path.is_file():
        fail(f"Figure does not exist: {figure_path}")
    manifest_path = paper_dir / "sources.yaml"
    manifest = read_json_yaml(manifest_path)
    figures = [entry for entry in manifest.get("figures", []) if entry.get("path") != relative.as_posix()]
    figures.append(
        {
            "id": args.id or slugify(figure_path.stem),
            "path": relative.as_posix(),
            "paper_figure": args.paper_figure,
            "caption": args.caption,
            "source_id": args.source_id,
            "source_file": args.source_file,
            "crop": args.crop,
            "accessed": date.today().isoformat(),
        }
    )
    manifest["figures"] = figures
    write_json_yaml(manifest_path, manifest)
    print(f"registered: {relative.as_posix()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_source = subparsers.add_parser("download-source", help="Download and safely unpack arXiv source.")
    download_source.add_argument("--arxiv-id", required=True)
    download_source.add_argument("--workspace", type=Path, required=True)

    download_pdf = subparsers.add_parser("download-pdf", help="Download an arXiv PDF.")
    download_pdf.add_argument("--arxiv-id", required=True)
    download_pdf.add_argument("--output", type=Path, required=True)

    inventory = subparsers.add_parser("inventory", help="List includegraphics uses and nearby captions.")
    inventory.add_argument("--source-dir", type=Path, required=True)
    inventory.add_argument("--output", type=Path)

    render = subparsers.add_parser("render", help="Render one PDF page or PDF figure to PNG.")
    render.add_argument("--input", type=Path, required=True)
    render.add_argument("--output", type=Path, required=True)
    render.add_argument("--page", type=int, default=1)
    render.add_argument("--dpi", type=int, default=220)

    crop = subparsers.add_parser("crop", help="Crop a raster image using pixel coordinates.")
    crop.add_argument("--input", type=Path, required=True)
    crop.add_argument("--output", type=Path, required=True)
    crop.add_argument("--x", type=int, required=True)
    crop.add_argument("--y", type=int, required=True)
    crop.add_argument("--width", type=int, required=True)
    crop.add_argument("--height", type=int, required=True)
    autocrop = subparsers.add_parser("autocrop", help="Trim uniform white margins and add a small border.")
    autocrop.add_argument("--input", type=Path, required=True)
    autocrop.add_argument("--output", type=Path, required=True)
    autocrop.add_argument("--fuzz", type=float, default=3.0, help="Near-white tolerance in percent (default: 3).")
    autocrop.add_argument("--border", type=int, default=8, help="White border in pixels (default: 8).")

    register = subparsers.add_parser("register", help="Record figure provenance in sources.yaml.")
    register.add_argument("--paper-dir", type=Path, required=True)
    register.add_argument("--file", type=Path, required=True)
    register.add_argument("--id")
    register.add_argument("--paper-figure", required=True)
    register.add_argument("--caption", required=True)
    register.add_argument("--source-id", default="paper")
    register.add_argument("--source-file", default="")
    register.add_argument("--crop", default="")

    verify = subparsers.add_parser("verify", help="Check that local figure files are non-empty and readable.")
    verify.add_argument("--figures-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "download-source":
        workspace = args.workspace.expanduser().resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="paper-source-") as temporary:
            bundle = Path(temporary) / "source.bundle"
            request_download(f"https://arxiv.org/e-print/{args.arxiv_id}", bundle)
            source_dir = workspace / "source"
            if tarfile.is_tarfile(bundle):
                safe_extract_tar(bundle, source_dir)
            else:
                source_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundle, source_dir / "main.tex")
        print(source_dir)
        return 0
    if args.command == "download-pdf":
        request_download(f"https://arxiv.org/pdf/{args.arxiv_id}", args.output.expanduser().resolve())
        print(args.output.expanduser().resolve())
        return 0
    if args.command == "inventory":
        source_dir = args.source_dir.expanduser().resolve()
        data = inventory_source(source_dir)
        rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(args.output)
        else:
            print(rendered, end="")
        return 0
    if args.command == "render":
        render_pdf(args.input.expanduser().resolve(), args.output.expanduser().resolve(), args.page, args.dpi)
        print(args.output.expanduser().resolve())
        return 0
    if args.command == "crop":
        crop_image(
            args.input.expanduser().resolve(),
            args.output.expanduser().resolve(),
            args.x,
            args.y,
            args.width,
            args.height,
        )
        print(args.output.expanduser().resolve())
        return 0
    if args.command == "autocrop":
        autocrop_image(args.input.expanduser().resolve(), args.output.expanduser().resolve(), args.fuzz, args.border)
        print(args.output.expanduser().resolve())
        return 0
    if args.command == "register":
        register_figure(args)
        return 0
    if args.command == "verify":
        figures = [path for path in args.figures_dir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS]
        bad = [path for path in figures if path.stat().st_size < 128]
        for path in figures:
            print(f"{path}: {path.stat().st_size} bytes")
        if not figures:
            print("no figure files found")
            return 1
        if bad:
            print("invalid or empty figures: " + ", ".join(str(path) for path in bad))
            return 1
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
