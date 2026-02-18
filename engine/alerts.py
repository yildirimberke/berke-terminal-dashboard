"""
The Anomaly Engine (Alerts System)
==================================
"The Watchman"
Systematically scans market data for "glitches in the matrix" using 
statistical models from engine.analytics.

Logic:
    If Z-Score > 2.0 (2 StdDevs): "Sigma Alert" (Rare)
    If Z-Score > 3.0 (3 StdDevs): "Black Swan Alert" (Very Rare)
"""
from .analytics import z_score
from .market import fetch_history
from .config import TICKER_CATEGORIES

class SigmaScanner:
    def __init__(self):
        self.history_cache = {} # Key -> List[Close Prices]
    
    def check_anomaly(self, key, current_value, history_series=None):
        """
        Checks if the current value is a statistical anomaly.
        Returns None or a Dict with alert details.
        
        Args:
            key (str): Ticker symbol or registry key (e.g. 'USDTRY=X', 'gap').
            current_value (float): Live value.
            history_series (list): Optional list of historical floats.
        """
        hist = history_series
        
        # If no history provided, try to fetch it
        if not hist or len(hist) < 5:
            # We assume key is a valid ticker if we are here
            # For non-tickers (macro), history might be passed in differently
            try:
                raw_hist = fetch_history(key, period="3mo")
                if raw_hist:
                    hist = [x["close"] for x in raw_hist if x.get("close")]
            except Exception:
                pass

        if not hist or len(hist) < 20: # Need decent sample size for Z-Score
            return None
            
        z = z_score(current_value, hist)
        
        # Thresholds
        if abs(z) >= 3.0:
            return {
                "type": "BLACK_SWAN",
                "level": "CRITICAL",
                "message": f"3-SIGMA EVENT ({z:+.1f}σ)",
                "z_score": round(z, 2)
            }
        elif abs(z) >= 2.0:
            return {
                "type": "SIGMA",
                "level": "WARNING",
                "message": f"Sigma Alert ({z:+.1f}σ)",
                "z_score": round(z, 2)
            }
            
        return None

    def check_divergence(self, key, current_val, change_pct, related_data={}):
        """
        Checks for cross-asset divergences (e.g. Price flat but Risk rising).
        related_data: Dict of {key: {"value": float, "change_pct": float}}
        """
        alerts = []
        
        # 1. USDTRY vs CDS (Hidden Analysis)
        # If USDTRY is flat/down but CDS is spiking -> Artificial Stability?
        if key == "usdtry" and related_data.get("cds"):
            cds = related_data["cds"]
            cds_chg = cds.get("change_pct", 0)
            
            if abs(change_pct) < 0.1 and cds_chg > 2.0:
                 alerts.append({
                     "type": "DIVERGENCE",
                     "level": "WARNING",
                     "message": "Hidden Stress: Lira flat but CDS spiking (+{:.1f}%)".format(cds_chg)
                 })

        # 2. BIST100 vs VIX (Fragile Rally)
        # If BIST is rallying but VIX (Global Fear) is rising -> Trap?
        if key == "bist100" and related_data.get("vix"):
            vix = related_data["vix"]
            vix_chg = vix.get("change_pct", 0)
            
            if change_pct > 1.0 and vix_chg > 5.0:
                 alerts.append({
                     "type": "DIVERGENCE",
                     "level": "CAUTION",
                     "message": "Fragile Rally: BIST up despite Global Fear (VIX +{:.1f}%)".format(vix_chg)
                 })
                 
        return alerts if alerts else None
