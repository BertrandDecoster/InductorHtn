# The Sinkhole

## Purpose

The demo level for the ability layer (`components/abilities/`), on the standard catalogue. A stone
golem stands on the rim of a sinkhole, by a hole where the floor has already fallen in; beside the
rim, a pump automaton wades in a flooded pool that drains into the sinkhole, and a wicker tender
minds an oil slick. The player and the mage pick one skill each from six.

The golem is the level's **heavy attack**. It will not be baited (it ignores taunts), but pinned
(`rooted`, a vortex) or jolted (`electrocuted`, a lightning flash) it stamps: a telegraphed cave-in
(the catalogue's `caveIn`, physical, so it cannot be interrupted) on its own rim. The whole rim
becomes a chasm and everything on it falls - the golem, any mook brought there, and any companion
still standing there. The team wants to trigger it with the mooks on the rim. It is both the weapon
and the danger:
- only a hook or a taunt brings a mook onto the rim, and the caster has to stand on the rim to do it;
- a hooked mook stays where it lands, so the hooker walks off; a taunted mook follows its taunter,
  so the taunter has to stay on the rim and go down with it (sacrifice is allowed);
- provoking the golem cuts the level: afterwards the rim is a chasm, nothing can stand on it, and a
  mook still off the rim is out of reach of everything but fire.

It exists to show the layer's claims in one place:
- skills are bundles of keywords (a vortex is a knock-in and a pin; a flash is a jolt and a dash);
- the map has two kinds of movement: only a hook or a taunt changes a mook's area, every knock stays
  inside it (into the hole, into the drain);
- combos are physics (oil + fire = blaze, wet + fire = steam, wet + jolt on a machine = dead);
- a heavy boss cannot be moved until something takes its weight away (Turn to Mist);
- a telegraphed heavy attack is a weapon to aim, and its zone takes whoever is left on it;
- different pairs clear the level by different recipes.

| Method | Skills | How |
|--------|--------|-----|
| **The sinkhole** | `hook` or `taunt`, then `vortex` or `lightningFlash` | bring both mooks onto the rim from the rim; the hooker walks off, the taunter stays; pin or jolt the golem from the ledge: one cave-in takes all three |
| **One by one** | `fireball`, then `vortex` or `lightningFlash` | the fireball burns the tender (blaze) and knocks the wader into the drain; then the golem is made to stamp on its empty rim |
| **Mist** | `fireball` + `turnToMist` | the same two fireballs, then the golem is misted and a third fireball knocks it into the hole |

Mixed plans come for free: the vortex on the drain, or the flash in the pool, takes the wader where
it stands, and only the tender is brought onto the rim.

Why no single skill works:
- Only the golem's own cave-in or the hole stops it, and the hole needs its weight gone first
  (`turnToMist`) and then a knock.
- A vortex or a flash takes the wader and provokes the golem, but never reaches the tender: it has to
  be burnt or brought onto the rim.
- A hook or a taunt only brings the mooks; nothing of theirs provokes the golem.
- Fire alone takes both mooks, but never provokes the golem, and never knocks it while it is heavy.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
            ledge (player, mage)
              |
   slick --- rim (golem; the hole) --- pool (wader; the drain)
```

- **Areas and links:** four areas, all walkable; the rim is the hub.
- **Features:** the hole (`chasm`) inside the rim; the drain (`chasm`) inside the pool.
- **Zones:** the pool is a `puddle`, the slick is a `slick` (oil).
- **Line of sight:** the ledge sees the rim, the pool and the slick; the rim, the pool and the slick
  see each other through the rim.
- **Golem:** `rank(boss)`, `heavy`, `living`; immune to `taunted`; `behavior(golem, rooted, caveIn,
  here)` and `behavior(golem, electrocuted, caveIn, here)`.
- **Wader:** `machine`, `wet`. **Tender:** `wooden`, `oiled`.
- Both companions have 6 mana: three fireballs or three flashes.

The goal `clearSinkhole` spells out the stages: each mook is brought onto the rim or taken where it
stands (`neutralize`); whoever stands on the rim walks off or stays; then the golem goes down -
provoked (any cast that lands `rooted` or `electrocuted` on it, including a vortex's pin on the NPCs
of its area), or by `neutralize` (mist and the hole). The goal then confirms both mooks are out.

## Hypothesis

Measured by `htn_components combos sinkhole` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 14 of the 36 assignments win (7 pairs, whichever companion holds which half), by 7 methods of
  three kinds (bring and collapse, one by one, mist); no solo plans; no dead skills:
  - hook or taunt, with vortex or lightningFlash: 4 pairs (the sinkhole);
  - fireball, with vortex or lightningFlash: 2 pairs (one by one);
  - fireball with turnToMist: 1 pair (mist).
- Every taunt plan loses the taunter to the rim; a hook plan can keep everyone.
- Bringing the golem down first leaves the tender out of reach.
- The vortex and the flash each play two roles: the wader (drain, jolt) and the golem (pin, jolt).

## Examples

### Example 1: The sinkhole

**Given:** the player knows `hook`, the mage knows `vortex` (the default kit).

**When:** `clearSinkhole`

**Then:** the player walks onto the rim, hooks the wader in from the pool and the tender in from the
slick, and walks back to the ledge; the mage's vortex pins the golem, which winds up a cave-in on the
rim; the rim falls with the golem, the wader and the tender.

### Example 2: The taunter holds the rim

**Given:** the player knows `taunt`, the mage knows `lightningFlash`.

**When:** `clearSinkhole`

**Then:** the taunted mooks walk onto the rim after the player, and follow it; the mage's flash jolts
the golem, which stamps; the player goes down with the rim and the mooks.

### Example 3: One by one

**Given:** the player knows `fireball`, the mage knows `lightningFlash`.

**When:** `clearSinkhole`

**Then:** a fireball on the slick blazes the tender (`dead`); a fireball on the wader makes steam and
knocks it into the drain (`fell`); the mage's flash from the ledge jolts the golem, which stamps on
its empty rim. The flash's dash does not land in the new chasm.

### Example 4: Mist and the hole

**Given:** the player knows `turnToMist`, the mage knows `fireball`.

**When:** `clearSinkhole`

**Then:** two fireballs take the mooks; the player mists the golem; the mage's third fireball knocks
it into the hole. The cave-in never happens.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Seven pairs win | Exactly the seven measured pairs have a plan. |
| P3 | The taunter is spent | Every taunt plan loses the taunter; a hooker can walk off. |
| P4 | The golem first cuts the rim | Provoking the golem before the mooks: no plan. |
| P5 | The golem cannot be knocked as it stands | Heavy: no knock into the hole. |
| P6 | Fire clears the mooks only | Fire takes both mooks, never the golem. |
