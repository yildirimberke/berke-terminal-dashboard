"""
Data Registry — Every metric has a name.
Maps canonical @names to their metadata, data source, and educational explanations.
"""

DATA_REGISTRY = {
    # ── POLICY RATES ─────────────────────────────────────────────────
    "policy_rate":    {"name": "CBRT Policy Rate",      "group": "rates",      "key": "policy_rate",     "source": "macro", "unit": "%",
                       "explain": "The CBRT's one-week repo rate — the benchmark interest rate for Turkey. Higher = tighter monetary policy = stronger TRY but slower growth."},
    "deposit_rate":   {"name": "Deposit Rate",          "group": "rates",      "key": "deposit_rate",    "source": "macro", "unit": "%",
                       "explain": "Interest rate paid on overnight deposits at the central bank. Acts as the floor of the interest rate corridor."},
    "com_loan":       {"name": "Commercial Loan Rate",  "group": "rates",      "key": "com_loan",        "source": "macro", "unit": "%",
                       "explain": "Average interest rate on commercial loans. Shows the real cost of borrowing for Turkish businesses."},
    "real_rate":      {"name": "Real Interest Rate",    "group": "rates",      "key": "real_rate",       "source": "macro", "unit": "%",
                       "explain": "Policy Rate minus Inflation. Positive = monetary tightening is biting. Negative = inflation outpaces rates (loose policy in disguise)."},
    "real_carry":     {"name": "Real Carry",            "group": "rates",      "key": "real_carry",      "source": "macro", "unit": "%",
                       "explain": "The return a foreign investor earns by borrowing in USD and depositing in TRY, adjusted for inflation. High carry attracts hot money into TRY assets."},

    # ── BONDS & RISK ─────────────────────────────────────────────────
    "tr_2y":          {"name": "TR 2Y Bond Yield",      "group": "bonds",      "key": "tr_2y",           "source": "macro", "unit": "%",
                       "explain": "Yield on Turkish 2-year government bonds. Reflects near-term rate expectations and central bank credibility."},
    "tr_10y":         {"name": "TR 10Y Bond Yield",     "group": "bonds",      "key": "tr_10y",          "source": "equity_risk", "unit": "%",
                       "explain": "Yield on Turkish 10-year government bonds. The long-term benchmark — reflects inflation expectations and sovereign risk."},
    "us_10y":         {"name": "US 10Y Bond Yield",     "group": "bonds",      "key": "us_10y",          "source": "macro", "unit": "%",
                       "explain": "The global risk-free rate. When US 10Y rises, capital flows out of EM (including Turkey) back to USD safety."},
    "risk_premium":   {"name": "Risk Premium (Spread)", "group": "bonds",      "key": "risk_premium",    "source": "macro", "unit": "bps",
                       "explain": "TR 10Y minus US 10Y. Shows how much extra yield investors demand to hold Turkish debt vs US Treasuries. Higher = more perceived risk."},
    "tr_curve":       {"name": "Yield Curve (10Y-2Y)",  "group": "bonds",      "key": "tr_curve",        "source": "macro", "unit": "bps",
                       "explain": "10Y yield minus 2Y yield. Negative (inverted) = market expects rate cuts or recession. Deeply inverted = danger signal."},
    "cds":            {"name": "Turkey 5Y CDS",         "group": "bonds",      "key": "cds",             "source": "macro", "unit": "bps",
                       "explain": "Credit Default Swap spread — the cost of insuring Turkish sovereign debt against default. Higher = market thinks Turkey is riskier."},
    "erp":            {"name": "Equity Risk Premium",   "group": "bonds",      "key": "erp",             "source": "equity_risk", "unit": "%",
                       "explain": "Earnings Yield minus Risk-Free Rate. Positive ERP = stocks are cheap vs bonds. Negative = bonds beat stocks (why take equity risk?)."},
    "pe":             {"name": "BIST 100 P/E Ratio",    "group": "bonds",      "key": "pe",              "source": "equity_risk", "unit": "x",
                       "explain": "Price-to-Earnings ratio of the BIST 100 index. Lower P/E = cheaper market. Turkey historically trades at 5-8x (deep discount vs EM peers at 12-15x)."},

    # ── INFLATION ────────────────────────────────────────────────────
    "cpi_yoy":        {"name": "CPI YoY",               "group": "inflation",  "key": "cpi_yoy",         "source": "macro", "unit": "%",
                       "explain": "Consumer Price Index, year-over-year change. The headline inflation number Turkey reports monthly. Above 50% = hyperinflation territory."},
    "cpi_mom":        {"name": "CPI MoM",               "group": "inflation",  "key": "cpi_mom",         "source": "macro", "unit": "%",
                       "explain": "Monthly inflation rate. Annualize this (×12) for a rough read of current inflation momentum."},
    "core_cpi":       {"name": "Core CPI",              "group": "inflation",  "key": "core_cpi",        "source": "macro", "unit": "%",
                       "explain": "CPI excluding food and energy — shows 'sticky' underlying inflation. If core is high, rate cuts won't come soon."},
    "ppi_yoy":        {"name": "PPI YoY",               "group": "inflation",  "key": "ppi_yoy",         "source": "macro", "unit": "%",
                       "explain": "Producer Price Index YoY. A leading indicator for CPI — today's PPI increase becomes tomorrow's CPI increase as costs pass through."},
    "ppi_cpi_gap":    {"name": "PPI-CPI Gap",           "group": "inflation",  "key": "ppi_cpi_gap",     "source": "macro", "unit": "pts",
                       "explain": "PPI minus CPI. Positive gap = producers are absorbing costs (margins shrinking). Negative gap = cost pressures easing, disinflation signal."},
    "food_cpi":       {"name": "Food CPI",              "group": "inflation",  "key": "food_cpi",        "source": "macro", "unit": "%",
                       "explain": "Food inflation — critical in Turkey where food is 25%+ of the CPI basket. Politically sensitive."},

    # ── REAL ECONOMY ─────────────────────────────────────────────────
    "gdp_growth":     {"name": "GDP Growth",            "group": "economy",    "key": "gdp_growth",      "source": "macro", "unit": "%",
                       "explain": "Real GDP growth rate. Turkey's economy is consumption-driven. Positive growth + high inflation = overheating."},
    "unemployment":   {"name": "Unemployment Rate",     "group": "economy",    "key": "unemployment",    "source": "macro", "unit": "%",
                       "explain": "Official unemployment rate. Note: Turkey's broad unemployment (including discouraged workers) is typically 2-3x the official figure."},
    "current_account":{"name": "Current Account",       "group": "economy",    "key": "current_account", "source": "macro", "unit": "M$",
                       "explain": "Current account balance. Negative = Turkey imports more than it exports = needs foreign currency inflows = vulnerable to capital flight."},
    "fx_reserves":    {"name": "FX Reserves (Net)",     "group": "economy",    "key": "fx_reserves",     "source": "macro", "unit": "M$",
                       "explain": "Central bank net FX reserves. Turkey's reserves are notoriously low. Below $30B net = danger zone (can't defend TRY)."},
    "m2_supply":      {"name": "M2 Money Supply",       "group": "economy",    "key": "m2_supply",       "source": "macro", "unit": "B TL",
                       "explain": "Broad money supply. Rapid M2 growth = too much money chasing goods = fuel for inflation."},
    "total_credit":   {"name": "Total Credit",          "group": "economy",    "key": "total_credit",    "source": "macro", "unit": "B TL",
                       "explain": "Total bank credit in the economy. Rapid credit growth = overheating risk. CBRT uses 'macroprudential' tools to slow this."},
    "biz_confidence": {"name": "Business Confidence",   "group": "economy",    "key": "biz_confidence",  "source": "macro", "unit": "",
                       "explain": "Business confidence index. Above 100 = optimistic. Below 100 = pessimistic. A leading indicator for investment and hiring."},
    "consumer_conf":  {"name": "Consumer Confidence",   "group": "economy",    "key": "consumer_conf",   "source": "macro", "unit": "",
                       "explain": "Consumer confidence index. Low confidence = people delay purchases = slower growth."},
    "rating":         {"name": "Sovereign Credit Rating","group": "economy",   "key": "rating",          "source": "macro", "unit": "",
                       "explain": "Turkey's sovereign credit rating (Moody's/Fitch/S&P). Currently sub-investment grade ('junk'). Upgrade = massive capital inflows."},

    # ── CBRT & TRY ───────────────────────────────────────────────────
    "cbrt_rate":      {"name": "CBRT Policy Rate",      "group": "cbrt",       "key": "policy_rate",     "source": "cbrt",  "unit": "%",
                       "explain": "Same as Policy Rate, shown in the CBRT context panel. The CBRT's main policy lever."},
    "cbrt_next":      {"name": "CBRT Next Meeting",     "group": "cbrt",       "key": "next_meeting",    "source": "cbrt",  "unit": "",
                       "explain": "Date of the next Monetary Policy Committee (MPC) meeting. Markets price in rate decisions weeks before."},

    # ── MARKET INSTRUMENTS ───────────────────────────────────────────
    "bist100":        {"name": "BIST 100 Index",        "group": "equities",   "key": "XU100.IS",        "source": "market", "unit": "pts", "chartable": True,
                       "explain": "Borsa Istanbul 100 — Turkey's main stock index. Composed of the 100 largest companies by market cap."},
    "bist30":         {"name": "BIST 30 Index",         "group": "equities",   "key": "XU030.IS",        "source": "market", "unit": "pts", "chartable": True,
                       "explain": "The 30 most liquid stocks on Borsa Istanbul. More concentrated = more volatile. Used for futures trading."},
    "sp500":          {"name": "S&P 500",               "group": "equities",   "key": "^GSPC",           "source": "market", "unit": "pts", "chartable": True,
                       "explain": "The US benchmark index. When S&P drops, EM markets like Turkey typically drop harder (risk-off)."},
    "dowjones":       {"name": "Dow Jones",             "group": "equities",   "key": "^DJI",            "source": "market", "unit": "pts", "chartable": True,
                       "explain": "Dow Jones Industrial Average — 30 large US companies. Price-weighted (not market-cap weighted like S&P)."},
    "nasdaq":         {"name": "NASDAQ Composite",      "group": "equities",   "key": "^IXIC",           "source": "market", "unit": "pts", "chartable": True,
                       "explain": "Tech-heavy US index. Sensitive to interest rates — when rates rise, growth/tech stocks suffer."},
    "dax":            {"name": "DAX (Germany)",         "group": "equities",   "key": "^GDAXI",          "source": "market", "unit": "pts", "chartable": True,
                       "explain": "Germany's main index. Important for Turkey because Germany is Turkey's largest trade partner."},
    "ftse":           {"name": "FTSE 100 (UK)",         "group": "equities",   "key": "^FTSE",           "source": "market", "unit": "pts", "chartable": True,
                       "explain": "UK's main stock index."},
    "nikkei":         {"name": "Nikkei 225 (Japan)",    "group": "equities",   "key": "^N225",           "source": "market", "unit": "pts", "chartable": True,
                       "explain": "Japan's main stock index."},
    "russell":        {"name": "Russell 2000",          "group": "equities",   "key": "^RUT",            "source": "market", "unit": "pts", "chartable": True,
                       "explain": "US small-cap index. Small caps are more sensitive to domestic economic conditions."},

    # ── FX ───────────────────────────────────────────────────────────
    "usdtry":         {"name": "USD/TRY",               "group": "fx",         "key": "TRY=X",           "source": "market", "unit": "",    "chartable": True,
                       "explain": "US Dollar to Turkish Lira. The single most important price in Turkey. Drives import costs, inflation expectations, and political stability."},
    "eurtry":         {"name": "EUR/TRY",               "group": "fx",         "key": "EURTRY=X",        "source": "market", "unit": "",    "chartable": True,
                       "explain": "Euro to Turkish Lira. Important because Europe is Turkey's largest trading partner."},
    "dxy":            {"name": "Dollar Index (DXY)",     "group": "fx",         "key": "DX-Y.NYB",        "source": "market", "unit": "",    "chartable": True,
                       "explain": "US Dollar strength vs a basket of 6 currencies. When DXY rises, EM currencies (including TRY) weaken."},
    "gbptry":         {"name": "GBP/TRY",               "group": "fx",         "key": "GBPTRY=X",        "source": "market", "unit": "",    "chartable": True,
                       "explain": "British Pound to Turkish Lira."},

    # ── COMMODITIES ──────────────────────────────────────────────────
    "gold":           {"name": "Gold (XAU/USD)",        "group": "commodities","key": "GC=F",            "source": "market", "unit": "$",   "chartable": True,
                       "explain": "Global gold price in USD. Turkish citizens are massive gold buyers — it's a traditional inflation hedge and store of value."},
    "gram_gold":      {"name": "Gram Gold (TRY)",       "group": "commodities","key": "gram_gold",       "source": "market", "unit": "₺",   "chartable": True,
                       "explain": "Gold price per gram in Turkish Lira (XAU/USD × USDTRY / 31.1035). The price Turkish citizens actually pay at the 'kuyumcu' (jeweler)."},
    "silver":         {"name": "Silver",                "group": "commodities","key": "SI=F",            "source": "market", "unit": "$",   "chartable": True,
                       "explain": "Silver price. More volatile than gold, with industrial demand component."},
    "oil_brent":      {"name": "Brent Crude Oil",       "group": "commodities","key": "BZ=F",            "source": "market", "unit": "$",   "chartable": True,
                       "explain": "Brent crude oil price. Turkey imports nearly ALL its oil — rising oil = wider current account deficit = weaker TRY."},
    "oil_wti":        {"name": "WTI Crude Oil",         "group": "commodities","key": "CL=F",            "source": "market", "unit": "$",   "chartable": True,
                       "explain": "US benchmark crude oil."},
    "natgas":         {"name": "Natural Gas",           "group": "commodities","key": "NG=F",            "source": "market", "unit": "$",   "chartable": True,
                       "explain": "Henry Hub natural gas price. Turkey imports most of its gas from Russia and Iran."},

    # ── CRYPTO ───────────────────────────────────────────────────────
    "btc":            {"name": "Bitcoin",               "group": "crypto",     "key": "BTC-USD",         "source": "market", "unit": "$",   "chartable": True,
                       "explain": "Bitcoin. Turkey has one of the highest crypto adoption rates globally, partly as a hedge against TRY depreciation."},
    "eth":            {"name": "Ethereum",              "group": "crypto",     "key": "ETH-USD",         "source": "market", "unit": "$",   "chartable": True,
                       "explain": "Ethereum. The second largest cryptocurrency by market cap."},

    # ── SCORECARD / COMPOSITE ────────────────────────────────────────
    "scorecard":      {"name": "Macro Scorecard",       "group": "scorecard",  "key": "composite",       "source": "scorecard", "unit": "",
                       "explain": "Composite macro score (-10 to +10) combining yield curve, real carry, PPI-CPI gap, and gold correlation signals. Below -5 = BEARISH, above +5 = BULLISH."},
    "gold_corr":      {"name": "Gold/TRY Correlation",  "group": "scorecard",  "key": "gold_corr",       "source": "gold_corr", "unit": "",
                       "explain": "3-month correlation between Gram Gold and USDTRY. High correlation (>0.8) = gold is just an FX hedge (Lira fear). Low correlation = gold has independent safe-haven appeal."},
}

