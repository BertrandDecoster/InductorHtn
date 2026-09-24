# Cinder

## Purpose

An elemental-chemistry level about **one tag guarding against another** and **terrain that stores a
tag**. A fire imp, wreathed in flame (`tag(imp, burning)`), holds the cloister yard. Things of fire
freeze solid when chilled (`weakness: chilled -> frozen`), but cold on a burning thing only quenches the
flame (`quench` removes burning). So the fire goes out first, and then the cold lands. The cloister
keeps a fountain, a `puddle` basin nobody can walk into, and a frozen pond, an `iceSheet` that chills
whoever arrives. The player and the mage pick one skill each from a pool of eight.

| Method | One companion puts the fire out | The other freezes it |
|--------|---------------------------------|----------------------|
| **Douse, then chill** | rain or a wave: `rainCall`, `tidalWave` (`extinguish`) | frost: `glaciate`, `iceStorm` |
| **Quench, then drag onto the ice** | anything wet or cold: `rainCall`, `tidalWave`, `glaciate`, `iceStorm` | from the pond, drag it onto the ice (`magnetize`) or trade places with it (`translocate`) |
| **Dunk, then freeze** | a blast from the court throws it into the fountain: `gust`, or `fireball`, whose fire does nothing to it but whose blast still lands | frost it there (`glaciate`, `iceStorm`), or drag it out onto the ice (`magnetize`, `translocate`) |

Why no single skill works:
- Cold first only quenches it, and the ice then lies under it. A second frost there lands on ice
  already there, and a spilled zone does not land twice.
- Dragged onto the pond while burning, it is only quenched there. Nothing sees the pond, so nothing can
  bring it onto the ice a second time.
- Water alone only puts the fire out. A blast alone only dunks it.
- `fireball`'s fire does nothing to a thing of fire (`immune(?e, burning)`).

Several skills serve two roles. `glaciate` and `iceStorm` quench in one method and freeze in another.
`magnetize` and `translocate` either bring the imp onto the ice to freeze, or put the fire out by
dragging it through the ice first. `fireball` is a push here, not a fire.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
court (player, mage) ---- yard (imp: fire, burning) ---- gate
  |                          \
cloister                   fountain  (puddle; reached only by a push from the court)
  |
pond  (iceSheet)
```

- **Walking:** court–yard, yard–gate, court–cloister, cloister–pond. The fountain is not walkable.
- **Line of sight:** court→yard, court→fountain, pond→yard, pond→fountain. Nothing sees the pond.
- **Push line:** from the court, the yard tips into the fountain.
- **Zones:** fountain `puddle`; pond `iceSheet`.
- **Imp:** element fire, burning. Both companions have 4 mana.
- **Level recipe:** `putOutAndFreeze`: one companion puts the fire out (a cast of water or cold, a
  push into water, or a drag through water or ice), then another lands the cold (a cast, or a drag
  or swap onto the ice). The generic `neutralize` is tried too. It finds nothing, because cold on the
  burning imp only quenches it.
- **Not in the pool: `taunt`.** Its pull comes from `onGrant(taunted, pull)`, which the engine applies
  raw, so a taunted imp dragged onto the ice skips the quench and freezes while still burning: one
  skill, one companion. `translocate` does the same job, and its swap arrives in react mode.

## Hypothesis

Measured with `htn_components combos chem_cinder`:

- No single skill wins, even when both companions hold it: 0 of 8.
- **40 of 64** assignments win (20 unordered pairs, in either seat). There are **20 methods** of
  three kinds, and no dead skills:
  - douse, then chill: {rainCall, tidalWave} x {glaciate, iceStorm}, 4 pairs;
  - quench, then drag: {rainCall, tidalWave, glaciate, iceStorm} x {magnetize, translocate},
    8 pairs;
  - dunk, then freeze: {gust, fireball} x {glaciate, iceStorm, magnetize, translocate}, 8 pairs.
- Skill usage: glaciate 12, iceStorm 12, magnetize 12, translocate 12, and 8 each for rainCall,
  tidalWave, gust and fireball.
- Losing pairs, each for a named reason: two frosts (quench, then ice already there), two drags (the
  ice takes it once), two waters or two blasts (nothing cold), frost then rain (only wet), a douse and
  a blast (wet, never cold).

## Examples

### Example 1: Douse, then chill

**Given:** the player knows `rainCall`, the mage knows `glaciate`.

**When:** `win`

**Then:** the rain puts the imp's fire out (`extinguish`), and the mage's frost freezes it solid
(`frozen`).

### Example 2: Dunk, then drag onto the ice

**Given:** the player knows `gust`, the mage knows `magnetize`.

**When:** `win`

**Then:** the gust blows the imp into the fountain, and its fire goes out. The mage walks round to
the frozen pond and drags it out of the fountain onto the ice (`frozen`).

### Example 3: Quench, then swap

**Given:** the player knows `glaciate`, the mage knows `translocate`.

**When:** `win`

**Then:** the frost only quenches it (`quench`). The mage, on the pond, trades places with it, and it
arrives on the ice (`frozen`).

### Example 4: Fire is only a blast

**Given:** the player knows `fireball`, the mage knows `iceStorm`.

**When:** `win`

**Then:** the fireball's flames do nothing to the imp, but the blast throws it into the fountain. The
ice storm freezes it there.

### Example 5: Cold twice only quenches

**Given:** the player knows `glaciate`, the mage knows `iceStorm`.

**When:** `win`

**Then:** no plan. The first frost quenches it, and the second lands on ice already there.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Twenty pairs win | Exactly the twenty measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | The ice takes it once | Dragged onto the pond while burning, it is only quenched; magnetize + translocate find no plan. |
