# Ab Effects

## Purpose

The physics of the ability layer: what an ability does to the world once it is used. Whoever
acts owns an ability: a companion, an NPC, a hazard, or a reaction. An ability is a bundle of effects
applied in declared order (GAS: a GameplayEffect is data). The set of effect atoms is closed and
small: `grant(T)`, `remove(T)`, `purge(Group)`, `damage(Type)`, `push`, `pull`, `dash`, `teleport(R)`,
`spill(Zone)`. The recipient is `target`, `self` (the source), or `area`: everyone else in the target's
region, friendly fire included. An ability may be aimed at a region; only `area`, `spill` and `dash`
act on one.

Combos are physics too, and they live here as data, not in methods. `reaction(?have, ?incoming, ?ab)`
says that when `?incoming` (a tag or a damage type) lands on something carrying `?have`, ability `?ab`
fires instead. It works like a Genshin aura consumed by its trigger, or DOS2's wet + shock. The
reaction table is consulted only as a *filter* on what just happened. It is never *searched* to plan a
combo; the recipe methods at the top plan combos. A reaction's own effects apply `raw`: they fire no
further reaction, so a decomposition never chains.

This split keeps the simulated world honest. Whichever recipe chose the fireball, a fireball on
something wet makes steam.

## Layer

primitive

## Dependencies

- `core/primitives/core_world`
- `abilities/primitives/ab_tags`

## Operators

| Operator | Description |
|----------|-------------|
| `opReact(?src, ?e, ?have, ?incoming, ?ab)` | Marker: `?incoming` met `?have` on `?e` and fired `?ab`. |
| `opForcedMove(?src, ?e, ?from, ?to)` | `?src` pushes, pulls or teleports `?e`. |
| `opDash(?a, ?from, ?to)` | `?a` closes on its target. |

## Methods

| Method | Description |
|--------|-------------|
| `applyAbility(?src, ?ab, ?e, ?mode)` | Every `effect/3` of `?ab`, in order, from `?src` onto `?e` (`target`), `?src` (`self`), or everyone else in the region of `?e` (`area`). |
| `purgeGroup(?src, ?e, ?g)` | Removes every stored tag of `?e` in group `?g`. |
| `spillZone(?src, ?e, ?z, ?mode)` | The region of `?e` becomes a zone of `?z`; everyone there takes it at once. |
| `grantTag(?src, ?e, ?t, ?mode)` | React: a reaction, else the bearer's weakness, else stored. Raw: weakness, else stored. Bare: stored. A stored tag then does its `onGrant/2` atoms. |
| `suffer(?src, ?e, ?h)` | A hazard: whatever is weak to it takes the outcome. |
| `removeTag(?src, ?e, ?t)` | Deleted if stored. |
| `takeDamage(?src, ?e, ?type, ?mode)` | A reaction first (blunt on brittle; a shield absorbs; steam saves the wet from fire); else kills the vulnerable; else nothing. |
| `shove` / `drag` / `dashTo` / `blink` | Forced movement along `beyond/3`, towards the source, onto the target, to a region. |
| `arrive(?src, ?e, ?r, ?mode)` / `enterZone` | Whoever arrives in `?r` takes its `onEnter` abilities. The mover is the source. |
| `walkTo(?a, ?r)` | A companion walks one region at a time, taking what each region does, never into a closed door, through a blocker, or into a live hazard it is weak to. |
| `hookOn` / `swapPlaces` / `openDoor` | The `hook`, `swap` and `open(D)` atoms. |

Every "nothing happens" branch carries the explicit negation of the branches before it. In this
engine, `else` is not a cut: when a later task fails, the planner backtracks into an `else` no-op and
would skip an effect it finds inconvenient.

## Rules

| Rule | Description |
|------|-------------|
| `reactionFor(?e, ?incoming, ?have, ?ab)` | The reaction `?incoming` triggers on `?e`: the first stored tag (then bundled atom) with one wins; an exact match beats `damage`. |
| `matches(?have, ?incoming, ?ab)` | `reaction/3` on exactly `?incoming`, or on `damage` when `?incoming` is a `damageType`. |
| `locus(?e, ?r)` | Where an entity is, or a region itself. |
| `kills(?e, ?type)` | `vulnerable(?e, ?type)` and `?e` can still die. |
| `weakFor(?e, ?in, ?have, ?out)` | The first `weakness/4` of `?e` for `?in` whose prerequisite it carries. |
| `anchoredAgainst(?e)` | Not receptive to `forcedMove` (immune and not unbalanced, or gone). |
| `landing(?from, ?over, ?to)` | Where a push from `?from` on `?over` lands: the first `beyond/3` line declared, so planning and physics agree. |
| `pushLine` / `pullLine` / `dashLine` / `blinkLine` | Where the movement goes, if anywhere. |
| `hasZone(?r)` | `?r` has an `onEnter` ability. |
| `between(?x, ?y, ?m)` | `?m` lies between `?x` and `?y` on a declared line. |
| `pullLand(?src, ?e, ?from, ?land)` | Where a pull lands: the first live hazard between that `?e` is weak to, else at the source. |
| `filled(?r)` / `hazardAt(?r, ?h)` / `deadly(?e, ?r)` | A filler at the bottom makes a hazard dead. |
| `passable(?a, ?r)` / `nextStep` / `canReach(?a, ?f, ?r)` | Walkable routes, found by iterative deepening (at most eight steps, never stepping straight back). |

