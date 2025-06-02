#!/usr/bin/env python3
"""Test script for InductorHTN MCP Server"""

import asyncio
import json
import sys
from pathlib import Path

# Add the mcp-server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from indhtn_mcp.session import IndHTNSession, SessionManager


async def test_session():
    """Test basic session functionality"""
    print("Testing InductorHTN MCP Server components...")
    
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
        print(f"  Compilation output: {output[:100]}...")
    except Exception as e:
        print(f"✗ Failed to create session: {e}")
        return False
    
    # Test 2: Execute query
    print("\n2. Testing query execution...")
    try:
        result = await session_manager.execute_query(session_id, "at(?where).")
        print(f"✓ Query executed successfully")
        print(f"  Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"✗ Failed to execute query: {e}")
        return False
    
    # Test 3: Find plans
    print("\n3. Testing HTN planning...")
    try:
        result = await session_manager.execute_query(session_id, "goals(travel-to(suburb)).")
        print(f"✓ Planning query executed")
        print(f"  Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"✗ Failed to find plans: {e}")
        return False
    
    # Test 4: REPL commands
    print("\n4. Testing REPL commands...")
    try:
        # Test help
        result = await session_manager.execute_query(session_id, "/?")
        print(f"✓ Help command executed")
        
        # Test trace toggle
        result = await session_manager.execute_query(session_id, "/t")
        print(f"✓ Trace toggle executed")
    except Exception as e:
        print(f"✗ Failed to execute REPL command: {e}")
        return False
    
    # Test 5: Clean up
    print("\n5. Testing session cleanup...")
    try:
        await session_manager.end_session(session_id)
        print(f"✓ Session ended successfully")
    except Exception as e:
        print(f"✗ Failed to end session: {e}")
        return False
    
    print("\n✅ All tests passed!")
    return True


async def test_error_handling():
    """Test error handling scenarios"""
    print("\n\nTesting error handling...")
    
    indhtn_path = "../build/Release/indhtn"
    if not Path(indhtn_path).exists():
        indhtn_path = "../build/Debug/indhtn"
    
    session_manager = SessionManager(indhtn_path)
    
    # Test invalid session ID
    print("\n1. Testing invalid session ID...")
    try:
        result = await session_manager.execute_query("invalid-id", "test.")
        print(f"✗ Should have raised error")
    except ValueError as e:
        print(f"✓ Correctly raised error: {e}")
    
    # Test syntax error
    print("\n2. Testing syntax error...")
    try:
        session_id, _ = await session_manager.create_session(["../Examples/Taxi.htn"])
        result = await session_manager.execute_query(session_id, "invalid syntax")
        if not result["success"]:
            print(f"✓ Correctly detected syntax error")
            print(f"  Error type: {result.get('error_type')}")
        else:
            print(f"✗ Should have detected syntax error")
        await session_manager.end_session(session_id)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n✅ Error handling tests completed")


if __name__ == "__main__":
    print("InductorHTN MCP Server Test Suite")
    print("=" * 50)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(test_session())
        if success:
            loop.run_until_complete(test_error_handling())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nTest suite failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()