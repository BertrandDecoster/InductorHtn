# The Gauntlet

## Purpose

The pure-movement level on the ability layer. Nothing dies except by falling. Three companions have
to reach the exit: the player and the mage pick **one skill each** from a pool of six movement
skills, and the Warden, who only knows `sunder`, cannot leap - so the guard has to be moved out of
his way and the chasm has to be bridged for him. Three obstacles, each with several answers:

| Obstacle | Answers |
|----------|---------|
| **The armoured guard at the choke** | The Warden sunders the armour; then someone drops it through the trapdoor (`gust`, `shieldBash` from the start) or moves it out of the doorway (`magnetize` drags it back, `translocate` swaps with it). |
| **The plate in the grated alcove** (latches the gate) | Nobody walks onto it. A dasher blinks onto it (`shadowStep`, `pounce`) and dashes on over the chasm; or a pusher throws a friend onto it from the rim (`gust`), and the friend gets out forward: hooks the far pillar (`magnetize`) or swaps with the idol across (`translocate`). |
| **The chasm** | The crate bridges it for the Warden: two pushes (`gust`, `shieldBash`: onto the rim, then in), or a hook hauls it to the rim, the hooker grapples across on the pillar and drags it in from the far side (`magnetize`). |

The crate can hold the plate or fill the chasm - not both: on the plate it strands the Warden.

Why no single skill wins, even held by both seats:
- a pusher cannot leave the alcove, so whoever it throws onto the plate is stranded;
- a dasher or a swapper cannot move the crate, so the Warden stays behind;
- `magnetize` alone cannot get anyone onto the plate.

Traps: `shieldBash` throws a friend onto the plate *stunned* - silenced, the friend cannot grapple or
swap out. Two pushers only strand each other.

Several skills serve several roles: `gust` drops the guard, throws a friend and pushes the crate;
`magnetize` drags the guard, hauls the crate, grapples the pillar out of the alcove and across the
chasm; the dashes cross the choke, land on the plate and cross the chasm.

## Layer

level

## Dependencies

- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
start --- choke (guard) --- hall (crate) --- rim ~~ chasm ~~ far (pillar, idol) --- gate --- exit
  |                          :       :                         :
 pit (trapdoor)            alcove (plate; seen from the hall, the rim and far; never walked into)
```

- **Lines:** from the start, a push on the choke lands in the pit; from the hall, back to the start.
  From the choke a push on the hall lands on the rim; from the rim, in the alcove; from the hall, a
  push on the rim lands in the chasm. The chasm lies between the rim and far, so a pull from far
  drops what stands on the rim into it.
- **Line of sight:** start-choke-hall-rim (both ways, but the hall does not see the start), the
  hall and the rim see the alcove, the alcove and the rim see far, and far sees both back.
- **Guard:** living, armoured, a blocker. **Crate:** a filler, mindless. **Pillar:** heavy (an
  anchor). **Idol:** light (a swap target).
- **Warden:** knows `sunder` only. The player and the mage start with `gust` and `shadowStep`.

## Hypothesis

Measured by `htn_components combos gauntlet` (every assignment replanned, ~60 s in parallel; the
slowest plan about 25 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 16 of 36 assignments win (both seat orders counted): gust + {magnetize, translocate, shadowStep,
  pounce} and magnetize + {shadowStep, pounce} either way round; shieldBash + {shadowStep, pounce}
  either way round; `translocate` only as the thrown friend (mage) with the player pushing.
- 8 methods (sets of skills cast), of four kinds: dash onto the plate + push the crate; throw a
  friend who grapples out; throw a friend who swaps out; dash onto the plate + haul the crate.
- No dead skill; no plan carried by one companion.

## Examples

### Example 1: Dash onto the plate, push the crate

**Given:** the default kit (player `gust`, mage `shadowStep`).

**When:** `win`

**Then:** the Warden sunders the guard and the player gusts it into the pit; the mage dashes onto the
plate and on over the chasm; the player pushes the crate in twice; everyone walks out.

### Example 2: Throw a friend who grapples out

**Given:** player `gust`, mage `magnetize`.

**When:** `win`

**Then:** the player gusts the mage from the rim onto the plate; she hooks the pillar and is dragged
across; the player bridges the chasm with the crate.

### Example 3: Throw a friend who swaps out

**Given:** player `gust`, mage `translocate`.

**When:** `win`

**Then:** thrown onto the plate, the mage swaps places with the idol across the chasm.

### Example 4: Haul the crate to the rim

**Given:** player `magnetize`, mage `shadowStep`.

**When:** `win`

**Then:** the player hooks the crate from the hall to the rim, grapples across on the pillar, and
drags the crate into the chasm from the far side.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions acting. |
| P2 | The crate cannot do both | With the crate on the plate, the Warden cannot reach the exit. |
| P3 | No single skill wins | Each pool skill held by both seats: no plan. |
| P4 | The measured assignments win | Exactly the 16 measured assignments have a plan, and `combos` passes. |
| P5 | A bashed friend is stunned | `shieldBash` + `magnetize` loses: the thrown mage cannot grapple out. |
