# CLAUDE.md

InductorHTN: a lightweight HTN planner for C++ and Python. SHOP model, memory-constrained,
stackless execution. This fork is used to write game-AI rulesets for a cooperative puzzle game.

Always enter the Python venv first. On Windows: `source .venv/Scripts/activate`.

## Writing HTN rulesets (.htn)

**Use the `htn-author` skill** for any `.htn` work. The short version:

- **The language:** `docs/reference/language.md`. It is test-backed (`python scripts/htn_doctest.py
  docs/reference/language.md`). This is not SWI-Prolog: `\+`, `\=` and `member` are silently
  false; `del`/`add` must be guarded; `else` is not a cut.
- **Quality:** `docs/authoring/rubric.md`, the owner's rules. A strategy's `if()` states what
  makes it possible, and its `do()` lists the states to achieve with generic verbs. Imperative
  scripts, effect engines and invented jargon are slop.
- **Examples, by pattern:** `docs/authoring/patterns.md`. The gold examples are
  `Examples/Taxi.htn`, `Examples/Game.htn` and `Examples/TrunkThumper.htn`. Good architecture:
  `Examples/GameHack8AgentAtTop.htn`, `Examples/CombatLevel1_GreaseTrap.htn` and
  `components/gamehack/`.
- **Checks:** a PostToolUse hook runs `python -m htn_components check --fast` on every `.htn`
  edit. `check <file> --goal "task."` prints the plans. The `htn-reviewer` agent scores a
  ruleset against the rubric.

Levels, fun metrics and MCP playtesting: the `htn-level` skill.

## Build & Test

See `BUILD.md` for full commands.

```bash
cmake --build ./build --config Release        # build
./build/Release/runtests.exe                  # C++ tests
./build/Release/indhtn.exe Examples/Taxi.htn  # interactive REPL
python -m pytest tests                        # Python: metrics, parity, built-ins sync
python -m pytest src/Python/tests             # Python: bindings, linter, components CLI
PYTHONPATH=src/Python python -m htn_components test-all   # every component and level
```

## Directory Structure

```
src/FXPlatform/Htn/      # HTN engine (HtnPlanner, HtnMethod, HtnOperator)
src/FXPlatform/Prolog/   # Prolog engine (HtnGoalResolver, HtnRuleSet, HtnTerm)
src/FXPlatform/Parser/   # Lexer and parser framework
src/Python/              # Python bindings (indhtnpy), htn_components CLI, htn_metrics
gui/                     # Web IDE (Flask backend with the linter, React frontend)
mcp-server/              # MCP server for AI assistants
Examples/                # .htn examples (the gold ones are listed above)
components/              # Reusable HTN components (primitives, strategies, goals, gamehack)
levels/                  # Puzzle levels
bench/                   # Authoring benchmark and reviewer calibration (hidden answers inside)
docs/                    # All documentation; start at docs/README.md
```

## Documentation Map

- **Language** → `docs/reference/language.md`; **quality** → `docs/authoring/rubric.md`,
  `docs/authoring/patterns.md`
- **Planner internals** → `docs/reference/planner-internals.md`
- **Component system** (layers, manifests, CLI) → `docs/reference/component-system.md`
- **Level design loop** → `docs/reference/level-design-loop.md`; **fun metrics** → `docs/FUN_METRICS.md`
- **Tools** (REPL, tests, Python, GUI, MCP, components CLI) → `docs/TOOLS.md`
- **Design decisions** → `docs/DESIGN.md`; **fork upgrades** → `docs/upgrades/`; **upstream** → `docs/legacy/`

## Component System

Layers: Primitives → Strategies → Goals → Levels. `PYTHONPATH=src/Python python -m
htn_components <command>`: `check`, `status`, `test <path>`, `test-all`, `certify <path>`,
`trace <level>`, `play <level>`, `verify <level>`, plus the `fun*` commands (`htn-level` skill).

Certified components: the original tree (primitives `locomotion`, `tags`, `aggro`; strategies
`the_burn`, `the_slipstream`; goals `defeat_enemy`, `clear_room`; level `puzzle1`) and
GameHack (`components/gamehack/`: primitives `gh_movement`, `gh_tags`, `gh_aggro`,
`gh_skills`; action `gh_tag_application`; strategies `wet_and_electrocute`,
`stun_and_slow_skill`, `stun_and_burn`; goal `plan_to_damage`; levels `gamehack_*`).

## C++ Engine Rules

- All terms must come from the same `HtnTermFactory` for unification to work.
- Clear state before each test: `compiler->ClearWithNewRuleSet();`
- Expected test formats:
  - success: `"[ { operator1(args) } ]"`
  - empty plan: `"[ { () } ]"`
  - failure: `"null"`
  - bindings: `"((?X = value))"`
- C++11. Platform code goes in `Win/`, `iOS/` and `Posix/`.
