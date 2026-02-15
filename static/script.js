/* =========================================================================
   Bloomberg Terminal Lite – Cockpit Logic v3
   Sidebar instrument panel + center workspace + right alerts
   ========================================================================= */
(function () {
    "use strict";

    const POLL_INTERVAL = 15000;

    // --- State ---
    let currentChartSymbol = "XU100.IS";
    let currentChartPeriod = "1mo";
    let currentNewsFilter = "all";
    let currentMoversTab = "gainers";
    let currentMoversIndex = "bist30";
    let newsData = [];
    let moversData = {};
    let chartDataStore = null; // Store latest historical data for AI

    // Global data stores (for sidebar cross-referencing)
    let macroStore = null;
    let turkeyMacroStore = null;
    let marketStore = null;
    let cbrtStore = null;
    let calendarStore = null;
    let erpStore = null;

    // Override system
    let overrideStore = {};  // { entity_key: { value, source, timestamp } }
    let overrideMode = false;

    // Debug
    let debugMode = false;
    let debugSelected = new Set();

    // -----------------------------------------------------------------------
    // ANNOTATIONS – educational context for each metric
    // -----------------------------------------------------------------------
    const ANN = {
        tr_funding_cost: "CBRT's main policy tool (1-week repo). Banks borrow at this rate. When it rises, all lending rates follow.",
        deposit_rate: "Average bank deposit rate. When real deposit rate (rate minus inflation) is positive, TRY savings become attractive.",
        lending_rate: "Average bank lending rate. Directly impacts corporate borrowing costs. The gap vs deposit rate = bank margin.",
        real_rate: "Nominal policy rate minus CPI YoY. THE most important number. Positive = genuinely tight policy. Negative = loose despite high nominal rate.",
        tr_2y_bond: "Short-term govt borrowing cost. Reflects market expectations for near-term rates and inflation over 2 years.",
        tr_10y_bond: "Long-term benchmark. Corporate loans priced as 10Y + credit spread. Key driver of bank profitability.",
        us_10y: "Global risk-free rate. When it rises, capital exits EM (incl. Turkey) seeking safer returns in the US.",
        spread: "Risk premium for holding Turkish debt vs US debt. Widens during crises. Key measure of Turkey's credit risk.",
        vix: "S&P 500 implied volatility. <20 calm, 20-30 anxious, 30+ fear. High VIX triggers EM capital outflows.",
        cpi: "Consumer Price Index YoY. CBRT's primary target. Drives every rate decision.",
        cpi_mom: "Month-over-month CPI. Annualize (×12) to get the run rate. Above 3% MoM = annual target likely missed.",
        core_cpi: "CPI ex food, energy, alcohol, tobacco, gold. The 'true' inflation CBRT watches for persistence.",
        ppi: "Producer Price Index YoY. Leading indicator — cost pressures pass through to CPI with 2-3 month lag.",
        food_inflation: "Food CPI. Highly volatile in Turkey. Can swing headline CPI significantly. Social stability metric.",
        gdp_yoy: "Annual GDP growth. Turkey's potential is ~4-5%. Above = overheating risk. Below = slack.",
        unemployment: "Labor market health. Turkey's structural rate is ~10%. Below that signals overheating.",
        current_account: "External balance (USD M). Deficit = Turkey needs foreign capital. Oil prices are the key driver.",
        fx_reserves: "CBRT's FX reserves (USD M). Defense capacity. Net reserves below $20B signals vulnerability.",
        m2: "Broad money supply. Rapid M2 growth signals future inflation. CBRT monitors alongside credit growth.",
        loans_private: "Total bank credit (TRY). Rapid loan growth = stimulus but risks inflation. CBRT uses macro-prudential tools.",
        biz_confidence: "Business confidence index. Above 100 = optimistic. Leading indicator for investment & hiring.",
        consumer_confidence: "Consumer sentiment. Below 100 = pessimistic. Affects spending. Recovers with falling inflation.",
        credit_rating: "Sovereign rating (Moody's/S&P/Fitch). Investment grade (Baa3+) = cheap foreign capital. Sub-IG = higher spreads.",
        interest_rate: "CBRT policy rate. Central tool for fighting inflation.",
        gram_altin: "Gold in TRY per gram. Popular Turkish savings vehicle. Calc: (Gold USD × USDTRY) / 31.1035.",
        usdtry: "The exchange rate. Drives import costs, inflation pass-through, and foreign debt burden in TRY terms.",
    };

    // -----------------------------------------------------------------------
    // Utility
    // -----------------------------------------------------------------------
    function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
    function chgCls(v) { if (v === "N/A" || v == null) return "na"; return parseFloat(v) >= 0 ? "up" : "down"; }
    function fmtChg(v) { if (v === "N/A" || v == null) return "N/A"; const n = parseFloat(v); return (n >= 0 ? "+" : "") + n.toFixed(2) + "%"; }
    function fmtPrice(v) {
        if (v === "N/A" || v == null) return "N/A";
        const n = parseFloat(v);
        if (Math.abs(n) >= 10000) return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (Math.abs(n) >= 1) return n.toFixed(2);
        return n.toFixed(4);
    }
    function timeNow() { return new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }); }

    function srcTag(src) {
        if (!src || src === "N/A") return "";
        const isScr = src.startsWith("SCRAPE");
        const isCal = src === "CALC" || src.includes("+CALC");
        const cls = isScr ? "src-tag src-scrape" : (isCal ? "src-tag src-calc" : "src-tag src-api");
        const label = isScr ? "S" : (isCal ? "C" : "A");
        return ` <span class="${cls}" title="${esc(src)}">${label}</span>`;
    }

    // Clock
    setInterval(() => { const el = document.getElementById("clock"); if (el) el.textContent = timeNow(); }, 1000);

    // -----------------------------------------------------------------------
    // SIDEBAR – The Instrument Panel
    // -----------------------------------------------------------------------
    function sbRow(label, value, source, annotation, extra) {
        const tip = annotation ? ` title="${esc(annotation)}"` : "";
        const tipCls = annotation ? " has-tip" : "";
        const st = srcTag(source);
        const hlCls = extra && extra.highlight ? " sb-highlight" : "";
        const valCls = extra && extra.valCls ? ` class="${extra.valCls}"` : "";
        const dbgAttr = debugMode ? ` data-debug-id="sb:${esc(label)}"` : "";
        const dbgCls = debugMode ? " debug-selectable" : "";
        const selCls = debugSelected.has("sb:" + label) ? " debug-selected" : "";
        const expAttr = extra && extra.key ? ` data-explain="${extra.key}"` : "";
        const expTag = extra && extra.key ? ` <span class="src-tag src-exp" title="Click for Digital Tutor">?</span>` : "";

        // Override M badge
        const entityKey = extra && extra.registryKey;
        const ovr = entityKey && overrideStore[entityKey];
        const ovrBadge = ovr ? ' <span class="override-badge" title="Manual Override: ' + esc(ovr.value) + '">M</span>' : '';
        const ovrCls = overrideMode && entityKey ? " ovr-editable" : "";
        const ovrAttr = entityKey ? ` data-registry-key="${entityKey}"` : "";

        return `<div class="sb-row${hlCls}${dbgCls}${selCls}${ovrCls}" style="position:relative"${dbgAttr}${expAttr}${ovrAttr}><span class="sb-label${tipCls}"${tip}>${esc(label)}${st}${expTag}</span><span class="sb-val"${valCls}>${value}${ovrBadge}</span></div>`;
    }

    function renderSidebar() {
        renderSbRates();
        renderSbBonds();
        renderSbInflation();
        renderSbEconomy();
        renderSbCbrt();
    }

    function renderSbRates() {
        const el = document.getElementById("sb-rates");
        if (!macroStore) { el.innerHTML = '<div class="sb-loading">Loading...</div>'; return; }
        const r = macroStore.policy_rates || {};
        let html = "";
        html += sbRow("CBRT AOFM", fmtPctSb(r.aofm), r.aofm_source, ANN.tr_funding_cost, { key: "aofm", registryKey: "policy_rate" });
        html += sbRow("Deposit Rate", fmtPctSb(r.deposit), r.deposit_source, ANN.deposit_rate, { key: "deposit_rate", registryKey: "deposit_rate" });
        html += sbRow("Comm. Loan", fmtPctSb(r.comm_loan), r.comm_loan_source, ANN.lending_rate, { key: "commercial_loan", registryKey: "com_loan" });

        // Real Rate = AOFM - CPI YoY
        if (turkeyMacroStore) {
            const cpiItem = tmFind("cpi");
            const aofm = parseFloat(String(r.aofm || "").replace(",", "."));
            const trDep = parseFloat(String(r.deposit || "").replace(",", "."));
            const cpi = cpiItem ? parseFloat(cpiItem.last) : NaN;

            if (!isNaN(aofm) && !isNaN(cpi)) {
                const real = (aofm - cpi).toFixed(1);
                const sign = parseFloat(real) >= 0 ? "+" : "";
                const cls = parseFloat(real) >= 0 ? "up" : "down";
                html += sbRow("Real Rate", `<span class="${cls}">${sign}${real}%</span>`, "CALC", ANN.real_rate, { highlight: true, key: "real_rate", registryKey: "real_rate" });
            }

            // Real Carry = (TR Dep - TR CPI) - (US Fed - US CPI)
            const b = macroStore.bonds || {};
            const fed = b.fed_funds;
            const usCpi = b.us_cpi;

            if (!isNaN(trDep) && !isNaN(cpi) && fed != null && usCpi != null && fed !== "N/A" && usCpi !== "N/A") {
                const trReal = trDep - cpi;
                const usReal = fed - usCpi;
                const carry = (trReal - usReal).toFixed(1);
                const sign = parseFloat(carry) >= 0 ? "+" : "";
                const cls = parseFloat(carry) >= 0 ? "up" : "down";
                const ann = "Difference between Turkey's Real Deposit Rate vs US Real Federal Funds Rate. Positive = Lira attractive.";
                html += sbRow("Real Carry", `<span class="${cls}">${sign}${carry}%</span>`, "CALC", ann, { highlight: true, key: "real_carry", registryKey: "real_carry" });
            }
        }
        el.innerHTML = html;
        if (debugMode) attachDebug(el);
    }

    function renderSbBonds() {
        const el = document.getElementById("sb-bonds");
        if (!macroStore) { el.innerHTML = '<div class="sb-loading">Loading...</div>'; return; }
        const b = macroStore.bonds || {};
        const x = macroStore.extras || {};
        const c = macroStore.cds || {};

        let html =
            sbRow("TR 2Y", fmtPctSb(b.tr_2y), b.tr_2y_source, ANN.tr_2y_bond, { key: "TR_2Y", registryKey: "tr_2y" }) +
            sbRow("TR 10Y", fmtPctSb(b.tr_10y), b.tr_10y_source, ANN.tr_10y_bond, { key: "TR_10Y", registryKey: "tr_10y" }) +
            sbRow("US 10Y", fmtPctSb(b.us_10y), b.us_10y_source, ANN.us_10y, { key: "US_10Y", registryKey: "us_10y" }) +
            sbRow("Risk Prem.", b.spread != null && b.spread !== "N/A" ? (b.spread * 100).toFixed(0) + " bps" : "N/A", "CALC", ANN.spread, { key: "Spread", registryKey: "risk_premium" }) +
            sbRow("TR Curve", b.tr_yield_curve != null && b.tr_yield_curve !== "N/A" ? (b.tr_yield_curve * 100).toFixed(0) + " bps" : "N/A", "CALC", "Turkey Yield Curve Slope (10Y - 2Y). Negative = Inverted (Recession/Tightness signal).", { key: "TR_Curve", highlight: true, registryKey: "tr_curve" });

        // Add CDS
        html += sbRow("CDS 5Y", c.val != null && c.val !== "N/A" ? c.val.toFixed(0) + " bps" : "N/A", c.source, "Turkey 5-Year Credit Default Swap (USD)", { key: "CDS", registryKey: "cds" });

        html += sbRow("VIX", x.vix !== "N/A" && x.vix != null ? parseFloat(x.vix).toFixed(1) : "N/A", x.vix_source, ANN.vix, { key: "VIX" });

        // Add Equity Risk Premium
        if (erpStore) {
            const pe = erpStore.pe;
            const ey = erpStore.earnings_yield;
            const erp = erpStore.erp;

            if (ey !== "N/A") {
                html += sbRow("Earn. Yield", ey + "%", "CALC", "BIST 100 Earnings Yield (1 / PE Ratio). Theoretical return of owning the index.", { key: "Earnings_Yield", registryKey: "pe" });
            }
            if (erp !== "N/A") {
                const cls = parseFloat(erp) > 0 ? "up" : "down";
                const sign = parseFloat(erp) > 0 ? "+" : "";
                html += sbRow("ERP", `<span class="${cls}">${sign}${erp}%</span>`, "CALC", "Equity Risk Premium (Earnings Yield - 10Y Bond Yield). excess return for holding stocks over bonds.", { key: "ERP", highlight: true, registryKey: "erp" });
            }
        }

        el.innerHTML = html;
        if (debugMode) attachDebug(el);
    }

    function renderSbInflation() {
        const el = document.getElementById("sb-inflation");
        if (!turkeyMacroStore) { el.innerHTML = '<div class="sb-loading">Loading...</div>'; return; }
        const items = [
            ["CPI YoY", "cpi", ANN.cpi],
            ["CPI MoM", "cpi_mom", ANN.cpi_mom],
            ["Core CPI", "core_cpi", ANN.core_cpi],
            ["PPI YoY", "ppi", ANN.ppi],
            ["PPI-CPI Gap", "ppi_cpi_gap", "Producer vs Consumer Inflation Spread. Positive = Producers absorbing costs (Margin Squeeze)."],
            ["Food CPI", "food_inflation", ANN.food_inflation],
        ];
        const regKeyMap = { cpi: "cpi_yoy", cpi_mom: "cpi_mom", core_cpi: "core_cpi", ppi: "ppi_yoy", ppi_cpi_gap: "ppi_cpi_gap", food_inflation: "food_cpi" };
        el.innerHTML = items.map(([label, key, ann]) => {
            const item = tmFind(key);
            const val = item ? item.last + "%" : "N/A";
            const src = item ? item._source : null;
            return sbRow(label, val, src, ann, { key: key, registryKey: regKeyMap[key] || key });
        }).join("");
        if (debugMode) attachDebug(el);
    }

    function renderSbEconomy() {
        const el = document.getElementById("sb-economy");
        if (!turkeyMacroStore) { el.innerHTML = '<div class="sb-loading">Loading...</div>'; return; }

        function row(label, key, ann, fmt, registryKey) {
            const item = tmFind(key);
            if (!item || item.last === "N/A" || item.last === "") return sbRow(label, "N/A", null, ann);
            let val = item.last;
            if (fmt === "pct") val = val + "%";
            else if (fmt === "musd") {
                const n = parseFloat(String(val).replace(",", "."));
                val = isNaN(n) ? val : n.toLocaleString("en-US", { maximumFractionDigits: 0 }) + " M$";
            } else if (fmt === "idx") {
                const n = parseFloat(String(val).replace(",", "."));
                val = isNaN(n) ? val : parseFloat(n.toFixed(1)).toString();
            }
            return sbRow(label, val, item._source, ann, { key: key, registryKey: registryKey || key });
        }

        el.innerHTML =
            row("GDP Growth", "gdp_yoy", ANN.gdp_yoy, "pct", "gdp") +
            row("Unemployment", "unemployment", ANN.unemployment, "pct", "unemployment") +
            row("Current Account", "current_account", ANN.current_account, "musd", "current_account") +
            row("FX Reserves", "fx_reserves", ANN.fx_reserves, "musd", "fx_reserves") +
            row("M2 Supply", "m2", ANN.m2, null, "m2") +
            row("Total Credit", "loans_private", ANN.loans_private, null, "total_credit") +
            row("Biz Confidence", "biz_confidence", ANN.biz_confidence, "idx", "biz_confidence") +
            row("Consumer Conf.", "consumer_confidence", ANN.consumer_confidence, "idx", "consumer_confidence") +
            row("Rating", "credit_rating", ANN.credit_rating, null, "credit_rating");
        if (debugMode) attachDebug(el);

        // Distressed container hook
        const rightBar = document.getElementById("sidebar-right");
        if (rightBar && !document.getElementById("sb-distressed-container")) {
            const container = document.createElement("div");
            container.id = "sb-distressed-container";
            container.className = "sb-section";
            container.innerHTML = `<div class="sb-header" style="color:#ff1744">DISTRESSED (>20% Drop)</div><div id="sb-distressed-list"></div>`;
            rightBar.appendChild(container);
        }
    }

    function renderSbDistressed(data) {
        const list = document.getElementById("sb-distressed-list");
        if (!list) return;

        if (!data || data.length === 0) {
            list.innerHTML = `<div class="sb-row text-muted">None found</div>`;
            return;
        }

        let html = "";
        data.slice(0, 5).forEach(d => {
            html += sbRow(d.symbol, `<span class="down">${d.drawdown}</span>`, "CALC", `Down ${d.drawdown} from 3-month high (${d.high_3mo}). Price: ${d.price}`, { key: "Dist_" + d.symbol });
        });
        list.style.display = "block";
        list.innerHTML = html;
    }

    function renderSbGoldCorr(data) {
        // Create container if not exists
        const rightBar = document.getElementById("sidebar-right");
        if (rightBar && !document.getElementById("sb-gold-corr-container")) {
            const container = document.createElement("div");
            container.id = "sb-gold-corr-container";
            container.className = "sb-section";
            container.innerHTML = `<div class="sb-header" style="color:#ffd700">GOLD CORRELATION (3mo)</div><div id="sb-gold-corr-list"></div>`;
            const dist = document.getElementById("sb-distressed-container");
            if (dist) rightBar.insertBefore(container, dist);
            else rightBar.appendChild(container);
        }

        const list = document.getElementById("sb-gold-corr-list");
        if (!list || !data || !data.corr_usd) return;

        let html = "";
        const u = data.corr_usd;
        const g = data.corr_gold;

        const clsU = u > 0.8 ? "up" : u < -0.8 ? "down" : "";
        const clsG = g > 0.8 ? "up" : g < -0.8 ? "down" : "";

        html += sbRow("vs USDTRY", `<span class="${clsU}">${u}</span>`, "CALC", "Correlation(Gram Gold, USDTRY). If High, Gram Gold is a currency hedge.");
        html += sbRow("vs XAUUSD", `<span class="${clsG}">${g}</span>`, "CALC", "Correlation(Gram Gold, Global Gold). If High, Gram Gold is a commodity play.");

        list.style.display = "block";
        list.innerHTML = html;
    }

    function renderSbCbrt() {
        const el = document.getElementById("sb-cbrt");
        let html = "";

        if (cbrtStore) {
            html += sbRow("Policy Rate", cbrtStore.current_rate != null ? cbrtStore.current_rate + "%" : "N/A", "EVDS", ANN.interest_rate, { key: "interest_rate" });
            if (cbrtStore.next_meeting) {
                const days = Math.ceil((new Date(cbrtStore.next_meeting) - new Date()) / 86400000);
                const dLabel = days === 0 ? "TODAY" : days === 1 ? "TOMORROW" : days + "d";
                html += sbRow("Next MPC", `${cbrtStore.next_meeting} <span class="sb-countdown">${dLabel}</span>`, null, "Next Monetary Policy Committee decision date.");
            }
        }

        if (macroStore && macroStore.extras) {
            const ga = macroStore.extras.gram_altin;
            if (ga && ga !== "N/A") {
                html += sbRow("Gram Altin", parseFloat(ga).toLocaleString("tr-TR", { maximumFractionDigits: 0 }) + " ₺", macroStore.extras.gram_altin_source, ANN.gram_altin, { key: "gram_altin" });
            }
        }

        if (marketStore) {
            const usdtry = marketStore["USDTRY=X"];
            if (usdtry && usdtry.price !== "N/A") {
                const cls = chgCls(usdtry.change_pct);
                html += sbRow("USD/TRY", `${fmtPrice(usdtry.price)} <span class="${cls}" style="font-size:9px">${fmtChg(usdtry.change_pct)}</span>`, usdtry._source, ANN.usdtry, { key: "usdtry" });
            }
        }

        el.innerHTML = html || '<div class="sb-loading">Loading...</div>';
        if (debugMode) attachDebug(el);
    }

    function tmFind(key) {
        if (!turkeyMacroStore) return null;
        return turkeyMacroStore.find(i => i.key === key) || null;
    }

    function fmtPctSb(val) {
        if (val === "N/A" || val == null) return '<span class="na">N/A</span>';
        const n = parseFloat(String(val).replace(",", "."));
        return isNaN(n) ? esc(String(val)) : n.toFixed(2) + "%";
    }

    // -----------------------------------------------------------------------
    // UPCOMING EVENTS (right sidebar compact calendar)
    // -----------------------------------------------------------------------
    function renderUpcoming() {
        const el = document.getElementById("upcoming-body");
        if (!calendarStore || !calendarStore.length) {
            el.innerHTML = '<div class="loading">Loading</div>';
            return;
        }
        const today = new Date().toISOString().slice(0, 10);
        const upcoming = calendarStore.filter(e => e.date >= today).slice(0, 7);
        if (!upcoming.length) { el.innerHTML = '<div class="na" style="padding:6px;text-align:center">No upcoming events</div>'; return; }

        el.innerHTML = upcoming.map(e => {
            const d = new Date(e.date);
            const dayStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
            const daysAway = Math.ceil((d - new Date(today)) / 86400000);
            const daysLabel = daysAway === 0 ? '<span style="color:var(--orange);font-weight:700">TODAY</span>' : (daysAway === 1 ? "tmrw" : daysAway + "d");
            const ccls = "country-" + e.country;
            const icls = e.importance === "high" ? "importance-high" : (e.importance === "medium" ? "importance-medium" : "importance-low");
            const dots = e.importance === "high" ? "●●●" : (e.importance === "medium" ? "●●" : "●");
            return `<div class="upcoming-row"><span class="upcoming-date">${dayStr}</span><span class="upcoming-country ${ccls}">${esc(e.country)}</span><span class="upcoming-event">${esc(e.event)}</span><span class="upcoming-imp ${icls}">${dots}</span><span class="upcoming-days">${daysLabel}</span></div>`;
        }).join("");
    }

    // -----------------------------------------------------------------------
    // DAILY BRIEF
    // -----------------------------------------------------------------------
    async function fetchBrief() {
        try {
            const r = await fetch("/api/brief");
            const j = await r.json();
            const el = document.getElementById("brief-content");
            if (!j || !j.lines || !j.lines.length) { el.innerHTML = '<span class="brief-loading">Brief unavailable</span>'; return; }
            el.innerHTML = j.lines.map(([l, t]) => `<span class="brief-line"><span class="brief-label">${esc(l)}</span><span class="brief-text">${esc(t)}</span></span>`).join("");
        } catch (e) { console.error("Brief:", e); }
    }

    // -----------------------------------------------------------------------
    // MARKET DATA
    // -----------------------------------------------------------------------
    async function fetchMarket() {
        try {
            const r = await fetch("/api/market");
            const j = await r.json();
            marketStore = j.data || {};
            renderTickerTape(j);
            renderMarketTabs(j);
            renderStatus(j.status);
            renderSbCbrt(); // update USD/TRY in sidebar
            document.getElementById("last-update").textContent = timeNow();
        } catch (e) { console.error("Market:", e); }
    }

    function renderStatus(s) {
        if (!s) return;
        // s structure: {ist: {label, status, time, is_open}, ny:..., ln:..., sh:...}

        const makeBadge = (key) => {
            const d = s[key];
            if (!d) return "";
            const colorClass = d.is_open ? "open" : "closed";
            return `<span class="status-group"><span class="status-dot ${colorClass}"></span><span class="status-text">${d.label} ${d.time}</span></span>`;
        };

        const html = `
            ${makeBadge("ist")}
            <span class="status-sep">|</span>
            ${makeBadge("ny")}
            <span class="status-sep">|</span>
            ${makeBadge("ln")}
            <span class="status-sep">|</span>
            ${makeBadge("sh")}
        `;

        document.getElementById("market-status").innerHTML = html;
    }

    function renderTickerTape(j) {
        const track = document.getElementById("ticker-track");
        const order = j.ticker_tape || [];
        const data = j.data || {};
        const names = j.names || {};
        let html = "";
        for (const sym of order) {
            const d = data[sym];
            if (!d) continue;
            html += `<span class="ticker-item"><span class="ticker-name">${esc(names[sym] || sym)}</span><span class="ticker-price">${fmtPrice(d.price)}</span><span class="${chgCls(d.change_pct)}">${fmtChg(d.change_pct)}</span></span>`;
        }
        track.innerHTML = html + html;
    }


    let lastPrices = {}; // {symbol: price_float}

    // ... (rest of the file until renderMarketTabs)

    function renderMarketTabs(j) {
        const cats = j.categories || {};
        const data = j.data || {};
        const newPrices = {};

        for (const [cat, symbols] of Object.entries(cats)) {
            const c = document.getElementById("tab-" + cat);
            if (!c) continue;

            // Check if table needs full rebuild (initial load)
            const tableExists = c.querySelector("table");
            if (!tableExists) {
                // Initial Build
                let rows = "";
                for (const sym of symbols) {
                    const d = data[sym];
                    if (!d) continue;
                    newPrices[sym] = d.price;
                    const cls = chgCls(d.change_pct);
                    const st = srcTag(d._source);
                    rows += `<tr id="row-${sym}" data-sym="${sym}"><td class="sym">${esc(d.name || sym)}${st}</td><td class="price text-right">${fmtPrice(d.price)}</td><td class="text-right">${fmtPrice(d.prev_close)}</td><td class="change text-right ${cls}">${fmtChg(d.change_pct)}</td></tr>`;
                }
                c.innerHTML = `<table class="market-table"><colgroup><col class="col-sym"><col class="col-price"><col class="col-prev"><col class="col-change"></colgroup><thead><tr><th>Symbol</th><th>Price</th><th>Prev</th><th>Chg%</th></tr></thead><tbody>${rows}</tbody></table>`;
                if (debugMode) attachDebug(c);
            } else {
                // Update Existing Rows
                for (const sym of symbols) {
                    const d = data[sym];
                    if (!d) continue;
                    newPrices[sym] = d.price;

                    const row = document.getElementById(`row-${sym}`);
                    if (row) {
                        const cellPrice = row.querySelector(".price");
                        const cellChange = row.querySelector(".change");

                        // Diffing
                        const oldPrice = lastPrices[sym];
                        if (oldPrice !== undefined && d.price !== oldPrice) {
                            // Flash
                            const flashClass = d.price > oldPrice ? "flash-up" : "flash-down";
                            if (cellPrice) {
                                cellPrice.textContent = fmtPrice(d.price);
                                cellPrice.classList.remove("flash-up", "flash-down");
                                void cellPrice.offsetWidth; // Trigger reflow
                                cellPrice.classList.add(flashClass);
                            }
                        } else {
                            // Just update text if no flash needed (or first load after rebuild)
                            if (cellPrice && cellPrice.textContent !== fmtPrice(d.price)) {
                                cellPrice.textContent = fmtPrice(d.price);
                            }
                        }

                        if (cellChange) {
                            cellChange.className = `change text-right ${chgCls(d.change_pct)}`;
                            cellChange.textContent = fmtChg(d.change_pct);
                        }
                    }
                }
            }
        }
        lastPrices = newPrices;
    }

    // -----------------------------------------------------------------------
    // MACRO DATA (feeds sidebar)
    // -----------------------------------------------------------------------
    async function fetchMacro() {
        try {
            const r = await fetch("/api/macro");
            macroStore = await r.json();
            renderSbRates();
            renderSbBonds();
            renderSbCbrt();
        } catch (e) { console.error("Macro:", e); }
    }

    // -----------------------------------------------------------------------
    // TURKEY MACRO (feeds sidebar + center tab)
    // -----------------------------------------------------------------------
    async function fetchTurkeyMacro() {
        try {
            const r = await fetch("/api/turkey-macro");
            turkeyMacroStore = await r.json();
            renderSbRates();  // for real rate calc
            renderSbInflation();
            renderSbEconomy();
            renderTurkeyMacroTab();
        } catch (e) { console.error("TurkeyMacro:", e); }
    }

    function renderTurkeyMacroTab() {
        const c = document.getElementById("tab-turkey-macro");
        if (!turkeyMacroStore || !turkeyMacroStore.length) { c.innerHTML = '<div class="loading">No data</div>'; return; }
        let rows = "";
        for (const item of turkeyMacroStore) {
            const ann = ANN[item.key] || "";
            const tip = ann ? ` title="${esc(ann)}"` : "";
            const nc = ann ? "indicator-name" : "";
            const st = srcTag(item._source);
            const dbA = debugMode ? ` data-debug-id="tm:${item.key}"` : "";
            const dbC = debugMode ? " debug-selectable" : "";
            const sel = debugSelected.has("tm:" + item.key) ? " debug-selected" : "";
            const expAttr = ` data-explain="${item.key}"`;
            rows += `<tr class="${dbC}${sel}"${dbA}${expAttr}><td class="${nc}"${tip}>${esc(item.name)}${st}</td><td class="last-val" style="font-weight:600">${esc(item.last)}</td><td>${esc(item.previous)}</td><td style="color:var(--text-muted);font-size:10px">${esc(item.unit)}</td><td style="color:var(--text-muted);font-size:10px">${esc(item.date)}</td></tr>`;
        }
        c.innerHTML = `<table class="macro-table"><colgroup><col class="col-name"><col class="col-last"><col class="col-prev"><col class="col-unit"><col class="col-date"></colgroup><thead><tr><th>Indicator</th><th>Last</th><th>Previous</th><th>Unit</th><th>Date</th></tr></thead><tbody>${rows}</tbody></table>`;
        if (debugMode) attachDebug(c);
    }

    // -----------------------------------------------------------------------
    // CBRT TRACKER (feeds sidebar + center tab)
    // -----------------------------------------------------------------------
    async function fetchCBRT() {
        try {
            const r = await fetch("/api/cbrt");
            cbrtStore = await r.json();
            renderSbCbrt();
            renderCBRTTab();
        } catch (e) { console.error("CBRT:", e); }
    }

    function renderCBRTTab() {
        const c = document.getElementById("tab-cbrt");
        if (!cbrtStore) { c.innerHTML = '<div class="loading">Loading</div>'; return; }
        const cur = cbrtStore.current_rate || "N/A";
        const prev = cbrtStore.previous_rate || "N/A";
        const lc = cbrtStore.last_change_date || "N/A";
        const nm = cbrtStore.next_meeting || "TBD";
        const hist = cbrtStore.history || [];

        let chDir = "N/A";
        if (cur !== "N/A" && prev !== "N/A") {
            const d = cur - prev;
            chDir = d > 0 ? `+${d.toFixed(0)} bps (hike)` : `${d.toFixed(0)} bps (cut)`;
        }

        let html = `<div class="cbrt-summary">`;
        html += `<div class="cbrt-stat" data-explain="interest_rate"><div class="stat-label">Current Rate</div><div class="stat-value">${cur}%</div><div class="stat-sub">1-Week Repo</div></div>`;
        html += `<div class="cbrt-stat"><div class="stat-label">Last Change</div><div class="stat-value">${esc(chDir)}</div><div class="stat-sub">${esc(lc)}</div></div>`;
        html += `<div class="cbrt-stat"><div class="stat-label">Next Meeting</div><div class="stat-value" style="font-size:13px">${esc(nm)}</div><div class="stat-sub">MPC Decision</div></div>`;
        html += `</div>`;

        if (hist.length) {
            const mx = Math.max(...hist.map(h => h.rate));
            html += `<div class="cbrt-timeline"><div class="cbrt-timeline-title">Rate Decision History</div>`;
            for (const h of hist.slice(-16)) {
                const pct = mx > 0 ? (h.rate / mx) * 100 : 0;
                html += `<div class="cbrt-timeline-row"><span class="cbrt-timeline-date">${esc(h.date)}</span><span class="cbrt-timeline-rate">${h.rate}%</span><div class="cbrt-timeline-bar"><div class="cbrt-timeline-fill" style="width:${pct}%"></div></div></div>`;
            }
            html += `</div>`;
        }
        c.innerHTML = html;
    }

    // -----------------------------------------------------------------------
    // ECONOMIC CALENDAR (feeds upcoming + center tab)
    // -----------------------------------------------------------------------
    async function fetchCalendar() {
        try {
            const r = await fetch("/api/calendar");
            calendarStore = await r.json();
            renderUpcoming();
            renderCalendarTab();
        } catch (e) { console.error("Calendar:", e); }
    }

    function renderCalendarTab() {
        const c = document.getElementById("tab-calendar");
        if (!calendarStore || !calendarStore.length) { c.innerHTML = '<div class="loading">No events</div>'; return; }
        const today = new Date().toISOString().slice(0, 10);
        let rows = "";
        for (const e of calendarStore) {
            const isT = e.date === today ? " cal-today" : "";
            const iCls = e.importance === "high" ? "importance-high" : (e.importance === "medium" ? "importance-medium" : "importance-low");
            const cCls = "country-" + e.country;
            const dots = e.importance === "high" ? "●●●" : (e.importance === "medium" ? "●●" : "●");
            const da = Math.ceil((new Date(e.date) - new Date(today)) / 86400000);
            const dl = da === 0 ? "TODAY" : (da === 1 ? "Tmrw" : da + "d");
            rows += `<tr class="${isT}"><td class="cal-date">${esc(e.date)}</td><td style="font-size:10px;color:var(--text-muted)">${esc(dl)}</td><td class="cal-country ${cCls}">${esc(e.country)}</td><td>${esc(e.event)}</td><td class="${iCls}" style="text-align:center">${dots}</td></tr>`;
        }
        c.innerHTML = `<table class="calendar-table"><thead><tr><th>Date</th><th></th><th></th><th>Event</th><th></th></tr></thead><tbody>${rows}</tbody></table>`;
    }

    // -----------------------------------------------------------------------
    // MOVERS
    // -----------------------------------------------------------------------
    async function fetchMovers() {
        try {
            const r = await fetch("/api/movers");
            moversData = await r.json();
            renderMovers();
        } catch (e) { console.error("Movers:", e); }
    }

    function renderMovers() {
        const body = document.getElementById("movers-body");
        const idx = moversData[currentMoversIndex] || {};
        const items = idx[currentMoversTab] || [];
        const src = moversData._source || "N/A";
        if (!items.length) { body.innerHTML = '<div class="na" style="padding:6px;text-align:center">No data</div>'; return; }
        const hasVol = currentMoversTab === "most_traded";
        const st = srcTag(src);
        let rows = "";
        for (const item of items) {
            const cls = chgCls(item.change);
            rows += `<tr><td class="sym">${esc(item.symbol)}${st}</td><td class="price text-right">${esc(item.price)}</td><td class="change text-right ${cls}">${esc(item.change)}%</td>`;
            if (hasVol && item.volume) rows += `<td class="text-right" style="font-size:9px;color:var(--text-muted)">${esc(item.volume)}</td>`;
            rows += `</tr>`;
        }
        body.innerHTML = `<table class="movers-table"><tbody>${rows}</tbody></table>`;
    }

    // Movers controls
    document.querySelectorAll(".mi-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".mi-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentMoversIndex = btn.dataset.moversIndex;
            renderMovers();
        });
    });
    document.querySelectorAll(".mt-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".mt-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentMoversTab = btn.dataset.moversTab;
            renderMovers();
        });
    });

    // -----------------------------------------------------------------------
    // NEWS
    // -----------------------------------------------------------------------
    async function fetchNews() {
        try {
            const r = await fetch("/api/news");
            newsData = await r.json();
            buildNewsFilters();
            renderNews();
        } catch (e) { console.error("News:", e); }
    }

    function buildNewsFilters() {
        const bar = document.getElementById("news-filter-bar");
        const sources = [...new Set(newsData.map(n => n.source))];
        let html = `<button class="news-filter-btn ${currentNewsFilter === 'all' ? 'active' : ''}" data-source="all">All</button>`;
        for (const s of sources) {
            html += `<button class="news-filter-btn ${currentNewsFilter === s ? 'active' : ''}" data-source="${esc(s)}">${esc(s)}</button>`;
        }
        bar.innerHTML = html;
        bar.querySelectorAll(".news-filter-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                currentNewsFilter = btn.dataset.source;
                bar.querySelectorAll(".news-filter-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                renderNews();
            });
        });
    }

    function renderNews() {
        const body = document.getElementById("news-body");
        let filtered = currentNewsFilter === "all" ? newsData : newsData.filter(n => n.source === currentNewsFilter);
        if (!filtered.length) { body.innerHTML = '<div class="loading">No news</div>'; return; }
        body.innerHTML = filtered.slice(0, 40).map(item =>
            `<div class="news-item"><div class="news-source">${esc(item.source)}</div><a class="news-title" href="${esc(item.link)}" target="_blank" rel="noopener">${esc(item.title)}</a>` +
            (item.summary ? `<div class="news-summary">${esc(item.summary)}</div>` : "") +
            (item.published ? `<div class="news-time">${esc(item.published)}</div>` : "") +
            `</div>`
        ).join("");
    }

    // -----------------------------------------------------------------------
    // CHART
    // -----------------------------------------------------------------------
    async function loadSymbols() {
        try {
            const r = await fetch("/api/symbols");
            const syms = await r.json();
            const sel = document.getElementById("chart-symbol");
            sel.innerHTML = syms.map(s => `<option value="${s.symbol}">${s.name} (${s.symbol})</option>`).join("");
            sel.value = currentChartSymbol;
        } catch (e) { console.error("Symbols:", e); }
    }

    async function fetchChart() {
        const c = document.getElementById("chart-container");
        try {
            const r = await fetch(`/api/history?symbol=${encodeURIComponent(currentChartSymbol)}&period=${currentChartPeriod}`);
            if (!r.ok) { c.innerHTML = '<div class="loading">No chart data</div>'; return; }
            const j = await r.json();
            chartDataStore = {
                symbol: currentChartSymbol,
                period: currentChartPeriod,
                data: j.data.slice(-100) // Keep last 100 points for context
            };
            renderChart(j.data);
        } catch (e) { c.innerHTML = '<div class="loading">Chart error</div>'; }
    }

    function renderChart(data) {
        if (!data || !data.length) return;
        const dates = data.map(d => new Date(d.time * 1000));
        const closes = data.map(d => d.close);
        const highs = data.map(d => d.high);
        const lows = data.map(d => d.low);
        const isUp = closes[closes.length - 1] >= closes[0];
        const lc = isUp ? "#00e676" : "#ff1744";
        const fc = isUp ? "rgba(0,230,118,0.07)" : "rgba(255,23,68,0.07)";
        const mn = Math.min(...lows), mx = Math.max(...highs);
        const rng = mx - mn;
        const pad = rng * 0.08 || mx * 0.01;
        const yMin = mn - pad, yMax = mx + pad;

        Plotly.newPlot("chart-container", [
            { x: dates, y: Array(dates.length).fill(yMin), type: "scatter", mode: "lines", line: { color: "transparent", width: 0 }, showlegend: false, hoverinfo: "skip" },
            { x: dates, y: closes, type: "scatter", mode: "lines", line: { color: lc, width: 1.5 }, fill: "tonexty", fillcolor: fc, showlegend: false, hovertemplate: "%{x}<br>%{y:.2f}<extra></extra>" },
        ], {
            paper_bgcolor: "#111", plot_bgcolor: "#111",
            margin: { l: 45, r: 10, t: 6, b: 24 },
            xaxis: { color: "#444", gridcolor: "#1a1a1a", tickfont: { family: "Roboto Mono", size: 8, color: "#444" } },
            yaxis: { color: "#444", gridcolor: "#1a1a1a", tickfont: { family: "Roboto Mono", size: 8, color: "#444" }, side: "right", range: [yMin, yMax], tickformat: mx > 1000 ? ",.0f" : ".2f" },
            hovermode: "x unified",
            hoverlabel: { bgcolor: "#1a1a1a", bordercolor: "#333", font: { family: "Roboto Mono", size: 9, color: "#d4d4d4" } },
        }, { displayModeBar: false, responsive: true });
    }

    document.getElementById("chart-symbol").addEventListener("change", function () {
        currentChartSymbol = this.value;
        fetchChart();
    });
    document.querySelectorAll(".period-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".period-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentChartPeriod = btn.dataset.period;
            fetchChart();
        });
    });

    // -----------------------------------------------------------------------
    // TAB SWITCHING
    // -----------------------------------------------------------------------
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const tab = btn.dataset.tab;
            const bar = btn.closest(".tab-bar");
            bar.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const body = document.getElementById("markets-body");
            if (body) {
                body.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
                const t = body.querySelector("#tab-" + tab);
                if (t) t.classList.add("active");
            }
        });
    });

    // -----------------------------------------------------------------------
    // DEBUG MODE
    // -----------------------------------------------------------------------
    function attachDebug(container) {
        container.querySelectorAll(".debug-selectable").forEach(el => {
            el.addEventListener("click", () => {
                const id = el.dataset.debugId;
                if (!id) return;
                if (debugSelected.has(id)) { debugSelected.delete(id); el.classList.remove("debug-selected"); }
                else { debugSelected.add(id); el.classList.add("debug-selected"); }
                updateDebugPanel();
            });
        });
    }

    function updateDebugPanel() {
        const panel = document.getElementById("debug-panel");
        const cnt = panel.querySelector(".debug-count");
        if (cnt) cnt.textContent = debugSelected.size;
        const list = panel.querySelector(".debug-list");
        if (list) {
            if (!debugSelected.size) {
                list.innerHTML = '<div style="color:#444;font-size:9px;padding:4px">Click data points to flag</div>';
            } else {
                list.innerHTML = [...debugSelected].map(id =>
                    `<div class="debug-list-item"><span>${esc(id)}</span><button class="debug-remove" data-id="${esc(id)}">×</button></div>`
                ).join("");
                list.querySelectorAll(".debug-remove").forEach(btn => {
                    btn.addEventListener("click", e => {
                        e.stopPropagation();
                        const rid = btn.dataset.id;
                        debugSelected.delete(rid);
                        document.querySelectorAll(`[data-debug-id="${rid}"]`).forEach(el => el.classList.remove("debug-selected"));
                        updateDebugPanel();
                    });
                });
            }
        }
    }

    document.getElementById("debug-toggle").addEventListener("click", () => {
        debugMode = !debugMode;
        document.getElementById("debug-toggle").classList.toggle("active", debugMode);
        document.getElementById("debug-panel").classList.toggle("hidden", !debugMode);
        document.body.classList.toggle("debug-active", debugMode);
        if (debugMode) { renderSidebar(); fetchMarket(); }
    });

    document.getElementById("debug-clear").addEventListener("click", () => {
        debugSelected.clear();
        document.querySelectorAll(".debug-selected").forEach(el => el.classList.remove("debug-selected"));
        updateDebugPanel();
    });

    document.getElementById("debug-create-ticket").addEventListener("click", () => {
        if (!debugSelected.size) { alert("No items flagged."); return; }
        const items = [...debugSelected];
        const ticketBody = "DATA QUALITY TICKET\nCreated: " + new Date().toISOString().slice(0, 16) + "\nFlagged items (" + items.length + "):\n" + items.map((id, i) => "  " + (i + 1) + ". " + id).join("\n") + "\n\nAction: verify and fix flagged data sources.";

        // Save to SQL
        fetch("/api/tickets", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items, notes: "Automated report via terminal DBG mode." })
        }).then(r => r.json()).then(j => {
            console.log("Ticket saved locally ID:", j.ticket_id);
            navigator.clipboard.writeText(ticketBody).then(() => {
                alert(`Ticket #${j.ticket_id} saved to DB and copied to clipboard!`);
            }).catch(() => prompt("Copy:", ticketBody));
        }).catch(err => {
            console.error("Failed to save ticket:", err);
            navigator.clipboard.writeText(ticketBody).then(() => alert("Saved to clipboard (SQL sync failed)")).catch(() => prompt("Copy:", ticketBody));
        });
    });

    // -----------------------------------------------------------------------
    // CONTEXT DRAWER / DIGITAL TUTOR
    // -----------------------------------------------------------------------
    if (document.getElementById("drawer-close")) {
        document.getElementById("drawer-close").addEventListener("click", () => {
            document.getElementById("context-drawer").classList.add("hidden");
        });
    }

    document.addEventListener("click", e => {
        const explainEl = e.target.closest("[data-explain]");
        if (explainEl) {
            const key = explainEl.getAttribute("data-explain");
            openContextDrawer(key, explainEl);
        }
    });

    async function openContextDrawer(key, explainEl) {
        const drawer = document.getElementById("context-drawer");
        const nameEl = document.getElementById("concept-name");
        const defEl = document.getElementById("concept-definition");
        const instEl = document.getElementById("concept-institutional");
        const relEl = document.getElementById("concept-relationships");
        const newsEl = document.getElementById("concept-news");
        const aiBox = document.getElementById("drawer-ai-synthesis");

        if (!drawer) return;

        // UI Reset
        nameEl.textContent = "Loading...";
        defEl.textContent = "";
        instEl.textContent = "";
        relEl.innerHTML = "";
        newsEl.innerHTML = "";
        aiBox.classList.add("hidden");
        drawer.classList.remove("hidden");

        try {
            const r = await fetch(`/api/knowledge/${key}`);
            const ctx = await r.json();

            nameEl.textContent = ctx.full_name || key;
            defEl.textContent = ctx.definition || "";
            instEl.textContent = ctx.institutional_meaning || "";

            // Relationships
            if (ctx.relationships && Object.keys(ctx.relationships).length) {
                let relHtml = "";
                for (const [target, desc] of Object.entries(ctx.relationships)) {
                    relHtml += `<li><b>${esc(target)}</b> ${esc(desc)}</li>`;
                }
                relEl.innerHTML = relHtml;
                document.getElementById("section-relationships").style.display = "block";
            } else {
                if (document.getElementById("section-relationships"))
                    document.getElementById("section-relationships").style.display = "none";
            }

            // News context (filter from newsData)
            let filteredNews = [];
            if (newsData && newsData.length) {
                const searchText = (ctx.full_name || key).toLowerCase();
                filteredNews = newsData.filter(n => {
                    const fullText = (n.title + (n.summary || "")).toLowerCase();
                    return fullText.includes(searchText);
                }).slice(0, 5);

                if (filteredNews.length) {
                    newsEl.innerHTML = filteredNews.map(n => `
                        <div class="drawer-news-item" onclick="window.open('${esc(n.link)}','_blank')">
                            <div style="font-weight:600">${esc(n.title)}</div>
                            <div style="color:var(--text-muted); font-size:9px; margin-top:2px;">${esc(n.source)} • ${esc(n.published)}</div>
                        </div>
                    `).join("");
                } else {
                    newsEl.innerHTML = '<div style="color:#444; font-size:9px">No direct headlines found in current feed.</div>';
                }
            }

            // AI Synthesis (Optional Narrative)
            let valText = "N/A";
            const sbVal = explainEl.querySelector(".sb-val");
            const lastVal = explainEl.querySelector(".last-val");
            const statVal = explainEl.querySelector(".stat-value");

            if (sbVal) valText = sbVal.innerText;
            else if (lastVal) valText = lastVal.innerText;
            else if (statVal) valText = statVal.innerText;

            aiSynthesis(ctx.full_name || key, valText, "", filteredNews || []);

        } catch (e) {
            console.error("Drawer Error:", e);
            nameEl.textContent = "Concept not found.";
            defEl.textContent = "Knowledge base indexing in progress.";
        }
    }

    async function aiSynthesis(concept, value, unit, headlines) {
        const aiBox = document.getElementById("drawer-ai-synthesis");
        const aiText = document.getElementById("ai-narrative");
        if (!aiBox || !aiText) return;

        aiBox.classList.remove("hidden");
        aiText.innerHTML = '<div class="sb-loading">Synthesizing narrative...</div>';

        try {
            const r = await fetch("/api/synthesis", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ concept, value, unit, headlines: headlines.slice(0, 5) })
            });
            const j = await r.json();
            aiText.innerHTML = `<div style="line-height:1.4; font-size:11px;">${esc(j.narrative)}</div>`;
        } catch (e) {
            aiText.innerHTML = '<div style="color:var(--red); font-size:9px">Synthesis failed. AI Research Desk is busy.</div>';
        }
    }

    // -----------------------------------------------------------------------
    // TERMINAL ASSISTANT (Chatbot)
    // -----------------------------------------------------------------------
    function handleChat() {
        const toggle = document.getElementById("chat-toggle");
        const container = document.getElementById("chat-container");
        const minimize = document.getElementById("chat-minimize");
        const input = document.getElementById("chat-input");
        const sendBtn = document.getElementById("chat-send");

        if (!toggle || !container) return;

        toggle.addEventListener("click", () => {
            container.classList.toggle("hidden");
            if (!container.classList.contains("hidden")) input.focus();
        });

        minimize.addEventListener("click", () => container.classList.add("hidden"));

        sendBtn.addEventListener("click", sendChatMessage);
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendChatMessage();
        });
    }

    function appendChatMessage(sender, text) {
        const hist = document.getElementById("chat-history");
        if (!hist) return;
        const msg = document.createElement("div");
        msg.className = `chat-msg ${sender}`;
        msg.innerHTML = text.replace(/\n/g, '<br>');
        hist.appendChild(msg);
        hist.scrollTop = hist.scrollHeight;
    }

    async function sendChatMessage() {
        const input = document.getElementById("chat-input");
        const sendBtn = document.getElementById("chat-send");
        const query = input.value.trim();
        if (!query) return;

        input.value = "";
        input.disabled = true;
        sendBtn.disabled = true;

        appendChatMessage("user", esc(query));

        try {
            // Context injection
            const news = (newsData || []).slice(0, 10);
            const markets = {
                indices: marketStore,
                macro: turkeyMacroStore,
                movers: moversData
            };

            const r = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query,
                    news,
                    markets,
                    chartContext: chartDataStore
                })
            });
            const j = await r.json();
            appendChatMessage("ai", j.response);
        } catch (e) {
            appendChatMessage("ai", "Communication with the Research Desk failed.");
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    // -----------------------------------------------------------------------
    // INIT + POLL
    // -----------------------------------------------------------------------
    async function fetchEquityRisk() {
        try {
            const res = await fetch("/api/equity-risk");
            if (res.ok) {
                erpStore = await res.json();
                renderSbBonds();
            }
        } catch (e) {
            console.error("ERP fetch error:", e);
        }
    }

    async function fetchDistressed() {
        try {
            const res = await fetch("/api/distressed");
            if (res.ok) {
                const data = await res.json();
                renderSbDistressed(data);
            }
        } catch (e) { console.error("Distressed fetch error:", e); }
    }

    async function fetchGoldCorrelation() {
        try {
            const res = await fetch("/api/gold-correlation");
            if (res.ok) {
                const data = await res.json();
                renderSbGoldCorr(data);
            }
        } catch (e) { console.error("Gold Corr fetch error:", e); }
    }

    async function fetchScorecard() {
        try {
            const res = await fetch("/api/scorecard");
            if (res.ok) {
                const data = await res.json();
                renderSbScorecard(data);
            }
        } catch (e) { console.error("Scorecard fetch error:", e); }
    }

    function renderSbScorecard(data) {
        // Create container at top of right sidebar if not exists
        const rightBar = document.getElementById("sidebar-right");
        if (!rightBar) return;

        let container = document.getElementById("sb-scorecard-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "sb-scorecard-container";
            container.className = "sb-section";
            rightBar.insertBefore(container, rightBar.firstChild);
        }

        if (!data || !data.signal) {
            container.innerHTML = `<div class="sb-header">MACRO SCORECARD</div><div class="sb-row text-muted">Loading...</div>`;
            return;
        }

        const score = data.composite || 0;
        const signal = data.signal;

        // Color based on signal
        let signalColor = "#ffd700"; // NEUTRAL
        if (signal === "RISK-ON") signalColor = "#00e676";
        else if (signal === "RISK-OFF") signalColor = "#ff1744";

        // Gauge bar (linear from -100 to +100)
        const pct = ((score + 100) / 200) * 100; // 0-100%

        let html = `<div class="sb-header" style="color:${signalColor}">MACRO SCORECARD</div>`;

        // Signal badge
        html += `<div style="text-align:center;padding:8px 0">`;
        html += `<span style="font-size:1.6em;font-weight:900;color:${signalColor};letter-spacing:2px">${signal}</span>`;
        html += `<div style="font-size:0.85em;color:var(--text-muted);margin-top:2px">Score: ${score}</div>`;
        html += `</div>`;

        // Gauge bar
        html += `<div style="background:var(--bg-tertiary);border-radius:4px;height:8px;margin:4px 12px 8px;position:relative;overflow:hidden">`;
        html += `<div style="position:absolute;left:0;top:0;height:100%;width:${pct}%;background:linear-gradient(90deg,#ff1744,#ffd700 50%,#00e676);border-radius:4px;transition:width 0.5s ease"></div>`;
        html += `<div style="position:absolute;left:50%;top:-2px;width:2px;height:12px;background:var(--text-secondary)"></div>`;
        html += `</div>`;

        // Individual metrics
        const labels = {
            "yield_curve": "Yield Curve",
            "real_carry": "Real Carry",
            "ppi_cpi_gap": "PPI-CPI Gap",
            "erp": "ERP",
            "cds": "CDS",
            "gold_corr": "Gold Corr"
        };

        if (data.scores) {
            for (const [key, info] of Object.entries(data.scores)) {
                const lbl = labels[key] || key;
                const s = info.score;
                const cls = s > 0 ? "up" : s < 0 ? "down" : "";
                const icon = s > 0 ? "▲" : s < 0 ? "▼" : "●";
                html += sbRow(lbl, `<span class="${cls}">${icon} ${info.signal}</span>`, null, `Value: ${info.value}, Score: ${s}`);
            }
        }

        html += `<div style="text-align:center;font-size:0.7em;color:var(--text-muted);padding:4px">${data.metrics_available}/${data.metrics_total} metrics</div>`;

        container.innerHTML = html;
    }

    // =====================================================================
    //  COMMAND BAR — Everything has a name
    // =====================================================================
    let cmdSelectedIndex = -1;
    let cmdResults = [];

    function initCommandBar() {
        const input = document.getElementById("cmd-input");
        const ac = document.getElementById("cmd-autocomplete");
        const overlay = document.getElementById("cmd-popup-overlay");
        const closeBtn = document.getElementById("cmd-popup-close");

        if (!input) return;

        // Keyboard shortcut: "/" focuses command bar
        document.addEventListener("keydown", (e) => {
            if (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
                e.preventDefault();
                input.focus();
                input.select();
            }
            // Escape closes popup
            if (e.key === "Escape") {
                ac.classList.add("hidden");
                if (overlay) overlay.classList.add("hidden");
                input.blur();
            }
        });

        // Input handler — live search
        let debounceTimer;
        input.addEventListener("input", () => {
            clearTimeout(debounceTimer);
            const val = input.value.trim();
            if (val.length < 1) {
                ac.classList.add("hidden");
                cmdResults = [];
                cmdSelectedIndex = -1;
                return;
            }
            debounceTimer = setTimeout(() => searchRegistry(val), 150);
        });

        // Arrow keys + Enter on autocomplete
        input.addEventListener("keydown", (e) => {
            if (ac.classList.contains("hidden")) {
                // Enter on full command (e.g., "@cds set 280")
                if (e.key === "Enter") {
                    e.preventDefault();
                    handleCommand(input.value.trim());
                }
                return;
            }
            if (e.key === "ArrowDown") {
                e.preventDefault();
                cmdSelectedIndex = Math.min(cmdSelectedIndex + 1, cmdResults.length - 1);
                renderAutocomplete();
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                cmdSelectedIndex = Math.max(cmdSelectedIndex - 1, 0);
                renderAutocomplete();
            } else if (e.key === "Enter") {
                e.preventDefault();
                if (cmdSelectedIndex >= 0 && cmdResults[cmdSelectedIndex]) {
                    selectEntity(cmdResults[cmdSelectedIndex].key);
                } else {
                    handleCommand(input.value.trim());
                }
            }
        });

        // Click outside autocomplete closes it
        document.addEventListener("click", (e) => {
            if (!e.target.closest("#command-bar")) {
                ac.classList.add("hidden");
            }
        });

        // Focus shows results if we have them
        input.addEventListener("focus", () => {
            if (cmdResults.length > 0) ac.classList.remove("hidden");
        });

        // Close popup
        if (closeBtn) closeBtn.onclick = () => overlay.classList.add("hidden");
        if (overlay) overlay.addEventListener("click", (e) => {
            if (e.target === overlay) overlay.classList.add("hidden");
        });
    }

    async function searchRegistry(query) {
        const ac = document.getElementById("cmd-autocomplete");
        try {
            const clean = query.replace(/^@/, "");
            const r = await fetch(`/api/registry/search?q=${encodeURIComponent(clean)}`);
            cmdResults = await r.json();
            cmdSelectedIndex = cmdResults.length > 0 ? 0 : -1;
            if (cmdResults.length === 0) {
                ac.classList.add("hidden");
                return;
            }
            ac.classList.remove("hidden");
            renderAutocomplete();
        } catch (e) {
            ac.classList.add("hidden");
        }
    }

    function renderAutocomplete() {
        const ac = document.getElementById("cmd-autocomplete");
        ac.innerHTML = cmdResults.map((item, i) => `
            <div class="cmd-ac-item ${i === cmdSelectedIndex ? 'selected' : ''}" data-key="${item.key}">
                <span class="cmd-ac-key">@${item.key}</span>
                <span class="cmd-ac-name">${item.name}</span>
                <span class="cmd-ac-group">${item.group}</span>
            </div>
        `).join("");

        // Click handlers
        ac.querySelectorAll(".cmd-ac-item").forEach(el => {
            el.addEventListener("click", () => selectEntity(el.dataset.key));
        });
    }

    async function selectEntity(key) {
        const ac = document.getElementById("cmd-autocomplete");
        const input = document.getElementById("cmd-input");
        ac.classList.add("hidden");
        input.value = `@${key}`;
        input.blur();
        showEntityPopup(key);
    }

    async function handleCommand(rawInput) {
        const ac = document.getElementById("cmd-autocomplete");
        ac.classList.add("hidden");

        if (!rawInput) return;
        const input = rawInput.replace(/^@/, "").trim();

        // Check for "vs" comparison: @gold vs @usdtry
        const vsMatch = input.match(/^(\S+)\s+vs\s+@?(\S+)$/i);
        if (vsMatch) {
            showComparisonPopup(vsMatch[1], vsMatch[2]);
            return;
        }

        const parts = input.split(/\s+/);
        const entityKey = parts[0];
        const verb = parts[1]?.toLowerCase();
        const value = parts.slice(2).join(" ");

        if (verb === "set" && value) {
            await setEntityOverride(entityKey, value);
            return;
        }

        if (verb === "clear") {
            await clearEntityOverride(entityKey);
            return;
        }

        if (verb === "graph" || verb === "chart") {
            switchChartToEntity(entityKey);
            return;
        }

        if (verb === "explain") {
            showEntityPopup(entityKey);
            return;
        }

        // Default: lookup popup
        showEntityPopup(entityKey);
    }

    async function showEntityPopup(key) {
        const overlay = document.getElementById("cmd-popup-overlay");
        const titleEl = document.getElementById("cmd-popup-title");
        const groupEl = document.getElementById("cmd-popup-group");
        const bodyEl = document.getElementById("cmd-popup-body");

        try {
            const r = await fetch(`/api/entity/${encodeURIComponent(key)}`);
            if (!r.ok) {
                bodyEl.innerHTML = `<div style="color:var(--red)">Entity "@${key}" not found.</div>`;
                titleEl.textContent = "Not Found";
                groupEl.textContent = "?";
                overlay.classList.remove("hidden");
                return;
            }
            const entity = await r.json();

            titleEl.textContent = entity.name;
            groupEl.textContent = entity.group.toUpperCase();

            let html = "";

            // Current value section
            html += `<div class="cmd-popup-section">`;
            html += `<div class="cmd-popup-section-title">Current Data</div>`;
            html += `<div class="cmd-popup-value-row">
                        <span class="cmd-popup-value-label">Key</span>
                        <span class="cmd-popup-value-data" style="color:var(--orange)">@${key}</span>
                     </div>`;
            html += `<div class="cmd-popup-value-row">
                        <span class="cmd-popup-value-label">Source</span>
                        <span class="cmd-popup-value-data">${entity.source}</span>
                     </div>`;
            html += `<div class="cmd-popup-value-row">
                        <span class="cmd-popup-value-label">Unit</span>
                        <span class="cmd-popup-value-data">${entity.unit || "—"}</span>
                     </div>`;
            if (entity.override) {
                html += `<div class="cmd-popup-value-row" style="background:#1a1500;">
                            <span class="cmd-popup-value-label">⚠ Manual Override</span>
                            <span class="cmd-popup-value-data" style="color:var(--orange)">${entity.override.value} ${entity.unit} <span class="override-badge">M</span></span>
                         </div>`;
                html += `<div class="cmd-popup-value-row">
                            <span class="cmd-popup-value-label">Override Source</span>
                            <span class="cmd-popup-value-data">${entity.override.source} (${entity.override.timestamp})</span>
                         </div>`;
            }
            if (entity.chartable) {
                html += `<div class="cmd-popup-value-row">
                            <span class="cmd-popup-value-label">Chartable</span>
                            <span class="cmd-popup-value-data" style="color:var(--green)">✓ @${key} graph</span>
                         </div>`;
            }
            html += `</div>`;

            // Explain section
            if (entity.explain) {
                html += `<div class="cmd-popup-section">`;
                html += `<div class="cmd-popup-section-title">What is this?</div>`;
                html += `<div class="cmd-popup-explain">${entity.explain}</div>`;
                html += `</div>`;
            }

            // Related entities
            if (entity.related && entity.related.length > 0) {
                html += `<div class="cmd-popup-section">`;
                html += `<div class="cmd-popup-section-title">Related (${entity.group})</div>`;
                html += `<div class="cmd-popup-related">`;
                for (const rel of entity.related) {
                    html += `<button class="cmd-popup-related-tag" data-key="${rel.key}">@${rel.key} — ${rel.name}</button>`;
                }
                html += `</div></div>`;
            }

            // Quick actions
            html += `<div class="cmd-popup-section">`;
            html += `<div class="cmd-popup-section-title">Quick Actions</div>`;
            html += `<div style="display:flex;gap:6px;flex-wrap:wrap;">`;
            html += `<button class="cmd-popup-related-tag cmd-action-set" data-key="${key}">Set Override</button>`;
            if (entity.override) {
                html += `<button class="cmd-popup-related-tag cmd-action-clear" data-key="${key}" style="border-color:var(--red);color:var(--red)">Clear Override</button>`;
            }
            if (entity.chartable) {
                html += `<button class="cmd-popup-related-tag cmd-action-graph" data-key="${key}">Show Graph</button>`;
            }
            html += `</div></div>`;

            bodyEl.innerHTML = html;

            // Wire up related tag clicks
            bodyEl.querySelectorAll(".cmd-popup-related-tag[data-key]").forEach(btn => {
                if (btn.classList.contains("cmd-action-set")) {
                    btn.addEventListener("click", () => {
                        const val = prompt(`Set @${btn.dataset.key} value:`);
                        if (val !== null) setEntityOverride(btn.dataset.key, val);
                    });
                } else if (btn.classList.contains("cmd-action-clear")) {
                    btn.addEventListener("click", () => clearEntityOverride(btn.dataset.key));
                } else if (btn.classList.contains("cmd-action-graph")) {
                    btn.addEventListener("click", () => {
                        overlay.classList.add("hidden");
                        switchChartToEntity(btn.dataset.key);
                    });
                } else {
                    btn.addEventListener("click", () => showEntityPopup(btn.dataset.key));
                }
            });

            overlay.classList.remove("hidden");
        } catch (e) {
            console.error("[CMD]", e);
            bodyEl.innerHTML = `<div style="color:var(--red)">Error loading entity.</div>`;
            overlay.classList.remove("hidden");
        }
    }

    async function setEntityOverride(key, value) {
        try {
            const r = await fetch(`/api/entity/${encodeURIComponent(key)}/set`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ value })
            });
            const result = await r.json();
            if (result.ok) {
                // Refresh the popup to show the override
                showEntityPopup(key);
            }
        } catch (e) {
            console.error("[CMD] Override failed:", e);
        }
    }

    async function clearEntityOverride(key) {
        try {
            await fetch(`/api/entity/${encodeURIComponent(key)}/clear`, { method: "POST" });
            showEntityPopup(key);
        } catch (e) {
            console.error("[CMD] Clear failed:", e);
        }
    }

    function switchChartToEntity(key) {
        fetch(`/api/entity/${encodeURIComponent(key)}`)
            .then(r => r.json())
            .then(entity => {
                if (entity.chartable && entity.key) {
                    const chartSymbol = document.getElementById("chart-symbol");
                    let optionExists = false;
                    for (const opt of chartSymbol.options) {
                        if (opt.value === entity.key) { optionExists = true; break; }
                    }
                    if (!optionExists) {
                        const opt = document.createElement("option");
                        opt.value = entity.key;
                        opt.textContent = entity.name;
                        chartSymbol.appendChild(opt);
                    }
                    chartSymbol.value = entity.key;
                    fetchChart();
                }
            });
    }

    async function showComparisonPopup(keyA, keyB) {
        const overlay = document.getElementById("cmd-popup-overlay");
        const titleEl = document.getElementById("cmd-popup-title");
        const groupEl = document.getElementById("cmd-popup-group");
        const bodyEl = document.getElementById("cmd-popup-body");

        try {
            const [rA, rB] = await Promise.all([
                fetch(`/api/entity/${encodeURIComponent(keyA)}`).then(r => r.json()),
                fetch(`/api/entity/${encodeURIComponent(keyB)}`).then(r => r.json())
            ]);

            if (rA.error || rB.error) {
                bodyEl.innerHTML = `<div style="color:var(--red)">One or both entities not found: @${keyA}, @${keyB}</div>`;
                titleEl.textContent = "Comparison Error";
                groupEl.textContent = "VS";
                overlay.classList.remove("hidden");
                return;
            }

            titleEl.textContent = `${rA.name} vs ${rB.name}`;
            groupEl.textContent = "COMPARE";

            let html = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">`;

            // Entity A column
            html += `<div class="cmd-popup-section">`;
            html += `<div class="cmd-popup-section-title" style="color:var(--green)">@${keyA}</div>`;
            html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Name</span><span class="cmd-popup-value-data">${rA.name}</span></div>`;
            html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Group</span><span class="cmd-popup-value-data">${rA.group}</span></div>`;
            html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Source</span><span class="cmd-popup-value-data">${rA.source}</span></div>`;
            html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Unit</span><span class="cmd-popup-value-data">${rA.unit || "—"}</span></div>`;
            if (rA.chartable) html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Chart</span><span class="cmd-popup-value-data" style="color:var(--green)">✓</span></div>`;
            html += `</div>`;

            // Entity B column
            html += `<div class="cmd-popup-section">`;
            html += `<div class="cmd-popup-section-title" style="color:var(--orange)">@${keyB}</div>`;
            html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Name</span><span class="cmd-popup-value-data">${rB.name}</span></div>`;
            html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Group</span><span class="cmd-popup-value-data">${rB.group}</span></div>`;
            html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Source</span><span class="cmd-popup-value-data">${rB.source}</span></div>`;
            html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Unit</span><span class="cmd-popup-value-data">${rB.unit || "—"}</span></div>`;
            if (rB.chartable) html += `<div class="cmd-popup-value-row"><span class="cmd-popup-value-label">Chart</span><span class="cmd-popup-value-data" style="color:var(--green)">✓</span></div>`;
            html += `</div>`;

            html += `</div>`; // close grid

            // Explanations side by side
            html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;">`;
            html += `<div class="cmd-popup-explain">${rA.explain || "No explanation"}</div>`;
            html += `<div class="cmd-popup-explain">${rB.explain || "No explanation"}</div>`;
            html += `</div>`;

            // Actions
            html += `<div class="cmd-popup-section" style="margin-top:12px">`;
            html += `<div class="cmd-popup-section-title">Actions</div>`;
            html += `<div style="display:flex;gap:6px;">`;
            html += `<button class="cmd-popup-related-tag" data-key="${keyA}">View @${keyA}</button>`;
            html += `<button class="cmd-popup-related-tag" data-key="${keyB}">View @${keyB}</button>`;
            html += `</div></div>`;

            bodyEl.innerHTML = html;

            // Click handlers for action buttons
            bodyEl.querySelectorAll(".cmd-popup-related-tag[data-key]").forEach(btn => {
                btn.addEventListener("click", () => showEntityPopup(btn.dataset.key));
            });

            overlay.classList.remove("hidden");
        } catch (e) {
            console.error("[CMD] Comparison failed:", e);
        }
    }

    async function fetchOverrides() {
        try {
            const r = await fetch("/api/overrides");
            const overrides = await r.json();
            overrideStore = {};
            for (const ovr of overrides) {
                overrideStore[ovr.entity_key] = {
                    value: ovr.value,
                    source: ovr.source,
                    timestamp: ovr.timestamp
                };
            }
            // Re-render sidebar to show M badges
            if (Object.keys(overrideStore).length > 0) {
                renderSidebar();
            }
        } catch (e) {
            console.error("[CMD] Failed to fetch overrides:", e);
        }
    }

    function initOverrideToggle() {
        const btn = document.getElementById("override-toggle");
        if (!btn) return;

        btn.addEventListener("click", () => {
            overrideMode = !overrideMode;
            btn.classList.toggle("active", overrideMode);
            // Re-render sidebar to add/remove editable indicators
            renderSidebar();

            if (overrideMode) {
                // Attach click-to-edit on sidebar rows with registry keys
                document.querySelectorAll(".sb-row[data-registry-key]").forEach(row => {
                    row.addEventListener("click", handleOverrideClick);
                });
            }
        });
    }

    function handleOverrideClick(e) {
        if (!overrideMode) return;
        const row = e.currentTarget;
        const key = row.dataset.registryKey;
        if (!key) return;

        const currentVal = row.querySelector(".sb-val")?.textContent?.trim() || "";
        const newVal = prompt(`Set @${key} override value:\n(Current: ${currentVal})`);
        if (newVal !== null && newVal.trim() !== "") {
            setEntityOverride(key, newVal.trim()).then(() => {
                fetchOverrides();
            });
        }
    }

    async function init() {
        initCommandBar();
        initOverrideToggle();
        await Promise.all([
            fetchMarket(),
            fetchMacro(),
            fetchTurkeyMacro(),
            fetchCBRT(),
            fetchCalendar(),
            fetchMovers(),
            fetchNews(),
            fetchBrief(),
            loadSymbols(),
            handleChat(),
            fetchEquityRisk(),
            fetchOverrides(),
        ]);
        fetchChart();
        fetchDistressed();
        fetchGoldCorrelation();
        fetchScorecard(); // Final synthesis
    }

    function poll() {
        // Fast: market + macro + brief (60s)
        setInterval(() => { fetchMarket(); fetchMacro(); fetchBrief(); }, POLL_INTERVAL);
        // Medium: movers + news (3 min)
        setInterval(() => { fetchMovers(); fetchNews(); }, POLL_INTERVAL * 3);
        // Slow: turkey macro, cbrt, calendar, erp, distressed, gold corr, scorecard (10 min)
        setInterval(() => { fetchTurkeyMacro(); fetchCBRT(); fetchCalendar(); fetchEquityRisk(); fetchDistressed(); fetchGoldCorrelation(); fetchScorecard(); }, POLL_INTERVAL * 10);
        // Check overrides every 2 min
        setInterval(() => { fetchOverrides(); }, POLL_INTERVAL * 2);
    }

    init().then(poll);
})();
