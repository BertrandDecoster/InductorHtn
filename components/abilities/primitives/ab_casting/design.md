# Ab Casting

## Purpose

Who may use an ability, from where, and at what cost. These are the GAS activation gates, written as
facts: tags the caster or the target must carry (`requires/3`) or must not carry (`blockedBy/3`), a
mana cost paid with a numeric fluent, and a once-per-encounter use. Reach decides where the caster
stands: `melee` means the target's region, `ranged` means anywhere with line of sight (staying put if
it can), and `self` means where it is.

Anyone casts what they know: the player character, an AI companion, an NPC. Nothing gates on
`role(?a, player)`. `knows/2` is the loadout, the fact a level varies.

## Layer

primitive

## Dependencies

- `abilities/primitives/ab_effects`

## Operators

| Operator | Description |
|----------|-------------|
| `opCast(?a, ?ab, ?e)` | Marker: `?a` uses `?ab` on `?e`. Its effects follow as their own operators. |
| `opSpendMana(?a, ?n)` | `decrease(mana(?a), ?n)`. |
| `opUseUp(?a, ?ab)` | Adds `spent(?a, ?ab)` for a `once` ability. |

## Methods

| Method | Description |
|--------|-------------|
| `cast(?a, ?ab, ?e)` | Ready, then cast from the first spot within reach. |
| `castFrom(?a, ?ab, ?e, ?from)` | Walk to `?from` (taking what is there), then use. A push needs the right side. |
| `useAbility(?a, ?ab, ?e)` | Gates checked again on arrival, in reach, pay, `opCast`, apply the bundle. |
| `payMana(?a, ?ab)` / `useUp(?a, ?ab)` | Each cost branch negates the other: backtracking can never take the free branch of a costly ability. |

## Rules

| Rule | Description |
|------|-------------|
| `unmet(?a, ?ab, ?e)` | Any reason not to: a missing required tag, a blocking tag, spent, not enough mana, a kind the caster is forbidden, a target that wards `targeted`. |
| `kindOf(?ab, ?k)` | Its declared kinds, plus `ranged` for a ranged ability. |
| `ready(?a, ?ab, ?e)` | Knows it, neither side gone, nothing unmet. |
| `inRange(?reach, ?from, ?r)` | Melee: same region or the next one. Ranged: `canTarget`. |
| `spot(?a, ?ab, ?r, ?from)` | Where to cast from: where it stands if in range, else a region it can walk to. |

## Required Facts

| Fact | Description |
|------|-------------|
| `knows(?a, ?ab)` | The loadout |
| `reach(?ab, self\|melee\|ranged)` | |
| `requires(?ab, caster\|target, ?t)` / `blockedBy(?ab, caster\|target, ?t)` | Optional gates |
| `manaCost(?ab, ?n)` + `mana(?a, ?m)` | Optional cost |
| `once(?ab)` | Optional: one use per encounter |
| `kind(?ab, spell\|attack\|dash\|heavy)` | Optional: what a forbidding tag checks |

## Examples

### Example 1: A ranged cast from where it stands

**Given:** player at `ledge`, gob at `pool`, `lineOfSight(ledge, pool)`, `reach(shock, ranged)`.

**When:** `cast(player, shock, gob)`

**Then:** plan contains `opCast(player, shock, gob)`, `opGrant(player, gob, shocked)`, no `opNavigate`.

### Example 2: Melee reaches the next region

**Given:** `reach(hammer, melee)`; gob in the pool, next to the player's ledge.

**When:** `cast(player, hammer, gob)`

**Then:** plan contains `opCast(player, hammer, gob)` and no step; the player is tired and dry.

### Example 3: Mana is paid

**Given:** `manaCost(fireball, 2)`, `mana(player, 3)`.

**When:** `cast(player, fireball, gob)`

**Then:** plan contains `opSpendMana(player, 2)`; the state has `mana(player, 1)`.

### Example 4: A self ability

**Given:** `reach(rally, self)`, `effect(rally, self, grant(inspired))`.

**When:** `cast(player, rally, player)`

**Then:** the player is inspired.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | A tired caster cannot swing | `blockedBy(hammer, caster, tired)` and a tired player: no plan. |
| P2 | Requirements on the target | `requires(jolt, target, wet)`: a plan on a wet target, none on a dry one. |
| P3 | No mana, no cast | `mana(player, 1)` for a cost of 2: no plan. |
| P4 | Once means once | A `once` ability is spent after one use; a second use has no plan. |
| P5 | Anyone casts what they know | A companion casts the same ability the same way. |
| P6 | The gone are no targets | No cast on a dead target. |
| P7 | A forbidden kind is not cast | A silenced caster (`forbids(silenced, spell)`) swings a hammer but casts no spell. |
| P8 | The hidden cannot be aimed at | `wards(stealthed, targeted)`: no cast aimed at a stealthed target. |
| P9 | A region is a target | An area ability aimed at a region hits everyone standing there. |
| P10 | Melee walks within reach | A target two regions away: the caster walks to the next region, no further. |
