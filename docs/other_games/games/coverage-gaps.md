# Coverage gaps & open questions
What was requested but not verifiable, and where a future research pass should dig.

This study deliberately reports only adversarially-verified, guide-cited tactics. After **two
research passes**, three of the originally-requested games still produced no confirmed tactics, and
one pattern rests on thin single-game evidence. This file records those gaps honestly so the catalog
is not mistaken for complete coverage.

See the verified material in [`../team-patterns-catalog.md`](../team-patterns-catalog.md).

## Resolved by the second pass

The second research pass closed the two biggest gaps from pass 1:
- **Helldivers 2** → now a [full appendix](helldivers-2.md) (reinforcement economy, sentry
  crossfire/CC-layering, beacon-placed revives, four-role split).
- **Deep Rock Galactic** → promoted from "thin" to a [full appendix](deep-rock-galactic.md)
  (resupply economy, ziplines/tunnels/platforms, defend-while-task, shielded revives). The earlier
  *refuted* platform→mining dependency was reclassified as an optional fall-safety assist.

It also upgraded **Pattern 7 (resource economy)** out of "medium" and confirmed primary industry
sources (Killzone 3, UT bots, Decima) validating the whole HTN approach.

## Still under-covered

| Game | Status | What is missing |
|------|--------|------------------|
| **Dota 2 / League of Legends** | Absent from verified set | Teamfight target-call priority, initiation timing, save-vs-engage cooldown trades |
| **Overwatch** | Absent from verified set | Ult economy / tracking, dive-vs-poke composition triggers |
| **FFXIV raids** | Absent from verified set | Phase markers, scripted role assignments (would parallel the WoW material) |

Candidate (unverified) sources prior searches surfaced for these — a starting point, **not**
citations to rely on yet:
- Dota 2: boosteria.org teamfights guide, bsjdota.com initiation guide
- Overwatch: boosteria.org ult-economy guide, dignitas.gg ult-tracking articles
- FFXIV: thebalanceffxiv.com

## Thin patterns in the catalog

- **[Pattern 9 — Phase / state transitions](../team-patterns-catalog.md#problem-9--phase--state-transitions-medium-confidence)**
  is still supported only by spawn-event re-prioritization. No explicit *named multi-phase timeline*
  (L4D AI Director crescendo/finale model, FFXIV phase markers) has survived verification.

## Open questions for the next research pass

1. **PvP coordination tactics** for Overwatch and Dota 2 / LoL — target-call priority, initiation
   timing, ult/ability economy, save-vs-engage cooldown trades.
2. **Explicit multi-phase boss timelines** — how real encounters encode named phases, transition
   triggers, and soft-enrage timers, and how an HTN method should re-bind roles and swap sub-methods
   on a phase transition. The L4D AI Director crescendo/finale phase model in particular was not
   captured.
3. **Optimal CC-budget policy** — given Monster Hunter's doubling status thresholds, is there a
   guide-prescribed heuristic for when re-applying a status is no longer worth the proc cost?
4. **FFXIV as a second raid corpus** — would likely yield a rich phase-timeline and role-assignment
   appendix paralleling the WoW material, strengthening Patterns 1, 2, and 9.

## See also
- [`../team-patterns-catalog.md`](../team-patterns-catalog.md) — the verified cross-game pattern catalog
- [`../README.md`](../README.md) — the `other_games` hub and methodology note
