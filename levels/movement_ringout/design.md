# Ring-Out

## Purpose

A pure-movement ring-out, after Into the Breach: an ogre stands on a plinth at the edge of the void,
and the only victory is getting it into the void. Nothing hurts it. The ogre never starts on a line
into the void - a push from the yard only shoves it back onto the ledge - so one companion has to
move something first and the other finishes. The player and the mage pick **one skill each** from
seven movement skills.

| Method | First | Then |
|--------|-------|------|
| **Lure it onto the brink** | pull it to your feet on the brink (`magnetize`, `taunt`), or stand on the brink and swap with it (`translocate`) | push it off the brink from the yard (`gust`, `shieldBash`) |
| **Get behind it** | land on the perch, which opens the grate: blink up (`shadowStep`, `pounce`) or swap with the idol (`translocate`) | walk round through the grate to the ledge and push it off the plinth (`gust`, `shieldBash`) |
| **Drag it across** | the swapper gets onto the perch (the idol), then swaps the puller up (`translocate`) | from the perch, pull it across the void (`magnetize`, `taunt`) |

Why no single skill wins, even held by both seats:
- a pusher alone never finds a line into the void: the yard push lands on the ledge, and the ledge
  is behind the grate;
- a puller alone drags it onto the brink, then nobody pushes; and no puller can reach the perch;
- a dasher or a swapper on the perch has nothing to push or pull with.

`translocate` plays three roles (swap the ogre onto the brink, climb the perch, ferry a friend up);
`magnetize` and `taunt` two (lure onto the brink, drag across the void).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
              perch (idol; plate: opens the grate)
                :
  gate --- yard ---------- grate (door) --- ledge
             |   \                            |
           brink  plinth (ogre) --------------+
             |       \
            void      void (between the perch and the plinth)
```

- **Lines:** from the yard, a push on the brink lands in the void; from the ledge, a push on the
  plinth lands in the void; from the yard or the brink, a push on the plinth lands on the ledge. The
  void lies between the perch and the plinth, so a pull from the perch drops the ogre in.
- **Line of sight:** the yard sees the gate, the brink, the plinth and the perch; the brink and the
  ledge see the plinth; the perch sees the yard, the gate and the plinth.
- **Ogre:** living, a blocker. **Idol:** light, on the perch (a swap target). The perch is not
  walkable; the grate opens for good when something lands on the perch.

## Hypothesis

Measured by `htn_components combos movement_ringout` (~15 s for all 56 replans; one plan < 5 s):

- No single skill wins, even when both seats hold it: 0 of 7.
- 24 of 49 assignments win: 12 unordered pairs, each in both seat orders - every pusher (`gust`,
  `shieldBash`) with every non-pusher (10 pairs), and `translocate` with `magnetize` or `taunt`.
- 12 methods, of three kinds (lure + push, open the grate + push from behind, ferry a puller up and
  drag across). No dead skill; no plan carried by one companion.

## Examples

### Example 1: Lure it onto the brink, then push

**Given:** the default kit (player `gust`, mage `magnetize`).

**When:** `win`

**Then:** the mage hooks the ogre from the brink onto the brink; the player gusts it off into the
void.

### Example 2: Open the grate, push from behind

**Given:** player `gust`, mage `shadowStep`.

**When:** `win`

**Then:** the mage blinks onto the perch and the grate opens; the player walks round to the ledge and
gusts the ogre off the plinth.

### Example 3: Ferry the puller across the void

**Given:** player `translocate`, mage `taunt`.

**When:** `win`

**Then:** the player swaps places with the idol on the perch, then swaps the mage up; her taunt drags
the ogre across the void.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has both companions acting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured pairs win | Exactly the 12 measured pairs win, in both seat orders, and `combos` passes. |
| P4 | A push from the yard is not enough | Two pushers cannot ring it out. |
