# Damage the enemy

Design and write an InductorHTN domain for a cooperative game. The allies find every way to
damage an enemy. You choose the tasks, methods and operators.

Put the domain in `task/domain.htn`. It holds methods, operators and rules only.
`task/problem.htn` is a sample level. The grader runs your domain on other levels, with other
characters, places, skills and immunities. Do not put level facts in the domain, and don't
name specific characters, places or skills in it.

## The game

- Characters (allies and enemies) stand at locations. An ally can move to any location in one
  step. The game engine handles pathfinding.
- An enemy doesn't move on its own, but an ally can lure it: the ally goes to the enemy,
  draws its attention, and walks to another location; the enemy follows. An enemy marked
  static never moves.
- Skills put **tags** on characters. A skill has the tags it applies, and it can also have
  properties (a fireball applies fire and has the slow property).
- A character gets a tag in one of three ways:
  - an ally uses a skill that applies it, from the same location;
  - the character stands at a location that applies it;
  - another non-ally character (for instance a static lightning tower) uses a skill that
    applies it, and the two must be at the same location.
- An ally can learn a skill at a location that teaches it. Learning replaces the ally's
  current skill, if they have one.
- An enemy immune to a tag never gets that tag.

An enemy is **damaged** by a combination:

- **Wet, then electrocuted:** once it has the wet tag, electrocute it.
- **Stunned and slowed at the same moment:** two different allies act in sync, one with a
  skill that applies stun, the other with a skill that has the slow property.

## The task

`damage(?e)`. `FindAllPlans` must return the ways to damage `?e`. Each plan must end with the
enemy damaged. There must be no plan when the enemy can't be damaged.

## Facts the levels use

```
ally(?a)   enemy(?e)   location(?l)   at(?who, ?l)   static(?who)
hasSkill(?who, ?skill)   skillAppliesTag(?skill, ?tag)   skillHasTag(?skill, ?property)
locationCanApplyTag(?l, ?tag)   canGetSkillAtLocation(?l, ?skill)   immune(?e, ?tag)
```

## What your operators must record

Your operators are up to you, but the state must show outcomes with these facts:
`at(?who, ?l)` for positions, `hasTag(?who, ?tag)` for tags, `hasSkill(?who, ?skill)` for
skills, and `damaged(?e)` once the enemy is damaged.
