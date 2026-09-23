# Ruleset Design Policies

The register of recurring judgment calls, so an authoring run (human or
`/htn-improve`, `/htn-create`, `/htn-audit`) applies a recorded ruling instead
of re-asking. Each entry: the rule, why, and a worked exemplar in the repo.
Add new entries here when a design call gets made mid-run — one numbered
policy per call.

Companion docs: `ruleset-writing.md` (heuristics), `ruleset-creating.md`
(the end-to-end creation workflow these policies gate).

## POL-1 — Latent mechanics are allowed, but must be declared

A world rule with no player-reachable trigger (stated physics, a content hook
for a future enemy/environment source) may stay in the ruleset **iff** its
declaration comment names it as latent and says what would activate it.
Undeclared unreachable methods are bugs.

- Exemplar: `meltIce` / `effect(fire)` in `prototypes/fortress-loadout/level.htn`
  — fire melts the frozen river, but no equippable skill grants fire; the
  comment block declares the hook.
- Consequence: `SEM004`/`SEM005` on a declared latent is **expected**. List it
  in the audit report as "declared latent (POL-1)"; do not "fix" it, and do not
  silently accept it on an undeclared method either.
- Ruling recorded 2026-07-02 (fire-mechanic veto: "latent hooks OK if declared").

## POL-2 — A combo means both actors act at once

"Neutralize the blocker, then do the trivial thing" is NOT a combo — that is a
disable plus a free action. A combo requires simultaneous (or near) action:
taunt + backstab, wet + stunned on a fire elemental, hold + crank. Encode
simultaneity with `parallel(...)`.

- Structural rules the fortress sweep asserts: every combo input must be
  skill-producible, and no combo output may be reused as an input (no cycles).
- Combo-gated targets are marked `invulnerable` so the fight baseline cannot
  leak through (the harness's `P6_comboGated` property checks this via
  resolve markers).

## POL-3 — No dominant loadout

Not every loadout must win (dead-end loadouts are content — finding which
challenge kills a loadout is the player skill), but **no loadout may solve
most of the level's methods**: a pair an order of magnitude above the rest is
a ruleset bug, not a balance nit.

- Precedent: `kiteAndSlip` was commented out (2026-06-10) because it gave
  shadowStep+warHorn 72 full plans vs 6-24 for every other pair
  (`level.htn`, the `bypassBrute` section).
- Detectors: the harness's `dominance` (proper-superset strategy sets) and the
  FULL-column spread in the matrix; a skill appearing in nearly every
  full-clear loadout is the same smell.

## POL-4 — Comment out, don't delete (and keep metadata in sync)

Removing a method to fix balance: comment it out with a dated comment stating
why, and comment out its `atomMethod` metadata line together with it —
otherwise the drift check (`P5_methodDrift`) fires. History stays readable in
the file, not just in git.

- Exemplar: the `kiteAndSlip` block and its metadata line in
  `prototypes/fortress-loadout/level.htn`.

## POL-5 — ASCII only in .htn sources

The loader is strict UTF-8 and chokes on em/en dashes and smart quotes. Keep
every `.htn` file pure ASCII (comments included).

## POL-6 — Flat, decodable names

Prefer `attackBackWhileDistracted` over `dismantleCore`: a name should state
the mechanic, not the fiction. Fluff is layered on after the ruleset is
verified ("ruleset first, fluff after" — the preconditions and effects ARE
the design).

## POL-7 — The canonical benign-lint list

The single source of truth for which lint codes to accept. Other docs and
commands link here; do not restate the list elsewhere.

| Code | Status | When it is benign |
|------|--------|-------------------|
| `HTN005` | benign | empty `do()` — the base case of a recursive / make-ready method |
| `SEM002` | benign | predicate only produced by an operator `add()`; runtime-injected facts (e.g. `equipped/2`); a numeric literal in a goal position (known linter gap) |
| `SEM004`/`SEM005` | conditionally benign | ONLY for (a) declared latent mechanics (POL-1) and (b) tasks entered via goals outside the linted file. Anything else is real dead code. |
| `SEM006` | benign | intended recursion bounded by world facts |
| `SYN012` | benign | `hidden`/`parallel` used as bare atoms — the engine accepts them |
| `VAR003` | **real** | catches typos; known false positive only on a "probe" variable chaining two preconditions |
| `TYP010` | **real** | fires only on provably disjoint types — treat as a bug |
| `SEM001` | **real** | undefined task. (Since 2026-07-02 the linter follows `parallel(...)` in the call graph, so `parallel/2` itself and its callees no longer false-positive.) |

Trust the engine over the linter when they disagree (`find_plans` is the
arbiter), but every acceptance must cite a row in this table or a POL-1
declaration.
