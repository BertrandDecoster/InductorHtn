# The Lunging Wraith

## Purpose

An enemy-state-machine level built around a **guard that hides** (stealth) and a **telegraphed
reaction that spends the boss** (a Dark Souls recovery window). The Wraith haunts the crypt,
stealthed: nothing can be aimed at it, only areas and zones reach it. It is a boss (no hard control)
and bound to its crypt (nothing drags or pushes it: it moves only by its own lunge).

Its state machine is three tags and two behaviours:

| Trigger | Behaviour | Leaves it |
|---------|-----------|-----------|
| `taunted` or `blinded` | `lunge` at the source: loses stealth, spends itself, stuns the source, dashes to it | `exhausted` |
| `electrocuted` | `flinch`: shaken out of hiding | not stealthed |
| (`exhausted`) | the window: `electrocuted` → dead, `burning` → dead, `chilled` → frozen | - |

Three methods:

| Method | Lure | Strike (the other companion) |
|--------|------|------------------------------|
| **Lure and strike** | `provoke` (an area taunt: it reaches the unseen) or `flashbang` (it blinds, and the blinded Wraith lashes out) | in the window: `zap`, `chainLightning`, `frostBolt`, `flameWall` |
| **Lure into fire** | the same lures, sprung from a region `flameWall` set alight first | nothing: it lunges, already spent, into the flames and burns |
| **Shake and taunt** | `chainLightning` shakes it out of hiding; now `taunt` reaches it and spends it | a second `chainLightning` |

Why no single skill works:
- A lure alone leaves it spent and standing. The lure is stunned by the lunge, so it could not
  strike anyway.
- A strike before the lunge does nothing lasting. `zap`, `frostBolt` and `taunt` cannot be aimed at
  it while it hides.
- A chain alone shakes it out of hiding, but never spends it.

Traps:
- Lure it from the mist and it lunges back into hiding (the mist is a shadows zone). Then only an area
  or a zone (`chainLightning`, `flameWall`) reaches it in its window: `zap` and `frostBolt` cannot be
  aimed.
- `flashbang` blinds everyone in the crypt, companions included.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage) --- nave --- mist --- crypt (Wraith) --- ossuary
                         |                  .
                      balcony . . . . . . . .   (the balcony overlooks the mist and the crypt)
```

- **Line of sight:** gate-nave, nave-mist, nave-balcony, balcony-mist, balcony-crypt, mist-crypt,
  crypt-ossuary.
- **Zones:** `onEnter(mist, shadows)`: whoever arrives is stealthed. That includes companions walking
  through, and the Wraith if it lunges there.
- **Wraith:** boss, stealthed, `immune(wraith, forcedMove)`. `behavior(wraith, taunted, lunge,
  source)`, `behavior(wraith, blinded, lunge, source)`, `behavior(wraith, electrocuted, flinch,
  self)`. `lunge` = `self: remove(stealthed)`, `self: grant(exhausted)`, `target: grant(stunned)`,
  `target: dash`, in that order: it lands already spent. `flinch` = `self: remove(stealthed)`.
- **Goal:** `win` is the standard `neutralize(wraith)`, or `lure` (a trigger cast from any region in
  range, the Wraith confirmed spent, then a strike by the other companion aimed at it, or at its
  region while it hides), or a flinch first then `lure`, or flames laid in a region, then the lure
  sprung from there.
- Both companions have 4 mana.

## Hypothesis

Measured with `htn_components combos fsm_wraith` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 18 of 49 assignments win: 9 pairs, each whichever companion holds which half:
  - `provoke` or `flashbang`, plus `zap`, `chainLightning`, `frostBolt` or `flameWall`: 8 pairs;
  - `taunt` plus `chainLightning`: 1 pair (`chainLightning` plays two roles here: reveal, then strike).
- 9 methods, 0 solo plans, no dead skills.
- The other 12 pairs lose, each for a nameable reason: two lures (nobody strikes), two strikes
  (nobody spends it), `taunt` with anything but the chain (it cannot be aimed at the unseen).

## Examples

### Example 1: Provoke, then jolt

**Given:** the player knows `provoke`, the mage knows `zap`.

**When:** `win`

**Then:** the player provokes the crypt; the Wraith lunges, spent and revealed, and stuns the player;
the mage's zap stops it (`dead`).

### Example 2: Lure into fire

**Given:** the player knows `flameWall`, the mage knows `flashbang`.

**When:** `win`

**Then:** one plan has the player set a region alight first; the mage flashbangs the crypt from
there; the blinded Wraith lunges, already spent, into the flames and burns (`dead`).

### Example 3: Shake, then taunt

**Given:** the player knows `taunt`, the mage knows `chainLightning`.

**When:** `win`

**Then:** the mage's chain flinches the Wraith out of hiding; the player taunts it and it lunges,
spent; the mage's second chain stops it (`dead`).

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the nine measured pairs have a plan. |
| P3 | The mist hides it again | No provoke+frostBolt plan lures it into the mist; a chain still reaches it there. |
| P4 | The lure is stunned | The lunge stuns whoever set it off, who casts nothing afterwards. |
