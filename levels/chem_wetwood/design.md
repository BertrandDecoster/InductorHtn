# Wet Wood

## Purpose

An elemental-chemistry level about **a reaction that dries its target**, **a reaction that spreads
fire**, and **terrain that burns up**. A treant, rooted and rain-soaked, blocks the grove. Wood burns
(catalogue: `wooden`, `burning -> dead`), but fire on something wet only makes steam (`steam` removes
wet). Up on the ramp, in a spill of lamp oil (a `slick` zone), stands a keg; beyond the grove glows
the charcoal-burners' kiln (a `flames` zone). The player and the mage pick one skill each from a
pool of seven.

| Method | One companion | The other |
|--------|---------------|-----------|
| **Keg, then fire** | bring the keg into the grove: `tidalWave` (push it off the ramp from the landing), `hook` or `taunt` (drag it in from the grove), `vortex` (pull it into the grove) | set it off: `fireball`, or a spark (`lightningFlash`; this level's reaction `reaction(oiled, electrocuted, blaze)`) |
| **Fire, then keg** | `fireball` on the grove: the steam dries the treant, and the grove stays a fire zone | bring the keg in (`tidalWave`, `hook`, `taunt`, `vortex`): it blazes as it arrives |
| **Into the kiln** | `turnToMist`: for one cast the treant is not heavy | `fireball` from the glade: its flames dry the treant (steam) and its blast throws it into the kiln, where it burns |

The blaze throws `burning` on everyone in the keg's region, and a reaction's effects apply **raw**:
no further reaction, so the soak does not save the treant.

Why no single skill works:
- One fire only steams the treant. A second fire on the grove lands on flames already there (a
  spilled zone does not land twice), and the rooted treant never arrives anywhere new.
- Fire or a spark on the keg where it stands burns the oil off on the ramp: flames on a slick are
  flames (a zone reaction), and the keg blazes there, wasted. `fireball` does this even while it
  throws the keg into the grove: the spill comes before the push.
- A mover alone brings the keg, and nothing lights it. The mist alone moves nothing.

Skills in two roles: `fireball` lights the keg, sets the grove alight before the keg comes, and
throws a misted treant into the kiln. `lightningFlash` is a spark here, not a jolt.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
ridge ---- glade (player, mage) ---- grove (treant) ---- kiln (flames)
             |                         |
           landing ---------------- ramp (slick; keg)
```

- **Walking:** glade–grove, glade–landing, landing–ramp, ramp–grove, glade–ridge, grove–kiln.
- **Line of sight:** glade→grove, ridge→grove, landing→ramp, grove→ramp.
- **Push lines:** from the landing, the ramp tips into the grove; from the glade, the grove falls away
  into the kiln.
- **Zones:** ramp `slick`, kiln `flames`.
- **Treant:** `wooden`, `heavy` (rooted: nothing moves it), `wet`.
- **Keg:** `oiled`, light.
- **Level physics:** `reaction(oiled, electrocuted, blaze)`: a spark sets oil off.
- **Level recipes:** `blazeBeside` (bring the fuel in and set it off, or set the region alight and
  bring the fuel in, by two companions) and `intoTheFire` (one takes the heavy ward off, another
  places it in a fire zone). The generic `neutralize` is tried too and finds nothing: fire on the wet
  treant only steams it.
- **Heavy attack:** none.

## Hypothesis

Measured with `htn_components combos chem_wetwood`:

- No single skill wins, even when both companions hold it: 0 of 7.
- **18 of 49** assignments win (9 unordered pairs, in either seat). **9 methods** of three kinds, no
  solo plans, no dead skills:
  - keg and fire: {tidalWave, hook, vortex, taunt} x fireball, 4 pairs (each in both orders: keg
    first, or the grove alight first);
  - keg and spark: {tidalWave, hook, vortex, taunt} x lightningFlash, 4 pairs;
  - into the kiln: turnToMist x fireball.
- Skill usage: fireball 10, lightningFlash 8, tidalWave 4, hook 4, vortex 4, taunt 4, turnToMist 2.
- Losing pairs, each for a named reason: two fires, or fire and a spark (steam, then flames already
  there; the keg wasted on the ramp), two movers (nothing lights anything), mist with a wave, a
  vortex, a hook or a taunt (the treant reaches the kiln still wet, or not at all), mist and a spark.

## Examples

### Example 1: Keg, then fire

**Given:** the player knows `tidalWave`, the mage knows `fireball`.

**When:** `win`

**Then:** the player walks to the landing and bursts a wave that washes the keg off the ramp into the
grove. The mage's fireball sets the grove alight: the treant only steams, but the keg blazes
(`blaze`), and the blaze's raw fire burns the treant (`dead`).

### Example 2: Fire, then keg

**Given:** the player knows `tidalWave`, the mage knows `fireball`.

**When:** `win` (the second plan)

**Then:** the mage sets the grove alight first. The steam dries the treant, and the grove stays a fire
zone. The keg is washed in afterwards and blazes as it arrives.

### Example 3: Hook, then spark

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player walks into the grove and hooks the keg down off the ramp. The mage's lightning
flash strikes the keg: sparks set the oil off, and the blaze burns the treant.

### Example 4: Mist, then into the kiln

**Given:** the player knows `turnToMist`, the mage knows `fireball`.

**When:** `win`

**Then:** the player turns the treant to mist. The mage's fireball dries it (steam) and blows it out
of the grove into the kiln, where it burns (`dead`).

### Example 5: Wet wood only steams

**Given:** both companions know `fireball`.

**When:** `win`

**Then:** no plan. The first fire steams the treant dry, and the second lands on flames already there.
Fireball on the keg burns its oil off before throwing it into the grove.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Nine pairs win, in either hand | Exactly the nine measured pairs have a plan, whichever companion holds which half. |
| P3 | Fire on the ramp wastes the oil | Fireball on the keg where it stands: slick + flames = flames, the keg blazes on the ramp and lands in the grove with no oil. |
| P4 | The kiln needs a dry treant | Mist with a wave or a vortex finds no plan: the treant reaches the kiln wet, and the kiln only steams it. |
