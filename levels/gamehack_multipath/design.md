# GameHack Multipath Level

## Purpose

Prove the decomposed GameHack stack composes broadly, not just end-to-end. Where
`gamehack_mvp` exercised a single ally with a single strategy, this level arranges
a world in which:

- All three damage strategies succeed independently: `wetAndElectrocute`,
  `stunAndSlowSkill`, `stunAndBurn`.
- All three paths of `applyTagNotPresent` (ally skill, location, non-ally mob skill)
  produce viable plans for at least one tag.
- `planToDamage(gob)` returns many structurally distinct plans rather than one.

## Layer

level

## Dependencies

- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_tags`
- `gamehack/primitives/gh_aggro`
- `gamehack/primitives/gh_skills`
- `gamehack/actions/gh_tag_application`
- `gamehack/strategies/wet_and_electrocute`
- `gamehack/strategies/stun_and_slow_skill`
- `gamehack/strategies/stun_and_burn`
- `gamehack/goals/plan_to_damage`

## World Overview

- Allies: `player`, `companionA` (waterSkill), `companionB` (fireballSkill),
  `companionC` (no skill).
- Enemies: `gob` (target), `teslaTower` (static, lightningSkill), `iceElemental`
  (iceBlastSkill).
- Locations: `arena` (where `gob` lives), `forge`, `glacier`, `lakeShore`, `sea`,
  `volcano`.
- `lakeShore` and `sea` apply `wet`; `glacier` applies `ice`.
- Skill acquisition sites: `volcano`→`fireballSkill`, `glacier`→`iceBlastSkill`,
  `lakeShore`→`waterSkill`.
- `fireballSkill` has the `slow` modifier, which unlocks `stunAndSlowSkill`.

## Examples

### Example 1: `wetAndElectrocute(gob)` is viable

**Given:** multipath world state
**When:** `planToDamage(gob)` is planned
**Then:** at least one plan contains both `opApplyTag(wet, gob)` and
`opApplyTag(electrocute, gob)`.

### Example 2: `stunAndSlowSkill(gob)` is viable

**Given:** two distinct allies can carry `iceBlastSkill` and `fireballSkill`
**When:** `planToDamage(gob)` is planned
**Then:** at least one plan contains `opSynchronize` (the hallmark of the
simultaneous two-ally strategy).

### Example 3: `stunAndBurn(gob)` is viable

**Given:** ice and fire tags both reachable (via glacier / iceElemental /
iceBlastSkill learning, and fireballSkill direct or learned at volcano)
**When:** `planToDamage(gob)` is planned
**Then:** at least one plan contains both `opApplyTag(ice, gob)` and
`opApplyTag(fire, gob)`.

### Example 4: Plan multiplicity

**Given:** multipath world state
**When:** `planToDamage(gob)` is planned with `FindAllPlans`
**Then:** at least **10** distinct plans are returned.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Ally-skill dispatcher path | At least one plan applies `wet` via an ally's `waterSkill`, detectable by the `opApplyTag(clean, gob)` side-effect (only `waterSkill` carries the `clean` tag). |
| P2 | Location dispatcher path | At least one plan applies `wet` by luring `gob` to `lakeShore` or `sea` (contains `bringMobToLocation`). |
| P3 | Mob-skill dispatcher path (electrocute) | At least one plan applies `electrocute` by bringing `gob` together with `teslaTower` (contains `bringMobsTogether`). |
| P4 | Mob-skill dispatcher path (ice) | At least one plan applies `ice` by bringing `gob` together with `iceElemental`. |
| P5 | State after `wetAndElectrocute(gob)` | Running that strategy leaves `hasTag(gob, wet)` and `hasTag(gob, electrocute)` in state. |
| P6 | State after `stunAndBurn(gob)` | Running that strategy leaves `hasTag(gob, ice)` and `hasTag(gob, fire)` in state. |
| P7 | Skill acquisition in `stunAndSlowSkill` | At least one plan contains `opSwapSkill` or `opGetSkill` paired with `opSynchronize`, proving the learn-a-skill path fires. |
