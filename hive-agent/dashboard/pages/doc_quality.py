"""PAGE 4 — DOC QUALITY EVALUATION: VIZ18-20."""
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc

from dashboard.theme import (
    BG_CARD, BG_PRIMARY, ACCENT_BLUE, SUCCESS, WARNING, CRITICAL, INFO, TEXT, BORDER, FONT, PLOTLY_THEME, CARD_STYLE,
)


def render_viz18_bertscore_rouge(doc_quality_scores: Optional[Dict] = None) -> html.Div:
    """VIZ18: BERTScore + ROUGE dashboard."""
    scores = doc_quality_scores or {}
    metrics = {
        "BERTScore F1": scores.get("bertscore_f1", 0.0),
        "ROUGE-1": scores.get("rouge1", 0.0),
        "ROUGE-2": scores.get("rouge2", 0.0),
        "ROUGE-L": scores.get("rougeL", 0.0),
    }
    fig = go.Figure(go.Bar(
        x=list(metrics.keys()),
        y=list(metrics.values()),
        marker_color=[ACCENT_BLUE, SUCCESS, WARNING, INFO],
        text=[f"{v:.3f}" for v in metrics.values()],
        textposition="auto",
    ))
    fig.update_layout(title="Documentation Quality Metrics", yaxis_range=[0, 1], **PLOTLY_THEME)
    return html.Div([
        html.H4("◈ VIZ18 — BERTSCORE + ROUGE METRICS", style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"}),
        dcc.Graph(figure=fig, id="viz18-metrics"),
    ], style=CARD_STYLE)


def render_viz19_rubric_breakdown(doc_quality_scores: Optional[Dict] = None) -> html.Div:
    """VIZ19: Quality rubric radar."""
    scores = doc_quality_scores or {}
    avg_rubric = scores.get("avg_rubric_score", 0.0)
    dimensions = ["Completeness", "Accuracy", "Clarity", "Examples", "Edge Cases", "Consistency"]
    values = [avg_rubric / 5] * 6
    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=dimensions,
        fill="toself",
        fillcolor="rgba(55,138,221,0.3)",
        line=dict(color=ACCENT_BLUE),
        name="Current Repo",
    ))
    fig.update_layout(
        title=f"Quality Rubric (avg: {avg_rubric:.1f}/30)",
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], color=TEXT),
            angularaxis=dict(color=TEXT),
            bgcolor=BG_PRIMARY,
        ),
        **PLOTLY_THEME,
    )
    return html.Div([
        html.H4("◈ VIZ19 — DOC QUALITY RUBRIC", style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"}),
        dcc.Graph(figure=fig, id="viz19-rubric"),
    ], style=CARD_STYLE)


def render_viz20_before_after(doc_quality_scores: Optional[Dict] = None) -> html.Div:
    """VIZ20: Before vs after doc coverage comparison."""
    scores = doc_quality_scores or {}
    before = 0.0
    after = scores.get("coverage_functions", 0.0)
    bertscore_after = scores.get("bertscore_f1", 0.0)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Before HIVE-AGENT", x=["Coverage", "BERTScore"], y=[before * 100, 0.0], marker_color=CRITICAL))
    fig.add_trace(go.Bar(name="After HIVE-AGENT", x=["Coverage", "BERTScore"], y=[after * 100, bertscore_after * 100], marker_color=SUCCESS))
    fig.update_layout(title="Before vs After HIVE-AGENT Documentation", barmode="group", yaxis_title="Score (%)", **PLOTLY_THEME)
    delta_cov = after - before
    return html.Div([
        html.H4("◈ VIZ20 — BEFORE VS AFTER", style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"}),
        html.Div(f"Coverage improvement: +{delta_cov*100:.1f}%", style={"color": SUCCESS, "fontFamily": FONT, "fontSize": "12px", "marginBottom": "8px"}),
        dcc.Graph(figure=fig, id="viz20-comparison"),
    ], style=CARD_STYLE)


def render_page(state: Optional[Dict] = None) -> html.Div:
    if state is None:
        state = {}
    scores = state.get("doc_quality_scores")
    return html.Div([
        render_viz18_bertscore_rouge(scores),
        render_viz19_rubric_breakdown(scores),
        render_viz20_before_after(scores),
    ])
