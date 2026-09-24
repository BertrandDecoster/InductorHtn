# The Envoy

## Purpose

An escort level about making a road for someone who only walks. An **envoy** who cannot fight
must reach the gate road. Between the yard and the lawn run the **briars**, a strip of thorns (a
`gap`): a leaper clears it, but the envoy only walks, and pulled across it would fall in. Past the
lawn an armoured **sentry** (heavy) holds the gatehouse: nobody walks through it while it stands
there. Two companions, the player and the mage, pick one skill each from a pool of six:

| Obstacle | Answers |
|----------|---------|
| **The briars** (a gap) | bridge them with the crate in the yard: knock it in from the yard side (`fireball`, `shieldBash`, `tidalWave` standing in the yard), or grapple over to the statue on the lawn (`hook`: an anchored target pulls you to it) and drag the crate across behind you - it falls in and fills the gap |
| **The sentry** (heavy, a blocker) | lure it: `taunt` from the tower, and it walks after its taunter, off the envoy's road; or drop it: `turnToMist`, and in that moment knock it through the trapdoor (`fireball`, `shieldBash`) |

Then the envoy walks out on its own.

Why no single skill works:
- A bridger cannot move the heavy sentry; a knock on it does nothing.
- The taunt and the mist do nothing to the briars.
- `fireball` or `shieldBash` held by both bridges, but the sentry stays heavy.

The traps:
- Hooking the envoy over the briars drops it in the thorns.
- A hook on the heavy sentry drags the caster into the gatehouse instead; mist lasts one cast, so
  the knock must be the very next one.
- A taunt from the lawn only brings the sentry onto the lawn, into the envoy's way: the level's
  goal lures it to the tower.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
camp (envoy, player, mage) --- yard (crate) ~~briars~~ lawn (statue) --- gatehouse (sentry, trapdoor) --- road
                                                         |
                                                       tower
```

- **Areas (6):** camp, yard, lawn, gatehouse, road, tower.
- **Links:** walkable camp-yard, lawn-gatehouse, gatehouse-road, lawn-tower; a `gap` yard-lawn (the
  briars).
- **Features:** `trapdoor` (chasm) in the gatehouse.
- **Line of sight:** camp-yard, yard-lawn, lawn-gatehouse, lawn-tower, tower-gatehouse,
  gatehouse-road (both ways).
- **Route** (`progress/2`, for leaps): camp 0, yard 1, lawn 2, tower and gatehouse 3, road 4.
- **Things:** a crate (filler) in the yard; a statue (heavy: an anchor) on the lawn; the sentry
  (living, heavy, `blocker`) in the gatehouse.
- **Envoy:** living, `mustSurvive`; walks.
- **Mana:** four each.
- **Goal:** `win` = `crossBriars` (bridged already; `bridge(yard, lawn)`; or someone `reach`es the
  lawn first - a hook to the statue - then bridges), then `clearGate(sentry)` (`intoThePit`, or
  `bringTo` the tower), then the envoy walks to the road, whole.

## Hypothesis

Measured with `htn_components combos escort_envoy`:

- No single skill wins, even when both companions hold it: 0 of 6.
- 12 of 36 assignments win (6 pairs, either way round), by 6 methods:
  `taunt` + `fireball` / `shieldBash` / `tidalWave` / `hook`;
  `turnToMist` + `fireball` / `shieldBash`.
- No solo plan; no dead skill. `fireball` and `shieldBash` play two roles (the crate into the gap,
  then the misted sentry through the trapdoor), and so does `hook` (grapple over, drag the crate).
- The whole matrix replans in under three seconds.

## Examples

### Example 1: Blast the crate, lure the sentry

**Given:** the player knows `fireball`, the mage knows `taunt`.

**When:** `win`

**Then:** the player blasts the crate into the briars: it bridges them. The mage walks over to the
tower and taunts the sentry, which walks after it through the lawn to the tower. The envoy walks
out through the gatehouse.

### Example 2: Grapple over and drag the crate

**Given:** the player knows `hook`, the mage knows `taunt`.

**When:** `win`

**Then:** the player hooks the statue from the yard (it is anchored: the player is pulled over the
briars to it), then hooks the crate from the lawn: it falls into the briars and bridges them.

### Example 3: Mist and bash

**Given:** the player knows `turnToMist`, the mage knows `shieldBash`.

**When:** `win`

**Then:** the mage bashes the crate into the briars from the camp; the player walks to the lawn and
turns the sentry to mist; the mage's next cast, a bash, knocks it through the trapdoor.

### Example 4: Wash the crate in

**Given:** the player knows `tidalWave`, the mage knows `taunt`.

**When:** `win`

**Then:** the player stands in the yard and casts the wave: the crate is washed into the briars.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | The measured pairs win either way | Exactly the 6 measured pairs have a plan, whichever companion holds which half. |
| P3 | The envoy is never dragged | No winning plan moves it by force; it walks from the gatehouse to the road. |
| P4 | Mist is a moment | The knock on the misted sentry is the very next cast. |
| P5 | Two companions cast | Both cast in every winning plan. |
