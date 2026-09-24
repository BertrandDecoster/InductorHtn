# Ember Swarm

## Purpose

A crowd-control level (category 8): **one shared surface catches the whole group, in the right
order.** Three ember beetles swarm in a nest at the bottom of a ravine, still aflame. They are
insects: the cold kills them (the catalogue's `weakness(?e, chilled, none, dead)` for `insect`) - but
not while they burn. A chill on a burning beetle only quenches it (`quench`), an area ices over only
once, and a wet beetle chilled only freezes (`wet` + `chilled` = stunned). So the whole swarm has to
be doused and left dry first, then chilled - two steps, two companions. The player and the mage pick
one skill each from a pool of six. Nothing grants an outcome: `dead` is the insects' own weakness.

The map is four coarse areas in a line - camp, ridge, ford, nest - and the swarm only leaves the
nest when it is herded: a taunt (the beetle walks after its taunter, through every zone on the way)
or a hook (one area at a time). Knockbacks never change the area; they throw the swarm into the
features of its area: the **spring** in the nest (a pool: wet) and the **frost vent** on the ridge
(a crevasse breathing cold: slowed and chilled). The **ford** between them is shallow water: whoever
wades it is soaked. So herding the swarm out of the nest is a douse by itself.

The level's goal is a crowd recipe, spelled out top-down from the need: every beetle's fire out
(`douseAll`: lay on it a tag its fire reacts to by going out), then every beetle dead (`freezeAll`:
lay on it the tag it is lethally weak to). Laying a tag (`lay`) is one of three things: a skill that
gives it, cast on the beetle, its area or everyone around the caster; herding the beetle into an area
whose zone gives it; or herding the whole swarm to a feature that gives it and knocking the beetle in
(`knockOn`).

| Step | Skills | How |
|------|--------|-----|
| **Douse** | `tidalWave` | from the nest: the wave soaks everyone around, the fires go out |
| | `vortex` | on the spring: the whole swarm is knocked into the water |
| | `shieldBash` | each beetle into the spring |
| | `taunt`, `hook` | herd the swarm into the ford: taunted, they walk after you; hooked, one at a time |
| **Chill** | `blizzard` | on the doused swarm, wherever it stands: the nest, or the ford (its water ices over) |
| | `vortex` | on the frost vent, once the swarm is up on the ridge: the whole crowd thrown in |
| | `shieldBash` | each beetle into the frost vent |
| | `taunt`, `hook` | bring the doused swarm up to the ridge (the taunted follow you; hooked out of the ford) |

Why no single skill works: a douse alone leaves them standing. A blizzard on the burning nest only
quenches it, and the nest will not ice again. The vent is on the ridge and the spring in the nest:
only a mover brings the swarm from one to the other, and a mover knocks nothing. A second wave, or a
herd through the ford after the fires are out, leaves the beetles wet, and wet beetles only freeze.

Skills serving two roles: `vortex` and `shieldBash` douse (into the spring) in one plan and chill
(into the vent) in another; `taunt` and `hook` douse and bring to the vent in the same plan.

The traps: cold twice (`blizzard` + `blizzard`); a wave and then a herd (wet); two movers, two knocks,
two waves (nothing chills). Whoever wades the ford is wet: the vortex that throws the swarm into the
vent throws the herder in too, and freezes it - a sacrifice the plan can afford once the herding is
done.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp (player, mage) --- ridge (frostVent) --- ford (puddle) --- nest (spring; b1, b2, b3)
```

- **Links:** all walkable (`connected`).
- **Line of sight:** the camp sees the ridge; the ridge overlooks the ford and the nest; the ford and
  the nest see each other, and the ford sees the ridge.
- **Zones:** the ford is a `puddle` (whoever wades it is wet).
- **Features:** `feature(nest, spring, puddle)` (wet); `feature(ridge, frostVent, iceSheet)` (slowed
  and chilled). Neither is a hazard: nothing falls.
- **Beetles:** `insect`, `burning`. Both companions have 2 mana: one wave or blizzard each.
- **Heavy attacks:** none. Sacrifice is allowed: a herder frozen in the vent is not a failure.

## Hypothesis

Measured with `htn_components combos crowd_ember_swarm` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 18 of 36 assignments win (9 unordered pairs, whichever companion holds which half): `blizzard`
  with `tidalWave`, `vortex`, `taunt`, `hook` or `shieldBash`; `vortex` with `taunt` or `hook`;
  `shieldBash` with `taunt` or `hook`.
- 9 methods (distinct skill sets cast), in three kinds of douse (a wave, a knock into the spring, a
  herd through the ford) and two kinds of chill (a blizzard where they stand, a knock into the vent).
- Skill usage: `blizzard` 10, `vortex` 6, `taunt` 6, `hook` 6, `shieldBash` 6, `tidalWave` 2. No dead
  skills. No solo plans. One replan takes 0.3 to 3 s.

## Examples

### Example 1: A wave, then a blizzard

**Given:** the player knows `tidalWave`, the mage knows `blizzard` (the default kit).

**When:** `win`

**Then:** the player wades the ford into the nest and bursts a wave: the three fires go out. The mage
ices the nest from the ridge: the swarm dies of the cold (and the soaked player freezes).

### Example 2: Herded through the ford, thrown into the vent

**Given:** the player knows `taunt`, the mage knows `vortex`.

**When:** `win`

**Then:** the player taunts the beetles from the ford: each walks after it through the water, and its
fire goes out. The player walks up to the ridge, the swarm on its heels; the mage's vortex throws
everyone on the ridge into the frost vent. The beetles die; the wet player freezes.

### Example 3: One skill, two roles

**Given:** `vortex` or `shieldBash` for the player; `blizzard` or `taunt` for the mage.

**When:** `win`

**Then:** with `blizzard`, the vortex (or each bash) knocks the swarm into the spring - a douse; with
`taunt`, it knocks the herded swarm into the frost vent - the chill.

### Example 4: Traps

**Given:** `blizzard` twice; `tidalWave` and `taunt`; `tidalWave` and `vortex`; `taunt` and `hook`.

**When:** `win`

**Then:** no plan. The nest ices once; the waved swarm herded through the ford is wet; nothing
chills without a blizzard or the vent; two movers knock nothing.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Nine pairs win | Exactly the nine measured pairs have a plan. |
| P3 | Each hand matters | Every winning pair wins whichever companion holds which half. |
| P4 | Douse before chill | In every winning plan all three fires are out before any beetle dies, and all three die of the cold. |
