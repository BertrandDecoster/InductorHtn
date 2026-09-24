# The ability layer

Building blocks for abilities that apply tags and effects: `components/abilities/`. It is a layer
parallel to the core vocabulary. It depends only on `core/primitives/core_world` (regions, `at`,
`navigate`, `canAct`, `canTarget`) and never uses `status/2`, `hasSkill` or `signature`. The research
behind every decision is in [`../research/ability-systems-survey.md`](../research/ability-systems-survey.md).
The worked examples are the `sinkhole` level (its own small physics), the `crossing` level (the
standard catalogue: 16 atomic tags, 8 composites, 3 outcomes, 51 skills -
[`ability-catalog.md`](ability-catalog.md)), and the `gauntlet` level (pure movement).

## The one rule: physics at the bottom, recipes at the top

| Layer | Components | What it holds | May it search? |
|-------|------------|---------------|----------------|
| Physics | `ab_tags`, `ab_effects`, `ab_casting` | What happens when an ability lands: tags, bundles of effects, reactions, zones, forced movement, gates and costs. A small closed set of atoms, all data. | No. Every branch is determined by the state. |
| Data | `ab_catalog` | The standard tags, reactions, zones, skills and archetype rules. | - |
| Acts | `ab_acts` | One need, one cast: inflict a tag, push into a region, strike, prime, unset, combo. The actor is bound at the leaf; `?not` excludes a companion. | Only over who and with what. It never recurses into its own prerequisites. |
| Recipes | `exploit` (the enemy's weakness), `into_the_pit` (hazards), `conduct`, `shatter`, `ignite`; goal `neutralize`; `passage` (reach, openWay, span, clear) | The combos: every step in order, the roles, the details. Each ends by confirming the simulated world. A guard comes off first. | Yes: each recipe is an alternative plan. |

Why the split, and not "reactions everywhere" or "specialized methods everywhere":

- **Search belongs to recipes.** In SHOP-style planners the methods carry the designer's knowledge,
  and method order is the priority (SHOP, Killzone, Fall of Cybertron). A generic `achieve(tag)` that
  searched the reaction table backwards would be GOAP inside an HTN: unbounded recursion, no pruning,
  no designer priority.
- **Physics belongs to data.** If a fireball lands on something wet, the simulated world must show
  steam *whichever recipe chose the fireball*. If combos lived only in the recipes, a plan that is not
  following the "right" recipe would simulate a world that is wrong. So `reaction/3` sits at the bottom
  as a filter on what just happened, never as a generator of plans. What a reaction cannot express
  (conditions on the target, geometry, several entities, "only mooks") goes in a recipe.

## Vocabulary

| Concept | Facts a level declares | Notes |
|---------|------------------------|-------|
| Tag | `tag(?e, ?t)` | The only store. |
| Composite | `bundles(?composite, ?atom)` | One level deep. `has/2` = stored or bundled. Atoms are never stored, so removing the composite removes them. |
| Group | `group(?t, ?g)` | Orthogonal categories. `gone` (dead, frozen, fell) is read by the layer. |
| Immunity | `immune(?e, ?x)` | `?x` is a tag, a damage type, or `forcedMove`, which is what "heavy" means. Immunity to an atom refuses the composites that bundle it. |
| Suspension | `suspends(?t, ?x)` | While `?e` has `?t`, its immunity to `?x` lapses (an unbalanced golem can be pushed). |
| Ward | `wards(?t, ?x)` | While `?e` has `?t`, it is immune to `?x`: a flyer to `fell`, the stealthed to `targeted`, the invulnerable to `damage` (any type). |
| Ban | `forbids(?t, ?kind)` | While `?e` has `?t`, it cannot do `?kind`: `spell`, `| Kind | `kind(?ab, ...)` | What a ban checks. In the catalogue every ability is a `skill` (silence) and dashes are `dash`; ranged abilities are also `ranged`. |`, `ranged`, `dash`, `move`, `heavy`, or `any`. Casting checks the caster; walking checks `move`. |
| Out of the fight | `stops(?e, ?t)` | Anything in group `gone` (dead, frozen, fell). A controlled enemy is set up, not beaten. |
| Weakness | `weakness(?e, ?in, ?have, ?out)` | This entity, taking `?in` (a tag or a hazard) while carrying `?have` (or `none`), gets `?out` instead. The only source of outcomes in the catalogue: a combo is deadly because of who it lands on. |
| On landing | `onGrant(?t, ?atom)` | Storing `?t` also does `?atom` to the bearer: feared pushes it away, taunted pulls it in. |
| Hostile | `hostile(?t)` | The tags `hostile` stands for in a reaction (a shield absorbs the next one; a blow wakes a sleeper) or a ward (invulnerability). |
| Look | `appearance(?look, ?tag)` | A status that plays like a tag and only looks different (petrified is a stun). The planner never sees a look. |
| Vulnerability | `vulnerable(?e, ?type)` | That damage kills outright. Meant for mooks; bosses never have it. |
| Ability | `knows(?a, ?ab)`, `reach(?ab, self\|melee\|ranged)` | `knows` is the loadout. Companions, NPCs and hazards all use abilities. |
| Effect bundle | `effect(?ab, target\|self\|area\|path, ?atom)` | Atoms: `grant(T)`, `remove(T)`, `purge(Group)`, `damage(Type)`, `push`, `pull`, `hook`, `swap`, `dash`, `teleport(R)`, `spill(Zone)`, `hazard(H)`, `open(Door)`. Applied in declared order. `area` is everyone else in the target's region, allies included; `path` is everyone in the regions between the source and the target (declare it before the move). An ability may be aimed at a region. The catalogue uses no damage. |
| Hook, swap | `hook`, `swap` atoms | A hook drags a light target in, or drags the source to an anchored one (a grappling hook). A swap trades places. A pull across a live hazard the target is weak to drops it there. |
| Walking | `connected/2`, `door/1` + `open/1`, `blocker/1`, `trait(?x, filler)` | A walk goes one region at a time by the shortest route (at most eight steps), never into a closed door, a blocker's region, or a live hazard the walker is weak to. A door opens for good when something arrives on its plate (a zone with `open(D)`). A filler fallen into a hazard makes it walkable. Melee reaches the next region too. |
| Route | `progress(?r, ?n)` | For `passage`: leaps only go forward. |
| Kind | `kind(?ab, ...)` | What a ban checks. In the catalogue every ability is a `skill` (silence) and dashes are `dash`; ranged abilities are also `ranged`. |
| Gates | `requires(?ab, caster\|target, ?t)`, `blockedBy(?ab, caster\|target, ?t)` | The GAS activation required / blocked tags. |
| Costs | `manaCost(?ab, ?n)` + `mana(?a, ?m)`; `once(?ab)` | Mana is a numeric fluent. `once` adds `spent(?a, ?ab)`. A self-tag (`tired`) plus `blockedBy` is a cooldown with no clock. |
| Reaction | `reaction(?have, ?incoming, ?ab)` | For everyone: `?incoming` (a tag, a damage type, `damage` or `hostile`) meeting `?have` fires ability `?ab` instead. A tag landing meets, in order: a reaction, the bearer's weakness, else it is stored. A reaction's effects apply `raw` (weaknesses still answer, no further reaction), and what a weakness produces is stored `bare`, so nothing chains. If several tags react, the first stored wins, and an exact match beats a class. |
| Guard | `group(?t, guard)` | A tag `neutralize` takes off first (`unset`: strip it, or pop it with what it reacts to), then plans again: stealth, a shield, invulnerability. |
| Zone / hazard | `onEnter(?r, ?ab)` | Whoever arrives takes `?ab`, credited to whoever moved them (walker or pusher). A hazard is a zone whose ability has `hazard(H)`: it takes only what is weak to `H`. |
| Push line | `beyond(?from, ?over, ?to)` | A push from `?from` on something at `?over` lands it in `?to`. The first line declared per `(?from, ?over)` is the only landing. |

## Authoring

**An ability.** A bundle of tags and movements. Here, a stun and a knockback:
```prolog
knows(warden, shieldBash).
reach(shieldBash, melee).
effect(shieldBash, target, grant(stunned)).
effect(shieldBash, target, push).
```

**A composite, and what landing it does.**
```prolog
bundles(feared, blinded).  bundles(feared, silenced).  bundles(feared, uncontrolledMove).
onGrant(feared, push).                     % it runs from whoever frightened it
```

**A weakness.** The only way to an outcome: this enemy, not everyone.
```prolog
weakness(?e, electrocuted, wet, dead) :- trait(?e, machine).      % soaked, then jolted
weakness(?e, electrocuted, none, stunned) :- trait(?e, machine).  % jolted
weakness(golem, burning, oiled, dead).                            % a level adds its own
```

**A reaction.** For everyone, and it never kills. A reaction is an ability, so it can do anything
a skill can.
```prolog
reaction(oiled, burning, blaze).
effect(blaze, target, remove(oiled)).  effect(blaze, area, grant(burning)).
```

**A hazard.** A zone whose ability takes only what is weak to it.
```prolog
onEnter(abyss, chasm).  effect(chasm, target, hazard(chasm)).
weakness(?e, chasm, none, fell) :- not(trait(?e, flier)).
beyond(hall, brink, abyss).
```

**A recipe.** It is specialized and states its steps and roles. Build it from the acts and end with
`confirmStopped`:
```prolog
% ab_acts: the shape most combos share
combo(?have, ?in, ?e) :-
    if(receptive(?e, ?in), supplier(?p, ?have, ?e)),
    do(supply(?p, ?have, ?e), deliver(?in, ?e, ?p), confirmStopped(?e)).

% a recipe names its halves
conduct(?e) :- if(), do(combo(wet, shocked, ?e)).
exploit(?e) :-                          % the enemy's own weakness names the halves
    if(lethalWeakness(?e, ?in, ?have), \==(?have, none)), do(combo(?have, ?in, ?e)).
```
A recipe that doesn't fit the shape states its own steps (`shatter`, `intoThePit`).
`supplier/3` gives `none` if `?e` already has the tag, and otherwise one companion per answer who can
prime it by a cast or by a push into a zone. The pay-off excludes that companion (`?not`), which is
how cooperation is forced without naming the player.

## Engine rules this layer depends on

- **`else` is not a cut.** When a later task fails, InductorHTN backtracks into an `else` branch, so
  an `else, if(), do()` no-op lets a plan skip an effect or a cost it finds inconvenient. Every
  "nothing happens" branch in the physics carries the explicit negation of the branches before it.
  `ab_effects` P5 pins this.
- **One landing per push.** Planning (`placement/5`) and physics (`shove`) both read `landing/3`, so
  the planner cannot promise a destination the physics would not produce.
- **Operator rules** (`component-system.md`) still apply: actor first, ground `del`, guarded adds, no
  `hidden`, a fresh planner per world.

## Interaction with the fun metrics

The physics records every consequence as its own operator: `opGrant`, `opRemove`, `opReact`,
`opForcedMove` follow each `opCast`, with the caster (or the mover, for zones) first. That is honest
for F6's actor convention: the pusher, not the pit, gets the credit. But it shifts the other readings:

- F3 `plan_length` counts consequences, not decisions (the sinkhole's ~20 operators are about 8
  casts and walks).
- F3 interlock and F6 `teamwork_edge_ratio` are diluted by edges that run from a cast to its own
  consequences.
- The MCP level tools offer the player consequence operators as moves, and observations read
  `status/2` and `hasSkill`, so tags and abilities are not shown.

A future step: let a level or component declare consequence operators, so that fun and the MCP tools
group a cast with its consequences and read `tag/2` and `knows/2`.

## Recipes

| Recipe | Shape |
|--------|-------|
| `exploit` | The enemy's own lethal weakness: one blow, or `combo(?have, ?in, ?e)` - someone primes, someone else delivers, confirm. |
| `intoThePit` | Push into a zone that stops it (a hazard it is weak to); unbalance the heavy, strip the armour, or ground the flying first. |
| `conduct`, `ignite` | `combo(wet, shocked)`, `combo(oiled, burning)` - the `sinkhole` level's physics. |
| `shatter` | Soak, freeze; stop, or break it with a blunt blow (`sinkhole`). |
| `improvise` | One cast: a stopping tag, or damage the target is vulnerable to. |
| `reach` | Walk; or leap forward (dash, hook to an anchor, swap, an ally's swap), then carry on. |
| `openWay`, `span`, `clear` | Latch a door (someone or something on the plate); bridge a gap (push or drag a filler in, or leave it); a blocker dropped, moved, or left. |

## Open questions (deferred on purpose)

- **Windows and synchronization.** An NPC's triggered sequence (provoke → slam → tired) that the plan
  exploits at the right moment. The existing `opSynchronize` / `parallel()` idea is the likely
  vehicle. Build levels first, then decide.
- **Zone-bound tags.** Tags that exist only while standing somewhere (submerged, in cover). No level
  needs them yet.
- **Zones that react.** Fire on an oil region turning it into a fire region: a region-level
  reaction. Core's `reacts/3` does this for core levels; this layer has no effect atom for it yet.
- **Durations.** There are no turns. A self-tag plus `blockedBy` models a one-use drawback, and
  anything longer waits for a real need.
