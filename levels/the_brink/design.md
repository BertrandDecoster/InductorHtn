# The Brink

## Purpose

A sibling of The Grease Trap on the core vocabulary, where the need comes from the enemy
instead of the ground. Nothing hurts the ogre or the bearer; both are `vulnerable(_, fall)`.
The level exists to show a ruleset whose every method is generic: the goal asks for the
enemy's weakness, a weakness names the ways to cause it, and each way is a composition of
needs (`bringTo`, `forceInto`, `castElement`) whose alternatives come from what the companions hold.

Two ways to make something fall:

- **Bring and push** - bring it, on foot, next to ground that drops away (the brink over the
  void), then force it in (a push or a pull).
- **Cut the floor** - bring it onto ground that some element turns into a drop (the rope
  bridge burns), and put that element down.

## Layer

level

## Dependencies

- `core/goals/exploit_weakness`

## World

```
ledge (far side) --- gate --- yard --- keep (ogre) --- bridge (rope) --- tower (bearer)
  :                            \        |                                 /
 void  . . . . . . . . . . . .  \------ brink (near side) ---------------/
```

- The void is reached one way from each side (`brink -> void`, `ledge -> void`) and is not a
  region: nobody walks into it or casts from it. A push from the near side sends something
  over; so does a pull from the far side.
- The rope bridge turns into the abyss under fire, once; whoever stands on it then falls.
- Movements, not skills: a **push** sends an NPC one region away from the caster, a **pull**
  brings it one region toward the caster, a **taunt** makes it follow the taunter one region.
  The bearer resists a push (`immune(bearer, push)`).
- What the skills do. Player (picks two): gust = push (unlimited), dash = taunt (one),
  ignite = fire (one), lightning and flare = nothing here. Warden: magnetize = pull (one).

## Hypothesis

Current, after round 6. The v1 hypothesis and every revision are in Iterations.

- F1: two ideas, *bring and push* and *cut the floor*. Every plan brings an enemy and then
  forces it or cuts under it; plans differ in the second step and in who does which half.
- The plan set, per kit, in movements:

  | Kit | Plans |
  |-----|-------|
  | push + fire (gust, ignite) | 2: ogre pushed onto the brink and over, bearer pulled onto the bridge and burned; or both brought onto the bridge, one fire |
  | push + taunt (gust, dash) | 1: ogre pushed over; bearer taunted onto the brink, pulled over from the far ledge |
  | taunt + fire (dash, ignite) | 1: ogre taunted onto the bridge, bearer pulled on, one fire |
  | the other 7 | none |

- F4: 3 of 10 kits win (0.3). No mandatory pick. Lightning and flare are the herrings.
- F6: no single-actor plan in any kit, not only the default one.
- Known and accepted:
  - Causal depth 2: the shape *is* two steps (bring, then force).
  - F2 fails for the default kit. Its two plans differ only in where the ogre is pushed (the
    brink or the bridge), and the ablation finds no fact only one of them needs. The kits'
    plans differ from each other far more than the default kit's two plans do.

## Iterations

(Each round: what I expected, what I saw, the one thing I changed.)

**Round 1 (v1).**
- Expected: 2 plans with the default kit; winning kits {gust, ignite} and {dash, ignite};
  ignite mandatory.
- Saw, before the fix: no plan at all. `defeat(bearer)` failed because the Warden's only
  vantage on the tower was three hops away, and core `navigate` walks two. I added
  `lineOfSight(keep, tower)`.
