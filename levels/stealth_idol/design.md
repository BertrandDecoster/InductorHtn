# The Idol

## Purpose

A stealth level on the ability layer where **you can sneak in, but not out**. A golden idol sits in a
temple shrine. The way in is the nave, watched from the altar by a keeper - with a second keeper
dozing beside him. The way out is a one-way chute down to the crypt, where a skeleton watches the
exit. The idol glows: whoever carries it cannot hide. One companion must carry the idol out; each
picks one skill from a pool of six.

| Obstacle | Answers | Not answers |
|----------|---------|-------------|
| **The nave** (`watches(keeper, nave)` and `watches(dozer, nave)` while they stand at the altar) | sneak in (`vanish`; `shadowStep` dashes in, hidden), put the keeper to sleep (`sleepDart`), lure him off the altar (`taunt` drags him to the taunter) | a flash or any area effect at the altar: it blinds the keeper and **rouses the dozer**, alarmed - and nothing dazzles an alarmed guard (a taunt can still drag him off) |
| **The crypt** (`watches(skeleton, crypt)`), crossed carrying the idol | dazzle the skeleton (`flashbang`), shove it into the ossuary from the ledge (`gust`) | any stealth (the idol's glow strips and wards it); sleep (it is mindless); taunts (it is deaf to them) |

Why no single skill works:
- Every nave answer fails in the crypt: the thief is laden (`wards(laden, stealthed)`), the skeleton
  is `mindless` (no sleep) and `immune(skeleton, taunted)`.
- Every crypt answer fails in the nave: gust has no push line at the altar, and a flashbang at the
  altar wakes the dozer (a second flash is refused: `wards(alarmed, blinded)`).

Level-local pieces: the `idol` zone and the `laden` tag; the dozer's composite `dozing` (it bundles
`blinded`, so he cannot watch), its `reaction(dozing, hostile, rouse)` and the `alarmed` ward; the
positional watch rules; and the recipe `getTo/3` (walk; else hide, dash in hidden, or stop a watcher
watching with anyone's skill, and try again).

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
ledge .................................. (sees down into the crypt)
  |                                        :
entry (player, mage) ---- nave ---- shrine (idol) --> chute ---- crypt (skeleton) ---- exit
                           :                                       :
                         altar (keeper, dozer)                   ossuary (a pit)
```

- **Lines of sight:** the entry sees the nave and the altar; the nave sees the altar and the shrine;
  only the ledge sees into the crypt.
- **Push line:** from the ledge, whatever stands in the crypt goes into the ossuary (a chasm).
- **The chute runs one way:** shrine to crypt.
- **Keeper, dozer:** living; they watch the nave while they stand at the altar. The dozer starts
  `dozing`.
- **Skeleton:** mindless, deaf to taunts; watches the crypt while it stands there.
- **Victory:** `heist` - a companion enters the shrine (taking the idol), then reaches the exit.

## Hypothesis

Measured by `htn_components combos stealth_idol` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 6.
- **16 of 36** assignments win, by **8** methods; no solo plans; no dead skill.
  - a way into the nave (`vanish`, `shadowStep`, `sleepDart`, `taunt`) plus a way past the skeleton
    (`flashbang`, `gust`), whichever companion holds which: 4 x 2 x 2 = 16.
- flashbang + taunt wins two ways: taunt the keeper off the altar, or flash the altar (keeper blind,
  dozer roused) and taunt the roused dozer off it.
- The 20 losing assignments fail for nameable reasons: two ways in (the idol cannot be hidden from
  the skeleton), flashbang + gust (the flash rouses the dozer), one skill twice.
- Usage: flashbang, gust 8 each; each nave answer 4.

## Examples

### Example 1: Sneak in, shove the skeleton

**Given:** the player knows `vanish`, the mage knows `gust`.

**When:** `heist`

**Then:** the player vanishes and walks through the nave; the idol strips the stealth. The mage, on
the ledge, shoves the skeleton into the ossuary; the player drops down the chute and walks out.

### Example 2: A dart and a flash

**Given:** the player knows `sleepDart`, the mage knows `flashbang`.

**When:** `heist`

**Then:** a dart puts the keeper to sleep (the dozer never stirs); the mage's flash from the ledge
blinds the skeleton.

### Example 3: The flash that wakes the dozer

**Given:** the player knows `flashbang`, the mage knows `taunt`.

**When:** `heist`

**Then:** one plan: the player's flash at the altar blinds the keeper and rouses the dozer; the mage
taunts the roused dozer off the altar. Another: the mage simply taunts the keeper. Either way the
player later blinds the skeleton from the ledge.

### Example 4: Dash in hidden

**Given:** the player knows `shadowStep`, the mage knows `gust`.

**When:** `heist`

**Then:** the player dashes into the nave and is hidden on landing; the mage shoves the skeleton away.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | The measured assignments win | Exactly the 16 measured assignments have a plan; none solo; no dead skill. |
| P3 | The idol cannot be hidden | vanish + sleepDart and shadowStep + vanish have no plan: sneaking gets the thief in, never out. |
| P4 | A flash at the altar rouses the dozer | flashbang + gust has no plan: the roused dozer still watches the nave. |
| P5 | The skeleton is mindless and deaf | sleepDart + taunt has no plan. |
