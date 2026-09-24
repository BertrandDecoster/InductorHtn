# Sync: The Drawbridge

## Purpose

A synchronisation level: **one companion crosses alone and lowers the bridge; the others cross and
finish the job**. A sentinel machine stands on a ledge beyond a gulf. The drawbridge is raised and
its winch is on the far pier. Three companions: the player and the mage pick one skill each from a
pool of eight; the porter only knows `rainCall` (a weak fixed skill: it soaks, it never kills). The
ledge is out of sight from the dock, so nothing is done from the near side. The Lost Vikings
relay: the one who can get over is never the one who can do the job.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The gulf** | a chasm, and the drawbridge (a `door`) is up | dash onto the pier (`pounce`, `charge`, `shadowStep`); swap with the barrel on the pier (`translocate`). Arriving on the pier works the winch (a zone with `open(drawbridge)`); the bridge latches down and the others walk over |
| **The sentinel** | a machine: only a drop or a short takes it out | push it off the ledge into the cliff from the pier (`gust`); from the overlook, drag it across the cliff so it falls in (`magnetize`, `taunt`); the porter soaks it and `zap` jolts it (short-circuit) |

Why no single skill works:
- The crossing skills move only their caster, and none drops or shorts the sentinel: `charge`'s
  push comes after its dash (it lands on the ledge, with no line from there); `pounce` only roots;
  `translocate` only swaps it; `shadowStep` only hides.
- The job skills never cross the gulf. There is no anchor on the pier for `magnetize` to hook, and
  no line that pushes anyone over.
- A dry jolt only stuns a machine: `zap` needs the porter's rain, and the porter can't cross alone.

The methods differ in kind on both sides: a dash or a swap to get over; a push, a pull across the
cliff, or an element combo (soak, then jolt) with the third companion.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
dock (player, mage, porter) ~~ gulf (chasm) ~~ pier (barrel) [winch] --- ledge (sentinel) ~~ cliff (chasm)
   \                                         /     |
    ----------- drawbridge (door) -----------     stair --- overlook (facing the ledge across the cliff)
```

- **Lines of sight:** dock-pier (both ways), pier-ledge, overlook-ledge.
- **Push lines:** from the pier, a push on the ledge lands in the cliff; from the overlook, the cliff
  lies between it and the ledge, so a pull from there drops the sentinel in.
- **Sentinel:** `trait(sentinel, machine)`: a jolt stuns it, soaked first it dies.
- **Porter:** a third companion with `knows(porter, rainCall)`, not a seat.
- **Goal:** `win` = `lowerBridge` (someone `reach`es the pier; the drawbridge must be open), then
  `neutralize(sentinel)` (the standard recipes: `intoThePit` for the drops, `exploit` for the
  short).

## Hypothesis

Measured with `htn_components combos sync_drawbridge` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 32 of the 64 assignments win: each of the 4 crossing skills with each of the 4 job skills,
  whichever companion holds which (16 pairs).
- 16 methods (distinct sets of skills cast; the four `zap` methods also cast the porter's
  `rainCall`), 0 solo plans, no dead skill: every skill is in 8 winning assignments.
- Every losing pair has a named reason: two crossers (nothing drops the sentinel), two job skills
  (nobody gets over).

## Examples

### Example 1: Pounce over, gust it off

**Given:** the player knows `pounce`, the mage knows `gust`.

**When:** `win`

**Then:** the player pounces onto the pier and the drawbridge comes down; the mage walks over and
gusts the sentinel off the ledge into the cliff (`fell`).

### Example 2: Swap over, taunt it across the cliff

**Given:** the player knows `translocate`, the mage knows `taunt`.

**When:** `win`

**Then:** the player swaps places with the barrel on the pier (the bridge comes down); the mage
walks over, up the stair to the overlook, and taunts the sentinel, which is dragged toward it and
falls into the cliff on the way.

### Example 3: Charge over, rain, then jolt

**Given:** the player knows `zap`, the mage knows `charge`.

**When:** `win`

**Then:** the mage charges onto the pier; the porter walks over and soaks the sentinel with rain;
the player walks over and zaps it: soaked, the machine short-circuits (`dead`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Sixteen pairs win | Exactly the 16 crossing-by-job pairs have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | Zap needs the porter | `pounce` + `zap` wins with the porter's rain, and not without it. |
| P5 | The bridge is up until someone crosses | Nobody walks to the pier until the winch is worked from it. |
