# Grease fire

Write an InductorHTN domain for a cooperative puzzle: companions burn flammable enemies by
setting fire to oil under them.

Put the domain in `task/domain.htn`. It holds methods, operators and rules only.
`task/problem.htn` is a sample level. The grader runs your domain on other levels. Do not put
level facts in the domain, and don't name specific areas, companions, skills or enemies in it.

## How the world works

- Fire is only dangerous on oil. When a companion ignites an oiled area, the area is ablaze
  and stays ablaze.
- A flammable enemy standing in an ablaze area is burned. One fire burns every flammable enemy
  in that area.
- Every skill has an element (`oil`, `fire` or `lure`) and a number of charges. Each use spends
  one charge first (`opSpend`, then the effect). A skill with 0 charges can't be used.
- Casting oil or fire needs no walking: a companion can cast into any area from where they
  stand. Luring needs the lurer to stand in the area the enemy is lured into.
- Companions are interchangeable. The same companion may do several steps if they have the
  skills and charges.

## The tasks

`burnOut(?e)` burns one enemy. `FindAllPlans` must return one plan for **every** way below,
and for every companion and skill that can do each step:

1. **Ignite.** The enemy stands in an oiled area: a companion with a fire skill ignites it.
2. **Spill and ignite.** The enemy's area is not oiled: a companion with an oil skill spills
   oil there (`opSpill`), then a companion with a fire skill ignites it.
3. **Lure into oil.** The enemy's area is not oiled. An oiled area that is **not already
   ablaze** is linked to it. A companion with a lure skill walks there (one link at a time,
   shortest route) and lures (`opLure`). The enemy follows (`opChase`). Then a companion with a
   fire skill ignites that area.

`clear` burns every flammable enemy. It takes the enemies one at a time, always next the first
unburned flammable enemy in the order of the `enemy(?e)` facts, and burns it as `burnOut` does.
An enemy that is already burned (because a fire took it along) is skipped. When no unburned
flammable enemy is left, the rest of the plan is empty. If some flammable enemy cannot be
burned, there is no plan. Non-flammable enemies are ignored.

## World facts

```
linked(?a, ?b)       both directions are listed
oiled(?area)         ablaze(?area)
companion(?c)        at(?who, ?area)   (companions and enemies)
knows(?c, ?skill)    skillElement(?skill, oil | fire | lure)    charges(?c, ?skill, ?n)
enemy(?e)            flammable(?e)
```

## Operators (use these exactly)

```prolog
opMoveTo(?who, ?from, ?to) :- del(at(?who, ?from)), add(at(?who, ?to)).
opSpend(?who, ?skill, ?old, ?new) :- del(charges(?who, ?skill, ?old)), add(charges(?who, ?skill, ?new)).
opSpill(?who, ?skill, ?area) :- del(), add(oiled(?area)).
opIgnite(?who, ?skill, ?area) :- del(), add(ablaze(?area)).
opLure(?who, ?skill, ?e) :- del(), add(lured(?e, ?who)).
opChase(?e, ?from, ?to) :- del(at(?e, ?from)), add(at(?e, ?to)).
```

Step order for a lure: the walk, then `opSpend`, `opLure`, `opChase`, then the ignite (its
`opSpend`, then `opIgnite`).
