from typing import TypedDict, Optional, List, Dict, Any

class GraphState(TypedDict):
    """
    Shared State object maintained across all Graph nodes.
    Tracks user input, dataset, classification flags, calculation code, audit logs,
    chart output, and execution history.
    """
    question: str
    cleaned_df: Optional[Any]  # pd.DataFrame
    data_audit_report: Optional[Dict[str, Any]]
    
    # Classification & Intent Flags
    question_type: str  # "answerable", "ambiguous", "unanswerable"
    intent_category: Optional[str]  # "totals", "driver_analysis", "ranking", "pacing", "comparison", "trend", "ltv", "aov"
    
    # Execution Planning
    plan: Optional[str]
    generated_code: Optional[str]
    code_execution_count: int
    max_code_retries: int
    
    # Execution Results
    execution_success: bool
    execution_result_data: Optional[Dict[str, Any]]  # Calculated key metrics/table
    execution_output_str: Optional[str]
    execution_error: Optional[str]
    
    # Ambiguity / Unanswerable context
    clarification_needed: bool
    clarification_prompt: Optional[str]
    clarification_options: Optional[List[str]]
    unanswerable_reason: Optional[str]
    
    # Visualization Output
    requires_chart: bool
    chart_path: Optional[str]
    chart_title: Optional[str]
    
    # Final Output
    final_answer: Optional[str]
    audit_trail: List[Dict[str, Any]]
    execution_trace: List[Dict[str, Any]]
