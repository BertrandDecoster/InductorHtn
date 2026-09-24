# The Shellback

## Purpose

An enemy-state-machine level about **guards**, and about a defence that turns into a weakness (Hades
armour, XCOM shields). A giant tortoise holds the causeway over a chasm. It is a boss (no stuns),
heavy (nothing moves it), blocks the way, and wears an energy shield that eats the next hostile tag.
Its state machine:

| State or trigger | Behaviour | Result |
|------------------|-----------|--------|
| `shielded` | (the catalogue's `absorb` reaction) | any hostile tag only pops the shield |
| `burning` | `withdraw`: curls into its shell | `shielded` again (the shell closes), `heavy` removed (it lets go of the stone: a ball that rolls) |
| `taunted` | `snap` at the taunter | the taunter is `rooted`; it is `exhausted` |
| `exhausted` | the window | `chilled` or `electrocuted` → `dead` |

The fire that shuts it in also makes it roll. Turn to Mist is the third way in: for a moment, no
shield and no weight.

| Method | Take the shield | Set it up | Finish |
|--------|-----------------|-----------|--------|
| **Curl and roll** | any hostile tag: `taunt`, `tidalWave` (wet), `lightningFlash` | `fireball`: it burns and curls | the same fireball's blast rolls it off the causeway into the chasm |
| **Taunt and strike** | the first `taunt` | the second `taunt`: it snaps and is spent | `blizzard` (chilled) or `lightningFlash` (electrocuted) on its head |
| **Mist and roll** | `turnToMist`: for a moment | `turnToMist`: for a moment, not heavy | at once: a push from the shore (`fireball`, `tidalWave`), a pull across the chasm from the islet (`hook`, a `taunt`'s drag), or a `vortex` on the chasm |

Why no single skill works:
- The first hostile tag is always lost on the shield. A fire that pops the shield leaves flames there
  that will not burn it a second time, because a zone only takes whoever arrives.
- While it is heavy, a push, a pull or a vortex does nothing to it (a hook drags the caster onto
  the causeway instead).
- Taunted and spent, it is still standing until frost or a jolt reaches it.
- The mist moves nothing by itself, and lasts only through the next cast.

Traps: `blizzard` then `fireball` only thaws it (frost and fire undo each other); `hook` pops no
shield, so fireball's one fire is lost; a `vortex` on the causeway pops the shield but sucks the
partner onto it, rooted; once curled, the shell is up again and eats the next tag.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
strand --- islet                (the islet faces the causeway across the chasm)
  |
shore (player, mage) --- causeway (Shellback) --- far
                            |
                          chasm (below)
```

- **Lines:** a push from the shore on the causeway lands in the chasm; from the islet, the chasm lies
  between it and the causeway, so a pull from there drops it in. The chasm is next to the causeway,
  so a vortex on the chasm draws the causeway in.
- **Line of sight:** shore-causeway, far-causeway, islet-causeway, shore-strand, strand-islet; the
  shore and the islet see the chasm.
- **Shellback:** boss, living, heavy, shielded, blocker. `behavior(shellback, burning, withdraw,
  self)`: `remove(heavy)`, `grant(shielded)`. `behavior(shellback, taunted, snap, source)`:
  `target: grant(rooted)`, `self: grant(exhausted)`. `weakness(shellback, chilled|electrocuted,
  exhausted, dead)`.
- **Goal:** `win` is the standard `neutralize(shellback)` (the guard off first; `intoThePit` strips
  the heavy with the mist), or the level's stages: pop the shield (any skill that lands a hostile
  tag), set off a behaviour, then the standard `neutralize` in the state it is left in; and no
  companion lost.
- Both companions have 4 mana. Pool: `fireball`, `tidalWave`, `hook`, `taunt`, `blizzard`,
  `lightningFlash`, `turnToMist`, `vortex`.

## Hypothesis

Measured with `htn_components combos fsm_shellback` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 20 of 64 assignments win: 10 pairs, each whichever companion holds which half:
  - `fireball` plus a popper: `taunt`, `tidalWave`, `lightningFlash` (3 pairs);
  - `taunt` plus a strike: `blizzard`, `lightningFlash` (2 pairs);
  - `turnToMist` plus a mover: `fireball`, `tidalWave`, `hook`, `taunt`, `vortex` (5 pairs).
- 10 methods, 0 solo plans, no dead skills.
- Several skills play two roles. `taunt` pops the shield, sets off the snap, or drags the misted
  shell across the chasm. `lightningFlash` pops the shield or strikes the spent head. `fireball`
  curls and rolls it, or pushes the misted shell. `tidalWave` pops or pushes.
- The other 18 pairs lose, each for a nameable reason: `fireball`+`blizzard` (frost thaws the fire),
  `fireball`+`hook` (nothing pops the shield but the fire), `fireball`+`vortex` (the vortex drags
  the partner onto the causeway), two movers without mist or fire (it is heavy), two poppers (nothing
  pays off).

## Examples

### Example 1: Pop, then fireball

**Given:** the player knows `taunt`, the mage knows `fireball`.

**When:** `win`

**Then:** the player's taunt is eaten by the shield; the mage's fireball sets the causeway alight,
the Shellback curls up (no longer heavy), and the same blast rolls it off into the chasm (`fell`).

### Example 2: Mist, then hook across

**Given:** the player knows `hook`, the mage knows `turnToMist`.

**When:** `win`

**Then:** the mage turns it to mist; the player walks to the islet and, while the mist lasts, hooks
the weightless shell across the chasm, where it falls.

### Example 3: Taunt, then freeze

**Given:** the player knows `taunt`, the mage knows `blizzard`.

**When:** `win`

**Then:** the first taunt pops the shield; the second makes it snap, pinning the player, and leaves
it spent; the mage's blizzard stops it (`dead`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the ten measured pairs have a plan. |
| P3 | The shield eats the first blow | Without the mist, every winning plan loses one hostile tag to `absorb`. |
| P4 | Heavy, it holds | `fireball`+`hook`, `fireball`+`blizzard`, `vortex`+`hook`: no plan. |
