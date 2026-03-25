"""LangGraph 8-node StateGraph with conditional edges."""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from agents.state import HiveAgentState
from agents.fetcher_agent import fetcher_node
from agents.parser_agent import parser_node
from agents.analyzer_agent import analyzer_node
from agents.similarity_agent import similarity_node
from agents.doc_agent import doc_agent_node
from agents.review_agent import review_node
from agents.test_agent import test_agent_node
from agents.evaluator_agent import evaluator_node

logger = logging.getLogger(__name__)


def should_continue_after_fetch(state: HiveAgentState) -> Literal["parser", "end"]:
    """Route after fetch: continue if successful, end on error."""
    if state.get("error") or not state.get("repo_path"):
        return "end"
    return "parser"


def should_run_review(state: HiveAgentState) -> Literal["review", "doc_agent"]:
    """Route after similarity: run review if high-complexity functions found."""
    complexity_scores = state.get("complexity_scores", {})
    high_complexity = [v for v in complexity_scores.values() if v >= 10]
    if high_complexity:
        return "review"
    return "doc_agent"


class HiveAgentGraph:
    """LangGraph 8-node StateGraph for HIVE-AGENT pipeline."""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(HiveAgentState)

        # Add all 8 nodes
        workflow.add_node("fetcher", fetcher_node)
        workflow.add_node("parser", parser_node)
        workflow.add_node("analyzer", analyzer_node)
        workflow.add_node("similarity", similarity_node)
        workflow.add_node("doc_agent", doc_agent_node)
        workflow.add_node("review", review_node)
        workflow.add_node("test_agent", test_agent_node)
        workflow.add_node("evaluator", evaluator_node)

        # Entry point
        workflow.set_entry_point("fetcher")

        # Conditional edge after fetcher
        workflow.add_conditional_edges(
            "fetcher",
            should_continue_after_fetch,
            {"parser": "parser", "end": END},
        )

        # Parser → analyzer (always)
        workflow.add_edge("parser", "analyzer")

        # Analyzer → similarity (always)
        workflow.add_edge("analyzer", "similarity")

        # Similarity → conditional: review (if high complexity) or doc_agent directly
        workflow.add_conditional_edges(
            "similarity",
            should_run_review,
            {"review": "review", "doc_agent": "doc_agent"},
        )

        # Review → doc_agent
        workflow.add_edge("review", "doc_agent")

        # doc_agent → test_agent
        workflow.add_edge("doc_agent", "test_agent")

        # test_agent → evaluator
        workflow.add_edge("test_agent", "evaluator")

        # evaluator → END
        workflow.add_edge("evaluator", END)

        return workflow

    def run(self, repo_url: str) -> HiveAgentState:
        """Run the full 8-node pipeline on a repository URL."""
        initial_state: HiveAgentState = {
            "repo_url": repo_url,
            "pipeline_trace": [],
            "claude_tokens_used": 0,
            "generated_docs": {},
            "generated_tests": {},
            "code_smells": [],
            "review_comments": [],
            "similar_clusters": [],
            "security_issues": [],
            "complexity_scores": {},
            "pagerank_scores": {},
            "doc_quality_scores": {},
        }
        app = self.graph.compile()
        result = app.invoke(initial_state)
        return result
