# agents/parser.py
from typing import Dict, TypedDict
import re
import json

class ParserInput(TypedDict):
    user_input: str

class ParserOutput(TypedDict):
    amount: float
    description: str
    suggested_category: str
    date: str
    parsed: bool
    error: str

def extract_expense_tool(user_input: str) -> Dict:
    """
    Extract expense details from natural language.
    Student 1's tool.
    
    Args:
        user_input: Raw text like "spent $50 on groceries yesterday"
        
    Returns:
        Dictionary with amount, description, category suggestion
    """
    # Simple regex extraction (no LLM needed for basic parsing)
    # This works reliably with 3.2 3B because it's deterministic
    
    text = user_input.lower()
    
    # Extract amount
    amount_patterns = [
    r'\$(\d+(?:\.\d{2})?)',           # $50 or $50.00
    r'(\d+(?:\.\d{2})?)\s*(?:dollars|usd)',  # 50 dollars
    r'\b(\d+)\b',                  # 200000 (plain number, 4-6 digits)
    r'spent\s+(\d+(?:\.\d{2})?)',      # spent 50
    r'paid\s+(\d+(?:\.\d{2})?)',       # paid 50
    ]
    
    amount = None
    for pattern in amount_patterns:
        match = re.search(pattern, text)
        if match:
            amount = float(match.group(1))
            break
    
    if not amount:
        return {
            "parsed": False,
            "error": "Could not find amount in input",
            "amount": 0, "description": "", "suggested_category": "", "date": ""
        }
    
    # Extract description (what was bought)
    description = "general expense"
    desc_indicators = ["on ", "for ", "at "]
    for indicator in desc_indicators:
        if indicator in text:
            parts = text.split(indicator)
            if len(parts) > 1:
                # Get text after indicator, before amount mention
                desc_part = parts[1]
                # Remove amount mentions
                desc_part = re.sub(r'\$\d+(?:\.\d{2})?', '', desc_part)
                desc_part = re.sub(r'\d+(?:\.\d{2})?\s*(?:dollars|usd)', '', desc_part)
                description = desc_part.strip() or "general expense"
                break

    if description == "general expense":
        # Remove the amount number from input for description
        desc_text = re.sub(r'\d+(?:\.\d{2})?', '', user_input).strip()
        description = desc_text or "general expense"

    # Suggest category based on keywords
    category_keywords = {
        "food": ["food", "grocery", "groceries", "restaurant", "lunch", 
                "dinner", "breakfast", "coffee", "meal"],
        "transport": ["gas", "uber", "taxi", "bus", "train", "fuel", 
                     "car", "transport", "commute"],
        "entertainment": ["movie", "game", "netflix", "spotify", "fun",
                         "entertainment", "concert", "show"],
        "utilities": ["electric", "water", "bill", "internet", "phone",
                     "rent", "utility"]
    }
    
    suggested_category = "other"
    for cat, keywords in category_keywords.items():
        if any(kw in text for kw in keywords):
            suggested_category = cat
            break
    
    # Date (default to today, simple extraction)
    from datetime import datetime, timedelta
    date = datetime.now().strftime("%Y-%m-%d")
    
    if "yesterday" in text:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "tomorrow" in text:
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    return {
        "amount": amount,
        "description": description,
        "suggested_category": suggested_category,
        "date": date,
        "parsed": True,
        "error": ""
    }

class ParserAgent:
    """
    Agent 1: Parses user input into structured expense data.
    Student 1's implementation.
    """
    
    def __init__(self, model=None):
        self.name = "ParserAgent"
        # 3.2 3B only used for complex cases, regex handles 90%
    
    def run(self, state: Dict) -> Dict:
        """
        Process user input and extract expense details.
        
        Args:
            state: Must contain 'user_input' key
            
        Returns:
            Updated state with parsed expense data
        """
        user_input = state.get("user_input", "")
        
        # Use deterministic tool first
        result = extract_expense_tool(user_input)
        
        # Update state
        new_state = state.copy()
        new_state["parser_output"] = result
        
        if result["parsed"]:
            new_state["amount"] = result["amount"]
            new_state["description"] = result["description"]
            new_state["suggested_category"] = result["suggested_category"]
            new_state["date"] = result["date"]
            new_state["errors"] = state.get("errors", [])
        else:
            new_state["errors"] = state.get("errors", []) + [
                f"Parser: {result['error']}"
            ]
        
        return new_state