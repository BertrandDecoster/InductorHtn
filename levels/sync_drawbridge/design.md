# Sync: The Drawbridge

## Purpose

A synchronisation level: **one companion crosses alone and lowers the bridge; then two casts must
land back to back**. A sentinel machine stands on a ledge beyond a gulf. It is heavy, so nothing
moves it. The drawbridge is raised, and its winch is on the far pier. Three companions: the player
and the mage pick one skill each from a pool of seven; the porter only knows `turnToMist`. The ledge
is out of sight from the dock, so nothing is done from the near side. The Lost Vikings relay: the
one who can get over is never the one who can do the job.

The synchronisation is a **moment** (`moment(remove(heavy))`). The porter turns the sentinel to mist,
and for a moment it is not heavy. The moment lasts through the next cast by anyone, so the throw has
to be the very next cast: mist, then throw, back to back. Walking in between is fine. Casting
anything else in between wastes the mist.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The gulf** | a chasm, and the drawbridge (a `door`) is up | teleport onto the pier (`blink`); dash there (`lightningFlash`). Arriving on the pier works the winch (a zone with `open(drawbridge)`): the bridge latches down and the others walk over |
| **The sentinel** | a heavy machine: only a drop or a short takes it out | right after the porter's mist: push it off the ledge into the cliff from the pier (`fireball`, `tidalWave`); from the overlook, drag it across the cliff so it falls in (`hook`, `taunt`); suck it into the cliff (`vortex`). With no mist at all: `tidalWave` soaks it and `lightningFlash` jolts it (a short circuit) |

Why no single skill works:
- The crossing skills move only their caster, and neither of them throws the sentinel.
- The throwers never cross the gulf: there is no anchor on the pier for a hook, and no line that
  pushes anyone over.
- A dry jolt only stuns a machine. The short needs the wave's soak, and the only other way to land
  a flash is to cross with it.

The methods differ in kind: a teleport or a dash to get over; a push, a pull across the cliff, a
vortex into it, or an element combo (soak, then jolt) that needs no mist.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
dock (player, mage, porter) ~~ gulf (chasm) ~~ pier [winch] --- ledge (sentinel) ~~ cliff (chasm)
   \                                         /     |
    ----------- drawbridge (door) -----------     stair --- overlook (facing the ledge across the cliff)
```

- **Lines of sight:** dock-pier (both ways), pier-ledge, pier-cliff, overlook-ledge, overlook-cliff.
- **Push lines:** from the pier, a push on the ledge lands in the cliff. From the overlook, the cliff
  lies between it and the ledge, so a pull from there drops the sentinel in.
- **Sentinel:** `tag(sentinel, machine)`, `tag(sentinel, heavy)`.
- **Porter:** a third companion with `knows(porter, turnToMist)`; not a seat.
- **Goal:** `win` = `lowerBridge` (someone `reach`es the pier; the drawbridge must be open), then
  `neutralize(sentinel)`. The standard recipes are used: `intoThePit` strips the heavy ward with the
  porter's mist and then `sendInto`s the cliff; `exploit` handles the short.

## Hypothesis

Measured with `htn_components combos sync_drawbridge` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 20 of the 49 assignments win: each of the 2 crossing skills with each of the 5 throwers,
  whichever companion holds which (10 pairs).
- 11 methods (distinct sets of skills cast; every throw also casts the porter's `turnToMist`, and
  `lightningFlash` + `tidalWave` wins both with the mist and without it). 0 solo plans, no dead
  skill. Usage: blink and lightningFlash 10 each; each thrower 4.
- Every losing pair has a reason: two crossers (nothing throws or shorts the sentinel), or two
  throwers (nobody gets over).
- One replan takes under a second.

## Examples

### Example 1: Blink over, mist, then fireball

**Given:** the player knows `blink`, the mage knows `fireball`.

**When:** `win`

**Then:** the player blinks onto the pier, and the drawbridge comes down. The porter walks over and
turns the sentinel to mist. The mage walks over, and the very next cast is the mage's fireball,
which throws the sentinel off the ledge into the cliff (`fell`).

### Example 2: Flash over, mist, then taunt it across the cliff

**Given:** the player knows `lightningFlash`, the mage knows `taunt`.

**When:** `win`

**Then:** the player dashes onto the pier, and the bridge comes down. The porter mists the sentinel.
The mage goes up the stair to the overlook and taunts it. The sentinel is dragged toward the mage
and falls into the cliff on the way.

### Example 3: Soak, then jolt, with no mist

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the mage flashes onto the pier, and the bridge comes down. The player walks over, and the
wave soaks the sentinel. The mage's second flash jolts it, and soaked, the machine short-circuits
(`dead`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the 10 crossing-by-thrower pairs have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | Mist, then throw | In every throw plan, the cast right after the porter's mist is the throw. Without the porter, no throw wins; only the short does. |
| P5 | The bridge is up until someone crosses | Nobody walks to the pier until the winch is worked from it. |
