# The Crossing

## Purpose

The demo level for the ability catalogue (`abilities/primitives/ab_catalog`). Three enemies, each
beaten only by its own weakness; nothing in the catalogue kills in general. The player picks 2 of 8
skills. It exists to show:
- guards that come off first: a shield takes the next hostile tag, stealth takes light;
- per-enemy weaknesses: soaked then jolted, or soaked then chilled;
- a hazard that takes whoever is weak to it (the abyss takes anything that walks);
- a boss that ignores hard control but not a push, once its armour is off.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/primitives/ab_catalog`

## World

```
gate (player, mage, warden)
  |
hall ---- crypt (bramble; shadows)
  |          \
brink (sentry, brute) --> abyss (chasm)
```

- **Walking:** gate–hall, hall–crypt, hall–brink.
- **Line of sight:** gate→hall, gate→brink, hall→crypt, hall→brink.
- **Push lines:** whatever stands at the brink or in the crypt goes into the abyss.
- **Zones:** the crypt hides whoever walks in (`shadows`); the abyss is a `chasm`.

| Enemy | Traits | Weak to |
|-------|--------|---------|
| sentry | machine, heavy (cannot be moved), shielded | electrocuted on wet → dead (machine); chilled on wet → frozen (this level) |
| bramble | wooden, stealthed | burning → dead (wooden); the chasm → fell |
| brute | boss (no hard control), living, armored (cannot be moved while armoured) | the chasm → fell |

- **The Mage** knows flashbang and rainCall.
- **The Warden** knows sunder, shieldBash and taunt.
- **The player** has 4 mana and picks 2 of: zap, chainLightning, fireball, iceStorm, frostBolt,
  tidalWave, gust, charge.

## Hypothesis

Measured by `fun crossing --loadouts`:

- **F4:** 16 of 28 kits win (feasibility 0.57), with no mandatory and no dead pick. The winners are
  exactly one sentry pick (zap, chainLightning, frostBolt or iceStorm) times one push pick (gust,
  fireball, tidalWave or charge). The multi-use factor is 1.0: each pick answers one enemy, so the
  kit choice is a matching exercise, not yet a puzzle.
- **F6:** 0 single-actor and 0 soloable plans (`funExpect(single_actor_plans, atMost, 0)`). The
  default kit (zap + gust) has 5 player decision points.
- **F1:** the default kit has 10 plans in one strategy class: the ways to break the sentry's shield
  (any hostile tag) and to soak it vary; the recipe does not.

The first version of this level was too tight: 2 of 28 kits won and gust was mandatory. The player's
pushes cost mana and two enemies needed one each. Mana went from 3 to 4, the sentry gained a frost
weakness, and pushes that hit an area (tidalWave) or land after a dash (charge) were taught to the
planner.

## Examples

### Example 1: The default kit clears the crossing

**Given:** the player knows `zap` and `gust`.

**When:** `clearCrossing`

**Then:** the sentry is dead, the bramble is out, the brute fell.

### Example 2: The sentry is soaked, then jolted

**Given:** the default kit.

**When:** `neutralize(sentry)`

**Then:** a plan has the mage call rain on it and the player's zap short-circuit it.

### Example 3: The brute loses its armour, then its footing

**Given:** the default kit.

**When:** `neutralize(brute)`

**Then:** the warden sunders its armour and the player pushes it into the abyss.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every default-kit plan has two or more companions acting. |
| P2 | The boss is not stunned | A shield bash on the brute leaves it unstunned. |
| P3 | Kits that win and lose | The measured winning and losing kits pinned in the test still hold. |
