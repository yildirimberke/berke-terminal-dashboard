"""
The Second-Order Map (Graph Engine)
===================================
"The Market Graph"
Maps causal relationships between assets (e.g. Oil -> Airlines).
Checks if correlated assets are moving in sync or diverging.
"""
from .alerts import SigmaScanner

SCANNER = SigmaScanner()

def get_impact_chain(trigger_key):
    """
    Returns a list of correlated assets and their reaction status.
    Args:
        trigger_key: The entity being viewed (e.g. 'oil_brent').
    Returns:
        List of dicts: [
            {"symbol": "THYAO.IS", "correlation": "Linked", "z_score": -1.5, "status": "Clean"}
        ]
    """
    from .resolver import get_current_level
    from .registry import resolve_entity
    entity = resolve_entity(trigger_key)
    if not entity or "correlations" not in entity:
        return []
        
    chain = []
    
    for linked_key in entity["correlations"]:
        # Resolve linked entity
        # Note: correlated keys in registry might be tickers (THYAO.IS) or logic keys (@thyao)
        # We try resolve_entity first.
        linked_ent = resolve_entity(linked_key) 
        
        # If not found via resolve_entity (maybe it's a raw ticker not in registry?),
        # fallback to using it as a raw key for market fetch.
        if not linked_ent:
            # Create a dummy entity wrapper for raw tickers
            linked_ent = {"key": linked_key, "technical_key": linked_key, "source": "market", "name": linked_key}
            
        # Get live data
        val, _, chg = get_current_level(linked_ent["key"], linked_ent)
        
        if val is None:
            # Still append to show the link exists, but mark as N/A
            chain.append({
                "key": linked_ent.get("key"),
                "name": linked_ent.get("name"),
                "price": "N/A",
                "change_pct": 0,
                "z_score": 0.0,
                "status": "No Data"
            })
            continue

        # Check Z-Score for the linked asset to see if it's reacting
        # We need history for Z-Score. 
        # Using SCANNER.check_anomaly which fetches history internally.
        alert = SCANNER.check_anomaly(linked_ent["key"], val)
        
        z = alert["z_score"] if alert else 0.0
        
        chain.append({
            "key": linked_ent.get("key"),
            "name": linked_ent.get("name"),
            "price": val,
            "change_pct": chg,
            "z_score": z,
            "alert": alert # Full alert dict if exists
        })
        
    return chain
