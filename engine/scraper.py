"""
The Smart Scraper Engine
========================
"The Collector"
Fetches data from user-defined URLs using heuristics to find the relevant price.
"""
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

class SmartScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }

    def fetch_price(self, url, keywords=[]):
        """
        Attempts to scrape a price from a URL.
        """
        # INTELLIGENCE LAYER: Check for specific handlers for difficult sites
        if "worldgovernmentbonds.com" in url and "cds" in url:
            print(f"[scraper] Detected worldgovernmentbonds.com. Using Smart Handler (TradingEconomics)...")
            smart_val = self._smart_fallback_cds(url)
            if smart_val:
                return smart_val
            # If smart fallback fails, continue to generic scrape as last resort
            print(f"[scraper] Smart Handler failed. Falling back to generic scrape.")

        try:
            print(f"[scraper] Fetching {url}...")
            resp = requests.get(url, headers=self.headers, timeout=10)
            print(f"[scraper] Status: {resp.status_code}, Len: {len(resp.text)}")
            
            if resp.status_code != 200:
                print(f"[scraper] Failed: {resp.status_code}")
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text(" ", strip=True)
            
            # Regex to find numbers: 
            # Supports: 1,234.56 | 1.234,56 | 1234.56 | 1234
            # We look for a number that appears shortly after a keyword.
            
            for keyword in keywords:
                # Find keyword index
                matches = [m.start() for m in re.finditer(re.escape(keyword), text, re.IGNORECASE)]
                for start in matches:
                    # Look at the next 200 chars (expanded window)
                    chunk = text[start:start+200]
                    
                    # Find all numbers in this chunk
                    # Heuristic: CDS is usually > 100.
                    # Price is usually > 0.
                    
                    # Regex: Find potential float strings
                    # Exclude dates (2024, 2025) if possible? Hard.
                    nums = re.findall(r'(\d+[.,]\d+|\d+)', chunk)
                    
                    for raw in nums:
                        try:
                            # Clean: 1,235.50 -> 1235.50
                            # If it has comma and dot, assume dot is decimal if it's at end
                            # If only comma, assume decimal? Or thousand?
                            # TR/EU: 1.234,56
                            # US: 1,234.56
                            
                            val_str = raw
                            if "," in val_str and "." in val_str:
                                if val_str.rfind(",") > val_str.rfind("."):
                                    # 1.234,56 -> 1234.56
                                    val_str = val_str.replace(".", "").replace(",", ".")
                                else:
                                    # 1,234.56 -> 1234.56
                                    val_str = val_str.replace(",", "")
                            elif "," in val_str:
                                # 12,34 or 1,234 ? 
                                # If comma is near end (2 chars), it's decimal.
                                if len(val_str) - val_str.rfind(",") <= 3:
                                     val_str = val_str.replace(",", ".")
                                else:
                                     val_str = val_str.replace(",", "")
                                     
                            val = float(val_str)
                            
                            # Filter: Avoid years (1990-2030) if likely a date
                            if 2020 <= val <= 2030: continue 

                            # Filter: Avoid small integers (years/days)
                            is_int = val.is_integer()
                            if is_int and val <= 30: continue

                            # Return first valid number
                            print(f"[scraper] Found {val} near '{keyword}'")
                            return val
                        except:
                            continue
            
            # If we are here, we found nothing.
            # SMART FALLBACK: "Can't be the engine more intelligent?"
            # If the user is looking for CDS from a difficult site, try a known friendly site.
            if "cds" in keywords or "worldgovernmentbonds" in url:
                print(f"[scraper] Primary scrape failed. Attempting Smart Fallback...")
                return self._smart_fallback_cds(url)
                
            print("[scraper] No matching number found near keywords.")
            return None
            
        except Exception as e:
            print(f"[scraper] Error: {e}")
            return None

    def _smart_fallback_cds(self, original_url):
        """
        If the user provides a link to a hard-to-scrape site (like worldgovernmentbonds),
        we try to find the same data on a friendlier site (TradingEconomics) automatically.
        """
        try:
            # Extract country from URL
            # Url format: .../turkey/...
            # We look for common country names
            import re
            country = None
            
            # Simple heuristic: Split url by / and look for country names? 
            # Or just take the segment after 'cds-historical-data/' if it exists
            if "worldgovernmentbonds.com" in original_url:
                parts = original_url.split("/")
                if "cds-historical-data" in parts:
                    idx = parts.index("cds-historical-data")
                    if idx + 1 < len(parts):
                        country = parts[idx+1]
            
            if not country:
                # Fallback: fuzzy match key?
                # For now, just return None if we can't extract
                return None
                
            print(f"[scraper] Smart Fallback identified country: {country}")
            
            # Construct TE URL
            # TradingEconomics usually uses /country/credit-default-swap/
            # e.g. /turkey/credit-default-swap
            te_url = f"https://tradingeconomics.com/{country}/credit-default-swap"
            
            print(f"[scraper] Fetching fallback: {te_url}")
            resp = requests.get(te_url, headers=self.headers, timeout=10)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text = soup.get_text(" ", strip=True)
                
                # Trading economics usually has the value near "CDS" or just the first Number
                # We look for a number in the logical range (10-10000)
                # TE specific: The value is often in a specific table or ID, but regex search is robust.
                
                # Look for "Turkey 5 Years CDS" buffer
                # Actually, TE page is specific to the instrument. The big number IS the price.
                # We can search for the first float.
                
                nums = re.findall(r'(\d{2,4}\.\d{2}|\d{3})', text) # 200.00, 202
                for raw in nums:
                    try:
                        v = float(raw)
                        # CDS range check
                        if 50 <= v <= 5000:
                            print(f"[scraper] Fallback success: {v}")
                            return v
                    except:
                        continue
                        
            return None
        except Exception as e:
            print(f"[scraper] Fallback Error: {e}")
            return None

    def auto_discover(self, url, expected_price_range=None):
        """
        Try to find a number that matches the expected range.
        Useful for initial setup: "I know CDS is around 300".
        """
        pass
