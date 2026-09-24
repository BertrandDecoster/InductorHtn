# The Idol

## Purpose

A stealth level on the ability layer where **you can slip in, but you come out hushed**. A golden
idol sits in a temple shrine. The way in is the nave, watched from the altar by a keeper rooted in
prayer. The way out is a one-way chute down to the crypt, where a skeleton watches the exit. The
idol silences whoever takes it: its bearer casts nothing more. One companion must carry the idol out;
each picks one skill from a pool of eight catalogue skills.

| Obstacle | Answers | Not answers |
|----------|---------|-------------|
| **The nave** (`watches(keeper, nave)` while he stands at the altar; `tag(keeper, heavy)`) | slip in (`blink` teleports, `lightningFlash` dashes: both pass a watched region), or take his weight for a moment (`turnToMist`) and then drag him off the altar (`taunt`, `hook`) or draw him into the nave (`vortex`) | any mover alone (he is heavy; a hook drags the hooker onto the altar instead); `blindingFlash` and `shieldBash` (the altar is next to the nave alone, so nobody gets close) |
| **The crypt** (`watches(skeleton, crypt)` while it stands there), reached down the chute | from the ledge: blind the skeleton (`blindingFlash`), stun it (`shieldBash`), drag it up onto the ledge (`taunt`, `hook`), draw it into the ossuary pit (`vortex` on the ossuary) or onto the ledge (`vortex` on the ledge) | anything the thief casts after taking the idol; a blink or a dash (nobody in the chute sees into the crypt, and the silenced thief casts nothing) |

Why no single skill works:
- Every nave answer but mist-and-move fails in the crypt: blink and lightningFlash only carry their
  caster, and the other companion blinking into the crypt does not help the thief.
- Every crypt answer fails in the nave: the keeper is heavy and the altar is out of reach.

Level-local pieces: the `idol` zone (`remove(disjoint)`, `grant(silenced)` - blink's disjoint would
otherwise let the hush miss), the positional watch rules, and the recipes `getTo/3` (walk; else leap
by teleport or dash, or stop a watcher watching, and try again), `unwatch/1` and `budge/1`.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
ledge .................................. (sees down into the crypt)
  |                                        |
entry (player, mage) ---- nave ---- shrine (idol) --> chute ---- crypt (skeleton) ---- exit
                           |                                       |
                         altar (keeper)                          ossuary (a pit)
```

- **Lines of sight:** the entry sees the nave and the altar; the nave sees the altar and the shrine;
  the ledge sees the crypt and the ossuary.
- **Push line:** from the ledge, whatever stands in the crypt goes into the ossuary (a chasm).
- **The chute runs one way:** shrine to crypt.
- **Keeper:** living, heavy; watches the nave while at the altar.
- **Skeleton:** watches the crypt while it stands there.
- **Mana:** 4 each (lightningFlash costs 2).
- **Victory:** `heist` - a companion enters the shrine (taking the idol: silenced), then reaches the exit.

## Hypothesis

Measured by `htn_components combos stealth_idol` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- **26 of 64** assignments win, by **13** methods; no solo plans; no dead skill.
  - a way into the nave (`blink`, `lightningFlash`) and a way past the skeleton (`blindingFlash`,
    `shieldBash`, `taunt`, `hook`, `vortex`), either companion holding either: 2 x 5 x 2 = 20;
  - `turnToMist` and a mover (`taunt`, `hook`, `vortex`), which then serves both watchers: 3 x 2 = 6.
    The mover clears the crypt from the ledge either before its holder takes the idol, or as the lookout.
- The 38 losing assignments fail for nameable reasons: two ways in (the skeleton still watches),
  two crypt answers (the keeper cannot be moved or reached), turnToMist with a way in or a stun.
- Usage: blink, lightningFlash 10; turnToMist, taunt, hook, vortex 6; blindingFlash, shieldBash 4.
- One skill, two roles: after `turnToMist`, a `taunt`, `hook` or `vortex` clears the altar and the crypt.
- Every plan takes under 5 s.

## Examples

### Example 1: Blink in, taunt the skeleton

**Given:** the player knows `blink`, the mage knows `taunt`.

**When:** `heist`

**Then:** the player blinks into the nave and walks into the shrine; the idol takes the blink's
disjoint and silences the player. The mage, on the ledge, taunts the skeleton up out of the crypt; the
player drops down the chute and walks out.

### Example 2: A dash and a bash

**Given:** the player knows `lightningFlash`, the mage knows `shieldBash`.

**When:** `heist`

**Then:** the player dashes into the nave; the mage stuns the skeleton from the ledge.

### Example 3: Mist and a taunt

**Given:** the player knows `turnToMist`, the mage knows `taunt`.

**When:** `heist`

**Then:** the player turns the keeper to mist; within the moment the mage taunts him off the altar;
later the mage taunts the skeleton up to the ledge.

### Example 4: Into the ossuary

**Given:** the player knows `blink`, the mage knows `vortex`.

**When:** `heist`

**Then:** the mage's vortex on the ossuary draws the skeleton into the pit (it falls).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured assignments win | Exactly the 26 measured assignments have a plan; none solo; no dead skill. |
| P3 | The idol silences | In every plan (blink + hook, lightningFlash + blindingFlash), the carrier casts nothing after taking the idol. |
| P4 | The heavy keeper | hook + shieldBash and taunt + vortex have no plan. |
| P5 | Two ways in are not a way out | blink + lightningFlash has no plan. |
