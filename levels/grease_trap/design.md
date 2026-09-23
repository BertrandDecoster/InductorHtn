# The Grease Trap

## Purpose

The flagship encounter for the core vocabulary. One oil corridor, two
enemies, two strategies, and a kit of two skills chosen from five. It exists
to show, in one level, the things the fun metrics were built to see: a
choice space whose picks matter across both fights, terrain that one fight
consumes and the other reuses, a companion commitment with a visible cost,
and a role structure that puts two companions in every plan - the
controlled one among them - while leaving the team decisions to make.

## Layer

level

## Dependencies

- `core/goals/defeat_group`

## World

```
entry --- corridor (oil) --- exit (bearer, iron)
              |
           gallery (swarm)
```

Line of sight to the corridor from `entry` and `gallery`; the entry
overlooks the gallery; the gallery and the corridor overlook the exit. The
Warden carries Magnetize (moves iron only) and Shield; the Arcanist carries
Freeze. The player has one Ignite charge, one Lightning charge, an unlimited
Gust (moves flesh only), Dash (taunts an enemy into following, and lands the
player beside it) and Flare (dazzles one enemy into taking a direct strike).

## Hypothesis

Measured by `python -m htn_components fun grease_trap --ablate --loadouts`:

- F1: two ideas - the burn and the slipstream - with the default kit, and
  the same two across the lattice.
- F3: median plan length 6 to 12; causal depth at least 3.
- F4: encounter feasibility between 0.2 and 0.4; no mandatory pick; one
  herring dead; near misses exist.
- F6: no single-actor plan and no plan that idles the controlled
  companion; at least two player decision points; teamwork edge ratio
  above 0.3.

## Examples

### Example 1: The burn takes the swarm

**Given:** the level as declared (default kit: `ignite`, `gust`).

**When:** `defeatGroup(swarm)`

**Then:** some plan contains `opPush(player, swarm, gallery, corridor)` and `opCastRegion(player, ignite, corridor, oil, scorched)`; after `theBurn(swarm)`, `regionHas(corridor, scorched)` and `status(swarm, dead)`.

### Example 2: The slipstream takes the bearer

**Given:** the level as declared.

**When:** `theSlipstream(bearer)`

**Then:** some plan contains `opCastRegion(arcanist, freeze, corridor, oil, sludge)`, `opAnchor(warden)`, `opLure(warden, bearer, exit, corridor)`, `opStatus(warden, bearer, snared)`, `opCastEntity(player, ignite, bearer, dead)`.

### Example 3: The whole encounter

**Given:** the level as declared.

**When:** `clearGreaseTrap`

**Then:** a plan exists; after it both `swarm` and `bearer` are `dead`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every plan for `clearGreaseTrap` has operators by at least two companions, and the controlled companion (`player`) is one of them. |
| P2 | A gust does not move iron | `push(bearer, corridor)` has no plan; the bearer is the Warden's problem. |
| P3 | Burned oil cannot be frozen | After `theBurn(swarm)`, `theSlipstream(bearer)` has no plan when no sludge exists. |
