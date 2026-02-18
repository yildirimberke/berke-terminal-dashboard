"""
The Mathematical Core (Analytics Engine)
========================================
Pure functions for financial and statistical analysis.
NO external API calls. NO side effects. 100% Testable.

"Bloomberg-level precision means handling NaNs, 
 zero-division, and edge cases gracefully."
"""
import math
import statistics

def z_score(current_value, history_series):
    """
    Computes the Z-Score (Standard Deviations from Mean).
    
    Args:
        current_value (float): The live price/value.
        history_series (list[float]): List of historical values (e.g. 30 days).
        
    Returns:
        float: The Z-Score. 
               +2.0 means 2 StdDev above mean.
               Returns 0.0 if not enough data (<2 points).
    """
    clean_history = [x for x in history_series if x is not None]
    # For a live Z-Score, we should check where 'current' sits within the distribution
    # OF THE HISTORY. 
    # Option A: (Current - Mean_History) / StdDev_History
    # Option B: Add Current to History, then Compute.
    # Bloomberg usually compares Current to the Moving Average of the LAST N days.
    # So Current is NOT in the history used for Mean/StdDev.
    
    if len(clean_history) < 2:
        return 0.0
        
    mean = statistics.mean(clean_history)
    stdev = statistics.stdev(clean_history)
    
    if stdev == 0:
        return 0.0
        
    return (current_value - mean) / stdev

def percentile_rank(current_value, history_series):
    """
    Computes the percentile rank of the current value against history.
    0.0 = Lowest ever, 1.0 = Highest ever.
    """
    clean_history = [x for x in history_series if x is not None]
    if not clean_history:
        return 0.5 # Neutral fallback
        
    # Count how many historical values are less than current
    count = sum(1 for x in clean_history if x < current_value)
    return count / len(clean_history)

def real_return(nominal_rate, inflation_rate):
    """
    Fisher Equation: (1 + n) = (1 + r) * (1 + i)
    Returns r = (1 + n)/(1 + i) - 1
    
    Args:
        nominal_rate (float): E.g. 0.50 for 50%.
        inflation_rate (float): E.g. 0.40 for 40%.
    """
    if inflation_rate <= -1.0: # Hyper-deflation protection
        return 0.0
        
    return ((1 + nominal_rate) / (1 + inflation_rate)) - 1

def implied_carry_trade(long_yield, short_yield, spot_fx, expected_spot_fx):
    """
    Calculates the expected return of a carry trade.
    
    Args:
        long_yield (float): Annual yield of currency being bought (e.g. TRY 0.50).
        short_yield (float): Annual yield of currency being borrowed (e.g. USD 0.05).
        spot_fx (float): Current USDTRY.
        expected_spot_fx (float): Expected USDTRY in 1 year.
    
    Returns:
        float: Expected ROI (e.g. 0.12 for 12%).
    """
    interest_diff = long_yield - short_yield
    fx_depreciation = (expected_spot_fx - spot_fx) / spot_fx
    
    # Approx logic: Yield - Depreciation
    return interest_diff - fx_depreciation

def fair_value_ppp(spot_fx, home_cpi_index, foreign_cpi_index, base_spot_fx=None):
    """
    Relative PPP Model:
    Fair Change % = (Home Inflation / Foreign Inflation) - 1
    
    Since we don't have infinite history, we use 'Inflation Differential' to 
    adjust a 'Base Fair Value'.
    
    Simplified for Terminal Use:
    Fair Value = Spot * (1 + (Home_Inf - Foreign_Inf))
    (Assuming Spot was 'Fair' 1 period ago)
    
    Args:
        spot_fx (float): Current price.
        home_cpi_index (float): YoY Inflation (e.g. 0.45).
        foreign_cpi_index (float): YoY Inflation (e.g. 0.03).
    
    Returns:
        float: The 'Theoretical' fair value based on inflation differential forcing.
    """
    diff = home_cpi_index - foreign_cpi_index
    return spot_fx * (1 + diff) # Very rough 'Instant' PPP pressure. 
                                # Better: use a base period, but we lack deep DB. 
