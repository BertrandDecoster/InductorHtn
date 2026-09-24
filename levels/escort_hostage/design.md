# The Hostage

## Purpose

A rescue level: a frail **hostage** sits shackled (`rooted`) in a cell and must reach the gate. It is
not a companion: it never casts, and while shackled it cannot walk at all. A hound in its kennel
watches the only corridor to the cell: nobody walks in under its eyes. Two companions, the player
and the mage, pick one skill each from a pool of eight:

| Obstacle | Answers |
|----------|---------|
| **The hound** (watches the corridor; a wooden war-construct) | blind it: `net`, `flashbang`, `sleepDart`, `terrify` (feared bundles blinded); or burn it: `flameWall` on the kennel (wooden: burning kills it) |
| **The shackles** (the hostage cannot walk) | drag it out, from the corridor and then from the gate (`magnetize`, twice); shove it out from behind, from the bunk into the corridor and from the cell to the gate (`gust`, twice); or strip the shackles (`cleanse`: rooted is a hostile tag) and it walks out |

The two families differ in kind: blinding vs. killing the watcher; dragging (pull), shoving
(push), or freeing (a tag removed, then an ordinary walk).

Why no single skill works:
- A silencer leaves the hostage shackled; nothing else moves it.
- A mover cannot get into the corridor while the hound watches it; the cell is reached only
  through the corridor.

The protect traps:
- The hostage is `frail`: `weakness(?e, burning, none, dead)`. `flameWall` kills the hound, but
  aimed at the cell or the corridor it would kill the hostage too.
- The kennel window looks into the cell over a fire pit (`beyond(kennel, firepit, cell)`): a pull
  from the kennel drops the hostage into the lava.
- `taunt` is not in the pool: the taunted tag is stored once, so a second taunt does not move the
  hostage again (see the wishlist in the report).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage) --- corridor --- cell (hostage, shackled) --- bunk
                           |            :
                        kennel ...... firepit (lava, under the window)
                        (hound)
```

- **Lines:** a push from the bunk on the cell lands in the corridor; a push from the cell on the
  corridor lands at the gate; the fire pit lies between the kennel and the cell.
- **Line of sight:** gate-corridor, corridor-cell, corridor-kennel, kennel-cell, bunk-cell, and
  gate-kennel (so the hound can be blinded or burnt from the gate).
- **Hound:** wooden, `watches(hound, corridor)`.
- **Goal:** `win` = `silenceHound`, then `extract(hostage, gate, 3)` (walk; cleanse and walk; or
  up to three drags or shoves, each bringing it nearer the gate by `progress/2`), then
  `confirmSafe`.

## Hypothesis

Measured with `htn_components combos escort_hostage`:

- No single skill wins, even when both companions hold it: 0 of 8.
- 30 of 64 assignments win (15 pairs, either way round), by 15 methods: one of five silencers
  (`net`, `flashbang`, `sleepDart`, `terrify`, `flameWall`) plus one of three movers
  (`magnetize`, `gust`, `cleanse`).
- No solo plan; no dead skill.

## Examples

### Example 1: Blind and drag

**Given:** the player knows `net`, the mage knows `magnetize`.

**When:** `win`

**Then:** the player nets the hound from the gate; the mage walks into the corridor, hooks the
hostage out of the cell, walks back to the gate and hooks it again.

### Example 2: Unshackle

**Given:** the player knows `terrify`, the mage knows `cleanse`.

**When:** `win`

**Then:** the hound is frightened (blinded); the mage cleanses the shackles from the corridor; the
hostage walks out to the gate.

### Example 3: Burn and shove

**Given:** the player knows `flameWall`, the mage knows `gust`.

**When:** `win`

**Then:** the player sets the kennel alight and the wooden hound burns (`dead`); the mage walks
through the cell to the bunk and gusts the hostage into the corridor, then steps into the cell and
gusts it on to the gate.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 15 measured pairs have a plan, whichever companion holds which half. |
| P3 | The hostage is spared | Fire goes only on the kennel; the hostage never burns or falls into the pit. |
| P4 | The hound first | The hound is silenced before anyone walks into the corridor. |
