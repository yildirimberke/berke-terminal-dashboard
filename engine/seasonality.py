"""
The Seasonality Engine
======================
"History doesn't repeat, but it rhymes."
Analyzes 10-year historical data to find seasonal tendencies (e.g. "USDTRY rises in Dec").
Also provides intraday context (e.g. "London Fix").
"""
from datetime import datetime
import statistics
from .market import fetch_long_history

def get_monthly_seasonality(symbol):
    """
    Computes average monthly returns over the last 10 years.
    Returns: Dict {month_int: avg_return_pct} and best/worst months.
    """
    # Fetch 10y monthly data
    # We rely on market.fetch_long_history defaulting to period="10y", interval="1mo"
    history = fetch_long_history(symbol)
    if not history:
        return None
        
    # Group by month
    month_changes = {m: [] for m in range(1, 13)}
    
    for candle in history:
        # candle = {date, month, year, close, open}
        # Calculate % change for that month
        if candle["open"] and candle["open"] > 0:
            chg = ((candle["close"] - candle["open"]) / candle["open"]) * 100
            month_changes[candle["month"]].append(chg)
            
    # Compute Averages
    seasonality = {}
    for m, changes in month_changes.items():
        if changes:
            avg = statistics.mean(changes)
            win_rate = len([x for x in changes if x > 0]) / len(changes) * 100
            seasonality[m] = {
                "avg_return": round(avg, 2),
                "win_rate": round(win_rate, 0),
                "count": len(changes)
            }
            
    if not seasonality:
        return None
        
    # Context Logic: "Best Month", "Worst Month"
    # Find current month stats
    current_month = datetime.now().month
    current_stats = seasonality.get(current_month)
    
    return {
        "monthly_map": seasonality,
        "current_month_stats": current_stats,
        "current_month_name": datetime.now().strftime("%B")
    }

def get_intraday_context():
    """
    Checks if we are near key liquidity events (London Fix, Market Opens).
    Returns list of strings or None.
    """
    import pytz
    
    now_utc = datetime.now(pytz.utc)
    tz_ist = pytz.timezone('Europe/Istanbul')
    now_ist = now_utc.astimezone(tz_ist)
    
    warnings = []
    
    # London Fix (16:00 London = 19:00 TR in Winter, 18:00 in Summer?)
    # Let's use London time directly to be safe.
    tz_ldn = pytz.timezone('Europe/London')
    now_ldn = now_utc.astimezone(tz_ldn)
    
    # Fix is at 16:00 London
    if now_ldn.hour == 15 and now_ldn.minute >= 45:
        warnings.append("⚠️ Approaching London Fix (16:00 LDN) - High Volatility Exp.")
    elif now_ldn.hour == 16 and now_ldn.minute <= 15:
         warnings.append("London Fix Window")
         
    # US Open (09:30 NY)
    tz_ny = pytz.timezone('America/New_York')
    now_ny = now_utc.astimezone(tz_ny)
    
    if now_ny.hour == 9 and 20 <= now_ny.minute < 30:
        warnings.append("🔔 US Market Open Imminent")
        
    return warnings if warnings else None
