# Powder Keg

## Purpose

Category: **an enemy whose trigger is being hit by something a companion can cause** (Hades bomb
enemies, Into the Breach). A clockwork powder-mule carries a keg up on the ridge; knocked flat
(`stunned`) the keg goes off where it lies and sets everything around it alight
(`behavior(mule, stunned, keg, here)`, `effect(keg, area, grant(burning))`). Down in the grove stands
an ent: wood burns (its catalogue weakness), but nothing in the party makes fire. Two companions, one
skill each from eight.

| Step | Skills |
|------|--------|
| **Bring keg and ent together** | the keg to the ent: `taunt`, `magnetize` (pull it from the grove), `translocate` (swap with it from the grove), `gust` (blow it down from the crag), `concuss` (shove it down from the crag, melee); or the ent to the keg: `taunt`, `magnetize`, `translocate` aimed at the ent from the ridge |
| **Knock the mule down** | `shieldBash` (melee), `charge` (a dash), `thunderclap` (melee area, once) |

Why no single skill works:
- A stun where the mule stands spends the keg on the ridge, and a stunned mule cannot be stunned again.
- Every stunner also pushes, but only after the stun, and no line runs through the grove.
- A mover alone brings the two together and nothing goes off.

Skills with two roles: `taunt`, `magnetize` and `translocate` each move either the keg or the ent (pull
the bomb to the victim, or the victim to the bomb). The mule is clockwork (`mindless`): the confusion a
translocate or concuss leaves does not land on it, so it cannot wake it up and waste the blow.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
camp --- road --- grove (ent)
           |      /
          ridge (mule) --- crag
```

- **Line:** from the crag, a push on the ridge lands in the grove.
- **Line of sight:** camp-road, road-grove, road-ridge, grove-ridge, crag-ridge.
- **Ent:** wooden. **Mule:** mindless, immune to burning; stunned, it goes off where it stands.
- Both companions start at the camp with 4 mana.
- **Level-local recipes:** `gather(?b, ?v, ?p)` (pull one to the other, push one into the other's
  region, or swap places with one while standing by the other) and `setOff(?b, ?not)` (land the
  NPC's trigger tag). `detonate` = gather, set off by the other companion, confirm.

## Hypothesis

Measured with `htn_components combos versus_powder_keg`:

- No single skill wins, even held by both companions: 0 of 8.
- 30 of 64 assignments win: every one of the 5 movers with every one of the 3 stunners (15 unordered
  pairs), 15 methods, 0 solo plans, no dead skills.
- Losing pairs, each for a named reason: two stunners (the keg goes off on the ridge), two movers
  (nothing goes off).
- Skill usage: shieldBash 10, charge 10, thunderclap 10, each mover 6.

## Examples

### Example 1: Taunt it down, bash it

**Given:** the player knows `taunt`, the mage knows `shieldBash`.

**When:** `win`

**Then:** the player walks into the grove and taunts the mule, which is dragged down beside the ent;
the mage bashes it from the road; the keg goes off and the ent burns (`dead`).

### Example 2: Swap the ent up to the keg

**Given:** the player knows `translocate`, the mage knows `charge`.

**When:** `win`

**Then:** the player climbs to the ridge and swaps places with the ent, which now stands by the mule;
the mage charges the mule; the keg goes off on the ridge with the ent beside it.

### Example 3: Shove it off the crag

**Given:** the player knows `thunderclap`, the mage knows `concuss`.

**When:** `win`

**Then:** the mage goes round to the crag and shoves the mule down into the grove; the player
thunderclaps it from the road; the keg goes off.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No single skill wins | Each of the eight, held by both companions: no plan. |
| P2 | Measured pairs win | Exactly the fifteen mover-stunner pairs have a plan. |
| P3 | The keg blows once | Two stunners: no plan. |
| P4 | Nobody lights it | Two movers: no plan. |
