#!/usr/bin/env python3
"""docs_lint.py — keep documentation honest about the code.

Mechanically checks that what the docs claim still exists in the code:

  - MCP tool names documented in docs/tools/mcp-server.md          vs server.py
  - Flask endpoints documented in docs/tools/gui.md                vs app.py
  - Python binding methods documented in docs/tools/python-bindings.md vs indhtnpy.py
  - htn_components CLI commands documented in docs/tools/htn-components.md vs cli.py

This catches the exact rot class that bit the 2025-12 doc validation pass:
documented-but-nonexistent API (e.g. a phantom `HtnQuery`), missing endpoints,
renamed tools.

Severity model:
  BROKEN  (documented but does NOT exist in code)  -> non-zero exit. A lie to readers.
  MISSING (exists in code but NOT documented)       -> warning, exit stays 0.

Run:  python scripts/docs_lint.py
CI:   add to your test job; non-zero exit fails the build.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        print(f"  ! source not found: {rel}", file=sys.stderr)
        return ""
    return p.read_text()


# ---- extractors: ACTUAL surfaces (from code) -------------------------------

def actual_mcp_tools() -> set[str]:
    # _HANDLERS registry is authoritative for dispatchable tools.
    src = read("mcp-server/indhtn_mcp/server.py")
    block = src.split("_HANDLERS", 1)[-1]
    return set(re.findall(r'"(indhtn_[a-z_]+)"\s*:', block))


def actual_flask_routes() -> set[str]:
    src = read("gui/backend/app.py")
    routes = re.findall(r"@app\.route\(\s*['\"]([^'\"]+)['\"]", src)
    return {normalize_route(r) for r in routes}


def actual_binding_methods() -> set[str]:
    src = read("src/Python/indhtnpy.py")
    # methods of HtnPlanner (4-space indented defs)
    return set(re.findall(r"^\s{4}def ([A-Za-z_]\w*)\s*\(", src, re.M))


def actual_cli_commands() -> set[str]:
    src = read("src/Python/htn_components/cli.py")
    return set(re.findall(r"add_parser\(\s*['\"]([a-z0-9-]+)['\"]", src))


# ---- extractors: DOCUMENTED tokens (from docs) -----------------------------

def strip_code_fences(doc: str) -> str:
    # remove ```...``` blocks: they hold illustrative templates, not claims
    return re.sub(r"```.*?```", "", doc, flags=re.S)


def normalize_route(r: str) -> str:
    # collapse <param> path segments so docs may name them anything
    return re.sub(r"<[^>]+>", "<>", r.rstrip("/")) or "/"


# tokens that match a pattern but are not actually a documented surface claim
IGNORE_MCP = {"indhtn_mcp"}  # the package name, not a tool


def documented_mcp_tools(doc: str) -> set[str]:
    return set(re.findall(r"\b(indhtn_[a-z_]+)\b", doc)) - IGNORE_MCP


def documented_flask_routes(doc: str) -> set[str]:
    # routes are claimed in the endpoint table (prose); code fences hold
    # add-an-endpoint templates like /api/new/endpoint — exclude them.
    raw = re.findall(r"(/api/[A-Za-z0-9/_<>:-]+|/health)", strip_code_fences(doc))
    return {normalize_route(r) for r in raw}


def documented_binding_methods(doc: str, actual: set[str]) -> set[str]:
    # backticked CamelCase identifiers used as calls: `SomeMethod(`
    cand = set(re.findall(r"`([A-Z][A-Za-z0-9_]+)\(", doc))
    cand |= set(re.findall(r"^- `([A-Z][A-Za-z0-9_]+)\(", doc, re.M))
    # only judge tokens that *look like* binding methods; ignore class/ctor names
    ignore = {"HtnPlanner"}
    return {c for c in cand if c not in ignore}


def documented_cli_commands(doc: str, actual: set[str]) -> set[str]:
    # only consider tokens that are real commands or look like them; compare to actual
    toks = set(re.findall(r"^\s*([a-z][a-z-]+)\b", doc, re.M))
    # restrict to plausible command words to limit noise: those in actual OR
    # appearing right before a description with two+ spaces in a code block line
    explicit = set(re.findall(r"^\s*([a-z][a-z-]+)\s{2,}#", doc, re.M))
    return (toks & actual) | explicit


# ---- check driver ----------------------------------------------------------

def check(label, doc_rel, actual, documented, *, judge_missing=True):
    broken = sorted(documented - actual)
    missing = sorted(actual - documented)
    status = "OK"
    if broken:
        status = "BROKEN"
    print(f"\n[{label}] {doc_rel}  ({len(actual)} in code, {len(documented)} documented) -> {status}")
    for b in broken:
        print(f"  BROKEN  documented but not in code: {b}")
    if judge_missing:
        for m in missing:
            print(f"  missing  in code but not documented: {m}")
    return len(broken)


LINE_REF = re.compile(r'[A-Za-z_][\w]*\.(?:cpp|h|py|js|jsx):~?\d+|~line \d+')
# active docs that describe current code — line numbers here rot on every edit.
LINE_REF_DIRS = ["docs/reference", "docs/tools", "docs/upgrades", "docs/design"]


def check_no_line_refs() -> int:
    """file:line citations rot the instant code is edited. Cite symbols instead."""
    hits = []
    for d in LINE_REF_DIRS:
        for p in sorted((ROOT / d).rglob("*.md")):
            for i, line in enumerate(p.read_text().splitlines(), 1):
                for m in LINE_REF.finditer(line):
                    hits.append((p.relative_to(ROOT), i, m.group(0)))
    print(f"\n[line-number refs] {', '.join(LINE_REF_DIRS)} -> "
          f"{'BROKEN' if hits else 'OK'}")
    for rel, i, tok in hits:
        print(f"  BROKEN  {rel}:{i} cites a line number ({tok}) — use a symbol name")
    return len(hits)


def main() -> int:
    mcp_doc = read("docs/tools/mcp-server.md")
    gui_doc = read("docs/tools/gui.md")
    py_doc = read("docs/tools/python-bindings.md")
    cli_doc = read("docs/tools/htn-components.md")

    a_mcp = actual_mcp_tools()
    a_routes = actual_flask_routes()
    a_bind = actual_binding_methods()
    a_cli = actual_cli_commands()

    errors = 0
    errors += check("MCP tools", "docs/tools/mcp-server.md",
                    a_mcp, documented_mcp_tools(mcp_doc))
    errors += check("Flask endpoints", "docs/tools/gui.md",
                    a_routes, documented_flask_routes(gui_doc))
    errors += check("Python bindings", "docs/tools/python-bindings.md",
                    a_bind, documented_binding_methods(py_doc, a_bind),
                    judge_missing=False)
    errors += check("Components CLI", "docs/tools/htn-components.md",
                    a_cli, documented_cli_commands(cli_doc, a_cli))
    errors += check_no_line_refs()

    print()
    if errors:
        print(f"docs-lint FAILED: {errors} broken reference(s) — docs claim "
              f"things the code does not have.")
        return 1
    print("docs-lint OK: no documented-but-nonexistent references.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
