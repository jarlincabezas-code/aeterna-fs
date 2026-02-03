import sqlite3
import os


class VaultManager:
    def __init__(self, db_path: str = "vault/aeterna_vault.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    prev_hash TEXT,
                    curr_hash TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            conn.commit()

    def get_last_hash(self):
        with self._connect() as conn:
            cur = conn.execute("""
                SELECT curr_hash
                FROM audit_log
                ORDER BY id DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            return row[0] if row else "GENESIS"

    def persist(self, record: tuple):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO audit_log (
                    session_id,
                    timestamp,
                    event_type,
                    payload,
                    prev_hash,
                    curr_hash,
                    signature,
                    metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, record)
            conn.commit()

    def get_events_by_session(self, session_id: str):
        with self._connect() as conn:
            cur = conn.execute("""
                SELECT
                    session_id,
                    timestamp,
                    event_type,
                    payload,
                    prev_hash,
                    curr_hash,
                    signature,
                    metadata
                FROM audit_log
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,))
            return cur.fetchall()
