# agents/validator.py
from typing import Dict
from tools.budget import BudgetManager

class ValidatorAgent:
    def __init__(self):
        self.name = "ValidatorAgent"
        self.budget = BudgetManager()
    
    def run(self, state: Dict) -> Dict:
        amount = state.get("amount", 0)
        category = state.get("suggested_category", "other")
        
        if amount <= 0:
            return {
                "validation": {
                    "valid": False,
                    "message": "Invalid amount for validation"
                },
                "budget_status": {}
            }
        
        # Use the BudgetManager tool
        validation = self.budget.validate_expense(category, amount)
        budget_status = self.budget.get_budget(category) or {}
        
        new_state = state.copy()
        new_state["validation"] = validation
        new_state["budget_status"] = budget_status
        return new_state