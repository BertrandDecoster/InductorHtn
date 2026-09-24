# The Hostage

## Purpose

A rescue level built around a telegraphed attack on the escort. A **hostage** sits hobbled in a
cell and must reach the gate. It is not a companion: it never casts, and it never walks on its own.
It is dragged out (`hook`, one area at a time) or it shuffles after a voice it trusts (`taunt`: it
follows its caller). A **warlock** in the guardroom watches the corridor to the cell through a
window: no companion walks in under his eyes. Alarm him and he calls a **meteor** down on the cell
to execute the hostage. Two companions, the player and the mage, pick one skill each from a pool of
seven catalogue skills:

| Obstacle | Answers |
|----------|---------|
| **The warlock** (watches the corridor) | quietly: `shieldBash` (stunned: blind and silenced, so no alarm), or drop him in his fire pit - `vortex` on the pit from the gate, `tidalWave` standing in the guardroom. Loudly: `blindingFlash` in the guardroom blinds him, the meteor winds up on the cell, and in that one cast a friend at the gate hooks him (`hook`: the meteor is magic, interrupted). Or `fireball`: he burns, the meteor winds up, and in the window the fireballer throws a second one that knocks him into the pit - a fallen warlock's meteor misses |
| **The hostage** (never walks alone) | `hook` it from the corridor (cell to corridor), then from the gate (corridor to gate); or `taunt` it from the corridor: it walks after its caller, and follows it out to the gate |

The alarms are ordinary behaviours: `behavior(warlock, T, meteor, there(cell))` for `T` in blinded,
taunted and burning. A stun silences him, so it raises no alarm. `mustSurvive(hostage)` makes the
planner refuse any plan in which the meteor lands on it.

Why no single skill works:
- A stopper leaves the hostage in its cell; only a hook or a taunt moves it.
- A mover cannot get into the corridor while the warlock watches it, and nobody sees into the cell
  from anywhere else a companion can use.
- `fireball` held by both drops the warlock, but nobody can then move the hostage.

The traps:
- An alarm nobody can answer: a `blindingFlash` with a `taunt` partner; a `taunt` on the warlock
  (the meteor falls, and he still watches). No plan.
- A `hook` answering a `fireball` interrupts the meteor but drags the burning warlock to the gate,
  away from his pit: the blast's knockback finds nothing, and he still watches. Only the second
  fireball saves that plan, so the fireballer needs all four mana.
- A `vortex` or a `tidalWave` knocks into the pit whoever stands in the guardroom, friends
  included.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage) ---- corridor ---- cell (hostage)
  |                      (watched)      :
guardroom (warlock, firepit) ..wall.....:   (a spyhole)
```

- **Areas (4):** gate, corridor, cell, guardroom.
- **Links:** walkable gate-corridor, corridor-cell, gate-guardroom; a `wall` guardroom-cell (the
  spyhole: sight, no passage).
- **Features:** `firepit` (lava) in the guardroom.
- **Line of sight:** gate-corridor, corridor-cell, gate-guardroom, guardroom-corridor,
  guardroom-cell (both ways). Nobody at the gate sees into the cell.
- **Warlock:** living, `watches(warlock, corridor)`, the three alarms above.
- **Hostage:** living, `mustSurvive`; the goal never walks it.
- **Mana:** four each.
- **Goal:** `win` = `quiet(warlock)` (blinded - a stun blinds too - or `sendDown` into the pit),
  then `extract(hostage)` (`bringTo` the corridor, by a hook or a taunt; then `lead` it to the
  gate: a follower follows its caller's walk, anything else is hooked again), then `confirmSafe`
  (the hostage at the gate, whole; companions may be lost).

## Hypothesis

Measured with `htn_components combos escort_hostage`:

- No single skill wins, even when both companions hold it: 0 of 7.
- 18 of 49 assignments win (9 pairs, either way round), by 9 methods:
  `hook` + `shieldBash` / `vortex` / `tidalWave` / `fireball` / `blindingFlash`;
  `taunt` + `shieldBash` / `vortex` / `tidalWave` / `fireball`.
- No solo plan; no dead skill. `hook` plays two roles (breaking the meteor, dragging the hostage),
  and so does `fireball` (the alarm, and its own answer).
- The meteor winds up on the escort in two methods (`blindingFlash` + `hook`, `fireball` + either
  mover) and never lands.
- The whole matrix replans in under three seconds.

## Examples

### Example 1: Bash and hook

**Given:** the player knows `shieldBash`, the mage knows `hook`.

**When:** `win`

**Then:** the player bashes the warlock from the gate (stunned, no alarm; the knock may drop him in
the pit too); the mage walks into the corridor, hooks the hostage out of the cell, walks back to the
gate and hooks it again.

### Example 2: Blind him and break the meteor

**Given:** the player knows `blindingFlash`, the mage knows `hook`.

**When:** `win`

**Then:** the player walks into the guardroom and flashes; the warlock is blinded and winds up a
meteor on the cell. In the window the mage hooks the warlock from the gate: the meteor is
interrupted (and he is dragged to the gate, still blind). The mage then hooks the hostage out.

### Example 3: Burn him twice and call the hostage out

**Given:** the player knows `fireball`, the mage knows `taunt`.

**When:** `win`

**Then:** the player's fireball sets the warlock alight: the meteor winds up on the cell. In the
window the player throws a second fireball that knocks him into the fire pit; the meteor misses.
The mage walks into the corridor and taunts the hostage, which walks after it and follows it to the
gate.

### Example 4: The vortex drops him

**Given:** the player knows `vortex`, the mage knows `taunt`.

**When:** `win`

**Then:** the player's vortex on the fire pit, from the gate, knocks the warlock in; no alarm.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 9 measured pairs have a plan, whichever companion holds which half. |
| P3 | An unanswered alarm has no plan | A flash with a caller, a taunt with a hook, a flash with a bash: no plan. |
| P4 | The meteor never lands | No winning plan has a blow. |
| P5 | The warlock first, two hands | Both companions cast; nobody walks into the corridor before the first cast. |
