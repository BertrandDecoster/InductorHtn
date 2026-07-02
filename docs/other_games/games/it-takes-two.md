# It Takes Two — evidence appendix
Designed-for-two co-op: per-chapter asymmetric tool pairs, cross-player combo pipelines, relay
gating, simultaneous-action gates, and distract-while-acting beats.

It Takes Two (Hazelight, 2021) is the purest source in this study for **2-agent** coordination:
the game is built from the ground up for exactly two players, and "the two players must fulfill
different roles and achieve their objectives cooperatively"
([Wikipedia](https://en.wikipedia.org/wiki/It_Takes_Two_(video_game))). Its defining trick is the
**asymmetric tool-split**: every chapter hands Cody and May a *different* tool pair that is
"intentionally incomplete without one another", then builds every puzzle and boss as a combination
of the two. For a 2-companion HTN domain this is the closest published model — almost every beat
decomposes into "agent A's operator produces a fact that agent B's operator consumes."

See the cross-game synthesis in [`../team-patterns-catalog.md`](../team-patterns-catalog.md).

## Patterns this game exemplifies

| Catalog pattern | Tactic from this game |
|-----------------|-----------------------|
| [1 — Role assignment](../team-patterns-catalog.md#problem-1--role--responsibility-assignment) | The tool-split *is* the role assignment: each chapter hard-binds a different capability pair to the two fixed agents |
| [2 — Threat & aggro](../team-patterns-catalog.md#problem-2--threat--aggro-management) | Distract + act: Moon Baboon "distract + trigger" roles; Cody's whip holds a boss in place while May strikes; luring the beetle over a sap-filled grate |
| [5 — Timing & synchronization](../team-patterns-catalog.md#problem-5--timing--synchronization) | Simultaneous gates: pull the lever together, twin buttons powering the blower, mutual magnet attraction; timed button-launch windows |
| [9 — Phase transitions](../team-patterns-catalog.md#problem-9--phase--state-transitions-medium-confidence) | Moon Baboon re-binds both players' roles each phase (run/trigger → fly/ride → inside/outside) |
| [10 — Recovery](../team-patterns-catalog.md#problem-10--recovery--failure-handling) | Tethered progress ("no players proceed unless all players proceed") and survival/attrition — play continues as long as one player is alive |
| [11 — Safety constraints](../team-patterns-catalog.md#problem-11--safety-constraints) | Hold-open gates where releasing the mechanism kills the partner (Garden bulb) |

> **Two beats here are *not* in the 11-pattern catalog**: the **relay / leapfrog gate** (A crosses
> a path only A can cross, opens the way for B, B opens the next section for both) and the
> **cross-agent combo pipeline** (A's tool stages a world state that only B's tool can consume).
> Both are candidate additions for a future catalog pass — see
> [`coverage-gaps.md`](coverage-gaps.md). The catalog itself is unchanged by this appendix.

## Verified tactics

**Asymmetric tool-split per chapter.** Every chapter discards the previous mechanics and issues a
new pair of abilities "tied to the theme of the current level"; Josef Fares pushed the team to
never repeat mechanics because repetition would make them "less special"
([Wikipedia](https://en.wikipedia.org/wiki/It_Takes_Two_(video_game))). Verified pairs:

| Chapter | Cody | May | Combo shape |
|---------|------|-----|-------------|
| The Shed | Throwable/recallable nails | Hammer head | Nails pin moving platforms and make swing points; May smashes, swings, pounds buttons |
| The Tree | Sap gun (coats targets) | Match gun (ignites sap) | Coat → ignite: opens passages, detonates enemies |
| Rose's Room | Size change (shrink/grow) | Gravity boots (walk walls/ceilings) | Each crosses spaces only their tool allows |
| Cuckoo Clock | Time rewind/fast-forward on objects | Place a clone, teleport to it | Rewind holds a state open; clone pre-positions a future crossing |
| Snow Globe | One magnet pole | The opposite pole | Attract/repel each other and colored objects; dual-pole objects force simultaneous action |
| Garden | Plant transformations + head-whip (grab/hold) | Sickle (melee), water | Cody holds/peels/traverses as plants; May cuts and strikes |
| The Attic | Cymbal shield (blocks/deflects) | Singing voice (activates machinery) | Voice opens, cymbal protects |

— Pairs from [vgtimes complete walkthrough](https://vgtimes.com/guides/114022-complete-walkthrough-it-takes-two-bosses-and-puzzles-at-all-levels.html),
[Hone chapters list](https://hone.gg/blog/it-takes-two-chapters-list/),
[Gamepur Shed guide](https://www.gamepur.com/guides/it-takes-two-the-shed-gameplay-tips-and-walkthrough-guide),
[anuflora design analysis](https://www.anuflora.com/game/?p=6023),
[Neoseeker/ordinarygaming Garden results](https://www.gamepur.com/guides/it-takes-two-garden-gameplay-tips-and-walkthrough-guide). See caveats for per-cell conflicts.

**Cross-agent combo pipeline (the two-step grammar).** The Shed's puzzles follow "a two-step
rhythm: May sets the timing/position, then Cody locks it with a nail"
([walkthroughs.games](https://walkthroughs.games/lorebase/it-takes-two)); Cody's "nails can lock
movable platforms into place through holes against yellow surfaces" and "May can swing on nails
that Cody sticks on walls" ([Gamepur](https://www.gamepur.com/guides/it-takes-two-the-shed-gameplay-tips-and-walkthrough-guide)).
The Tree generalizes it: "Cody needs to smear sap onto them with his sap gun, while May has to
finish them off with her match gun" ([anuflora](https://www.anuflora.com/game/?p=6023)) — one
agent *stages* a world state, the other *consumes* it. Boss variants: coat the Wasp Queen's armor
in sap, then ignite, across three phases
([GameRant boss guide](https://gamerant.com/takes-two-defeat-every-boss/)).

**Relay / leapfrog gating.** One player crosses via something only they can use, then opens the
way for the other, who opens the next stretch — alternating until they rejoin. Verified instances:
in the Shed intro, "one player grabs the break point immediately after the button. The second
player presses the button and heads to the second break point"
([vgtimes](https://vgtimes.com/guides/114022-complete-walkthrough-it-takes-two-bosses-and-puzzles-at-all-levels.html));
in the Cuckoo Clock, "Cody lifts a destroyed bridge [time-rewind] for May. [May] sets a clone near
the entrance and returns back. When the door opens, May uses the ability to teleport"
([vgtimes](https://vgtimes.com/guides/114022-complete-walkthrough-it-takes-two-bosses-and-puzzles-at-all-levels.html));
in the Shed, one player stands on a red button while the other waits on the launched platform,
then "P1 pounds the button and P2 quickly enters the tube"
([Neoseeker Shed walkthrough](https://www.neoseeker.com/it-takes-two/walkthrough/The_Shed)). The
Medium deconstruction names the underlying constraint **gating/tethering**: "no players proceed
unless all players proceed"
([Jahani, level deconstruction](https://medium.com/@jahani.rana/generating-new-cooperative-levels-by-deconstructing-components-of-it-takes-two-d2d4df8c7d36)).

**Simultaneous-action gates.** Some interactions only work if both act at once: the opening lever
must be pulled *together* ([Gamepur](https://www.gamepur.com/guides/it-takes-two-the-shed-gameplay-tips-and-walkthrough-guide));
"both buttons are activated, the blower in front of you will start sucking air" (Shed); facing
magnet players "simultaneously press the ability activation key to attract to each other" (Snow
Globe, Slippery Slopes)
([vgtimes](https://vgtimes.com/guides/114022-complete-walkthrough-it-takes-two-bosses-and-puzzles-at-all-levels.html)).
The Snowglobe deconstruction makes the design rule explicit: single-colored magnet objects allow
*turn-based* (asynchronous) solving, while **dual-colored objects require simultaneous action**
([Jahani](https://medium.com/@jahani.rana/generating-new-cooperative-levels-by-deconstructing-components-of-it-takes-two-d2d4df8c7d36)).

**Distract / hold + act.** One agent occupies a mechanism or an enemy's attention while the other
does the real work. The Moon Baboon boss assigns explicit "distract + trigger" roles — one player
draws the laser while the other activates floor buttons
([walkthroughs.games](https://walkthroughs.games/lorebase/it-takes-two),
[GameRant](https://gamerant.com/takes-two-defeat-every-boss/)). Toolbox boss: "Cody must fix [the
boss's arm] in one position. At this moment, May moves to the boss using the previously placed
nails" ([vgtimes](https://vgtimes.com/guides/114022-complete-walkthrough-it-takes-two-bosses-and-puzzles-at-all-levels.html)).
Garden: "Cody must use his head-whip to hold the boss in place, while May gets up close and whacks
it with her sickle"; and a traversal variant where Cody pulls a bulb open and "needs to keep
holding it down; releasing it will trap May and kill her"
([Gamepur Garden guide](https://www.gamepur.com/guides/it-takes-two-garden-gameplay-tips-and-walkthrough-guide)).
Beetle fight: Cody fills grates with sap, one player lures the beetle over the grate, May ignites
([GameRant](https://gamerant.com/takes-two-defeat-every-boss/)).

**Teaching combos via narrative affordance (readability).** Abilities are diegetically motivated
so players can *deduce* the combo from the fiction: May complains Cody "has no sense of time" → he
gets time manipulation; May laments "she cannot be in two places at once" → she gets the clone
([Wikipedia](https://en.wikipedia.org/wiki/It_Takes_Two_(video_game))). Each chapter's tools are
introduced against the chapter's theme, the pair is exercised in a simple two-step form first (the
Shed's "two-step rhythm"), and then recombined in escalating variations — the deconstruction shows
a single mechanic (circular magnets) reused as horizontal gap-crossing *and* vertical
wall-launching ("dual-functionality objects")
([Jahani](https://medium.com/@jahani.rana/generating-new-cooperative-levels-by-deconstructing-components-of-it-takes-two-d2d4df8c7d36)).
The HTN reading: the *player-facing affordance* of each tool is the method's precondition — a
player who knows "sap is flammable, matches ignite" can derive every sap puzzle's solution.

## HTN sketches

The whole game reduces to a small grammar over two fixed agents. Roles are tool facts, not class
tokens — re-binding them per chapter is one `del`/`add` away.

```prolog
% Per-chapter tool grant: the role IS the tool. (Chapter transition swaps these facts.)
% hasTool(cody, sapGun). hasTool(may, matchGun).

% --- Cross-agent combo pipeline (Tree: coat -> ignite). A stages, B consumes. ---
burnObstacle(?obs) :-
    if(blocked(?obs, flammable),
       hasTool(?a, sapGun), hasTool(?b, matchGun)),
    do(opSpraySap(?a, ?obs), opIgnite(?b, ?obs)).
opSpraySap(?a, ?obs) :- add(sapped(?obs)).
opIgnite(?b, ?obs)   :- del(sapped(?obs)), del(blocked(?obs, flammable)).

% Shed variant: May positions a moving part, Cody freezes it with a nail.
lockPlatform(?plat) :-
    if(moving(?plat), hasTool(?c, nails), hasTool(?m, hammer)),
    do(opAlignPlatform(?m, ?plat), opPinWithNail(?c, ?plat)).

% --- Relay / leapfrog gate (Shed break points; Cuckoo Clock bridge + clone). ---
% A crosses via an A-only affordance, opens B's path; B opens the next stretch; rejoin.
relaySection(?zoneEnd) :-
    if(canCross(?a, ?obstacle1), at(?a, ?start), at(?b, ?start)),
    do(crossSolo(?a, ?obstacle1),
       opPressButton(?a, button1),      % opens partner's path
       moveTo(?b, button2),
       opPressButton(?b, button2),      % opens the shared path forward
       moveTo(?a, ?zoneEnd), moveTo(?b, ?zoneEnd)).
opPressButton(?p, ?btn) :- del(closed(?btn)), add(open(?btn)).

% Tether constraint: a section only completes when BOTH agents arrive.
sectionDone(?zone) :- if(at(cody, ?zone), at(may, ?zone)), do(advanceChapter()).

% --- Simultaneous-action gate (twin buttons / mutual magnet pull). ---
% parallel() is the author-guaranteed concurrency marker (see ruleset-keywords.md).
openBlower() :-
    if(at(?a, pad1), at(?b, pad2), \==(?a, ?b)),
    do(parallel(opHoldButton(?a, b1), opHoldButton(?b, b2))).

magnetPull(?a, ?b) :-
    if(facing(?a, ?b), polarity(?a, ?p1), polarity(?b, ?p2), \==(?p1, ?p2)),
    do(parallel(opAttract(?a), opAttract(?b))).

% --- Distract / hold + act (Toolbox arm pin; Garden whip-hold; Moon Baboon roles). ---
% Reuses the aggro idiom: the holder is a getAggro/lureToRoom-shaped beat.
holdAndStrike(?boss) :-
    if(vulnerableWhileHeld(?boss), canHold(?holder, ?boss), canStrike(?striker, ?boss),
       \==(?holder, ?striker)),
    do(parallel(opHold(?holder, ?boss), opStrike(?striker, ?boss))).

% Safety flavor: releasing the hold kills the partner -> the hold is a precondition
% of the partner's traversal, not an optional assist.
crossBulbGap(?m) :-
    if(heldOpen(bulb, ?c), \==(?c, ?m)),
    do(moveTo(?m, farSide)).
```

> The relay sketch is a *generalization*: the sources attest the structure in pieces (leapfrog
> break points, bridge-rewind + clone-teleport, button-launch handoffs), not as one named template.
> The combo pipeline and simultaneous gates are directly attested.

## Caveats

- **Magnet color/polarity assignment conflicts across sources** (Jahani: May blue / Cody red;
  vgtimes: the reverse; Hone: "red North, blue South"). Structurally irrelevant — model it as
  opposite polarities, not colors.
- **Sap/matches ownership**: most sources (anuflora, GameRant, Gamepur-adjacent guides) say
  **Cody = sap, May = matches**; the Hone chapters list flips it. The majority reading is used
  here; the *pipeline shape* is unaffected either way.
- May's Garden **water gun** is single-source (vgtimes/walkthrough aggregation) — low confidence
  on the tool, high confidence on sickle + plant-transformations.
- GameRant places the **Giant Beetle** in a "Sewer chapter"; It Takes Two has no such chapter (it
  is most likely the Tree's underground section). Chapter attribution uncertain; the
  lure-over-sap-grate tactic itself is the verified part.
- Chapter *numbering* varies across sources (some count the prologue, some count sub-levels);
  this doc names chapters and avoids numbers.
- The "teaching via narrative affordance" claim rests on the Wikipedia development section
  (primary Fares interviews) plus design-blog analysis — directionally solid, but no GDC-style
  primary talk on It Takes Two's onboarding was found in this pass.
- All puzzle blow-by-blows come from walkthrough sites, not developer documentation; multiple
  independent walkthroughs agree on every tactic kept here.

## See also
- [`../team-patterns-catalog.md`](../team-patterns-catalog.md) — the cross-game pattern catalog
- [`coverage-gaps.md`](coverage-gaps.md) — where the relay-gate and combo-pipeline candidates belong
- [`../../upgrades/ruleset-keywords.md`](../../upgrades/ruleset-keywords.md) — the `parallel()`
  keyword the simultaneous-gate and hold-and-strike sketches use
- `../../../components/primitives/aggro/src.htn` — `getAggro` / `lureToRoom`, the repo idiom behind
  the distract-and-act beat
