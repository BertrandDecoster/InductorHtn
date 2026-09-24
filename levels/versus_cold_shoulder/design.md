# Cold Shoulder

## Purpose

Category: **an enemy's area ability turned on its allies, through its moods**. Two fire imps keep a
goblin foundry hot, one in the forge and one in the kiln; a chilled imp dies (it is a
`fireElemental`: its catalogue weakness), but nobody in the party carries cold. The frost troll in the
cave does. Taunted, blinded or jolted, it **breathes frost** on the area it stands in
(`behavior(troll, taunted|blinded|electrocuted, frostBreath, here)`,
`effect(frostBreath, target, spill(iceSheet))`): the floor ices over and everyone there is chilled,
applied raw, so the imps' weakness answers. **The ice stays**: an imp brought onto it later dies too.
Each mood works once (the tag stays stored), and a taunted troll keeps following its taunter. The
breath is instant: this level has no heavy blow (the other two versus levels do). Two companions,
one skill each from seven.

| Way | How |
|-----|-----|
| **Lure it, lead it on** | `taunt` from the forge: the troll walks over and breathes there (imp1). It follows the taunter on to the kiln, where a second mood sets it off again: `blindingFlash` from inside, `lightningFlash` from next door |
| **Gather** | `hook` imp1 into the hall, then into the cave; set the troll off where it stands (`blindingFlash`, `lightningFlash`) - or breathe first and hook the imp onto the ice |
| **The lip** | imp2 stands at the gap between the kiln and the cave: knock it in (`fireball`, `tidalWave`, `shieldBash`) or hook it across from the cave (it falls) |

Why no single skill works:
- Nothing in the pool chills (no `blizzard`). The only cold is the troll's.
- The imps are mindless (`immune(imp, taunted)`): only a hook moves them.
- The troll answers each mood once: two taunts reach one imp.
- Knocks only reach imp2 (the lip); hooks alone gather imp1 but nothing sets the troll off; a flash
  alone leaves the imps where they are.

Traps: a stunned troll (a shield bash) is silenced and breathes no more; a knock can drop the troll
itself into the gap; fire on the ice leaves a puddle (a fireball on an iced room undoes it for the
second imp); a wave soaks the imps, and a soaked imp brought onto the ice only freezes over (wet meets
chilled: stunned) - only the breath itself, applied raw, still kills it.

Skills with two roles: `taunt` moves the troll, sets it off, and leads it on; `hook` gathers imp1,
delivers it onto the ice, and drops imp2 over the lip.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
hall (party) ---------- cave (troll)
  |                  .'   :
forge (imp1) ---- kiln (imp2)        kiln : cave is a gap (the lip of the cold-room)
```

- **Links:** walkable hall-forge, hall-cave, forge-kiln; a gap kiln-cave.
- **Sight:** hall-forge, hall-cave, forge-cave, kiln-cave.
- **Imps:** `fireElemental`, immune to taunts, light. **Troll:** living, light, immune to chilled.
- Both companions start in the hall with 4 mana.
- **Level-local recipes:** `fetch(?e, ?r)` (there, or brought one or two links by `bringTo`),
  `come(?r)` (the troll brought, or led by the one it follows), `setOff(?r)` (a flash from inside,
  a jolt or a taunt from where it reaches; the others step aside), `chill(?imp)` (dropped in the gap,
  fetched onto the ice, or caught in the breath: the troll brought to it or it to the troll, or the
  troll first and the imp after). `win` = chill imp1, then imp2.

## Hypothesis

Measured with `htn_components combos versus_cold_shoulder`:

- No single skill wins, even held by both companions: 0 of 7.
- 16 of 49 assignments win (8 unordered pairs), 8 methods, 0 solo plans, no dead skills:
  - `taunt` + `blindingFlash` / `lightningFlash` (lure, lead on, set off again);
  - `taunt` + `fireball` / `tidalWave` / `shieldBash` / `hook` (lure; imp2 over the lip);
  - `hook` + `blindingFlash` / `lightningFlash` (gather or deliver onto the ice; imp2 over the lip).
- Losing pairs, each for a named reason: two taunts (one mood each), two flashes or a flash and a
  knock (imp1 never meets the cold), a hook and a knock (nothing sets the troll off).
- Skill usage: taunt 12, hook 6, blindingFlash 4, lightningFlash 4, fireball 2, tidalWave 2,
  shieldBash 2.
- One `FindAllPlans` takes under 4 s.

## Examples

### Example 1: Lure it, then lead it on

**Given:** the player knows `taunt`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** the player taunts the troll from the forge; it walks over and breathes there (imp1 dies).
The player walks on to the kiln and the troll follows; the mage flashes it there and it breathes
again (imp2 dies).

### Example 2: Gather, then jolt

**Given:** the player knows `hook`, the mage knows `lightningFlash`.

**When:** `win`

**Then:** the player hooks imp1 into the hall, then into the cave; the mage's lightning flash jolts
the troll, which breathes on the cave (imp1 dies); the player hooks imp2 across the lip, and it falls.

### Example 3: Breathe first, then hook onto the ice

**Given:** the player knows `hook`, the mage knows `blindingFlash`.

**When:** `win`

**Then:** among the plans: the mage flashes the troll in its cave first; the player then hooks imp1
through the hall onto the ice, where it dies.

### Example 4: Over the lip

**Given:** the player knows `taunt`, the mage knows `fireball`.

**When:** `win`

**Then:** the player lures the troll to the forge (imp1 dies); the mage's fireball knocks imp2 into
the gap at the kiln's edge.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the seven, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the eight measured pairs have a plan. |
| P3 | Each mood once | taunt + taunt: no plan. |
| P4 | A stunned troll never breathes | With the troll stunned, taunt + blindingFlash: no plan. |
| P5 | A soaked imp only freezes | With imp1 wet, no plan kills it by arrival on the ice; the breath still does. |
| P6 | Fire melts the ice | A fireball on an iced room leaves a puddle. |
