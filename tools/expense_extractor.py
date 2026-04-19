# tools/expense_extractor.py
"""
Expense extraction tool for natural language input.
Student 1's custom tool with strict type hinting and docstrings.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict


class ExtractedExpense(TypedDict):
    """Structured output from expense extraction."""
    amount: float
    description: str
    suggested_category: str
    date: str
    parsed: bool
    error: str


# Keyword maps for categorization
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "food": [
        "food", "grocery", "groceries", "restaurant", "lunch",
        "dinner", "breakfast", "coffee", "meal", "eat", "pizza",
        "burger", "snack", "lunch", "biryani", "kottu"
    ],
    "transport": [
        "gas", "uber", "taxi", "bus", "train", "fuel",
        "car", "transport", "commute", "drive", "pickme",
        "tuk", "petrol", "diesel"
    ],
    "entertainment": [
        "movie", "game", "netflix", "spotify", "fun",
        "entertainment", "concert", "show", "party",
        "cinema", "theater", "pub", "trip"
    ],
    "utilities": [
        "electric", "water", "bill", "internet", "phone",
        "rent", "utility", "wifi", "broadband", "electricity",
        "current", "water bill"
    ],
    "healthcare": [
        "doctor", "medicine", "pharmacy", "hospital",
        "clinic", "medical", "dental", "health"
    ]
}

AMOUNT_PATTERNS: List[str] = [
    r'\$(\d+(?:\.\d{2})?)',                    # $50 or $50.00
    r'(\d+(?:\.\d{2})?)\s*(?:dollars?|usd)',   # 50 dollars
    r'\b(\d{4,6})\b',                          # 200000 (plain large number)
    r'\b(\d{2,3})\b',                          # 50, 99 (common amounts)
    r'spent\s+(\d+(?:\.\d{2})?)',              # spent 50
    r'paid\s+(\d+(?:\.\d{2})?)',               # paid 50
    r'cost\s+(?:me\s+)?(\d+(?:\.\d{2})?)',     # cost me 50
]


def _extract_amount(text: str) -> Optional[float]:
    """
    Extract the first valid monetary amount from input text.
    
    Args:
        text: Lowercase input string.
        
    Returns:
        Positive float amount, or None if no amount found.
    """
    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                value = float(match.group(1))
                if value > 0:
                    return value
            except (ValueError, IndexError):
                continue
    return None


def _extract_description(text: str, user_input: str) -> str:
    """
    Extract description from expense text.
    
    Args:
        text: Lowercase processed text.
        user_input: Original raw input for fallback.
        
    Returns:
        Clean description string.
    """
    description = "general expense"
    
    # Try to find description after common prepositions
    for indicator in [" on ", " for ", " at "]:
        if indicator in text:
            parts = text.split(indicator, 1)
            if len(parts) > 1:
                desc = parts[1]
                # Remove amount mentions and extra whitespace
                desc = re.sub(r'[\$\d]+\.?\d*', '', desc).strip()
                # Remove trailing punctuation
                desc = re.sub(r'[.,;]+$', '', desc).strip()
                if desc and len(desc) > 1:
                    description = desc
                    break
    
    # Fallback: use input minus numbers
    if description == "general expense":
        desc_text = re.sub(r'[\$\d]+\.?\d*', '', user_input).strip()
        desc_text = re.sub(r'[^\w\s]', '', desc_text).strip()
        if desc_text and len(desc_text) > 1:
            description = desc_text
    
    return description or "general expense"


def _detect_category(text: str) -> str:
    """
    Detect expense category from keywords.
    
    Args:
        text: Lowercase input text.
        
    Returns:
        Category string (defaults to "other").
    """
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "other"


def _extract_date(text: str) -> str:
    """
    Extract or infer date from input text.
    
    Args:
        text: Lowercase input text.
        
    Returns:
        ISO format date string (YYYY-MM-DD).
    """
    today = datetime.now()
    date = today.strftime("%Y-%m-%d")
    
    if "yesterday" in text:
        date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "tomorrow" in text:
        date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "last week" in text:
        date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    
    return date


def extract_expense(user_input: str) -> ExtractedExpense:
    """
    Extract structured expense data from natural language input.
    
    This is the primary tool function used by the Parser Agent.
    It uses deterministic regex (no LLM) for reliable, fast extraction.
    
    Args:
        user_input: Raw user input string. Examples:
            - "spent $50 on lunch"
            - "200000"
            - "paid $25 for gas yesterday"
            
    Returns:
        ExtractedExpense dictionary with all fields populated.
        If parsing fails, 'parsed' will be False and 'error' contains details.
        
    Raises:
        No exceptions raised; errors are captured in the returned dict.
    """
    if not user_input or not isinstance(user_input, str):
        return {
            "amount": 0.0,
            "description": "",
            "suggested_category": "",
            "date": "",
            "parsed": False,
            "error": "Input must be a non-empty string"
        }
    
    text = user_input.lower().strip()
    
    # Extract amount
    amount = _extract_amount(text)
    if amount is None:
        return {
            "amount": 0.0,
            "description": "",
            "suggested_category": "",
            "date": "",
            "parsed": False,
            "error": (
                "Could not find valid amount. "
                "Try formats like: '$50 lunch', 'spent 200 on groceries', '100'"
            )
        }
    
    # Extract metadata
    description = _extract_description(text, user_input)
    category = _detect_category(text)
    date = _extract_date(text)
    
    return {
        "amount": amount,
        "description": description,
        "suggested_category": category,
        "date": date,
        "parsed": True,
        "error": ""
    }