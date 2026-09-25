# Guard

Write an InductorHTN domain for a game guard's behaviour. Each time it is called, it picks what
the guard does next, by priority.

Put the domain in `task/domain.htn`. It holds methods, operators and rules only.
`task/problem.htn` is a sample state. The grader runs your domain on many other states. Do not
put state facts in the domain, and don't name specific areas or characters in it.

## The task

`think(?g)`. `FindAllPlans` must return **exactly one plan**: the highest-priority behaviour
that can actually be carried out. A behaviour that applies but cannot be carried out (for
instance, its destination cannot be reached) gives way to the next one.

1. **Heal.** Health below 30, and there is a medkit: walk to the first medkit listed and heal.
   Only that first medkit is considered.
2. **Fight.** The guard sees an enemy: fight the first enemy listed in its `sees` facts.
   - Same area, ammo left: shoot.
   - Same area, no ammo: melee.
   - Enemy in a directly linked area, ammo left: shoot from where the guard stands.
   - Otherwise: walk to the enemy's area and melee.
3. **Investigate.** There is a noise: walk to the first noise listed and search there.
4. **Patrol.** Walk to the patrol target waypoint, then advance the target to the next
   waypoint.

**Walking:** one link at a time, along the shortest route. No steps if already there.

## World facts

```
linked(?a, ?b)            at(?who, ?area)
health(?g, ?hp)           ammo(?g, ?n)          medkit(?area)
sees(?g, ?enemy)          noise(?area)
patrolTarget(?g, ?waypoint)   nextWaypoint(?waypoint, ?next)
```

## Operators (use these exactly)

```prolog
opMoveTo(?who, ?from, ?to) :- del(at(?who, ?from)), add(at(?who, ?to)).
opHeal(?g, ?area) :- del(medkit(?area)), add(healed(?g)).
opShoot(?g, ?e, ?old, ?new) :- del(ammo(?g, ?old)), add(ammo(?g, ?new), hit(?e)).
opMelee(?g, ?e) :- del(), add(hit(?e)).
opSearch(?g, ?area) :- del(noise(?area)), add(searched(?area)).
opNextWaypoint(?g, ?w, ?next) :- del(patrolTarget(?g, ?w)), add(patrolTarget(?g, ?next)).
```

`opShoot` takes the ammo before and after, e.g. `opShoot(g1, thief, 3, 2)`.
