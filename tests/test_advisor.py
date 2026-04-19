# tests/test_advisor.py
"""
Unit tests for Advisor Agent and llm_advisor tool.
Student 4's testing contribution.
Uses built-in unittest (no pytest required).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, patch
from agents.advisor import AdvisorAgent
from tools.llm_advisor import LLMAdvisor


class TestLLMAdvisorTool(unittest.TestCase):
    """Test cases for LLMAdvisor tool class."""
    
    def setUp(self):
        """Setup fresh advisor for each test."""
        self.advisor = LLMAdvisor(model_name="llama3.2:3b")
    
    def test_initialization(self):
        """Test advisor initializes correctly."""
        self.assertEqual(self.advisor.model_name, "llama3.2:3b")
        self.assertEqual(self.advisor.temperature, 0.3)
    
    def test_fallback_advice_over_budget(self):
        """Test fallback when over budget."""
        data = {
            "amount": 100.0,
            "category": "food",
            "budget_remaining": -20.0,
            "over_budget": True,
            "monthly_total": None,
            "transaction_count": None
        }
        
        result = self.advisor._fallback_advice(data)
        
        self.assertEqual(result["tone"], "warning")
        self.assertEqual(result["confidence"], 1.0)
        self.assertIn("over budget", result["advice"].lower())
        self.assertIn("$100", result["advice"])
    
    def test_fallback_advice_low_budget(self):
        """Test fallback when budget is low."""
        data = {
            "amount": 30.0,
            "category": "entertainment",
            "budget_remaining": 25.0,
            "over_budget": False,
            "monthly_total": None,
            "transaction_count": None
        }
        
        result = self.advisor._fallback_advice(data)
        
        self.assertEqual(result["tone"], "warning")
        self.assertIn("25", result["advice"])
    
    def test_fallback_advice_healthy_budget(self):
        """Test fallback with healthy budget."""
        data = {
            "amount": 50.0,
            "category": "transport",
            "budget_remaining": 150.0,
            "over_budget": False,
            "monthly_total": None,
            "transaction_count": None
        }
        
        result = self.advisor._fallback_advice(data)
        
        self.assertEqual(result["tone"], "positive")
        self.assertIn("$50", result["advice"])
        self.assertIn("150", result["advice"])
    
    def test_generate_advice_invalid_amount(self):
        """Test handling of invalid amount."""
        data = {
            "amount": 0,
            "category": "food",
            "budget_remaining": 100.0,
            "over_budget": False,
            "monthly_total": None,
            "transaction_count": None
        }
        
        result = self.advisor.generate_advice(data, use_llm=False)
        
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("invalid", result["advice"].lower())
    
    def test_generate_advice_negative_amount(self):
        """Test handling of negative amount."""
        data = {
            "amount": -50.0,
            "category": "food",
            "budget_remaining": 100.0,
            "over_budget": False,
            "monthly_total": None,
            "transaction_count": None
        }
        
        result = self.advisor.generate_advice(data, use_llm=False)
        
        self.assertEqual(result["confidence"], 0.0)
    
    def test_build_prompt_contains_key_info(self):
        """Test prompt construction includes all data."""
        data = {
            "amount": 75.0,
            "category": "utilities",
            "budget_remaining": 225.0,
            "over_budget": False,
            "monthly_total": None,
            "transaction_count": None
        }
        
        prompt = self.advisor._build_prompt(data)
        
        # Check that key info is in prompt
        self.assertIn("utilities", prompt)
        self.assertIn("within budget", prompt)
    
    def test_generate_summary_advice(self):
        """Test monthly summary generation."""
        monthly_data = {
            "total": 500.0,
            "top_category": "food",
            "transaction_count": 10,
            "over_budget_categories": ["entertainment"]
        }
        
        result = self.advisor.generate_summary_advice(monthly_data)
        
        self.assertIn("$500", result)
        self.assertIn("food", result)
        self.assertIn("10", result)
    
    def test_advice_not_empty(self):
        """Test that advice is never empty string."""
        test_cases = [
            {"amount": 1.0, "category": "food", "budget_remaining": 99.0, 
             "over_budget": False, "monthly_total": None, "transaction_count": None},
            {"amount": 999.0, "category": "other", "budget_remaining": -100.0,
             "over_budget": True, "monthly_total": None, "transaction_count": None},
        ]
        
        for case in test_cases:
            result = self.advisor.generate_advice(case, use_llm=False)
            self.assertGreater(len(result["advice"]), 0)
            self.assertIsInstance(result["advice"], str)
    
    def test_tone_values_valid(self):
        """Test tone is always one of allowed values."""
        test_cases = [
            (100.0, 50.0, False, "positive"),
            (100.0, 10.0, False, "warning"),
            (100.0, -20.0, True, "warning"),
        ]
        
        for amount, remaining, over, expected_tone in test_cases:
            data = {
                "amount": amount,
                "category": "food",
                "budget_remaining": remaining,
                "over_budget": over,
                "monthly_total": None,
                "transaction_count": None
            }
            result = self.advisor.generate_advice(data, use_llm=False)
            self.assertIn(result["tone"], ["positive", "neutral", "warning"])
    
    def test_confidence_range(self):
        """Test confidence is always 0.0 to 1.0."""
        data = {
            "amount": 50.0,
            "category": "food",
            "budget_remaining": 100.0,
            "over_budget": False,
            "monthly_total": None,
            "transaction_count": None
        }
        
        result = self.advisor.generate_advice(data, use_llm=False)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)


class TestAdvisorAgent(unittest.TestCase):
    """Test cases for AdvisorAgent class."""
    
    def setUp(self):
        """Setup fresh agent for each test."""
        self.agent = AdvisorAgent()
    
    def test_agent_initialization(self):
        """Test agent creates correctly."""
        self.assertEqual(self.agent.name, "AdvisorAgent")
        self.assertIsInstance(self.agent.advisor, LLMAdvisor)
    
    def test_agent_run_success(self):
        """Test successful advice generation."""
        state = {
            "amount": 50.0,
            "final_category": "food",
            "validation": {
                "remaining": 450.0,
                "warning": False
            },
            "budget_status": {},
            "date": "2026-04-19"
        }
        
        result = self.agent.run(state)
        
        self.assertIn("advice", result)
        self.assertIn("final_summary", result)
        self.assertEqual(result["final_summary"]["amount"], 50.0)
        self.assertEqual(result["final_summary"]["category"], "food")
        self.assertFalse(result["final_summary"]["over_budget"])
    
    def test_agent_run_over_budget(self):
        """Test advice when over budget."""
        state = {
            "amount": 100.0,
            "final_category": "entertainment",
            "validation": {
                "remaining": -25.0,
                "warning": True
            },
            "budget_status": {},
            "date": "2026-04-19"
        }
        
        result = self.agent.run(state)
        
        self.assertTrue(result["final_summary"]["over_budget"])
        self.assertEqual(result["final_summary"]["budget_remaining"], -25.0)
    
    def test_agent_preserves_state(self):
        """Test that agent preserves other state keys."""
        state = {
            "amount": 30.0,
            "final_category": "transport",
            "validation": {"remaining": 70.0, "warning": False},
            "budget_status": {},
            "date": "2026-04-19",
            "custom_data": "should_be_preserved",
            "errors": []
        }
        
        result = self.agent.run(state)
        
        self.assertEqual(result["custom_data"], "should_be_preserved")
        self.assertIn("errors", result)
    
    def test_agent_zero_amount(self):
        """Test agent with zero/invalid amount."""
        state = {
            "amount": 0,
            "final_category": "invalid",
            "validation": {},
            "budget_status": {},
            "date": None
        }
        
        result = self.agent.run(state)
        
        self.assertIn("advice", result)
        self.assertEqual(result["final_summary"]["amount"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)