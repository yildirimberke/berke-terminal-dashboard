from .cache import get_cached
from .market import fetch_market_data, fetch_gold_correlation
from .macro import fetch_macro_data, fetch_turkey_macro, fetch_cbrt_tracker, fetch_equity_risk
from .scorecard import compute_scorecard
from .alerts import SigmaScanner
from .valuation import compute_fair_value
from .graph import get_impact_chain

# Global scanner instance to share cache if implemented later
SCANNER = SigmaScanner()

def get_entity_analysis(key, current_value, change_pct=0.0):
    """
    Orchestrates all analysis engines (Alerts, Valuation, Graph, Seasonality).
    Returns a dict with 'alerts', 'valuation', 'graph', 'seasonality' keys.
    """
    result = {}

    # 1. Anomaly / Sigma Scanner
    try:
        # We need history for anomaly detection. 
        # For optimization, we rely on cached history or fetch fresh if critical.
        alert = SCANNER.check_anomaly(key, current_value)
        if alert:
            result["alert"] = alert
    except Exception as e:
        print(f"[resolver] Anomaly check failed for {key}: {e}")

    # 2. Valuation Engine
    try:
        val_data = compute_fair_value(key, current_value)
        if val_data:
            result["valuation"] = val_data
    except Exception as e:
        print(f"[resolver] Valuation failed for {key}: {e}")

    # 3. Graph / Second-Order
    try:
        chain = get_impact_chain(key)
        if chain:
            result["graph"] = chain
    except Exception as e:
        print(f"[resolver] Graph failed for {key}: {e}")

    # 4. Seasonality
    try:
        # Only check seasonality for major assets (tickers)
        if "." in key or "=" in key or key in ["usdtry", "eurtry", "xauusd", "bist100"]:
             from .seasonality import get_monthly_seasonality
             from .registry import resolve_entity # Fix NameError
             
             # Map simple keys to tickers if needed, but let's assume key is passable or resolver helps.
             # Actually get_monthly_seasonality calls fetch_long_history(symbol).
             # If key is "usdtry", fetch_long_history needs "USDTRY=X".
             # We should use the entity's technical_key or symbol.
             entity = resolve_entity(key)
             if entity:
                 sym = entity.get("technical_key") or entity.get("key")
                 # Check if it's a valid ticker format for yfinance
                 if sym:
                     seas = get_monthly_seasonality(sym)
                     if seas:
                         result["seasonality"] = seas
    except Exception as e:
        print(f"[resolver] Seasonality failed for {key}: {e}")

    # 5. Divergence Spotter
    try:
        related_metrics = {}
        # Fetch CDS for USDTRY
        if key == "usdtry":
            cds_ent = resolve_entity("cds")
            if cds_ent:
                val, _, chg = get_current_level("cds", cds_ent)
                if val: related_metrics["cds"] = {"value": val, "change_pct": chg}
        
        # Fetch VIX for BIST100
        elif key == "bist100":
             # VIX might be registered as 'vix' or part of macro
             vix_ent = resolve_entity("vix") # Ensure 'vix' is in registry
             if vix_ent:
                 vix_val, _, vix_chg = get_current_level("vix", vix_ent)
                 if vix_val: related_metrics["vix"] = {"value": vix_val, "change_pct": vix_chg}

        if related_metrics:
            div_alerts = SCANNER.check_divergence(key, current_value, change_pct, related_metrics)
            if div_alerts:
                # Merge with existing alert if any, or create list
                # Currently 'alert' key is a single dict. We might need a list 'alerts'.
                # For now, let's just REPLACE 'alert' if it's None, or append to a new 'divergence' key.
                # Let's use a new key 'divergence' for clarity in UI.
                result["divergence"] = div_alerts[0] # Just take the first one for now
                
    except Exception as e:
        print(f"[resolver] Divergence failed for {key}: {e}")
        
    return result

