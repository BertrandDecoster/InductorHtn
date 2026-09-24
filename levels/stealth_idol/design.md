# The Idol

## Purpose

A stealth level on the ability layer where **you can slip in, but you come out hushed**. A golden
idol sits in a temple shrine. The way in is the nave, watched from the altar by the high keeper. The
way out is the stair down to the crypt, where a skeleton watches its own floor before the exit. The
idol silences whoever takes it: its bearer casts nothing more. One companion must carry the idol out;
each picks one skill from a pool of eight catalogue skills.

| Obstacle | Answers | Not answers |
|----------|---------|-------------|
| **The nave** (`watches(keeper, nave)` while he stands at the altar; `tag(keeper, heavy)`, `rank(keeper, boss)`) | slip in (`blink` teleports into the nave, or through the temple wall straight into the shrine; `lightningFlash` dashes into the nave), blind him (`blindingFlash` at the altar, reached by the side aisle), or take his weight for a moment (`turnToMist`) and then move him: `hook` drags him out to the entry; `fireball`, `shieldBash`, or `vortex` on the well knock him into the sacred well | `shieldBash` alone (a boss: no stun; heavy: no knock); `hook` alone (it drags the hooker to him); `fireball`, `vortex` alone (heavy) |
| **The crypt** (`watches(skeleton, crypt)` while it stands there), below the gallery across a drop | from the gallery: `shieldBash` stuns it (or knocks it into the drop or the ossuary), `hook` drags it across the drop (it falls), `fireball` blows it into the drop or the ossuary, `vortex` on the ossuary sucks it in - by the lookout, or by the thief on the way in | anything the thief casts after taking the idol; `blink`, `lightningFlash`, `blindingFlash` (none stops it watching from where they can reach) |

Why no single skill works:
- Every nave answer but mist-and-move fails in the crypt: blink and lightningFlash only carry their
  caster, and the flash cannot reach the crypt (it is watched, and the thief is hushed by then).
- Every crypt answer fails at the altar: the keeper is heavy and a boss.

Level-local pieces: the `idol` zone (`remove(disjoint)`, `grant(silenced)` - blink's disjoint would
otherwise let the hush miss), the positional watch rules, and the recipes `getTo/3` (walk; else leap
by teleport or dash, or answer a watcher, and try again), `answer/1` and `answerAs/2` (one cast on the
watcher, or a vortex on a pit in its area via `knocks/6`; for a heavy one, `turnToMist` first),
`cleared/1` (the physics tries every aim: confirm it no longer watches) and `heist/0`, whose second
method lets the thief clear the crypt before taking the idol.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gallery ::drop:: crypt (skeleton; the ossuary) ---- exit
  |                 |
entry ---- nave ---- shrine (the idol)
  |   \      |       ||
  |    altar (keeper; the sacred well)
  ||==================||  (the temple wall, entry to shrine)
```

- **Areas (7):** entry, gallery, nave, altar, shrine, crypt, exit.
- **Links:** walkable entry-gallery, entry-nave, entry-altar (the side aisle), nave-altar,
  nave-shrine, shrine-crypt (the stair), crypt-exit; `gap(gallery, crypt)` (the drop);
  `wall(entry, shrine)` (the temple wall).
- **Features:** `feature(altar, well, chasm)`, `feature(crypt, ossuary, chasm)`.
- **Lines of sight:** the entry sees the nave and the altar; the nave sees the altar and the shrine;
  the gallery sees the crypt.
- **Keeper:** living, heavy, a boss; watches the nave while at the altar.
- **Skeleton:** watches the crypt while it stands there.
- **Mana:** 4 each (lightningFlash and fireball cost 2).
- **Victory:** `heist` - a companion enters the shrine (taking the idol: silenced), then reaches the
  exit.

## Hypothesis

Measured by `htn_components combos stealth_idol` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- **32 of 64** assignments win, by **16** methods; no solo plans; no dead skill.
  - a way into the nave (`blink`, `lightningFlash`, `blindingFlash`) and a way past the skeleton
    (`hook`, `shieldBash`, `fireball`, `vortex`), either companion holding either: 3 x 4 x 2 = 24;
  - `turnToMist` and a crypt answer, which then also moves the misted keeper: 4 x 2 = 8.
- The 32 losing assignments fail for nameable reasons: two ways in (the skeleton still watches), two
  crypt answers (the keeper cannot be moved or stunned), turnToMist with a way in, one skill twice.
- Usage: every skill in 8 winning assignments.
- Methods differ in kind: slip (teleport, dash, through a wall) vs. blind vs. mist-and-drop for the
  nave; stun vs. a drop (the gap, the ossuary) for the crypt.
- One skill, two roles: after `turnToMist`, one hook, fireball, bash or vortex clears the altar and
  the crypt. The crypt answer can be the thief's (on the way in) or the lookout's.
- Every assignment plans in under 16 s.

## Examples

### Example 1: Through the wall, and a hook

**Given:** the player knows `blink`, the mage knows `hook`.

**When:** `heist`

**Then:** the player blinks through the temple wall into the shrine; the idol takes the blink's
disjoint and silences the player. The mage, on the gallery, hooks the skeleton across the drop (it
falls); the player walks down and out.

### Example 2: The thief clears the way out first

**Given:** the player knows `vortex`, the mage knows `blindingFlash`.

**When:** `heist`

**Then:** the player's vortex on the ossuary takes the skeleton; the mage walks up the side aisle and
blinds the keeper; the player walks through the nave, takes the idol, and walks out.

### Example 3: Mist and a bash

**Given:** the player knows `turnToMist`, the mage knows `shieldBash`.

**When:** `heist`

**Then:** the player turns the keeper to mist; the mage bashes him into the well; later the mage
bashes the skeleton from the gallery.

### Example 4: A dash and a fireball

**Given:** the player knows `lightningFlash`, the mage knows `fireball`.

**When:** `heist`

**Then:** the player dashes into the nave; the mage's fireball blows the skeleton into the drop or
the ossuary.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured assignments win | Exactly the 32 measured assignments have a plan, by 16 methods; none solo; no dead skill. |
| P3 | The idol silences | In every plan (blink + hook, blindingFlash + fireball), the carrier casts nothing after taking the idol. |
| P4 | The heavy boss | hook + shieldBash and fireball + vortex have no plan. |
| P5 | Two ways in are not a way out | blink + lightningFlash and blink + blindingFlash have no plan. |
