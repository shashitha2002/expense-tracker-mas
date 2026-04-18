# agents/advisor.py
from typing import Dict
from langchain_ollama import OllamaLLM
import json

class AdvisorAgent:
    """
    Agent 4: Generates spending advice based on budget status.
    Student 4's implementation.
    """
    
    def __init__(self):
        self.name = "AdvisorAgent"
        # Use 3.2 3B for simple text generation
        self.llm = OllamaLLM(model="llama3.2:3b", temperature=0.3)
    
    def run(self, state: Dict) -> Dict:
        """
        Generate final advice message.
        
        Args:
            state: All previous data including validation results
            
        Returns:
            State with advice and final summary
        """
        amount = state.get("amount", 0)
        category = state.get("final_category", "unknown")
        validation = state.get("validation", {})
        budget = state.get("budget_status", {})
        
        # Build simple prompt - easy for 3.2 3B
        prompt = f"""You are a friendly budget advisor. Write a brief 2-sentence response.

Facts:
- User spent ${amount} on {category}
- Budget remaining: ${validation.get('remaining', 0):.2f}
- Over budget: {'Yes' if validation.get('warning') else 'No'}

Response format:
"Expense logged: $[amount] for [category]. [Advice about budget]."

Keep it friendly and concise. No JSON, just text.
"""
        
        try:
            advice = self.llm.invoke(prompt)
        except Exception as e:
            # Fallback if LLM fails
            advice = f"Expense logged: ${amount} for {category}. " \
                    f"Budget remaining: ${validation.get('remaining', 0):.2f}."
        
        new_state = state.copy()
        new_state["advice"] = advice.strip()
        new_state["final_summary"] = {
            "amount": amount,
            "category": category,
            "date": state.get("date"),
            "budget_remaining": validation.get("remaining", 0),
            "over_budget": validation.get("warning", False)
        }
        
        return new_state