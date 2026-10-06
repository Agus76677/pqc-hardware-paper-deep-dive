#!/usr/bin/env python3
"""Shared helpers for the paper deep-dive command-line tools."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, Sequence


WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class ToolError(RuntimeError):
    """Raised when a helper tool cannot complete its work."""


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def executable(*names: str) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    if check and result.returncode != 0:
        rendered = " ".join(command)
        details = f"\n{result.stdout}" if capture and result.stdout else ""
        raise ToolError(f"Command failed ({result.returncode}): {rendered}{details}")
    return result


def slugify(value: str, *, limit: int = 96) -> str:
    """Create a Unicode-safe, cross-platform directory name."""
    value = unicodedata.normalize("NFKC", value).strip().lower()
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "-", value)
    value = re.sub(r"[^\w.-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"[-_.]{2,}", "-", value).strip(" .-_")
    value = value[:limit].rstrip(" .-_") or "paper-deep-dive"
    if value.upper() in WINDOWS_RESERVED_NAMES:
        value = f"paper-{value}"
    return value


def yaml_double_quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def bibtex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "_": r"\_",
    }
    return "".join(replacements.get(char, char) for char in value)


def bibtex_url_escape(value: str) -> str:
    return value.replace("{", r"\{").replace("}", r"\}")


def read_json_yaml(path: Path) -> dict:
    """Read sources.yaml, which intentionally uses JSON (a valid YAML subset)."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": 1, "paper": {}, "sources": [], "figures": []}
    except json.JSONDecodeError as exc:
        raise ToolError(
            f"{path} is not in the plugin's JSON-compatible YAML format: {exc}"
        ) from exc


def write_json_yaml(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique_preserving_order(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def fail(message: str, code: int = 2) -> "None":
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def is_admin() -> bool:
    if os.name == "nt":
        try:
            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return hasattr(os, "geteuid") and os.geteuid() == 0
