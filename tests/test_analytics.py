import unittest
from engine.analytics import z_score, percentile_rank, real_return, implied_carry_trade, fair_value_ppp

class TestAnalytics(unittest.TestCase):
    
    def test_z_score_basic(self):
        # Mean 10, StdDev ~2.23
        history = [8, 9, 10, 11, 12]
        # Mean of [8, 9, 10, 11, 12] is 10.0
        # Sample StdDev (divisor N-1) is 1.5811
        # Current = 14. Diff = 4.
        # Z = 4 / 1.5811 = 2.5298 (approx)
        z = z_score(14, history)
        self.assertAlmostEqual(z, 2.5298, places=3)
        
    def test_z_score_edge_cases(self):
        self.assertEqual(z_score(10, []), 0.0) # Empty
        self.assertEqual(z_score(10, [10]), 0.0) # Single item
        self.assertEqual(z_score(10, [5, 5, 5]), 0.0) # Zero variance
        self.assertEqual(z_score(10, [None, 5, 5]), 0.0) # None handling

    def test_percentile_rank(self):
        history = [10, 20, 30, 40, 50]
        self.assertEqual(percentile_rank(35, history), 0.6) # Greater than 3 items (60%)
        self.assertEqual(percentile_rank(5, history), 0.0) # Lowest
        self.assertEqual(percentile_rank(60, history), 1.0) # Highest
        self.assertEqual(percentile_rank(10, []), 0.5) # Fallback

    def test_real_return(self):
        # 50% Nominal, 40% Inflation
        # (1.50 / 1.40) - 1 = 1.0714 - 1 = 0.0714 (7.14%)
        # Approx calculation (50-40=10) is wrong. Fisher is accurate.
        r = real_return(0.50, 0.40)
        self.assertAlmostEqual(r, 0.0714, places=4)
        
        # Deflation case
        # Nominal 5%, Inflation -2%
        # (1.05 / 0.98) - 1 = 0.0714
        r_def = real_return(0.05, -0.02)
        self.assertAlmostEqual(r_def, 0.0714, places=4)

    def test_implied_carry(self):
        # TR Rate 50%, US Rate 5%
        # USDTRY 30.00
        # Expected USDTRY 40.00 (33% depreciation)
        # Carry = (0.50 - 0.05) - 0.333 = 0.45 - 0.333 = 0.117
        res = implied_carry_trade(0.50, 0.05, 30.0, 40.0)
        self.assertAlmostEqual(res, 0.1166, places=3)
    
    def test_fair_value_ppp(self):
        # Spot 30.00
        # TR Inf 0.50, US Inf 0.05 -> Diff 0.45
        # Fair = 30 * 1.45 = 43.5
        res = fair_value_ppp(30.0, 0.50, 0.05)
        self.assertEqual(res, 43.5)

if __name__ == '__main__':
    unittest.main()
