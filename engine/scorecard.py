"""
Macro Risk Scorecard
====================
Aggregates all study-case metrics into a single RISK-ON / RISK-OFF / NEUTRAL
signal with a composite score from -100 (maximum risk-off) to +100 (maximum risk-on).

Each metric is scored from -1 (bearish) to +1 (bullish) and weighted.
"""

from .macro import fetch_turkey_macro, fetch_macro_data, fetch_equity_risk
from .market import fetch_gold_correlation


def _safe_float(val):
    if val is None or val == "N/A":
        return None
    try:
        return float(str(val).replace(",", ".").replace("%", "").strip())
    except (ValueError, TypeError):
        return None


def _find_metric(store, key):
    """Find a metric in turkey_macro store by key."""
    if not store:
        return None
    for item in store:
        if item.get("key") == key:
            return _safe_float(item.get("last"))
    return None


def compute_scorecard():
    """
    Compute aggregate macro scorecard.
    Returns dict with individual scores, composite score, and signal.
    """
    # Fetch all data sources
    turkey_macro = fetch_turkey_macro()
    macro_data = fetch_macro_data()
    erp_data = fetch_equity_risk()
    gold_corr = fetch_gold_correlation()

    bonds = macro_data.get("bonds", {}) if macro_data else {}
    rates = macro_data.get("policy_rates", {}) if macro_data else {}

    scores = {}

    # ─── 1. Yield Curve (TR 10Y - TR 2Y) ───
    # Positive = normal (risk-on), Negative = inverted (recession signal)
    tr_10y = _safe_float(bonds.get("tr_10y"))
    tr_2y = _safe_float(bonds.get("tr_2y"))
    if tr_10y is not None and tr_2y is not None:
        spread = tr_10y - tr_2y
        if spread > 2:
            scores["yield_curve"] = {"score": 1.0, "value": f"{spread:.2f}%", "signal": "STEEP (Normal)"}
        elif spread > 0:
            scores["yield_curve"] = {"score": 0.3, "value": f"{spread:.2f}%", "signal": "FLAT (Watch)"}
        elif spread > -1:
            scores["yield_curve"] = {"score": -0.5, "value": f"{spread:.2f}%", "signal": "INVERTED (Warning)"}
        else:
            scores["yield_curve"] = {"score": -1.0, "value": f"{spread:.2f}%", "signal": "DEEP INVERSION (Danger)"}

    # ─── 2. Real Carry ───
    # Positive = Lira attractive (risk-on for TRY assets)
    deposit = _safe_float(rates.get("deposit"))
    cpi = _find_metric(turkey_macro, "cpi")
    fed = _safe_float(bonds.get("fed_funds"))
    us_cpi = _safe_float(bonds.get("us_cpi"))

    if all(v is not None for v in [deposit, cpi, fed, us_cpi]):
        tr_real = deposit - cpi
        us_real = fed - us_cpi
        carry = tr_real - us_real
        if carry > 5:
            scores["real_carry"] = {"score": 1.0, "value": f"{carry:.1f}%", "signal": "STRONG CARRY"}
        elif carry > 0:
            scores["real_carry"] = {"score": 0.5, "value": f"{carry:.1f}%", "signal": "POSITIVE CARRY"}
        elif carry > -3:
            scores["real_carry"] = {"score": -0.3, "value": f"{carry:.1f}%", "signal": "NEGATIVE CARRY"}
        else:
            scores["real_carry"] = {"score": -1.0, "value": f"{carry:.1f}%", "signal": "CAPITAL FLIGHT RISK"}

    # ─── 3. PPI-CPI Gap ───
    # Positive gap = margin squeeze on producers (bearish for equities)
    ppi_cpi = _find_metric(turkey_macro, "ppi_cpi_gap")
    if ppi_cpi is not None:
        if ppi_cpi < -5:
            scores["ppi_cpi_gap"] = {"score": 0.5, "value": f"{ppi_cpi:.1f} pts", "signal": "DEFLATIONARY (Margins expanding)"}
        elif ppi_cpi < 0:
            scores["ppi_cpi_gap"] = {"score": 0.3, "value": f"{ppi_cpi:.1f} pts", "signal": "HEALTHY"}
        elif ppi_cpi < 5:
            scores["ppi_cpi_gap"] = {"score": -0.3, "value": f"{ppi_cpi:.1f} pts", "signal": "COST PRESSURE"}
        else:
            scores["ppi_cpi_gap"] = {"score": -1.0, "value": f"{ppi_cpi:.1f} pts", "signal": "MARGIN SQUEEZE"}

    # ─── 4. Equity Risk Premium (ERP) ───
    # Positive = stocks cheap vs bonds (risk-on), Negative = bonds dominate
    erp = _safe_float(erp_data.get("erp")) if erp_data else None
    if erp is not None:
        if erp > 3:
            scores["erp"] = {"score": 1.0, "value": f"{erp:.1f}%", "signal": "STOCKS CHEAP"}
        elif erp > 0:
            scores["erp"] = {"score": 0.3, "value": f"{erp:.1f}%", "signal": "STOCKS FAIR"}
        elif erp > -5:
            scores["erp"] = {"score": -0.5, "value": f"{erp:.1f}%", "signal": "BONDS ATTRACTIVE"}
        else:
            scores["erp"] = {"score": -1.0, "value": f"{erp:.1f}%", "signal": "STOCKS EXPENSIVE"}

    # ─── 5. CDS / Sovereign Risk ───
    cds = _find_metric(turkey_macro, "cds_5y") if turkey_macro else None
    if cds is None:
        # Try from macro_data
        cds = _safe_float(macro_data.get("cds", {}).get("value")) if macro_data else None
    if cds is not None:
        if cds < 200:
            scores["cds"] = {"score": 1.0, "value": f"{cds:.0f} bps", "signal": "LOW RISK"}
        elif cds < 350:
            scores["cds"] = {"score": 0.3, "value": f"{cds:.0f} bps", "signal": "MODERATE"}
        elif cds < 500:
            scores["cds"] = {"score": -0.5, "value": f"{cds:.0f} bps", "signal": "ELEVATED"}
        else:
            scores["cds"] = {"score": -1.0, "value": f"{cds:.0f} bps", "signal": "DISTRESSED"}

    # ─── 6. Gold Correlation (FX Hedge vs Commodity) ───
    corr_usd = _safe_float(gold_corr.get("corr_usd")) if gold_corr else None
    if corr_usd is not None:
        if corr_usd > 0.85:
            scores["gold_corr"] = {"score": -0.8, "value": f"{corr_usd}", "signal": "PURE FX HEDGE (Lira fear)"}
        elif corr_usd > 0.5:
            scores["gold_corr"] = {"score": -0.3, "value": f"{corr_usd}", "signal": "MIXED DRIVER"}
        else:
            scores["gold_corr"] = {"score": 0.5, "value": f"{corr_usd}", "signal": "COMMODITY PLAY (Healthy)"}

    # ─── Composite Score ───
    weights = {
        "yield_curve": 0.20,
        "real_carry": 0.20,
        "ppi_cpi_gap": 0.10,
        "erp": 0.20,
        "cds": 0.20,
        "gold_corr": 0.10,
    }

    total_weight = 0
    weighted_sum = 0
    for key, w in weights.items():
        if key in scores:
            weighted_sum += scores[key]["score"] * w
            total_weight += w

    if total_weight > 0:
        composite = (weighted_sum / total_weight) * 100  # Scale to -100 to +100
    else:
        composite = 0

    # Signal
    if composite > 25:
        signal = "RISK-ON"
    elif composite > -25:
        signal = "NEUTRAL"
    else:
        signal = "RISK-OFF"

    return {
        "scores": scores,
        "composite": round(composite, 1),
        "signal": signal,
        "metrics_available": len(scores),
        "metrics_total": len(weights),
    }
