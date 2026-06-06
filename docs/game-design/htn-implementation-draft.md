Attempting to run an HTN planner on a tile-by-tile basis (e.g., move(tile_1_1, tile_1_2)) is a recipe for disaster. The search space explodes exponentially, and it duplicates the work that the pathfinding/RL layer is already good at.

The Correct Architecture:

HTN Layer (The General): Reasons over a Navigational Graph. It knows about "The Bridge," "The Switch Alcove," and "The Generator Platform." It does not know about tile (14, 5).

RL Layer (The Soldier): Receives an operator like Maps(?agent, bridge). It handles the localized grid movement, obstacle avoidance, and pathfinding.

Here are the 3 Best Environmental and 3 Best Combat levels adapted for this architecture, using standardized InductorHTN syntax.

I. The Domain Definition (Standardized API)
Before looking at the levels, we define the common language (predicates) used across all maps.

State Predicates:

at(?entity, ?region): Entity is in a high-level region.

connected(?regionA, ?regionB): A navigable path exists between regions.

line_of_sight(?regionA, ?regionB): Ranged skills can target B from A.

region_has(?region, ?feature): Features like oil, water, switch, generator.

status(?entity, ?status): e.g., frozen, wet, shielded.

RL-Delegated Operators (The Primitives): These are the "leaf nodes" of the plan. When the HTN selects these, they are sent to C++ to be executed by the RL models or game engine.

Prolog

/* Moves an agent to a region using RL pathfinding */
navigate(?agent, ?target_region) :- 
    del(at(?agent, ?old)), 
    add(at(?agent, ?target_region)).

/* RL agent executes a skill on a target (Entity or Region) */
cast_skill(?agent, ?skill_name, ?target) :- 
    /* logic for specific effects handled in engine, HTN tracks abstract state change */
    check_skill_effects(?skill_name, ?target).

/* Specialized RL task: Coordinate timing with another agent */
sync_operate(?agent1, ?agent2, ?target1, ?target2) :-
    /* Tells RL to wait for the other agent before triggering */
    del(status(?target1, off)), add(status(?target1, on)),
    del(status(?target2, off)), add(status(?target2, on)).

/* Specialized RL task: Keep an enemy's attention while moving to a region */
lure_enemy(?agent, ?enemy, ?region) :-
    del(at(?agent, ?old)), add(at(?agent, ?region)),
    del(at(?enemy, ?old_e)), add(at(?enemy, ?region)).
II. Environmental Levels (Puzzle Solving)
1. The Conductor's Gap (Connectivity & State)
The Concept: A generator is separated from the door by a water channel. The HTN must realize that Water connects the two if electrified.

Prolog

/* STATE */
region(generator_platform). region(water_channel). region(door_platform).
connected(generator_platform, water_channel).
connected(water_channel, door_platform).

/* The physical layout logic */
region_has(generator_platform, generator).
region_has(water_channel, water).
region_has(door_platform, door_node).

/* METHODS */
/* Goal: Open the door */
solve_room :- 
    if(status(door, closed)), 
    do(power_door_node).

/* Method A: The Frozen Bridge (Safe) */
/* If we have freeze and pushable objects, build a bridge */
power_door_node :-
    if(
        at(arcanist, generator_platform),
        region_has(water_channel, water),
        item(crate, ?crate)
    ),
    do(
        cast_skill(arcanist, freeze, water_channel), /* Creates Ice Surface */
        navigate(warden, generator_platform),
        push_object(warden, ?crate, water_channel), /* Push crate onto ice */
        navigate(player, door_platform), /* Cross the bridge */
        cast_skill(arcanist, lightning, generator)
    ).

/* Method B: The Human Chain (Fast/Damage) */
/* If no crates, use bodies as conductors */
power_door_node :-
    else,
    do(
        navigate(warden, water_channel),
        navigate(player, water_channel),
        cast_skill(arcanist, lightning, generator)
    ).
2. The Logic Gate (Synchronization)
The Concept: Two switches far apart must be pressed simultaneously.

Prolog

/* STATE */
region(room_left). region(room_right). region(corridor).
region_has(room_left, switch_a).
region_has(room_right, switch_b).

/* METHODS */
solve_room :-
    if(status(door, closed)),
    do(press_switches_sync(switch_a, switch_b)).

/* Method: Split Up and Sync */
press_switches_sync(?s1, ?s2) :-
    if(
        region_has(?r1, ?s1),
        region_has(?r2, ?s2)
    ),
    do(
        /* Parallel navigation tasks */
        navigate(warden, ?r1),
        navigate(player, ?r2),
        /* The RL model handles the precise 'wait for partner' logic */
        sync_operate(warden, player, ?s1, ?s2)
    ).
