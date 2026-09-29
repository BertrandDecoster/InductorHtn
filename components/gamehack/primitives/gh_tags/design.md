# GH Tags

## Purpose

An agent arriving at a location gets its tag (`landLocationTag`). A skill's tags land on its target, combining with the location tag the target carries. A companion holding the skill and standing with the target uses it (`useSkillOnTarget`); each of its tags lands through `landSkillTag`:

| Target's tag + skill tag | Result |
|---|---|
| `wet` + `electrified` | in water, everyone there is `electrified` (the location stays wet); elsewhere, the target alone |
| `oil` + `burning` | on the oil, the oil becomes `burning` and everyone there is `burning`; elsewhere, the target alone |
| `wet` or `ice` + `chilled` | the target alone is `stunned` |
| anything else | the tag just lands on the target |

Each combo defeats (`dead`) the enemies there that are `vulnerableToLocationCombo` it; a skill alone never does. A world lists the tag of every agent that starts on a tagged location. The component also holds the physics (`locationCombo` facts), `agent/1` (every companion, neutral and enemy) and the tag types.

## Layer

primitive

## Dependencies

None.

## Operators

| Operator | Description |
|----------|-------------|
| `opUseSkill(?a, ?s, ?t)` | No state change; the engine plays the skill |
| `opApplyTag(?tag, ?t)` | Adds `hasTag(?t, ?tag)` |
| `opAddLocationTag(?tag, ?l)`, `opRemoveLocationTag(?tag, ?l)` | Adds or removes `locationCanApplyTag(?l, ?tag)` |
| `opTagAlreadyOnTarget(?tag, ?t)` | Already true: no state change |

## Methods

| Method | Description |
|--------|-------------|
| `useSkillOnTarget(?a, ?s, ?t)` | `?a`, holding `?s` and standing with `?t`, uses it; each tag lands |
| `applySkillTags(?s, ?t)` | Each of the skill's tags lands (`landSkillTag`) |
| `landSkillTag(?tag, ?t)` | A skill's tag lands, with the combo on `?t`'s tags |
| `landLocationTag(?x, ?l)` | `?x`, arriving at `?l`, gets its tag, if it has one |
| `landTag(?tag, ?t)` | `?t` has the tag, unless immune |
| `tagEveryoneAt(?tag, ?l)` | Every agent at `?l` has the tag |
| `defeatVulnerable(?e, ?base, ?tag)`, `defeatVulnerableAt(?base, ?tag, ?l)` | The enemies vulnerable to that combo (`?e`, or everyone at `?l`) are `dead` |

## Required Facts

| Fact | Description |
|------|-------------|
| `hasSkill(?a, ?s)`, `skillAppliesTag(?s, ?tag)` | Skills and their tags |
| `at(?x, ?l)`, `locationCanApplyTag(?l, ?tag)` | Where agents stand, and the location's one tag |
| `companion/1`, `enemy/1`, `neutral/1` | The agents |
| `immune(?t, ?tag)`, `hasTag(?t, ?tag)`, `vulnerableToLocationCombo(?e, ?base, ?tag)` | Optional |

## Examples

An agent that starts in the lake is wet, in the kitchen has oil, on the rink has ice.

### Example 1: No combo, the tag just lands

**Given:** pyro (fireballSkill: burning) and gob in the hall (no location tag)
**When:** `useSkillOnTarget(pyro, fireballSkill, gob)`
**Then:** the only plan is `opUseSkill(pyro, fireballSkill, gob), opApplyTag(burning, gob)`

### Example 2: Every tag of the skill lands

**Given:** waterSkill applies `wet` and `clean`
**When:** it is used on gob in the hall
**Then:** `opApplyTag(wet, gob), opApplyTag(clean, gob)`

### Example 3: Wet + electrified

**Given:** volt (lightningSkill), gob and orc at the wet lake; `vulnerableToLocationCombo(gob, wet, electrified)`
**When:** `useSkillOnTarget(volt, lightningSkill, gob)`
**Then:** the only plan electrifies volt, gob and orc, then `opApplyTag(dead, gob)`; the lake stays wet

### Example 4: Oil + burning

**Given:** pyro, gob and orc in the kitchen, which holds oil; both enemies vulnerable to oil + burning
**When:** `useSkillOnTarget(pyro, fireballSkill, gob)`
**Then:** `opRemoveLocationTag(oil, kitchen), opAddLocationTag(burning, kitchen)`, pyro, gob and orc burning, both enemies dead

### Example 5: Chilled on ice

**Given:** frost (frostSkill: chilled), gob and orc on the ice rink; gob vulnerable to ice + chilled
**When:** `useSkillOnTarget(frost, frostSkill, gob)`
**Then:** the only plan is `opUseSkill(frost, frostSkill, gob), opApplyTag(stunned, gob), opApplyTag(dead, gob)` (orc is untouched)

### Example 6: Chilled in water, not vulnerable

**Given:** frost and gob in the lake, no vulnerability
**When:** `useSkillOnTarget(frost, frostSkill, gob)`
**Then:** gob is stunned, not dead

### Example 7: Immune and present tags

**Given:** Example 3 with `immune(orc, electrified)` and `hasTag(gob, electrified)`
**When:** volt uses lightningSkill on gob
**Then:** volt is electrified, `opTagAlreadyOnTarget(electrified, gob)`, orc gets nothing

### Example 8: The user holds the skill and stands with the target

**Given:** pyro in the hall, gob in the lake
**When:** `useSkillOnTarget(pyro, fireballSkill, gob)`, or frost (who lacks fireballSkill) tries
**Then:** no plan

### Example 9: Arriving

**Then:** `landLocationTag(orc, kitchen)` is `opApplyTag(oil, orc)`; `landLocationTag(orc, hall)` is empty

### Example 10: Wet, off the water

**Given:** volt, gob (wet, vulnerable to wet + electrified) and orc in the hall
**When:** `useSkillOnTarget(volt, lightningSkill, gob)`
**Then:** gob alone is electrified, and dead

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No duplicate tags | A tag already present is not added twice |
| P2 | Skill alone never defeats | Without a location combo, a vulnerable enemy is not defeated |
