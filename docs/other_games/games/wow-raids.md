# WoW Raid Encounters — evidence appendix
The richest verified source of threshold-driven team coordination beats.

World of Warcraft Mythic raid encounters are scripted, numeric, and exhaustively documented by
top-tier guide sites. That makes them the single best-mined source in this study: nearly every
mechanic reduces to "an agent performs a discrete action when a numeric/state condition holds",
which is exactly the HTN method/operator split.

See the cross-game synthesis in [`../team-patterns-catalog.md`](../team-patterns-catalog.md).

## Patterns this game exemplifies

| Catalog pattern | Tactic from this game |
|-----------------|-----------------------|
| [1 — Role assignment](../team-patterns-catalog.md#problem-1--role--responsibility-assignment) | Fixed Mythic composition (Volcoross = 2 tanks / 4 healers / 14 DPS) |
| [2 — Threat & aggro](../team-patterns-catalog.md#problem-2--threat--aggro-management) | Taunt-based tank swap at a debuff-stack threshold (Salhadaar, ~8 stacks) |
| [3 — Focus fire](../team-patterns-catalog.md#problem-3--focus-fire--target-prioritization) | Concentrated Void orbs as a forced top-priority target swap |
| [4 — Positioning](../team-patterns-catalog.md#problem-4--positioning--formation) | Despotic Command run-to-edge; non-overlapping soak circles |
| [5 — Timing](../team-patterns-catalog.md#problem-5--timing--synchronization) | Coiling Eruption: ≥2 simultaneous soakers per circle |
| [7 — Cooldown economy](../team-patterns-catalog.md#problem-7--resource--cooldown-economy) | Hold the dispel until the target repositions, then dispel + remove heal-absorb |
| [9 — Phase transitions](../team-patterns-catalog.md#problem-9--phase--state-transitions-medium-confidence) | Orb spawn forces event-driven re-prioritization off the boss |
| [11 — Safety constraints](../team-patterns-catalog.md#problem-11--safety-constraints) | Soak-no-overlap; Despotic Command pulses AoE onto nearby allies |

## Verified tactics

**Tank swap (threshold-driven aggro transfer).** Destabilizing Strikes is applied on every boss
auto-attack; the team swaps tanks **at around 8 stacks**. A taunt forces the boss onto the taunter
for ~6 seconds and equalizes the taunter's threat to the current holder's. Correct execution: the
incoming tank stands in *exactly* the current tank's spot before taunting (so the boss does not
move), times a high-threat ability to land immediately after the taunt, and the outgoing tank stops
high-threat abilities for a few seconds to let aggro settle.
— [Icy Veins Salhadaar guide](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide),
[Icy Veins tanking guide](https://www.icy-veins.com/wow/tanking-guide)

**Focus fire on priority adds.** Concentrated Void orbs must be killed ASAP — "DPS should swap to
these" — because an orb reaching the boss buffs it and wipes the raid. Refinement: each orb kill
applies a stacking raid-wide DoT, so kills are staggered between two orbs.
— [Icy Veins Salhadaar guide](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide)

**Spread-debuff repositioning + dispel economy.** A player hit by Despotic Command pulses AoE onto
nearby allies and must run to the room edge; the healer holds the dispel until they are clear, then
dispels *and* removes the attached heal-absorb.
— [Icy Veins Salhadaar guide](https://www.icy-veins.com/wow/fallen-king-salhadaar-raid-guide)

**Soak constraints.** Coiling Eruption wants "the maximum amount of players to soak, at least 2 per
soak", and the soak circles "are not allowed to overlap" or a wipe mechanic triggers.
— [Method.gg Volcoross guide](https://www.method.gg/guides/amirdrassil-the-dreams-hope/volcoross)

**Fixed composition.** Mythic Volcoross is listed as 2 Tanks, 4 Healers, 14 DPS (the 20-player cap).
— [Method.gg Volcoross guide](https://www.method.gg/guides/amirdrassil-the-dreams-hope/volcoross)

## Caveats

- WoW figures (taunt ~6s, swap ~8 stacks, Salhadaar) are current for **Patch 12.0.0 (2026)** and
  change with patches. Volcoross is from **Dragonflight 10.2**, a closed historical tier.
- Role counts are *recommended/optimal*, not game-enforced (only the 20-player cap is enforced).
- Treat all threshold numbers as **tunable domain parameters**, not constants.

## See also
- [`../team-patterns-catalog.md`](../team-patterns-catalog.md) — the cross-game pattern catalog
- `../../../components/primitives/aggro/src.htn` — `hasAggro/2`, the fact the tank-swap sketch reuses
- `../../../components/primitives/locomotion/src.htn` — `moveTo`, used for tank pre-positioning
