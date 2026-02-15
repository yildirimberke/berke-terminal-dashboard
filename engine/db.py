import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "terminal.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # News Archive
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            source TEXT,
            timestamp DATETIME,
            link TEXT,
            summary TEXT,
            UNIQUE(title, source)
        )
    ''')
    
    # Market Snapshots
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            symbol TEXT,
            price REAL,
            change_pct REAL
        )
    ''')
    
    # Data Quality Tickets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            items_json TEXT,
            status TEXT DEFAULT 'open',
            notes TEXT
        )
    ''')
    
    # Data Overrides (manual data entry)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_key TEXT UNIQUE,
            value TEXT,
            source TEXT DEFAULT 'manual',
            set_by TEXT DEFAULT 'user',
            timestamp DATETIME,
            active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

def set_override(key, value, source="manual"):
    """Store or update a manual data override."""
    conn = get_db_connection()
    cursor = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO data_overrides (entity_key, value, source, set_by, timestamp, active)
        VALUES (?, ?, ?, 'user', ?, 1)
        ON CONFLICT(entity_key) DO UPDATE SET
            value=excluded.value, source=excluded.source,
            timestamp=excluded.timestamp, active=1
    ''', (key, str(value), source, ts))
    conn.commit()
    conn.close()
    return {"key": key, "value": value, "source": source, "timestamp": ts}

def get_override(key):
    """Get an active override for a key, or None."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM data_overrides WHERE entity_key = ? AND active = 1', (key,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_overrides():
    """Get all active overrides."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM data_overrides WHERE active = 1 ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_override(key):
    """Deactivate an override."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE data_overrides SET active = 0 WHERE entity_key = ?', (key,))
    conn.commit()
    conn.close()
    return True

def archive_news(news_list):
    """Save a list of news items to the database, skipping duplicates."""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    for item in news_list:
        try:
            # RSS timestamps can be messy, ensure we have a datetime
            ts = item.get("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            cursor.execute('''
                INSERT OR IGNORE INTO news (title, source, timestamp, link, summary)
                VALUES (?, ?, ?, ?, ?)
            ''', (item['title'], item.get('source', 'Unknown'), ts, item.get('link', ''), item.get('summary', '')))
            if cursor.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"[DB] Error archiving news: {e}")
    
    conn.commit()
    conn.close()
    return count

def get_recent_news(limit=50):
    """Retrieve the most recent news from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def archive_market_snapshot(snapshot):
    """Save market prices to history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for symbol, data in snapshot.items():
        if isinstance(data, dict) and 'price' in data:
            cursor.execute('''
                INSERT INTO market_snapshots (timestamp, symbol, price, change_pct)
                VALUES (?, ?, ?, ?)
            ''', (ts, symbol, data.get('price'), data.get('change_pct')))
    conn.commit()
    conn.close()

def search_news(query_text, limit=15):
    """Simple keyword search in the news archive."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Simple case-insensitive search
    cursor.execute('''
        SELECT * FROM news 
        WHERE title LIKE ? OR summary LIKE ? 
        ORDER BY timestamp DESC LIMIT ?
    ''', (f'%{query_text}%', f'%{query_text}%', limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_top_movers_by_date(date_str, limit=5):
    """Retrieve top gainers and losers for a specific date (YYYY-MM-DD)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search for snapshots on that date
    # market_snapshots: timestamp, symbol, price, change_pct
    date_pattern = f"{date_str}%"
    
    # Gainers
    cursor.execute('''
        SELECT symbol, price, change_pct FROM market_snapshots 
        WHERE timestamp LIKE ? AND change_pct > 0
        ORDER BY change_pct DESC LIMIT ?
    ''', (date_pattern, limit))
    gainers = [dict(r) for r in cursor.fetchall()]
    
    # Losers
    cursor.execute('''
        SELECT symbol, price, change_pct FROM market_snapshots 
        WHERE timestamp LIKE ? AND change_pct < 0
        ORDER BY change_pct ASC LIMIT ?
    ''', (date_pattern, limit))
    losers = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {"gainers": gainers, "losers": losers}

def save_ticket(items_json, notes=""):
    """Store a digital quality ticket."""
    conn = get_db_connection()
    cursor = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO data_tickets (timestamp, items_json, status, notes)
        VALUES (?, ?, 'open', ?)
    ''', (ts, items_json, notes))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_tickets(limit=10):
    """Retrieve recent data quality tickets."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM data_tickets ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Initialize on import
if not os.path.exists(DB_PATH):
    init_db()
else:
    # Always try to ensure tables exist in case of schema updates
    init_db()
