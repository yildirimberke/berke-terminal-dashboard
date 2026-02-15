import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
from .config import ALL_TICKERS, CONFIG
from .cache import get_cached, set_cached
from .db import archive_market_snapshot

def fetch_market_data():
    """Batch-fetch all tickers via yfinance. Returns dict keyed by symbol."""
    cached = get_cached("market", ttl_seconds=15)
    if cached is not None:
        return cached

    symbols = list(ALL_TICKERS.keys())
    result = {}

    try:
        ticker_dfs = _yf_download_batched(symbols, chunk_size=10, pause=0.4)
        for sym in symbols:
            try:
                ticker_df = ticker_dfs.get(sym)

                if ticker_df is None or ticker_df.empty or len(ticker_df) < 1:
                    result[sym] = _fetch_single_ticker_fast(sym)
                    continue

                last = ticker_df.iloc[-1]
                price = float(last["Close"])
                if len(ticker_df) >= 2:
                    prev_close = float(ticker_df.iloc[-2]["Close"])
                else:
                    prev_close = float(last["Open"]) if "Open" in last else price

                change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0

                if pd.isna(price) or pd.isna(prev_close) or pd.isna(change_pct) or price <= 0:
                    result[sym] = _fetch_single_ticker_fast(sym)
                else:
                    result[sym] = {
                        "symbol": sym,
                        "name": ALL_TICKERS.get(sym, sym),
                        "price": round(price, 2),
                        "prev_close": round(prev_close, 2),
                        "change_pct": round(change_pct, 2),
                        "_source": "YFINANCE",
                    }
            except Exception:
                result[sym] = _fetch_single_ticker_fast(sym)
    except Exception as e:
        print(f"[engine.market] yf.download error: {e}")
        for sym in symbols:
            result[sym] = _fetch_single_ticker_fast(sym)

    # Gram Altin Calculation
    try:
        usdtry = result.get("USDTRY=X", {}).get("price")
        gold_oz = result.get("GC=F", {}).get("price")
        if isinstance(usdtry, (int, float)) and isinstance(gold_oz, (int, float)):
            price_gram = (gold_oz * usdtry) / 31.1035
            # We assume change_pct for Gram Altin is roughly reflected by the combo
            # Simplification: use the calculated price
            result["GRAM_ALTIN"] = {
                "symbol": "GRAM_ALTIN",
                "name": "Gram Altın",
                "price": round(price_gram, 2),
                "prev_close": result.get("GRAM_ALTIN", {}).get("prev_close", "N/A"), # Placeholder
                "change_pct": 0, # To be improved
                "_source": "CALC",
            }
    except Exception:
        pass

    has_any_price = any(result.get(s, {}).get("price") != "N/A" for s in result)
    if has_any_price:
        set_cached("market", result)
        archive_market_snapshot(result)
    return result

def _fetch_single_ticker_fast(sym):
    """Fallback method using Ticker.fast_info for reliable single-point data."""
    try:
        t = yf.Ticker(sym)
        info = t.fast_info
        price = info.last_price
        prev_close = info.previous_close or price

        if pd.isna(price) or price <= 0:
            return _na_entry(sym)

        change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0

        return {
            "symbol": sym,
            "name": ALL_TICKERS.get(sym, sym),
            "price": round(price, 2),
            "prev_close": round(prev_close, 2),
            "change_pct": round(change_pct, 2),
            "_source": "YFINANCE:FAST",
        }
    except Exception:
        return _na_entry(sym)

def _na_entry(sym):
    return {
        "symbol": sym,
        "name": ALL_TICKERS.get(sym, sym),
        "price": "N/A",
        "prev_close": "N/A",
        "change_pct": "N/A",
        "_source": "N/A",
    }

