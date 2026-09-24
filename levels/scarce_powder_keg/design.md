# Powder Keg

## Purpose

A **resource scarcity** level where the resource is a **heavy attack that can be spent**. A walled
yard, sunk over an old cellar, holds one powder keg. A bruiser guards the keg, and a lurker waits on
the stair above. The team watches from the landing at the top of the stair. Nothing the team
carries can stop either enemy. Only the keg can: it blows the yard's floor into the cellar, and it
blows once. The player and the mage pick one skill each from six.

The keg is a **telegraphed heavy attack the team sets off on purpose**. Fire or a spark (`burning`,
`electrocuted`) lights its fuse: `behavior(keg, burning | electrocuted, caveIn, here)`. The catalogue's
`caveIn` is physical, so nothing stops it once lit. The team gets one cast, then the yard's floor gives
way. Everything still in the yard falls into the cellar: the bruiser, the keg itself, and any companion
who did not get out. With the keg gone, it cannot blow again. No level-local ability, tag or
weakness is needed: a keg, two catalogue triggers and the catalogue's cave-in.

| Method | First | Then |
|--------|-------|------|
| **Gather, then burn** | bring the lurker down into the yard: wash it down the stair from the landing (`tidalWave`), drag it down from the yard and walk out (`hook`, `taunt`), or draw it in with a vortex on the yard from the landing (`vortex`) | a fireball on the keg from the landing (`fireball`) |
| **Gather, then spark** | the same | a lightning flash from the stair at the gate (`lightningFlash`): it strikes the keg on its way through the yard and carries its caster out the far side |
| **Burn, then the crater** | light the keg first (`fireball`, `lightningFlash`) | wash (`tidalWave`) or draw (`vortex`) the lurker into the crater |

Why no single skill works:
- A gatherer alone kills nothing: only the keg's cave-in stops anyone.
- A lighter alone drops the bruiser and leaves the lurker on the stair, out of reach. Two fireballs
  can't move it: a fireball's push needs a line, and none leads from where it can be seen.

The order is the puzzle for a puller. Lighting the keg is the obvious first move, and it leaves a
crater where the puller would have to stand. The lighter has a trap of its own: a flash aimed at
the keg carries its caster into the yard, and it lands in the crater. The flash has to be aimed
*through* the yard, at the gate, from the stair.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate --- yard (keg, bruiser) --- stair (lurker) --- landing (player, mage)
  |                                                    |
  +------------------------ side path -----------------+
```

- **Lines:** from the landing, a push on the stair lands in the yard. From the stair, the yard lies on
  the way to the gate, so a flash from the stair at the gate strikes whatever is in the yard.
- **Line of sight:** landing and gate to the yard; yard and stair to each other; yard to the gate;
  stair to the gate. The landing cannot see the stair (it winds under it).
- **Keg:** an object, `heavy`; `behavior(keg, burning, caveIn, here)`,
  `behavior(keg, electrocuted, caveIn, here)`.
- **Enemies:** bruiser (yard) and lurker (stair), both `living`.
- Both companions have 2 mana (`tidalWave`, `fireball` and `lightningFlash` cost 2).
- **Goal:** `win`. Either `herd(lurker, yard)`, `clearOut(yard, landing)` (whoever can walk leaves the
  yard), then `detonate(keg)`, and confirm both enemies fell. Or `detonate(keg)` first, then
  neutralize the lurker (into the crater). Both methods end with `confirmTeam` (no companion went
  down). `detonate` lands fire or a spark on the keg, or casts a skill that strikes its path through
  the keg's region (the flash through the yard).

## Hypothesis

Measured by `htn_components combos scarce_powder_keg` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 16 of 36 assignments win, i.e. 8 of the 15 pairs, whichever companion holds which half. The winners
  are exactly one gatherer (`tidalWave`, `hook`, `taunt`, `vortex`) and one lighter (`fireball`,
  `lightningFlash`).
- 8 methods (distinct skill sets). No dead skills, and no plan carried by one companion.
- Every winning plan blows the keg exactly once, and no companion is in the yard when it goes.
- The 7 losing pairs are two gatherers (nothing lights the keg) or two lighters (nothing moves the
  lurker).

## Examples

### Example 1: Wash down, then burn

**Given:** the default kit: the player knows `tidalWave`, the mage knows `fireball`.

**When:** `win`

**Then:** the player's wave from the landing washes the lurker down the stair into the yard. The
mage's fireball lights the keg; it winds up its cave-in, and the yard's floor takes the keg, the
bruiser and the lurker.

### Example 2: Drag down, step out, then burn

**Given:** the player knows `taunt`, the mage knows `fireball`.

**When:** `win`

**Then:** the player walks into the yard and taunts the lurker, which is dragged down to them. The
player walks out, and the mage lights the keg.

### Example 3: Spark through the yard

**Given:** the player knows `vortex`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player's vortex on the yard draws the lurker in. The mage goes down to the stair and
flashes at the gate: the strike lights the keg on the way through the yard, and the mage comes out at
the gate (`opDash(mage, stair, gate)`) as the floor falls.

### Example 4: Burn, then the crater

**Given:** the player knows `tidalWave`, the mage knows `fireball`.

**When:** `win`

**Then:** one plan lights the keg first: the bruiser falls with the floor. The wave then washes the
lurker down the stair into the crater (`opExploit(player, lurker, chasm, fell)`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | A gatherer and a lighter win | Exactly the eight measured pairs have a plan. |
| P3 | One blast | Every winning plan sets the keg off exactly once, and no companion falls. |
| P4 | Wrong order loses for a puller | With `taunt` and `fireball`, lighting the keg first has no plan. The keg is gone with the floor, so it cannot be set off again. |
| P5 | A spark on the keg buries its caster | No winning plan flashes the keg itself. |
| P6 | Each hand matters | A pair wins whichever companion holds which half. |
