# Ember Swarm

## Purpose

A crowd-control level (category 8): **one shared surface catches the whole group, in the right
order.** Three ember beetles swarm in a nest, still aflame. They are insects: the cold kills them
(the catalogue's `weakness(?e, chilled, none, dead)` for `insect`) - but not while they burn. A chill
on a burning beetle only quenches it (`quench`), and a region ices over only once. So the whole swarm
has to be doused first, then frozen - two steps, two companions. The player and the mage pick one
skill each from a pool of six. Nothing grants an outcome: `dead` is the insects' own weakness.

The douse must leave the beetles dry: fire meeting water (`extinguish`) or cold (`quench`) cancels
both, but a beetle soaked after its fire is out would only freeze (`wet` + `chilled` = stunned).

The level's goal is a crowd recipe, spelled out top-down from the need: every beetle's fire out
(`douseAll`: lay on it a tag its fire reacts to by going out), then every beetle dead (`freezeAll`:
lay on it the tag it is lethally weak to). Laying a tag (`lay`) is one of three things: a skill that
gives it, cast on the beetle or everyone around it; a pull-in or push into a region that gives it
(`placement/6`); or a drag into such a region by someone standing in it.

| Step | Skills | How |
|------|--------|-----|
| **Douse** | `tidalWave` | from the nest: the wave soaks everyone around, the fires go out |
| | `blizzard` | the nest ices: the fires are quenched - and the nest will not chill again |
| | `vortex` | on the brook: the swarm is sucked into the deep water, and pinned there |
| **Freeze** | `blizzard` | on the doused swarm: the nest, or the brook (the water ices into a floor) |
| | `vortex` | on the ice cave: the whole nest is sucked into the ice |
| | `taunt`, `hook` | from inside the ice cave: one beetle at a time is dragged into the ice |

Why no single skill works: a douse alone leaves them standing. A freeze alone reaches a burning
swarm, which only quenches. Blizzard cannot do both halves, because the nest ices only once. A vortex
pins what it gathers: this level declares `wards(rooted, forcedMove)` ("suck enemies into one spot
and pin them there"), so a second vortex cannot fetch the swarm back out of the ice or the brook. A
taunted beetle cannot be taunted again, and the ice cave cannot see the brook, so no dragger yo-yos
a beetle from one to the other.

Skills serving two roles: `blizzard` douses (quench) in one plan and freezes in another; `vortex`
douses (into the brook) in one plan and freezes (into the ice cave) in another.

The traps: cold twice (`blizzard` + `blizzard`); a vortex into the ice first (quenched and pinned);
two waves (the second soaks the doused swarm, which then only freezes); dragging the beetles into
the brook yourself (`taunt`, `hook`: the blizzard that freezes them freezes you, and the plan is
refused); `fireball`, which relights the nest and pushes nobody anywhere useful. Fireball is the one
skill that wins nothing: every fire relights the region it lands on.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp (player, mage) --- gate --- nest (b1, b2, b3; insects, burning) --- icecave (iceSheet)
                                  |
                                brook (deepWater)
```

- **Line of sight:** the gate overlooks the nest, the brook and the ice cave; the brook and the ice
  cave each see the nest, not each other.
- **Zones:** the ice cave is an `iceSheet` (slowed, chilled); the brook is `deepWater` (wet; nothing
  here is heavy).
- **Level physics:** `wards(rooted, forcedMove)` - a vortex pins what it gathers.
- **Beetles:** `insect`, `burning`. Both companions have 2 mana: one wave, blizzard or fireball each.
- **The team:** a plan that leaves a companion frozen (stunned) is refused (`teamFit`).

## Hypothesis

Measured with `htn_components combos crowd_ember_swarm` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 14 of 36 assignments win (7 unordered pairs, whichever companion holds which half):
  `tidalWave` with `blizzard`, `vortex`, `taunt` or `hook`; `blizzard` with `vortex`, `taunt` or
  `hook`.
- 7 methods (distinct skill sets cast), in two kinds of douse (water, cold) and two kinds of freeze
  (freeze in place, move into the ice). Skill usage: `tidalWave` 8, `blizzard` 8, `vortex` 4,
  `taunt` 4, `hook` 4, `fireball` 0 (a trap).
- No solo plans. One replan takes 0.3 to 4 s; the whole matrix well under a minute.

## Examples

### Example 1: A wave, then a vortex into the ice

**Given:** the player knows `tidalWave`, the mage knows `vortex` (the default kit).

**When:** `win`

**Then:** the player walks into the nest and bursts a wave: the three fires go out. The mage casts a
vortex on the ice cave from the gate: the swarm is sucked into the ice and dies of the cold.

### Example 2: Quench, then drag into the ice

**Given:** the player knows `blizzard`, the mage knows `taunt`.

**When:** `win`

**Then:** the blizzard ices the nest: the fires are quenched, nobody dies. The mage walks across the
ice into the ice cave and taunts the beetles one at a time: each is dragged into the ice and dies.

### Example 3: One vortex, two roles

**Given:** the player knows `vortex`, the mage knows `blizzard`.

**When:** `win`

**Then:** two plans. The vortex sucks the swarm into the brook (the fires go out, the swarm is
pinned) and the blizzard ices the brook into a floor, freezing them; or the blizzard quenches the
nest and the vortex sucks the swarm into the ice cave.

### Example 4: Traps

**Given:** `blizzard` twice; `vortex` twice; `taunt` and `hook`; `tidalWave` twice; `fireball` and
`blizzard`.

**When:** `win`

**Then:** no plan. The nest ices once; a vortexed swarm is pinned; the brook and the ice cave do not
see each other; the second wave soaks them and wet beetles only freeze; fire relights the nest.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Seven pairs win | Exactly the seven measured pairs have a plan. |
| P3 | Each hand matters | Every winning pair wins whichever companion holds which half. |
| P4 | Douse before freeze | In every winning plan all three fires are out before any beetle dies, and no companion is left frozen. |
