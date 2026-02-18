
import requests
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.getcwd())
from engine.config import EVDS_API_KEY

def check_latest(series_code):
    # Check last 6 months
    start = (datetime.now() - timedelta(days=180)).strftime("%d-%m-%Y")
    end = datetime.now().strftime("%d-%m-%Y")
    
    url = f"https://evds3.tcmb.gov.tr/igmevdsms-dis/series={series_code}&startDate={start}&endDate={end}&type=json"
    print(f"Checking {series_code}...")
    try:
        r = requests.get(url, headers={"key": EVDS_API_KEY}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            items = data.get("items", [])
            print(f"Items found: {len(items)}")
            if items:
                print(f"Last Item: {items[-1]}")
            else:
                print("No items.")
        else:
            print(f"HTTP {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

check_latest("TP.KREDI.L002") # Loans
check_latest("TP.DK.USD.S.YTL") # Control
