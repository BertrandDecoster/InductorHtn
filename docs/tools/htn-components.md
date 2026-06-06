# Components CLI (`htn_components`)

Build, certify, test, and assemble the reusable HTN component library.

```bash
PYTHONPATH=src/Python python -m htn_components <command>
```

## Commands

```
status                           # List all components with certification status
test <path>                      # Run tests for a component
certify <path> [--dry-run]       # Full certification (linter + tests + design)
new <path>                       # Create a component from template
coverage <path>                  # Check design-to-test coverage

play <level>                     # Step-by-step plan narrative
trace <level> [--goal GOAL]      # Decomposition tree visualization

test-all [--layer <layer>]       # Run all component tests
verify <level>                   # Full level verification (assemble + certify deps + test)
evaluate <level>                 # Plan-space richness (solvability, difficulty, operator variety)
library-coverage [--layer <l>]   # Aggregate plan-space metrics across all levels

assemble <level> [-o <path>]     # Assemble level + deps into a single .htn
  [--no-verify]                  #   write output without running the verifier
  [--verify-only]                #   run the verifier but skip writing output
  [--skip-compile-check]         #   skip the C++ HtnCompile round-trip
```

## Concepts

The component system has four layers — **Primitives → Strategies → Goals →
Levels** — with a certification workflow and a 3-layer assembly verifier. The
full conceptual model, directory layout, certification rules, typed-parameter
diagnostics, and assembly verifier codes are documented in
[`../reference/component-system.md`](../reference/component-system.md).

To step through an assembled level interactively, see the challenge-play
protocol in [`../reference/challenge-play-protocol.md`](../reference/challenge-play-protocol.md).
