
import sys
import os

# Mock Flask request/app context if needed, or just import logic
from engine.db import set_custom_source, update_source_value, set_override, get_db_connection
from engine.scraper import SmartScraper

url = "https://www.worldgovernmentbonds.com/cds-historical-data/turkey/5-years/"
key = "cds"

print(f"Testing URL: {url}")

try:
    # 1. Test DB
    print("1. Testing DB Insert...")
    set_custom_source(key, url)
    print("DB Insert OK.")

    # 2. Test Scraper
    print("2. Testing Scraper...")
    scraper = SmartScraper()
    keywords = [key, key.upper(), key.replace("_", " ")]
    print(f"Keywords: {keywords}")
    
    val = scraper.fetch_price(url, keywords)
    print(f"Scrape Result: {val}")

    if val is not None:
        set_override(key, val, source=f"scraper:{url[:20]}...")
        update_source_value(key, val)
        print("Override Set OK.")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
