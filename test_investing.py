
import requests
from bs4 import BeautifulSoup
import re

url = "https://www.investing.com/rates-bonds/turkey-5-year-cds"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.google.com/"
}

print(f"Fetching {url}...")
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Investing.com price class often changes, look for big numbers
    # text-5xl or instrument-price-last
    
    vals = soup.find_all(class_=re.compile("text-5xl"))
    for v in vals:
        print(f"Found big text: {v.text}")
        
    vals2 = soup.find_all(class_=re.compile("last-price"))
    for v in vals2:
        print(f"Found last price: {v.text}")
            
    # Dump text
    text = soup.get_text(" ", strip=True)
    nums = re.findall(r'(\d{3}\.\d{2})', text)
    print(f"Numbers found: {nums[:10]}")
    
except Exception as e:
    print(f"Error: {e}")
