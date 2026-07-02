# Helldivers 2 — evidence appendix
Shared finite economies, sentry crossfire discipline, and friendly-fire as a hard constraint.

Helldivers 2 is a four-player objective co-op shooter where the defining coordination pressures are
*shared finite resources* (reinforcement tickets), *line-of-fire safety* (every stratagem and
sentry can kill teammates), and *role division* across a 16-slot stratagem budget. These were
**absent from the first research sweep** and recovered in a targeted second pass; the verified
tactics map cleanly onto the resource-economy, positioning, CC-chaining, and safety patterns.

See the cross-game synthesis in [`../team-patterns-catalog.md`](../team-patterns-catalog.md).

## Patterns this game exemplifies

| Catalog pattern | Tactic from this game |
|-----------------|-----------------------|
| [1 — Role assignment](../team-patterns-catalog.md#problem-1--role--responsibility-assignment) | Difficulty-10 four-role split: Anti-Tank / Crowd Control / Saboteur / Support |
| [4 — Positioning](../team-patterns-catalog.md#problem-4--positioning--formation) | Sentry crossfire placement; reinforcement beacon controls revive landing |
| [6 — CC chaining](../team-patterns-catalog.md#problem-6--crowd-control-chaining--cc-economy) | EMS Mortar slows a horde → Gatling/Autocannon sentry kills it |
| [7 — Resource economy](../team-patterns-catalog.md#problem-7--resource--cooldown-economy) | Reinforcement tickets: 5/player, 20/squad, mission fails when exhausted |
| [10 — Recovery](../team-patterns-catalog.md#problem-10--recovery--failure-handling) | Reinforce a dead teammate via a beacon-placed drop pod |
| [11 — Safety constraints](../team-patterns-catalog.md#problem-11--safety-constraints) | Sentry firing-arc call-outs; drop pod squashes allies too |

## Verified tactics

**Reinforcement economy (shared finite resource).** Reinforcements are limited to **five tickets
per player, up to a maximum of 20 in a full squad**; exhausting all reinforcements (including
regenerating ones) with the objective incomplete **fails the mission**. Reinforce is therefore a
finite economy to manage, not a free respawn.
— [Helldivers Wiki, Reinforce](https://helldivers.wiki.gg/wiki/Reinforce)

**Beacon-placed revive (positioning the drop).** "The reinforcement pod is necessarily limited to
an area around the beacon that calls it, and that it squashes enemies and allies alike." Where a
revived player lands is controlled by *beacon placement* — and the pod is itself a hazard.
— [Helldivers Wiki, Reinforce](https://helldivers.wiki.gg/wiki/Reinforce)

**Sentry crossfire placement.** Place sentries "far off to one side, preferably behind some cover"
and "away from your squad to create a crossfire", so that "when the bots focus their attention on
you, your sentry can fire at their weaker side and back panels."
— [zleague Sentry Guide](https://www.zleague.gg/theportal/helldivers-2-sentry-guide/)

**Sentry firing-arc communication (line-of-fire safety).** "You need to talk to your squad. Call
out where you're placing your sentry so they know which angles are covered." Sentries shoot
teammates who cross their lane — placement is a *communicated* safety constraint.
— [zleague Sentry Guide](https://www.zleague.gg/theportal/helldivers-2-sentry-guide/),
corroborated by [Helldivers Wiki](https://helldivers.wiki.gg/wiki/Stratagems)

**CC-then-damage sentry layering.** "An EMS Mortar Sentry can slow down a horde of bots, making
them easy targets for a Gatling or Autocannon Sentry" — a crowd-control-then-damage chaining combo.
— [zleague Sentry Guide](https://www.zleague.gg/theportal/helldivers-2-sentry-guide/)

**Four-role squad split (Difficulty 10).** Super Helldive squads divide into **Anti-Tank**
(eliminates heavies), **Crowd Control** (manages swarms), **Saboteur** (side objectives / stealth),
and **Support/Medic** (team resources / survivability), because "teams that assign roles perform
significantly better than those that try to do everything individually."
— [2upskill Super Helldive guide](https://2upskill.com/helldivers-2-super-helldive-meta-guide-2026-best-stratagems-and-loadouts-for-difficulty-10/)

## HTN sketches

```prolog
% Reinforcement economy: spend a shared ticket only when it's worth it, and drop somewhere safe
% (the pod squashes allies — beacon placement is both a positioning AND a safety decision).
reinforce(?deadAlly) :-
    if(dead(?deadAlly), tickets(squad, ?n), >(?n, 0),
       safeBeacon(?spot)),
    do(opThrowBeacon(?caller, ?spot), opReinforce(?deadAlly, ?spot)).
opReinforce(?ally, ?spot) :-
    decrease(tickets(squad), 1), del(dead(?ally)), add(at(?ally, ?spot)).

% CC-then-damage sentry chain.
layerSentries(?horde) :-
    if(sentry(?ems, emsMortar), ready(?ems), sentry(?dmg, gatling)),
    do(opFireEMS(?ems, ?horde), opFireSentry(?dmg, ?horde)).

% Sentry placement gated on a clear firing arc, then broadcast the covered lane.
placeSentry(?s, ?lane) :-
    if(flankLane(?lane), behindCover(?lane), not(allyInArc(?lane))),
    do(opPlaceSentry(?s, ?lane), opBroadcastArc(?s, ?lane)).
```

## Caveats

- The four-role split passed verification **2-1** — it is *one taxonomy among several* the meta
  community uses, not a single canonical assignment. Treat the four roles as an example template,
  not the only valid composition.
- Most sentry sources are blogs; the claims are mainstream consensus and independently corroborated
  (including by the official wiki), but not primary developer documentation.
- **Refuted (do not model):** that the Reinforce stratagem has a literal *0-second cooldown* and a
  precondition of purely "teammate dead AND tickets remaining" (0-3); and that an EMS Mortar is
  prescribed *specifically* to stop Automaton bot drops from escalating (1-2). The reinforcement
  *economy* above is solid; these two finer claims are not.

## See also
- [`../team-patterns-catalog.md`](../team-patterns-catalog.md) — the cross-game pattern catalog
- [`deep-rock-galactic.md`](deep-rock-galactic.md) — the other co-op PvE game from this second pass
- [`coverage-gaps.md`](coverage-gaps.md) — what still lacks verified coordination tactics
