# 📜 The Definitive Terminal Bible: Zero-Ambiguity Edition
*Berke Yıldırım's Dashboard — Architecture, Philosophy, and Chronicled History*

> **Instruction for Future AI Models**: This document is your primary source of truth. Rely on this to understand the "why" and "how" of every logic gate in the system. The terminal is a delicate balance of 15-second real-time pulses and professional financial pedagogy. **Do not break the pulse. Do not genericize the aesthetic.**

---

## I. PROJECT PHILOSOPHY: The "Bloomberg" Soul
We are NOT building a generic web dashboard. We are building a **Market Research Terminal**.

### 1. The Design Language
*   **High Density**: Information density is a feature, not a bug. Minimal whitespace. Every pixel must serve a financial purpose.
*   **Visual Precision**: 
    *   **Background**: Pitch black (`#0a0a0a`). Non-negotiable.
    *   **Colors**: Neon Green (`#00e676`) for "Up", Neon Red (`#ff1744`) for "Down", and Bloomberg Orange (`#ff9800`) for navigation/UI.
    *   **Typography**: `Roboto Mono`. Fixed-width ensures numeric columns line up perfectly, creating the "Excel/Bloomberg" look.
*   **Real-Time "Liveness"**: The dashboard must feel alive. Prices flash green/red on the 15-second heartbeat to simulate a live trading floor.

### 2. Pedagogy (The Digital Tutor)
The terminal's unique value is **Educational Context**. Data without meaning is noise. 
*   Every metric is linked to a professional explanation. 
*   The AI Assistant acts as a "Market Veteran", synthesizing news into macro narratives.

---

## II. SYSTEM ARCHITECTURE: The Three Pillars

### Pillar 1: The Pulse (Frontend - `static/`)
The frontend is a **Single Page Application (SPA)** written in Vanilla JavaScript.
*   **Heartbeat**: `setInterval(() => { ... }, 15000)` in `script.js`. Every 15s, it triggers 5-7 parallel fetches to different API endpoints.
*   **State Diffing**: Before updating the DOM, the JS compares the "Incoming Value" with the "Current Value". If different, it applies a CSS class (`flash-green`/`flash-red`) that triggers a temporary glow animation.
*   **Zero Framework**: We bypass React/Vue to avoid the "shadow DOM" overhead, allowing us to update hundreds of numeric nodes instantly on low-power hardware.

