# Fun Metrics for HTN Levels

> **The claim this document makes is narrow.** We cannot measure fun. We can measure the *shape of
> the solution space the player searches*, and the GDD asserts that certain shapes produce fun. Every
> number below is a proxy for one of those asserted properties. A level that scores well has "the
> structural properties we believe make solving it fun" — never "is fun."

## 1. Why this exists

The point of the level work in this repo is not *does a plan exist*. It is **the player is the
solver**. The HTN planner is an oracle we use while authoring, to confirm that several genuinely
different, satisfying plans exist — so we know the player has interesting things to find.

Before this tooling, nothing measured that. `certify` checks syntax, tests, and design coverage. The
only interestingness assertions in the whole repo were two hand-written lines in one level test
(`levels/gamehack_multipath/test.py`: `>= 10` plans plus a complexity bound). The design intent lived
in prose:

- `src/docs/GDD.md` §2 Core Pillars — *"Challenges are designed to be solvable in several distinct
  ways"*; *"No single entity can overcome significant challenges alone"*; *"the player is crucial for
  initiating, enabling, and finalizing key actions."*
- `src/docs/GDD.md` §3.6 Core Gameplay Principles — 2-3 ways per enemy; plans neither too long nor too
  short (*"is 'I cast fireball and everyone dies' a satisfying plan?"*); no single companion can solo
  the map, whoever controls it. The human's companion standing idle is a lesser, seat-level concern.
- `src/docs/PUZZLE_IDEAS.md` — complexity comes from **depth** (combining existing rules), not
  **width** (adding new rules); no ambiguity; no frustration mechanics.

This document turns that prose into a scorecard a human can read, disagree with, and iterate on.

## 2. What we actually measure

The player's experience is **search over a lattice of choices**, not the execution of one plan. So the
object measured is not a plan, and not even the plan set. It is three layers:

1. **the plan set** — what can be done;
2. **strategy classes** — plans grouped by fingerprint, i.e. how many genuinely different *ideas*
   exist;
3. **the choice → solvability map** — which of the player's X-of-Y combinations actually work.

The third layer is the target shape this whole design is built around:

> The player chooses **X** things among **Y**. Each choice enables multiple things. The puzzle is
> finding a combination that solves all the blockers.

That is a set-cover / constraint-satisfaction structure. It is the core of the design, not an
afterthought — family F4 exists to measure it directly.

### Vocabulary

| Term | Meaning |
|------|---------|
| **plan** | One solution returned by `FindAllPlansCustomVariables` — an ordered list of ground operators. |
| **strategy fingerprint** | The ordered tuple of `(task/arity#methodIndex)` for every *method* node on the plan's decomposition path that passes two filters: its defining component sits in a **fingerprint layer** (default `goals`, `strategies`, `levels`), and it sits within `fingerprint_max_depth` (default 2) of the root. Primitive-layer choices are mechanical re-binding, not a different idea; and a strategy is a choice made near the top of a plan, so alternatives deep inside a phase are implementation detail. The depth cap is what keeps a self-contained level honest — a level defining all its methods in `level.htn` has no layering to appeal to, and without the cap every phase choice would read as a separate strategy. |
| **decomposition path** | The plan's *own* decomposition, recovered from the accumulated tree. See §3a. |
| **strategy class** | An equivalence class of plans sharing a fingerprint. This is the unit of "a way to solve it." |
| **mechanism** | The component that owns an operator, via `ComponentLoader.operator_owner`. The mechanism set of a plan is which parts of the rule library it exercises. |
| **blocker** | A thing the level declares must be solved (`funBlocker/1`). |
| **loadout** | One X-sized subset of the Y declared choices. |

## 3. The level-declared choice space

F4 needs to know what X-of-Y and "blockers" mean for a given level. This is declared as **facts in
`level.htn`**, matching the existing convention that tunable knobs are Prolog facts rather than
manifest fields:

```prolog
funChoiceSpace(skillLoadout, 2).                              % pick 2 ...
funChoice(skillLoadout, waterSkill).                          % ... from these
funChoice(skillLoadout, fireballSkill).
funChoice(skillLoadout, iceBlastSkill).

funChoiceFact(waterSkill, hasSkill(companionA, waterSkill)).  % how a pick alters world state
funChoiceFact(waterSkill, hasSkill(companionB, waterSkill)).  % a pick may carry several facts

funBlocker(gob).                                              % must be solved
funBlockerGoal(gob, planToDamage(gob)).                       % optional; else derived from goals()
```

