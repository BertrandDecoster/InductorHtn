#!/usr/bin/env python3
"""Simple test script for backend API"""

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
    # Execute query
    print("\n3. Executing query: at(?where).")
    response = requests.post(
        f"{BASE_URL}/api/query/execute",
        json={"session_id": session_id, "query": "at(?where)."}
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    if 'error' in result:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Solutions: {result['total_count']}")
        for sol in result['solutions']:
            print(f"      {sol}")
