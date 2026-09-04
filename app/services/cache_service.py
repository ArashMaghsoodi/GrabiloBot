import json
import sqlite3
import time
from typing import Optional, Dict, Any
from app.config import config


class CacheService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or config.db_path)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Media info cache table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS media_info_cache (
                    url_key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            # Telegram file_id cache table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telegram_file_cache (
                    cache_key TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    caption TEXT,
                    created_at INTEGER NOT NULL
                )
                """
            )
            # User rate limit tracking
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_rate_limits (
                    user_id INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_user ON user_rate_limits(user_id, timestamp)")
            conn.commit()

    # Metadata Cache
    def get_media_info(self, url: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data, created_at FROM media_info_cache WHERE url_key = ?", (url,))
            row = cursor.fetchone()
            if row:
                data_str, created_at = row
                if time.time() - created_at < config.cache_ttl:
                    return json.loads(data_str)
                else:
                    cursor.execute("DELETE FROM media_info_cache WHERE url_key = ?", (url,))
                    conn.commit()
        return None

    def set_media_info(self, url: str, data: Dict[str, Any]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            cursor.execute(
                "INSERT OR REPLACE INTO media_info_cache (url_key, data, created_at) VALUES (?, ?, ?)",
                (url, json.dumps(data), now),
            )
            conn.commit()

    # Telegram File Cache
    def get_telegram_file(self, cache_key: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_id, file_type, caption, created_at FROM telegram_file_cache WHERE cache_key = ?",
                (cache_key,),
            )
            row = cursor.fetchone()
            if row:
                file_id, file_type, caption, created_at = row
                if time.time() - created_at < config.cache_ttl:
                    return {
                        "file_id": file_id,
                        "file_type": file_type,
                        "caption": caption,
                    }
                else:
                    cursor.execute("DELETE FROM telegram_file_cache WHERE cache_key = ?", (cache_key,))
                    conn.commit()
        return None

    def set_telegram_file(self, cache_key: str, file_id: str, file_type: str, caption: Optional[str] = None):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            cursor.execute(
                "INSERT OR REPLACE INTO telegram_file_cache (cache_key, file_id, file_type, caption, created_at) VALUES (?, ?, ?, ?, ?)",
                (cache_key, file_id, file_type, caption or "", now),
            )
            conn.commit()

    # Rate Limiting
    def check_rate_limit(self, user_id: int) -> bool:
        """Returns True if within limit, False if rate-limited"""
        now = int(time.time())
        window = 60  # 1 minute window
        cutoff = now - window
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_rate_limits WHERE timestamp < ?", (cutoff,))
            cursor.execute("SELECT COUNT(*) FROM user_rate_limits WHERE user_id = ? AND timestamp >= ?", (user_id, cutoff))
            count = cursor.fetchone()[0]
            if count >= config.user_rate_limit:
                return False
            cursor.execute("INSERT INTO user_rate_limits (user_id, timestamp) VALUES (?, ?)", (user_id, now))
            conn.commit()
        return True

    def cleanup_expired(self):
        cutoff = int(time.time()) - config.cache_ttl
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM media_info_cache WHERE created_at < ?", (cutoff,))
            cursor.execute("DELETE FROM telegram_file_cache WHERE created_at < ?", (cutoff,))
            cursor.execute("DELETE FROM user_rate_limits WHERE timestamp < ?", (int(time.time()) - 3600,))
            conn.commit()
