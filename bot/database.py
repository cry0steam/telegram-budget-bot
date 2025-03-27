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


def get_top_expenses_per_category():
    """Get top 5 expenses per category for the current month starting from the 5th day."""
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

    # Get top 5 expenses for each category except Travel
    cursor.execute('''
        WITH RankedExpenses AS (
            SELECT 
                category,
                username,
                pos,
                ROUND(amount_eur, 2) as amount_eur,
                ROW_NUMBER() OVER (PARTITION BY category ORDER BY amount_eur DESC) as rn
            FROM expenses 
            WHERE created_at >= ? AND category != 'Travel'
        )
        SELECT category, username, pos, amount_eur
        FROM RankedExpenses
        WHERE rn <= 5
        ORDER BY category, amount_eur DESC
    ''', (start_date,))

    results = cursor.fetchall()
    conn.close()

    return results


def add_budget(month, category, amount_eur):
    """Add or update budget target for a category in a specific month."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute(
            '''INSERT INTO budget_targets 
               (month, category, amount_eur, created_at) 
               VALUES (?, ?, ?, ?)
               ON CONFLICT(month, category) 
               DO UPDATE SET amount_eur = ?, created_at = ?''',
            (
                month,
                category,
                amount_eur,
                datetime.now().isoformat(),
                amount_eur,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        success = True
    except sqlite3.Error:
        success = False
    finally:
        conn.close()

    return success


def get_budget_comparison():
    """Get budget vs actual expenses comparison by month."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get all months that have either budget or expenses
    cursor.execute('''
        WITH months AS (
            -- Get months from budget_targets
            SELECT DISTINCT month FROM budget_targets
            UNION
            -- Get months from expenses (extract month from created_at)
            SELECT DISTINCT CAST(strftime('%m', substr(created_at, 1, 10)) AS INTEGER) as month 
            FROM expenses
            WHERE created_at >= datetime('now', 'start of year')
        )
        SELECT month FROM months ORDER BY month
    ''')
    months = [row[0] for row in cursor.fetchall()]

    result = []
    for month in months:
        # Get budget data for the month
        cursor.execute('''
            SELECT category, amount_eur
            FROM budget_targets
            WHERE month = ?
        ''', (month,))
        budget_data = dict(cursor.fetchall())

        # Get actual expenses for the month
        cursor.execute('''
            SELECT category, ROUND(SUM(amount_eur), 2) as total
            FROM expenses
            WHERE strftime('%m', substr(created_at, 1, 10)) = ?
            AND created_at >= datetime('now', 'start of year')
            GROUP BY category
        ''', (f"{month:02d}",))
        actual_data = dict(cursor.fetchall())

        # Calculate totals and remaining budget
        month_data = {'month': month}
        total_budget = 0
        total_actual = 0

        for category in EXPENSE_CATEGORIES:
            budget = budget_data.get(category, 0) or 0
            actual = actual_data.get(category, 0) or 0
            remaining = budget - actual

            month_data[f"{category}_budget"] = budget
            month_data[f"{category}_actual"] = actual
            month_data[f"{category}_left"] = remaining

            total_budget += budget
            total_actual += actual

        month_data["Total_budget"] = total_budget
        month_data["Total_actual"] = total_actual
        month_data["Total_left"] = total_budget - total_actual

        result.append(month_data)

    conn.close()
    return result
