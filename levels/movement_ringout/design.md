# Ring-Out

## Purpose

A pure-movement ring-out, after Into the Breach. An ogre stands on a plinth at the edge of the
void, and the only victory is getting it into the void; nothing hurts it. The ogre never starts on
a line into the void (a push from the yard only shoves it back onto the ledge), so one companion
has to move something first and the other finishes. The player and the mage pick **one skill each**
from seven catalogue skills.

The ogre answers a taunt: dragged to the taunter, it slams the ground where it lands. That is a
heavy `groundSlam` on its own region: everyone else there is stunned and thrown away from it, and
off the brink that means into the void.

| Method | First | Then |
|--------|-------|------|
| **Onto the brink** | Draw it onto the brink: `hook` it to your feet there, or a `vortex` on the brink sucks it in (and roots it). Whoever stands on the brink steps off. | Push it over: `fireball` from the gate or the yard, `tidalWave` from the yard. |
| **Taunt it onto the brink** | `taunt` from the brink: it is dragged there and winds up its slam on the brink, taunter included. | In the one-cast window, a friend's `fireball` knocks it over; it is gone before the blow lands. |
| **From behind** | Land on the perch, which opens the grate: `blink` or `lightningFlash` up there. | Walk round through the grate to the ledge and push it off the plinth (`fireball`, `tidalWave`). |
| **Across** | A friend's `vortex` on the perch sucks the puller up from the yard. | From the perch, pull it across the void (`hook`, `taunt`): it falls on the way, before it can slam. |

Why no single skill wins, even held by both seats:
- a pusher alone never finds a line into the void: the yard push lands on the ledge, and the ledge
  is behind the grate;
- a puller alone drags it onto the brink, and nobody pushes; nobody who pulls can get onto the
  perch alone;
- a leaper on the perch has nothing to push or pull with;
- a vortex alone sucks it onto the brink and roots it there.

Traps:
- Two pushers only shove it about.
- A tidal wave from the yard throws whoever still stands on the brink into the void with the ogre.
- A vortex on the brink sucks in friends standing in the yard.
- Taunt it onto the brink with no fireball ready, and it slams the taunter into the void. A tidal
  wave in the window would wash the taunter off too, so it does not count.

Skills serving two roles:
- `vortex`: lure onto the brink, lift a friend onto the perch.
- `hook`: lure onto the brink, drag across the void.
- `taunt`: lure (at the price of the slam), drag across.
- `fireball`: push off the brink, push from behind, beat the slam in its window.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
              perch (barred; plate: opens the grate)
                :
gate --- yard ------------ grate (door) --- ledge
           |   \                              |
         brink - plinth (ogre) ---------------+
           |        \
          void       void (between the perch and the plinth)
```

- **Walking:**
  - gate–yard; yard–brink, yard–plinth, yard–grate, yard–perch;
  - brink–plinth, grate–ledge, ledge–plinth.
  - The perch is a door that never opens: nobody walks up, but a blink, a flash or a vortex puts
    you there.
- **Lines:**
  - From the yard, the gate or the brink itself, a push on the brink lands in the void.
  - From the ledge, a push on the plinth lands in the void; from the yard or the brink, on the
    ledge.
  - The void lies between the perch and the plinth.
- **Line of sight:**
  - gate→yard, gate→brink, gate→perch;
  - yard→brink, yard→plinth, yard→perch;
  - brink→plinth, ledge→plinth;
  - perch→yard, perch→gate, perch→plinth.
- **Ogre:** living, a blocker; `behavior(ogre, taunted, groundSlam, here)`.
- **Mana:** 4 each. **Default kit:** player `fireball`, mage `hook`.

## Hypothesis

Measured by `htn_components combos movement_ringout` (49 replans in about 6 s; each plan is under
2 s):

- No single skill wins, even when both seats hold it: 0 of 7.
- 22 of 49 assignments win, 11 pairs each way round:
  - onto the brink: `fireball` + {`hook`, `vortex`, `taunt`}, `tidalWave` + {`hook`, `vortex`};
  - from behind: {`fireball`, `tidalWave`} + {`blink`, `lightningFlash`};
  - across: `vortex` + {`hook`, `taunt`}.
- 11 methods (sets of skills cast), of four kinds (the table above).
- Skill usage: fireball 10, tidalWave 8, vortex 8, hook 6, taunt 4, blink 4, lightningFlash 4. No
  dead skill; no plan carried by one companion.

## Examples

### Example 1: Hook it onto the brink, then push

**Given:** the default kit (player `fireball`, mage `hook`).

**When:** `win`

**Then:** the mage hooks the ogre onto the brink and steps back; the player's fireball knocks it
into the void.

### Example 2: Land on the perch, push from behind

**Given:** player `tidalWave`, mage `blink`.

**When:** `win`

**Then:** the mage blinks onto the perch and the grate opens. The player walks round to the ledge,
and her wave throws the ogre off the plinth.

### Example 3: Taunt it, and knock it over before the slam

**Given:** player `fireball`, mage `taunt`.

**When:** `win`

**Then:** the mage taunts the ogre from the brink. It is dragged there and winds up a ground slam on
the brink. In the window, the player's fireball throws it into the void, and the slam misses.

### Example 4: A vortex lifts the puller

**Given:** player `vortex`, mage `hook`.

**When:** `win`

**Then:** the player's vortex on the perch sucks the mage up from the yard, which opens the grate.
From the perch, her hook drags the ogre across the void.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions acting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured assignments win | Exactly the 11 measured pairs win, both ways round; `combos` passes; no dead skill. |
| P4 | Two pushers only shove it about | `fireball` + `tidalWave` loses. |
| P5 | The slam must be answered | A taunt lure works with a fireball ready; with a blinker, the taunter is slammed into the void. |
