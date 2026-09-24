# Ability systems: a survey for HTN building blocks

This is the research behind the ability layer (`components/abilities/`, spec in
[`../reference/ability-system.md`](../reference/ability-system.md)). It covers two questions:
1. How do games apply tags and effects through abilities?
2. Where should that knowledge live in an HTN ruleset?

Several web sources blocked automated fetching. Claims marked *(from memory)* were not confirmed
against a page and should be checked before they are relied on.

## 1. Unreal Gameplay Ability System (GAS)

- **Gameplay tags** are hierarchical names (`State.Debuff.Stun`), and a query for a parent matches
  its children (`HasTag` vs `HasTagExact`). They are stored in counted containers, so two effects that
  grant the same tag must both end before it disappears.
- **Gameplay abilities** are gated by tags on the caster and the target: `ActivationRequiredTags` /
  `ActivationBlockedTags`, `Source/TargetRequiredTags` / `...BlockedTags`. While active, an ability can
  cancel or block other abilities by tag. *(from memory)*
- **Gameplay effects** are data: a duration policy (instant, has-duration, infinite), modifiers,
  granted tags, application / ongoing / removal tag requirements, effects removed by tag, immunity,
  and stacking. **Costs are instant effects; cooldowns are effects that grant a `Cooldown.X` tag.**
- **UE 5.3+** splits a GameplayEffect into modular components (`TargetTagsGameplayEffectComponent`,
  `TargetTagRequirementsGameplayEffectComponent`, `ImmunityGameplayEffectComponent`,
  `RemoveOtherGameplayEffectComponent`, `AdditionalEffectsGameplayEffectComponent`, ...). An effect
  becomes a list of small typed parts, which maps directly onto Prolog facts.
- **Takeaway:** an effect is a list of atoms; gates are required and blocked tag sets on each side;
  a cooldown is just a tag.

