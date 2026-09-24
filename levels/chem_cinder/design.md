# Cinder

## Purpose

An elemental-chemistry level about **layers that absorb a chill** and **terrain that reacts to
terrain**. A fire imp, wreathed in flame (`tag(imp, burning)`), holds the cloister yard. Things of fire
die of the cold (catalogue: `fireElemental`, `chilled -> dead`). But cold on a burning thing only
quenches the flame (`quench`), and cold on a wet thing only freezes it (`freeze`: stunned, which is
not out). So each chill is spent on a layer, and only a chill on a dry, unlit imp kills. The cloister
keeps a fountain (`puddle`) and a frozen pond (`iceSheet`), and the zones react when a skill spills
another zone on them: ice over a puddle is ice, ice on flames is a puddle, flames on ice is a puddle.
The imp's heat keeps everyone out of its region (`blocker`). The player and the mage pick one skill
each from a pool of six.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Douse beside, then chill** | a `tidalWave` from the arch, next to the yard, where no push line runs: the fire goes out (`extinguish`) | a `blizzard` on the yard, or a drag onto the pond (`hook`, `taunt`) |
| **Quench, then drag** | a `blizzard` on the yard: only a quench | from the pond, `hook` or `taunt` drags it onto the ice |
| **Dunk, then freeze** | `fireball` from the court (its blast; its flames do nothing to a thing of fire) or a `vortex` on the fountain drops it in the water: the fire goes out | a `blizzard` on the fountain: puddle + ice = iceSheet, and it freezes where it stands; or `hook` / `taunt` from the pond, over the water onto the ice |
| **Light, then ice twice** | `fireball` aimed at the yard itself (a region: no push) leaves flames | a `blizzard`: flames + ice = puddle, the fire goes out; a second `blizzard`: puddle + ice = iceSheet, a dry chill |

Why no single skill works:
- Two blizzards: the first quenches it, and the second lands on ice already there. A spilled zone does
  not land twice.
- Two drags: dragged onto the pond while burning, it is only quenched. Nothing sees the pond, and the
  imp blocks it, so nothing brings it onto the ice a second time.
- Water, blasts and pull-ins alone never chill it.

Skills in two roles: `blizzard` quenches in one method and kills in three others. `fireball` is a
push in one method and a fire zone to melt in another. `hook` and `taunt` either finish the imp on the
ice or, when it is still burning, quench it there first.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
court (player, mage) ---- yard (imp) ---- fountain (puddle)
  |                         |
cloister --------------- arch
  |
pond (iceSheet)
```

- **Walking:** court–yard, yard–fountain, court–cloister, cloister–pond, cloister–arch, arch–yard.
  Nobody walks into the imp's region (`blocker(imp)`).
- **Line of sight:** court→yard, court→fountain, arch→yard, pond→yard, pond→fountain. Nothing sees
  the pond.
- **Push line:** from the court, the yard tips into the fountain.
- **Zones:** fountain `puddle`; pond `iceSheet`.
- **Imp:** `fireElemental`, `burning`, blocker. Both companions have 4 mana (two 2-mana casts).
- **Level recipes:** `douseThenChill` (one companion puts the fire out - a wave from beside it, a
  cast, a push or pull into water, a drag onto ice - then another chills it) and `lightThenIce` (one
  sets the yard alight, another ices it twice). The generic `neutralize` is tried too and finds
  nothing: cold on the burning imp only quenches it.
- **Heavy attack:** none.

## Hypothesis

Measured with `htn_components combos chem_cinder`:

- No single skill wins, even when both companions hold it: 0 of 6.
- **22 of 36** assignments win (11 unordered pairs, in either seat). **11 methods**, four kinds, no
  solo plans, no dead skills:
  - douse beside, then chill: tidalWave x {blizzard, hook, taunt};
  - quench, then drag: blizzard x {hook, taunt};
  - dunk, then freeze: {fireball, vortex} x {blizzard, hook, taunt}, 6 pairs;
  - light, then ice twice: fireball x blizzard (a second plan for that pair).
- Skill usage: blizzard 10, hook 8, taunt 8, tidalWave 6, fireball 6, vortex 6.
- Losing pairs, each for a named reason: two chills of the same kind (see above), wave + fireball or
  wave + vortex (wet, never cold), fireball + vortex (only water), hook + taunt (the pond takes it
  once).

## Examples

### Example 1: Douse beside, then chill

**Given:** the player knows `tidalWave`, the mage knows `blizzard`.

**When:** `win`

**Then:** the player walks round to the arch and bursts a wave beside the yard. The imp's fire goes
out (`extinguish`) and it stays where it is. The mage's blizzard chills a dry imp (`dead`).

### Example 2: Dunk, then freeze the fountain

**Given:** the player knows `fireball`, the mage knows `blizzard`.

**When:** `win`

**Then:** the fireball from the court blows the imp into the fountain, and the water puts its fire
out. The mage's blizzard on the fountain turns the puddle to ice (`opReshape(fountain, puddle,
iceSheet)`), and the imp dies of the cold where it stands.

### Example 3: Light, then ice twice

**Given:** the player knows `fireball`, the mage knows `blizzard`.

**When:** `win` (the second plan)

**Then:** the fireball, aimed at the yard itself, leaves flames there. The first blizzard melts them
into a puddle (`flames -> puddle`), which puts the imp's fire out. The second blizzard freezes the
puddle over (`puddle -> iceSheet`), and the chill lands on a dry imp.

### Example 4: Vortex, then hook onto the ice

**Given:** the player knows `vortex`, the mage knows `hook`.

**When:** `win`

**Then:** the vortex on the fountain pulls the imp in and roots it; the water puts the fire out. The
mage walks to the pond and hooks it out of the fountain onto the ice (`dead`).

### Example 5: Cold twice only quenches

**Given:** both companions know `blizzard`.

**When:** `win`

**Then:** no plan. The first blizzard quenches the imp, and the second lands on ice already there.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Eleven pairs win, in either hand | Exactly the eleven measured pairs have a plan, whichever companion holds which half. |
| P3 | A wave from the court soaks it twice | The wave washes it into the fountain: wet again, so the blizzard on the fountain only freezes it (stunned). It soaks the partner beside the caster too. |
| P4 | Fire on the ice is a puddle | Blizzard, then fire on the yard: ice + flames = puddle, the imp is wet, and the next blizzard only freezes it. |
| P5 | The pond takes it once | Dragged onto the pond while burning, it is only quenched; hook + taunt find no plan. |