Semantics: a loadout is evaluated by taking the level's fact set, **removing every `funChoiceFact` of
every declared choice**, then **adding back only those of the selected choices**. The level's **own
goal** (the encounter) is then planned in that world, once, with persistent state. A loadout is
*winning* if the encounter has at least one plan. Each blocker's goal is also probed on its own from
the same start world - those per-blocker answers are **diagnostics**: they say which blocker a losing
loadout failed on and how close it came (`near_miss_count`), and they give
`loadout_feasibility_independent`, the old "wins each fight" number. When the two feasibilities
diverge, a resource that one fight consumes is needed by the next: the loadout wins each fight but
not the level (`shared_resource_loadouts` names them).

Read via `PrologQuery`. No linter, loader, or C++ change is required. Levels that declare none of
these facts still get F1-F3, F5 and F6, plus an explicit **"F4 not declared"** note — never a silent
zero.

## 3a. Two things the planner does not hand you

Both were discovered while building this, and both are load-bearing for
everything downstream. They are documented here because the numbers are wrong
in silent, plausible ways if either is got wrong.

### Per-solution trees accumulate

`GetDecompositionTree(i)` does **not** return solution *i*'s decomposition. It
returns every node the planner has created up to and including solution *i*, so
the calls are nested: `tree(i) ⊇ tree(i-1)`. Used raw, every plan in
`gamehack_multipath` appears to use all three strategies at once.

Taking only the nodes *new* in `tree(i)` is also wrong — it drops the prefix the
solution shares with its predecessor.

The recovery anchors on the operators instead. A plan's ground operators must
appear as operator nodes in the tree in order; matching them **backwards,
preferring the highest-numbered node at each step**, selects the most recent
occurrence of each, which is the one belonging to this solution. The
decomposition is then the union of those operators' ancestor chains. This is
self-checked: the operator nodes on the recovered path must equal the plan's
operator sequence exactly, and a mismatch is reported as a note on the profile.
It currently reconciles for 116/116 plans on `gamehack_multipath`.

### Operators have no preconditions

HTN operators here are unconditional `del`/`add`. All the gating lives in
method `if()` clauses, which are evaluated *top-down, before* their subtasks
run. So a plan that acquires a skill and then uses it contains no re-check to
observe: nothing in the ruleset ever reads `hasSkill` again after acquisition.

A causal graph built only from "operator *i* adds what operator *j*'s
precondition consumes" therefore reads depth ≈ 2 for every plan in every
gamehack level — not because the plans are shallow, but because the encoding
hides the dependency. F3 adds a third edge kind (`provides`) for exactly this:
*i* is the **first** producer of a fact that was not true initially, and some
method ancestor of *j* consumed it. The world still requires *i* before *j*
even though the planner committed to the order structurally.

### A probe that did not finish proves nothing

Every counterfactual (ablating one fact, trying one loadout) is a planning run that can hit the
memory budget, the plan cap, or a world that will not compile. Such a probe is **`unknown`**, not
"unsolvable". `ProbeResult.status` is tri-state (`solvable | unsolvable | unknown`, with the error
kept), and every conclusion drawn from probes - a lost class, a linchpin, an independent pair, a dead
choice - is computed over the conclusive probes only. The scorecard reports `unknown_probes` and
withholds the affected conclusions when it is non-zero, and says so.

Probes are cached by an identity that covers the level source, **the sources of every dependency**,
the fingerprint configuration, and the extractor version. Editing a strategy component invalidates
the level's cache.

## 4. The six metric families

Each family reports a verdict: **pass**, **warn**, or **fail**, with the offending numbers. Bands live
in `src/Python/htn_metrics/metrics.json` — iterating on calibration means editing that file, not the
code.

---

### F1 — Multiplicity: *are there several ways?*

Encodes GDD §3.6 "always have at least 2 or 3 ways to defeat an enemy."

| Metric | Definition |
|--------|------------|
| `plan_count` | Number of plans returned. Carries a `truncated` flag. |
| `strategy_classes` | Number of distinct strategy fingerprints. |
| `redundancy` | `plan_count / strategy_classes`. |

**Bands.** `strategy_classes` ∈ [2, 5] passes. Below 2 → **fail** (one idea). Above 5 → **warn** (an
author cannot hold that many distinct intents; usually the fingerprint layer is picking up noise).
`redundancy` > 10 → **warn**: the plan space is mostly re-binding noise, which inflates `plan_count`
without giving the player anything new to find.

