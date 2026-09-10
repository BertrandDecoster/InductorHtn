# Core Attunement

## Purpose

The Primer / Detonator chain of the GDD as a **role** rule: whoever primes
a region may not be the one who pays it off. Any companion can fill either
role - the player character and the AI companions have the same abilities
and differ only by who controls them - so no strategy built on these can
be run by one companion alone, and the team still decides who does what,
where, and with which skill.

## Layer

primitive

## Dependencies

- `core/primitives/core_world`
- `core/primitives/core_chemistry`

## Methods

| Method | Description |
|--------|-------------|
| `primer(?el, ?a)` (rule) | The first companion who can put `?el` down. |
| `prime(?el, ?r)` / `prime(?el, ?r, ?a)` | The first able companion applies the element to `?r`; the named form takes a chosen primer. |
| `detonate(?el, ?r)` / `detonate(?el, ?r, ?not)` | Any companion but `?not` applies the element to `?r`. |
| `detonateLethal(?r)` / `detonateLethal(?r, ?not)` | Any companion but `?not` blasts `?r` with a lethal element for its terrain. |
| `finish(?e)` / `finish(?e, ?not)` | Any companion but `?not` strikes a vulnerable enemy with the first affordable lethal element it is not immune to. |
| `expose(?e)` | Whoever holds a marking element drops the enemy's guard. |

## Examples

### Example 1: A companion primes

**Given:** `arcanist` holds `freeze` (signature), oil at `pit`.

**When:** `prime(freeze, pit)`

**Then:** plan contains `opCastRegion(arcanist, freeze, pit, oil, sludge)`.

### Example 2: Anyone detonates but the primer

**Given:** `arcanist` holds `ignite` with a charge; the player holds `ignite` with a charge.

**When:** `detonate(fire, pit)`, then `detonate(fire, pit, arcanist)`

**Then:** the first has a plan cast by each of them; the second only by `player`.

### Example 3: Finish a snared enemy

**Given:** `gob` snared, `strike(lightning, dead)`, player holds `lightning` with a charge.

**When:** `finish(gob)`

**Then:** plan contains `opCastEntity(player, lightning, gob, dead)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Two roles, two companions | With a single fire holder, `detonate(fire, ?r)` has a plan but `detonate(fire, ?r, ?thatHolder)` has none: the primer cannot pay off its own prime. |
| P2 | Immunity is respected | `finish` never strikes with an element the target is immune to; with only that element available it has no plan. |
