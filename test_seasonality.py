
from engine.market import fetch_long_history
from engine.seasonality import get_monthly_seasonality

print("Testing fetch_long_history for USDTRY=X...")
hist = fetch_long_history("USDTRY=X")
if hist:
    print(f"Success! Got {len(hist)} records.")
    print("First record:", hist[0])
    print("Last record:", hist[-1])
else:
    print("Failed to fetch history.")

print("\nTesting get_monthly_seasonality for USDTRY=X...")
seas = get_monthly_seasonality("USDTRY=X")
if seas:
    print("Seasonality Map keys:", seas["monthly_map"].keys())
    print("Current month stats:", seas["current_month_stats"])
else:
    print("Failed to compute seasonality.")
