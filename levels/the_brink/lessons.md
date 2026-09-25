# Lessons from The Brink

Rules that turned out to matter while building and iterating this level, each with the evidence
that showed it. The ruleset-authoring docs are written from this file.

1. **Decompose from the enemy's weakness, and give each way to cause it a method.**
   `defeat(?e)` asks `vulnerable(?e, ?how)`, then calls `apply(?e, ?how)`, which has one method
   per way (`bringAndPush`, `cutTheFloor`). Adding a way means adding a clause. Evidence: with
   the default kit, `defeat(gob)` gives exactly one plan per way (exploit_weakness Example 2).
   The plan set per kit is stated in the header and checked (the_brink P1).

2. **A strategy is two or three needs, not a script.** `bringAndPush = bringTo + forceInto`.
   Every alternative comes from a lower need (who can bring, who can force), so the plan count
   is a product that can be predicted. It was predicted before each run in all four rounds.
   The old `Examples/RingOut.htn` instead copied a design table into three methods that named
   areas and skills.

3. **Think in movements and tags, not skills** (user, 2026-09-25). A skill is only a name for
   what it does. It is declared as data (`skillElement(gust, push)`), and methods reason only
   about the movement or element: a push, a pull, a taunt, fire. What an NPC resists is a fact
   on the NPC, `immune(?e, push)`, not a quirk inside a skill's method. Evidence: core had
   `metal(?e)` inside `lure`/`push`, and The Brink's puzzle rested on that quirk. The design
   text and plan tables also spoke in skill names ("gust + ignite: 2 plans"); they now speak
   in movements ("push + fire").

3b. **Give a movement its geometry.** A push sends an NPC away from the caster and a pull
   brings it toward the caster (`aims`/`takeAim` in core_world). Without that, core let the
   Warden pull the bearer into the void from the gate. With it, nothing is pulled into a drop
   unless someone stands beyond it, so the level needed a far ledge (round 6). The geometry
   produced a better puzzle than the quirk did: push from the near side, pull from the far
   side.

4. **Resources force cooperation. Role rules are not needed for that.** Round 2: each companion
   solo'd "its" enemy (unlimited magnet in and magnet over). Round 3: one charge on the magnet
   fixed it. Round 4: one charge on the dash removed the last single-actor plan.

5. **Check solo plans in every kit, not just the default one.** The scorecard's F6 only reads the
   default kit, so a {dash, ignite} plan carried by the player alone went unseen until a
   per-kit sweep flagged it. The level's P2 test now covers every kit.

6. **Probe bottom-up when a plan is missing.** v1 gave no plan at all. Probing
   `bringTo` → `push` → `bringAndPush` → `defeat` one level at a time located the cause: a
   vantage three hops away, while core `navigate` walks two. The fix was a line of sight in the
   level, not a rule change.

7. **Every cost is paid through the same `payFor`.** Core `lure` skipped `payFor`, so a charge on
   the magnet did nothing. The fix went into core_aggro with a property test (P4), and every
   core test and grease_trap still pass.

8. **`try(X)` does X whenever X can be done.** It does not produce a second plan that skips X.
   So `try(bringOthers(...))` means "take everyone who can be brought". `defeat(bearer)` gives
   one plan, not two.

9. **`verify` does not run the loadout sweep**, so a `funExpect` on `loadout_feasibility` is
   reported as MISS there. Kit-level claims belong in the level's `test.py`.

10. **Playing through shows presentation problems the metrics don't.**
    - Paying for a skill is a separate step from casting it. A wasted charge therefore shows up
      as a loss before any target is chosen.
    - The fall is a separate `opStatus` action the player has to take.
    - Companion intentions narrate the bookkeeping ("I'll spend one magnetize charge").
    - The observation lists charges for skills the player doesn't hold.

11. **A physics fix in a shared primitive changes every level built on it, so re-measure them.**
    After round 5, grease_trap still passed its tests and its F1/F3/F4. But player load rose
    (0.58 to 0.65), because pushers now walk to the correct side of their target. Tests
    passing is not the same as the design being unchanged; rerun `fun` on every dependent
    level.

12. **Report a failing family instead of tuning it away.** F2 fails for The Brink's default
    kit: its two plans differ only in where the ogre is pushed. That is a true statement
    about that kit. `verify` gates only on `funExpect` and F7, so the failure is recorded in
    the hypothesis as known.
