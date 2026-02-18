
from engine.alerts import SigmaScanner

scanner = SigmaScanner()

print("Testing Divergence Logic...")

# Case 1: Hidden Stress (USDTRY Flat, CDS Spiking)
print("\nCase 1: Hidden Stress (USDTRY Flat, CDS +3.5%)")
alerts = scanner.check_divergence(
    "usdtry", 
    current_val=34.50, 
    change_pct=0.05, 
    related_data={"cds": {"value": 300, "change_pct": 3.5}}
)
if alerts:
    print("SUCCESS: Alert Triggered ->", alerts[0]["message"])
else:
    print("FAILURE: No Alert")

# Case 2: Normal Market (USDTRY Up, CDS Down)
print("\nCase 2: Normal Market (USDTRY +1%, CDS -2%)")
alerts = scanner.check_divergence(
    "usdtry", 
    current_val=34.80, 
    change_pct=1.0, 
    related_data={"cds": {"value": 290, "change_pct": -2.0}}
)
if alerts:
    print("FAILURE: Alert Triggered ->", alerts[0]["message"])
else:
    print("SUCCESS: No Alert")

# Case 3: Fragile Rally (BIST Up, VIX Spiking)
print("\nCase 3: Fragile Rally (BIST +1.5%, VIX +6%)")
alerts = scanner.check_divergence(
    "bist100", 
    current_val=9000, 
    change_pct=1.5, 
    related_data={"vix": {"value": 25, "change_pct": 6.0}}
)
if alerts:
    print("SUCCESS: Alert Triggered ->", alerts[0]["message"])
else:
    print("FAILURE: No Alert")
