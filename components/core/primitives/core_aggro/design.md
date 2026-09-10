# Core Aggro

## Purpose

Moving enemies and holding ground. Three ways to bring an enemy somewhere,
each with its own cost: the Warden's Magnetize drags iron only, from range;
the player's Gust pushes anything, from range; the player's Dash taunts
anything into following, and lands the player in the same region, terrain
and all. Holding a position (the Warden's shield) is a commitment: an
anchored agent neither moves nor pulls until it is released, and releasing
is a visible step.

## Layer

primitive

## Dependencies

- `core/primitives/core_world`
- `core/primitives/core_chemistry`

## Operators

| Operator | Description |
|----------|-------------|
| `opLure(?a, ?e, ?from, ?to)` | `?a` drags iron `?e` into `?to`. |
| `opPush(?a, ?e, ?from, ?to)` | `?a` shoves `?e` from `?from` into `?to`. |
| `opTaunt(?a, ?e, ?from, ?to)` | `?a` dashes through `?e`; both end up in `?to`. |
| `opAnchor(?a)` / `opRelease(?a)` | Plant / lift the shield. |

## Methods

| Method | Description |
|--------|-------------|
| `lure(?e, ?to)` | First free puller, from a vantage, drags a `metal` enemy one edge; an anchored puller is released first. The enemy suffers the terrain. |
| `push(?e, ?to)` | The player, from a vantage, pushes a non-iron enemy one edge; it suffers the terrain. |
| `taunt(?e, ?to)` | The player goes to the enemy and dashes on; both suffer the terrain. |
| `holdPosition(?a, ?r)` | Anchor at `?r` (re-anchor if anchored elsewhere). |
| `bringTo(?e, ?r)` | No-op if the enemy is at `?r`, else lure, push or taunt - alternatives, not fallbacks. |

## Required Facts

| Fact | Description |
|------|-------------|
| `skillElement(?skill, pull)` | Marks a pulling skill (Magnetize) |
| `skillElement(?skill, push)` | Marks a pushing skill (Gust) |
| `skillElement(?skill, dash)` | Marks the taunting dash |
| `metal(?e)` | What Magnetize can move |

## Examples

### Example 1: Lure

**Given:** `warden` at `entry` with `magnetize` (`pull`) and line of sight to `gallery`, iron `gob` at `gallery`, `connected(gallery, corridor)`.

**When:** `lure(gob, corridor)`

**Then:** plan contains `opLure(warden, gob, gallery, corridor)` and no `opNavigate`; final state has `at(gob, corridor)` and the warden still at `entry`.

### Example 2: Push

**Given:** player at `entry` with `gust` (`push`, unlimited) and line of sight to `gallery`, `gob` at `gallery`.

**When:** `push(gob, corridor)`

**Then:** plan contains `opPush(player, gob, gallery, corridor)`.

### Example 3: Taunt

**Given:** player with `dash`, `gob` at `gallery`.

**When:** `taunt(gob, corridor)`

**Then:** plan contains `opTaunt(player, gob, gallery, corridor)`; final state has both at `corridor`.

### Example 4: Hold position

**Given:** `warden` at `entry`.

**When:** `holdPosition(warden, corridor)`

**Then:** plan contains `opNavigate(warden, entry, corridor)`, `opAnchor(warden)`.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Anchored pullers are released first | With the only puller anchored, `lure` contains `opRelease` before `opLure`. |
| P2 | Magnetize only moves iron | An enemy without `metal/1` cannot be lured, and an iron enemy cannot be pushed. |
| P3 | Arrivals suffer the terrain | Taunting an enemy into a `sludge` region leaves it `snared`, and the taunting player with it. |
