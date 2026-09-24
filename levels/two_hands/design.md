# Two Hands

## Purpose

The reference example of a level where **no single skill can win, and many combinations can**. A
heavy sentinel machine stands on a bridge over a pit. Two companions, the player and the mage, pick
one skill each from a pool of seven catalogue skills. Nothing grants the sentinel an outcome; the
catalogue gives it two ways out, and each takes two different kinds of step:

| Method | First | Then |
|--------|-------|------|
| **Drop it** (the chasm takes anything that walks) | take its weight away for a moment: `turnToMist` | move it into the pit while the moment lasts: `fireball`, `tidalWave` (push from the ledge), `hook`, `taunt` (pull from the overlook, across the pit), `vortex` (draw it down into the pit) |
| **Short it** (a machine soaked, then jolted, is dead) | soak it: `tidalWave` | jolt it: `lightningFlash` |

Why no single skill works:
- Heavy wards forced movement, so a push, a pull or a vortex alone does nothing. A hook on the heavy
  sentinel drags the caster to it instead.
- Turn to Mist alone leaves it standing, and the mist lasts only through the next cast: whoever
  mists it cannot also push it.
- A jolt on a dry machine only stuns it, and a stun is not out.
- The primer may never pay off, so one companion can't do both halves even with both skills.

One skill serves two roles: `tidalWave` is a push in the first method and a soak in the second.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
ledge (the player, the mage) --- bridge (sentinel) --- far
  |                                 |
  |                                pit (chasm)
path --- overlook   (facing the bridge across the pit)
```

- **Lines:** a push from the ledge on the bridge lands in the pit; from the overlook, the pit lies
  between it and the bridge, so a pull from there drops the sentinel in. The pit is next to the
  bridge, so a vortex on the pit draws the sentinel down.
- **Line of sight:** the ledge sees the bridge and the pit, and so does the overlook.
- **Sentinel:** `machine`, `heavy`. Both companions have 4 mana.

## Hypothesis

Measured by `htn_components combos two_hands` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 12 of the 49 assignments win (6 pairs, whichever companion holds which half), by 6 methods;
  no solo plans; no dead skills:
  - turnToMist, plus fireball, tidalWave, hook, taunt or vortex: 5 pairs;
  - tidalWave plus lightningFlash: 1 pair.
- The other pairs lose, and each for a reason you can name: two movers (it stays heavy), mist and
  lightningFlash (nothing moves it, it stays dry), a mover and lightningFlash (the push is warded, and
  a dry jolt only stuns).

## Examples

### Example 1: Mist, then push

**Given:** the player knows `turnToMist`, the mage knows `fireball`.

**When:** `win`

**Then:** the player turns the sentinel to mist; while it lasts, the mage's fireball throws it off the
bridge into the pit.

### Example 2: Mist, then pull across

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the player mists the sentinel; the mage walks round to the overlook and hooks it across the
pit, and it falls in.

### Example 3: Soak, then jolt

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the wave soaks it; the flash short-circuits it (`dead`).

### Example 4: Mist, then draw it down

**Given:** the player knows `turnToMist`, the mage knows `vortex`.

**When:** `win`

**Then:** the player mists the sentinel; the mage's vortex on the pit draws it down.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Six pairs win | Exactly the six measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | The mist is a moment | Mist alone, or a push alone, leaves the sentinel standing. |
