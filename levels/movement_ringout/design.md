# Ring-Out

## Purpose

A pure-movement level on the ability layer: nothing hurts the ogre, so the only way to win is to
ring it out - get it over the verge into the void. Two companions pick **one skill each** from six.
The idea is Into the Breach's: the enemy never starts on a line into the void, so somebody moves it
first.

Under the catalogue's map rule this is exactly the two-step shape: **bring** the NPC to the area
that holds the danger, then **knock** it in. A knockback never changes the area, and the plinth
has no edge on the void, so a push there goes nowhere.

| Step | Answers |
|------|---------|
| **Bring it onto the brink** | Stand on the brink and `hook` it over from the plinth next door; or stand on the brink and `taunt` it - it walks after you, and slams the ground where it arrives: a heavy physical blow (`groundSlam`) on everyone else on the brink, stunned and knocked back (over the verge, if the ogre aims there). |
| **Knock it over the verge** | `fireball` (from the gate or the yard), `shieldBash` (from next door), `tidalWave` (standing on the brink), or a `vortex` on the verge (it draws in everything on the brink, friends too). |

The slam is answered or taken. With one cast in the window, a friend can knock the ogre over before
the blow lands (a fireball or a bash from the yard): the slam misses. Or the taunter takes it:
sacrifice is allowed, and the knocker finishes the job. Whoever stands on the brink may step back
into the yard before the knock (a taunter who steps back leads the ogre off again).

Why no single skill wins, even held by both seats: a bringer cannot knock, and a knocker has
nothing to knock the ogre into on the plinth.

Traps:
- Two knockers only scorch or stun it where it stands (P4).
- A vortex on the verge takes whoever still stands on the brink (P6).
- A wave on the brink knocks the hooker as well as the ogre: every aim is a plan.
- Taunted, the ogre stays fixated: a taunter who walks away takes it along.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate --- yard --- plinth (ogre)
           \        /
            brink (verge: the void)
```

- **Areas:** gate, yard, brink, plinth (four). All links walkable: gate–yard, yard–brink,
  yard–plinth, brink–plinth.
- **Feature:** `verge` (a chasm) on the brink. The plinth has none.
- **Line of sight:** gate → yard, brink; the yard, the brink and the plinth see each other.
- **The ogre:** living; `behavior(ogre, taunted, groundSlam, here)`.
- **Kit:** mana 4 each (two costly casts). Default: player `fireball`, mage `hook`.
- **Goal:** `win` = `bringTo(ogre, brink)`, an optional step back, then `finish`: already over (it
  was knocked in during its wind-up), or `knockOn(ogre, feature(verge))`.

## Hypothesis

Measured by `htn_components combos movement_ringout` (36 assignments in about 3 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 16 of 36 assignments win: exactly one bringer (`hook`, `taunt`) with one knocker (`fireball`,
  `tidalWave`, `shieldBash`, `vortex`), each way round.
- 8 methods.
- Skill usage: hook 8, taunt 8, fireball 4, tidalWave 4, shieldBash 4, vortex 4. No dead skill; no
  plan carried by one companion.

## Examples

### Example 1: Hook it onto the brink, then knock it over

**Given:** the default kit (player `fireball`, mage `hook`).

**When:** `win`

**Then:** the mage walks onto the brink and hooks the ogre over from the plinth; the player's
fireball knocks it over the verge.

### Example 2: Taunt it, and knock it over before the slam

**Given:** player `taunt`, mage `fireball`.

**When:** `win`

**Then:** the player taunts the ogre from the brink. It walks over and winds up a slam; in the
window, the mage's fireball knocks it over the verge, and the slam misses.

### Example 3: A wave on the brink

**Given:** player `hook`, mage `tidalWave`.

**When:** `win`

**Then:** the player hooks the ogre onto the brink; the mage walks on and the wave washes it over.

### Example 4: Take the slam, then the vortex

**Given:** player `taunt`, mage `vortex`.

**When:** `win`

**Then:** the taunted ogre slams the brink (the player is stunned, or knocked over the verge); the
mage's vortex on the verge draws the ogre in.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has both companions casting. |
| P2 | No single skill wins | Each pool skill held by both seats: no plan. |
| P3 | The measured pairs win | Exactly the 8 bringer × knocker pairs win, both ways round; `combos` passes; no dead skill. |
| P4 | The plinth has no edge | `fireball` + `shieldBash` loses; a fireball on the plinth knocks the ogre into nothing. |
| P5 | The taunter may be sacrificed | With `taunt` + `shieldBash`, some plans lose the taunter over the verge and some keep everyone. |
| P6 | Step back before the vortex | With `hook` + `vortex`, the hooker steps back first, or goes over with the ogre. |
