# tools/category_manager.py
"""
Category management and record preparation tool.
Student 3's custom tool with strict type hinting and docstrings.
"""

from typing import Dict, Optional, TypedDict, List


class CategoryRule(TypedDict):
    """Category validation rule structure."""
    allowed: bool
    requires_description: bool
    min_amount: float
    max_amount: Optional[float]


class PreparedRecord(TypedDict):
    """Database-ready expense record."""
    amount: float
    category: str
    description: str
    date: str
    raw_input: str
    valid: bool
    error: Optional[str]


# Category configuration with validation rules
CATEGORY_CONFIG: Dict[str, CategoryRule] = {
    "food": {
        "allowed": True,
        "requires_description": False,
        "min_amount": 0.01,
        "max_amount": None  # No max for food
    },
    "transport": {
        "allowed": True,
        "requires_description": False,
        "min_amount": 0.01,
        "max_amount": 500.0  # Flag unusually high transport
    },
    "entertainment": {
        "allowed": True,
        "requires_description": True,  # Should explain what entertainment
        "min_amount": 0.01,
        "max_amount": 1000.0
    },
    "utilities": {
        "allowed": True,
        "requires_description": True,
        "min_amount": 0.01,
        "max_amount": None
    },
    "healthcare": {
        "allowed": True,
        "requires_description": False,
        "min_amount": 0.01,
        "max_amount": None  # Medical can be expensive
    },
    "other": {
        "allowed": True,
        "requires_description": True,  # Must explain "other"
        "min_amount": 0.01,
        "max_amount": 2000.0
    }
}


class CategoryManager:
    """
    Manages expense category validation and record preparation.
    
    Confirms category assignments, validates against business rules,
    and prepares database-ready records.
    """
    
    def __init__(self) -> None:
        """Initialize CategoryManager with default rules."""
        self.rules = CATEGORY_CONFIG
    
    def get_valid_categories(self) -> List[str]:
        """
        Return list of valid category names.
        
        Returns:
            List of category strings.
        """
        return list(self.rules.keys())
    
    def validate_category(self, category: str, amount: float, 
                        description: str) -> Dict[str, any]:
        """
        Validate a category assignment against business rules.
        
        Args:
            category: Proposed category name.
            amount: Expense amount.
            description: Expense description.
            
        Returns:
            Validation result with warnings and flags.
        """
        category = category.lower().strip()
        
        if category not in self.rules:
            return {
                "valid": False,
                "final_category": "other",
                "warnings": [f"Unknown category '{category}', defaulting to 'other'"],
                "requires_review": True
            }
        
        rule = self.rules[category]
        warnings = []
        requires_review = False
        
        # Check amount limits
        if rule["max_amount"] and amount > rule["max_amount"]:
            warnings.append(
                f"Amount ${amount} exceeds typical {category} limit of ${rule['max_amount']}"
            )
            requires_review = True
        
        if amount < rule["min_amount"]:
            return {
                "valid": False,
                "final_category": category,
                "warnings": [f"Amount below minimum ${rule['min_amount']}"],
                "requires_review": True
            }
        
        # Check description requirement
        if rule["requires_description"]:
            desc_length = len(description.strip())
            if desc_length < 3 or description.lower() == "general expense":
                warnings.append(
                    f"{category} expenses should have specific descriptions"
                )
                requires_review = True
        
        return {
            "valid": True,
            "final_category": category,
            "warnings": warnings,
            "requires_review": requires_review
        }
    
    def prepare_record(self, amount: float, category: str,
                      description: str, date: str,
                      raw_input: str) -> PreparedRecord:
        """
        Prepare database-ready expense record.
        
        This is the primary tool function used by the Categorizer Agent.
        
        Args:
            amount: Validated expense amount.
            category: Final confirmed category.
            description: Expense description.
            date: ISO format date string.
            raw_input: Original user input text.
            
        Returns:
            PreparedRecord ready for database insertion.
            
        Raises:
            ValueError: If amount is invalid or category is empty.
        """
        if not amount or amount <= 0:
            raise ValueError("Amount must be positive")
        
        if not category:
            raise ValueError("Category cannot be empty")
        
        # Clean description
        clean_desc = description.strip() or "general expense"
        
        # Truncate if too long
        if len(clean_desc) > 100:
            clean_desc = clean_desc[:97] + "..."
        
        return {
            "amount": round(float(amount), 2),
            "category": category.lower().strip(),
            "description": clean_desc,
            "date": date,
            "raw_input": raw_input[:200],  # Limit raw input storage
            "valid": True,
            "error": None
        }
    
    def suggest_category_improvement(self, description: str,
                                    current_category: str) -> Optional[str]:
        """
        Suggest better category based on description keywords.
        
        Args:
            description: Expense description.
            current_category: Currently assigned category.
            
        Returns:
            Suggested better category, or None if current is fine.
        """
        desc_lower = description.lower()
        
        # Re-check keywords against description
        keyword_map = {
            "food": ["lunch", "dinner", "breakfast", "meal", "restaurant", 
                    "coffee", "pizza", "burger", "eat", "grocery"],
            "transport": ["bus", "train", "taxi", "uber", "fuel", "petrol",
                         "commute", "travel", "ticket"],
            "entertainment": ["movie", "cinema", "game", "concert", "show",
                            "netflix", "spotify", "fun"],
            "utilities": ["bill", "electric", "water", "internet", "wifi",
                         "phone", "rent"],
            "healthcare": ["doctor", "medicine", "pharmacy", "hospital",
                          "medical", "dental", "clinic"]
        }
        
        for cat, keywords in keyword_map.items():
            if cat != current_category and any(kw in desc_lower for kw in keywords):
                return cat
        
        return None