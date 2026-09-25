# Tags

## Purpose

Tags are the status of agents (`hasTag(?who, ?tag)`) and of locations
(`locationCanApplyTag(?l, ?tag)`). Two tags on the same agent or location can combine
(`tagCombines(?a, ?b, ?new)`): whatever lands a tag ends with `combineTags`, which replaces
combining pairs until none is left.

Two scales. A skill used on a location changes the location only when one of its tags reacts
(burning an oily location leaves it burning; a fire spell on plain ground does nothing). When
the location's tag changes, every agent standing there (companion, neutral or enemy) gets the
location's tags. Skills that hit every agent on a location directly ("strong" skills) are not
implemented yet.

## Layer

primitive

## Dependencies

None.

## Methods

| Method | Description |
|--------|-------------|
| `useLocationToApplyTag(?l, ?tag, ?t)` | the location's tag lands on `?t`, who stands there, then `combineTags(?t)`; `opTagAlreadyOnTarget` if it has it; never on an immune agent |
| `useSkillOnLocation(?a, ?s, ?l)` | `?a` uses `?s` on `?l` (the engine handles range); every tag of the skill lands on the location |
| `applySkillTagsToLocation(?s, ?l)` | `applyTagToLocation` for each tag the skill applies |
| `applyTagToLocation(?tag, ?l)` | if a tag of `?l` reacts to `?tag`: add it, `combineTags(?l)`, then `applyLocationTagsToAgents(?l)`; otherwise nothing |
| `applyLocationTagsToAgents(?l)` | every agent at `?l` gets each location tag it lacks (and isn't immune to), each landing followed by `combineTags` on that agent |
| `combineTags(?x)` | on an agent or a location: while two of its tags combine, remove both and add the result (unless the result is already held as a third tag) |

`agent(?x)` is a rule here: a companion, a neutral or an enemy.

## Operators

| Operator | Effect |
|----------|--------|
| `opApplyTag(?tag, ?t)`, `opRemoveTag(?tag, ?t)` | add or remove `hasTag` |
| `opUseSkill(?a, ?s, ?target)` | no state change; the engine plays the skill |
| `opAddLocationTag(?tag, ?l)`, `opRemoveLocationTag(?tag, ?l)` | add or remove `locationCanApplyTag` |
| `opTagAlreadyOnTarget(?tag, ?t)` | already true (no state change) |

## Combinations

| A | B | Become |
|---|---|--------|
| burning / wet | wet / burning | steam |
| wet / electrified | electrified / wet | stunned |
| frozen / burning | burning / frozen | wet |
| electronics / electrified | electrified / electronics | disabled |
| oily | burning | burning |
| oily / wet | frozen | frozen |

## Examples

### Example 1: wet + burning = steam
**Then:** `combineTags(gob)` is `opRemoveTag(wet, gob), opRemoveTag(burning, gob), opApplyTag(steam, gob)`

### Example 2: frozen + burning = wet

### Example 3: The result is already a third tag
**Given:** wet, burning and steam **Then:** wet and burning are removed, nothing is added

### Example 4: The result is one of the pair (oily + burning = burning)
**Then:** both are removed, burning is added back

### Example 5: Nothing combines
**Then:** the empty plan

### Example 6: A location combines
**Given:** `storage` oily and burning **Then:** it is left burning

### Example 7: Igniting an oily location
**Given:** oily `storage` holding `gob`, `warden` (frozen) and a barrel (not an agent); `pyro` holds igniteSkill (burning)
**When:** `useSkillOnLocation(pyro, igniteSkill, storage)`
**Then:** the storage burns; warden gets burning (frozen + burning = wet, then wet + burning =
steam, then burning again) and so does gob; the barrel gets nothing

### Example 8: Plain ground doesn't burn
**When:** `useSkillOnLocation(pyro, igniteSkill, field)` **Then:** only `opUseSkill`

### Example 9: A location's tag lands on an agent
**Given:** a wet `lake`; gob burning, imp already wet, ox immune to wet
**Then:** gob ends with steam; imp: `opTagAlreadyOnTarget(wet, imp)`; ox: no plan

### Example 10: electronics + electrified = disabled

## Properties

### P1: After combineTags, no two tags combine
frozen + burning + electrified ends as stunned.

### P2: wet + electrified gives stunned whichever landed first
