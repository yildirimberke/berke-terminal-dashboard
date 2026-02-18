import feedparser
from bs4 import BeautifulSoup
from .cache import get_cached, set_cached
from .db import archive_news, get_recent_news
from collections import deque

# Set a browser-like User Agent to avoid being blocked
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

RSS_SOURCES = {
    "Bloomberg HT": "https://www.bloomberght.com/rss",
    "Investing TR": "https://tr.investing.com/rss/news.rss",
    "Dünya": "https://www.dunya.com/rss",
    "Reuters BIZ": "https://www.reutersagency.com/feed/?best-topics=business&post_type=best", 
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "MarketWatch": "https://www.marketwatch.com/rss/marketpulse",
}

def fetch_news():
    """Aggregate news from RSS feeds with source-balancing (Round Robin)."""
    cached = get_cached("news", ttl_seconds=300)
    if cached is not None: return cached

    all_fetched = []
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                summary = entry.get("summary", "") or entry.get("description", "")
                if "<" in summary:
                    summary = BeautifulSoup(summary, "lxml").get_text()
                summary = summary[:160].strip()
                if len(summary) == 160: summary += "..."
                
                import time
                ts_struct = entry.get("published_parsed") or entry.get("updated_parsed")
                if ts_struct:
                    ts_iso = time.strftime("%Y-%m-%d %H:%M:%S", ts_struct)
                else:
                    ts_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                all_fetched.append({
                    "source": name,
                    "title": entry.get("title", ""),
                    "summary": summary,
                    "link": entry.get("link", ""),
                    "time": ts_iso,
                })
        except Exception: pass
    
    if all_fetched:
        archive_news(all_fetched)
    
    # BALANCED RETRIEVAL:
    # 1. Fetch a large enough buffer from DB (e.g., 200 items)
    raw_history = get_recent_news(limit=200)
    
    # 2. Group by source
    by_source = {}
    for item in raw_history:
        s = item['source']
        if s not in by_source: by_source[s] = deque()
        by_source[s].append(item)
    
    # 3. Interleave (Round Robin) to ensure diversity at the top
    balanced = []
    sources_cycle = list(by_source.keys())
    
    while len(balanced) < 60 and sources_cycle:
        for s in list(sources_cycle):
            if by_source[s]:
                balanced.append(by_source[s].popleft())
            else:
                sources_cycle.remove(s)
            
            if len(balanced) >= 60: break

    set_cached("news", balanced)
    return balanced
