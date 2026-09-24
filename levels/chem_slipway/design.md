# Slipway

## Purpose

An elemental-chemistry level about **a moment** and **reactions that cancel a soak**. A clockwork
crab, a **heavy machine**, squats on a slipway above the flooded dock. A jolt on a dry machine only
stuns it; soaked first, it short-circuits (catalogue: `machine`, `electrocuted` + `wet -> dead`). It
cannot swim, heavy or not (this level: `weakness(crab, deepWater, none, fell)`), but it is heavy, so
nothing knocks or pulls it - until Turn to Mist takes `heavy` off it for a moment (through the next
cast by anyone). The dock is deep water at the slipway's edge (a feature); the gantry stands across
the dock channel (a gap); the berth beside the slipway is awash (a `puddle` zone). The player and the
mage pick one skill each from a pool of eight.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Short it** | soak it: a `tidalWave` in the slipway, or lure it through the berth (`taunt` from the berth: it walks in and is soaked) | jolt it: `lightningFlash` from next door, or `blindingFlash` beside it (with the wave, a one-area short circuit) |
| **Mist, then sink it** | `turnToMist`: for one cast it is not heavy | on the very next cast, knock it into the dock or the channel (`tidalWave`, `fireball`, a `vortex` on the dock), or `hook` it from the gantry across the channel: it falls in |

Why no single skill works:
- It is heavy: a knock or a pull alone does nothing, and a hook drags the caster to it instead.
- A jolt on a dry machine only stuns it, and a stun is not out.
- The mist alone makes it light for a moment, and nothing moves it.

The chemistry is in the order of the tags: water then lightning kills; lightning then water only
stuns; fire then water puts the fire out (`extinguish`) and leaves it dry; water then fire dries it
(`steam`). So fireball and tidalWave never make a pair, though one burns and the other soaks.

Skills in two roles: `tidalWave` soaks for the short and knocks a misted crab into the dock; `taunt`
is a soak (a lure through the berth); `turnToMist` is the hub of the sinking method: four movers,
one gate.

No zone reaction in this level: the catalogue's melting ice leaves a puddle, never the deep water it
covered, so a "freeze the dock, lure it on, melt it" method cannot be written (see the wishlist).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
quay (player, mage) ---- slipway (crab; dock) ---- berth (puddle)
  |                         :
gantry ....... gap .........:
```

- **Areas:** 4. **Links:** walkable quay-slipway, slipway-berth, quay-gantry; a `gap` (the dock
  channel) between the gantry and the slipway.
- **Line of sight:** quay->slipway, quay->berth, berth->slipway, gantry->slipway.
- **Features:** `dock` in the slipway (`deepWater`: wet, and the crab cannot swim).
- **Zones:** berth `puddle`.
- **Crab:** `machine`, `heavy`; this level's weakness: `deepWater -> fell` whether heavy or not. Both
  companions have 4 mana.
- **Level recipe:** none. The generic `neutralize` finds every method: `exploit` (the short: a wave,
  or a taunt into the puddle zone, then a jolt) and `intoThePit` (take the `heavy` ward off, then
  `sendDown`: knock it into the dock, or drop it in the channel).
- **Heavy attack:** none. **Terrain use:** the dock feature and the channel gap (knock and pull
  targets), the berth zone (a lure soaks).

## Hypothesis

Measured with `htn_components combos chem_slipway`:

- No single skill wins, even when both companions hold it: 0 of 8.
- **16 of 64** assignments win (8 unordered pairs, in either seat). **8 methods** of two kinds (a
  weakness, a hazard drop), no solo plans, no dead skills:
  - short it: {tidalWave, taunt} x {lightningFlash, blindingFlash};
  - mist, then sink it: turnToMist x {tidalWave, fireball, hook, vortex}.
- Skill usage: turnToMist 8, tidalWave 6, and 4 each for lightningFlash, blindingFlash, taunt; 2 each
  for fireball, hook, vortex.
- Losing pairs, each for a named reason: two movers (heavy), a mover and a jolt (heavy, dry), fire and
  water (they cancel), mist and a jolt (light, but nothing moves it), mist and a taunt (a lure walks
  it, never into the water), two soaks or two jolts.

## Examples

### Example 1: Soak, then jolt

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player walks onto the slipway and bursts a wave that soaks the crab (its knockback does
nothing to the heavy crab). The mage's lightning flash strikes the wet machine: it short-circuits
(`dead`).

### Example 2: Lure it through the berth, then flash

**Given:** the player knows `taunt`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the player walks into the flooded berth and taunts the crab; it walks after the player into
the puddle and is soaked. The mage walks in and flashes: everyone around is blinded and electrocuted,
and the wet machine short-circuits.

### Example 3: Mist, then hook across the channel

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the player turns the crab to mist. The mage walks round to the gantry and hooks it across
the channel: it falls in (`fell`).

### Example 4: Mist, then vortex into the dock

**Given:** the player knows `turnToMist`, the mage knows `vortex`.

**When:** `win`

**Then:** the mage's vortex on the dock knocks the misted crab into the deep water (`fell`).

### Example 5: Fire, then water is steam, not a soak

**Given:** the player knows `fireball`, the mage knows `tidalWave`.

**When:** `win`

**Then:** no plan. After the fireball, the wave only puts the fire out (`extinguish`), and the crab
stays dry.

### Example 6: A dry jolt only stuns

**Given:** the player knows `lightningFlash`, the mage knows `hook`.

**When:** `cast(player, lightningFlash, crab)`

**Then:** the crab is stunned (`opExploit(crab, electrocuted, stunned)`), not out; the pair finds no
plan.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Eight pairs win, in either hand | Exactly the eight measured pairs have a plan, whichever companion holds which half. |
| P3 | The mist lasts one cast | Mist, a wasted wave, then a wave on the slipway: the crab is heavy again and stays put. |
| P4 | Heavy stops every mover | A hook on the heavy crab drags the caster to it; hook + vortex and fireball + taunt find no plan. |
| P5 | The berth only soaks | A misted crab hooked from the berth lands in the puddle: wet, not sunk. |
