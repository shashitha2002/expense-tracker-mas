# tools/budget.py
"""
Budget management and validation tool.
Student 2's custom tool with strict type hinting and docstrings.
"""

import sqlite3
from typing import Dict, List, Optional, TypedDict
from pathlib import Path
from contextlib import contextmanager


class BudgetStatus(TypedDict):
    """Budget query response structure."""
    category: str
    monthly_limit: float
    current_spent: float
    remaining: float
    percent_used: float


class ValidationResult(TypedDict):
    """Expense validation response."""
    valid: bool
    warning: bool
    message: str
    remaining: float
    over_by: float


DEFAULT_BUDGETS: Dict[str, float] = {
    "food": 500.0,
    "transport": 200.0,
    "entertainment": 150.0,
    "utilities": 300.0,
    "healthcare": 100.0,
    "other": 250.0
}


class BudgetManager:
    """
    Manages budget limits and validates expenses against them.
    
    Uses SQLite for persistence. Initializes default budgets on first run.
    """
    
    def __init__(self, db_path: str = "data/expenses.db") -> None:
        """
        Initialize BudgetManager with database path.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for safe database connections.
        
        Yields:
            sqlite3.Connection object with row factory configured.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_tables(self) -> None:
        """Create budget table and seed defaults if empty."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    monthly_limit REAL NOT NULL,
                    current_spent REAL DEFAULT 0.0
                )
            """)
            
            # Seed defaults only if table is empty
            count = conn.execute(
                "SELECT COUNT(*) FROM budgets"
            ).fetchone()[0]
            
            if count == 0:
                for cat, limit in DEFAULT_BUDGETS.items():
                    conn.execute(
                        "INSERT INTO budgets (category, monthly_limit, current_spent) VALUES (?, ?, 0)",
                        (cat, limit)
                    )
    
    def get_budget(self, category: str) -> Optional[BudgetStatus]:
        """
        Retrieve budget status for a specific category.
        
        Args:
            category: Expense category string.
            
        Returns:
            BudgetStatus dict if found, None if category doesn't exist.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM budgets WHERE category = ?",
                (category,)
            ).fetchone()
            
            if not row:
                return None
            
            data = dict(row)
            limit = data.get("monthly_limit", 0.0)
            spent = data.get("current_spent", 0.0)
            
            return {
                "category": category,
                "monthly_limit": limit,
                "current_spent": spent,
                "remaining": limit - spent,
                "percent_used": round((spent / limit * 100), 2) if limit > 0 else 0.0
            }
    
    def get_all_budgets(self) -> Dict[str, BudgetStatus]:
        """
        Retrieve budget status for all categories.
        
        Returns:
            Dictionary mapping category names to BudgetStatus.
        """
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM budgets").fetchall()
            result = {}
            for row in rows:
                cat = row["category"]
                limit = row["monthly_limit"]
                spent = row["current_spent"]
                result[cat] = {
                    "category": cat,
                    "monthly_limit": limit,
                    "current_spent": spent,
                    "remaining": limit - spent,
                    "percent_used": round((spent / limit * 100), 2) if limit > 0 else 0.0
                }
            return result
    
    def add_spending(self, category: str, amount: float) -> None:
        """
        Add expense amount to current spending for a category.
        
        Args:
            category: Budget category.
            amount: Positive expense amount.
            
        Raises:
            ValueError: If amount is not positive.
            sqlite3.Error: If database operation fails.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE budgets SET current_spent = current_spent + ? WHERE category = ?",
                (amount, category)
            )
    
    def reset_monthly_spending(self) -> None:
        """Reset all current_spent values to zero (call on month rollover)."""
        with self._get_connection() as conn:
            conn.execute("UPDATE budgets SET current_spent = 0")
    
    def validate_expense(self, category: str, amount: float) -> ValidationResult:
        """
        Validate an expense against its category budget.
        
        This is the primary tool function used by the Validator Agent.
        
        Args:
            category: Expense category.
            amount: Proposed expense amount (must be > 0).
            
        Returns:
            ValidationResult with warning flags and messaging.
            
        Raises:
            ValueError: If amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Expense amount must be positive")
        
        budget = self.get_budget(category)
        
        if not budget:
            return {
                "valid": True,
                "warning": False,
                "message": f"No budget set for '{category}'. Expense logged without limit check.",
                "remaining": 0.0,
                "over_by": 0.0
            }
        
        remaining = budget["remaining"]
        over_by = amount - remaining if amount > remaining else 0.0
        
        if amount > remaining:
            return {
                "valid": True,
                "warning": True,
                "message": (
                    f"⚠️ Over budget! Category: {category}. "
                    f"Remaining: ${remaining:.2f}, Expense: ${amount:.2f}, "
                    f"Over by: ${over_by:.2f}"
                ),
                "remaining": remaining,
                "over_by": over_by
            }
        
        new_remaining = remaining - amount
        return {
            "valid": True,
            "warning": False,
            "message": (
                f"✓ Within budget. Remaining for {category}: ${new_remaining:.2f}"
            ),
            "remaining": new_remaining,
            "over_by": 0.0
        }
    
    def update_budget_limit(self, category: str, new_limit: float) -> bool:
        """
        Update monthly limit for a category.
        
        Args:
            category: Category to update.
            new_limit: New monthly limit (must be >= 0).
            
        Returns:
            True if updated successfully.
        """
        if new_limit < 0:
            raise ValueError("Budget limit cannot be negative")
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE budgets SET monthly_limit = ? WHERE category = ?",
                (new_limit, category)
            )
            return cursor.rowcount > 0