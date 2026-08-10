import os
import sqlite3
import threading


class DatabaseManager:
    """Thread-safe singleton SQLite connection shared across the application."""

    _instance = None
    _lock = threading.Lock()

    DB_PATH = "database/extensometer.db"

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._write_lock = threading.RLock()
        self.conn = self._open_connection()
        self.create_tables()
        self._initialized = True

    def _open_connection(self):
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(
            self.DB_PATH,
            check_same_thread=False,
            isolation_level=None,
        )
        self._configure_connection(conn)
        return conn

    @staticmethod
    def _configure_connection(conn):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")

    @staticmethod
    def _is_sqlite_file(path):
        try:
            with open(path, "rb") as handle:
                return handle.read(16).startswith(b"SQLite format 3\x00")
        except OSError:
            return False

    def backup_to(self, dest_path):
        """Create a consistent SQLite backup while the app is running."""
        dest_path = os.path.abspath(dest_path)
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        with self._write_lock:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            dest_conn = sqlite3.connect(dest_path)
            try:
                self.conn.backup(dest_conn)
            finally:
                dest_conn.close()

        if not self._is_sqlite_file(dest_path):
            raise ValueError("Backup file was created but failed validation.")

    def restore_from(self, source_path):
        """Replace the live database from a backup and refresh the open connection."""
        source_path = os.path.abspath(source_path)
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"Backup file not found: {source_path}")
        if not self._is_sqlite_file(source_path):
            raise ValueError("Selected file is not a valid SQLite database.")

        with self._write_lock:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            source_conn = sqlite3.connect(source_path)
            try:
                source_conn.backup(self.conn)
            finally:
                source_conn.close()
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT,
            role TEXT,
            action TEXT NOT NULL,
            result TEXT,
            reason TEXT,
            machine_name TEXT,
            os_username TEXT,
            session_id TEXT,
            app_version TEXT,
            session_duration_seconds REAL,
            details TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            gauge_length REAL,
            initial_distance REAL,
            final_distance REAL,
            strain REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            material TEXT,
            sample_name TEXT,
            test_name TEXT,
            operator TEXT,
            remarks TEXT,
            camera_resolution TEXT,
            software_version TEXT
        )
        """)

        self._migrate_audit_logs_schema(cur)
        self._ensure_audit_archive_schema(cur)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS company_settings(
            id INTEGER PRIMARY KEY,
            company_name TEXT,
            company_logo TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            postal_code TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            authorized_by TEXT,
            footer_text TEXT,
            report_title TEXT,
            gst_number TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)
        self._migrate_company_settings_schema(cur)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS test_samples(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            elapsed_time REAL NOT NULL,
            distance_mm REAL NOT NULL,
            extension_mm REAL NOT NULL,
            strain REAL NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY(report_id) REFERENCES reports(id) ON DELETE CASCADE
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_test_samples_report_id
        ON test_samples(report_id)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_test_samples_elapsed_time
        ON test_samples(elapsed_time)
        """)

        cols_to_add = [
            ("material", "TEXT"),
            ("sample_name", "TEXT"),
            ("test_name", "TEXT"),
            ("operator", "TEXT"),
            ("remarks", "TEXT"),
            ("camera_resolution", "TEXT"),
            ("software_version", "TEXT"),
        ]
        for col, col_type in cols_to_add:
            try:
                cur.execute(f"ALTER TABLE reports ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass

        cur.close()

    def _migrate_company_settings_schema(self, cur):
        """Rename legacy license_number column to gst_number."""
        cur.execute("PRAGMA table_info(company_settings)")
        existing = {row[1] for row in cur.fetchall()}
        if not existing:
            return
        if "license_number" in existing and "gst_number" not in existing:
            cur.execute(
                "ALTER TABLE company_settings RENAME COLUMN license_number TO gst_number"
            )
        elif "gst_number" not in existing:
            try:
                cur.execute("ALTER TABLE company_settings ADD COLUMN gst_number TEXT")
            except sqlite3.OperationalError:
                pass

    def _migrate_audit_logs_schema(self, cur):
        """Upgrade legacy audit_logs table to the enterprise schema."""
        cur.execute("PRAGMA table_info(audit_logs)")
        existing = {row[1] for row in cur.fetchall()}

        if not existing:
            return

        if "timestamp" in existing and existing == {"id", "username", "action", "timestamp"}:
            cur.execute("""
                CREATE TABLE audit_logs_new(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    username TEXT,
                    role TEXT,
                    action TEXT NOT NULL,
                    result TEXT,
                    reason TEXT,
                    machine_name TEXT,
                    os_username TEXT,
                    session_id TEXT,
                    app_version TEXT,
                    session_duration_seconds REAL,
                    details TEXT
                )
            """)
            cur.execute("""
                INSERT INTO audit_logs_new(
                    id, timestamp, username, action, result, reason
                )
                SELECT
                    id,
                    COALESCE(timestamp, datetime('now', 'localtime')),
                    username,
                    action,
                    CASE
                        WHEN action IN ('LOGIN SUCCESS') THEN 'Success'
                        WHEN action IN ('LOGIN FAILED', 'USER NOT FOUND') THEN 'Failed'
                        ELSE NULL
                    END,
                    CASE
                        WHEN action = 'USER NOT FOUND' THEN 'Unknown User'
                        WHEN action = 'LOGIN FAILED' THEN 'Invalid Password'
                        ELSE NULL
                    END
                FROM audit_logs
            """)
            cur.execute("DROP TABLE audit_logs")
            cur.execute("ALTER TABLE audit_logs_new RENAME TO audit_logs")
            return

        audit_columns = {
            "timestamp": "TEXT",
            "role": "TEXT",
            "result": "TEXT",
            "reason": "TEXT",
            "machine_name": "TEXT",
            "os_username": "TEXT",
            "session_id": "TEXT",
            "app_version": "TEXT",
            "session_duration_seconds": "REAL",
            "details": "TEXT",
        }
        for col, col_type in audit_columns.items():
            if col not in existing:
                cur.execute(f"ALTER TABLE audit_logs ADD COLUMN {col} {col_type}")

    def _ensure_audit_archive_schema(self, cur):
        """Create archive table, metadata store, and performance indexes."""
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs_archive(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT,
            role TEXT,
            action TEXT NOT NULL,
            result TEXT,
            reason TEXT,
            machine_name TEXT,
            os_username TEXT,
            session_id TEXT,
            app_version TEXT,
            session_duration_seconds REAL,
            details TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)

        index_specs = [
            ("audit_logs", "idx_audit_logs_timestamp", "timestamp"),
            ("audit_logs", "idx_audit_logs_username", "username"),
            ("audit_logs", "idx_audit_logs_action", "action"),
            ("audit_logs", "idx_audit_logs_result", "result"),
            ("audit_logs", "idx_audit_logs_role", "role"),
            ("audit_logs_archive", "idx_audit_archive_timestamp", "timestamp"),
            ("audit_logs_archive", "idx_audit_archive_username", "username"),
            ("audit_logs_archive", "idx_audit_archive_action", "action"),
            ("audit_logs_archive", "idx_audit_archive_result", "result"),
            ("audit_logs_archive", "idx_audit_archive_role", "role"),
        ]
        for table, index_name, column in index_specs:
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table}({column})
                """
            )

    def commit_audit(self):
        """Immediately flush audit writes to disk."""
        with self._write_lock:
            self.conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            self.conn.commit()

    @classmethod
    def reset_instance(cls):
        """Close and reset singleton (for tests only)."""
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance.conn.close()
                except Exception:
                    pass
                cls._instance = None
