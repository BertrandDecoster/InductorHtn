# decision-dag spike

A minimal InductorHTN prototype testing one idea: model a game **level as a DAG of
fundamental states** whose edges are **default-locked** and become traversable only
when the player holds the capability a *decision* grants. The puzzle is to find a
decision-set that opens a full `start → goal` path.

It exists to settle two questions before any larger investment:

1. **Can the planner act as a design-time solvability prover that finds *multiple*
   distinct strategies?** (Yes — `FindAllPlans` enumerates every simple path.)
2. **Can we mechanically detect when a "valid" path is actually unfair to the
   player** (relies on an unlock the player had no clue to deduce)? (Yes — the
   `masterKey` edge is the planted trap, and the driver flags it.)

See the research backing in the plan file
`~/.claude/plans/i-want-to-gather-buzzing-hinton.md` (Parts B5, C7, C8, C10).

## Files

- `level.htn` — the level as data: `edge(from, to, unlock)` facts (acyclic),
  `clue(capability, text)` for fair-deducibility, and a thin recursive traversal
  (`solve`/`go`/`passable`/`opMove`). Methods use **no `else`**, so the planner
  enumerates *every* winning path as a distinct plan (= distinct strategy).
- `sweep.py` — driver. Pulls the DAG + clues from the domain, then for each
  decision-set (subset of capability tokens) resets state, injects `have(...)`
  facts, runs `find_plans`, and reports solvability, strategy count, and fairness.

## Run

```bash
source .venv/bin/activate
PYTHONPATH=mcp-server python prototypes/decision-dag/sweep.py
```

(`PYTHONPATH=mcp-server` puts the `indhtn_mcp` package on the path; the driver uses
the in-process MCP API, mirroring `mcp-server/play_taxi_game.py`. Build first if the
bindings are missing: `cmake --build ./build --config Release`.)

The engine prints informational `Query ... is a <kind> syntax query` lines to
stdout during `add_facts`; they are harmless noise, not errors.

## Reading the report

```
decision-set                  solvable  #strat  #fair  flags
{}                            no        0       0
{electric, orcAlly}           yes       2       2
{electric, fireImmune, orcAlly}  yes    4       4
{... , masterKey}             yes       N       N-1    1 UNFAIR
```

- **solvable** — `no` means the prover proved the level *unwinnable* with that
  decision-set (the `FindAllPlans` failure result). The empty set is unsolvable
  because every edge out of `start` is gated. (B5)
- **#strat** — number of distinct winning paths = number of strategies. ≥2 is the
  multi-strategy goal. (C7)
- **#fair / flags** — a strategy is *fair* only if every gated edge it uses has a
  clue. Any decision-set containing `masterKey` exposes the `start → goal`
  shortcut, which has no clue and is flagged `UNFAIR`. This proves design-time
  solvability is **necessary but not sufficient** — a prover will happily bless
  moon-logic. (C10)
- Confirmation is reported **per whole plan**, never per edge — the commit-whole-
  plan gate that stops incremental guessing. (C8)

## Manual check in the REPL

```bash
printf 'assert(have(electric)).\nassert(have(orcAlly)).\ngoals(solve(player)).\n/q\n' \
  | ./build/indhtn prototypes/decision-dag/level.htn
```

Expect two plans:
`[ { (opMove(player,start,vault), opMove(player,vault,goal)) } { (opMove(player,start,bridge), opMove(player,bridge,goal)) } ]`.
The trailing `/q` is required — without it the REPL loops on EOF.

## What this does NOT cover (deliberately)

NPC plan-execution, the knowledge-gated-vs-commitment-gated design fork, perfect-
information modeling (Into the Breach), and any player-facing legibility/UI. This
spike validates the solver-side claims and the *mechanical* fairness check only.
The remaining hard design work — making the preconditions legible enough that a
human *deduces* the decision-set rather than enumerating it — is authoring, not
solver output, and is the real risk to confront next.
