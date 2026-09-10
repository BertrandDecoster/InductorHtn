# Core Attunement

## Purpose

The Primer / Detonator chain of the GDD, with the player as the required
link. A companion primes; the player detonates or finishes. No strategy built
on these can be run by companions alone, and the player still decides where
(the region) and with what (the skill), so the requirement is a decision,
not a mandatory button.

## Layer

primitive

## Dependencies

- `core/primitives/core_world`
- `core/primitives/core_chemistry`

## Methods

| Method | Description |
|--------|-------------|
| `prime(?el, ?r)` | The first companion holding the element applies it to `?r`; failing that, the player. |
| `detonate(?el, ?r)` | The player applies the element to `?r`. |
| `finish(?e)` | The player strikes a vulnerable enemy with the first affordable lethal element it is not immune to. |

## Examples

### Example 1: A companion primes

**Given:** `arcanist` holds `freeze` (signature), oil at `pit`.

**When:** `prime(freeze, pit)`

**Then:** plan contains `opCastRegion(arcanist, freeze, pit, oil, sludge)`.

### Example 2: Only the player detonates

**Given:** `arcanist` also holds `ignite` with a charge; the player holds `ignite` with a charge.

**When:** `detonate(fire, pit)`

**Then:** every plan casts as `player`; none as `arcanist`.

### Example 3: Finish a snared enemy

**Given:** `gob` snared, `strike(lightning, dead)`, player holds `lightning` with a charge.

**When:** `finish(gob)`

**Then:** plan contains `opCastEntity(player, lightning, gob, dead)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No player skill, no detonation | If the player has no skill carrying the element, `detonate` has no plan even when a companion does. |
| P2 | Immunity is respected | `finish` never strikes with an element the target is immune to; with only that element available it has no plan. |
