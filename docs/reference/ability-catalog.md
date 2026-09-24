# The ability catalogue

The standard tags and skills of the ability layer ([`ability-system.md`](ability-system.md)), in
`components/abilities/primitives/ab_catalog`: **11 skills, 3 enemy moves, 13 status tags, 1
composite, 2 outcomes, 9 identity tags, 9 zones, 25 looks**.

## The base

Every skill is written with a handful of keywords, in three families, plus terrain:

| Family | Keywords |
|--------|----------|
| **Tags** | grant or remove a tag, for good or **for a moment** |
| **Movement** | forced movement (push to any neighbouring area, pull to the caster, pull into an area), dash, teleport, walk (a chase) |
| **Effects on actions** | **interrupt** (a magic heavy attack being wound up stops), **disjoint** (for a moment, nothing aimed at you lands) |
| **Terrain** | a zone left on an area (whoever is there or walks in takes it); zones reacting to zones; doors opened or closed |

**The map.** Areas are large: a small room, or a quarter of a large one. They are joined by links,
and a chokepoint is two areas with a special link:

| Link | Walk | Dash | Teleport | Forced movement |
|------|------|------|----------|-----------------|
| walkable (`connected`) | yes | yes | yes | passes |
| `gap` (a short pit) | no | yes | yes | falls in, unless flying; a filler that falls in bridges it |
| `wall` | no | no | yes | stopped |
| `doorway` | while open | while open | yes | while open |

Every movement goes **one link**. Ranged skills aim at anything in line of sight; melee reaches the
same area or next door (not through a wall). A push sends its target to any neighbouring area but
the caster's own: you aim the blast wherever you like, so you choose where it lands, a friend or
yourself included. A dash or a teleport never lands its caster in a live hazard.

**For a moment** is the only duration: an effect lasts through the next cast by anyone, then is
undone, and never ends in the middle of a heavy attack's window.

**What an entity is, is a tag.** Heavy, flying, machine, living, insect, wooden, fireElemental,
waterElemental and filler are tags, so a skill can take one off (Turn to Mist removes heavy).

## Skills

"Around" means everyone else in the caster's area.

| Skill | Reach | Tags applied | Movement | On actions | Description |
|-------|-------|--------------|----------|------------|-------------|
| **Hook** | melee | - | the target is pulled into the caster's area (an anchored, heavy target pulls the caster to it instead) | interrupts the target | Drag an enemy to you and break the spell it was casting. Across a gap, it falls in. Hooked to a pillar across a gap, you cross it. |
| **Vortex** | ranged | `rooted` for a moment on the NPCs in the target area | everything next door is pulled into the target area | - | Suck everything into one area and pin the enemies there for a moment. Allies get pulled too, but not pinned. |
| **Tidal Wave** | self | `wet` on everyone around | everyone around is pushed next door, each where the caster likes | - | A wave bursts from you, soaking everyone near and washing them out. |
| **Blizzard** | ranged | `slowed` and `chilled` on everyone in the area, now and later (an ice sheet) | - | - | The area ices over. Chilled does nothing alone; on the wet it freezes them (stunned). It kills fire elementals and insects. Over deep water or lava, the ice is a floor. |
| **Fireball** | ranged | `burning` on everyone in the area, now and later (flames) | the target is pushed next door, wherever the caster likes | - | The whole area catches fire and the target is blown out of it. Aimed at a friend or yourself, it throws them. |
| **Lightning Flash** | melee | `electrocuted` on everyone in the target area | the caster dashes there | - | You become lightning and strike the area next door, landing in it. |
| **Blink** | near | `disjoint` on the caster, for a moment | the caster teleports next door, through any link | disjoint | Vanish and reappear next door, even through a wall; whatever was coming at you misses. |
| **Blinding Flash** | self | `disjoint` on the caster, for a moment; `blinded` and `electrocuted` on everyone around | - | disjoint | You flicker out in a flash of lightning that blinds and shocks everyone near you, friends included; the attack aimed at you misses. |
| **Taunt** | ranged | `taunted` on the target (NPCs only) | the target walks after the caster, and keeps following | - | The enemy fixates on you and comes at you, through whatever lies on the way; if it cannot walk to you, the taunt breaks. |
| **Turn to Mist** | ranged | `heavy` and `shielded` removed from the target, for a moment | - | - | The target turns to mist: for a moment nothing anchors it and nothing shields it. |
| **Shield Bash** | melee | `stunned` on the target; `shielded` on the caster | - | interrupts the target | Stun a normal enemy, break its spell, and raise your shield: it takes the next hit, even a heavy blow. |

