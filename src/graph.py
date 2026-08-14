from typing import Dict, Any
from src.graph_state import GraphState
from src.nodes.orchestrator import OrchestratorNode
from src.nodes.planner import PlannerNode
from src.nodes.workers import Workers
from src.nodes.synthesizer import SynthesizerNode

class CampaignDiagnosticGraph:
    """
    Explicit Graph Engine managing control flow between:
    - ORCHESTRATOR
    - DATA CLEANER WORKER
    - PLANNER
    - QUERY EXECUTOR WORKER (with retry loop & sandbox execution)
    - VISUALIZATION WORKER
    - AMBIGUITY CLARIFIER WORKER
    - SYNTHESIZER
    """

    def __init__(self, data_path: str = None):
        self.data_path = data_path

    def run(self, question: str) -> GraphState:
        # Step 1: Orchestrator initializes graph state
        state = OrchestratorNode.initialize_state(question)

        # Step 2: Data Cleaning Worker
        state = Workers.data_cleaner_worker(state)

        # Step 3: Planner Node
        state = PlannerNode.execute(state)

        # Step 4: Conditional Graph Routing based on Planner assessment
        q_type = state.get("question_type")

        if q_type == "ambiguous":
            state = Workers.ambiguity_clarifier_worker(state)
            state = SynthesizerNode.execute(state)
        elif q_type == "unanswerable":
            state = SynthesizerNode.execute(state)
        else:
            # Answerable flow: Query Execution -> Visualization -> Synthesizer
            state = Workers.query_executor_worker(state)

            # Retry loop if code failed
            while not state.get("execution_success") and state.get("code_execution_count", 0) < state.get("max_code_retries", 3):
                # Fallback simple summary code
                state["generated_code"] = """# Fallback Execution Query
res = df.groupby('channel')['spend_inr'].sum().reset_index()
print("Fallback Channel Spend Summary:")
print(res.to_string())
"""
                state = Workers.query_executor_worker(state)

            if state.get("requires_chart"):
                state = Workers.visualization_worker(state)

            state = SynthesizerNode.execute(state)

        return state

if __name__ == '__main__':
    graph = CampaignDiagnosticGraph()
    test_state = graph.run("Why did CPA go up in June?")
    print("Graph Execution Completed Successfully!")
    print("Final Answer Preview:")
    print(test_state["final_answer"])
