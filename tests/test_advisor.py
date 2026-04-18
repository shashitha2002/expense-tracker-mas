import pytest
from agents.advisor import AdvisorAgent

def test_advisor_generates_text():
    agent = AdvisorAgent()
    state = {
        "amount": 50.0,
        "final_category": "food",
        "validation": {"remaining": 100.0, "warning": False},
        "date": "2024-01-15"
    }
    result = agent.run(state)
    assert "advice" in result
    assert isinstance(result["advice"], str)
    assert len(result["advice"]) > 10

def test_advisor_handles_over_budget():
    agent = AdvisorAgent()
    state = {
        "amount": 200.0,
        "final_category": "entertainment",
        "validation": {"remaining": -50.0, "warning": True},
        "date": "2024-01-15"
    }
    result = agent.run(state)
    assert "over" in result["advice"].lower() or "budget" in result["advice"].lower()