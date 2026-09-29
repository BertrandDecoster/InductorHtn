# Monster Hunter — evidence appendix
Status/trap combos on a mobile target, with an explicit CC-economy mechanic.

Monster Hunter World is the cleanest verified model for crowd-control as a *budget* and for
two-step trap/capture combos gated by a weakened-state flag. The target is mobile and resistant,
so coordination is about quantified thresholds and fixed windows — both of which map directly onto
HTN preconditions and the engine's numeric-fluent operators.

See the cross-game synthesis in [`../team-patterns-catalog.md`](../team-patterns-catalog.md).

## Patterns this game exemplifies

| Catalog pattern | Tactic from this game |
|-----------------|-----------------------|
| [5 — Timing](../team-patterns-catalog.md#problem-5--timing--synchronization) | Shock Trap immobilizes for a fixed 7.5s window (10s on 3-star paralysis weakness) |
| [6 — CC chaining & economy](../team-patterns-catalog.md#problem-6--crowd-control-chaining--cc-economy) | Per-status buildup thresholds that roughly double after each proc |
| [10 — Recovery](../team-patterns-catalog.md#problem-10--recovery--failure-handling) (loosely) | Two-step capture combo gated by a weakened-state flag |

## Verified tactics

**Status buildup with diminishing returns (the CC economy).** Poison, Sleep, Paralysis, Blast, and
Stun can be inflicted on monsters via weapon attacks; elemental Blights (Fireblight, Waterblight,
…) cannot. Each ailment has a per-monster buildup threshold and triggers only once accumulated
buildup crosses it. Critically: "once a monster succumbs to a status effect, it becomes more
resistant, subsequently requiring additional procs to trigger the same effect" — **the threshold
roughly doubles after each trigger**.
— [Fextralife MHW Status Effects](https://monsterhunterworld.wiki.fextralife.com/Status+Effects),
corroborated by [MH Wilds Status Effects](https://monsterhunterwilds.wiki.fextralife.com/Status+Effects)

**Trap window (fixed-duration immobilize).** A Shock Trap immobilizes a monster for **7.5 seconds
(10 seconds if it has a 3-star paralysis weakness)** — a known window in which the now-stationary
target can be focused.
— [Fextralife Shock Trap](https://monsterhunterworld.wiki.fextralife.com/Shock+Trap)

**Capture combo (precondition + ordered actions).** Capture requires the monster to be in a
*weakened* state first (signalled by a limp, a skull/weak-status icon on the radar, or a flatlining
heart rate). Then applying **two** Tranquilizer items (Tranq Bombs/Knives/Ammo) before *or* after
catching it in a trap completes the capture.
— [Fextralife Shock Trap](https://monsterhunterworld.wiki.fextralife.com/Shock+Trap),
[Shacknews capture guide](https://www.shacknews.com/article/103008/monster-hunter-world-how-to-trap-a-monster)

## Caveats

- "Doubles" is *roughly/often*, not a hard universal 2×; treat the growth factor as a domain
  parameter. Blademaster hits only have a ~⅓ chance to contribute buildup — model probabilistic
  contribution at the controller layer, not in the plan.
- **Refuted:** "sleep bombing" as a coordinated burst tactic (one hunter sleeps, teammates
  pre-position bombs) did **not** survive verification (1-2). Do not model it as a sourced pattern.
- The weakened signal is described by Fextralife as a "weak status symbol" rather than strictly a
  skull icon; the substance (weakened → trap + 2 tranq) is confirmed by both sources.

## See also
- [`../team-patterns-catalog.md`](../team-patterns-catalog.md) — the cross-game pattern catalog
- `../../../components/primitives/tags/src.htn` — status application, the idiom the CC sketch extends
- `../../../Examples/GameHack7Combined.htn` — a worked two-ally stun + slow status combo
