# Cinder

## Purpose

An elemental-chemistry level about **layers that absorb a chill** and **terrain that reacts to
terrain**. A fire imp, wreathed in flame (`tag(imp, burning)`), holds the cloister yard. Things of fire
die of the cold (catalogue: `fireElemental`, `chilled -> dead`). But cold on a burning thing only
quenches the flame (`quench`), and cold on a wet thing only freezes it (`freeze`: stunned, which is
not out). So each chill is spent on a layer, and only a chill on a dry, unlit imp kills. The yard keeps
a fountain (a pool feature: what is knocked in is soaked); next door lies the frozen pond (an
`iceSheet` zone over the whole area). Zones react when a skill spills another on them: ice on flames
is a puddle, ice over a puddle is ice. The player and the mage pick one skill each from a pool of
seven.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Douse, then chill** | a `tidalWave` in the yard puts the fire out (`extinguish`) | a `blizzard` on the yard, or bring it onto the pond: `hook` from the pond, or `taunt` (it walks onto the ice after you) |
| **Quench, then the pond** | a `blizzard` on the yard: only a quench | `hook` or `taunt` brings it onto the ice, now dry |
| **Dunk, then chill** | a knock into the fountain: `fireball`, `shieldBash`, or a `vortex` on the fountain | a `blizzard` on the yard (not after a fireball), `hook` onto the pond, or `taunt` (not after a bash or a vortex) |
| **Light, then ice twice** | `fireball` aimed at the yard itself leaves flames | a `blizzard`: flames + ice = puddle, the fire goes out; a second `blizzard`: puddle + ice = iceSheet, a dry chill |

Why no single skill works:
- Two blizzards: the first quenches it, the second lands on ice already there.
- Two drags: brought onto the pond while burning, it is only quenched, and the pond takes it once.
- Water, blasts and vortices alone never chill it.

Skills in two roles: `blizzard` quenches in one method and kills in three others; `fireball` is a
knock in one method and a fire zone to melt in another; `hook` and `taunt` finish the imp on the ice,
or quench it there when it arrives still burning.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
court (player, mage) ---- yard (imp; fountain) ---- pond (iceSheet)
  |                                                   |
  +-------------------- cloister --------------------+
```

- **Areas:** 4. **Links:** all walkable: court-yard, yard-pond, court-cloister, cloister-pond.
- **Line of sight:** court->yard, cloister->pond, pond->yard.
- **Features:** `fountain` in the yard (`puddle`: what is knocked in is soaked).
- **Zones:** pond `iceSheet` (whoever enters is slowed and chilled).
- **Imp:** `fireElemental`, `burning`. Both companions have 4 mana (two 2-mana casts).
- **Level recipes:** `douseThenChill` (one companion puts the fire out - a wave, a blizzard, a knock
  into the fountain - then another chills it - a blizzard, or bring it onto the pond with
  `bringTo`) and `lightThenIce` (one sets the yard alight, another ices it twice).
- **Heavy attack:** none. **Terrain use:** the fountain feature (knock target), the pond zone (bring
  target), and three zone reactions (flames/ice -> puddle, puddle/ice -> ice).

## Hypothesis

Measured with `htn_components combos chem_cinder`:

- No single skill wins, even when both companions hold it: 0 of 7.
- **24 of 49** assignments win (12 unordered pairs, in either seat). **12 methods**, four kinds, no
  solo plans, no dead skills:
  - douse, then chill: tidalWave x {blizzard, hook, taunt};
  - quench, then the pond: blizzard x {hook, taunt};
  - dunk, then chill: blizzard x {shieldBash, vortex}, fireball x {hook, taunt}, hook x {shieldBash,
    vortex};
  - light, then ice twice: fireball x blizzard.
- Skill usage: blizzard 12, hook 10, tidalWave 6, fireball 6, taunt 6, shieldBash 4, vortex 4.
- Losing pairs, each for a named reason: two chills of the same kind, a wave with a knock (wet, never
  cold), two knocks, hook + taunt (the pond takes it once), shieldBash + taunt (stunned, it cannot
  follow), vortex + taunt (rooted on the next cast, it cannot follow).

## Examples

### Example 1: Douse, then chill

**Given:** the player knows `tidalWave`, the mage knows `blizzard`.

**When:** `win`

**Then:** the player walks into the yard and bursts a wave. The imp's fire goes out (`extinguish`). The
mage's blizzard ices the yard and chills a dry imp (`dead`).

### Example 2: Dunk, then lure it onto the ice

**Given:** the player knows `fireball`, the mage knows `taunt`.

**When:** `win`

**Then:** the fireball blows the imp into the fountain, which puts its fire out. The mage walks onto
the pond and taunts it: the imp walks after the mage onto the ice and dies of the cold.

### Example 3: Light, then ice twice

**Given:** the player knows `fireball`, the mage knows `blizzard`.

**When:** `win`

**Then:** the fireball, aimed at the yard itself, leaves flames there. The first blizzard melts them
into a puddle (`flames -> puddle`), which puts the imp's fire out. The second blizzard freezes the
puddle over (`puddle -> iceSheet`), and the chill lands on a dry imp.

### Example 4: Vortex, then hook onto the ice

**Given:** the player knows `vortex`, the mage knows `hook`.

**When:** `win`

**Then:** the vortex on the fountain knocks the imp in and roots it; the water puts the fire out. The
mage walks onto the pond and hooks it out of the yard onto the ice (`dead`).

### Example 5: Cold twice only quenches

**Given:** both companions know `blizzard`.

**When:** `win`

**Then:** no plan. The first blizzard quenches the imp, and the second lands on ice already there.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Twelve pairs win, in either hand | Exactly the twelve measured pairs have a plan, whichever companion holds which half. |
| P3 | The wave can soak it again | Aimed into the fountain, the wave's own knockback soaks the doused imp: the blizzard then only freezes it. |
| P4 | Rooted, it cannot follow | After a shield bash (stunned) or a vortex (rooted for a moment), a taunt from the pond does not bring it. |
| P5 | The pond takes it once | Brought onto the pond while burning, it is only quenched; hook + taunt find no plan. |
