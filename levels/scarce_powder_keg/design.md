# Powder Keg

## Purpose

A resource-scarcity level: **a spent reaction**. A walled yard with one powder keg in it, sunk over
an old cellar, and a tripwire across the yard. A bruiser stands guard by the keg; a lurker waits on
the stair above. The team watches from the landing. Nothing the team carries stops either enemy -
only the keg does, and it blows once.

The keg is a **telegraphed heavy attack the team sets off on purpose**. Fire or a spark (`burning`,
`electrocuted`) lights its fuse: it winds up the catalogue's `caveIn` on the yard (physical, so it
cannot be stopped). The yard's floor becomes a chasm and everything still in it falls - the bruiser,
the keg, and any companion who stayed. The tripwire is a **plate**: whatever is knocked onto it
throws a spark into the powder trail and the whole yard catches fire (`spill(flames, yard)`), the keg
with it.

So the lurker has to be brought down into the yard first, and only a hook or a taunt changes its
area; then the keg is lit.

| Step | Skills | How |
|------|--------|-----|
| **Gather** | `hook` | from the yard, hook the lurker down off the stair; the hooker walks out (it stays where it landed) |
| | `taunt` | from the yard, taunt it: it walks down after the taunter and follows it, so the taunter stays - and goes down with the yard |
| **Light** | `fireball` | on anything in the yard, from the landing: the yard burns |
| | `lightningFlash` | from the stair or the gate: it jolts the keg, and its dash never lands in the new chasm |
| | `shieldBash` | from the stair: knocks the bruiser (or the lurker) onto the tripwire |
| | `vortex` | on the tripwire, from the landing: everything in the yard is knocked onto it |
| | `blindingFlash` | inside the yard: the shock lights the keg; disjoint passes the blow, but the chasm takes the caster |

Why no single skill works:
- A lighter alone takes the bruiser and spends the keg; the lurker is then out of reach for good.
- A gatherer alone never lights the keg.
- The primer (the gatherer) and the payoff (the lighter) are two companions.

The scarce thing is the keg's one reaction, and - for a taunter or a blinding flash - a companion.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
landing (player, mage) --- stair (lurker) --- yard (keg, bruiser; tripwire)
    |                                            |
    +------------------ side path ------------- gate
```

- **Areas and links:** four areas round a walkable loop.
- **Features:** the tripwire, a plate (`plate(tripwire)`) in the yard; its ability `spark` is
  `spill(flames, yard)`.
- **Line of sight:** the landing sees the stair and the yard; the stair, the yard and the gate see
  each other through the yard.
- **Keg:** an object, `heavy`; `behavior(keg, burning, caveIn, here)` and `behavior(keg,
  electrocuted, caveIn, here)`.
- **Bruiser, lurker:** `living`. Both companions have 2 mana: one fireball or one flash.

The goal `win` spells out the stages: `bringTo(lurker, yard)`, whoever stands in the yard walks out
or stays, then `detonate(keg)` (land its fuse tag, or knock something onto the tripwire), then
confirm both enemies fell.

## Hypothesis

Measured by `htn_components combos scarce_powder_keg` (and this level's `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 20 of the 49 assignments win: every gatherer (hook, taunt) with every lighter (fireball,
  lightningFlash, shieldBash, vortex, blindingFlash), either way round - 10 pairs, 10 methods; no
  other pair wins; no solo plans; no dead skills.
- Every taunt plan and every blinding-flash plan spends a companion; a hook plan with a lighter from
  outside keeps the whole team.
- Lighting the keg first loses.
- A tidal wave in the yard soaks the keg: knocked onto the tripwire, the bruiser only makes steam.

## Examples

### Example 1: Hook, then fire

**Given:** the player knows `hook`, the mage knows `fireball` (the default kit).

**When:** `win`

**Then:** the player walks down into the yard, hooks the lurker off the stair, and walks out by the
gate; the mage's fireball sets the yard alight; the keg winds up and the yard caves in under the
bruiser and the lurker.

### Example 2: The tripwire

**Given:** the player knows `hook`, the mage knows `shieldBash`.

**When:** `win`

**Then:** after the gather, the mage bashes the bruiser from the stair onto the tripwire: the yard
catches fire, and the keg with it.

### Example 3: The taunter holds the yard

**Given:** the player knows `taunt`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the lurker walks down after the player and follows it; the player stays; the mage's flash
lights the keg, and the player goes down with the yard.

### Example 4: The flash from the stair

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the flash jolts the keg; the cave-in lands before the flash's dash, which then has nowhere
to land: its caster stays out.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Ten pairs win | Exactly every gatherer with every lighter. |
| P3 | The keg blows once | Lit first, the lurker is lost. |
| P4 | A blinding flash spends its caster | Every blinding-flash plan loses the flasher. |
| P5 | The wave drowns the fuse | A soaked keg only steams. |
