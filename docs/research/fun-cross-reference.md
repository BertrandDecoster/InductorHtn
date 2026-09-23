# Fun rulesets: cross-reference of design theory, planning literature and generation workflows

*Research note, 2026-09-23.* This note checks the fun-metrics work (`docs/FUN_METRICS.md`) and the level design loop (`docs/reference/level-design-loop.md`) against three bodies of work:

1. game-design writing on what makes mechanics fun;
2. HTN and planning research, especially metrics for plan *sets*;
3. published workflows that generate game content iteratively and score it as they go.

The note records what the literature confirms, what it adds, and what was built as a result (§5).

Sources are linked inline. A few could only be read as abstracts or search snippets; those are marked *(abstract only)* or *(unverified)*. Treat their details as leads, not facts.

---

## 1. The one-paragraph answer

The repo's central bet is to score the *shape of the enumerated solution space*, not to guess at fun. That bet is what the planning and PCG literature supports.

- **What predicts human difficulty.** The best-validated difficulty measures model how a *human* searches, not how much work the solver does. Pelánek's Sudoku model reaches r = .95 against human solve times; raw backtracking count reaches only .25. Chen, White & Sturtevant's solution-information entropy reproduces The Witness's puzzle order.
- **What enumeration gives for free.** The strongest cheap checks are *for-all* checks over every solution:
  - Smith et al.'s "no solution avoids the intended concept";
  - landmarks;
  - padded-variant detection.

  An enumerating HTN planner answers these exactly, where sampling generators can only estimate them.
- **How to run the loop.** The workflow literature (search-based PCG, quality-diversity, Eureka, ChatHTN) agrees on three rules:
  1. hard symbolic gates reject a candidate outright;
  2. the soft metrics are given to the agent as a per-component breakdown, never one scalar to climb;
  3. some metrics are held back from the agent, so that gaming the visible ones shows up.

No paper was found that validates any metric as a measure of *fun in cooperative puzzles*. That calibration is this project's to do (§4.5).

---

## 2. Fun mechanics: what design theory says, and what can be measured

