# Ab Catalog

## Purpose

The standard tags and skills of the ability layer. It has three kinds of tag:

- **Atomic:** one meaning each.
  - Bans: blinded (no basic attack), silenced (no skills), rooted (no moving), slowed (no dashing),
    uncontrolledMove (it moves, but not where it chooses).
  - Elemental ingredients: wet, oiled, burning, electrocuted.
  - taunted, and wakeOnHit.
  - Buffs: stealthed, shielded, hasted, armored, invulnerable.
- **Composite:** a named bundle of atoms (stunned, asleep, feared, chilled, charmed, confused,
  berserk, polymorphed).
- **Outcome:** dead, frozen, fell. No skill grants one. Only an enemy's own `weakness/4`, or a hazard
  it is weak to, produces one. A combo is deadly because of who it lands on: a robot is stunned by
  a jolt, and short-circuits if it is soaked first. Otherwise players would find the one combo that
  kills anything and spam it.

Skills do no damage. Damage is incremental, and this layer is about combos. Each skill lands several
tags, or a tag and a movement.

**Looks.** `appearance(?look, ?tag)` lists statuses that play exactly like a catalogue tag and only
look different: petrified is a stun, webbed is a slow, a sheep is polymorphed. The runtime draws the
look; the planner only sees the tag.

The full tables are in `docs/reference/ability-catalog.md`.

## Layer

primitive

## Dependencies

- `abilities/primitives/ab_acts`

## Operators

None.

## Methods

None.

## Rules

| Rule | Description |
|------|-------------|
| `hostile(?t)` | Group `hostile`: what a shield absorbs, what wakes a sleeper, what invulnerability wards. |
| `immune(?e, ?t)` for `rank(?e, boss)` | Hard control (the composites). The atoms still land: a boss can be rooted, not stunned. |
| `immune(?e, ?t)` for `trait(?e, mindless \| machine)` | The `mind` group. |
| `weakness/4` for traits and elements | machine, living, insect, wooden, flier, heavy; element fire and water. |
| `weakness/4` for hazards | chasm (unless flier), lava (unless flier or fire), deepWater (the heavy sink). |
| `kind(?ab, skill)` | Every catalogue ability is a skill (for silence). |

## Required Facts

A level provides regions, `onEnter/2` placements of the zones, `beyond/3` push lines, `knows/2`, and
the enemies' `rank/2`, `trait/2`, `element/2`, extra `weakness/4` and starting `tag/2`.

## Examples

### Example 1: A robot is stunned or short-circuited

**Given:** `trait(foe, machine)`; the player knows `zap`.

**When:** `cast(player, zap, foe)`

**Then:** the robot is stunned, not dead.

### Example 2: A soaked robot dies

**Given:** a machine carrying `wet`.

**When:** the player zaps it

**Then:** it is dead.

### Example 3: A fire imp freezes solid

**Given:** `element(foe, fire)`.

**When:** `cast(player, frostBolt, foe)`

**Then:** it is frozen (out of the fight).

### Example 4: The floor gives way

**Given:** a walker and a flier on the floor.

**When:** `collapse` opens a chasm there

**Then:** the walker fell; the flier did not.

### Example 5: Fear sends it running

**Given:** `beyond(ledge, floor, far)`.

**When:** the player terrifies the foe from the ledge

**Then:** it is feared and has run to `far`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Every tag from two skills | Directly, through a composite, a spilled zone, or a weakness it triggers. |
| P2 | Every tag does something | Reacts, bundles, forbids, wards, moves its bearer, gates a skill, triggers a weakness, or stops the fight. |
| P3 | No skill grants an outcome | No `grant(dead \| frozen \| fell)` in any skill. |
| P4 | Looks map to tags | Every `appearance/2` names a catalogue tag, and no look is itself a tag. |
| P5 | A shield takes the next hostile tag | A net on a shielded foe: the shield absorbs the root; the blinding lands. |
| P6 | A hit wakes the sleeper | Any hostile tag on a sleeper removes `asleep`. |
| P7 | Bosses keep the atoms | A shield bash does not stun a boss; a net still roots it. |
| P8 | Haste counters slow | A hasted foe is not slowed by a grapple. |
| P9 | Only the hasted blitz | `blitz` needs the caster hasted. |
| P10 | Lightning flash strikes the path | The caster lands beyond the floor; everyone on it is electrocuted (a machine is stunned). |
| P11 | Fireball leaves a fire | The floor becomes a fire zone, everyone there burns, and the target is thrown out of it. |
