# Extend: burning on oil

`task/domain.htn` is a working domain for a cooperative game. Allies find every way to
`damage(?e)` an enemy, by making it wet then electrocuting it, or by stunning and slowing it at
the same moment. Read it first. Tags, skills, luring and learning work as it shows.

Add a third way to damage an enemy: **burning on oil.** Edit `task/domain.htn` in place.
Everything the domain does today must keep working. `task/problem.htn` is a sample level. The
grader runs the domain on other levels. Do not put level facts in the domain, and don't name
specific characters, places or skills in it.

## The new rule

- Some locations are oily: `oily(?l)`.
- An enemy standing at an oily location that gets the fire tag is damaged.
- An enemy immune to fire can't be burned. A static enemy can't be moved to the oil, so it can
  only burn if it already stands on oil.

`damage(?e)` must now also return the burn plans. Each plan must end with the enemy damaged,
recorded as `damaged(?e)`, and there must be no plan when the enemy can't be damaged.
