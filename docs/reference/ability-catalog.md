# The ability catalogue

The standard tags and skills of the ability layer ([`ability-system.md`](ability-system.md)),
in `components/abilities/primitives/ab_catalog`: **16 atomic tags, 8 composites, 3 outcomes, 51
skills, 34 looks**. The tables below are generated from the catalogue's source. The worked examples
are `crossing`, `gauntlet` (pure movement) and `two_hands` (no single skill wins; ten pairs do).

## The rules the catalogue follows

1. **Tags are atomic or composite.** An atomic tag has one gameplay meaning. A composite is a named
   bundle of atoms, one level deep: stunned = blinded + silenced + rooted.
2. **A look is not a tag.** Statuses that play identically but look different (petrified, paralyzed
   and knocked-down are all a stun; webbed is a slow; a sheep is polymorphed) are listed as
   `appearance(?look, ?tag)`. The runtime draws the look; the planner only sees the tag.
3. **Nothing grants an outcome.** `dead`, `frozen` and `fell` come only from an enemy's own
   `weakness(?e, ?in, ?have, ?out)`, or from a hazard it is weak to. A combo is deadly because of who
   it lands on. A robot is stunned by a jolt and short-circuits if soaked first; a fire imp freezes
   solid when chilled; a living enemy soaked and jolted only seizes up. Otherwise players would find
   the one combo that kills anything and spam it.
4. **No damage.** Damage, damage over time and damage modifiers are incremental, and this layer is
   about the combos. Bleeding, poison, curses and "vulnerable to X damage" are gone.
5. **Each skill lands several tags, or a tag and a movement, and has several uses.** Fireball sets
   the whole impact region burning, leaves it a fire zone, and throws the target out of it.
   lightningFlash teleports the caster and electrocutes everyone on the way and where it lands.
   Magnetize is a pull, a way across (it drags you to anything anchored), a way to drop an enemy
   (dragged across a pit it falls in) and a way to bridge (a crate dragged across the gap).
   Translocate gets you past a guard, across a gap, or a friend across.
6. **Every tag can be applied by at least two skills, and every tag does something.** The
   component's tests enforce both.
7. **A controlled enemy is not beaten.** Stunned, asleep or feared are setups; only an outcome ends
   a fight. Bosses ignore hard control (the composites), but the atoms still land: a boss can be
   rooted, not stunned.

## Using it in a level

```prolog
% Zones: place the standard zone abilities; hazards take whoever is weak to them.
onEnter(crypt, shadows).  onEnter(abyss, chasm).
beyond(hall, brink, abyss).                    % push lines
% Companions pick skills from the catalogue.
knows(mage, flashbang).  knows(warden, sunder).  mana(player, 3).
% Enemies: rank, traits, element, extra weaknesses, starting tags.
trait(sentry, machine).  trait(sentry, heavy).  tag(sentry, shielded).
rank(brute, boss).  trait(brute, living).  tag(brute, armored).
weakness(golem, electrocuted, oiled, dead).    % a level can add its own
```
The level depends on `abilities/goals/neutralize` and `abilities/primitives/ab_catalog`.

## Tables

### Atomic tags

| Tag | Does | Groups | Put on by | Looks |
|-----|------|--------|-----------|-------|
| `blinded` | no attack | - | charge, charm, concuss, confuse, enthrall, flashbang, hex, lullaby, net, roar, shieldBash, sleepDart, smokeBomb, terrify, thunderclap, toadCurse, translocate | disarmed, nearsighted |
| `silenced` | no skill | - | bloodlust, charge, charm, enrage, enthrall, hex, lullaby, roar, shieldBash, sleepDart, terrify, thunderclap, toadCurse | - |
| `rooted` | no move, dash | - | charge, entangle, iceBlock, lullaby, net, pounce, shieldBash, sleepDart, stoneSkin, thunderclap | snared, entangled, netted |
| `slowed` | no dash; reacts: hasted → quicken | - | blitz, frostBolt, glaciate, hex, iceStorm, magnetize, tarPot, toadCurse | webbed, crippled |
| `uncontrolledMove` | no move, dash | - | concuss, confuse, hex, roar, terrify, toadCurse, translocate | - |
| `wet` | reacts: burning → steam | - | frostBolt, glaciate, iceStorm, rainCall, tidalWave | drenched |
| `oiled` | reacts: burning → blaze | - | oilFlask, tarPot | - |
| `burning` | reacts: wet → extinguish; chilled → quench; oiled → blaze; triggers weaknesses: dead | - | fireball, flameWall | ignited |
| `electrocuted` | triggers weaknesses: dead, dead (on wet), stunned, stunned (on wet) | - | chainLightning, lightningFlash, zap | shocked |
| `taunted` | wards feared; on landing: pull | - | provoke, taunt | provoked |
| `wakeOnHit` | reacts: hostile → wake | - | charm, concuss, confuse, enthrall, lullaby, sleepDart, translocate | - |
| `stealthed` | wards targeted | buff, guard | shadowStep, smokeBomb, vanish | invisible, camouflaged |
| `shielded` | reacts: hostile → absorb | buff, guard | aegis, barrier | warded |
| `hasted` | wards slowed; needed by blitz | buff | bloodlust, haste | swift |
| `armored` | wards forcedMove | buff | aegis, stoneSkin | barkskin, ironclad |
| `invulnerable` | wards hostile | buff, guard | divineShield, iceBlock | untouchable |

