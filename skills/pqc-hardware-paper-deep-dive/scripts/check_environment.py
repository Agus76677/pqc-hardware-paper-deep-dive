#!/usr/bin/env python3
"""Check the cross-platform HTML/Chromium/PDF asset toolchain."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from dataclasses import asdict, dataclass

from paper_common import executable


@dataclass
class Capability:
    name: str
    required: bool
    available: bool
    command: str | None
    detail: str


def first_line(command: str, *args: str) -> str:
    try:
        result = subprocess.run(
            [command, *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
        )
        return (result.stdout or "").splitlines()[0].strip()
    except Exception as exc:
        return str(exc)


def command_capability(name: str, required: bool, names: tuple[str, ...], args: tuple[str, ...]) -> Capability:
    command = executable(*names)
    return Capability(
        name=name,
        required=required,
        available=bool(command),
        command=command,
        detail=first_line(command, *args) if command else "not found on PATH",
    )


def tex_file_capability(name: str, filename: str, required: bool = True) -> Capability:
    kpsewhich = executable("kpsewhich")
    if not kpsewhich:
        return Capability(name, required, False, None, "kpsewhich not found")
    try:
        result = subprocess.run(
            [kpsewhich, filename],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
        )
        location = (result.stdout or "").strip()
        return Capability(name, required, result.returncode == 0 and bool(location), kpsewhich, location or "not found")
    except Exception as exc:
        return Capability(name, required, False, kpsewhich, str(exc))


def inspect_environment() -> list[Capability]:
    capabilities = [
        command_capability("PDF rasterizer", True, ("pdftocairo", "pdftoppm"), ("-v",)),
        command_capability("PDF metadata", True, ("pdfinfo",), ("-v",)),
        command_capability("ImageMagick", True, ("magick", "convert"), ("-version",)),
        command_capability("HTML PDF browser", True, ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome", "msedge"), ("--version",)),
        command_capability("Git", False, ("git",), ("--version",)),
    ]
    return capabilities


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--allow-missing-figure-tools",
        action="store_true",
        help="Treat Poppler and ImageMagick as optional when no figures need extraction.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    capabilities = inspect_environment()
    if args.allow_missing_figure_tools:
        for item in capabilities:
            if item.name in {"PDF rasterizer", "PDF metadata", "ImageMagick"}:
                item.required = False

    payload = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "ready": all(item.available for item in capabilities if item.required),
        "capabilities": [asdict(item) for item in capabilities],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in capabilities:
            status = "OK" if item.available else ("MISSING" if item.required else "OPTIONAL")
            print(f"[{status:8}] {item.name}: {item.detail}")
        print("READY" if payload["ready"] else "NOT READY")
    return 0 if payload["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
