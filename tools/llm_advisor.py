from typing import Dict, Optional, TypedDict, List
from langchain_ollama import OllamaLLM


class AdviceInput(TypedDict):
    """Input structure for advice generation."""
    amount: float
    category: str
    budget_remaining: float
    over_budget: bool
    monthly_total: Optional[float]
    transaction_count: Optional[int]


class AdviceOutput(TypedDict):
    """Output structure from advice generation."""
    advice: str
    tone: str  # "positive", "neutral", "warning"
    confidence: float  # 0.0 to 1.0
    suggested_action: Optional[str]


class LLMAdvisor:
    """
    Generates personalized financial advice using local LLM.
    
    """
    
    def __init__(self, model_name: str = "llama3.2:3b",
                 temperature: float = 0.3) -> None:
        """
        Initialize LLM advisor with specified model.
        
        Args:
            model_name: Ollama model identifier.
            temperature: Sampling temperature (lower = more deterministic).
        """
        self.model_name = model_name
        self.temperature = temperature
        self._llm: Optional[OllamaLLM] = None
        self._init_llm()
    
    def _init_llm(self) -> None:
        try:
            self._llm = OllamaLLM(
                model=self.model_name,
                temperature=self.temperature
            )
        except Exception as e:
            print(f"Warning: Could not initialize LLM: {e}")
            self._llm = None
    
    def _build_prompt(self, data: AdviceInput) -> str:
        """
        Construct prompt for 3.2 3B model.
        
        Args:
            data: Advice input parameters.
            
        Returns:
            Formatted prompt string.
        """
        tone_context = "over budget" if data["over_budget"] else "within budget"
        
        prompt = f"""You are a friendly budget advisor. Write ONE concise sentence (max 20 words) responding to this expense.

Context:
- Spent ${data['amount']:.0f} on {data['category']}
- Budget remaining: ${data['budget_remaining']:.0f}
- Status: {tone_context}

Rules:
- Be brief and specific
- Mention the amount and category
- Give one actionable tip if over budget
- Friendly, conversational tone

Response:"""
        return prompt
    
    def _fallback_advice(self, data: AdviceInput) -> AdviceOutput:
        """
        Generate deterministic advice when LLM unavailable.
        
        Args:
            data: Advice input parameters.
            
        Returns:
            AdviceOutput without LLM call.
        """
        amount = data["amount"]
        category = data["category"]
        remaining = data["budget_remaining"]
        
        if data["over_budget"]:
            advice = (
                f"Expense of ${amount:.0f} for {category} logged. "
                f"You're over budget by ${abs(remaining):.0f}. "
                f"Consider reducing {category} spending this month."
            )
            tone = "warning"
            confidence = 1.0
            action = f"Reduce {category} spending"
        elif remaining < 50:
            advice = (
                f"${amount:.0f} spent on {category}. "
                f"Only ${remaining:.0f} left in budget—spend carefully!"
            )
            tone = "warning"
            confidence = 1.0
            action = "Monitor spending closely"
        else:
            advice = (
                f"Logged ${amount:.0f} for {category}. "
                f"${remaining:.0f} remaining in your budget."
            )
            tone = "positive"
            confidence = 1.0
            action = None
        
        return {
            "advice": advice,
            "tone": tone,
            "confidence": confidence,
            "suggested_action": action
        }
    
    def generate_advice(self, data: AdviceInput,
                       use_llm: bool = True) -> AdviceOutput:
        """
        Generate personalized financial advice.
        
        Args:
            data: Expense and budget information.
            use_llm: Whether to use LLM or fallback logic.
            
        Returns:
            AdviceOutput with generated advice and metadata.
        """
        # Validate input
        if data["amount"] <= 0:
            return {
                "advice": "Invalid expense amount provided.",
                "tone": "neutral",
                "confidence": 0.0,
                "suggested_action": "Check expense amount"
            }
        
        # Use fallback if LLM disabled or unavailable
        if not use_llm or self._llm is None:
            return self._fallback_advice(data)
        
        # Attempt LLM generation
        try:
            prompt = self._build_prompt(data)
            response = self._llm.invoke(prompt)
            
            # Clean response
            advice = response.strip().replace('"', '')
            
            # Truncate if too long
            if len(advice) > 150:
                advice = advice[:147] + "..."
            
            # Determine tone
            tone = "neutral"
            if data["over_budget"]:
                tone = "warning"
            elif "great" in advice.lower() or "good" in advice.lower():
                tone = "positive"
            
            return {
                "advice": advice,
                "tone": tone,
                "confidence": 0.8,
                "suggested_action": None
            }
            
        except Exception as e:
            # Graceful degradation to fallback
            print(f"LLM call failed: {e}, using fallback")
            return self._fallback_advice(data)
    
    def generate_summary_advice(self, monthly_data: Dict) -> str:
        """
        Generate broader monthly spending advice.
        
        Args:
            monthly_data: Dictionary with monthly totals and categories.
            
        Returns:
            Multi-sentence advice paragraph.
        """
        total = monthly_data.get("total", 0)
        top_cat = monthly_data.get("top_category", "none")
        count = monthly_data.get("transaction_count", 0)
        
        lines = [
            f"This month you've spent ${total:.2f} across {count} transactions.",
            f"Your highest spending category is {top_cat}."
        ]
        
        # Add warning if available
        if "over_budget_categories" in monthly_data:
            over = monthly_data["over_budget_categories"]
            if over:
                lines.append(
                    f"Over budget in: {', '.join(over)}. "
                    f"Consider cutting back next month."
                )
        
        return " ".join(lines)