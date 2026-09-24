# The Wyvern Roost

## Purpose

A hazard-terrain level where **the mountain is the weapon, and the mountain can be reshaped**. A
wyvern roosts on a crag across a channel of lava, above a sheer cliff. While it flies, neither the
lava nor the drop can take it (`wards(flying, fell)`). Nobody can hurt it; the mountain can, once it
is on the ground. The player and the mage pick one skill each from a pool of six catalogue skills.

Its wings fail it (level-local reactions, each a `remove(flying)` plus the tag that came in): soaked
(`wet`), frosted (`chilled`), or struck (`electrocuted`).

| Method | First | Then |
|--------|-------|------|
| **Ground it, drop it** | freeze the crag (`blizzard`) or strike the wyvern (`lightningFlash`, which dashes the caster onto the crag) | pull it across the lava from the ledge (`hook`, `taunt`), or blast it off the crag into the cliff from the overlook (`fireball`) |
| **Fetch it, wash it back** | hook or taunt the flyer across the lava onto the ledge (`hook`, `taunt`): flying, it just crosses; the puller steps aside | a wave from the camp (`tidalWave`) soaks its wings and washes it into the lava |
| **Cool the lava, wade out** (terrain) | a `blizzard` on the lava channel: lava meeting an ice sheet leaves no zone - cooled rock | walk out onto the rock next to the crag; a `tidalWave` soaks the wyvern and washes it over the cliff |

Terrain chemistry does the work twice: the blizzard turns the lava into ground, and a fireball on a
frozen crag melts the ice sheet into a puddle (`zoneReaction(iceSheet, flames, puddle)`) - the
frosted wyvern is soaked where it stands, freezes solid (`freezeOver`), and goes over the cliff.

Why no single skill works:
- Flying, it is pulled over the lava or pushed over the drop and simply hovers.
- A grounder alone leaves it grounded on the crag; nothing reaches it on foot.
- A wave needs to stand next to it: only on the ledge (fetched) or on cooled rock.

Traps: cool the lava and nobody can drop it in any more; whoever stands on the ledge when the wave
comes goes into the lava with it.

`blizzard` serves two roles (frost the wings; cool the lava), and so do `tidalWave` (wash the fetched
flyer back into the lava; wash it off the crag from the rock), `hook` and `taunt` (drag the grounded
wyvern into the lava; fetch the flyer over it).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp --- ledge ~~ lava ~~ crag (wyvern) ::: cliff
           |                 :
          path --- overlook -'   (the overlook looks down on the crag)
```

- **Walking:** camp-ledge-path-overlook; ledge-lava-crag, but the lava is a live hazard and the
  wyvern holds the crag (a blocker). Once cooled, the channel is walkable.
- **Line of sight:** camp to ledge; ledge to lava and crag; overlook to crag.
- **Push lines:** a pull from the ledge on the crag crosses the lava; a push from the overlook, or
  from the lava channel, throws the crag's occupant over the cliff; a push from the camp throws the
  ledge's occupant into the lava.
- **Zones:** the channel is `lava`, the cliff is `chasm`.
- **Wyvern:** `tag(wyvern, living)`, `tag(wyvern, flying)`, blocker; reactions `sodden`, `frosted`,
  `struck`.
- Both companions have 2 mana (one blizzard, fireball, tidalWave or lightningFlash).
- **Goal** `win`, with `standing()` after each: `neutralize(wyvern)`; `ground(wyvern)` then
  `neutralize`; `fetch(wyvern)` then `neutralize`; or `cool()` then `neutralize`.

## Hypothesis

Measured by `htn_components combos hazard_wyvern_roost` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 18 of 36 assignments win: 9 pairs, whichever companion holds which half:
  - ground, drop: `blizzard` or `lightningFlash`, plus `hook`, `taunt` or `fireball` (6 pairs);
  - fetch, wash back: `tidalWave` plus `hook` or `taunt` (2 pairs);
  - cool, wade out: `blizzard` + `tidalWave`.
- 9 methods (distinct skill sets) of three kinds. No solo plans; no dead skills.

## Examples

### Example 1: Frost, then hook

**Given:** the player knows `blizzard`, the mage knows `hook`.

**When:** `win`

**Then:** the player's blizzard ices the crag and frosts the wyvern's wings; the mage hooks it from
the ledge, and it is dragged into the lava.

### Example 2: Ice, then fire

**Given:** the player knows `blizzard`, the mage knows `fireball`.

**When:** `win`

**Then:** the blizzard frosts the wyvern; the mage's fireball from the overlook melts the ice sheet
into a puddle, the soaked, chilled wyvern freezes solid, and the blast throws it over the cliff.

### Example 3: Fetch it, wash it back

**Given:** the player knows `hook`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the player hooks the flying wyvern across the lava onto the ledge and steps aside; the
mage's wave from the camp soaks its wings and washes it back into the lava.

### Example 4: Cool the lava

**Given:** the player knows `blizzard`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the player's blizzard on the channel cools the lava to rock; the mage walks out onto it
and raises a wave that soaks the wyvern and washes it over the cliff.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Nine pairs win | Exactly the nine measured pairs have a plan. |
| P3 | A flyer just hovers | hook + fireball, taunt + fireball, hook + taunt: no plan. |
| P4 | Blizzard, two roles | With taunt it grounds the wyvern; with tidalWave it turns the lava into ground. |
| P5 | Nobody falls | No winning plan washes a companion into the lava. |
