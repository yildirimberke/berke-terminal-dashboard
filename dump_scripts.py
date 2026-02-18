
import requests
from bs4 import BeautifulSoup

url = "https://www.worldgovernmentbonds.com/cds-historical-data/turkey/5-years/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print(f"Fetching {url}...")
resp = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(resp.text, 'html.parser')

with open("debug_scripts.txt", "w", encoding="utf-8") as f:
    for i, script in enumerate(soup.find_all("script")):
        if script.string:
            f.write(f"\n\n--- SCRIPT {i} ---\n")
            f.write(script.string)
        elif script.get("src"):
            f.write(f"\n\n--- SCRIPT {i} (SRC) ---\n")
            f.write(script.get("src"))

print("Dumped scripts to debug_scripts.txt")
