import pytest
from agents.parser import extract_expense_tool, ParserAgent

def test_extract_amount_dollar_sign():
    result = extract_expense_tool("spent $50 on lunch")
    assert result["parsed"] is True
    assert result["amount"] == 50.0

def test_extract_amount_number_only():
    result = extract_expense_tool("spent 25 dollars on gas")
    assert result["amount"] == 25.0

def test_category_detection():
    result = extract_expense_tool("paid $30 for movie tickets")
    assert result["suggested_category"] == "entertainment"

def test_invalid_input():
    result = extract_expense_tool("hello world")
    assert result["parsed"] is False

def test_agent_integration():
    agent = ParserAgent()
    state = {"user_input": "bought $20 coffee", "errors": []}
    result = agent.run(state)
    assert result["amount"] == 20.0