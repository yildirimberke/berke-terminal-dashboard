
import requests
from bs4 import BeautifulSoup
import re

url = "https://www.cnbc.com/quotes/TURKEYCDS"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print(f"Fetching {url}...")
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # CNBC usually puts price in .QuoteStrip-lastPrice
    price_tag = soup.find("span", class_="QuoteStrip-lastPrice")
    if price_tag:
        print(f"Found price tag: {price_tag.text}")
    else:
        # Fallback to meta tags
        meta = soup.find("meta", property="og:description")
        if meta:
            print(f"Meta Description: {meta['content']}")
            
    # Dump text
    text = soup.get_text(" ", strip=True)
    nums = re.findall(r'(\d{3}\.\d{2})', text)
    print(f"Numbers found: {nums[:10]}")
    
except Exception as e:
    print(f"Error: {e}")
