from database.db_manager import DatabaseManager
from auth.password_utils import verify_password
from database.audit_manager import AuditManager


class AuthManager:

    def __init__(self):

        self.db = DatabaseManager()

        self.audit = AuditManager()

        self.current_user = None

    def login(self, username, password):

        cur = self.db.conn.cursor()

        cur.execute(
            """
            SELECT username, password, role
            FROM users
            WHERE username=?
            """,
            (username,)
        )

        row = cur.fetchone()

        print("DATABASE ROW =", row)

        if not row:

            print("USER NOT FOUND")

            self.audit.log(
                username,
                "USER NOT FOUND"
            )

            return False

        db_username, hashed, role = row

        print("ENTERED PASSWORD =", password)
        print("HASH IN DB =", hashed)

        if verify_password(password, hashed):

            print("LOGIN SUCCESS")

            self.audit.log(
                username,
                "LOGIN SUCCESS"
            )

            self.current_user = {
                "username": db_username,
                "role": role
            }

            return True

        self.audit.log(
            username,
            "LOGIN FAILED"
        )

        print("PASSWORD MISMATCH")

        return False