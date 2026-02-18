
import requests
from bs4 import BeautifulSoup
import re

def search_ddg(query):
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    data = {"q": query}
    
    print(f"Searching DDG for '{query}'...")
    resp = requests.post(url, data=data, headers=headers, timeout=10)
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Look for results
    for res in soup.find_all("div", class_="result__body"):
        text = res.get_text(" ", strip=True)
        # Look for CDS pattern: "Turkey 5 Years CDS ... 215.29"
        print(f"\nResult: {text[:200]}...")
        
        # Regex for price
        nums = re.findall(r'(\d{3}\.\d{2})', text)
        if nums:
            print(f"  -> Candidates: {nums}")
            return float(nums[0])
            
    return None

val = search_ddg("Turkey 5 Year CDS Price worldgovernmentbonds")
print(f"\nExtracted: {val}")
