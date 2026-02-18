
import unittest
from engine.scraper import SmartScraper

class MockResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

class TestSmartScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = SmartScraper()

    def test_price_extraction(self):
        # Simulated HTML from a financial site
        html = """
        <html>
            <h1>USD/TRY Exchange Rate</h1>
            <div class="price-container">
                <span class="label">Last Price</span>
                <span class="value">34.50</span>
                <span class="currency">TRY</span>
            </div>
            <p>The previous close was 34.20.</p>
        </html>
        """
        # Mock requests.get
        import requests
        original_get = requests.get
        requests.get = lambda url, headers=None, timeout=5: MockResponse(html)
        
        try:
            # Test 1: Finding "34.50" near "USD/TRY" or "Price"
            val = self.scraper.fetch_price("http://mock", ["USD/TRY", "Price"])
            print(f"Extracted: {val}")
            self.assertEqual(val, 34.50)
            
        finally:
            requests.get = original_get

if __name__ == '__main__':
    unittest.main()
