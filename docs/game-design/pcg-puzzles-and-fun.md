# Planning-as-Gameplay + Planner-Driven NPCs — Research Findings & Next Steps

## Context

Bertrand wants to design a game where **building a good plan is the central mechanic**, and to drive
it with InductorHTN. The proposed model: game state is a **DAG of "fundamental states"** (root =
initial state, leaves toward the goal). By default *every edge is locked*; **player decisions unlock
edges**. The puzzle is to find a combination of decisions that opens a full root→goal path. InductorHTN
would be used (a) at design time to verify a level is solvable in multiple ways, and (b) in-game so
NPCs "know" the locked-in plan and act accordingly.

This file records a deep-research pass (web, multi-source, adversarially fact-checked) on prior art for
both halves — **design & fun** and **planner tech** — and a recommended concrete next step.

---

## Part A — Design & Fun (what makes plan-building fun, not tedious search)

### A1. Dormans' mission/space separation — the foundational pattern (your DAG, formalized)
Joris Dormans models an action-adventure level as **two separable graphs**: a *space* (geometric
room/connection graph) and a *mission* (a **directed dependency graph of tasks** where completing one
task unlocks the next), and the task ordering is **independent of geometry**. The same mission maps onto
many spaces; one space hosts many missions; a linear mission can live in nonlinear space and vice versa.
→ **Your "DAG of fundamental states" is exactly Dormans' mission graph.** This is the strongest
validation that your core structure is sound and well-trodden.
Source: Dormans 2010, "Adventures in Level Design" (PCG Workshop/FDG) — primary.

### A2. Lock-and-key as a generative grammar
Lock-and-key dependency structure can be written as a grammar over symbols (key/lock/room/monster/
treasure), e.g. `Obstacle -> key + Obstacle + lock + Obstacle`, producing solvable ordered sequences.
→ Your "edges unlocked by decisions" = locks opened by keys, where the *keys are player decisions*.
Caveat from the source itself: naive grammar output is "not all very good" — the mechanism guarantees
*solvability*, not *fun*. Same primary source (Dormans 2010).

