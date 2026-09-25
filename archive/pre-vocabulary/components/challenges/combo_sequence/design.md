# combo_sequence

## Purpose

Insight-class challenge: agent must apply N effects to a target in the
correct order (determined by `comboStep` facts). Models tag combos, skill
rotations, and puzzle solutions where sequence matters.

The correct order is encoded as `comboStep(effect, N)` facts. Effects
already present are skipped (idempotent). Supports 2-step and 3-step
combos.

## Layer

challenges

## Dependencies

None (self-contained)

## Operators

| Operator | Description |
|----------|-------------|
| `opApplyEffect(?target, ?effect)` | Apply one effect to target. Deletes `needsEffect(?target, ?effect)`, adds `hasEffect(?target, ?effect)`. |

## Methods

| Method | Description |
|--------|-------------|
| `applyEffect(?target, ?effect)` | Apply one effect, skipping if already present. |
| `executeCombo(?target)` | Execute all combo steps in order. Handles 2-step and 3-step combos. |

## Required Facts

| Fact | Description |
|------|-------------|
| `needsEffect(?target, ?effect)` | Effect must be applied to target to complete the combo |
| `comboStep(?effect, ?stepN)` | Effect belongs at position N in the combo sequence |
| `hasEffect(?target, ?effect)` | Effect is already present on target (used for idempotency check) |

## Examples

### Example 1: Two-step combo in correct order

**Given:**
- `needsEffect(boss, wet)`, `comboStep(wet, 1)`
- `needsEffect(boss, electrocute)`, `comboStep(electrocute, 2)`

**When:**
- `executeCombo(boss)`

**Then:**
- Plan contains: `opApplyEffect(boss, wet)`, then `opApplyEffect(boss, electrocute)`
- Final state has: `hasEffect(boss, wet)`, `hasEffect(boss, electrocute)`
- Final state does not have: `needsEffect(boss, wet)`, `needsEffect(boss, electrocute)`

### Example 2: Effect already applied -- skip it

**Given:**
- `hasEffect(boss, wet)` (already applied)
- `needsEffect(boss, electrocute)`, `comboStep(electrocute, 2)`
- `comboStep(wet, 1)`

**When:**
- `applyEffect(boss, wet)`

**Then:**
- Plan is empty (already has the effect)
- State unchanged

### Example 3: No combo defined -- no plan

**Given:**
- (no `needsEffect` or `comboStep` facts)

**When:**
- `executeCombo(boss)`

**Then:**
- Planning fails (no steps to execute)

### Example 4: Three-step combo

**Given:**
- `needsEffect(target, freeze)`, `comboStep(freeze, 1)`
- `needsEffect(target, shatter)`, `comboStep(shatter, 2)`
- `needsEffect(target, burn)`, `comboStep(burn, 3)`

**When:**
- `executeCombo(target)`

**Then:**
- Plan applies all three effects in order: freeze, shatter, burn

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | All effects applied | After plan, every `needsEffect` is gone and `hasEffect` is present for each |
| P2 | Correct order | Effects are applied in ascending `comboStep` order |
| P3 | Idempotent effects | Applying an already-present effect produces no operators |
