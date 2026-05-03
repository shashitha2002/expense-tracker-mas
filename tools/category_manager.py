from typing import Dict, Optional, TypedDict, List


class CategoryRule(TypedDict):
    allowed: bool
    requires_description: bool
    min_amount: float
    max_amount: Optional[float]


class PreparedRecord(TypedDict):
    amount: float
    category: str
    description: str
    date: str
    raw_input: str
    valid: bool
    error: Optional[str]


CATEGORY_CONFIG: Dict[str, CategoryRule] = {
    "food": {
        "allowed": True,
        "requires_description": False,
        "min_amount": 0.01,
        "max_amount": None
    },
    "transport": {
        "allowed": True,
        "requires_description": False,
        "min_amount": 0.01,
        "max_amount": 500.0  # Flag unusually high transport spend for review
    },
    "entertainment": {
        "allowed": True,
        "requires_description": True,
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
        "max_amount": None
    },
    "other": {
        "allowed": True,
        "requires_description": True,
        "min_amount": 0.01,
        "max_amount": 2000.0
    }
}


class CategoryManager:

    def __init__(self) -> None:
        self.rules = CATEGORY_CONFIG

    def get_valid_categories(self) -> List[str]:
        return list(self.rules.keys())

    def validate_category(self, category: str, amount: float,
                        description: str) -> Dict[str, any]:
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
        if not amount or amount <= 0:
            raise ValueError("Amount must be positive")

        if not category:
            raise ValueError("Category cannot be empty")

        clean_desc = description.strip() or "general expense"

        if len(clean_desc) > 100:
            clean_desc = clean_desc[:97] + "..."

        return {
            "amount": round(float(amount), 2),
            "category": category.lower().strip(),
            "description": clean_desc,
            "date": date,
            "raw_input": raw_input[:200],
            "valid": True,
            "error": None
        }

    def suggest_category_improvement(self, description: str,
                                    current_category: str) -> Optional[str]:
        desc_lower = description.lower()

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
