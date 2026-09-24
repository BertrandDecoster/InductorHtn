# Sync: The Vault

## Purpose

A synchronisation level: **two plates held at once**. The vault door opens only once both of its
plates are weighed down at the same time (`plateFor/2` + `openWhenHeld`). One plate stands on an
island across a rift; the other lies in the warden's forge, behind a grate (a wall you can see
through), on a floor of lava no companion can set foot on. A barrel stands in the forge beside the
warden. Two companions, the player and the mage, pick one skill each from a pool of six, with two
mana each. Whoever holds the island plate is stranded there: leaving the island leaves the plate.
The other must weigh the forge plate down with the barrel, through the grate, and then walk into the
vault.

The warden is heavy: nothing knocks it. It answers a taunt with a telegraphed `groundSlam` where it
stands. Walled in, it cannot walk after its taunter, so the taunt breaks and the slam falls on its
own forge: everything there but the warden is knocked down and thrown - the barrel onto the plate.
Nobody stands in the forge, so there is no window to answer.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The island** | a `gap` from the rim: no walking over | teleport onto it (`blink`), dash over (`lightningFlash`), or hook the anchored pillar on it (`hook`: the hook drags you over). Then step on the plate and stay |
| **The forge** | a `wall` from the hall and a lava floor: no companion gets in (a blink would land in lava, so it never does) | knock the barrel onto the plate through the grate: `fireball` it, `vortex` the plate, or `taunt` the warden and let its own slam throw it |
| **The vault** | the vault door (a `doorway`) opens only when both plates are held at once | the one left in the hall walks in |

Why no single skill works:
- The island skills move only their caster, and none reaches into the forge (the wall stops a
  dash, a hook and any melee; the lava stops a blink).
- The forge skills cannot cross the rift, and the island plate holds only a companion.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
rim ~~rift (gap)~~ island (pillar) [islandPlate]
 |
hall ==vaultdoor== vault
 :
grate (wall, line of sight)
 :
forge (lava: warden, barrel) [forgePlate]
```

- **Areas (5):** hall, rim, island, forge, vault. Links: walkable hall-rim; a `gap` rim-island; a
  `wall` hall-forge; a `doorway` (the vault door) hall-vault.
- **Lines of sight:** the hall sees the forge (through the grate); the rim sees the island.
- **Zone:** lava on the forge.
- **Features:** `islandPlate` on the island, `forgePlate` in the forge; both `plateFor(_, vaultdoor)`
  with `openWhenHeld(vaultdoor)`.
- **Warden:** living, heavy, fire elemental (lava does not take it),
  `behavior(warden, taunted, groundSlam, here)`.
- **Things:** a pillar on the island (heavy: a hook anchor), a barrel in the forge.
- **Goal:** `win` = `weighIsland(?a)` (`reach` the island, step on its plate), `weighForge(?a)` (the
  other companion knocks the barrel onto the forge plate with `knockOn`, or taunts the warden; the
  barrel must be on the plate), the door must be open, then someone not on the island walks into
  the vault.

## Hypothesis

Measured with `htn_components combos sync_vault` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 18 of the 36 assignments win: each island skill (`blink`, `lightningFlash`, `hook`) with each forge
  skill (`fireball`, `vortex`, `taunt`), whichever companion holds which half (9 pairs).
- 9 methods (distinct sets of skills cast), 0 solo plans, no dead skill; every skill is used by 6
  winning assignments.
- One replan takes well under a second.

## Examples

### Example 1: Blink to the island, fireball the barrel

**Given:** the player knows `blink`, the mage knows `fireball` (the default kit).

**When:** `win`

**Then:** the player walks to the rim, blinks onto the island and steps on its plate. From the hall,
through the grate, the mage's fireball sets the forge alight and knocks the barrel onto the forge
plate: both plates are held, the vault door opens, and the mage walks in.

### Example 2: Hook the pillar, taunt the warden

**Given:** the player knows `hook`, the mage knows `taunt`.

**When:** `win`

**Then:** the player hooks the pillar and is dragged over the rift, then steps on the island plate.
The mage taunts the warden through the grate: walled in, it cannot follow, and the taunt breaks; it
slams its own forge, and the blow knocks the barrel onto the plate. The door opens; the mage walks
in.

### Example 3: Flash over, vortex the plate

**Given:** the player knows `lightningFlash`, the mage knows `vortex`.

**When:** `win`

**Then:** the player dashes over the rift and holds the island plate. The mage's vortex on the forge
plate draws the barrel onto it (the heavy warden stays, rooted for a moment). The door opens.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the 9 island-by-forge pairs have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | The door waits for both plates | One plate held does not open it; the second one pressed does. |
| P5 | Nobody sets foot in the forge | No companion ever moves into the forge; only the barrel presses its plate. |
| P6 | The warden does not budge | No plan knocks the warden anywhere. |
| P7 | The island holder stays | The door opens while the island holder is still on its plate; the other walks into the vault. |
