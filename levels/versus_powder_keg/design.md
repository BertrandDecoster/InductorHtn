# Powder Keg

## Purpose

Category: **an enemy whose trigger is being hit by something a companion can cause** (Hades bomb
enemies, Into the Breach). A powder-mule carries a keg up on the ridge. Jolt it, startle it or goad it
and the fuse catches: a heartbeat later the keg goes off, a telegraphed heavy blow on the region the
mule stands in, which catches fire (`behavior(mule, electrocuted|blinded|taunted, blast, here)`,
`heavy(blast)`, `effect(blast, target, spill(flames))`). Down in the grove stands an old ent: wood
burns (its catalogue weakness), it is rooted (`heavy`: nothing moves it), and nothing in the party
makes fire. Two companions, one skill each from six.

| Step | Skills |
|------|--------|
| **Bring the keg to the ent** | `hook` (from the grove), `vortex` (on the grove: the ridge is drawn in), `tidalWave` (from the crag, washed down the slope - soaked) |
| **Light the fuse** | `lightningFlash` (a jolt; lands before the flasher's dash, so it is never caught); `blindingFlash` (from the grove or next to it; its disjoint lets the flasher stay inside); `taunt` (from the grove: the mule is dragged in and goes off there, with the taunter inside) |
| **Get the taunter out** | a friend's one cast in the window: `hook` drags it clear, `tidalWave` from the road washes it (and the mule) into the hollow, `vortex` on the road or the ridge draws it out - the rooted ent stays for the blast |

Why no single skill works:
- Nothing in the pool burns (no `fireball`). The only fire is the keg's.
- The ent is rooted: nothing brings it to the keg.
- A taunter is always inside its own lure's blast; the party keeps its head (`immune(player|mage,
  taunted)`), so a second taunt cannot drag it out.
- A trigger on the ridge spends the keg there; a mover alone brings the keg and nothing lights it.

Traps: a soaked mule only seizes up under lightning (living, wet and electrocuted: stunned, and its
fuse never catches) - the wave that washed it down wets its fuse, so wave + lightning loses, while a
blinding flash still sets it off; two triggers spend the keg on the ridge.

Skills with two roles: `hook`, `vortex` and `tidalWave` each bring the keg down (for a flash) or save
the taunter (for a goad). `taunt` both moves and lights the keg.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp --- road --- grove (ent) --- hollow
           |      /
          ridge (mule) --- crag
```

- **Walks:** camp-road, road-grove, road-ridge, grove-ridge, grove-hollow, ridge-crag. Line of sight
  along every walk.
- **Lines:** from the crag, a push on the ridge lands in the grove (the slope); from the road, a push
  on the grove lands in the hollow; from the grove, a push on the ridge lands on the crag.
- **Ent:** wooden, heavy. **Mule:** living, light, immune to burning.
- Both companions start at the camp with 4 mana; both are immune to taunts.
- **Level-local recipes:** `bring(?e, ?r)`, `trigger(?npc, ?r)` (a lure given from ?r, or a trigger in
  place), `standBy(?r, ?a)` (before a lure, the other companion steps out of ?r or takes a stand
  anywhere else, ready to answer), `stepAside(?r, ?a)`, `setOff(?npc, ?v)` (lured to ?v, or brought
  to ?v and set off). `win` = set the mule off on the ent, confirm.

## Hypothesis

Measured with `htn_components combos versus_powder_keg`:

- No single skill wins, even held by both companions: 0 of 6.
- 16 of 36 assignments win (8 unordered pairs), 8 methods, 0 solo plans, no dead skills:
  - `lightningFlash` + `hook` / `vortex` (2 pairs);
  - `blindingFlash` + `hook` / `vortex` / `tidalWave` (3 pairs);
  - `taunt` + `hook` / `vortex` / `tidalWave` (3 pairs).
- Losing pairs, each for a named reason: two triggers (the keg blows on the ridge; a taunter nobody can
  get out), `lightningFlash` + `tidalWave` (a soaked fuse), two movers (nothing lights it).
- Skill usage: blindingFlash 6, taunt 6, hook 6, vortex 6, lightningFlash 4, tidalWave 4.
- One `FindAllPlans` takes 0.1-3 s.

## Examples

### Example 1: Hook the keg down, jolt it

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player stands in the grove, hooks the mule down and steps out to the road; the mage's
lightning flash jolts it: the keg winds up and blows on the grove, and the ent burns (`dead`).

### Example 2: Goad it, wash the taunter out

**Given:** the player knows `taunt`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the mage waits on the road; the player taunts the mule from the grove, it is dragged in and
the fuse catches; in the window the mage's wave washes the player and the mule into the hollow; the
rooted ent stays, and the blast sets the grove on fire.

### Example 3: Wash it down the slope, flash it

**Given:** the player knows `tidalWave`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** from the crag the player's wave washes the mule down into the grove (soaked); the mage
flashes it, the keg blows on the grove.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the eight measured pairs have a plan. |
| P3 | A soaked fuse | lightningFlash + tidalWave: no plan. |
| P4 | The ent stays | In every taunt plan the ent is never moved. |
| P5 | The keg blows once | Two triggers and no mover: no plan. |
