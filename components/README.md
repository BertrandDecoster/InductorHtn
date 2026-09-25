# Components

Reusable HTN building blocks: primitives → strategies → goals → levels (see
`docs/reference/component-system.md`). The owner rated both trees 3-4★: the architecture is
right, but they are work in progress. On 2026-09-25 both were rewritten in the words and tag system
of `docs/authoring/vocabulary.md` (earlier versions: `archive/pre-vocabulary/`, `archive/pre-tag-system/`). For a clean
example of the same ideas, read `Examples/Combos.htn`.

| Tree | What it is | Still rough |
|---|---|---|
| `gamehack/` | wetAndFreeze, oilAndBurn and stunAndSlow, each with two distinct companions; skills from objects; doors with two plates | `complete_toy_level` names `door1` and `gob1` (rubric R8) |
| `primitives/`, `strategies/`, `goals/`, `challenges/` | small verbs; wetAndFreeze and oilAndBurn; `linked` maps; `clearLocation`; a one-plate door | `clearLocation` handles enemies in fact order |

The two trees define some of the same verbs, so a level depends on one of them.

Editing a component changes the assembled goldens in `tests/fixtures/assembled/`. Re-run
`python -m pytest src/Python/tests/test_cli_assemble.py` after any change.
