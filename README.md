# Bloomberg Terminal Lite (Python/Streamlit)

A professional, high-precision financial dashboard for personal use.

## Features
- **Zero Hallucination Policy:** Data is either verified from official sources (EVDS, FRED) or marked "N/A".
- **Dual Macro Data:** Displays both Policy Rate (Repo) and Funding Cost (AOFM) side-by-side.
- **Real-Time Market Data:** Uses Yahoo Finance with strict previous-close calculation.
- **Scraped Intelligence:** BIST "Stars of the Day" directly from BloombergHT.
- **News Wire:** Aggregated RSS feeds from BloombergHT and Investing.com.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
- Rename `.env.example` to `.env`
- Add your **TCMB EVDS API Key** (Required for Macro Data)
- Add your **FRED API Key** (Required for US Yields)

### 3. Run Data Setup (Critical)
This script will help you find and map the exact EVDS Series Codes (e.g., `TP.KTF10`).
```bash
python setup_evds.py
```
Follow the on-screen prompts to search for "tahvil" or "politika" and select the correct series.

### 4. Launch Terminal
```bash
streamlit run main.py
```

## Directory Structure
- `main.py`: Main dashboard application.
- `modules/`:
  - `macro_data.py`: EVDS/FRED client.
  - `market_data.py`: Yahoo Finance client.
  - `scraper.py`: BloombergHT scraper.
  - `news.py`: RSS aggregator.
  - `ui_components.py`: Custom HTML/CSS widgets.
- `config.json`: Stores your verified series codes.