## Enemy moves

A level gives them to NPCs with `behavior(?npc, ?trigger, ?move, source|self|here|there(R))`. A move
aimed at `source` follows that entity; one aimed at a region falls there.

| Move | Heavy | Kind | On everyone in the struck region but the attacker |
|------|-------|------|----------------------------------------------------|
| `groundSlam` | yes | physical | `stunned`, and thrown next door |
| `caveIn` | yes | physical | the floor becomes a chasm: whoever is weak to it falls |
| `meteor` | yes | magic | the region catches fire |

A heavy move winds up. With a companion in the struck area, the team may answer with one cast (no
walking) or take the blow: sacrifice is allowed, unless a level declares someone `mustSurvive`.
Answers: leave the area (Blink, Lightning Flash, Hook onto an anchor, a friend's push), disjoint
(Blink, Blinding Flash: a move that follows you misses entirely), a shield (Shield Bash: it takes the
blow and breaks), or, for a magic move, interrupt (Hook, Shield Bash). A physical move cannot be
stopped. Whatever else stands in the struck area takes it, enemies included. The zone a blow leaves
(a cave-in's chasm) is terrain: it takes everyone there, the attacker included.

## Tags

### Status tags

| Tag | Does | Put on by | Looks |
|-----|------|-----------|-------|
| `blinded` | no basic attack; cannot keep watch | Blinding Flash; bundled in stunned | disarmed, nearsighted |
| `silenced` | no skills; its behaviours do not fire | bundled in stunned | - |
| `rooted` | no walking, no dashing | Vortex (for a moment); bundled in stunned | snared, entangled, netted |
| `slowed` | no dashing | Blizzard (ice sheet) | webbed, crippled |
| `wet` | fire on it: steam; cold on it: stunned | Tidal Wave, puddle, deep water | drenched |
| `chilled` | nothing alone; water on it: stunned; kills fire elementals and insects | Blizzard (ice sheet) | frostbitten |
| `oiled` | fire on it: a blaze (everyone in its region burns) | slick (a level places it) | - |
| `burning` | water puts it out, cold quenches it; kills the wooden | Fireball (flames), a blaze, meteor | ignited |
| `electrocuted` | stuns machines and wet living things; kills wet machines and water elementals | Lightning Flash, Blinding Flash | shocked |
| `taunted` | an NPC walks after its taunter; the taunt breaks when it cannot; sets off behaviours; companions are immune | Taunt | provoked |
| `stealthed` | cannot be aimed at, or seen by a watcher | shadows (a level places it) | invisible, camouflaged |
| `shielded` | takes the next hostile tag, or the next heavy blow, instead | Shield Bash; innate | warded |
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
| (a gap link) | falls in when forced across (anything not flying) | - |
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
connected(hall, brink).  gap(brink, ledge).  wall(hall, vault).  doorway(hall, crypt, gate).
onEnter(crypt, shadows).  onEnter(abyss, chasm).  connected(brink, abyss).
knows(mage, blindingFlash).  knows(warden, shieldBash).  mana(player, 3).
tag(sentry, machine).  tag(sentry, heavy).  tag(sentry, shielded).
rank(brute, boss).  tag(brute, living).  tag(brute, heavy).
behavior(brute, taunted, groundSlam, source).      % taunted, it slams you
weakness(golem, electrocuted, oiled, dead).        % a level can add its own
mustSurvive(envoy).                                % an escort no blow may land on
                                                   % (companions may be sacrificed)
```
The level depends on `abilities/goals/neutralize` and `abilities/primitives/ab_catalog`.
