# Two Hands

## Purpose

The reference example of a level where **no single skill can win, and many combinations can**. An
armoured sentinel machine stands on a bridge over a pit. Two companions, the player and the mage, pick one skill
each from a pool of eight catalogue skills. Nothing grants the sentinel an outcome; it has two
weaknesses, and each takes two different kinds of step:

| Method | First | Then |
|--------|-------|------|
| **Drop it** (the chasm takes anything that walks) | take the armour off: `sunder`, `dispel` | move it into the pit: `gust`, `tidalWave` (push from the ledge), `magnetize`, `taunt` (pull from the overlook, across the pit) |
| **Short it** (a machine soaked, then jolted, is dead) | soak it: `tidalWave`, `rainCall` | jolt it: `zap` |

Why no single skill works:
- The armour wards off forced movement, so a push or pull alone does nothing. A hook on the armoured
  sentinel drags the caster to it instead.
- An armour-breaker alone leaves it standing.
- A jolt on a dry machine only stuns it, and a stun is not out.
- The primer may never pay off, so one companion can't do both halves even with both skills.

Several skills serve more than one role. tidalWave is a push in the first method and a soak in the
second.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
ledge (the player, the mage) --- bridge (sentinel) --- far
                        |
                       pit (chasm)
ledge --- path --- overlook   (facing the bridge across the pit)
```

- **Lines:** a push from the ledge on the bridge lands in the pit; from the overlook, the pit lies
  between it and the bridge, so a pull from there drops the sentinel in.
- **Line of sight:** the ledge sees the bridge, and so does the overlook.
- **Sentinel:** machine, armored. Both companions have 4 mana.

## Hypothesis

Measured by replanning every assignment (this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 10 of the 28 pairs win, whichever companion holds which half:
  - sunder or dispel, plus gust, tidalWave, magnetize or taunt: 8 pairs;
  - tidalWave or rainCall, plus zap: 2 pairs.
- The other 18 pairs lose, and each for a reason you can name: two movers (the armour stays), two
  armour-breakers (nothing moves it), a breaker and zap (nothing wet), a mover and zap (the push is
  warded, and a dry jolt only stuns).

## Examples

### Example 1: Strip, then push

**Given:** the player knows `sunder`, the mage knows `gust`.

**When:** `win`

**Then:** the player sunders the armour; the mage's gust throws the sentinel off the bridge into the pit.

### Example 2: Strip, then pull across

**Given:** the player knows `dispel`, the mage knows `magnetize`.

**When:** `win`

**Then:** the player dispels the armour; the mage walks round to the overlook and hooks the sentinel across the pit, and it falls in.

### Example 3: Soak, then jolt

**Given:** the player knows `rainCall`, the mage knows `zap`.

**When:** `win`

**Then:** the rain soaks it; the jolt short-circuits it (`dead`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Ten pairs win | Exactly the ten measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
