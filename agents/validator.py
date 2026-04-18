# agents/validator.py
from typing import Dict
from tools.database import ExpenseDatabase

class ValidatorAgent:
    """
    Agent 2: Validates expense against budget limits.
    Student 2's implementation.
    """
    
    def __init__(self):
        self.name = "ValidatorAgent"
        self.db = ExpenseDatabase()
    
    def run(self, state: Dict) -> Dict:
        """
        Check if expense is within budget.
        
        Args:
            state: Must have amount, suggested_category
            
        Returns:
            State with validation result and budget status
        """
        amount = state.get("amount", 0)
        category = state.get("suggested_category", "other")
        
        # Get budget status
        budget = self.db.get_budget_status(category)
        
        if not budget:
            # No budget set for this category
            validation_result = {
                "valid": True,
                "warning": False,
                "message": "No budget limit set for this category"
            }
        else:
            limit = budget.get("monthly_limit", 0)
            spent = budget.get("current_spent", 0)
            remaining = limit - spent
            
            if amount > remaining:
                validation_result = {
                    "valid": True,  # Allow but warn
                    "warning": True,
                    "message": f"Over budget! Remaining: ${remaining:.2f}, "
                              f"Expense: ${amount:.2f}",
                    "remaining": remaining,
                    "over_by": amount - remaining
                }
            else:
                validation_result = {
                    "valid": True,
                    "warning": False,
                    "message": f"Within budget. Remaining after expense: "
                              f"${remaining - amount:.2f}",
                    "remaining": remaining - amount
                }
        
        new_state = state.copy()
        new_state["validation"] = validation_result
        new_state["budget_status"] = budget
        
        return new_state