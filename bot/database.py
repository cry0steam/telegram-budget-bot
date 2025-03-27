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
        username TEXT NOT NULL,
        pos TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        amount_eur REAL NOT NULL,
        category TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planned_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT NOT NULL,
        category TEXT NOT NULL,
        amount_eur REAL NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(month, category)
    )
    """)

    conn.commit()
    conn.close()


def add_expense(date, username, pos, amount, currency, amount_eur, category):
    """Add a new expense to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO expenses (date, username, pos, amount, currency, amount_eur, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
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
        'SELECT date, username, pos, amount, currency, amount_eur, category FROM expenses ORDER BY created_at DESC LIMIT ?',
        (limit,),
    )

    results = cursor.fetchall()
    conn.close()

    return results


def create_budget_table():
    """Create a table for storing monthly budget targets per category."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budget_targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        amount_eur REAL NOT NULL,
        month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
        created_at TEXT NOT NULL,
        UNIQUE(category, month)
    )
    """)

    conn.commit()
    conn.close()


def get_current_month_expenses():
    """Get expenses for the current month starting from the 5th day."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get current month's start date (5th day)
    today = datetime.now()
    if today.day < 5:
        # If we're before the 5th, get previous month's data from the 5th
        if today.month == 1:
            start_date = f"{today.year-1}-12-05T00:00:00"
        else:
            start_date = f"{today.year}-{today.month-1:02d}-05T00:00:00"
    else:
        # Get current month's data from the 5th
        start_date = f"{today.year}-{today.month:02d}-05T00:00:00"

    # Get main expenses (excluding Travel)
    cursor.execute('''
        SELECT category, ROUND(SUM(amount_eur), 2) as total_amount
        FROM expenses 
        WHERE created_at >= ? AND category != 'Travel'
        GROUP BY category
        ORDER BY total_amount DESC
    ''', (start_date,))
    main_results = cursor.fetchall()

    # Calculate total (excluding Travel)
    cursor.execute('''
        SELECT ROUND(SUM(amount_eur), 2) as total_amount
        FROM expenses 
        WHERE created_at >= ? AND category != 'Travel'
    ''', (start_date,))
    total = cursor.fetchone()[0] or 0.0

    # Get Travel expenses separately
    cursor.execute('''
        SELECT 'Travel' as category, ROUND(SUM(amount_eur), 2) as total_amount
        FROM expenses 
        WHERE created_at >= ? AND category = 'Travel'
    ''', (start_date,))
    travel_result = cursor.fetchone()
    travel_amount = travel_result[1] if travel_result and travel_result[1] else 0.0

    conn.close()

    return main_results, total, travel_amount
