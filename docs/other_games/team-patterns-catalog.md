# Team Coordination Patterns Catalog
A cross-game vocabulary of team "beats", each translated into an HTN method/operator sketch.

This is the primary deliverable of `docs/other_games/`. It mines top-tier strategy guides for
the recurring *coordination problems* teams face in great team-based games, and maps each
proven solution onto this engine's grammar: an **operator** is a discrete game action a
low-level controller (FSM / behavior tree / RL policy) plays out, and a **method** decides
*which* operators to chain and *when* via its `if()` preconditions.

> **Status of the code blocks.** The `prolog` sketches are *illustrative* — shaped to match the
> repo's method/operator syntax and to reuse existing component predicates, but not guaranteed
> to compile. They are a starting point for real rulesets, not drop-in code. See
> [`../reference/ruleset-htn-syntax.md`](../reference/ruleset-htn-syntax.md) for the exact grammar.

## Companion references
- [`../reference/ruleset-htn-syntax.md`](../reference/ruleset-htn-syntax.md) — method/operator/modifier syntax
- [`../reference/ruleset-writing.md`](../reference/ruleset-writing.md) — how to grow a ruleset from a domain
- [`../upgrades/ruleset-keywords.md`](../upgrades/ruleset-keywords.md) — the `parallel()` keyword used below
- `../../components/primitives/aggro/src.htn` — `getAggro`, `loseAggro`, `enemyFollows`, `lureToRoom`
- `../../components/primitives/locomotion/src.htn` — `moveTo`, `opMoveTo`, `canReach`
- `../../Examples/GameHack7Combined.htn` — multi-ally skill combos, `opSynchronize`, aggro herding

## How to read this catalog

The recurring shape across every verified tactic is:

> A fixed **role-assignment template** sets up *who* acts; then per-mechanic **preconditions**
> — debuff stack counts, status-buildup thresholds, target-priority conditions, spawn events,
> weakened-state flags — gate *which* discrete action fires and *when*.

That is exactly HTN. So each pattern below is presented as:

1. **Problem** — stated crisply.
2. **What the guides prescribe** — concrete, cited tactics from real strategy resources.
3. **Actions → operators / Decisions → preconditions** — the decomposition.
4. **HTN sketch** — `prolog` reusing repo idioms.

