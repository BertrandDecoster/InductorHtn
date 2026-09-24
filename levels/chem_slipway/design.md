# Slipway

## Purpose

An elemental-chemistry level about **a moment** and **reactions that cancel a soak**. A clockwork
crab, a **heavy machine**, squats on a slipway above a flooded dock. A jolt on a dry machine only
stuns it; soaked first, it short-circuits (catalogue: `machine`, `electrocuted` + `wet -> dead`). It
cannot swim (this level: `weakness(crab, deepWater, none, fell)`), but it is heavy, so nothing moves
it - until Turn to Mist takes `heavy` off it for a moment (through the next cast by anyone). The
player and the mage pick one skill each from a pool of seven.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Short it** | soak it: `tidalWave` | jolt it: `lightningFlash` |
| **Mist, then sink it** | `turnToMist`: for one cast it is not heavy | on the very next cast, move it into the dock: a push from the quay (`tidalWave`, `fireball`), a pull-in on the dock (`vortex`), or a drag across the dock from the gantry (`hook`, `taunt`): it falls in |

Why no single skill works:
- It is heavy: a push or a pull alone does nothing, and a hook drags the caster to it instead.
- A jolt on a dry machine only stuns it, and a stun is not out.
- The mist alone makes it light for a moment, and nothing moves it.

The chemistry is in the order of the tags: water then lightning kills; lightning then water only
stuns; fire then water puts the fire out (`extinguish`) and leaves it dry; water then fire dries it
(`steam`). So fireball and tidalWave never make a pair, though one burns and the other soaks.

Skills in two roles: `tidalWave` soaks for the short and pushes a misted crab into the dock.
`turnToMist` is the hub of the sinking method: five movers, one gate.

No zone reaction in this level: the catalogue's melting ice leaves a puddle, never the deep water it
covered, so a "freeze the dock, lure it on, melt it" method cannot be written (see the report).

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

- **Walking:** quay–slipway, slipway–berth, slipway–dock, quay–stairs, stairs–gantry.
- **Line of sight:** quay→slipway, quay→dock, gantry→slipway, gantry→dock.
- **Push lines:** from the quay, the slipway falls into the dock; from the gantry, the dock lies
  between it and the slipway (a drag from there crosses the water).
- **Zone:** dock `deepWater`.
- **Crab:** `machine`, `heavy`; this level's weakness: `deepWater -> fell` whether heavy or not.
  Both companions have 4 mana.
- **Level recipe:** none. The generic `neutralize` finds every method: `exploit` (the short: wet, then
  electrocuted) and `intoThePit` (take the `heavy` ward off, then send it into the dock).
- **Heavy attack:** none.

## Hypothesis

Measured with `htn_components combos chem_slipway`:

- No single skill wins, even when both companions hold it: 0 of 7.
- **12 of 49** assignments win (6 unordered pairs, in either seat). **6 methods** of two kinds (a
  weakness, a hazard drop), no solo plans, no dead skills:
  - short it: tidalWave x lightningFlash;
  - mist, then sink it: turnToMist x {tidalWave, fireball, hook, vortex, taunt}.
- Skill usage: turnToMist 10, tidalWave 4, and 2 each for lightningFlash, fireball, hook, vortex,
  taunt.
- Losing pairs, each for a named reason: two movers (heavy), a mover and a jolt (heavy, dry), fire and
  water (they cancel), mist and a jolt (light, but nothing moves it).

## Examples

### Example 1: Soak, then jolt

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player's wave soaks the crab (its push does nothing to the heavy crab). The mage's
lightning flash strikes the wet machine: it short-circuits (`dead`).

### Example 2: Mist, then hook across the dock

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the mage walks up to the gantry. The player turns the crab to mist; for that moment it is
not heavy, and the mage's hook drags it across the dock. It falls in (`fell`).

### Example 3: Mist, then wash it in

**Given:** the player knows `tidalWave`, the mage knows `turnToMist`.

**When:** `win`

**Then:** the mage mists the crab; the player's wave from the quay soaks it and washes it off the
slipway into the dock (`fell`).

### Example 4: Fire, then water is steam, not a soak

**Given:** the player knows `fireball`, the mage knows `tidalWave`.

**When:** `win`

**Then:** no plan. After the fireball, the wave only puts the fire out (`extinguish`), and the crab
stays dry.

### Example 5: A dry jolt only stuns

**Given:** the player knows `lightningFlash`, the mage knows `hook`.

**When:** `cast(player, lightningFlash, crab)`

**Then:** the crab is stunned (`opExploit(crab, electrocuted, stunned)`), not out; the pair finds no
plan.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Six pairs win, in either hand | Exactly the six measured pairs have a plan, whichever companion holds which half. |
| P3 | The mist lasts one cast | Mist, a wasted wave, then a wave from the quay: the crab is heavy again and stays put. |
| P4 | Heavy stops every mover | A hook on the heavy crab drags the caster to it; hook + vortex and fireball + taunt find no plan. |
