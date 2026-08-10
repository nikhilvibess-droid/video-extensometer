"""
Reliability test: 100 consecutive login/logout cycles.
Expected: 100 login audit records, 100 logout records, 0 duplicates, 0 missing.
"""
import sys

from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

from auth.auth_manager import AuthManager
from database.audit_manager import AuditManager
from database.db_manager import DatabaseManager

USERNAME = "superadmin"
PASSWORD = "ChangeMe123"
CYCLES = 100


def count_login_records():
    db = DatabaseManager()
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM audit_logs
        WHERE action = 'Login' AND result = 'Success' AND username = ?
        """,
        (USERNAME,),
    )
    count = cur.fetchone()[0]
    cur.close()
    return count


def count_logout_records():
    db = DatabaseManager()
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM audit_logs
        WHERE action = 'Logout' AND username = ?
        """,
        (USERNAME,),
    )
    count = cur.fetchone()[0]
    cur.close()
    return count


def count_duplicate_login_sessions():
    db = DatabaseManager()
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT session_id, COUNT(*) AS cnt
        FROM audit_logs
        WHERE action = 'Login' AND result = 'Success' AND session_id IS NOT NULL
        GROUP BY session_id
        HAVING cnt > 1
        """
    )
    dups = cur.fetchall()
    cur.close()
    return len(dups)


def main():
    audit = AuditManager.get_instance()
    baseline_logins = count_login_records()
    baseline_logouts = count_logout_records()

    failed_logins = 0
    failed_logouts = 0
    failed_inserts = 0

    for i in range(1, CYCLES + 1):
        auth = AuthManager()
        ok = auth.login(USERNAME, PASSWORD)
        if not ok:
            failed_logins += 1
            print(f"[TEST] Cycle {i}: LOGIN FAILED")
            continue

        audit.log_logout(USERNAME, auth.current_user.get("role"))

        current_logins = count_login_records() - baseline_logins
        if current_logins < i:
            failed_inserts += 1
            print(f"[TEST] Cycle {i}: MISSING login record (expected {i}, got {current_logins})")

    final_logins = count_login_records() - baseline_logins
    final_logouts = count_logout_records() - baseline_logouts
    duplicates = count_duplicate_login_sessions()

    print("\n" + "=" * 60)
    print("AUDIT RELIABILITY TEST RESULTS")
    print("=" * 60)
    print(f"Cycles run:              {CYCLES}")
    print(f"Login records created:   {final_logins}")
    print(f"Logout records created:  {final_logouts}")
    print(f"Failed logins:           {failed_logins}")
    print(f"Failed logout inserts:   {failed_logouts}")
    print(f"Missing login records:   {max(0, CYCLES - final_logins)}")
    print(f"Duplicate session IDs:   {duplicates}")
    print(f"Failed insert detections:{failed_inserts}")
    print("=" * 60)

    success = (
        failed_logins == 0
        and final_logins == CYCLES
        and final_logouts == CYCLES
        and duplicates == 0
        and failed_inserts == 0
    )

    if success:
        print("PASS: All audit records accounted for.")
        return 0

    print("FAIL: Audit reliability test did not pass.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
