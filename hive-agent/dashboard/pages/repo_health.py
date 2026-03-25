"""PAGE 5 — REPO HEALTH DASHBOARD: VIZ21-22."""
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc

from dashboard.theme import (
    BG_CARD, BG_PRIMARY, ACCENT_BLUE, SUCCESS, WARNING, CRITICAL, INFO, TEXT, BORDER, FONT, PLOTLY_THEME, CARD_STYLE,
)


def render_viz21_commit_activity(repo_metadata: Optional[Dict] = None) -> html.Div:
    """VIZ21: Commit activity analysis."""
    fig_heatmap = go.Figure()
    fig_top = go.Figure()
    if repo_metadata:
        commit_history = repo_metadata.get("commit_history", [])
        if commit_history:
            from collections import Counter
            from datetime import datetime
            by_day: dict = Counter()
            by_hour: dict = Counter()
            authors: dict = Counter()
            for c in commit_history:
                date_str = c.get("date", "")
                author = c.get("author", "unknown")
                authors[author] += 1
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    by_day[dt.weekday()] += 1
                    by_hour[dt.hour] += 1
                except Exception:
                    pass
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            hours = list(range(24))
            heatmap_z = [[by_day.get(d, 0) + by_hour.get(h, 0) for h in hours] for d in range(7)]
            fig_heatmap = go.Figure(go.Heatmap(
                z=heatmap_z,
                x=[f"{h:02d}:00" for h in hours],
                y=days,
                colorscale=[[0, BG_PRIMARY], [1, ACCENT_BLUE]],
            ))
            fig_heatmap.update_layout(title="Commit Activity Heatmap (Day × Hour)", **PLOTLY_THEME)
            top_authors = authors.most_common(10)
            fig_top = go.Figure(go.Bar(
                y=[a[0] for a in top_authors],
                x=[a[1] for a in top_authors],
                orientation="h",
                marker_color=ACCENT_BLUE,
            ))
            fig_top.update_layout(title="Top Contributors", xaxis_title="Commits", **PLOTLY_THEME)
    return html.Div([
        html.H4("◈ VIZ21 — COMMIT ACTIVITY ANALYSIS", style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"}),
        dbc.Row([
            dbc.Col([dcc.Graph(figure=fig_heatmap, id="viz21-heatmap")], width=7),
            dbc.Col([dcc.Graph(figure=fig_top, id="viz21-top-contributors")], width=5),
        ]),
    ], style=CARD_STYLE)


def _traffic_light(value: float, warn: float, crit: float, higher_is_better: bool = True) -> str:
    if higher_is_better:
        return SUCCESS if value >= warn else WARNING if value >= crit else CRITICAL
    else:
        return SUCCESS if value <= warn else WARNING if value <= crit else CRITICAL


def render_viz22_health_scorecard(
    doc_quality_scores: Optional[Dict] = None,
    complexity_scores: Optional[Dict] = None,
    security_issues: Optional[List] = None,
    similar_clusters: Optional[List] = None,
    repo_metadata: Optional[Dict] = None,
    tokens_used: int = 0,
) -> html.Div:
    """VIZ22: Repo health scorecard."""
    scores = doc_quality_scores or {}
    complexities = list((complexity_scores or {}).values())
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0.0
    high_security = sum(1 for i in (security_issues or []) if i.get("severity") == "HIGH")
    clone_count = len(similar_clusters or [])
    open_issues = (repo_metadata or {}).get("open_issues", 0)
    total_commits = (repo_metadata or {}).get("total_commits", 0)
    coverage = scores.get("coverage_functions", 0.0)
    cost = tokens_used * (3 + 15) / 2 / 1_000_000
    metrics = [
        ("DOC COVERAGE", f"{coverage*100:.0f}%", _traffic_light(coverage, 0.8, 0.5)),
        ("AVG COMPLEXITY", f"{avg_complexity:.1f}", _traffic_light(avg_complexity, 5, 10, higher_is_better=False)),
        ("SECURITY ISSUES (HIGH)", str(high_security), _traffic_light(high_security, 0, 5, higher_is_better=False)),
        ("CLONE GROUPS", str(clone_count), _traffic_light(clone_count, 3, 10, higher_is_better=False)),
        ("OPEN ISSUES", str(open_issues), _traffic_light(open_issues, 10, 50, higher_is_better=False)),
        ("TOTAL COMMITS", str(total_commits), SUCCESS if total_commits > 100 else WARNING),
        ("TOKENS USED", f"{tokens_used:,}", SUCCESS),
        ("COST (USD)", f"${cost:.3f}", SUCCESS if cost < 0.5 else WARNING),
    ]
    score_points = sum(2 if c == SUCCESS else 1 if c == WARNING else 0 for _, _, c in metrics)
    max_points = len(metrics) * 2
    pct = score_points / max_points
    grade = "A" if pct >= 0.9 else "B" if pct >= 0.8 else "C" if pct >= 0.7 else "D" if pct >= 0.6 else "F"
    grade_color = SUCCESS if grade in ("A", "B") else WARNING if grade == "C" else CRITICAL
    metric_cards = [
        html.Div([
            html.Div(label, style={"color": TEXT, "fontFamily": FONT, "fontSize": "9px", "letterSpacing": "1px"}),
            html.Div(value, style={"color": color, "fontFamily": FONT, "fontSize": "16px", "fontWeight": "bold"}),
        ], style={"display": "inline-block", "padding": "8px 12px", "textAlign": "center", "border": f"1px solid {BORDER}", "margin": "4px", "minWidth": "100px"})
        for label, value, color in metrics
    ]
    indicator = go.Figure(go.Indicator(
        mode="number",
        value=score_points,
        title={"text": "Health Score", "font": {"color": TEXT, "family": FONT}},
        number={"font": {"color": grade_color, "size": 48}, "suffix": f"/{max_points}"},
    ))
    indicator.update_layout(**PLOTLY_THEME)
    return html.Div([
        html.H4("◈ VIZ22 — REPO HEALTH SCORECARD", style={"color": ACCENT_BLUE, "fontFamily": FONT, "fontSize": "11px", "letterSpacing": "2px"}),
        dbc.Row([
            dbc.Col([
                html.Div(grade, style={"color": grade_color, "fontFamily": FONT, "fontSize": "72px", "fontWeight": "bold", "textAlign": "center"}),
                html.Div("OVERALL GRADE", style={"color": TEXT, "fontFamily": FONT, "fontSize": "10px", "textAlign": "center", "letterSpacing": "2px"}),
            ], width=2),
            dbc.Col([html.Div(metric_cards, style={"display": "flex", "flexWrap": "wrap"})], width=10),
        ]),
        dcc.Graph(figure=indicator, id="viz22-health-score"),
    ], style=CARD_STYLE)


def render_page(state: Optional[Dict] = None) -> html.Div:
    if state is None:
        state = {}
    return html.Div([
        render_viz21_commit_activity(state.get("repo_metadata")),
        render_viz22_health_scorecard(
            doc_quality_scores=state.get("doc_quality_scores"),
            complexity_scores=state.get("complexity_scores"),
            security_issues=state.get("security_issues"),
            similar_clusters=state.get("similar_clusters"),
            repo_metadata=state.get("repo_metadata"),
            tokens_used=state.get("claude_tokens_used", 0),
        ),
    ])
