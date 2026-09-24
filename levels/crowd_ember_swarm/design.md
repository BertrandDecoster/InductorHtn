# Ember Swarm

## Purpose

A crowd-control level (category 8): **one shared surface catches the whole group, in the right
order.** Three ember beetles swarm in a nest, still aflame. An ember freezes solid once its fire is
out; a chill on a burning one only quenches it (the catalogue's `quench`), and an iced room does not
chill again. So the whole swarm has to be doused first, then frozen - two steps, two companions.
The player and the mage pick one skill each from a pool of seven. Nothing grants an outcome: `frozen`
comes from the beetles' own weakness, declared in the level.

The level's goal is a crowd recipe, spelled out top-down from the need: every beetle's fire out
(`douseAll`: blanket its room, or blow its flame out), then every beetle frozen (`freezeAll`: chill
its room, or move it into a room that chills - drag it there, or frighten it there).

| Step | Skills | How |
|------|--------|-----|
| **Douse** | `rainCall` | the nest floods: the fire goes out (`extinguish`) |
| | `glaciate`, `iceStorm` | the nest ices: the fire is quenched - and the nest will not chill again |
| | `gust` | one beetle at a time: the flame is blown out |
| **Freeze** | `glaciate`, `iceStorm` | ice a doused nest: the whole swarm freezes |
| | `roar` | from the ridge, round the corner: the frightened swarm runs into the ice cave |
| | `provoke`, `taunt` | from the ice cave: the whole nest (provoke) or one beetle at a time (taunt) is dragged into the ice |

Why no single skill works: a douse alone leaves them standing. A freeze alone reaches a burning
swarm, which only quenches (a chill cast on it) or slows (a beetle frightened or dragged into the
ice). The cold skills can't do both halves, because the nest ices only once. And a frightened or
taunted beetle can't be moved the same way a second time: the tag is already there.

The traps: freezing first (`glaciate` + `iceStorm`: the first quenches, the second finds the nest
already iced); two herders (`roar` + `provoke`: the swarm reaches the ice still burning); two douses
(`rainCall` + `gust`).

Skills serving two roles: `glaciate` and `iceStorm` douse in one plan (quench) and freeze in
another (a doused nest).

Level-local physics (wishlist evidence): `weakness(?e, chilled, burning, slowed)` declared before
`weakness(?e, chilled, none, frozen)` for the `ember` trait. The catalogue's `insect` would not do:
a beetle dragged or frightened into ice lands in *raw* mode (an `onGrant` movement), which skips the
`quench` reaction, so a burning insect would freeze outright, and `provoke` alone would win.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage)
 |
ridge --- nest (b1, b2, b3, burning) --- icecave (iceSheet)
```

- **Line of sight:** the gate overlooks the nest and the ice cave; the ice cave sees the nest. The
  ridge is round the corner: it has no sight of the nest, so only a melee skill works from there.
- **Lines:** a push from the ridge on the nest throws it into the ice cave.
- **Zones:** the ice cave is an `iceSheet`: whoever arrives is chilled.
- **Beetles:** trait `ember`, burning. Both companions have 2 mana.

## Hypothesis

Measured with `htn_components combos crowd_ember_swarm` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 32 of 49 assignments win (16 unordered pairs, whichever companion holds which half): a douser
  (`rainCall`, `gust`) with a cold skill or a herder (10 pairs), and a cold skill with a herder
  (6 pairs).
- 16 methods, in four kinds: douse + freeze in place, douse + drive into the ice, douse + drag into
  the ice, quench + move into the ice. No dead skill: every skill is in 8 to 10 winning assignments.
- The losing pairs: two cold skills, two herders, two douses.
- One replan takes about 0.5 s; the whole matrix under 5 s.

## Examples

### Example 1: Rain, then roar them into the ice

**Given:** the player knows `rainCall`, the mage knows `roar`.

**When:** `win`

**Then:** rain on the nest puts all three fires out. The mage walks to the ridge and roars: the
frightened swarm runs into the ice cave and freezes.

### Example 2: Quench, then drag into the ice

**Given:** the player knows `glaciate`, the mage knows `provoke`.

**When:** `win`

**Then:** the player ices the nest (the fires are quenched, nobody freezes). The mage walks into the
ice cave and provokes the nest: the swarm is dragged into the ice and freezes.

### Example 3: Blow them out, then freeze

**Given:** the player knows `gust`, the mage knows `iceStorm`.

**When:** `win`

**Then:** three gusts blow out three flames; one iceStorm on the nest freezes the swarm.

### Example 4: Trap - cold twice, or two herders

**Given:** `glaciate` and `iceStorm`; or `roar` and `provoke`.

**When:** `win`

**Then:** no plan. The first cold quenches and the second finds the nest already iced; the herders
bring a burning swarm to the ice, and it only slows.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Sixteen pairs win | Exactly the sixteen measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | Douse before freeze | In every winning plan, all three fires are out before any beetle freezes. |
