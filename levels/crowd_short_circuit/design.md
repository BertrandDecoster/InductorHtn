# Short Circuit

## Purpose

A crowd-control level (category 8): **too many enemies to take one by one; shape them as a group,
then one blow takes the group.** Three clockwork drones guard the yard of an old foundry. A drone is
a machine: a jolt on a dry one only stuns it, a jolt on a wet one short-circuits it (dead). A jolt is
an area effect - `lightningFlash` electrocutes everyone in the area it strikes, `blindingFlash`
everyone around the caster - so once the crowd is soaked, one jolt takes it. `lightningFlash` costs
all of a companion's mana: a bolt on dry drones is spent. Or leave the jolts alone:

- **the slag pit** in the forge (a `lava` feature): drones knocked in are lost;
- **the ogre** who works the forge stamps the rotten floor through (`caveIn`, the catalogue's
  physical heavy attack) when it is dazzled (`blinded`) or jolted (`electrocuted`). Whatever is in its
  area falls - the drones, the ogre itself, and any companion who stayed there (sacrifice is
  allowed).

Two companions, the player and the mage, pick one skill each from a pool of seven. Nothing grants an
outcome: `dead` comes only from the catalogue's machine weakness, `fell` only from the lava and the
chasm.

The map is four coarse areas around a hub: the yard (the drones, and a coolant pool: wet), the gate
(the companions), the sump (flooded: whoever walks in is soaked) and the forge (the ogre, the slag).
Only a taunt (the drone walks after you) or a hook (one area at a time) moves a drone or the ogre to
another area; a knockback only throws it into a feature of its own area.

The level's goal is spelled out top-down from the need: take the first drone still standing out of
the fight (`takeOut`), and repeat - an area effect takes the rest with it. `takeOut` is one of:

| Method | First | Then |
|--------|-------|------|
| **Short them** (a weakness) | soak the whole crowd (`primeCrowd(wet)`): `tidalWave` among them, `vortex` on the coolant pool, `shieldBash` each into the pool, or herd them into the sump (`taunt`, `hook`) | one jolt: `lightningFlash` into their area, or `blindingFlash` among them |
| **Drop them** (a hazard) | herd the crowd into the forge (`herdCrowd`: `taunt`, `hook`) | knock them into the slag: `vortex` (the whole forge), `tidalWave` (everyone around), `shieldBash` (one at a time) |
| **Turn the ogre on them** (a heavy blow) | bring the ogre among the drones (`taunt`, `hook`) - or the drones to the ogre | set it off: `blindingFlash` among them (the flasher is disjoint, but the floor still gives way under it), `lightningFlash` into their area (the caster's dash never lands in the chasm) |

Why no single skill works: a soak or a herd leaves the drones standing; a jolt on dry drones only
stuns them; a knock throws nothing that matters out of the yard; the slag and the ogre are in the
forge, and only a mover brings the drones there (or the ogre here).

Skills serving two roles: `vortex`, `tidalWave` and `shieldBash` soak in the yard in one plan and
knock into the slag in another; `taunt` and `hook` herd into the water, into the forge, or bring the
ogre; the two flashes jolt the soaked crowd or set the ogre off.

The traps: two soaks, two herders, two jolts (each half alone does nothing); a bolt first (dry drones
are only stunned, and there is no second bolt); jolting the ogre alone in its forge (the floor gives
way under nobody that matters).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
                     sump (puddle)
                        |
gate (player, mage) --- yard (cog1, cog2, cog3; coolant) --- forge (ogre; slag)
```

- **Links:** all walkable (`connected`); the yard is the hub.
- **Line of sight:** the gate sees the yard; the yard, the sump and the forge see each other.
- **Zones:** the sump is a `puddle`.
- **Features:** `feature(yard, coolant, puddle)` (wet); `feature(forge, slag, lava)` (a pit).
- **Drones:** `machine`. **Ogre:** `living`; `behavior(ogre, blinded, caveIn, here)`,
  `behavior(ogre, electrocuted, caveIn, here)`.
- **Companions:** 2 mana each (one wave or one lightning flash). Sacrifice is allowed.

## Hypothesis

Measured with `htn_components combos crowd_short_circuit` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 32 of 49 assignments win (16 unordered pairs, whichever companion holds which half): the pool is
  three kinds - soakers/knockers (`tidalWave`, `vortex`, `shieldBash`), movers (`taunt`, `hook`) and
  jolts (`lightningFlash`, `blindingFlash`) - and every pair of two different kinds wins; no pair of
  the same kind does.
- 16 methods (distinct skill sets cast), in three kinds: a short (a weakness), a drop into the slag
  (a hazard), and the ogre's cave-in (a heavy blow turned on the crowd).
- Skill usage: `taunt` 10, `hook` 10, `lightningFlash` 10, `blindingFlash` 10, `tidalWave` 8,
  `vortex` 8, `shieldBash` 8. No dead skills. No solo plans. One replan takes 0.2 to 12 s.

## Examples

### Example 1: Soak the yard, then one bolt

**Given:** the player knows `vortex`, the mage knows `lightningFlash` (the default kit).

**When:** `win`

**Then:** the vortex on the coolant pool knocks the whole yard into it: three soaked drones. The
mage's flash of lightning into the yard short-circuits all three.

### Example 2: Herded into the slag

**Given:** the player knows `taunt`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the player taunts the drones from the forge: they walk after it. The mage walks into the
forge and bursts a wave: everyone around is soaked and thrown into the slag (the ogre, and perhaps
the player, too).

### Example 3: The floor gives way

**Given:** `hook` and `blindingFlash`; `taunt` and `lightningFlash`.

**When:** `win`

**Then:** the ogre is hooked (or taunted) out of its forge into the yard. The flash dazzles it (or the
bolt jolts it, and the drones, only stunned): it stamps the yard through, and everything in it falls.

### Example 4: One skill, two roles

**Given:** `vortex`, `shieldBash` or `tidalWave` for the player; a jolt or a mover for the mage.

**When:** `win`

**Then:** with a jolt, they soak the drones in the yard (the coolant pool, the wave); with a mover,
they throw the herded drones into the slag.

### Example 5: Traps

**Given:** `lightningFlash` and `blindingFlash`; `tidalWave` and `vortex`; `taunt` and `hook`.

**When:** `win`

**Then:** no plan. The dry drones are only stunned (and the ogre is alone in its forge); nothing jolts;
nothing knocks or jolts.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Sixteen pairs win | Exactly the measured pairs have a plan: every pair of two different kinds. |
| P3 | Each hand matters | Every winning pair wins whichever companion holds which half. |
| P4 | Shorted wet, or dropped | In every winning plan all three drones are out: electrocuted (wet), or fallen into the lava or the chasm. |
