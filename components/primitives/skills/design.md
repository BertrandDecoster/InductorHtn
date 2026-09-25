# Skills

## Purpose

A companion gets ready to use a skill (holds it and stands with the target), gets a skill it
lacks from an object (`canGetSkillFrom(?o, ?s)`; the object stays), and uses a skill on a
target in the same location: each of the skill's tags lands through `landSkillTag` (tags
primitive), with the location's combo. The verbs are copied from `Examples/Combos.htn`.

## Layer

primitive

## Dependencies

- `primitives/locomotion` (`goToSameLocation`), `primitives/tags` (`landSkillTag`)

## Methods

| Method | Description |
|--------|-------------|
| `prepareToUseSkill(?a, ?s, ?t)` | holds `?s` and walks to `?t`; or walks to an object that grants it, learns it, then walks to `?t` |
| `getSkillFrom(?a, ?o, ?s)` | standing at `?o`, learns `?s`: it replaces the current skill (`opSwapSkill`) or is the first (`opGetSkill`) |
| `useSkillOnTarget(?a, ?s, ?t)` | `?a`, holding `?s` and standing with `?t`, uses it (`opUseSkill`); its tags land |
| `applySkillTags(?s, ?t)` | `landSkillTag` for each tag of the skill |

## Operators

| Operator | Effect |
|----------|--------|
| `opUseSkill(?a, ?s, ?t)` | no state change; the engine plays the skill |
| `opGetSkill(?a, ?s)`, `opSwapSkill(?a, ?old, ?s)` | learns a skill |

## Examples

pyro (fireballSkill: burning; stormSkill: burning and electrified), frost (frostSkill:
chilled) and page (no skill) at the camp; a shrine at the forge grants fireballSkill; gob at
the hut, imp at the camp.

### Example 1: Holds the skill
**Then:** `prepareToUseSkill(pyro, fireballSkill, gob)` is `opMoveTo(pyro, camp, hut)`

### Example 2: Swaps it at the object
**Then:** frost walks to the forge, swaps frostSkill for fireballSkill, walks to the hut

### Example 3: Learns a first skill
**Then:** page walks to the forge, `opGetSkill(page, fireballSkill)`, walks to the hut

### Example 4: Same location only
**Then:** pyro can't use a skill on gob from the camp; on imp it lands `burning`

### Example 5: Every tag lands
**Then:** stormSkill on imp: `opApplyTag(burning, imp), opApplyTag(electrified, imp)`

## Properties

### P1: Learning replaces the companion's skill
