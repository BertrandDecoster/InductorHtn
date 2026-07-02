# fortress-loadout — cooperative skill-combo puzzle level

Third spike in the loadout series (after `decision-dag` and `loadout-decision`).
One level, three challenges. Before the level, the player and their one
companion each equip a single skill from a pool of 7 — that 2-of-7 choice
(21 unordered loadouts) is the puzzle decision. Skills have 2 "natural"
effects each; methods are gated on which effects the loadout can produce.

## Structure

Challenge = OR over 3 atoms (alternative approaches). Atom = OR over 1-3
authored methods. Methods are **cooperative combos**: both companions act
simultaneously (`parallel(...)` in the plan), or a skill meets the
environment. "Neutralize the blocker, then do the trivial thing" is not a
combo and is not authored as one.

Design rules (from the design discussion):

1. **Fight always works** on non-`invulnerable` enemies. `disableEnemy` is
   one abstraction with interchangeable ways (kill, stun, freeze,
   taunt-hold, shove into the moat). The Sentinel and the Brute are
   `invulnerable`, so combos are mandatory there.
2. **forcedMovement + adjacent element area = element applied** (quench
   pool -> wet, electric fence -> electrified, chasm -> gone).
3. **Slot combos**: `attackBackWhileDistracted` = distract (taunted |
   frozen | stunned) + reach the back (teleport | sneaky). Effects are
   **directional**: `skillGrants(skill, effect, direction)`, where `source`
   lands on the caster (teleport, sneaky, the grappling self-pull) and
   `target` lands on an enemy/the environment.
4. **Challenge 1 is an It-Takes-Two style relay** (see
   `docs/other_games/games/it-takes-two.md`): one companion crosses a
   fast-flowing river only their skill can (teleport, a grappling self-pull,
   or by freezing it into a bridge), presses button 1 to unlock a plain path
   for the partner, who presses button 2 to let both through.

## The 7 skills

| Skill | Effects (direction) | Reading |
|---|---|---|
| frostNova | frozen (t), slowed (t) | cold locks targets in place, numbs |
| lightningStep | electrified (t), teleport (s) | zap an enemy, or blink yourself across |
| tidalWave | wet (t), forcedMovement (t) | the wave soaks and shoves enemies |
| smokeBomb | sneaky (s), slowed (t) | conceals you; choking smoke slows enemies |
| warHorn | taunted (t), stunned (t) | the challenge draws aggro; the blast dazes |
| shadowStep | teleport (s), sneaky (s) | melt into shadow, reappear |
| grapplingHook | forcedMovement (s), stunned (t) | hook a wall/entity and pull YOURSELF to it; the hooked enemy is briefly stunned |

Direction: **s** = on the caster itself, **t** = on an enemy/the environment.
Note `forcedMovement` is granted by two skills in *opposite* directions —
tidalWave shoves enemies (t), grapplingHook pulls itself (s) — which is why
only grapplingHook can use it to cross (see `crossEffect` in `level.htn`).

Combo rules as world data: `wet + electrified -> overloaded` (lethal,
long-disables machines), `wet + frozen -> frozenSolid` (lethal, shatter).
`overloaded`/`frozenSolid` are derived outputs only — never granted by a skill.

## Run

```bash
source .venv/bin/activate && PYTHONPATH=mcp-server python prototypes/fortress-loadout/sweep.py
```

(The `Query ... is a ... syntax query` lines on stdout are harmless engine
noise, same as the other spikes.)

Manual REPL check:

```bash
printf 'assert(equipped(player, tidalWave)).\nassert(equipped(companion, lightningStep)).\ngoals(defeatVaultBrute()).\n/q\n' \
  | ./build/indhtn prototypes/fortress-loadout/level.htn
```

## Observed matrix (2026-06-17, after the arity-3 skill-direction refactor, all properties PASS)

```
loadout                      enterFortress   secureWorkshop  defeatVaultBrute  FULL
frostNova+grapplingHook      6               2               1                 12
frostNova+lightningStep      4               2               1                 8
frostNova+shadowStep         4               3               1                 12
frostNova+smokeBomb          2               2               2                 8
frostNova+tidalWave          3               1               2                 6
frostNova+warHorn            4               3               1                 12
grapplingHook+lightningStep  4               2               0                 0
grapplingHook+shadowStep     4               3               0                 0
grapplingHook+smokeBomb      2               2               1                 4
grapplingHook+tidalWave      3               1               1                 3
grapplingHook+warHorn        4               3               0                 0
lightningStep+shadowStep     2               0               0                 0
lightningStep+smokeBomb      1               0               1                 0
lightningStep+tidalWave      2               2               1                 4
lightningStep+warHorn        3               4               0                 0
shadowStep+smokeBomb         1               0               1                 0
shadowStep+tidalWave         2               0               0                 0
shadowStep+warHorn           3               6               0                 0
smokeBomb+tidalWave          0               0               1                 0
smokeBomb+warHorn            0               4               1                 0
tidalWave+warHorn            0               2               3                 0
```