## Required Facts

| Fact | Description |
|------|-------------|
| `effect(?ab, target\|self, ?atom)` | The bundle |
| `reaction(?have, ?incoming, ?ab)` | Combo physics for everyone (`?incoming` may be `damage` or `hostile`) |
| `weakness(?e, ?in, ?have, ?out)` | What this entity gets from `?in` (a tag or a hazard) when carrying `?have` (or `none`) |
| `onGrant(?t, ?atom)` | Optional: what storing `?t` does at once (feared pushes) |
| `behavior(?npc, ?t, ?ab, ?aim)` | Optional: an NPC that gains `?t` casts `?ab` at `source`, `self`, `here` or `there(R)`, raw |
| `vulnerable(?e, ?type)` | Optional: mooks die to one hit of that type |
| `onEnter(?r, ?ab)` | Zones and hazards (a pool soaks, a pit takes) |
| `beyond(?from, ?over, ?to)` | Push lines |

## Examples

### Example 1: A reaction replaces the incoming tag

**Given:** `tag(gob, wet)`, `reaction(wet, shocked, electrocution)` whose effects are `remove(wet)` and `grant(dead)`.

**When:** `applyAbility(player, shock, gob, react)`

**Then:** plan contains `opReact(player, gob, wet, shocked, electrocution)`, `opRemove(player, gob, wet)`, `opGrant(player, gob, dead)`, and no `opGrant(player, gob, shocked)`.

### Example 2: A push lands in a zone

**Given:** player at `ledge`, gob at `pool`, `beyond(ledge, pool, pit)`, `onEnter(pit, fall)` granting `fell`.

**When:** `applyAbility(player, gust, gob, react)`

**Then:** plan contains `opForcedMove(player, gob, pool, pit)` and `opGrant(player, gob, fell)`; gob is at the pit, fallen.

### Example 3: A blunt blow shatters the frozen

**Given:** `tag(gob, frozen)`, frozen bundles `brittle`, `reaction(brittle, blunt, shatterBlow)`.

**When:** `applyAbility(player, hammer, gob, react)` (damage(blunt), self grant(tired))

**Then:** gob is dead and no longer frozen; the player is tired.

### Example 4: A walk into water soaks

**Given:** `onEnter(pool, soak)` granting `wet`.

**When:** `walkTo(player, pool)`

**Then:** the player is at the pool, wet.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Immunity spares one atom, not the ability | A golem immune to shock, frozen so it can be moved, is pushed by an ability that shocks and pushes. |
| P2 | Reactions do not chain | A reaction that grants `shocked` to something wet stores `shocked`; no electrocution follows. |
| P3 | Steam dries | Burning on something wet removes wet and stores no burning. |
| P4 | The mover is credited | A push into the pit credits `fell` to the pusher, not the region. |
| P5 | An effect cannot be skipped | No plan drops the hammer's self-tiring to pass a later gate that needs a fresh caster. |
| P6 | A push lands in one place | With two lines from the same side, the first declared is the only landing. |
| P7 | An area hits everyone but the source | `effect(nova, area, grant(chilled))` aimed at a region chills everyone there except the caster. |
| P8 | A spill makes a zone | `spill(z)` adds `onEnter(region, z)` and everyone standing there takes `z`. |
| P9 | A purge takes a group | `purge(affliction)` removes every stored affliction and nothing else. |
| P10 | A reaction before a kill | A shield (`reaction(shielded, damage, ...)`) absorbs a blow the target is vulnerable to. |
| P11 | A weakness answers for that entity | The same tag stuns a machine, is only stored on anyone else, and kills a soaked machine. |
| P12 | A hazard takes only the weak | A gale pushes a walker and a flier into a chasm: the walker falls, the flier hovers. |
| P13 | A tag can move its bearer | `onGrant(feared, push)`: being frightened sends it running (here, into the pit). |
| P14 | A path strikes whoever stands between | A flash from the ledge to the shore sparks everyone in the pool between, and moves the caster there. |
| P15 | A hook pulls the light and is pulled by the anchored | Hooking a goblin drags it to the caster; hooking a heavy golem drags the caster to it. |
| P16 | A swap trades places | Caster and target exchange regions, and each takes what is where it lands. |
| P17 | A pull across a hazard drops it in | Hooking an imp from across a gap it is weak to: it falls into the gap. |
| P18 | A filled hazard is walked over | With a filler fallen into the gap, the walk crosses it safely. |
| P19 | Nobody walks into a live hazard | The walk has no plan while the gap is live. |
| P20 | Blockers and doors stop a walk | Nobody walks into a blocker's region (it is hit from the next one) or a closed door. |
| P21 | A taunted golem discharges on its taunter | `behavior(golem, taunted, discharge, here)`: dragged to the taunter, it discharges there, and the robot standing by is short-circuited. |
| P22 | A watched region is closed to the seen | `watches(golem, pool)`: no route into the pool, unless stealthed. |
| P23 | A blinded watcher sees nothing | `forbids(blinded, watch)`: a blinded guard's region is open. |
| P24 | Two plates open together | With a companion on one plate, stepping on the other opens the door for good. |
| P25 | One plate is not enough | Stepping on one of two plates leaves the door shut. |
