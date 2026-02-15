import os
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

EVDS_API_KEY = os.getenv("EVDS_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

with open(os.path.join(BASE_DIR, "config.json"), "r") as f:
    CONFIG = json.load(f)

ALL_TICKERS = {
    # Indices
    "XU100.IS": "BIST 100",
    "XU030.IS": "BIST 30",
    "^GSPC":    "S&P 500",
    "^OEX":     "S&P 100",
    "^DJI":     "Dow Jones",
    "^IXIC":    "NASDAQ",
    "^NDX":     "NASDAQ-100",
    "^FTSE":    "FTSE 100",
    "^GDAXI":   "DAX",
    "^N225":    "Nikkei 225",
    "^RUT":     "Russell 2000",
    # US Sector ETFs
    "XLK":      "S&P Tech",
    "XLF":      "S&P Financials",
    "XLE":      "S&P Energy",
    "XLV":      "S&P Healthcare",
    "XLI":      "S&P Industrials",
    "XLY":      "S&P Cons Disc",
    "XLP":      "S&P Cons Staples",
    # Crypto
    "BTC-USD":  "Bitcoin",
    "ETH-USD":  "Ethereum",
    "SOL-USD":  "Solana",
    "XRP-USD":  "XRP",
    "BNB-USD":  "BNB",
    # Commodities – Metals
    "GC=F":     "Gold",
    "SI=F":     "Silver",
    "PL=F":     "Platinum",
    "PA=F":     "Palladium",
    "HG=F":     "Copper",
    # Commodities – Energy
    "CL=F":     "Oil WTI",
    "BZ=F":     "Oil Brent",
    "NG=F":     "Natural Gas",
    # Commodities – Agricultural
    "ZW=F":     "Wheat",
    "ZC=F":     "Corn",
    "KC=F":     "Coffee",
    "CT=F":     "Cotton",
    # Currencies
    "USDTRY=X": "USD/TRY",
    "EURTRY=X": "EUR/TRY",
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    # Volatility
    "^VIX":     "VIX",
}

TICKER_CATEGORIES = {
    "indices":     ["XU100.IS", "XU030.IS", "^GSPC", "^OEX", "^DJI", "^IXIC", "^NDX", "^FTSE", "^GDAXI", "^N225", "^RUT"],
    "sectors":     ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP"],
    "crypto":      ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD"],
    "commodities": ["GC=F", "SI=F", "PL=F", "PA=F", "HG=F", "CL=F", "BZ=F", "NG=F", "ZW=F", "ZC=F", "KC=F", "CT=F"],
    "currencies":  ["USDTRY=X", "EURTRY=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X"],
    "volatility":  ["^VIX"],
}

TICKER_TAPE_ORDER = [
    "XU100.IS", "^GSPC", "^DJI", "^IXIC", "^NDX", "^GDAXI", "^FTSE", "^N225",
    "BTC-USD", "ETH-USD", "GC=F", "BZ=F",
    "USDTRY=X", "EURTRY=X", "^VIX",
]
