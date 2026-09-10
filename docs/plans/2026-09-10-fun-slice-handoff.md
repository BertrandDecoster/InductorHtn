# Handoff: fun-metrics vertical slice (completed 2026-09-10)

Plan of record: `~/.claude/plans/review-the-uncommited-changes-jaunty-charm.md`
(approved; phases B -> A -> C). **All three phases are done and committed.**
Phase C landed: `htn_metrics/narrate.py`, `profile_level`, the player-perspective
`LevelSession` and its eight MCP tools, `mcp-server/launch.py` + a Windows-safe
`.mcp.json`, `play --solution/--class`, the non-gating scorecard in `verify`,
recursive component discovery, and the docs (`level-design-loop.md`, the
mcp-server rule, the core vocabulary, FUN_METRICS.md). Verification: 50 metrics/
session tests, 58 MCP tests, 31 component test suites, level re-certified, MCP
stdio handshake through `launch.py` exercising load -> forced act -> explain.
The sections below are kept as the record of how the slice was built.

## State right now

**Green:** `PYTHONPATH=src/Python python -m pytest tests/test_fun_metrics.py tests/test_fun_counterfactual.py tests/test_fun_agency.py tests/test_replay_sources.py tests/test_core_level.py` → 39 passed.

**Certified:** all eight core bundles (`components/core/primitives/{core_world,core_chemistry,core_attunement,core_aggro}`, `components/core/strategies/{the_burn,the_slipstream}`, `components/core/goals/defeat_group`, `levels/grease_trap`).