When the planner runs out of memory the family says so ("planner ran out of memory") rather than
reporting "unsolvable". With `--loadouts`, `strategy_classes_across_loadouts` counts the classes that
appear under *any* winning loadout, since the default kit need not expose them all.

**Blind spot.** `strategy_classes` is only as good as the fingerprint-layer choice. If a level puts
real tactical alternatives in a `primitives` component, they will not be counted.

---

### F2 — Distinctness: *are the ways actually different?*

This is the family that catches fake multiplicity — the failure mode a level like `multipath` is most
at risk of.

| Metric | Definition |
|--------|------------|
| `min_pairwise_distance` | Minimum over class pairs of `1 − J(a, b)`, where `J` is **weighted Jaccard** (`Σ min / Σ max`) over a bag combining the plan's operator-name multiset with its mechanism set. Each class is represented by its canonical (shortest, then lexicographically first) member. |
| `mean_pairwise_distance` | Mean of the same over all class pairs. |
| `mechanism_disjointness` | Fraction of class pairs whose mechanism sets are not nested in one another. |
| `independence` *(needs `--ablate`)* | Number of class pairs with **disjoint critical-fact sets**. A fact is *critical* for a class if removing it from the initial state kills every plan in that class. |
| `shared_linchpin` *(needs `--ablate`)* | A single fact whose removal kills **all** classes. |
| `goal_target_linchpins` *(needs `--ablate`)* | Linchpins that name an atom from the goal itself — `enemy(gob)` for the goal `planToDamage(gob)`. Tracked but never counted as a flaw: delete the target and there is nothing to plan against, which is true of every level and says nothing about its design. They are also excluded when comparing classes, since a shared target is shared by definition and would otherwise mask genuine independence. |
| `shared_gates` *(needs `--ablate`)* | Facts every route needs **because a declared blocker needs them** — removing the fact also kills a `funBlockerGoal`. A corridor both routes walk through, or the Warden both routes rely on, is infrastructure the encounter passes through, not one idea under several names. Gates are reported as a note and excluded from independence. Cast facts (`role/2`, `signature/2`) are never linchpin candidates. |
| `ablation_conclusive`, `ablation_unknown_probes` | Whether every ablation probe finished. When any did not, linchpin and independence claims are withheld. |

**Bands.** `min_pairwise_distance` ≥ 0.4 passes; below `0.4 × severe_distance_factor` (0.2) is
*severe*. At least one class pair with disjoint critical sets passes. A non-goal-target, non-gate
`shared_linchpin` → **warn**, and **fail** only when the distance is also severe: shared
infrastructure is a smell, not proof of a duplicate idea. Sampled ablation (`max_ablation_facts`) is
reported and downgrades a fail to a warn.

**Ablation outranks distance.** When ablation confirms the classes depend on disjoint facts, a
syntactic-distance shortfall is downgraded from fail to warn — the classes are surface-similar but
genuinely independent, which is a different (and much smaller) problem than a duplicate idea.

**Blind spot.** Operator-name distance ignores arguments, so "companion A does it" vs "companion B
does it" correctly reads as *identical* — but so does "burn the goblin" vs "burn the ogre," which a
designer might consider different. Ablation is the honest test; the syntactic distance is the cheap
one.

---

### F3 — Depth: *is the plan worth executing?*

Encodes GDD §3.6 — *"is 'I cast fireball and everyone dies' a satisfying plan?"* — and distinguishes a
**combo** from a **chore**.

| Metric | Definition |
|--------|------------|
| `plan_length` | min / median / max operator count across plans. |
| `causal_depth` | Longest path in the plan's **causal DAG**, in operators. Three edge kinds, in decreasing strength of evidence: **consumes** (`i` adds a fact `j` deletes); **enables** (`i` adds a fact a method ancestor of `j` consumed, evaluated *after* `i` ran); **provides** (`i` is the first producer of a fact not true initially that a method ancestor of `j` consumed — see §3a). This is the Primer → Catalyst → Detonator depth. |
| `interlock` | Fraction of operators participating in at least one causal edge. A chore of independent actions scores 0; a true chain scores 1. |
| `decomposition_depth` | Maximum tree depth of the decomposition. |

**Bands.** `plan_length` ∈ [3, 12] (configurable). Best class `causal_depth` ≥ 3. `interlock` ≥ 0.5.

**Blind spot.** `interlock` measures *participation*, not *necessity* — an operator on a causal edge
may still be removable. True necessity requires re-planning without it, which is deliberately not done
here for cost reasons. `causal_depth` also cannot see effects that exist only in the game engine
(an operator whose real consequence is visual or spatial, like `opSynchronizeOnPlates`).

