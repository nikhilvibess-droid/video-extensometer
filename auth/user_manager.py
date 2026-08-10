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

    def get_user_role(self, username):
        cur = self.db.conn.cursor()
        cur.execute(
            "SELECT role FROM users WHERE username = ?",
            (username,),
        )
        row = cur.fetchone()
        cur.close()
        return row[0] if row else None

    def count_administrators(self):
        cur = self.db.conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM users
            WHERE role IN ('admin', 'superadmin')
            """
        )
        count = cur.fetchone()[0]
        cur.close()
        return count

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