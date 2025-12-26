# Tags

## Purpose

Manage status effects (tags) on entities. Tags represent conditions like burning, frozen, stunned, etc. When certain tags combine, they produce different results (e.g., burning + wet = steam).

## Layer

primitive

## Dependencies

None (foundational component)

## Operators

| Operator | Description |
|----------|-------------|
| `opApplyTag(?entity, ?tag)` | Add a tag to an entity |
| `opRemoveTag(?entity, ?tag)` | Remove a tag from an entity |

## Methods

| Method | Description |
|--------|-------------|
| `applyTag(?entity, ?tag)` | Apply tag with combination logic. If entity has a combinable tag, both are replaced with the result. |
| `removeTag(?entity, ?tag)` | Remove a tag. No-op if tag doesn't exist. |

## Tag Combinations

Built-in combinations (can be extended per-level):

| Tag 1 | Tag 2 | Result |
|-------|-------|--------|
| burning | wet | steam |
| wet | electrified | stunned |
| frozen | burning | wet |
| electronics | electrified | disabled |

Note: Combinations are commutative (order doesn't matter).

## Required Facts

| Fact | Description |
|------|-------------|
| `hasTag(?entity, ?tag)` | Entity currently has this tag |
| `vulnerability(?entity, ?tag)` | Entity is vulnerable to this tag type |

## Parameters

No configurable parameters. Tag combinations are defined as facts.

## Examples

### Example 1: Simple tag application

**Given:**
- Entity has no tags

**When:**
- `applyTag(entity1, burning)`

**Then:**
- Plan contains: `opApplyTag(entity1, burning)`
- Final state has: `hasTag(entity1, burning)`

### Example 2: Tag combination (burning + wet = steam)

**Given:**
- `hasTag(entity1, wet)`

**When:**
- `applyTag(entity1, burning)`

**Then:**
- Plan contains: `opRemoveTag(entity1, wet)`, `opApplyTag(entity1, steam)`
- Final state has: `hasTag(entity1, steam)`
- Final state does not have: `hasTag(entity1, wet)`, `hasTag(entity1, burning)`

### Example 3: Applying same tag (no-op)

**Given:**
- `hasTag(entity1, burning)`

**When:**
- `applyTag(entity1, burning)`

**Then:**
- Plan contains: empty (no operators)
- Final state has: `hasTag(entity1, burning)`

### Example 4: Remove tag

**Given:**
- `hasTag(entity1, burning)`

**When:**
- `removeTag(entity1, burning)`

**Then:**
- Plan contains: `opRemoveTag(entity1, burning)`
- Final state does not have: `hasTag(entity1, burning)`

### Example 5: Frozen + burning = wet (ice melts)

**Given:**
- `hasTag(entity1, frozen)`

**When:**
- `applyTag(entity1, burning)`

**Then:**
- Plan contains: `opRemoveTag(entity1, frozen)`, `opApplyTag(entity1, wet)`
- Final state has: `hasTag(entity1, wet)`
- Final state does not have: `hasTag(entity1, frozen)`, `hasTag(entity1, burning)`

### Example 6: Remove nonexistent tag (no-op)

**Given:**
- Entity has no tags

**When:**
- `removeTag(entity1, burning)`

**Then:**
- Plan contains: empty (no operators)

### Example 7: Tags on different entities are independent

**Given:**
- `hasTag(entity1, burning)`, `hasTag(entity2, wet)`

**When:**
- `applyTag(entity1, wet)`

**Then:**
- entity1 gets steam (burning + wet)
- entity2 unchanged

### Example 8: Electronics + electrified = disabled

**Given:**
- `hasTag(device1, electronics)`

**When:**
- `applyTag(device1, electrified)`

**Then:**
- Plan contains: `opRemoveTag(device1, electronics)`, `opApplyTag(device1, disabled)`
- Final state has: `hasTag(device1, disabled)`
- Final state does not have: `hasTag(device1, electronics)`, `hasTag(device1, electrified)`

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No double tags | An entity cannot have the same tag twice |
| P2 | Combination replaces | After combination, neither original tag exists |
| P3 | Commutative combinations | A+B and B+A produce the same result |
