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

    def get_reports(self):

        cur = self.db.conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM reports
            ORDER BY id DESC
            """
        )

        return cur.fetchall()