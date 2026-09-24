# Puzzle authoring brief (ability layer)

This is the brief for writing puzzle levels on the ability layer. It serves human designers and the
per-category generation agents alike. Read it with [`ability-system.md`](ability-system.md) (the
engine) and [`ability-catalog.md`](ability-catalog.md) (the standard tags and skills). The reference
level is `levels/two_hands`: copy its shape.

## The hard rules (checked by `htn_components combos`)

1. **No single skill wins.** Give any one pool skill to every seat at once: no plan.
2. **No single companion wins.** Every winning plan has actions by two or more companions.
3. **Several combinations win.** At least `comboMinWins` assignments (default 2); aim for 4 or more.
4. **Several methods.** At least `comboMinMethods` distinct sets of skills cast (default 2); aim for
   3 or more, and at least two that differ in kind (for example a hazard drop vs. a weakness).
5. **Nothing grants an outcome.** `dead`, `frozen` and `fell` come only from an enemy's own
   `weakness/4` or a hazard it is weak to, never from `grant(dead)` in a skill.
6. **No damage.** No `damage(...)` atoms: damage is incremental; the game is about combos.
7. **Skills are multi-use.** Every skill lands several tags, or a tag and a movement. A skill whose
   tag has no consequence in the level is a bad skill.

Also aim for:
- No mandatory pick: every pool skill should appear in some winning assignment. The report lists
  "dead skills".
- One skill serving two roles: a single skill that appears in two different methods is the best
  sign of a good puzzle.

## Size caps (planner time)

- 4 to 8 areas, 2 or 3 companions, at most 4 enemies or objects, and a pool of 6 to 8 skills
  drawn from the eleven catalogue skills.
  Two seats picking one skill each gives 64 assignments; three seats gives 512.
- One `FindAllPlans` of the level goal should take under about 20 seconds. `combos` times each out
  at 180 s by default. If you are slow, shrink the map or give fixed skills to non-seat companions.
- Prefer the level's own top-level goal method, spelling out stages (as `gauntlet`'s `escape`
  does), over asking a generic recipe to discover everything.

## What you can use

**Engine** (`components/abilities/`; see `ability-system.md`):

- Tags:
  - `tag(?e, ?t)`, composites `bundles/2`, groups `group/2`
  - `immune/2`, `wards/2`, `forbids/2`, `suspends/2`
  - what an entity is, is a tag: `tag(golem, heavy)`, `tag(bot, machine)`, `tag(crate, filler)`
    (no `trait/2`, no `element/2`)
