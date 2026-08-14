import datetime
from typing import Dict, Any
from src.graph_state import GraphState

class OrchestratorNode:
    """
    ORCHESTRATOR NODE:
    Controls execution flow, initializes and owns GraphState, manages step transitions,
    and logs step execution traces for auditability.
    """

    @staticmethod
    def initialize_state(question: str) -> GraphState:
        return GraphState(
            question=question,
            cleaned_df=None,
            data_audit_report=None,
            question_type="answerable",
            intent_category=None,
            plan=None,
            generated_code=None,
            code_execution_count=0,
            max_code_retries=3,
            execution_success=False,
            execution_result_data=None,
            execution_output_str=None,
            execution_error=None,
            clarification_needed=False,
            clarification_prompt=None,
            clarification_options=None,
            unanswerable_reason=None,
            requires_chart=False,
            chart_path=None,
            chart_title=None,
            final_answer=None,
            audit_trail=[],
            execution_trace=[{
                "timestamp": datetime.datetime.now().isoformat(),
                "node": "ORCHESTRATOR",
                "action": "Initialize Graph State",
                "question": question
            }]
        )

    @staticmethod
    def log_step(state: GraphState, node_name: str, action: str, details: Dict[str, Any] = None) -> GraphState:
        trace_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "node": node_name,
            "action": action,
            "details": details or {}
        }
        state["execution_trace"].append(trace_entry)
        return state
