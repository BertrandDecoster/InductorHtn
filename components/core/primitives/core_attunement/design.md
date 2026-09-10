# Core Attunement

## Purpose

What a fight needs - an enemy blasted dead, struck dead, or exposed - and
the role rule that makes meeting it a team effort: whoever primes a region
may not be the one who pays it off. Any companion can fill either role;
the player character and the AI companions have the same abilities and
differ only by who controls them. Methods here say *what would work* (a
lethal reaction with the feature present, a strike element the enemy is
not immune to) and hand the ingredients to `core_chemistry`, which finds
who holds them.

## Layer

primitive

## Dependencies

- `core/primitives/core_world`
- `core/primitives/core_chemistry`

## Methods

| Method | Description |
|--------|-------------|
| `primer(?el, ?a)` (rule) | The first companion who can put `?el` down. |
| `prime(?el, ?r)` / `prime(?el, ?r, ?a)` | Put an element on a region: chemistry picks the holder, or the named primer does it. |
| `blastDeadAt(?r)` / `blastDeadAt(?r, ?not)` | The need "everything exposed in `?r` is blasted dead": some element reacts lethally with the feature there; anyone but `?not` casts it. |
| `strikeDead(?e)` / `strikeDead(?e, ?not)` | The need "`?e` is struck dead": a lethal strike element it is not immune to; anyone but `?not` casts it. |
| `expose(?e)` | The need "`?e` takes blasts": already exposed, or a marking element drops its guard. |

## Examples

### Example 1: A companion primes

**Given:** `arcanist` holds `freeze` (signature), oil at `pit`.

**When:** `prime(freeze, pit)`

**Then:** plan contains `opCastRegion(arcanist, freeze, pit, oil, sludge)`.

### Example 2: Anyone pays off but the primer

**Given:** `arcanist` holds `ignite` with a charge; the player holds `ignite` with a charge; oil at `pit`.

**When:** `blastDeadAt(pit)`, then `blastDeadAt(pit, arcanist)`

**Then:** the first has a plan cast by each of them; the second only by `player`.

### Example 3: Strike a snared enemy dead

**Given:** `gob` snared, `strike(lightning, dead)`, player holds `lightning` with a charge.

**When:** `strikeDead(gob)`

**Then:** plan contains `opCastEntity(player, lightning, gob, dead)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Two roles, two companions | With a single fire holder, `blastDeadAt(?r)` has a plan but `blastDeadAt(?r, ?thatHolder)` has none: the primer cannot pay off its own prime. |
| P2 | Immunity is respected | `strikeDead` never strikes with an element the target is immune to; with only that element available it has no plan. |
