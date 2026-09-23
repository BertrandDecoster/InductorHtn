# trigger_gate

## Purpose

Multi-step mastery challenge: agent must find and activate a switch that opens
a gate blocking the path to their destination, then navigate through the
now-open route.

Models classic puzzle-game "press button, door opens" mechanics at the HTN
level. Low-level movement is handled by nav_obstacle (dependency).

## Layer

challenges

## Dependencies

- `challenges/nav_obstacle` — provides `navigateTo` and `opMoveTo`

## Operators

| Operator | Description |
|----------|-------------|
| `opActivateSwitch(?switch)` | Trigger a switch. Deletes `switchIdle(?switch)`, adds `switchTriggered(?switch)`. |
| `opOpenGate(?gate)` | Open a gate. Deletes `gateBlocking(?gate, ?dest)`, adds `gateOpen(?gate, ?dest)`. |

## Methods

| Method | Description |
|--------|-------------|
| `reachThroughGate(?agent, ?dest)` | Navigate to destination by first activating the controlling switch to open the blocking gate. Falls through to direct nav if gate already open. |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(?agent, ?location)` | Current agent location |
| `connected(?from, ?to)` | Traversable link between locations |
| `blocked(?location)` | Location is impassable (from nav_obstacle) |
| `gateBlocking(?gate, ?dest)` | Gate is currently blocking access to destination |
| `switchControls(?switch, ?gate)` | Switch opens the specified gate |
| `switchAt(?switch, ?location)` | Physical location of the switch |
| `switchIdle(?switch)` | Switch has not yet been activated |

## Examples

### Example 1: Standard gate-and-switch puzzle

**Given:**
- `at(agent, entrance)`
- `gateBlocking(gate1, exitRoom)`
- `switchControls(switch1, gate1)`
- `switchAt(switch1, sideRoom)`
- `switchIdle(switch1)`
- `connected(entrance, sideRoom)`, `connected(sideRoom, exitRoom)`

**When:**
- `reachThroughGate(agent, exitRoom)`

**Then:**
- Plan contains: `navigateTo` to sideRoom, `opActivateSwitch(switch1)`, `opOpenGate(gate1)`, `navigateTo` to exitRoom
- Final state has: `switchTriggered(switch1)`, `gateOpen(gate1, exitRoom)`
- Final state does not have: `gateBlocking(gate1, exitRoom)`, `switchIdle(switch1)`

### Example 2: Gate already open — direct navigation

**Given:**
- `at(agent, entrance)`
- `gateOpen(gate1, exitRoom)` (already open)
- `connected(entrance, exitRoom)`

**When:**
- `reachThroughGate(agent, exitRoom)`

**Then:**
- Plan uses `navigateTo` directly, no switch activation needed

### Example 3: No switch for blocking gate — no plan

**Given:**
- `at(agent, entrance)`
- `gateBlocking(gate1, exitRoom)`
- (no switchControls fact)

**When:**
- `reachThroughGate(agent, exitRoom)`

**Then:**
- Planning fails (no way to open gate)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Agent reaches destination | After successful plan, agent is at `?dest` |
| P2 | Gate opened | After plan, `gateOpen` fact exists for the activated gate |
| P3 | Switch consumed | After plan, `switchIdle` is gone and `switchTriggered` is present |
| P4 | Already-open gate requires no activation | If gate is already open, no switch operator is executed |
