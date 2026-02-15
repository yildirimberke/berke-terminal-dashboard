import requests
import os
import json
from datetime import datetime, timedelta
from .cache import get_cached, set_cached
from .db import search_news, get_top_movers_by_date, get_tickets

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def synthesize_narrative(concept_name, value, unit, news_headlines):
    """
    Generate a professional economic narrative using Groq Cloud.
    Anchors the AI to provided facts to prevent hallucination.
    """
    if not GROQ_API_KEY:
        return "AI Narrative Synthesis offline: API Key missing."

    system_prompt = (
        "You are a specialized Economic Research Analyst for a high-density financial terminal. "
        "Your task is to provide a concise, professional narrative explaining a specific market metric. "
        "STRICT RULES:\n"
        "1. DO NOT change or hallucinate any numbers. Only use the provided 'Current Value'.\n"
        "2. Anchoring: Synthesize the relationship between the metric and the provided headlines.\n"
        "3. Tone: Institutional, precise, and objective (Bloomberg-style).\n"
        "4. Format: 2-3 short sentences. Markdown-lite.\n"
        "5. Language: Primarily English, but preserve Turkish institutional terms if relevant."
    )

    headlines_text = "\n".join([f"- {h['title']} ({h.get('source','Unknown')})" for h in news_headlines[:5]])
    
    user_prompt = (
        f"Metric: {concept_name}\n"
        f"Current Value: {value} {unit}\n\n"
        f"Recent Relevant Headlines:\n{headlines_text}\n\n"
        f"Synthesis Task: Explain how these headlines relate to the current level of {concept_name}."
    )

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 200
    }

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[Research Engine] Synthesis Error: {e}")
        return "Narrative synthesis is currently being recalibrated."

