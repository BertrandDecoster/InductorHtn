# The Wyvern Roost

## Purpose

A hazard-terrain level about **a flier that no hazard can take until it is on the ground**. A wyvern
roosts on a crag across a channel of lava, above a sheer cliff. While it flies, the lava, the drop
and a collapsing floor all leave it hovering. Nobody can hurt it; the mountain can, once it is down.
The player and the mage pick one skill each from a pool of eight, and it always takes both: one
brings it down, the other lets the mountain have it.

| Step | Skills | How |
|------|--------|-----|
| **Bring it down** | `net`, `entangle` (rooted), `sleepDart` (asleep), `rainCall` (soaked wings) | each lands something the wyvern answers by losing `flying` (level-local reactions) |
| **Pull it across the lava** | `magnetize`, `taunt` | from the ledge, the pull crosses the lava channel |
| **Push it off the crag** | `gust` | from the overlook, the push goes over the cliff |
| **Drop the crag from under it** | `collapse`; or `gust` the boulder off the overlook from the path | the crag's crust breaks under anything that lands on it |

Why no single skill works:
- Aloft, `flying` wards `fell`: pulled over the lava, pushed over the drop, or with the crag collapsed
  under it, it simply hovers there.
- A grounder alone leaves it standing on its crag.
- A sleeping wyvern that is taunted wakes up instead (a taunt is a blow, and `wakeOnHit` answers
  it), so `sleepDart` and `taunt` do not go together.

`gust` serves two roles: it pushes the wyvern over the cliff, or the boulder onto the crag.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp --- ledge  ~~ lava ~~  crag (wyvern) ::: cliff
           |                  :
          path --- overlook --'   (the overlook, with a loose boulder)
```

- **Walking:** camp-ledge, ledge-path-overlook. The lava, the crag and the cliff connect to nothing.
- **Line of sight:** the ledge and the overlook see the crag; the path sees the overlook.
- **Push lines:** a pull from the ledge on the crag crosses the lava; a push from the overlook on
  the crag goes over the cliff; a push from the path on the overlook lands on the crag.
- **Zones:** lava (`lava`), cliff (`chasm`), and the crag's crust (level-local:
  `effect(crust, target, spill(chasm))` - whatever lands on the crag breaks it).
- **Wyvern** (level-local rules): living, `tag(wyvern, flying)`, `wards(flying, fell)`, and
  `reaction(flying, rooted | asleep | wet, ...)`: each removes `flying` and stores the tag.
- **Boulder:** an object on the overlook.
- **Goal** `win`: `ground(wyvern)`, then `neutralize(wyvern)` (the generic pit recipe), a
  `dropFloor` (a spill of a hazard it is weak to) or a `rockslide` (an object pushed onto its crag).

## Hypothesis

Measured by `htn_components combos hazard_wyvern_roost` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 30 of 64 assignments win: 15 pairs, whichever companion holds which half - every grounder with
  every dropper, except `sleepDart` with `taunt`.
- 15 methods (distinct skill sets); the drops are of three kinds (a pull across lava, a push over
  the cliff, the floor dropped from under it). No solo plans; no dead skills.
- Every loss has a nameable reason: two grounders (nothing drops it), two droppers (it flies),
  `sleepDart` with `taunt` (the taunt wakes it).

## Examples

### Example 1: Net it, then hook it across the lava

**Given:** the player knows `net`, the mage knows `magnetize`.

**When:** `win`

**Then:** the net brings the wyvern down onto the crag; the mage hooks it from the ledge and it is
dragged across the lava channel and falls in.

### Example 2: Net it, then push it off

**Given:** the player knows `net`, the mage knows `gust`.

**When:** `win`

**Then:** the mage walks to the overlook and gusts the grounded wyvern off the crag, into the cliff.

### Example 3: Net it, then the rockslide

**Given:** the player knows `net`, the mage knows `gust`.

**When:** `win`

**Then:** the mage gusts the boulder off the overlook from the path; it lands on the crag, the crust
breaks, and boulder and wyvern go down together.

### Example 4: Sleep, then collapse

**Given:** the player knows `sleepDart`, the mage knows `collapse`.

**When:** `win`

**Then:** the sleeping wyvern drops onto the crag; the mage collapses the crag from under it.

### Example 5: Soak its wings, then taunt it

**Given:** the player knows `rainCall`, the mage knows `taunt`.

**When:** `win`

**Then:** the rain soaks its wings and it comes down; the taunt drags it across the lava.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Fifteen pairs win | Exactly the fifteen measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | A taunt wakes a sleeper | sleepDart with taunt: no plan. |
| P5 | Down before it falls | In every winning plan, `flying` comes off before a hazard takes it. |
| P6 | Aloft, it hovers | Hook, push or collapse on a flying wyvern: it stays in the fight; the same hook on a netted one takes it. |
