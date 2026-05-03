from typing import Dict
from tools.category_manager import CategoryManager


class CategorizerAgent:
    
    def __init__(self):
        self.name = "CategorizerAgent"
        self.manager = CategoryManager() 
    
    def run(self, state: Dict) -> Dict:
        suggested = state.get("suggested_category") or "other"
        amount = state.get("amount") or 0
        description = state.get("description", "")
        date = state.get("date", "")
        raw_input = state.get("user_input", "")
        
        if amount <= 0:
            return {
                "final_category": "invalid",
                "db_record": {},
                "ready_to_store": False,
                "error": "Invalid amount",
                "validation_warnings": []
            }
        
        # CategoryManager tool for validation
        validation = self.manager.validate_category(
            category=suggested,
            amount=amount,
            description=description
        )
        
        final_category = validation["final_category"]
        
        # CategoryManager tool for record preparation
        try:
            record = self.manager.prepare_record(
                amount=amount,
                category=final_category,
                description=description,
                date=date,
                raw_input=raw_input
            )
            
            new_state = state.copy()
            new_state["final_category"] = final_category
            new_state["db_record"] = record
            new_state["ready_to_store"] = record["valid"]
            new_state["validation_warnings"] = validation["warnings"]
            new_state["requires_review"] = validation["requires_review"]
            
            return new_state
            
        except ValueError as e:
            return {
                "final_category": "invalid",
                "db_record": {},
                "ready_to_store": False,
                "error": str(e),
                "validation_warnings": [str(e)]
            }