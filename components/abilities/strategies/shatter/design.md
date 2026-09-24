# Shatter

## Purpose

A recipe: soak it and freeze it. Where frozen stops the enemy (`stops(?e, frozen)`), stalling is the
finisher and the recipe ends there. Otherwise a blunt blow breaks what the freeze made brittle. The
level's physics turns wet + chilled into frozen, and blunt on brittle into a kill; the recipe only
orders the steps and assigns roles.

## Layer

strategy

## Dependencies

- `abilities/primitives/ab_acts`

## Operators

None.

## Methods

| Method | Description |
|--------|-------------|
| `shatter(?e)` | Frozen is enough: supply wet, chill from anyone else, confirm. |
| `shatter(?e)` | Otherwise: supply wet, chill and a blunt strike from anyone but the primer, confirm. |

## Rules

None.

## Required Facts

The ability layer's facts; `reaction(wet, chilled, ...)` making a composite that bundles `brittle`;
`reaction(brittle, blunt, ...)`; optional `stops(?e, frozen)`.

## Examples

### Example 1: Frozen is enough

**Given:** `tag(wader, wet)`, `stops(wader, frozen)`, the player knows `chill`.

**When:** `shatter(wader)`

**Then:** plan contains `opReact(player, wader, wet, chilled, freezeOver)`, no hammer; the wader is frozen.

### Example 2: Frozen, then broken

**Given:** the mage knows `douse`, the player `chill`, the warden `hammer`.

**When:** `shatter(gob)`

**Then:** plan contains the mage's douse, the player's chill, the warden's hammer, and `opReact(warden, gob, brittle, blunt, shatterBlow)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | A blow that cannot land | `immune(gob, blunt)` and frozen is not enough: no plan. |
| P2 | The primer neither chills nor breaks | One companion knowing douse, chill and hammer: no plan. |
