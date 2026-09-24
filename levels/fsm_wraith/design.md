# The Soulfire Wraith

## Purpose

An enemy-state-machine level about a hidden boss that has to be made to **spend itself**, with a
**telegraphed, magic heavy spell** the team provokes on purpose. A Wraith haunts the crypt,
stealthed: nothing can be aimed at it, only areas and zones reach it. It is a boss (no stuns), it
flies, and it is bound to its crypt (nothing moves it). Its state machine:

| State or trigger | Behaviour | Result |
|------------------|-----------|--------|
| `stealthed` | (innate) | cannot be aimed at: a taunt, a hook, a bolt at it all fail |
| `wet`, `electrocuted` | `flinch` | it loses stealth, nothing more |
| `blinded`, `taunted` | `soulfire` (heavy, magic, aimed `here`) | wind-up on the crypt; one team cast; then the crypt bursts into flames and the Wraith is out of hiding, `exhausted`, and no longer `flying` |
| `exhausted` | the window | its binding lapses (`suspends(exhausted, forcedMove)`); `electrocuted` → `dead`; with no wings it falls into the well |

The spell is magic, so a hook or a shield bash would interrupt it: that saves whoever stands in the
crypt, and wastes the window.

| Method | Set off the soulfire | Survive it | Finish it (the other companion) |
|--------|----------------------|------------|---------------------------------|
| **Flash and ...** | `blindingFlash` in or next to the crypt (it reaches the unseen) | the flash made its caster `disjoint`: the blow passes through them | drop it into the well (`tidalWave` or `fireball` from the mist, `vortex` into the well, `hook` or `taunt` across the well from the balcony) or jolt it (`lightningFlash`) |
| **Reveal and taunt** | a jolt through the crypt (`lightningFlash` from the mist to the ossuary) or a wave from next door (`tidalWave`) shows it; then `taunt` | nobody is in the crypt | the revealer: a second bolt, or a second wave into the well |

Why no single skill works:
- Taunt, hook and bolt cannot be aimed at it while it hides.
- A jolt or a wave only reveals it: it is bound and not spent, so nothing moves it and a jolt does
  not kill it.
- Two flashes: the second soulfire finds the crypt already ablaze, and nobody finishes it.

Traps: fire does nothing to it (the flames just burn: `fireball` + `taunt` never reveals it);
`lightningFlash` + `tidalWave` reveal it twice and never spend it; interrupting the soulfire keeps it
fresh. After the spell, whoever stands in the crypt steps back to the mist, so a wave or a vortex
does not throw them into the well; a companion lost on the way is no win (`teamStanding`).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate --- nave --- mist --- crypt (Wraith) --- ossuary
           |                  |
        balcony . . . . . .  well (a shaft beside the crypt)
```

- **Zones:** the mist is `shadows` (whoever stands there is stealthed); the well is a `chasm`.
- **Lines:** a push from the mist (or the ossuary) on the crypt drops into the well; from the
  mist, the crypt lies between it and the ossuary (a bolt flies through); from the balcony, the
  well lies between it and the crypt (a hook or a taunt's drag drops what it pulls).
- **Line of sight:** the balcony overlooks the crypt and the well; the mist sees the crypt, the
  well and the ossuary; the crypt and the ossuary see each other.
- **Wraith:** boss, flying, stealthed, `immune(wraith, forcedMove)`, `suspends(exhausted,
  forcedMove)`. `soulfire`: `target: spill(flames)`, `self: remove(stealthed)`,
  `self: grant(exhausted)`, `self: remove(flying)`; `heavy`, `kind magic`.
  `weakness(wraith, electrocuted, exhausted, dead)`.
- **Goal:** `win` sets off the soulfire (revealing it first when the trigger must be aimed),
  confirms it is spent, steps everyone out of the crypt, runs the standard `neutralize(wraith)`
  in that state (`exploit` or `intoThePit`), and checks no companion was lost.
- Both companions have 4 mana. Pool: `blindingFlash`, `taunt`, `lightningFlash`, `tidalWave`,
  `fireball`, `vortex`, `hook`.

## Hypothesis

Measured with `htn_components combos fsm_wraith` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 16 of 49 assignments win: 8 pairs, each whichever companion holds which half:
  - `blindingFlash` plus any finisher: `taunt`, `lightningFlash`, `tidalWave`, `fireball`,
    `vortex`, `hook` (6 pairs);
  - `taunt` plus a revealer that also finishes: `lightningFlash`, `tidalWave` (2 pairs).
- 8 methods, 0 solo plans, no dead skills.
- Skills with two roles: `lightningFlash` reveals it (through the crypt) and kills it; `tidalWave`
  reveals it (wet) and washes it into the well; `taunt` sets off the soulfire, or drags the spent
  Wraith across the well.
- The other 13 pairs lose for a nameable reason: two finishers (it is never spent), fire with
  anything but the flash (fire never reveals it), a taunt with nothing that reveals it.

## Examples

### Example 1: Flash, then jolt

**Given:** the player knows `blindingFlash`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player walks into the crypt and flashes; the blinded Wraith winds up its soulfire; it
lands, passing through the disjoint player; the Wraith is out of hiding and spent; the mage's
lightning flash kills it (`dead`).

### Example 2: Reveal, taunt, jolt

**Given:** the player knows `lightningFlash`, the mage knows `taunt`.

**When:** `win`

**Then:** the player's bolt from the mist to the ossuary strikes through the crypt, and the Wraith
flinches out of hiding; the mage taunts it from the balcony; the soulfire burns an empty crypt and
spends it; the player's second bolt kills it.

### Example 3: Flash, then hook into the well

**Given:** the player knows `hook`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the mage's flash sets off the soulfire; spent, the Wraith has lost its wings and its
binding; the player hooks it from the balcony across the well, and it falls (`fell`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the eight measured pairs have a plan. |
| P3 | The soulfire spends it | Every winning plan lets the soulfire land and grants `exhausted`. |
| P4 | The flash survives the blow | With `blindingFlash`, the flasher stands in the crypt, disjoint, when it lands. |
| P5 | Revealing is not spending | `lightningFlash`+`tidalWave` and `fireball`+`taunt`: no plan. |
