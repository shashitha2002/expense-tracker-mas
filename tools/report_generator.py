# tools/report_generator.py
"""
Expense report generation and analytics tool.
Student 4's custom tool with strict type hinting and docstrings.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict
from pathlib import Path


class MonthlySummary(TypedDict):
    """Monthly spending summary structure."""
    total_spent: float
    category_breakdown: Dict[str, float]
    transaction_count: int
    top_category: str
    average_transaction: float


class ReportData(TypedDict):
    """Complete report payload."""
    title: str
    generated_at: str
    period: str
    summary: MonthlySummary
    insights: List[str]


class ReportGenerator:
    """
    Generates spending reports and analytics from expense database.
    
    Provides text summaries, category breakdowns, and trend insights
    for the Advisor Agent to use in recommendations.
    """
    
    def __init__(self, db_path: str = "data/expenses.db") -> None:
        """
        Initialize ReportGenerator.
        
        Args:
            db_path: Path to SQLite database.
        """
        self.db_path = db_path
    
    def _query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute SELECT query safely.
        
        Args:
            sql: SQL query string.
            params: Query parameters.
            
        Returns:
            List of sqlite3.Row objects.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(sql, params).fetchall()
    
    def get_monthly_summary(self, year_month: Optional[str] = None) -> MonthlySummary:
        """
        Generate spending summary for a specific month.
        
        Args:
            year_month: YYYY-MM format. Defaults to current month.
            
        Returns:
            MonthlySummary with totals, breakdowns, and insights.
        """
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")
        
        # Total spent
        total_row = self._query(
            "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date LIKE ?",
            (f"{year_month}%",)
        )[0]
        total_spent = total_row["total"]
        
        # Category breakdown
        cat_rows = self._query(
            "SELECT category, SUM(amount) as total FROM expenses WHERE date LIKE ? GROUP BY category",
            (f"{year_month}%",)
        )
        breakdown = {row["category"]: row["total"] for row in cat_rows}
        
        # Transaction count
        count_row = self._query(
            "SELECT COUNT(*) as cnt FROM expenses WHERE date LIKE ?",
            (f"{year_month}%",)
        )[0]
        transaction_count = count_row["cnt"]
        
        # Top category
        top_category = max(breakdown, key=breakdown.get) if breakdown else "none"
        
        avg_txn = total_spent / transaction_count if transaction_count > 0 else 0.0
        
        return {
            "total_spent": round(total_spent, 2),
            "category_breakdown": breakdown,
            "transaction_count": transaction_count,
            "top_category": top_category,
            "average_transaction": round(avg_txn, 2)
        }
    
    def get_spending_trend(self, days: int = 7) -> Dict[str, float]:
        """
        Get daily spending totals for recent days.
        
        Args:
            days: Number of days to look back.
            
        Returns:
            Dictionary mapping dates to daily totals.
        """
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self._query(
            "SELECT date, SUM(amount) as total FROM expenses WHERE date >= ? GROUP BY date ORDER BY date",
            (since,)
        )
        return {row["date"]: row["total"] for row in rows}
    
    def generate_insights(self, summary: MonthlySummary) -> List[str]:
        """
        Generate human-readable insights from summary data.
        
        Args:
            summary: MonthlySummary from get_monthly_summary().
            
        Returns:
            List of insight strings.
        """
        insights: List[str] = []
        
        if summary["transaction_count"] == 0:
            insights.append("No transactions recorded this period.")
            return insights
        
        insights.append(
            f"You've made {summary['transaction_count']} transactions "
            f"totaling ${summary['total_spent']:.2f}."
        )
        
        if summary["top_category"] != "none":
            top_amount = summary["category_breakdown"][summary["top_category"]]
            insights.append(
                f"Your highest spending category is {summary['top_category']} "
                f"at ${top_amount:.2f}."
            )
        
        # Budget warnings
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            budgets = conn.execute("SELECT * FROM budgets").fetchall()
            for row in budgets:
                cat = row["category"]
                limit = row["monthly_limit"]
                spent = row["current_spent"]
                if limit > 0 and spent > limit:
                    over = spent - limit
                    insights.append(
                        f"🚨 You've exceeded your {cat} budget by ${over:.2f}."
                    )
                elif limit > 0 and spent > limit * 0.8:
                    insights.append(
                        f"⚠️ You've used {(spent/limit)*100:.0f}% of your {cat} budget."
                    )
        
        return insights
    
    def generate_report(self, period: Optional[str] = None) -> ReportData:
        """
        Generate complete spending report.
        
        This is the primary tool function used by the Advisor Agent.
        
        Args:
            period: YYYY-MM format, defaults to current month.
            
        Returns:
            Complete ReportData with summary and insights.
        """
        summary = self.get_monthly_summary(period)
        insights = self.generate_insights(summary)
        period_label = period or datetime.now().strftime("%Y-%m")
        
        return {
            "title": f"Expense Report - {period_label}",
            "generated_at": datetime.now().isoformat(),
            "period": period_label,
            "summary": summary,
            "insights": insights
        }
    
    def export_to_text(self, report: ReportData, filepath: Optional[str] = None) -> str:
        """
        Export report to human-readable text file.
        
        Args:
            report: ReportData from generate_report().
            filepath: Output path. Defaults to logs/report_YYYYMM.txt
            
        Returns:
            Path to generated file.
        """
        if filepath is None:
            Path("logs").mkdir(exist_ok=True)
            filepath = f"logs/report_{report['period']}.txt"
        
        lines = [
            "=" * 50,
            report["title"],
            f"Generated: {report['generated_at']}",
            "=" * 50,
            "",
            f"Total Spent: ${report['summary']['total_spent']:.2f}",
            f"Transactions: {report['summary']['transaction_count']}",
            f"Average: ${report['summary']['average_transaction']:.2f}",
            f"Top Category: {report['summary']['top_category']}",
            "",
            "Category Breakdown:",
        ]
        
        for cat, amount in report["summary"]["category_breakdown"].items():
            lines.append(f"  - {cat}: ${amount:.2f}")
        
        lines.extend([
            "",
            "Insights:",
        ])
        for insight in report["insights"]:
            lines.append(f"  • {insight}")
        
        lines.append("")
        lines.append("=" * 50)
        
        content = "\n".join(lines)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath