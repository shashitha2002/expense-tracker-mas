import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from agents.categorizer import CategorizerAgent
from tools.category_manager import CategoryManager, CATEGORY_CONFIG


class TestCategoryManagerTool(unittest.TestCase):

    def setUp(self):
        self.manager = CategoryManager()

    def test_initialization(self):
        self.assertEqual(len(self.manager.rules), 6)
        self.assertIn("food", self.manager.rules)
        self.assertIn("transport", self.manager.rules)

    def test_get_valid_categories(self):
        categories = self.manager.get_valid_categories()
        self.assertIsInstance(categories, list)
        self.assertIn("food", categories)
        self.assertIn("other", categories)
        self.assertEqual(len(categories), 6)

    def test_validate_category_food_valid(self):
        result = self.manager.validate_category("food", 50.0, "lunch")
        self.assertTrue(result["valid"])
        self.assertEqual(result["final_category"], "food")
        self.assertFalse(result["requires_review"])

    def test_validate_category_unknown_defaults_to_other(self):
        result = self.manager.validate_category("invalid_category", 100.0, "test")
        self.assertFalse(result["valid"])
        self.assertEqual(result["final_category"], "other")
        self.assertTrue(result["requires_review"])

    def test_validate_category_amount_too_high(self):
        result = self.manager.validate_category("transport", 600.0, "taxi")
        self.assertTrue(result["valid"])
        self.assertTrue(result["requires_review"])
        self.assertIn("exceeds", str(result["warnings"]))

    def test_validate_category_amount_below_minimum(self):
        result = self.manager.validate_category("food", 0.001, "candy")
        self.assertFalse(result["valid"])
        self.assertIn("below minimum", str(result["warnings"]))

    def test_validate_category_requires_description(self):
        result = self.manager.validate_category(
            "entertainment", 50.0, "general expense"
        )
        self.assertTrue(result["valid"])
        self.assertTrue(result["requires_review"])
        self.assertIn("specific descriptions", str(result["warnings"]))

    def test_validate_category_short_description(self):
        result = self.manager.validate_category("entertainment", 30.0, "x")
        self.assertTrue(result["valid"])
        self.assertTrue(result["requires_review"])

    def test_prepare_record_success(self):
        record = self.manager.prepare_record(
            amount=50.0,
            category="food",
            description="lunch at cafe",
            date="2026-04-19",
            raw_input="spent $50 on lunch at cafe"
        )

        self.assertTrue(record["valid"])
        self.assertEqual(record["amount"], 50.0)
        self.assertEqual(record["category"], "food")
        self.assertEqual(record["description"], "lunch at cafe")
        self.assertEqual(record["date"], "2026-04-19")
        self.assertIn("lunch at cafe", record["raw_input"])

    def test_prepare_record_amount_rounding(self):
        record = self.manager.prepare_record(
            amount=49.999,
            category="food",
            description="test",
            date="2026-04-19",
            raw_input="test"
        )
        self.assertEqual(record["amount"], 50.0)

    def test_prepare_record_description_truncation(self):
        long_desc = "a" * 150
        record = self.manager.prepare_record(
            amount=10.0,
            category="other",
            description=long_desc,
            date="2026-04-19",
            raw_input="test"
        )
        self.assertEqual(len(record["description"]), 100)

    def test_prepare_record_empty_description(self):
        record = self.manager.prepare_record(
            amount=25.0,
            category="transport",
            description="",
            date="2026-04-19",
            raw_input="test"
        )
        self.assertEqual(record["description"], "general expense")

    def test_prepare_record_raw_input_limit(self):
        long_input = "x" * 300
        record = self.manager.prepare_record(
            amount=10.0,
            category="food",
            description="test",
            date="2026-04-19",
            raw_input=long_input
        )
        self.assertEqual(len(record["raw_input"]), 200)

    def test_prepare_record_invalid_amount_zero(self):
        with self.assertRaises(ValueError) as context:
            self.manager.prepare_record(
                amount=0,
                category="food",
                description="test",
                date="2026-04-19",
                raw_input="test"
            )
        self.assertIn("positive", str(context.exception))

    def test_prepare_record_invalid_amount_negative(self):
        with self.assertRaises(ValueError):
            self.manager.prepare_record(
                amount=-10.0,
                category="food",
                description="test",
                date="2026-04-19",
                raw_input="test"
            )

    def test_prepare_record_empty_category(self):
        with self.assertRaises(ValueError):
            self.manager.prepare_record(
                amount=10.0,
                category="",
                description="test",
                date="2026-04-19",
                raw_input="test"
            )

    def test_suggest_category_improvement_food(self):
        result = self.manager.suggest_category_improvement(
            "pizza dinner with friends", "other"
        )
        self.assertEqual(result, "food")

    def test_suggest_category_improvement_transport(self):
        result = self.manager.suggest_category_improvement(
            "uber ride to airport", "other"
        )
        self.assertEqual(result, "transport")

    def test_suggest_category_improvement_entertainment(self):
        result = self.manager.suggest_category_improvement(
            "netflix and chill subscription", "other"
        )
        self.assertEqual(result, "entertainment")

    def test_suggest_category_improvement_no_change_needed(self):
        result = self.manager.suggest_category_improvement(
            "lunch at restaurant", "food"
        )
        self.assertIsNone(result)

    def test_category_config_structure(self):
        for cat, rules in CATEGORY_CONFIG.items():
            self.assertIn("allowed", rules)
            self.assertIn("requires_description", rules)
            self.assertIn("min_amount", rules)
            self.assertIn("max_amount", rules)
            self.assertIsInstance(rules["allowed"], bool)


