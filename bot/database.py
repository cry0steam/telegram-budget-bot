import os
import sqlite3
from datetime import datetime
import logging
from categories import EXPENSE_CATEGORIES

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

    # Convert month number to text format (e.g., "3" to "03")
    month_text = f"{month:02d}"

    try:
        cursor.execute(
            '''INSERT INTO planned_expenses 
               (month, category, amount_eur, created_at) 
               VALUES (?, ?, ?, ?)
               ON CONFLICT(month, category) 
               DO UPDATE SET amount_eur = ?, created_at = ?''',
            (
                month_text,
                category,
                amount_eur,
                datetime.now().isoformat(),
                amount_eur,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        success = True
    except sqlite3.Error as e:
        logging.error(
            f"""Database error in add_budget:
            month={month_text}, category={category}, amount={amount_eur}
            Error: {str(e)}"""
        )
        success = False
    except Exception as e:
        logging.exception(
            f"""Unexpected error in add_budget:
            month={month_text}, category={category}, amount={amount_eur}
            Error: {str(e)}"""
        )
        success = False
    finally:
        conn.close()

    return success


def get_budget_comparison():
    """Get budget vs actual expenses comparison by month."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Get all months that have either budget or expenses
        cursor.execute('''
            WITH months AS (
                -- Get months from planned_expenses
                SELECT DISTINCT month FROM planned_expenses
                UNION
                -- Get months from expenses (extract month from created_at)
                SELECT DISTINCT strftime('%m', substr(created_at, 1, 10)) as month 
                FROM expenses
                WHERE created_at >= datetime('now', 'start of year')
            )
            SELECT month FROM months ORDER BY month
        ''')
        months = [row[0] for row in cursor.fetchall()]
        logging.debug(f"Found months: {months}")

        result = []
        for month in months:
            # Get budget data for the month
            cursor.execute('''
                SELECT category, amount_eur
                FROM planned_expenses
                WHERE month = ?
            ''', (month,))  # month is already in correct format
            budget_data = dict(cursor.fetchall())
            logging.debug(f"Month {month} budget data: {budget_data}")

            # Get actual expenses for the month
            cursor.execute('''
                SELECT category, ROUND(SUM(amount_eur), 2) as total
                FROM expenses
                WHERE strftime('%m', substr(created_at, 1, 10)) = ?
                AND created_at >= datetime('now', 'start of year')
                GROUP BY category
            ''', (month,))  # month is already in correct format
            actual_data = dict(cursor.fetchall())
            logging.debug(f"Month {month} actual data: {actual_data}")

            # Calculate totals and remaining budget
            month_data = {'month': int(month)}  # Convert month to integer for display
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
            logging.debug(f"Processed data for month {month}: {month_data}")

    except Exception as e:
        logging.exception("Error in get_budget_comparison:")
        raise

    finally:
        conn.close()

    return result
