# Ruleset Creating

> **Ruleset doc quartet.** Syntax (`ruleset-htn-syntax.md`) - keywords.
> Writing (`ruleset-writing.md`) - heuristics + measured optimizations.
> Iterating (`ruleset-iterating.md`) - debug/analyze a ruleset you have.
> **Creating** (this file) - the end-to-end workflow from design brief to a
> ruleset that is *verified interesting*, not just correct. Recurring design
> rulings live in `ruleset-policies.md`.

Correctness is the floor, not the bar. A ruleset can lint clean, plan
correctly, and still be a bad puzzle: one-action solves, a dominant loadout,
one real strategy dressed up as three. Every step below therefore names the
**tool** that checks it — the fun criteria from
`../game-design/pcg-puzzles-and-fun.md` and `../game-design/GDD.md` §3.6 are
wired in as concrete gates, not vibes.

## The gates, up front

| Gate | Target | Tool | Theory it operationalizes |
|------|--------|------|---------------------------|
| Causal depth | 3-5 layers per challenge | `indhtn_quality.dag --assert-depth 3:5` | "not too short, not too convoluted" (GDD 3.6); the player's unlock chain |
| Solution diversity | >= 2 mechanically distinct clusters per challenge | harness `diversity` | "2-3 ways to defeat an enemy" (GDD 3.6) |
| Decision matters | some-but-not-all loadouts full-clear | harness `P2_decision` | loadout choice is load-bearing |
| No choke point | each challenge solvable by enough loadouts | harness `P1_choke` | dead-end loadouts are fine; unsolvable-for-most is not |
| No dominant pair | no proper-superset loadout | harness `dominance` (POL-3) | Sirlin: degenerate strategy |
| No dead content | every skill/atom/method reachable | harness `P3/P4/P5` | authored content must be live (or POL-1 declared) |
| Gating is real | no marker-less solve of a gated challenge | harness `P6_comboGated` | combos can't be bypassed by the fight baseline |
| Fairness | every gated edge has a discoverable clue | harness `fairness` (opt-in) | solvability is necessary, NOT sufficient (pcg-puzzles-and-fun.md C10) |
| No trivial plan | shortest plan >= N ops | harness `minPlanLength` | quantify-over-play: a universal property of ALL plans |

**Causal depth** is the metric behind the "trivial plans" complaint, and it is
NOT plan length: an action is deeper only when it consumes a fact an earlier
action produced (via `del()` or a method `if()`). A 7-step do() montage of
independent actions is depth 1. Depth comes from *threading state*: freeze
adds the bridge, the bridge enables the crossing, the crossing enables the
button, the button opens the doors. If your challenge measures depth 1,
the fix is to make operators produce facts that later preconditions consume.

## The workflow

### 1. Sketch the unlock-DAG backward from the goal (paper first)

Start from the challenge's end state and work backward: what fact does the
final action consume? What action produces it? What does *that* action
consume? (Gilbert's puzzle dependency chart; `pcg-puzzles-and-fun.md`.)
Target shape:

- **3-5 causal layers** from initial facts to the goal.
- **Bushy diamonds**: a layer opens 2-3 options that collapse to a bottleneck
  (a fact every plan needs) before opening again. Pure chains are corridors;
  undifferentiated fans are button-mashing.
- **Player choice prunes the DAG**: each loadout should enable a small subset
  of edges (skills gate edges via `equipped`/`skillGrants`-style facts).
- Decide up front which facts are **choice** (the loadout), which are
  **fluent** (operator-produced state — your depth budget), and which are
  **static** world data.

### 2. Vocabulary: facts and general verbs

Per `ruleset-writing.md`: data plus general verbs, one source of truth, full
relations, closed vocabulary, decodable flat names (POL-6). Model the sketch's
edges as operators whose `add()` is exactly the fact the next layer consumes.

### 3. Methods bottom-up, exemplar in hand

Copy the matching pattern from `exemplars/` (connectivity -> `logistics.htn`,
recursion -> `blocksworld.htn`, fluents -> `barman.htn`, multi-goal ->
`rover.htn`; the most elaborate live level is
`prototypes/fortress-loadout/level.htn`). One method per genuinely different
strategy; combos follow POL-2 (simultaneous, `parallel(...)`,
`invulnerable`-gated); add `opResolveAtom(atom, method)` markers plus
`challengeAtom`/`atomMethod` metadata as you go — the harness needs them.

### 4. Lint and plan (the correctness floor)

`indhtn_lint` (accept only what POL-7 or a POL-1 declaration covers), then
`indhtn_find_plans` per challenge; `indhtn_method_failures` when a strategy
doesn't fire. This is the `ruleset-iterating.md` loop — go there for the
debugging playbook.

### 5. DAG gate (depth and structure)

```
PYTHONPATH=mcp-server python -m indhtn_quality.dag <level.htn> \
    --goal "<challenge>()." --facts "<one loadout's facts>" \
    --format summary --assert-depth 3:5 --verify-replay 1
```

Read the layer listing: it should look like your step-1 sketch. `--format
mermaid` renders the graph for review; bottleneck facts are the diamond
waists; `--verify-replay` cross-checks the analysis against the engine.
Depth 1-2 with a long plan = a montage — go back to step 2 and thread state.

### 6. Harness sweep (the full battery)

Write a `quality.json` next to the level (copy
`prototypes/fortress-loadout/quality.json` and adjust pool/goals/metadata),
then:

```
PYTHONPATH=mcp-server python -m indhtn_quality.harness <dir>/quality.json
```

Read the matrix like a designer: the FULL-column spread (healthy: same order
of magnitude, e.g. 3-18), which loadouts die where, what each skill
exclusively unlocks (`generativity` — a zero-score skill is a key that opens
nothing; merge or enrich it). Structural gates (P1-P6, cross-check) are
`error` severity: they must pass. Aspirational gates (depth, diversity,
dominance, generativity) are `warn`: each WARN is either fixed or explicitly
accepted in the report with a reason.

Fix moves, cheapest first (proven on the fortress level): edit world FACTS
(an `adjacentArea` vs `lureSpot` flip turns a solo shove into a co-op combo);
add a target trait + method to rescue a dead pairing; comment out (POL-4) the
method a dominant pair rides. Re-run after every change — collateral is
normal and the matrix shows it immediately.

### 7. Report with evidence

Baseline vs final: plan counts per challenge, the DAG summary (depth,
clusters, bottlenecks), the harness verdict, lint status vs POL-7, and every
accepted WARN with its reason. Never claim a gate passed without showing the
tool output (the `/htn-improve` closing rule applies here too).

## See also

- `/htn-create` (`.claude/commands/htn-create.md`) — runs this workflow from
  a design brief; `/htn-audit` — runs gates 4-6 on an existing level.
- `ruleset-policies.md` — the design rulings the gates encode.
- `../game-design/pcg-puzzles-and-fun.md` — why "solvable" is not "fun":
  preconditions must be inspectable, commitment needs a confirmation gate,
  and every gated edge needs a discoverable clue.
