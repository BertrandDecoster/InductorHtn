# Overcooked 2 — evidence appendix
Pure cooperative throughput: role/zone assignment, parallel prep, and dedicated long-task owners.

Overcooked has no combat — its entire difficulty is *coordination throughput*. That makes it the
canonical model for the pipelining pattern: the team is a production line, and the bottleneck is
idle hands, clogged stations, and long tasks that stall everything behind them. Multiple independent
guides converge on the same three tactics, which map onto the repo's `parallel()` keyword and
buffer-threshold preconditions.

See the cross-game synthesis in [`../team-patterns-catalog.md`](../team-patterns-catalog.md).

## Patterns this game exemplifies

| Catalog pattern | Tactic from this game |
|-----------------|-----------------------|
| [1 — Role assignment](../team-patterns-catalog.md#problem-1--role--responsibility-assignment) | Allocate specific jobs / distinct kitchen zones per chef |
| [8 — Throughput / pipelining](../team-patterns-catalog.md#problem-8--throughput--task-pipelining) | Parallel prep ahead of orders; a dedicated chef owns long-running tasks |

## Verified tactics

**Role / zone assignment.** Allocate specific jobs to each chef, and assign different zones to
different players, to minimize multitasking — "if the stage is more segmented" this matters more.
— [GameRant Overcooked 2 guide](https://gamerant.com/overcooked-2-how-to-get-four-stars/)

**Parallel prep (produce-ahead staging).** "Have one player throw down multiple plates with buns and
toppings, while another player cooks the meat"; "cook pizza dough in bulk and lay out multiple plates
with crust … and set plates with lettuce for salad." Components are staged *ahead* of orders so
assembly is instant.
— [GameRant Overcooked 2 guide](https://gamerant.com/overcooked-2-how-to-get-four-stars/)

**Dedicated long-task owner.** "Have a chef that stays on top of actions like mixing, baking, or
washing a load of dishes," keeping "the assembly line chugging along as smoothly as possible;
unhindered and unclogged." Dishwashing in particular is repeatedly called out as a dedicated
bottleneck role.
— [GameRant Overcooked 2 guide](https://gamerant.com/overcooked-2-how-to-get-four-stars/),
corroborated by DualShockers, SteelSeries, MakeUseOf, and Steam community guides.

## Caveats

- All tactics come from a single primary game, but multiple independent guide sources agree on them,
  so confidence is high for the *pattern* even though the game count is one.
- "Buffer threshold" for produce-ahead staging (e.g. keep ≥3 staged plates) is an HTN modelling
  choice — the guides prescribe *staging ahead*, not a specific number.

## See also
- [`../team-patterns-catalog.md`](../team-patterns-catalog.md) — the cross-game pattern catalog
- [`../../upgrades/ruleset-keywords.md`](../../upgrades/ruleset-keywords.md) — the `parallel()` keyword
  the prep/cook sketch uses
