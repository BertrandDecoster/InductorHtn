# Deep Rock Galactic — evidence appendix
Inter-class traversal synergies, a quantified resupply economy, and defend-while-task objectives.

Deep Rock Galactic is a four-class co-op mining shooter. The first research sweep verified only the
base class roles; a targeted second pass recovered the deeper coordination layer: cross-class
*traversal and safety* synergies (ziplines, drilled tunnels, platforms), a precisely quantified
*shared resupply economy*, swarm-coordinated revives, and a *defend-while-doing-the-task* division
of labor on stationary objectives. Crucially, it also **resolved** an earlier refutation (see below).

See the cross-game synthesis in [`../team-patterns-catalog.md`](../team-patterns-catalog.md).

## Patterns this game exemplifies

| Catalog pattern | Tactic from this game |
|-----------------|-----------------------|
| [1 — Role assignment](../team-patterns-catalog.md#problem-1--role--responsibility-assignment) | Four hard class roles; defend-while-task split on stationary objectives |
| [4 — Positioning](../team-patterns-catalog.md#problem-4--positioning--formation) | Scout flares light swarm approach lanes; Engineer platforms as fall-safety assists |
| [6 — CC chaining](../team-patterns-catalog.md#problem-6--crowd-control-chaining--cc-economy) | Engineer Platform Gun seals a tunnel to deny a swarm an angle |
| [7 — Resource economy](../team-patterns-catalog.md#problem-7--resource--cooldown-economy) | Resupply pod: 80 Nitra, 4 racks, take a rack only below ~50% |
| [8 — Throughput / traversal](../team-patterns-catalog.md#problem-8--throughput--task-pipelining) | Driller tunnels as team shortcuts to the drop pod |
| [10 — Recovery](../team-patterns-catalog.md#problem-10--recovery--failure-handling) | Gunner shields a downed dwarf to enable a safe revive mid-swarm |
| [11 — Safety constraints](../team-patterns-catalog.md#problem-11--safety-constraints) | Ziplines zero out fall damage; platform tunnel-seal area denial |

## Verified tactics

**Base class roles** ([jeu.video](https://jeu.video/en/guide/deep-rock-galactic-classes-coop-en)):
Scout = light + high minerals, Gunner = safety + sustained damage, Engineer = area control +
platforms, Driller = terrain + crowd clear. These are the role tokens for
[Pattern 1](../team-patterns-catalog.md#problem-1--role--responsibility-assignment).

**Resupply economy (quantified shared resource).** "All classes are able to order a resupply using
80 Nitra … there is a short delay before any player can order another." A single pod provides
**four racks**, each restoring "50% of a player's ammunition (rounded up), and half of their overall
health." Benefits "cannot be refilled higher than the amount the player starts the mission with …
cannot be stored or transferred" — so over-resupplying *wastes* the shared resource, and the rule of
thumb is to take a rack only when below ~50%.
— [DRG Wiki, Resupply Pod](https://deeprockgalactic.wiki.gg/wiki/Resupply_Pod)

**Gunner ziplines (traversal + fall safety).** "If a dwarf attaches to a zipline before they hit the
ground, no matter the height or velocity, no fall damage is taken." Deploy when the team faces a
dangerous drop or needs a safe descent.
— [Steam class-synergy guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2950418160)

**Driller tunnels (team shortcut / escape).** "You can drill your whole team safely back to the drop
pod, which often makes it there quicker than Molly." The official wiki corroborates: "During
extraction phases, the Driller can also create long tunnels to the Drop Pod, which can be safer and
quicker than following the M.U.L.E. through winding cave tunnels."
— [Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2950418160),
[DRG Wiki, Tips](https://deeprockgalactic.wiki.gg/wiki/Tips,_tricks_and_strategies)

**Scout flares (swarm-approach illumination).** "During a swarm, make sure EVERYTHING is well lit,
including where a swarm could come from" — triggered by an incoming swarm or entering a new cave.
— [Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2950418160)

**Gunner shield revive (CC-protected recovery).** "Throw your shield over downed dwarves for the
safest possible revive amidst a swarm" — the shield is thrown first, then the revive happens inside
it.
— [Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2950418160)

**Platform Gun tunnel-seal (area denial).** "With careful shots in a tight corridor, it is possible
to completely seal a tunnel shut using platforms. This may be useful during Swarms in order to block
off an angle of attack."
— [DRG Wiki, Tips](https://deeprockgalactic.wiki.gg/wiki/Tips,_tricks_and_strategies)

**Defend-while-task objectives (division of labor).** Stationary-objective missions split the team
between *doing the task* and *holding the ground*: On-site Refining (set up pipes refinery→pumpjacks,
protect/repair pipes), Salvage Operation (reattach Mini-MULE legs, establish Uplink, refuel the Drop
Pod while surviving), Point Extraction (collect Aquarqs while turrets/players defend waves), Escort
Duty (protect and refuel the Drilldozer, Doretta).
— [DRG Fandom, How to Play](https://deeprockgalactic.fandom.com/wiki/How_to_Play_Guide_for_Deep_Rock_Galactic)

## The platform synergy — refutation resolved

The first sweep **refuted (0-3)** the claim that "the Engineer *must* place platforms before the
Scout can mine high minerals" as a hard pipelined dependency. The second pass clarifies what is
actually true: the Engineer-Scout platform synergy is a **safety assist**, not a gate. "An Engineer
places a platform underneath a pile of minerals in order to assist the Scout, who can then safely
grapple onto the minerals **without risk of falling**."
— [DRG Fandom, How to Play](https://deeprockgalactic.fandom.com/wiki/How_to_Play_Guide_for_Deep_Rock_Galactic)

So model it as an *optional safety-improving assist* (a `try()`-style optional sub-task), **never** as
a precondition that blocks the Scout from mining.

## HTN sketches

```prolog
% Resupply economy: only take a rack when actually low; only order when the team can afford it.
takeResupply(?dwarf, ?pod) :-
    if(ammo(?dwarf, ?a), <(?a, 50), racksLeft(?pod, ?r), >(?r, 0)),
    do(opTakeRack(?dwarf, ?pod)).
opTakeRack(?dwarf, ?pod) :-
    decrease(racksLeft(?pod), 1), increase(ammo(?dwarf), 50).

orderResupply(?dwarf) :-
    if(nitra(team, ?n), >=(?n, 80), not(podPending)),
    do(opOrderPod(?dwarf)).

% CC-protected revive: shield first, then revive (Pattern 10 + 11 + 6).
safeRevive(?down) :-
    if(downed(?down), swarmActive, role(?g, gunner), ready(?g, shield)),
    do(opThrowShield(?g, ?down), opRevive(?g, ?down)).

% Platform synergy as an OPTIONAL assist — note try(), not a hard precondition.
scoutMine(?node) :-
    if(role(?s, scout), mineralPile(?node)),
    do(try(engineerPlatform(?node)), opGrappleMine(?s, ?node)).
```

## Caveats

- Most synergy tactics come from a community Steam guide (secondary) but are corroborated by the
  official wiki where they overlap (tunnels, platform-seal). The resupply numbers are from the
  primary wiki.
- **Refuted (do not model):** the Scout's L.U.R.E. grenade as a "throw at untargeted enemies so they
  swarm the lure for easy round-up" tactic did **not** survive verification (0-3).

## See also
- [`../team-patterns-catalog.md`](../team-patterns-catalog.md) — the cross-game pattern catalog
- [`helldivers-2.md`](helldivers-2.md) — the other co-op PvE game from this second pass
- [`coverage-gaps.md`](coverage-gaps.md) — what still lacks verified coordination tactics
