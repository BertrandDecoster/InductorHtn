# Other Games — Team Coordination → HTN Patterns
A panorama of how great team-based games structure coordination, mined into reusable HTN beats.

This folder turns the recurring "beats" of team-based games into a vocabulary of HTN
method/operator patterns. The end goal: author rulesets where an **operator** is a straightforward
game action (e.g. "aggro a mob to a location") that a low-level controller (FSM / behavior tree /
Deep RL policy) plays out, and a **method** decides *which* operators to chain and *when*.

The repo is already partway there — `components/primitives/aggro` and `locomotion`, the
`Examples/GameHack7Combined.htn` multi-ally combos, and the `parallel()` keyword. This study widens
that vocabulary with patterns drawn from real strategy guides — and the approach is validated by
primary sources showing shipped games (Killzone 3, Decima) build squad AI this exact way.

## Start here

- **[`team-patterns-catalog.md`](team-patterns-catalog.md)** — the primary deliverable. Eleven
  recurring team-coordination problems, each with cited guide tactics and an HTN sketch.
- **[`games/`](games/)** — per-game evidence appendices: which patterns each game exemplifies, with
  source citations and caveats.

## The 11 coordination problems

The catalog is organized by *problem*, not by game, so patterns are reusable across domains:

| # | Problem | Best-supported by |
|---|---------|-------------------|
| 1 | [Role / responsibility assignment](team-patterns-catalog.md#problem-1--role--responsibility-assignment) | WoW, Deep Rock, Overcooked, Helldivers 2 |
| 2 | [Threat & aggro management](team-patterns-catalog.md#problem-2--threat--aggro-management) | WoW |
| 3 | [Focus fire / target prioritization](team-patterns-catalog.md#problem-3--focus-fire--target-prioritization) | WoW, Left 4 Dead |
| 4 | [Positioning & formation](team-patterns-catalog.md#problem-4--positioning--formation) | WoW, Left 4 Dead, Helldivers 2, Deep Rock |
| 5 | [Timing & synchronization](team-patterns-catalog.md#problem-5--timing--synchronization) | WoW, Monster Hunter |
| 6 | [Crowd-control chaining & CC economy](team-patterns-catalog.md#problem-6--crowd-control-chaining--cc-economy) | Monster Hunter, Helldivers 2, Deep Rock |
| 7 | [Resource / cooldown economy](team-patterns-catalog.md#problem-7--resource--cooldown-economy) | Helldivers 2, Deep Rock, WoW |
| 8 | [Throughput / task pipelining](team-patterns-catalog.md#problem-8--throughput--task-pipelining) | Overcooked, Deep Rock |
| 9 | [Phase / state transitions](team-patterns-catalog.md#problem-9--phase--state-transitions-medium-confidence) *(medium)* | WoW |
| 10 | [Recovery & failure handling](team-patterns-catalog.md#problem-10--recovery--failure-handling) | Left 4 Dead, Deep Rock, Helldivers 2 |
| 11 | [Safety constraints](team-patterns-catalog.md#problem-11--safety-constraints) | WoW, Left 4 Dead, Helldivers 2, Deep Rock |

## Fit for *The Companions*

This catalog is the **supplier**; the game in [`../game-design/GDD.md`](../game-design/GDD.md) — *The
Companions* — is the **consumer**. The patterns here were mined from 4–20-player games with fungible
roles and shared economies, so only the ones that survive a **3-agent, single-hero, no-shared-economy**
team transfer directly. The rest are breadth and validation, not direct fuel.

The catalog's core assumption — *an operator is one discrete game action; a method chains which and
when* — matches the game as designed. The GDD's engine is a **discrete grid**: RL emits tile-step
actions, Unreal interpolates the visuals, and the coordinator runs either real-time-polled or
turn-locked. The tile/turn math in the `game-design/` level drafts is that operator altitude, not a
contradiction to resolve.

| Fit | Pattern | Why |
|-----|---------|-----|
| **Core** | 5 Timing / sync · 6 CC chaining | The Attunement System (Primer → Catalyst → Detonator) *is* these, verbatim |
| **High** | 4 Positioning / area control | Marauder swarms are AoE-vulnerable; grid AoE templates + herding/zoning |
| **High** | 9 Phase transitions | GDD multi-phase bosses with explicit vulnerability windows |
| **Medium** | 10 Recovery / revive | Companions go down; protect-then-revive applies |
| **Medium** | 11 Safety constraints | Includes the GDD's "plans must need the human" rule |
| **Medium** | 2 Threat / aggro | Warden-as-anchor + the `aggro` primitive exist; no dedicated tank loop |
| **Medium** | 7 Cooldown economy | Only the **cooldown-sequencing** half — there is no shared ammo/ticket pool |
| **Low** | 3 Focus fire | Small enemy counts; kill-order matters little |
| **Low** | 1 Role assignment | 3 fixed agents — there is no assignment problem |
| **None** | 8 Throughput pipelining | Not a production game |

**Direct fuel:** patterns 4, 5, 6, 9. **Validation / breadth:** the rest (the
Helldivers / Overcooked / raid-economy material).

Highest-ROI next step: author the Core/High patterns as reusable `../../components/` and compose the
`../../levels/` rulesets from them. `../../components/strategies/the_burn` (lure-to-oil + ignite) is a
first sketch of the oil+fire combo — it shares the elemental idea but not yet the
Primer/Catalyst/Detonator role structure or companion-casting, so it's a starting point, not the
finished Attunement pattern.

## Game appendices

| Game | Coverage | Notes |
|------|----------|-------|
| [WoW raids](games/wow-raids.md) | **Strong** | Threshold-driven swaps, focus-fire, soaks, dispel economy |
| [Monster Hunter](games/monster-hunter.md) | **Strong** | Status buildup thresholds, trap windows, capture combo |
| [Left 4 Dead 2](games/left-4-dead.md) | **Strong** | Pin-and-rescue, pounce priority, formation, hazard steering |
| [Overcooked 2](games/overcooked.md) | **Strong** | Role/zone assignment, parallel prep, dedicated long-task owner |
| [Helldivers 2](games/helldivers-2.md) | **Good** | Reinforcement economy, sentry crossfire/CC-layering, four-role split |
| [Deep Rock Galactic](games/deep-rock-galactic.md) | **Good** | Resupply economy, traversal synergies, defend-while-task, safe revives |
| [Coverage gaps](games/coverage-gaps.md) | — | Dota 2 / LoL, Overwatch, FFXIV: requested but still unverified |

## Methodology & honesty note

These docs were produced by **two deep-research passes** that fanned out parallel web searches,
fetched dozens of sources, and **adversarially verified** every candidate claim (3-vote majority
needed to confirm). Pass 1 covered WoW / Monster Hunter / L4D2 / Overcooked (23/25 confirmed); a
targeted pass 2 recovered Helldivers 2 and Deep Rock (21/25 confirmed). Every prescribed tactic
traces to a cited guide rather than model recall.

**Refuted claims are flagged, not hidden** — including a DRG handoff that pass 2 reclassified from a
hard dependency to an optional safety assist, plus Monster Hunter "sleep bombing", a Helldivers
cooldown misclaim, and a DRG L.U.R.E. tactic. Numeric thresholds (stack counts, ticket pools, trap
durations) are **tunable domain parameters**, not constants, and some are patch-sensitive.

Still uncovered: Dota 2 / League of Legends, Overwatch, and FFXIV. See
[`games/coverage-gaps.md`](games/coverage-gaps.md) for what remains.

## Companion references
- [`../reference/ruleset-writing.md`](../reference/ruleset-writing.md) — growing a ruleset from a domain
- [`../reference/ruleset-htn-syntax.md`](../reference/ruleset-htn-syntax.md) — method/operator/modifier syntax
- [`../upgrades/ruleset-keywords.md`](../upgrades/ruleset-keywords.md) — the `parallel()` keyword
- `../../components/` — `aggro`, `locomotion`, `tags` primitives the sketches reuse
- `../../Examples/GameHack7Combined.htn` — multi-ally combos and aggro herding
