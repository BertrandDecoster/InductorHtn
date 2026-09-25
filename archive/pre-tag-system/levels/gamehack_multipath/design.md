# GameHack Multipath Level

## Purpose

Prove the GameHack stack composes broadly, not just end to end. Where `gamehack_mvp` exercises a single companion with a single strategy, this level arranges a world in which:

- All three strategies succeed independently: `wetAndElectrify`, `stunAndSlow`, `stunAndBurn`.
- All three ways of `applyTagNotPresent` (a companion skill, a location, a non-companion skill) produce plans for at least one tag.
- `defeat(gob)` returns many structurally distinct plans rather than one.

## Layer

level

## Dependencies

- `gamehack/primitives/gh_movement`
- `gamehack/primitives/gh_tags`
- `gamehack/primitives/gh_aggro`
- `gamehack/primitives/gh_skills`
- `gamehack/actions/gh_tag_application`
- `gamehack/strategies/wet_and_electrify`
- `gamehack/strategies/stun_and_slow`
- `gamehack/strategies/stun_and_burn`
- `gamehack/goals/defeat`

## World Overview

- Companions: `player`, `companionA` (waterSkill), `companionB` (fireballSkill), `companionC` (no skill).
- Enemies: `gob` (target), `teslaTower` (static, lightningSkill), `iceElemental` (iceBlastSkill).
- Locations: `arena` (where `gob` is), `forge`, `glacier`, `lakeShore`, `sea`, `volcano`.
- `lakeShore` and `sea` apply `wet`; `glacier` applies `stunned`.
- Objects that grant a skill: `volcanoShrine` (fireballSkill), `glacierShrine` (iceBlastSkill), `shoreShrine` (waterSkill).
- `fireballSkill` is `slow`, which makes `stunAndSlow` possible.

## Examples

### Example 1: wetAndElectrify

**Given:** multipath world state
**When:** `wetAndElectrify(gob)`
**Then:** 36 plans; `defeat(gob)` has plans with both `opApplyTag(wet, gob)` and `opApplyTag(electrified, gob)`

### Example 2: stunAndSlow

**Given:** two distinct companions can carry `iceBlastSkill` and `fireballSkill`
**When:** `stunAndSlow(gob)`
**Then:** 12 plans, each with `opSynchronize`

### Example 3: stunAndBurn

**Given:** stunned is reachable (the glacier, the ice elemental, or iceBlastSkill from its shrine) and burning too (companionB, or fireballSkill from the volcano shrine)
**When:** `stunAndBurn(gob)`
**Then:** 48 plans

### Example 4: Plan multiplicity

**Given:** multipath world state
**When:** `defeat(gob)`
**Then:** 96 distinct plans (12 + 36 + 48), each ending with `opApplyTag(dead, gob)`

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Companion-skill way | Some plan wets gob with companionA's waterSkill (it also lands `clean`) |
| P2 | Location way | Some plans wet gob by luring it to `lakeShore`, others to `sea` |
| P3 | Agent-skill way (electrified) | Some plan electrifies gob with the static tesla tower's lightningSkill |
| P4 | Location and agent ways (stunned) | At the glacier, gob gets stunned by the location or by the ice elemental's skill |
| P5 | State after `wetAndElectrify(gob)` | gob is wet and electrified |
| P6 | State after `stunAndBurn(gob)` | gob is stunned and burning |
| P7 | Skill objects in `stunAndSlow` | Some plan has `opSwapSkill` or `opGetSkill` with `opSynchronize` |