class TestCategorizerAgent(unittest.TestCase):

    def setUp(self):
        self.agent = CategorizerAgent()

    def test_agent_initialization(self):
        self.assertEqual(self.agent.name, "CategorizerAgent")
        self.assertIsInstance(self.agent.manager, CategoryManager)

    def test_agent_run_success(self):
        state = {
            "amount": 50.0,
            "suggested_category": "food",
            "description": "lunch",
            "date": "2026-04-19",
            "user_input": "spent $50 on lunch"
        }

        result = self.agent.run(state)

        self.assertEqual(result["final_category"], "food")
        self.assertTrue(result["ready_to_store"])
        self.assertTrue(result["db_record"]["valid"])
        self.assertEqual(result["db_record"]["amount"], 50.0)

    def test_agent_run_invalid_amount(self):
        state = {
            "amount": 0,
            "suggested_category": "food",
            "description": "test",
            "date": "2026-04-19",
            "user_input": "test"
        }

        result = self.agent.run(state)

        self.assertEqual(result["final_category"], "invalid")
        self.assertFalse(result["ready_to_store"])
        self.assertIn("error", result)

    def test_agent_run_none_amount(self):
        state = {
            "amount": None,
            "suggested_category": "food",
            "description": "test",
            "date": "2026-04-19",
            "user_input": "test"
        }

        result = self.agent.run(state)

        self.assertEqual(result["final_category"], "invalid")
        self.assertFalse(result["ready_to_store"])

    def test_agent_run_unknown_category(self):
        state = {
            "amount": 100.0,
            "suggested_category": "luxury",
            "description": "watch",
            "date": "2026-04-19",
            "user_input": "bought luxury watch"
        }

        result = self.agent.run(state)

        self.assertEqual(result["final_category"], "other")
        self.assertTrue(result["ready_to_store"])

    def test_agent_preserves_existing_state(self):
        state = {
            "amount": 25.0,
            "suggested_category": "transport",
            "description": "bus",
            "date": "2026-04-19",
            "user_input": "$25 bus",
            "custom_key": "custom_value",
            "errors": []
        }

        result = self.agent.run(state)

        self.assertEqual(result["custom_key"], "custom_value")
        self.assertEqual(result["errors"], [])

    def test_agent_captures_warnings(self):
        state = {
            "amount": 600.0,
            "suggested_category": "transport",
            "description": "taxi",
            "date": "2026-04-19",
            "user_input": "spent $600 on taxi"
        }

        result = self.agent.run(state)

        self.assertTrue(result["requires_review"])
        self.assertGreater(len(result["validation_warnings"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
