#!/usr/bin/env python3
"""Detect the host package manager and install the paper/PDF toolchain."""

from __future__ import annotations

import argparse
import os
import platform
import shlex
import sys
from dataclasses import dataclass

from check_environment import inspect_environment
from paper_common import executable, is_admin, run


@dataclass
class InstallPlan:
    manager: str
    commands: list[list[str]]
    notes: list[str]


def detect_manager(preferred: str | None = None) -> str | None:
    if preferred:
        return preferred if executable(preferred) else None
    system = platform.system()
    if system == "Linux" and executable("apt-get"):
        return "apt-get"
    if system == "Darwin" and executable("brew"):
        return "brew"
    if system == "Windows":
        if executable("winget"):
            return "winget"
        if executable("choco"):
            return "choco"
    return None


def build_plan(manager: str) -> InstallPlan:
    if manager == "apt-get":
        prefix = [] if is_admin() else ["sudo"]
        packages = [
            "poppler-utils",
            "imagemagick",
            "fonts-noto-cjk",
            "chromium",
        ]
        return InstallPlan(
            manager,
            [prefix + ["apt-get", "update"], prefix + ["apt-get", "install", "-y", *packages]],
            ["apt may request administrator credentials through sudo."],
        )
    if manager == "brew":
        return InstallPlan(
            manager,
            [
                ["brew", "install", "poppler", "imagemagick"],
                ["brew", "install", "--cask", "font-noto-serif-cjk-sc", "chromium"],
            ],
            ["Restart the shell if browser or font binaries are not immediately on PATH."],
        )
    if manager == "winget":
        ids = [
            "oschwartz10612.Poppler",
            "ImageMagick.ImageMagick",
            "Google.Chrome",
        ]
        commands = [
            [
                "winget",
                "install",
                "--id",
                package_id,
                "--exact",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ]
            for package_id in ids
        ]
        return InstallPlan(
            manager,
            commands,
            [
                "Open a new terminal after installation so PATH changes take effect.",
            ],
        )
    if manager == "choco":
        return InstallPlan(
            manager,
            [["choco", "install", "-y", "poppler", "imagemagick", "googlechrome"]],
            [
                "Run the terminal as Administrator if Chocolatey requests elevation.",
            ],
        )
    raise ValueError(f"Unsupported package manager: {manager}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Execute the installation plan.")
    parser.add_argument("--yes", action="store_true", help="Skip this script's confirmation prompt.")
    parser.add_argument("--manager", choices=["apt-get", "brew", "winget", "choco"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    missing = [item.name for item in inspect_environment() if item.required and not item.available]
    if not missing:
        print("Environment is already ready; no packages need installation.")
        return 0

    manager = detect_manager(args.manager)
    if not manager:
        print(
            "No supported package manager was detected. Install Chromium, Poppler, ImageMagick, "
            "and Noto CJK fonts manually.",
            file=sys.stderr,
        )
        return 2
    plan = build_plan(manager)
    print("Missing capabilities: " + ", ".join(missing))
    print(f"Detected package manager: {manager}")
    for command in plan.commands:
        print("  " + " ".join(shlex.quote(part) for part in command))
    for note in plan.notes:
        print(f"note: {note}")

    if not args.apply:
        print("Dry run only. Re-run with --apply to install these dependencies.")
        return 0
    if not args.yes:
        answer = input("Install the listed system dependencies? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Installation cancelled.")
            return 1

    environment = os.environ.copy()
    if platform.system() == "Darwin":
        environment.setdefault("HOMEBREW_NO_AUTO_UPDATE", "1")
    for command in plan.commands:
        run(command)

    remaining = [item.name for item in inspect_environment() if item.required and not item.available]
    if remaining:
        print(
            "Installation commands completed, but these capabilities are still unavailable: "
            + ", ".join(remaining),
            file=sys.stderr,
        )
        print("Restart the terminal, then run check_environment.py again.", file=sys.stderr)
        return 1
    print("Environment is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
