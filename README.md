# 📊 Berke Yıldırım's Dashboard — Professional Market Terminal
*High-Density Financial Intelligence & Macro Research Tool*

Berke Yıldırım's Dashboard is a professional-grade market research terminal built for high-density information analysis. It follows the "Bloomberg Lite" philosophy: pitch-black aesthetics, a 15-second real-time pulse, and educational context for every metric.

## 🚀 Key Features
- **15-Second Pulse**: Real-time price flashes and data refreshes without page reloads.
- **Universal Command Bar**: Powerful navigation via `@entity` commands, fuzzy search, and autocomplete.
- **Data Quality Overrides**: Force manual data points via `@entity set <value>` with persistent SQLite storage.
- **Digital Tutor**: Professional economic explanations for every registered metric to bridge the gap between "price" and "why".
- **Live Insight Layers**: Automated Z-Score analysis, Cross-asset divergence spotting, and 10Y Seasonality heatmaps.
- **Custom Intelligence**: Scrape any financial data from the web using simple commands.
- **Onboarding**: Check out the [USER_HANDBOOK.md](file:///home/berke/Desktop/Terminal Projesi/my_terminal/USER_HANDBOOK.md) for a guide to all features.
- **AI Analytics**: Integrated Terminal Assistant that synthesizes live news and market context using LLMs.

## 🏗️ Technical Architecture
- **Backend**: Python (Flask) with a modular engine architecture.
- **Frontend**: Vanilla JavaScript & CSS (No frameworks) for maximum performance and DOM control.
- **Data Engine**:
  - `yfinance` for global equities, FX, and commodities.
  - `TCMB EVDS` & `FRED` for macro indicators.
  - Custom scrapers for CDS and regional market data.
- **Persistence**: SQLite for manual overrides, data quality tickets, and market snapshots.

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Rename `.env.example` to `.env` and add your API keys:
- `EVDS_API_KEY`: Required for Turkish Macro data.
- `GROQ_API_KEY`: Required for the AI Terminal Assistant.

### 3. Launch the Dashboard
```bash
./start_desktop.sh
```
*Or manually:*
```bash
python app.py
```
Then navigate to `http://127.0.0.1:5000` in your browser.

## 📂 Project Structure
- `app.py`: Central Flask API router.
- `engine/`: Modular Python services (Market, Macro, Registry, Research, DB).
- `static/`: Frontend cockpit (HTML, CSS Variables, Functional JS).
- `project_bible.md`: The definitive, high-density documentation of every file and feature.


## 🧠 Mechanical Intelligence Features (New in v2.0)
The terminal now includes a "bloomberg-like" computed insight engine.

### How to Access
1. **Click the Command Bar** (or press `/`).
2. **Type an entity key** (e.g., `@usdtry`, `@tr_10y`, `@bist100`).
3. **Press Enter** to open the Entity Popup.

### What to Look For
- **INTELLIGENCE Section**: Appears automatically if insights are found.
    - **⚡ Divergence Alerts**: Warns of "Hidden Stress" (e.g., Price flat but Risk spking).
    - **⚠ Sigma Alerts**: Warns of statistical anomalies (>2σ moves).
- **VALUATION Box**:
    - Shows "Fair Value" vs "Current Price" based on financial models (PPP, Bond Spreads).
- **SEASONALITY Grid**:
    - Shows 10-year monthly return probabilities (e.g., "December: +2.4% Avg").
- **CORRELATION CHAIN**:
    - Shows how a move in one asset (e.g., Oil) impacts related assets (e.g., Airlines).

### 3. Dynamic Data Sources (Live Link)
Instead of manually updating a number, you can tell the terminal where to find it. The `SmartScraper` will visit the URL periodically and update the value automatically.

**Command:**
`@<key> source <url>`

**Example:**
*   `@cds source https://investing.com/rates-bonds/turkey-5-year-cds` (The system will hunt for the price on the page)

**Status:**
*   **S (Scrape)**: Data is coming from your custom URL.
*   **A (API)**: Data is coming from standard APIs (Yahoo/yfinance).
*   **M (Manual)**: Data is statically overridden by you.

---
*Created as a labor of professional market research. Version 2.0 Intelligent.*