- 9/21 loadouts full-clear; 12 dead-end on some challenge (the decision
  matters, and reading WHICH challenge kills a loadout is the player skill).
- Cross-check: `playLevel()` (loadout bound in-plan) = 69 plans = sum of
  the swept FULL column.
- Properties: P1 each challenge solvable by 14-18/21 loadouts (C1 18, C2 16,
  C3 14); P2 9/21 full-clear; P3 every skill in some full-clear loadout; P4
  all 7 atoms reachable; P5 all 11 authored methods seen, no metadata drift;
  P6 no invulnerable target ever falls to bare fighting.
- The 3 loadouts that fail C1 (smokeBomb+tidalWave, smokeBomb+warHorn,
  tidalWave+warHorn) are exactly the pairs where neither skill grants a
  crossing effect (teleport / forcedMovement-source / frozen) — the loadout
  now genuinely gates the relay.

### Tuning history

- 2026-06-17, arity-3 skill-direction refactor: `skillGrants/2` became
  `skillGrants(skill, effect, direction)` and `canUse` became
  `canApply(source, effect, target)`, so an effect now knows whom it lands
  on. Dropped the `rooted` and `hookPull` effects (rooted folded into a
  direct `distracts(frozen)`; hookPull became `forcedMovement` on the
  caster). Challenge-1 crossing was retargeted to self-movement /
  terrain-change effects only (`crossEffect`: teleport-source,
  forcedMovement-source, frozen-target), so electrified and sneaky no longer
  cross. Consequence: grapplingHook can no longer shove enemies (its
  forcedMovement is `source`), making tidalWave the sole shover. Full-clears
  9/21 (was 10), spread 3-12, all properties still PASS.
- First sweep: shadowStep+warHorn dominated (72 full plans vs 6-24 for
  everything else) because `bypassBrute/kiteAndSlip` (taunt-kite + slip
  past) cleared challenge 3 with no elemental investment. That method is
  now commented out in `level.htn`; full-plan spread is 3-18.
- `environmentKill` was unreachable on any winning run. The Brute is now a
  fire elemental: water flash-steams off it unless it is stunned while
  soaked (`drowned` = wet + stunned in parallel). That gives
  grapplingHook+tidalWave its full-clear (hook up the ledge, stun-hold
  under the press, drown the Brute) and puts environmentKill on a winning
  path.

## How the encoding works

- `equipped(?who, ?skill)` is the single capability gate. The sweep injects
  it per loadout (per-challenge analysis); `playLevel()` binds it in-plan
  with an index trick (`<(?i1, ?i2)`) so each unordered pair appears once.
- `canApply(?source, ?effect, ?target)` axiom: a `target`-direction
  `skillGrants` lands `?effect` on an enemy; a `source`-direction one lands
  it on the caster itself (teleport, sneaky, the grappling self-pull).
- `shoveIntoArea(?t, ?a)`: solo if `adjacentArea(?t, ?a)` (gate guard by
  the moat, sentinel by its quench pool), co-op lure+shove (taunt +
  forcedMovement from two different companions) if `lureSpot(?t, ?a)`.
- Every atom-method ends in `opResolveAtom(atom, method)`; the sweep
  regexes those markers, so atom/method usage tracking never depends on
  fingerprinting operator sequences.
- Plain alternative methods everywhere, no `else`: FindAllPlans enumerates
  every approach as a distinct plan (the established multi-strategy rule).

## Honest caveats

- Challenges are measured independently from the initial state; effects
  land on per-challenge targets so no cross-challenge leakage exists, but
  nothing would catch it if a future edit introduced some.
- `parallel(...)` marks simultaneity for the parallelizer; the planner does
  not simulate timing. "Both act at once" is a fiction contract, not a
  verified constraint.
- `slowed` fuels only `bypassBrute/slowAndOutrun`; it is the weakest effect
  in the pool (but it does carry frostNova+smokeBomb loadouts to C3).
- No cost axis: a 7-step co-op plan and a 1-step fight count the same.
- The sweep needs a raised session memory budget (256 MB) for the
  `playLevel()` enumeration (69 plans); the default 1 MB budget dies on it.
