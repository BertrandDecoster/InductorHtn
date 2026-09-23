# Design of the Legacy InductorHtn

The original engine's design goals, distilled from the upstream project README
(now at [`../legacy/engine-readme.md`](../legacy/engine-readme.md)). This page
summarises intent; it does not restate the how-to.

## Origin

InductorHTN was first used in production in the iPhone strategy game
**Exospecies**. In the upstream author's words:

> This lightweight Hierarchical Task Network engine [...] is designed to be
> small, memory constrained, and used as an implementation detail of an app. It
> used the classic SHOP Planner as inspiration and largely followed that model.

## Design pillars

1. **SHOP model.** The planner follows the Simple Hierarchical Ordered Planner
   model — methods decompose tasks into ordered subtasks; operators apply
   primitive state changes.
2. **Memory-constrained.** Built to run inside a memory-limited mobile app, not
   a server. This drives the term factory's string/term interning, copy-on-write
   rule sets, and explicit memory budgets in the planner.
3. **Stackless execution.** The planner uses an explicit search stack and a
   continue-point state machine instead of native recursion, so it avoids
   recursion-depth limits and can pause/resume search. See
   [`../reference/planner-internals.md`](../reference/planner-internals.md).
4. **Embeddable in C++ and Python.** Native C++ with Python 3.x bindings via
   ctypes; built and tested on Windows, macOS, and Linux.

## Relationship to this fork

This fork keeps all four pillars and layers additions on top — see
[`../upgrades/`](../upgrades/) for the new ruleset keywords and planner
instrumentation, and [`language-design.md`](language-design.md) for the
ruleset-language choices.
