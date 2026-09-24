# The Drowned Knight

## Purpose

A hazard-terrain level where **the enemy's own armour is the puzzle**. A knight in full plate holds a
keep on a spit of rock: on one side the keep drops into a moat (a chasm), and below the quay wall
lies a deep lake. Nobody can hurt the knight; the terrain can. The armour cuts both ways - it wards
off every push and pull, and it would drag the knight to the bottom of the lake. The player and the
mage pick one skill each from a pool of eight.

| Method | First | Then |
|--------|-------|------|
| **Drown it** (keep the armour on, make it move itself) | a friend pushes the baiter off the quay into the lake (`gust`, `tidalWave`) | the baiter provokes the knight from the water (`taunt`, `enrage`): it leaps in after them and sinks in its plate |
| **Drop it** (take the armour off) | strip the armour (`sunder`, `dispel`): now it floats, but it can be moved | push it off the keep into the moat from the causeway (`gust`, `shieldBash`, `tidalWave`), or pull it across the moat from the tower (`magnetize`, `taunt`) |

Why no single skill works:
- The armour wards off forced movement, and a stripped knight no longer drowns.
- A knight taunted or enraged from dry land just leaps over to its provoker: a leap never falls.
- Nobody can walk down to the lake; the only way in is to be pushed off the quay.
- A friend shield-bashed into the lake is stunned (silenced) and cannot bait.

`taunt` serves two roles (the bait from the water; a pull across the moat), and so do `gust` and
`tidalWave` (push a friend into the lake; push the stripped knight into the moat).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate --- quay --- causeway --- keep (knight) ::: moat
 |        :                      :
tower    lake (below the wall; no way down but a fall)
```

- **Walking:** gate-quay-causeway-keep, gate-tower. The knight holds the keep (a blocker). The lake
  and the moat connect to nothing.
- **Line of sight:** gate to quay; causeway, tower and lake to the keep.
- **Push lines:** from the gate, whoever stands on the quay goes into the lake; from the causeway,
  the keep's occupant goes into the moat; a pull from the tower crosses the moat.
- **Zones:** the lake is `deepWater`, the moat is `chasm`.
- **Knight** (level-local rules): living, `armored`, blocker.
  - `weakness(knight, deepWater, armored, fell)`: it sinks only in its plate.
  - `behavior(knight, taunted, lunge, source)`, `behavior(knight, berserk, lunge, source)` with
    `effect(lunge, target, dash)`: provoked, it leaps at whoever did it.
- Both companions have 2 mana (one tidalWave).
- **Goal** `win`: `neutralize(knight)` (the generic armour-then-drop recipe), or `bait(knight)`: a
  companion is pushed into water that drowns the knight, then provokes it from there.

## Hypothesis

Measured by `htn_components combos hazard_drowned_knight` (pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 28 of 64 assignments win: 14 pairs, whichever companion holds which half:
  - `sunder` or `dispel`, plus `gust`, `shieldBash`, `tidalWave`, `magnetize` or `taunt`: 10 pairs;
  - `taunt` or `enrage`, plus `gust` or `tidalWave`: 4 pairs.
- 14 methods (distinct skill sets) of two opposite kinds. No solo plans; no dead skills.
- Every loss has a nameable reason: two strippers (nothing moves it), a mover without a stripper
  (the armour holds), a provoker without a friend to push them in (it just leaps over),
  `shieldBash` with a provoker (the bashed friend is stunned), `magnetize` with a provoker (a hook
  cannot put anyone in the lake).

## Examples

### Example 1: Bait it with a taunt

**Given:** the player knows `gust`, the mage knows `taunt`.

**When:** `win`

**Then:** the mage walks onto the quay and the player gusts them over the wall into the lake; the
mage taunts the knight from the water, it leaps in after them and sinks in its armour.

### Example 2: Bait it with rage

**Given:** the player knows `tidalWave`, the mage knows `enrage`.

**When:** `win`

**Then:** the player's wave washes the mage off the quay into the lake; the enraged knight leaps in
and sinks.

### Example 3: Strip, then push

**Given:** the player knows `sunder`, the mage knows `gust`.

**When:** `win`

**Then:** the player sunders the armour from the causeway; the mage gusts the knight off the keep
into the moat.

### Example 4: Strip, then pull across

**Given:** the player knows `dispel`, the mage knows `taunt`.

**When:** `win`

**Then:** the player dispels the armour; the mage walks to the tower and taunts the knight, which
is dragged across the moat and falls.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Fourteen pairs win | Exactly the fourteen measured pairs have a plan. |
| P3 | Each hand matters | A pair wins whichever companion holds which half. |
| P4 | A bashed friend cannot bait | shieldBash with taunt or enrage: no plan (the bait is stunned). |
| P5 | Stripped, it does not drown | With the armour off, no winning plan uses the lake. |
