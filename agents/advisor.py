from typing import Dict
from tools.llm_advisor import LLMAdvisor, AdviceInput


class AdvisorAgent:
    def __init__(self):
        self.name = "AdvisorAgent"
        self.advisor = LLMAdvisor(model_name="llama3.2:3b")  # Student 4's tool
    
    def run(self, state: Dict) -> Dict:
        """
        Generate final advice based on global state.
        
        Args:
            state: All previous agent outputs including budget status
            
        Returns:
            State with advice and final summary
        """
        amount = state.get("amount", 0)
        category = state.get("final_category", "unknown")
        validation = state.get("validation", {})
        budget_status = state.get("budget_status", {})
        
        # Prepare input for LLM tool
        advice_input: AdviceInput = {
            "amount": amount,
            "category": category,
            "budget_remaining": validation.get("remaining", 0),
            "over_budget": validation.get("warning", False),
            "monthly_total": None,
            "transaction_count": None
        }
        
        # Use LLMAdvisor tool
        result = self.advisor.generate_advice(
            data=advice_input,
            use_llm=True
        )
        
        # Build final summary
        summary = {
            "amount": amount,
            "category": category,
            "date": state.get("date"),
            "budget_remaining": advice_input["budget_remaining"],
            "over_budget": advice_input["over_budget"],
            "advice_tone": result["tone"],
            "confidence": result["confidence"]
        }
        
        new_state = state.copy()
        new_state["advice"] = result["advice"]
        new_state["final_summary"] = summary
        new_state["suggested_action"] = result["suggested_action"]
        
        return new_state