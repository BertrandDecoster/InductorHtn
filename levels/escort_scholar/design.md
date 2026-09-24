# The Scholar

## Purpose

An escort level with an enemy behaviour to survive. A **scholar** who cannot act must get from the
library to the exit. It is not a companion: it never casts, and it walks on its own when the way is
clear. The only door runs through the hall, where a clockwork **brute** (a heavy machine) stands as
a blocker. The other way is round by the balcony and across a flooded **cistern**, but the scholar
cannot swim, and the brute's searchlight eye sweeps the cistern (nobody wades in under it). Two
companions, the player and the mage, pick one skill each from a pool of eight catalogue skills.

Three families of method, each needing both companions:

| Method | First | Then |
|--------|-------|------|
| **Short it** (the scholar walks through the hall) | soak it: `tidalWave` from the library. Soaked, the brute sparks and winds up a `groundSlam` on the soaker - and on the scholar standing beside it | jolt it in that window: `lightningFlash` (a wet machine electrocuted is dead, and a dead brute's blow misses) |
| **Drop it** (the scholar walks through the hall) | turn it to mist: `turnToMist` (for a moment it is not heavy) | move it out of the doorway on the very next cast: suck it into the pit (`vortex` on the pit), or hook it into the library or onto the balcony (`hook`) |
| **Ice the way** (the scholar never passes the brute) | switch the eye off: `shieldBash` (stunned), `blindingFlash` (blinded), or a dry `lightningFlash` (a machine jolted is stunned) | `blizzard` on the cistern: ice over deep water is a floor, and the scholar walks across |

`lightningFlash` plays two roles: on a wet brute it kills, on a dry one it stuns. `blizzard` is the
bridge, never a weapon here.

Why no single skill works:
- `tidalWave` alone soaks the brute and brings the slam down on the library: nobody can stop a
  physical blow, so there is no plan.
- A dry `lightningFlash`, `shieldBash` or `blindingFlash` only switches the eye off: the hall is
  still blocked, and the cistern is still deep water.
- `turnToMist` alone moves nothing; `hook` or `vortex` alone meets the heavy brute (a hook drags the
  caster in instead; a vortex draws nothing that is anchored).
- `blizzard` alone ices the cistern under the brute's eye.

The protect traps:
- The heavy attack: `behavior(brute, wet, groundSlam, source)`. The slam follows the soaker, and
  the wave was cast from the library, where the scholar stands (`mustSurvive(scholar)`). A
  physical blow cannot be interrupted (`shieldBash` does not help), mist does not move it, and a
  flash disjoints only its caster: only killing the brute in the window saves the scholar.
- A wave from the library soaks the scholar too: walking onto the ice it freezes (wet + chilled:
  stunned) and cannot go on. So `tidalWave` + `blizzard` has no plan.
- Hooking the scholar over the cistern, or a vortex on the cistern, drops it in the water.
- A frozen or stunned brute still fills the doorway.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
library (scholar, player, mage) --- hall (brute) --- exit (pillar)
   |                                  |                |
balcony ------------ cistern (deep water) -------------+
                                      pit (chasm, below the hall)
```

- **Walking:** library-hall-exit, library-balcony-cistern-exit, hall-pit. The hall is the brute's
  (a blocker); the pit is a chasm.
- **Lines:** the cistern lies between the balcony and the exit, both ways.
- **Line of sight:** library-hall, library-balcony, balcony-hall, balcony-cistern, balcony-exit,
  exit-hall (both ways); library to the pit, exit to the cistern.
- **Brute:** machine, heavy, blocker, `watches(brute, cistern)`, and its wet behaviour above.
  **Pillar:** heavy.
- **Scholar:** living, `mustSurvive`, `weakness(scholar, deepWater, none, fell)`.
- **Goal:** `win` = `clearWay(brute)` (neutralize it; soak it and let the window finish it; or
  mist it and shift it), then the scholar walks out; or `iceOver(cistern, brute)` (the eye off,
  then the blizzard), then the scholar walks out. Both end with `confirmSafe` (the scholar at the
  exit and whole, and no companion lost).

## Hypothesis

Measured with `htn_components combos escort_scholar`:

- No single skill wins, even when both companions hold it: 0 of 8.
- 12 of 64 assignments win (6 pairs, either way round), by 6 methods:
  `tidalWave` + `lightningFlash`; `turnToMist` + `hook` / `vortex`; `blizzard` + `shieldBash` /
  `blindingFlash` / `lightningFlash`.
- No solo plan; no dead skill. Every plan takes under a second.

## Examples

### Example 1: Soak, and jolt in the window

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player's wave soaks the brute (and the scholar). The brute winds up a ground slam on
the player's region. In that window the mage's lightning flash kills the wet machine (`dead`); the
slam misses. The scholar walks through the hall.

### Example 2: Mist and vortex

**Given:** the player knows `turnToMist`, the mage knows `vortex`.

**When:** `win`

**Then:** the brute turns to mist; the mage's vortex on the pit sucks it in (`fell`). The scholar
walks through the hall.

### Example 3: Ice the cistern

**Given:** the player knows `shieldBash`, the mage knows `blizzard`.

**When:** `win`

**Then:** the player bashes the brute (stunned: its eye is off); the mage steps onto the balcony
and ices the cistern. The scholar walks round and across the ice.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 6 measured pairs have a plan, whichever companion holds which half. |
| P3 | The traps have no plan | Wave + blizzard (the scholar freezes on the ice), wave + bash and wave + mist (the slam lands), a dry jolt alone. |
| P4 | The slam never lands | No winning plan has a blow; every wind-up ends with the brute dead and the blow missing. |
| P5 | Two companions cast | Both companions cast in every winning plan. |