Confidence is flagged per pattern. See [Confidence & coverage](#confidence--coverage) at the end
for what is well-sourced versus thin. Per-game evidence lives in [`games/`](games/).

> **This is not a metaphor — it is how shipped games build squad AI.** Primary industry and
> academic sources describe exactly this structure. *Killzone 3*'s multiplayer bots use an HTN whose
> `DefendMarker` method **branches on character class** — the engineer branch decomposes to "move
> there, place a turret nearby", the tactician branch to "move there, call in a sentry drone" — and
> whose method branches are "tried in listed order and selected by precondition match, with priority
> encoded by ordering" (so a self-preservation branch sits before a heal-friendly branch, and a medic
> aborts a revive to flee a grenade on replan).
> [[Killzone 3 / Game AI Pro ch.29](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter29_Hierarchical_AI_for_Multiplayer_Bots_in_Killzone_3.pdf)]
> Domination bots in *Unreal Tournament* likewise let "the HTN decomposition process decide which bot
> gets activated" for each primitive task, recapturing a point "only if it has been recaptured by the
> enemy; otherwise continue searching".
> [[Hoang et al.](https://link.springer.com/chapter/10.1007/11780519_49)]
> Guerrilla Games ships HTN planning in its Decima engine. The patterns below are the *game-design*
> vocabulary that feeds this *engine* vocabulary.

---

## Problem 1 — Role / responsibility assignment

**Problem.** Before any mechanic can be handled, every agent needs a job. Who tanks, who heals,
who does damage; in class-based co-op, who fills which class niche. Get the *counts* wrong and
later beats become unsatisfiable.

**What the guides prescribe.**
- WoW Mythic raids publish exact compositions — e.g. Mythic Volcoross is **2 tanks / 4 healers /
  14 DPS**, summing to the 20-player cap ([Method.gg](https://www.method.gg/guides/amirdrassil-the-dreams-hope/volcoross)).
- Deep Rock Galactic hard-assigns each of four classes a role: Scout = light + high minerals,
  Gunner = safety + sustained damage, Engineer = area control + platforms, Driller = terrain +
  crowd clear ([jeu.video](https://jeu.video/en/guide/deep-rock-galactic-classes-coop-en)).
- Overcooked teams allocate specific jobs, or distinct kitchen *zones* per chef, to minimize
  multitasking ([GameRant](https://gamerant.com/overcooked-2-how-to-get-four-stars/)).
- Helldivers 2 Difficulty-10 squads split into four roles — Anti-Tank, Crowd Control, Saboteur,
  Support/Medic — because "teams that assign roles perform significantly better than those that try
  to do everything individually"
  ([2upskill](https://2upskill.com/helldivers-2-super-helldive-meta-guide-2026-best-stratagems-and-loadouts-for-difficulty-10/)).
- Deep Rock Galactic *stationary-objective* missions split the team between **doing the task** and
  **holding the ground** — e.g. Salvage Operation: reattach Mini-MULE legs, establish the Uplink,
  refuel the Drop Pod *while surviving*
  ([DRG Fandom](https://deeprockgalactic.fandom.com/wiki/How_to_Play_Guide_for_Deep_Rock_Galactic)).

**Actions → operators / Decisions → preconditions.** Assignment is a one-time bind producing
`role(?agent, ?token)` facts. The decision point is the composition constraint (counts / raid
size). Every downstream beat then gates on `role(?a, ...)`.

**HTN sketch.**
```prolog
% Role tokens are facts the assignment step produces: role(agent1, tank). role(agent2, healer). ...
% A composition is valid only when the prescribed counts are present.
% (countRole/2 is a domain helper — aggregate counting; see note below.)
assembleTeam() :-
    if(countRole(tank, ?nt),   >=(?nt, 2),
       countRole(healer, ?nh), >=(?nh, 4),
       countRole(dps, ?nd),    >=(?nd, 14)),
    do(beginEncounter()).

% Class-based variant (Deep Rock): role tokens drive which jobs an agent may take.
mineHighMinerals(?node) :- if(role(?a, scout), free(?a)), do(opMine(?a, ?node)).
holdChokepoint(?gate)  :- if(role(?a, gunner), free(?a)), do(opSuppress(?a, ?gate)).

% A single method branching on role to dispatch a different operator — the Killzone 3
% DefendMarker shape (engineer places a turret; tactician calls a drone; otherwise scan).
defendMarker(?m) :- if(role(?a, engineer)), do(moveTo(?a, ?m), opPlaceTurret(?a, ?m)).
defendMarker(?m) :- else, if(role(?a, tactician)), do(moveTo(?a, ?m), opCallDrone(?a, ?m)).
defendMarker(?m) :- else, if(role(?a, ?any)), do(moveTo(?a, ?m), opScan(?a, ?m)).

% Defend-while-task split (Deep Rock stationary objectives): one agent works, one holds.
salvageOperation() :-
    if(role(?worker, ?rw), free(?worker), role(?guard, ?rg), free(?guard), \==(?worker, ?guard)),
    do(parallel(doObjective(?worker), defendArea(?guard))).
```
> **Note.** Count constraints (`countRole/2`) need an aggregate; InductorHTN has no built-in
> `findall`, so model counts as domain facts maintained by the assignment step, or enforce the
> minimum structurally (e.g. an `allOf` over the agents that should hold each role). The role
> *token* itself — `role(?a, tank)` — is the part that matters downstream, and it's a plain fact.

Exemplified by: [WoW raids](games/wow-raids.md), [Deep Rock Galactic](games/deep-rock-galactic.md),
[Overcooked](games/overcooked.md), [Helldivers 2](games/helldivers-2.md). Prior art: Killzone 3
`DefendMarker` ([Game AI Pro ch.29](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter29_Hierarchical_AI_for_Multiplayer_Bots_in_Killzone_3.pdf)).

---

## Problem 2 — Threat & aggro management

**Problem.** A boss attacks whoever holds aggro. Hold it on one tank too long and a stacking
debuff kills them; transfer it badly and the boss repositions or cleaves the raid.

**What the guides prescribe.** WoW's tank-swap is the canonical threshold-driven beat
([Icy Veins tanking](https://www.icy-veins.com/wow/tanking-guide),
[Salhadaar](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide)):
- A **taunt** forces the target onto the taunter for a fixed ~6s and equalizes the taunter's
  threat to the current holder's — a discrete *aggro-transfer* action.
- Swap is triggered by a **stack count**: Destabilizing Strikes applies on every auto-attack;
  **swap at ~8 stacks**.
- Correct execution: the incoming tank pre-positions in *exactly* the current tank's spot (so the
  boss doesn't move), times a high-threat ability to land immediately after the taunt, and the
  outgoing tank *stops* high-threat abilities for a few seconds to let aggro stabilize.

**Actions → operators / Decisions → preconditions.** Operators: `opTaunt` (transfer),
`opHighThreat`, `moveTo` (position), `opStopThreat`. Decisions: stack count ≥ threshold, who
currently holds aggro, am-I-incoming-vs-outgoing.

**HTN sketch.** Reuses the `hasAggro/2` fact shape from `components/primitives/aggro` (generalized
here from `hasAggro(?enemy, player)` to a named tank) and `moveTo` from `locomotion`.
```prolog
% Fluents: stacks(destabilizing, ?tank, ?n).  Aggro: hasAggro(?boss, ?tank).
tankSwap(?boss) :-
    if(hasAggro(?boss, ?current),
       stacks(destabilizing, ?current, ?n), >=(?n, 8),     % threshold decision
       role(?incoming, tank), \==(?incoming, ?current),
       at(?current, ?spot)),
    do(moveTo(?incoming, ?spot),        % stand exactly where the current tank stands
       opTaunt(?incoming, ?boss),       % aggro transfer (6s forced window)
       opHighThreat(?incoming, ?boss),  % land immediately after the taunt
       opStopThreat(?current)).         % outgoing tank backs off threat to let it settle

opTaunt(?tank, ?boss) :-
    del(hasAggro(?boss, ?old)),
    add(hasAggro(?boss, ?tank)).
```
> The ~8 stacks and 6s figures are *tunable parameters*, not constants — they change per
> encounter and per patch. Treat threshold numbers as domain facts, not hard-coded literals.

Exemplified by: [WoW raids](games/wow-raids.md). Related repo idiom: `lureToRoom` /
`enemyFollows` in `components/primitives/aggro/src.htn`.

---

## Problem 3 — Focus fire / target prioritization

**Problem.** Spread damage across many targets and nothing dies in time. The team must agree on a
single target, and re-prioritize the instant a higher-priority target appears.

**What the guides prescribe.**
- WoW Salhadaar: **Concentrated Void orbs are top priority** — "DPS should swap to these ASAP",
  because if an orb reaches the boss it buffs it and wipes the raid. (Refinement: killing an orb
  applies a stacking raid-wide DoT, so stagger kills between two orbs.)
  ([Icy Veins](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide))
- Left 4 Dead 2 inverts this for the *attacker*: a Hunter is given an explicit list of favorable
  pounce situations — caught in a horde, saving a pinned ally is impossible, a survivor is >10s
  from the group, awkward ladder/stair angles, a lone survivor holed up.
  ([StrategyWiki](https://strategywiki.org/wiki/Left_4_Dead_2/Infected))

**Actions → operators / Decisions → preconditions.** Operator: `opAttack` / `opPounce`.
Decision: a higher-priority target exists (an add spawned), or the target satisfies a priority
condition. This is the canonical "do X when condition Y" branch, expressed as an `else` ladder.

**HTN sketch.**
```prolog
% Priority ladder: a spawned high-threat add pre-empts boss damage.
dealDamage(?boss) :-
    if(spawned(?orb), threat(?orb, high)),
    do(focusFire(?orb)).
dealDamage(?boss) :-
    else, if(),
    do(focusFire(?boss)).

% Every DPS converges on the single called target (allOf = act for every binding).
focusFire(?target) :- allOf, if(role(?a, dps)), do(opAttack(?a, ?target)).

% Attacker-side priority list (L4D Hunter) as an ordered else ladder:
shouldPounce(?survivor) :- if(inHorde(?survivor)),            do(opPounce(?survivor)).
shouldPounce(?survivor) :- else, if(isolated(?survivor, 10)), do(opPounce(?survivor)).
shouldPounce(?survivor) :- else, if(holedUpAlone(?survivor)), do(opPounce(?survivor)).
```

Exemplified by: [WoW raids](games/wow-raids.md), [Left 4 Dead](games/left-4-dead.md).

---

## Problem 4 — Positioning & formation

**Problem.** Many actions are only *safe* in the right place: spread effects must clear allies,
soak zones must not overlap, and the team must not let a member straggle into a pin.

**What the guides prescribe.**
- WoW Salhadaar: a player hit by **Despotic Command** pulses AoE onto nearby allies and must
  **run to the room edge** before being dispelled.
  ([Icy Veins](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide))
- WoW Volcoross: **soak circles must not overlap** or a wipe triggers
  ([Method.gg](https://www.method.gg/guides/amirdrassil-the-dreams-hope/volcoross)).
- L4D2: survivors must **stick together** because stragglers are prime pin targets; the Smoker's
  explicit role is to **drag a member away** to break formation
  ([StrategyWiki](https://strategywiki.org/wiki/Left_4_Dead_2/Infected)).
- Helldivers 2: place sentries "far off to one side … away from your squad to create a crossfire"
  so they hit the enemy's weaker rear while the enemy focuses the players
  ([zleague](https://www.zleague.gg/theportal/helldivers-2-sentry-guide/)); and a reinforced
  player's drop pod is "limited to an area around the beacon that calls it" — *where the revive lands
  is chosen by beacon placement* ([Helldivers Wiki](https://helldivers.wiki.gg/wiki/Reinforce)).
- Deep Rock: the Scout lights swarm approach lanes — "during a swarm, make sure EVERYTHING is well
  lit, including where a swarm could come from"
  ([Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2950418160)).

**Actions → operators / Decisions → preconditions.** Operators: `moveTo`, `opSoak`,
`opStayWithGroup`, `opPlaceSentry`, `opThrowBeacon`, `opDeployFlare`. Decisions:
am-I-carrying-a-spread-effect, is-the-target-zone-clear, is-a-teammate-straggling,
is-the-sentry-arc-clear-of-allies, is-the-beacon-drop-safe.

**HTN sketch.** `moveTo` is from `locomotion`. **Herding a mob to a spot already exists** as
`lureToRoom` in `components/primitives/aggro` — reuse it rather than re-authoring.
```prolog
% Spread debuff: clear allies before the dispel can land (see Problem 7).
handleSpreadDebuff(?a) :-
    if(debuffed(?a, despotic), at(?a, ?room), edge(?edge, ?room)),
    do(moveTo(?a, ?edge), requestDispel(?a)).

% Soak with a no-overlap guard (the safety half lives in Problem 11).
assignSoak(?a, ?circle) :-
    if(role(?a, dps), free(?a), not(occupied(?circle))),
    do(opMoveToCircle(?a, ?circle), opMarkOccupied(?circle)).
```

Exemplified by: [WoW raids](games/wow-raids.md), [Left 4 Dead](games/left-4-dead.md),
[Helldivers 2](games/helldivers-2.md), [Deep Rock Galactic](games/deep-rock-galactic.md).

---

## Problem 5 — Timing & synchronization

**Problem.** Some beats only work if N agents act *simultaneously*, or within a fixed time window
opened by another action.

**What the guides prescribe.**
- WoW Volcoross Coiling Eruption needs **at least 2 players per soak circle at the same time** —
  a quantified minimum-agents-per-task constraint
  ([Method.gg](https://www.method.gg/guides/amirdrassil-the-dreams-hope/volcoross)).
- Monster Hunter Shock Trap immobilizes a monster for a fixed **7.5s (10s on a 3-star paralysis
  weakness)** — a known window to act on a now-stationary target
  ([Fextralife](https://monsterhunterworld.wiki.fextralife.com/Shock+Trap)).

**Actions → operators / Decisions → preconditions.** Operators: `opSoak`, `opBurstAttack`.
Decisions: enough free agents to meet the minimum, trap-active timer > 0, target-is-stationary.
This is where the repo's [`parallel()`](../upgrades/ruleset-keywords.md) keyword earns its keep.

**HTN sketch.**
```prolog
% Coiling Eruption: two distinct soakers act concurrently on one circle.
soakEruption(?circle) :-
    if(role(?a1, dps), free(?a1),
       role(?a2, dps), free(?a2), \==(?a1, ?a2)),
    do(parallel(opSoak(?a1, ?circle), opSoak(?a2, ?circle))).

% Trap window: burst while the immobilize timer still has ticks left.
exploitTrap(?monster) :-
    if(trapped(?monster, ?ticksLeft), >(?ticksLeft, 0)),
    do(opBurstAttack(?monster)).
```

Exemplified by: [WoW raids](games/wow-raids.md), [Monster Hunter](games/monster-hunter.md).
Related repo idiom: `opSynchronize` in `Examples/GameHack7Combined.htn`.

---

## Problem 6 — Crowd-control chaining & CC economy

**Problem.** Statuses (stun, sleep, paralysis, poison) are a *budget*, not a free resource:
repeated application of the same status gets harder, so the team must spend it deliberately.

**What the guides prescribe.** Monster Hunter is the cleanest model
([Fextralife MHW](https://monsterhunterworld.wiki.fextralife.com/Status+Effects),
[MH Wilds](https://monsterhunterwilds.wiki.fextralife.com/Status+Effects)):
- Each ailment has a **per-monster buildup threshold**; the status procs only when accumulated
  buildup crosses it. (Note: elemental *Blights* cannot affect monsters — only Poison, Sleep,
  Paralysis, Blast, Stun.)
- Critically, the threshold **roughly doubles after each proc** — a concrete diminishing-returns /
  CC-economy mechanic.

**Actions → operators / Decisions → preconditions.** Operator: `opStatusHit(type)` (adds buildup).
Decisions: accumulated buildup ≥ current threshold (proc fires); threshold grows ~2× per prior
proc (track remaining CC budget before re-applying).

**HTN sketch.** This maps beautifully onto the repo's numeric-fluent sugar (`increase`/`decrease`,
see [ruleset-htn-syntax.md](../reference/ruleset-htn-syntax.md)) and extends the `tags` component's idea of
applying status.
```prolog
% Fluents: buildup(?monster, ?status, ?b).  threshold(?monster, ?status, ?t).
% Below threshold: a hit just accumulates buildup, no proc yet.
applyStatus(?monster, ?status) :-
    if(buildup(?monster, ?status, ?b),
       threshold(?monster, ?status, ?t), <(?b, ?t)),
    do(opStatusHit(?monster, ?status)).

% At/over threshold: it procs — apply the CC, reset buildup, and double the threshold.
applyStatus(?monster, ?status) :-
    else, if(buildup(?monster, ?status, ?b),
             threshold(?monster, ?status, ?t), >=(?b, ?t)),
    do(opProcStatus(?monster, ?status, ?b, ?t)).

opStatusHit(?monster, ?status) :- increase(buildup(?monster, ?status), 10).

% Adding the current threshold value (?t) to itself doubles it — the diminishing return.
opProcStatus(?monster, ?status, ?b, ?t) :-
    decrease(buildup(?monster, ?status), ?b),       % reset accumulated buildup to 0
    increase(threshold(?monster, ?status), ?t),     % ~2x: next proc costs more
    add(afflicted(?monster, ?status)).
```
> "Doubles" is *roughly/often*, not a hard universal 2×; treat the growth factor as a domain
> parameter. Blademaster hits also only have ~⅓ chance to contribute buildup — model probabilistic
> contribution at the controller layer, not in the plan.

**Adjacent CC-coordination tactics.** Beyond the per-target *economy*, two more team CC beats showed
up: Helldivers 2 layers CC *then* damage — "an EMS Mortar Sentry can slow down a horde of bots,
making them easy targets for a Gatling or Autocannon Sentry"
([zleague](https://www.zleague.gg/theportal/helldivers-2-sentry-guide/)); and Deep Rock's Engineer
"can completely seal a tunnel shut using platforms … to block off an angle of attack" during a swarm
— *area denial* as crowd control
([DRG Wiki](https://deeprockgalactic.wiki.gg/wiki/Tips,_tricks_and_strategies)).
```prolog
% Slow the horde, then a damage sentry mops up the immobilized targets.
ccThenDamage(?horde) :-
    if(sentry(?ems, emsMortar), ready(?ems), sentry(?dmg, gatling)),
    do(opFireEMS(?ems, ?horde), opFireSentry(?dmg, ?horde)).
```

Exemplified by: [Monster Hunter](games/monster-hunter.md), [Helldivers 2](games/helldivers-2.md),
[Deep Rock Galactic](games/deep-rock-galactic.md). Related repo idiom:
`components/primitives/tags/src.htn` (status application), `Examples/GameHack7Combined.htn`
(stun + slow two-ally combo).

---

## Problem 7 — Resource / cooldown economy

**Problem.** Shared or consumable team resources (reinforcement tickets, resupply charges, dispels,
defensive cooldowns) must be *spent* at the right moment by the right person — not reflexively, and
not wastefully.

**What the guides prescribe.** This pattern has two flavours, both well-sourced.

*Shared finite pools* with quantified rules:
- Helldivers 2 reinforcements are **five tickets per player, up to 20 per squad**; exhausting them
  all with the objective incomplete **fails the mission**
  ([Helldivers Wiki](https://helldivers.wiki.gg/wiki/Reinforce)).
- Deep Rock resupply costs **80 Nitra** for a pod of **four racks**, each restoring 50% ammo + half
  health; benefits "cannot be stored or transferred" and can't overfill — so the rule is *take a
  rack only when below ~50%*, or you waste the shared pool
  ([DRG Wiki](https://deeprockgalactic.wiki.gg/wiki/Resupply_Pod)).

*Timing-gated consumables*:
- WoW healers **hold the dispel** on Despotic Command until the player has repositioned, then dispel
  *and* remove the attached heal-absorb
  ([Icy Veins](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide)).

**Actions → operators / Decisions → preconditions.** Operators: `opReinforce`, `opTakeRack`,
`opOrderPod`, `opDispel`. Decisions: is the pool non-empty (`tickets > 0`, `racksLeft > 0`); is *this*
agent actually low (`ammo < 50%`); is the team able to afford ordering (`nitra >= 80`); is the
consumable's positioning gate satisfied. The shared pool is a numeric fluent the operator decrements.

**HTN sketch.**
```prolog
% Take from a shared pool only when genuinely low (don't waste a rack topping off).
takeResupply(?dwarf, ?pod) :-
    if(ammo(?dwarf, ?a), <(?a, 50), racksLeft(?pod, ?r), >(?r, 0)),
    do(opTakeRack(?dwarf, ?pod)).
opTakeRack(?dwarf, ?pod) :- decrease(racksLeft(?pod), 1), increase(ammo(?dwarf), 50).

% Spend a shared reinforcement ticket only when the pool isn't empty.
reinforce(?deadAlly) :-
    if(dead(?deadAlly), tickets(squad, ?n), >(?n, 0), safeBeacon(?spot)),
    do(opThrowBeacon(?caller, ?spot), opReinforce(?deadAlly, ?spot)).
opReinforce(?ally, ?spot) :- decrease(tickets(squad), 1), del(dead(?ally)), add(at(?ally, ?spot)).

% Timing-gated consumable: hold the dispel until the target is clear of allies.
manageDispel(?a) :-
    if(debuffed(?a, despotic), clearOfAllies(?a), ready(?healer, dispel)),
    do(opDispel(?healer, ?a), opRemoveAbsorb(?healer, ?a)).
```
> The numeric fluent sugar (`decrease(tickets(squad), 1)`) models a shared pool naturally — the same
> fact is decremented by whichever agent spends from it. Pool sizes (20 tickets, 4 racks, the ~50%
> rule of thumb) are tunable domain parameters.

Exemplified by: [Helldivers 2](games/helldivers-2.md),
[Deep Rock Galactic](games/deep-rock-galactic.md), [WoW raids](games/wow-raids.md).

---

## Problem 8 — Throughput / task pipelining

**Problem.** When the team is a production line, the bottleneck is coordination: idle hands,
clogged stations, and long tasks that stall everything behind them.

**What the guides prescribe.** Overcooked is the canonical model
([GameRant](https://gamerant.com/overcooked-2-how-to-get-four-stars/), corroborated by multiple
independent guides):
- **Parallel prep**: one chef batch-produces staged components (plates with buns/toppings, pizza
  crusts, salad plates) *ahead of orders* while another cooks protein.
- **Dedicate a chef to long-running tasks** (mixing, baking, dishwashing) while others handle short
  tasks, keeping the assembly line unclogged.

**Actions → operators / Decisions → preconditions.** Operators: `opPrep`, `opCook`,
`opStartTask`/`opMonitor`. Decisions: a long-running task is in progress *and* a chef is free to
own it; staged components are below a buffer threshold (produce-ahead trigger).

**HTN sketch.** Uses [`parallel()`](../upgrades/ruleset-keywords.md) for the concurrent prep/cook.
```prolog
serveOrders() :-
    if(),
    do(parallel(prepComponents, cookProtein), assemble, plate).

% Dedicate one free chef to a long-running task and let them own it to completion.
ownLongTask(?task) :-
    if(longRunning(?task), role(?c, chef), free(?c)),
    do(opStartTask(?c, ?task), opMonitor(?c, ?task)).

% Produce-ahead: top up a staged component buffer when it runs low.
stageAhead(?component) :-
    if(staged(?component, ?n), <(?n, 3), role(?c, chef), free(?c)),
    do(opPrep(?c, ?component)).
```

**Traversal as throughput (Deep Rock).** A related throughput beat is *cutting the path itself*:
"you can drill your whole team safely back to the drop pod, which often makes it there quicker than
Molly", and "during extraction phases, the Driller can also create long tunnels to the Drop Pod"
([Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2950418160),
[DRG Wiki](https://deeprockgalactic.wiki.gg/wiki/Tips,_tricks_and_strategies)).
```prolog
% Shortcut the whole team to the pod when extraction is called (faster than the default escort).
regroupToPod() :- if(extractionCalled, role(?d, driller)), do(opDrillTunnel(?d, dropPod)).
```

Exemplified by: [Overcooked](games/overcooked.md), [Deep Rock Galactic](games/deep-rock-galactic.md).
Related repo idiom: the `parallel()` worked example in
[`../upgrades/ruleset-keywords.md`](../upgrades/ruleset-keywords.md).

---

## Problem 9 — Phase / state transitions *(medium confidence)*

**Problem.** The plan must adapt when the world changes state mid-encounter: an add spawns, a boss
hits a new phase, a crescendo event starts.

**What the guides prescribe.** The strongest verified instance is *event-driven re-prioritization*:
in WoW Salhadaar, a Concentrated Void orb spawning forces DPS to abandon the boss — a higher-priority
sub-method pre-empts the default
([Icy Veins](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide)). An explicit
*named multi-phase timeline* (e.g. the L4D AI Director crescendo/finale model, FFXIV phase markers)
**did not survive verification** and is an open question.

**Actions → operators / Decisions → preconditions.** The spawn/phase event is a precondition that
activates a higher-priority method, expressed as an `else` ladder ordered most-urgent-first.

**HTN sketch.**
```prolog
encounterBeat(?boss) :-
    if(spawned(?orb)),                 % event-driven preemption — clear adds first
    do(clearAdds(?boss)).
encounterBeat(?boss) :-
    else, if(phase(?boss, ?p)),        % otherwise run the current phase's default tactic
    do(phaseTactic(?boss, ?p)).
```
> Where a true phase timeline exists, re-bind roles and swap sub-methods on the transition (a
> `phase(?boss, ?p)` fact updated by an operator). The verified set only firmly supports the
> spawn-event flavor; treat named multi-phase timelines as a design extension, not a sourced pattern.

Exemplified by: [WoW raids](games/wow-raids.md). See [open questions](games/coverage-gaps.md).

---

## Problem 10 — Recovery & failure handling

**Problem.** When a member is downed or pinned, the team must drop its current plan and execute a
*rescue* — and the rescue depends on *how* they were caught.

**What the guides prescribe.** L4D2 pin-and-rescue is the core PvE recovery loop
([StrategyWiki](https://strategywiki.org/wiki/Left_4_Dead_2/Infected)):
- Special Infected pins (Smoker tongue, Hunter pounce, Jockey ride, Charger pummel) leave a
  survivor helpless and **unable to self-rescue after a short grip** — a teammate must free them.
- The freeing action is **type-dependent**: melee/shove the attacker, kill it, or melee the trapped
  ally — **except the Charger, which is melee-immune** and must be killed or frag/explosive-stunned.

**Actions → operators / Decisions → preconditions.** Operators: `opKill`, `opShove`,
`opMeleePinned`. Decision: a teammate is pinned *and* the attacker's type — the textbook branch.

**HTN sketch.** The type branch is a natural `else` ladder.
```prolog
% Charger is the exception: shove/melee won't work — it must be killed.
rescue(?ally) :-
    if(pinnedBy(?ally, ?attacker), type(?attacker, charger),
       role(?r, dps), free(?r)),
    do(opKill(?r, ?attacker)).
% Generic pin: shoving/meleeing the attacker frees the ally.
rescue(?ally) :-
    else, if(pinnedBy(?ally, ?attacker), role(?r, dps), free(?r)),
    do(opShove(?r, ?attacker)).
```

**Revive under fire (protect-then-rescue).** Two co-op games gate the *revive* on first making it
safe. Deep Rock's Gunner "throw[s] your shield over downed dwarves for the safest possible revive
amidst a swarm" — shield first, then revive
([Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2950418160)). Helldivers 2
reinforces a dead teammate by throwing a beacon that lands a drop pod (the revive's position is the
beacon's position) ([Helldivers Wiki](https://helldivers.wiki.gg/wiki/Reinforce)).
```prolog
% Make the revive safe before performing it.
safeRevive(?down) :-
    if(downed(?down), swarmActive, role(?g, gunner), ready(?g, shield)),
    do(opThrowShield(?g, ?down), opRevive(?g, ?down)).
```

Exemplified by: [Left 4 Dead](games/left-4-dead.md), [Deep Rock Galactic](games/deep-rock-galactic.md),
[Helldivers 2](games/helldivers-2.md).

---

## Problem 11 — Safety constraints

**Problem.** Some states are *forbidden*: two players on the same soak, friendly fire, standing in
a hazard. These are hard "do-not" rules that gate otherwise-valid actions.

**What the guides prescribe.**
- WoW Volcoross: **soak circles must not overlap** (else wipe)
  ([Method.gg](https://www.method.gg/guides/amirdrassil-the-dreams-hope/volcoross)).
- WoW Salhadaar: a Despotic Command player **pulses AoE onto nearby allies** — clear the group
  first ([Icy Veins](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide)).
- L4D attackers *exploit* safety gaps: a Boomer's vision obstruction (~20–25s) lets Hunters/Smokers
  strike undetected, and a Jockey can steer a ridden survivor into a Spitter acid patch — a designed
  hazard combo ([StrategyWiki](https://strategywiki.org/wiki/Left_4_Dead_2/Infected)).
- Helldivers 2 treats friendly fire as a hard constraint: sentry placement "must be called out … so
  they know which angles are covered", and the reinforcement drop pod "squashes enemies and allies
  alike" — so a beacon must land clear of teammates
  ([zleague](https://www.zleague.gg/theportal/helldivers-2-sentry-guide/),
  [Helldivers Wiki](https://helldivers.wiki.gg/wiki/Reinforce)).
- Deep Rock turns geometry into safety: attaching to a zipline before landing takes **zero fall
  damage** "no matter the height or velocity", and a sealed-platform tunnel denies a swarm an angle
  ([Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2950418160),
  [DRG Wiki](https://deeprockgalactic.wiki.gg/wiki/Tips,_tricks_and_strategies)).

**Actions → operators / Decisions → preconditions.** The pattern is uniform: gate the action on
`not(forbidden_condition)`. Safety is a *precondition*, not a separate action.

**HTN sketch.**
```prolog
% Soak only an unoccupied zone (no-overlap safety).
soakSafe(?a, ?circle) :-
    if(role(?a, dps), free(?a), not(occupied(?circle))),
    do(opSoak(?a, ?circle)).

% Friendly-fire guard: never fire an explosive when an ally is near the target.
fireExplosive(?a, ?target) :-
    if(weapon(?a, explosive), not(allyNear(?target))),
    do(opFire(?a, ?target)).

% Helldivers sentry: only place when its firing arc is clear of allies, then broadcast the lane.
placeSentry(?s, ?lane) :-
    if(flankLane(?lane), behindCover(?lane), not(allyInArc(?lane))),
    do(opPlaceSentry(?s, ?lane), opBroadcastArc(?s, ?lane)).
```

Exemplified by: [WoW raids](games/wow-raids.md), [Left 4 Dead](games/left-4-dead.md),
[Helldivers 2](games/helldivers-2.md), [Deep Rock Galactic](games/deep-rock-galactic.md).

---

## Confidence & coverage

This catalog is built from adversarially-verified strategy guides across **two research passes**
(pass 1: 23/25 claims confirmed; pass 2 on Helldivers 2 + Deep Rock: 21/25 confirmed). Coverage is
**deliberately uneven** and reflects where verifiable, prescriptive material actually exists:

| Coverage | Games | Patterns best supported |
|----------|-------|--------------------------|
| **Strong** | WoW raids, Monster Hunter World, Left 4 Dead 2, Overcooked 2 | 1, 2, 3, 4, 5, 6, 8, 10, 11 |
| **Good** (pass 2) | Helldivers 2, Deep Rock Galactic | 1, 4, 6, 7, 8, 10, 11 |
| **Medium / single-source** | — | 9 (phase transitions) |
| **Absent (requested, unverified)** | Dota 2 / LoL, Overwatch, FFXIV | — |

The second pass also confirmed a cluster of **primary** industry/academic sources (Killzone 3
multiplayer bots, Unreal Tournament domination bots, Guerrilla's HTN-in-Decima) showing this exact
method/operator structure is how shipped games build squad AI — see the note under
[How to read this catalog](#how-to-read-this-catalog). It **upgraded Pattern 7** (resource economy)
out of "medium" by adding Deep Rock's resupply pool and Helldivers' reinforcement pool.

**Refuted claims** (do not model these):
- A DRG Engineer-platform → Scout-mining *pipelined dependency* (0-3). Pass 2 clarified the real
  relationship: the platform is an **optional fall-safety assist**, *not* a gate —
  see [deep-rock-galactic.md](games/deep-rock-galactic.md).
- Monster Hunter "sleep bombing" as a coordinated burst tactic (1-2).
- Helldivers Reinforce having a literal *0-second cooldown* / a purely "dead + tickets" precondition
  (0-3); and an EMS Mortar prescribed *specifically* to suppress Automaton bot drops (1-2).
- DRG Scout L.U.R.E. grenade as a "throw at untargeted enemies to round them up" tactic (0-3).

**Time-sensitivity.** WoW figures (taunt ~6s, swap at ~8 stacks, Salhadaar) are current for Patch
12.0.0 (2026) and shift with patches; Volcoross is a closed historical tier (Dragonflight 10.2).
Monster Hunter, L4D2, Overcooked, DRG, and the HD2 reinforcement/resupply economies are stable.
Numeric thresholds throughout should be treated as **tunable domain parameters**, not constants.

The still-uncovered games and unanswered design questions (PvP ult/ability economy, explicit
multi-phase timelines, optimal CC-budget policy) are catalogued in
[`games/coverage-gaps.md`](games/coverage-gaps.md) for a future research pass.