---

### F4 — Choice structure: *the X-of-Y lattice*

The user's target structure. `multi_use_factor` is what makes this a puzzle rather than a 1:1
blocker↔pick matching exercise.

| Metric | Definition |
|--------|------------|
| `loadout_feasibility` | Fraction of the C(Y, X) loadouts under which the **encounter goal** has a plan (one persistent world). |
| `loadout_feasibility_independent` | Fraction under which every blocker has a plan **on its own** from the start world - the old rule, kept as a diagnostic. A gap between the two is a shared consumable. |
| `shared_resource_loadouts` | Loadouts that win every fight independently but not the encounter. |
| `unknown_probes` | Loadout probes that did not finish; feasibility is computed over the rest and the shortfall is reported. |
| `winning_loadout_count` | Absolute count of winners. |
| `minimal_cover_count` | Winners with no winning proper subset — the genuinely distinct "answers." |
| `multi_use_factor` | Mean number of blockers a single choice addresses, averaged over the choices that address at least one. A choice *addresses* a blocker when dropping it from an evaluated loadout loses that blocker — so this measures work done, not mere co-presence. Dead choices are excluded from the mean: they are reported separately, and counting them here would conflate "my picks are single-purpose" with "some picks are red herrings", which are different problems with different fixes. |
| `mandatory_choices` | Choices present in *every* winning loadout — a tax, not a choice. |
| `dead_choices` | Choices present in *no* winning loadout — red herrings. |
| `near_miss_count` | Loadouts solving all but exactly one blocker. |

**Bands.** `loadout_feasibility` ∈ [0.05, 0.4] passes. At or above `feasibility_saturated_at` (0.95)
→ **fail**: no scarcity, any pick wins. At or below `feasibility_unsatisfiable_below` → **fail**:
nothing wins. `multi_use_factor` ≥ 1.5. Not all X mandatory. `dead_choices` ≤ 40% of Y — too many
red herrings are noise; **no minimum**, a level with no dead pick is not penalised. `near_miss_count`
≥ 1 — near misses are what make a wrong attempt feel *close* rather than random. A level that
declares a choice space but was run without `--loadouts` reports **"declared but not measured"**.

**Blind spot.** F4 is combinatorial. Large Y requires sampling, which makes `loadout_feasibility` an
estimate. Whenever a cap or sample is applied it is **reported in the scorecard**, never applied
silently.

---

### F5 — Discovery difficulty: *is it a puzzle to find?*

**This is the weakest family. It is built from proxies and is expected to need the most iteration.**
Read its numbers as conversation starters.

| Metric | Definition |
|--------|------------|
| `decision_breadth` | Mean number of method alternatives defined for each task signature that appears on some plan's decomposition path. Static (counts rules in the loaded sources), restricted to tasks the level actually reaches. Single-method primitives count, which drags the mean down by design. |
| `search_cost` | Planner resolution steps divided by median plan length. Reported as `unavailable` when the build does not surface a step count. |
| `insight_depth` | Minimum over classes of the number of operators whose added facts are first consumed **≥ 2 operators later** — a setup move you have to plan ahead for, rather than a greedy next step. |
| `red_herring_ratio` | Fraction of world entities (atoms appearing in level facts) that appear in no plan. |

Two further numbers are reported but not banded, because it is not yet clear what a good value is:
`planner_dead_ends` and `planner_nodes_explored`.

**Bands.** `decision_breadth` ≥ 2. `insight_depth` ≥ 1 — at least one non-greedy move must be
required. Note this is a **minimum over classes**: one route that demands foresight does not make the
level non-greedy if another route can be played straight through. `red_herring_ratio` ≤ 0.6 and **no
minimum** - unused scenery is a tool the author may use, not something the scorecard rewards -
counting only entities outside the declared choice space (those are F4's to judge, via
`dead_choices`, and would otherwise be counted twice).

**Correction to an earlier assumption.** This family was designed expecting that per-solution trees
contain only the success path — `MarkPathSuccess` tags only the winning path and
`SolutionFromCurrentNode` filters by `solutionID`. In practice the accumulated tree (§3a) *does*
retain explored-and-failed branches, flagged `isFailed`, so per-solution dead-end counts are
available today without any C++ change. They are surfaced as `planner_dead_ends`. Turning them into
a *banded* difficulty metric is the obvious v2 work for this family; right now they are raw
observation.

**Blind spot.** `search_cost` measures the **planner's** difficulty, which correlates with but is not
the player's. On this build it is usually `unavailable`: `FindAllPlans` does not update the Prolog
resolution-step counter, which only tracks `PrologQuery`.

