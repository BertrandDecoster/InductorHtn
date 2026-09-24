# The Shellback

## Purpose

An enemy-state-machine level about a boss whose **defence becomes its weakness**. A giant tortoise
sits on the causeway over a chasm. It is a boss (no stuns), heavy (nothing moves it), and wears an
energy shield that eats the next hostile tag. Its state machine:

| State or trigger | Behaviour | Result |
|------------------|-----------|--------|
| `shielded` | (a guard) | the next hostile tag only pops the shield |
| `burning` | `withdraw` (self) | it curls into its shell: `shielded` again, but `heavy` removed - a ball that rolls |
| `taunted` | it follows its taunter (a taunt's chase), then `snap` (source) | the taunter is `rooted`; the Shellback is `exhausted` |
| `exhausted` | the window | `chilled` or `electrocuted` → `dead` |

And Turn to Mist takes its weight and its shield away for a moment.

| Method | Step 1 | Step 2 | Step 3 |
|--------|--------|--------|--------|
| **Curl and roll** | a popper takes the shield: `taunt`, `lightningFlash`, `tidalWave` (standing on the causeway), `vortex` (its moment of roots) | `fireball`: it burns and curls (no longer heavy) | the same blast knocks the ball into the abyss or over the edge into the chasm (or a vortex draws it into the abyss) |
| **Taunt and strike** | `taunt` pops the shield (or a `lightningFlash` or a `blizzard` does) | a (second) `taunt`: it follows its taunter to the shore and snaps itself spent | `blizzard` or `lightningFlash` on its head |
| **Mist and roll** | `turnToMist`: for a moment no shield, no weight | in that moment, a knock (`fireball`; `tidalWave` on the causeway; a `vortex` into the abyss) or a `hook` across the chasm from the islet | - |

Why no single skill works:
- The first hostile tag is always lost on the shield; a fireball that pops it leaves flames that
  will not burn it twice.
- Two taunts spend it, but nothing strikes the head; two jolts pop the shield, but it never tires.
- The mist lasts one cast: whoever turned it to mist has nothing left to knock it with.

Traps: frost then fire (`blizzard`+`fireball`) only melts the ice sheet into a puddle: it is soaked,
not burning. `fireball`+`hook`: the hook pops nothing, and on the heavy shell it only drags its
caster onto the causeway. Taunted, it walks round by the strand, never across the chasm.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
strand ------ islet
  |             :   (gap: the chasm)
shore ------ causeway (Shellback; the abyss)
```

- **Areas:** shore, causeway, strand, islet. Walkable: shore-causeway, shore-strand, strand-islet.
  The causeway and the islet face each other across the chasm (`gap(causeway, islet)`).
- **Feature:** `feature(causeway, abyss, chasm)` - the open side of the causeway. A knock on the
  causeway sends its target into the abyss or over the edge into the chasm; a vortex aimed at the
  abyss draws everything movable on the causeway into it.
- **Line of sight:** shore-causeway, islet-causeway (across the chasm), shore-strand, strand-islet.
- **Shellback:** boss, living, heavy, shielded. `behavior(shellback, burning, withdraw, self)`:
  `remove(heavy)`, `grant(shielded)`. `behavior(shellback, taunted, snap, source)`:
  `target: grant(rooted)`, `self: grant(exhausted)`. `weakness(shellback, chilled|electrocuted,
  exhausted, dead)`.
- **Goal:** `win` is the standard `neutralize(shellback)` (the guard off first; `intoThePit` strips
  the heavy with the mist), or the level's stages: pop the shield (any skill that lands a hostile
  tag on it, a vortex's roots included), set off a behaviour, then the standard `neutralize` in the
  state it is left in. A companion may be lost on the way (sacrifice is allowed).
- Both companions start on the shore with 4 mana. Pool: `fireball`, `tidalWave`, `hook`, `taunt`,
  `blizzard`, `lightningFlash`, `turnToMist`, `vortex`.

## Hypothesis

Measured with `htn_components combos fsm_shellback` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 20 of 64 assignments win: 10 pairs, each whichever companion holds which half:
  - `fireball` plus a popper: `taunt`, `tidalWave`, `lightningFlash`, `vortex` (4 pairs);
  - `taunt` plus a strike: `blizzard`, `lightningFlash` (2 pairs);
  - `turnToMist` plus a mover: `fireball`, `tidalWave`, `hook`, `vortex` (4 pairs).
- 10 methods, 0 solo plans, no dead skills.
- Skills with two roles: `taunt` pops the shield or sets off the snap; `lightningFlash` pops the
  shield or strikes the spent head; `fireball` curls and rolls it, or knocks the misted shell;
  `tidalWave` pops or knocks; `vortex` pops (its roots) or draws the ball into the abyss.
- The other 34 assignments lose for a nameable reason: frost then fire leaves only a puddle, the hook pops
  nothing, the taunt no longer drags anything across the chasm (it walks round), two poppers or two
  movers pay nothing off.

## Examples

### Example 1: Pop, then curl and roll

**Given:** the player knows `taunt`, the mage knows `fireball`.

**When:** `win`

**Then:** the player's taunt is eaten by the shield; the mage's fireball sets the causeway alight,
the Shellback curls up (no longer heavy), and the same blast knocks it into the abyss (`fell`).

### Example 2: Mist, then hook across

**Given:** the player knows `hook`, the mage knows `turnToMist`.

**When:** `win`

**Then:** the mage turns it to mist; the player walks round to the islet and, while the mist lasts,
hooks the weightless shell across the chasm, where it falls.

### Example 3: Taunt, follow, snap, freeze

**Given:** the player knows `taunt`, the mage knows `blizzard`.

**When:** `win`

**Then:** the first taunt pops the shield; the second makes it lumber after the player onto the
shore and snap, pinning the player and spending itself; the mage's blizzard stops it (`dead`).

### Example 4: The vortex pops, then gathers

**Given:** the player knows `vortex`, the mage knows `fireball`.

**When:** `win`

**Then:** the vortex's moment of roots is eaten by the shield; the fireball makes it curl; then a
second vortex on the abyss draws the ball in (or the fireball's own blast knocks it).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan; no solo plan anywhere. |
| P2 | The measured pairs win | Exactly the ten measured pairs have a plan (20 of 64), with 10 methods and no dead skill. |
| P3 | The shield eats the first blow | Without the mist, every winning plan loses one hostile tag to `absorb`. |
| P4 | Heavy, it holds | `fireball`+`hook`, `blizzard`+`fireball`, `vortex`+`hook`: no plan. |
| P5 | Knockbacks stay on the causeway | No plan moves the Shellback to another area by force: it goes down where it stands. |