3. The Battery Charge (Sequencing)
The Concept: A battery needs sequential inputs from rotating nodes (A -> B -> C).

Prolog

/* STATE */
region(node_a). region(node_b). region(node_c).
power_cycle(node_a, node_b). /* Power moves from A to B */
power_cycle(node_b, node_c).

/* METHODS */
solve_room :-
    do(charge_battery_sequence(node_a)).

/* Recursive method to handle the sequence */
charge_battery_sequence(?current_node) :-
    if(
        power_cycle(?current_node, ?next_node)
    ),
    do(
        /* Assign closest agent to the current active node */
        assign_agent_to_node(?agent, ?current_node),
        navigate(?agent, ?current_node),
        /* Wait for power to cycle to next */
        wait_for_power_cycle(?current_node),
        /* Recursively handle the next step */
        charge_battery_sequence(?next_node)
    ).

/* Base case: Final node */
charge_battery_sequence(node_c) :-
    do(
        navigate(player, node_c),
        trigger_final_charge
    ).
III. Combat Levels (Tactical Encounters)
4. The Grease Trap (Environment Interaction)
The Concept: Use oil regions to defeat swarms efficiently.

Prolog

/* STATE */
region(corridor). region(oil_pit).
region_has(oil_pit, oil).
enemy_group(swarm_1). at(swarm_1, oil_pit).

/* METHODS */
kill_enemy_group(?group) :-
    if(
        at(?group, ?loc),
        region_has(?loc, oil),
        skill_ready(player, ignite)
    ),
    do(
        /* Optimization: If they are already in oil, just burn */
        cast_skill(player, ignite, ?loc)
    ).

kill_enemy_group(?group) :-
    else,
    if(
        region_has(?trap_loc, oil),
        at(?group, ?enemy_loc)
    ),
    do(
        /* RL Task: Run to trap_loc while keeping ?group aggro */
        lure_enemy(warden, ?group, ?trap_loc),
        cast_skill(player, ignite, ?trap_loc)
    ).
5. The Phalanx (Coordination/Flanking)
The Concept: Enemies are invulnerable from the front (Shielded).

Prolog

/* STATE */
region(choke_point). region(flank_route).
enemy(shield_guard). status(shield_guard, shielded).

/* METHODS */
kill_enemy(?target) :-
    if(
        status(?target, shielded)
    ),
    do(
        break_shield_formation(?target),
        attack_vulnerable(?target)
    ).

/* Strategy: Bait and Turn */
break_shield_formation(?target) :-
    do(
        /* Warden holds aggro in the main region */
        lure_enemy(warden, ?target, choke_point),
        /* Player moves to flank region */
        navigate(player, flank_route),
        /* Player attacks from side/rear (handled by RL targeting logic) */
        cast_skill(player, backstab, ?target)
    ).

/* Strategy: Magnetize Disruption */
break_shield_formation(?target) :-
    if(skill_ready(warden, magnetize)),
    do(
        cast_skill(warden, magnetize, ?target) /* Pulls enemy, exposing back */
    ).
6. The Hydro Chamber (Regional Hazards)
The Concept: Water conducts electricity. Enemies in water are vulnerable to Lightning.

Prolog

/* STATE */
region(dry_ledge). region(water_pool).
region_has(water_pool, water).
enemy(eel). at(eel, water_pool).

/* METHODS */
kill_enemy(?target) :-
    if(
        at(?target, ?loc),
        region_has(?loc, water),
        skill_ready(arcanist, lightning)
    ),
    do(
        /* High-Value Play: Zap the water */
        cast_skill(arcanist, lightning, ?loc)
    ).

kill_enemy(?target) :-
    if(
        at(?target, dry_ledge) /* Enemy is not in water */
    ),
    do(
        /* Strategy: Force them into the hazard */
        cast_skill(player, gust, ?target), /* Push into water */
        /* Re-evaluate plan now that state has changed */
        kill_enemy(?target)
    ).
Why this fits the GDD better
Graph Abstraction: The HTN planner doesn't care how the Warden gets from the generator_platform to the water_channel. It just issues the Maps command. The C++ game loop handles the A* or NavMesh pathing.

RL Specialization: The operator lure_enemy(warden, swarm_1, oil_pit) is a perfect task for an RL agent. The agent's reward function would be: Maximize proximity to Oil Pit + Maintain Aggro on Swarm + Minimize Damage Taken.

Visual Debugging: In the "Tactical Focus" mode described in the GDD, the player would see the high-level plan: Lure to Oil -> Ignite. They wouldn't see a messy list of 50 movement steps.