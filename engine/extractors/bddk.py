
import requests
import logging
from datetime import datetime, timedelta
from ..config import EVDS_API_KEY

class BDDKExtractor:
    """
    Extracts banking sector data.
    Primary Source: TCMB EVDS (Stability Protocol)
    Secondary Source: BDDK Website (Scraper - Currently Disabled due to Dynamic auth)
    """
    
    # EVDS Series Codes for Banking Sector
    SERIES_MAPPING = {
        "loans": "TP.KREDI.L002", # Banking Sector Total Loans
        "deposits": "TP.MEV.M002", # Banking Sector Total Deposits
        "npl": "TP.TK.L002"       # Banking Sector NPL Volume
    }

    def __init__(self):
        self.logger = logging.getLogger("BDDKExtractor")
        self.logger.setLevel(logging.INFO)

    def fetch_latest_data(self):
        """
        Main entry point.
        Returns dict with keys: 'loans', 'deposits', 'npl', 'npl_ratio', 'date'
        """
        try:
            # 1. Try EVDS (Golden Source)
            data = self._fetch_from_evds()
            if data:
                self.logger.info(f"BDDK Data fetched via EVDS: {data['date']}")
                return data
            
            # 2. Fallback to Scraper (Future Implementation)
            self.logger.warning("EVDS failed, no backup scraper available.")
            return None
            
        except Exception as e:
            self.logger.error(f"BDDK Critical Error: {e}")
            return None

    def _fetch_from_evds(self):
        """Fetch latest available data from EVDS API (Independent execution)."""
        if not EVDS_API_KEY:
            self.logger.error("No EVDS API Key found.")
            return None

        # Helper to get last value for a single series
        def get_last_val(series_code):
            try:
                # Fetch last 120 days to ensure we find a value
                start_date = (datetime.now() - timedelta(days=120)).strftime("%d-%m-%Y")
                end_date = datetime.now().strftime("%d-%m-%Y")
                url = f"https://evds3.tcmb.gov.tr/igmevdsms-dis/series={series_code}&startDate={start_date}&endDate={end_date}&type=json"
                
                self.logger.info(f"Fetching EVDS Series: {series_code} | URL: {url}")
                
                r = requests.get(url, headers={"key": EVDS_API_KEY}, timeout=10)
                if r.status_code != 200: 
                    self.logger.error(f"EVDS HTTP {r.status_code} for {series_code}")
                    return None, None
                
                items = r.json().get("items", [])
                self.logger.info(f"Items found: {len(items)}")
                
                if not items: return None, None
                
                # Reverse search for first non-null
                key = series_code.replace(".", "_")
                for item in reversed(items):
                    v = item.get(key)
                    if v and v != "null":
                         self.logger.info(f"Found Value for {series_code}: {v}")
                         return float(v), item.get("Tarih")
                
                self.logger.warning(f"No non-null value found for {series_code} in last {len(items)} items.")
                return None, None
            except Exception as e:
                self.logger.error(f"EVDS/get_last_val Error: {e}")
                return None, None

        # Fetch all
        data = {}
        dates = []
        
        loans, l_date = get_last_val(self.SERIES_MAPPING["loans"])
        
        # Deposits/NPL are currently FAILING (HTTP 400).
        # We will skip them for now to allow Loans to work.
        # deposits, d_date = get_last_val(self.SERIES_MAPPING["deposits"])
        # npl, n_date = get_last_val(self.SERIES_MAPPING["npl"])
        
        deposits, d_date = None, None
        npl, n_date = None, None
        
        if not loans:
             self.logger.warning("BDDK/EVDS: Could not fetch Loans data.")
             return None # Loans are mandatory
            
        # Parse units (EVDS Banking data is usually Thousand TL)
        # We want Billions TL
        data["loans"] = loans / 1_000_000 # Thousand -> Billion
        dates.append(l_date)
        
        data["deposits"] = 0
        data["npl"] = 0
        data["npl_ratio"] = 0
             
        # Use the latest date found
        data["date"] = l_date if l_date else "N/A"
        
        return data

