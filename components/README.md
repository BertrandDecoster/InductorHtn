# Components

Reusable HTN building blocks: primitives → strategies → goals → levels (see
`docs/reference/component-system.md`). The owner rated both trees 3-4★: the architecture is
right, but they are work in progress. **Imitate their shape, not their details.** For a clean
example of the same ideas, read `Examples/Combos.htn`. For the words to use, read
`docs/authoring/vocabulary.md`.

| Tree | Keep | Don't copy |
|---|---|---|
| `gamehack/` | strategies that state feasibility in `if()`; `applyTag` with one method per way; `prepareToUseSkill` | `opTagAlreadyOnTarget` and `opStayInLocation` (no-op operators standing in for an empty `do()`), `useLocationToApplyTag` / `useMobSkillToApplyTag` with empty bodies, `stun_and_burn` (no world has its skills) |
| `primitives/`, `strategies/`, `goals/` | small verbs (`moveTo`, `applyTag`, `lureToRoom`), strategies as named methods | 1-, 2- and 3-hop `moveTo` ladders (the engine pathfinds: use one-step `goToLocation`), `player` hard-coded in `aggro`, do-nothing `else, if()` fallbacks, `connected` / `hasAggro` / `roomHasHazard` (use the vocabulary's words), `defeatEnemy`'s `else` between strategies |
| `challenges/` | one small challenge per file | 2-hop ladders, `agent` hard-coded, a new predicate in every file |

Editing a component changes the assembled goldens in `tests/fixtures/assembled/`. Re-run
`python -m pytest src/Python/tests/test_cli_assemble.py` after any change.
