# Core Chemistry

## Purpose

The multiplicative part of the ruleset: elements change materials, elements
change entities, materials never change materials. A level declares a handful
of `reacts`, `blast`, `terrain` and `strike` facts and every combination of
skills and terrain follows from them. Reactions rewrite the world, so what one
fight consumes is gone for the next; that persistence is what makes the
second encounter depend on how the first was won.

## Layer

primitive

## Dependencies

- `core/primitives/core_world`

## Operators

| Operator | Description |
|----------|-------------|
| `opSpendCharge(?a, ?skill, ?tok)` | One use of a consumable skill. |
| `opCastRegion(?a, ?skill, ?r, ?old, ?new)` | `?a` casts on region `?r`; its feature `?old` becomes `?new`. |
| `opCastEntity(?a, ?skill, ?e, ?status)` | `?a` strikes `?e`, which takes `?status`. |
| `opStatus(?a, ?e, ?status)` | A consequence `?a` caused: `?e` takes `?status`. |

## Methods

| Method | Description |
|--------|-------------|
| `payFor(?a, ?skill)` | Free for signature/unlimited skills; else spends one token. |
| `applyToRegion(?a, ?el, ?r)` | Cast the element; the feature reacts; the blast hits exposed enemies present; the new terrain settles on everyone standing there. |
| `applyToEntity(?a, ?el, ?e)` | Direct strike on a vulnerable (snared) entity. |
| `sufferTerrain(?a, ?e, ?r)` | `?e` arriving in `?r` takes the terrain's status. |

## Rules

| Rule | Description |
|------|-------------|
| `canPay(?a, ?skill)` | Free, or a charge token exists. |
| `exposed(?e)` | Not shielded, or snared (guard dropped). |
| `vulnerable(?e)` | Snared. |

## Required Facts

| Fact | Description |
|------|-------------|
| `skillElement(?skill, ?el)` | Which element a skill carries |
| `reacts(?el, ?feat, ?new)` | Feature transformation |
| `blast(?el, ?feat, ?status)` | Effect on enemies present at the reaction |
| `terrain(?feat, ?status)` | Effect on whoever enters or stands in it |
| `strike(?el, ?status)` | Effect of a direct cast on a vulnerable target |
| `immune(?e, ?el)` | Optional |
| `signature/2`, `unlimited/1`, `charge/3` | How casts are paid for |

## Examples

### Example 1: Fire on oil

**Given:** `regionHas(pit, oil)`, `reacts(fire, oil, scorched)`, `blast(fire, oil, dead)`, an enemy `gob` at `pit`, the player at `pit` with one `ignite` charge.

**When:** `applyToRegion(player, fire, pit)`

**Then:** plan contains `opSpendCharge(player, ignite, c1)`, `opCastRegion(player, ignite, pit, oil, scorched)`, `opStatus(player, gob, dead)`; final state has `regionHas(pit, scorched)` and no `charge(player, ignite, c1)`.

### Example 2: A signature skill is free

**Given:** `signature(arcanist, freeze)`, `reacts(freeze, oil, sludge)`.

**When:** `applyToRegion(arcanist, freeze, pit)`

**Then:** plan contains `opCastRegion(arcanist, freeze, pit, oil, sludge)` and no `opSpendCharge`.

### Example 3: A strike needs a snared target

**Given:** `strike(fire, dead)`, `gob` not snared.

**When:** `applyToEntity(player, fire, gob)`

**Then:** no plan. With `status(gob, snared)` the plan contains `opCastEntity(player, ignite, gob, dead)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No charge, no cast | Without a `charge` token or a free skill there is no `applyToRegion` plan. |
| P2 | Shields turn blasts | A `shielded` enemy in the region is not given the blast status. |
| P3 | Terrain settles | After freezing oil to sludge with `terrain(sludge, snared)`, an enemy standing there is `snared`. |
