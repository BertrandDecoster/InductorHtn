# Powder Keg

## Purpose

A crowd-control level (category 8): **gather the group, then one reaction spreads through it.**
Three treants shamble in a rain-soaked grove. Wood burns (the catalogue's `wooden` weakness), but
they are drenched: fire cast on one only steams it dry (`steam`), and a room that has caught fire
does not catch again. Up the ramp sits a keg of lamp oil. Oil that catches fire blazes (`blaze`), and
a blaze sets everyone else in the room alight at once, raw: hot enough to burn wood straight through
the wet. So the keg and the crowd have to share a room before anyone strikes a light. The player and
the mage pick one skill each from a pool of seven. Nothing grants an outcome: `dead` is the
treants' catalogue weakness to burning.

The level's goal is a crowd recipe, spelled out top-down from the need. Fire on the treants only
steams them, so the burning must come from a **fuse**: anything a flame would set blazing over
its room (read from `reactionFor/4` and the reaction's area effect, not from the keg's name). Then:
`gather` (the fuse to the crowd, or the crowd to the fuse, one straggler at a time), `light` (a fire
on the fuse's room), and confirm that nobody is standing.

| Method | Gather | Then light it |
|--------|--------|---------------|
| **Roll the keg down** | `gust`, `tidalWave` from the camp: the ramp runs into the grove | `flameWall`, `fireball` on the grove |
| **Drag the keg in** | `magnetize`, `taunt`, `provoke` from the grove: the keg comes to the caster | the same |
| **Drag the crowd up** | `provoke` from the ramp (the whole grove at once), `taunt` or `magnetize` (one at a time) | the same, on the ramp |

Why no single skill works: a mover lights nothing, and a fire lights the crowd or the keg where they
stand, never both. Two fires don't help either: the first spends the room, and `fireball`'s own
flames light the keg on the ramp *before* its push rolls it down. The ignition order inside one
skill is part of the puzzle.

The traps: burning the grove first (the treants steam, and the grove's fire is spent); fireball on
the keg from the camp (it blazes alone on the ramp, then rolls down already spent); oiling the crowd
would not help either, since a wet treant steams before its oil can blaze.

Skills serving two roles: `taunt`, `magnetize` and `provoke` each gather in both directions, pulling
the keg in or pulling the crowd up. `tidalWave` soaks the keg and rolls it, and the oil still
blazes (it was there first).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp (player, mage) --- ramp (keg, oiled) --- grove (t1, t2, t3; wooden, wet)
```

- **Line of sight:** the camp sees the ramp and the grove; the ramp and the grove see each other.
- **Lines:** a push from the camp on the ramp lands in the grove (the keg rolls down).
- **Keg:** an object, oiled. **Treants:** wooden, wet. Both companions have 2 mana.

## Hypothesis

Measured with `htn_components combos crowd_powder_keg` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 20 of 49 assignments win (10 unordered pairs, whichever companion holds which half): one of five
  movers (`gust`, `tidalWave`, `magnetize`, `taunt`, `provoke`) with one of two fires
  (`flameWall`, `fireball`).
- 10 methods, in two kinds: bring the keg to the crowd (roll it or drag it), or bring the crowd to
  the keg. `taunt`, `magnetize` and `provoke` each find both kinds (2 plans each). No dead skill.
- The losing pairs: two movers (nothing lit), two fires (nothing gathered).
- One replan takes about 0.5 s; the whole matrix under 5 s.

## Examples

### Example 1: Roll the keg down, then light it

**Given:** the player knows `gust`, the mage knows `flameWall`.

**When:** `win`

**Then:** the gust rolls the keg down the ramp into the grove. The flame wall steams the treants, then
reaches the keg: it blazes, and all three treants burn.

### Example 2: Drag the crowd up the ramp

**Given:** the player knows `provoke`, the mage knows `fireball`.

**When:** `win`

**Then:** the player walks onto the ramp and provokes the grove; the treants are dragged up round the
keg. The mage fireballs the ramp: the keg blazes and the crowd burns. The provoker catches fire too,
and lives.

### Example 3: Drag the keg in

**Given:** the player knows `magnetize`, the mage knows `flameWall`.

**When:** `win`

**Then:** the player walks into the grove and hooks the keg down to them; the flame wall on the grove
does the rest.

### Example 4: Trap - two fires, or two movers

**Given:** `flameWall` and `fireball`; or `gust` and `provoke`.

**When:** `win`

**Then:** no plan. The fires steam the crowd or light the keg alone; the movers gather everything and
nothing lights it.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Ten pairs win | Exactly the ten measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | One blaze takes the crowd | Every winning plan has one blaze, and all three treants die of it. |
