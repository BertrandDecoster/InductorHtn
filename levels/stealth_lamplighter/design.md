# The Lamplighter

## Purpose

A stealth level on the ability layer where **sneaking has a limit**. Everyone must get out through
the town gate. The gate's lever lies in a guardroom under a warden's eyes; the road runs under the
lamps, which strip stealth, and through a hall that a lamplighter watches from his post. Two
companions pick one skill each from a pool of seven.

| Obstacle | Who has to solve it | Answers |
|----------|---------------------|---------|
| **The lever** (`onEnter(guardroom, lever)` opens the gate for good) | one companion, or the crate | sneak in (`vanish`, `smokeBomb`'s cloud), blind the warden (`flashbang`, `smokeBomb`), put him to sleep (`sleepDart`), or shove the crate onto the lever from the start (`gust`) |
| **The hall** (`watches(lamplighter, hall)` while he is on his post and nothing stands in the hall to hide behind) | everyone, after the lamps | lure him off his post (`taunt` drags him to the taunter; a `pebble` at his feet sends him to look down the well), or shove the crate into the hall from under the lamps (`gust`) and walk behind it |

Why no single skill works:
- The lamps (`lamplight`: remove stealthed, grant `lit`, and `wards(lit, stealthed)`) undo any
  stealth before the hall, and no one can hide again while lit. So sneaking gets one companion onto
  the lever, never anyone across the hall.
- The lamplighter's lantern: `immune(lamplighter, blinded)`, so no flash, cloud or sleep dart helps
  with him.
- The warden is heavy and has no behaviour for a pebble: no lure moves him.
- **gust has two roles, and there is one crate.** It weighs down the lever, or it is cover in the
  hall - not both. Two gusts leave one obstacle.

Level-local pieces: the lamps and the `lit` tag, the crate's `cover` trait (a watcher's positional
rule reads it), the `pebble` skill (a tag, `curious`, and the lamplighter's `behavior` that answers
it with a `teleport(well)`), and the recipe `getTo/3` (walk; else hide, stop a watcher watching with
anyone's skill, or put cover in a watched region, and try again).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
guardroom (warden; the lever)      yard (a crate)
     |                               :
   start (player, mage) -------- lamps (lit) ---- hall ---- gate (shut) ---- exit
                                                   :
                                                  post (lamplighter)         well
```

- **Lines of sight:** the start sees the guardroom, the yard and the post; the lamps see the yard,
  the hall and the post.
- **Push lines:** from the start, the crate in the yard goes into the guardroom (onto the lever);
  from under the lamps, into the hall (cover).
- **Warden:** living, heavy, watches the guardroom while he stands in it.
- **Lamplighter:** living, cannot be blinded, watches the hall from the post unless the hall holds
  cover. A taunt drags him to the taunter; a pebble sends him to the well.
- **Victory:** `escape` - the gate open, then both companions at the exit.

## Hypothesis

Measured by `htn_components combos stealth_lamplighter` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7 (gust twice included: one crate).
- **28 of 49** assignments win, by **14** methods; no solo plans; no dead skill.
  - a lever answer (`vanish`, `smokeBomb`, `flashbang`, `sleepDart`, `gust`) plus a different hall
    answer (`gust`, `taunt`, `pebble`), either companion holding either: 14 pairs x 2 seats.
- `gust` is in 12 winning assignments, in both roles. Usage otherwise: taunt, pebble 10; the four
  lever-only skills 6 each.
- The 21 losing assignments fail for nameable reasons: two lever answers (the lamps and the lantern
  keep the hall shut), two hall answers other than gust (nobody reaches the lever), one skill twice.

## Examples

### Example 1: The crate on the lever, and a taunt

**Given:** the player knows `gust`, the mage knows `taunt`.

**When:** `escape`

**Then:** the player shoves the crate from the yard into the guardroom and the gate opens; the mage
taunts the lamplighter off his post to the start; both walk under the lamps, through the hall and out.

### Example 2: Sneak onto the lever, and a pebble

**Given:** the player knows `vanish`, the mage knows `pebble`.

**When:** `escape`

**Then:** the player vanishes and walks onto the lever past the warden; the mage's pebble sends the
lamplighter to look down the well; the lamps strip the player's stealth, but the hall is unwatched.

### Example 3: Blind the warden, and take cover

**Given:** the player knows `flashbang`, the mage knows `gust`.

**When:** `escape`

**Then:** the player's flash blinds the warden and the player pulls the lever; the mage, under the
lamps, shoves the crate into the hall, and both walk through behind it.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan - gust twice included. |
| P2 | The measured assignments win | Exactly the 28 measured assignments have a plan; none solo; no dead skill. |
| P3 | The lamps undo stealth | vanish + smokeBomb has no plan; with vanish + taunt, every plan strips the thief's stealth under the lamps. |
| P4 | The lantern and the heavy warden | flashbang + sleepDart (nothing dazzles the lamplighter) and taunt + pebble (nothing lures the warden) have no plan. |
| P5 | gust has two roles | With gust + pebble, gust puts the crate on the lever; with sleepDart + gust, the crate is cover in the hall. |
