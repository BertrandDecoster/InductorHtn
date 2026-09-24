# The Envoy

## Purpose

An escort level: a frail **envoy** who cannot act must reach the exit. It is not a companion: it
never casts, and it walks on its own only when the way is clear. Two companions, the player and the
mage, pick one skill each from a pool of eight. Two obstacles stand between the envoy and the exit,
and no pool skill answers both:

| Obstacle | Answers |
|----------|---------|
| **The briars** (a hazard only the frail and the crate are weak to) | fill them with the crate: push it in from the camp (`gust`, `tidalWave`), or drag it across them from the lawn (`magnetize`, `taunt`: a taunted crate is pulled to its taunter) |
| **The sentry** (watches the gatehouse; armoured) | blind it (`net`, `flashbang`, `sleepDart`), or drop it: `sunder` the armour, then push it off the tower into the moat (`gust`, `tidalWave`) |

Once both are dealt with, the envoy walks out: camp, yard, briars (filled), lawn, gatehouse, exit.

Why no single skill works:
- A crate-mover leaves the sentry watching the gatehouse; nobody walks through it.
- A blinder leaves the briars live, and the envoy never walks into a hazard it is weak to.
- `sunder` alone leaves the sentry on its tower; a push alone is warded by the armour.

`gust` and `tidalWave` each serve two roles: the push that fills the briars is also the push that
drops the stripped sentry.

The escort traps: the companions wade through the briars unharmed, so it is tempting to drag the
envoy after them. A pull stops in the first live hazard on its way that the target is weak to, so a
`magnetize` or `taunt` on the envoy from the lawn drops it in the briars.

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
                                                           tower (sentry) ... moat (chasm)
```

- **Briars:** a zone whose ability is `hazard(thorns)`. Only `frail` things (the envoy) and
  `filler` things (the crate) are weak to it (`fell`). The crate falling in fills it.
- **Lines:** a push from the camp on the yard lands in the briars; the briars lie between the lawn
  and the yard, and between the lawn and the camp (so a pull from the lawn crosses them); a push
  from the lawn on the tower lands in the moat.
- **Sentry:** living, armoured, `watches(sentry, gatehouse)`.
- Both companions have 4 mana (`tidalWave` costs 2).
- **Goal:** `win` = `crossBriars`, `passSentry`, then the envoy walks to the exit and must arrive
  whole (`confirmSafe`).

## Hypothesis

Measured with `htn_components combos escort_envoy`:

- No single skill wins, even when both companions hold it: 0 of 8.
- 28 of 64 assignments win (14 pairs, either way round), by 14 methods:
  - a crate-mover (`gust`, `tidalWave`, `magnetize`, `taunt`) plus a blinder (`net`, `flashbang`,
    `sleepDart`): 12 pairs;
  - `sunder` plus `gust` or `tidalWave`: the pusher fills the briars and drops the stripped sentry.
- No solo plan; no dead skill. `magnetize` and `taunt` fail with `sunder`: a pull does not
  unseat the sentry.

## Examples

### Example 1: Fill and blind

**Given:** the player knows `gust`, the mage knows `net`.

**When:** `win`

**Then:** the player gusts the crate into the briars; the mage nets the sentry (blinded); the envoy
walks out through the gatehouse.

### Example 2: Drag the crate in

**Given:** the player knows `magnetize`, the mage knows `flashbang`.

**When:** `win`

**Then:** the player wades to the lawn and hooks the crate across the briars, where it sinks and
fills them; the mage's flashbang blinds the sentry.

### Example 3: Drop the sentry

**Given:** the player knows `gust`, the mage knows `sunder`.

**When:** `win`

**Then:** the gust fills the briars; the mage sunders the sentry's armour; the player gusts it off
the tower into the moat (`fell`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 14 measured pairs have a plan, whichever companion holds which half. |
| P3 | The envoy is never dragged | No winning plan moves the envoy by force; it walks out. |
| P4 | Two companions cast | Both companions cast in every plan. |
