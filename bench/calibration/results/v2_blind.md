# Reviewer calibration: v2_blind

Spearman rho = **0.73** over 34 rulesets; exact 21, within 1 star 31; cost $10.98.

| ruleset | owner | reviewer | reviewer summary |
|---|---|---|---|
| game | 5 | 5 | This is a clear teaching example. doAI is a short, prioritized menu of strategies built from reusable verbs (attackUnit, moveClosestPawnNearKing, tryMove), and  |
| jam | 5 | 2 | It compiles, but it is a one-step reactive policy, not a plan. It hard-codes 'boss' and 'button', hand-rolls reachability with invented connected_1/connected_2/ |
| pathtest | 5 | 3 | This is a topology fixture: symmetric linked/2 facts and no tasks, so there is nothing wrong in its design, but there is also nothing to plan. The unused 'movem |
| taxi | 5 | 5 | Every travel-to method's if() states what makes that way of travelling possible, and its do() is a few game actions. The goal is a menu of strategies, and the o |
| taxi2 | 5 | 5 | This is the gold Taxi example. The only change is that the person is now `at(person, ?x)`, which makes `at/2` the same for people and vehicles and is if anythin |
| trunkthumper | 5 | 5 | This is a clear, idiomatic top-down domain: attackEnemy is a menu of plain strategies, doTrunkSlam uses a correct else ladder for variants, navigation uses path |
| challenges | 4 | 3 | Each file is one small reusable verb, which is the right direction. But the methods count hops instead of being different ways to do the task, the vocabulary sp |
| combatlevel1_greasetrap | 4 | 4 | The architecture is right: skills are chosen by the tags they apply, the actors are distinct, the verbs are mostly generic, and the file is level facts plus a g |
| gamehack8agentattop | 4 | 4 | The architecture is right: a menu of strategies, feasibility in if(), and reusable tag, skill and aggro verbs with one method per way. It is unfinished: wetAndE |
| old_primitives | 4 | 4 | The primitives have the right shape: small generic verbs, operators with one effect each, and tags instead of stats. But movement is a broken 2- and 3-hop ladde |
| old_upper | 4 | 4 | The architecture is right: primitives, strategies and a goal layer, with theBurn as 'oil room + someone can burn → lure, ignite'. But the strategies name specif |
| gamehack | 3 | 2 | The top is the right shape: planToDamage is a menu, and wetAndElectrocute lists the tags it needs. Below that, skills are chosen by name, the per-tag verbs are  |
| gamehack2 | 3 | 2 | Underneath this is the right idea: a menu of strategies, plus a skill way and a location way to get a tag. But the file is a pile of copied per-tag helpers and  |
| gamehack3 | 3 | 3 | The shape is right: planToDamage is a menu of strategies, applyEffect has one method per way to apply a tag, and bringMobToLocation uses aggro. But stunAndBurn  |
| gamehack4 | 3 | 3 | The shape is right: a menu of strategies, and an applyTag verb with one method per way. But the strategies' if() hides feasibility and ignores immunity, two of  |
| gamehack5onlyplans | 3 | 4 | This is the right GameHack architecture: a menu of strategies, a generic applyTag verb whose methods are the ways to apply a tag, and tags chosen by skill prope |
| gamehack6swapskills | 3 | 3 | The GameHack architecture is right: a strategy menu, an applyTag verb whose methods are the ways to apply a tag, and aggro to pull mobs. But the strategies don' |
| gamehack7combined | 3 | 4 | The architecture is right: `planToDamage` is a menu of strategies, and `stunAndSlowSkill` and `wetAndElectrocute` state their needs through reusable verbs such  |
| gamehack_gh4 | 3 | 4 | The level has the right shape (world facts plus a goal, running on the GameHack verbs), and the lake plus static tesla tower gives the puzzle real alternative r |
| gamehack_gh7 | 3 | 3 | It is a level of the right shape: world facts and a goal built on the GameHack components. But a third of it is linter scaffolding and dead vocabulary (type/2,  |
| gamehack_multipath | 3 | 4 | The shape is right: the level is only facts plus a goal, uses the component vocabulary, and names nothing inside the components. But the fireball fact uses a se |
| gamehack_mvp | 3 | 3 | The shape is correct: a level made only of facts plus a goal, with no level specifics leaking into components. But the world is trivial: one ally solos a single |
| gh_primitives | 3 | 4 | The architecture is right: reusable verbs (`applyTag`, `prepareToUseSkill`, `bringMobToLocation`), and each verb's methods are the ways to achieve it. But the m |
| gh_upper | 3 | 4 | The architecture is right: a menu goal, sequential strategies built from a reusable applyTag verb whose methods are the three ways to apply a tag, and skills ch |
| grease_trap | 3 | 1 | The level has the right shape (facts plus a goal), but its whole vocabulary is the deleted core ontology (reacts/blast/strike/mark/signature/role/charge), which |
| puzzle1 | 3 | 3 | Most of the level is facts plus a goal, the right overall shape. But the goal is written around named rooms and named characters, the old components' character- |
| ringout | 2 | 2 | The knockOver dispatch and the navigation are sound, but the strategies are imperative scripts that also simulate the ogre's turn-by-turn behaviour. Skills are  |
| the_brink | 2 | 2 | The goal menu (defeat -> apply(?e, fall) with two plain alternatives) and the negated base case are the right shape. Everything below it is a chemistry/effect e |
| ab_effects | 1 | 1 | A physics and effect interpreter with its own invented ontology, not an HTN ruleset. It has no strategies and no feasibility in any `if()`, and it searches simu |
| core_primitives | 1 | 1 | This is an effect engine with an invented ontology: a chemistry simulator, role-exclusion sentinels, charge bookkeeping and a 2-hop navigation ladder, with no s |
| core_upper | 1 | 1 | This is the deleted core the_burn/the_slipstream shape: imperative chains of one-off helpers over an invented ontology (primer, reacts, blast, expose, signature |
| fsm_wraith | 1 | 1 | An effect-engine level in the style of the deleted core tree: a made-up behavior/effect/spill vocabulary, feasibility hidden in one-off helpers, maybe-walks and |
| movement_ringout | 1 | 1 | This is a level whose goal is an imperative script over deleted core helpers. It has an empty `if()`, a maybe-walk `stepBack`, an invented slam and verge ontolo |
| reference_good | 1 | 2 | The top-level menu (runHeist) and the tool-versus-blocker clear/defeats check are reasonable. Both routes, though, are imperative scripts of single-use helpers  |
