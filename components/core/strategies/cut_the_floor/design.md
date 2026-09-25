# Cut the Floor

## Purpose

The ground goes from under them. The need is an enemy with a status that some hazard does to
whoever stands on it (the abyss: `fallen`). This way of meeting it: ground with a feature that
some element turns into that hazard (fire on a rope bridge), the enemy brought onto it - and
every other enemy that can be brought, since the ground goes only once - the companions off it,
then whoever holds the element puts it down. Who brings each enemy is decided by what the
companions hold (`bringTo`); who casts, by who holds the element (`castElement`).

The reaction rewrites the ground: what burned cannot burn again.

## Layer

strategy

## Dependencies

- `core/primitives/core_aggro`
- `core/primitives/core_chemistry`

## Methods

| Method | Description |
|--------|-------------|
| `cutTheFloor(?e, ?s)` | Find a feature some element turns into a hazard doing `?s`; bring `?e` there, bring the others if they can be brought, step off, cast the element. |
| `bringOthers(?e, ?r, ?s)` | Every other enemy without `?s` and not on `?r` is brought there (all or nothing; the caller tries it). |
| `stepOff(?r)` | Every companion on `?r` walks to the first region next to it; nothing to do if nobody is there. |

## Examples

### Example 1: One burn takes both

**Given:** a rope `bridge` between the `keep` (a `gob`) and the `tower` (a `bot` that resists a push); fire turns rope into the abyss, `hazard(abyss, fallen)`; the player holds `gust` and one `ignite` charge, the Warden holds `magnetize`.

**When:** `cutTheFloor(gob, fallen)`

**Then:** plan contains `opPush(player, gob, keep, bridge)`, `opLure(warden, bot, tower, bridge)`, `opCastRegion(player, ignite, bridge, rope, abyss)`; final state has `status(gob, fallen)`, `status(bot, fallen)`, `regionHas(bridge, abyss)`.

### Example 2: The taunter steps off first

**Given:** the same, but the player holds `dash` instead of `gust`.

**When:** `cutTheFloor(gob, fallen)`

**Then:** plan contains `opTaunt(player, gob, keep, bridge)`, `opNavigate(player, bridge, keep)`; final state has `status(gob, fallen)` and not `status(player, fallen)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No element, no cut | Without anyone holding fire, there is no plan. |
| P2 | The ground is spent | After the cut, no region has `rope`. |
| P3 | Whoever cannot be brought is left | With no pull, the `bot` (which resists a push) stays in its tower and does not fall; the `gob` still does. |
