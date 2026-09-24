# Neutralize

## Purpose

The goal: take an enemy out of the fight. Its methods are the recipes, as plain alternatives, so every
recipe that works is a different plan (`FindAllPlans` enumerates them). The specialized recipes come
first. The last is a generic one-step improvisation: a tag that stops the enemy, or damage it is
vulnerable to. This follows Killzone's rule that "the generic branch is always available". Every
recipe ends by confirming the simulated world, so a recipe the level's physics doesn't support finds
no plan instead of a wrong one.

## Layer

goal

## Dependencies

- `abilities/strategies/conduct`
- `abilities/strategies/shatter`
- `abilities/strategies/into_the_pit`
- `abilities/strategies/ignite`
- `abilities/strategies/exploit`

## Operators

None.

## Methods

| Method | Description |
|--------|-------------|
| `neutralize(?e)` | Already out: nothing. A guard up (group `guard`: shield, stealth, invulnerability): `unset` it, then neutralize again. Else each recipe is a separate plan: `exploit` (its weakness), `intoThePit`, `conduct`, `shatter`, `ignite`, `improvise`. |
| `improvise(?e)` | One cast: a tag with `stops(?e, ?t)`, or damage `?e` is vulnerable to. |

## Rules

None.

## Required Facts

The ability layer's facts.

## Examples

### Example 1: Already out

**Given:** `tag(gob, fell)`.

**When:** `neutralize(gob)`

**Then:** an empty plan.

### Example 2: Each recipe is a plan

**Given:** the wet wader in the pool, `beyond(ledge, pool, pit)`, `stops(wader, frozen)`; the player knows `shock` and `chill`, the mage `gust`.

**When:** `neutralize(wader)`

**Then:** at least three plans: electrocution, a freeze, and the mage's push into the pit.

### Example 3: Improvise on a mook

**Given:** `vulnerable(gob, fire)`, the player knows `bolt` (damage(fire)).

**When:** `neutralize(gob)`

**Then:** plan contains `opCast(player, bolt, gob)` and `opGrant(player, gob, dead)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | A tag that stops is one step | `stops(gob, stunned)` and a stun ability: `improvise` grants it. |
| P2 | Nothing works, no plan | A heavy golem and only a douse: no plan. |
| P3 | A guard comes off first | On the catalogue, a stealthed treant: a flashbang on its region strips the stealth, then fire plays its weakness. |
