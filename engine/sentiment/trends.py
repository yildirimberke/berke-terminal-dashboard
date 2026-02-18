
import logging
import pandas as pd
from pytrends.request import TrendReq

class TrendsExtractor:
    def __init__(self):
        self.logger = logging.getLogger("TrendsExtractor")
        # Use defaults to avoid urllib3/requests compatibility issues
        try:
            self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        except Exception as e:
            self.logger.error(f"Failed to init TrendReq: {e}")
            self.pytrends = None

    def fetch_panic_index(self):
        """
        Fetches 'Panic' (Dolar + Altın) and 'Greed' (Borsa) sentiment.
        Returns:
            dict: {
                "panic_score": float (0-100),
                "greed_score": float (0-100),
                "ratios": {"dolar": int, "altın": int, "borsa": int}
            }
        """
        if not self.pytrends: return None

        keywords = ["dolar", "altın", "borsa"]
        try:
            # Build Payload (7 Days)
            self.pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='TR', gprop='')
            
            # Fetch Data
            df = self.pytrends.interest_over_time()
            if df.empty:
                self.logger.warning("Google Trends returned empty DataFrame.")
                return None
                
            # Get latest values (last row) - ignoring partial data flag for now
            last_row = df.iloc[-1]
            
            dolar = int(last_row.get("dolar", 0))
            altin = int(last_row.get("altın", 0))
            borsa = int(last_row.get("borsa", 0))
            
            # Panic Index = Average of Dolar and Altin interest
            panic_score = (dolar + altin) / 2
            
            # Greed Index = Borsa interest
            greed_score = borsa
            
            return {
                "panic_score": round(panic_score, 2),
                "greed_score": greed_score,
                "ratios": {
                    "dolar": dolar,
                    "altin": altin,
                    "borsa": borsa
                }
            }
            
        except Exception as e:
            self.logger.error(f"Trends Fetch Error: {e}")
            return None
