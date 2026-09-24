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
| Group | `group(?t, ?g)` | Orthogonal categories. `gone` (dead, fell) is read by the layer. |
| Immunity | `immune(?e, ?x)` | `?x` is a tag, a damage type, or `forcedMove`. Immunity to an atom refuses the composites that bundle it. What an entity is (heavy, flying, machine) is a tag, so a skill can take it off. |
| Suspension | `suspends(?t, ?x)` | While `?e` has `?t`, its immunity to `?x` lapses (an unbalanced golem can be pushed). |
| Ward | `wards(?t, ?x)` | While `?e` has `?t`, it is immune to `?x`: a flyer to `fell`, the stealthed to `targeted`, the heavy to `forcedMove`, the disjoint to everything aimed at it. |
| Ban | `forbids(?t, ?kind)` | While `?e` has `?t`, it cannot do `?kind`: `skill`, `attack`, `ranged`, `dash`, `move`, `watch`, or `any`. Casting checks the caster; walking checks `move`; a silenced NPC's heavy attack stops. |
| Out of the fight | `stops(?e, ?t)` | Anything in group `gone` (dead, fell). A controlled or frozen enemy is set up, not beaten; a level may add `stops(?e, frozen)`. |
| Weakness | `weakness(?e, ?in, ?have, ?out)` | This entity, taking `?in` (a tag or a hazard) while carrying `?have` (or `none`), gets `?out` instead. The only source of outcomes in the catalogue: a combo is deadly because of who it lands on. |
| On landing | `onGrant(?t, ?atom)` | Storing `?t` also does `?atom` to the bearer: a taunted NPC chases its taunter. |
| Hostile | `hostile(?t)` | The tags `hostile` stands for in a reaction (a shield absorbs the next one; a blow wakes a sleeper) or a ward (invulnerability). |
| Look | `appearance(?look, ?tag)` | A status that plays like a tag and only looks different (petrified is a stun). The planner never sees a look. |
| Vulnerability | `vulnerable(?e, ?type)` | That damage kills outright. Meant for mooks; bosses never have it. |
| Ability | `knows(?a, ?ab)`, `reach(?ab, self\|melee\|ranged)` | `knows` is the loadout. Companions, NPCs and hazards all use abilities. |
| Effect bundle | `effect(?ab, target\|self\|area\|around\|path, ?atom)` | Atoms, by family: tags `grant(T)`, `remove(T)`, `purge(Group)`, `damage(Type)`; movement `push`, `pull`, `hook`, `swap`, `dash`, `teleport` (the source to the target's region), `teleport(R)` (the target to R), `pullIn` (everything next door into the target region); actions `interrupt`; terrain `spill(Zone)`, `hazard(H)`, `open(Door)`, `close(Door)`. Duration: `moment(grant(T))` / `moment(remove(T))` last through the next cast by anyone. `area` is everyone else in the target's region, allies included; `around` is everyone else in the source's region and the regions next to it (a push from the source's own region goes nowhere); `path` is everyone between the source and the target (declare it before the move). An ability may be aimed at a region. The catalogue uses no damage. |
| Movement | `push`, `pull`, `hook`, `pullIn`, `dash`, `teleport`, `chase` atoms | Every movement goes one link. A push sends its target to any neighbouring area but the source's own: the caster aims where it lands, so every choice is a plan. A pull brings it into the source's area from next door. A hook is a pull; an anchored target pulls the source to it instead (a grappling hook). `pullIn` draws everything next door into the target area. Dash and teleport take the source next door, never into a live hazard it is weak to. A chase: the target walks after the source, and follows it whenever it moves; if it cannot walk there, it gives up (a taunt breaks). |
| Moment | `moment(Atom)`, `clock/1`, `lasts/4` | The only duration. Every cast ticks `clock`; a moment granted or taken at clock `c` is undone when the clock passes `c + 1`, never inside a heavy attack's window. |
| Terrain | `zoneReaction(?old, ?in, ?new)` | A spill of zone `?in` on a region holding `?old` leaves `?new` there instead, or no zone for `none` (ice over deep water is a floor). |
| Heavy attack | `heavy(?ab)`, `kind(?ab, magic)`, `mustSurvive(?x)` | An NPC behaviour whose ability is heavy winds up (`windingUp(?npc, ?ab, ?x)`) on an area, or on an entity it follows. With a companion in the struck area the team may answer with one cast, without walking, by any companion - or take the blow: sacrifice is allowed. What a level declares `mustSurvive` may never be caught, so there the team must answer. The blow then falls on everyone in the struck area but the NPC: a disjoint one is passed through, a shielded one's shield breaks, anyone else takes the ability's `target` effects. Its spill lands on the area, and takes everyone there. `interrupt` stops a magic one; a physical one cannot be stopped. A silenced NPC's behaviours do not fire; an NPC winding up does not start another. |
| Map | `connected(?a, ?b)`, `gap(?a, ?b)`, `wall(?a, ?b)`, `doorway(?a, ?b, ?d)` + `open(?d)` | Areas are large - a small room, or a quarter of a large one - joined by links, declared once either way round. A chokepoint is two areas with a special link. Walk: walkable links. Dash: walkable links and gaps. Teleport: any link. Forced movement: walkable links; across a gap it falls in (a flyer crosses; a filler that falls in bridges it); a wall stops it. A door is walkable while open, else a wall. A walk takes the shortest route (at most eight steps), never into a blocker's area, a live hazard, or - for a companion - a watched area. Melee reaches the same area or next door over a walkable link or a gap. |
| Route | `progress(?r, ?n)` | For `passage`: leaps only go forward. |
| Kind | `kind(?ab, ...)` | What a ban checks. In the catalogue every ability is a `skill` (silence) and dashes are `dash`; ranged abilities are also `ranged`. |
| Gates | `requires(?ab, caster\|target, ?t)`, `blockedBy(?ab, caster\|target, ?t)` | The GAS activation required / blocked tags. |
| Costs | `manaCost(?ab, ?n)` + `mana(?a, ?m)`; `once(?ab)` | Mana is a numeric fluent. `once` adds `spent(?a, ?ab)`. A self-tag (`tired`) plus `blockedBy` is a cooldown with no clock. |
| Reaction | `reaction(?have, ?incoming, ?ab)` | For everyone: `?incoming` (a tag, a damage type, `damage` or `hostile`) meeting `?have` fires ability `?ab` instead. A tag landing meets, in order: a reaction, the bearer's weakness, else it is stored. A reaction's effects apply `raw` (weaknesses still answer, no further reaction), and what a weakness produces is stored `bare`, so nothing chains. If several tags react, the first stored wins, and an exact match beats a class. |
| Guard | `group(?t, guard)` | A tag `neutralize` takes off first (`unset`: strip it, or pop it with what it reacts to), then plans again: stealth, a shield, invulnerability. |
| Zone / hazard | `onEnter(?r, ?ab)` | Whoever arrives takes `?ab`, credited to whoever moved them (walker or pusher). A hazard is a zone whose ability has `hazard(H)`: it takes only what is weak to `H`. |

