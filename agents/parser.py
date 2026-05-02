# agents/parser.py
from typing import Dict
from tools.expense_extractor import extract_expense

class ParserAgent:
    def __init__(self):
        self.name = "ParserAgent"
    
    def run(self, state: Dict) -> Dict:
        user_input = state.get("user_input", "")
        result = extract_expense(user_input)  # Uses the standalone tool
        
        new_state = state.copy()
        new_state["parser_output"] = result
        
        if result["parsed"]:
            new_state["amount"] = result["amount"]
            new_state["description"] = result["description"]
            new_state["suggested_category"] = result["suggested_category"]
            new_state["date"] = result["date"]
            new_state["errors"] = state.get("errors", [])
        else:
            new_state["amount"] = 0
            new_state["errors"] = state.get("errors", []) + [f"Parser: {result['error']}"]
        
        return new_state