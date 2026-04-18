# tools/database.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class ExpenseDatabase:
    """
    Simple SQLite database for expense tracking.
    Student 3's tool.
    """
    
    def __init__(self, db_path: str = "data/expenses.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create tables if not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    raw_input TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    monthly_limit REAL NOT NULL,
                    current_spent REAL DEFAULT 0
                )
            """)
            
            # Insert default budgets
            defaults = [
                ("food", 500, 0),
                ("transport", 200, 0),
                ("entertainment", 150, 0),
                ("utilities", 300, 0)
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO budgets VALUES (?, ?, ?)",
                defaults
            )
            conn.commit()
    
    def add_expense(self, amount: float, category: str, 
                    description: str, date: str, raw_input: str) -> bool:
        """
        Add expense to database.
        
        Args:
            amount: Expense amount (positive number)
            category: One of: food, transport, entertainment, utilities, other
            description: Brief description
            date: ISO format date string
            raw_input: Original user input text
            
        Returns:
            True if successful, raises ValueError if invalid
        """
        # Validation
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        valid_categories = ["food", "transport", "entertainment", 
                          "utilities", "other"]
        if category not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        
        try:
            datetime.fromisoformat(date)
        except ValueError:
            raise ValueError("Date must be ISO format (YYYY-MM-DD)")
        
        with sqlite3.connect(self.db_path) as conn:
            # Insert expense
            conn.execute("""
                INSERT INTO expenses (amount, category, description, date, raw_input)
                VALUES (?, ?, ?, ?, ?)
            """, (amount, category, description, date, raw_input))
            
            # Update budget spent
            conn.execute("""
                UPDATE budgets 
                SET current_spent = current_spent + ?
                WHERE category = ?
            """, (amount, category))
            
            conn.commit()
        
        return True
    
    def get_budget_status(self, category: Optional[str] = None) -> Dict:
        """
        Get current budget spending status.
        
        Args:
            category: Specific category or None for all
            
        Returns:
            Dictionary with budget info
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if category:
                row = conn.execute(
                    "SELECT * FROM budgets WHERE category = ?",
                    (category,)
                ).fetchone()
                return dict(row) if row else {}
            else:
                rows = conn.execute("SELECT * FROM budgets").fetchall()
                return {row["category"]: dict(row) for row in rows}
    
    def get_monthly_summary(self) -> Dict:
        """Get total spending this month."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            current_month = datetime.now().strftime("%Y-%m")
            rows = conn.execute("""
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE date LIKE ?
                GROUP BY category
            """, (f"{current_month}%",)).fetchall()
            
            return {row["category"]: row["total"] for row in rows}