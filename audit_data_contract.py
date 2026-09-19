#!/usr/bin/env python3
"""
COMPLETE DATA CONTRACT AUDIT - Trace full data flow from capture to dashboard.

This script inspects the actual implementation at every stage of the pipeline.
It is read-only (no code modification).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
ENGINE = ROOT / "network-engine"
DASH = ROOT / "dashboard"

SKIP_DIRS = {".git", ".venv", "node_modules", ".next", "public", "test-results", "__pycache__"}

def section(title):
    print("\n" + "=" * 90)
    print("  " + title)
    print("=" * 90)

def walk_files(root: Path):
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        yield f

def find_mock_patterns(root: Path):
    """Search for mock/dummy/sample/demo/fake/random/hardcoded/fallback/static patterns."""
    patterns = [
        r"\bmock\b", r"\bdummy\b", r"\bsample\b", r"\bdemo\b", r"\bfake\b",
        r"Math\.random", r"random\.rand", r"hardcod", r"fallback", r"static",
        r"seed", r"generated\s+traffic", r"fake\s+device", r"demo\s+data",
    ]
    section("SEARCH FOR MOCK/DUMMY/FAKE/RANDOM/HARDCODED DATA")
    hits = []
    for f in walk_files(root):
        if f.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".sql"}:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                start = max(0, m.start() - 100)
                end = min(len(text), m.end() + 100)
                ctx = text[start:end].replace("\n", "\\n")
                hits.append((str(f.relative_to(root)), pat, ctx))
    if not hits:
        print("  (no hits found)")
    for fname, pat, ctx in hits[:300]:
        print(f"  [{pat}] {fname}\n      ...{ctx}...")
    if len(hits) > 300:
        print(f"  ... and {len(hits)-300} more hits suppressed")

def list_module_files(root: Path, label: str):
    section(label)
    for f in walk_files(root):
        if f.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".sql"}:
            print(f"  {f.relative_to(root)}")

if __name__ == "__main__":
    list_module_files(ENGINE, "ENGINE MODULE FILES")
    list_module_files(DASH, "DASHBOARD MODULE FILES")
    find_mock_patterns(ROOT)