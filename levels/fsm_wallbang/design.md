# Wall-Bang

## Purpose

An enemy-state-machine level in the Monster Hunter wall-bang style, built on a **telegraphed,
physical heavy attack** the team provokes on purpose. The Ram is a boss: heavy (nothing moves it)
and immune to stuns. Taunted or blinded, it lowers its horns and **charges down its lane to the
brink**: a heavy blow. The team gets one cast; then the Ram lands on the brink, goring whoever
stands there (stunned, and knocked wherever the charge throws them), and crashes into the stone
pillar:

| State or trigger | Behaviour | Result |
|------------------|-----------|--------|
| `taunted`, `blinded` | `ramCharge` (heavy, physical, aimed `there(brink)`) | wind-up; one team cast; then it dashes to the brink, gores everyone there (`stunned` + a knockback) and crashes: `staggered`, `heavy` removed |
| `staggered` | the window | a knock or a hook drops it into the ravine; a vortex draws it into the rift |

The charge is physical: nothing interrupts it. The team splits at the start: the player holds the
brink, in front of the pillar; the mage waits in the pen. So the charge is a threat as well as the
key: whoever is still on the brink when it lands is stunned and finishes nothing.

| Method | The lure | The finisher (the other companion) |
|--------|----------|------------------------------------|
| **Flash and ...** | `blindingFlash` in the arena: it charges blind and leaves its caster behind | `fireball` (anywhere that sees the brink), `tidalWave` (walking onto the brink after the charge), `vortex` into the rift, `hook` across the ravine from the ledge, `shieldBash` from next door |
| **Taunt and ...** | `taunt` in the arena: it charges the brink all the same | the same five |
| **Hold the brink** | the mage lures (either skill) | the player, still on the brink, survives with one cast in the window: `shieldBash` at the Ram (the shield takes the gore, then a second bash knocks it in), or `hook` at the heavy Ram (it drags its caster into the arena, out of the way; then round by the gallery to the ledge, and a hook across the ravine) |

Why no single skill works: a lure alone leaves a staggered Ram standing (the lure knocks nothing);
a finisher alone never gets the Ram off its feet.

Traps: a knock, a hook or a vortex before the crash does nothing (heavy); a hook's or a bash's
interrupt in the window does not stop a physical charge; the brink holder with a fireball, a wave
or a vortex is gored before it can finish (a vortex on the rift in the window draws nobody away,
a fireball on itself throws it into the ravine); a hook from the pen only drags the staggered Ram
onto the pen.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
arena (Ram) ---- brink (pillar; the rift) ---- pen
                   :                            |
                   : (gap: the ravine)        gallery
                   :                            |
                  ledge ------------------------+
```

- **Areas:** arena, brink, pen, gallery, ledge. Walkable: arena-brink, brink-pen, pen-gallery,
  gallery-ledge. The brink and the ledge face each other across the ravine (`gap(brink, ledge)`).
- **Feature:** `feature(brink, rift, chasm)` - the brink's crumbling lip.
- **Line of sight:** arena-brink both ways; pen-brink both ways; ledge and gallery see the brink;
  pen-gallery, gallery-ledge. Nothing outside the brink sees into the arena.
- **Ram:** boss, living, heavy. `behavior(ram, taunted|blinded, ramCharge, there(brink))`;
  `heavy(ramCharge)`, physical; effects: `target: dash`, `self: grant(staggered)`,
  `self: remove(heavy)`, `target: grant(stunned)`, `target: push`.
- **Goal:** `win` provokes the charge (any cast that lands a trigger tag), confirms the crash
  (`staggered`), then runs the standard `neutralize(ram)` in that state (`intoThePit`). A companion
  may be lost on the way (sacrifice is allowed).
- The player starts on the brink, the mage in the pen, both with 4 mana. Pool: `blindingFlash`,
  `taunt`, `hook`, `vortex`, `fireball`, `tidalWave`, `shieldBash`.

## Hypothesis

Measured with `htn_components combos fsm_wallbang` (and pinned by `test.py`):

- No single skill wins, even when both companions hold it: 0 of 7.
- 14 of 49 assignments win:
  - the player lures (`blindingFlash` or `taunt`), the mage finishes with any of `fireball`,
    `tidalWave`, `vortex`, `hook`, `shieldBash` (10);
  - the mage lures, and the player finishes only with a skill that survives the charge where it
    stands: `shieldBash` or `hook` (4).
- 10 methods, 0 solo plans, no dead skills.
- Skills with two roles: `shieldBash` shields its caster against the gore and knocks the staggered
  Ram into the rift; `hook` pulls its caster out of the brink (on the heavy Ram) and drags the
  staggered Ram across the ravine.
- The other 35 assignments lose for a nameable reason: no lure (nothing takes the Ram's weight),
  two lures (nothing finishes), or a brink holder with a fireball, a wave or a vortex (gored).

## Examples

### Example 1: Flash, crash, blast

**Given:** the player knows `blindingFlash`, the mage knows `fireball`.

**When:** `win`

**Then:** the player walks into the arena and flashes; the blinded Ram winds up; its charge lands on
an empty brink, and it crashes into the pillar (`staggered`, no longer heavy); the mage's fireball
knocks it into the rift (or over the edge into the ravine).

### Example 2: Taunt, then hook from the ledge

**Given:** the player knows `taunt`, the mage knows `hook`.

**When:** `win`

**Then:** the player taunts it from the arena; the charge crashes it into the pillar; the mage walks
round to the ledge and hooks it across the ravine, where it falls.

### Example 3: Hook out of the way

**Given:** the player (on the brink) knows `hook`, the mage knows `taunt`.

**When:** `win`

**Then:** the mage taunts it; in the window the player hooks the heavy Ram, which anchors the hook
and drags the player into the arena (no interrupt: the charge is physical); the charge finds an
empty brink; the player walks round to the ledge and hooks the staggered Ram into the ravine.

### Example 4: The shield takes the gore

**Given:** the player (on the brink) knows `shieldBash`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the mage flashes in the arena; in the window the player bashes the Ram (nothing lands on
it, but the player is shielded); the gore breaks the shield instead; the second bash knocks the
staggered Ram into the rift.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan; no solo plan anywhere. |
| P2 | The measured assignments win | Exactly the 14 measured assignments have a plan, with 10 methods and no dead skill. |
| P3 | Every plan crashes the Ram | Every winning plan lets the charge land on the brink and staggers the Ram. |
| P4 | Heavy, it holds | Without a lure (`fireball`+`vortex`, `tidalWave`+`hook`): no plan. |
| P5 | The brink holder is gored | A finisher with a fireball or a wave on the brink: no plan; the same finisher in the pen wins; a mage moved onto the brink loses too. |
