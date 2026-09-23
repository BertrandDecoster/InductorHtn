# Fork Upgrades

What this fork added on top of the upstream InductorHtn engine — both new
ruleset-language capabilities and new planner-algorithm instrumentation.

| Upgrade | Page | Layer |
|---------|------|-------|
| New ruleset keywords | [`ruleset-keywords.md`](ruleset-keywords.md) | Language — `parallel()`, numeric fluent effects (`increase`/`decrease`), typed parameters |
| Query tracing | [`query-tracing.md`](query-tracing.md) | Planner — trace decomposition and Prolog resolution |
| Method-failure tracking | [`method-failure-tracking.md`](method-failure-tracking.md) | Planner — per-method failure histogram (where each method's decomposition blocks) |

For the full syntax of all keywords (including upstream ones), see
[`../reference/htn-syntax.md`](../reference/htn-syntax.md).
