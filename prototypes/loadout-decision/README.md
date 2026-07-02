# loadout-decision spike

Models the **decision as a constrained loadout chosen *inside* the plan**, and a
**multipurpose skill that unlocks a whole region of the precondition tree**.

This is the follow-up to `prototypes/decision-dag/`, which was tautological: there
"decisions" were free, independent capability tokens swept externally in Python, so
"take everything" dominated and the "fairness check" was a set-membership test that
detected only what it was hand-fed. Here the decision is load-bearing and the
analysis measures real structure.

## The idea

`defeatWithLoadout(?t)` binds two **distinct** skills over `equippableSkill` facts,
commits them with `loadSkill` operators onto two bare companions, then decomposes the
real combat goal (`planToDamage`) against whatever got equipped:

```prolog
defeatWithLoadout(?t) :-
    if(equippableSkill(?s1), equippableSkill(?s2), \==(?s1, ?s2)),
    do(loadSkill(companionA, ?s1), loadSkill(companionB, ?s2), planToDamage(?t)).
```

So a single `FindAllPlans` call enumerates every `(loadout × strategy)` as a distinct
plan — the planner itself chooses the loadout. No external sweep.

The combat substrate is the **existing gamehack stack**, reused verbatim: tag
application routes `applyTag → applyTagNotPresent` (the 3-path dispatcher) →
`prepareToUseSkill`, whose first method requires `hasSkill`. That `hasSkill` is the
hook the loadout drives.

### Why it measures something (the world is stripped on purpose)

For the loadout to *determine* capability, it must be the only source of `hasSkill`.
So vs. the assembled `tests/fixtures/assembled/gamehack_multipath.htn`, this level
removes:

- static ally `hasSkill` facts — companions start **bare**;
- `canGetSkillAtLocation` — kills `prepareToUseSkill`'s learn-at-location fallback;
- `locationCanApplyTag` and enemy `hasSkill` — kills dispatcher Paths 2 & 3 (location
  and non-ally-mob tag sources).

The only route to a tag is now: an ally that **equipped** a skill that applies it.

## Files

- `level.htn` — the gamehack combat stack (verbatim) + the stripped world + the
  `equippableSkill` pool + the `loadSkill` operator + the `defeatWithLoadout` root.
  Based on `tests/fixtures/assembled/gamehack_multipath.htn` (the internally
  consistent, skill-routed assembly — **not** the drifted `components/.../gh_tags`).
- `sweep.py` — loads the level via in-process MCP, makes one `find_plans` call, then
  **groups plans by equipped skill-set** and reports the matrix + analysis.

## Run

```bash
source .venv/bin/activate
PYTHONPATH=mcp-server python prototypes/loadout-decision/sweep.py
```

(Build first if the bindings are missing: `cmake --build ./build --config Release`.
The `Query ... is a <kind> syntax query` lines on stdout are harmless engine noise.)

## What it shows (current world)

```
loadout (skill-set)               #plans  unlocked strategies
{fireballSkill, iceBlastSkill}    4       stunAndBurn, stunAndSlowSkill
{fireballSkill, lightningSkill}   0       -- nothing --
{fireballSkill, waterSkill}       0       -- nothing --
{iceBlastSkill, lightningSkill}   0       -- nothing --
{iceBlastSkill, waterSkill}       0       -- nothing --
{lightningSkill, waterSkill}      2       wetAndElectrocute
```

- **Load-bearing:** 4 of 6 loadouts unlock *nothing*. The decision genuinely gates
  capability — the opposite of the prior spike's "take everything wins."
- **Multipurpose payoff:** `{fireball, iceBlast}` unlocks **two** combos because
  `iceBlastSkill` is multi-tag (`stun` **and** `ice`): its `stun` feeds
  `stunAndSlowSkill`, its `ice` feeds `stunAndBurn`. One equip, a *set* of combos —
  the thesis, demonstrated mechanically. (`waterSkill` is also multi-tag, `clean`+`wet`,
  but `clean` drives no strategy, so it isn't a meaningful multipurpose unlock here —
  the report distinguishes the two.)

The matrix is sparse because the world is minimal — each strategy needs one specific
skill-pair. That sparsity is a property of the data, not the mechanism: adding more
`skillAppliesTag` mappings (e.g. `skillAppliesTag(lightningSkill, stun)` — "lightning
also stuns") immediately widens which loadouts are viable and creates overlapping
multipurpose unlocks. It's a tuning knob, deliberately left at its honest minimum.

## Manual check in the REPL

```bash
printf 'goals(defeatWithLoadout(gob)).\n/q\n' | ./build/indhtn prototypes/loadout-decision/level.htn
```

Expect 6 plans, each beginning with two `loadSkill(...)` operators. The count must
match `sweep.py`'s `total plans returned by FindAllPlans: 6`.

## What this does NOT cover (deliberately) — and what's next

- **No cost / exclusion axis.** Loadouts here only *differ*; they don't *trade off*.
  With limited slots and no per-skill cost, a "richer" loadout is strictly better
  when it unlocks more. The next increment is per-skill costs or hard exclusions
  (pick `orcAlly` **or** `killOrc`), which is what turns "which loadout unlocks most"
  into a genuine decision with regret. (This is also why dominance analysis is in the
  driver already — it'll start firing once costs exist.)
- **No loadout-vs-fetch trade-off.** We deleted the location/mob tag routes and
  learn-at-location. Re-adding them makes the loadout one option among several
  (equip up-front vs. fetch from the world mid-plan) — a richer and more game-like
  question.
- **No legibility / deduction.** Unchanged from the prior spike's honest caveat: the
  planner proves a loadout *works*; it says nothing about whether a human can *deduce*
  the right loadout from inspectable preconditions rather than enumerate it. That is
  authoring + UI, not solver output, and remains the real risk to confront.
