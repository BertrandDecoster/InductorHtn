---
name: htn-level
description: Use when designing, scoring or playtesting a puzzle level (levels/*): the fun scorecard, choice-space declarations, verify, and playing a level through the MCP level tools. For writing the rules themselves, use htn-author first.
---

# Level design loop and fun metrics

Iterate a level like this:
1. One hypothesis.
2. One rule change.
3. `certify`.
4. Play it through the MCP level tools as the player.
5. Run `explain` and `fun` afterwards, and compare.
6. A human tries it.

Rules: `docs/reference/level-design-loop.md`. Tools: `docs/tools/mcp-server.md`
(`indhtn_load_level`, `indhtn_observe`, `indhtn_actions`, `indhtn_act`, `indhtn_undo`,
`indhtn_explain`, `indhtn_fun`). `.mcp.json` starts the server via `mcp-server/launch.py`, and
`python mcp-server/launch.py --check` verifies the setup. Playthroughs land in `.playthroughs/`
(gitignored).

## The CLI (`PYTHONPATH=src/Python python -m htn_components <command>`)

```
verify <level>                   # deps + tests + plan + fun scorecard (non-gating)
play <level> [--solution N | --class LABEL] [-i]   # plan narrative (grounded effects)
trace <level> [--goal GOAL]      # decomposition tree
fun <level> [--ablate] [--loadouts] [--json] [--md FILE]   # fun scorecard
fun-all [--range X Y]            # comparison table; --range = expressive-range grid
fun-compare <a> <b>              # side-by-side profile diff
fun-rate <level> --rating 1..5   # held-out human rating -> levels/fun_ratings.jsonl
fun-calibrate                    # which metrics track the ratings (Spearman)
```

## Fun metrics

`fun` scores the *shape of a level's solution space*:
- how many genuinely different ways exist, and how deep they are,
- whether any one companion can carry a plan alone (an idle human seat is only a warning),
- which of the declared X-of-Y choices work.

It never claims a level is fun. The full definition, bands and blind spots are in
`docs/FUN_METRICS.md`. Bands and weights are data, in `src/Python/htn_metrics/metrics.json`:
calibrate there, not in code. Fixtures are in `tests/fun_fixtures/`. Those are metric
calibration cases, not style examples.

A level opts into the choice-space family (F4) by declaring facts in `level.htn`:

```prolog
funChoiceSpace(kit, 2).                       % pick 2 ...
funChoice(kit, emp).                          % ... from these
funChoiceFact(emp, carrying(player, emp)).    % how a pick alters the world
funBlocker(door).                             % must be solved
funBlockerGoal(door, clear(door)).            % optional; else derived from goals()
```

It can also state its intent and keep its hypothesis as a regression test. `verify` fails on
either one; nothing else in the scorecard gates:

```prolog
funIntended(combo, opCastRegion).             % F7: every plan uses a member of `combo`
funForbidden(opBribe).                        % F7: no plan uses this
funExpect(player_decision_points, atLeast, 2). % checked by fun and verify
```

`--ablate` and `--loadouts` re-plan many times. Their results are cached on disk in
`.htn_metrics_cache/`.
