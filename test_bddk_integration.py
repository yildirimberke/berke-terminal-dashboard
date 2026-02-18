
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)

from engine.macro import fetch_banking_monitor

print("--- Testing BDDK Integration ---")
try:
    data = fetch_banking_monitor()
    print("Result:")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    if data and data.get("loans") and data.get("loans") != "N/A":
        print("\n✅ SUCCESS: Fetched and parsed banking data.")
    else:
        print("\n❌ FAILURE: Could not fetch valid data.")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
