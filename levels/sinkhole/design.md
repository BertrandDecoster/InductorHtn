# The Sinkhole

## Purpose

The demo level for the ability layer (`components/abilities/`). A stone golem stands at the rim of a
pit; below it a cultist wades in a flooded pool and another tends an oil slick. The player picks two
abilities from six. The Mage douses, and the Warden swings a hammer or shoves, but either one tires
them, so the Warden gets one of the two.

It exists to show the layer's claims in one place:
- abilities are bundles (a fireball damages, sets alight and pushes);
- combos are physics (wet + shocked, wet + chilled, oiled + burning, brittle + blunt, wet + burning = steam);
- a heavy boss is immune to forced movement until something unbalances it;
- stalling is a finisher for one enemy and a setup for another;
- different kits clear the level by different recipes.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`

## World

```
            ledge (player, mage, warden)
              |
   slick --- rim (golem) --- pool (wader)
                  \\
                   pit
```

- **Walking:** ledge–rim, rim–pool and rim–slick. Nobody walks into the pit.
- **Line of sight:** the ledge sees everything; the rim sees the pool and the slick.
- **Push lines:**
  - ledge on rim → pit
  - rim on rim → pit (a shove at the edge)
  - rim on pool → pit
  - ledge on slick → pool
- **Zones:** the pool soaks (wet), the slick oils, the pit takes (fell).
- **Frozen** bundles rooted, brittle and offBalance, and offBalance suspends immunity to forced movement.

| Enemy | Traits |
|-------|--------|
| golem | Boss. Immune to forced movement, shock, burning and blunt. Only the pit takes it, once it is unbalanced (quake) or frozen (wet, then chilled). |
| wader | Mook, starts wet, and frozen stops it. Shock it, chill it, or push it from the rim into the pit. |
| tender | Mook, starts oiled, vulnerable to fire. Burn it, douse and shock it, douse and chill and break it, or push it into the pool. |

**Kit (pick 2):**
- fireball: damage(fire) + burning + push, 2 mana of the player's 3
- shock
- gust: push
- chill
- quake: offBalance, tires the caster
- douse

## Hypothesis

Measured by `fun sinkhole --loadouts` and pinned by `test.py`:

- F4: at least three kits win, and no pick is mandatory. **Measured:** 4 of 15 (chill+fireball, chill+gust, chill+shock, quake+shock), no mandatory pick, 6 near misses. Fireball+quake wins every enemy alone but not the encounter, because the mana is shared.
- F6: every plan needs two companions with the player among them; no single-actor plans. **Measured:** 0 single-actor and 0 soloable plans (`funExpect(single_actor_plans, atMost, 0)`).
- F1: several ways per kit. **Measured:** the default kit (chill + fireball) has 3 plans in 3 recipe classes, and 7 classes across the winning kits.

Known shortfalls, left visible on purpose:
- **F2 Distinctness fails for every kit.** Each kit has one golem recipe, so its plans share their first third, and fireball on the tender is found both by `ignite` and `improvise`.
- **F3 plan length is ~20.** The physics records every consequence as its own operator (grant, remove, react), so length counts consequences, not decisions.
- **F6 teamwork edge ratio is low.** Most causal edges run from a cast to its own consequences.

These come from how finely the layer records physics, not from the level. See
`docs/reference/ability-system.md`, "Interaction with the fun metrics".

## Examples

### Example 1: The default kit clears the sinkhole

**Given:** the player knows `chill` and `fireball`.

**When:** `clearSinkhole`

**Then:** the golem fell, the wader is frozen, the tender is dead.

### Example 2: The golem is frozen, then pushed

**Given:** the default kit.

**When:** `neutralize(golem)`

**Then:** a plan has the mage douse the golem, the player's chill freeze it, and the warden shove it into the pit.

### Example 3: Steam dries the wader

**Given:** the wader is wet.

**When:** a fireball hits it

**Then:** it is no longer wet.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every plan has at least two companions acting, the player among them. |
| P2 | At least three kits, none mandatory | Replanning every pick-2 kit finds three or more winners, and each pick is absent from at least one. |
| P3 | The golem cannot be shoved as it stands | Without unbalancing it, the warden's shove has no plan. |