### A3. Puzzle Dependency Diagrams — author the DAG backward from the goal
Noah Falstein's GDC 2013 "The Arcane Art of Puzzle Dependency Diagrams" formalizes designing puzzles
**from the end (goal) backward to the beginning** via dependency-only diagrams (Ron Gilbert's "Puzzle
Dependency Chart" is the related lineage). → This is the practical authoring discipline for your DAG.
NOTE: the claim that *Gilbert invented the PDD for Maniac Mansion* was **REFUTED 0-3** — credit the
PDD method/talk to Falstein. Source: GDC Vault #1017978 — primary.

### A4. The central failure mode + the fix (most important design finding)
**HITMAN (2016) failure mode:** IO Interactive's user research found the open combinatorial solution
space *too overwhelming* — "the learning curve was way too steep and the scale of the first level
(Paris) was incomprehensible," even though players had fun.
**The fix is scaffolding, NOT removing non-linearity:** IO layered a deliberate *linear guidance
system* + tutorial **on top of** the open sandbox, teaching players to "think and act like 47 without
changing the sandbox core."
→ This is the canonical warning for your idea: a "find the combination that unlocks a path" puzzle
degrades into brute-force enumeration unless you scaffold legibility on top of the combinatorial core.
Source: GDC Europe 2016, Andersen & Mikkelsen (IO Interactive) — primary.

### A5. Honest coverage gap (do not overclaim)
The brief named Deus Ex, Dishonored, Prey, Outer Wilds, Tunic, Animal Well, Into the Breach, Baba Is
You, and Zachtronics. **No primary-source claims about these survived verification.** Secondary sources
exist (immersive-sim overviews; a "metroidbrainia"/knowledge-gating feature; Baba Is You and Into the
Breach design talks; Zachtronics "Open-Ended Puzzle Design" GDC talk) and are worth reading directly,
but the specific "what makes the *planning* fun" conclusions for these titles are **not independently
substantiated** by this pass. The thing your design most depends on — *deduction-driven* unlocking
(Outer Wilds) rather than *enumeration* — is precisely the under-evidenced part. Treat it as the open
risk to prototype against, not a settled result.
Secondary/blog leads: thinkygames.com metroidbrainia feature; Zachtronics GDC #1025715; Into the Breach
GDC #1025772; Baba Is You (gamedeveloper.com); Emily Short "Emergent Puzzle Solutions" blog.

---

## Part B — Planner Tech (how shipped games use HTN/GOAP in NPCs)

### B1. F.E.A.R. — GOAP (the other family)
F.E.A.R. (2005, Jeff Orkin/Monolith) pioneered Goal-Oriented Action Planning: a 3-state FSM
(GoTo, Animate, UseSmartObject) + **A\* searching over actions**, with **real-time replanning** — when a
route is blocked the NPC re-derives a plan (kick door / dive through window / flank). Tactical-looking
behavior is **emergent from individual replanning**, not coordination ("none of the enemy AI in FEAR
know that each other exists"). GOAP = backward search, short plans (1–2 actions).
Sources: Orkin GDC 2006 "Three States and a Plan" (#1013282) — primary; gamedeveloper.com — secondary.

### B2. Guerrilla's HTN lineage — *architecturally almost identical to InductorHTN*
Guerrilla has shipped a custom **HTN planner** as the NPC decision tech since **Killzone 2**, through
Killzone 3, Horizon Zero Dawn and Forbidden West (Decima engine; HZD pairs HTN with utility selection
for lower-level choices). Key details that map onto this project:
- Plans are generated by recursively decomposing a root task ("behave"), **trying method branches in
  listed order** and **backtracking** over branches, precondition variable bindings, and compound-task
  instantiations until the **first all-primitive plan** is found — **"backtracking similar to Prolog."**
- Domains authored in **SHOP-style Lisp**: variables prefixed `?`, constants `@`, `call` for C++,
  primitive tasks `!`; an HTN compiler emits C++.
→ **This is the same family as InductorHTN** (SHOP model, Prolog-backed, first-solution DFS, `?`-prefix
variables per this repo's CLAUDE.md). Your engine is the AAA-validated architecture for the NPC half.
Sources: Guerrilla "HTN Planning in Decima" (primary); Game AI Pro Ch.29 "Hierarchical AI for
Multiplayer Bots in Killzone 3" (primary); GDC 2017 "AI of Horizon Zero Dawn."

### B3. Transformers: Fall of Cybertron — HTN replacing GOAP, and faster
High Moon shipped an HTN planner (2012) based on **total-order forward decomposition**, replacing the
GOAP system from War for Cybertron (2010). It was considerably faster because the task hierarchy **culls
large search-space sections** and it skips heuristic/cost sorting (no A\*/Dijkstra). Caveat: self-reported
postmortem, not a controlled benchmark. Source: Game AI Pro Ch.12 (Humphreys) — primary.

### B4. Plan-shape analytics
Across three shipped FPS titles, GOAP plans are short (1–2 actions, state-space search) while HTN plans
are longer (2–5; ~38% of Transformers plans length 3) because HTN bundles several actions. Caveat: only
three game sessions, hedged causal framing. Source: Jacopin, AIIDE 2014 (AAAI) — primary.

### B5. Planners as design-time solvability provers (your "verify a level" half)
- **Zook & Riedl, "Automatic Game Design via Mechanic Generation" (AAAI 2019):** an AI planner *proves*
  that designer-specified requirements ("reach end of level," "win without dying") are achievable —
  proving the presence/absence of valid play traces, i.e. solvability/unsolvability. Exactly your
  design-time use. (PCG research system, not a shipped in-NPC planner.)
- **"Point-and-Click: A Procedural Benchmark for 2D Adventure Puzzle Solving" (preprint):** generates
  puzzles by sampling **controllable DAGs** of dependencies over primitives (Key-Lock, Code-Lock,
  Pattern-Match), **enforcing acyclicity to guarantee solvability**; all interactions are derived from
  the DAG so every instance is solvable *by construction*; difficulty scales along explicit axes —
  **DAG size = number of steps, branching factor = linear chains vs parallel/merging sub-puzzles.**
  → This is your idea, built and validated as a generator. Caveat: unrefereed preprint, 3 primitives.

---

## Part C — The Fun Gap: deduce vs. enumerate (second research pass)

Targeted pass on the titles the first run couldn't substantiate. 25/25 claims verified, 0 killed.
The evidence converges hard: a planning puzzle is *reasoning* (fun) rather than *search* (tedium) when
the player can **evaluate a plan by inspecting a coherent, legible system before committing**, and
becomes enumeration when the only way to test a choice is to execute it and see. Concrete principles,
each tied to a primary/named source, with the translation to the DAG design:

### C1. Knowledge-as-key — put the lock in the player's head, not the game state
Outer Wilds (Alex Beachum): "It's all knowledge-gated. So if you know everything, you can just
boop-da-boop-da-boop." Nothing persists between loops *except what the player learned*. Tunic (Andrew
Shouldice): learning the systems *is* progression. → **The most satisfying version of your DAG is one
where the edge was always physically traversable and the "unlock" is the player *understanding* the
precondition** — not a flag the player toggles blindly. The planner verifies a path exists; the player's
job is comprehension. (Beachum interview; Tunic/gamedeveloper.com.)

### C2. Distribute preconditions, signpost open threads, pursue-by-question
Outer Wilds: each mystery has ~3 clues, deliberately *split* so "you'll never have two rules for one
Curiosity on the same planet"; the ship-log signposts unresolved threads so you chase questions, not
areas. → **Each locked edge's precondition should be discoverable from clues spread across the level,
and the UI must signpost which transitions are *close to* unlockable** — make the dependency web
legible. (Beachum interview; one sub-claim was 2-1, a precision nit on asterisk-vs-color.)

### C3. Derive from a clean system, not a combinatoric table
Blow & ten Bosch (The Witness): design by asking "if X happens, what are the consequences?" and express
the system's truths "in the cleanest possible way… *different from more-traditional combinatoric design
techniques*." → **Your edges' preconditions should follow from a small set of consistent world rules the
player can learn once and apply everywhere — not a per-edge lookup table of arbitrary requirements.**
That is the literal line between deduction and enumeration. (the-witness.net; gamedeveloper.com.)

### C4. Engineer the epiphany; simpler is stronger; ground it in something real
Blow: "The clearer and simpler the puzzle, the more beautiful and strong the epiphany"; meaningful when
"about something real and specific" not "an arbitrary set of moves." → **Resist combinatorial bloat in
the DAG. A level whose winning decision-set follows from one clean realization beats one that needs a
6-flag combination found by trying.** (gamedeveloper.com "Modeling Epiphany.")

### C5. Consistency is the substrate of reasoning
Blow (IndieCade 2011): "I will get rid of fun if it means I can get at something deeper or more
complete." Players can only deduce against rules they can trust. → **Preconditions must be deterministic
and consistent; if an edge sometimes opens and sometimes doesn't, players stop reasoning and start
flailing.** (gamedeveloper.com.)

### C6. Legible affordances let players FORM plans (immersive sims)
Arkane (Dishonored, GDC 2013): built on "consistent, coherent game systems… that enable the player to
improvise and experiment, devising their own solutions." Spector's "pull/attract" guidance over
prescribed solutions. → **The player must be able to *see* what each decision will enable or foreclose
*before* committing it.** This is the affordance-legibility requirement; it's the immersive-sim answer to
your "decisions unlock edges." (GDC #1018062; Spector via gamedeveloper.com.)

### C7. Open-ended, multi-solution, player-owned (directly serves your "multiple strategies" goal)
Zachtronics (Zach Barth, GDC 2019): "shipping puzzles… you haven't solved yourself, confident players
find creative solutions"; SpaceChem's open-endedness was "the biggest thing we did right." Histograms,
not leaderboards → self-imposed optimization goals; optimizing one metric worsens others (real
trade-offs). → **This is your explicit design goal ("multiple different strategies") validated. Don't
author N strategies; author a consistent system and let the planner confirm many decision-sets win, then
let players optimize among them.** (GDC #1025715; SpaceChem postmortem.)

### C8. Bound the inference space + add an anti-brute-force confirmation gate (the key mechanic)
Obra Dinn (Lucas Pope): deduction = filling a finite matrix (60 fixed identities); the **"rule of
three"** — fates lock only when *three correct ones are logged simultaneously* — is a deliberate
anti-trial-and-error device, "the right balance between educated guesses and just doing trial and
error." → **This is the concrete defense against the failure mode. If a player can lock in one edge and
immediately learn it was right, they will enumerate. Require committing a *whole plan* (decision-set)
before revealing success, so guessing doesn't pay incrementally.** (gamedeveloper.com.)

### C9. Guided discovery, not pure discovery
Tunic: a mysterious manual page "feels like mystery-solving" where a tutorial popup "ruins wonder";
self-made discoveries get "owned." Caveat the source itself flags: pure *unguided* discovery frustrates
novices (Kirschner, Sweller & Clark 2006) — this works only as *guided* discovery within curated
constraints. → **Teach the world's rules diegetically and scaffold early levels, or the legible system
still reads as moon-logic to a newcomer.** (gamedeveloper.com.)

### C10. Insight must be FAIR — the moon-logic line
Kim & Pajitnov (GDC 2000): "Good puzzles require insight… *Obscure* insights feel unfair." → **Every
precondition must have been *fairly discoverable* before the player needed it. An unlock that depends on
knowledge the player had no way to obtain is the cardinal sin — and a planner will happily generate
exactly such "valid" paths, so design-time solvability is necessary but NOT sufficient.** (Kim &
Pajitnov GDC 2000.)

### Fun-gap coverage notes
Substantiated by primary/strong sources: Outer Wilds, The Witness/Blow, SpaceChem/Zachtronics, Obra
Dinn, Tunic, Dishonored, Kim & Pajitnov. **NOT substantiated this pass** (named but no surviving
claims): Into the Breach (perfect-information/telegraphing), Baba Is You (rule-manipulation), Animal
Well, Lorelei and the Laser Eyes, deeper immersive-sim canon (Deus Ex/Prey/System Shock, Spector/Bare
"intentional vs emergent"), Bob Bates, Mark Brown/GMTK. The Into the Breach "perfect information makes
planning the whole game" thread is the most valuable remaining gap for your specific design.

## Synthesis — keep three uses separate

1. **Design-time solvability prover** ("is this level winnable, in N distinct ways?") — STRONGLY
   supported (Zook & Riedl; Point-and-Click DAG benchmark). InductorHTN is a natural fit; multi-path =
   enumerate multiple decompositions, not just the first.
2. **NPCs execute a locked-in plan** — STRONGLY supported; Guerrilla's shipped HTN is the same
   architecture as InductorHTN. Low conceptual risk.
3. **Making the *player's* planning fun** — NOT a solver output; it's an authored-design problem, now
   backed by a concrete principle set (Part C). The fun lives in *evaluating a plan against a legible,
   consistent system before committing*; the tedium lives in *only being able to test a choice by
   executing it*. Part C C1–C10 are the design constraints that move a level from the second to the
   first.

**Blind spot to confront:** the project's value is easy to assert for uses (1) and (2) and easy to
*assume* for (3). The planner can guarantee a path *exists*; it cannot guarantee the human finds choosing
it *satisfying* rather than a lock-picking grind — and worse (C10), **a solvability prover will happily
emit "valid" paths whose preconditions were never fairly discoverable by the player.** Design-time
solvability is necessary but NOT sufficient. The two non-negotiables the evidence forces:
- **Preconditions must be inspectable before commitment** (C3, C5, C6) — the player can read why an edge
  is locked and reason about which decisions open it, without executing.
- **Commit-the-whole-plan confirmation gate** (C8, Obra Dinn rule-of-three) — never confirm single edges
  incrementally, or the design collapses into enumeration regardless of how clean the system is.

---

## THE SPIKE — executable plan

Goal: the smallest InductorHTN artifact that (1) proves the **design-time solvability/multi-strategy**
use, and (2) operationalizes the **fun-gap checks** (C8 commit-whole-plan, C10 fair-deducibility) so the
planner can't silently mask an enumeration grind. Decisive go/no-go on the concept.

### Engine facts that shape the design (from codebase exploration)
- `indhtn_find_plans` / `HtnPlanner::FindAllPlans` (`src/FXPlatform/Htn/HtnPlanner.h:317`) returns **all**
  distinct plans with a `planCount` — native "solvable in N ways."
- **Multiple plain methods (NO `else`) → enumerated as distinct plans**; `else` collapses to one
  (`docs/reference/ruleset-writing.md`, "one method per genuinely different strategy"). So strategies = plain alternative methods.
- Unsolvable result = `{ "ok": false, "planCount": 0, "failureContext": [...] }` (the prover's "no").
- Acyclic graph ⇒ recursive traversal terminates and enumerates all simple paths (matches the
  Point-and-Click "enforce acyclicity for solvability" finding, B5). Keep the DAG acyclic.
- Fast loop = in-process MCP via `create_server()`/`call_tool_direct()`, mirroring
  `mcp-server/play_taxi_game.py`. Closest existing domain analog: `tests/fixtures/assembled/gamehack_multipath.htn`.

### Files to create (new `prototypes/decision-dag/` dir — keeps the spike out of shipped `Examples/`)
1. **`prototypes/decision-dag/level.htn`** — the level as data + thin traversal logic:
   - **DAG as data:** `edge(?from, ?to, ?unlock)` facts. `?unlock = none` for free edges, else a
     *capability* token (`electric`, `orcAlly`, `masterKey`). Acyclic, ~6–8 nodes.
   - **Decisions → capabilities:** `grants(?capability, ?clue)` — and a deliberately **unclued** edge
     (`masterKey`, no `clue`) to prove the C10 check catches moon-logic the prover would otherwise bless.
   - **Capabilities in state:** `have(?capability)` facts = the decision-set under test (set per run).
   - **Traversal (plain methods, no `else`, so all paths enumerate):**
     ```
     solve(?p) :- if(at(?p, start)), do(go(?p, goal)).
     go(?p, ?d) :- if(at(?p, ?d)), do().
     go(?p, ?d) :- if(at(?p, ?c), passable(?c, ?n)), do(opMove(?p, ?c, ?n), go(?p, ?d)).
     passable(?a, ?b) :- edge(?a, ?b, none).
     passable(?a, ?b) :- edge(?a, ?b, ?cap), have(?cap).
     opMove(?p, ?from, ?to) :- del(at(?p, ?from)), add(at(?p, ?to)).
     at(player, start).
     goals(solve(player)).
     ```
     (Method/operator forms verified against `Examples/TrunkThumper.htn:156-265`.)

2. **`prototypes/decision-dag/sweep.py`** — driver mirroring `mcp-server/play_taxi_game.py`. For each
   decision-set (subset of the capability tokens; n≤4 ⇒ ≤16 combos):
   - `reset_state` → `add_facts(["have(electric)", ...])` for that subset → `find_plans("solve(player).")`.
   - Record: solvable? (`ok`/`planCount`), **# distinct strategies** (`planCount`), and for each plan the
     **gated edges used** (parse `operators` → look up each traversed edge's `?unlock`).
   - **C10 check:** flag any winning plan that traverses a gated edge whose capability has **no `clue`**
     (unfair/moon-logic path) — the report must call these out, not hide them.
   - **C8 note:** the unit of confirmation is the *whole plan* (find_plans returns complete plans),
     which is the commit-whole-plan model; the report says success only at plan granularity.
   - Print a matrix: decision-set → {unsolvable | N strategies, clued? } .

3. **`prototypes/decision-dag/README.md`** — what it demonstrates, how to run, how to read the matrix,
   and how each column maps to a research principle (B5 prover, C7 multi-strategy, C8, C10).

### Reuse, don't reinvent
- Driver: `mcp-server/play_taxi_game.py` (in-process MCP pattern).
- MCP tools: `indhtn_create_session`, `indhtn_load_source` (dialect `htn_custom_vars`),
  `indhtn_add_facts`, `indhtn_remove_facts`, `indhtn_reset_state`, `indhtn_find_plans`,
  `indhtn_get_decomposition_tree`, `indhtn_preview_solution_facts`.
- Authoring patterns: `Examples/TrunkThumper.htn`, `Examples/Taxi.htn`,
  `tests/fixtures/assembled/gamehack_multipath.htn`; `docs/reference/ruleset-writing.md`.
- REPL for manual poking: `build/indhtn prototypes/decision-dag/level.htn` then `goals(solve(player)).`.

## Verification
The spike succeeds when the `sweep.py` report shows all of:
- **(a) Multi-strategy (C7):** at least one decision-set yields `planCount ≥ 2` distinct winning plans.
- **(b) Prover negative (B5):** the empty decision-set (and any insufficient set) returns
  `ok:false / planCount:0` — the level is correctly *unsolvable* without the right decisions; adding the
  enabling capability flips it to solvable.
- **(c) Fair-deducibility (C10) — the real test:** for every winning plan, the report lists the clues a
  player would chain for each gated edge used; and the deliberately **unclued `masterKey` path is flagged**
  as unfair. This proves design-time solvability is necessary-but-not-sufficient and that we can
  mechanically detect moon-logic paths.
- **(d) Commit-whole-plan (C8):** confirmation is reported only at whole-plan granularity, never
  per-edge.
Run: `source .venv/bin/activate && python prototypes/decision-dag/sweep.py`. Sanity-check one case by
hand in the REPL. (Build first if needed: `cmake --build ./build --config Release`.)

### Out of scope for the spike (note, don't build)
NPC plan-execution (use #2), the knowledge-gated-vs-commitment-gated design fork (decide before scaling),
Into-the-Breach perfect-information modeling, and any UI/legibility surfacing — the spike validates the
solver-side claims and the *mechanical* fairness check only.

---

## Full source list (verified-primary unless noted)
- Dormans 2010, "Adventures in Level Design" — pcgworkshop.com/archive/dormans2010adventures.pdf
- Falstein, GDC 2013 "Arcane Art of Puzzle Dependency Diagrams" — gdcvault.com #1017978
- IO Interactive, GDC Europe 2016 "Level Design in HITMAN" — gdcvault.com #1023849
- Orkin, GDC 2006 "Three States and a Plan" (F.E.A.R. GOAP) — gdcvault.com #1013282
- Guerrilla, "HTN Planning in Decima" — guerrilla-games.com/read/htn-planning-in-decima
- Game AI Pro Ch.29, "Hierarchical AI for Multiplayer Bots in Killzone 3" — gameaipro.com
- Game AI Pro Ch.12, "Exploring HTN Planners through Example" (Transformers FoC) — gameaipro.com
- Jacopin, AIIDE 2014 "Game AI Planning Analytics: Three FPS" — cdn.aaai.org/ojs/12728
- Zook & Riedl, AAAI 2019 "Automatic Game Design via Mechanic Generation" — arxiv.org/pdf/1908.01420
- "Point-and-Click: A Procedural Benchmark for 2D Adventure Puzzle Solving" — openreview.net (preprint)
- Secondary leads (Part A5): thinkygames.com metroidbrainia; Zachtronics GDC #1025715; Into the Breach
  GDC #1025772; Baba Is You (gamedeveloper.com); Emily Short "Emergent Puzzle Solutions" blog
- REFUTED (0-3): "Ron Gilbert invented the PDD for Maniac Mansion" — credit Falstein for the PDD method

Part C (fun gap) sources:
- Alex Beachum interview (Outer Wilds knowledge-gating) — medium.com/@cordialkobold
- Jonathan Blow & Marc ten Bosch, "Designing to Reveal the Nature of the Universe" — the-witness.net
- "The Witness: Modeling Epiphany" + "Inside Jonathan Blow's Puzzle Design Process" — gamedeveloper.com
- Arkane/Dishonored, GDC 2013 "Empowering the Player in a Permissive World" — gdcvault.com #1018062
- Zach Barth, GDC 2019 "Open-Ended Puzzle Design at Zachtronics" — gdcvault.com #1025715
- "Postmortem: Zachtronics Industries' SpaceChem" — gamedeveloper.com
- Lucas Pope (Return of the Obra Dinn, "rule of three") — gamedeveloper.com
- Andrew Shouldice (Tunic, diegetic/guided discovery) — gamedeveloper.com
- Scott Kim & Alexey Pajitnov, GDC 2000 "The Art of Puzzle Design" (fair-insight / moon-logic) — PDF
- Open (unsubstantiated this pass, worth a 3rd run): Into the Breach perfect-information/telegraphing;
  Baba Is You rule-manipulation; immersive-sim "intentional vs emergent" (Spector/Bare)
