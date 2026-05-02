# tests/test_parser.py
"""
Unit tests for Parser Agent and expense_extractor tool.
Student 1's testing contribution.
Uses built-in unittest (no pytest required).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from datetime import datetime, timedelta
from agents.parser import ParserAgent
from tools.expense_extractor import extract_expense


class TestExtractExpenseTool(unittest.TestCase):
    """Test cases for the extract_expense tool function."""
    
    def test_extract_dollar_sign_amount(self):
        """Test parsing with $ prefix."""
        result = extract_expense("spent $50 on lunch")
        self.assertTrue(result["parsed"])
        self.assertEqual(result["amount"], 50.0)
        self.assertEqual(result["description"], "lunch")
    
    def test_extract_amount_with_cents(self):
        """Test parsing decimal amounts."""
        result = extract_expense("paid $49.99 for dinner")
        self.assertTrue(result["parsed"])
        self.assertEqual(result["amount"], 49.99)
    
    def test_extract_plain_number(self):
        """Test parsing number without currency symbol."""
        result = extract_expense("200")
        self.assertTrue(result["parsed"])
        self.assertEqual(result["amount"], 200.0)
        self.assertEqual(result["description"], "general expense")
    
    def test_extract_large_number(self):
        """Test parsing large amounts (4-6 digits)."""
        result = extract_expense("150000")
        self.assertTrue(result["parsed"])
        self.assertEqual(result["amount"], 150000.0)
    
    def test_extract_with_dollars_word(self):
        """Test parsing 'X dollars' format."""
        result = extract_expense("spent 75 dollars on groceries")
        self.assertTrue(result["parsed"])
        self.assertEqual(result["amount"], 75.0)
    
    def test_extract_spent_keyword(self):
        """Test parsing with 'spent' keyword."""
        result = extract_expense("spent 100 on taxi")
        self.assertEqual(result["amount"], 100.0)
    
    def test_extract_paid_keyword(self):
        """Test parsing with 'paid' keyword."""
        result = extract_expense("paid 250 for utilities")
        self.assertEqual(result["amount"], 250.0)
    
    def test_extract_cost_keyword(self):
        """Test parsing with 'cost me' phrase."""
        result = extract_expense("it cost me 500 for the repair")
        self.assertEqual(result["amount"], 500.0)
    
    def test_category_detection_food(self):
        """Test food category keywords."""
        test_cases = ["$20 lunch", "$15 pizza", "$30 restaurant", "$10 coffee"]
        for case in test_cases:
            result = extract_expense(case)
            self.assertEqual(result["suggested_category"], "food", f"Failed for: {case}")
    
    def test_category_detection_transport(self):
        """Test transport category keywords."""
        test_cases = ["$50 gas", "$25 uber", "$10 bus ticket", "$100 fuel"]
        for case in test_cases:
            result = extract_expense(case)
            self.assertEqual(result["suggested_category"], "transport", f"Failed for: {case}")
    
    def test_category_detection_entertainment(self):
        """Test entertainment category keywords."""
        test_cases = ["$15 movie", "$10 game", "$20 netflix subscription"]
        for case in test_cases:
            result = extract_expense(case)
            self.assertEqual(result["suggested_category"], "entertainment", f"Failed for: {case}")
    
    def test_category_detection_utilities(self):
        """Test utilities category keywords."""
        test_cases = ["$100 electric bill", "$50 water", "$80 internet"]
        for case in test_cases:
            result = extract_expense(case)
            self.assertEqual(result["suggested_category"], "utilities", f"Failed for: {case}")
    
    def test_default_category_other(self):
        """Test default category when no keywords match."""
        result = extract_expense("$500 random purchase")
        self.assertEqual(result["suggested_category"], "other")
    
    def test_date_extraction_yesterday(self):
        """Test 'yesterday' date parsing."""
        result = extract_expense("$40 lunch yesterday")
        expected = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(result["date"], expected)
    
    def test_date_extraction_tomorrow(self):
        """Test 'tomorrow' date parsing."""
        result = extract_expense("$60 dinner tomorrow")
        expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(result["date"], expected)
    
    def test_date_default_today(self):
        """Test default date is today."""
        result = extract_expense("$50 lunch")
        expected = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(result["date"], expected)
    
    def test_no_amount_found(self):
        """Test graceful failure when no amount present."""
        result = extract_expense("went to the store")
        self.assertFalse(result["parsed"])
        self.assertEqual(result["amount"], 0.0)
        self.assertIn("error", result)
        self.assertIn("Could not find", result["error"])
    
    def test_empty_input(self):
        """Test empty string input."""
        result = extract_expense("")
        self.assertFalse(result["parsed"])
        self.assertIn("error", result)
    
    def test_whitespace_only_input(self):
        """Test whitespace-only input."""
        result = extract_expense("   ")
        self.assertFalse(result["parsed"])
    
    def test_special_characters_in_description(self):
        """Test handling special characters."""
        result = extract_expense("$25 lunch @ cafe!")
        self.assertTrue(result["parsed"])
        self.assertIn("cafe", result["description"])
    
    def test_multiple_amounts_takes_first(self):
        """Test that first amount is extracted when multiple present."""
        result = extract_expense("spent 50 on lunch and 30 on coffee")
        self.assertEqual(result["amount"], 50.0)  # Takes first match
    
    def test_case_insensitive(self):
        """Test case insensitivity."""
        result = extract_expense("SPENT $100 ON GROCERIES")
        self.assertTrue(result["parsed"])
        self.assertEqual(result["amount"], 100.0)
    
    def test_very_small_amount(self):
        """Test minimum valid amount."""
        result = extract_expense("$0.01 candy")
        self.assertTrue(result["parsed"])
        self.assertEqual(result["amount"], 0.01)
    
    def test_zero_amount_rejected(self):
        """Test that zero is not valid."""
        result = extract_expense("$0 free item")
        self.assertFalse(result["parsed"])
    
    def test_very_large_amount(self):
        """Test very large amounts."""
        result = extract_expense("999999")
        self.assertTrue(result["parsed"])
        self.assertEqual(result["amount"], 999999.0)


class TestParserAgent(unittest.TestCase):
    """Test cases for ParserAgent class."""
    
    def setUp(self):
        """Setup fresh agent for each test."""
        self.agent = ParserAgent()
    
    def test_agent_initialization(self):
        """Test agent creates correctly."""
        self.assertEqual(self.agent.name, "ParserAgent")
    
    def test_agent_successful_parse(self):
        """Test agent run with valid input."""
        state = {"user_input": "$50 lunch", "errors": []}
        result = self.agent.run(state)
        
        self.assertEqual(result["amount"], 50.0)
        self.assertEqual(result["description"], "lunch")
        self.assertEqual(result["suggested_category"], "food")
        self.assertEqual(result["errors"], [])
    
    def test_agent_failed_parse(self):
        """Test agent run with invalid input."""
        state = {"user_input": "hello world", "errors": []}
        result = self.agent.run(state)
        
        self.assertEqual(result["amount"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Parser:", result["errors"][0])
    
    def test_agent_preserves_existing_errors(self):
        """Test that existing errors are preserved."""
        state = {
            "user_input": "invalid",
            "errors": ["Previous error"]
        }
        result = self.agent.run(state)
        
        self.assertEqual(len(result["errors"]), 2)
        self.assertIn("Previous error", result["errors"])
    
    def test_agent_preserves_other_state(self):
        """Test that unrelated state keys are preserved."""
        state = {
            "user_input": "$25 taxi",
            "errors": [],
            "custom_key": "custom_value"
        }
        result = self.agent.run(state)
        
        self.assertEqual(result["custom_key"], "custom_value")
        self.assertEqual(result["amount"], 25.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)