"""PAGE 2 — CODE INTELLIGENCE LAB: VIZ08-13."""

from typing import Dict, List, Optional

import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto

from dashboard.theme import (
    BG_PRIMARY,
    ACCENT_BLUE,
    INFO,
    SUCCESS,
    WARNING,
    CRITICAL,
    TEXT,
    BORDER,
    FONT,
    PLOTLY_THEME,
    CARD_STYLE,
)


def make_empty_fig(title: str = "") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        annotations=[
            {"text": title or "Awaiting data...", "showarrow": False, "font": {"color": TEXT}}
        ],
        **PLOTLY_THEME,
    )
    return fig


def render_viz08_dependency_graph(dep_elements: Optional[List] = None) -> html.Div:
    """VIZ08: Dependency graph in dash-cytoscape."""
    elements = dep_elements or []
    default_stylesheet = [
        {
            "selector": "node",
            "style": {
                "background-color": ACCENT_BLUE,
                "label": "data(label)",
                "color": TEXT,
                "font-size": "9px",
                "width": "mapData(pagerank, 0, 0.1, 10, 40)",
                "height": "mapData(pagerank, 0, 0.1, 10, 40)",
            },
        },
        {
            "selector": "edge",
            "style": {
                "curve-style": "bezier",
                "target-arrow-shape": "triangle",
                "arrow-scale": 1,
                "line-color": BORDER,
                "target-arrow-color": ACCENT_BLUE,
                "width": 1,
            },
        },
    ]
    return html.Div(
        [
            html.H4(
                "◈ VIZ08 — DEPENDENCY GRAPH",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            cyto.Cytoscape(
                id="viz08-cytoscape-dep",
                layout={"name": "cose"},
                style={"width": "100%", "height": "350px", "backgroundColor": BG_PRIMARY},
                elements=elements,
                stylesheet=default_stylesheet,
            ),
            html.Div(
                id="viz08-node-info",
                style={"color": TEXT, "fontFamily": FONT, "fontSize": "10px", "marginTop": "4px"},
            ),
        ],
        style=CARD_STYLE,
    )


def render_viz09_complexity_histogram(ast_results: Optional[Dict] = None) -> html.Div:
    """VIZ09: Complexity distribution histogram."""
    complexities = []
    high_funcs = []
    if ast_results:
        for filepath, result in ast_results.items():
            for func in result.get("functions", []):
                cc = func.get("cyclomatic_complexity", 0)
                complexities.append(cc)
                if cc >= 10:
                    high_funcs.append(
                        f"{filepath.split('/')[-1]}::{func.get('name', '?')} (CC={cc})"
                    )

    fig = make_empty_fig("VIZ09: Complexity Distribution")
    if complexities:
        fig = go.Figure(
            go.Histogram(
                x=complexities,
                nbinsx=20,
                marker_color=ACCENT_BLUE,
                opacity=0.8,
            )
        )
        fig.add_vline(x=10, line_color=CRITICAL, line_dash="dash", annotation_text="Threshold=10")
        fig.update_layout(
            title="Cyclomatic Complexity Distribution",
            xaxis_title="Cyclomatic Complexity",
            yaxis_title="Function Count",
            **PLOTLY_THEME,
        )

    high_list = (
        html.Ul(
            [
                html.Li(f, style={"color": CRITICAL, "fontSize": "10px", "fontFamily": FONT})
                for f in high_funcs[:10]
            ]
        )
        if high_funcs
        else html.Div("No high-complexity functions found.", style={"color": TEXT})
    )

    return html.Div(
        [
            html.H4(
                "◈ VIZ09 — COMPLEXITY DISTRIBUTION",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            dcc.Graph(figure=fig, id="viz09-histogram"),
            html.Div(
                "High complexity functions (CC ≥ 10):",
                style={"color": WARNING, "fontFamily": FONT, "fontSize": "10px"},
            ),
            high_list,
        ],
        style=CARD_STYLE,
    )


def render_viz10_code_clones(similar_clusters: Optional[List] = None) -> html.Div:
    """VIZ10: Code clone detection map."""
    fig = make_empty_fig("VIZ10: Clone Detection")
    clone_count = 0
    if similar_clusters:
        x_labels, y_labels, scores = [], [], []
        for cluster in similar_clusters[:20]:
            funcs = cluster.get("functions", [])
            for i, fa in enumerate(funcs[:5]):
                for fb in funcs[i + 1 :]:
                    x_labels.append(fa.get("name", "?"))
                    y_labels.append(fb.get("name", "?"))
                    scores.append(0.9)
                    clone_count += 1
        if x_labels:
            fig = go.Figure(
                go.Scatter(
                    x=list(range(len(x_labels))),
                    y=scores,
                    mode="markers",
                    marker=dict(
                        color=scores,
                        colorscale=[[0, ACCENT_BLUE], [1, CRITICAL]],
                        size=8,
                        showscale=True,
                    ),
                    text=[f"{a} ↔ {b}" for a, b in zip(x_labels, y_labels)],
                    hovertemplate="%{text}<br>Similarity: %{y:.2f}<extra></extra>",
                )
            )
            fig.update_layout(
                title="Code Clone Similarity Scores",
                xaxis_title="Function Pair",
                yaxis_title="Similarity",
                **PLOTLY_THEME,
            )

    return html.Div(
        [
            html.H4(
                "◈ VIZ10 — CODE CLONE DETECTION",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            html.Div(
                f"Detected {clone_count} potential clone pairs",
                style={
                    "color": WARNING,
                    "fontFamily": FONT,
                    "fontSize": "10px",
                    "marginBottom": "4px",
                },
            ),
            dcc.Graph(figure=fig, id="viz10-clones"),
        ],
        style=CARD_STYLE,
    )


def render_viz11_call_graph(ast_results: Optional[Dict] = None) -> html.Div:
    """VIZ11: Call graph visualization."""
    elements = []
    if ast_results:
        added_nodes = set()
        for filepath, result in list(ast_results.items())[:5]:
            for func in result.get("functions", []):
                fname = func.get("name", "")
                if fname and fname not in added_nodes:
                    elements.append({"data": {"id": fname, "label": fname}, "group": "nodes"})
                    added_nodes.add(fname)
                for called in func.get("calls_made", []):
                    if called and called not in added_nodes:
                        elements.append({"data": {"id": called, "label": called}, "group": "nodes"})
                        added_nodes.add(called)
                    if called:
                        elements.append(
                            {"data": {"source": fname, "target": called}, "group": "edges"}
                        )

    stylesheet = [
        {
            "selector": "node",
            "style": {
                "background-color": SUCCESS,
                "label": "data(label)",
                "color": TEXT,
                "font-size": "9px",
                "width": "20px",
                "height": "20px",
            },
        },
        {
            "selector": "edge",
            "style": {
                "curve-style": "bezier",
                "target-arrow-shape": "triangle",
                "line-color": ACCENT_BLUE,
                "target-arrow-color": ACCENT_BLUE,
                "width": 1,
            },
        },
    ]

    return html.Div(
        [
            html.H4(
                "◈ VIZ11 — CALL GRAPH",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            cyto.Cytoscape(
                id="viz11-call-graph",
                layout={"name": "breadthfirst", "directed": True},
                style={"width": "100%", "height": "300px", "backgroundColor": BG_PRIMARY},
                elements=elements,
                stylesheet=stylesheet,
            ),
        ],
        style=CARD_STYLE,
    )


def render_viz12_security(security_issues: Optional[List] = None) -> html.Div:
    """VIZ12: Security scan results."""
    from collections import Counter

    issues = security_issues or []
    severity_counts = Counter(i.get("severity", "LOW") for i in issues)

    fig = go.Figure(
        go.Bar(
            x=["HIGH", "MEDIUM", "LOW"],
            y=[
                severity_counts.get("HIGH", 0),
                severity_counts.get("MEDIUM", 0),
                severity_counts.get("LOW", 0),
            ],
            marker_color=[CRITICAL, WARNING, INFO],
            text=[str(severity_counts.get(s, 0)) for s in ["HIGH", "MEDIUM", "LOW"]],
            textposition="auto",
        )
    )
    fig.update_layout(title="Security Issues by Severity", **PLOTLY_THEME)

    cwe_counts = Counter(i.get("cwe", "Unknown") for i in issues if i.get("cwe"))
    cwe_fig = go.Figure(
        go.Pie(
            labels=list(cwe_counts.keys())[:10],
            values=list(cwe_counts.values())[:10],
            marker_colors=[CRITICAL, WARNING, ACCENT_BLUE, INFO, SUCCESS],
        )
    )
    cwe_fig.update_layout(title="CWE Category Breakdown", **PLOTLY_THEME)

    return html.Div(
        [
            html.H4(
                "◈ VIZ12 — SECURITY SCAN RESULTS",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            html.Div(
                f"Total issues: {len(issues)}",
                style={
                    "color": CRITICAL if len(issues) > 0 else SUCCESS,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                },
            ),
            dbc.Row(
                [
                    dbc.Col([dcc.Graph(figure=fig, id="viz12-severity")], width=6),
                    dbc.Col([dcc.Graph(figure=cwe_fig, id="viz12-cwe")], width=6),
                ]
            ),
        ],
        style=CARD_STYLE,
    )


def render_viz13_smell_radar(code_smells: Optional[List] = None) -> html.Div:
    """VIZ13: Code smell radar chart."""
    from collections import Counter

    smells = code_smells or []
    category_counts = Counter(s.get("category", "other") for s in smells)

    categories = ["god_class", "long_method", "dead_code", "clone_code", "deep_nesting"]
    values = [category_counts.get(c, 0) for c in categories]

    fig = go.Figure(
        go.Scatterpolar(
            r=values,
            theta=["God Classes", "Long Methods", "Dead Code", "Clone Code", "Deep Nesting"],
            fill="toself",
            fillcolor="rgba(55, 138, 221, 0.3)",
            line=dict(color=ACCENT_BLUE),
            name="Current Repo",
        )
    )
    fig.update_layout(
        title="Code Smell Radar",
        polar=dict(
            radialaxis=dict(visible=True, color=TEXT),
            angularaxis=dict(color=TEXT),
            bgcolor=BG_PRIMARY,
        ),
        **PLOTLY_THEME,
    )

    return html.Div(
        [
            html.H4(
                "◈ VIZ13 — CODE SMELL RADAR",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            html.Div(
                f"Total smells detected: {len(smells)}",
                style={"color": WARNING, "fontFamily": FONT, "fontSize": "10px"},
            ),
            dcc.Graph(figure=fig, id="viz13-smell-radar"),
        ],
        style=CARD_STYLE,
    )


def render_page(state: Optional[Dict] = None) -> html.Div:
    if state is None:
        state = {}
    from analysis.dependency_graph import DependencyGraphBuilder

    dep_elements = []
    dep_graph = state.get("dependency_graph")
    if dep_graph:
        try:
            builder = DependencyGraphBuilder()
            dep_elements = builder.export_to_cytoscape(dep_graph)
        except Exception:
            pass

    return html.Div(
        [
            render_viz08_dependency_graph(dep_elements),
            render_viz09_complexity_histogram(state.get("ast_results")),
            render_viz10_code_clones(state.get("similar_clusters")),
            render_viz11_call_graph(state.get("ast_results")),
            render_viz12_security(state.get("security_issues")),
            render_viz13_smell_radar(state.get("code_smells")),
        ]
    )
