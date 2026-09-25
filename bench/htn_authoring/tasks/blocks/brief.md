# Blocks

Write an InductorHTN domain that solves blocks-world problems. This is the classic HTN blocks
domain; solve it the way hierarchical planners do, not by blind search.

Put the domain in `task/domain.htn`. It holds methods, operators and rules only.
`task/problem.htn` is a sample problem. The grader runs your domain on other problems (up to
six blocks, several towers, blocks with no goal, problems that are already solved). Do not put
problem facts in the domain.

## The task

`solve`. `FindAllPlans` must return **exactly one plan**. Its final state must satisfy every
goal fact, and it must not move blocks more than necessary: moving each block straight to its
final place when it can go there, and otherwise out of the way onto the table, is good enough.

## World facts

```
block(?b)
on(?b, ?c)      onTable(?b)     clear(?b)      handEmpty      holding(?b)
goalOn(?b, ?c)  goalOnTable(?b)   % a block may have no goal at all
```

## Operators (use these exactly)

```prolog
pickup(?b) :- del(onTable(?b), clear(?b), handEmpty), add(holding(?b)).
unstack(?b, ?c) :- del(on(?b, ?c), clear(?b), handEmpty), add(holding(?b), clear(?c)).
putdown(?b) :- del(holding(?b)), add(onTable(?b), clear(?b), handEmpty).
stack(?b, ?c) :- del(holding(?b), clear(?c)), add(on(?b, ?c), clear(?b), handEmpty).
```
