#!/usr/bin/env python3
"""Play through the Taxi game using the MCP server components"""

import asyncio
import json
import sys
from pathlib import Path

# Import session module directly
import importlib.util
spec = importlib.util.spec_from_file_location("session", 
    str(Path(__file__).parent / "indhtn_mcp" / "session.py"))
session_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session_module)

SessionManager = session_module.SessionManager


async def play_taxi_game():
    """Play through the Taxi game interactively"""
    print("🚕 Playing the Taxi Game with InductorHTN")
    print("=" * 50)
    
    # Find indhtn executable
    indhtn_path = "../build/Release/indhtn"
    if not Path(indhtn_path).exists():
        indhtn_path = "../build/Debug/indhtn"
    
    session_manager = SessionManager(indhtn_path)
    
    # Start session with Taxi game
    print("\n1. Starting game session...")
    session_id, output = await session_manager.create_session(["../Examples/Taxi.htn"])
    print(f"✓ Session started: {session_id}")
    
    # Check initial state
    print("\n2. Checking initial state...")
    queries = [
        ("at(?where).", "Current location"),
        ("have-cash(?amount).", "Available cash"),
        ("distance(downtown, ?dest, ?dist).", "Distances from downtown"),
        ("bus-route(?bus, downtown, ?dest).", "Bus routes from downtown"),
        ("at-taxi-stand(?taxi, ?loc).", "Available taxis")
    ]
    
    for query, desc in queries:
        result = await session_manager.execute_query(session_id, query)
        print(f"\n{desc}: {query}")
        if result['success']:
            print(f"  → {result['output'].replace('?- >>', '').strip()}")
    
    # Try different travel scenarios
    print("\n\n3. Exploring travel options...")
    
    # Scenario 1: Travel to park (short distance)
    print("\n📍 Scenario 1: Travel to park")
    result = await session_manager.execute_query(session_id, "goals(travel-to(park)).")
    if result['success']:
        print(f"  Plans found: {result['output'].replace('?- >>', '').strip()}")
    
    # Check if we can walk there
    result = await session_manager.execute_query(session_id, "walking-distance(downtown, park).")
    print(f"  Can walk? {result['output'].replace('?- >>', '').strip()}")
    
    # Apply the plan
    print("\n  Applying plan to travel to park...")
    result = await session_manager.execute_query(session_id, "apply(travel-to(park)).")
    if result['success']:
        print(f"  Result: {result['output'].replace('?- >>', '').strip()}")
    
    # Check new state
    result = await session_manager.execute_query(session_id, "at(?where).")
    print(f"  New location: {result['output'].replace('?- >>', '').strip()}")
    
    result = await session_manager.execute_query(session_id, "have-cash(?amount).")
    print(f"  Remaining cash: {result['output'].replace('?- >>', '').strip()}")
    
    # Reset for next scenario
    print("\n  Resetting game state...")
    await session_manager.execute_query(session_id, "/r")
    
    # Scenario 2: Travel to uptown (medium distance)
    print("\n📍 Scenario 2: Travel to uptown")
    result = await session_manager.execute_query(session_id, "goals(travel-to(uptown)).")
    if result['success']:
        print(f"  Plans found: {result['output'].replace('?- >>', '').strip()}")
    
    # Check taxi fare
    result = await session_manager.execute_query(session_id, "have-taxi-fare(8).")
    print(f"  Can afford taxi? {result['output'].replace('?- >>', '').strip()}")
    
    print("\n  Applying plan to travel to uptown...")
    result = await session_manager.execute_query(session_id, "apply(travel-to(uptown)).")
    if result['success']:
        print(f"  Result: {result['output'].replace('?- >>', '').strip()}")
    
    result = await session_manager.execute_query(session_id, "at(?where).")
    print(f"  New location: {result['output'].replace('?- >>', '').strip()}")
    
    result = await session_manager.execute_query(session_id, "have-cash(?amount).")
    print(f"  Remaining cash: {result['output'].replace('?- >>', '').strip()}")
    
    # Reset for next scenario
    print("\n  Resetting game state...")
    await session_manager.execute_query(session_id, "/r")
    
    # Scenario 3: Travel to suburb (long distance)
    print("\n📍 Scenario 3: Travel to suburb")
    result = await session_manager.execute_query(session_id, "goals(travel-to(suburb)).")
    if result['success']:
        print(f"  Plans found: {result['output'].replace('?- >>', '').strip()}")
    
    # Check if we can afford taxi to suburb
    result = await session_manager.execute_query(session_id, "have-taxi-fare(12).")
    print(f"  Can afford taxi? {result['output'].replace('?- >>', '').strip()}")
    
    # Apply the plan (should use bus)
    print("\n  Applying plan to travel to suburb...")
    result = await session_manager.execute_query(session_id, "apply(travel-to(suburb)).")
    if result['success']:
        print(f"  Result: {result['output'].replace('?- >>', '').strip()}")
    
    result = await session_manager.execute_query(session_id, "at(?where).")
    print(f"  New location: {result['output'].replace('?- >>', '').strip()}")
    
    result = await session_manager.execute_query(session_id, "have-cash(?amount).")
    print(f"  Remaining cash: {result['output'].replace('?- >>', '').strip()}")
    
    # Scenario 4: Try to get back with remaining money
    print("\n📍 Scenario 4: Can we get back to downtown?")
    result = await session_manager.execute_query(session_id, "goals(travel-to(downtown)).")
    if result['success']:
        output = result['output'].replace('?- >>', '').strip()
        if "false" in output or "[]" in output:
            print("  ❌ No plans found - we're stuck! Not enough money to get back.")
        else:
            print(f"  Plans found: {output}")
    
    # End session
    print("\n\n4. Ending game session...")
    await session_manager.end_session(session_id)
    print("✓ Session ended")
    
    print("\n🎮 Game Complete!")


if __name__ == "__main__":
    asyncio.run(play_taxi_game())