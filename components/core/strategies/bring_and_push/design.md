# Bring and Push

## Purpose

Ring-out. The need is an enemy with a status that some ground does to whatever enters it (the
void: `fallen`). This way of meeting it: bring the enemy, on foot, to a region at the edge of
that ground, then force it in. Two steps, and each step's alternatives come from what the
companions hold, never from names: whoever holds a pull, a push or a dash can bring it
(`bringTo`); whoever holds a forced movement that moves it can force it in (`forceInto`: a push or a
pull, unless it is immune to that movement). A taunt is not a forced movement: the taunter goes along.

The drop is reached only by a one-way link from its edge (`connected(brink, void)`) and is not a
`region/1`, so nobody takes it as a vantage or walks through it.

## Layer

strategy

## Dependencies

- `core/primitives/core_aggro`

## Methods

| Method | Description |
|--------|-------------|
| `bringAndPush(?e, ?s)` | Find ground whose hazard does `?s` and a region at its edge; `bringTo` the edge, then `forceInto` the ground. |
| `forceInto(?e, ?to)` | A push or a pull moves `?e` into `?to` - alternatives, not fallbacks. |

## Examples

### Example 1: Pushed over

**Given:** a `gob` in `keep`, next to the `brink`, whose ledge drops into the `void` (`abyss`, `hazard(abyss, fallen)`); the player holds an unlimited `gust`.

**When:** `bringAndPush(gob, fallen)`

**Then:** plan contains `opPush(player, gob, keep, brink)`, `opPush(player, gob, brink, void)`; final state has `status(gob, fallen)`.

### Example 2: Pulled to the edge, pushed over

**Given:** the same ground; the Warden's `magnetize` (a pull) as a signature, and one `gust` charge (a push) for the player.

**When:** `bringAndPush(gob, fallen)`

**Then:** exactly one plan; it contains `opLure(warden, gob, keep, brink)`, `opPush(player, gob, brink, void)`.

### Example 3: Taunted there, pushed over

**Given:** the `gob` in `keep`; the player holds `dash`, the Warden holds `gust`.

**When:** `bringAndPush(gob, fallen)`

**Then:** plan contains `opTaunt(player, gob, keep, brink)`, `opPush(warden, gob, brink, void)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | A taunt is not a forced movement | With only a `dash`, the enemy is brought to the edge but not over: no plan. |
| P2 | Nobody walks into the drop | No plan moves a companion into the `void`. |
| P3 | What has fallen needs nothing | An enemy that is already `fallen` gives no plan. |
| P4 | Nothing is pulled into the drop | A pull brings something toward the puller, and nobody stands beyond the void: with only a pull, no plan. |
