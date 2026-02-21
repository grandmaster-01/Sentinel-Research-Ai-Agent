from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    """
    The state of the agentic workflow.
    """
    question: str
    context: List[str]
    web_results: List[str]
    report: Optional[str]
    critique: Optional[str]
    score: Optional[float]
    revision_count: int
    chat_history: Optional[List[str]]
    file_content: Optional[str]
    mode: Optional[str]          # "fast" | "deep" | "rag" | "coding"
    model_used: Optional[str]    # display name of the LLM that generated the answer
