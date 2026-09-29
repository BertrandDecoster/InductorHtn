# Defeat

## Purpose

Goal: take an enemy out of the fight. A menu of strategies, one plain method each, so `FindAllPlans` returns one plan per strategy (and per binding) that works: `wetAndFreeze`, `oilAndBurn`, `stunAndSlow`. The two location-combo strategies defeat a vulnerable enemy themselves (the combo adds `dead`); `stunAndSlow` is followed by `landTag(dead, ?t)` (its slow skill may already have landed a combo that defeated `?t`). An enemy that already has `dead` has no plan.

## Layer

goal

## Dependencies

- `gamehack/strategies/wet_and_freeze` (wetAndFreeze)
- `gamehack/strategies/oil_and_burn` (oilAndBurn)
- `gamehack/strategies/stun_and_slow` (stunAndSlow)

## Methods

| Method | Description |
|--------|-------------|
| `defeat(?t)` | Enemy `?t`, not yet dead, is taken out by one of the strategies |

## Required Facts

| Fact | Description |
|------|-------------|
| `enemy(?t)` | Target must be an enemy |
| `hasTag(?t, dead)` | Already out of the fight (optional) |

## Examples

Same world as the strategies: player (iceBlastSkill: stunned), frost (frostSkill: chilled), pyro (fireballSkill: burning, slow) at camp; gob at the hut; a wet lake, an ice rink, a kitchen with oil.

### Example 1: All three strategies

**Given:** gob vulnerable to wet + chilled and to oil + burning
**When:** `defeat(gob)`
**Then:** 5 plans: wetAndFreeze with player or pyro luring (frost chills), oilAndBurn with player or frost luring (pyro burns), and stunAndSlow (player and pyro)

### Example 2: Only stunAndSlow

**Given:** gob vulnerable to no combo
**When:** `defeat(gob)`
**Then:** the only plan is stunAndSlow, then `opApplyTag(dead, gob)`

### Example 3: Non-enemy fails

**Given:** no `enemy(player)`
**When:** `defeat(player)`
**Then:** no plan

### Example 4: Already dead

**Given:** `hasTag(gob, dead)`
**When:** `defeat(gob)`
**Then:** no plan

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Ends dead | Every plan leaves `?t` with `dead` |
| P2 | Two companions | In every plan, two different companions act |
