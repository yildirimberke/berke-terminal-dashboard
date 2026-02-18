"""
The Valuation Engine (Context System)
=====================================
"The Judge"
Computes "Fair Value" for assets using deterministic financial models.
"""
from .analytics import fair_value_ppp
def compute_fair_value(key, current_value):
    """
    Computes the fair value for a given entity key based on its registry model.
    Returns Dict with details or None.
    """
    from .resolver import get_current_level
    from .registry import resolve_entity

    entity = resolve_entity(key)
    if not entity or "valuation" not in entity:
        return None
        
    model_cfg = entity["valuation"]
    model_type = model_cfg["model"]
    inputs = model_cfg["inputs"]
    
    # Fetch Inputs
    input_values = {}
    for k in inputs:
        # resolve_entity might trigger a recursive lookup if not careful, 
        # but inputs are usually macro vars (cpi, rates) which don't have valuation models.
        # We use get_current_level directly.
        ie = resolve_entity(k)
        if ie:
            val, _, _ = get_current_level(ie["key"], ie)
            input_values[k] = val
            
    # Helper to safe float
    def safe_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    # Model Logic
    if model_type == "PPP":
        cpi = safe_float(input_values.get("cpi_yoy"))
        if cpi is not None:
             diff = cpi - 2.5 # US CPI approx
             return {
                 "model": "Relative PPP",
                 "fair_value_desc": f"Inflation Gap ({diff:+.1f}%)",
                 "signal": "Undervalued" if diff > 0 else "Overvalued"
             }
        else:
            return {"model": "Relative PPP", "error": "Waiting for CPI Data"}

    elif model_type == "SOVEREIGN_SPREAD":
        us = safe_float(input_values.get("us_10y"))
        cds = safe_float(input_values.get("cds"))
        
        if us is not None and cds is not None:
            fair_yield = us + (cds / 100.0)
            gap = current_value - fair_yield
            return {
                "model": "Sovereign Spread",
                "fair_value": round(fair_yield, 2),
                "gap": round(gap, 2),
                "message": f"Fair Yield: {fair_yield:.2f}%"
            }
        else:
            missing = []
            if us is None: missing.append("US10Y")
            if cds is None: missing.append("CDS")
            return {"model": "Sovereign Spread", "error": f"Waiting for: {', '.join(missing)}"}

    elif model_type == "ERP_YIELD":
        rf = safe_float(input_values.get("tr_10y"))
        pe = safe_float(input_values.get("pe"))
        
        if rf is not None and pe and pe > 0:
            ey = (100.0 / pe)
            erp = ey - rf
            return {
                "model": "Equity Risk Premium",
                "metric": "ERP",
                "value": round(erp, 2),
                "message": f"ERP: {erp:+.1f}%"
            }
        else:
            return {"model": "Equity Risk Premium", "error": "Waiting for PE/Rates"}
            
    return None
