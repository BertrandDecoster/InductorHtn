# The Doorman

## Purpose

A stealth level on the ability layer: **get past a guard who watches, and a guard who blocks**.
One companion, the thief, must reach the vault; the other helps. Each picks one skill from a pool of
eight catalogue skills. The two guards want different kinds of answer:

| Obstacle | What it does | Answers |
|----------|--------------|---------|
| **The sentry** on the gatehouse tower | `watches(sentry, court)` while it stands on the tower. A clockwork machine; the tower stands across the moat (a gap from the yard, a gap to the courtyard) with a murder hole in its floor. | slip into the courtyard (`blink` teleports, `lightningFlash` dashes: both pass a watched area), or from the yard: `shieldBash` stuns it (or knocks it down the hole or into the moat), `hook` drags it across the moat (it falls), `fireball` blows it into the moat or the hole, `vortex` on the murder hole sucks it in, `lightningFlash` shorts it (a jolted machine is stunned) |
| **The doorman** in the hall | `blocker(doorman)`: nobody walks into the hall. From it, `watches(doorman, vault)`. Portly (`heavy`) and `immune(doorman, blinded)` (the lantern), so nothing stuns him either. | `taunt` him out (he walks after the taunter, to the yard), or `turnToMist` him (not heavy for a moment) and then knock him down the cellar steps (`fireball`, `shieldBash`, `vortex` on the steps) or `hook` him into the courtyard |
| **The house wards** | `onEnter(hall, wards)`: whoever arrives in the hall loses `disjoint` and is `silenced`. | none needed: they only stop a thief from blinking on from the hall into the vault |

Why no single skill works:
- The sentry cannot walk off its tower (gaps only): a taunt on it breaks. Only a taunt, or a skill
  after `turnToMist`, moves the doorman.
- A blink or a dash into the hall is hushed there, and the vault is under the doorman's eyes.
- The doorman answers are `taunt` and `turnToMist`, neither of which touches the sentry.

Level-local pieces: the `wards` zone (`remove(disjoint)`, `grant(silenced)` - built from catalogue
atoms), the positional watch rules, and the recipes `getTo/3` (walk; else leap by teleport or dash,
answer a watcher, or answer a blocker, and try again), `answer/1` (one cast on the guard, or on a pit
in its area with `knocks/6`; for a heavy guard, `turnToMist` first) and `cleared/1` (the physics
tries every aim: confirm the guard no longer watches or holds the hall).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
yard (player, mage) ::moat:: tower (sentry; murder hole) ::moat:: court
  |__________________________________________________________|
                                                             |
                           vault ---- hall (doorman; the wards; the cellar steps)
```

- **Areas (5):** yard, tower, court, hall, vault.
- **Links:** `connected(yard, court)`, `gap(yard, tower)`, `gap(tower, court)` (the moat),
  `connected(court, hall)`, `connected(hall, vault)`.
- **Features:** `feature(tower, murderHole, chasm)`, `feature(hall, cellarSteps, chasm)`.
- **Lines of sight:** the yard sees the tower, the courtyard and the hall (through the gate); the
  courtyard sees the tower and the hall. Nothing sees into the vault.
- **Sentry:** a machine; watches the courtyard while on the tower.
- **Doorman:** living, heavy, a blocker, immune to `blinded`; watches the vault while in the hall.
- **Mana:** 4 each (fireball and lightningFlash cost 2).
- **Victory:** `win` - either companion reaches the vault.

## Hypothesis

Measured by `htn_components combos stealth_doorman` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- **20 of 64** assignments win, by **10** methods; no solo plans; no dead skill.
  - a sentry answer (`blink`, `lightningFlash`, `shieldBash`, `hook`, `fireball`, `vortex`) and a
    `taunt` for the doorman, either companion holding either: 6 x 2 = 12;
  - `turnToMist` and a skill that serves both guards (`shieldBash`, `hook`, `fireball`, `vortex`):
    4 x 2 = 8.
- The 44 losing assignments fail for nameable reasons: two sentry answers (the doorman stays), taunt
  with turnToMist (the sentry cannot be taunted), blink or a dash with turnToMist (nothing moves the
  misted doorman), one skill twice.
- Methods differ in kind: slip vs. stun vs. short-circuit vs. a drop (moat, murder hole) for the
  sentry; lure vs. mist-then-knock vs. mist-then-hook for the doorman. Usage: taunt 12, turnToMist 8,
  shieldBash, hook, fireball, vortex 4, blink, lightningFlash 2.
- One skill, two roles: after `turnToMist`, one hook, fireball, bash or vortex clears both guards;
  `lightningFlash` is a way over the moat or a jolt.
- Every assignment plans in under 15 s.

## Examples

### Example 1: Blink and taunt

**Given:** the player knows `blink`, the mage knows `taunt`.

**When:** `win`

**Then:** the player blinks over the moat into the courtyard; the mage, from the yard, taunts the
doorman out of the hall (he walks to the yard); the player walks through the hall (hushed) into the
vault.

### Example 2: Into the moat

**Given:** the player knows `hook`, the mage knows `taunt`.

**When:** `win`

**Then:** the player hooks the sentry from the yard; dragged across the moat, it falls in. The mage
taunts the doorman out, and the player walks in.

### Example 3: Mist and hook

**Given:** the player knows `turnToMist`, the mage knows `hook`.

**When:** `win`

**Then:** the mage hooks the sentry into the moat; the player turns the doorman to mist; the mage,
in the courtyard, hooks him out of the hall (he now blocks the courtyard, behind the mage) and walks
into the vault.

### Example 4: Two vortices

**Given:** the player knows `vortex`, the mage knows `turnToMist`.

**When:** `win`

**Then:** the player's vortex on the murder hole takes the sentry; the mage turns the doorman to
mist; the player's vortex on the cellar steps takes him.

### Example 5: A jolt

**Given:** the player knows `lightningFlash`, the mage knows `taunt`.

**When:** `win`

**Then:** the player's lightning strikes the tower and lands on it: the clockwork sentry is stunned.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured assignments win | Exactly the 20 measured assignments have a plan, by 10 methods; none solo; no dead skill. |
| P3 | The hall is hushed | blink + lightningFlash has no plan; in every blink + taunt plan the thief is silenced in the hall. |
| P4 | The heavy doorman | hook + fireball and shieldBash + vortex have no plan. |
| P5 | The sentry cannot be taunted | taunt + turnToMist has no plan. |
| P6 | One skill, two roles | With turnToMist + fireball, every plan fireballs both the sentry and the doorman. |
