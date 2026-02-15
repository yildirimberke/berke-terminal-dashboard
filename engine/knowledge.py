# Deterministic Knowledge Base: "The Economics Lexicon"
# This file stores verified, textbook-grade definitions and relationships.
# It acts as the 'Ground Truth' for the terminal's educative mode.

KNOWLEDGE_BASE = {
    "CDS": {
        "full_name": "5-Year Credit Default Swap",
        "definition": "A financial derivative that allows an investor to 'swap' or offset their credit risk with that of another investor. It acts as insurance against a sovereign default.",
        "institutional_meaning": "A high CDS spread indicates the market perceives high risk in Turkey's ability to repay USD-denominated debt. For a bank, higher CDS means higher costs of external borrowing.",
        "relationships": {
            "USDTRY": "Strong positive correlation. When CDS rises (risk up), the Lira usually weakens (USDTRY up).",
            "BIST100": "Strong negative correlation. Risk spikes (CDS up) usually lead to equity sell-offs (BIST down).",
            "Spread": "CDS often tracks the 10Y Yield Spread, but with faster sensitivity to short-term political/geopolitical shocks."
        }
    },
    "real_rate": {
        "full_name": "Ex-Ante Real Interest Rate",
        "definition": "The interest rate a lender receives after accounting for expected inflation.",
        "formula": "Real Rate = Policy Rate - Expected Inflation",
        "institutional_meaning": "This is the primary driver of foreign 'Hot Money' inflows. If the Real Rate is negative, investors lose purchasing power by holding Lira, leading to currency pressure.",
        "relationships": {
            "USDTRY": "If Real Rates rise, it typically supports the Lira (lowers USDTRY) by making TRY assets more attractive."
        }
    },
    "VIX": {
        "full_name": "CBOE Volatility Index (The 'Fear Gauge')",
        "definition": "A measure of the stock market's expectation of volatility based on S&P 500 index options.",
        "institutional_meaning": "When VIX crosses above 20-25, international investors go into 'Risk-Off' mode, typically pulling money out of Emerging Markets like Turkey.",
        "relationships": {
            "BIST100": "Inverse. High VIX = Global fear = Lower BIST prices.",
            "CDS": "Positive. Global fear (VIX) often causes EM risk premiums (CDS) to rise."
        }
    },
    "aofm": {
        "full_name": "CBRT Average Cost of Funding (AOFM)",
        "definition": "The weighted average interest rate at which the Central Bank of Turkey provides liquidity to the banking system.",
        "institutional_meaning": "This is the 'Actual' policy rate. If AOFM rises above the official 1-week repo rate, it indicates 'hidden tightening' by the CBRT.",
        "relationships": {
            "Deposit Rate": "AOFM usually sets the floor for bank deposit rates.",
            "USDTRY": "Higher funding costs increase the carrying cost of USD or short-selling TRY, supporting the currency."
        }
    },
    "Spread": {
        "full_name": "10-Year Bond Yield Spread (TR vs US)",
        "definition": "The difference between Turkey's 10-year sovereign bond yield and the US 10-year Treasury yield.",
        "institutional_meaning": "This spread represents the 'Risk Premium' investors demand to hold Turkish debt over risk-free US debt. A widening spread indicates capital outflow from Turkey.",
        "relationships": {
            "CDS": "Usually move in tandem. Spread measures yield risk; CDS measures default risk.",
            "Foreign Flows": "Wider spread attracts 'Carry Traders' if inflation is stable, but repels 'Real Money' if it indicates macro instability."
        }
    },
    "deposit_rate": {
        "full_name": "Bank Deposit Interest Rate (Up to 3-Months)",
        "definition": "The interest rate banks offer to retail and corporate clients for Lira deposits.",
        "institutional_meaning": "This is the primary competitor to the stock market. If deposit rates are 40-50%, the BIST100 needs higher returns to attract capital.",
        "relationships": {
            "BIST100": "Inverse. Higher deposit rates drain liquidity from the equity market.",
            "Inflation": "Should ideally be higher than inflation to provide a positive real return."
        }
    },
    "TR_2Y": {
        "full_name": "Turkey 2-Year Benchmark Bond Yield",
        "definition": "The annual interest rate the Turkish Treasury pays to borrow money for a 2-year duration.",
        "institutional_meaning": "Reflects market expectations for CBRT interest rates and inflation over the next 24 months. Often called the 'Policy Sensitivity' yield.",
        "relationships": {
            "aofm": "Positive. If the Central Bank raises rates today, the 2Y yield usually jumps immediately.",
            "BIST100": "Inverse. Higher yields increase the discount rate for equity valuations, making stocks less attractive."
        }
    },
    "TR_10Y": {
        "full_name": "Turkey 10-Year Benchmark Bond Yield",
        "definition": "The annual yield on Turkey's long-term sovereign debt.",
        "institutional_meaning": "A key 'Anchor' for long-term borrowing costs in the country. It reflects long-term inflation expectations and fiscal sustainability.",
        "relationships": {
            "TR_2Y": "Yield Curve. If 10Y is lower than 2Y, the curve is 'inverted', often signaling a future recession or significant disinflation expectation.",
            "Spread": "Positive. Wide spreads vs US yields usually mean the 10Y TR yield is rising due to risk premiums."
        }
    },
    "US_10Y": {
        "full_name": "United States 10-Year Treasury Yield",
        "definition": "The yield on the 10-year US government bond, considered the global 'Risk-Free Rate'.",
        "institutional_meaning": "The most important number in global finance. When US yields rise, capital flows out of Emerging Markets (like Turkey) and back into the US dollar.",
        "relationships": {
            "CDS": "When US_10Y rises sharply, EM risk premiums (CDS) typically widen as dollar liquidity tightens.",
            "USDTRY": "Positive. Rising US yields strengthen the USD globally, putting pressure on the Lira."
        }
    },
    "commercial_loan": {
        "full_name": "Commercial Loan Interest Rate",
        "definition": "The average interest rate banks charge businesses for TRY-denominated corporate loans.",
        "institutional_meaning": "Measures the 'Transmission Mechanism'. If CBRT raises rates but loan rates stay low, policy isn't reaching the real economy. High loan rates slow down investment.",
        "relationships": {
            "GDP Growth": "Inverse. Very high commercial loan rates usually precede a slowdown in industrial production and overall growth."
        }
    },
    "cpi": {
        "full_name": "Consumer Price Index (Headline Inflation) YoY",
        "definition": "A measure that examines the weighted average of prices of a basket of consumer goods and services.",
        "institutional_meaning": "The ultimate yardstick for the CBRT. If CPI is trending above the target (currently 5%), rate cuts are impossible without risking currency instability.",
        "relationships": {
            "interest_rate": "Positive. Higher inflation forces the Central Bank to maintain higher interest rates.",
            "USDTRY": "Inverse. High inflation erodes the purchasing power of the Lira, leading to currency devaluation."
        }
    },
    "gdp_yoy": {
        "full_name": "Real GDP Growth (Year-over-Year)",
        "definition": "The inflation-adjusted measure of the value of all goods and services produced by the economy.",
        "institutional_meaning": "Turkey's 'Speed Limit' is roughly 4.5%. Growth significantly above this is usually fueled by debt and leading to high inflation.",
        "relationships": {
            "unemployment": "Inverse. Higher growth creates jobs and lowers the unemployment rate."
        }
    },
    "usdtry": {
        "full_name": "USD/TRY Exchange Rate",
        "definition": "The number of Turkish Liras required to purchase one US Dollar.",
        "institutional_meaning": "The most psychologically important price in Turkey. It drives the cost of imports (energy, tech) and impacts the inflation expectations of the entire population.",
        "relationships": {
            "cpi": "Direct Pass-through. In Turkey, roughly 20-30% of an exchange rate move passes into inflation within 6 months."
        }
    },
    "fx_reserves": {
        "full_name": "CBRT Gross Foreign Exchange Reserves",
        "definition": "Total foreign currency assets held by the Central Bank of Turkey.",
        "institutional_meaning": "The country's 'Defense Shield'. High reserves provide confidence to foreign investors that Turkey can meet its external debt obligations.",
        "relationships": {
            "CDS": "Inverse. Rising reserves lead to lower CDS (lower perceived risk)."
        }
    },
    "current_account": {
        "full_name": "Current Account Balance",
        "definition": "The difference between a country's savings and its investment, largely driven by the trade balance.",
        "institutional_meaning": "A persistent deficit means Turkey is consuming more than it produces, requiring foreign capital inflows (Hot Money or FDI) to balance the books.",
        "relationships": {
            "fx_reserves": "A large deficit usually drains FX reserves unless offset by financial inflows."
        }
    },
    "interest_rate": {
        "full_name": "CBRT One-Week Repo Auction Rate",
        "definition": "The official policy rate of the Central Bank of the Republic of Turkey.",
        "institutional_meaning": "The 'Cost of Money'. It is the primary tool used to control inflation and stabilize the currency.",
        "relationships": {
            "deposit_rate": "Positive. Bank deposit rates usually track the repo rate with a small lag."
        }
    },
    "gram_altin": {
        "full_name": "Gram Gold (TRY)",
        "definition": "The price of one gram of gold in Turkish Lira.",
        "institutional_meaning": "The traditional 'Safe Haven' for Turkish households. It protects against both global gold price volatility and Lira devaluation.",
        "relationships": {
            "usdtry": "Positive. Gram gold rises if the Lira weakens, even if global gold prices stay flat."
        }
    }
}

def get_context(key):
    """Safely retrieve deterministic context for a given metric."""
    return KNOWLEDGE_BASE.get(key, {
        "full_name": key,
        "definition": "Context documentation for this metric is being indexed.",
        "institutional_meaning": "Monitoring for volatility and deviations from historical norms.",
        "relationships": {}
    })
