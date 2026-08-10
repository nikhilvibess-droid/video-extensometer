import logging
import os
from datetime import datetime

from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

ACTIVE_TABLE = "audit_logs"
ARCHIVE_TABLE = "audit_logs_archive"
MAX_ACTIVE_RECORDS = 10000
SUPERADMIN_ROLE = "superadmin"

AUDIT_COLUMNS = (
    "id",
    "timestamp",
    "username",
    "role",
    "action",
    "result",
    "reason",
    "machine_name",
    "os_username",
    "session_id",
    "app_version",
    "session_duration_seconds",
    "details",
)

AUDIT_INSERT_COLUMNS = AUDIT_COLUMNS[1:]
AUDIT_SELECT_COLUMNS = ", ".join(AUDIT_COLUMNS)

DATE_RANGE_SQL = {
    "Today": "date({table}.timestamp) = date('now', 'localtime')",
    "Last 7 Days": "{table}.timestamp >= datetime('now', 'localtime', '-7 days')",
    "Last 30 Days": "{table}.timestamp >= datetime('now', 'localtime', '-30 days')",
    "Last 90 Days": "{table}.timestamp >= datetime('now', 'localtime', '-90 days')",
    "Last Year": "{table}.timestamp >= datetime('now', 'localtime', '-1 year')",
}


class AuditClearPermissionError(PermissionError):
    """Raised when a non-superadmin attempts to clear audit logs."""


