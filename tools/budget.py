import sqlite3
from typing import Dict, List, Optional, TypedDict
from pathlib import Path
from contextlib import contextmanager


class BudgetStatus(TypedDict):
    category: str
    monthly_limit: float
    current_spent: float
    remaining: float
    percent_used: float


class ValidationResult(TypedDict):
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
    
    def __init__(self, db_path: str = "data/expenses.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    @contextmanager
    def _get_connection(self):
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
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    monthly_limit REAL NOT NULL,
                    current_spent REAL DEFAULT 0.0
                )
            """)

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
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE budgets SET current_spent = current_spent + ? WHERE category = ?",
                (amount, category)
            )
    
    def reset_monthly_spending(self) -> None:
        with self._get_connection() as conn:
            conn.execute("UPDATE budgets SET current_spent = 0")
    
    def validate_expense(self, category: str, amount: float) -> ValidationResult:
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
                    f"Over budget! Category: {category}. "
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
                f"Within budget. Remaining for {category}: ${new_remaining:.2f}"
            ),
            "remaining": new_remaining,
            "over_by": 0.0
        }
    
    def update_budget_limit(self, category: str, new_limit: float) -> bool:
        if new_limit < 0:
            raise ValueError("Budget limit cannot be negative")
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE budgets SET monthly_limit = ? WHERE category = ?",
                (new_limit, category)
            )
            return cursor.rowcount > 0