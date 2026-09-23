# escort

## Purpose

Mastery challenge: agent must reach an NPC and guide them to a destination
through locations declared safe for that NPC. Unsafe locations may contain
enemies or hazards that would harm the NPC.

Models classic escort mechanics. The agent must plan a safe route, not just
the shortest route.

## Layer

challenges

## Dependencies

- `challenges/nav_obstacle` -- provides `navigateTo` and `opMoveTo`

## Operators

| Operator | Description |
|----------|-------------|
| `opEscort(?npc, ?from, ?to)` | Move NPC one hop. Deletes `npcAt(?npc, ?from)`, adds `npcAt(?npc, ?to)`. Agent must be at `?from` before this executes. |

## Methods

| Method | Description |
|--------|-------------|
| `escortTo(?npc, ?dest)` | Navigate agent to NPC, then escort the NPC to `?dest` through safe locations. Handles already-there, single-hop, and two-hop escort paths. |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(agent, ?location)` | Current agent location |
| `npcAt(?npc, ?location)` | Current NPC location |
| `connected(?from, ?to)` | Traversable link between locations |
| `safeFor(?npc, ?location)` | Location is safe for the NPC to pass through |
| `blocked(?location)` | Impassable location (from nav_obstacle, for agent routing) |

## Examples

### Example 1: Direct escort to safe destination

**Given:**
- `at(agent, agentStart)`
- `npcAt(villager, npcStart)`
- `safeFor(villager, safeExit)`
- `connected(agentStart, npcStart)`, `connected(npcStart, safeExit)`

**When:**
- `escortTo(villager, safeExit)`

**Then:**
- Plan: agent navigates to villager, then escorts to safeExit
- Plan contains: `opEscort(villager, npcStart, safeExit)`
- Final state has: `npcAt(villager, safeExit)`

### Example 2: Unsafe destination -- no plan

**Given:**
- `at(agent, agentStart)`
- `npcAt(villager, npcStart)`
- `connected(npcStart, dangerZone)`
- (no `safeFor(villager, dangerZone)` fact)

**When:**
- `escortTo(villager, dangerZone)`

**Then:**
- Planning fails (destination not declared safe)

### Example 3: Already at destination -- no-op

**Given:**
- `npcAt(villager, safeExit)`

**When:**
- `escortTo(villager, safeExit)`

**Then:**
- Plan is empty, state unchanged

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | NPC at destination | After successful plan, `npcAt(npc, dest)` is true |
| P2 | Only safe locations | Every intermediate location visited by the NPC has a `safeFor` fact |
| P3 | Idempotent when at destination | No operators if NPC already at destination |
