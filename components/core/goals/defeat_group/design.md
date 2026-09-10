# Defeat Group

## Purpose

The goal a level composes: beat an enemy group, by the burn or by the
slipstream. Both alternatives are kept enumerable so the plan space shows
both ideas; the choice between them is the player's.

## Layer

goal

## Dependencies

- `core/strategies/the_burn`
- `core/strategies/the_slipstream`

## Methods

| Method | Description |
|--------|-------------|
| `defeatGroup(?e)` | `theBurn(?e)`, or `theSlipstream(?e)`, or nothing if `?e` is already dead. |

## Examples

### Example 1: Two ways

**Given:** the Grease Trap corridor with oil, a swarm that can be lured, the player holding `ignite` (one charge), `gust` and `lightning`.

**When:** `defeatGroup(swarm)`

**Then:** at least two plans; one contains `opCastRegion(player, ignite, corridor, oil, scorched)` and one contains a direct strike `opCastEntity(player, ...)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Dead enemies need nothing | `defeatGroup` on a dead enemy yields a plan with no operators. |
