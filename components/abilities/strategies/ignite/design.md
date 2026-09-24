# Ignite

## Purpose

A recipe: oil it, then set it alight. The enemy carries `oiled` because it stands in a slick or is
pushed into one. Then a different companion lands `burning` on it. The physics sets a trap: if the
enemy is also wet, and wet was stored first, burning makes steam instead of a blaze, and the recipe
has no plan.

## Layer

strategy

## Dependencies

- `abilities/primitives/ab_acts`

## Operators

None.

## Methods

| Method | Description |
|--------|-------------|
| `ignite(?e)` | A supplier of oiled (nobody if already oiled), burning from anyone else, then confirm. |

## Rules

None.

## Required Facts

The ability layer's facts, plus a `reaction(oiled, burning, ...)` that stops the target.

## Examples

### Example 1: Already oiled takes one spark

**Given:** `tag(tender, oiled)`, the player knows `ignite`.

**When:** `ignite(tender)`

**Then:** plan contains `opCast(player, ignite, tender)` and `opReact(player, tender, oiled, burning, blaze)`.

### Example 2: Walked into the slick

**Given:** imp at `pool`, `beyond(ledge, pool, slick)`, the mage knows `gust`, the player `ignite`.

**When:** `ignite(imp)`

**Then:** plan contains `opForcedMove(mage, imp, pool, slick)`, `opCast(player, ignite, imp)`, `opGrant(player, imp, dead)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Steam spoils the blaze | Wet stored before oiled: burning makes steam, no plan. |
| P2 | The primer never pays off | One companion knowing both gust and ignite: no plan. |