### Pillar 2: The Logic (Backend - `engine/`)
The backend is a **Modular Python Engine** hosted via Flask.
*   **Registry-First Logic**: Every entity (`@gold`, `@cds`) exists in `registry.py` with its metadata. The rest of the engine uses this registry to "know" how to fetch, unit-format, and explain each data point.
*   **Smart Caching**: `cache.py` provides a unified memory layer. Since the frontend pulses every 15s, the backend only hits external APIs (Yahoo Finance/EVDS) if the cache is older than the TTL.
*   **Scrapers & Proxies**: When official APIs fail (or don't exist), we use BeautifulSoup scrapers (e.g., `macro.py` for CDS data) to maintain uptime.

### Pillar 3: The Memory (Persistence - `engine/db.py`)
A lightweight **SQLite Database** acts as the system's long-term memory.
*   **Data Quality Tickets**: Users flag bad numbers; the system stamps them in DB with a full context snapshot.
*   **Manual Overrides**: The user can "force" a value. This override persists in the database even after a server restart.

---

## III. FILE-BY-FILE MISSION REGISTRY

### 📂 Root Directory
| File | Mission | Core Code Details |
| :--- | :--- | :--- |
| **`app.py`** | **The Grand Central Station** | Flask entry. Defines 20+ routes (`/api/market`, `/api/news`, etc.). Logic-lite; its only job is to import from `engine/` and return JSON. |
| **`config.json`** | **The Config Hub** | JSON file mapping EVDS codes and Yahoo symbols. If a data point breaks, change the code here. |
| **`requirements.txt`**| **Dependencies** | `yfinance` (market), `beautifulsoup4` (scraping), `feedparser` (news), `plotly` (charts). |
| **`start_desktop.sh`**| **One-Click Launch** | Automates: `venv activation` -> `python app.py` -> `open browser` in a dedicated app window. |

### 📂 `engine/` (The Brain)
| File | Mission | Core Code Details |
| :--- | :--- | :--- |
| **`registry.py`** | **The Source of Truth** | A massive dict of ~50 entities. Contains: `key`, `source`, `unit`, and `explain`. **Mandatory to update when adding metrics.** |
| **`market.py`** | **Market Data Factory** | Uses `yf.download(symbols)` in batches of 10 to avoid Yahoo rate limits. Calculates **Gram Altın** on the fly. |
| **`macro.py`** | **The Economic Engine** | Python logic for TR macro. Scrapes WorldGovBonds for CDS. Fetches EVDS. Calculates **Real Rate** and **Carry Trade**. |
| **`research.py`** | **AI Context Builder** | Injects current dashboard state into the LLM prompt. Ensures the AI knows exactly what the user is seeing in the News/Movers boxes. |
| **`db.py`** | **Persistence Layer** | Pure SQL queries. Manages `news`, `market_snapshots`, `data_tickets`, and `data_overrides` tables. |
| **`news.py`** | **Interleaved Scraper** | RSS feed parser. It interleaves news from Reuters, Investing.com, and Bloomberg to ensure a balanced feed. |
| **`scorecard.py`** | **Quant Risk Model** | Logic for the "Macro Scorecard". Weights Yield Curve, CDS, and Inflation to produce a Signal (Buy/Sell/Neutral). |
| **`cache.py`** | **TTL Manager** | A simple dict-based memory cache with expiration timestamps. Prevents API throttling. |
| **`knowledge.py`** | **Semantic Map** | Static JSON relationships used by the AI to explain link-chains (e.g., "Why does high inflation weaken the Lira?"). |
| **`analytics.py`** | **Math Library** | Core statistical functions (Z-Score, Percentiles, CAGR). Used by all other intelligence engines. |
| **`alerts.py`** | **Anomaly Engine** | Implements the **Sigma Scanner** and **Divergence Spotter**. Monitors for statistical outliers. |
| **`valuation.py`** | **Valuation Hub** | Calculates Fair Value and Price Gaps using sovereign and equity models. |
| **`graph.py`** | **Causal Engine** | Maps second-order impacts between entities (e.g., Oil -> USDTRY). |
| **`seasonality.py`** | **History Engine** | Analyzes 10Y monthly return patterns for any chartable asset. |
| **`resolver.py`** | **The Dispatcher** | Orchestrates all of the above. It takes a key, gathers alerts/valuation/seasonality details, and returns a unified bundle to `app.py`. |

### 📂 `static/` (The Interface)
| File | Mission | Core Code Details |
| :--- | :--- | :--- |
| **`index.html`** | **The Layout** | 3-Column Grid: Left (Instrument Panel), Center (Chart/Markets/News), Right (Movers/Calendar). |
| **`style.css`** | **Design System** | Defines CSS Variables for the whole app. Contains the `@keyframes` for the "Price Flash" animations. |
| **`script.js`** | **Frontend Logic** | The "Heavy Lifter". Handles Chart.js initialization, command parsing, autocomplete, and the 15s refresh loop. |

---

## IV. DATA FLOW & CORRELATION MAPPINGS

### How a Command is Processed:
1.  **User Input**: `Enter` in `#cmd-input` triggers `handleCommand(val)` in `script.js`.
2.  **JS Parsing**: Recognizes keywords like `set`, `graph`, `vs`.
3.  **API Call**: Calls `POST /api/entity/<key>/set`.
4.  **Backend (app.py)**: Routes to `set_override(key, val)` in `db.py`.
5.  **SQL Update**: `data_overrides` table is updated.
6.  **Refresh Loop**: Next `fetchMacro()` or `fetchMarket()` check `registryKey`.
7.  **UI Badge**: `sbRow()` in `script.js` sees the override and adds the **"M" badge**.

### How AI Chat Works:
1.  **Context Capture**: `sendChatMessage()` in `script.js` grabs the current `marketStore`, `newsData`, and `chartDataStore`.
2.  **API Send**: `POST /api/chat` sends user text + context bundle.
3.  **Prompt Engineering**: `research.py` wraps the context in a "System Prompt" that defines the AI as "Terminal Assistant".
4.  **Streaming**: Response returned to UI.

---

## V. THE CHRONICLE (Development Log)

### Epoch 1: Foundation (V1 - V10)
-   Built the Flask/JS bridge.
-   Integrated `yfinance` as the primary ticker source.
-   Established the dark theme and 3-column "Cockpit" layout.

### Epoch 2: Intelligence (V11 - V14)
-   **V11 Persistence**: Introduced SQLite for "Data Tickets" (quality tracking).
-   **V12 Global Awareness**: Added clock logic and market status for NY/Lon/Sha/Ist.
-   **V14 Performance**: Moved to a strict **15-second polling cycle** with visual "Price Flash" feedback.

### Epoch 3: The Command Tier (V15 - V17)
-   **V15 Branding**: Official name change to **"Berke Yıldırım's Dashboard"**.
-   **V16 Registry**: Moved from "hardcoded strings" to the `registry.py` system. Every data point now has a unique ID and educational explanation.
-   **V17 Pro Features**: 
    -   Universal Command Bar (`/` shortcut).
    -   Manual Overrides (Persistence + M Badges).
    -   Multi-Entity Comparison Engine (`@key vs @key`).

### Epoch 4: The Final Handover (V1.0 Official)
-   **Git Snapshot**: Primary code and documentation "frozen" into an official V1 local and cloud repository.
-   **Documentation Signature**: Final deep-dive "Ultimate Project Bible" created to ensure zero knowledge loss.
-   **Accuracy Check**: Removed legacy Streamlit artifacts and updated README for the production architecture.

---

## VI. CURRENT SYSTEM STATE: Handover Checklist

### 1. Known Dependencies
- **yfinance**: Rock solid, but prone to 1-2s latency. Always use batch fetches.
- **EVDS**: Registered for ~15 series. Currently transitioning more macro data from "scrape" to "official EVDS".
- **Groq AI**: Used for chat. System prompt expects `llama-3.3-70b`.

### 2. Critical "Do Not Touch" Rules
-   **Grid Widths**: Sidebars are fixed at 320px (Left) and 300px (Right). The center is fluid. Changing this will break the Chart.js responsive scaling.
-   **Flash Logic**: The green/red flash logic in `script.js` relies on `lastPrice` being an exact float. Do not string-format before the diff.
-   **Registry Sync**: The `key` in `registry.py` MUST match the key used in the API JSON responses for the `M` badges and `explain` functions to work.

### 3. Immediate Future Priorities
-   **Phase 2: Data Hunting**: Moving the remaining "Scraped" macro items to official TCMB EVDS series.
-   **BIST Movers Stability**: The BIST Movers list occasionally hits Yahoo's "empty dataframe" bug; it needs a robust fallback script.

---
*Generated by Antigravity (Google DeepMind) on 2026-02-15.*
*Authorized for use by all future Terminal AIs.*
