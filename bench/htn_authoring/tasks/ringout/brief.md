# Ring-out

Write an InductorHTN domain for a cooperative puzzle: companions defeat an enemy by knocking it
off an edge into a drop. Nothing else can hurt it.

Put the domain in `task/domain.htn`. It holds methods, operators and rules only.
`task/problem.htn` is a sample level. The grader runs your domain on other levels, with other
maps, companions, skills, enemies and resistances. Do not put level facts in the domain, and
don't name specific areas, companions or skills in it.

## The designer's strategies

`ringOut(?e)`. `FindAllPlans` must return exactly the plans below. **Every combination is its
own plan**: each companion and skill that can do a step, each edge area that works, and each
drop.

1. **Knock.** If the enemy already stands in an edge area (an area with at least one drop),
   any companion who knows a push skill walks to the enemy's area and pushes it into a drop of
   that area.
2. **Bring, then knock.** If the enemy is not in an edge area, one companion (the bringer)
   brings it into an edge area directly linked to the enemy's area. Then a **different**
   companion walks there and knocks it, as in 1. There are two ways to bring it:
   - **Pull:** the bringer walks to the edge area and pulls the enemy there.
   - **Taunt:** the bringer walks to the edge area and taunts; the enemy chases into the
     bringer's area.

An enemy can be immune to push, to pull or to taunt: `immune(?e, pull)`. An immune enemy cannot
be affected that way. A companion may know several skills.

**Walking:** a companion walks one link at a time, along the shortest route, to the area where
the step happens. A companion already there doesn't move. Routes can be any length.

## World facts

```
linked(?a, ?b)          both directions are listed
edge(?area, ?drop)      the area borders that drop; an area can border several drops
companion(?c)           at(?who, ?area)   (companions and enemies)
knows(?c, ?skill)       skillKind(?skill, push | pull | taunt)
immune(?enemy, push | pull | taunt)
```

## Operators (use these exactly)

```prolog
opMoveTo(?who, ?from, ?to) :- del(at(?who, ?from)), add(at(?who, ?to)).
opPush(?who, ?skill, ?e, ?area, ?drop) :- del(at(?e, ?area)), add(fell(?e, ?drop)).
opPull(?who, ?skill, ?e, ?from, ?to) :- del(at(?e, ?from)), add(at(?e, ?to)).
opTaunt(?who, ?skill, ?e) :- del(), add(taunted(?e, ?who)).
opChase(?e, ?from, ?to) :- del(at(?e, ?from)), add(at(?e, ?to)).
```

Step order in a plan: the bringer's walk, then the pull, or the taunt followed by the chase. Then
the knocker's walk, then the push.
