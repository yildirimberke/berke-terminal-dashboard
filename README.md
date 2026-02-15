# 📊 Berke Yıldırım's Dashboard — Professional Market Terminal
*High-Density Financial Intelligence & Macro Research Tool*

Berke Yıldırım's Dashboard is a professional-grade market research terminal built for high-density information analysis. It follows the "Bloomberg Lite" philosophy: pitch-black aesthetics, a 15-second real-time pulse, and educational context for every metric.

## 🚀 Key Features
- **15-Second Pulse**: Real-time price flashes and data refreshes without page reloads.
- **Universal Command Bar**: Powerful navigation via `@entity` commands, fuzzy search, and autocomplete.
- **Data Quality Overrides**: Force manual data points via `@entity set <value>` with persistent SQLite storage.
- **Digital Tutor**: Professional economic explanations for every registered metric to bridge the gap between "price" and "why".
- **Comparison Engine**: Side-by-side analysis via `@entityA vs @entityB`.
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

---
*Created as a labor of professional market research. Version 1.0 Stable.*
