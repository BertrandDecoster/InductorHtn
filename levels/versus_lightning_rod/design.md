# Lightning Rod

## Purpose

Category: **an enemy's power used against another enemy**. A sentry robot guards a hall; next door, a
storm golem idles. Nobody in the party can make lightning, but the golem can. Taunted, it is dragged
to whoever taunted it; blinded, it lashes out where it stands. Either way it winds up a **discharge**,
a telegraphed heavy blow on the region it stands in (`behavior(golem, taunted|blinded, discharge,
here)`, `heavy(discharge)`, `effect(discharge, area, grant(electrocuted))`). It lands on everyone in
that region but the golem. The robot is a machine: a dry jolt only stuns it; soaked, then jolted, it
short-circuits (its catalogue weakness). Two companions, one skill each from six.

Three things must meet: a **wet robot**, the **golem in its region**, and the golem **set off there**,
with **no companion left inside** when the blow lands (the team gets one cast in the window).

| Step | Skills |
|------|--------|
| **Soak the robot** | `tidalWave` (in place, or washed from the gallery into the fountain); `hook` (dragged into the fountain from the fountain); `vortex` (drawn into the fountain) |
| **Bring them together** | `hook` (either one to the other); `vortex` (both into the hall); `tidalWave` (the golem washed out of the forge from the vent or the chimney) |
| **Set it off** | `blindingFlash` (where it stands; its disjoint lets the flasher stay inside); `taunt` (from the robot's region: the golem is dragged there, with the taunter inside) |
| **Get out** | the taunter needs a friend's cast in the window: only a `hook` drags it out without the robot |

Why no single skill works:
- Nothing in the pool jolts. The only lightning is the golem's.
- The robot has no temper (`immune(robot, taunted)`): a taunt cannot move it.
- A taunter is always inside its own lure's blow. A wave or a vortex cast to save it moves the robot
  (and the golem) out too; only a hook takes one companion alone.
- Movers alone bring a wet robot to the golem, and nothing sets it off.
- Fire dries: a fireball on the soaked robot is steam, and one that sends it into the fountain puts its
  own fire out instead of soaking it. Fireball is in the pool as the wrong element.

Skill with two roles: `hook` soaks (drags the robot into the pool), gathers (either enemy to the
other), and rescues (drags the taunter out of the struck region).

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
- **Robot:** machine, immune to taunts. **Golem:** light; taunted or blinded, it winds up a heavy,
  physical discharge (it cannot be interrupted) on its region.
- Both companions start in the gallery with 4 mana.
- **Level-local recipes:** `bring(?e, ?r)` (pulled there by someone standing in ?r, or pushed,
  washed or drawn there - `placement/6`), `soak(?v)` (a cast that wets it, or brought into a pool),
  `trigger(?npc, ?r)` (a trigger whose drag lands it in ?r, given from ?r; or any trigger in place),
  `stepAside(?r, ?a)` (the other companion leaves ?r for a region that still sees it), and
  `setOff(?npc, ?v)` (lured to ?v, brought to ?v, ?v brought to it, or both brought to a third
  region). `win` = soak, set off, confirm.

## Hypothesis

Measured with `htn_components combos versus_lightning_rod`:

- No single skill wins, even held by both companions: 0 of 6.
- 8 of 36 assignments win (4 unordered pairs), 4 methods, 0 solo plans; dead skill: `fireball` (by
  design, the wrong element):
  - `hook` + `taunt`: hook the robot into the fountain, taunt the golem there, hook the taunter out;
  - `hook` + `blindingFlash`: hook the robot into the pool and the golem to it (or the robot on into
    the forge), flash;
  - `vortex` + `blindingFlash`: vortex the robot into the pool, then both into the hall, flash;
  - `tidalWave` + `blindingFlash`: soak the robot, wash the golem out of the forge to it, flash.
- Losing pairs, each for a named reason: `taunt` + `tidalWave` / `vortex` (the rescue moves the robot
  out), `taunt` + `blindingFlash` (nothing soaks), two movers (nothing sets it off), anything with
  `fireball`.
- Skill usage: blindingFlash 6, hook 4, taunt 2, vortex 2, tidalWave 2, fireball 0.
- One `FindAllPlans` takes 0.1-4 s.

## Examples

### Example 1: Hook it in, taunt, hook the taunter out

**Given:** the player knows `hook`, the mage knows `taunt`.

**When:** `win`

**Then:** the player stands in the fountain and hooks the robot in (soaked), then steps back into the
hall; the mage walks into the fountain and taunts the golem, which is dragged in and winds up its
discharge; in the window the player hooks the mage out to the hall; the blow lands on the robot
(`dead`).

### Example 2: Wash them both into the pool, then flash

**Given:** the player knows `tidalWave`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** from the gallery the player's wave soaks the robot and washes it into the fountain; from the
chimney a second wave washes the golem down the sluice into the fountain; the mage flashes it and the
discharge lands on the robot.

### Example 3: Vortex twice, flash from inside

**Given:** the player knows `vortex`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the player vortexes the fountain (the robot is drawn in and soaked), then the hall from the
hall: the golem, the robot and the mage are drawn in. The mage flashes from inside the struck hall;
its disjoint lets the blow pass through it.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the four measured pairs have a plan. |
| P3 | The taunter is pulled out | Every hook + taunt plan hooks the taunter between the wind-up and the blow. |
| P4 | Only a hook rescues | taunt + tidalWave, taunt + vortex: no plan. |
| P5 | Fire dries | fireball with any other skill: no plan. |
