import unittest
from unittest.mock import patch, MagicMock
from engine.alerts import SigmaScanner

class TestAlerts(unittest.TestCase):
    
    def setUp(self):
        self.scanner = SigmaScanner()
        
    def test_check_anomaly_explicit_history(self):
        # Mean 10, Std ~1.58
        history = [8, 9, 10, 11, 12] * 4 # 20 items to pass threshold
        # Current 15 (> 3 sigmas)
        alert = self.scanner.check_anomaly("TEST", 15, history)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "BLACK_SWAN")
        self.assertTrue("3-SIGMA" in alert["message"])
        
    def test_check_anomaly_normal(self):
        history = [10] * 20
        alert = self.scanner.check_anomaly("TEST", 10.1, history)
        self.assertIsNone(alert)

    @patch("engine.alerts.fetch_history")
    def test_fetch_history_integration(self, mock_fetch):
        # Mock fetch_history to return a list of dicts
        # Simulate stable history 100...100
        mock_data = [{"close": 100.0} for _ in range(50)]
        mock_fetch.return_value = mock_data
        
        # Test a jump to 110 (massive if stddev is 0, but analytics handles 0 stddev safe)
        # Let's add some variance so stddev is not 0
        mock_data[0]["close"] = 101.0
        mock_fetch.return_value = mock_data
        
        # StdDev of [101, 100, 100...] is small (~0.14)
        # Jump to 105 is Huge sigma
        alert = self.scanner.check_anomaly("AAPL", 105.0)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "BLACK_SWAN")
        mock_fetch.assert_called_with("AAPL", period="3mo")

if __name__ == '__main__':
    unittest.main()
