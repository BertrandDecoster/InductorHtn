# Ab Acts

## Purpose

The middle layer: the fixed-depth acts that recipes are built from. Each act answers one need with
one cast: "?e carries ?t", "?e is in ?r", "?e takes ?type damage". It binds who does it at the leaf,
as the answer. An act never recurses to create its own prerequisites. A recipe states every step in
order, so every decomposition is finite (Erol, Hendler & Nau: acyclic methods mean bounded depth). A
generic `achieve(tag)` that searched the reaction table backwards would be GOAP inside an HTN, with
neither GOAP's heuristic nor the HTN's pruning.

Cooperation is a role rule, not an identity rule. Every act comes in a form that takes `?not`, the
companion excluded from it, so the primer cannot also deliver the pay-off. Anyone can fill any role.

## Layer

primitive

## Dependencies

- `abilities/primitives/ab_casting`

## Operators

None. Acts cast; the physics below records what happens.

## Methods

| Method | Description |
|--------|-------------|
| `inflictAs(?a, ?t, ?e)` / `inflict(?t, ?e, ?not)` | Someone casts an ability whose target effect grants `?t`. |
| `placeAs(?a, ?e, ?r)` / `place(?e, ?r, ?not)` | Someone pushes `?e` into `?r` from the side a `beyond/3` line starts. |
| `strike(?type, ?e, ?not)` | Someone deals `?type` damage to `?e`. |
| `primeAs(?a, ?t, ?e)` | `?a` makes `?e` carry `?t`: a cast, or a push into a zone that grants it. |
| `supply(?p, ?t, ?e)` | The supplier found by `supplier/3` does its part (nothing if `?t` is already there). |
| `confirmStopped(?e)` | Only succeeds if `?e` is out. Recipes end with it (GTPyhop's verify step). |
| `deliver(?in, ?e, ?not)` | `?in` lands on `?e`: cast as a tag, or dealt as damage. |
| `combo(?have, ?in, ?e)` | The shape of most combos: a supplier of `?have`, someone else delivers `?in`, confirm. |
| `dislodge(?e)` | Someone moves `?e` out of where it stands, any way. |
| `unset(?t, ?e)` | Someone takes `?t` off `?e` - strips it, or pops it with what it reacts to (aimed at the region when `?e` cannot be aimed at) - and confirms it is gone. |

## Rules

| Rule | Description |
|------|-------------|
| `grants(?ab, ?t)` / `zoneFor(?r, ?t)` | Which abilities, and which regions, put `?t` on a target. |
| `canInflict(?a, ?ab, ?t, ?e)` / `canStrike(?a, ?ab, ?type, ?e)` | `?a` knows such an ability and is ready. |
| `placement(?a, ?ab, ?from, ?e, ?r)` | `?a` can push `?e` into `?r` standing at `?from`. |
| `canPrime(?a, ?t, ?e)` | Either of the above for `?t`. |
| `supplier(?p, ?t, ?e)` | `none` if `?e` has `?t`; else one answer per companion who can prime it. |
| `dropFor(?r, ?e)` | A region whose arrival stops `?e` (a pit). |
| `grants(?ab, ?t)` | Includes the atoms of a composite it grants, `area` grants, and what a zone it spills grants. |
| `strips(?ab, ?t)` / `pops(?ab, ?t)` / `canUnset(...)` | `remove`/`purge`; or an incoming that `?t` reacts to by going away. |

## Required Facts

The facts of `ab_tags`, `ab_effects` and `ab_casting`. Nothing new.

## Examples

### Example 1: An act excludes a companion

**Given:** the player and the mage both know `shock`.

**When:** `inflict(shocked, gob, player)`

**Then:** plan contains `opCast(mage, shock, gob)` and no `opCast(player, shock, gob)`.

### Example 2: A push from the right side

**Given:** `beyond(ledge, pool, pit)`, gob at `pool`, the player at `ledge` knowing `gust`.

**When:** `place(gob, pit, none)`

**Then:** plan contains `opCast(player, gust, gob)`, `opForcedMove(player, gob, pool, pit)`, `opGrant(player, gob, fell)`.

### Example 3: A zone primes

**Given:** tender at `slick`, `beyond(ledge, slick, pool)`, the pool soaks.

**When:** `primeAs(player, wet, tender)`

**Then:** a plan pushes the tender into the pool, which makes it wet.

### Example 4: What is there needs no supplier

**Given:** `tag(gob, wet)`.

**When:** `supply(none, wet, gob)`

**Then:** an empty plan.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | An act never makes its own prerequisites | `place` on a golem immune to forced movement has no plan; unbalancing it first is a recipe's job. |
| P2 | One supplier per companion, each means a plan | Two companions who can douse, one of whom can also push into the pool: three plans. |
| P3 | A recipe is confirmed against the world | `confirmStopped` on an enemy still standing has no plan. |
| P4 | A combo names its halves | `combo(wet, shocked, gob)`: either companion primes, the other delivers. |
| P5 | Unset takes a tag off | `unset(shielded, gob)` casts a stripping ability and confirms the shield is gone. |
| P6 | Dislodge moves it any way | `dislodge(gob)`: a push, a pull, a hook or a swap - anything that leaves it elsewhere. |
