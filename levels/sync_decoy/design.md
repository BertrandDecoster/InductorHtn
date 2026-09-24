# Sync: The Decoy

## Purpose

A synchronisation level: **one companion baits an enemy's big blow while the other pulls them clear
of it**. A golem holds the arch to the switch room. Up on a balcony, a stone gargoyle (heavy,
living) watches the hall in front of the arch. Two companions, the player and the mage, pick one
skill each from a pool of six, with two mana each (one costly cast). Someone gets past the golem,
someone gets past the gargoyle, then one of them steps on the switch plate and walks into the vault.

The decoy is a heavy attack (`ab_casting`): taunted, the golem walks after its taunter and winds up
a `groundSlam` where it arrives. The slam is physical, so nothing stops it. Taunt it from the
balcony and the slam stuns the gargoyle, which then cannot watch, and the golem has left the arch:
one taunt does both jobs. The catch is that the taunter stands in the blast, and the level declares
both companions `mustSurvive` (whoever baits the golem is pulled clear). The taunter has no second
skill; the friend's one cast in the window, from the nook next door, must hook them out. The Lost
Vikings / Trine split: one draws the blow, the other saves them from it.

| Obstacle | What stops you | Methods (pool skills) |
|----------|----------------|-----------------------|
| **The golem** | a `blocker` in the arch: nobody walks into its area | the decoy: `taunt` (it follows you out, and the slam does the rest); `hook` it into the hall (once the gargoyle is out); knock it into the well from the nook: `fireball`, `vortex` on the well; or slip past it: `lightningFlash` from the hall into the arch (a dash is not a walk) |
| **The gargoyle** | `watches(gargoyle, hall)`: nobody walks in seen | blind it: `blindingFlash` on the balcony; bait the golem's slam onto it (the decoy); or slip past it: `lightningFlash` from the camp into the hall |
| **The slam** | the taunter is in the struck area and must survive | the friend's cast in the window: `hook` the taunter into the nook. Nothing else saves them: a flash is disjoint for its caster only, a knockback never leaves the area, and dropping the golem during the window cancels the slam the gargoyle needed |
| **The vault** | the portcullis (a door) | step on the switch plate (it latches open) and walk in |

Why no single skill works:
- A lure does not blind the gargoyle, and a blinder does not move the golem.
- The taunt does both jobs but leaves the taunter under the slam; a companion cannot be taunted, and
  a second taunt rescues nobody.
- `lightningFlash` gets its caster into the hall or past the golem, but two mana buys one flash:
  two flashers still leave the golem in the arch.

`lightningFlash` serves two roles (past the gazer, or past the golem), and `hook` serves two (lure the
golem, or rescue the decoy).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
camp ------- nook ------- balcony (gargoyle: heavy, living)
  |            \  sight      /  sight
hall (watched) --- arch (golem; well) --- switch [lever plate] ==portcullis== vault
```

- **Areas (7):** camp, nook, balcony, hall, arch, switch, vault. Walkable links: camp-nook,
  nook-balcony, camp-hall, hall-arch, arch-switch; a doorway (the portcullis) switch-vault.
- **Lines of sight:** nook and balcony see the arch; the nook sees the balcony.
- **Features:** a well (chasm) in the arch; the lever plate in the switch room (`open(portcullis)`,
  latching).
- **Golem:** living, `blocker`, `behavior(golem, taunted, groundSlam, here)`.
- **Gargoyle:** living, heavy, `watches(gargoyle, hall)`.
- **Companions:** player and mage, two mana each, both `mustSurvive`.
- **Goal:** `win` = `veil` (the gargoyle is out, or blinded, or left for a dash), `lure` (the golem
  is hooked out, baited by a taunt with the friend standing by in the nook, knocked into the well,
  or left for a dash), then `slip`: someone reaches the switch (`passage` `reach`: walk, or one
  leap forward), steps on the lever and walks into the vault.

## Hypothesis

Measured with `htn_components combos sync_decoy` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- 14 of the 36 assignments win, whichever companion holds which half (7 pairs):
  - `blindingFlash` with each golem answer: `hook`, `fireball`, `vortex`, `lightningFlash`;
  - `lightningFlash` (into the hall) with each knock into the well: `fireball`, `vortex`;
  - the decoy: `taunt` with `hook`.
- 7 methods (distinct sets of skills cast), 0 solo plans, no dead skill. Usage: blindingFlash 8,
  lightningFlash 6, hook, fireball, vortex 4 each, taunt 2.
- Every losing pair has a reason: two lures (the hall is still seen), `lightningFlash` with `hook`
  (the flasher is in the hall alone, the hooker cannot follow), a taunt with anything but a hook
  (nobody pulls the decoy out).
- One replan takes 1 to 5 s.

## Examples

### Example 1: Bait the slam, hook the decoy out

**Given:** the player knows `taunt`, the mage knows `hook`.

**When:** `win`

**Then:** the mage takes post in the nook. The player climbs to the balcony and taunts the golem,
which walks out of the arch, through the hall and the camp, up to the balcony, and winds up a ground
slam there. In the window, the mage hooks the player down into the nook. The slam stuns the
gargoyle. The player crosses the unseen hall and the empty arch, steps on the lever, and the
portcullis opens.

### Example 2: Flash past the gargoyle, vortex the golem

**Given:** the player knows `lightningFlash`, the mage knows `vortex`.

**When:** `win`

**Then:** from the nook, the mage's vortex on the well drops the golem in. The player
lightning-flashes from the camp into the watched hall (a dash, not a walk), walks through the arch,
steps on the lever and walks into the vault.

### Example 3: Blind the gargoyle, flash past the golem

**Given:** the player knows `blindingFlash`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player blinds the gargoyle from the balcony. The mage walks into the hall and
lightning-flashes into the arch, past the golem, which never moves. The mage steps on the lever and
walks into the vault.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | The measured pairs win | Exactly the 7 pairs above have a plan. |
| P3 | Either seat | A pair wins whichever companion holds which half. |
| P4 | The rescue is the one cast in the window | In every taunt plan the slam is wound up on the balcony, the only cast between the wind-up and the blow is the mage's hook on the player, and the blow stuns the gargoyle. |
| P5 | No one else saves the decoy | `taunt` with `fireball`, `vortex`, `blindingFlash` or `lightningFlash`: no plan. |
| P6 | One lightning flash each | `lightningFlash` + `lightningFlash` and `lightningFlash` + `hook`: no plan. |
| P7 | Companions cannot be taunted | `receptive(mage, taunted)` fails. |
