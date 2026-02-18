
import requests
import logging
import sys
import os

sys.path.append(os.getcwd())
from engine.config import EVDS_API_KEY

candidates = [
    # Loans (We know TP.KREDI.L002 works)
    "TP.KREDI.L002",
    
    # Deposits Candidates
    "TP.MEV.M002", # Failed?
    "TP.MEV.L002",
    "TP.MEV.K002",
    "TP.YM.K01",
    "TP.DK.USD.S.YTL", # Just a control (should work)
    "TP.MEV.TR.L002",
    "TP.MEV.YP.L002",

    # NPL Candidates
    "TP.TK.L002", # Failed
    "TP.TK.M002",
    "TP.NPL.L002",
    "TP.TGA.L002"
]

print("Testing Series Codes...")
for code in candidates:
    url = f"https://evds3.tcmb.gov.tr/igmevdsms-dis/series={code}&startDate=01-01-2025&endDate=16-02-2026&type=json"
    try:
        r = requests.get(url, headers={"key": EVDS_API_KEY}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            items = data.get("items", [])
            if items:
                 print(f"✅ {code}: FOUND {len(items)} items. Last val: {items[-1].get(code.replace('.', '_'))}")
            else:
                 print(f"⚠️ {code}: 200 OK but NO ITEMS.")
        else:
            print(f"❌ {code}: HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ {code}: Exception {e}")
