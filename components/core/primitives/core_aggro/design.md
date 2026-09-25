# Core Aggro

## Purpose

Moving enemies and holding ground. Three movements bring an enemy
somewhere, named for what they do, never for a skill: a pull brings it one
region toward the puller; a push sends it one region away from the pusher;
a dash taunts it into following, and lands the dasher in the same region,
terrain and all. What resists a movement says so on the enemy
(`immune(?e, pull | push | dash)`); a skill is only the movements it
declares (`skillElement`). Any companion may do
any of them; what they hold decides. Holding a position (the Warden's shield) is a commitment: an
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
| `opLure(?a, ?e, ?from, ?to)` | `?a` pulls `?e` from `?from` into `?to`, toward itself. |
| `opPush(?a, ?e, ?from, ?to)` | `?a` shoves `?e` from `?from` into `?to`, away from itself. |
| `opTaunt(?a, ?e, ?from, ?to)` | `?a` dashes through `?e`; both end up in `?to`. |
| `opAnchor(?a)` / `opRelease(?a)` | Plant / lift the shield. |

## Methods

| Method | Description |
|--------|-------------|
| `lure(?e, ?to)` | First free puller takes aim (a region that targets the enemy's and lies on `?to`'s side) and pulls an enemy not immune to `pull` one edge; an anchored puller is released first. The enemy suffers the terrain. |
| `push(?e, ?to)` | Whoever holds a push takes aim (a region that targets the enemy's and lies on the far side from `?to`) and pushes an enemy not immune to `push` one edge; it suffers the terrain. |
| `taunt(?e, ?to)` | Whoever holds a dash goes to the enemy and dashes on; both suffer the terrain. |
| `holdPosition(?a, ?r)` | Anchor at `?r` (re-anchor if anchored elsewhere). |
| `bringTo(?e, ?r)` | No-op if the enemy is at `?r`, else lure, push or taunt - alternatives, not fallbacks. |

## Required Facts

| Fact | Description |
|------|-------------|
| `skillElement(?skill, pull)` | Marks a pulling skill (Magnetize) |
| `skillElement(?skill, push)` | Marks a pushing skill (Gust) |
| `skillElement(?skill, dash)` | Marks the taunting dash |
| `immune(?e, ?movement)` | What a movement (`pull`, `push`, `dash`) cannot do to `?e` |

## Examples

### Example 1: Lure

**Given:** `warden` at `entry` with `magnetize` (`pull`) and line of sight to `gallery`, `gob` at `gallery`, `entry - corridor - gallery`: the entry is on the corridor's side.

**When:** `lure(gob, corridor)`

**Then:** plan contains `opLure(warden, gob, gallery, corridor)` and no `opNavigate`; final state has `at(gob, corridor)` and the warden still at `entry`.

### Example 2: Push

**Given:** player at `entry` with `gust` (`push`, unlimited), `gob` at `gallery`.

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
| P2 | Immunity stops a movement | An enemy `immune(?e, pull)` cannot be lured; one `immune(?e, push)` cannot be pushed. |
| P3 | Arrivals suffer the terrain | Taunting an enemy into a `sludge` region leaves it `snared`, and the taunting player with it. |
| P4 | A pull is paid for | A pull skill held as a charge is spent by `lure`: with one charge, one pull and no second. |
| P5 | A pull brings it toward the puller | Pulling an enemy from the corridor into the gallery takes the puller into the gallery first. |
| P6 | A push sends it away from the pusher | Pushing the gob from the gallery into the corridor is cast from the gallery: nobody stands beyond it. |
