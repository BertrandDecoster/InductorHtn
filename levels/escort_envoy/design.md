# The Envoy

## Purpose

An escort level: an **envoy** who cannot act must reach the exit. It is not a companion: it never
casts, and it walks on its own only when the way is clear. Two companions, the player and the mage,
pick one skill each from a pool of eight catalogue skills. Two obstacles stand between the envoy and
the exit, and no pool skill answers both alone:

| Obstacle | Answers |
|----------|---------|
| **The briars** (a hazard only the envoy and the crate are weak to) | fill them with the crate: wash it in from the camp (`tidalWave`), blast it in (`fireball` from the camp), suck it in (`vortex` on the briars), or hook it across them from the lawn (`hook`) |
| **The sentry** (heavy; watches the gatehouse from its tower) | blind it (`blindingFlash` from the lawn or the tower), stun it (`shieldBash`), freeze it (a `tidalWave` from the lawn soaks it, a `blizzard` on the tower chills it: stunned), or drop it: `turnToMist`, and on the very next cast wash it (`tidalWave` from the lawn), blast it (`fireball`) or suck it (`vortex` on the moat) into the moat |

Once both are dealt with, the envoy walks out: camp, yard, briars (filled), lawn, gatehouse, exit.

Why no single skill works:
- A crate-mover leaves the sentry watching the gatehouse; nobody walks through it. A push or a pull
  on the heavy sentry does nothing; a hook on it drags the caster up the tower instead.
- A blinder or a basher leaves the briars live, and the envoy never walks into a hazard it is weak
  to.
- `turnToMist` alone moves nothing; `blizzard` alone chills a dry sentry, which does nothing.

`tidalWave`, `fireball` and `vortex` each serve two roles: the move that fills the briars is also
the move that drops the misted sentry, and the wave that fills the briars from the camp soaks the
sentry from the lawn for the blizzard (the soaker spends all four mana).

The escort traps: the companions wade through the briars unharmed, so it is tempting to drag the
envoy after them. A pull stops in the first live hazard on its way that the target is weak to, so a
`hook` on the envoy from the lawn drops it in the briars. And mist lasts one cast: the push that
drops the sentry must be the very next one.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
camp (player, mage, envoy) --- yard (crate) --- briars --- lawn --- gatehouse --- exit
                                                             |      (watched)
                                                           tower (sentry) --- moat (chasm)
```

- **Briars:** a zone whose ability is `hazard(thorns)`. Only the envoy and the crate are weak to it
  (`weakness(envoy, thorns, none, fell)`, the same for the crate). The crate (`tag(crate, filler)`)
  falling in fills it.
- **Lines:** a push from the camp on the yard lands in the briars; the briars lie between the lawn
  and the yard, and between the lawn and the camp (so a pull from the lawn crosses them); a push
  from the lawn on the tower lands in the moat. The tower and the moat are next to each other, so a
  vortex on the moat draws the tower in.
- **Sentry:** living, heavy, `watches(sentry, gatehouse)`.
- Both companions have 4 mana (`tidalWave`, `fireball` and `blizzard` cost 2).
- **Goal:** `win` = `crossBriars` (passage's `span`), `passSentry` (blinded or stunned; soaked and
  then iced or jolted; or `neutralize`: into the moat once the heavy tag is off), then the envoy
  walks to the exit and must arrive whole, with no companion lost (`confirmSafe`).

## Hypothesis

Measured with `htn_components combos escort_envoy`:

- No single skill wins, even when both companions hold it: 0 of 8.
- 24 of 64 assignments win (12 pairs, either way round), by 12 methods:
  - a filler (`tidalWave`, `fireball`, `hook`, `vortex`) with `blindingFlash` or `shieldBash`:
    8 pairs;
  - `tidalWave` + `blizzard` (fill, soak, freeze);
  - `turnToMist` + `tidalWave` / `fireball` / `vortex` (fill, then mist and drop): 3 pairs.
- No solo plan; no dead skill. Every plan takes under a second.

## Examples

### Example 1: Wash and blind

**Given:** the player knows `tidalWave`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the player's wave from the camp washes the crate into the briars (filled); the mage wades
over to the tower and flashes (the sentry is blinded); the envoy walks out.

### Example 2: Hook the crate over

**Given:** the player knows `hook`, the mage knows `shieldBash`.

**When:** `win`

**Then:** the player wades to the lawn and hooks the crate across the briars (it falls in and fills
them); the mage bashes the sentry from the lawn; the envoy walks out.

### Example 3: Mist and drop

**Given:** the player knows `vortex`, the mage knows `turnToMist`.

**When:** `win`

**Then:** the player's vortex on the briars sucks the crate in; the mage turns the sentry to mist,
and the player's second vortex, on the moat, draws it off the tower (`fell`).

### Example 4: Soak and freeze

**Given:** the player knows `tidalWave`, the mage knows `blizzard`.

**When:** `win`

**Then:** one wave from the camp fills the briars, a second from the tower soaks the sentry; the
mage's blizzard freezes it (stunned).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 12 measured pairs have a plan, whichever companion holds which half. |
| P3 | The envoy is never dragged | No winning plan moves the envoy by force; it always walks out. |
| P4 | Mist is a moment | The cast that drops the misted sentry is the one right after the mist. |
| P5 | Two companions cast | Both companions cast in every winning plan. |
