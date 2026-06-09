import sqlite3


class DatabaseManager:

    def __init__(self):

        self.conn = sqlite3.connect(
            "database/extensometer.db"
        )

        self.create_tables()

    def create_tables(self):

        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
        """)

        self.conn.commit()