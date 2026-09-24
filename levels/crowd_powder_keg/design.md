# Powder Keg

## Purpose

A crowd-control level (category 8): **one fire that spreads through the whole group - and a heavy
blow turned on the crowd.** Three old treants stand rooted in a rain-soaked grove. Wood burns (the
catalogue's `wooden` weakness), but they are drenched: fire cast on one only steams it dry
(`steam`), and a region that has caught fire does not catch again. They are `heavy`: nothing drags
or pushes them. Two things burn hot enough to take them through the wet:

- **The keg** of lamp oil up the ramp. Oil that catches fire blazes (`blaze`), and a blaze sets
  everyone else in the region alight at once, raw: the steam never gets a say.
- **The cinder priest's meteor**, the catalogue's magic heavy attack. Taunted, the priest is dragged
  to its taunter; taunted or dazzled (`blinded`), it winds up a meteor on the region it stands in.
  The team gets one cast, then the region burns, raw. No plan may leave a companion in it.

The player and the mage pick one skill each from a pool of six. Nothing grants an outcome: `dead`
is the treants' catalogue weakness to burning.

The level's goal is spelled out top-down from the need, "burn out the crowd's region":

| Method | First | Then |
|--------|-------|------|
| **Keg** | bring the fuse (anything a flame sets blazing over its region, read from `reactionFor/4`) to the crowd: `tidalWave` from the camp (it rolls down the ramp), `vortex` on the grove, `hook` or `taunt` from the grove | `fireball` the grove: the keg blazes, all three burn. Or lay the fire first and bring the keg into it. |
| **Meteor, provoked** | `taunt` the priest from the grove: it is dragged in and winds up on the grove | in the wind-up the other companion pulls the taunter out: `hook` (the taunter is dragged to the camp) or `vortex` on the ramp (the taunter and the priest are sucked out; the heavy treants stay) |
| **Meteor, dazzled** | `vortex` on the grove: the keg and the priest are sucked in | `blindingFlash` from the grove (disjoint: the meteor passes through the flasher), the ramp or the shrine |

Why no single skill works: a mover lights nothing; a fireball lights the crowd or the keg where they
stand, never both (on the keg from the camp it blazes alone on the ramp before its push rolls it
down); the taunter is always in the meteor's region and has no second skill to leave it;
companions cannot be taunted, so no friend can taunt you out of the way.

Skills serving several roles: `vortex` fetches the keg, fetches the priest, or pulls a friend out
from under the meteor; `taunt` fetches the keg or provokes the priest; `hook` fetches the keg or
rescues the taunter.

The traps: fire on the keg first (it blazes alone on the ramp); two movers or two fires; hooking the
priest into the grove and flashing it (the hooker is still under the meteor); taunting the priest
from anywhere but the grove (the meteor falls on the taunter's region, not on the trees).

Level-local facts (wishlist evidence): `immune(player, taunted)` and `immune(mage, taunted)` - without
them a second taunter drags the first out of the wind-up, and taunt alone wins.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp (player, mage) --- ramp (keg, oiled) --- grove (t1, t2, t3; wooden, wet, heavy) --- shrine (priest)
```

- **Line of sight:** the camp sees the ramp and the grove; the ramp and the grove see each other;
  the grove sees the shrine.
- **Lines:** a push from the camp on the ramp lands in the grove (the keg rolls down).
- **Keg:** an object, `oiled`. **Treants:** `wooden`, `wet`, `heavy`.
- **Priest:** an enemy, `fireElemental` (its own fire does not touch it);
  `behavior(priest, taunted, meteor, here)` and `behavior(priest, blinded, meteor, here)`.
- **Companions:** 2 mana each (one wave or fireball); immune to `taunted`.
- **The team:** a plan that leaves a companion stunned is refused (`teamFit`).

## Hypothesis

Measured with `htn_components combos crowd_powder_keg` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 14 of 36 assignments win (7 unordered pairs, whichever companion holds which half): `fireball`
  with `tidalWave`, `vortex`, `hook` or `taunt` (the keg); `taunt` with `hook` or `vortex`, and
  `vortex` with `blindingFlash` (the meteor).
- 7 methods, in two kinds (a reaction spread by a fuse; an enemy's heavy attack turned on its
  allies). Skill usage: `fireball` 8, `vortex` 6, `taunt` 6, `hook` 4, `tidalWave` 2,
  `blindingFlash` 2. No dead skill.
- No solo plans. One replan takes under a second.

## Examples

### Example 1: Roll the keg down, then light it

**Given:** the player knows `tidalWave`, the mage knows `fireball` (the default kit).

**When:** `win`

**Then:** the wave from the camp soaks the keg and rolls it down into the grove. The fireball on the
grove steams the treants, then reaches the keg: it blazes (the oil was there first), and all three
treants burn.

### Example 2: Taunt the priest, be hooked out

**Given:** the player knows `taunt`, the mage knows `hook`.

**When:** `win`

**Then:** the player walks into the grove and taunts the priest: it is dragged in and winds up a
meteor on the grove. In the wind-up the mage hooks the player back to the camp. The meteor falls:
all three treants burn.

### Example 3: Gather and dazzle

**Given:** the player knows `vortex`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the vortex on the grove sucks in the keg and the priest. The mage flashes from the grove
(disjoint: the meteor passes through), the ramp or the shrine; the dazzled priest calls the meteor
down on the grove.

### Example 4: Traps

**Given:** `fireball` twice; `taunt` twice; `hook` and `blindingFlash`; `tidalWave` and `vortex`.

**When:** `win`

**Then:** no plan.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Seven pairs win | Exactly the seven measured pairs have a plan. |
| P3 | Each hand matters | Every winning pair wins whichever companion holds which half. |
| P4 | One fire takes the crowd | Every winning plan has exactly one blaze or one meteor, all three treants die of it, and no companion stands under a blow unless disjoint. |
| P5 | The meteor needs two hands | Every meteor plan has a wind-up and casts by both companions. |
