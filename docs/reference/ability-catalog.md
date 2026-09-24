# The ability catalogue

The standard tags and skills of the ability layer ([`ability-system.md`](ability-system.md)), in
`components/abilities/primitives/ab_catalog`: **11 skills, 3 enemy moves, 13 status tags, 1
composite, 2 outcomes, 9 identity tags, 9 zones, 25 looks**.

## The base

Every skill is written with a handful of keywords, in three families, plus terrain:

| Family | Keywords |
|--------|----------|
| **Tags** | grant or remove a tag, for good or **for a moment** |
| **Movement** | forced movement (push away from the source, pull toward it, pull into a point), dash, teleport |
| **Effects on actions** | **interrupt** (a magic heavy attack being wound up stops), **disjoint** (for a moment, nothing aimed at you lands) |
| **Terrain** | a zone left on a region (whoever is there or walks in takes it); zones reacting to zones; doors opened or closed |

**For a moment** is the only duration: an effect lasts through the next cast by anyone, then is
undone, and never ends in the middle of a heavy attack's window.

**What an entity is, is a tag.** Heavy, flying, machine, living, insect, wooden, fireElemental,
waterElemental and filler are tags, so a skill can take one off (Turn to Mist removes heavy).

## Skills

"Around" means the caster's region and the regions next to it.

| Skill | Tags applied | Movement | On actions | Description |
|-------|--------------|----------|------------|-------------|
| **Hook** | - | the target is pulled toward the caster (an anchored, heavy target pulls the caster to it instead) | interrupts the target | Drag an enemy to you and break the spell it was casting. Across a pit, it falls in. Hooked to a pillar, you cross a gap. |
| **Vortex** | `rooted` on everyone in the target region | everything next to the target region is pulled into it | - | Suck enemies into one spot and pin them there. |
| **Tidal Wave** | `wet` on everyone around | everyone next to the caster is pushed away | - | A wave bursts from you, soaking everyone near and washing them back. |
| **Blizzard** | `slowed` and `chilled` on everyone in the region, now and later (an ice sheet) | - | - | The region ices over. Chilled does nothing alone; on the wet it freezes them (stunned). It kills fire elementals and insects. Over deep water or lava, the ice is a floor. |
| **Fireball** | `burning` on everyone in the region, now and later (flames) | the target is pushed away from the caster | - | The impact region catches fire and the target is blown out of it. |
| **Lightning Flash** | `electrocuted` on the target and everyone on the way | the caster dashes to the target | - | You become lightning, striking everything on your path. |
| **Blink** | `disjoint` on the caster, for a moment | the caster teleports to the target region | disjoint | Vanish and reappear elsewhere; whatever was coming at you misses. |
| **Blinding Flash** | `disjoint` on the caster, for a moment; `blinded` on everyone around | - | disjoint | You flicker out in a flash of light that blinds everyone near you; the attack aimed at you misses. |
| **Taunt** | `taunted` on the target | the target is dragged toward the caster | - | The enemy fixates on you, comes at you, and does what it does when provoked. |
| **Turn to Mist** | `heavy` and `shielded` removed from the target, for a moment | - | - | The target turns to mist: for a moment nothing anchors it and nothing shields it. |
| **Shield Bash** | `stunned` on the target | - | interrupts the target | Stun a normal enemy and break the spell it was casting. |

## Enemy moves

A level gives them to NPCs with `behavior(?npc, ?trigger, ?move, source|self|here|there(R))`. A move
aimed at `source` follows that entity; one aimed at a region falls there.

| Move | Heavy | Kind | On everyone in the struck region but the attacker |
|------|-------|------|----------------------------------------------------|
| `groundSlam` | yes | physical | `stunned`, and pushed away from the attacker |
| `caveIn` | yes | physical | the floor becomes a chasm: whoever is weak to it falls |
| `meteor` | yes | magic | the region catches fire |

A heavy move winds up; the team gets one cast (no walking); then it lands. A companion still in the
struck region is downed, so no plan allows it. Survive it by leaving the region (Blink, Lightning
Flash, Hook onto an anchor, being washed out by a friend's Tidal Wave), by disjointing (Blink,
Blinding Flash: a move that follows you misses entirely), or, for a magic move, by interrupting
(Hook, Shield Bash). A physical move cannot be stopped. Whatever else stands in the struck region
takes it, enemies included.

## Tags

### Status tags