class AuditArchiveService:
    """Retention, archiving, and indexed querying for audit log tables."""

    _instance = None

    def __new__(cls, db=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db=None):
        if getattr(self, "_initialized", False) and db is None:
            return
        self.db = db or DatabaseManager()
        self._initialized = True

    @classmethod
    def get_instance(cls):
        return cls()

    @staticmethod
    def table_for_source(active=True):
        return ACTIVE_TABLE if active else ARCHIVE_TABLE

    def get_stats(self):
        cur = self.db.conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {ACTIVE_TABLE}")
        active_count = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {ARCHIVE_TABLE}")
        archived_count = cur.fetchone()[0]
        last_archive = self.get_meta("last_archive_date", "—")
        db_size = self._database_size()
        cur.close()
        return {
            "active_count": active_count,
            "archived_count": archived_count,
            "max_active_records": MAX_ACTIVE_RECORDS,
            "last_archive_date": last_archive,
            "database_size": db_size,
        }

    def count_records(self, active=True, filters=None):
        table = self.table_for_source(active)
        where_sql, params = self._build_where_clause(table, filters or {})
        cur = self.db.conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table} {where_sql}", params)
        count = cur.fetchone()[0]
        cur.close()
        return count

    def fetch_page(
        self,
        active=True,
        filters=None,
        page=0,
        page_size=100,
        order_by="id DESC",
    ):
        table = self.table_for_source(active)
        where_sql, params = self._build_where_clause(table, filters or {})
        offset = page * page_size
        cur = self.db.conn.cursor()
        cur.execute(
            f"""
            SELECT {AUDIT_SELECT_COLUMNS}
            FROM {table}
            {where_sql}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
            """,
            params + [page_size, offset],
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    def maybe_archive_excess(self):
        active_count = self.count_records(active=True)
        print(f"[AUDIT] Current Active Records: {active_count}")
        if active_count <= MAX_ACTIVE_RECORDS:
            return 0
        excess = active_count - MAX_ACTIVE_RECORDS
        return self._archive_oldest(excess)

    def archive_now(self, username="system", role="system"):
        active_count = self.count_records(active=True)
        if active_count <= MAX_ACTIVE_RECORDS:
            return 0
        excess = active_count - MAX_ACTIVE_RECORDS
        return self._archive_oldest(excess, username=username, role=role)

    def fetch_all_for_export(
        self,
        active=True,
        filters=None,
        order_by="id DESC",
        max_rows=100000,
    ):
        table = self.table_for_source(active)
        where_sql, params = self._build_where_clause(table, filters or {})
        cur = self.db.conn.cursor()
        cur.execute(
            f"""
            SELECT {AUDIT_SELECT_COLUMNS}
            FROM {table}
            {where_sql}
            ORDER BY {order_by}
            LIMIT ?
            """,
            params + [max_rows],
        )
        rows = cur.fetchall()
        cur.close()
        return rows

    def optimize_database(self):
        print("[AUDIT] Database Optimized")
        with self.db._write_lock:
            self.db.conn.execute("ANALYZE")

    def vacuum_database(self):
        with self.db._write_lock:
            self.db.conn.execute("VACUUM")
        self.optimize_database()

    def clear_all_audit_logs(self, username, role, reason="Manual Maintenance"):
        """Permanently delete all active and archived audit logs (superadmin only)."""
        normalized_role = (role or "").strip().lower()
        actor = (username or "unknown").strip() or "unknown"

        if normalized_role != SUPERADMIN_ROLE:
            self._log_unauthorized_clear_attempt(actor, role or "")
            raise AuditClearPermissionError(
                "Only Super Admin users may clear audit logs."
            )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("[AUDIT MAINTENANCE]")
        print("  Action: Clear All Audit Logs")
        print(f"  Performed By: {actor}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Reason: {reason}")
        logger.info(
            "Audit maintenance clear requested by %s at %s (%s)",
            actor,
            timestamp,
            reason,
        )

        cur = None
        try:
            with self.db._write_lock:
                cur = self.db.conn.cursor()
                cur.execute("BEGIN")

                cur.execute(f"DELETE FROM {ACTIVE_TABLE}")
                cur.execute(f"DELETE FROM {ARCHIVE_TABLE}")
                cur.execute(
                    """
                    DELETE FROM sqlite_sequence
                    WHERE name IN (?, ?)
                    """,
                    (ACTIVE_TABLE, ARCHIVE_TABLE),
                )

                cur.execute("COMMIT")
            return True
        except Exception:
            try:
                self.db.conn.rollback()
            except Exception:
                pass
            logger.exception("Failed to clear audit logs")
            raise
        finally:
            if cur:
                cur.close()

    def _log_unauthorized_clear_attempt(self, username, role):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("[AUDIT SECURITY] Unauthorized clear attempt")
        print(f"  Username: {username}")
        print(f"  Role: {role}")
        print(f"  Timestamp: {timestamp}")
        logger.warning(
            "Unauthorized audit clear attempt by %s (%s) at %s",
            username,
            role,
            timestamp,
        )

        cur = None
        try:
            with self.db._write_lock:
                cur = self.db.conn.cursor()
                cur.execute(
                    f"""
                    INSERT INTO {ACTIVE_TABLE}(
                        timestamp, username, role, action, result, reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        username,
                        role,
                        "Unauthorized Audit Clear Attempt",
                        "Denied",
                        "Insufficient permissions",
                    ),
                )
                cur.close()
                self.db.commit_audit()
        except Exception:
            logger.exception("Failed to record unauthorized audit clear attempt")
        finally:
            if cur:
                cur.close()

    def get_meta(self, key, default=""):
        cur = self.db.conn.cursor()
        cur.execute("SELECT value FROM audit_meta WHERE key = ?", (key,))
        row = cur.fetchone()
        cur.close()
        return row[0] if row else default

    def _set_meta(self, key, value):
        cur = self.db.conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_meta(key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        cur.close()

    def _archive_oldest(self, move_count, username="system", role="system"):
        if move_count <= 0:
            return 0

        print("[AUDIT] Archive Started")
        cur = None
        moved_ids = []
        try:
            with self.db._write_lock:
                cur = self.db.conn.cursor()
                cur.execute("BEGIN")
                cur.execute(
                    f"""
                    SELECT id FROM {ACTIVE_TABLE}
                    ORDER BY id ASC
                    LIMIT ?
                    """,
                    (move_count,),
                )
                moved_ids = [row[0] for row in cur.fetchall()]
                if not moved_ids:
                    cur.execute("ROLLBACK")
                    return 0

                placeholders = ",".join("?" for _ in moved_ids)
                cur.execute(
                    f"""
                    INSERT INTO {ARCHIVE_TABLE}
                    SELECT * FROM {ACTIVE_TABLE}
                    WHERE id IN ({placeholders})
                    """,
                    moved_ids,
                )
                cur.execute(
                    f"""
                    SELECT COUNT(*) FROM {ARCHIVE_TABLE}
                    WHERE id IN ({placeholders})
                    """,
                    moved_ids,
                )
                verified = cur.fetchone()[0]
                if verified != len(moved_ids):
                    raise RuntimeError(
                        f"Archive verification failed: expected {len(moved_ids)}, found {verified}"
                    )

                cur.execute(
                    f"DELETE FROM {ACTIVE_TABLE} WHERE id IN ({placeholders})",
                    moved_ids,
                )
                deleted = cur.rowcount
                if deleted != len(moved_ids):
                    raise RuntimeError(
                        f"Archive delete verification failed: expected {len(moved_ids)}, deleted {deleted}"
                    )

                archive_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(
                    """
                    INSERT INTO audit_meta(key, value)
                    VALUES ('last_archive_date', ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (archive_ts,),
                )

                cur.execute(
                    f"""
                    INSERT INTO {ACTIVE_TABLE}(
                        timestamp, username, role, action, result, details
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        archive_ts,
                        username,
                        role,
                        "Audit Archive",
                        "Success",
                        f"Moved Records: {len(moved_ids)}",
                    ),
                )
                cur.execute("COMMIT")

            print(f"[AUDIT] Records Archived: {len(moved_ids)}")
            print("[AUDIT] Archive Complete")
            self.optimize_database()
            return len(moved_ids)
        except Exception:
            try:
                self.db.conn.rollback()
            except Exception:
                pass
            print("[AUDIT] Archive Rolled Back")
            raise
        finally:
            if cur:
                cur.close()

    def _build_where_clause(self, table, filters):
        clauses = []
        params = []

        username = (filters.get("username") or "").strip()
        if username:
            clauses.append(f"{table}.username LIKE ?")
            params.append(f"%{username}%")

        role = (filters.get("role") or "").strip()
        if role:
            clauses.append(f"{table}.role LIKE ?")
            params.append(f"%{role}%")

        action = (filters.get("action") or "").strip()
        if action:
            clauses.append(f"{table}.action LIKE ?")
            params.append(f"%{action}%")

        result = (filters.get("result") or "").strip()
        if result and result != "All Results":
            clauses.append(f"{table}.result = ?")
            params.append(result)

        machine = (filters.get("machine") or "").strip()
        if machine:
            clauses.append(f"{table}.machine_name LIKE ?")
            params.append(f"%{machine}%")

        session = (filters.get("session") or "").strip()
        if session:
            clauses.append(f"{table}.session_id LIKE ?")
            params.append(f"%{session}%")

        os_user = (filters.get("os_user") or "").strip()
        if os_user:
            clauses.append(f"{table}.os_username LIKE ?")
            params.append(f"%{os_user}%")

        date_val = (filters.get("date") or "").strip()
        if date_val:
            clauses.append(f"{table}.timestamp LIKE ?")
            params.append(f"{date_val}%")

        timestamp_val = (filters.get("timestamp") or "").strip()
        if timestamp_val:
            clauses.append(f"{table}.timestamp LIKE ?")
            params.append(f"%{timestamp_val}%")

        date_range = (filters.get("date_range") or "All").strip()
        if date_range in DATE_RANGE_SQL:
            clauses.append(DATE_RANGE_SQL[date_range].format(table=table))

        where_sql = ""
        if clauses:
            where_sql = "WHERE " + " AND ".join(clauses)
        return where_sql, params

    @staticmethod
    def _database_size():
        path = DatabaseManager.DB_PATH
        if not os.path.exists(path):
            return "0 B"
        size_bytes = os.path.getsize(path)
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        return f"{size_bytes / (1024 * 1024):.2f} MB"

    @staticmethod
    def order_clause(sort_key):
        mapping = {
            "Newest First": "id DESC",
            "Oldest First": "id ASC",
            "Username A-Z": "username COLLATE NOCASE ASC, id DESC",
            "Action A-Z": "action COLLATE NOCASE ASC, id DESC",
        }
        return mapping.get(sort_key, "id DESC")
