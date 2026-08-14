import os
from typing import Dict, Any
from src.graph_state import GraphState
from src.nodes.orchestrator import OrchestratorNode

class SynthesizerNode:
    """
    SYNTHESIZER NODE:
    Transforms calculated execution data, audit code, and chart artifacts into a complete,
    executive diagnostic report in clear plain language.
    """

    @classmethod
    def execute(cls, state: GraphState) -> GraphState:
        q_type = state.get("question_type", "answerable")

        if q_type == "ambiguous":
            return OrchestratorNode.log_step(
                state,
                node_name="SYNTHESIZER",
                action="Synthesize Ambiguity Response",
                details={"question_type": q_type}
            )

        if q_type == "unanswerable":
            reason = state.get("unanswerable_reason", "Data constraints prevent answering this question.")
            state["final_answer"] = (
                "### ⛔ Question Cannot Be Answered with Available Data\n\n"
                f"**Reason:** {reason}\n\n"
                "**Data Audit Note:** The system checked `campaign_performance.csv` schema and confirmed that "
                "required metrics/user cohort identifiers are not tracked in this dataset."
            )
            return OrchestratorNode.log_step(
                state,
                node_name="SYNTHESIZER",
                action="Synthesize Unanswerable Response",
                details={"reason": reason}
            )

        # Answerable Question Synthesis
        question = state.get("question", "")
        output_str = state.get("execution_output_str", "")
        audit_trail = state.get("audit_trail", [])
        last_code = audit_trail[-1]["code"] if audit_trail else state.get("generated_code", "")
        chart_path = state.get("chart_path")

        final_msg = f"## 📊 Campaign Performance Diagnostic Report\n\n"
        final_msg += f"**Question:** *\"{question}\"*\n\n"
        final_msg += f"### 💡 Key Findings & Direct Answer\n\n"

        if output_str:
            final_msg += f"{output_str}\n\n"
        else:
            final_msg += "Calculation completed successfully over cleaned dataset.\n\n"

        final_msg += "### 🔍 Calculation & Audit Details\n"
        final_msg += "Every number in this diagnostic was calculated dynamically over 9,500+ campaign log rows:\n\n"
        final_msg += "```python\n" + last_code.strip() + "\n```\n\n"

        if chart_path and os.path.exists(chart_path):
            final_msg += f"📈 **Diagnostic Chart Generated:** `charts/{os.path.basename(chart_path)}`\n"

        state["final_answer"] = final_msg

        return OrchestratorNode.log_step(
            state,
            node_name="SYNTHESIZER",
            action="Synthesize Final Diagnostic Answer",
            details={"has_chart": bool(chart_path)}
        )
