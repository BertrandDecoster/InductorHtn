# Sync: The Decoy

## Purpose

A synchronisation level: **one companion baits an enemy while the other slips past it to the
switch**. A stone golem blocks the arch to the switch room and, from wherever it stands, watches the
hall in front of it. Two companions, the player and the mage, pick one skill each from a pool of
eight. The decoy gets the golem out of the arch; the slipper waits in the nook, apart, then crosses
the hall unseen and steps onto the switch. The Lost Vikings / Trine split: one draws the fire, one
does the job.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The arch** | the golem is a `blocker`: nobody walks into its region | drag it out: `taunt` (dragged to the taunter, which it then slams), `magnetize` (hooked to the caster); shove it into the alcove from the nook: `gust`, `tidalWave` |
| **The hall** | `watches(golem, hall)`: nobody walks in seen, wherever the golem stands | the slipper goes stealthed (`vanish`, `smokeBomb`); someone blinds the golem (`flashbang`, `net`, `smokeBomb`) |

Why no single skill works:
- Moving the golem out of the arch does not stop it watching the hall.
- Blinding the golem, or going stealthed, does not move it out of the arch.
- The nook does not open onto the arch: the only way to the switch is across the hall.

The decoy pays for it: a taunted golem is dragged to its taunter and slams the ground there
(`behavior(golem, taunted, slam, here)`, `slam` = area stun), so the taunter is stunned where it
stands, and so is anyone standing with it. That is why the slipper waits in the nook, and why in
every taunt plan the one who reaches the switch is the other companion.

`smokeBomb` serves two roles: it stealths its thrower (who then slips) or it blinds the golem (for
whoever slips).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp (player, mage) --- hall (watched) --- arch (golem) --- switch [plate] --- portcullis (door)
    \                  /      \
     nook -------------        alcove
```

- **Lines of sight:** camp and nook each see the hall, the arch, the alcove and each other.
- **Push line:** from the nook, a push on the arch lands in the alcove.
- **Golem:** living, `blocker`, `watches(golem, hall)`, slams on being taunted.
- **Switch:** a zone with `open(portcullis)`: the portcullis latches open when someone steps on.
- **Goal:** `win` = the slipper `?b` walks to the nook; `lure` (a pull, or a shove along the line);
  `veil(?b)` (stealth for `?b`, or a blinded golem); `?b` walks onto the switch; the portcullis
  must be open.

## Hypothesis

Measured with `htn_components combos sync_decoy` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 32 of the 64 assignments win: each of the 4 lures with each of the 4 veils, whichever companion
  holds which (16 pairs).
- 16 methods (distinct sets of skills cast), 0 solo plans, no dead skill: every skill is in 8
  winning assignments.
- Every losing pair has a named reason: two lures (the hall is still seen), two veils (the arch is
  still held).

## Examples

### Example 1: The decoy is slammed, the slipper walks

**Given:** the player knows `taunt`, the mage knows `flashbang`.

**When:** `win`

**Then:** the mage waits in the nook; the player taunts the golem, which is dragged to the camp and
slams the player (stunned); the mage flashbangs the golem blind, crosses the hall, and steps onto the
switch; the portcullis opens.

### Example 2: Shoved into the alcove, then sneak

**Given:** the player knows `vanish`, the mage knows `gust`.

**When:** `win`

**Then:** from the nook the mage gusts the golem out of the arch into the alcove; the player vanishes
and walks across the hall onto the switch.

### Example 3: Hooked away, then netted

**Given:** the player knows `magnetize`, the mage knows `net`.

**When:** `win`

**Then:** the player hooks the golem out of the arch; the mage nets it (rooted and blinded); the
slipper crosses the hall to the switch.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Sixteen pairs win | Exactly the 16 lure-by-veil pairs have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | The taunter never slips | In a taunt plan, the switch is reached by the other companion. |
| P5 | Blinding does not clear the arch | A veil alone leaves the switch out of reach. |
