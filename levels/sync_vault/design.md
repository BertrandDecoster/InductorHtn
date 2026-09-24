# Sync: The Vault

## Purpose

A synchronisation level: **a door with two plates that must be weighed down at the same moment**
(the `plateFor/2` + `openWhenHeld(D)` door of `ab_effects`). One plate is on an island across a
rift, the other in a closet a sentry keeps its eye on. Two companions, the player and the mage,
pick one skill each from a pool of eight. Whoever takes the island plate is stranded there, so the
closet has to be done by the other one. Portal 2 co-op's two-button door, with one twist: the enemy
can be the weight.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The island** | a rift (chasm): nobody walks over it | dash onto the outcrop (`pounce`, `charge`); hook the anchored pillar there (`magnetize`); swap with the barrel there (`translocate`) - then walk onto the plate |
| **The closet** | the sentry watches it: nobody walks in seen; no line of sight in, so nothing dashes in | walk in stealthed (`vanish`); walk in once the sentry is blinded (`flashbang`, `net`); shove the sentry itself off its post onto the plate (`gust`) |

Why no single skill works:
- The island skills only move their caster, and only over the rift.
- The closet skills never cross the rift.
- The sentry is a boss: `charge`'s stun and `translocate`'s confusion are hard control and do not
  land, so neither blinds it. `flashbang` and `net` land the `blinded` atom itself.
- The sentry's watch belongs to the sentry, not to its post: swapping it away (`translocate`),
  dragging it (`magnetize`) or dashing up to it (`pounce`, `charge`) leaves the closet watched.
- One companion can never hold both plates, and the island holder cannot come back.

The two kinds of method differ in kind on both sides: a dash, a hook or a swap for the island;
stealth, a blinded watcher, or the enemy used as a counterweight for the closet.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
foyer (player, mage) --- hall --- rim ~~ rift (chasm) ~~ outcrop (pillar, barrel) --- island [plate]
                          |  \
                          |   post (sentry) --- closet [plate, watched by the sentry]
                          |
                      vaultdoor (door: both plates at once) --- vault
```

- **Plates:** `plateFor(island, vaultdoor)`, `plateFor(closet, vaultdoor)`; each plate region is a
  zone with `openWhenHeld(vaultdoor)`. The door latches open the moment both are weighed down.
- **Lines of sight:** foyer-hall, hall-rim, rim-outcrop, hall-post. None into the closet.
- **Push line:** from the hall, a push on the post lands in the closet.
- **Sentry:** living, `rank(sentry, boss)`, `watches(sentry, closet)`.
- **Outcrop:** a heavy pillar (an anchor for a hook) and a light barrel (a swap partner). They stand
  off the plate, so the island plate starts empty.
- **Goal:** `win` = `weighIsland`, `weighCloset`, confirm the door opened, then someone walks into
  the vault. The level's own methods name the closet options (stealth, blind, shove).

## Hypothesis

Measured with `htn_components combos sync_vault` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 32 of the 64 assignments win: each of the 4 island skills with each of the 4 closet skills,
  whichever companion holds which half (16 pairs).
- 16 methods (distinct sets of skills cast), 0 solo plans, no dead skill: every skill is in 8
  winning assignments.
- Every losing pair has a named reason: two island skills (nobody reaches the closet), two closet
  skills (nobody crosses), or a hard-control skill against the boss sentry.

## Examples

### Example 1: Pounce over, blind the sentry

**Given:** the player knows `pounce`, the mage knows `flashbang`.

**When:** `win`

**Then:** the player pounces from the rim onto the outcrop and walks onto the island plate; the mage
flashbangs the sentry and walks into the closet; the vault door opens.

### Example 2: Hook over, the sentry holds the door

**Given:** the player knows `magnetize`, the mage knows `gust`.

**When:** `win`

**Then:** the player hooks the pillar and is dragged over the rift; the mage gusts the sentry off its
post onto the closet plate, and walks into the vault.

### Example 3: Swap over, sneak in

**Given:** the player knows `vanish`, the mage knows `translocate`.

**When:** `win`

**Then:** the mage swaps places with the barrel and walks onto the island plate; the player vanishes
and walks into the closet under the sentry's nose.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Sixteen pairs win | Exactly the 16 island-by-closet pairs have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | Hard control does not blind the boss | `charge` + `translocate` has no plan. |
| P5 | The door needs both plates | One plate alone leaves the vault shut. |