def terminal_chat(query, news_context, market_context, chart_context=None):
    """
    General purpose market assistant chat using Groq.
    Injects recent market headlines, indices and chart data into the context.
    """
    if not GROQ_API_KEY:
        return "Chat system offline. API Key is missing from environment."

    system_prompt = (
        "You are 'Terminal Assistant', a professional financial AI built into Berke Yıldırım's Dashboard. "
        "You have access to real-time headlines, market prices, and historical chart data.\n\n"
        "STRICT BEHAVIOR:\n"
        "1. Focus: Be concise, analytical, and objective. Think like a Bloomberg analyst.\n"
        "2. Context Usage: Use news, market snapshot, and the provided chart data to answer.\n"
        "3. Technical Analysis: If chart data is provided, analyze trends (higher highs/lower lows), "
        "volatility, and price ranges. Don't just give generic advice; give numbers-based insights.\n"
        "4. No Hallucinations: If data is missing, say 'Data for that specific range/instrument is not in my current buffer'.\n"
        "5. Tone: Institutional but helpful. Markdown formatting encouraged.\n"
        "6. Language: Answer in the same language as the user query."
    )

    # Format context for AI
    headlines = "\n".join([f"- {h['title']} ({h.get('source','N/A')})" for h in news_context[:12]])
    markets = json.dumps(market_context, indent=2)
    
    chart_info = ""
    if chart_context and chart_context.get("data"):
        data_points = chart_context["data"]
        sym = chart_context.get("symbol", "Instrument")
        per = chart_context.get("period", "Period")
        
        # Simple stats for prompt
        closes = [d["close"] for d in data_points]
        first, last = closes[0], closes[-1]
        hi, lo = max(closes), min(closes)
        chg = ((last - first) / first) * 100
        
        # Sample points to not blow up context
        sampled = data_points[::max(1, len(data_points)//15)]
        sampled_str = "\n".join([f"{d.get('time_label','Pt')}: {d['close']:.2f}" for d in sampled])
        
        chart_info = (
            f"\n--- {sym} {per} CHART DATA ---\n"
            f"Range: {lo:.2f} to {hi:.2f}\n"
            f"Start: {first:.2f} -> End: {last:.2f} ({chg:+.2f}%)\n"
            f"Sampled Series:\n{sampled_str}\n"
        )

    # If query mentions "missed", "past", "history", "trace back", or "yesterday"...
    # We trigger a search-augmented retrieval
    historical_context = ""
    trigger_words = ["missed", "past", "history", "trace", "yesterday", "since", "last time", "daha önce", "geçmiş"]
    if any(w in query.lower() for w in trigger_words):
        # Extract keywords (simple split for now, could be improved)
        # Search for a few variations
        hits = []
        words = [w for w in query.split() if len(w) > 3]
        for word in words[:3]:
            hits.extend(search_news(word, limit=5))
        
        if hits:
            # Deduplicate by title
            unique_hits = {h['title']: h for h in hits}.values()
            hist_str = "\n".join([f"- {h['title']} ({h['timestamp']})" for h in unique_hits])
            historical_context = f"\n--- ARCHIVED NEWS (TRACED BACK) ---\n{hist_str}\n"

    # If query mentions "best", "worst", "gainers", "losers", "performers"
    perf_context = ""
    perf_trigger = ["best", "worst", "gainer", "loser", "performer", "anomaly", "en çok"]
    if any(w in query.lower() for w in perf_trigger):
        # Determine target date
        target_date = datetime.now()
        if "yesterday" in query.lower():
            target_date -= timedelta(days=1)
        elif "friday" in query.lower():
            # Simple weekday logic
            days_back = (target_date.weekday() - 4) % 7
            if days_back == 0: days_back = 7
            target_date -= timedelta(days=days_back)
        
        date_str = target_date.strftime("%Y-%m-%d")
        perf_data = get_top_movers_by_date(date_str)
        
        if perf_data["gainers"] or perf_data["losers"]:
            gainers_str = ", ".join([f"{s['symbol']} ({s['change_pct']:+.2f}%)" for s in perf_data["gainers"]])
            losers_str = ", ".join([f"{s['symbol']} ({s['change_pct']:+.2f}%)" for s in perf_data["losers"]])
            perf_context = (
                f"\n--- PERFORMANCE DATA FOR {date_str} ---\n"
                f"Top Gainers: {gainers_str}\n"
                f"Top Losers: {losers_str}\n"
            )
        else:
            # Fallback for "today" if no data archived yet
            perf_context = "\n--- PERFORMANCE DATA ---\n(Live movers in snapshot above)\n"

    # If query mentions "ticket", "bug", "issue", "report", "flagged"
    ticket_context = ""
    ticket_trigger = ["ticket", "bug", "issue", "report", "flagged", "hatalı", "sorun"]
    if any(w in query.lower() for w in ticket_trigger):
        tickets = get_tickets(limit=5)
        if tickets:
            t_str = "\n".join([f"- Ticket #{t['id']} [{t['timestamp']}]: {t['items_json']} (Status: {t['status']})" for t in tickets])
            ticket_context = f"\n--- DATA QUALITY TICKETS (RECENT) ---\n{t_str}\n"
        else:
            ticket_context = "\n--- DATA QUALITY TICKETS ---\nNo open tickets found in archive.\n"

    user_prompt = (
        f"LATEST MARKET CONTEXT:\n"
        f"--- CURRENT HEADLINES ---\n{headlines}\n\n"
        f"--- MARKET SNAPSHOT ---\n{markets}\n\n"
        f"{chart_info}"
        f"{historical_context}"
        f"{perf_context}"
        f"{ticket_context}\n"
        f"USER QUERY: {query}"
    )

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[Research Engine] Chat Error: {e}")
        return "The Research Desk is currently experiencing high volume. Please try your query again in a moment."

def generate_daily_brief():
    """Build a daily market summary from live data. No hallucination."""
    cached = get_cached("brief", ttl_seconds=120)
    if cached is not None:
        return cached

    # Avoid circular imports by importing inside function
    from .market import fetch_market_data
    from .macro import fetch_macro_data
    from .macro import fetch_economic_calendar

    market = fetch_market_data()
    macro = fetch_macro_data()

    now = datetime.utcnow() + timedelta(hours=3)
    lines = []

    # --- Turkey line ---
    bist = market.get("XU100.IS", {})
    usdtry = market.get("USDTRY=X", {})
    gram = market.get("GRAM_ALTIN", {})
    rates = macro.get("policy_rates", {})

    bist_price = bist.get("price", "N/A")
    bist_chg = bist.get("change_pct", "N/A")
    tr_line = f"BIST 100 at {_fmt(bist_price)} ({_sign(bist_chg)})"
    tr_line += f" | USDTRY {_fmt(usdtry.get('price', 'N/A'))}"
    tr_line += f" | Gram Altin {_fmt(gram.get('price', 'N/A'))} TRY"
    tr_line += f" | AOFM {rates.get('aofm', 'N/A')}%"
    lines.append(("TURKEY", tr_line))

    # --- Global line ---
    sp = market.get("^GSPC", {})
    dji = market.get("^DJI", {})
    vix = market.get("^VIX", {})
    oil = market.get("BZ=F", {})
    gold = market.get("GC=F", {})
    bonds = macro.get("bonds", {})
    gl_line = f"S&P 500 {_fmt(sp.get('price','N/A'))} ({_sign(sp.get('change_pct','N/A'))})"
    gl_line += f" | DJI {_fmt(dji.get('price','N/A'))} ({_sign(dji.get('change_pct','N/A'))})"
    gl_line += f" | US 10Y {bonds.get('us_10y','N/A')}%"
    gl_line += f" | VIX {_fmt(vix.get('price','N/A'))}"
    gl_line += f" | Oil ${_fmt(oil.get('price','N/A'))}"
    gl_line += f" | Gold ${_fmt(gold.get('price','N/A'))}"
    lines.append(("GLOBAL", gl_line))

    # --- Watch line ---
    calendar = fetch_economic_calendar()
    upcoming = calendar[:3]
    if upcoming:
        watch_parts = [f"{e['event']} ({e['date']})" for e in upcoming]
        lines.append(("WATCH", " | ".join(watch_parts)))

    # --- Scorecard line ---
    try:
        from .scorecard import compute_scorecard
        sc = compute_scorecard()
        if sc and sc.get("signal"):
            sc_line = f"Signal: {sc['signal']} (Score: {sc['composite']})"
            details = []
            for key, info in sc.get("scores", {}).items():
                details.append(f"{key}: {info['signal']}")
            if details:
                sc_line += " | " + " | ".join(details[:4])
            lines.append(("RISK", sc_line))
    except Exception:
        pass

    result = {"lines": lines, "timestamp": now.strftime("%Y-%m-%d %H:%M")}
    set_cached("brief", result)
    return result

def _fmt(val):
    if val == "N/A" or val is None:
        return "N/A"
    if isinstance(val, (int, float)):
        if abs(val) >= 10000:
            return f"{val:,.2f}"
        return f"{val:.2f}"
    return str(val)

def _sign(val):
    if val == "N/A" or val is None:
        return "N/A"
    if isinstance(val, (int, float)):
        s = "+" if val >= 0 else ""
        return f"{s}{val:.2f}%"
    return str(val)
