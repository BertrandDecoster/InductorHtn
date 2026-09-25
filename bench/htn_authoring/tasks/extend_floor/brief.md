# Extend: fragile floors

`task/domain.htn` is a working ring-out domain. Companions defeat an enemy by knocking it off
an edge into a drop, bringing it to an edge first (pull or taunt) when needed. Read it first.

Add a second way to make an enemy fall: **breaking a fragile floor under it.** Edit
`task/domain.htn` in place. Everything the domain does today must keep working exactly as it
does. `task/problem.htn` is a sample level. The grader runs the domain on other levels. Do not
put level facts in the domain, and don't name specific areas, companions or skills in it.

## The new rules

- `fragile(?area, ?drop)`: the floor of that area can collapse into that drop. An area can have
  several such drops, and an area can be both an edge and fragile.
- A new skill kind, `quake`: `skillKind(?skill, quake)`. Breaking a floor needs no walking;
  the companion does it from wherever they stand. An enemy can be `immune(?e, quake)`.
- **Break.** The enemy stands on a fragile area: a companion with a quake skill breaks the
  floor (`opBreak`), and the enemy falls into one of its drops (`opFall`).
- **Bring, then break.** The enemy is not on a fragile area. A fragile area is directly linked
  to the enemy's area. A bringer brings the enemy there by pull or taunt, exactly as the
  existing domain brings enemies to an edge. Then a **different** companion breaks the floor.

`ringOut(?e)` must now return the existing plans plus **one plan for every break
combination**: each companion and quake skill, each fragile area that works, each drop, and
each bringer and bringing skill.

## New operators (use these exactly)

```prolog
opBreak(?who, ?skill, ?area) :- del(), add(broken(?area)).
opFall(?e, ?area, ?drop) :- del(at(?e, ?area)), add(fell(?e, ?drop)).
```

Step order: the bringing steps, as today, then `opBreak`, then `opFall`.
