# The Soulfire Wraith

## Purpose

An enemy-state-machine level about a hidden boss that has to be made to **spend itself**, with a
**telegraphed, magic heavy spell** the team provokes on purpose. A Wraith haunts the crypt,
stealthed: nothing can be aimed at it, only areas and zones reach it. It is a boss (no stuns), it
flies, and it is bound to its crypt (`rooted`: it follows no one; immune to forced movement). Its
state machine:

| State or trigger | Behaviour | Result |
|------------------|-----------|--------|
| `stealthed` | (innate) | cannot be aimed at: a taunt, a hook, a fireball or a bash at it all fail |
| `wet`, `electrocuted`, `chilled`, `burning` | `flinch` | it loses stealth, nothing more |
| `blinded`, `taunted` | `soulfire` (heavy, magic, aimed `here`) | wind-up on the crypt; one team cast; then the Wraith is out of hiding, `exhausted` and no longer `flying`, and the crypt bursts into flames that sear whoever stands there (`silenced`): a disjoint one is passed through, a shield breaks instead |
| `exhausted` | the window | its binding lapses (`suspends(exhausted, forcedMove)`): a knock or a hook drops it into the well; `wet` → `dead` |

The spell is magic, so a hook or a shield bash would interrupt it: that saves whoever stands in the
crypt, and wastes the window.

| Method | Reveal | Set off the soulfire | Finish |
|--------|--------|----------------------|--------|
| **Flash and ...** | - (the flash reaches the unseen) | `blindingFlash` in the crypt; its caster is disjoint and the searing passes through | the partner drops it into the well: `tidalWave` in the crypt, `fireball`, `vortex`, `hook` across the well from the balcony, `shieldBash` from the mist |
| **Ice first** | `blizzard` on the crypt (it flinches from the frost, and the crypt is an ice sheet) | `blindingFlash` or `taunt` | none needed: the soulfire's flames melt the ice into a puddle, and the spent Wraith drowns in it |
| **Reveal and taunt** | `tidalWave` in the crypt, or a `fireball` | the revealer steps out of the crypt; `taunt` | the revealer knocks it into the well |

Why no single skill works:
- Taunt, hook, fireball and bash cannot be aimed at it while it hides.
- A wave, a fire or a frost only reveals it: it is bound and not spent.
- Two flashes spend it but finish nothing; two taunts cannot be aimed.

Traps: water after the soulfire only puts out the fire on it, and frost after it only melts into
that water (the cold must come first); whoever stays in the crypt when the soulfire lands (and is
not disjoint) is silenced and finishes nothing; interrupting the soulfire keeps it fresh.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
nave ---- mist ---- crypt (Wraith; the well)
  |                   :
balcony . . . . . . . :   (gap: the well)
```

- **Areas:** nave, balcony, mist, crypt. Walkable: nave-balcony, nave-mist, mist-crypt. The
  balcony overlooks the crypt across the well (`gap(balcony, crypt)`).
- **Feature:** `feature(crypt, well, chasm)` - the well's mouth in the crypt.
- **Zones:** the mist is `shadows` (whoever stands there is stealthed).
- **Line of sight:** nave-mist, nave-balcony, mist-crypt, balcony-crypt (all both ways).
- **Wraith:** boss, flying, stealthed, rooted, `immune(wraith, forcedMove)`,
  `suspends(exhausted, forcedMove)`. `soulfire`: `self: remove(stealthed)`,
  `self: grant(exhausted)`, `self: remove(flying)`, `target: grant(silenced)`,
  `target: spill(flames)`; `heavy`, `kind magic`. `weakness(wraith, wet, exhausted, dead)`.
- **Goal:** `win` sets off the soulfire and confirms it is spent, then runs the standard
  `neutralize(wraith)` in that state (`exploit` or `intoThePit`); or reveals it first (a skill that
  makes it flinch and is not a lure), lets the team step out of the crypt (or stay), then sets it
  off; or ices its crypt first. A companion may be lost on the way (sacrifice is allowed).
- Both companions start in the nave with 4 mana. Pool: `blindingFlash`, `taunt`, `tidalWave`,
  `blizzard`, `fireball`, `vortex`, `hook`, `shieldBash`.

## Hypothesis

Measured with `htn_components combos fsm_wraith` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- 18 of 64 assignments win: 9 pairs, each whichever companion holds which half:
  - `blindingFlash` plus a finisher: `tidalWave`, `fireball`, `vortex`, `hook`, `shieldBash` (5);
  - ice first: `blizzard` plus `blindingFlash` or `taunt` (2);
  - `taunt` plus a revealer that also knocks: `tidalWave`, `fireball` (2).
- 9 methods, 0 solo plans, no dead skills.
- Skills with two roles: `tidalWave` and `fireball` reveal it and knock it into the well;
  `blizzard` reveals it and lays the ice its own flames turn to water; `blindingFlash` sets off the
  soulfire and survives it; `taunt` sets it off from a distance.
- The other 46 assignments lose for a nameable reason: two finishers (it is never spent), a taunt
  with nothing that reveals it (`hook`, `vortex`, `shieldBash`), a flash with a taunt (nothing
  finishes).

## Examples

### Example 1: Flash, then wave into the well

**Given:** the player knows `blindingFlash`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the player walks into the crypt and flashes; the blinded Wraith winds up its soulfire; it
lands, passing through the disjoint player; the Wraith is out of hiding, spent and wingless; the
mage walks into the burning crypt and its wave knocks the Wraith into the well (`fell`).

### Example 2: Ice first, and it drowns

**Given:** the player knows `taunt`, the mage knows `blizzard`.

**When:** `win`

**Then:** the mage's blizzard ices the crypt, and the Wraith flinches out of hiding; the player
taunts it; the soulfire spends it, and its flames melt the ice sheet into a puddle: the spent
Wraith is soaked, and drowns (`dead`).

### Example 3: Reveal, step out, taunt

**Given:** the player knows `taunt`, the mage knows `tidalWave`.

**When:** `win`

**Then:** the mage's wave in the crypt shows it; the mage steps back into the mist; the player
taunts it from the balcony; the soulfire burns an empty crypt and spends it; the mage walks back in
and its second wave knocks it into the well.

### Example 4: Flash, then hook across the well

**Given:** the player knows `hook`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the mage's flash sets off the soulfire; spent, the Wraith has lost its wings and its
binding; the player hooks it from the balcony across the well, and it falls.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan; no solo plan anywhere. |
| P2 | The measured pairs win | Exactly the nine measured pairs have a plan (18 of 64), with 9 methods and no dead skill. |
| P3 | The soulfire spends it | Every winning plan lets the soulfire land and grants `exhausted`; none interrupts it. |
| P4 | Revealing is not spending | `tidalWave`+`fireball`, `blizzard`+`fireball`, `taunt`+`hook`: no plan. |
| P5 | The crypt sears who stays | With the wave's reveal, every plan steps the waver out of the crypt before the taunt. |
