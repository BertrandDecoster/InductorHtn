# The Hostage

## Purpose

A rescue level built around a telegraphed attack on the escort. A **hostage** sits shackled
(`rooted`) in a cell and must reach the gate. It is not a companion: it never casts, and it never
walks. A **warlock** in the guardroom watches the only corridor to the cell (nobody walks in under
his eyes). Alarm him and he calls a **meteor** down on the cell to execute the hostage. Two
companions, the player and the mage, pick one skill each from a pool of seven catalogue skills:

| Obstacle | Answers |
|----------|---------|
| **The warlock** (watches the corridor) | quietly: `shieldBash` (stunned: blind and silenced, so he cannot cast); or soak him (`tidalWave`) and then ice him (`blizzard`: wet + chilled freezes) or jolt him (`lightningFlash`: a wet living thing seizes up). Loudly: `blindingFlash` blinds him, the meteor winds up on the cell, and in that one cast a friend breaks it with `hook` (the meteor is magic: interrupt) |
| **The shackles** (the hostage cannot walk) | `hook` it out (from the corridor, then from the gate), wash it out from behind (`tidalWave` from the bunk, then from the cell), or blast it out (`fireball` from the bunk, then from the cell) |

The alarms are ordinary behaviours: `behavior(warlock, T, meteor, there(cell))` for `T` in blinded,
taunted, burning and electrocuted. A stun silences him, so it raises no alarm; the soaked warlock
takes a jolt as a stun (his weakness), so the electrocuted tag is never stored and no alarm fires
either. `mustSurvive(hostage)` makes the planner refuse any plan in which the meteor lands on it.

Why no single skill works:
- A silencer leaves the hostage shackled; nothing else moves it.
- A mover cannot get into the corridor while the warlock watches it, and the cell is reached only
  through the corridor.
- `tidalWave` alone soaks him but never stops him; `blindingFlash` held by both only saves its
  caster when the meteor winds up.

The traps:
- An alarm nobody can answer: a `blindingFlash` with a `tidalWave` or `fireball` partner, a
  `fireball` on him (burning), a dry `lightningFlash` (electrocuted). The meteor would land on the
  hostage: no plan.
- The guardroom window looks into the cell over a fire pit (`beyond(guardroom, firepit, cell)`):
  a hook from the guardroom drops the hostage in the lava.
- The soaker has six mana for three waves: one on the warlock, two on the hostage.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage) --- corridor --- cell (hostage, shackled) --- bunk
   \                       |            :
    guardroom -------------+ ..... firepit (lava, under the window)
    (warlock)
```

- **Walking:** gate-corridor-cell-bunk, corridor-guardroom, gate-guardroom.
- **Lines:** a push from the bunk on the cell lands in the corridor; a push from the cell on the
  corridor lands at the gate; the fire pit lies between the guardroom and the cell.
- **Line of sight:** gate-corridor, gate-guardroom, corridor-cell, corridor-guardroom,
  guardroom-cell, cell-bunk (both ways). Nobody at the gate sees into the cell.
- **Warlock:** living, `watches(warlock, corridor)`, the four alarms above.
- **Hostage:** living, rooted, `mustSurvive`.
- **Mana:** six each.
- **Goal:** `win` = `quiet(warlock)` (blinded or stunned; or soaked by one companion and iced or
  jolted by the other), then `extract(hostage, gate, 3)` (up to three forced moves, each bringing it
  nearer the gate by `progress/2`: a pull from a spot nearer the gate, or a push from behind found
  by `placement/6`), then `confirmSafe` (the hostage there and whole, and no companion lost).

## Hypothesis

Measured with `htn_components combos escort_hostage`:

- No single skill wins, even when both companions hold it: 0 of 7.
- 12 of 49 assignments win (6 pairs, either way round), by 6 methods:
  `shieldBash` + `hook` / `tidalWave` / `fireball`; `blindingFlash` + `hook` (the meteor window);
  `tidalWave` + `blizzard` (freeze); `tidalWave` + `lightningFlash` (shock).
- No solo plan; no dead skill. `hook` plays two roles (breaking the meteor, dragging the hostage),
  and so does `tidalWave` (soaking the warlock, washing the hostage out).
- Every plan takes under a second.

## Examples

### Example 1: Bash and hook

**Given:** the player knows `shieldBash`, the mage knows `hook`.

**When:** `win`

**Then:** the player bashes the warlock from the gate (stunned, no alarm); the mage walks into the
corridor, hooks the hostage out of the cell, walks back to the gate and hooks it again.

### Example 2: Blind him and break the meteor

**Given:** the player knows `blindingFlash`, the mage knows `hook`.

**When:** `win`

**Then:** the player walks into the guardroom and flashes; the warlock is blinded and winds up a
meteor on the cell. In the window the mage hooks the warlock from the gate: the meteor is
interrupted (and he is dragged to the gate, still blind). The mage then hooks the hostage out.

### Example 3: Freeze and wash out

**Given:** the player knows `tidalWave`, the mage knows `blizzard`.

**When:** `win`

**Then:** the player's wave soaks the warlock; the mage's blizzard freezes him (stunned, no alarm).
The player walks through the cell to the bunk and washes the hostage into the corridor, then steps
into the cell and washes it on to the gate.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 6 measured pairs have a plan, whichever companion holds which half. |
| P3 | An unanswered alarm has no plan | Blinding flash with a wave, a fireball or another flash; a fireball or a dry jolt with a hook: no plan. |
| P4 | The meteor never lands | No winning plan has a blow; every wind-up is interrupted. |
| P5 | The warlock first | Nobody walks into the corridor before he is stopped; both companions cast. |
