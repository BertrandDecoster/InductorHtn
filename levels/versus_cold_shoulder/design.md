# Cold Shoulder

## Purpose

Category: **an enemy's area ability turned on its allies, through its moods**. Two fire imps keep a
goblin foundry hot, one in the forge and one in the kiln; a chilled imp dies (it is a
`fireElemental`: its catalogue weakness), but nobody in the party carries cold. The frost troll in the
cave does. Taunted, it is dragged to whoever taunted it; blinded, it lashes out where it stands. Either
way it winds up a **frost breath**, a telegraphed heavy blow on its region: everyone there but the
troll is chilled, and the floor ices over (`behavior(troll, taunted|blinded, frostBreath, here)`,
`heavy(frostBreath)`, `effect(frostBreath, area, grant(chilled))`,
`effect(frostBreath, target, spill(iceSheet))`). **The ice stays**: an imp that arrives on it later is
chilled too. Each mood works once (the tag stays stored). Two companions, one skill each from six.

| Shape | First | Then |
|-------|-------|------|
| **Gather, then one breath** | both imps in one room: hook one across (`hook`), draw everything into the hall (`vortex`), wash or blast one along a line (`tidalWave`, `fireball`) | the troll there: brought and flashed (`blindingFlash`), or taunted from that room (`taunt`) |
| **Breathe first, then deliver** | flash the troll where it stands (`blindingFlash`) | send the imps onto the ice it leaves (`hook`, `fireball`) |
| **Get the taunter out** | a taunter is inside its own lure's breath | a friend's one cast: `hook` drags it out; `fireball` knocks it clear; `vortex` draws everyone (imps too) out of the room - and a second vortex draws the imps back onto the ice |

Why no single skill works:
- Nothing in the pool chills (no `blizzard`). The only cold is the troll's.
- The imps are mindless (`immune(imp, taunted)`): a taunt cannot move them.
- A taunter is always in the breath and cannot save itself with a taunt; a flash or a wave cannot save
  it either (a wave washes the imps away with it).
- Movers alone gather the imps and nothing breathes; a flash alone leaves the imps apart.

Traps: a soaked imp that arrives on the ice only freezes over (wet meets chilled: stunned, not dead) -
only the breath itself (applied raw) kills a wet imp; fire on the iced room leaves a puddle (a fireball
rescue turns the ice under the breath to water, so nothing can be delivered there later); taunting from
a room with one imp spends the taunt.

Skills with two roles: `fireball` gathers (blasts an imp or the troll along a line) and rescues (knocks
the taunter clear); `vortex` gathers and, cast twice, rescues then delivers; `hook` gathers, delivers
onto the ice, and rescues.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
               kiln (imp2)
              /   |
gate --- hall ----+------ cave (troll) --- vent
              \   |
               forge (imp1)
```

- **Walks:** the hall joins the gate, forge, kiln and cave; forge-kiln; cave-vent.
- **Line of sight:** the hall sees everything next to it; forge-kiln; forge and kiln both see the cave;
  the vent sees the cave.
- **Lines:** from the vent, a push on the cave lands in the kiln; from the hall, in the vent. From the
  hall, a push on the forge lands in the kiln; from the forge, a push on the kiln lands in the cave.
- **Imps:** `fireElemental`, immune to taunts, light. **Troll:** living, light, immune to chilled.
- Both companions start at the gate with 4 mana.
- **Level-local recipes:** `bring(?e, ?r)` (pulled by someone standing in ?r, or pushed, washed or
  drawn - `placement/6`), `trigger(?npc, ?r)` (a lure given from ?r, or a trigger in place),
  `standBy(?r, ?a)` / `stepAside(?r, ?a)` (before a lure, the other companion leaves ?r, or a pusher
  takes a stand on a line that would knock the lurer clear), `breatheOn(?npc, ?r)`, and
  `before`/`after` (an imp brought to the room before the breath, or delivered onto the ice after).
  `win` picks the room (`floor/1`: hall, forge, kiln, cave), optionally brings the troll first, then
  the imps, the breath, the rest onto the ice.

## Hypothesis

Measured with `htn_components combos versus_cold_shoulder`:

- No single skill wins, even held by both companions: 0 of 6.
- 14 of 36 assignments win (7 unordered pairs), 7 methods, 0 solo plans, no dead skills:
  - taunt, and a friend who gets the taunter out: `hook`, `fireball`, `vortex` (3 pairs);
  - a flash, and a gatherer or deliverer: `hook`, `vortex`, `tidalWave`, `fireball` (4 pairs).
- Losing pairs, each for a named reason: `taunt` + `blindingFlash` / `tidalWave` (nobody gets the
  taunter out: a wave washes the imps away too), two movers (nothing breathes).
- Skill usage: blindingFlash 8, taunt 6, hook 4, vortex 4, fireball 4, tidalWave 2.
- One `FindAllPlans` takes 1-13 s (hook + taunt is the slowest: 30 plans).

## Examples

### Example 1: Breathe first, then hook the other imp onto the ice

**Given:** the player knows `hook`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** among the plans: the player hooks one imp into the cave and steps out; the mage flashes the
troll, which breathes on the cave (that imp dies, the cave ices over); the player then hooks the other
imp onto the ice, where it dies too.

### Example 2: Fireball the imp over, taunt, knock the taunter clear

**Given:** the player knows `fireball`, the mage knows `taunt`.

**When:** `win`

**Then:** from the hall the player's fireball blasts the forge imp into the kiln and takes a stand in
the forge; the mage taunts the troll from the kiln, it is dragged in and winds up; the player's second
fireball knocks the mage clear into the cave; the breath kills both imps, and the ice meets the fire
the fireball left: the kiln is a puddle.

### Example 3: Vortex out, then back onto the ice

**Given:** the player knows `taunt`, the mage knows `vortex`.

**When:** `win`

**Then:** among the plans: the player taunts the troll into the hall and it winds up; the mage vortexes
the gate, drawing the player (and the troll) out; the breath ices the empty hall; a second vortex on
the hall draws both imps onto the ice.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the six, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the seven measured pairs have a plan. |
| P3 | The taunter is answered | Every taunt plan has the partner cast between the wind-up and the breath. |
| P4 | The ice stays | An imp sent onto the ice after the breath dies there (fireball + blindingFlash). |
| P5 | A soaked imp only freezes | With imp1 wet, no plan kills it by arrival on the ice. |
| P6 | A taunt with no rescue | taunt + blindingFlash, taunt + tidalWave: no plan. |