**RED on purpose (the next step's spec, they fail at import):**
`tests/test_narrate.py` (needs `src/Python/htn_metrics/narrate.py`) and
`mcp-server/tests/test_level_tools.py` (needs `mcp-server/indhtn_mcp/level_tools.py`).

**Environment:** `mcp 1.30.0` is installed in `.venv` (pinned `>=1.2,<2`; mcp 2.x
dropped the decorator API `server.py` uses). Earlier a stray `pip` put mcp 2.2.0
into miniconda's site-packages; harmless, but use `.venv/Scripts/python.exe -m pip`.

## Done

### Phase B – metrics (all of B1–B9, plus two fixes found while measuring)
- `counterfactual.py`: probes keyed by fingerprint (not label); tri-state
  `ProbeResult.status` (`solvable|unsolvable|unknown`) with the error kept;
  `world_hash` covers level + dependency sources + fingerprint config +
  `EXTRACTOR_VERSION`/`CACHE_VERSION`; sampling of ablation *and* loadout
  subsets is always reported; F4 evaluates the **encounter goal** with
  persistent state, keeps per-blocker probes as diagnostics, reports
  `loadout_feasibility_independent`, `shared_resource_loadouts`, and
  `strategy_classes_across_loadouts`; **shared gates**: a linchpin whose
  removal also kills a declared blocker goal is infrastructure, not a
  duplicate idea, and is excluded from independence.
- `metrics.py`: F1 reports OOM as OOM and softens to WARN when the lattice
  holds ≥2 ideas; F2 reads `sampled`/`conclusive`, gates are a note; F4
  "declared but not measured" message, thresholds from `metrics.json`, no
  "no dead choices" warning; F5 no red-herring minimum; **F6 rewritten**:
  actor convention (`actor_position`, `funActor/2`, `funNoop/1`),
  consequential player actions only, `passive_involvement`,
  `teamwork_edge_ratio`, `player_causal_out`, `player_decision_points`.
  Causal graphs computed once in `compute_all`.
- New modules: `agency.py` (ActorConvention), `trie.py` (PlanTrie:
  children/surviving/auto_advance_companions/player_decision_points).
- `canonical.py`: depth cap applies to the `levels` layer only; helpers
  inside the same component layer (looking through `try` nodes) are not
  ideas.
- `causal.py`: partially-bound conditions are matched as patterns (allOf
  nodes carry no bindings); `first`/`and` are transparent.
- `extract.py`: `EXTRACTOR_VERSION`, `split_args`, `replay_with_check`,
  missing operator template ⇒ `effects_resolved=False`.
- `loader.py`: `resolve_sources(roots)`; `load_level_htn` records the level
  source in `sources`.
- `cli.py`: `play --interactive` prints replay warnings; `fun` exit code 2
  only when unsolvable/truncated (scorecard is a diagnostic).
- `metrics.json`: `actor_position`, `severe_distance_factor`,
  `feasibility_saturated_at`, `feasibility_unsatisfiable_below`, no
  `red_herring_ratio_min`, F6 `teamwork_edge_ratio_min`,
  `player_decision_points_min`.
- Fixtures: `reference_good` is one coherent encounter (breach then route;
  default kit declared); `any_loadout_wins`/`one_to_one` have encounter
  goals + default kits + explicit blocker goals; new `shared_consumable`,
  `nominal_player`, `actor_override`.

### Phase A – ruleset
- Unified vocabulary implemented in `components/core/*` (see each `design.md`):
  regions/LoS/roles; chemistry as facts (`skillElement`, `reacts`, `blast`,
  `terrain`, `strike`, `mark`, `immune`); charges as tokens; signature/
  unlimited skills; `prime`/`detonate`/`finish`/`expose` with the player as
  the only detonator; `lure` (iron only, from range), `push` (flesh only),
  `taunt` (dash; player lands in the terrain too), `holdPosition` commitment.
- Level `levels/grease_trap` with declared choice space (pick 2 of 5).
  Latest scorecard: F1 PASS (burn + slipstream), F3 PASS (depth 3,
  interlock 0.86), F4 PASS (feasibility 0.4, nothing mandatory, `flare`
  dead, 3 near misses), F6 PASS (no soloable, 1 decision point, teamwork
  0.58, load 0.58), F2 WARN (distance 0.33 – both strategies share
  `bringTo` operator names), F5 WARN (decision breadth 1.73). Overall WARN,
  composite 0.85.
- Engine facts learned (recorded in component headers): no arithmetic in
  operators; every del/add variable must be in the head; a fact added twice
  is a planner error, so every `allOf`/status-adding method needs a
  `not(status(...))` guard and rules used inside `allOf` conditions must be
  single-clause (`exposed`, `vulnerable`).

## Phase C + docs (done; listed as built)

1. **`src/Python/htn_metrics/narrate.py`** – `narrate_operator(text, dels, adds, actor)`
   (core + gamehack op table, effects fallback), `narrate_intention(text, actor)`
   (first person, "Warden: I'll …"), `narrate_fact`. Spec: `tests/test_narrate.py`.
2. **`src/Python/htn_metrics/profile.py: profile_level(level, ablate, loadouts, progress)`**
   with `try/finally` around `harness.close()`; make `cli._fun_profile` call it.
3. **`mcp-server/indhtn_mcp/level_tools.py`** – `LevelSession(level, cfg=None,
   playthrough_dir=None)` with `observe()`, `actions()` (auto-advance companion
   steps by planner preference, then the player's own options, no strategy
   labels), `act(action, force=False)` (force ⇒ ground the operator's effects via
   `ground_solution`, rebuild the plan space with `extract_plan_space(level,
   facts=new_facts)`, rebuild the trie), `undo()`, `explain()` (reached class,
   missed classes, per-decision alternatives), `state()`, playthrough JSON to
   `.playthroughs/<level>/<ts>.json`; module function `fun_profile(level, ablate,
   loadouts)`. Spec: `mcp-server/tests/test_level_tools.py`. Builds on
   `PlanTrie`, `ActorConvention`, `replay_states`, `classify`.
4. **`server.py`**: register `indhtn_load_level`, `indhtn_observe`, `indhtn_actions`,
   `indhtn_act`, `indhtn_undo`, `indhtn_explain`, `indhtn_state`, `indhtn_fun`;
   replace the if/elif dispatch with a name→coroutine dict; do not raise when
   the exe is missing (lazy `SessionManager`); `main()` tries `indhtn.exe`;
   mark `indhtn_state_diff`/`indhtn_step` deprecated in descriptions.
5. **`mcp-server/launch.py`** (resolves `.venv/Scripts/python.exe` |
   `.venv/bin/python`, `build/Release/indhtn.exe` | `build/indhtn`, joins
   `PYTHONPATH` with `os.pathsep`, `--check`) and **`.mcp.json`** →
   `{"command": "python", "args": ["mcp-server/launch.py"]}`; bump
   `mcp-server/setup.py` and `requirements.txt` to `mcp>=1.2,<2`.
6. **CLI**: `play --solution N` / `--class LABEL`; narration via `narrate.py`
   (drop the fact whitelist); `verify` prints the scorecard, non-gating;
   `manifest.list_all_components` must walk `components/**` recursively (the
   `core/` and `gamehack/` trees are invisible to `status`/`test-all` today).
7. **Docs**: `.claude/rules/level-design-loop.md` (hypothesis → one rule change →
   certify → play via MCP → explain/fun → compare → human try); rewrite
   `.claude/rules/mcp-server.md`; add the core vocabulary + operator rules to
   `.claude/rules/component-system.md`; fix the `drive` example in
   `.claude/rules/htn-syntax.md`; `CLAUDE.md` certified list; update
   `docs/FUN_METRICS.md` (encounter feasibility, tri-state probes, gates,
   agency metrics, band changes, "composite is a diagnostic", Tactical Focus
   design recommendation); add `.playthroughs/` to `.gitignore`.
8. **Verify end to end** (plan's Verification section), then commit.

## Backlog (not in the slice)
Telegraphed enemy intent; cost model (`funCost/2`); companion inclinations;
migrate `components/gamehack/*` and `components/primitives|strategies|goals`
to the core vocabulary; `toy_two_step`; playthrough-derived metrics; C++
decomposition tree could record `conditionBindings` for allOf nodes (the
Python pattern-match workaround would then be unnecessary); F5 decision
breadth counts single-method primitives, which is by design and drags the
mean down.

## Corrections (2026-09-10, after the slice)

Two design laws from the user override parts of the record above:

1. **Companions are interchangeable.** The player character and the AI
   companions have the same abilities and differ only by who controls them.
   The slice had made the player the only detonator (role(?a, player) in
   core_attunement); that is gone. Cooperation is forced by task roles
   (primer and pay-off must be different companions), which anyone may fill.
   F6 now fails on single_actor_plans (one companion does everything) as
   well as on soloable_plans (the controlled companion is idle). Recorded in
   src/docs/GDD.md sections 2, 3.3 and 3.6.
2. **Rulesets are top-down.** Methods are named after the need they satisfy
   and bind actors, skills and regions at the leaves as the answer to how
   can I get X. The bottom-up applyToRegion(?a, ?el, ?r) shape was replaced.
   Recorded in .claude/rules/crafting-rulesets.md and component-system.md.
