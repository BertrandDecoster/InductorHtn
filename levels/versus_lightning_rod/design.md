# Lightning Rod

## Purpose

Category: **an enemy's power used against another enemy**. A sentry robot guards a hall; next door,
a storm golem idles. Nobody in the party can make lightning, but the golem can. It answers a mood:
taunted, it is dragged to whoever taunted it and discharges into everything around it; feared, it
bolts along the line away from whoever frightened it and discharges where it lands
(`behavior(golem, taunted|feared, discharge, here)`). The robot is a machine: a dry jolt only stuns
it; soaked, then jolted, it short-circuits (its own catalogue weakness). Two companions, one skill
each from eight.

| Step | Skills |
|------|--------|
| **Soak the robot** | `rainCall` (it stays in the hall); `tidalWave`, `gust` (from the gallery, washed or blown into the fountain); `magnetize` (hooked into the fountain) |
| **Lure the golem onto it** | `taunt` (from the robot's region: the golem is dragged there); `provoke` (melee, from the hall only); `terrify`, `roar` (from the vent it bolts into the hall, from the chimney down the sluice into the fountain) |

Why no single skill works:
- Nothing in the pool jolts. The only lightning is the golem's.
- The robot has no temper (`immune(robot, taunted)`): a taunt cannot drag it into the fountain.
- A lure onto a dry robot only stuns it, and the golem will not answer the same mood twice (the tag
  stays stored).
- A soaker alone leaves the robot wet and standing.

Skills with two roles: `tidalWave` soaks and moves (the wave's area push washes the robot out of the
hall). The fear skills lure in two different directions depending on where they are cast from.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
                          vent   chimney
                             \   /
gallery --- hall (robot) --- forge (golem)
               |
            fountain (puddle)
```

- **Lines:** from the gallery, a push on the hall lands in the fountain; from the vent, a push on the
  forge lands in the hall; from the chimney, in the fountain.
- **Line of sight:** gallery-hall, hall-forge, hall-fountain, fountain-forge, vent-forge,
  chimney-forge.
- **Robot:** machine, immune to taunts. **Golem:** light; taunted or feared, it discharges
  (`area: grant(electrocuted)`) where it stands after the tag's movement.
- Both companions start in the gallery with 4 mana.
- **Level-local recipes:** `soak(?v, ?p)` (a cast, a push into the fountain, or a hook into it) and
  `lure(?npc, ?v, ?not)` (give the NPC its trigger tag from where the tag's own movement lands it on
  ?v). `shortOut` = soak, lure by the other companion, confirm.

## Hypothesis

Measured with `htn_components combos versus_lightning_rod`:

- No single skill wins, even held by both companions: 0 of 8.
- 26 of 64 assignments win (13 unordered pairs), 13 methods, 0 solo plans, no dead skills.
  - `rainCall` + any lure: `taunt`, `provoke`, `terrify`, `roar` (4 pairs);
  - `tidalWave`, `gust` or `magnetize` + `taunt`, `terrify` or `roar` (9 pairs).
- Losing pairs, each for a named reason: two soakers (no lightning), two lures (a dry jolt only
  stuns), a mover + `provoke` (the fountain is not next to the forge).
- Skill usage: rainCall 8, taunt 8, terrify 8, roar 8, tidalWave 6, gust 6, magnetize 6, provoke 2.

## Examples

### Example 1: Rain, then taunt

**Given:** the player knows `rainCall`, the mage knows `taunt`.

**When:** `win`

**Then:** rain soaks the robot in the hall; the mage walks into the hall and taunts the golem, which is
dragged in and discharges; the robot short-circuits (`dead`).

### Example 2: Blown into the fountain, scared down the sluice

**Given:** the player knows `gust`, the mage knows `terrify`.

**When:** `win`

**Then:** the player's gust blows the robot into the fountain; the mage goes round to the chimney and
frightens the golem, which bolts down the sluice into the fountain and discharges there.

### Example 3: Provoke from next door

**Given:** the player knows `provoke`, the mage knows `rainCall`.

**When:** `win`

**Then:** the mage's rain soaks the robot; the player steps into the hall and provokes the golem across
the doorway; it is dragged into the hall and discharges.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the thirteen measured pairs have a plan. |
| P3 | A dry jolt only stuns | Two lures and no water: no plan. |
| P4 | Provoke stays in the hall | A mover with provoke loses: the fountain is out of melee reach. |
