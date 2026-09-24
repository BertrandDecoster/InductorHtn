# Powder Keg

## Purpose

A crowd-control level (category 8): **one fire that spreads through the whole group - and a heavy
blow turned on the crowd.** Three old treants stand rooted in a rain-soaked grove. Wood burns (the
catalogue's `wooden` weakness), but they are drenched: fire cast on one only steams it dry (`steam`),
and an area that has caught fire does not catch again. They are `heavy` (nothing knocks or hooks
them) and `rooted` (a taunt cannot walk them anywhere). Two things burn hot enough to take them
through the wet, raw - the steam never gets a say:

- **The keg** of lamp oil on the ramp above the grove. Oil that catches fire blazes (`blaze`), and a
  blaze sets everyone else in its area alight at once.
- **The cinder priest's meteor**, the catalogue's magic heavy attack. Dazzled (`blinded`) or jolted
  (`electrocuted`), the priest calls it down on the area it stands in; the team gets one cast, then
  the blow falls on everyone there but the priest, and the area burns.

The player and the mage pick one skill each from a pool of seven. Nothing grants an outcome: `dead`
is the treants' catalogue weakness to burning.

The map is four coarse areas in a line: camp, ramp, grove, shrine. Only a hook or a taunt moves
something into another area, so the keg (an object: never taunted) comes down by a hook from the
grove - or over the **lip**, a feature of the ramp: a chute whose ability is `teleport(grove)`, so
whatever is knocked over it slides down into the grove. The priest (it walks) comes by a taunt or a
hook.

The level's goal is spelled out top-down from the need, "burn out the crowd's area":

| Method | First | Then |
|--------|-------|------|
| **Keg** | bring the fuse (anything a flame sets blazing over its area, read from `reactionFor/4`) to the crowd: `hook` it from the grove; `vortex` on the lip (everything on the ramp goes over); `tidalWave` on the ramp (the wave washes it over) | `fireball` the grove: the keg blazes, all three burn. Or lay the fire first and bring the keg into the flames. |
| **Meteor** | bring the striker (an enemy whose heavy blow burns where it stands) among the trees: `taunt` it (it walks after you) or `hook` it from the grove | set it off: `blindingFlash` in the grove (the flasher is disjoint: the meteor passes through), or `lightningFlash` into the grove from the ramp (the jolt sets it off at once; the caster dashes into the burning grove afterwards) |

Why no single skill works: a mover lights nothing; a fireball lights the crowd or the keg where they
stand, never both (on the keg it blazes alone on the ramp, and the spent keg that rolls down is only
burning, no longer oiled); the priest in its shrine, dazzled or jolted, burns only the shrine.

Skills serving two roles: `hook` fetches the keg or the priest; the two flashes each dazzle or jolt
the priest. `vortex` and `tidalWave` both knock the keg over the lip, and `taunt` herds the priest.

The traps: fire on the keg first (it blazes alone on the ramp); two movers or two fires; the wrong
mover (a taunt on the keg, a vortex on the priest); setting the priest off at home.

Level-local definitions (wishlist evidence): the lip, `effect(chute, target, teleport(grove))` - a
feature that moves what is knocked into it to another area, built from the existing `teleport(R)`
atom, because a knockback never changes the area and the keg is not an NPC a taunt can move;
`immune(keg, taunted)` - an object would otherwise chase its taunter.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp (player, mage) --- ramp (keg, oiled; lip) --- grove (t1, t2, t3) --- shrine (priest)
```

- **Links:** all walkable (`connected`).
- **Line of sight:** the camp sees the ramp and the grove; the ramp and the grove see each other; the
  grove sees the shrine.
- **Features:** `feature(ramp, lip, chute)`: whatever is knocked in lands in the grove.
- **Treants:** `wooden`, `wet`, `heavy`, `rooted`.
- **Priest:** `fireElemental` (the meteor does not burn it); `behavior(priest, blinded, meteor, here)`
  and `behavior(priest, electrocuted, meteor, here)`. The meteor is magic: a hook or a bash would
  interrupt it.
- **Companions:** 2 mana each (one wave, fireball or lightning flash). Sacrifice is allowed: a
  companion under the meteor burns, and the plan goes on.

## Hypothesis

Measured with `htn_components combos crowd_powder_keg` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 14 of 49 assignments win (7 unordered pairs, whichever companion holds which half): `fireball`
  with `hook`, `vortex` or `tidalWave` (the keg); `blindingFlash` or `lightningFlash` with `hook` or
  `taunt` (the meteor).
- 7 methods (distinct skill sets cast), in two kinds: a blaze (a fuse brought and lit) and a heavy
  blow turned on the crowd.
- Skill usage: `hook` 6, `fireball` 6, `taunt` 4, `blindingFlash` 4, `lightningFlash` 4, `vortex` 2,
  `tidalWave` 2. No dead skills. No solo plans. One replan takes 0.3 to 8 s (the meteor's window
  multiplies the answers).

## Examples

### Example 1: Over the lip, then light it

**Given:** the player knows `vortex`, the mage knows `fireball` (the default kit).

**When:** `win`

**Then:** the player's vortex on the lip knocks the keg over: it slides down into the grove. The
mage's fireball sets the grove alight: the treants only steam, but the keg blazes and all three burn.
(Or the fireball first, and the keg slides down into the flames.)

### Example 2: The meteor on the grove

**Given:** the player knows `taunt`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the player taunts the priest from the grove: it walks in among the trees. The mage walks
into the grove and flashes: dazzled, the priest winds up its meteor on the grove; the flasher is
disjoint, the meteor passes through it and burns the treants (and the player).

### Example 3: The hook, two roles

**Given:** the player knows `hook`; the mage `fireball`, `blindingFlash` or `lightningFlash`.

**When:** `win`

**Then:** with `fireball`, the hook drags the keg down from the ramp; with a flash, it drags the priest
out of its shrine.

### Example 4: Traps

**Given:** `fireball` twice; `hook` twice; `taunt` and `fireball`; `vortex` and `blindingFlash`;
`lightningFlash` twice.

**When:** `win`

**Then:** no plan. The keg lit on the ramp blazes alone; nothing lit; the keg does not walk; the vortex
moves nothing out of its area; the jolted priest burns its own shrine.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Seven pairs win | Exactly the seven measured pairs have a plan. |
| P3 | Each hand matters | Every winning pair wins whichever companion holds which half. |
| P4 | Through the wet | In every winning plan the treants die only after a blaze or a meteor blow. |
