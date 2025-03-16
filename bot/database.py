import os
import sqlite3
from datetime import datetime

DB_FILE = os.getenv('DB_FILE', 'expenses.db')


def init_db():
    """Initialize the database with the required tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        username TEXT,
        pos TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        amount_eur REAL NOT NULL,
        category TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def add_expense(date, username, pos, amount, currency, amount_eur, category):
    """Add a new expense to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO expenses (date, username, pos, amount, currency, amount_eur, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (
            date,
            username,
            pos,
            amount,
            currency,
            amount_eur,
            category,
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()
    return True


def get_last_expenses(limit=5):
    """Get the last N expenses from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        'SELECT date, username, pos, amount, currency, amount_eur, category FROM expenses ORDER BY id DESC LIMIT ?',
        (limit,),
    )

    results = cursor.fetchall()
    conn.close()

    return results
