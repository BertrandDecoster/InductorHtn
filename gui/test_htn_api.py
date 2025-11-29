#!/usr/bin/env python3
"""Test script for HTN plan execution API"""

import requests
import json

BASE_URL = "http://localhost:5000"

# Create session
print("1. Creating session...")
response = requests.post(f"{BASE_URL}/api/session/create")
session_data = response.json()
session_id = session_data['session_id']
print(f"   Session ID: {session_id}")

# Load file
print("\n2. Loading Taxi.htn...")
response = requests.post(
    f"{BASE_URL}/api/file/load",
    json={"session_id": session_id, "file_path": "Examples/Taxi.htn"}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

if response.status_code == 200:
    # Execute HTN query
    print("\n3. Executing HTN query: travel-to(uptown).")
    response = requests.post(
        f"{BASE_URL}/api/htn/execute",
        json={"session_id": session_id, "query": "travel-to(uptown)."}
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    if 'error' in result:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Total solutions: {result['total_count']}")
        print(f"   Number of trees: {len(result['trees'])}")

        # Show first solution's tree
        if result['trees']:
            print("\n   First tree structure:")
            tree = result['trees'][0]
            def print_tree(node, indent=0):
                prefix = "  " * indent
                bracket = f"[{node['id']}]" if node.get('isOperator') else f"{{{node['id']}}}"
                status = "FAILED" if node.get('status') == 'failure' else ""
                print(f"{prefix}{bracket} {node['name']} {status}")
                if node.get('fullSignature'):
                    print(f"{prefix}    {node['fullSignature']}")
                if node.get('bindings'):
                    print(f"{prefix}    Head: {node['bindings']}")
                if node.get('conditionBindings'):
                    print(f"{prefix}    Condition: {node['conditionBindings']}")
                for child in node.get('children', []):
                    print_tree(child, indent + 1)

            print_tree(tree)
