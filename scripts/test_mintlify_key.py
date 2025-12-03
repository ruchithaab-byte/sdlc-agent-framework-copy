#!/usr/bin/env python3
"""Test Mintlify Assistant API key with different authentication methods."""

import requests
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

key = os.getenv("MINTLIFY_API_KEY")
if not key:
    print("❌ MINTLIFY_API_KEY not found in .env file")
    sys.exit(1)

print("=" * 70)
print("Mintlify API Key Test")
print("=" * 70)
print(f"Key: {key[:20]}...{key[-10:]}")
print()

# Test different authentication methods
methods = [
    ("Bearer Token", {"Authorization": f"Bearer {key}"}),
    ("X-API-Key Header", {"X-API-Key": key}),
    ("API-Key Header", {"API-Key": key}),
    ("X-Mintlify-Key Header", {"X-Mintlify-Key": key}),
]

endpoints = [
    "/v1/assistant/search",
    "/v1/search",
    "/search",
]

for endpoint in endpoints:
    print(f"\nTesting endpoint: {endpoint}")
    print("-" * 70)
    
    for method_name, headers in methods:
        try:
            headers["Content-Type"] = "application/json"
            resp = requests.post(
                f"https://api.mintlify.com{endpoint}",
                headers=headers,
                json={"query": "test", "limit": 1},
                timeout=5
            )
            
            if resp.status_code == 200:
                print(f"  ✅ SUCCESS with {method_name}!")
                print(f"     Response: {resp.json()}")
                sys.exit(0)
            elif resp.status_code == 401:
                print(f"  ❌ {method_name}: Unauthorized (401)")
            elif resp.status_code == 404:
                print(f"  ⚠️  {method_name}: Not Found (404)")
            else:
                print(f"  ⚠️  {method_name}: {resp.status_code} - {resp.text[:80]}")
        except Exception as e:
            print(f"  ❌ {method_name}: Error - {str(e)[:80]}")

print("\n" + "=" * 70)
print("All tests failed. Key may need activation or different configuration.")
print("Check Mintlify dashboard: Settings → API Keys")
print("=" * 70)
