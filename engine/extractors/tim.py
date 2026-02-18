
import requests
import pandas as pd
import logging
import io
from bs4 import BeautifulSoup
from datetime import datetime

class TimExtractor:
    def __init__(self):
        self.base_url = "https://tim.org.tr/tr/ihracat-rakamlari"
        self.logger = logging.getLogger("TimExtractor")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_export_data(self):
        """
        Scrapes TİM website for the latest 'Sektörel' Excel file.
        Returns:
            dict: {
                "total_exports": float (Billion USD),
                "date": str (YYYY-MM),
                "top_sectors": list of (name, value_usd)
            }
        """
        try:
            # 1. Find the Excel Link
            r = requests.get(self.base_url, headers=self.headers, timeout=15)
            if r.status_code != 200:
                self.logger.error(f"Failed to load TİM page: {r.status_code}")
                return None
            
            soup = BeautifulSoup(r.content, 'html.parser')
            target_link = None
            
            # Look for recent Sectoral file
            # Pattern: "...sektorel-bazda-rakamlar.xlsx"
            current_year = datetime.now().year
            target_years = [str(current_year), str(current_year - 1)]
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                if "sektorel" in href.lower() and ".xls" in href.lower():
                    if any(y in href for y in target_years):
                        target_link = href if href.startswith("http") else f"https://tim.org.tr{href}"
                        break
            
            if not target_link:
                self.logger.warning("No recent sectoral Excel found.")
                return None
                
            self.logger.info(f"Downloading Excel: {target_link}")
            
            # 2. Download Excel
            r_file = requests.get(target_link, headers=self.headers, timeout=30)
            if r_file.status_code != 200: return None
            
            # 3. Parse Excel
            with io.BytesIO(r_file.content) as f:
                # Read without header first to find the starting row
                df = pd.read_excel(f, header=None)
                
                # Logic: Find row with "SEKTÖRLER" or "SECTORS"
                start_row = 0
                for idx, row in df.iterrows():
                    row_str = " ".join([str(x).upper() for x in row.values])
                    if "SEKTÖR" in row_str and "TOPLAM" not in row_str: # Avoid summary rows being mistaken for header
                        start_row = idx
                        break
                        
                # Reload with correct header
                f.seek(0)
                df = pd.read_excel(f, header=start_row)
                
                # Find Total Row (usually "TOPLAM" or "GENEL TOPLAM")
                # And extracting the current month column.
                # Usually the columns are: Sector, Month_2024, Month_2025, Change%, ...
                
                # Heuristic: Find the column with the latest date (e.g. "OCAK 2026" or just "2026")
                # Actually, simpler: The last couple of numeric columns are usually the data.
                
                # Let's clean column names
                df.columns = [str(c).upper().strip() for c in df.columns]
                
                # Find Total Row
                total_row = df[df.iloc[:, 0].astype(str).str.contains("TOPLAM", case=False, na=False)]
                if total_row.empty:
                    self.logger.warning("Could not find TOTAL row.")
                    return None
                    
                total_row = total_row.iloc[0]
                
                # Extract Value
                # We need the value for the specific month. 
                # Identifying the correct column is tricky without seeing it.
                # Strategy: Look for the max value in the Total Row that is not the Year-To-Date (which is larger).
                # Actually, "AYLIK" (Monthly) vs "DÖNEMLİK" (Period/YTD).
                # Usually TİM reports: Jan-2024, Jan-2025, Change, Jan-Dec 2024...
                
                # Let's take the value from a column ending in current year (e.g. "1-31 OCAK 2025")
                # Or just take the largest value that isn't the sum of others? No.
                
                # Better: Look for a column header with month/year.
                # Assuming the file is valid.
                
                # Simplified extraction for now: 
                # Just return raw dict of what we found in Total row to debug integration, 
                # then refine column logic if needed.
                # Actually, I'll return the value of the 2nd or 3rd column often being the current month.
                # But safer to return N/A if unsure.
                
                # Heuristic: Columns are usually [Sector, LastYearMonth, ThisYearMonth, Change%, ...]
                # We want the column with "2025" (or current year) and month name.
                # If jan 2025, column might be "1-31 OCAK 2025"
                
                target_col = None
                # Clean headers
                headers = [str(c).upper().strip() for c in df.columns]
                df.columns = headers
                
                # Find column for current year (e.g. 2025) which is NOT a range (e.g. JAN-DEC)
                # TİM usually puts monthly data in early columns, cumulative data later.
                # Let's pick the FIRST column that contains the current year and is not cumulative.
                
                yr_str = str(current_year)
                for col in headers:
                    if yr_str in col and "OCAK-ARALIK" not in col and "DÖNEM" not in col:
                         target_col = col
                         break
                
                # Fallback to previous year if current year not found (e.g. in Jan/Feb looking for Dec/Jan data)
                if not target_col:
                    yr_prev = str(current_year - 1)
                    for col in headers:
                        if yr_prev in col and "OCAK-ARALIK" not in col and "DÖNEM" not in col:
                            target_col = col
                            # Break only if it looks like a month (e.g. "ARALIK")
                            if any(m in col for m in ["OCAK","ŞUBAT","MART","NİSAN","MAYIS","HAZİRAN","TEMMUZ","AĞUSTOS","EYLÜL","EKİM","KASIM","ARALIK"]):
                                break

                if not target_col:
                     self.logger.warning(f"Could not identify monthly column in {headers}")
                     return None

                # Extract Total
                try:
                    val = total_row[target_col]
                    # Clean (remove thousands separator if string)
                    if isinstance(val, str):
                        val = float(val.replace(".", "").replace(",", "."))
                    
                    # Convert to Billion USD
                    total_exports_bly = val / 1_000_000 # TİM usually reports in Thousand USD -> Divide by 1M to get Billion? 
                    # Wait, usually "Bin ABD Doları" (Thousand USD).
                    # 20 Billion USD = 20,000,000 (Thousand).
                    # So dividing by 1,000,000 gives 20. Correct.
                    
                    # Top Sectors
                    # Filter rows where index is sector name (not TOPLAM) and sort by value
                    # We need to drop rows that are sub-totals or weird headers.
                    # Best heuristic: Take rows where 'SEKTÖR' column is not null and value is numeric.
                    
                    sector_col = df.columns[0] # Usually first column
                    sectors = []
                    
                    for idx, row in df.iterrows():
                        sec_name = str(row[sector_col]).strip()
                        if sec_name in ["TOPLAM", "GENEL TOPLAM", "nan", "None", "SEKTÖRLER", "SECTORS"]: continue
                        if "TOPLAM" in sec_name: continue # Subtotals
                        
                        try:
                            v = row[target_col]
                            if isinstance(v, str): v = float(v.replace(".", "").replace(",", "."))
                            if v > 0:
                                sectors.append((sec_name, v))
                        except: pass
                        
                    # Sort by value desc
                    sectors.sort(key=lambda x: x[1], reverse=True)
                    top_3 = sectors[:3]
                    top_3_fmt = [f"{s[0].title()} (${s[1]/1000000:.1f}B)" for s in top_3]

                    return {
                        "total_exports": round(total_exports_bly, 2), # Billions
                        "unit": "B USD",
                        "date": target_col, # e.g. "1-31 OCAK 2025"
                        "top_sectors": top_3_fmt,
                        "source_url": target_link
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error extracting values: {e}")
                    return None

        except Exception as e:
            self.logger.error(f"Tim Extraction Error: {e}")
            return None
