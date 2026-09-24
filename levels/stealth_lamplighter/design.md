# The Lamplighter

## Purpose

A stealth level on the ability layer where **everyone has to get out, past two watchers who want
different answers**. The gate's winch stands in the gatehouse yard, which the warden watches from his
lodge; the road runs down the lamp-lit street, which the lamplighter watches from his post while the
lamps burn. At the post hangs the lamp rope: weigh it down and every lamp goes out. Two companions
pick one skill each from a pool of seven catalogue skills.

| Obstacle | Who has to solve it | Answers |
|----------|---------------------|---------|
| **The winch** (`plate(winch)` in the yard: pressed, it opens the gate for good; `watches(warden, yard)` from the lodge) | one companion stands on it | blind the warden (`blindingFlash` in his lodge), stun him (`shieldBash`), or soak him (`tidalWave` in his lodge) and freeze him (`blizzard`: wet and chilled is stunned) |
| **The street** (`watches(lamplighter, street)` while he is on his post and the lamps burn) | everyone | lure him off his post (`taunt`: he walks after you), knock him onto his own lamp rope (`fireball`, or `vortex` on the rope: the street goes dark, `spill(shadows, street)`), or frost the lamps over (`blizzard` on the street) |

Why no single skill works:
- The warden is heavy and rooted in his chair: a taunt breaks, nothing knocks him; dry, a blizzard
  only chills him.
- The lamplighter's lantern: `immune(lamplighter, blinded)`, so no flash and no stun (it bundles
  `blinded`) helps with him; the post is reached only through the lit street, so no bash reaches
  him.
- The skills that answer the street do nothing to the warden, and the other way round - except
  blizzard, which freezes the warden only once he is wet.

Level-local pieces: the `lamplight` zone (no effect of its own) and its reactions
`zoneReaction(lamplight, shadows, shadows)` and `zoneReaction(lamplight, iceSheet, iceSheet)`; the
winch plate (`open(gate)`) and the lamp-rope plate (`spill(shadows, street)`); the positional watch
rules; and the recipes `getTo/3` (walk; else answer a watcher, and try again), `answer/1` (one cast on
the watcher or on what it watches, or a vortex on a plate in its area via `knocks/6`; or soak it
first), `cleared/1` and `openGate/0`.

The old level's "one crate, two uses" does not survive the new movement model: a knockback never
changes the area, so one crate cannot be both a weight on a lever and cover in another room. Its
place is taken by the lamp rope (the lamplighter knocked onto his own plate) and blizzard's two roles.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
lodge (warden) ---- square (player, mage) ---- yard (the winch)
                       |
                     street (lamps) ==gate== exit
                       |
                     post (lamplighter; the lamp rope)
```

- **Areas (6):** square, lodge, yard, street, post, exit.
- **Links:** walkable square-lodge, square-yard, square-street, street-post;
  `doorway(street, exit, gate)` (shut until the winch turns).
- **Features:** `feature(yard, winch, turnWinch)` and `feature(post, lampRope, douse)`, both plates.
- **Lines of sight:** the square sees the lodge, the yard, the street and the post; the lodge sees
  the yard; the street sees the post.
- **Warden:** living, heavy, rooted; watches the yard while in his lodge.
- **Lamplighter:** living, cannot be blinded; watches the street from the post while the lamps burn.
- **Mana:** 4 each (tidalWave, blizzard and fireball cost 2).
- **Victory:** `escape` - the gate open, then both companions at the exit.

## Hypothesis

Measured by `htn_components combos stealth_lamplighter` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- **18 of 49** assignments win, by **9** methods; no solo plans; no dead skill.
  - a warden answer (`blindingFlash`, `shieldBash`) and a street answer (`taunt`, `fireball`,
    `vortex`, `blizzard`): 2 x 4 x 2 = 16;
  - `tidalWave` and `blizzard`: soak and freeze the warden, then frost the lamps: 2.
- The 31 losing assignments fail for nameable reasons: two warden answers or two street answers
  (one obstacle left), tidalWave without blizzard (a wet warden still sees), one skill twice.
- Usage: blindingFlash, shieldBash 8; blizzard 6; taunt, fireball, vortex 4; tidalWave 2.
- Methods differ in kind: blind vs. stun vs. soak-and-freeze for the warden; lure vs. a knock onto a
  plate vs. terrain (frosted lamps) for the street.
- One skill, two roles: `blizzard` frosts the lamps and freezes a soaked warden.
- Every assignment plans in under 6 s.

## Examples

### Example 1: A bash and a taunt

**Given:** the player knows `shieldBash`, the mage knows `taunt`.

**When:** `escape`

**Then:** the player stuns the warden from the square, walks into the yard and stands on the winch:
the gate opens. The mage taunts the lamplighter off his post (he walks to the square and follows the
mage); both walk down the street and out.

### Example 2: Onto his own rope

**Given:** the player knows `blindingFlash`, the mage knows `fireball`.

**When:** `escape`

**Then:** the player blinds the warden in his lodge and turns the winch; the mage's fireball knocks
the lamplighter onto his lamp rope: the street goes dark, and both walk through it, stealthed.

### Example 3: Soak and freeze

**Given:** the player knows `tidalWave`, the mage knows `blizzard`.

**When:** `escape`

**Then:** the player's wave, in the lodge, soaks the warden; the mage's blizzard freezes him. The
player turns the winch; the mage's second blizzard frosts the lamps over.

### Example 4: The vortex on the rope

**Given:** the player knows `vortex`, the mage knows `blindingFlash`.

**When:** `escape`

**Then:** the mage blinds the warden, the player turns the winch, and the player's vortex on the lamp
rope pulls the lamplighter onto it.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | The measured assignments win | Exactly the 18 measured assignments have a plan, by 9 methods; none solo; no dead skill. |
| P3 | The lantern | blindingFlash + shieldBash has no plan. |
| P4 | The rooted warden | taunt + fireball and vortex + blizzard have no plan. |
| P5 | Blizzard, two roles | With tidalWave + blizzard, every plan freezes the warden and frosts the street. |