def _yf_download_batched(symbols, chunk_size=10, pause=0.4):
    merged = {}
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i : i + chunk_size]
        if not chunk: continue
        try:
            df = yf.download(chunk, period="2d", group_by="ticker", threads=False, progress=False, auto_adjust=True, timeout=15)
            part = _yf_get_ticker_dfs(df, chunk)
            merged.update(part)
        except Exception as e:
            print(f"[engine.market] yf batch error ({chunk[0]}...): {e}")
        if i + chunk_size < len(symbols) and pause > 0:
            time.sleep(pause)
    return merged

def _yf_get_ticker_dfs(df, symbols):
    out = {}
    if df is None or df.empty: return out
    if len(symbols) == 1:
        sym = symbols[0]
        if isinstance(df.columns, pd.MultiIndex):
            if sym in df.columns.get_level_values(0): out[sym] = _yf_flatten_ticker_df(df[sym].copy())
            elif sym in df.columns.get_level_values(1): out[sym] = _yf_flatten_ticker_df(df.xs(sym, axis=1, level=1).copy())
        else:
            out[sym] = _yf_flatten_ticker_df(df.copy())
        return out
    if not isinstance(df.columns, pd.MultiIndex): return out
    level0 = df.columns.get_level_values(0)
    level1 = df.columns.get_level_values(1)
    for sym in symbols:
        if sym in level0: out[sym] = _yf_flatten_ticker_df(df[sym].copy())
        elif sym in level1: out[sym] = _yf_flatten_ticker_df(df.xs(sym, axis=1, level=1).copy())
    return out

def _yf_flatten_ticker_df(ticker_df):
    if ticker_df is None or ticker_df.empty: return ticker_df
    if isinstance(ticker_df.columns, pd.MultiIndex):
        ticker_df = ticker_df.copy()
        ticker_df.columns = ticker_df.columns.get_level_values(ticker_df.columns.nlevels - 1)
    if "Close" not in ticker_df.columns and "Adj Close" in ticker_df.columns:
        ticker_df = ticker_df.copy()
        ticker_df["Close"] = ticker_df["Adj Close"]
    return ticker_df

def fetch_movers():
    cached = get_cached("movers", ttl_seconds=120)
    if cached is not None: return cached
    empty = {"gainers": [], "losers": [], "most_traded": []}
    result = {"bist30": dict(empty), "bist100": dict(empty), "_source": "YFINANCE"}
    bist30_tickers = CONFIG.get("bist_components", {}).get("bist30", [])
    bist100_extra = CONFIG.get("bist_components", {}).get("bist100_extra", [])
    bist100_tickers = bist30_tickers + bist100_extra
    try:
        result["bist30"] = _calc_movers_for_index(bist30_tickers)
        result["bist100"] = _calc_movers_for_index(bist100_tickers)
    except Exception as e:
        print(f"[engine.market] Movers error: {e}")
    has_any = (result["bist30"]["gainers"] or result["bist100"]["gainers"])
    if has_any: set_cached("movers", result)
    return result

