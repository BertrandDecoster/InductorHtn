# Conduct

## Purpose

A recipe: soak it, then shock it. The enemy carries `wet` because it stands in water, is doused, or is
pushed into a pool. Then a *different* companion lands `shocked` on it. The recipe doesn't say what
wet + shocked does; that is the level's physics (a `reaction/3`). It states the steps and the roles,
and ends by confirming the simulated world, so a level where the combo does not kill simply has no
`conduct` plan.

## Layer

strategy

## Dependencies

- `abilities/primitives/ab_acts`

## Operators

None.

## Methods

| Method | Description |
|--------|-------------|
| `conduct(?e)` | A supplier of wet (nobody if it is already wet), a shock from anyone else, then confirm. |

## Rules

None.

## Required Facts

The ability layer's facts, plus a `reaction(wet, shocked, ...)` that stops the target.

## Examples

### Example 1: Already wet takes one shock

**Given:** `tag(wader, wet)`, the player knows `shock`.

**When:** `conduct(wader)`

**Then:** plan contains `opCast(player, shock, wader)` and the electrocution reaction; nobody douses.

### Example 2: One soaks, another shocks

**Given:** the mage knows `douse`, the player knows `shock`, gob is dry.

**When:** `conduct(gob)`

**Then:** plan contains `opCast(mage, douse, gob)`, `opCast(player, shock, gob)`, `opGrant(player, gob, dead)`.

### Example 3: A push into the pool soaks

**Given:** tender at `slick`, `beyond(ledge, slick, pool)`, the mage knows `gust`.

**When:** `conduct(tender)`

**Then:** plan contains `opForcedMove(mage, tender, slick, pool)` and `opCast(player, shock, tender)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | The primer never pays off | One companion knowing both douse and shock: no plan. |
| P2 | Immune to shock, no conduct | `immune(gob, shocked)`: no plan. |
| P3 | The world confirms the recipe | Electrocution fires but `immune(gob, dead)`: no plan. |
