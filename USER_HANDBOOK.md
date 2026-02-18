# 📟 Berke Yıldırım's Terminal: User Handbook
*A guide to the most powerful (and complex) features of your personal Bloomberg Lite.*

Welcome to the cockpit. This terminal is no longer just a data viewer; it is an **Intelligence Engine**. This guide will help you master the "Mechanical Intelligence" layers we've added.

---

## 1. The Core Experience: Navigation
The terminal pulses every **15 seconds**. If a number flashes **Green**, it just went up. **Red**, it went down. 

### Essential Shortcuts:
- **`/` (Slash key)**: Jumps to the Command Bar.
- **Click any Row**: Opens the **Context Popup** for that asset.
- **`@entity vs @entity`**: Type this in the command bar to compare two things (e.g., `@usdtry vs @cds`).

---

## 2. Reading the "Intelligence" Layer
When you open an entity popup (like `@usdtry`), you'll see an **INTELLIGENCE** section. Here is how to read it:

### ⚠️ Sigma Alerts (The Anomaly Detector)
- **What it is:** A measure of how "weird" the current price move is based on the last 30 days.
- **0.0 - 1.5σ:** Normal market noise.
- **> 2.0σ:** **Warning**. Something unusual is happening.
- **> 3.0σ:** **Black Swan**. A massive outlier move. *Check the news immediately.*

### ⚖️ Fair Value & Gaps
- **Goal:** Tells you if the asset is "Cheap" or "Expensive" based on math.
- **Example (`@tr_10y`):** We calculate the "Fair" 10Y yield by adding the **US 10Y Yield + Turkey's CDS**. If the actual yield is much higher than this, the bond might be undervalued.

### ⚡ Divergence Warnings
- **The Concept:** When two related things stop moving together.
- **Example:** If `@usdtry` is flat but `@cds` is spiking, you'll see a **Yellow Lightning Bolt**. This means the Lira is under "Hidden Stress" that isn't showing in the price yet.

---

## 3. Advanced Features
### 📅 Seasonality (The Time Machine)
Found in major assets like `@usdtry` or `@bist100`. It shows a grid of **10 years of history**.
- **Avg Return:** What usually happens this month?
- **Win Rate:** Out of 10 years, how many times did it end the month profitable?
- *Tip: If it shows 90% Win Rate for February, historically, this is a strong month.*

### 🌐 Sentiment Analysis (The Retail Pulse)
We now monitor **Google Trends** for Turkey-specific keywords.
- **Panic Index:** High interest in "Dolar" and "Altın". High score = People are scared and moving to safety.
- **Greed Index:** High interest in "Borsa". High score = People are FOMO-ing into stocks.

### 📂 Trade & Macro (The Fundamental Truth)
- **Exports:** We scrape TİM's monthly Excel data as soon as it's published.
- **Banking:** We pull Loan data directly from the TCMB EVDS API.

---

## 4. Current Data Health (The "Why is it N/A?" List)
Some parts of the system are "Stalled" due to external blocks. We've built the system to stay stable (showing `N/A`) instead of crashing.

| Feature | Status | Reason |
| :--- | :--- | :--- |
| **Market Prices** | ✅ Perfect | Live via Yahoo Finance. |
| **Seasonality** | ✅ Perfect | 10Y historical depth. |
| **Exports** | ✅ Live | Monthly TİM Excel parsing. |
| **CDS Data** | 🟡 Scraped | Scraped from WorldGovBonds. Unstable. |
| **Hazine Auctions** | 🔴 Stalled | Website blocks automated access. |
| **EPIAŞ Energy** | 🔴 Stalled | Transparency Platform requires API keys. |

---

## 5. Tips for Master Use
1. **Combine Insights:** If you see a **Sigma Alert** (+3.0σ) AND a **Divergence Warning**, it's a high-conviction signal that the market is at a breaking point.
2. **Talk to the AI:** The chatbox knows everything mentioned above. Ask: *"What is the current Panic Index and why should I care?"*
3. **Manual Overrides:** If you know a number is wrong (e.g., CDS is actually 280), type `@cds set 280`. The terminal will remember this for you (marked with an **M** badge).

---
*This terminal is your edge. Use the math, trust the context.*
