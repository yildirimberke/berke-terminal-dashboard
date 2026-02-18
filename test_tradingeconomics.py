
import requests
from bs4 import BeautifulSoup
import re

# Guessing the URL
urls = [
    "https://tradingeconomics.com/turkey/credit-default-swap",
    "https://tradingeconomics.com/turkey/cds",
    "https://tradingeconomics.com/bonds/turkey-5-year-credit-default-swap"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

for url in urls:
    print(f"Fetching {url}...")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
             soup = BeautifulSoup(resp.text, 'html.parser')
             text = soup.get_text(" ", strip=True)
             nums = re.findall(r'(\d{3}\.\d{2}|2\d{2})', text) # Look for ~200-300
             print(f"  -> Candidates: {nums[:10]}")
             if nums:
                 print("  -> SUCCESS?")
                 break
    except Exception as e:
        print(f"Error: {e}")
