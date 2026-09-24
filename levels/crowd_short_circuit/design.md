# Short Circuit

## Purpose

A crowd-control level (category 8): **too many enemies to take one by one; shape them as a group,
then one blow takes the group.** Three clockwork drones guard a long foundry hall. A drone is a
machine: a jolt on a dry one only stuns it, a jolt on a wet one short-circuits it. The jolts are
dear (`chainLightning`, `lightningFlash`: 2 mana, and each companion has 2), so exactly **one bolt**
has to catch the whole crowd. Two companions, the player and the mage, pick one skill each from a
pool of seven. Nothing grants an outcome; `dead` comes only from the catalogue's machine weakness.

The level's goal is a crowd recipe, spelled out top-down from the need: every drone wet
(`primeAll(wet)`), then one bolt that leaves nobody standing (`boltAll(electrocuted)`). Priming a
drone is one of three things: blanket its room (a spilled zone or an area grant), pull it into a
room that soaks (a pull, or a tag that drags), or push it into one.

| Method | Wet the crowd | Then one bolt |
|--------|---------------|---------------|
| **Soak in place, bolt the line** | `rainCall`, `glaciate` on the yard (cog3 in the sump is wet already) | `lightningFlash` from the gate to the forge: everyone between is struck |
| **Wash them into the sump** | `tidalWave` from the gate: it soaks the yard and washes the yard into the sump | `chainLightning` on the sump, or `lightningFlash` down the hall |
| **Pull them into the sump** | `provoke` from the sump (the whole yard at once) or `taunt` (one drone at a time) | `chainLightning` on the sump, or `lightningFlash` down the hall |

Why no single skill works: a soak or a herd leaves the drones alive; a bolt on dry drones only stuns
them; and two bolts cannot happen with one skill because every seat can afford just one.

The trap: soaking where they stand and then chaining. The chain takes the yard and misses cog3 in
the sump - one room per area bolt. The crowd is split, so either the bolt has to be a line
(`lightningFlash`) or the crowd has to be put in one room first.

Skills serving two roles: `tidalWave` is a soak and a herd in one cast; `lightningFlash` finishes
both a crowd soaked in place and a crowd herded into the sump.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage) --- yard (cog1, cog2) --- sump (cog3, flooded) --- forge
```

- **Line of sight:** the gate sees the whole hall (yard, sump, forge); the sump sees the yard and the
  forge.
- **Lines:** a push from the gate on the yard lands in the sump; the yard and the sump lie between
  the gate and the forge, so a `lightningFlash` from the gate to the forge strikes both rooms.
- **Zones:** the sump is flooded (`puddle`): whoever arrives there is soaked.
- **Drones:** machines; cog3 starts wet. Both companions have 2 mana.

## Hypothesis

Measured with `htn_components combos crowd_short_circuit` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 16 of 49 assignments win (8 unordered pairs, whichever companion holds which half):
  - `lightningFlash` with `rainCall`, `glaciate`, `tidalWave`, `provoke` or `taunt`: 5 pairs;
  - `chainLightning` with `tidalWave`, `provoke` or `taunt`: 3 pairs.
- 8 methods (distinct sets of skills cast), in three kinds: soak in place + line bolt, wash in +
  bolt, pull in + bolt. No dead skill; `lightningFlash` is in 10 winning assignments, `rainCall`
  and `glaciate` in 2 each.
- The losing pairs each fail for a reason you can name: a soak and `chainLightning` (one room per
  chain), two primers (nothing jolts), two bolts (the yard is dry).
- One replan takes about 0.4 s; the whole matrix under 5 s.

## Examples

### Example 1: Pull into the sump, then chain

**Given:** the player knows `provoke`, the mage knows `chainLightning`.

**When:** `win`

**Then:** the player walks into the sump (soaked) and provokes the yard: both drones are dragged into
the water. The mage chains the sump from the gate and all three short-circuit.

### Example 2: Rain, then a line bolt

**Given:** the player knows `rainCall`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** rain on the yard; the mage flashes from the gate to the forge, striking the yard, the sump
and the forge on the way: all three short-circuit.

### Example 3: Wash into the sump

**Given:** the player knows `tidalWave`, the mage knows `chainLightning`.

**When:** `win`

**Then:** the wave soaks the yard and washes both drones into the sump; one chain there takes all
three.

### Example 4: Trap - one room per chain

**Given:** the player knows `rainCall` (or `glaciate`), the mage knows `chainLightning`.

**When:** `win`

**Then:** no plan: the yard is soaked and chained, cog3 in the sump is out of the chain's room, and
nobody has the mana for a second one.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Eight pairs win | Exactly the eight measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | One bolt | Every winning plan casts exactly one bolt. |