# Build aliases for quick lookup (e.g., "inflation" matches all inflation group entities)
GROUP_ALIASES = {}
for key, entry in DATA_REGISTRY.items():
    g = entry["group"]
    if g not in GROUP_ALIASES:
        GROUP_ALIASES[g] = []
    GROUP_ALIASES[g].append(key)


def search_registry(query):
    """Fuzzy search across entity keys, names, and groups. Returns list of matches."""
    query = query.lower().strip().lstrip("@")
    if not query:
        return []

    results = []

    # Exact key match first
    if query in DATA_REGISTRY:
        results.append({"key": query, **DATA_REGISTRY[query], "match_type": "exact"})
        return results

    # Group match — e.g., "inflation" returns all inflation metrics
    if query in GROUP_ALIASES:
        for key in GROUP_ALIASES[query]:
            results.append({"key": key, **DATA_REGISTRY[key], "match_type": "group"})
        return results

    # Fuzzy: search key, name, group, explain
    for key, entry in DATA_REGISTRY.items():
        searchable = f"{key} {entry['name']} {entry['group']} {entry.get('explain', '')}".lower()
        if query in searchable:
            # Rank: key match > name match > explain match
            if query in key:
                score = 3
            elif query in entry["name"].lower():
                score = 2
            else:
                score = 1
            results.append({"key": key, **entry, "match_type": "fuzzy", "score": score})

    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:15]


def resolve_entity(key):
    """Return full entity info for a given key, or None if not found."""
    if key in DATA_REGISTRY:
        entry = dict(DATA_REGISTRY[key])
        entry["key"] = key
        return entry
    return None


def get_group_entities(group):
    """Return all entities in a group."""
    return [{"key": k, **v} for k, v in DATA_REGISTRY.items() if v["group"] == group]
