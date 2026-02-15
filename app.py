"""
Berke Yıldırım's Dashboard – Flask Backend
Serves the static dashboard and exposes JSON API endpoints.
"""
import os
from flask import Flask, jsonify, request, send_from_directory
from engine import (
    fetch_market_data,
    fetch_macro_data,
    fetch_movers,
    fetch_news,
    fetch_history,
    get_market_status,
    fetch_turkey_macro,
    fetch_cbrt_tracker,
    fetch_economic_calendar,
    fetch_equity_risk,
    fetch_distressed,
    fetch_gold_correlation,
    compute_scorecard,
    generate_daily_brief,
    synthesize_narrative,
    terminal_chat,
    get_context,
    save_ticket,
    get_tickets,
    search_registry,
    resolve_entity,
    get_group_entities,
    set_override,
    get_override,
    get_all_overrides,
    clear_override,
    ALL_TICKERS,
    TICKER_CATEGORIES,
    TICKER_TAPE_ORDER,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR)


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.route("/api/market")
def api_market():
    """All market data (indices, crypto, commodities, currencies, VIX)."""
    try:
        data = fetch_market_data()
    except Exception as e:
        print(f"[app] api_market error: {e}")
        data = {sym: {"symbol": sym, "name": ALL_TICKERS.get(sym, sym), "price": "N/A", "prev_close": "N/A", "change_pct": "N/A", "_source": "N/A"} for sym in ALL_TICKERS}
        data["GRAM_ALTIN"] = {"symbol": "GRAM_ALTIN", "name": "Gram Altın", "price": "N/A", "prev_close": "N/A", "change_pct": "N/A", "_source": "N/A"}
    return jsonify({
        "data": data,
        "categories": TICKER_CATEGORIES,
        "ticker_tape": TICKER_TAPE_ORDER,
        "names": {k: v for k, v in ALL_TICKERS.items()},
        "status": get_market_status(),
    })


@app.route("/api/macro")
def api_macro():
    """Macro data: policy rates, bond yields, VIX, Gram Altin."""
    data = fetch_macro_data()
    return jsonify(data)


@app.route("/api/movers")
def api_movers():
    """BIST top gainers and losers."""
    try:
        data = fetch_movers()
    except Exception as e:
        print(f"[app] api_movers error: {e}")
        data = {
            "bist30": {"gainers": [], "losers": [], "most_traded": []},
            "bist100": {"gainers": [], "losers": [], "most_traded": []},
            "_source": "N/A",
        }
    return jsonify(data)


@app.route("/api/news")
def api_news():
    """Aggregated RSS news."""
    data = fetch_news()
    return jsonify(data)


@app.route("/api/history")
def api_history():
    """OHLCV history for a single ticker (for charting).
    Query params: symbol (required), period (default 3mo).
    """
    symbol = request.args.get("symbol", "XU100.IS")
    period = request.args.get("period", "3mo")
    # Validate period
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
    if period not in valid_periods:
        period = "3mo"
    data = fetch_history(symbol, period)
    if data is None:
        return jsonify({"error": "No data available", "symbol": symbol}), 404
    return jsonify({"symbol": symbol, "period": period, "data": data})


@app.route("/api/symbols")
def api_symbols():
    """List all available symbols for the chart dropdown."""
    symbols = [{"symbol": k, "name": v} for k, v in ALL_TICKERS.items()]
    return jsonify(symbols)


@app.route("/api/turkey-macro")
def api_turkey_macro():
    """Comprehensive Turkey macro indicators."""
    data = fetch_turkey_macro()
    return jsonify(data)


@app.route("/api/cbrt")
def api_cbrt():
    """CBRT policy rate tracker with history."""
    data = fetch_cbrt_tracker()
    return jsonify(data)


@app.route("/api/calendar")
def api_calendar():
    """Upcoming economic events."""
    data = fetch_economic_calendar()
    return jsonify(data)


@app.route("/api/equity-risk")
def api_equity_risk():
    """Equity Risk Premium (ERP) metrics."""
    return jsonify(fetch_equity_risk())


@app.route("/api/distressed")
def api_distressed():
    """Fallen Angels (Down >20% from 3mo High)."""
    return jsonify(fetch_distressed())


@app.route("/api/gold-correlation")
def api_gold_correlation():
    """Gold/USD Correlations."""
    return jsonify(fetch_gold_correlation())


@app.route("/api/scorecard")
def api_scorecard():
    """Macro Risk Scorecard composite signal."""
    return jsonify(compute_scorecard())


@app.route("/api/brief")
def api_brief():
    """Auto-generated daily market brief."""
    data = generate_daily_brief()
    return jsonify(data)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Terminal Assistant chatbot endpoint."""
    j = request.json
    query = j.get("query")
    news_context = j.get("news", [])
    market_context = j.get("markets", {})
    chart_context = j.get("chartContext")
    
    response = terminal_chat(query, news_context, market_context, chart_context)
    return jsonify({"response": response})

@app.route("/api/knowledge/<key>")
def api_knowledge(key):
    """Textbook context for a specific concept."""
    data = get_context(key)
    return jsonify(data)


@app.route("/api/synthesis", methods=["POST"])
def api_synthesis():
    """AI narrative synthesis for a metric."""
    j = request.json
    concept = j.get("concept")
    value = j.get("value")
    unit = j.get("unit", "")
    headlines = j.get("headlines", [])
    
    narrative = synthesize_narrative(concept, value, unit, headlines)
    return jsonify({"narrative": narrative})


@app.route("/api/tickets", methods=["GET", "POST"])
def api_tickets():
    """Handle data quality tickets."""
    if request.method == "POST":
        j = request.json
        items = j.get("items", [])
        notes = j.get("notes", "")
        import json
        ticket_id = save_ticket(json.dumps(items), notes)
        return jsonify({"status": "ok", "ticket_id": ticket_id})
    else:
        tickets = get_tickets()
        return jsonify(tickets)


# ---------------------------------------------------------------------------
# Command Bar / Registry API
# ---------------------------------------------------------------------------
@app.route("/api/registry/search")
def api_registry_search():
    """Search the data registry for entities matching the query."""
    q = request.args.get("q", "")
    results = search_registry(q)
    return jsonify(results)


@app.route("/api/entity/<key>")
def api_entity(key):
    """Full entity info + current value + override status."""
    entity = resolve_entity(key)
    if not entity:
        return jsonify({"error": "Entity not found"}), 404
    # Check for override
    override = get_override(key)
    entity["override"] = override
    # Get related entities in same group
    related = get_group_entities(entity["group"])
    entity["related"] = [r for r in related if r["key"] != key]
    return jsonify(entity)


@app.route("/api/entity/<key>/set", methods=["POST"])
def api_entity_set(key):
    """Set a manual override for an entity."""
    entity = resolve_entity(key)
    if not entity:
        return jsonify({"error": "Entity not found"}), 404
    data = request.get_json(force=True)
    value = data.get("value")
    source = data.get("source", "manual")
    if value is None:
        return jsonify({"error": "No value provided"}), 400
    result = set_override(key, value, source)
    return jsonify({"ok": True, **result})


@app.route("/api/entity/<key>/clear", methods=["POST"])
def api_entity_clear(key):
    """Clear a manual override."""
    clear_override(key)
    return jsonify({"ok": True, "key": key})


@app.route("/api/overrides")
def api_overrides():
    """List all active manual overrides."""
    return jsonify(get_all_overrides())


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n  Berke Y\u0131ld\u0131r\u0131m's Dashboard \u2013 http://127.0.0.1:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
