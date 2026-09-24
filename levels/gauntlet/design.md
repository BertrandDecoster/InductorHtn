# The Gauntlet

## Purpose

The pure-movement level on the ability layer. Nothing dies except by falling. Three companions have
to reach the exit: the player and the mage pick **one skill each** from six catalogue skills, and
the Warden, who only knows `turnToMist`, cannot leap. So the guard has to be moved out of his way
and the lava channel has to be bridged for him. Three obstacles, each with several answers:

| Obstacle | Answers |
|----------|---------|
| **The heavy guard at the choke** | Nothing moves it until the Warden turns it to mist. For that moment (the next cast) someone drops it through the trapdoor (`fireball` or `tidalWave` from the start) or drags it out of the doorway (`hook`). |
| **The plate in the grated alcove** (latches the exit gate) | Nobody walks onto it. A leaper lands on it (`blink`, `lightningFlash`) and leaps on over the lava; or a pusher throws a friend onto it from the rim (`fireball`, `tidalWave`), and the friend gets out forward: hooks the far pillar (`hook`), or is hooked out by a friend across. The crate can be thrown onto it too. |
| **The lava channel** | The crate fills it: two pushes (`fireball`, `tidalWave`: onto the rim, then in), or a hook hauls it to the rim, the hooker grapples across on the pillar and drags it in from the far side (`hook`). Or a `blizzard` cools the lava to rock (a zone reaction: ice on lava leaves no zone). |

The crate can hold the plate or fill the channel. The plate latches, so a `hook` can take the crate
back off it and still bridge the lava; without a hook, a crate on the plate leaves only the
blizzard.

Why no single skill wins, even held by both seats:
- a pusher throws a friend onto the plate and strands him there, or spends the crate on the plate
  and cannot bridge the lava;
- a leaper cannot move the guard or the crate;
- a hook gets nobody onto the plate;
- the blizzard moves nothing.

Traps: a tidal wave from the rim throws everyone in the hall onto the plate: the crate, friends and
the Warden alike. The mist lasts through exactly one more cast, so the push must come next. Two
pushers only strand each other.

Several skills serve several roles:
- `fireball` and `tidalWave` drop the guard, throw a friend or the crate onto the plate, and push
  the crate into the lava.
- `hook` drags the guard, hauls the crate (even back off the plate), grapples the pillar out of the
  alcove and across the lava, and hauls a stranded friend out.
- The leapers land on the plate and cross the lava.
- `blizzard` turns the lava into a floor.

## Layer

level

## Dependencies

- `abilities/goals/neutralize`
- `abilities/strategies/passage`
- `abilities/primitives/ab_catalog`

## World

```
start --- choke (guard) --- hall (crate) --- rim ~~ channel (lava) ~~ far (pillar) --- exit (gate)
  |                          :       :                                 :
 pit (trapdoor)            alcove (plate; seen from the hall, the rim and far; never walked into)
```

- **Lines:**
  - From the start, a push on the choke lands in the pit; from the hall, back to the start.
  - From the choke, a push on the hall lands on the rim; from the rim, in the alcove.
  - From the hall, a push on the rim lands in the lava.
  - The lava lies between the rim and far, so a pull from far drops what stands on the rim into it.
- **Line of sight:**
  - start-choke-hall-rim;
  - the hall and the rim see the alcove;
  - the rim and far see the lava and each other;
  - the alcove and far see each other.
- **Guard:** living, heavy, a blocker. **Crate:** a filler. **Pillar:** heavy (an anchor).
- **Exit:** a gate (a door region) that the plate latches open.
- **Warden:** knows `turnToMist` only. The player and the mage have 6 mana each and start with
  `fireball` and `blizzard`. This default kit is the one whose plan fits the planner's default 1 MB
  memory budget, which `verify` uses. Kits that throw the crate twice need about 1.5 MB, which
  `combos` and the tests give them.

## Hypothesis

Measured by `htn_components combos gauntlet` (36 replans in about 8 s in parallel; the slowest
plan takes 5.2 s):

- No single skill wins, even when both seats hold it: 0 of 6.
- 20 of 36 assignments win, 10 pairs each way round:
  - a pusher (`fireball`, `tidalWave`) with a leaper, a `hook` or the `blizzard`;
  - `hook` with a leaper (`blink`, `lightningFlash`).
- 10 methods (sets of skills cast), of five kinds:
  - leap onto the plate, push the crate twice;
  - throw the crate onto the plate, ice the lava;
  - throw a friend who grapples out (or the crate, hooked back off the plate);
  - leap onto the plate, haul the crate and drag it in;
  - mist and hook the guard aside.
- Skill usage: fireball 8, tidalWave 8, hook 8, blink 6, lightningFlash 6, blizzard 4. No dead
  skill; no plan carried by one companion.

## Examples

### Example 1: Mist and drop, crate on the plate, ice on the lava

**Given:** the default kit (player `fireball`, mage `blizzard`).

**When:** `win`

**Then:**
1. The Warden mists the guard, and the player's fireball from the start drops it through the
   trapdoor.
2. The player throws the crate onto the plate from the rim.
3. The mage's blizzard cools the lava into a floor.
4. Everyone walks out.

### Example 2: Blink onto the plate, push the crate in

**Given:** player `fireball`, mage `blink`.

**When:** `win`

**Then:** the mage blinks onto the plate and on over the lava; the player pushes the crate into the
lava in two fireballs.

### Example 3: The latch holds - hook the crate back

**Given:** player `tidalWave`, mage `hook`.

**When:** `win`

**Then:** the wave from the rim throws the crate onto the plate, and the gate latches. The mage then:
1. hooks the crate back to the rim;
2. grapples across on the pillar;
3. drags the crate into the lava.

### Example 4: Haul the crate and grapple across

**Given:** player `hook`, mage `lightningFlash`.

**When:** `win`

**Then:** the player drags the misted guard out of the doorway. The mage flashes onto the plate.
The player hooks the crate to the rim, grapples across on the pillar, and drags the crate in.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | No companion carries a plan alone | Every winning plan of the default kit has two or more companions acting. |
| P2 | Without a hook the crate cannot do both | With the crate on the plate (`fireball` + `blink`), the Warden cannot get across. |
| P3 | No single skill wins | Each pool skill held by both seats: no plan. |
| P4 | The measured assignments win | Exactly the 10 measured pairs win, both ways round; `combos` passes; no dead skill. |
| P5 | The mist lasts one cast | A fireball right after the mist drops the guard; after one more cast in between, it only scorches it. |
| P6 | Two pushers strand each other | `fireball` + `tidalWave` loses. |
