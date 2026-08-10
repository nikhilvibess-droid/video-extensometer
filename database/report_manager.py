from datetime import datetime
import glob
import logging
import os
import tempfile

from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

SUPERADMIN_ROLE = "superadmin"
REPORTS_TABLE = "reports"
SAMPLES_TABLE = "test_samples"


class ReportClearPermissionError(PermissionError):
    """Raised when a non-superadmin attempts to clear all reports."""
class ReportManager:

    def __init__(self):
        self.db = DatabaseManager()

    def save_report(
        self,
        username,
        gauge_length,
        initial_distance,
        final_distance,
        strain,
        material="",
        sample_name="",
        test_name="",
        operator="",
        remarks="",
        camera_resolution="",
        software_version=""
    ):
        """
        Saves a reports record with extended fields to the SQLite database.
        """
        cur = None
        try:
            cur = self.db.conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                """
                INSERT INTO reports
                (
                    username,
                    gauge_length,
                    initial_distance,
                    final_distance,
                    strain,
                    created_at,
                    material,
                    sample_name,
                    test_name,
                    operator,
                    remarks,
                    camera_resolution,
                    software_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    gauge_length,
                    initial_distance,
                    final_distance,
                    strain,
                    created_at,
                    material,
                    sample_name,
                    test_name,
                    operator,
                    remarks,
                    camera_resolution,
                    software_version
                )
            )
            self.db.conn.commit()
            print("[REPORT SAVED]")
            return cur.lastrowid
        except Exception as e:
            try:
                self.db.conn.rollback()
            except Exception as rollback_err:
                print(f"[ERROR] Failed to rollback connection: {rollback_err}")
            print(f"[ERROR] Failed to save report: {e}")
            raise e
        finally:
            if cur:
                cur.close()

    def get_reports(self):
        """
        Fetches all report records (including extended columns) from the SQLite database.
        """
        cur = None
        try:
            cur = self.db.conn.cursor()
            cur.execute(
                """
                SELECT id, username, gauge_length, initial_distance, final_distance, strain, created_at,
                       material, sample_name, test_name, operator, remarks, camera_resolution, software_version
                FROM reports
                ORDER BY id DESC
                """
            )
            reports = cur.fetchall()
            print("[REPORT FETCHED]")
            return reports
        except Exception as e:
            print(f"[ERROR] Failed to fetch reports: {e}")
            raise e
        finally:
            if cur:
                cur.close()

    def delete_report(self, report_id):
        """
        Delete a single report and its timeline samples without resetting IDs.
        """
        cur = None
        try:
            with self.db._write_lock:
                cur = self.db.conn.cursor()
                cur.execute("BEGIN")
                cur.execute(
                    "DELETE FROM test_samples WHERE report_id = ?",
                    (report_id,),
                )
                cur.execute(
                    "DELETE FROM reports WHERE id = ?",
                    (report_id,),
                )
                if cur.rowcount != 1:
                    raise RuntimeError(
                        f"Expected to delete exactly 1 report, affected {cur.rowcount}"
                    )
                cur.execute("COMMIT")
            self._delete_report_attachments(report_id)
            print("[REPORT DELETED]")
        except Exception as e:
            try:
                self.db.conn.rollback()
            except Exception as rollback_err:
                print(f"[ERROR] Failed to rollback connection: {rollback_err}")
            print(f"[ERROR] Failed to delete report: {e}")
            raise e
        finally:
            if cur:
                cur.close()

    def clear_all_reports(self, username, role, reason="Manual Maintenance"):
        """
        Delete all reports and timeline samples (superadmin only).
        Returns a dict with deleted report and sample counts.
        """
        normalized_role = (role or "").strip().lower()
        actor = (username or "unknown").strip() or "unknown"

        if normalized_role != SUPERADMIN_ROLE:
            self._log_unauthorized_clear_attempt(actor, role or "")
            raise ReportClearPermissionError(
                "Only Super Admin users may clear all reports."
            )

        cur = None
        try:
            with self.db._write_lock:
                cur = self.db.conn.cursor()
                cur.execute("BEGIN")

                cur.execute(f"SELECT COUNT(*) FROM {REPORTS_TABLE}")
                report_count = cur.fetchone()[0]
                cur.execute(f"SELECT COUNT(*) FROM {SAMPLES_TABLE}")
                sample_count = cur.fetchone()[0]

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                maintenance_details = (
                    f"Deleted Reports: {report_count}; "
                    f"Deleted Timeline Samples: {sample_count}; "
                    f"Reason: {reason}"
                )
                print("[REPORT MAINTENANCE]")
                print("  Action: Clear All Reports")
                print(f"  Performed By: {actor}")
                print(f"  Timestamp: {timestamp}")
                print(f"  Deleted Reports: {report_count}")
                print(f"  Deleted Timeline Samples: {sample_count}")
                print(f"  Reason: {reason}")
                logger.info(
                    "Report maintenance clear requested by %s at %s (%s)",
                    actor,
                    timestamp,
                    maintenance_details,
                )

                cur.execute(
                    """
                    INSERT INTO audit_logs(
                        timestamp, username, role, action, result, reason, details
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        actor,
                        SUPERADMIN_ROLE,
                        "Clear All Reports",
                        "Success",
                        reason,
                        maintenance_details,
                    ),
                )

                cur.execute(f"DELETE FROM {SAMPLES_TABLE}")
                cur.execute(f"DELETE FROM {REPORTS_TABLE}")
                cur.execute(
                    """
                    DELETE FROM sqlite_sequence
                    WHERE name IN (?, ?)
                    """,
                    (REPORTS_TABLE, SAMPLES_TABLE),
                )

                cur.execute("COMMIT")

            self._delete_report_attachments()
            print("[REPORTS CLEARED]")
            return {
                "report_count": report_count,
                "sample_count": sample_count,
            }
        except Exception as e:
            try:
                self.db.conn.rollback()
            except Exception as rollback_err:
                print(f"[ERROR] Failed to rollback connection: {rollback_err}")
            logger.exception("Failed to clear all reports")
            print(f"[ERROR] Failed to clear all reports: {e}")
            raise e
        finally:
            if cur:
                cur.close()

    def _log_unauthorized_clear_attempt(self, username, role):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("[REPORT SECURITY] Unauthorized clear attempt")
        print(f"  Username: {username}")
        print(f"  Role: {role}")
        print(f"  Timestamp: {timestamp}")
        logger.warning(
            "Unauthorized report clear attempt by %s (%s) at %s",
            username,
            role,
            timestamp,
        )

        cur = None
        try:
            with self.db._write_lock:
                cur = self.db.conn.cursor()
                cur.execute(
                    """
                    INSERT INTO audit_logs(
                        timestamp, username, role, action, result, reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        username,
                        role,
                        "Unauthorized Report Clear Attempt",
                        "Denied",
                        "Insufficient permissions",
                    ),
                )
                cur.close()
                self.db.commit_audit()
        except Exception:
            logger.exception("Failed to record unauthorized report clear attempt")
        finally:
            if cur:
                cur.close()

    @staticmethod
    def _managed_export_directories():
        directories = {os.path.abspath(os.getcwd())}
        directories.add(tempfile.gettempdir())
        return directories

    @staticmethod
    def _managed_export_patterns(report_id=None):
        if report_id is not None:
            return [
                f"report_{report_id}.pdf",
                f"report_{report_id}.csv",
                f"vex_strain_timeline_{report_id}.png",
                f"vex_distance_timeline_{report_id}.png",
            ]
        return [
            "report_*.pdf",
            "report_*.csv",
            "vex_strain_timeline_*.png",
            "vex_distance_timeline_*.png",
        ]

    @classmethod
    def _delete_report_attachments(cls, report_id=None):
        """Remove generated report exports and timeline chart images."""
        paths = []
        for directory in cls._managed_export_directories():
            for pattern in cls._managed_export_patterns(report_id):
                paths.extend(glob.glob(os.path.join(directory, pattern)))

        seen = set()
        for path in paths:
            normalized = os.path.normcase(os.path.abspath(path))
            if normalized in seen:
                continue
            seen.add(normalized)
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError as exc:
                print(f"[WARN] Failed to remove report attachment {path}: {exc}")

    def get_reports_filtered(self, material="", username="", date_str="", sample_name="", test_name=""):
        """
        Fetches reports filtered by material, operator/username, date, sample name, and test name.
        """
        cur = None
        try:
            cur = self.db.conn.cursor()
            query = """
                SELECT id, username, gauge_length, initial_distance, final_distance, strain, created_at,
                       material, sample_name, test_name, operator, remarks, camera_resolution, software_version
                FROM reports
                WHERE 1=1
            """
            params = []
            if material:
                query += " AND material LIKE ?"
                params.append(f"%{material}%")
            if username:
                query += " AND (username LIKE ? OR operator LIKE ?)"
                params.extend([f"%{username}%", f"%{username}%"])
            if date_str:
                query += " AND created_at LIKE ?"
                params.append(f"%{date_str}%")
            if sample_name:
                query += " AND sample_name LIKE ?"
                params.append(f"%{sample_name}%")
            if test_name:
                query += " AND test_name LIKE ?"
                params.append(f"%{test_name}%")
                
            query += " ORDER BY id DESC"
            cur.execute(query, params)
            reports = cur.fetchall()
            print("[FILTERED REPORTS FETCHED]")
            return reports
        except Exception as e:
            print(f"[ERROR] Failed to fetch filtered reports: {e}")
            raise e
        finally:
            if cur:
                cur.close()