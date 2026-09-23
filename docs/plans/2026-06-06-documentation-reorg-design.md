# Documentation Reorg Design

**Date**: 2026-06-06
**Status**: Approved (via brainstorming dialogue)

## Goal

Consolidate all documentation into a single `docs/` tree with a clear taxonomy,
kill the parallel `.claude/rules/` set (single source of truth), and trim
`CLAUDE.md` back toward ~80 lines. Root keeps only crucial info.

## Decisions (validated)

1. **Single home = `docs/`.** `.claude/rules/` is deleted; `CLAUDE.md` routes
   into `docs/`. No content duplication ("both places" rejected). Path-triggered
   auto-loading via glob frontmatter is given up — it was not reliably gating
   anyway (all rules loaded wholesale).
2. **A dedicated `docs/reference/` bucket** holds the deep manuals that are
   neither tool, design rationale, legacy, nor upgrade.
3. **`src/docs/` game-design drafts move to `docs/game-design/`** (option 1).
4. **`design/` is populated from existing sources only — no fabrication.**
   - `hddl.md` ← move `HDDL.md` nearly as-is.
   - `legacy-inductorhtn.md` ← distil/quote upstream `inductorHtnDocs/readme.md`.
   - `language-design.md` ← **empty stub** + `TODO:` (author to fill).
   - `online-htn-rulesets.md` ← **empty stub** + `TODO:` (author to fill).
5. **`CLAUDE.md` trimmed** to identity, build/test pointer, directory structure,
   Critical Rules, and a docs map. Bulky tables/sections move into `docs/`.

## Target layout

```
CLAUDE.md            (root, ~80 lines)
BUILD.md             (root)
license.md           (root)
docs/
  README.md          ← map of all docs
  TOOLS.md           ← index → tools/*
  DESIGN.md          ← index → design/*
  legacy/
    README.md        (⚠️ superseded banner)
    getting-started.md   ← inductorHtnDocs/gettingstarted.md
    engine-readme.md     ← inductorHtnDocs/readme.md
  upgrades/
    README.md
    ruleset-keywords.md      (consolidated from htn-syntax keyword sections)
    query-tracing.md         ← TRACE.md
    method-failure-tracking.md ← docs/method-failure-analysis.md
  tools/
    indhtn-repl.md  runtests.md  python-bindings.md
    gui.md          mcp-server.md  htn-components.md
  design/
    legacy-inductorhtn.md  language-design.md(stub)
    hddl.md                online-htn-rulesets.md(stub)
  reference/
    htn-syntax.md  prolog-reference.md  planner-internals.md
    component-system.md  authoring-rulesets.md  build-setup.md
    challenge-play-protocol.md
  game-design/
    GDD.md  htn-implementation-draft.md
    puzzle-ideas.md  combat-levels-ideas.md
  plans/             (unchanged)
```

## File mapping

| Source | Destination | Method |
|--------|-------------|--------|
| `inductorHtnDocs/gettingstarted.md` | `docs/legacy/getting-started.md` | git mv |
| `inductorHtnDocs/readme.md` | `docs/legacy/engine-readme.md` | git mv |
| `TRACE.md` | `docs/upgrades/query-tracing.md` | git mv |
| `docs/method-failure-analysis.md` | `docs/upgrades/method-failure-tracking.md` | git mv |
| `HDDL.md` | `docs/design/hddl.md` | git mv |
| `.claude/rules/htn-syntax.md` | `docs/reference/htn-syntax.md` | git mv (strip frontmatter) |
| `.claude/rules/prolog-reference.md` | `docs/reference/prolog-reference.md` | git mv |
| `.claude/rules/planner-internals.md` | `docs/reference/planner-internals.md` | git mv |
| `.claude/rules/component-system.md` | `docs/reference/component-system.md` | git mv |
| `.claude/rules/build-setup.md` | `docs/reference/build-setup.md` | git mv |
| `.claude/rules/challenge-play-protocol.md` | `docs/reference/challenge-play-protocol.md` | git mv |
| `.claude/rules/python-bindings.md` | `docs/tools/python-bindings.md` | git mv |
| `GENERATING_HTN_RULESETS.md` + `.claude/rules/crafting-rulesets.md` | `docs/reference/authoring-rulesets.md` | merge |
| `.claude/rules/gui-backend.md` + `gui-frontend.md` + `gui/README.md` | `docs/tools/gui.md` | merge |
| `.claude/rules/mcp-server.md` + `mcp-server/README.md` | `docs/tools/mcp-server.md` | merge |
| `src/docs/GDD.md` | `docs/game-design/GDD.md` | git mv |
| `src/docs/HTN_IMPLEMENTATION_DRAFT.md` | `docs/game-design/htn-implementation-draft.md` | git mv |
| `src/docs/PUZZLE_IDEAS.md` | `docs/game-design/puzzle-ideas.md` | git mv |
| `src/docs/COMBAT_LEVELS_IDEAS.md` | `docs/game-design/combat-levels-ideas.md` | git mv |

### Newly authored (reorg of existing documented content, not invention)
- `docs/README.md`, `docs/TOOLS.md`, `docs/DESIGN.md`, `docs/legacy/README.md`,
  `docs/upgrades/README.md`
- `docs/upgrades/ruleset-keywords.md` (parallel(), increase/decrease, typed
  params, anyOf/allOf — all already documented)
- `docs/tools/indhtn-repl.md`, `docs/tools/runtests.md`,
  `docs/tools/htn-components.md` (consolidated from CLAUDE.md tables +
  authoring guide)
- `docs/design/legacy-inductorhtn.md` (distilled from upstream readme)

### Stubs (author to fill — no source exists)
- `docs/design/language-design.md`
- `docs/design/online-htn-rulesets.md`

### Pointers left behind (discoverability anchors)
- `gui/README.md`, `mcp-server/README.md` → trimmed to a one-line link into
  `docs/tools/`.

## Cross-reference fixups
- Update every `.claude/rules/...` and `GENERATING_HTN_RULESETS.md` reference in
  `CLAUDE.md` and across the repo to the new `docs/...` paths.

## Not committed automatically
Work is staged in the working tree for review. Branching/commit left to the
author (current branch is feature work unrelated to docs).
```