---

### F6 — Cooperation: *does any one companion carry the plan alone?*

Encodes GDD §2 (*"No single entity can overcome significant challenges alone"*) and §3.6 (*"no single
companion can solo the map, whoever controls it"*).

**The pillar is cooperation, not human presence.** A plan that two companions complete together is
fine whether or not the human-controlled companion is one of them. What may never happen is one
companion doing everything: that is `single_actor_plans`, and it is the family's real hard fail. The
seat metrics (`soloable_plans`, `player_load`, `player_decision_points`, `player_causal_out`) describe
how much the controlled companion has to do and decide *in the seat the level gives it*. They are
level-design diagnostics, useful for choosing which companion the human should be, not proxies for
the pillar. The scorecard reports `soloable_plans` above `soloable_plans_max` as a **warn**, never a
fail; a level whose hypothesis wants the seat busy (`grease_trap`) pins that in its own tests.

Two facts about the design shape this family. The player character and the AI companions are
**interchangeable in ability** - they differ only by who controls them - so no ruleset may reserve
an ability for the player, and cooperation has to come from *task roles* (the primer may not pay
off). And read literally as "some operator mentions the player", a no-op `opStayInLocation(player)`
satisfies the pillar, and so does a companion shielding the player; neither is the player *doing*
anything. The family therefore uses an **actor convention**: an operator's actor is its first argument
(`actor_position` in `metrics.json`), or the index a level's `funActor(opName, index)` fact names.
An operator is **consequential** when it has a non-empty del/add and is not declared
`funNoop(opName)`. A **player action** is a consequential operator whose actor is the controlled
companion (`player_atom`).

| Metric | Definition |
|--------|------------|
| `single_actor_plans` | Plans whose consequential operators all have the same actor - one companion, whoever controls it, does everything. |
| `soloable_plans` | Plans with no player action: the AI companions complete the level while the controlled companion stands idle. |
| `player_load` | Player actions as a fraction of consequential operators, across all plans. |
| `passive_involvement` | Operators that name the player without the player being the actor (being shielded, being lured to). Reported, not banded. |
| `teamwork_edge_ratio` | Fraction of causal edges (F3's graph) whose two operators have **different actors** - a companion's move that the player's move depends on, or the reverse. |
| `player_causal_out` | Fraction of player actions that feed a later operator. A player whose moves nothing depends on is pressing buttons. |
| `player_decision_points` | Nodes of the plan-space **trie** (all plans overlaid as operator prefixes) where at least two distinct next steps exist and at least one is the player's own action. Choosing to act, or to let a companion open instead, is a decision; a fork among companion operators alone is the planner's. |
| `player_criticality` *(needs `--ablate`)* | Whether removing every fact mentioning the player kills all plans. |

**Bands.** `single_actor_plans` == 0 is the family's only **hard fail**: one companion carried a plan
alone. Everything else is a **warn** about the seat: `soloable_plans` == 0; `player_load` ∈ [0.2, 0.6]
(below is a spectator, above is micromanagement); `teamwork_edge_ratio` ≥ 0.2;
`player_decision_points` ≥ 1.

**How a ruleset guarantees the pillar.** Not with an ability only the player has, but with task
roles that consume state: a primer role and a pay-off role that the same companion cannot fill
(`core_attunement`'s `?not` arguments, or a `free(?slot)` token deleted when a role is taken). The
test is structural: with a single companion the level must have **no plan**, and removing the role
exclusivity must be what brings a single-actor plan back.

The one-companion fixtures (`single_path`, `chore`, `one_shot`, ...) fail F6 on `single_actor_plans`
by construction; their calibration tests pin that reading and assert the controlled companion is
never blamed for it.

**Blind spot.** The actor convention is a convention. An operator written target-first
(`opApplyTag(?tag, ?target)`) has no actor at all unless the level declares `funActor`; such
operators count as nobody's, which understates load but never invents agency. The reverse also
happens: an operator whose first argument is not a companion (`opBreak(golem)`, an enemy;
`opFollow(?e, ...)`) is credited to that atom, so a plan where one companion does everything plus
one enemy-actor operator reads as *two* actors and slips past `single_actor_plans`. Give such
operators the acting companion first, or declare `funActor`/`funNoop` for them.

## 5. The composite score is a diagnostic

A single weighted `fun_score` ∈ [0, 1] is emitted as a convenience for later automated level
generation, computed from explicit per-family weights in `metrics.json`. It is rendered as
"diagnostic composite", it is **never a target**, it is never wired into `certify`, and the `fun`
command's exit code does not depend on it (exit 2 only when the level is unsolvable or the plan
space was truncated).

**It is the least trustworthy output in this document.** It collapses six independent judgments into
one number and thereby hides exactly the information an author needs. Use the per-family profile.
The composite exists so that a fitness function can be derived from the same extraction layer later,
not because a level's fun is one-dimensional.

The composite is **withheld entirely** when the plan space is truncated (see below).

## 6. Truncation

`FindAllPlans` can return partial results when the memory budget is exhausted. Metrics computed over a
partial plan set are meaningless — `plan_count`, `redundancy`, `loadout_feasibility` and every
distinctness number silently become wrong rather than merely imprecise.

The tool therefore detects truncation (an out-of-memory error, or hitting the configured plan cap),
prints **"plan space truncated"** prominently, and **refuses to emit a composite score**. Individual
family numbers are still shown, marked as unreliable. The same discipline applies to every
counterfactual probe (§3a): an unfinished probe is `unknown`, and nothing is concluded from it.

## 7. Calibration

No current level is a positive exemplar. Metrics are therefore calibrated against fixtures that are
degenerate **by construction** — one tiny level per failure mode in `tests/fun_fixtures/` — rather than
against a ranking of levels nobody likes.

| Fixture | Must be flagged by |
|---------|--------------------|
| `single_path` — exactly one plan | F1 |
| `fake_multiplicity` — many plans, one idea, differing only in which ally acts | F1 `redundancy`, F2 `min_pairwise_distance` |
| `shared_linchpin` — three "strategies", all dying to one fact | F2 `independence` |
| `one_shot` — a single operator wins | F3 length, `causal_depth` |
| `chore` — causally independent operators | F3 `interlock` |
| `any_loadout_wins` — every X-of-Y works | F4 `loadout_feasibility` ≈ 1 |
| `one_to_one` — each pick solves exactly one blocker | F4 `multi_use_factor` ≈ 1 |
| `companions_solo` — two companions win while the controlled one is idle | F6 `soloable_plans` > 0 as a **warn**, with `single_actor_plans` == 0: the pillar holds, the seat is the finding |
| `shared_consumable` — one token, two blockers | F4: `loadout_feasibility_independent` > `loadout_feasibility`; the level has 0 plans under a loadout that wins each fight |
| `nominal_player` — the player is only ever mentioned, never the actor | F6 `player_load` 0, `passive_involvement` > 0 |
| `actor_override` — operators written target-first, `funActor` declared | F6 reads the declared index |
| `reference_good` — one coherent encounter: breach three blockers with the chosen tools, then run the vault one of two ways | passes all families, under encounter feasibility |

`tests/test_fun_metrics.py` asserts each fixture trips its intended family **and that the families it
is not about stay clean** — that second half is what makes these calibration tests rather than smoke
tests. A metric that flags everything is as useless as one that flags nothing. `reference_good`
doubles as the documented target pattern for future levels and passes all six families; its
`runHeist` requires the blockers cleared, so the 19 plans are one encounter, not a heist beside a
lattice.

The `shared_linchpin` pair of tests is the load-bearing one: the first asserts F2 **passes**
observationally (distance 0.86, three classes, distinct operators), the second that it **fails**
under `--ablate`. If the first ever starts failing, the second stops proving anything.

### Baseline over the real levels — 2026-07-25

Recorded with `fun-all` plus per-level `--ablate`. This is the thing to iterate against; no level is
a positive exemplar yet, which is the expected starting point.

| level | plans | classes | F1 | F2 | F3 | F4 | F5 | F6 | composite |
|-------|------:|--------:|----|----|----|----|----|----|----------:|
| `gamehack_gh4` | 67 | 1 | FAIL | pass | warn | n/a | warn | FAIL | 0.44 |
| `gamehack_gh7` | 21 | 2 | warn | warn | warn | n/a | warn | FAIL | 0.44 |
| `gamehack_multipath` | 116 | 3 | warn | FAIL | warn | n/a | warn | FAIL | 0.31 |
| `gamehack_mvp` | 1 | 1 | FAIL | pass | warn | n/a | warn | pass | 0.56 |
| `puzzle1` | 1 | 1 | FAIL | pass | warn | n/a | warn | pass | 0.56 |

Three findings worth acting on, in priority order:

1. **The controlled companion is idle in most gamehack plans.** 66 of 116 plans in `multipath`, 35
   of 67 in `gh4`, 10 of 21 in `gh7` contain no player-bound operator, and in `multipath` removing
   every fact that mentions the player still leaves plans. When this baseline was recorded the
   scorecard read that as a pillar violation; under the clarified pillar it is a seat finding
   (`soloable_plans`), and whether one companion carried a plan alone (`single_actor_plans`) was not
   measured yet. Still worth acting on, as a ruleset property: nothing in the gamehack components
   gives the controlled seat a role.
2. **`multipath`'s three strategies are real but shallow-looking.** Ablation confirms all three class
   pairs have disjoint critical fact sets — `stunAndSlowSkill` needs
   `canGetSkillAtLocation(glacier,iceBlastSkill)`, `wetAndElectrocute` needs
   `hasSkill(teslaTower,lightningSkill)`, `stunAndBurn` needs `skillAppliesTag(fireballSkill,fire)` —
   and there is no shared linchpin. The syntactic distance (0.167) is low because all three end in
   the same `opApplyTag` moves. That is a warning about presentation, not about structure.
3. **Nothing has depth.** Best-class `causal_depth` is 1-2 everywhere except `puzzle1` (4), and mean
   `interlock` never reaches 0.5. Per §3a this is partly an artefact of how the gamehack components
   encode ordering, but only partly: `mvp` and `gh4` genuinely have plans whose operators do not feed
   each other.

No gamehack level declares a choice space, so F4 is `n/a` for them.

### The first level on the core vocabulary — 2026-09-10

`levels/grease_trap` (`components/core/*`): swarm in the gallery, iron bearer at the exit, oil in
the corridor, pick 2 of 5 player skills. `fun grease_trap --ablate --loadouts`:

| plans | classes | F1 | F2 | F3 | F4 | F5 | F6 | composite |
|------:|--------:|----|----|----|----|----|----|----------:|
| 2 | 2 (`theBurn`, `theSlipstream`) | pass | warn | pass | pass | warn | pass | 0.85 |

F4: encounter feasibility 0.4 (= independent: nothing consumed across fights *with these picks*),
4 winners, no mandatory pick, `flare` dead, 3 near misses. F6: no single-actor plan and no idle
seat, load 0.58, teamwork
0.58, 1 decision point. F2 warns on operator-name distance (0.33; both routes end in `opStatus` and
`opCastRegion`) while ablation shows 1 independent pair and 18 shared gates (the corridor, the oil,
the cast) - surface similarity, not a duplicate. F5 warns on decision breadth (1.73): single-method
primitives drag the mean, by design. The hypothesis asked for ≥ 2 decision points and got 1: with the
default kit each route is a single line once chosen. That is the next rule to change.

The loop steered three design changes on the way here: iron for the bearer instead of a shield
(so Magnetize, not Gust, is the answer to it), Magnetize moving iron only, and `lure` no longer
dragging the Warden into the sludge. Two design laws then reshaped the ruleset without moving a
number: the player character and the AI companions are interchangeable in ability (the
player-only detonator became a primer/pay-off role rule), and the ruleset decomposes top-down
from the need (`defeatGroup` → `theBurn`/`theSlipstream` → `blastDeadAt`/`strikeDead` →
`castElement`, which binds the holder at the leaf). Same two plans, same scorecard.

## 8. Usage

```bash
source .venv/Scripts/activate

PYTHONPATH=src/Python python -m htn_components fun levels/gamehack_multipath
PYTHONPATH=src/Python python -m htn_components fun levels/gamehack_multipath --ablate --loadouts
PYTHONPATH=src/Python python -m htn_components fun levels/gamehack_multipath --json --md report.md
PYTHONPATH=src/Python python -m htn_components fun-all
PYTHONPATH=src/Python python -m htn_components fun-compare gamehack_mvp gamehack_multipath
```

```bash
PYTHONPATH=src/Python python -m htn_components verify grease_trap             # ends with the scorecard, non-gating
PYTHONPATH=src/Python python -m htn_components play grease_trap --class theSlipstream
PYTHONPATH=src/Python python -m htn_components play grease_trap --solution 1 -i
```

`--ablate` and `--loadouts` re-plan many times and are disk-cached under
`.htn_metrics_cache/`, keyed by (level source, dependency sources, fingerprint config, extractor
version, perturbed fact set). A second run over an unchanged level is fast; editing a dependency
invalidates the cache.

From an AI assistant, the same scorecard is `indhtn_fun(level, ablate, loadouts)` on the MCP server,
and the level is *played* rather than scored with `indhtn_load_level` → `indhtn_observe` →
`indhtn_actions` → `indhtn_act` → `indhtn_explain`. See `docs/reference/level-design-loop.md`.

## 9. Deliberately out of scope (v1)

- **Wiring bands into `certify` as a gate.** The metrics must earn trust before they can block a
  build.
- **A GUI panel.**
- **Any C++ change.** Including the full-`PlanState` tree export that F5 wants.

## 10. Architecture

`src/Python/htn_metrics/`, consumed by the `htn_components` CLI and the MCP level tools. It reuses
rather than reimplements: `ComponentLoader` (dependency-ordered assembly, `operator_owner`,
`resolve_sources`), `parse_htn` (AST), and `indhtnpy.HtnPlanner`.

| Module | Responsibility |
|--------|----------------|
| `extract.py` | One planning run → a `PlanSpace` dataclass. The single source of raw data for every metric. |
| `canonical.py` | Canonicalization, strategy fingerprinting, equivalence classes, pairwise distance (F1, F2). |
| `causal.py` | Per-plan causal graph from operator del/add; `causal_depth`, `interlock`, `insight_depth`, intermediate-state reconstruction (F3, F5). |
| `counterfactual.py` | The shared perturbation harness: single-fact **ablation** (F2) and **X-of-Y loadout enumeration** (F4), over one disk cache. |
| `metrics.py` | The six families as pure functions over `PlanSpace`. |
| `config.py` + `metrics.json` | Bands, weights, caps — the iteration surface. |
| `agency.py` | `ActorConvention`: who performed an operator, whether it is consequential (F6, trie, MCP play). |
| `trie.py` | `PlanTrie`: the plan space as operator prefixes; player decision points; companion auto-advance (F6, MCP play). |
| `narrate.py` | Operators, companion intentions and facts as sentences (`play`, MCP play). |
| `profile.py` / `report.py` | `profile_level` (plan + counterfactuals + verdicts, harness closed in `finally`); terminal scorecard, `--json`, `--md`. |

Two small additions were made outside the package, both additive:

- `ComponentLoader` gained `sources` and `method_owners` accessors, so metrics can re-parse exactly
  what the planner was given without re-walking the dependency graph.
- `extract.ground_solution` / `extract.replay_states` are public, and are now used by
  `htn_test_framework.get_plan_timeline` and `cli.play_interactive` to reconstruct **intermediate
  states**. The planner exposes only the initial and final fact sets; replaying each operator's
  `del`/`add` fills in every step between, and the result is asserted equal to `GetSolutionFacts` in
  the test suite. This closes the two standing "TODO: implement intermediate state tracking"
  comments.

## 11. Status

Implemented: the six families, the counterfactual harness with tri-state probes and
dependency-aware caching, encounter feasibility, the agency metrics, the plan trie, narration,
the `core/*` ruleset with `levels/grease_trap`, and the player-perspective MCP loop.
`python -m pytest tests/test_fun_metrics.py tests/test_fun_counterfactual.py tests/test_fun_agency.py
tests/test_replay_sources.py tests/test_core_level.py tests/test_narrate.py
mcp-server/tests/test_level_tools.py` — 50 passed.

Not done, deliberately: the metrics are not wired into `certify` as a gate; there is no GUI panel;
no C++ was changed. Backlog: telegraphed enemy intent (`intends/3`), a cost model (`funCost/2`) for
nondominated approaches across time/risk/resources, companion inclinations, migrating the two older
component trees to the core vocabulary, `toy_two_step`, and playthrough-derived metrics (observed
decision breadth, recovery after a mistake) once `.playthroughs/` holds data.

## 12. Design recommendations

Things the metrics and the play loop surfaced that are decisions for the GDD, not for this tool.

- **Tactical Focus should default to the companions' intentions and the local affordances, not to
  full plans.** Playing `grease_trap` through the MCP tools, the interesting moment is reading
  "Arcanist: I'll freeze the corridor" and deciding whether to let her, or to push the swarm onto the
  oil first. A full plan shown up front turns that into a button. Full plans belong behind an
  explicit "show me the whole idea" assistance step.
- **Every decision the scorecard counts must be visible in play.** `player_decision_points` counts
  forks in the plan space; a fork the player cannot see (because the companions have already
  committed) is the planner's, not the player's. Telegraphed companion intent is the cheapest way
  to make a fork visible; telegraphed enemy intent is the next.
- **Persistent terrain is the cheapest source of depth.** The gap between encounter and independent
  feasibility only exists when a fight consumes something the next fight wants. Prefer a reaction
  that rewrites the world over a new ability.
