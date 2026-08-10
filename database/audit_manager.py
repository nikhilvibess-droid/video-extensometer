import getpass
import logging
import platform
import socket
import threading
import time
import uuid
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal

from database.db_manager import DatabaseManager
from database.audit_archive_service import AuditArchiveService

logger = logging.getLogger(__name__)

APP_VERSION = "v2.5.0-industrial"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 0.05

LOGIN_ACTION_ALIASES = {
    "LOGIN SUCCESS": ("Login", "Success", None),
    "LOGIN FAILED": ("Login Attempt", "Failed", "Invalid Password"),
    "USER NOT FOUND": ("Login Attempt", "Failed", "Unknown User"),
}


class AuditManager(QObject):
    """Enterprise-grade audit logger — single source of truth for security events."""

    audit_record_created = pyqtSignal()

    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._qt_initialized = False
            return cls._instance

    def __init__(self):
        if self._qt_initialized:
            return

        super().__init__()
        self.db = DatabaseManager()
        self._write_lock = threading.Lock()
        self._session_id = None
        self._login_time = None
        self._current_username = None
        self._current_role = None
        self._login_in_flight = False
        self._archive_in_progress = False
        self._qt_initialized = True

    @classmethod
    def get_instance(cls):
        return cls()

    def log(self, username, action):
        """Backward-compatible entry point used by AuthManager."""
        normalized = (action or "").strip().upper()

        if normalized == "LOGIN SUCCESS":
            print("[AUDIT] Login Started")
            self._record_login_success(username)
            print("[AUDIT] Login Completed")
            return

        if normalized in LOGIN_ACTION_ALIASES:
            mapped_action, result, reason = LOGIN_ACTION_ALIASES[normalized]
            self._insert_record(
                username=username or "",
                action=mapped_action,
                result=result,
                reason=reason,
            )
            return

        self._insert_record(
            username=username or "",
            action=action,
        )

    def log_event(
        self,
        action,
        username="",
        role="",
        result="",
        reason="",
        details="",
        session_duration_seconds=None,
    ):
        self._insert_record(
            username=username,
            role=role,
            action=action,
            result=result,
            reason=reason,
            details=details,
            session_duration_seconds=session_duration_seconds,
        )

    def log_logout(self, username=None, role=None):
        username = username or self._current_username or ""
        role = role or self._current_role or self._lookup_role(username)

        duration = None
        if self._login_time is not None:
            duration = round(time.time() - self._login_time, 2)

        self._insert_record(
            username=username,
            role=role,
            action="Logout",
            result="Success",
            session_id=self._session_id,
            session_duration_seconds=duration,
        )

        self._session_id = None
        self._login_time = None
        self._current_username = None
        self._current_role = None
        self._login_in_flight = False

    @property
    def session_id(self):
        return self._session_id

    def _record_login_success(self, username):
        with self._write_lock:
            if self._login_in_flight:
                print("[AUDIT] Duplicate login audit suppressed")
                return

            self._login_in_flight = True

        try:
            role = self._lookup_role(username)
            session_id = str(uuid.uuid4())

            print("[AUDIT] Writing Login Record")

            record_id = self._insert_record(
                username=username,
                role=role,
                action="Login",
                result="Success",
                session_id=session_id,
                debug_login=True,
            )

            self._session_id = session_id
            self._login_time = time.time()
            self._current_username = username
            self._current_role = role

            if record_id is not None:
                print(f"[AUDIT] Record ID {record_id}")
        finally:
            with self._write_lock:
                self._login_in_flight = False

    def _lookup_role(self, username):
        if not username:
            return ""
        try:
            cur = self.db.conn.cursor()
            cur.execute(
                "SELECT role FROM users WHERE username=?",
                (username,),
            )
            row = cur.fetchone()
            cur.close()
            return row[0] if row else ""
        except Exception as exc:
            logger.exception("Failed to look up role for audit: %s", exc)
            return ""

    def _insert_record(
        self,
        username="",
        role="",
        action="",
        result="",
        reason="",
        machine_name=None,
        os_username=None,
        session_id=None,
        app_version=None,
        session_duration_seconds=None,
        details="",
        debug_login=False,
    ):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        machine_name = machine_name or self._machine_name()
        os_username = os_username or self._os_username()
        session_id = session_id if session_id is not None else self._session_id
        app_version = app_version or APP_VERSION

        if not role and username:
            role = self._lookup_role(username)

        payload = (
            timestamp,
            username,
            role,
            action,
            result,
            reason,
            machine_name,
            os_username,
            session_id,
            app_version,
            session_duration_seconds,
            details,
        )

        record_id = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with self.db._write_lock:
                    cur = self.db.conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO audit_logs(
                            timestamp,
                            username,
                            role,
                            action,
                            result,
                            reason,
                            machine_name,
                            os_username,
                            session_id,
                            app_version,
                            session_duration_seconds,
                            details
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        payload,
                    )
                    record_id = cur.lastrowid
                    cur.close()
                    self.db.commit_audit()

                if debug_login:
                    print("[AUDIT] Commit Successful")

                self.audit_record_created.emit()
                if not self._archive_in_progress:
                    self._maybe_archive_active_logs()
                return record_id

            except Exception as exc:
                logger.exception(
                    "Audit insert failed (attempt %s/%s): %s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS * attempt)

        return None

    @staticmethod
    def _machine_name():
        try:
            return socket.gethostname()
        except Exception:
            return platform.node() or "unknown"

    @staticmethod
    def _os_username():
        try:
            return getpass.getuser()
        except Exception:
            return "unknown"

    def _maybe_archive_active_logs(self):
        try:
            self._archive_in_progress = True
            AuditArchiveService.get_instance().maybe_archive_excess()
        except Exception as exc:
            logger.exception("Audit retention archive failed: %s", exc)
        finally:
            self._archive_in_progress = False
