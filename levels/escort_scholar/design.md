# The Scholar

## Purpose

An escort level with two roads and a blow aimed at the escort. A **scholar** who cannot fight must
get from the library to the exit. The short way runs through the hall, where a clockwork **brute**
(a heavy machine) stands in the doorway: nobody walks past it. The long way is round by the balcony
and across the flooded **cistern**, but the scholar cannot swim, and the brute's searchlight eye
sweeps the cistern: no companion wades in under it. Two companions, the player and the mage, pick
one skill each from a pool of seven:

| Way | Answers |
|-----|---------|
| **Drop it** (the hall) | `turnToMist` (for a moment it is not heavy), then knock it down the shaft (`fireball`, `shieldBash`, `vortex` on the shaft), or hook it out of the doorway into the library (`hook`) |
| **Ice the way** (the cistern) | put the eye out - `shieldBash` (stunned: blind) or `lightningFlash` (a dry machine is stunned by a jolt; the flash lands its caster in the hall) - then wade the cistern to the exit and `blizzard` it from there: the scholar crosses on the ice |

**The heavy blow.** Set alight, the brute lashes out at the library doorway:
`behavior(brute, burning, groundSlam, there(library))`, a telegraphed physical slam on the library,
where the scholar waits. A fireball that drops the misted brute sets it alight first: the slam
winds up, and in that one cast the fireballer throws a second fireball that knocks it down the
shaft (a fallen brute's blow misses). The slam cannot be interrupted, and `mustSurvive(scholar)`
forbids letting it land.

Why no single skill works:
- A mover cannot shift the heavy brute; mist alone moves nothing.
- The blizzard needs a caster at the far side of the cistern, and no companion walks in under the
  eye; the eye-stunners do nothing to the water.

The traps:
- A stunned brute still fills the doorway: only the ice route gets past it.
- A hook on the heavy brute drags the caster into the hall; mist lasts one cast, so the knock must
  be the very next one.
- Only the exit (and the cistern itself) sees the water: the blizzard cannot be cast from the
  balcony.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
library (scholar, player, mage) --- hall (brute, shaft) --- exit
   |                                                        |
balcony ------------------ cistern (deep water) -------------+
```

- **Areas (5):** library, hall, exit, balcony, cistern.
- **Links:** walkable library-hall, hall-exit, library-balcony, balcony-cistern, cistern-exit.
- **Terrain:** the cistern is `deepWater` (a zone): the scholar (`weakness(scholar, deepWater,
  none, fell)`) and the heavy sink in it; companions wade and get wet. Iced, it is a floor.
- **Features:** `shaft` (chasm) in the hall.
- **Line of sight:** library-hall, hall-exit, library-balcony, exit-cistern (both ways).
- **Brute:** machine, heavy, `blocker`, `watches(brute, cistern)`, the burning slam above.
- **Scholar:** living, `mustSurvive`; walks.
- **Mana:** four each.
- **Goal:** `win` = `dropBrute(brute)` (`intoThePit`: mist, then a knock; or mist, then `bringTo`
  the library) then the scholar walks out; or `iceOver(cistern, brute)` (`lookAway`: blinded or
  electrocuted, confirmed by the watch being forbidden; then a blizzard on the cistern) then the
  scholar walks out, whole.

## Hypothesis

Measured with `htn_components combos escort_scholar`:

- No single skill wins, even when both companions hold it: 0 of 7.
- 12 of 49 assignments win (6 pairs, either way round), by 6 methods:
  `turnToMist` + `fireball` / `shieldBash` / `vortex` / `hook`;
  `blizzard` + `shieldBash` / `lightningFlash`.
- No solo plan; no dead skill. `shieldBash` plays two roles (the knock on the misted brute, the
  stun on its eye); `fireball` is both the trigger of the slam and its answer.
- The whole matrix replans in under three seconds.

## Examples

### Example 1: Mist, and fireball twice

**Given:** the player knows `turnToMist`, the mage knows `fireball`.

**When:** `win`

**Then:** the player turns the brute to mist; the mage's fireball sets it alight, and its slam
winds up on the library. In the window the mage throws a second fireball: the brute is knocked
down the shaft, and the slam misses. The scholar walks through the hall.

### Example 2: Mist and hook

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the misted brute is hooked out of the doorway into the library; the scholar walks through
the empty hall.

### Example 3: Jolt the eye, ice the cistern

**Given:** the player knows `lightningFlash`, the mage knows `blizzard`.

**When:** `win`

**Then:** the player's flash stuns the dry brute and lands the player in the hall. The mage wades
the cistern to the exit and ices it from there; the scholar walks round by the balcony and over the
ice.

### Example 4: Mist and vortex

**Given:** the player knows `turnToMist`, the mage knows `vortex`.

**When:** `win`

**Then:** a vortex on the shaft takes the misted brute.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 6 measured pairs have a plan, whichever companion holds which half. |
| P3 | The slam never lands | No winning plan has a blow. |
| P4 | The scholar walks on ice | It is never moved by force, and steps into the cistern only after the blizzard. |
| P5 | Two companions cast | Both cast in every winning plan. |