def _calc_movers_for_index(ticker_list):
    if not ticker_list: return {"gainers": [], "losers": [], "most_traded": []}
    yf_symbols = [t + ".IS" for t in ticker_list]
    ticker_dfs = _yf_download_batched(yf_symbols, chunk_size=25, pause=0.5)
    stocks = []
    for sym in yf_symbols:
        try:
            ticker_df = ticker_dfs.get(sym)
            if ticker_df is None or ticker_df.empty or len(ticker_df) < 1:
                info = _fetch_single_ticker_fast(sym)
                if info["price"] != "N/A":
                    stocks.append({
                        "symbol": info["symbol"], "price": f"{info['price']:.2f}",
                        "change": f"{info['change_pct']:.2f}", "change_val": info["change_pct"],
                        "volume": "0", "volume_val": 0,
                    })
                continue
            last = ticker_df.iloc[-1]
            price = float(last["Close"])
            volume = int(last["Volume"]) if "Volume" in last and not pd.isna(last["Volume"]) else 0
            prev_close = float(ticker_df.iloc[-2]["Close"]) if len(ticker_df) >= 2 else float(last["Open"]) if "Open" in last else price
            if pd.isna(price) or pd.isna(prev_close) or prev_close == 0:
                info = _fetch_single_ticker_fast(sym)
                if info["price"] != "N/A":
                    stocks.append({
                        "symbol": info["symbol"], "price": f"{info['price']:.2f}",
                        "change": f"{info['change_pct']:.2f}", "change_val": info["change_pct"],
                        "volume": "0", "volume_val": 0,
                    })
                continue
            change_pct = round(((price - prev_close) / prev_close) * 100, 2)
            stocks.append({
                "symbol": sym.replace(".IS", ""), "price": f"{price:.2f}",
                "change": f"{change_pct:.2f}", "change_val": change_pct,
                "volume": f"{volume:,}", "volume_val": volume,
            })
        except Exception:
            continue
    sorted_by_change = sorted(stocks, key=lambda x: x["change_val"], reverse=True)
    sorted_by_vol = sorted(stocks, key=lambda x: x["volume_val"], reverse=True)
    _clean = lambda item: {"symbol": item["symbol"], "price": item["price"], "change": item["change"], "volume": item["volume"]}
    return {
        "gainers": [_clean(s) for s in sorted_by_change if s["change_val"] > 0][:10],
        "losers": [_clean(s) for s in reversed(sorted_by_change) if s["change_val"] < 0][:10],
        "most_traded": [_clean(s) for s in sorted_by_vol][:10]
    }

def fetch_history(symbol, period="3mo"):
    cached_key = f"hist_{symbol}_{period}"
    cached = get_cached(cached_key, ttl_seconds=1800)
    if cached is not None: return cached
    try:
        t = yf.Ticker(symbol); interval = "1d"
        if period == "1d": interval = "5m"
        elif period == "5d": interval = "1h"
        df = t.history(period=period, interval=interval)
        if df.empty: return None
        df = _yf_flatten_ticker_df(df)
        data = [{"time": int(i.timestamp()), "open": float(r["Open"]), "high": float(r["High"]), "low": float(r["Low"]), "close": float(r["Close"]), "volume": int(r["Volume"])} for i, r in df.iterrows()]
        set_cached(cached_key, data)
        return data
    except Exception: return None


def get_market_status():
    from datetime import datetime, time as dt_time
    import pytz
    
    now_utc = datetime.now(pytz.utc)
    
    # Istanbul (UTC+3)
    tz_ist = pytz.timezone('Europe/Istanbul')
    now_ist = now_utc.astimezone(tz_ist)
    bist_open = False
    if now_ist.weekday() < 5 and dt_time(9, 55) <= now_ist.time() <= dt_time(18, 10):
        bist_open = True
        
    # New York (UTC-4/5)
    tz_ny = pytz.timezone('America/New_York')
    now_ny = now_utc.astimezone(tz_ny)
    ny_open = False
    if now_ny.weekday() < 5 and dt_time(9, 30) <= now_ny.time() <= dt_time(16, 0):
        ny_open = True
        
    # London (UTC+0/1)
    tz_ln = pytz.timezone('Europe/London')
    now_ln = now_utc.astimezone(tz_ln)
    ln_open = False
    if now_ln.weekday() < 5 and dt_time(8, 0) <= now_ln.time() <= dt_time(16, 30):
        ln_open = True
        
    # Shanghai (UTC+8) - Simplified (09:30-15:00 with lunch break, ignoring lunch for simplicity)
    tz_sh = pytz.timezone('Asia/Shanghai')
    now_sh = now_utc.astimezone(tz_sh)
    sh_open = False
    if now_sh.weekday() < 5 and dt_time(9, 30) <= now_sh.time() <= dt_time(15, 0):
        sh_open = True

    return {
        "ist": {"label": "IST", "status": "OPEN" if bist_open else "CLOSED", "time": now_ist.strftime("%H:%M"), "is_open": bist_open},
        "ny":  {"label": "NY",  "status": "OPEN" if ny_open else "CLOSED",   "time": now_ny.strftime("%H:%M"), "is_open": ny_open},
        "ln":  {"label": "LDN", "status": "OPEN" if ln_open else "CLOSED",   "time": now_ln.strftime("%H:%M"), "is_open": ln_open},
        "sh":  {"label": "SHA", "status": "OPEN" if sh_open else "CLOSED",   "time": now_sh.strftime("%H:%M"), "is_open": sh_open},
    }

