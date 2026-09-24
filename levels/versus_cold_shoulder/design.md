# Cold Shoulder

## Purpose

Category: **an enemy's area ability turned on its allies, through its moods** (fear it so it flees
where you want, charm it so it acts where it stands, taunt it so it comes to you). Two fire imps keep a
goblin foundry hot, one in the forge and one in the kiln; a chilled imp freezes solid (its catalogue
weakness), but nobody in the party carries cold. The frost troll in the cave does: every new mood makes
it breathe frost on everything around it (`behavior(troll, taunted|feared|charmed, frost, here)`).

- **taunted:** it is dragged to whoever taunted it, and breathes there.
- **feared:** it bolts along the line away from whoever frightened it, and breathes where it lands.
- **charmed:** it breathes where it stands.

Each mood works once (the tag stays stored). A taunted troll cannot be frightened (`wards(taunted,
feared)`), and a charmed troll wakes at the next hostile tag instead of taking it. Two companions, one
skill each from eight.

| Method | First | Then |
|--------|-------|------|
| **Two moods** | frighten it from the vent (`terrify`, `roar`): it bolts into the kiln | drag it into the forge (`taunt` from the forge, `provoke` from the forge next door) |
| **Gather, then one mood** | put both imps in one room: hook or swap one across (`magnetize`, `translocate`), or blow the forge imp into the kiln from the hall (`gust`) | any mood that lands the troll there |
| **Bring them to the troll** | hook or swap both imps into the cave (`magnetize`, `translocate`) | `charm` it where it stands |

Why no single skill works:
- The same mood twice is one breath, and the imps are apart.
- The imps are mindless and have no temper: no mood lands on them, so no mood skill moves them.
- A mover alone brings imps together and nothing breathes.

Skills with two roles: `magnetize` and `translocate` gather the imps in either imp's room, or both in
the troll's cave; `provoke` is a second mood (after a fear) or the mood that fetches the troll to a
gathered pair.

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
- **Lines:** from the vent, a push on the cave lands in the kiln; from the hall, in the vent (the
  trap). From the hall, a push on the forge lands in the kiln; from the forge, a push on the kiln
  lands in the cave.
- **Imps:** element fire, mindless, immune to taunts. **Troll:** living; its frost is
  `area: grant(chilled)`.
- Both companions start at the gate with 4 mana.
- **Level-local recipes:** `bringTo(?e, ?r, ?p)` (pull, push or swap an imp into a region, then
  confirm it arrived) and `lure(?npc, ?v, ?not)` (a mood that drags it, drives it along a line, or
  sets it off in place, so that it breathes where ?v stands). `win` has five alternatives: two moods
  in either order, one imp brought to the other then one mood, both brought to the troll then one
  mood.

## Hypothesis

Measured with `htn_components combos versus_cold_shoulder`:

- No single skill wins, even held by both companions: 0 of 8.
- 34 of 64 assignments win (17 unordered pairs), 17 methods, 0 solo plans, no dead skills:
  - two moods: `terrify` or `roar`, plus `taunt` or `provoke` (4 pairs);
  - gather, then one mood: `gust` + `taunt`, `terrify`, `roar`; `magnetize` or `translocate` + `taunt`,
    `provoke`, `terrify`, `roar` (11 pairs);
  - bring them to the troll: `magnetize` or `translocate` + `charm` (2 pairs).
- The 11 losing pairs, each for a named reason: the same mood twice (`taunt`+`provoke`,
  `terrify`+`roar`); two movers (nothing breathes); `charm` with anything but a two-imp mover (it
  breathes where it stands, and nothing follows a charm); `gust`+`provoke` (provoke drags the troll
  into the hall, not the kiln).
- Skill usage: taunt 10, terrify 10, roar 10, magnetize 10, translocate 10, provoke 8, gust 6, charm 4.
- One `FindAllPlans` takes about 0.5-1.5 s.

## Examples

### Example 1: Fear, then taunt

**Given:** the player knows `terrify`, the mage knows `taunt`.

**When:** `win`

**Then:** the player goes round to the vent and frightens the troll, which bolts into the kiln and
freezes the kiln imp; the mage taunts it from the forge, it is dragged in and freezes the forge imp.

### Example 2: Blow one imp over, then scare the troll in

**Given:** the player knows `gust`, the mage knows `roar`.

**When:** `win`

**Then:** from the hall the player blows the forge imp into the kiln; the mage roars at the troll from
the vent, it bolts into the kiln and its frost freezes both imps.

### Example 3: Hook both, then charm

**Given:** the player knows `magnetize`, the mage knows `charm`.

**When:** `win`

**Then:** the player walks into the cave and hooks both imps in; the mage charms the troll, which
breathes where it stands and freezes both.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the seventeen measured pairs have a plan. |
| P3 | One breath per mood | taunt + provoke, terrify + roar: no plan. |
| P4 | Charm does not travel | charm with a mood skill or with gust: no plan. |
