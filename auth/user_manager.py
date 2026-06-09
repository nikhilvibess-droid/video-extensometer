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

    def get_users(self):

        cur = self.db.conn.cursor()

        cur.execute(
            """
            SELECT username, role
            FROM users
            ORDER BY username
            """
        )

        return cur.fetchall()

    def delete_user(
        self,
        username
    ):

        cur = self.db.conn.cursor()

        cur.execute(
            """
            DELETE FROM users
            WHERE username=?
            """,
            (username,)
        )

        self.db.conn.commit()

    def change_role(
        self,
        username,
        role
    ):

        cur = self.db.conn.cursor()

        cur.execute(
            """
            UPDATE users
            SET role=?
            WHERE username=?
            """,
            (
                role,
                username
            )
        )

        self.db.conn.commit()