# The Shellback

## Purpose

An enemy-state-machine level about **guards**, and about a defence that turns into a weakness (Hades
armour, XCOM shields). A giant tortoise holds the causeway over a chasm. It is a boss (no hard
control), heavy (nothing moves it), blocks the way, and wears an energy shield that eats the next
hostile tag. Its state machine:

| State or trigger | Behaviour | Result |
|------------------|-----------|--------|
| `shielded` | (the catalogue's `absorb` reaction) | any hostile tag only pops the shield |
| `burning` | `withdraw`: curls into its shell | `curled` (its immunity to forced movement lapses: a ball that rolls) and `invulnerable` (no hostile tag lands) |
| `taunted` | `snap` at the taunter | the taunter is `rooted`; it is `exhausted` |
| `exhausted` | the window | `chilled` → `frozen` |

The fire that makes it untouchable also makes it roll.

| Method | Pop the shield | Set off a transition | Finish |
|--------|----------------|----------------------|--------|
| **Curl and roll** | any hostile tag: `zap`, `taunt`, `frostBolt`, `tidalWave` (its puddle), `magnetize` (its slow) | burn it: `fireball`, `flameWall` | roll it: fireball's own blast, `tidalWave`'s push from the shore, or `magnetize` from the islet (dragged across the chasm, it falls) |
| **Taunt and freeze** | `taunt` or `frostBolt` | `taunt`: it snaps and is spent | `frostBolt`: frozen |

Why no single skill works:
- The first hostile tag is always lost on the shield. A fire that pops the shield leaves flames there
  that will not burn it a second time, because a zone only takes whoever arrives.
- Before it curls it is heavy: a push, a pull or a hook does nothing to it (a hook drags the caster
  onto its shell instead).
- Curled, it is invulnerable. No taunt, frost or jolt lands, and a taunt's pull never happens.
- Taunted and spent, it is still standing until frost reaches it.

Traps: burn it after taunting it and the window closes (curled, the frost is refused). The taunter is
pinned by the snap. `zap` only ever pops the shield: a jolt means nothing to this beast.

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
                            :
                          chasm (below)
```

- **Lines:** a push from the shore on the causeway lands in the chasm; from the islet, the chasm lies
  between it and the causeway, so a pull from there drops it in.
- **Line of sight:** shore-causeway, far-causeway, islet-causeway, shore-strand, strand-islet.
- **Shellback:** boss, living, heavy, blocker, shielded. `behavior(shellback, burning, withdraw,
  self)`: `grant(curled)`, `grant(invulnerable)`; `suspends(curled, forcedMove)`.
  `behavior(shellback, taunted, snap, source)`: `target: grant(rooted)`, `self: grant(exhausted)`.
  `weakness(shellback, chilled, exhausted, frozen)`.
- **Goal:** `win` is the standard `neutralize(shellback)`, or the level's stages: pop the shield
  (any skill that lands a hostile tag, by cast, area or spilled zone), set off a behaviour, then the
  standard `neutralize` in the state it is left in (`intoThePit` rolls a curled shell; `exploit`
  plays the exhausted window).
- Both companions have 4 mana.

## Hypothesis

Measured with `htn_components combos fsm_shellback` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 16 of 49 assignments win: 8 pairs, each whichever companion holds which half:
  - `fireball` plus any popper: `zap`, `taunt`, `frostBolt`, `tidalWave`, `magnetize` (5 pairs);
  - `flameWall` plus a popper that also rolls: `tidalWave`, `magnetize` (2 pairs);
  - `taunt` plus `frostBolt` (1 pair).
- 8 methods, 0 solo plans, no dead skills.
- Several skills play two roles. `tidalWave` and `magnetize` pop the shield and later roll the
  shell. `taunt` and `frostBolt` pop the shield, or set off the snap and freeze.
- The other 13 pairs lose, each for a nameable reason: `fireball`+`flameWall` (the one fire is lost
  on the shield), `flameWall` with `taunt`, `frostBolt` or `zap` (nothing rolls it once curled), two
  poppers (nothing sets off a transition that pays).

## Examples

### Example 1: Pop, then fireball

**Given:** the player knows `zap`, the mage knows `fireball`.

**When:** `win`

**Then:** the player's jolt is eaten by the shield; the mage's fireball sets the causeway alight, the
Shellback curls up, and the same blast rolls it off into the chasm (`fell`).

### Example 2: Hook the rolled shell across

**Given:** the player knows `flameWall`, the mage knows `magnetize`.

**When:** `win`

**Then:** the mage's hook drags her onto its shell, and its slow is eaten by the shield; the player's
flames curl it; the mage walks round to the islet and hooks the curled shell across the chasm.

### Example 3: Taunt, then freeze

**Given:** the player knows `taunt`, the mage knows `frostBolt`.

**When:** `win`

**Then:** one blow pops the shield; the taunt makes it snap, pinning the player, and leaves it spent;
the mage's frost bolt freezes it (`frozen`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the eight measured pairs have a plan. |
| P3 | The shield eats the first blow | Every winning plan loses one hostile tag to `absorb`. |
| P4 | Curled, it takes no tags | After flameWall, a taunt or frost never finishes it. |
