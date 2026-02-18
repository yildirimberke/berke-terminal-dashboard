
import requests
from bs4 import BeautifulSoup
import re

url = "https://www.worldgovernmentbonds.com/cds-historical-data/turkey/5-years/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print(f"Fetching {url}...")
resp = requests.get(url, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, 'html.parser')
# Remove noise
for s in soup(["script", "style", "nav", "footer"]):
    s.decompose()

text = soup.get_text(" ", strip=True)

print("\n--- NUMBERS FOUND (Expanded) ---")
nums = re.findall(r'(\d+[.,]\d+|\d+)', text)
found_target = False
for i, n in enumerate(nums):
    try:
        val_str = n.replace(",", ".")
        v = float(val_str)
        if 100 <= v <= 1000: # CDS Range
            print(f"Candidate #{i}: {n} (Value: {v})")
            found_target = True
    except:
        pass

if not found_target:
    print("No candidates in 100-1000 range found.")
