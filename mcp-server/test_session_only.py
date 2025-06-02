#!/usr/bin/env python3
"""Test script for InductorHTN session management (without MCP dependency)"""

import asyncio
import json
import sys
from pathlib import Path

# Add the mcp-server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the session module directly to avoid __init__ imports
import importlib.util
spec = importlib.util.spec_from_file_location("session", 
    str(Path(__file__).parent / "indhtn_mcp" / "session.py"))
session_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session_module)

IndHTNSession = session_module.IndHTNSession
SessionManager = session_module.SessionManager


async def test_session():
    """Test basic session functionality"""
    print("Testing InductorHTN Session Management...")
    
    # Find indhtn executable
    indhtn_path = "../build/Release/indhtn"
    if not Path(indhtn_path).exists():
        indhtn_path = "../build/Debug/indhtn"
    
    if not Path(indhtn_path).exists():
        print(f"Error: Could not find indhtn executable")
        return False
    
    print(f"Using indhtn at: {indhtn_path}")
    
    # Test 1: Create session
    print("\n1. Testing session creation...")
    session_manager = SessionManager(indhtn_path)
    
    try:
        session_id, output = await session_manager.create_session(
            ["../Examples/Taxi.htn"]
        )
        print(f"✓ Session created: {session_id}")
        print(f"  Compilation output: {output[:200]}...")
    except Exception as e:
        print(f"✗ Failed to create session: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Execute query
    print("\n2. Testing query execution...")
    try:
        result = await session_manager.execute_query(session_id, "at(?where).")
        print(f"✓ Query executed successfully")
        print(f"  Success: {result['success']}")
        print(f"  Output: {result['output']}")
    except Exception as e:
        print(f"✗ Failed to execute query: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Find plans
    print("\n3. Testing HTN planning...")
    try:
        result = await session_manager.execute_query(session_id, "goals(travel-to(suburb)).")
        print(f"✓ Planning query executed")
        print(f"  Success: {result['success']}")
        print(f"  Output: {result['output'][:500]}...")
    except Exception as e:
        print(f"✗ Failed to find plans: {e}")
        return False
    
    # Test 4: Multiple queries
    print("\n4. Testing multiple queries...")
    queries = [
        "cash(?amount).",
        "bus(?b, ?from, ?to).",
        "taxi(?t, ?loc)."
    ]
    
    for query in queries:
        try:
            result = await session_manager.execute_query(session_id, query)
            print(f"✓ Query '{query}' - Success: {result['success']}")
            if result['success']:
                print(f"    Output: {result['output'][:100]}...")
        except Exception as e:
            print(f"✗ Query '{query}' failed: {e}")
    
    # Test 5: REPL commands
    print("\n5. Testing REPL commands...")
    try:
        # Test help
        result = await session_manager.execute_query(session_id, "/?")
        print(f"✓ Help command executed")
        print(f"  Output preview: {result['output'][:200]}...")
        
        # Test trace toggle
        result = await session_manager.execute_query(session_id, "/t")
        print(f"✓ Trace toggle executed")
    except Exception as e:
        print(f"✗ Failed to execute REPL command: {e}")
        return False
    
    # Test 6: Clean up
    print("\n6. Testing session cleanup...")
    try:
        await session_manager.end_session(session_id)
        print(f"✓ Session ended successfully")
    except Exception as e:
        print(f"✗ Failed to end session: {e}")
        return False
    
    print("\n✅ All tests passed!")
    return True


if __name__ == "__main__":
    print("InductorHTN Session Management Test")
    print("=" * 50)
    
    # Set up asyncio
    asyncio.run(test_session())