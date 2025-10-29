#!/usr/bin/env python3
"""
Repository scanner for suspicious Python code.

Features:
- Detects common obfuscation patterns such as base64 + zlib + exec
- Flags risky constructs: exec/eval/compile/marshal
- Flags network calls and embedded domains/URLs
- Optional --decode attempts to safely decode base64+zlib payloads for preview

Usage:
  python tools/scan_repo.py --root . --decode

This tool DOES NOT execute any decoded payloads; it only previews strings.
"""
from __future__ import annotations

import argparse
import base64
import dataclasses
import os
import re
import sys
import textwrap
import zlib
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


@dataclasses.dataclass
class Finding:
    file_path: Path
    line_number: int
    kind: str
    snippet: str
    decoded_preview: Optional[str] = None

    def to_display(self, color: bool = True) -> str:
        rel = self.file_path
        header = f"[{self.kind}] {rel}:{self.line_number}"
        body = self.snippet.strip()
        if self.decoded_preview:
            preview = textwrap.indent(self.decoded_preview.rstrip(), prefix="    ")
            body = f"{body}\n  Decoded preview (first 30 lines):\n{preview}"
        return f"{header}\n  {body}\n"


OBFUSCATED_RGXS: List[Tuple[str, re.Pattern[str]]] = [
    (
        "B64_ZLIB_EXEC",
        re.compile(
            r"exec\s*\(\s*zlib\.decompress\(\s*base64\.b64decode\(\s*\"([A-Za-z0-9+/=]{40,})\"\s*\)\s*\)\s*\)"
        ),
    ),
    (
        "B64_ZLIB",
        re.compile(r"zlib\.decompress\(\s*base64\.b64decode\(\s*\"([A-Za-z0-9+/=]{40,})\"\s*\)\s*\)")
    ),
]

RISKY_RGXS: List[Tuple[str, re.Pattern[str]]] = [
    ("EXEC_CALL", re.compile(r"(?<![\w.])exec\s*\(")),
    ("EVAL_CALL", re.compile(r"(?<![\w.])eval\s*\(")),
    ("COMPILE_CALL", re.compile(r"(?<![\w.])compile\s*\(")),
    ("MARSHAL_LOADS", re.compile(r"marshal\s*\.\s*loads\s*\(")),
]

NETWORK_RGXS: List[Tuple[str, re.Pattern[str]]] = [
    ("REQUESTS_GET", re.compile(r"requests\s*\.\s*get\s*\(")),
    ("URL_IN_STRING", re.compile(r"https?://[\w\-._~:/?#\[\]@!$&'()*+,;=%]+")),
]


def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        # Skip common virtualenv or build folders
        parts = set(path.parts)
        if any(skip in parts for skip in {".venv", "venv", "build", "dist", "__pycache__"}):
            continue
        yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def try_decode_base64_zlib(b64_text: str) -> Optional[str]:
    try:
        raw = base64.b64decode(b64_text)
        decompressed = zlib.decompress(raw)
        text = decompressed.decode("utf-8", errors="replace")
        # Return first 30 lines to avoid dumping huge payloads
        lines = text.splitlines()
        head = "\n".join(lines[:30])
        if len(lines) > 30:
            head += "\n... (truncated)"
        return head
    except Exception:
        return None


def scan_file(path: Path, do_decode: bool) -> List[Finding]:
    findings: List[Finding] = []
    content = read_text(path)
    if not content:
        return findings

    # Prepare per-line lookup for line numbers
    line_offsets: List[int] = []
    start = 0
    for line in content.splitlines(True):  # keepends
        line_offsets.append(start)
        start += len(line)

    def line_number_from_index(idx: int) -> int:
        # Binary search could be used; linear is OK for small files
        line_no = 1
        for i, off in enumerate(line_offsets):
            if off > idx:
                break
            line_no = i + 1
        return line_no

    # Obfuscation patterns
    for kind, rgx in OBFUSCATED_RGXS:
        for m in rgx.finditer(content):
            idx = m.start()
            line_no = line_number_from_index(idx)
            snippet = content[max(0, idx - 60) : m.end() + 60]
            decoded_preview: Optional[str] = None
            if do_decode and m.groups():
                decoded_preview = try_decode_base64_zlib(m.group(1))
            findings.append(
                Finding(
                    file_path=path,
                    line_number=line_no,
                    kind=kind,
                    snippet=snippet,
                    decoded_preview=decoded_preview,
                )
            )

    # Risky constructs
    for kind, rgx in RISKY_RGXS:
        for m in rgx.finditer(content):
            idx = m.start()
            line_no = line_number_from_index(idx)
            snippet = content[max(0, idx - 40) : m.end() + 40]
            findings.append(Finding(file_path=path, line_number=line_no, kind=kind, snippet=snippet))

    # Network usage / URLs
    for kind, rgx in NETWORK_RGXS:
        for m in rgx.finditer(content):
            idx = m.start()
            line_no = line_number_from_index(idx)
            snippet = content[max(0, idx - 40) : m.end() + 40]
            findings.append(Finding(file_path=path, line_number=line_no, kind=kind, snippet=snippet))

    return findings


def scan_repo(root: Path, do_decode: bool) -> List[Finding]:
    all_findings: List[Finding] = []
    for file_path in iter_python_files(root):
        all_findings.extend(scan_file(file_path, do_decode))
    return all_findings


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a repository for suspicious Python patterns.")
    parser.add_argument("--root", type=str, default=str(Path.cwd()), help="Root directory to scan (default: CWD)")
    parser.add_argument("--decode", action="store_true", help="Attempt to decode base64+zlib payloads for preview")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Error: path does not exist: {root}", file=sys.stderr)
        return 2

    findings = scan_repo(root, args.decode)

    # Summarize and display
    if not findings:
        print("No suspicious patterns found.")
        return 0

    # Sort by file then line
    findings.sort(key=lambda f: (str(f.file_path), f.line_number))

    kinds_count: dict[str, int] = {}
    for f in findings:
        kinds_count[f.kind] = kinds_count.get(f.kind, 0) + 1

    print("Findings:")
    print("- total:", len(findings))
    print("- by kind:")
    for k, v in sorted(kinds_count.items()):
        print(f"  - {k}: {v}")
    print()

    for f in findings:
        print(f.to_display(color=not args.no_color))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
