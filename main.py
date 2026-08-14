import sys
import os
import json
import argparse

# Add code root directory to python path
sys.path.insert(0, os.path.dirname(__file__))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.graph import CampaignDiagnosticGraph

def run_single_question(question: str, save_trace_path: str = None):
    print("=" * 80)
    print(f"Running Campaign Diagnostic Engine for Question:")
    print(f"  '{question}'")
    print("=" * 80)

    graph = CampaignDiagnosticGraph()
    state = graph.run(question)

    print("\n--- DIAGNOSTIC RESULT ---")
    print(f"Status / Type: [{state['question_type'].upper()}]")
    if state.get("intent_category"):
        print(f"Intent Category: {state['intent_category']}")
    
    print("\nAnswer Output:")
    # Print without emoji encoding errors on Windows terminal
    print(state["final_answer"].encode('utf-8', errors='replace').decode('utf-8'))

    if state.get("chart_path"):
        print(f"\nGenerated Visual Chart: {state['chart_path']}")

    if save_trace_path:
        trace_data = {
            "question": state["question"],
            "question_type": state["question_type"],
            "intent_category": state.get("intent_category"),
            "execution_success": state.get("execution_success"),
            "audit_trail": state.get("audit_trail", []),
            "execution_trace": state.get("execution_trace", []),
            "data_audit_report": state.get("data_audit_report")
        }
        with open(save_trace_path, 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, indent=2)
        print(f"\nSaved Execution Trace to: {save_trace_path}")

    return state

def run_all_sample_questions():
    questions = [
        "1. What was total spend and total conversions last month?",
        "2. Why did CPA go up in June?",
        "3. Which creative has the best ROAS on mobile in Tier 1 cities?",
        "4. Is CMP-1006 pacing correctly against its daily budget?",
        "5. Which city has the worst cost per conversion, and by how much?",
        "6. Compare Meta and Google Search on CPA over the full period.",
        "7. What happened to CMP-1006 in the middle of June?",
        "8. Show me the CTR trend for CRE-2002 week by week.",
        "9. Which age group converts best on Connected TV?",
        "10. What is our average order value by channel?",
        "11. How did last week compare to the week before?",
        "12. Why is Tier 3 mobile traffic on CMP-1004 performing so badly?",
        "13. What is the customer lifetime value of people acquired through YouTube?",
        "14. Should we increase budget on CMP-1003?",
        "15. Which campaign is closest to hitting a 4x ROAS target?"
    ]

    print(f"Running All {len(questions)} Sample Diagnostic Questions...\n")
    for q in questions:
        run_single_question(q)
        print("\n" + "-" * 80 + "\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Campaign Performance Diagnostic Engine CLI")
    parser.add_argument("--question", type=str, help="Single question to diagnose")
    parser.add_argument("--all", action="store_true", help="Run all 15 sample questions")
    parser.add_argument("--save-trace", type=str, default="saved_trace_sample.json", help="Path to save trace file")

    args = parser.parse_args()

    if args.question:
        run_single_question(args.question, save_trace_path=args.save_trace)
    elif args.all:
        run_all_sample_questions()
    else:
        # Default test run with sample trace save
        default_q = "Why did CPA go up in June?"
        run_single_question(default_q, save_trace_path="saved_trace_sample.json")
