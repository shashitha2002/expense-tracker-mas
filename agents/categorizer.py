# agents/categorizer.py
from typing import Dict

class CategorizerAgent:
    """
    Agent 3: Confirms category and prepares for storage.
    Student 3's implementation.
    """
    
    def __init__(self):
        self.name = "CategorizerAgent"
    
    def run(self, state: Dict) -> Dict:
        """
        Finalize category and prepare database record.
        
        Args:
            state: Has suggested_category, description, amount, date
            
        Returns:
            State with final category and DB-ready data
        """
        # Simple confirmation - 3.2 3B can handle this
        suggested = state.get("suggested_category") or "other"
        amount = state.get("amount") or 0

        if amount <= 0:
            return {
                "final_category": "invalid",
                "db_record": {},
                "ready_to_store": False,
                "error": "Invalid amount"
            }
        
        # Map to final category (could use LLM for disambiguation)
        final_category = suggested
        
        # Prepare record
        record = {
            "amount": state.get("amount"),
            "category": final_category,
            "description": state.get("description"),
            "date": state.get("date"),
            "raw_input": state.get("user_input")
        }
        
        new_state = state.copy()
        new_state["final_category"] = final_category
        new_state["db_record"] = record
        new_state["ready_to_store"] = True
        
        return new_state