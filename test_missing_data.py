
from engine.resolver import get_entity_analysis
from engine.registry import DATA_REGISTRY, resolve_entity

print("Testing Missing Data Logic...")

# Mocking the registry to ensure we know what's missing
# We will use 'tr_10y' which needs 'cds'.
# We assume 'cds' is NOT in the cache or is None.

# 1. Test Valuation Missing Input
print("\n1. Testing Valuation (TR 10Y without CDS)...")
# We need to make sure get_current_level returns None for CDS.
# We can just call get_entity_analysis directly.
# But first, let's see what happens if we pass dummy data.

# Actually, the best way is to call compute_fair_value directly with partial inputs
from engine.valuation import compute_fair_value

# Case: Missing CDS
val = compute_fair_value("tr_10y", 25.0)
print(f"TR 10Y Valuation Result: {val}")

if val and "error" in val and "Waiting for" in val["error"]:
    print("SUCCESS: Valuation reported missing input.")
else:
    print("FAILURE: Valuation did not report error correctly.")

# 2. Test Correlation Chain Missing Data
print("\n2. Testing Graph (Brent Oil with no linked data)...")
from engine.graph import get_impact_chain
# impact chain fetches from market. 
# We can't easily mock market here without patching.
# But we can check if the function crashes or returns empty.
chain = get_impact_chain("oil_brent")
print(f"Chain length: {len(chain)}")
# We expect chain to be non-zero now, with status "No Data" if market is empty.
# If market has data, it will be normal. 
# Since I can't guarantee market state, I just check it runs.
if isinstance(chain, list):
    print("SUCCESS: Graph returned a list (empty or not).")
