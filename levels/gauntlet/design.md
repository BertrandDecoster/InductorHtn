# The Gauntlet

## Purpose

The first pure-movement level on the ability layer. Nothing dies except by falling. It has two
victories: escape (all three companions reach the exit) or rout (both enemies fall). Every obstacle
has several answers:

- **The guard at the choke:** drop it through the trapdoor, move it out of the doorway, or slip past.
- **The latching gate:** someone walks onto the plate, or the crate is pushed onto it.
- **The chasm:** bridge it with the crate (two pushes, or dragged across), or cross one by one:
  blink, dash, hook the pillar, swap with someone, or be swapped over by a friend.
- **The archer:** armoured, so the Warden must sunder it from close by (which needs the bridge), then
  someone pushes it off the cliff.

**Known flaw, to be reworked.** `htn_components combos gauntlet` fails. The companions' fixed skills
(the Warden's shield bash and sunder, the Mage's translocate) win the level with no player skill at
all, so every pool skill "wins alone". `test.py` pins that flaw (P3) until the rework removes it.

## Layer

level

## Dependencies

- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
start --- choke (guard) --- hall (crate) --- rim ~~ chasm ~~ far (archer, pillar) --- gate --- exit
            |                 |                                  |
           pit              alcove (plate: latches the gate)    cliff
```

## Hypothesis

- Several routes per obstacle, and both victories reachable. The default kit (gust + magnetize) has
  about 80 plans; none is carried by one companion.
- Not yet met: the player's pick should matter (see the flaw above).

## Examples

### Example 1: Everyone escapes

**Given:** the default kit.

**When:** `escape`

**Then:** all three companions reach the exit; the gate is open.

### Example 2: The crate bridges the chasm

**Given:** the default kit.

**When:** `escape`

**Then:** a plan has the Warden and the player push the crate into the chasm.

### Example 3: The rout

**Given:** the default kit.

**When:** `rout`

**Then:** the Warden sunders the archer, and the player gusts it off the cliff.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan has two or more companions acting. |
| P2 | The crate cannot do both | Pushed onto the plate, the crate no longer bridges the chasm, and the Warden is stranded. |
| P3 | The companions carry it (known flaw) | With no player skill, the level is still won. |
