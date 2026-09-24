# The Crossing

## Purpose

A demo level for the ability catalogue (`abilities/primitives/ab_catalog`). There are three
enemies, each beaten only by its own weakness; nothing in the catalogue kills in general. The
player and the mage pick **one skill each** from six; the Warden only knows `turnToMist`. The
level shows:

- An identity tag as a weakness: a soaked machine short-circuits, and a wooden thing burns.
- A guard no skill takes off: the stealthed bramble can only be reached by what lands on its whole
  region.
- Heavy as an anchor, taken off for a moment by `turnToMist`: the next cast can move the target.
- A heavy enemy attack the team triggers on purpose. Taunted, the brute stamps and caves in the
  rotten brink under itself, so the team only needs to stand clear.
- A hazard between two regions: a pull across the abyss drops the target in.

| Enemy | Where | Answers |
|-------|-------|---------|
| **sentry** (machine, heavy, soaked) | on the flooded ledge, across the abyss | `lightningFlash`: the jolt kills it (it is already wet), and the flash carries the caster over. Or the Warden mists it, and in that moment someone drags it across the abyss from the brink (`hook`, `taunt`: it falls on the way) or sucks it into the abyss (`vortex`). |
| **bramble** (wooden, stealthed) | in the crypt's shadows | It cannot be aimed at. A `fireball` at the crypt itself sets it on fire; a `tidalWave` from the hall washes it through the broken wall into the abyss. |
| **brute** (boss, living, heavy) | on the rotten brink | Taunted (`taunt` from the hall), it stamps: a heavy `caveIn` on its own region, and it falls into the hole it made. Or the Warden mists it and someone throws it in (`fireball`, `tidalWave` from the hall) or sucks it in (`vortex` on the abyss). |

Why no single skill wins, even held by both seats:
- only fire or the wave reaches the bramble;
- neither of them reaches the sentry across the abyss: a push from the hall has no line to the
  ledge, and a wave from the brink does not reach it.

Traps:
- The cave-in takes the brink for good. Drag the sentry across before you provoke the brute (P4).
- A vortex on the abyss sucks in anyone on the brink or the ledge, friends included (P5).
- A wave from the hall throws whoever still stands on the brink into the abyss. `regroup` steps
  them back first.
- The lightning flash strands its caster on the ledge (harmless here: the goal is the enemies).

Skills serving two roles:
- `taunt` drags the sentry across, and provokes the brute into its cave-in.
- `vortex` sucks in the sentry or the brute.
- `fireball` and `tidalWave` take the bramble and throw the brute.
- `hook` drags the sentry across.
- `lightningFlash` is the jolt and the crossing.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage, warden)
  |
hall ---- crypt (bramble; shadows)
  |          \  (broken wall)
brink (brute) ~~ abyss (chasm) ~~ ledge (sentry, pillar; puddle)
```

- **Walking:**
  - gate–hall, hall–crypt, hall–brink;
  - the abyss is next to the brink and the ledge, and nobody walks into it.
- **Line of sight:**
  - gate→hall, gate→brink;
  - hall→crypt, hall→brink, hall→abyss, hall→ledge;
  - brink↔ledge; brink and ledge→abyss.
- **Push lines:**
  - from the hall or the gate, what stands on the brink goes over;
  - from the hall, what is in the crypt goes through the broken wall;
  - the abyss lies between the brink and the ledge.
- **Zones:**
  - the crypt hides whoever walks in (`shadows`);
  - the abyss is a `chasm`;
  - the ledge is flooded (`puddle`).
- **The brute:** `behavior(brute, taunted, caveIn, here)`, a heavy physical blow on its own region.
- **Mana:** 4 each for the player and the mage (two costly casts).
- **Default kit:** player `fireball`, mage `lightningFlash`.

## Hypothesis

Measured by `htn_components combos crossing` (36 replans in about 4 s; each plan is under 1 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 16 of 36 assignments win, each way round. They are exactly one bramble answer (`fireball`,
  `tidalWave`) times one sentry answer (`lightningFlash`, `hook`, `taunt`, `vortex`).
- 8 methods (sets of skills cast), plus the variants inside a set. The brute falls to the mist and
  a throw, a drag, a vortex, or its own cave-in (`taunt`).
- Skill usage: fireball 8, tidalWave 8, lightningFlash 4, hook 4, taunt 4, vortex 4. No dead skill;
  no plan carried by one companion.

## Examples

### Example 1: Jolt, burn and throw

**Given:** the default kit (player `fireball`, mage `lightningFlash`).

**When:** `clearCrossing`

**Then:**
1. The mage flashes onto the ledge and the jolt kills the soaked sentry.
2. The player's fireball on the crypt burns the bramble.
3. The Warden mists the brute, and the player's second fireball throws it over.

### Example 2: Provoke the brute into the cave-in

**Given:** player `taunt`, mage `tidalWave`.

**When:** `clearCrossing`

**Then:**
1. The Warden mists the sentry, and the player taunts it from the brink: dragged across the abyss,
   it falls in.
2. Everyone steps back into the hall.
3. The mage's wave washes the bramble through the broken wall.
4. The player taunts the brute from the hall. It winds up a cave-in on the brink, nobody is there,
   and it falls.

### Example 3: Vortex on the abyss

**Given:** player `fireball`, mage `vortex`.

**When:** `clearCrossing`

**Then:** the Warden mists the sentry, and the mage's vortex on the abyss sucks it off the ledge.

### Example 4: Drag it across

**Given:** player `hook`, mage `tidalWave`.

**When:** `clearCrossing`

**Then:** the Warden mists the sentry; the player hooks it from the brink and it falls on the way.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions acting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured assignments win | Exactly the 8 measured pairs win, both ways round; `combos` passes; no dead skill. |
| P4 | The cave-in takes the brink for good | With `taunt` + `hook`, the sentry can be dragged across before the brute is provoked, never after. |
| P5 | The vortex takes friends too | The Warden mists the sentry from the brink; a vortex on the abyss drops him in. |
| P6 | The bramble cannot be aimed at | `lightningFlash` + `hook` cannot beat it. |
