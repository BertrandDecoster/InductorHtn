# The Scholar

## Purpose

An escort level with an enemy behaviour to protect against. A **scholar** who cannot act must get
from the library to the exit. It is not a companion: it never casts, and it walks on its own when
the way is clear. The only door runs through the hall, where an armoured clockwork brute stands as
a blocker. From the balcony, a gap (a chasm) drops away to the exit landing, where an iron pillar is
bolted down. Two companions, the player and the mage, pick one skill each from a pool of eight.

Three methods, each needing both companions and differing in kind:

| Method | First | Then |
|--------|-------|------|
| **Move the brute** (then the scholar walks) | strip its armour: `sunder` | move it out of the doorway: push it into the pit from the library (`gust`), hook it onto the balcony or into the library (`magnetize`), lure it onto the balcony (`taunt`), or swap it away (`translocate`) |
| **Short it** (then the scholar walks) | soak it: `rainCall` | jolt it: `zap` (a machine soaked, then jolted, is dead) |
| **Swap it over** (the scholar never passes the brute) | one companion crosses: a dash (`pounce`) over the gap or into the hall, or a grappling hook (`magnetize`) to the pillar or onto the armoured brute | the other (`translocate`) swaps with it to reach the exit, then swaps the scholar over from the balcony |

`magnetize` and `translocate` each serve two roles: magnetize moves the stripped brute, or carries
its caster across as a grappling hook; translocate swaps the stripped brute out of the doorway, or
ferries a companion and then the scholar over the gap.

Why no single skill works:
- `sunder` alone leaves the brute in the doorway; a mover alone meets the armour (a push or a pull
  does nothing; a hook drags the caster in instead).
- `rainCall` alone only soaks it; a dry `zap` only stuns it, and a stunned brute still fills the
  doorway.
- `pounce` or `magnetize` alone gets a companion across, but nothing brings the scholar: dragging it
  over the gap drops it into the chasm. `translocate` alone has nobody on the far side to swap with.

The protect trap (an enemy behaviour): `behavior(brute, taunted, slam, here)` with
`effect(slam, area, grant(stunned))`. A taunted brute is dragged to whoever taunted it, then slams
the floor there, stunning everyone around it. Taunt it from the library and the scholar is stunned
where it stands (rooted) and can never walk out. Lure it from the balcony, away from the scholar.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
library (scholar, player, mage) --- hall (brute) --- exit (pillar)
   |                                  :
balcony ..... gap (chasm) ....... exit     pit (chasm, beyond the hall from the library)
```

- **Walking:** library-hall-exit, library-balcony. The hall is the brute's (a blocker).
- **Lines:** a push from the library on the hall lands in the pit; the gap lies between the balcony
  and the exit, both ways.
- **Line of sight:** library-hall, library-balcony, balcony-hall, balcony-exit, exit-hall.
- **Route (`progress/2`):** library 0, balcony and hall 1, exit 2 (for `passage`'s leaps).
- **Brute:** machine, armoured, blocker; its taunt behaviour above. **Pillar:** heavy (an anchor
  for a grappling hook).
- **Goal:** `win` = `clearWay(brute)` then the scholar walks out; or `swapAcross(scholar, exit)`.
  Both end with `confirmSafe` (at the exit, not gone).

## Hypothesis

Measured with `htn_components combos escort_scholar`:

- No single skill wins, even when both companions hold it: 0 of 8.
- 14 of 64 assignments win (7 pairs, either way round), by 7 methods:
  - `sunder` plus `gust`, `magnetize`, `taunt` or `translocate`: 4 pairs;
  - `rainCall` plus `zap`;
  - `translocate` plus `pounce` or `magnetize`: 2 pairs.
- No solo plan; no dead skill.

## Examples

### Example 1: Strip and lure

**Given:** the player knows `sunder`, the mage knows `taunt`.

**When:** `win`

**Then:** the player sunders the armour; the mage goes out on the balcony and taunts the brute,
which is dragged there and slams, stunning the mage; the scholar walks through the empty hall.

### Example 2: Soak and jolt

**Given:** the player knows `rainCall`, the mage knows `zap`.

**When:** `win`

**Then:** the rain soaks the brute; the jolt short-circuits it (`dead`); the scholar walks out.

### Example 3: Swap across

**Given:** the player knows `pounce`, the mage knows `translocate`.

**When:** `win`

**Then:** the player pounces over the gap to the exit; the mage, on the balcony, swaps with the
player; the scholar steps onto the balcony and the mage swaps it over to the exit.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 7 measured pairs have a plan, whichever companion holds which half. |
| P3 | Never lure it onto the scholar | Taunted from the library, the brute's slam stuns the scholar; every winning taunt plan lures it onto the balcony. |
| P4 | The scholar is never dragged | No winning plan moves the scholar by a push or a pull; it walks, or it is swapped. |
