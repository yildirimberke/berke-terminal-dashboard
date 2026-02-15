import requests
import pandas as pd
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from .config import CONFIG, EVDS_API_KEY, FRED_API_KEY
from .cache import get_cached, set_cached

def fetch_macro_data():
    cached = get_cached("macro", ttl_seconds=120)
    if cached is not None: return cached
    codes = CONFIG.get("macro_panel", {})
    aofm_val = _evds_last_value(codes.get("aofm", "TP.APIFON4"))
    comm_loan = _evds_last_value(codes.get("commercial_loan_rate", "TP.KTF17"))
    deposit = _evds_last_value(codes.get("deposit_rate_tl", "TP.TRY.MT06"))
    bonds = _fetch_bond_yields()
    cds = _fetch_cds(bonds)

    result = {
        "policy_rates": {
            "aofm": aofm_val, "aofm_source": "EVDS",
            "comm_loan": comm_loan, "comm_loan_source": "EVDS",
            "deposit": deposit, "deposit_source": "EVDS",
        },
        "bonds": bonds,
        "cds": cds,
    }
    set_cached("macro", result)
    return result

def _fetch_cds(bonds=None):
    """Fetch Turkey 5Y CDS with multi-stage fallback (WorldGov -> TE -> Synthetic)."""
    res = {"val": "N/A", "source": "N/A", "label": "CDS 5Y"}
    
    # 1. Try WorldGovernmentBonds (Dynamic fallback search)
    try:
        r = requests.get("https://www.worldgovernmentbonds.com/country/turkey/", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            # Look for 2xx.xx patterns near CDS keywords
            text = r.text
            match = re.search(r"CDS 5 years.*?(\d{3}\.\d{2})", text, re.I | re.S)
            if match:
                res.update({"val": float(match.group(1)), "source": "SCRAPE:worldgov"})
                return res
    except Exception: pass

    # 2. Try TradingEconomics 
    try:
        r = requests.get("https://tradingeconomics.com/turkey/cds", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            val = soup.select_one("#last")
            if val and val.text.strip():
                res.update({"val": float(val.text.strip()), "source": "SCRAPE:tradingeconomics"})
                return res
    except Exception: pass

    # 3. Fallback: N/A (We avoid misleading synthetic numbers for highly sensitive CDS data)
    return res

def fetch_turkey_macro():
    cached = get_cached("turkey_macro", ttl_seconds=600)
    if cached is not None: return cached
    codes = CONFIG.get("turkey_macro", {})
    result = []
    
    # helper for repetitive EVDS YoY/MoM appends
    def _add_evds_metric(name, series_key, key_slug, unit="%"):
        yoy, mom, date = _evds_yoy_from_index(codes.get(series_key))
        result.append({"name": name, "last": _fmt_pct(yoy), "unit": unit, "date": date, "key": key_slug, "_source": "EVDS+CALC"})
        if series_key == "cpi_index":
             result.append({"name": "Inflation Rate MoM", "last": _fmt_pct(mom), "unit": "%", "date": date, "key": "cpi_mom", "_source": "EVDS+CALC"})

    _add_evds_metric("Inflation Rate YoY", "cpi_index", "cpi")
    _add_evds_metric("Core Inflation YoY", "core_cpi_index", "core_cpi")
    _add_evds_metric("PPI YoY", "ppi_index", "ppi")
    _add_evds_metric("Food Inflation YoY", "food_cpi_index", "food_inflation")

    # Direct values
    def _add_direct(name, series_code, key_slug, unit="%", days=120):
        val = _evds_last_value(series_code, start_days_back=days)
        result.append({"name": name, "last": _fmt_pct(val) if unit=="%" else str(val), "unit": unit, "key": key_slug, "_source": "EVDS"})

    _add_direct("CBRT AOFM", CONFIG.get("macro_panel", {}).get("aofm"), "interest_rate")
    _add_direct("Deposit Rate (TL)", CONFIG.get("macro_panel", {}).get("deposit_rate_tl"), "deposit_rate")
    _add_direct("Commercial Loan Rate", CONFIG.get("macro_panel", {}).get("commercial_loan_rate"), "lending_rate")
    _add_direct("Unemployment Rate", codes.get("unemployment"), "unemployment")
    
    gdp_yoy, gdp_date = _calc_gdp_yoy(codes.get("gdp_volume"))
    result.append({"name": "GDP Growth YoY", "last": _fmt_pct(gdp_yoy), "unit": "%", "date": gdp_date, "key": "gdp_yoy", "_source": "EVDS+CALC"})
    
    _add_direct("Current Account", codes.get("current_account"), "current_account", unit="M USD")
    _add_direct("FX Reserves", codes.get("fx_reserves"), "fx_reserves", unit="M USD", days=60)
    
    # Special formatting for M2 and Credit
    m2 = _evds_last_value(codes.get("m2"), start_days_back=120)
    m2_display = f"{float(str(m2).replace(',','.'))/1e6:.0f} B TL" if m2 != "N/A" else "N/A"
    result.append({"name": "Money Supply M2", "last": m2_display, "unit": "", "key": "m2", "_source": "EVDS"})
    
    credit = _evds_last_value(codes.get("total_credit"), start_days_back=120)
    credit_display = f"{float(str(credit).replace(',','.'))/1e6:.0f} B TL" if credit != "N/A" else "N/A"
    result.append({"name": "Total Domestic Credit", "last": credit_display, "unit": "", "key": "loans_private", "_source": "EVDS"})

    _add_direct("Business Confidence", codes.get("business_confidence"), "biz_confidence", unit="index")
    _add_direct("Consumer Confidence", codes.get("consumer_confidence"), "consumer_confidence", unit="index")

    rating = _fetch_turkey_rating()
    result.append({"name": "Credit Rating (Moody's)", "last": rating.get("rating", "N/A"), "unit": "", "date": rating.get("date", ""), "key": "credit_rating", "_source": "SCRAPE:tradingeconomics"})

    # PPI - CPI Spread (Cost Push Indicator)
    try:
        cpi = next((x["last"] for x in result if x["key"] == "cpi"), "N/A")
        ppi = next((x["last"] for x in result if x["key"] == "ppi"), "N/A")
        if cpi != "N/A" and ppi != "N/A":
            spread = float(ppi) - float(cpi)
            result.append({
                "name": "PPI-CPI Gap", 
                "last": f"{spread:.2f}", 
                "unit": "pts", 
                "key": "ppi_cpi_gap", 
                "_source": "CALC"
            })
    except Exception: pass

    set_cached("turkey_macro", result)
    return result

def fetch_equity_risk():
    """Separate fetch for ERP to avoid blocking macro panel."""
    cached = get_cached("erp", ttl_seconds=300)
    if cached is not None: return cached
    res = fetch_erp()
    set_cached("erp", res)
    return res

def _evds_fetch(series_code, start_date=None, end_date=None, frequency=None):
    if not EVDS_API_KEY or not series_code or series_code == "N/A": return []
    if start_date is None: start_date = (datetime.now() - timedelta(days=60)).strftime("%d-%m-%Y")
    if end_date is None: end_date = datetime.now().strftime("%d-%m-%Y")
    url = f"https://evds3.tcmb.gov.tr/igmevdsms-dis/series={series_code}&startDate={start_date}&endDate={end_date}&type=json"
    if frequency: url += f"&frequency={frequency}"
    try:
        r = requests.get(url, headers={"key": EVDS_API_KEY}, timeout=15)
        return r.json().get("items", []) if r.status_code == 200 else []
    except Exception: return []

def _evds_last_value(series_code, start_days_back=60):
    start = (datetime.now() - timedelta(days=start_days_back)).strftime("%d-%m-%Y")
    items = _evds_fetch(series_code, start)
    if not items: return "N/A"
    col = series_code.replace(".", "_")
    for item in reversed(items):
        if item.get(col) is not None: return item.get(col)
    return "N/A"

def _evds_yoy_from_index(series_code, months_back=14):
    if not series_code: return "N/A", "N/A", ""
    items = _evds_fetch(series_code, (datetime.now() - timedelta(days=months_back*35)).strftime("%d-%m-%Y"))
    if not items: return "N/A", "N/A", ""
    col = series_code.replace(".", "_"); vals = []
    for item in items:
        v = item.get(col)
        if v is not None:
            try: vals.append((item.get("Tarih", ""), float(str(v).replace(",", "."))))
            except ValueError: pass
    if len(vals) < 2: return "N/A", "N/A", ""
    last_val = vals[-1][1]; prev_val = vals[-2][1]
    mom = round(((last_val / prev_val) - 1) * 100, 2) if prev_val else "N/A"
    yoy = round(((last_val / vals[-13][1]) - 1) * 100, 2) if len(vals) >= 13 and vals[-13][1] else "N/A"
    return yoy, mom, vals[-1][0]

def _fetch_bond_yields():
    res = {"tr_2y": "N/A", "tr_10y": "N/A", "us_10y": "N/A", "spread": "N/A", "fed_funds": "N/A", "us_cpi": "N/A"}
    if FRED_API_KEY:
        try:
            # US 10Y
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
            r = requests.get(url, timeout=5)
            obs = r.json().get("observations", [])
            if obs and obs[0]["value"] != ".": res["us_10y"] = float(obs[0]["value"])

            # Fed Funds
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
            r = requests.get(url, timeout=5)
            obs = r.json().get("observations", [])
            if obs and obs[0]["value"] != ".": res["fed_funds"] = float(obs[0]["value"])

            # US CPI YoY
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=13"
            r = requests.get(url, timeout=5)
            obs = r.json().get("observations", [])
            if len(obs) >= 13:
                curr = float(obs[0]["value"])
                prev = float(obs[12]["value"])
                res["us_cpi"] = round(((curr - prev) / prev) * 100, 2)
        except Exception: pass

    # Scraper Fallback
    try:
        # TradingEconomics for TR Bonds
        r = requests.get("https://tradingeconomics.com/turkey/government-bond-yield", headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            for row in soup.select("table tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    name = cells[0].text.lower(); val = cells[1].text
                    try: v = float(val)
                    except ValueError: continue
                    if "10y" in name or "10 year" in name: res["tr_10y"] = v
                    elif "2y" in name or "2 year" in name: res["tr_2y"] = v
        
        # TradingEconomics for US Rates (if FRED failed)
        if res["fed_funds"] == "N/A":
            r = requests.get("https://tradingeconomics.com/united-states/interest-rate", headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "lxml")
                val = soup.select_one("#last")
                if val: res["fed_funds"] = float(val.text.strip())

        # TradingEconomics for US CPI (if FRED failed)
        if res["us_cpi"] == "N/A":
            r = requests.get("https://tradingeconomics.com/united-states/inflation-cpi", headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "lxml")
                val = soup.select_one("#last")
                if val: res["us_cpi"] = float(val.text.strip())

    except Exception: pass

    if res["tr_10y"] != "N/A" and res["us_10y"] != "N/A":
        res["spread"] = round(float(res["tr_10y"]) - float(res["us_10y"]), 2)
    
    if res["tr_10y"] != "N/A" and res["tr_2y"] != "N/A":
        res["tr_yield_curve"] = round(float(res["tr_10y"]) - float(res["tr_2y"]), 2)
    else:
        res["tr_yield_curve"] = "N/A"
    return res

def _calc_gdp_yoy(series_code):
    items = _evds_fetch(series_code, (datetime.now() - timedelta(days=800)).strftime("%d-%m-%Y"))
    if not items: return "N/A", ""
    col = series_code.replace(".", "_"); vals = []
    for item in items:
        v = item.get(col)
        if v is not None:
            try: vals.append((item.get("Tarih", ""), float(str(v).replace(",", "."))))
            except ValueError: pass
    if len(vals) < 5: return "N/A", ""
    yoy = round(((vals[-1][1] / vals[-5][1]) - 1) * 100, 2) if vals[-5][1] else "N/A"
    return yoy, vals[-1][0]

def _fetch_turkey_rating():
    try:
        r = requests.get("https://tradingeconomics.com/turkey/rating", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            for row in soup.select("table tr"):
                cells = row.find_all("td")
                if len(cells) >= 4 and "moody's" in cells[0].text.lower():
                    return {"rating": cells[1].text.strip(), "outlook": cells[2].text.strip(), "date": cells[3].text.strip()}
    except Exception: pass
    return {}

def fetch_cbrt_tracker():
    cached = get_cached("cbrt_tracker", ttl_seconds=3600)
    if cached is not None: return cached
    res = {"current_rate": "N/A", "previous_rate": "N/A", "last_change_date": "N/A", "next_meeting": _get_next_cbrt_meeting(), "history": []}
    series = CONFIG.get("cbrt_tracker", {}).get("policy_rate_series", "TP.APIFON4")
    items = _evds_fetch(series, (datetime.now() - timedelta(days=730)).strftime("%d-%m-%Y"))
    if items:
        col = series.replace(".", "_"); hist = []; prev = None
        for item in items:
            v = item.get(col)
            if v is not None:
                try: r = float(str(v).replace(",", "."))
                except ValueError: continue
                hist.append({"date": item.get("Tarih", ""), "rate": r})
                if prev is not None and r != prev: res["last_change_date"] = item.get("Tarih", "")
                prev = r
        if hist:
            res["current_rate"] = hist[-1]["rate"]
            for i in range(len(hist)-2, -1, -1):
                if hist[i]["rate"] != res["current_rate"]:
                    res["previous_rate"] = hist[i]["rate"]; break
            changes = []; last_r = None
            for h in hist:
                if h["rate"] != last_r:
                    changes.append(h); last_r = h["rate"]
            res["history"] = changes[-24:]
    set_cached("cbrt_tracker", res)
    return res

def _get_next_cbrt_meeting():
    dates = ["2026-03-12", "2026-04-22", "2026-06-11", "2026-07-23", "2026-09-10", "2026-10-22", "2026-12-10", "2027-01-21"]
    today = datetime.now().strftime("%Y-%m-%d")
    for d in dates:
        if d >= today: return d
    return "TBD"

def fetch_economic_calendar():
    cached = get_cached("calendar", ttl_seconds=3600)
    if cached is not None: return cached
    # Simplified logic: merge recurring events
    events = []
    # CBRT
    for d in ["2026-03-12", "2026-04-22", "2026-06-11", "2026-07-23", "2026-09-10", "2026-10-22", "2026-12-10"]:
        events.append({"date": d, "event": "CBRT MPC Meeting", "country": "TR", "importance": "high"})
    # US FOMC
    for d in ["2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09"]:
        events.append({"date": d, "event": "FOMC Rate Decision", "country": "US", "importance": "high"})
    # Monthly releases (simple generation)
    for m in range(2, 13):
        events.append({"date": f"2026-{m:02d}-03", "event": "TR CPI Release", "country": "TR", "importance": "high"})
        events.append({"date": f"2026-{m:02d}-13", "event": "US CPI Release", "country": "US", "importance": "high"})
    
    events.sort(key=lambda x: x["date"])
    set_cached("calendar", events)
    return events

def _fetch_bist_pe():
    """Fetch BIST 100 PE Ratio from TradingEconomics."""
    try:
        r = requests.get("https://tradingeconomics.com/turkey/stock-market", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            # Look for P/E Ratio table
            # Usually in a table with 'Price to Earnings'
            for row in soup.select("table tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    name = cells[0].text.strip()
                    if "Price to Earnings" in name:
                        val = cells[1].text.strip()
                        return float(val)
    except Exception: pass
    return "N/A"

def fetch_erp():
    """Calculate Equity Risk Premium (Earnings Yield - 10Y Bond Yield)."""
    pe = _fetch_bist_pe()
    bonds = _fetch_bond_yields()
    tr_10y = bonds.get("tr_10y", "N/A")
    
    erp = "N/A"
    earnings_yield = "N/A"

    if pe != "N/A" and tr_10y != "N/A":
        earnings_yield = 100 / pe # Convert to percentage
        erp = earnings_yield - tr_10y
    
    return {
        "pe": pe,
        "earnings_yield": round(earnings_yield, 2) if earnings_yield != "N/A" else "N/A",
        "tr_10y": tr_10y,
        "erp": round(erp, 2) if erp != "N/A" else "N/A"
    }


def _fmt_pct(val):
    if val == "N/A" or val is None: return "N/A"
    try: return f"{float(val):.2f}"
    except (ValueError, TypeError): return str(val)
