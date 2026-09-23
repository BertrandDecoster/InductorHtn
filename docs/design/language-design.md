# Language Design

> **Status: DRAFT — to be written by the author.**
>
> This page should capture *why* the ruleset language looks the way it does.
> The codebase shows *what* the language is (see
> [`../reference/htn-syntax.md`](../reference/htn-syntax.md) and
> [`../reference/prolog-reference.md`](../reference/prolog-reference.md)) — but
> the rationale below lives only in the author's head and must not be invented.

## TODO

- **Why the `?varname` dialect** instead of standard Prolog capitalization?
  What problem did it solve; what was the trade-off?
  - TODO: author to fill.
- **Why SHOP-style methods/operators** as the surface syntax (vs. alternatives
  considered)?
  - TODO: author to fill.
- **Design of the modifiers** (`else`, `anyOf`, `allOf`, `hidden`, `try`,
  `first`) — what gap each one fills.
  - TODO: author to fill.
- **Numeric fluent effects** (`increase`/`decrease`) — why add sugar over
  `del`+`add`+`is`?
  - TODO: author to fill.
- **Typed parameters as opt-in facts** (`type/2`, `signature/2`) rather than a
  built-in type system — rationale and intended evolution.
  - TODO: author to fill.

## See also

- [`legacy-inductorhtn.md`](legacy-inductorhtn.md) — the engine the language sits on
- [`hddl.md`](hddl.md) — what HDDL contributed to the design thinking
