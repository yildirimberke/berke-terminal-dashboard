
import requests

url = "https://www.worldgovernmentbonds.com/wp-json/cds/v1/main"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Content-Type": "application/json",
    "Referer": "https://www.worldgovernmentbonds.com/cds-historical-data/turkey/5-years/"
}

payloads = [
    {},
    {"id": 33},
    {"page_id": 33},
    {"country": "Turkey"},
    {"iso": "TUR"},
    {"symbol": "TURKEY"},
    {"period": "5Y"}
]

print(f"Fuzzing {url}...")

for p in payloads:
    try:
        # Try POST
        r = requests.post(url, json=p, headers=headers, timeout=5)
        print(f"POST {p} -> {r.status_code} (len={len(r.text)})")
        if r.status_code == 200:
            print(f"SUCCESS: {r.text[:500]}")
            break
            
        # Try GET with params
        r = requests.get(url, params=p, headers=headers, timeout=5)
        print(f"GET {p} -> {r.status_code}")
        
    except Exception as e:
        print(f"Error: {e}")