| Source | Claim | Operationalised as | Status here |
|---|---|---|---|
| Koster, *A Theory of Fun* ([summary](https://game-studies.fandom.com/wiki/A_Theory_of_Fun_for_Game_Design)) | Fun is learning a pattern; boredom is mastery | Novelty of operator/method combinations compared with earlier levels | backlog: campaign metric |
| MDA, Hunicke/LeBlanc/Zubek ([paper](https://users.cs.northwestern.edu/~hunicke/MDA.pdf)) | Fun splits into aesthetics: Challenge, Discovery, Fellowship, Expression… | Challenge → F5 information; Discovery → F3/F5; Fellowship → F6; Expression → F1/F2 | the family split mirrors MDA |
| Flow, Csikszentmihalyi via [Jenova Chen](https://www.jenovachen.com/flowingames/Flow_in_games_final.pdf) | Challenge tracks skill | Difficulty rises in small steps across a level sequence | backlog: campaign metric |
| Sid Meier, "interesting decisions" ([GDC 2012](https://www.gamedeveloper.com/design/gdc-2012-sid-meier-on-how-to-see-games-as-sets-of-interesting-decisions)) | No option dominates, and picking at random does not work | F4 dead/mandatory picks and win-rate band; F6 player decision points | **have** |
| Mark Brown, GMTK "the catch" ([discussion](https://www.resetera.com/threads/what-makes-a-good-puzzle-game-makers-toolkit.29537/)) | Obvious *what*, hidden *how*; a tempting wrong path | Greedy or short prefixes that cannot complete | backlog: needs planner failure data |
| *Stephen's Sausage Roll* / "no filler" (folklore; [context](https://en.wikipedia.org/wiki/Stephen's_Sausage_Roll)) | Every element is essential | Landmarks plus red-herring ratio | F5 red herrings (have); landmarks (**added**) |
| *Breath of the Wild*, multiplicative gameplay ([GDC17](https://www.engadget.com/2017-03-12-breath-of-the-wild-gdc-talk.html)) | Objects react to each other, not only to the player | Share of causal links carried by world facts rather than actor facts | **added** (`world_chain_ratio`) |
| Immersive sims ([overview](https://en.wikipedia.org/wiki/Immersive_sim)) | Several consistent-systems ways past each obstacle | Strategy classes; per-blocker answers | F1, F4 (have) |
| Juul, *The Open and the Closed* ([text](https://jesperjuul.net/text/openandtheclosed.html)); *The Art of Failure* | Emergence versus progression; failing and recovering is part of the fun | Plans the author did not intend; recovery after a mistake | intent gate (**added**); recovery is a playthrough-derived backlog item |
| Anthropy & Clark, *A Game Design Vocabulary* ([review](https://lizengland.com/blog/review-a-game-design-vocabulary-by-anna-anthropy-and-naomi-clark/)) | Verbs and resistance | Distinct operator names; blockers | F2, F4 (have) |
| Portal 2 co-op ([wiki](https://theportalwiki.com/wiki/Cooperative_Testing_Initiative)) *(the testing anecdote is unverified)* | A chamber solved by one player's portals goes back to the designers | "No plan is carried by one companion" | F6 `single_actor_plans` (have) |
| *It Takes Two* ([GameSpot](https://www.gamespot.com/articles/josef-fares-it-takes-two-is-co-op-because-i-like-to-f-k-with-the-players-minds/1100-6488262/)) | Complementary abilities that must be combined | Teamwork edges between different actors | F6 `teamwork_edge_ratio` (have) |
| Pandemic quarterbacking ([Meeple Mountain](https://www.meeplemountain.com/articles/benching-the-quarterback-how-to-deal-with-alpha-players-in-co-op-games/)) | With full information, one player directs everyone | The human is always the quarterback of NPCs | see tension below |

**Tension with the repo's own rules.** The anti-quarterback literature prescribes *different abilities* per companion. This repo's rule is that companions are interchangeable in ability, and cooperation comes from *task roles* (`docs/reference/component-system.md`). The two can be reconciled by measuring non-substitutability of *roles* in a plan, which F6's teamwork edges already approximate. Swapping one companion's abilities for another's is not a test this project should adopt.

---

## 3. Computational metrics: puzzle quality and plan sets

### 3.1 Human-validated puzzle difficulty

| Work | Metric | Evidence | Maps to enumerated HTN plans as |
|---|---|---|---|
| Pelánek, Sudoku ([arXiv 1403.7373](https://arxiv.org/html/1403.7373v1)) | Per-step refutation difficulty combined with the dependency structure between steps | r = .95 against human solve times (backtracking: .25) | Alternatives a player must rule out at each decision, weighted by causal depth: F5 solution information plus F3 causal DAG |
| Jarušek & Pelánek, Sokoban ([PDF](https://www.fi.muni.cz/~xpelanek/publications/stairs2010-final.pdf)) *(abstract only)* | Problem decomposition; a model of human state-space traversal | About 2,000 puzzles, 785 hours of play; global state-space size predicted poorly | Independent subgoal chunks in the method tree (F3 decomposition) |
| Chen, White & Sturtevant, entropy ([AIIDE 2023](https://ojs.aaai.org/index.php/AIIDE/article/view/27499)) | Bits needed to tell a policy of given skill how to solve | Reproduced The Witness's ordering; correlated with ratings | **F5 `solution_information_bits`** (added, §5.2) |
| Shen & Sturtevant, MSI/TSI ([AIIDE 2024](https://ojs.aaai.org/index.php/AIIDE/article/view/31872)) | Minimum and total solution information under a policy | Extends the above | **F5 `easiest_plan_bits`** (MSI analogue, added) |
| Kartal, Sohre & Guy, Sokoban MCTS ([AIIDE 2016](https://ojs.aaai.org/index.php/AIIDE/article/view/12859)) *(abstract only)* | Congestion between boxes and goals | User study | Positional; out of scope while operators carry no geometry |
| Browne & Maire, Ludi ([thesis](https://eprints.qut.edu.au/17025/)) | Drama, uncertainty, completion (57 criteria in all) | Tracked human preference best among the criteria | Needs adversarial state; backlog |
| Isaksen et al., Flappy Bird ([FDG 2015](http://www.nealen.net/papers/exploring-game-space-FDG2015.pdf)) *(abstract only)* | Survival under simulated motor-skill noise | More than 10⁶ real sessions | A noisy policy over method choice (leniency); backlog |
| Holmgård et al., procedural personas ([NYU](https://game.engineering.nyu.edu/procedural-personas/)) | Agents with different utilities stand in for playtesters | Qualitative | Re-rank plans under persona utilities; backlog |
| Khalifa & Fayek, PuzzleScript ([Semantic Scholar](https://www.semanticscholar.org/paper/Automatic-Puzzle-Level-Generation:-A-General-using-Khalifa-Fayek/2370825a394496cd8bc2e4f2951539503a4d3906)) | Playability, solution length and solver effort | Correlated with player preference | F3 length band (have) |

The main lesson for F5: **solver effort is a poor proxy for difficulty.** The existing `search_cost`, `planner_dead_ends` and `planner_nodes_explored` are rightly left unbanded. What should be banded is a model of the *player's* search. §5.2 builds one.

### 3.2 For-all checks over solutions: where enumeration pays off

- **Smith, Butler & Popović, "Quantifying over Play"** ([FDG 2013, Refraction](https://adamsmith.as/papers/fdg2013_shortcuts.pdf)). Their result: puzzle quality depends mostly on the *absence of unwanted solutions*. Their answer-set-programming (ASP) generator constrains the whole space: "no solution avoids concept X". An enumerating planner gets this check exactly and cheaply. It is the strongest addition in this note: **F7 intent gate** (§5.1).
- **Landmarks** (Hoffmann, Porteous & Sebastia, [JAIR 2004](https://jair.org/index.php/jair/article/view/10390)). A landmark is a fact true at some point in every plan. Over an enumerated set it is an intersection. Landmarks are the level's bottleneck or "aha" facts. A high landmark ratio means the routes share most of their causal work. **Added to F2.**

### 3.3 Diversity metrics for plan sets (planning literature)

| Metric | Source | Applies to plan set Π as | Status |
|---|---|---|---|
| Top-k / top-quality / diverse planning | Katz & Sohrabi ([top-quality](https://cdn.aaai.org/ojs/6544/6544-13-9769-1-10-20200519.pdf)) | Count within a cost bound; the number of optimal plans versus all plans | F1 counts (have); cost model is backlog (`funCost/2`) |
| Action / state / causal-link distances | Nguyen et al. ([AIJ 2012](https://rakaposhi.eas.asu.edu/diverse-aij-final.pdf)) | Jaccard over action, state and causal-link sets | F2 action+mechanism Jaccard (have) |
| Qualitative distance | Coman & Muñoz-Avila ([AAAI 2011](https://ojs.aaai.org/index.php/AAAI/article/view/8006)) | Distance over domain-meaningful features: here, method choices | F1 fingerprint (have) |
| **Uniqueness** | Diverse-planning metrics ([arXiv 2310.01520](https://arxiv.org/html/2310.01520)) | Fraction of plans whose action multiset is not a strict superset of another's | **added to F1** (`plan_uniqueness`, `padded_classes`) |
| Subgoal-ordering distance | same | Hamming distance between subgoal sequences | backlog |
| Behaviour-space grid | Behaviour Planning ([arXiv 2405.04300](https://arxiv.org/abs/2405.04300)) | Plans or levels projected onto designer features; count occupied cells | **added** as `fun-all --range` (§5.3) |

Uniqueness matters because of Goodhart's law. An LLM agent told to raise multiplicity can add a detour method, producing "plan A plus one pointless step". Raw counts and even fingerprints can reward that. Superset detection does not.

---

## 4. Iterative generation workflows

### 4.1 Survey

| Workflow | Loop | What drives selection | Where humans enter | Failure mode |
|---|---|---|---|---|
| Search-based PCG ([Togelius et al. 2011](https://www.semanticscholar.org/paper/3288d7575f451d2e95f57cefc9566691ff272f1c)) | generate → evaluate → select → mutate | Direct, simulation-based or interactive fitness | Writing the fitness | Proxy optimisation; collapse onto one style |
| Quality-diversity: MAP-Elites, novelty search ([Gravina et al. 2019](https://par.nsf.gov/biblio/10132574-procedural-content-generation-through-quality-diversity)) | Archive cells over behaviour descriptors; keep the best per cell | Quality within a cell, coverage across cells | Choosing descriptors | Trivial variants filling cells |
| ASP constrained generation ([Smith & Mateas](https://ieeexplore.ieee.org/document/5783900/)) | Declare the space plus constraints; the solver enumerates | Hard constraints, including universally quantified ones | Writing constraints | Loopholes nobody forbade |
| Mixed-initiative: [Tanagra](https://dl.acm.org/doi/pdf/10.1145/1822348.1822376), [Sentient Sketchbook](http://julian.togelius.com/Liapis2013Sentient.pdf) *(abstract only)* | Designer edits; the tool guarantees playability and suggests | Playability and balance feedback | Continuous co-authoring | Suggestions drift from intent |
| Expressive range analysis: [Smith & Whitehead 2010](https://users.soe.ucsc.edu/~ejw/papers/smith-pcg-2010.pdf), [Danesh](https://qmro.qmul.ac.uk/xmlui/bitstream/handle/123456789/73222/Cook%20Danesh%20Interactive%20Tools%202021%20Accepted.pdf?sequence=2) | Sample widely; 2-D histograms of metrics; adjust | The *distribution*, not single artifacts | Reading plots, choosing axes | Correlated or meaningless axes ([metric selection](https://arxiv.org/pdf/2304.02366)) |
| LLM + evolution: [GAVEL](https://arxiv.org/abs/2407.09388), [MarioGPT](https://arxiv.org/pdf/2302.05981), [Word2World](https://arxiv.org/pdf/2405.06686) | LLM as mutator or generator; evaluator filters | QD archive (GAVEL), novelty (MarioGPT) | Prompts, curation | About 12% of MarioGPT output unplayable; drift toward typical content |
| [Eureka](https://arxiv.org/abs/2310.12931) (reward design, by analogy) | Sample N candidates, evaluate, summarise per-component statistics as text, mutate | Fitness plus textual "reflection" | Optional feedback | Reward hacking; removing reflection cost about 29% |
| [ChatHTN](https://arxiv.org/abs/2505.11814) (2025) and follow-up ([2511.12901](https://arxiv.org/abs/2511.12901)) | LLM proposes decompositions; the symbolic planner verifies; methods are learned from them | Soundness through symbolic checking | None | LLM-proposed methods are unsound without the check |
| Guan et al., LLM-built PDDL ([NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/hash/f9f54762cbb4fe4dbffdd4f792c31221-Abstract-Conference.html)) | LLM drafts the model; planner and human feedback correct it | Validation errors | Correction | Subtle model bugs |
| Automated playtesting, [procedural personas](https://arxiv.org/abs/1802.06881) | Agents with different utilities play | Differences between persona traces | Defining personas | Agents are not people |

HTN in shipped games (Humphreys, [Game AI Pro ch. 12](https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter12_Exploring_HTN_Planners_through_Example.pdf); Guerrilla, [HTN in Decima](https://www.guerrilla-games.com/read/htn-planning-in-decima) *(abstract only)*) confirms the component-library shape: domains are hand-authored, reusable and readable. Narrative planning (Riedl & Young, [IPOCL](https://faculty.cc.gatech.edu/~riedl/pubs/jair.pdf); Porteous & Cavazza, [trajectory constraints](https://link.springer.com/chapter/10.1007/978-3-642-10643-9_28)) adds a principle this project already follows: **an optimal plan is not a good experience, so steer with constraints on the whole trajectory.** `funIntended` is such a constraint.

### 4.2 How the current loop compares

| Principle from the literature | Current loop | Change |
|---|---|---|
| LLM proposes, symbolic certifies (ChatHTN, Guan) | certify, then verify, then MCP play | none; this is the right shape |
| Hard gates are separate from soft signals | certify gates; fun never gates | added hard *level-author* gates: F7 intent and `funExpect` regressions (§5) |
| Per-component reflection, not a scalar (Eureka) | families with findings; composite marked "least trustworthy" | none; keep feeding findings to the agent, not `fun_score` |
| One change per iteration as attribution | "one rule change" rule; `--ablate` | none |
| Regression suite over shared content | per-component tests; none at level-shape level | added `funExpect` facts checked by `verify` |
| Held-out evaluation to catch gaming | human playtest as the last step only | added a rating log plus rating-vs-metric correlation (`fun-rate`, `fun-calibrate`) |
| Expressive range / QD to catch mode collapse | `fun-all` verdict table | added `fun-all --range X Y` |

### 4.3 Recommended workflow (what `level-design-loop.md` now says)

1. **Hypothesis.** Write it with numbers, and encode the numbers as `funExpect` facts. The hypothesis then becomes a regression test that outlives the iteration.
2. **Declare intent.** Name the mechanic the level is *about* as `funIntended` facts, and anything that must never win as `funForbidden`. This is Smith et al.'s "quantifying over play" in the level's own words.
3. **One rule change.** Cheapest first, unchanged.
4. **Certify and verify.** Lint, tests and solvability, plus the two new gates. A gate failure rejects the change; it is not weighed against score.
5. **Play as the player** through MCP, unchanged.
6. **Read the families, not the score.** Pay particular attention to movement in `solution_information_bits`, `plan_uniqueness` and landmarks. A rise in plan count with a fall in uniqueness is padding.
7. **A human plays it and records a rating** with `fun-rate`. The rating is never shown to the agent during iteration; `fun-calibrate` compares ratings with metrics once enough are in.
8. **Across levels,** `fun-all --range solution_information_bits teamwork_edge_ratio` shows whether the levels cover the design space or cluster in one corner.

### 4.4 Pitfalls to design against

- **Goodhart and specification gaming** ([DeepMind](https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/)). Any number the agent sees gets optimised literally. The defences here:
  - gates are binary;
  - uniqueness counters padding;
  - the composite is never a gate;
  - human ratings are held out.
- **Mode collapse.** LLM mutators drift toward typical content. The expressive-range view makes that visible across levels.
- **Truncation bias.** Every plan-set metric is biased when Π is truncated. The composite is already withheld in that case, and the new metrics inherit that.
- **Structural metrics cannot say *why* two plans differ** (arXiv 2310.01520). Keep the playthrough and `explain` steps; they are the "why".

### 4.5 What remains unvalidated

None of the plan-set metrics above has been validated against human fun ratings for cooperative puzzles. Sturtevant's entropy is the closest, but it measures difficulty in single-player line puzzles. The rating log (§5.4) exists so the bands in `metrics.json` can eventually be fitted to data instead of intuition.

---

## 5. What was built from this note

### 5.1 F7 Intent: a hard gate (Smith et al. 2013)

**Declarations** (all optional; with none, the family is `skip`):

```prolog
funIntended(combo, opElectrocute).   % group `combo`: every plan uses one of its members
funIntended(combo, opIgnite).        % ... here, either operator satisfies the group
funIntended(opClear).                % a one-member group, named after its member
funForbidden(opBribe).               % no plan may use this
```

**Matching.** A member matches a plan when some operator in the plan has that *name*, or when the member is a component (mechanism) the plan uses.

**Verdicts.**
- It fails when any plan misses a group; the report names those shortcut plans.
- It fails when any plan uses a forbidden member.
- It never contributes to the composite (weight 0). A shortcut is a defect, not a low grade.
- `fun` exits 2 on an F7 fail, the same as on F1.

### 5.2 F5 solution information (Chen/White/Sturtevant; Shen & Sturtevant)

**The model.** The player follows a *uniform policy over method alternatives*. At every task decomposed on the way to a solution, they pick uniformly among the rules that define that task, successful or not.
- `k` is the static alternative count, the same one `decision_breadth` uses. It is Pelánek's "alternatives to refute".
- Plans are merged into a decision trie keyed by (task node, method), so two plans share a decision exactly when the planner shared it.

**Metrics.**
- `solution_information_bits` = −log₂ P(the uniform policy completes *some* solution).
- `easiest_plan_bits` = min over plans of Σ log₂ k along that plan's decisions. This is the MSI analogue: the fewest bits needed to specify one solution.
- `solution_information_per_class` = the minimum bits within each strategy class.
- Banded: WARN below `solution_information_bits_min` (default 1.0), meaning the uniform policy solves the level more than half the time, so there is nothing to find. There is no upper band until human ratings exist.

**Blind spots.**
- Operator-level choices the player makes without a method alternative (which companion, which binding) are invisible to it.
- A uniform policy is a novice. A skilled player prunes impossible methods at a glance, so the bits over-state difficulty wherever `if()` conditions are obviously false.

### 5.3 Plan-set structure metrics

- **F1 `plan_uniqueness`.** Fraction of plans whose ground-operator multiset does not strictly contain another plan's. WARN below `plan_uniqueness_min` (0.5). Computed exactly up to 1500 distinct multisets, then on a prefix sample, marked `plan_uniqueness_sampled`.
- **F1 `padded_classes`.** A strategy class whose representative's operator-name multiset strictly contains another class's representative. That is the other class plus a garnish. WARN when there are any.
- **F2 `landmark_facts`, `landmark_operators`, `landmark_ratio`.** Facts every plan adds, operator names every plan uses, and landmark facts as a share of the mean facts achieved per plan. Reported, unbanded.
- **F3 `world_chain_ratio`.** Share of causal edges whose linking fact names no actor (BotW's "the world does the work"). Reported, unbanded.

### 5.4 Workflow tools

- **`funExpect(metric, op, value)` and `funExpect(family, metric, op, value)`** in `level.htn`.
  - `op` is one of `atLeast`, `atMost`, `equals`.
  - Nested metrics are addressed flattened with `_`: `plan_length_median`, `causal_depth_best_class`.
  - `metric = verdict` compares a family's verdict: `funExpect(f6_player, verdict, pass)`.
  - `verify` checks every expectation and fails the level on any miss. `fun` prints them.
- **`fun-all --range X Y [--bins N]`.** An expressive-range grid of levels over two flattened metrics.
- **`fun-rate <level> --rating 1..5 [--rater R] [--note T]`.** Appends a human rating plus the level's flattened metrics and source hash to `levels/fun_ratings.jsonl`.
- **`fun-calibrate`.** Spearman rank correlation between ratings and every numeric metric, for the calibration step in §4.5. It needs at least 5 ratings before it reports anything.

### 5.5 Backlog, ranked by evidence × computability

1. **The catch.** Tempting prefixes that dead-end, from method-failure tracking (`docs/upgrades/method-failure-tracking.md`).
2. **Campaign metrics.** Novelty against earlier levels (Koster), and the difficulty step between consecutive levels in `solution_information_bits` (flow).
3. **Leniency.** Success rate of a noisy method policy (Isaksen), on the existing counterfactual harness.
4. **Persona spread.** Whether the preferred plan changes under persona utilities (Holmgård); needs `funCost/2`.
5. **Subgoal-ordering distance** between classes.
6. **Drama and uncertainty** (Browne), once enemies act (`intends/3`).
