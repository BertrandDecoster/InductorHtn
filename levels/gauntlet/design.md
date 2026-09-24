# The Gauntlet

## Purpose

The pure-movement level on the ability layer. Nothing dies except by falling. Three companions have
to reach the exit: the player and the mage pick **one skill each** from six catalogue skills, and
the Warden, who only knows `turnToMist`, cannot leap. So the guard has to be moved out of his way,
the lever behind the grate has to be pressed, and the lava channel has to be bridged for him. Each
seat has mana for one costly cast (the fireball and the tidal wave cost 2).

The level follows the map rule of the catalogue: a knockback never changes the area. Everything is
knocked into something *in its own area*: the guard into the trapdoor under him, the crate onto the
lever beside it, the barrel into the channel at the rim's edge.

| Obstacle | Answers |
|----------|---------|
| **The heavy guard in the choke** (a blocker) | Nothing moves it until the Warden turns it to mist. For that moment (the next cast) someone knocks it through the trapdoor under it (`fireball` from the start, `shieldBash` from next door, a `vortex` on the trapdoor) or drags it out into the start (`hook`). |
| **The lever in the grated alcove** (latches the exit gate) | The grate is a wall: nobody walks, dashes or pulls through it. The crate beside the lever is knocked onto it through the bars (`fireball`, a `vortex` on the lever); or a blinker lands in the alcove, steps on, and blinks on over the lava (`blink`). |
| **The lava channel** (a gap between the rim and the far bank) | The barrel on the rim is knocked into it and bridges it (`fireball`, `shieldBash`, a `tidalWave` from the rim); or a hooker swings across on the far pillar and drags the barrel in from the far side (`hook`). |

Why no single skill wins, even held by both seats:
- `fireball` does all three jobs, but mana gives each seat one;
- `vortex` drops the guard and works the lever, but cannot push into a gap;
- `shieldBash` and `hook` cannot reach through the grate;
- `blink` moves no one else; `tidalWave` only works where the caster stands.

Traps:
- The mist lasts through exactly one more cast, so the push must come next (P4).
- Unmisted, the guard is an anchor: a hook swings the hooker into the choke instead (P6).
- Two fireballs: three jobs, two casts (P5).
- A wave from the rim knocks everyone else standing there: the Warden too, if he came early.

Several skills serve several roles:
- `fireball`: the guard, the crate, the barrel.
- `vortex`: the guard (trapdoor) and the crate (lever).
- `hook`: drags the guard, grapples the far pillar, drags the barrel across.
- `shieldBash`: the guard and the barrel.
- `blink`: the lever, and the way out of the alcove.
- `tidalWave`: the barrel.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
start --- choke (guard; trapdoor) --- hall --- rim (barrel) ~~ lava ~~ far (pillar) --- exit
                                        #                              ~~                (gate)
                                     alcove (crate; lever) ~~~~~~~~~~~~
```

- **Areas:** start, choke, hall, alcove, rim, far, exit (seven).
- **Links:** start–choke, choke–hall, hall–rim walkable; hall # alcove a `wall` (the grate: seen
  through, only a teleport passes); rim ~ far and alcove ~ far `gap`s (the lava channel);
  far–exit a `doorway` (the gate).
- **Features:** `trapdoor` (a chasm) in the choke; `lever` (a plate: `open(gate)`) in the alcove.
- **Line of sight:** start → choke, hall; hall → alcove, rim, choke; rim ↔ far; rim, far → alcove.
- **Things:** the guard (enemy: heavy, living, blocker) in the choke; the crate beside the lever;
  the barrel (filler) on the rim; the pillar (heavy) on the far bank.
- **Kit:** the Warden knows `turnToMist`; the player and the mage have mana 2 each. Default (it
  fits the planner's default 1 MB budget, for `verify`): player `fireball`, mage `hook`.
- **Goal:** `escape` spells out the stages: `unguard`, `weighPlate`, `spanChannel`, then everyone
  leaves (walks, or leaps and walks on).

## Hypothesis

Measured by `htn_components combos gauntlet` (36 assignments in about 4 s; each plan under 1 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 16 of 36 assignments win: 8 pairs, each way round.
  - `vortex` with `fireball`, `shieldBash`, `hook` or `tidalWave`;
  - `fireball` with `shieldBash` or `hook`;
  - `blink` with `shieldBash` or `hook`.
- 8 methods (sets of skills cast, the Warden's mist included).
- Skill usage: vortex 8, fireball 6, shieldBash 6, hook 6, blink 4, tidalWave 2. No dead skill; no
  plan carried by one companion.

## Examples

### Example 1: Drag the guard, throw the crate, swing over

**Given:** the default kit (player `fireball`, mage `hook`).

**When:** `win`

**Then:**
1. The Warden mists the guard; the mage hooks it out of the choke into the start.
2. From the hall, the player's fireball knocks the crate onto the lever: the gate opens.
3. The mage hooks the far pillar, swings over the lava, and drags the barrel in: it bridges the
   channel.
4. Everyone walks out.

### Example 2: Drag the guard, blink on the lever, swing over

**Given:** player `blink`, mage `hook`.

**When:** `win`

**Then:** the mage hooks the misted guard out into the start. The player blinks through the grate,
steps on the lever and later blinks on to the far bank. The mage hooks the far pillar, swings over
the lava, and drags the barrel in behind him.

### Example 3: Bash the guard and the barrel

**Given:** player `shieldBash`, mage `blink`.

**When:** `win`

**Then:** the player bashes the misted guard through the trapdoor, and later bashes the barrel into
the channel; the mage works the lever.

### Example 4: A wave from the rim

**Given:** player `tidalWave`, mage `vortex`.

**When:** `win`

**Then:** one vortex on the trapdoor drops the misted guard, a second on the lever knocks the crate
onto it; the player's wave from the rim washes the barrel into the lava.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions casting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured pairs win | Exactly the 8 measured pairs win, both ways round; `combos` passes; no dead skill. |
| P4 | The mist lasts one cast | Misted, the guard drops on the next cast; a cast later it is heavy again and the fireball does not move it. |
| P5 | One fireball each is not enough | `fireball` + `fireball` loses; with mana 4 each it wins. |
| P6 | The heavy guard is an anchor | Unmisted, a hook on it swings the hooker into the choke; the guard stays. |
| P7 | The grate stops melee | `shieldBash` + `hook` cannot work the lever. |
