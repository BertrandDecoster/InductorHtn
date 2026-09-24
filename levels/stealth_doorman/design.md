# The Doorman

## Purpose

A stealth level on the ability layer: **get past a guard who watches, and a guard who blocks**.
One companion, the thief, must reach the vault; the other helps. Each picks one skill from a pool of
eight catalogue skills. The two guards want different kinds of answer:

| Obstacle | What it does | Answers |
|----------|--------------|---------|
| **The sentry** on the wall | `watches(sentry, court)` while he stands on the wall: nobody walks into the courtyard under his eyes. He is braced (`tag(sentry, heavy)`). | slip in (`blink` teleports into the courtyard: a teleport passes a watched region), blind him (`blindingFlash` from the yard or the wall), stun him (`shieldBash` from the yard), or take his bracing for a moment (`turnToMist`) and then drag him down (`taunt`, `hook`) or draw him into the yard (`vortex`) |
| **The doorman** in the vault door | `blocker(doorman)`: nobody walks into the doorway. From it, `watches(doorman, vault)`: whoever slips into the doorway is still seen stepping into the vault. `immune(doorman, blinded)` (the lantern over the door). | move him: `taunt` or `hook` drag him to the caster, `fireball` from the garden or the courtyard blows him down the cellar steps, `vortex` on the cellar draws him down and roots him |

Why no single skill works:
- The sentry is heavy: a taunt, a pull-in or a push does nothing to him, and a hook drags the hooker
  up onto the wall instead. Only `turnToMist` lets a mover take him.
- Nothing blinds or stuns the doorman (the stun bundles `blinded`, so it is refused whole), and nobody
  sees into the vault: a blink into the doorway leaves the thief under his eyes.
- `blink` twice: into the courtyard, into the doorway, and the vault is still watched.

Traps: a vortex draws in everyone next door, companions included, and roots them; a doorman drawn or
taunted into the courtyard blocks the courtyard.

Level-local pieces are recipes only: `getTo/3` (walk; else leap by teleport or dash, stop a watcher
watching, or budge a blocker, and try again), `unwatch/1` (blind, move, or mist then move) and
`budge/1` (a pull, or any `placement/6`). The positional watch rules are ordinary facts. The physics
(`spotted/2`, `forbids(blinded, watch)`, `heldAgainst/2`) is the shared `ab_effects`.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
         wall (sentry: watches the court)
          |
garden - yard (player, mage) ---- court ---- door (doorman: watches the vault) ---- vault
                                              |
                                            cellar (the steps down)
```

- **Lines of sight:** the yard sees the courtyard and the wall; the courtyard sees the wall, the
  doorway and the cellar; the garden sees the doorway and the cellar. Nothing sees into the vault.
- **Push lines:** from the garden or the courtyard, whatever stands in the doorway goes down the
  cellar steps (`beyond(garden, door, cellar)`, `beyond(court, door, cellar)`).
- **Sentry:** living, heavy, watches the courtyard while on the wall. The wall is reached from the yard.
- **Doorman:** living, a blocker, immune to `blinded`, watches the vault while in the doorway.
- **Mana:** 4 each (fireball costs 2).
- **Victory:** `win` - either companion reaches the vault.

## Hypothesis

Measured by `htn_components combos stealth_doorman` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- **30 of 64** assignments win, by **15** methods; no solo plans; no dead skill.
  - a sentry answer (`blink`, `blindingFlash`, `shieldBash`) and a doorman answer (`taunt`, `hook`,
    `vortex`, `fireball`), either companion holding either: 3 x 4 x 2 = 24;
  - `turnToMist` and a mover that drags or draws (`taunt`, `hook`, `vortex`), which then serves both
    guards: 3 x 2 = 6. `fireball` has no line off the wall, so mist + fireball loses.
- The 34 losing assignments fail for nameable reasons: two sentry answers (the doorway stays held),
  two movers without mist (the sentry stays braced), one skill twice.
- Methods differ in kind: slip vs. blind vs. stun vs. mist-and-drag for the sentry; drag vs. blow down
  the steps vs. draw into the cellar for the doorman. Usage: blink, blindingFlash, shieldBash, taunt,
  hook, vortex 8 each; turnToMist, fireball 6.
- One skill, two roles: after `turnToMist`, one `taunt`, `hook` or `vortex` clears both guards.
- Every plan takes under 8 s.

## Examples

### Example 1: Blink and taunt

**Given:** the player knows `blink`, the mage knows `taunt`.

**When:** `win`

**Then:** the player blinks into the courtyard (and on into the doorway); the mage walks to the
garden and taunts the doorman out to it; the player walks into the vault.

### Example 2: Bash and fireball

**Given:** the player knows `shieldBash`, the mage knows `fireball`.

**When:** `win`

**Then:** the player stuns the sentry from the yard; the mage's fireball, from the garden or the
courtyard, blows the doorman down the cellar steps; the player walks through the flames into the vault.

### Example 3: Mist and taunt

**Given:** the player knows `turnToMist`, the mage knows `taunt`.

**When:** `win`

**Then:** the sentry turns to mist; before the moment is over, the mage taunts him down into the yard;
the mage then taunts the doorman into the garden, and the player walks into the vault.

### Example 4: Flash and vortex

**Given:** the player knows `blindingFlash`, the mage knows `vortex`.

**When:** `win`

**Then:** the player blinds the sentry; the mage's vortex on the cellar draws the doorman down the
steps and roots him there.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured assignments win | Exactly the 30 measured assignments have a plan; none solo; no dead skill. |
| P3 | The doorman watches the vault | blink + blindingFlash has no plan: a blink into the doorway is still seen, and nothing blinds him. |
| P4 | The braced sentry | taunt + vortex and turnToMist + fireball have no plan. |
| P5 | One skill, two roles | With turnToMist + hook, every plan hooks both the sentry and the doorman. |
