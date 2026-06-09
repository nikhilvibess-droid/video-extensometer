from database.db_manager import DatabaseManager
from auth.password_utils import hash_password


class UserManager:

    def __init__(self):

        self.db = DatabaseManager()

    def create_user(
        self,
        username,
        password,
        role
    ):

        cur = self.db.conn.cursor()

        cur.execute(
            """
            INSERT INTO users
            (
                username,
                password,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                hash_password(password),
                role
            )
        )

        self.db.conn.commit()