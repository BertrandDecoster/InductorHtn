# Sync: The Decoy

## Purpose

A synchronisation level: **one companion baits an enemy's big blow while the other pulls them clear
of it**. A golem blocks the arch to the switch room. Up on a balcony, a stone eye (a heavy machine)
watches the hall in front of the arch. Two companions, the player and the mage, pick one skill each
from a pool of seven. Someone gets the golem out of the arch, someone puts the eye out, and then one
of them walks across the hall onto the switch.

The decoy is a heavy attack (`ab_casting`): a taunted golem is dragged to its taunter and winds up a
`groundSlam` on that region. The slam is physical, so nothing stops it. The team gets exactly one
cast before it lands on everyone in the region but the golem. Taunt it from the balcony and the slam
stuns the eye, which then cannot watch, so one taunt does two jobs. The catch is that the taunter is
standing in the blast and has no second skill to escape with. The friend's one cast in the window
must get the taunter out. The Lost Vikings / Trine split: one draws the blow, the other saves them
from it.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The arch** | the golem is a `blocker`: nobody walks into its region | drag it out: `taunt` (to the taunter), `hook` (to the hooker); throw it into the alcove from the nook: `fireball`; suck it into the alcove: `vortex` (rooted there) |
| **The hall** | `watches(eye, hall)`: nobody walks in seen | blind the eye: `blindingFlash` next to it, `shieldBash` (stunned); or taunt the golem from the balcony so that its slam stuns the eye |
| **The slam** | the taunter is in the struck region; a companion may never take a heavy blow | the friend's cast in the window: `hook` the taunter away, `fireball` or `tidalWave` them off the balcony (they land in the camp), `vortex` everything movable on the balcony into the nook. The heavy eye stays and takes the blow |

Why no single skill works:
- Moving the golem does not blind the eye, and blinding the eye does not move the golem.
- The taunt does both jobs but leaves the taunter under the slam. A companion cannot be taunted
  (`immune(?x, taunted) :- canAct(?x)`), so a second taunt rescues nobody.
- `blindingFlash` only makes its own caster disjoint. `shieldBash` cannot stop a physical blow.
- `tidalWave` has no lure line (nothing next to the arch can be reached unseen), so it is only a
  rescuer.

`hook`, `fireball` and `vortex` each serve two roles: they lure the golem, or they pull the decoy out
of the slam.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
                balcony (eye: heavy machine)
               /    (a shove from the nook throws whoever is up there down to the camp)
camp ----- nook
  \          \
   --------- hall (watched) --- arch (golem) --- switch [plate] --- portcullis (door)
               \                /
                --- alcove ----
```

- **Lines of sight:** the camp and the nook see each other, the balcony, the arch and the alcove.
  The balcony sees the arch.
- **Push lines:** from the nook, a push on the arch lands in the alcove; a push on the balcony lands
  in the camp.
- **Golem:** living, `blocker`, `behavior(golem, taunted, groundSlam, here)`.
- **Eye:** machine, heavy (no push, pull or vortex moves it), `watches(eye, hall)`.
- **Switch:** a zone with `open(portcullis)`.
- **Goal:** `win` = a companion stands by in the camp or the nook; `lure` (a puller cast from any
  region that sees the arch, or `place(golem, R)` for a push or a vortex); `veil` (the eye is already
  out, or `inflict(blinded, eye)`); someone walks onto the switch; the portcullis must be open.

## Hypothesis

Measured with `htn_components combos sync_decoy` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 20 of the 49 assignments win, whichever companion holds which half (10 pairs):
  - the taunt with each of its 4 rescuers (`hook`, `fireball`, `vortex`, `tidalWave`);
  - each of the 3 lures (`hook`, `fireball`, `vortex`) with each of the 2 blinders
    (`blindingFlash`, `shieldBash`).
- 10 methods (distinct sets of skills cast), 0 solo plans, no dead skill. Usage: taunt 8; hook,
  fireball, vortex, blindingFlash, shieldBash 6 each; tidalWave 2.
- Every losing pair has a reason: two lures (the hall is still seen), two blinders (the arch is
  still held), a taunt with a blinder (nobody pulls the decoy out), or the wave with anything but the
  taunt (it lures nothing).
- One replan takes 2 to 7 s.

## Examples

### Example 1: Bait the slam, hook the decoy out

**Given:** the player knows `taunt`, the mage knows `hook`.

**When:** `win`

**Then:** the player climbs to the balcony and taunts the golem. The golem is dragged up and winds up
a ground slam there. In the window, the mage hooks the player down to the camp. The slam stuns the
eye. Someone crosses the unseen hall and steps onto the switch, and the portcullis opens.

### Example 2: The vortex takes the decoy and the golem

**Given:** the player knows `vortex`, the mage knows `taunt`.

**When:** `win`

**Then:** the mage taunts from the balcony. In the window, the player vortexes the nook, which sucks
the mage and the golem off the balcony (both rooted in the nook). The heavy eye stays behind and takes
the slam. The player walks to the switch.

### Example 3: Thrown into the alcove, then bashed

**Given:** the player knows `fireball`, the mage knows `shieldBash`.

**When:** `win`

**Then:** from the nook, the player's fireball throws the golem out of the arch into the alcove, and
the arch catches fire (harmless). The mage shield-bashes the eye from the nook, which stuns it. The
player crosses the hall and the burning arch onto the switch. No slam is ever wound up.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the 10 pairs above have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | The rescue is the one cast in the window | In every taunt plan, the slam is wound up on the balcony, and the first cast between the wind-up and the blow is the partner's rescue. |
| P5 | A flash saves only its caster | `taunt` + `blindingFlash` and `taunt` + `shieldBash` have no plan. |
| P6 | Companions cannot be taunted | `receptive(mage, taunted)` fails. |
