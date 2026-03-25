"""HiveAgentState TypedDict for LangGraph StateGraph."""

from typing import TypedDict, List, Dict, Optional, Any


class HiveAgentState(TypedDict, total=False):
    repo_url: str
    repo_path: str
    repo_metadata: Dict[str, Any]
    all_files: List[Dict[str, Any]]
    ast_results: Dict[str, Any]
    dependency_graph: Optional[Any]  # nx.DiGraph (not serializable, kept as Any)
    complexity_scores: Dict[str, float]
    code_smells: List[Dict[str, Any]]
    similar_clusters: List[Dict[str, Any]]
    generated_docs: Dict[str, str]
    generated_tests: Dict[str, str]
    changelog: str
    doc_quality_scores: Dict[str, float]
    review_comments: List[Dict[str, Any]]
    pipeline_trace: List[str]
    claude_tokens_used: int
    error: Optional[str]
    security_issues: List[Dict[str, Any]]
    pagerank_scores: Dict[str, float]
