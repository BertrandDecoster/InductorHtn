# Commute

Write an InductorHTN domain for getting a person from where they are to a destination.

Put the domain in `task/domain.htn`. It holds methods, operators and rules only. The world
facts come from a separate problem file: `task/problem.htn` is a sample. The grader also runs
your domain against other problems with different people, places and numbers. Do not put
problem facts in the domain.

## The task

`travel(?who, ?to)`. `FindAllPlans` must return **one plan for every way of getting there
that works** (walk, bike, taxi, bus). The order of the plans doesn't matter.

- **Already there:** if `?who` is already at `?to`, the only plan is the empty plan.
- **Walk:** `walk(?who, ?from, ?to)`. Allowed when the weather is good and the distance is at
  most 3, or in any weather when the distance is at most 0.5. Walking is one plan, even when
  both conditions hold.
- **Bike:** `cycle(?who, ?from, ?to)`. Allowed when the person owns a bike, the weather is good
  and the distance is at most 10.
- **Taxi:** `hail`, then `ride`, then `pay`. The fare is 2 + distance, and the person must have
  at least the fare in cash. They hail the first taxi at a stand where they are (only one taxi
  plan, however many taxis wait there).
- **Bus:** `waitFor`, then `ride`, then `pay`. The fare is 1, and the person needs at least 1
  in cash. Every bus route from here to the destination is its own plan.

## World facts (the problem files use exactly these)

```
at(?who, ?place)            weather(good) or weather(bad)
cash(?who, ?amount)         ownsBike(?who)
distance(?from, ?to, ?km)   listed in both directions
taxiStand(?taxi, ?place)    busRoute(?bus, ?from, ?to)
```

## Operators (use these exactly)

```prolog
walk(?who, ?from, ?to) :- del(at(?who, ?from)), add(at(?who, ?to)).
cycle(?who, ?from, ?to) :- del(at(?who, ?from)), add(at(?who, ?to)).
hail(?who, ?taxi, ?place) :- del(), add(hailed(?who, ?taxi)).
waitFor(?who, ?bus, ?place) :- del(), add(boarded(?who, ?bus)).
ride(?who, ?vehicle, ?from, ?to) :- del(at(?who, ?from)), add(at(?who, ?to)).
pay(?who, ?old, ?new) :- del(cash(?who, ?old)), add(cash(?who, ?new)).
```

`pay` takes the cash before and the cash after, e.g. `pay(ann, 12, 8)`.