- Effects: `effect(?ab, target|self|area|foes|around, ?atom)` with the atoms (`area`: everyone
  else in the target's area; `foes`: the NPCs there; `around`: everyone else in the caster's area)
  - tags: `grant(T)`, `remove(T)`, `purge(Group)`
  - movement: `push`, `pull`, `hook` (pull a light target, or be dragged to an anchored one),
    `swap`, `dash`, `teleport` (the source next door), `teleport(R)`, `pullIn` (draw the
    neighbouring areas' contents into the target area), `chase` (walk after the source)
  - actions: `interrupt` (a magic heavy attack being wound up stops)
  - terrain: `spill(Zone)`, `hazard(H)`, `open(Door)`, `close(Door)`, `openWhenHeld(Door)`, and
    `zoneReaction(?old, ?in, ?new)` (ice over deep water is a floor)
  - duration: `moment(grant(T))`, `moment(remove(T))` - through the next cast by anyone
- Keep to the keywords. A new level-local ability is a combination of these atoms, never a new
  word.
- Heavy attacks: `heavy(?ab)` on an NPC ability makes its behaviour telegraphed. The NPC winds up
  on an area (aim `here`/`there(R)`) or on an entity it follows (aim `source`); with a companion
  in the struck area the team may answer with one cast (no walking), then the blow lands on
  everyone in the struck area but the NPC. A disjoint one is passed through; a shielded one's
  shield breaks instead. A companion may take it (sacrifice is allowed); a `mustSurvive(?x)`
  escort may not. `kind(?ab, magic)` makes it interruptible (Hook, Shield Bash); a physical one
  can only be survived. Use them where you want players to trigger a big effect on purpose and
  survive it: the catalogue has `groundSlam` (stun and throw), `caveIn` (the floor becomes a
  chasm) and `meteor` (magic: the area burns); define your own.
- Reactions (for everyone, never lethal): `reaction(?have, ?incoming, ?ab)`.
- Weaknesses (per entity, the only way to an outcome): `weakness(?e, ?in, ?have|none, ?out)`.
  `?in` is a tag or a hazard.
- NPC behaviour: `behavior(?npc, ?trigger, ?ab, source|self|here|there(R))`.
  - An NPC that gains the trigger tag casts its ability. Its effects apply raw: weaknesses answer,
    reactions do not.
  - Phases are ordinary tags. A weakness that needs a phase tag is a vulnerability window, e.g. a
    boss that exhausts itself: `effect(slam, self, grant(exhausted))` plus
    `weakness(boss, X, exhausted, dead)`.
  - `onGrant(taunted, chase)`: a taunted NPC walks after its taunter and follows it; if it
    cannot walk there, the taunt breaks. Companions cannot be taunted.
- Map: **areas are large** - a small room, or a quarter of a large one - joined by links,
  each declared once, either way round. A chokepoint is two areas with a special link.
  - `connected(?a, ?b)` walkable; `gap(?a, ?b)` a short pit (dash or teleport over it); `wall(?a,
    ?b)` (only a teleport goes through); `doorway(?a, ?b, ?d)` (walkable while `open(?d)`)
  - `feature(?r, ?f, ?ab)`: a pit, lava, deep water inside an area (walked around, knocked into);
    `plate(?f)` makes it a pressure plate (a companion `stepOn`s it, or something is knocked onto
    it; pressing applies `?ab`: `open(D)` locally, or `spill(Z, R)` area-wide)
  - a **chute** is a feature whose ability is `teleport(R)`: whatever is knocked onto it lands
    in area ?R. It is the one way a knockback moves something to another area, and it is only
    where a level puts one
  - **moving an NPC to another area** takes a hook (a pull from next door) or a taunt (it walks
    after you); **knockbacks never change the area**: a push (Fireball, Tidal Wave, Shield Bash,
    a slam) knocks its target into a feature of its area or a gap at its edge, and a Vortex aimed
    at a feature knocks everything in the area into it. So most plans bring the NPC to the right
    area first (`bringTo`), then force the interaction (`knockInto`)
  - dash (walkable or gap) and teleport (any link) move the caster next door
  - `lineOfSight(?a, ?b)` for ranged aims; melee reaches the same area or next door (not
    through a wall); `near` (Blink) reaches next door through any link
- Terrain:
  - `onEnter(?r, ?zoneAbility)` zones cover a whole area (flames, ice, shadows); an area-wide
    hazard zone (all lava) cannot be walked into
  - plates latch (`open(D)`), or `plateFor(?p, ?d)` plus `openWhenHeld(D)` (all at once)
  - `blocker(?e)` (nobody walks into its area)
  - `watches(?guard, ?r)` (no companion walks in unseen unless stealthed or the guard is blinded)
  - `tag(?x, filler)` (fills a pit or a gap it is knocked into)
- Walking is automatic (`walkTo`, shortest route of at most eight steps).
- Sacrifice is allowed: a companion may be lost and the plan still win. Declare
  `mustSurvive(?x)` for an escort no heavy blow may catch.

**Recipes:**
- `neutralize(?e)` (`abilities/goals/neutralize`): the enemy's lethal weakness (`exploit`), a push
  or pull into a hazard (`intoThePit`), guard stripping, `conduct`/`ignite`/`shatter`,
  `improvise`.
- `passage` (`abilities/strategies/passage`):
  - `reach(?a, ?r)`: walk, leap, hook, swap, be ferried; needs `progress/2` on the route
  - `openWay(?door)`
  - `span(?gap)`
  - `clear(?blocker)`
- Acts you can call from your own methods:
  - casting: `cast(?a, ?ab, ?e)`, `castFrom(?a, ?ab, ?e, ?from)`
  - tags: `inflict(?t, ?e, ?not)`, `combo(?have, ?in, ?e)`, `unset(?t, ?e)`
  - movement: `bringTo(?e, ?r, ?not)` (a hook or a taunt brings it to area ?r),
    `knockInto(?e, ?f, ?not)` (bring it to the feature's area, then knock it in),
    `knockOn(?e, feature(?f)|gap(?n), ?not)`, `dropInGap(?e, ?not)`, `sendDown(?e, ?not)`,
    `dislodge(?e)`, `walkTo(?a, ?r)`, `stepOn(?a, ?plate)`; the rules behind them are
    `bringing/7` and `knocks/6` (cast `?ab` at `?aim` from `?from`)
  - a knock is aimed by the caster, but the physics tries every aim: a recipe that wanted one
    outcome confirms it (`confirmHas`, `confirmStopped`, `confirmOpen`)
  - passage: `bridge(?a, ?b)` fills a gap with a filler; `span(?pit)` fills a pit
  - checks: `confirmStopped(?e)`

**Level-local definitions are allowed.** You may declare new abilities, zones, weaknesses,
behaviours and phase tags in your own `level.htn`. Anything you think belongs in the shared catalogue
goes on your **wishlist** instead (see below).

## Engine rules to respect

- **`else` is not a cut.** A "nothing happens" branch must negate the branches before it.
- **A failed search that decomposed locks the rule set.** Use a fresh planner per check, as
  `combos` and the `two_hands` test do.
- **Operators:** actor first, ground `del`, a `not(...)` guard before every add, no `hidden`.
- **`allOf` conditions** must use single-clause rules; use `holds/2`, not `has/2`.

## Deliverables per level

Folder `levels/<category>_<name>/`:

- **`level.htn`:**
  - a header comment: the fantasy, the obstacles, every method, and the traps;
  - areas, links, zones, companions, enemies;
  - a default kit;
  - the goal (`win` with alternatives if there are several victories);
  - the choice declaration: `comboSeat/2`, `comboPool/1`, optionally `comboMinWins/1` and
    `comboMinMethods/1`;
  - `funExpect(single_actor_plans, atMost, 0).` and `goals(...)`.
- **`manifest.json`:** layer `level`; dependencies `abilities/goals/neutralize` (and
  `abilities/strategies/passage` if used) and `abilities/primitives/ab_catalog`.
- **`design.md`:** same sections as `levels/two_hands/design.md`:
  - Purpose, Layer, Dependencies, World;
  - Hypothesis, with the measured `combos` numbers;
  - Examples (### Example N), Properties (P1...).
- **`test.py`:** pins the `combos` result, as `two_hands/test.py` does: no single skill wins, the
  winning set equals what you measured, plus the examples.

Acceptance, all from the repository root with the venv active and `PYTHONPATH=src/Python`:
```bash
python -m htn_components combos <name>      # RESULT: PASS
python -m htn_components certify levels/<name>
python -m htn_components verify <name>      # exit 0
```

## Do not

- Edit anything under `components/`, `src/`, `docs/`, or another level. Report engine bugs and
  missing mechanics instead.
- Grant an outcome, or use damage.
- Solve a hard requirement with a level-local special case the rules forbid (e.g. `grant(dead)`).

## Report (your final message)

For each level:
- the name, the idea in two lines, the obstacles, and each method;
- the `combos` numbers: winning / total assignments, methods, dead skills.

Then, across your levels:
- **Skills used:** each pool skill, and the roles it played (push, soak, bridge, ...).
- **Tags used**, and any tag you never needed.
- **Wishlist:** new tags, skills, mechanics or catalogue changes you would promote, each with the
  puzzle that needs it and why no existing piece does.
- **Friction:** engine bugs, slow spots, rules that got in the way.
