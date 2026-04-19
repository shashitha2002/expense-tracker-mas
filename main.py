# main.py
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator

# Import agents
from agents.parser import ParserAgent
from agents.validator import ValidatorAgent
from agents.categorizer import CategorizerAgent
from agents.advisor import AdvisorAgent

from tools.database import ExpenseDatabase

# Define state schema
class ExpenseState(TypedDict):
    # Input
    user_input: str
    
    # Parser outputs
    amount: float
    description: str
    suggested_category: str
    date: str
    parser_output: dict
    
    # Validator outputs
    validation: dict
    budget_status: dict
    
    # Categorizer outputs
    final_category: str
    db_record: dict
    ready_to_store: bool
    
    # Advisor outputs
    advice: str
    final_summary: dict
    
    # Report outputs (NEW)
    monthly_report: dict
    report_path: str
    
    # Tracking
    errors: Annotated[list, operator.add]

# Initialize agents
parser = ParserAgent()
validator = ValidatorAgent()
categorizer = CategorizerAgent()
advisor = AdvisorAgent()
db = ExpenseDatabase()

def parser_node(state: ExpenseState):
    """Node 1: Parse input."""
    print(f"\n🔍 Parser: Processing '{state['user_input']}'")
    new_state = parser.run(state)
    if new_state.get("amount"):
        print(f"   ✓ Found: ${new_state['amount']} for {new_state['description']}")
    return new_state

def validator_node(state: ExpenseState):
    """Node 2: Check budget."""
    print(f"\n💰 Validator: Checking budget...")
    new_state = validator.run(state)
    val = new_state.get("validation", {})
    print(f"   {'⚠️' if val.get('warning') else '✓'} {val.get('message', '')}")
    return new_state

def categorizer_node(state: ExpenseState):
    """Node 3: Confirm category."""
    print(f"\n📂 Categorizer: Confirming category...")
    new_state = categorizer.run(state)
    print(f"   ✓ Category: {new_state['final_category']}")
    return new_state

def store_node(state: ExpenseState):
    """Store in database."""
    print(f"\n💾 Storing to database...")
    record = state.get("db_record", {})
    
    # Validate record exists
    if not record or not record.get("amount"):
        print("   ⚠️ No valid record to store")
        # MUST return valid state keys
        return {
            "db_record": {},  # Return empty to clear it
            "errors": state.get("errors", []) + ["Store: No valid record"]
        }
    
    try:
        db.add_expense(
            amount=record["amount"],
            category=record["category"],
            description=record["description"],
            date=record["date"],
            raw_input=record["raw_input"]
        )
        print("   ✓ Saved successfully")
        # Return valid state update
        return {
            "db_record": record,  # Pass through
            "errors": state.get("errors", [])
        }
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "db_record": record,
            "errors": state.get("errors", []) + [f"Database: {str(e)}"]
        }

def advisor_node(state: ExpenseState):
    """Node 4: Generate advice."""
    print(f"\n🤖 Advisor: Generating advice...")
    new_state = advisor.run(state)
    print(f"   💬 {new_state.get('advice', '')[:80]}...")
    
    # Ensure we return the full state update
    return {
        "advice": new_state.get("advice", ""),
        "final_summary": new_state.get("final_summary", {})
    }

def should_continue(state: ExpenseState) -> str:
    """Check if parsing succeeded."""
    amount = state.get("amount")
    if amount is None or amount <= 0:
        return "error"
    return "continue"

def error_node(state: ExpenseState):
    """Handle parser failures gracefully."""
    errors = state.get("errors", ["Unknown parsing error"])
    error_msg = errors[-1] if errors else "Could not understand input"
    
    print(f"\n❌ Error: {error_msg}")
    print(f"   Try: 'spent $50 on lunch' or '$20 groceries'")
    
    return {
        "advice": f"Sorry, I couldn't understand that. {error_msg}",
        "final_summary": {
            "error": True,
            "amount": 0,
            "category": "none",
            "message": "Parse failed"
        }
    }

def report_node(state: ExpenseState):
    """Generate monthly report after advice."""
    from tools.report_generator import ReportGenerator
    
    reporter = ReportGenerator()
    report = reporter.generate_report()
    
    # Save to file
    path = reporter.export_to_text(report)
    
    print(f"\n📊 Monthly report saved: {path}")
    
    return {
        "monthly_report": report,
        "report_path": path
    }

# Build graph
workflow = StateGraph(ExpenseState)

# Add nodes
workflow.add_node("parser", parser_node)
workflow.add_node("validator", validator_node)
workflow.add_node("categorizer", categorizer_node)
workflow.add_node("store", store_node)
workflow.add_node("advisor", advisor_node)
workflow.add_node("report", report_node)
workflow.add_node("error", error_node)

# Entry point
workflow.set_entry_point("parser")

# CONDITIONAL: parser routes to validator OR error based on success
workflow.add_conditional_edges(
    "parser",
    should_continue,
    {
        "continue": "validator",  # amount > 0
        "error": "error"            # amount <= 0 or None
    }
)

# Success path (validator → advisor)
workflow.add_edge("validator", "categorizer")
workflow.add_edge("categorizer", "store")
workflow.add_edge("store", "advisor")
workflow.add_edge("advisor", "report")
workflow.add_edge("report", END)

# Error path ends immediately
workflow.add_edge("error", END)

# Compile
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

def main():
    print("=" * 50)
    print("💵 PERSONAL EXPENSE TRACKER (Multi-Agent System)")
    print("=" * 50)
    print("Using: LangGraph + Llama 3.2 3B (local)")
    print("Agents: Parser → Validator → Categorizer → Advisor")
    print("-" * 50)
    
    while True:
        user_input = input("\nEnter expense (or 'quit'): ").strip()
        if user_input.lower() == 'quit':
            break
        
        # Run workflow
        result = app.invoke(
            {"user_input": user_input, "errors": []},
            config={"configurable": {"thread_id": "session_1"}}
        )
        
        print("\n" + "=" * 50)
        print("FINAL RESULT:")
        print(f"Advice: {result.get('advice', 'N/A')}")
        print(f"Summary: {result.get('final_summary', {})}")
        print("=" * 50)

if __name__ == "__main__":
    main()