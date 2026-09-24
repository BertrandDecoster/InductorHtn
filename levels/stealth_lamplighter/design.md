# The Lamplighter

## Purpose

A stealth level on the ability layer where **everyone has to get out, and there is one crate**.
The gate's lever lies in a windowless guardroom under a warden's eyes; the road runs down the
lamp-lit street and through a shuttered hall that the lamplighter watches from his post. Nobody sees
into the guardroom or the hall, so nobody blinks or dashes in. Two companions pick one skill each
from a pool of seven catalogue skills.

| Obstacle | Who has to solve it | Answers |
|----------|---------------------|---------|
| **The lever** (`onEnter(guardroom, lever)` opens the gate for good; `watches(warden, guardroom)`) | one companion, or the crate | blind the warden from the start (`blindingFlash`), stun him (`shieldBash`), or push the crate from the yard onto the lever (`fireball` from the start, or `tidalWave` washing it in) |
| **The hall** (`watches(lamplighter, hall)` while he is on his post and the crate is not in the hall) | everyone | drag him off his post (`taunt`, `hook`), draw him into the street (`vortex` on the lamps), or push the crate into the hall from the lamps (`fireball`, `tidalWave`) and walk behind it |

Why no single skill works:
- The lamplighter's lantern: `immune(lamplighter, blinded)`, so no flash and no stun (it bundles
  `blinded`) helps with him.
- Nobody sees into the guardroom: no lure, hook or vortex reaches the warden.
- **fireball and tidalWave have two roles, and there is one crate.** It weighs down the lever, or it
  is cover in the hall - not both. Two crate skills (or one twice) leave one obstacle.
- **The vortex trap.** A vortex on the lamps draws in everyone next to the street, companions
  included, and roots them for good. It works only when the other companion is on the lever, in the
  guardroom - which needs the warden blinded. With the crate on the lever, there is nowhere to stand
  clear.

Level-local pieces: the lever zone (`open(gate)`), the positional watch rule that reads the crate,
and the recipes `getTo/3` (walk; else stop a watcher watching, or put the crate in a watched region,
and try again), `unwatch/1`, `budge/1` and `openGate/0`.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
guardroom (warden; the lever)      yard (a crate)
     |                         ___/    \___
   start (player, mage) ------------ lamps ---- hall ---- gate (shut) ---- exit
                                       |
                                      post (lamplighter)
```

- **Lines of sight:** the start sees the yard and the lamps; the lamps see the yard, the post and the
  start. Nothing sees into the guardroom or the hall.
- **Push lines:** from the start, the crate in the yard goes into the guardroom (onto the lever);
  from under the lamps, into the hall (cover).
- **Warden:** living, watches the guardroom while he stands in it.
- **Lamplighter:** living, cannot be blinded, watches the hall from the post unless the crate is in it.
- **Mana:** 4 each (fireball and tidalWave cost 2).
- **Victory:** `escape` - the gate open, then both companions at the exit.

## Hypothesis

Measured by `htn_components combos stealth_lamplighter` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7 (fireball twice included: one crate).
- **28 of 49** assignments win, by **14** methods; no solo plans; no dead skill.
  - a warden answer (`blindingFlash`, `shieldBash`) and any hall answer (`taunt`, `hook`, `vortex`,
    `fireball`, `tidalWave`): 2 x 5 x 2 = 20;
  - a crate skill on the lever (`fireball`, `tidalWave`) and a lure (`taunt`, `hook`): 2 x 2 x 2 = 8.
- The 21 losing assignments fail for nameable reasons: two warden answers or two lures (one obstacle
  left), two crate skills (one crate), a crate skill with a vortex (nowhere to stand clear), one skill
  twice.
- Usage: blindingFlash, shieldBash 10; fireball, tidalWave, taunt, hook 8; vortex 4.
- One skill, two roles: `fireball` and `tidalWave` each push the crate onto the lever or into the hall.
- Every plan takes under 7 s.

## Examples

### Example 1: The crate on the lever, and a taunt

**Given:** the player knows `fireball`, the mage knows `taunt`.

**When:** `escape`

**Then:** the player's fireball blows the crate from the yard into the guardroom and the gate opens;
the mage taunts the lamplighter off his post into the street; both walk through the hall and out.

### Example 2: A flash, and cover

**Given:** the player knows `blindingFlash`, the mage knows `tidalWave`.

**When:** `escape`

**Then:** the player's flash blinds the warden and the player pulls the lever; the mage, under the
lamps, washes the crate into the hall, and both walk through behind it.

### Example 3: A bash, and a vortex

**Given:** the player knows `shieldBash`, the mage knows `vortex`.

**When:** `escape`

**Then:** the player stuns the warden and stands on the lever; the mage's vortex on the lamps draws
the lamplighter off his post (and the crate out of the yard) and roots them in the street.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan - fireball twice included. |
| P2 | The measured assignments win | Exactly the 28 measured assignments have a plan; none solo; no dead skill. |
| P3 | One crate | fireball + tidalWave has no plan. |
| P4 | The lantern and the blind room | blindingFlash + shieldBash and taunt + hook have no plan. |
| P5 | The vortex trap | fireball + vortex has no plan: the vortex would draw in and root a companion. |
| P6 | Two roles for the crate | With fireball + hook the crate goes on the lever; with shieldBash + fireball it is cover in the hall. |