| Tag | Does | Put on by | Looks |
|-----|------|-----------|-------|
| `blinded` | no basic attack; cannot keep watch | Blinding Flash; bundled in stunned | disarmed, nearsighted |
| `silenced` | no skills; its behaviours do not fire | bundled in stunned | - |
| `rooted` | no walking, no dashing | Vortex; bundled in stunned | snared, entangled, netted |
| `slowed` | no dashing | Blizzard (ice sheet) | webbed, crippled |
| `wet` | fire on it: steam; cold on it: stunned | Tidal Wave, puddle, deep water | drenched |
| `chilled` | nothing alone; water on it: stunned; kills fire elementals and insects | Blizzard (ice sheet) | frostbitten |
| `oiled` | fire on it: a blaze (everyone in its region burns) | slick (a level places it) | - |
| `burning` | water puts it out, cold quenches it; kills the wooden | Fireball (flames), a blaze, meteor | ignited |
| `electrocuted` | stuns machines and wet living things; kills wet machines and water elementals | Lightning Flash | shocked |
| `taunted` | dragged to the taunter; sets off behaviours | Taunt | provoked |
| `stealthed` | cannot be aimed at, or seen by a watcher | shadows (a level places it) | invisible, camouflaged |
| `shielded` | takes the next hostile tag instead | innate | warded |
| `disjoint` | for a moment: cannot be aimed at, no hostile tag lands, not moved, a heavy blow misses | Blink, Blinding Flash | blinking, misty |

### Composite and outcomes

| Tag | Is | Comes from | Looks |
|-----|----|-----------|-------|
| `stunned` | blinded + silenced + rooted; a boss is immune | Shield Bash, groundSlam, wet + chilled, a jolt on a machine or a wet living thing | frozen, petrified, paralyzed, knockedDown, dazed |
| `dead` | out of the fight | an enemy's weakness only | - |
| `fell` | out of the fight | a hazard it is weak to | - |

### Identity tags

| Tag | Means |
|-----|-------|
| `heavy` | cannot be moved by force; sinks in deep water. Look: armored |
| `flying` | does not fall; weighs down no plate. Look: hovering |
| `machine` | electrocuted: stunned; wet and electrocuted: dead |
| `living` | wet and electrocuted: stunned |
| `fireElemental` | chilled: dead; immune to burning; does not fall in lava |
| `waterElemental` | electrocuted: dead; immune to wet |
| `insect` | chilled: dead |
| `wooden` | burning: dead |
| `filler` | fallen into a hazard, it fills it (a crate bridges a chasm) |

`rank(?e, boss)` makes an enemy immune to `stunned`.

## Reactions (for everyone)

| Have | Incoming | Does |
|------|----------|------|
| `shielded` | any hostile tag | the shield goes; the tag does not land |
| `wet` | burning | wet goes (steam) |
| `burning` | wet | burning goes |
| `oiled` / `burning` | burning / oiled | oiled goes; it and everyone in its region burn |
| `wet` | chilled | wet goes; stunned (frozen) |
| `chilled` | wet | chilled goes; stunned (frozen) |
| `chilled` | burning | chilled goes |
| `burning` | chilled | burning goes |

## Terrain

| Zone | Whoever is there or enters | Left by |
|------|---------------------------|---------|
| `puddle` | wet | - |
| `flames` | burning | Fireball, meteor |
| `iceSheet` | slowed, chilled | Blizzard |
| `slick` | oiled | - |
| `shadows` | stealthed | - |
| `chasm` | falls, if weak to it (anything not flying) | caveIn |
| `lava` | falls, if weak to it (not flying, not fire) | - |
| `deepWater` | wet; the heavy sink | - |

| Zone there | Meets | Becomes |
|------------|-------|---------|
| `deepWater` | iceSheet | iceSheet (a floor to walk on) |
| `puddle` | iceSheet | iceSheet |
| `lava` | iceSheet | no zone (cooled rock) |
| `iceSheet` | flames | puddle |
| `flames` | iceSheet | puddle |
| `slick` | flames | flames |

Doors: a level declares `door(?r)`; the atoms `open(D)` and `close(D)` change it, and a plate zone
opens it (`open(D)`, or `openWhenHeld(D)` when every plate must be held at once).

## Using it in a level

```prolog
onEnter(crypt, shadows).  onEnter(abyss, chasm).  onEnter(moat, deepWater).
beyond(hall, brink, abyss).                        % push lines
knows(mage, blindingFlash).  knows(warden, shieldBash).  mana(player, 3).
tag(sentry, machine).  tag(sentry, heavy).  tag(sentry, shielded).
rank(brute, boss).  tag(brute, living).  tag(brute, heavy).
behavior(brute, taunted, groundSlam, source).      % taunted, it slams you
weakness(golem, electrocuted, oiled, dead).        % a level can add its own
mustSurvive(envoy).                                % an escort no blow may land on
```
The level depends on `abilities/goals/neutralize` and `abilities/primitives/ab_catalog`.
