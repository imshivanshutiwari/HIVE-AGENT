"""PAGE 3 — AGENT FLOW MONITOR: VIZ14-17."""
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto

from dashboard.theme import (
    BG_CARD, BG_PRIMARY, ACCENT_BLUE, SUCCESS, WARNING, CRITICAL, INFO,
    TEXT, BORDER, FONT, PLOTLY_THEME, CARD_STYLE,
)

AGENT_NODES = [
    "fetcher", "parser", "analyzer", "similarity",
    "doc_agent", "review", "test_agent", "evaluator",
]

AGENT_LABELS = {
    "fetcher": "Fetcher",
    "parser": "Parser",
    "analyzer": "Analyzer",
    "similarity": "Similarity",
    "doc_agent": "DocAgent",
    "review": "Review",
    "test_agent": "TestAgent",
    "evaluator": "Evaluator",
}


def _node_color(node: str, trace: List[str]) -> str:
    if any(f"{node}:complete" in t for t in trace):
        return SUCCESS
    elif any(f"{node}:start" in t for t in trace):
        return WARNING
    elif any(f"{node}:error" in t for t in trace):
        return CRITICAL
    return ACCENT_BLUE


def render_viz14_langgraph_flow(pipeline_trace: Optional[List] = None) -> html.Div:
    """VIZ14: LangGraph 8-node flow diagram."""
    trace = pipeline_trace or []

    positions = {
        "fetcher": (0, 4),
        "parser": (1, 6),
        "analyzer": (2, 4),
        "similarity": (2, 2),
        "doc_agent": (3, 4),
        "review": (3, 6),
        "test_agent": (4, 4),
        "evaluator": (5, 4),
    }

    edges = [
        ("fetcher", "parser"),
        ("parser", "analyzer"),
        ("parser", "similarity"),
        ("analyzer", "doc_agent"),
        ("analyzer", "review"),
        ("similarity", "doc_agent"),
        ("review", "test_agent"),
        ("doc_agent", "test_agent"),
        ("doc_agent", "evaluator"),
        ("test_agent", "evaluator"),
    ]

    elements = []
    for node in AGENT_NODES:
        color = _node_color(node, trace)
        elements.append({
            "data": {"id": node, "label": AGENT_LABELS[node]},
            "position": {"x": positions[node][0] * 120, "y": (8 - positions[node][1]) * 60},
            "style": {"background-color": color},
        })
    for src, tgt in edges:
        elements.append({"data": {"source": src, "target": tgt}})

    stylesheet = [
        {
            "selector": "node",
            "style": {
                "label": "data(label)",
                "color": TEXT,
                "font-family": FONT,
                "font-size": "10px",
                "width": "60px",
                "height": "30px",
                "shape": "round-rectangle",
                "text-valign": "center",
            },
        },
        {
            "selector": "edge",
            "style": {
                "curve-style": "bezier",
                "target-arrow-shape": "triangle",
                "line-color": BORDER,
                "target-arrow-color": ACCENT_BLUE,
                "width": 1.5,
            },
        },
    ]

    return html.Div([
        html.H4(
            "◈ VIZ14 — LANGGRAPH 8-NODE FLOW",
            style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"},
        ),
        cyto.Cytoscape(
            id="viz14-langgraph",
            layout={"name": "preset"},
            style={"width": "100%", "height": "350px", "backgroundColor": BG_PRIMARY},
            elements=elements,
            stylesheet=stylesheet,
        ),
    ], style=CARD_STYLE)


def render_viz15_agent_timeline(pipeline_trace: Optional[List] = None) -> html.Div:
    """VIZ15: Agent decision timeline (Gantt chart)."""
    trace = pipeline_trace or []

    gantt_data = []
    for i, node in enumerate(AGENT_NODES):
        started = any(f"{node}:start" in t for t in trace)
        completed = any(f"{node}:complete" in t for t in trace)
        gantt_data.append({
            "agent": AGENT_LABELS[node],
            "start": i * 2,
            "end": i * 2 + (2 if completed else 1 if started else 0),
            "status": "complete" if completed else "running" if started else "pending",
        })

    fig = go.Figure()
    colors_map = {"complete": SUCCESS, "running": WARNING, "pending": ACCENT_BLUE}
    for d in gantt_data:
        fig.add_trace(go.Bar(
            name=d["agent"],
            x=[d["end"] - d["start"]],
            y=[d["agent"]],
            orientation="h",
            base=[d["start"]],
            marker_color=colors_map[d["status"]],
            showlegend=False,
            hovertemplate=f"{d['agent']}: {d['status']}<extra></extra>",
        ))
    fig.update_layout(
        title="Agent Execution Timeline",
        barmode="overlay",
        xaxis_title="Time (relative)",
        **PLOTLY_THEME,
    )

    return html.Div([
        html.H4(
            "◈ VIZ15 — AGENT DECISION TIMELINE",
            style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"},
        ),
        dcc.Graph(figure=fig, id="viz15-timeline"),
    ], style=CARD_STYLE)


