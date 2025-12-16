Here are 10 Combat Levels iterated to strictly use the 7-Skill Core Kit on a 2D grid.

These levels focus on tactical friction. The enemies obey the same grid rules as the player (movement speed, collision, status effects).

Level 1: The Grease Trap (Tutorial)
Setting: A small room packed with 8 weak "Swarmer" enemies. The floor has large patches of Oil. The Problem: There are too many to fight 1-on-1. They surround and chip you down.

HTN Plan A: "The Burn" (Area Denial)

Grid Logic: Oil + Ignite = Explosion + Pushback.

The Play: Warden uses Magnetize to pull a distant Swarmer into the oil patch. Player casts Ignite on the oil.

Result: The explosion kills the target and pushes adjacent Swarmers into walls (stun).

RL Spotlight: The Warden agent calculates the pull trajectory to ensure the enemy lands exactly in the center of the oil for maximum blast radius.

HTN Plan B: "The Slipstream" (Crowd Control)

Grid Logic: Freeze + Oil = Frozen Sludge (Rough Terrain, Slows Movement).

The Play: Arcanist casts Freeze on the oil. It becomes a sticky trap. Warden stands at the edge with Shield. Player uses Gust to push enemies into the sticky zone where they can be picked off at range.

Level 2: The Phalanx
Setting: A narrow corridor. Two "Shield Bearers" block the path side-by-side. The Problem: They have frontal shields (Invulnerable). You cannot pass them.

HTN Plan A: "The Strip" (Forced Movement)

Grid Logic: Magnetize pulls metal units 5 tiles.

The Play: Warden stands back. Warden casts Magnetize on the Left Bearer. It is yanked forward, breaking their formation.

The Kill: Player Dashes into the gap, flanking the Right Bearer to hit the unshielded back.

HTN Plan B: "The Freeze Flank" (Status)

Grid Logic: Freeze on enemy = Ice Block (Solid/Static).

The Play: Arcanist casts Freeze on the Left Bearer. He is now a statue.

The Kill: Player uses Gust on the Ice Block. It slides backward, knocking the Right Bearer out of position (Collision Stun).

Level 3: The Hydro Chamber
Setting: A room half-filled with water. "Electric Eels" (enemies) swim in it. The Problem: Standing in the water hurts (the Eels electrify it). The Eels are fast in water.

HTN Plan A: "Flash Fry" (Elemental)

Grid Logic: Lightning + Water = AoE Damage.

The Play: Warden stands on dry land and Magnetizes an Eel to pull it close (but keeps it in water). Arcanist casts Lightning on the water.

Result: The entire pool becomes a damage zone. Eels take massive damage.

HTN Plan B: "Solid Ground" (Terrain Mod)

Grid Logic: Freeze + Water = Ice (Walkable).

The Play: Arcanist casts Freeze on the water. The Eels are trapped inside the Ice Blocks (Insta-Kill or Stasis).

Result: Player walks over the frozen enemies to reach the exit.

Level 4: The Bull Pen
Setting: An open arena. A "Minotaur" charges in straight lines. If he hits a wall, he is Stunned. The Problem: He tracks your position before charging. High damage.

HTN Plan A: "The Matador" (Redirection)

Grid Logic: Gust pushes perpendicular to charge.

The Play: Minotaur charges Player. Warden stands to the side and uses Magnetize mid-charge? No, Warden pulls.

Correction: Warden uses Magnetize on the charging Minotaur. The pull vector disrupts the charge vector, causing him to crash into a pillar.

RL Spotlight: The agent times the pull for the exact tile where the diagonal trajectory intersects the pillar.

HTN Plan B: "The Oil Slick" (Friction)

Grid Logic: Ice/Oil = No Braking.

The Play: Arcanist casts Freeze on the floor in front of a spike wall. Minotaur charges. He tries to stop, but slides on the ice into the spikes.

Level 5: The Sniper's Nest
Setting: An inaccessible raised platform (conceptually) or across a chasm. Archers fire arrows. The Problem: You cannot reach them with melee. You have no ranged attacks (Arcanist Lightning range is 4 tiles; Archers are at 6).

HTN Plan A: "Return to Sender" (Physics)

Grid Logic: Gust reflects projectiles? No, let's stick to the kit. Gust pushes objects.

The Play: There are Oil Barrels in the room. Player uses Gust to shove a barrel across the gap/chasm toward the archers. Arcanist uses Lightning to ignite/explode the barrel when it arrives.

HTN Plan B: "Mobile Bunker" (Defense)

Grid Logic: Shield blocks projectiles.

