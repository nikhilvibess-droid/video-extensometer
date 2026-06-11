from database.db_manager import DatabaseManager


class ReportManager:

    def __init__(self):
        self.db = DatabaseManager()

    def save_report(
        self,
        username,
        gauge_length,
        initial_distance,
        final_distance,
        strain
    ):
        """
        Saves a reports record to the SQLite database.
        
        Prints [REPORT SAVED] on successful save.
        """
        cur = None
        try:
            cur = self.db.conn.cursor()
            cur.execute(
                """
                INSERT INTO reports
                (
                    username,
                    gauge_length,
                    initial_distance,
                    final_distance,
                    strain
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    username,
                    gauge_length,
                    initial_distance,
                    final_distance,
                    strain
                )
            )
            self.db.conn.commit()
            print("[REPORT SAVED]")
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
        Fetches all report records from the SQLite database.
        
        Prints [REPORT FETCHED] on successful fetch.
        """
        cur = None
        try:
            cur = self.db.conn.cursor()
            cur.execute(
                """
                SELECT id, username, gauge_length, initial_distance, final_distance, strain, created_at
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
        Deletes a report record by its ID from the SQLite database.
        
        Prints [REPORT DELETED] on successful delete.
        """
        cur = None
        try:
            cur = self.db.conn.cursor()
            cur.execute(
                """
                DELETE FROM reports
                WHERE id = ?
                """,
                (report_id,)
            )
            self.db.conn.commit()
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