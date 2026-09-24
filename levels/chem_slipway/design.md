# Slipway

## Purpose

An elemental-chemistry level on the ability catalogue. A clockwork crab, a **heavy machine**, squats
on a slipway above a flooded dock. The player and the mage pick one skill each from a pool of eight.
Nothing grants the crab an outcome. It has two weaknesses, and each needs two different kinds of step:

| Method | First | Then |
|--------|-------|------|
| **Short it** (a wet machine, jolted, is dead) | soak it: `rainCall`, `tidalWave` | jolt it: `zap`, `chainLightning` |
| **Slide it** (the heavy sink in deep water) | oil it: `oilFlask`, `tarPot`. This level's physics says an oiled heavy thing slides: `suspends(oiled, forcedMove)` | move it into the dock: `gust` or `tidalWave` push it from the quay; `magnetize` hooks it across the dock from the gantry |

Why no single skill works:
- It is heavy, so a push or a hook alone does nothing. A hook on the dry crab drags the caster to it
  instead.
- A jolt on a dry machine only stuns it, and a stun is not out.
- Oil alone makes it slippery, but nothing moves it.
- The primer never pays off its own setup, so one companion cannot do both halves even when both
  hold the same skill.

`tidalWave` has two roles: it soaks the crab for the jolt, and its area push slides an oiled crab
into the dock. That is the chemistry: water and oil on the same shell do different things.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
quay (player, mage) --- slipway (crab) --- berth
  |                        |
stairs                    dock  (deepWater)
  |
gantry   (across the dock, facing the slipway)
```

- **Lines:** a push from the quay on the slipway lands in the dock. From the gantry, the dock lies
  between it and the slipway, so a hook from there drops the crab in.
- **Line of sight:** the quay and the gantry both see the slipway.
- **Zones:** the dock is `deepWater`. It soaks whoever arrives, and the heavy sink (`fell`).
- **Crab:** machine, heavy. Both companions have 4 mana.
- **Level physics:** `suspends(oiled, forcedMove)`: oil lets a heavy thing be moved.

## Hypothesis

Measured with `htn_components combos chem_slipway`:

- No single skill wins, even when both companions hold it: 0 of 8.
- **20 of 64** assignments win (10 unordered pairs, and each works whichever companion holds which
  half). There are **10 methods** (distinct sets of skills cast) of two kinds, and no dead skills:
  - short it: {rainCall, tidalWave} x {zap, chainLightning}, 4 pairs;
  - slide it: {oilFlask, tarPot} x {gust, tidalWave, magnetize}, 6 pairs.
- Skill usage: tidalWave 8, oilFlask 6, tarPot 6, and 4 each for the rest.
- The other pairs lose, and each for a reason you can name: two movers (it is too heavy), a mover
  and a jolt (it is dry and heavy), oil and a jolt (oil does not conduct), rain and oil (nothing
  moves it).

## Examples

### Example 1: Oil, then push

**Given:** the player knows `oilFlask`, the mage knows `gust`.

**When:** `win`

**Then:** the player oils the crab. The mage's gust slides it off the slipway into the dock, where it
sinks (`fell`).

### Example 2: Tar, then hook across

**Given:** the player knows `tarPot`, the mage knows `magnetize`.

**When:** `win`

**Then:** the tar oils the crab. The mage climbs the stairs to the gantry and hooks it across the
dock, and it falls in on the way.

### Example 3: Soak, then jolt

**Given:** the player knows `rainCall`, the mage knows `zap`.

**When:** `win`

**Then:** the rain soaks it, and the jolt short-circuits it (`dead`).

### Example 4: The wave serves two roles

**Given:** `tidalWave` with `chainLightning`, or `tidalWave` with `oilFlask`.

**When:** `win`

**Then:** with the lightning, the wave is the soak (`dead`). With the oil, the wave is the push
(`fell`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Ten pairs win | Exactly the ten measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | Dry jolt, dry push fail | zap + gust (dry, unoiled) and tidalWave + magnetize (wet but not oiled) find no plan. |
