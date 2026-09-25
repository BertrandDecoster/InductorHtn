---
paths:
  - "**/*.htn"
---

# Writing .htn files

Before you write or change a ruleset, use the `htn-author` skill. It covers the workflow,
the rubric, the patterns and the checks.

**The owner's quality rule** (`docs/authoring/rubric.md`):
- **R1.** A strategy's `if()` states every property that makes it possible: the target, the
  actors (distinct with `\==`), the skills chosen **by property**, and the immunities ruled out.
  Its `do()` lists the **states to achieve**, with generic verbs that other strategies share.
- A script of one-off helpers ("scout, deploy trap, hide, finish") is slop.
- An effect or reaction engine that the strategies go through is slop.
- Invented jargon is slop. Use plain game words, and few of them.

**Dialect traps** (`docs/reference/language.md` explains and tests each one):
- Variables are `?x`, constants lowercase, and `if()` is required even when empty.
- `del` of a missing fact, or `add` of an existing one, is an error that **aborts the whole
  search**. Guard every operator in the calling method's `if()`.
- `else` is not a cut. A do-nothing `else, if()` fallback can let a plan skip work. Use the
  negated condition.
- `try()` commits: once it has run, the plan without it is never tried.
- An SWI built-in (`\+`, `\=`, `member`, `length`, `append`, `atom`, `var`) is **silently
  false**. There is no `;`. `/` on integers is integer division.
- Navigation is `pathNext` recursion, never 1-, 2- and 3-hop ladders.

**Checks:** a hook runs `python -m htn_components check --fast` after every `.htn` edit. Run
`check <file> --goal "task(args)."` to see the plans. Before calling the work done, have the
`htn-reviewer` agent score it.
