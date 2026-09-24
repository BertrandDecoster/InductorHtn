# Into The Pit

## Purpose

A recipe: push it where it can't come back from. It needs a region whose arrival stops the enemy (a
pit whose `onEnter` grants `fell`) and a push line that lands the enemy there. Something immune to
forced movement ("heavy") has to lose its footing first: either a tag that suspends the immunity,
put on directly (a quake), or the frozen composite that bundles it (soak, then chill). The recipe
carries the details that a reaction table cannot express: who unbalances, who pushes, and from
which side.

## Layer

strategy

## Dependencies

- `abilities/primitives/ab_acts`

## Operators

None.

## Methods

| Method | Description |
|--------|-------------|
| `intoThePit(?e)` | It can be moved: anyone pushes it in. |
| `intoThePit(?e)` | Someone who pulls stands so the pit lies between: it falls in on the way. |
| `intoThePit(?e)` | It can't: someone puts a suspending tag on it, someone else pushes. |
| `intoThePit(?e)` | It can't, and frozen bundles the suspending tag: supply wet, chill, push (neither by the primer). |
| `intoThePit(?e)` | It flies: someone brings it down (strip or pop `flying`), someone else pushes. |
| `intoThePit(?e)` | A tag it wears wards forced movement (armour): someone takes it off, someone else pushes. |

The stopping region is found by `dropFor/2`: a zone that grants a stopping tag, or one whose `hazard(H)` the target is weak to.

## Rules

None.

## Required Facts

The ability layer's facts; `onEnter(?r, ...)` granting a tag that stops; `beyond/3` lines into it;
`suspends(?t, forcedMove)` for heavy enemies.

## Examples

### Example 1: Push it in

**Given:** gob at `rim`, `beyond(ledge, rim, pit)`, the player knows `gust`.

**When:** `intoThePit(gob)`

**Then:** plan contains `opForcedMove(player, gob, rim, pit)` and `opGrant(player, gob, fell)`.

### Example 2: Unbalance, then push

**Given:** `immune(golem, forcedMove)`, `suspends(offBalance, forcedMove)`, the player knows `quake`, the mage `gust`.

**When:** `intoThePit(golem)`

**Then:** plan contains `opCast(player, quake, golem)` then `opForcedMove(mage, golem, rim, pit)`.

### Example 3: Freeze, then push

**Given:** frozen bundles `offBalance`; the mage knows `douse`, the player `chill` and `gust`.

**When:** `intoThePit(golem)`

**Then:** plan contains the mage's douse, the player's chill, and `opForcedMove(player, golem, rim, pit)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | The golem does not move on its own | Heavy and nothing to unbalance it: no plan. |
| P2 | The unbalancer does not push | One companion knowing quake and gust: no plan. |
| P3 | No pit, no recipe | No push line lands the target in a stopping region: no plan. |
| P4 | A flyer is brought down first | `wards(flying, fell)`: someone nets it, someone else pushes it in. |
| P5 | Armour comes off first | `wards(armored, forcedMove)`: someone sunders it, someone else pushes it in. |
| P6 | Dragged across the pit | A hook on something beyond the pit, from the near side, drags it in. |
