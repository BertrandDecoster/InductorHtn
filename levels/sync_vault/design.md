# Sync: The Vault

## Purpose

A synchronisation level: **a door with two plates that must be weighed down at the same moment**
(the `plateFor/2` + `openWhenHeld(D)` door of `ab_effects`). One plate is on an island across a
rift. The other is in a closet that a warden watches from its post. A barrel stands on the post
beside the warden. Two companions, the player and the mage, pick one skill each from a pool of
seven. Whoever takes the island plate is stranded there, so the other one has to do the closet. This
is Portal 2 co-op's two-button door, with one twist: the enemy's own blow can put the weight on the
plate.

The warden is a heavy boss: nothing moves it and nothing stuns it. It answers a taunt with a
telegraphed `groundSlam` on its own post. The slam is heavy and physical, so it cannot be stopped.
It knocks down everyone on the post except the warden and throws them into the closet. Bait it, and
its blow throws the barrel onto the plate. No companion may be standing on the post when it lands.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The island** | a rift (chasm): nobody walks over it | from the rim: teleport onto the outcrop (`blink`), dash there (`lightningFlash`), hook the anchored pillar there and be dragged over (`hook`); then walk onto the plate |
| **The closet** | the warden watches it: nobody walks in seen; there is no line of sight in, so nothing teleports or dashes in | blind the warden and walk in (`blindingFlash` from the hall); put the barrel on the plate: push it off the post from the hall (`fireball`, `tidalWave`), or `taunt` the warden so that its slam throws the barrel |

Why no single skill works:
- The island skills only move their caster, and only over the rift.
- The closet skills never cross the rift.
- The warden is heavy: pushes, pulls and the wave move only the barrel. It is a boss, so a stun does
  not land.
- A hook on the barrel drags it to the hooker, away from the plate. A hook on the warden drags the
  hooker to the warden.
- One companion can never hold both plates, and the island holder cannot come back.

The methods differ in kind on both sides. The island is reached by a teleport, a dash or a
grappling hook. The closet is done by a blinded watcher, a push, or the enemy's own blow used as the
push.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
foyer (player, mage) --- hall --- rim ~~ rift (chasm) ~~ outcrop (pillar) --- island [plate]
                          |  \
                          |   post (warden, barrel) --- closet [plate, watched by the warden]
                          |
                      vaultdoor (door: both plates at once) --- vault
```

- **Plates:** `plateFor(island, vaultdoor)`, `plateFor(closet, vaultdoor)`. Each plate region is a
  zone with `openWhenHeld(vaultdoor)`, so the door latches open the moment the second plate is
  weighed down.
- **Lines of sight:** foyer-hall, hall-rim, rim-outcrop, hall-post. None into the closet.
- **Push lines:** from the hall, a push on the post lands in the closet. So does the warden's slam
  on its own post (`beyond(post, post, closet)`).
- **Warden:** living, heavy, `rank(warden, boss)`, `watches(warden, closet)`,
  `behavior(warden, taunted, groundSlam, here)`.
- **Outcrop:** a heavy pillar, an anchor for a hook. The island plate starts empty.
- **Route:** `progress/2` only rises across the rift, so leaps go from the rim to the outcrop or
  the island.
- **Goal:** `win` = `weighIsland` (`reach` the island), `weighCloset`, confirm the door opened, then
  someone walks into the vault. The level's own methods name the closet options: blind and walk in,
  `place(barrel, closet)`, or a taunt followed by a check that the barrel is on the plate.

## Hypothesis

Measured with `htn_components combos sync_vault` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 24 of the 49 assignments win: each of the 3 island skills with each of the 4 closet skills,
  whichever companion holds which half (12 pairs).
- 12 methods (distinct sets of skills cast), 0 solo plans, no dead skill. Usage: blink,
  lightningFlash, hook 8 each; blindingFlash, fireball, tidalWave, taunt 6 each.
- Every losing pair has a reason: two island skills (nobody weighs the closet), or two closet skills
  (nobody crosses).
- One replan takes under 3 s.

## Examples

### Example 1: Blink to the island, fireball the barrel

**Given:** the player knows `blink`, the mage knows `fireball`.

**When:** `win`

**Then:** the player blinks from the rim onto the outcrop and walks onto the island plate. From the
hall, the mage fireballs the barrel off the post onto the closet plate, and the door opens. The mage
walks into the vault.

### Example 2: Hook over, the warden throws the barrel

**Given:** the player knows `hook`, the mage knows `taunt`.

**When:** `win`

**Then:** the player hooks the pillar and is dragged over the rift onto the outcrop, then walks onto
the plate. The mage taunts the warden from the hall. Heavy, the warden is not dragged anywhere; it
winds up a ground slam on its own post. Nobody is in danger, so the blow lands and throws the barrel
into the closet, and the door opens.

### Example 3: Flash over, blind and walk in

**Given:** the player knows `blindingFlash`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the mage dashes over the rift and walks onto the island plate. The player flashes in the
hall, which blinds the warden next door, then walks through the post onto the closet plate.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the 12 island-by-closet pairs have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | The door waits for both plates | The island plate alone leaves the door shut; the second plate opens it. |
| P5 | The slam throws only the barrel | In every taunt plan, the only thing the blow moves is the barrel, into the closet. |
| P6 | The warden does not budge | Fireball and tidal-wave plans never move the warden. |
