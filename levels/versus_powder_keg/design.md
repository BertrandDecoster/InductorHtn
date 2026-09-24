# Powder Keg

## Purpose

Category: **an enemy whose trigger is being hit by something a companion can cause** (Hades bomb
enemies, Into the Breach). A powder-mule carries a keg up on the ridge. Jolt it, startle it or snare
it and the fuse catches: the keg winds up, a telegraphed heavy blow that **follows the mule** and goes
off wherever it stands when it blows; that area catches fire
(`behavior(mule, electrocuted|blinded|rooted, blast, self)`, `heavy(blast)`,
`effect(blast, target, spill(flames))`). The keg blows once (`effect(blast, self, grant(silenced))`).
Down in the grove stands an old ent: wood burns (its catalogue weakness), it is heavy (nothing moves
it), and nothing in the party makes fire. The mule is living and follows a taunt. Two companions, one
skill each from eight.

| Way | Skills |
|-----|--------|
| **Bring the keg to the ent** | `hook` (two pulls along the road; straight across the ravine it falls); `taunt` (from the grove: it walks) |
| **Light the fuse** | `lightningFlash` (from next door: the jolt lands before the flasher does); `blindingFlash` (from inside); `vortex` (aimed at the sap pool: the mule is snared - rooted) |
| **In the window** | the keg follows the mule: flash it on the ridge while a friend in the grove taunts it - it runs down and blows there |
| **The hollow** | `turnToMist` on the ent (not heavy, for a moment), then knock it into the hollow: `tidalWave`, `shieldBash`, `vortex` on the hollow |

Why no single skill works:
- Nothing in the pool burns (no `fireball`). The only fire is the keg's.
- A mover alone brings the keg and nothing lights it; a trigger alone lights it on the ridge, and the
  keg is spent.
- The ent is heavy: a knock does not move it until it is mist, and the mist lasts one cast.

Traps: hooked straight across the ravine, the mule falls, keg and all; a soaked mule only seizes up
under lightning (living, wet and jolted: stunned) and a stunned mule's fuse never catches - a shield
bash does the same; lit anywhere but the grove, the keg is spent; a vortex on the hollow drops the
mule (and anyone near) in it.

Skills with two roles: `vortex` lights the fuse (a snare on the sap pool) or drops the misted ent
(on the hollow); `taunt` brings the mule before, or during the window.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp --- road --- grove (ent; the sap pool, the hollow)
           |     :
         ridge (mule)                ridge : grove is a gap (the ravine)
```

- **Links:** walkable camp-road, road-grove, road-ridge; a gap ridge-grove. Sight along every link.
- **Features:** in the grove, the sap pool (`puddle`) and the hollow (`chasm`).
- **Ent:** wooden, heavy, immune to taunts. **Mule:** living, immune to burning, light.
- Both companions start at the camp with 4 mana.
- **Level-local recipes:** `fetch(?e, ?r)` (there, or brought one or two links by `bringTo`),
  `light(?npc)` (inflict a trigger, or a vortex on a feature of its area that is no pit for it).
  `win` = the mule fetched to the ent and lit; or lit where it is, with a companion waiting in the
  grove to bring it in the window; or `unset(heavy, ent)` and `knockOn(ent, feature(hollow))`.

## Hypothesis

Measured with `htn_components combos versus_powder_keg`:

- No single skill wins, even held by both companions: 0 of 8.
- 18 of 64 assignments win (9 unordered pairs), 9 methods, 0 solo plans, no dead skills:
  - `hook` / `taunt` + `lightningFlash` / `blindingFlash` / `vortex` (bring the keg, light it);
  - `turnToMist` + `tidalWave` / `shieldBash` / `vortex` (the ent into the hollow).
- Losing pairs, each for a named reason: two movers or two triggers (nothing lit, or lit on the
  ridge), a mover and a knock (nothing lights it), mist and a trigger (the keg never comes).
- Skill usage: hook 6, taunt 6, vortex 6, turnToMist 6, lightningFlash 4, blindingFlash 4,
  tidalWave 2, shieldBash 2.
- One `FindAllPlans` takes under 3 s.

## Examples

### Example 1: Hook it down the road, jolt it

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** from the road the player hooks the mule off the ridge, then from the grove into the grove;
the mage's lightning flash from the road jolts it: the keg winds up and blows on the grove, and the
ent burns (`dead`).

### Example 2: Flash it on the ridge, taunt it down in the window

**Given:** the player knows `taunt`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** among the plans: the player waits in the grove; the mage flashes the mule on the ridge and
the keg winds up. In the window the player taunts it: the mule runs down the road into the grove, and
the keg blows there.

### Example 3: Snare it with a vortex

**Given:** the player knows `taunt`, the mage knows `vortex`.

**When:** `win`

**Then:** the player taunts the mule into the grove; the mage's vortex on the sap pool knocks it in
and snares it: the fuse catches.

### Example 4: Mist and the hollow

**Given:** the player knows `turnToMist`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the player turns the ent to mist; the mage's wave washes it into the hollow (or over the
ravine's edge): it falls.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the nine measured pairs have a plan. |
| P3 | A soaked fuse | With the mule wet, hook + lightningFlash: no plan; hook + blindingFlash still wins. |
| P4 | Over the ravine | Hooked from the grove, the mule falls into the gap. |
| P5 | The keg blows once | Lit on the ridge, it blows there and the mule is silenced. |
| P6 | The ent stays | No plan moves the ent to another area. |
