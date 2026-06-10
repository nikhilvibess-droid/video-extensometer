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
        cur.execute("""
CREATE TABLE IF NOT EXISTS audit_logs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    action TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
        cur.execute("""
CREATE TABLE IF NOT EXISTS reports(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    strain REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
        cur.execute("""
CREATE TABLE IF NOT EXISTS reports(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    gauge_length REAL,
    initial_distance REAL,
    final_distance REAL,
    strain REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
        cur.execute("""
CREATE TABLE IF NOT EXISTS reports(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    gauge_length REAL,
    initial_distance REAL,
    final_distance REAL,
    strain REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
        self.conn.commit()