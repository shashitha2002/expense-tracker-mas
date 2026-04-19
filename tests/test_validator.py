# tests/test_validator.py
"""
Unit tests for Validator Agent and budget tool.
Student 2's testing contribution.
Uses built-in unittest (no pytest required).
"""

# Fix import path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import sqlite3
import tempfile
from agents.validator import ValidatorAgent
from tools.budget import BudgetManager, DEFAULT_BUDGETS


class TestBudgetManagerTool(unittest.TestCase):
    """Test cases for BudgetManager tool class."""
    
    def setUp(self):
        """Setup fresh manager with temp database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.manager = BudgetManager(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up temp database."""
        import os
        os.unlink(self.temp_db.name)
    
    def test_initialization_creates_tables(self):
        """Test that initialization creates budget table."""
        # Should not raise, table exists
        result = self.manager.get_all_budgets()
        self.assertEqual(len(result), 6)  # 6 default categories
    
    def test_default_budgets_loaded(self):
        """Test that default budgets are seeded."""
        budgets = self.manager.get_all_budgets()
        
        self.assertIn("food", budgets)
        self.assertEqual(budgets["food"]["monthly_limit"], 500.0)
        self.assertEqual(budgets["food"]["current_spent"], 0.0)
        
        self.assertIn("transport", budgets)
        self.assertEqual(budgets["transport"]["monthly_limit"], 200.0)
    
    def test_get_budget_existing(self):
        """Test retrieval of existing budget."""
        result = self.manager.get_budget("food")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["monthly_limit"], 500.0)
        self.assertEqual(result["remaining"], 500.0)
        self.assertEqual(result["percent_used"], 0.0)
    
    def test_get_budget_nonexistent(self):
        """Test retrieval of non-existent budget."""
        result = self.manager.get_budget("luxury")
        self.assertIsNone(result)
    
    def test_add_spending_updates_budget(self):
        """Test that spending is added to budget."""
        self.manager.add_spending("food", 50.0)
        
        budget = self.manager.get_budget("food")
        self.assertEqual(budget["current_spent"], 50.0)
        self.assertEqual(budget["remaining"], 450.0)
        self.assertEqual(budget["percent_used"], 10.0)
    
    def test_add_spending_multiple(self):
        """Test multiple spending additions."""
        self.manager.add_spending("transport", 20.0)
        self.manager.add_spending("transport", 30.0)
        
        budget = self.manager.get_budget("transport")
        self.assertEqual(budget["current_spent"], 50.0)
    
    def test_add_spending_invalid_amount_zero(self):
        """Test that zero amount raises error."""
        with self.assertRaises(ValueError):
            self.manager.add_spending("food", 0)
    
    def test_add_spending_invalid_amount_negative(self):
        """Test that negative amount raises error."""
        with self.assertRaises(ValueError):
            self.manager.add_spending("food", -10.0)
    
    def test_validate_expense_within_budget(self):
        """Test validation when expense is within budget."""
        result = self.manager.validate_expense("food", 100.0)
        
        self.assertTrue(result["valid"])
        self.assertFalse(result["warning"])
        self.assertEqual(result["remaining"], 400.0)
        self.assertEqual(result["over_by"], 0.0)
        self.assertIn("Within budget", result["message"])
    
    def test_validate_expense_exactly_at_limit(self):
        """Test validation when expense equals remaining budget."""
        # Add some spending first
        self.manager.add_spending("food", 400.0)  # 100 remaining
        
        result = self.manager.validate_expense("food", 100.0)
        
        self.assertTrue(result["valid"])
        self.assertFalse(result["warning"])
        self.assertEqual(result["remaining"], 0.0)
    
    def test_validate_expense_over_budget(self):
        """Test validation when expense exceeds budget."""
        self.manager.add_spending("entertainment", 100.0)  # 50 remaining
        
        result = self.manager.validate_expense("entertainment", 75.0)
        
        self.assertTrue(result["valid"])  # Still valid, just warning
        self.assertTrue(result["warning"])
        self.assertEqual(result["over_by"], 25.0)
        self.assertIn("Over budget", result["message"])
    
    def test_validate_expense_no_budget_set(self):
        """Test validation for category without budget."""
        result = self.manager.validate_expense("nonexistent", 100.0)
        
        self.assertTrue(result["valid"])
        self.assertFalse(result["warning"])
        self.assertIn("No budget set", result["message"])
    
    def test_validate_expense_invalid_amount_zero(self):
        """Test validation with zero amount raises error."""
        with self.assertRaises(ValueError):
            self.manager.validate_expense("food", 0)
    
    def test_validate_expense_invalid_amount_negative(self):
        """Test validation with negative amount raises error."""
        with self.assertRaises(ValueError):
            self.manager.validate_expense("food", -50.0)
    
    def test_reset_monthly_spending(self):
        """Test resetting all spending to zero."""
        # Add spending first
        self.manager.add_spending("food", 100.0)
        self.manager.add_spending("transport", 50.0)
        
        # Reset
        self.manager.reset_monthly_spending()
        
        # Verify
        budgets = self.manager.get_all_budgets()
        for cat, data in budgets.items():
            self.assertEqual(data["current_spent"], 0.0)
            self.assertEqual(data["remaining"], data["monthly_limit"])
    
    def test_update_budget_limit_success(self):
        """Test updating budget limit."""
        result = self.manager.update_budget_limit("food", 1000.0)
        self.assertTrue(result)
        
        budget = self.manager.get_budget("food")
        self.assertEqual(budget["monthly_limit"], 1000.0)
    
    def test_update_budget_limit_nonexistent(self):
        """Test updating non-existent budget returns False."""
        result = self.manager.update_budget_limit("nonexistent", 500.0)
        self.assertFalse(result)
    
    def test_update_budget_limit_negative(self):
        """Test that negative limit raises error."""
        with self.assertRaises(ValueError):
            self.manager.update_budget_limit("food", -100.0)
    
    def test_percent_used_calculation(self):
        """Test percentage used calculation."""
        self.manager.add_spending("food", 250.0)  # Half of 500
        
        budget = self.manager.get_budget("food")
        self.assertEqual(budget["percent_used"], 50.0)
    
    def test_percent_used_zero_limit(self):
        """Test handling of zero limit (edge case)."""
        # Manually set limit to 0
        self.manager.update_budget_limit("other", 0.0)
        
        budget = self.manager.get_budget("other")
        self.assertEqual(budget["percent_used"], 0.0)


