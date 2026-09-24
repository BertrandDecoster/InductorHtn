# The Sinkhole

## Purpose

The demo level for the ability layer (`components/abilities/`), on the standard catalogue. A stone
golem stands at the rim of a sinkhole; beside the rim, a pump automaton wades in a flooded pool and a
wicker tender minds an oil slick. The player and the mage pick one skill each from seven.

The golem is the level's **heavy attack**. Provoked (taunted, or pinned by a vortex), it stamps: a
telegraphed cave-in (the catalogue's `caveIn`, physical, so it cannot be interrupted) on its own rim.
The rim falls into the sinkhole with the golem and everything else standing on it. The team wants to
trigger it, with the mooks on the rim and nobody of its own there. It is both the weapon and the
danger:
- a vortex on the rim draws both mooks onto it and pins the golem, which stamps at once. But it draws
  the other companion off the ledge too, pinned. The team gets one cast before the rim goes;
- provoking the golem cuts the level in two: afterwards nothing can stand on the rim, and whatever
  must be done from there is out of reach.

It exists to show the layer's claims in one place:
- skills are bundles of keywords (a vortex is a pull-in and a root; a wave is a soak and a push);
- combos are physics (oil + fire = blaze, wet + fire = steam);
- a heavy boss cannot be moved until something takes its weight away (Turn to Mist);
- a telegraphed heavy attack is a weapon to aim, and a window to survive (blink out, hook the pillar,
  or be pulled out by a friend's vortex);
- different pairs clear the level by different recipes.

| Method | Skills | How |
|--------|--------|-----|
| **The sinkhole** | `vortex` + `blink` or `hook` | the vortex on the rim gathers everything and pins the golem; the pinned companion blinks out, or hooks the stone pillar on the ledge and is dragged to it |
| **Gather first** | `hook` + `taunt` | hook both mooks onto the rim from the rim, step off, taunt the golem |
| **Mooks first** | `tidalWave` or `fireball`, then `taunt` or `vortex` | a wave from the rim washes both mooks into the pit, or a fireball knocks the wader in and another burns the tender; step off; provoke the golem. With a vortex, it draws the mage back onto the rim: the player's second vortex, on the ledge, pulls the mage out in the window |
| **Mist** | `turnToMist` + `tidalWave` | mist the golem, wash it off the rim into the pit, then wash both mooks off |

Why no single skill works:
- Only a provoked cave-in or the pit stops the golem, and the pit needs its weight gone first
  (`turnToMist`) and then a push.
- A vortex alone gathers and provokes, but the drawn companion has no way out.
- A taunt only provokes: the mooks ignore taunts, so they must be dealt with by something else.
- Fire alone kills the tender and knocks the wader into the pit, but never provokes the golem.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
            ledge (player, mage; stone pillar)
              |
   slick --- rim (golem) --- pool
                \
                 pit (chasm)
```

- **Walking:** ledge–rim, rim–pool and rim–slick. The pit is next to the rim; nobody walks into it.
- **Line of sight:** the ledge sees everything; the rim sees the ledge, the pool and the slick.
- **Push lines:** ledge on rim → pit; rim on pool → pit; rim on slick → pit.
- **Zones:** the pool is a puddle (wet), the slick oils, the pit is a chasm.
- **Pillar:** a heavy object on the ledge, to hook onto.
- Both companions have 4 mana.

| Enemy | Tags | What stops it |
|-------|------|---------------|
| golem | `heavy`, `living`, boss; `behavior(golem, taunted \| rooted, caveIn, here)` | its own cave-in; mist, then a push into the pit |
| wader | `machine`, `wet`; ignores taunts | the pit (a push from the rim); the cave-in |
| tender | `wooden`, `oiled`; ignores taunts | fire (the oil blazes); the pit; the cave-in |

**Goal:** `clearSinkhole`, with four staged methods: the mooks first, then everyone steps off the rim
and the golem goes down; the golem first, then the mooks; gather the mooks onto the rim, step off,
provoke the golem; or provoke it with everything already on the rim. Every method ends by checking
that no companion went down with the rim (`confirmTeam`).

## Hypothesis

Measured by `htn_components combos sinkhole` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 16 of 49 assignments win, i.e. 8 of the 21 pairs, whichever companion holds which half:
  - `vortex` + `blink`, `hook` (the sinkhole);
  - `hook` + `taunt` (gather first);
  - `vortex` or `taunt`, + `fireball` or `tidalWave` (mooks first);
  - `turnToMist` + `tidalWave` (mist).
- 8 methods (distinct skill sets), of four kinds. No dead skills, and no plan carried by one
  companion. Several skills serve two roles: `vortex` gathers and provokes, and a second vortex
  pulls a friend out of the window; `hook` gathers the mooks or anchors an escape; `tidalWave`
  washes the mooks off or washes the misted golem away.
- The losing pairs each lose for a reason you can name:
  - a vortex with no escape (`turnToMist`, `taunt`): the drawn companion would fall with the rim;
  - two provokers, or a provoker and nothing for the mooks: the mooks ignore taunts;
  - fire and no provoker: the golem stays.

## Examples

### Example 1: The sinkhole

**Given:** the default kit: the player knows `vortex`, the mage knows `blink`.

**When:** `clearSinkhole`

**Then:** the player's vortex on the rim draws the wader, the tender and the mage onto it, and pins
the golem, which winds up its cave-in. In the window the mage blinks back to the ledge. The rim falls
with the golem, the wader and the tender (`fell`); nobody of the team does.

### Example 2: Gather first

**Given:** the player knows `hook`, the mage knows `taunt`.

**When:** `clearSinkhole`

**Then:** the player hooks the wader and the tender onto the rim and steps off. The mage taunts the
golem, and the cave-in takes all three.

### Example 3: Mist

**Given:** the player knows `turnToMist`, the mage knows `tidalWave`.

**When:** `clearSinkhole`

**Then:** the golem turns to mist; the mage's wave from the ledge washes it into the pit. A second
wave from the rim washes the wader and the tender in. The golem is never provoked.

### Example 4: The vortex pulls a friend back

**Given:** the player knows `vortex`, the mage knows `fireball`.

**When:** `clearSinkhole`

**Then:** the mage knocks the wader into the pit and burns the tender, and steps off. The player's
vortex on the rim pins the golem and draws the mage back in. In the window the player's second
vortex, on the ledge, pulls the mage out.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Eight pairs win | Exactly the eight measured pairs have a plan. |
| P3 | Nobody falls with the rim | No winning plan loses a companion to the sinkhole. |
| P4 | The vortex takes friends | A vortex with no escape (`turnToMist`, `taunt`) loses. |
| P5 | The golem first cuts the rim | With `hook` and `taunt`, the golem first, then the mooks, has no plan. |
| P6 | The golem cannot be moved as it stands | Without the mist, no push places it in the pit. |