### Composite tags

| Tag | = atoms | Also | Groups | Put on by | Looks |
|-----|---------|------|--------|-----------|-------|
| `stunned` | blinded + rooted + silenced | - | hardControl | charge, shieldBash, thunderclap | petrified, paralyzed, knockedUp, knockedDown |
| `asleep` | blinded + rooted + silenced + wakeOnHit | - | hardControl, mind | lullaby, sleepDart | drowsy |
| `feared` | blinded + silenced + uncontrolledMove | on landing: push | hardControl, mind | roar, terrify | terrified, fleeing |
| `polymorphed` | blinded + silenced + slowed + uncontrolledMove | - | hardControl | hex, toadCurse | hexed, toad, sheep |
| `confused` | blinded + uncontrolledMove + wakeOnHit | - | hardControl, mind | concuss, confuse, translocate | dazed, drunk |
| `charmed` | blinded + silenced + wakeOnHit | - | hardControl, mind | charm, enthrall | infatuated |
| `berserk` | silenced | wards feared, charmed | hardControl, mind | bloodlust, enrage | enraged, frenzied |
| `chilled` | slowed + wet | reacts: burning → thaw; triggers weaknesses: frozen | - | frostBolt | frostbitten |

### Outcomes

| Outcome | Produced by (an enemy's weakness) | Reached by |
|---------|-----------------------------------|------------|
| `dead` | electrocuted on wet, electrocuted, burning | chainLightning, fireball, flameWall, lightningFlash, zap |
| `frozen` | chilled, chilled | frostBolt, glaciate, iceStorm |
| `fell` | chasm, lava, deepWater | collapse, magmaBurst |

### Archetype weaknesses

| Rule |
|------|
| `immune(?e, ?t) :- rank(?e, boss), group(?t, hardControl).` |
| `immune(?e, ?t) :- trait(?e, mindless), group(?t, mind).` |
| `weakness(?e, chasm, none, fell) :- not(trait(?e, flier)).` |
| `weakness(?e, lava, none, fell) :- not(trait(?e, flier)), not(element(?e, fire)).` |
| `weakness(?e, deepWater, none, fell) :- trait(?e, heavy).` |
| `immune(?e, forcedMove) :- trait(?e, heavy).` |
| `weakness(?e, electrocuted, wet, dead) :- trait(?e, machine).` |
| `weakness(?e, electrocuted, none, stunned) :- trait(?e, machine).` |
| `immune(?e, ?t) :- trait(?e, machine), group(?t, mind).` |
| `weakness(?e, electrocuted, wet, stunned) :- trait(?e, living).` |
| `weakness(?e, chilled, none, frozen) :- element(?e, fire).` |
| `immune(?e, burning) :- element(?e, fire).` |
| `weakness(?e, electrocuted, none, dead) :- element(?e, water).` |
| `immune(?e, wet) :- element(?e, water).` |
| `weakness(?e, chilled, none, frozen) :- trait(?e, insect).` |
| `weakness(?e, burning, none, dead) :- trait(?e, wooden).` |

### Reactions (for everyone)

| Have | Incoming | Reaction | Does |
|------|----------|----------|------|
| `shielded` | `hostile` | `absorb` | remove(shielded) |
| `wakeOnHit` | `hostile` | `wake` | remove(asleep), remove(charmed), remove(confused) |
| `wet` | `burning` | `steam` | remove(wet) |
| `burning` | `wet` | `extinguish` | remove(burning) |
| `chilled` | `burning` | `thaw` | remove(chilled), grant(wet) |
| `burning` | `chilled` | `quench` | remove(burning) |
| `oiled` | `burning` | `blaze` | remove(oiled), grant(burning), area: grant(burning) |
| `burning` | `oiled` | `blaze` | remove(oiled), grant(burning), area: grant(burning) |
| `slowed` | `hasted` | `quicken` | remove(slowed) |

### Zones

| Zone | Whoever enters | Spilled by |
|------|----------------|------------|
| `puddle` | grant(wet) | rainCall, tidalWave |
| `slick` | grant(oiled) | - |
| `flames` | grant(burning) | fireball, flameWall |
| `iceSheet` | grant(chilled) | glaciate, iceStorm |
| `tar` | grant(oiled), grant(slowed) | tarPot |
| `shadows` | grant(stealthed) | - |
| `chasm` | hazard(chasm) | collapse |
| `lava` | hazard(lava) | magmaBurst |
| `deepWater` | grant(wet), hazard(deepWater) | - |

### Skills

| Skill | Reach | Cost | Effects | Tags it lands | Can lead to |
|-------|-------|------|---------|---------------|-------------|
| `fireball` | ranged | mana 2 | spill(flames), push | - | burning, dead |
| `flameWall` | ranged | - | spill(flames) | - | burning, dead |
| `tidalWave` | ranged | mana 2 | spill(puddle), area: push | - | wet |
| `rainCall` | ranged | - | spill(puddle) | - | wet |
| `frostBolt` | ranged | - | grant(chilled) | chilled, slowed, wet | frozen |
| `iceStorm` | ranged | mana 2 | spill(iceSheet) | - | chilled, frozen, slowed, wet |
| `glaciate` | ranged | - | spill(iceSheet) | - | chilled, frozen, slowed, wet |
| `zap` | ranged | - | grant(electrocuted) | electrocuted | dead, stunned |
| `lightningFlash` | ranged | mana 2 | path: grant(electrocuted), grant(electrocuted), dash | electrocuted | dead, stunned |
| `chainLightning` | ranged | mana 2 | area: grant(electrocuted) | electrocuted | dead, stunned |
| `oilFlask` | ranged | - | area: grant(oiled) | oiled | - |
| `tarPot` | ranged | - | spill(tar) | - | oiled, slowed |
| `gust` | ranged | - | push, remove(burning) | - | - |
| `magnetize` | ranged | - | hook, grant(slowed) | slowed | - |
| `translocate` | ranged | - | swap, grant(confused) | blinded, confused, uncontrolledMove, wakeOnHit | - |
| `charge` | ranged | - | dash, grant(stunned), push | blinded, rooted, silenced, stunned | - |
| `pounce` | ranged | - | dash, grant(rooted) | rooted | - |
| `shadowStep` | ranged | - | dash, self: grant(stealthed) | stealthed | - |
| `shieldBash` | melee | - | grant(stunned), push | blinded, rooted, silenced, stunned | - |
| `thunderclap` | melee | once | area: grant(stunned), area: push | blinded, rooted, silenced, stunned | - |
| `collapse` | ranged | once | spill(chasm) | - | fell |
| `magmaBurst` | ranged | once | spill(lava) | - | fell |
| `net` | ranged | - | grant(rooted), grant(blinded) | blinded, rooted | - |
| `entangle` | ranged | - | area: grant(rooted) | rooted | - |
| `lullaby` | ranged | - | area: grant(asleep) | asleep, blinded, rooted, silenced, wakeOnHit | - |
| `sleepDart` | ranged | - | grant(asleep) | asleep, blinded, rooted, silenced, wakeOnHit | - |
| `roar` | melee | - | area: grant(feared) | blinded, feared, silenced, uncontrolledMove | - |
| `terrify` | ranged | - | grant(feared) | blinded, feared, silenced, uncontrolledMove | - |
| `taunt` | ranged | - | grant(taunted) | taunted | - |
| `provoke` | melee | - | area: grant(taunted) | taunted | - |
| `charm` | ranged | - | grant(charmed) | blinded, charmed, silenced, wakeOnHit | - |
| `enthrall` | ranged | once | area: grant(charmed) | blinded, charmed, silenced, wakeOnHit | - |
| `confuse` | ranged | - | grant(confused) | blinded, confused, uncontrolledMove, wakeOnHit | - |
| `concuss` | melee | - | grant(confused), push | blinded, confused, uncontrolledMove, wakeOnHit | - |
| `enrage` | ranged | - | grant(berserk) | berserk, silenced | - |
| `bloodlust` | self | - | self: grant(berserk), self: grant(hasted) | berserk, hasted, silenced | - |
| `hex` | ranged | - | grant(polymorphed) | blinded, polymorphed, silenced, slowed, uncontrolledMove | - |
| `toadCurse` | ranged | once | area: grant(polymorphed) | blinded, polymorphed, silenced, slowed, uncontrolledMove | - |
| `smokeBomb` | ranged | - | area: grant(blinded), self: grant(stealthed) | blinded, stealthed | - |
| `flashbang` | ranged | - | area: grant(blinded), area: remove(stealthed) | blinded | - |
| `vanish` | self | - | self: grant(stealthed) | stealthed | - |
| `barrier` | ranged | - | grant(shielded) | shielded | - |
| `aegis` | self | - | self: grant(shielded), self: grant(armored) | armored, shielded | - |
| `stoneSkin` | self | - | self: grant(armored), self: grant(rooted) | armored, rooted | - |
| `divineShield` | ranged | once | grant(invulnerable) | invulnerable | - |
| `iceBlock` | self | once | self: grant(invulnerable), self: grant(rooted) | invulnerable, rooted | - |
| `haste` | ranged | - | grant(hasted) | hasted | - |
| `blitz` | ranged | needs hasted | dash, area: push, grant(slowed) | slowed | - |
| `dispel` | ranged | - | purge(buff) | - | - |
| `cleanse` | ranged | - | purge(hostile) | - | - |
| `sunder` | melee | - | remove(armored), remove(shielded) | - | - |
