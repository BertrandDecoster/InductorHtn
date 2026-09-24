# Sync: The Drawbridge

## Purpose

A synchronisation level on **"for a moment"**: one companion crosses alone and lowers the bridge,
then two casts must land back to back. A sentinel (a heavy machine) stands on a ledge beyond a gulf;
nothing moves it. The drawbridge over the gulf is raised, and its winch is a plate on the far pier.
Three companions: the player and the mage pick one skill each from seven; the porter only knows
`turnToMist`. The ledge is out of sight from the dock, so nothing is done from the near side.

The moment: the porter turns the sentinel to mist, and for a moment it is not heavy. A moment lasts
through the next cast by anyone, so the very next cast must be the throw. Any other cast in between
and the sentinel is heavy again.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The gulf** | a `gap` between the dock and the pier; the drawbridge (a `doorway`) is up | teleport onto the pier (`blink`); dash over the gap (`lightningFlash`). On the pier, step on the winch plate (`open(drawbridge)`, latching): the bridge comes down for good and the others walk over |
| **The sentinel** | a heavy machine: only a drop or a short takes it out | right after the porter's mist, knock it into the cliff (a chasm feature of the ledge): `fireball` or `shieldBash` from the pier, `tidalWave` on the ledge, `vortex` on the cliff; or `hook` it from the overlook across the gap, where it falls. With no mist at all: `tidalWave` soaks it and `lightningFlash` jolts it (a short circuit) |

Why no single skill works:
- The crossing skills move only their caster; none throws the sentinel.
- The throwers cannot cross the gulf, and nothing can be done from the dock.
- `lightningFlash` crosses and jolts, but a dry jolt only stuns a machine.

`lightningFlash` serves two roles: crossing the gulf, and the jolt of the short circuit (four mana:
the flash over and the flash that shorts it). `tidalWave` serves two: a throw, or the soak.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
dock ==gulf (gap) + drawbridge (doorway)== pier [winch plate] --- ledge (sentinel; cliff)
                                              |                      :
                                           overlook ....... gap .....:
```

- **Areas (4):** dock, pier, ledge, overlook. Links: a `gap` and a `doorway` (the drawbridge) between
  the dock and the pier; walkable pier-ledge and pier-overlook; a `gap` overlook-ledge.
- **Lines of sight:** the dock sees the pier; the pier and the overlook see the ledge.
- **Features:** the winch plate on the pier (`open(drawbridge)`); the cliff (a chasm) on the ledge.
- **Sentinel:** machine, heavy.
- **Companions:** player and mage (four mana each, seats), porter (`turnToMist`, fixed).
- **Goal:** `win` = `lowerBridge` (someone `reach`es the pier by a leap, steps on the winch; the
  drawbridge must be open), then `drop`: the porter's mist and `sendDown(sentinel, porter)` right
  after it, or `conduct(sentinel)` (soak, then jolt).

## Hypothesis

Measured with `htn_components combos sync_drawbridge` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 20 of the 49 assignments win: each crossing skill (`blink`, `lightningFlash`) with each thrower
  (`fireball`, `tidalWave`, `hook`, `vortex`, `shieldBash`), whichever companion holds which half
  (10 pairs).
- 11 methods (distinct sets of skills cast): the ten mist-and-throw sets, plus the short circuit
  (`lightningFlash` + `tidalWave`, no mist). 0 solo plans, no dead skill. Usage: blink and
  lightningFlash 10 each; each thrower 4.
- One replan takes under 3 s.

## Examples

### Example 1: Blink over, mist, then fireball

**Given:** the player knows `blink`, the mage knows `fireball` (the default kit).

**When:** `win`

**Then:** the player blinks onto the pier and steps on the winch; the drawbridge comes down. The
porter walks over and turns the sentinel to mist. The mage walks onto the pier, and the very next
cast is the fireball: the sentinel is knocked into the cliff and falls.

### Example 2: Flash over, mist, then hook it across the gap

**Given:** the player knows `lightningFlash`, the mage knows `hook`.

**When:** `win`

**Then:** the player lightning-flashes over the gulf and works the winch. The porter mists the
sentinel; the mage, on the overlook, hooks it: dragged across the gap, it falls in.

### Example 3: Soak, then jolt, with no mist

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the mage flashes over and works the winch. The player walks onto the ledge and the wave
soaks the sentinel; the mage's second flash jolts the wet machine: it shorts out.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the 10 crossing-by-thrower pairs have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | Mist, then throw | In every throw plan, the cast right after the porter's mist is the throw. Without the porter, no throw wins; only the short does. |
| P5 | The bridge is up until someone crosses | Nobody walks to the pier until the winch is worked from it. |
