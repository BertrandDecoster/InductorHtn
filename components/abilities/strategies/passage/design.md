# Passage

## Purpose

The movement recipes: getting everyone through, around, over, or by moving whatever is in the way.
A level lays out its route with `progress(?r, ?n)` (higher is further along) and names its
obstacles. These recipes say how each kind of obstacle is overcome, each in several ways. The
catalogue's skills are what make the ways many: a hook is a way across (to an anchor), a way to drop
an enemy (across a pit), and a way to bridge (drag a crate in); a swap is a way past a guard, a way
across, and a way to ferry a friend.

| Recipe | Ways |
|--------|------|
| `reach(?a, ?r)` | Walk. Or leap forward and carry on: a dash or blink to a region, a hook to something anchored there, a swap with someone standing there, or an ally who swaps you forward. At most two leaps. |
| `openWay(?d)` | A door latches open when something weighs down its plate. Someone walks on (with leaps if needed), or something is pushed onto it. |
| `span(?g)` | Push something that fills a gap into it (one push, or two), drag it in across the gap, or leave the gap for everyone to cross on their own. |
| `clear(?e)` | Drop a blocker into a hazard, move it out of its doorway (`dislodge`), or leave it for everyone to get past. |

Leaps only go forward along the route, so every decomposition ends.

## Layer

strategy

## Dependencies

- `abilities/goals/neutralize`

## Operators

None.

## Methods

| Method | Description |
|--------|-------------|
| `reach(?a, ?r)` / `reachWithin(?a, ?r, ?n)` | Walk if a route exists; else one of `?n` forward leaps (own skill or an ally's swap), then again. |
| `openWay(?d)` | Already open; someone reaches the plate; or something is pushed onto it. Confirms the door is open. |
| `span(?g)` | Already filled; left; one push; two pushes; a pull across. Confirms the gap is filled when it bridges. |
| `clear(?e)` | Already out; `neutralize`; `dislodge`; left. |

## Rules

| Rule | Description |
|------|-------------|
| `leap(?a, ?ab, ?from, ?aim, ?land)` | `?a`, walking to `?from`, lands ahead at `?land` by a dash, a hook on an anchored thing, or a swap. Cheap tests first, the route search last. |
| `ferry(?a, ?b, ?ab, ?land)` | Ally `?b`, standing ahead at `?land`, can swap `?a` to it. |
| `ahead(?from, ?to)` | `?to` is further along the route. |
| `plateOf(?p, ?d)` / `filler(?x)` | The plate that opens a door; something that fills a gap. |

## Required Facts

`progress/2` for the route; the ability layer's facts; `door/1` and a plate zone with `open(D)`;
fillers (`trait(?x, filler)`).

## Examples

### Example 1: A walk

**Given:** the player at `a`, `b` next to it.

**When:** `reach(player, b)`

**Then:** one step, no cast.

### Example 2: A leap over the gap

**Given:** a live gap between `b` and `c`; the player knows `shadowStep`.

**When:** `reach(player, e)`

**Then:** the player blinks to `c` and walks on.

### Example 3: A hook to the pillar

**Given:** a heavy pillar at `c`; the player knows `magnetize`.

**When:** `reach(player, c)`

**Then:** the hook drags the player across (`opDash(player, b, c)`).

### Example 4: A friend swaps you over

**Given:** the mage at `c` knows `translocate`.

**When:** `reach(player, c)`

**Then:** the mage swaps the player over.

### Example 5: The door latches

**Given:** plate `p` opens door `d`.

**When:** `openWay(d)`

**Then:** the player walks onto the plate; the door is open for good.

### Example 6: The crate bridges the gap

**Given:** a crate at `b`, `beyond(a, b, gap)`; the player knows `gust`.

**When:** `span(gap)`, then `reach(player, c)`

**Then:** the crate falls into the gap and the player walks over it.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Leaps only go forward | A scout across the gap has no way back. |
| P2 | A pull across bridges too | A crate beyond the gap, hooked from the near side, falls in and fills it. |
| P3 | Nobody crosses a live gap on foot | Without a leap there is no plan. |