## Authoring

**An ability.** A bundle of tags and movements. Here, a stun, an interrupt, and a shield for the
caster:
```prolog
knows(warden, shieldBash).
reach(shieldBash, melee).
effect(shieldBash, target, interrupt).
effect(shieldBash, target, grant(stunned)).
effect(shieldBash, self, grant(shielded)).
```

**A composite, and what landing a tag does.**
```prolog
bundles(stunned, blinded).  bundles(stunned, silenced).  bundles(stunned, rooted).
onGrant(taunted, chase).                   % the NPC walks after its taunter
```

**A weakness.** The only way to an outcome: this enemy, not everyone.
```prolog
weakness(?e, electrocuted, wet, dead) :- has(?e, machine).        % soaked, then jolted
weakness(?e, electrocuted, none, stunned) :- has(?e, machine).    % jolted
weakness(golem, burning, oiled, dead).                            % a level adds its own
```

**A reaction.** For everyone, and it never kills. A reaction is an ability, so it can do anything
a skill can.
```prolog
reaction(oiled, burning, blaze).
effect(blaze, target, remove(oiled)).  effect(blaze, area, grant(burning)).
```

**A map.** Areas and the links between them; a hazard is a zone whose ability takes only what is
weak to it, and a gap is a short pit between two areas.
```prolog
connected(hall, brink).  gap(brink, ledge).  wall(hall, vault).  doorway(hall, crypt, gate).
onEnter(abyss, chasm).  connected(brink, abyss).
effect(chasm, target, hazard(chasm)).  weakness(?e, chasm, none, fell).
```

**A recipe.** It is specialized and states its steps and roles. Build it from the acts and end with
`confirmStopped`:
```prolog
% ab_acts: the shape most combos share
combo(?have, ?in, ?e) :-
    if(receptive(?e, ?in), supplier(?p, ?have, ?e)),
    do(supply(?p, ?have, ?e), deliver(?in, ?e, ?p), confirmStopped(?e)).

% a recipe names its halves
conduct(?e) :- if(), do(combo(wet, electrocuted, ?e)).
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
| `conduct`, `ignite` | `combo(wet, electrocuted)`, `combo(oiled, burning)`. |
| `shatter` | Soak, then chill: stop it, or deliver the blow its weakness names. |
| `improvise` | One cast: a stopping tag, or damage the target is vulnerable to. |
| `reach` | Walk; or leap forward (dash, teleport, hook to an anchor, swap, an ally's swap), then carry on. |
| `openWay`, `span`, `clear` | Latch a door (someone or something on the plate); bridge a gap (push or drag a filler in, or leave it); a blocker dropped, moved, or left. |

## Open questions (deferred on purpose)

- **Longer windows.** A heavy attack gives the team exactly one cast. Multi-step NPC sequences
  (provoke, slam, tired) and windows longer than one action are still open.
- **Durations.** There are no turns. The one duration is a moment (through the next cast); anything
  longer waits for a real need.
