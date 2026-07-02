# Left 4 Dead 2 — evidence appendix
Emergent survival: pin-and-rescue loops, formation discipline, and attacker priority lists.

Left 4 Dead 2 is unusual in that its richest *coordination* documentation is written for the
**Infected** (attacker) side — explicit lists of when to pounce, how to break survivor formation,
and how to exploit safety gaps. That makes it a strong source for both the survivor recovery loop
and the attacker decision lists, both of which decompose cleanly into condition-gated actions.

See the cross-game synthesis in [`../team-patterns-catalog.md`](../team-patterns-catalog.md).

## Patterns this game exemplifies

| Catalog pattern | Tactic from this game |
|-----------------|-----------------------|
| [3 — Focus fire / priority](../team-patterns-catalog.md#problem-3--focus-fire--target-prioritization) | Hunter's explicit favorable-pounce situation list |
| [4 — Positioning](../team-patterns-catalog.md#problem-4--positioning--formation) | Stick together (stragglers get pinned); Smoker drags members out of formation |
| [10 — Recovery](../team-patterns-catalog.md#problem-10--recovery--failure-handling) | Pin-and-rescue loop with a type-dependent freeing action |
| [11 — Safety constraints](../team-patterns-catalog.md#problem-11--safety-constraints) | Boomer vision obstruction and Jockey→Spitter hazard steering |

## Verified tactics

**Pin-and-rescue loop (type-dependent recovery).** Special Infected pins (Smoker tongue, Hunter
pounce, Jockey ride, Charger pummel) leave a survivor helpless; after a short grip the survivor
**can no longer self-rescue** and must be freed by a teammate. For a Smoker you can melee it, kill
it, melee the trapped survivor, or shoot the tongue. **Exception:** the Charger is *immune to melee
knockback* — a pummeled survivor must be freed by killing or frag/explosive-stunning the Charger.
— [StrategyWiki L4D2 Infected](https://strategywiki.org/wiki/Left_4_Dead_2/Infected)

**Pounce priority list (attacker focus fire).** A Hunter is given an explicit set of favorable
pounce situations: a survivor caught in a horde swarm, a survivor it's impossible to rescue, a
survivor more than ~10 seconds from the group, awkward ladder/stairwell angles, or a lone survivor
holed up in a room.
— [StrategyWiki L4D2 Infected](https://strategywiki.org/wiki/Left_4_Dead_2/Infected)

**Formation discipline.** Survivors should stick together; getting too far ahead of a slow member
exposes stragglers. The Smoker's "ideal role is to break up the survivor formation" by dragging a
member away from the group.
— [StrategyWiki L4D2 Infected](https://strategywiki.org/wiki/Left_4_Dead_2/Infected)

**Hazard exploitation (safety gaps).** A Boomer's vision/halo obstruction (~20–25s) prevents the
team from detecting a pinned survivor, letting Hunters/Smokers strike undetected. A Jockey can steer
a ridden survivor into a Spitter acid patch — a designed hazard combo (the "Rode Hard, Put Away Wet"
achievement).
— [StrategyWiki L4D2 Infected](https://strategywiki.org/wiki/Left_4_Dead_2/Infected)

## Caveats

- The pounce list is a *flat set* of favorable situations, not an explicitly ranked priority order;
  modelling it as an ordered `else` ladder is a design choice, not a sourced ranking.
- The Charger melee-immunity exception is the key reason the rescue operator must branch on attacker
  type — do not collapse it into a single generic "free the ally" action.
- Boomer obstruction duration is cited as ~20–25s (one outlier said ~15s) — a tunable parameter.

## See also
- [`../team-patterns-catalog.md`](../team-patterns-catalog.md) — the cross-game pattern catalog
- `../../../components/primitives/aggro/src.htn` — `lureToRoom` / `enemyFollows`, repo idioms for the
  "drag a target somewhere" beat the Smoker and Jockey perform
