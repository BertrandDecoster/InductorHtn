# Defeat

## Purpose

Goal: an enemy is out of the fight (`hasTag(?t, dead)`). A menu of strategies, as in
`Examples/Combos.htn`: every strategy that works gives its own plan. The location combo each
strategy lands defeats the enemy, so the goal adds nothing after it.

## Layer

goal

## Dependencies

- `primitives/locomotion`, `primitives/tags`, `primitives/aggro`, `primitives/skills`
- `strategies/wet_and_freeze`, `strategies/oil_and_burn`

## Methods

| Method | Description |
|--------|-------------|
| `defeat(?t)` | `wetAndFreeze(?t)` or `oilAndBurn(?t)`; no plan for an enemy already dead |

## Examples

pyro (fireballSkill: burning) and frost (frostSkill: chilled) at the camp; oil in the storage,
water in the corridor; the enemies at the hut.

### Example 1: Vulnerable to oil + burning
**Then:** one plan: frost lures guard1 onto the oil, pyro sets it burning

### Example 2: Vulnerable to wet + chilled
**Then:** one plan: pyro lures guard2 into the water, frost chills it

### Example 3: Vulnerable to both: the menu
**Then:** two plans, one per strategy

### Example 4: Already dead, no plan
### Example 5: Vulnerable to no combo, no plan

## Properties

### P1: Every plan ends with the enemy dead