def render_viz16_token_usage(
    tokens_used: int = 0, pipeline_trace: Optional[List] = None
) -> html.Div:
    """VIZ16: Claude API usage tracker."""
    cost = tokens_used * (3 + 15) / 2 / 1_000_000
    rate_limit = min(100, (tokens_used // 100))

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=tokens_used,
        title={"text": "Total Tokens Used", "font": {"color": TEXT, "family": FONT}},
        gauge={
            "axis": {"range": [0, 50000], "tickcolor": TEXT},
            "bar": {"color": ACCENT_BLUE},
            "steps": [
                {"range": [0, 10000], "color": SUCCESS},
                {"range": [10000, 30000], "color": WARNING},
                {"range": [30000, 50000], "color": CRITICAL},
            ],
        },
        number={"font": {"color": TEXT}},
    ))
    gauge.update_layout(**PLOTLY_THEME)

    return html.Div([
        html.H4(
            "◈ VIZ16 — CLAUDE API USAGE",
            style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"},
        ),
        dbc.Row([
            dbc.Col([dcc.Graph(figure=gauge, id="viz16-token-gauge")], width=6),
            dbc.Col([
                html.Div([
                    html.Div(
                        f"TOKENS USED: {tokens_used:,}",
                        style={"color": ACCENT_BLUE, "fontFamily": FONT},
                    ),
                    html.Div(
                        f"COST: ${cost:.4f} USD",
                        style={"color": WARNING, "fontFamily": FONT},
                    ),
                    html.Div(
                        "MODEL: claude-sonnet-4-6",
                        style={"color": TEXT, "fontFamily": FONT, "fontSize": "10px"},
                    ),
                    html.Div(
                        f"RATE LIMIT: {rate_limit}%",
                        style={
                            "color": SUCCESS if rate_limit < 70 else CRITICAL,
                            "fontFamily": FONT,
                            "fontSize": "10px",
                        },
                    ),
                ], style={"padding": "20px"}),
            ], width=6),
        ]),
    ], style=CARD_STYLE)


def render_viz17_tool_calls(pipeline_trace: Optional[List] = None) -> html.Div:
    """VIZ17: Tool call frequency heatmap."""
    from collections import Counter
    trace = pipeline_trace or []

    tool_agent_counts: dict = {}
    agents = AGENT_NODES
    tools = [
        "parse_python_ast", "build_dependency_graph", "compute_complexity",
        "embed_functions", "generate_function_doc", "review_function",
        "generate_unit_tests", "compute_bertscore",
    ]

    for agent in agents:
        tool_agent_counts[agent] = {}
        for tool in tools:
            count = sum(1 for t in trace if agent in t and tool in t)
            tool_agent_counts[agent][tool] = count

    z_values = [[tool_agent_counts[a].get(t, 0) for t in tools] for a in agents]

    fig = go.Figure(go.Heatmap(
        z=z_values,
        x=[t[:15] for t in tools],
        y=[AGENT_LABELS[a] for a in agents],
        colorscale=[[0, BG_PRIMARY], [1, ACCENT_BLUE]],
        showscale=True,
    ))
    fig.update_layout(title="Tool Call Frequency", **PLOTLY_THEME)

    return html.Div([
        html.H4(
            "◈ VIZ17 — TOOL CALL FREQUENCY",
            style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"},
        ),
        dcc.Graph(figure=fig, id="viz17-heatmap"),
    ], style=CARD_STYLE)


def render_page(state: Optional[Dict] = None) -> html.Div:
    if state is None:
        state = {}
    trace = state.get("pipeline_trace", [])
    tokens = state.get("claude_tokens_used", 0)
    return html.Div([
        render_viz14_langgraph_flow(trace),
        render_viz15_agent_timeline(trace),
        render_viz16_token_usage(tokens, trace),
        render_viz17_tool_calls(trace),
    ])
