import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "my_terminal/config.json"

def get_evds_series_search(keyword, api_key):
    """
    Search for series in EVDS metadata service.
    Note: The 'serieList' endpoint returns all series for a datagroup if code is provided, 
    but for keyword search we might need to iterate through datagroups or use a different approach.
    Since EVDS doesn't have a direct 'keyword search' API endpoint documented clearly in the user manual provided, 
    we will simulate it by fetching key datagroups for interest rates and filtering.
    """
    # Focusing on Interest Rates & Government Debt Securities datagroups
    # Datagroup codes: 'bie_yssk' (Yield Curve), 'bie_taboran' (Weighted Avg Cost of Funding), 'bie_bono' (Treasury Auctions)
    
    # Actually, simpler approach for user: just ask for the exact code if they know it, 
    # OR provide a pre-defined list of likely candidates to choose from.
    pass

def interactive_setup():
    api_key = os.getenv("EVDS_API_KEY")
    if not api_key:
        print("Error: EVDS_API_KEY not found in .env file.")
        return

    print("--- Bloomberg Terminal Lite: EVDS Setup ---")
    print("We need to map the exact Series Codes for your macro data.")
    print("If you don't know the code, we can try to find it.")

    config = {}
    
    # 1. Policy Rate (Repo)
    print("\n[1] Policy Rate (1-Week Repo Auction Rate)")
    print("   Common Code: TP.KTF17")
    repo = input("   Enter Series Code (press Enter for TP.KTF17): ").strip()
    config.setdefault("policy_rates", {})["repo"] = repo if repo else "TP.KTF17"

    # 2. Funding Cost (AOFM)
    print("\n[2] Weighted Average Cost of Funding (AOFM)")
    print("   Common Code: TP.KTF10")
    aofm = input("   Enter Series Code (press Enter for TP.KTF10): ").strip()
    config["policy_rates"]["aofm"] = aofm if aofm else "TP.KTF10"

    # 3. TR 2-Year Bond Yield
    print("\n[3] TR 2-Year Government Bond Yield")
    print("   Common Code: TP.TAHVIL.Y2 (Note: This might vary based on auction vs secondary)")
    tr_2y = input("   Enter Series Code (press Enter for TP.TAHVIL.Y2): ").strip()
    config.setdefault("bonds", {})["tr_2y"] = tr_2y if tr_2y else "TP.TAHVIL.Y2"

    # 4. TR 10-Year Bond Yield
    print("\n[4] TR 10-Year Government Bond Yield")
    print("   Common Code: TP.TAHVIL.Y10")
    tr_10y = input("   Enter Series Code (press Enter for TP.TAHVIL.Y10): ").strip()
    config["bonds"]["tr_10y"] = tr_10y if tr_10y else "TP.TAHVIL.Y10"

    # Save to config.json
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    
    print(f"\nConfiguration saved to {CONFIG_FILE}")
    print("Verifying API connection with these codes...")
    
    # Simple Verification
    headers = {"key": api_key}
    test_code = config["policy_rates"]["repo"]
    url = f"https://evds2.tcmb.gov.tr/service/evds/series={test_code}&startDate=01-01-2024&endDate=01-01-2025&type=json"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            print("✅ API Connection Successful!")
            print(f"   Sample Data for {test_code}: {r.json().get('totalCount', '0')} records found.")
        else:
            print(f"❌ API Connection Failed: {r.status_code}")
            print("   Check your API Key in .env")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    interactive_setup()
