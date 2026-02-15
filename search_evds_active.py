import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment
load_dotenv(os.path.join("my_terminal", ".env"))
API_KEY = os.getenv("EVDS_API_KEY")

if not API_KEY:
    print("❌ Error: EVDS_API_KEY not found in my_terminal/.env")
    exit(1)

def check_series(code):
    """Checks if a series has data in the last 60 days."""
    end_date = datetime.now().strftime("%d-%m-%Y")
    start_date = (datetime.now() - timedelta(days=60)).strftime("%d-%m-%Y")
    
    url = f"https://evds2.tcmb.gov.tr/service/evds/series={code}&startDate={start_date}&endDate={end_date}&type=json"
    headers = {"key": API_KEY}
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if "items" in data and len(data["items"]) > 0:
                # Check for non-null values
                last_item = data["items"][-1]
                val_key = code.replace(".", "_")
                if last_item.get(val_key) is not None:
                    return last_item.get(val_key)
    except:
        pass
    return None

# Candidate Codes based on common EVDS patterns for Government Bonds
# "Devlet İç Borçlanma Senetleri" -> "DİBS" -> "TAHVIL"
candidates = {
    "TR 2Y Bond": [
        "TP.TAHVIL.Y2", 
        "TP.DK.GSY.G02", # Government Securities Yield 2Y
        "TP.FB.TAHVIL.2Y",
        "TP.KTF10", # Often used as a proxy for short-term funding cost if bond is missing
        "TP.DIBS.2Y"
    ],
    "TR 10Y Bond": [
        "TP.TAHVIL.Y10",
        "TP.DK.GSY.G10",
        "TP.FB.TAHVIL.10Y",
        "TP.DIBS.10Y"
    ]
}

print("🔎 Searching for ACTIVE EVDS Bond Series (Data in last 60 days)...")
found_codes = {}

for name, codes in candidates.items():
    print(f"\nChecking {name}...")
    for code in codes:
        val = check_series(code)
        if val:
            print(f"   ✅ FOUND: {code} (Last Value: {val})")
            found_codes[name] = code
            break
        else:
            print(f"   ❌ Inactive/Missing: {code}")

if len(found_codes) < 2:
    print("\n⚠️ Warning: Could not find active codes for all bonds.")
    print("   We will stick to 'TP.KTF10' (Funding Cost) as a proxy for 2Y if needed.")

# Output results for config update
print("\nRecommended Config Update:")
print(json.dumps(found_codes, indent=4))
