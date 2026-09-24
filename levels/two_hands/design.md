# Two Hands

## Purpose

The reference example of a level where **no single skill can win, and many combinations can**. A
heavy sentinel machine stands on a bridge over an abyss. Two companions, the player and the mage,
pick one skill each from a pool of eight catalogue skills. Nothing grants the sentinel an outcome;
the catalogue gives it two ways out, and each takes two different kinds of step:

| Method | First | Then |
|--------|-------|------|
| **Drop it** (the abyss takes anything that walks) | take its weight away for a moment: `turnToMist` | while the moment lasts, knock it into the abyss - `fireball` or `shieldBash` from the ledge, `tidalWave` on the bridge itself, `vortex` on the abyss - or `hook` it across the gap from the overlook, and it falls in |
| **Short it** (a machine soaked, then jolted, is dead) | soak it: a `tidalWave` where it stands, or a `taunt` from the flooded ford - it walks after the taunter and arrives soaked | jolt it: `lightningFlash`, from next door |

Why no single skill works:
- Heavy wards forced movement, so a knock, a hook or a vortex alone does nothing. A hook on the heavy
  sentinel drags the caster onto the bridge instead.
- Turn to Mist alone leaves it standing, and the mist lasts only through the next cast: whoever
  mists it cannot also knock it.
- A jolt on a dry machine only stuns it, and a stun is not out.
- The primer may never pay off, so one companion can't do both halves even with both skills.

One skill serves two roles: `tidalWave` is a knockback in the first method and a soak in the
second. The map shows the two kinds of movement: every knock stays on the bridge (into the abyss);
only the hook (across the gap) and the taunt (a walk to the ford) change the sentinel's area.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
overlook ~~gap~~ bridge (sentinel; the abyss below it)
   |               |
   +---- ledge ----+          (the player, the mage)
           |
         ford (flooded)
```

- **Areas and links:** four areas. The ledge is walkable to the bridge, the overlook and the ford;
  the overlook faces the bridge across a gap (the chokepoint: a hook from there drags across it).
- **Features:** the abyss (`chasm`) inside the bridge area. The ford is a `puddle` zone.
- **Line of sight:** the ledge sees the bridge and the ford; the overlook and the ford see the bridge.
- **Sentinel:** `machine`, `heavy`. Both companions have 4 mana.

## Hypothesis

Measured by `htn_components combos two_hands` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 14 of the 64 assignments win (7 pairs, whichever companion holds which half), by 7 methods;
  no solo plans; no dead skills:
  - turnToMist, plus fireball, tidalWave, shieldBash, vortex or hook: 5 pairs;
  - lightningFlash, plus tidalWave or taunt: 2 pairs.
- The other pairs lose, and each for a reason you can name: two movers (it stays heavy), mist and
  lightningFlash or taunt (nothing moves it, it stays dry), a mover and lightningFlash (the knock is
  warded, and a dry jolt only stuns), taunt and a knocker (it comes to the ford, but nothing jolts
  it).
- A taunt from the overlook breaks at once: the sentinel cannot walk the gap.

## Examples

### Example 1: Mist, then knock

**Given:** the player knows `turnToMist`, the mage knows `fireball`.

**When:** `win`

**Then:** the player turns the sentinel to mist; while it lasts, the mage's fireball knocks it into
the abyss (`opKnock(mage, sentinel, abyss)`, `fell`).

### Example 2: Mist, then hook across the gap

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the player mists the sentinel; the mage walks to the overlook and hooks it across the
gap, and it falls in (`opFall(mage, sentinel, bridge, overlook)`).

### Example 3: Soak, then jolt

**Given:** the player knows `tidalWave`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player walks onto the bridge and the wave soaks the sentinel; the mage's flash from
the ledge short-circuits it (`dead`).

### Example 4: Lure it into the ford

**Given:** the player knows `taunt`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player wades into the ford and taunts the sentinel; it walks after the player through
the ledge into the ford, soaked; the mage's flash on the ford kills it.

### Example 5: Mist, then vortex

**Given:** the player knows `turnToMist`, the mage knows `vortex`.

**When:** `win`

**Then:** the player mists the sentinel; the mage's vortex on the abyss knocks it in.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Seven pairs win | Exactly the seven measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | The mist is a moment | Mist alone, or a knock alone, leaves the sentinel standing. |
| P5 | Heavy and dry | A hook and a flash leave it standing; a knock before the mist does nothing. |
