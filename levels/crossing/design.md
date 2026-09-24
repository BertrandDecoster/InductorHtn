# The Crossing

## Purpose

A demo level for the ability catalogue (`abilities/primitives/ab_catalog`). There are three
enemies, each beaten only by its own weakness or by a drop; nothing in the catalogue kills in
general. The player and the mage pick **one skill each** from six, with mana for one costly cast
each (fireball, tidal wave and lightning flash cost 2); the Warden only knows `turnToMist`. The
level shows:

- An identity tag as a weakness: a soaked machine short-circuits, and a wooden thing burns.
- A guard no skill takes off: the stealthed bramble can only be reached by what lands on its whole
  area, or by what knocks everything there.
- Heavy as an anchor, taken off for a moment by `turnToMist`: the next cast can move the target.
- The map rule: a knockback never changes the area, so each enemy is knocked into what is in or
  beside its own area - the rift in the crypt, the sinkhole in the brink, the abyss at the edge of
  the brink and of the ledge.
- A heavy enemy blow as a trap: set alight, the brute stamps and caves the brink in under itself -
  which also cuts the way to the ledge.

| Enemy | Where | Answers |
|-------|-------|---------|
| **sentry** (machine, heavy, soaked) | on the flooded ledge, across the abyss | `lightningFlash` from the brink: the jolt kills it (it is already wet), and the flash carries the caster over. Or the Warden mists it from the brink, and in that moment someone knocks it into the abyss (`shieldBash` over the gap, `fireball`) or drags it across (`hook`: it falls on the way). |
| **bramble** (wooden, stealthed) | in the crypt's shadows | It cannot be aimed at. A `fireball` at the crypt itself sets it on fire; a `tidalWave` in the crypt washes it into the rift; a `vortex` on the rift draws it in. |
| **brute** (boss, living, heavy) | on the rotten brink | The Warden mists it, and someone knocks it into the sinkhole or the abyss (`fireball`, `shieldBash`, `tidalWave` on the brink, a `vortex` on the sinkhole); or a hooker swings over to the ledge on the pillar and hauls it across the abyss. Fire on it (unmisted) makes it stamp: a heavy `caveIn` on the brink - it falls into its own hole. |

Why no single skill wins, even held by both seats:
- only fire, the wave or the vortex reach the bramble;
- none of those reaches the sentry, except a fireball - and two fireballs are two casts for three
  enemies.

Traps:
- The cave-in takes the brink for good: fire on the brute before the sentry is down cuts the way to
  the ledge (P5).
- One costly cast each: the fireball and the flash cannot also take the brute (P6).
- A vortex on the sinkhole draws in whoever stands on the brink, friends included.
- The flash strands its caster on the ledge (harmless here: the goal is the enemies).

Skills serving two roles:
- `fireball` burns the bramble (the crypt) or knocks the misted sentry or brute.
- `vortex` takes the bramble (the rift) and the brute (the sinkhole).
- `hook` drags the sentry across, swings over on the pillar, and hauls the brute.
- `shieldBash` knocks the sentry and the brute over the edge.
- `tidalWave` takes the bramble (and could take the brute, mana permitting).
- `lightningFlash` is the jolt and the crossing.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage, warden)
  |
hall ---- crypt (bramble; shadows; rift)
  |
brink (brute; sinkhole) ~~ abyss ~~ ledge (sentry, pillar; puddle)
```

- **Areas:** gate, hall, crypt, brink, ledge (five).
- **Links:** gate–hall, hall–crypt, hall–brink walkable; brink ~ ledge a `gap` (the abyss).
- **Features:** `rift` (a chasm) in the crypt; `sinkhole` (a chasm) in the brink.
- **Zones:** the crypt hides whoever walks in (`shadows`); the ledge is flooded (`puddle`).
- **Line of sight:** gate ↔ hall; hall → crypt, brink; brink ↔ hall, ledge. Only the brink sees
  the ledge.
- **The brute:** `behavior(brute, burning, caveIn, here)`, a heavy physical blow on its own area.
- **Kit:** the Warden knows `turnToMist`; mana 2 each for the player and the mage. Default:
  player `fireball`, mage `shieldBash`.
- **Goal:** `clearCrossing` beats the sentry, the bramble and the brute in turn, each by
  `neutralize`, `scorch` (a costly skill on its whole area) or `haul` (swing over, mist, hook back).

## Hypothesis

Measured by `htn_components combos crossing` (36 assignments in about 4 s; each plan about 1 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 16 of 36 assignments win: 8 pairs, each way round.
  - `fireball` with `hook`, `shieldBash` or `vortex`;
  - `tidalWave` with `hook` or `shieldBash`;
  - `vortex` with `lightningFlash`, `hook` or `shieldBash`.
- 8 methods (sets of skills cast, the Warden's mist included).
- Skill usage: vortex 8, fireball 6, hook 6, shieldBash 6, tidalWave 4, lightningFlash 2. No dead
  skill; no plan carried by one companion.

## Examples

### Example 1: Bash over the abyss, burn the crypt

**Given:** the default kit (player `fireball`, mage `shieldBash`).

**When:** `clearCrossing`

**Then:**
1. The Warden mists the sentry from the brink; the mage bashes it into the abyss.
2. The player's fireball on the crypt burns the bramble.
3. The Warden mists the brute; the mage bashes it into the sinkhole or the abyss.

### Example 2: Jolt the sentry, vortex the rest

**Given:** player `vortex`, mage `lightningFlash`.

**When:** `clearCrossing`

**Then:** the mage's flash from the brink short-circuits the soaked sentry. The player's vortex on
the rift draws in the bramble; the Warden mists the brute, and a vortex on the sinkhole draws it in.

### Example 3: Swing over and haul the brute

**Given:** player `tidalWave`, mage `hook`.

**When:** `clearCrossing`

**Then:** the mage hooks the misted sentry across the abyss (it falls). The player's wave in the
crypt washes the bramble into the rift. The mage hooks the pillar and swings over to the ledge; the
Warden mists the brute, and the mage hauls it into the abyss.

### Example 4: Fire on the crypt

**Given:** player `fireball`, mage `hook`.

**When:** `clearCrossing`

**Then:** as Example 3, but the player's fireball on the crypt burns the bramble.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions casting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured pairs win | Exactly the 8 measured pairs win, both ways round; `combos` passes; no dead skill. |
| P4 | The bramble cannot be aimed at | `lightningFlash` + `hook` and `shieldBash` + `hook` cannot beat it. |
| P5 | Fire on the brute caves in the brink | It winds up a cave-in and falls; after that, nobody beats the sentry. |
| P6 | One costly cast each | `fireball` + `lightningFlash` and `fireball` + `fireball` lose. |
