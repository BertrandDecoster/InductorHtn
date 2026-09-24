# The ability catalogue

The standard tags and skills of the ability layer ([`ability-system.md`](ability-system.md)),
in `components/abilities/primitives/ab_catalog`: **11 skills, 14 atomic tags (one of them an aura),
3 composites, 2 outcomes, 2 enemy moves, 25 looks**.

## The rules the catalogue follows

1. **Few skills, each with several uses.** Each skill lands a tag and a movement, or two tags, and
   is the answer to more than one kind of problem: Translocate crosses a gap, gets past a guard,
   ferries a friend, dodges a heavy blow, and puts an enemy under that blow.
2. **Tags are atomic or composite.** An atomic tag has one gameplay meaning. A composite is a named
   bundle of atoms, one level deep: stunned = blinded + silenced + rooted.
3. **A look is not a tag.** Statuses that play identically but look different (petrified and
   knocked-down are a stun; webbed is a slow) are listed as `appearance(?look, ?tag)`. The runtime
   draws the look; the planner only sees the tag.
4. **Nothing grants an outcome.** `dead` and `fell` come only from an enemy's own
   `weakness(?e, ?in, ?have, ?out)`, or from a hazard it is weak to. A combo is deadly because of who
   it lands on: a robot is stunned by a jolt and short-circuits if soaked first; a fire imp freezes
   solid when chilled; a living enemy soaked and jolted only seizes up.
5. **Frozen is a stun, not a kill.** Wet plus chilled freezes most enemies: they are stunned, and
   even the heavy can be pushed on the ice. A stunning blow then shatters them (Shield Bash), and fire
   thaws them. Only fire elementals and insects die of the cold. Bosses cannot be stunned or frozen.
6. **No damage.** Damage is incremental, and this layer is about the combos.
7. **Temporary without a clock.** A temporary effect lasts as long as its cause: `magnetized` is an
   aura of the magnetic field, carried only while standing in it, so a guard's armour works again
   the moment it leaves. `phased` lasts until the next heavy blow on its region, or until its bearer
   acts.
8. **Heavy attacks are telegraphed, and only they are.** An enemy move marked `heavy(?ab)` winds up
   on a region; the team gets one cast (no walking); then it lands on everyone there but the enemy.
   A companion still in it is downed, so the plan must not allow it. You provoke a heavy blow on
   purpose (it stuns and throws whatever it hits, or caves the floor in) and survive it with a
   skill: disjoint (Translocate, Lightning Flash, Hook onto an anchor), phase (Blinding Flash), be
   carried out (a friend's Translocate or Tidal Wave), or interrupt (Shield Bash stuns, and a
   silenced enemy stops winding up; not a boss).

## Using it in a level

```prolog
% Zones: place the standard zone abilities; hazards take whoever is weak to them.
onEnter(crypt, shadows).  onEnter(abyss, chasm).
beyond(hall, brink, abyss).                    % push lines
% Companions pick skills from the catalogue.
knows(mage, blindingFlash).  knows(warden, shieldBash).  mana(player, 3).
% Enemies: rank, traits, element, extra weaknesses, starting tags, behaviours.
trait(sentry, machine).  trait(sentry, metal).  tag(sentry, shielded).
rank(brute, boss).  trait(brute, living).  tag(brute, armored).
behavior(brute, taunted, groundSlam, source).  % taunted, it slams where you stand
weakness(golem, electrocuted, oiled, dead).    % a level can add its own
mustSurvive(envoy).                            % an escort a heavy blow must miss
```
The level depends on `abilities/goals/neutralize` and `abilities/primitives/ab_catalog`.

## Skills

"Around" is the caster's region and the regions next to it.

| Skill | Reach | Mana | Tags, and on whom | Movement, and of whom |
|-------|-------|------|-------------------|-----------------------|
| **Hook** | ranged | - | the target loses `flying` | a light target is pulled to the caster, falling into any live hazard between; an anchored one pulls the **caster** to it |
| **Vortex** | ranged, a region | - | - | everything in the regions next to the target region is pulled **into** it (not the caster, not the anchored) |
| **Tidal Wave** | self | 2 | the caster's region becomes a puddle: everyone in it, **the caster too**, is `wet`, and so is whoever walks in later; everyone next door is `wet` | everyone next door is pushed one region further **away** from the caster |
| **Blizzard** | ranged, a region | 2 | the region becomes an ice sheet: everyone there now and later is `chilled` (slowed); the `wet` freeze instead; fire elementals and insects die | - |
| **Fireball** | ranged | 2 | the target's region becomes flames: everyone there now and later is `burning` | the target is pushed away from the caster |
| **Lightning Flash** | ranged | 2 | everyone on the path between caster and target, and the target, is `electrocuted` | the **caster** teleports to the target's region |
| **Translocate** | ranged | - | - | at a region: the **caster** teleports there; at an entity: the two **swap** |
| **Blinding Flash** | self | - | the **caster** is `phased`; everyone around is `blinded` and loses `stealthed` | - |
| **Taunt** | ranged | - | the target is `taunted`, which sets off its behaviours | the target is dragged to the caster, falling into any live hazard between |
| **Magnetic Orb** | ranged, a region | 2 | the region becomes a magnetic field: whoever stands in it is `magnetized` | metal things next to the field are pulled into it |
| **Shield Bash** | melee | - | the target is `stunned` (and a heavy attack it was winding up stops) | the target is pushed away from the caster |

