# Short Circuit

## Purpose

A crowd-control level (category 8): **too many enemies to take one by one; shape them as a group,
then one blow takes the group.** Three clockwork drones guard the yard of an old foundry. A drone is
a machine: a jolt on a dry one only stuns it, a jolt on a wet one short-circuits it. The one jolt,
`lightningFlash`, costs 2 mana and each companion has 2, so exactly **one bolt** has to catch the
whole crowd - a flash down the hall electrocutes everyone on its path. Or leave the jolts alone: the
foundry floor is rotten, and the ogre at the forge stamps it through (`caveIn`, the catalogue's
physical heavy attack) when it is taunted (dragged to its taunter first) or dazzled (`blinded`)
where it stands. Everything in its region falls; no plan may leave a companion there.

Two companions, the player and the mage, pick one skill each from a pool of six. Nothing grants an
outcome: `dead` comes only from the catalogue's machine weakness, `fell` only from the chasm.

The level's goal is spelled out top-down from the need, with two kinds of victory:

| Method | First | Then |
|--------|-------|------|
| **Short them** (a weakness) | every drone wet (`primeAll(wet)`): `tidalWave` (from the gate it soaks the yard and washes it into the sump; from the yard it soaks in place), `vortex` on the sump (the whole yard is sucked into the water), `taunt` or `hook` from the sump (one drone at a time) | one `lightningFlash` down the hall (`boltAll`): everyone on the path is electrocuted |
| **Drop them, provoked** (a hazard) | `taunt` the ogre from the yard: it is dragged to the drones and winds up a cave-in on the yard | in the wind-up the other companion `hook`s the taunter out; the yard falls in |
| **Drop them, dazzled** | `vortex` on the sump: the drones AND the ogre are sucked in | `blindingFlash` from the yard or the forge: the dazzled ogre stamps the sump through |

Why no single skill works: a soak or a herd leaves the drones alive; a bolt on dry drones only stuns
them, and nobody can afford a second one; the taunter is always in the cave-in's region, and a wave
or a vortex that pulls them out takes the drones out too; companions cannot be taunted, so no friend
can taunt you out of the way.

Skills serving several roles: `vortex` soaks the crowd (into the sump) for the bolt, or gathers the
crowd and the ogre for the cave-in; `taunt` herds drones into the water, or provokes the ogre;
`hook` herds drones, or rescues the taunter; `tidalWave` soaks in place or washes into the sump.

The traps: a bolt first (dry drones are only stunned); two bolts, two soaks, two herders; a wave or a
vortex to rescue the taunter (the drones go too); hooking the ogre in and flashing (the hooker is
caught in the cave-in); flashing from inside the sump - the flash makes you disjoint, so the blow
passes through you, but the floor still gives way under your feet (the plan is refused).

Level-local facts (wishlist evidence): `immune(player, taunted)` and `immune(mage, taunted)`.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage) --- yard (cog1, cog2, cog3; machines) --- sump (puddle) --- forge (ogre)
```

- **Line of sight:** the gate sees the whole hall (yard, sump, forge); the yard sees the sump and the
  forge; the sump sees the yard and the forge.
- **Lines:** a push from the gate on the yard lands in the sump; the yard and the sump lie between
  the gate and the forge (a lightning flash from the gate to the forge strikes both).
- **Zones:** the sump is a `puddle` (wet).
- **Ogre:** an enemy, `living`; `behavior(ogre, taunted, caveIn, here)`,
  `behavior(ogre, blinded, caveIn, here)`.
- **Companions:** 2 mana each (one wave or flash); immune to `taunted`.
- **The team:** a plan that leaves a companion stunned or fallen is refused (`teamFit`).

## Hypothesis

Measured with `htn_components combos crowd_short_circuit` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 12 of 36 assignments win (6 unordered pairs, whichever companion holds which half):
  `lightningFlash` with `tidalWave`, `vortex`, `taunt` or `hook` (short them); `taunt` with `hook`,
  and `vortex` with `blindingFlash` (drop them).
- 6 methods, in two kinds (a weakness, a hazard drop by an enemy's heavy attack). Skill usage:
  `lightningFlash` 8, `vortex` 4, `taunt` 4, `hook` 4, `tidalWave` 2, `blindingFlash` 2. No dead
  skill.
- No solo plans. One replan takes under a second.

## Examples

### Example 1: Vortex into the sump, one flash

**Given:** the player knows `vortex`, the mage knows `lightningFlash` (the default kit).

**When:** `win`

**Then:** the vortex on the sump sucks the three drones (and the ogre) into the flooded sump. The mage
flashes from the gate to the forge: the path crosses the sump, and all three short-circuit.

### Example 2: A wave, one flash

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** from the gate the wave soaks the yard and washes it into the sump; from inside the yard it
soaks the drones where they stand. Either way one flash down the hall takes all three.

### Example 3: Taunt the ogre, be hooked out

**Given:** the player knows `taunt`, the mage knows `hook`.

**When:** `win`

**Then:** the player walks into the yard and taunts the ogre: it is dragged in among the drones and
winds up a cave-in. The mage hooks the player back to the gate. The yard falls in: all three drones
fall.

### Example 4: Gather and dazzle

**Given:** the player knows `vortex`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the vortex draws the drones and the ogre into the sump. The mage flashes from the yard or
the forge (never from inside the sump); the ogre stamps the sump through.

### Example 5: Traps

**Given:** `lightningFlash` twice; `taunt` twice; `taunt` and `tidalWave`; `hook` and
`blindingFlash`.

**When:** `win`

**Then:** no plan.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Six pairs win | Exactly the six measured pairs have a plan. |
| P3 | Each hand matters | Every winning pair wins whichever companion holds which half. |
| P4 | One blow | Every winning plan takes the crowd with exactly one flash or one cave-in; no companion is under the blow, stunned or fallen. |
