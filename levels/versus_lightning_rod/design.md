# Lightning Rod

## Purpose

Category: **an enemy's power used against another enemy**. A sentry robot guards a hall; next door,
a storm golem idles. Nobody in the party makes lightning, but the golem does. Taunted, or soaked, it
winds up a **discharge**, a telegraphed heavy blow on the area it stands in
(`behavior(golem, taunted|wet, discharge, here)`, `heavy(discharge)`,
`effect(discharge, target, grant(electrocuted))`). It lands on everyone in that area but the golem.
It has **one charge**: the discharge spends it (`effect(discharge, self, grant(silenced))`). The robot
is a machine: a dry jolt only stuns it; soaked, then jolted, it short-circuits (its catalogue
weakness). Two companions, one skill each from seven.

Three things must meet: a **wet robot**, the **golem in its area**, and the golem **set off there**.

| Step | Skills |
|------|--------|
| **Soak the robot** | `tidalWave` (in the hall); `vortex` (into the fountain); `shieldBash` (knocked into the fountain, from next door); `blink` (into the walled pump room, onto the valve: the hall floods) |
| **Bring them together** | `hook` (the golem into the hall); `taunt` (it walks in) |
| **Set it off** | `taunt` (on arrival); water on the golem: a wave or a vortex with both in the hall, or the flooded hall it is hooked or walks into |

Why no single skill works:
- Nothing in the pool jolts. The only lightning is the golem's.
- The robot has no temper (`immune(robot, taunted)`): a taunt cannot move it.
- One charge: a golem set off before the robot is wet only stuns it, and is spent.
- Soakers alone never bring the golem; a hook alone brings it and nothing soaks the robot.

Traps: fire dries (a fireball's flames on the robot meet the fountain's water: extinguish, and the
robot stays dry); a shield bash on the golem stuns it (silenced: no discharge); water on the golem in
its own forge spends the charge there. The fire trap has a way out the physics allows: a second
fireball, cast in the discharge's window, finds the hall already alight (no new flames land), and its
knock alone soaks the robot.

Skills with two roles: `taunt` brings and sets off; `tidalWave` and `vortex` soak the robot and, with
the golem there, set it off too; `hook` brings the golem into the water or into the flood.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
            pumps (the valve: a plate)
           //    \\                         // = wall (teleport only)
gallery --- hall (robot; fountain) --- forge (golem)
```

- **Links:** walkable gallery-hall, hall-forge; walls gallery-pumps and hall-pumps.
- **Sight:** gallery-hall, hall-forge.
- **Features:** the fountain, a pool in the hall (`puddle`: knocked in, wet); the valve, a plate in the
  pump room (`spill(puddle, hall)`: the hall floods - everyone there, and whoever walks in, is wet).
- **Robot:** machine, immune to taunts, light. **Golem:** immune to electrocuted, light.
- Both companions start in the gallery with 4 mana.
- **Level-local recipes:** `getTo(?a, ?r)` (walk, or teleport next door), `soak(?v)` (a cast, a knock
  into a pool, or a plate that floods its area), `meet(?npc, ?v)` (one brought to the other),
  `fire(?npc, ?v)` (inflict a trigger). `win` = soak, meet, fire; or meet, soak, fire.

## Hypothesis

Measured with `htn_components combos versus_lightning_rod`:

- No single skill wins, even held by both companions: 0 of 7.
- 16 of 49 assignments win (8 unordered pairs), 8 methods, 0 solo plans, no dead skills:
  - `taunt` + `tidalWave` / `vortex` / `shieldBash` / `blink` / `fireball` (soak, then taunt);
  - `hook` + `tidalWave` / `vortex` / `blink` (hook the golem in; water sets it off).
- Losing pairs, each for a named reason: `hook` + `taunt` (nothing soaks), `hook` + `shieldBash` (no
  trigger: a bash on the golem silences it), `blink` + `tidalWave` (the charge spent in the forge),
  two soakers (nothing brings the golem).
- Skill usage: taunt 10, hook 6, tidalWave 4, vortex 4, blink 4, shieldBash 2, fireball 2.
- One `FindAllPlans` takes at most about 13 s (`taunt` + `tidalWave`: two win orders, the wave's
  knock aims, and the window's answers).

## Examples

### Example 1: Flood the hall, hook the golem in

**Given:** the player knows `hook`, the mage knows `blink`.

**When:** `win`

**Then:** the mage blinks through the wall into the pump room and steps on the valve: the hall floods
and the robot is wet. The player hooks the golem into the hall; it arrives soaked and discharges:
the robot short-circuits.

### Example 2: Bash it into the fountain, taunt the golem in

**Given:** the player knows `taunt`, the mage knows `shieldBash`.

**When:** `win`

**Then:** from the gallery the mage bashes the robot into the fountain (wet); the player taunts the
golem from the hall; it walks in and discharges.

### Example 3: Hook, then vortex both into the fountain

**Given:** the player knows `hook`, the mage knows `vortex`.

**When:** `win`

**Then:** the player hooks the golem into the hall; the mage's vortex on the fountain knocks
everything there into it; the soaked golem discharges on the soaked robot.

### Example 4: The second fireball

**Given:** the player knows `taunt`, the mage knows `fireball`.

**When:** `win`

**Then:** the mage's first fireball sets the robot alight and knocks it into the fountain: the water
puts the fire out, and the robot stays dry. The player taunts the golem in; in the window the mage's
second fireball finds the hall already burning and only knocks the robot into the fountain: wet, it
short-circuits.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the eight measured pairs have a plan. |
| P3 | One charge | A taunt on a dry robot only stuns it and spends the golem; hook + taunt: no plan. |
| P4 | A stunned golem never discharges | hook + shieldBash: no plan; a stunned golem with hook + tidalWave: no plan. |
| P5 | Water in the forge | blink + tidalWave: no plan. |
