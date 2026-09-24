# Wall-Bang

## Purpose

An enemy-state-machine level in the Monster Hunter wall-bang style, built on a **telegraphed,
physical heavy attack** the team provokes on purpose. The Ram is a boss: heavy (nothing moves it),
immune to stuns, and it holds the arena (a blocker). Taunted or blinded, it lowers its horns and
**charges down its lane to the brink**: a heavy blow. The team gets one cast; then the Ram lands on
the brink, goring whoever stands there (stunned, thrown into the ravine). A stone pillar stands at
the brink, and the charge ends in it:

| State or trigger | Behaviour | Result |
|------------------|-----------|--------|
| `taunted`, `blinded` | `ramCharge` (heavy, physical, aimed `there(brink)`) | wind-up; one team cast; then it dashes to the brink and gores everyone there |
| arrives at the brink | the `pillar` zone | `staggered` (a hazard only the Ram is weak to) and `heavy` removed (knocked off its feet) |
| `staggered` | the window | `electrocuted` → `dead`; a push or a pull drops it into the ravine |

Only the brink sees into the arena, so the lure is always cast from the brink, and the charge comes
down on the lure's own head. Surviving it is half the puzzle:

| Method | The lure (from the brink) | Surviving the charge | The finisher (the other companion) |
|--------|---------------------------|----------------------|------------------------------------|
| **Flash and ...** | `blindingFlash` (it blinds everyone around) | the flash made its caster `disjoint`: the gore passes through them | `fireball` or `tidalWave` from the pen, `vortex` into the ravine, `hook` or `taunt` across the ravine from the ledge, or `lightningFlash` on its open heart |
| **Taunt and pull** | `taunt` | the partner pulls the taunter clear in the window: `hook` from the pen, or a `vortex` on the pen | the same skill drops the staggered Ram (hook across the ravine, vortex into it) |

Why no single skill works:
- A lure alone leaves a staggered Ram standing; two taunts leave the taunter on the brink when the
  charge lands.
- A push, a pull or a jolt before the crash does nothing: it is heavy, and a jolted living thing
  only seizes up.
- The charge is physical: nothing interrupts it. Only leaving the brink, or being disjoint, survives.

Traps: `fireball` and `tidalWave` "save" the taunter by throwing them into the ravine; the level
does not count a lost companion as a rescue (`teamStanding`). After the charge, whoever stands on
the brink steps back to the pen, so a finisher's wave or vortex does not take them too.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
         arena (Ram)
           |
pen --- brink (pillar) ... ravine (chasm, below the brink)
 |                            :
gallery ----------------- ledge   (faces the brink across the ravine)
```

- **Lines:** a push from the pen on the brink lands in the ravine; a blow landing on the brink
  throws whoever stands there over it; from the ledge, the ravine lies between it and the brink, so
  a pull (hook, a taunt's drag) drops what it drags.
- **Line of sight:** only the brink sees the arena. Pen-brink, pen-gallery, gallery-ledge,
  ledge-brink, pen and ledge see the ravine.
- **The pillar:** `onEnter(brink, pillar)`, a zone with `hazard(pillar)` and `remove(heavy)`. Only the
  Ram has a weakness to it (`weakness(ram, pillar, none, staggered)`).
- **Ram:** boss, living, heavy, blocker. `behavior(ram, taunted|blinded, ramCharge, there(brink))`,
  `heavy(ramCharge)` (physical): `target: dash`, `area: grant(stunned)`, `area: push`.
  `weakness(ram, electrocuted, staggered, dead)`.
- **Goal:** `win` provokes the charge (a skill that grants a trigger tag), confirms the Ram is
  staggered, steps everyone off the brink, runs the standard `neutralize(ram)` in that state
  (`intoThePit` or `exploit`), and checks no companion was lost.
- Both companions have 4 mana. Pool: `blindingFlash`, `taunt`, `hook`, `vortex`, `fireball`,
  `tidalWave`, `lightningFlash`.

## Hypothesis

Measured with `htn_components combos fsm_wallbang` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 16 of 49 assignments win: 8 pairs, each whichever companion holds which half:
  - `blindingFlash` plus any finisher: `taunt`, `hook`, `vortex`, `fireball`, `tidalWave`,
    `lightningFlash` (6 pairs);
  - `taunt` plus a partner who pulls: `hook`, `vortex` (2 pairs).
- 8 methods, 0 solo plans, no dead skills.
- Skills with two roles: `taunt` lures the charge, or drags the staggered Ram across the ravine;
  `hook` and `vortex` pull the taunter out of the charge, then drop the Ram.
- The other 13 pairs lose for a nameable reason: two finishers (it never charges), a taunt with a
  pusher (the only rescue is a push into the ravine), `taunt`+`lightningFlash` (nobody pulls the
  taunter clear).

## Examples

### Example 1: Flash, then throw

**Given:** the player knows `blindingFlash`, the mage knows `fireball`.

**When:** `win`

**Then:** the player walks to the brink and flashes; the blinded Ram winds up its charge; it dashes
to the brink, passes through the disjoint player, crashes into the pillar (`staggered`, no longer
heavy); the player steps back; the mage's fireball from the pen throws it into the ravine (`fell`).

### Example 2: Taunt, and the hook pulls you clear

**Given:** the player knows `taunt`, the mage knows `hook`.

**When:** `win`

**Then:** the player taunts from the brink; in the wind-up the mage hooks the player back to the pen;
the charge lands on an empty brink and the Ram crashes; the mage walks to the ledge and hooks the
Ram across the ravine (`fell`).

### Example 3: Flash, then jolt

**Given:** the player knows `lightningFlash`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the mage flashes from the brink and survives the gore; the player's lightning flash stops
the staggered Ram's open heart (`dead`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the eight measured pairs have a plan. |
| P3 | The crash is the key | Every winning plan winds up the charge and staggers the Ram at the pillar. |
| P4 | A push is no rescue | `taunt` with `fireball` or `tidalWave`: no plan. |
| P5 | Each hand matters | A pair wins whichever companion holds which half. |
