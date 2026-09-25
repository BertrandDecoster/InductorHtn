# Tags

## Purpose

A skill's tag lands on an agent (`hasTag(?who, ?tag)`), and combines with the one tag of the
location the agent stands on (`locationCanApplyTag(?l, ?tag)`). The physics is three location
combos (`locationCombo/2`); there are no other combinations. Each combo defeats the enemies
there that are `vulnerableToLocationCombo` it; the skill alone never does.

| Location + skill tag | Result |
|---|---|
| `wet` + `electrified` | everyone there is `electrified`; the location stays wet |
| `oil` + `burning` | everyone there is `burning`; the oil becomes `burning` |
| `wet` or `ice` + `chilled` | the target alone is `stunned` |

The verbs are copied from `Examples/Combos.htn`, the reference.

## Layer

primitive

## Dependencies

None.

## Methods

| Method | Description |
|--------|-------------|
| `landSkillTag(?tag, ?t)` | one method per combo, and one for "no combo where `?t` stands": the tag just lands |
| `landTag(?tag, ?t)` | `?t` has the tag (`opTagAlreadyOnTarget` if it had it); nothing on an immune agent |
| `tagEveryoneAt(?tag, ?l)` | every agent at `?l` (companion, neutral or enemy) gets the tag |
| `defeatVulnerable(?e, ?base, ?tag)` | `?e` is dead if it is vulnerable to the combo |
| `defeatVulnerableAt(?base, ?tag, ?l)` | the same for every enemy at `?l` |

`agent(?x)` is a rule here: a companion, a neutral or an enemy.

## Operators

| Operator | Effect |
|----------|--------|
| `opApplyTag(?tag, ?t)` | adds `hasTag` |
| `opAddLocationTag(?tag, ?l)`, `opRemoveLocationTag(?tag, ?l)` | add or remove `locationCanApplyTag` |
| `opTagAlreadyOnTarget(?tag, ?t)` | already true (no state change) |

## Examples

The world: a wet `pond` (companion ward, enemies gob and imp; imp vulnerable to wet +
electrified, gob to wet + chilled), an oil `pit` (companion sol, enemies orc and rat, a barrel;
orc vulnerable to oil + burning), an ice `rink` (yak vulnerable to ice + chilled, elk), and a
plain `field` (ant, immune to burning).

### Example 1: Electrified in water
**When:** `landSkillTag(electrified, gob)` **Then:** ward, gob and imp are electrified; imp is dead

### Example 2: Burning on oil
**When:** `landSkillTag(burning, orc)` **Then:** the pit's oil becomes burning; sol, orc and rat
burn (not the barrel); orc is dead

### Example 3: Chilled in water
**When:** `landSkillTag(chilled, gob)` **Then:** gob alone is stunned, and dead

### Example 4: Chilled on ice
**Then:** yak is stunned and dead; elk is only stunned

### Example 5: No combo
**When:** `landSkillTag(electrified, orc)` (electrified on oil) **Then:** `opApplyTag(electrified, orc)`

### Example 6: Immune
**When:** `landSkillTag(burning, ant)` **Then:** the empty plan

### Example 7: Already there
**Then:** `landTag(burning, elk)` is `opTagAlreadyOnTarget(burning, elk)`

## Properties

### P1: The skill alone never defeats
### P2: Only oil changes its tag
