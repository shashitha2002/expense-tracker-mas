import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import sqlite3
import tempfile
from agents.validator import ValidatorAgent
from tools.budget import BudgetManager, DEFAULT_BUDGETS


class TestBudgetManagerTool(unittest.TestCase):
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.manager = BudgetManager(db_path=self.temp_db.name)
    
    def tearDown(self):
        import os
        os.unlink(self.temp_db.name)
    
    def test_initialization_creates_tables(self):
        result = self.manager.get_all_budgets()
        self.assertEqual(len(result), 6)
        
    def test_default_budgets_loaded(self):
        budgets = self.manager.get_all_budgets()
        
        self.assertIn("food", budgets)
        self.assertEqual(budgets["food"]["monthly_limit"], 500.0)
        self.assertEqual(budgets["food"]["current_spent"], 0.0)
        
        self.assertIn("transport", budgets)
        self.assertEqual(budgets["transport"]["monthly_limit"], 200.0)
    
    def test_get_budget_existing(self):
        result = self.manager.get_budget("food")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "food")
        self.assertEqual(result["monthly_limit"], 500.0)
        self.assertEqual(result["remaining"], 500.0)
        self.assertEqual(result["percent_used"], 0.0)
    
    def test_get_budget_nonexistent(self):
        result = self.manager.get_budget("luxury")
        self.assertIsNone(result)
    
    def test_add_spending_updates_budget(self):
        self.manager.add_spending("food", 50.0)
        
        budget = self.manager.get_budget("food")
        self.assertEqual(budget["current_spent"], 50.0)
        self.assertEqual(budget["remaining"], 450.0)
        self.assertEqual(budget["percent_used"], 10.0)
    
    def test_add_spending_multiple(self):
        self.manager.add_spending("transport", 20.0)
        self.manager.add_spending("transport", 30.0)
        
        budget = self.manager.get_budget("transport")
        self.assertEqual(budget["current_spent"], 50.0)
    
    def test_add_spending_invalid_amount_zero(self):
        with self.assertRaises(ValueError):
            self.manager.add_spending("food", 0)
    
    def test_add_spending_invalid_amount_negative(self):
        with self.assertRaises(ValueError):
            self.manager.add_spending("food", -10.0)
    
    def test_validate_expense_within_budget(self):
        result = self.manager.validate_expense("food", 100.0)
        
        self.assertTrue(result["valid"])
        self.assertFalse(result["warning"])
        self.assertEqual(result["remaining"], 400.0)
        self.assertEqual(result["over_by"], 0.0)
        self.assertIn("Within budget", result["message"])
    
    def test_validate_expense_exactly_at_limit(self):
        self.manager.add_spending("food", 400.0)
        
        result = self.manager.validate_expense("food", 100.0)
        
        self.assertTrue(result["valid"])
        self.assertFalse(result["warning"])
        self.assertEqual(result["remaining"], 0.0)
    
    def test_validate_expense_over_budget(self):
        self.manager.add_spending("entertainment", 100.0)
        
        result = self.manager.validate_expense("entertainment", 75.0)
        
        self.assertTrue(result["valid"])
        self.assertTrue(result["warning"])
        self.assertEqual(result["over_by"], 25.0)
        self.assertIn("Over budget", result["message"])
    
    def test_validate_expense_no_budget_set(self):
        result = self.manager.validate_expense("nonexistent", 100.0)
        
        self.assertTrue(result["valid"])
        self.assertFalse(result["warning"])
        self.assertIn("No budget set", result["message"])
    
    def test_validate_expense_invalid_amount_zero(self):
        with self.assertRaises(ValueError):
            self.manager.validate_expense("food", 0)
    
    def test_validate_expense_invalid_amount_negative(self):
        with self.assertRaises(ValueError):
            self.manager.validate_expense("food", -50.0)
    
    def test_reset_monthly_spending(self):
        self.manager.add_spending("food", 100.0)
        self.manager.add_spending("transport", 50.0)
        
        self.manager.reset_monthly_spending()
        
        budgets = self.manager.get_all_budgets()
        for cat, data in budgets.items():
            self.assertEqual(data["current_spent"], 0.0)
            self.assertEqual(data["remaining"], data["monthly_limit"])
    
    def test_update_budget_limit_success(self):
        result = self.manager.update_budget_limit("food", 1000.0)
        self.assertTrue(result)
        
        budget = self.manager.get_budget("food")
        self.assertEqual(budget["monthly_limit"], 1000.0)
    
    def test_update_budget_limit_nonexistent(self):
        result = self.manager.update_budget_limit("nonexistent", 500.0)
        self.assertFalse(result)
    
    def test_update_budget_limit_negative(self):
        with self.assertRaises(ValueError):
            self.manager.update_budget_limit("food", -100.0)
    
    def test_percent_used_calculation(self):
        self.manager.add_spending("food", 250.0)
        
        budget = self.manager.get_budget("food")
        self.assertEqual(budget["percent_used"], 50.0)
    
    def test_percent_used_zero_limit(self):
        self.manager.update_budget_limit("other", 0.0)
        
        budget = self.manager.get_budget("other")
        self.assertEqual(budget["percent_used"], 0.0)


class TestValidatorAgent(unittest.TestCase):
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.agent = ValidatorAgent()
        self.agent.budget = BudgetManager(db_path=self.temp_db.name)
    
    def tearDown(self):
        import os
        os.unlink(self.temp_db.name)
    
    def test_agent_initialization(self):
        self.assertEqual(self.agent.name, "ValidatorAgent")
        self.assertIsInstance(self.agent.budget, BudgetManager)
    
    def test_agent_run_success_within_budget(self):
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
        self.agent.budget.add_spending("food", 480.0)
        
        state = {
            "amount": 50.0,
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertTrue(result["validation"]["valid"])
        self.assertTrue(result["validation"]["warning"])
        self.assertEqual(result["validation"]["over_by"], 30.0)
        self.assertIn("Over budget", result["validation"]["message"])
    
    def test_agent_run_invalid_amount_zero(self):
        state = {
            "amount": 0,
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertFalse(result["validation"]["valid"])
        self.assertIn("Invalid amount", result["validation"]["message"])
    
    def test_agent_run_invalid_amount_negative(self):
        state = {
            "amount": -10.0,
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertFalse(result["validation"]["valid"])
    
    def test_agent_run_no_category(self):
        state = {
            "amount": 50.0,
            "suggested_category": None,
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertTrue(result["validation"]["valid"])
    
    def test_agent_preserves_existing_state(self):
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
        self.agent.budget.add_spending("food", 40.0)
        
        state = {
            "amount": 10.0,
            "suggested_category": "food",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertEqual(result["budget_status"]["current_spent"], 40.0)
        self.assertEqual(result["validation"]["remaining"], 450.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)