Sources: [tranek GASDocumentation](https://github.com/tranek/GASDocumentation),
[Epic: Gameplay Effects](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-effects-for-the-gameplay-ability-system-in-unreal-engine),
[GE Components](https://bobby-liu.medium.com/unreal-gameplay-effect-just-got-better-introduction-to-gameplay-effect-components-d5c498b1d149).

## 2. Environments and combos

| Game | Mechanism | Reusable abstraction |
|------|-----------|----------------------|
| Divinity: Original Sin 2 | Surfaces (water, oil, fire, poison, ice) give a status to whoever stands in them; element × surface rewrites the surface; wet + shock stuns; burning removes wet | `surface → status on occupant`; `element × surface → surface'`; status × status reactions |
| Genshin Impact | An aura element sits on a target; a trigger element reacts and **consumes** the aura | `reaction(aura, trigger, result)`; consuming the aura is what stops chains |
| Breath of the Wild | Elements change materials, elements change elements, materials never change materials | split active elements from passive materials |
| Magicka | Opposing elements cancel; some pairs combine (water + cold = ice); a frozen target shatters to a strong blow | a small combine / cancel algebra; frozen is both a stall and a kill setup |
| Into the Breach | Every attack is telegraphed and deterministic; pushes into water, chasms and each other kill | forced movement plus terrain is an environmental kill; determinism lets a planner simulate it |
| Baldur's Gate 3 | Shove into a chasm; surfaces; conditions with saves | `shove` is an effect atom; the destination decides the outcome |
| Slay the Spire, Darkest Dungeon | Strong moves carry a drawback on the user (exhaust, self-debuff) *(from memory)* | the drawback is just another effect atom, aimed at `self` |

Sources: [DOS2 Environmental Effects](https://divinityoriginalsin2.wiki.fextralife.com/Environmental+Effects),
[KQM Elemental Gauge Theory](https://library.keqingmains.com/combat-mechanics/elemental-effects/elemental-gauge-theory),
[BotW chemistry, GDC 2017](https://www.thumbsticks.com/gdc-17-breath-of-the-wild-science-lies/),
[Magicka Elements](https://magicka.fandom.com/wiki/Elements/Details),
[Into the Breach postmortem](https://gdcvault.com/play/1026333/-Into-the-Breach-Design),
[bg3.wiki Shove](https://bg3.wiki/wiki/Shove).

## 3. Composition vs inheritance for statuses

None of the status systems surveyed decides rules with a single-parent tree:

- **Dota 2:** engine state flags (`STUNNED`, `ROOTED`, `SILENCED`, `MUTED`, `DISARMED`, `HEXED`,
  `FROZEN`, ...). Hex is a bundle (silence + mute + disarm + fixed speed) *and* keeps its own `HEXED`
  flag. Whether it can be dispelled is a separate property (`IsPurgable`, basic vs strong dispel).
- **League of Legends:** every crowd-control type has its own row of independent properties
  (tenacity, cleanse, interrupts channels). Airborne and Suppression behave like a stun but have
  their own exceptions.
- **World of Warcraft:** three independent classifications per aura: mechanic (stun, root, fear),
  dispel type (magic, curse, poison, disease), and diminishing-returns category.
- **Pathfinder 2e:** conditions include others (unconscious gives blinded and off-guard, and falls
  prone). Off-guard is reached by several routes, which makes a graph, not a tree. PF1e *helpless*
  is what enables a coup de grace.
- **Baldur's Gate 3:** one `StatusType` plus any number of `StatusGroups` (`SG_Incapacitated` has
  30+ members: frozen, petrified, hold person, ...).
- **GAS:** a dotted tag has one parent. Frozen can't be both `Debuff.Stun.Frozen` and
  `Element.Water.Frozen`, so projects add duplicate tags or extra containers.

**Conclusion.** A status is a named bundle of atomic flags, keeps an identity flag of its own, and
belongs to any number of orthogonal groups. Keep composites one level deep and let the author flatten
deeper nesting. In a Prolog-style engine that is one join (`tag(E, C), bundles(C, X)`), with no
transitive climb and no duplicate answers from diamond inclusion.

Sources: [Dota 2 Hex](https://dota2.fandom.com/wiki/Hex),
[LoL CC summary](https://wiki.leagueoflegends.com/en-us/Types_of_Crowd_Control/Summary),
[WoW Dispel type](https://warcraft.wiki.gg/wiki/Dispel_type),
[WoW DR](https://warcraft.wiki.gg/wiki/Diminishing_returns),
[PF2e Unconscious](https://2e.aonprd.com/Conditions.aspx?ID=95),
[BG3 Status groups](https://bg3.wiki/wiki/Status_groups),
[UE gameplay tags](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-tags?application_version=4.27).

## 4. Where knowledge lives in an HTN

- **SHOP / SHOP2 (Nau et al.).** Methods hold the domain knowledge and search control. Planning
  forward in execution order means the whole world state is known at each step, so full Horn-clause
  inference and external calls in preconditions are cheap. Method order is the preference. Planners
  tailored this way beat "fully automated" planners, whose only domain knowledge is their operators,
  by orders of magnitude.
  ([SHOP](https://www.cs.umd.edu/~nau/papers/nau2000shop.pdf), [applications](https://www.cs.umd.edu/~nau/papers/nau2004applications.pdf))
- **Erol, Hendler & Nau.** HTN planning is undecidable in general. Restricting methods to be
  acyclic bounds the expansion depth.
  ([complexity](https://www.cs.umd.edu/~nau/papers/erol1994htn.pdf))
- **Transformers: Fall of Cybertron (Humphreys, Game AI Pro ch. 12).** Compound tasks are containers
  of methods; the first method is the highest priority. The hierarchy culls whole branches, which
  made the HTN faster than the team's earlier GOAP. Recursion is fine when an effect breaks the loop.
  They kept in-order priority over costs for readability.
  ([chapter](https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter12_Exploring_HTN_Planners_through_Example.pdf))
- **Killzone 3 (Straatman, Verweij, Champandard).** Branches are tried in listed order; specialized
  branches come first and "the generic branch is always available". Preconditions call C++ solvers
  (line of attack, position picking) instead of searching for them.
  ([chapter](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter29_Hierarchical_AI_for_Multiplayer_Bots_in_Killzone_3.pdf))
- **GOAP vs HTN.** GOAP chains generic effects and preconditions: flexible, slower, and harder to
  direct. A generic `achieve(tag)` method that searches a reaction table backwards is GOAP inside an
  HTN, with neither GOAP's heuristic nor the HTN's pruning.
- **GTPyhop.** Goal methods are followed by a verify action that fails if the goal does not hold, so
  a wrong method backtracks. Loops are prevented only by how the domain is written.
  ([GTPyhop](https://www.cs.umd.edu/~nau/papers/nau2021gtpyhop.pdf))
- **InductorHTN (Zinda).** Every matching method is a separate solution; `else` gives priority;
  `anyOf` / `allOf` group solutions; `first()` stops at one binding. "The AI will only be as good a
  strategist as I am." ([overview](https://blog.inductorsoftware.com/blog/InductorHtnOverview))

**Conclusion, as built:**
- **Recipes** are specialized, ordered, top-level methods that carry the detail (who primes, who
  pays off, from which side).
- **Acts** are fixed-depth and never recurse into their own prerequisites.
- **Physics** is data at the bottom. The reaction table is consulted as a filter on what just
  happened, never as a generator of plans. Recipes end with a verify step.
