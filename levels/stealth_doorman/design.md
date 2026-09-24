# The Doorman

## Purpose

A stealth level on the ability layer: **get past a guard who watches, and a guard who blocks**.
One companion, the thief, must reach the vault; the other helps. Each picks one skill from a pool of
eight. The two guards want different kinds of answer:

| Obstacle | What it does | Answers |
|----------|--------------|---------|
| **The sentry** on the wall | `watches(sentry, court)`: nobody walks into the courtyard under his eyes | sneak past (`vanish`, `smokeBomb`'s cloud), blind him (`flashbang`, `smokeBomb`), put him to sleep (`sleepDart`, `lullaby`) |
| **The doorman** in the vault door | `blocker(doorman)`: nobody gets into his region, seen or not | lure him out (`taunt` drags him to the taunter), hook him (`magnetize`), shove him down the cellar steps from the garden (`gust`) |

Why no single skill works:
- The sentry is braced on the battlement (`immune(sentry, forcedMove)`): a lure, a hook or a
  shove does nothing to him.
- Blinding or sleeping the doorman does nothing: a blind man still fills a doorway.
- `vanish` hides only its caster: it makes a thief, never a helper.

The level-local pieces are the stealth recipe `getTo/3` (walk; else hide, blind a watcher, or budge a
blocker, and try again) and `blind/1`. The physics (`spotted/2`, `forbids(blinded, watch)`,
`heldAgainst/2`) is the shared `ab_effects`.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
wall (sentry: watches the court)
 :
yard (player, mage) ---- court ---- door (doorman) ---- vault
 |                                   :
garden ..............................:   (sees the doorway)
```

- **Lines of sight:** the yard, the court and the garden see the wall; the court and the garden see
  the doorway. The yard does not see the doorway, so a helper who stays out of the courtyard works
  from the garden.
- **Push line:** from the garden, whatever stands in the doorway goes down the cellar steps
  (`beyond(garden, door, cellar)`). It is the only one.
- **Sentry:** living, braced (immune to forced movement), watches the courtyard.
- **Doorman:** living, a blocker.
- **Victory:** `win` - either companion reaches the vault.

## Hypothesis

Measured by `htn_components combos stealth_doorman` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 8.
- **30 of 64** assignments win, by **15** methods (sets of skills cast); no solo plans; no dead skill.
  - any sentry answer (`vanish`, `smokeBomb`, `flashbang`, `sleepDart`, `lullaby`) plus any doorman
    answer (`taunt`, `magnetize`, `gust`), whichever companion holds which: 5 x 3 x 2 = 30.
- The 34 losing assignments each fail for a nameable reason: two sentry answers (the door stays
  shut), two doorman answers (the courtyard stays watched), or one skill twice.
- Methods differ in kind: sneak vs. blind vs. sleep for the sentry; lure vs. hook vs. shove for the
  doorman. Skill usage: taunt, magnetize, gust 10 each; the five sentry answers 6 each.

## Examples

### Example 1: Sneak and shove

**Given:** the player knows `vanish`, the mage knows `gust`.

**When:** `win`

**Then:** the player vanishes; the mage walks to the garden and shoves the doorman down the cellar
steps; the player crosses the courtyard unseen and walks into the vault.

### Example 2: Blind and lure

**Given:** the player knows `flashbang`, the mage knows `taunt`.

**When:** `win`

**Then:** the player's flash blinds the sentry; the mage crosses the courtyard, taunts the doorman out
of the doorway and walks into the vault.

### Example 3: Sleep and hook

**Given:** the player knows `sleepDart`, the mage knows `magnetize`.

**When:** `win`

**Then:** a dart puts the sentry to sleep; a hook drags the doorman out of the doorway.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | The measured assignments win | Exactly the 30 measured assignments have a plan; no plan is carried by one companion; no skill is dead. |
| P3 | Vanish makes a thief | With vanish and taunt, the vanisher is always the one who walks into the vault. |
| P4 | A blind doorman still blocks | Two sentry answers (flashbang + sleepDart, vanish + lullaby) never clear the door. |
| P5 | Nothing moves the sentry | Two doorman answers (taunt + gust, magnetize + taunt) leave the courtyard watched. |