## Enemy moves

A level gives them to NPCs with `behavior(?npc, ?trigger, ?move, source|self|here|there(R))`.

| Move | Heavy | On everyone in the struck region but the attacker |
|------|-------|----------------------------------------------------|
| `groundSlam` | yes | `stunned`, and pushed away from the attacker |
| `caveIn` | yes | the floor becomes a chasm: whoever is weak to it falls |

## Tags

### Atomic

| Tag | Does | Put on by | Looks |
|-----|------|-----------|-------|
| `blinded` | no basic attack; cannot keep watch | Blinding Flash; bundled in stunned, frozen | disarmed, nearsighted |
| `silenced` | no skills; a heavy attack winding up stops | bundled in stunned, frozen | - |
| `rooted` | no walking, no dashing | bundled in stunned, frozen | snared, entangled, netted |
| `slowed` | no dashing | bundled in chilled | webbed, crippled |
| `wet` | fire on it: steam (wet goes); cold on it: frozen | Tidal Wave, puddle, deepWater, a thaw | drenched |
| `oiled` | fire on it: blaze (everyone there burns) | slick (a level places it) | - |
| `burning` | water puts it out, cold quenches it; kills the wooden | Fireball, flames, blaze | ignited |
| `electrocuted` | stuns machines, kills wet machines and water elementals, stuns the wet living | Lightning Flash | shocked |
| `taunted` | dragged to the taunter | Taunt | provoked |
| `stealthed` | cannot be aimed at | shadows (a level places it) | invisible, camouflaged |
| `shielded` | takes the next hostile tag instead | innate | warded |
| `armored` | cannot be moved by force | innate | barkskin, ironclad |
| `invulnerable` | no hostile tag lands; a heavy blow passes through | innate | untouchable |
| `flying` | does not fall | innate | hovering |
| `phased` | untargetable; no hostile tag lands, nothing moves it, a heavy blow passes through; spent by the next blow on its region, or by acting | Blinding Flash | blinking |
| `magnetized` | *aura, never stored:* armour and shields do nothing; the heavy can be moved | standing in a magnetic field (Magnetic Orb) | - |

### Composite

| Tag | = atoms | Also | Put on by | Looks |
|-----|---------|------|-----------|-------|
| `stunned` | blinded + silenced + rooted | a boss is immune | Shield Bash, a groundSlam, a jolt on a machine or a wet living thing | petrified, paralyzed, knockedDown, dazed |
| `chilled` | slowed | on the wet: frozen | Blizzard, iceSheet | frostbitten |
| `frozen` | blinded + silenced + rooted | even the heavy can be pushed; a stunning blow shatters it (dead); fire thaws it to wet; a boss is immune | wet + chilled, either way round | encased |

### Outcomes

| Outcome | Comes from |
|---------|------------|
| `dead` | an enemy's weakness: a wet machine electrocuted, a water elemental electrocuted, a fire elemental or an insect chilled, a wooden thing burning, anything frozen given a stunning blow |
| `fell` | a hazard: a chasm (not fliers), lava (not fliers, not things of fire), deep water (the heavy) |

## Reactions (for everyone)

| Have | Incoming | Reaction | Does |
|------|----------|----------|------|
| `shielded` | any hostile tag | absorb | the shield goes; the tag does not land |
| `wet` | burning | steam | wet goes |
| `burning` | wet | extinguish | burning goes |
| `oiled` | burning | blaze | oiled goes; it and everyone in its region burn |
| `burning` | oiled | blaze | as above |
| `wet` | chilled | freeze | wet goes; frozen |
| `chilled` | wet | freezeOver | chilled goes; frozen |
| `chilled` | burning | thaw | chilled goes |
| `frozen` | burning | meltdown | frozen goes; wet |
| `burning` | chilled | quench | burning goes |

## Zones

| Zone | Whoever is in it or enters | Spilled by |
|------|---------------------------|------------|
| `puddle` | wet | Tidal Wave (under the caster) |
| `flames` | burning | Fireball |
| `iceSheet` | chilled | Blizzard |
| `magnetField` | magnetized while there (aura) | Magnetic Orb |
| `slick` | oiled | - |
| `shadows` | stealthed | - |
| `chasm` | falls, if weak to it | caveIn |
| `lava` | falls, if weak to it | - |
| `deepWater` | wet; the heavy sink | - |

## Archetypes

| Rule | |
|------|--|
| `rank(?e, boss)` | immune to stunned and frozen |
| `trait(?e, heavy)` | cannot be moved by force (unless frozen or magnetized); sinks in deep water |
| `trait(?e, flier)` | does not fall into a chasm or lava |
| `trait(?e, machine)` | electrocuted: stunned; wet and electrocuted: dead |
| `trait(?e, living)` | wet and electrocuted: stunned |
| `element(?e, fire)` | chilled: dead; immune to burning; does not fall in lava |
| `element(?e, water)` | electrocuted: dead; immune to wet |
| `trait(?e, insect)` | chilled: dead |
| `trait(?e, wooden)` | burning: dead |
| `trait(?e, metal)` | drawn in by a Magnetic Orb |
| anything | frozen, then stunned: dead |