def fetch_distressed():
    """Identify stocks down > 20% from 3-month high."""
    cached = get_cached("distressed", ttl_seconds=3600)
    if cached is not None: return cached

    bist30 = CONFIG.get("bist_components", {}).get("bist30", [])
    bist100_extra = CONFIG.get("bist_components", {}).get("bist100_extra", [])
    tickers = [t + ".IS" for t in (bist30 + bist100_extra)]
    
    distressed = []
    # Batch fetch 3mo history (small chunks to avoid timeout)
    chunk_size = 20
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i: i+chunk_size]
        try:
            data = yf.download(chunk, period="3mo", group_by="ticker", threads=False, progress=False, auto_adjust=True)
            for sym in chunk:
                try:
                    df = _yf_get_ticker_dfs(data, [sym]).get(sym)
                    if df is None or df.empty: continue
                    
                    high_3mo = df["High"].max()
                    current = df["Close"].iloc[-1]
                    
                    if high_3mo > 0:
                        drawdown = ((current - high_3mo) / high_3mo) * 100
                        if drawdown < -20:
                            distressed.append({
                                "symbol": sym.replace(".IS", ""),
                                "price": f"{current:.2f}",
                                "high_3mo": f"{high_3mo:.2f}",
                                "drawdown": f"{drawdown:.2f}%",
                                "val": drawdown
                            })
                except Exception: pass
        except Exception: pass
        time.sleep(0.5)

    distressed.sort(key=lambda x: x["val"]) # sort by biggest drop
    result = distressed[:15] # Top 15 worst
    set_cached("distressed", result)
    return result

def fetch_gold_correlation():
    """Calculate 3-month correlation: Gram Gold vs USDTRY and Gram Gold vs XAUUSD."""
    cached = get_cached("gold_corr", ttl_seconds=3600)
    if cached is not None: return cached
    
    try:
        # Fetch 3mo history for XAUUSD (GC=F) and USDTRY (TRY=X)
        tickers = ["GC=F", "TRY=X"]
        df = yf.download(tickers, period="3mo", interval="1d", group_by="ticker", threads=False, progress=False, auto_adjust=True)
        
        # Extract Close series
        try:
            gold = df["GC=F"]["Close"] if "GC=F" in df else df[("GC=F", "Close")]
            usd = df["TRY=X"]["Close"] if "TRY=X" in df else df[("TRY=X", "Close")]
        except KeyError:
            # Handle flattened columns fallback if yfinance behavior varies
            if "GC=F" in df.columns: gold = df["GC=F"] # if simple Index
            elif "Close" in df.columns: # unlikely if group_by used
                pass
            print("[market] Gold correlation data shape error"); return {}

        # Align dates
        data = pd.DataFrame({"gold": gold, "usd": usd}).dropna()
        
        # Calculate Gram Gold History: (Gold * USD) / 31.1035
        data["gram"] = (data["gold"] * data["usd"]) / 31.1035
        
        # Correlations
        corr_usd = data["gram"].corr(data["usd"])
        corr_gold = data["gram"].corr(data["gold"])
        
        res = {
            "corr_usd": round(corr_usd, 2),
            "corr_gold": round(corr_gold, 2),
            "period": "3mo"
        }
        set_cached("gold_corr", res)
        return res

    except Exception as e:
        print(f"[engine.market] Gold corr error: {e}")
        return {}
