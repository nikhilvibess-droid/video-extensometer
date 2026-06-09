from database.db_manager import DatabaseManager


class AuditManager:

    def __init__(self):

        self.db = DatabaseManager()
     

    def log(
        self,
        username,
        action
    ):

        cur = self.db.conn.cursor()

        cur.execute(
            """
            INSERT INTO audit_logs
            (
                username,
                action
            )
            VALUES (?, ?)
            """,
            (
                username,
                action
            )
        )

        self.db.conn.commit()