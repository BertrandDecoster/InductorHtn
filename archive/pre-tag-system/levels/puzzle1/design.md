# Puzzle 1: The Grease Trap

## Overview

An introductory puzzle for the two strategies of the old component tree: theBurn (ignite an
oily location under an enemy weak to burning) and theSlipstream (freeze the floor under an enemy
so it slides into a hazard it is weak to).

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

The map is `linked` facts (both directions), restored from the original `connected` facts.
Movement is one step (the engine pathfinds); the slide into the generator needs the
corridor-generator link.

## Locations

| Location | Contents | Tag |
|----------|----------|-----|
| main | player, warden, arcanist | - |
| storage | guard1 (weak to burning) | oily |
| generator | - | electrified |
| corridor | guard2 (weak to electrified) | wet |
| exit | goal | - |

## Companions

| Companion | Skill | Tag |
|-----------|-------|-----|
| player | igniteSkill | burning |
| arcanist | freezeSkill | frozen |
| warden | - | - |

## Goal

`completePuzzle`: `clearLocation(storage)`, `clearLocation(corridor)`, then every companion
reaches the exit (`reachExit`).

## HTN Solution (the only plan)

1. The player ignites the storage from the main room (the engine handles range): the oil
   burns, guard1 standing there burns and is dead.
2. The arcanist freezes the corridor from the main room: the wet floor freezes, guard2
   standing there is frozen, slides into the adjacent generator and is electrified; guard2 is dead.
3. The player, the warden and the arcanist walk to the exit.

## Examples

### Example 1: Puzzle can be completed

**When:** `completePuzzle` **Then:** exactly one plan (above)

### Example 2: guard1 is defeated by theBurn

**When:** `defeat(guard1)` **Then:** guard1 burning and dead; the storage burning

### Example 3: guard2 is defeated by theSlipstream

**When:** `defeat(guard2)` **Then:** guard2 electrified and dead, in the generator

## Properties

### P1: All enemies dead after completion

### P2: Every companion at the exit after completion