The Play: Warden activates Shield. Party moves 1 tile at a time behind him until they reach a switch that extends a bridge.

RL Spotlight: The Warden agent moves strictly in sync with the arrow reload timers.

Level 6: The Binary Guard
Setting: Two "Gemini Knights." If they are close to each other, they heal. The Problem: You must separate them to kill them.

HTN Plan A: "Repulsion" (Positioning)

Grid Logic: Gust pushes 3 tiles.

The Play: Warden engages Knight A. Player casts Gust on Knight B, shoving him away. Arcanist immediately Freezes Knight B (rooting him in place far away).

The Kill: Team focuses down Knight A while B is frozen.

HTN Plan B: "The Kidnap" (Isolation)

Grid Logic: Magnetize pulls 5 tiles.

The Play: Warden stands at max range and Magnetizes Knight A. Player Dashes to body-block Knight B from following.

RL Spotlight: The Player agent constantly repositions to block the pathing of the healing knight.

Level 7: The Construct's Core
Setting: A giant Metal Golem. He has high armor (takes 1 damage). The Problem: Normal attacks don't work. He is conductive.

HTN Plan A: "Overload" (Damage Loop)

Grid Logic: Lightning arcs.

The Play: Player throws water bottles (or lures him into water). Arcanist casts Lightning.

Refined: Warden uses Magnetize not to pull him (he's too heavy), but to pull himself to the Golem (Gap closer). Then Player uses Gust to push the Golem into an electric node on the wall.

HTN Plan B: "Thermal Shock" (Status Combo)

Grid Logic: Ignite (Heat) + Freeze (Cold) = Brittle (Armor Break).

The Play: Player Ignites the Golem (heating armor). Arcanist immediately casts Freeze. The metal shatters (Debuff applied: Armor 0).

The Kill: Team unloads attacks.

Level 8: The Shadow Stalker (Invisible)
Setting: An enemy that turns invisible and moves. He attacks from stealth. The Problem: You can't target what you can't see.

HTN Plan A: "Paint the Target" (Detection)

Grid Logic: Freeze creates physical ice on the floor.

The Play: Arcanist casts Freeze on the floor tiles. When the invisible enemy walks over them, he slips (slide animation plays, revealing location).

The Kill: Warden Magnetizes the slipping spot to grab him out of stealth.

HTN Plan B: "Sonar" (AoE Check)

Grid Logic: Gust hits everything in a cone/line.

The Play: Player spins and casts Gust blindly. If it hits "Air," nothing happens. If it hits the Stalker, he is pushed back and stunned (Collision).

Level 9: The Bombardiers
Setting: Enemies throw ticking bombs on the floor. 3-turn timer. The Problem: The floor is getting covered in explosives.

HTN Plan A: "Hockey" (Physics)

Grid Logic: Bombs are objects. Gust pushes objects.

The Play: Player runs to a bomb and casts Gust to slide it back at the enemy group.

RL Spotlight: Calculating the angle to slide the bomb so it stops adjacent to an enemy.

HTN Plan B: "Defusal" (Status)

Grid Logic: Freeze stops object states/timers? Let's say yes.

The Play: Arcanist casts Freeze on the bombs. They become inert Ice Blocks. Warden uses Magnetize to pull the Ice Blocks to create a defensive wall.

Level 10: The Iron Titan (Capstone)
Setting: A Boss with 3 Phases. He stands in the center. The room rotates. The Problem: Adapting to changing floor hazards (Water, Oil, Metal).

Phase 1 (Metal Floor): Boss charges electricity.

Plan: Arcanist casts Freeze on party members? No.

Plan: Warden Magnetizes debris to build a lightning rod tower away from the party.

Phase 2 (Water Floor): Boss creates waves (pushback).

Plan: Arcanist Freezes the water to create a solid path. Player Dashes across ice to hit the boss.

Phase 3 (Oil Floor): Boss prepares to explode the room.

Plan: Player casts Gust to clear a circle of oil around the party (Safe Zone). Warden holds Shield against the blast. Arcanist zaps the boss while he recovers.

Why these Combat Levels work
No New Rules: Every solution uses Push, Pull, Burn, Freeze, Block, or Zap.

Tactical Choice:

Warden (Positioning): Do I pull the enemy, or block the enemy?

Arcanist (Environment): Do I make the floor slippery (Freeze) or dangerous (Zap)?

Player (Trigger): Do I push the enemy (Gust) or trigger the trap (Ignite)?

RL Execution: The AI isn't just "attacking." It is calculating slide distances, pull vectors, and timing shields against projectile frames.