# HTN exemplars (translated classic domains)

Reference rulesets in **native InductorHTN syntax** (`?vars`, `task() :- if(...),
do(...).`, `op() :- del(...), add(...).`). Each is a faithful, deliberately *small*
re-expression of a classic AI-planning / HTN domain -- same dialect as the engine,
unlike the upstream SHOP / JSHOP / HDDL S-expression sources they come from. They
exist to be read as worked examples of idiomatic modeling, and to ground the
`/htn-improve` command before it edits a real ruleset.

Each file opens with a header comment (source, the pattern it teaches, the
`goals(...)` to run) and is verified to compile, lint clean (modulo the benign codes
below), and produce a single sensible plan.

| File | Source domain | Reach for it when you need... | Run |
|------|---------------|-------------------------------|-----|
| [`blocksworld.htn`](blocksworld.htn) | Blocks World (PyHOP / GTPyhop / SHOP) | **recursion + goal regression** -- clear a stack recursively before acting, with an empty-`do()` base case | `goals(buildTower()).` |
| [`logistics.htn`](logistics.htn) | IPC Logistics / Transport | **data-driven verbs over a connectivity graph** -- general verbs routing over `connected`/`inCity` facts; multi-vehicle (truck + plane) relay; case methods by mutually exclusive gates | `goals(deliver(pkg1, locB1)).` |
| [`barman.htn`](barman.htn) | IPC Barman | **resource / state tracking with a numeric fluent** -- `increase()` counting, a fluent gating a later step, clean/used container transitions | `goals(makeCocktail(cocktail1)).` |
| [`rover.htn`](rover.htn) | IPC Rover | **multi-goal decomposition + `anyOf` over reachable targets** -- a mission that fans out into sub-objectives; "make ready, then act" helpers with no-op base cases | `goals(surveyMission(rover1)).` |

In-repo, same-dialect rulesets worth reading alongside these:
`prototypes/fortress-loadout/level.htn` (cooperative skill-combo level, the most
elaborate hand-authored example) and `Examples/TrunkThumper.htn` (the Game AI Pro
boss-AI port: multi-plan enumeration, recursion, fluents).

## Verify an exemplar

```
indhtn_create_session
indhtn_load_files   [".../docs/reference/exemplars/<file>.htn"]
indhtn_find_plans   "<the goal from the header>"   # expect >= 1 plan
indhtn_lint         "<file source>"                # expect 0 errors
```

## Benign lint codes these carry

Trust the engine over the linter when they disagree (see
`../ruleset-iterating.md`). The warnings below are expected and **not** bugs:

- **`HTN005`** -- empty `do()`. The intended base case of a recursive / make-ready
  method (`clearBlock`, `goTo`, `ensureEmptyStore`, `moveTruck`, ...).
- **`SEM006`** -- "potential infinite recursion." The *intended* recursion in
  `blocksworld.htn` (`clearBlock -> toTable -> clearBlock`), bounded by the world.
- **`SEM002`** -- "undefined predicate." A predicate that is only ever produced by an
  operator `add()` (e.g. `storeFull/1` in `rover.htn`), or a numeric literal in a
  goal position (e.g. the `2` in `barman.htn`'s fluent gate) -- a known linter gap
  with integer literals; the engine evaluates it fine.

`VAR003` (singleton variable) is *not* benign in general -- it catches real typos --
but it can false-positive on a "probe" variable used only to chain preconditions; the
exemplars are written to avoid that so you can treat any `VAR003` here as real.
