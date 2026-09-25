# Puzzle 1: The Grease Trap

## Overview

An introductory puzzle for oilAndBurn and wetAndFreeze. Two guards hold the generator room.
Each is out of the fight only through one location combo, and each combo needs two companions:
one lures the guard onto the right floor, the other uses the right skill on it there.

## Layout

```
    [storage]     [generator]
         \           /  |
          [main]        |
             |          |
        [corridor]------+
             |
          [exit]
```

The map is `linked` facts (both directions). Movement is one step: the engine pathfinds.

## Locations

| Location | Contents | Tag |
|----------|----------|-----|
| main | player, arcanist | - |
| storage | - | oil |
| generator | guard1 (oil + burning), guard2 (wet + chilled) | - |
| corridor | - | wet |
| exit | goal | - |

## Companions

| Companion | Skill | Tag |
|-----------|-------|-----|
| player | igniteSkill | burning |
| arcanist | frostSkill | chilled |

## Goal

`completePuzzle`: `clearLocation(generator)`, then both companions reach the exit.

## HTN Solution (the only plan)

1. The arcanist lures guard1 from the generator onto the storage's oil; the player walks there
   and ignites it. The oil becomes burning; the player, the arcanist and guard1 burn; guard1
   is dead.
2. The player lures guard2 from the generator into the wet corridor; the arcanist walks there
   and chills it. guard2 is stunned and dead.
3. Both walk to the exit. The dead guards stay where they fell.

## Examples

### Example 1: Puzzle can be completed
**When:** `completePuzzle` **Then:** exactly one plan (above)

### Example 2: guard1 is defeated by oilAndBurn
### Example 3: guard2 is defeated by wetAndFreeze

## Properties

### P1: All enemies dead after completion
### P2: Both companions at the exit; the dead guards stay behind
