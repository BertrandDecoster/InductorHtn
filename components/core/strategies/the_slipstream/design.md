# The Slipstream

## Purpose

Crowd control. Freeze the oil into sludge, plant the shield at its edge, get
the enemy stuck in it - pushed, dragged or taunted - and either finish it
while it cannot move or electrify the sludge and take everything in it. Two
roles, primer and pay-off, and they must be different companions; anyone
may take either.
Sludge persists, so the trap made for one fight serves the next; the shield
commitment persists too, so the Warden holding the edge is not free to pull
until released.

## Layer

strategy

## Dependencies

- `core/primitives/core_aggro`
- `core/primitives/core_attunement`

## Methods

| Method | Description |
|--------|-------------|
| `theSlipstream(?e)` | Find a region that snares or can be made to, bind the primer, make the trap, cover its edge, bring `?e` in, bring whoever else can be brought, then someone other than the primer strikes the one dead or blasts the lot. |
| `trapSite(?r, ?trap, ?p)` (rule) | A region that has the snaring terrain (`?p` = `none`), or can be made to by a reaction whose first able caster is `?p`. |
| `makeTrap(?r, ?trap, ?p)` | No-op for `none`, else `?p` primes the reaction that makes the terrain. |
| `coverAt(?r)` | The shield-bearer holds the first region adjoining `?r`. |
| `gatherIntoTrap(?e, ?r)` | Every other living enemy that can be brought into the trap, is. |
| `finishTrap(?e, ?r, ?p)` | `strikeDead` the snared enemy, or `blastDeadAt` the trap, by anyone but `?p`. Alternatives. |

## Examples

### Example 1: Push them in

**Given:** oil in `corridor`, `swarm` at `gallery`, arcanist with `freeze`, warden with `shield`, player with `gust` and one `lightning` charge, line of sight from `entry` to `gallery` and `corridor`.

**When:** `theSlipstream(swarm)`

**Then:** some plan contains `opCastRegion(arcanist, freeze, corridor, oil, sludge)`, `opAnchor(warden)`, `opPush(player, swarm, gallery, corridor)`, `opStatus(player, swarm, snared)`, `opCastEntity(player, lightning, swarm, dead)`.

### Example 2: Drag them in

**Given:** as Example 1 but the swarm is iron and the player has no push.

**When:** `theSlipstream(swarm)`

**Then:** the plan releases the anchored Warden and lures: `opRelease(warden)`, `opLure(warden, swarm, gallery, corridor)`; no `opPush`.

### Example 3: Blast the lot

**Given:** as Example 1.

**When:** `theSlipstream(swarm)`

**Then:** some plan electrifies the sludge instead of striking: `opCastRegion(player, lightning, corridor, sludge, scorched)` then `opStatus(player, swarm, dead)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | The enemy ends dead | After `theSlipstream(?e)`, `status(?e, dead)`. |
| P2 | Nothing moves an unreachable enemy | A flesh enemy with no push and no dash available cannot be brought in: no plan. |
| P3 | The primer never pays off | Whoever froze the trap is excluded from the finish and the blast, even when they hold a lethal element. |