- Saw, after the fix: exactly the predicted 2 plans and 2/10 winning kits.
- Scorecard: F1 pass (2 classes). F2 warn (0.07: both plans burn the bearer on the bridge; only
  the ogre's route differs). F3 causal depth 2. F4 ignite mandatory, multi-use 1.33. F6 player
  load 0.71.
- Also seen: with {dash, ignite} one plan has the player taunt both enemies onto the bridge
  and burn it alone. The Warden stands idle, so that kit has a single-actor plan.
- Diagnosis: the bearer has one way to fall. And `bringAndPush` only accepted a *push* as the
  forced movement, while the spec is "any forced movement": the magnet's pull moves iron one
  region over just as the gust moves flesh.
- Change for round 2: **the bearer can be rung out too.** The final shove is any forced
  movement (push or pull), and the brink touches the tower.


**Round 2 (the bearer can be rung out too).**
- Expected: winning kits are gust + anything (4) and dash+ignite, so 5/10; no mandatory pick.
- Saw: exactly that. F1 now has 3 classes.
- But the plans show each companion soloing "its" enemy. The Warden rings the bearer out alone
  (magnet in, magnet over, unlimited). The player rings the ogre out alone (gust in, gust over).
  Scorecard: teamwork edge 0.14, multi-use 1.0, feasibility 0.5 (too forgiving). The
  dash+ignite solo is still there.
- Diagnosis: one companion can do both halves of a ring-out, because nothing limits a forced
  movement.
- Change for round 3: **the magnet is one pull** (`charge(warden, magnetize, m1)` instead of a
  signature). The bearer then needs a second pair of hands: a taunt to the brink and the
  magnet over, or the magnet onto the bridge and a fire.

**Round 3 (the magnet is one pull).**
- Expected: winning kits {gust, dash}, {gust, ignite}, {dash, ignite}, so 3/10; no mandatory
  pick; the Warden never rings the bearer out alone.
- Saw first: nothing changed. Core `lure` never paid for its skill (push and taunt do), so a
  one-charge magnet pulled forever. This was a bug in `core_aggro`. Fixed with a test
  (property P4, "a pull is paid for"); every core test and grease_trap still pass.
- Saw then: exactly the prediction. Feasibility 0.3, no mandatory pick, teamwork edge 0.21.
  Lightning and flare are dead herrings.
- F6 reads the default kit only, so it cannot see this: with {dash, ignite}, one plan has the
  player taunt both enemies onto the bridge and burn it alone. My sweep now flags
  single-actor plans in every kit.
- Change for round 4: **the dash is one charge** (`charge(player, dash, d1)`), like the magnet.
  A taunt then brings one enemy, not two.

**Round 4 (the dash is one charge).**
- Expected: the same 3 winning kits; plans per kit gust+dash 1, gust+ignite 2, dash+ignite 1;
  no single-actor plan in any kit.
- Saw: exactly that. Scorecard for the default kit: F1 pass (2 classes); F4 feasibility 0.3,
  no mandatory pick, lightning and flare dead, multi-use 1.33; F6 teamwork edge 0.21, player
  load 0.65.
- What is left, and why I stop here:
  - causal depth 2 is the design (bring, then force);
  - low F2 distance comes from the shared burn in the default kit;
  - the herrings are herrings.
  The next judge is play: over MCP, then the user.

**Round 5 (movements and tags, not skills - a core change).**
- User feedback: think in terms of the movements and tags a skill does, not the skill itself.
- Change in core: a push sends an NPC one region *away* from the caster and a pull brings it
  one region *toward* the caster (`aims`, `takeAim` in core_world). What resists a movement is
  a fact on the NPC, `immune(?e, push | pull | dash)`, instead of the hard-coded
  `metal(?e)`. In this level the bearer is `immune(bearer, push)`. Grease trap now declares
  `immune(bearer, push)` and `immune(swarm, pull)`. All core tests and grease_trap pass; its
  composite went from 0.81 to 0.80 (the player walks to the right side before a push).
- Expected: gust+dash stops winning. Its bearer ring-out was a pull into the void cast from the
  gate, which is not a pull; nobody stands beyond the void.
- Saw: exactly that. 2/10 kits win ({gust, ignite} 2 plans, {dash, ignite} 1), and ignite is
  mandatory again.
- Change for round 6: **a far ledge across the void from the brink.** A push sends something
  over from the near side, a pull from the far side. The bearer, which resists a push, can be
  rung out again, but only by two companions: one taunts it onto the brink, the other pulls
  from the ledge.

**Round 6 (a far ledge across the void).**
- Expected: the round-4 plan set with the new physics. Push + taunt wins again, because the
  pull now comes from the ledge: 1/2/1 plans, 3/10 kits, no single-actor plan.
- Saw: exactly that.
- Scorecard: F4 feasibility 0.3, no mandatory pick, multi-use 1.0. F6 teamwork edge 0.21.
- F2 flipped from WARN to FAIL. Both default-kit plans now push the ogre from inside the keep,
  so no fact is critical to only one of them.
- Level P3 changed from "the magnet does not move flesh", no longer true, to "the bearer resists
  a push".

## Examples

### Example 1: Rung out, then burned

**Given:** the level as declared (default kit: `gust`, `ignite`).

**When:** `clearTheBrink`

**Then:** some plan contains `opPush(player, ogre, keep, brink)`, `opPush(player, ogre, brink, void)`, `opLure(warden, bearer, tower, bridge)`, `opCastRegion(player, ignite, bridge, rope, abyss)`.

### Example 2: One burn takes both

**Given:** the level as declared.

**When:** `clearTheBrink`

**Then:** some plan contains `opPush(player, ogre, keep, bridge)`, `opLure(warden, bearer, tower, bridge)`, `opCastRegion(player, ignite, bridge, rope, abyss)`; after the plan, both the ogre and the bearer are `fallen`.

### Example 3: Taunted to the edge, pulled from the far side

**Given:** the kit `gust`, `dash`.

**When:** `clearTheBrink`

**Then:** the one plan contains `opTaunt(player, bearer, tower, brink)`, `opNavigate(warden, gate, ledge)`, `opLure(warden, bearer, brink, void)`: the pull comes from the far side.

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | The plan set is the stated one | Over all ten kits: gust+ignite 2 plans, gust+dash 1, dash+ignite 1, every other kit none. |
| P2 | No companion carries a plan alone | In every kit, every plan has operators by both the player and the Warden. |
| P3 | The bearer resists a push | `push(bearer, bridge)` has no plan: it is `immune(bearer, push)`. |
