
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

url = "https://www.bddk.org.tr/Veri/Detay/158"
print(f"Fetching {url }...")

try:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(r.content, 'html.parser')
    links = soup.find_all('a', href=True)
    
    print(f"--- ACTION LINKS ---")
    for a in links:
        href = a['href']
        text = a.get_text().strip()
        
        # Look for action-like URLs
        if any(x in href.lower() for x in ['indir', 'download', 'getfile', 'dosya']):
             print(f"POSSIBLE FILE: Text='{text}' | Href='{href}'")
             
except Exception as e:
    print(f"Error: {e}")