class TestValidatorAgent(unittest.TestCase):
    """Test cases for ValidatorAgent class."""
    
    def setUp(self):
        """Setup fresh agent with temp database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.agent = ValidatorAgent()
        # Replace agent's budget manager with temp one
        self.agent.budget = BudgetManager(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up."""
        import os
        os.unlink(self.temp_db.name)
    
    def test_agent_initialization(self):
        """Test agent creates correctly."""
        self.assertEqual(self.agent.name, "ValidatorAgent")
        self.assertIsInstance(self.agent.budget, BudgetManager)
    
    def test_agent_run_success_within_budget(self):
        """Test successful validation within budget."""
        state = {
            "amount": 50.0,
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertTrue(result["validation"]["valid"])
        self.assertFalse(result["validation"]["warning"])
        self.assertEqual(result["validation"]["remaining"], 450.0)
        self.assertIn("budget_status", result)
        self.assertEqual(result["budget_status"]["category"], "food")
    
    def test_agent_run_over_budget(self):
        """Test validation when over budget."""
        # Pre-spend most of food budget
        self.agent.budget.add_spending("food", 480.0)  # 20 remaining
        
        state = {
            "amount": 50.0,  # 30 over
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertTrue(result["validation"]["valid"])
        self.assertTrue(result["validation"]["warning"])
        self.assertEqual(result["validation"]["over_by"], 30.0)
        self.assertIn("Over budget", result["validation"]["message"])
    
    def test_agent_run_invalid_amount_zero(self):
        """Test handling of zero amount."""
        state = {
            "amount": 0,
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertFalse(result["validation"]["valid"])
        self.assertIn("Invalid amount", result["validation"]["message"])
    
    def test_agent_run_invalid_amount_negative(self):
        """Test handling of negative amount."""
        state = {
            "amount": -10.0,
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertFalse(result["validation"]["valid"])
    
    def test_agent_run_no_category(self):
        """Test handling of missing category."""
        state = {
            "amount": 50.0,
            "suggested_category": None,
            "errors": []
        }
        
        result = self.agent.run(state)
        
        # Should default to "other" or handle gracefully
        self.assertTrue(result["validation"]["valid"])
    
    def test_agent_preserves_existing_state(self):
        """Test that existing state keys are preserved."""
        state = {
            "amount": 25.0,
            "suggested_category": "transport",
            "custom_key": "custom_value",
            "parser_output": {"test": "data"},
            "errors": ["existing_error"]
        }
        
        result = self.agent.run(state)
        
        self.assertEqual(result["custom_key"], "custom_value")
        self.assertEqual(result["parser_output"]["test"], "data")
        self.assertIn("existing_error", result["errors"])
    
    def test_agent_reads_budget_status(self):
        """Test that agent correctly reads current budget status."""
        # Pre-add spending to simulate previous transactions
        self.agent.budget.add_spending("food", 40.0)
        
        state = {
            "amount": 10.0,
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        # Should show remaining budget after previous spending
        self.assertEqual(result["budget_status"]["current_spent"], 40.0)
        self.assertEqual(result["validation"]["remaining"], 450.0)  # 500 - 40 - 10


if __name__ == "__main__":
    unittest.main(verbosity=2)