def get_current_level(entity_key, entity_data):
    """
    Given an entity key (e.g. 'usdtry') and its registry data (dict),
    attempt to find its current live value from the various engine caches.
    Returns (value, unit, change_pct) or (None, None, None).
    """
    tech_key = entity_data.get("technical_key")
    source = entity_data.get("source")
    
    # Proactive Fetching if cache empty
    def get_or_fetch(cache_key, fetch_func):
        val = get_cached(cache_key)
        if val is None:
            try:
                # Some compute functions don't take args, others might. 
                # Most fetchers are arg-less.
                return fetch_func()
            except Exception:
                return None
        return val

    # 1. Market Data (Direct Ticker)
    if source == "market":
        market = get_or_fetch("market", fetch_market_data)
        if market and tech_key in market:
            m = market[tech_key]
            return m.get("price"), entity_data.get("unit"), m.get("change_pct")

    # 2. Macro Data (Policy Rates, Bonds, CDS)
    if source == "macro":
        macro = get_or_fetch("macro", fetch_macro_data)
        if macro:
            # Check Policy Rates
            if tech_key in macro.get("policy_rates", {}):
                return macro["policy_rates"][tech_key], "%", None
            # Check Bonds
            if tech_key in macro.get("bonds", {}):
                val = macro["bonds"][tech_key]
                unit = "%"
                if tech_key in ["spread", "tr_yield_curve", "risk_premium"]:
                     unit = "bps"
                     val = val * 100 if isinstance(val, (int, float)) else val
                return val, unit, None
            # Check CDS
            if tech_key == "cds" and macro.get("cds"):
                return macro["cds"].get("val"), "bps", None

    # 3. Turkey Macro / EVDS+CALC
    if source == "macro" or source == "EVDS+CALC":
        tm = get_or_fetch("turkey_macro", fetch_turkey_macro)
        if tm:
            for item in tm:
                if item.get("key") == entity_key or item.get("key") == tech_key:
                    return item.get("last"), item.get("unit"), None

    # 4. ERP Specific
    if source == "equity_risk":
        erp = get_or_fetch("erp", fetch_equity_risk)
        if erp and tech_key in erp:
            return erp[tech_key], entity_data.get("unit", "%"), None
        # Bonds are also under equity_risk sometimes in registry
        macro = get_or_fetch("macro", fetch_macro_data)
        if macro and tech_key in macro.get("bonds", {}):
            return macro["bonds"][tech_key], "%", None

    # 5. CBRT Tracker
    if source == "cbrt":
        cbrt = get_or_fetch("cbrt_tracker", fetch_cbrt_tracker)
        if cbrt:
            if tech_key == "aofm" or tech_key == "policy_rate":
                return cbrt.get("current_rate"), "%", None
            if tech_key == "next_meeting":
                return cbrt.get("next_meeting"), "", None

    # 6. Scorecard / Correlation
    if source == "gold_corr":
        gc = get_or_fetch("gold_corr", fetch_gold_correlation)
        if gc:
            if tech_key == "gold_corr" or tech_key == "composite":
                return gc.get("corr_usd"), "", None
    
    if source == "scorecard":
        sc = get_or_fetch("scorecard", compute_scorecard)
        if sc and tech_key == "composite":
            return sc.get("composite"), "pts", None

    # 7. Banking Monitor
    if source == "banking":
        from .macro import fetch_banking_monitor
        bm = get_or_fetch("banking_monitor", fetch_banking_monitor)
        if bm and tech_key in bm:
             return bm[tech_key], entity_data.get("unit"), None

    # 8. Sentiment (Google Trends)
    if source == "sentiment":
        from .macro import fetch_sentiment_dashboard
        sent = get_or_fetch("sentiment", fetch_sentiment_dashboard)
        if sent:
            # key is "panic_score" or "greed_score"
            # tech_key is "panic" or "greed"
            # but TrendsExtractor returns "panic_score", "greed_score"
            # registry tech_key is "panic", "greed".
            # Mapping: panic -> panic_score
            mapped_key = f"{tech_key}_score" if not tech_key.endswith("_score") else tech_key
            if mapped_key in sent:
                 return sent[mapped_key], entity_data.get("unit"), None
            # Or direct match
            if tech_key in sent:
                 return sent[tech_key], entity_data.get("unit"), None

    # 9. Trade (TİM)
    if source == "trade":
        from .macro import fetch_trade_data
        trade = get_or_fetch("trade", fetch_trade_data)
        if trade:
            if tech_key == "total_exports":
                # Add sectors to related values in the future?
                return trade.get("total_exports"), entity_data.get("unit"), None

    return None, None, None
