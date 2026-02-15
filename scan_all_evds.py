import os
import requests
import json
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment
load_dotenv(os.path.join("my_terminal", ".env"))
API_KEY = os.getenv("EVDS_API_KEY")

if not API_KEY:
    print("❌ Error: EVDS_API_KEY not found")
    exit(1)

# Target Datagroups for "Interest Rates" and "Gov Securities"
# We will iterate through these groups, get ALL series, and check their last value.
TARGET_GROUPS = [
    "bie_yssk",   # Yield Curve (General)
    "bie_bono",   # Treasury Auctions
    "bie_dbdborc",# Debt Stats
    "bie_tahvil", # Generic Bond Search
    "bie_mkmenk"  # Security Statistics
]

def get_series_list(datagroup):
    """Fetch all series in a group"""
    url = f"https://evds2.tcmb.gov.tr/service/evds/serieList/key={API_KEY}&type=json&code={datagroup}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def check_series_value(code):
    """Check if series has data in 2026"""
    start_date = "01-01-2026"
    end_date = datetime.now().strftime("%d-%m-%Y")
    
    url = f"https://evds2.tcmb.gov.tr/service/evds/series={code}&startDate={start_date}&endDate={end_date}&type=json"
    headers = {"key": API_KEY}
    
    try:
        r = requests.get(url, headers=headers, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if "items" in data and len(data["items"]) > 0:
                # Find the last non-null value
                for item in reversed(data["items"]):
                    val_key = code.replace(".", "_")
                    val = item.get(val_key)
                    if val is not None:
                        return val
    except:
        pass
    return None

print("🚀 Starting Brute-Force Scan for 10Y Bond Data...")
found_candidates = []

# Since we don't know the exact group, let's try a direct series search for common patterns
# if the metadata endpoint fails (which it often does with 403s on some keys)
patterns = [
    "TP.DK.GSY.G10", "TP.DK.GSY.10Y", "TP.TAHVIL.Y10", 
    "TP.FB.TAHVIL.10Y", "TP.DIBS.10Y", "TP.KTF10" # Benchmark proxies
]

print("\n--- Phase 1: Checking Known Candidates ---")
for code in patterns:
    val = check_series_value(code)
    if val:
        print(f"✅ ACTIVE: {code} = {val}")
        found_candidates.append((code, val))
    else:
        print(f"❌ Inactive: {code}")

# If we still haven't found a 10Y specific one, we might need to rely on the scrape backup.
# But let's output the results.

if not found_candidates:
    print("\n⚠️ No API data found for 10Y Bonds in 2026.")
    print("   Recommendation: Use Web Scraping (Investing.com) or a fixed proxy.")
else:
    print("\n🎉 Found potential codes!")
    print(found_candidates)
