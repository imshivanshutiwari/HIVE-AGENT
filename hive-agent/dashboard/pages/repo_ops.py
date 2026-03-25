"""PAGE 1 — REPO OPS CENTER: VIZ01-07."""

from typing import Dict, List, Optional

import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc

from dashboard.theme import (
    BG_CARD,
    BG_PRIMARY,
    ACCENT_BLUE,
    SUCCESS,
    WARNING,
    CRITICAL,
    INFO,
    TEXT,
    BORDER,
    FONT,
    PLOTLY_THEME,
    CARD_STYLE,
)


def make_empty_fig(title: str = "Awaiting data...") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        annotations=[{"text": title, "showarrow": False, "font": {"color": TEXT}}],
        **PLOTLY_THEME,
    )
    return fig


def render_viz01_input() -> html.Div:
    """VIZ01: Repo URL input + live analysis feed."""
    return html.Div(
        [
            html.H4(
                "◈ VIZ01 — REPOSITORY ANALYSIS FEED",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id="repo-url-input",
                                        placeholder="owner/repo  e.g. psf/requests",
                                        type="text",
                                        style={
                                            "backgroundColor": BG_CARD,
                                            "color": TEXT,
                                            "border": f"1px solid {BORDER}",
                                            "fontFamily": FONT,
                                        },
                                    ),
                                    dbc.Button(
                                        "▶ ANALYZE",
                                        id="analyze-btn",
                                        color="primary",
                                        style={"fontFamily": FONT, "letterSpacing": "1px"},
                                    ),
                                ]
                            ),
                        ],
                        width=10,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Div(id="progress-fetch", className="mb-1"),
                                    html.Div(id="progress-parse", className="mb-1"),
                                    html.Div(id="progress-analyze", className="mb-1"),
                                    html.Div(id="progress-generate", className="mb-1"),
                                ],
                                id="progress-bars",
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                id="live-analysis-log",
                                style={
                                    "backgroundColor": BG_PRIMARY,
                                    "color": SUCCESS,
                                    "fontFamily": FONT,
                                    "fontSize": "11px",
                                    "padding": "8px",
                                    "height": "120px",
                                    "overflowY": "auto",
                                    "border": f"1px solid {BORDER}",
                                },
                                children=[
                                    "[HIVE-AGENT] Ready. Enter a GitHub repo URL to begin analysis."
                                ],
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
            dcc.Interval(id="analysis-poll-interval", interval=2000, disabled=True),
            dcc.Store(id="current-job-id", data=None),
            dcc.Store(id="analysis-state", data={}),
        ],
        style=CARD_STYLE,
    )


def render_viz02_repo_overview(metadata: Optional[Dict] = None) -> html.Div:
    """VIZ02: Repo overview card with language pie and commit heatmap."""
    if not metadata:
        return html.Div(
            [
                html.H4(
                    "◈ VIZ02 — REPO OVERVIEW",
                    style={
                        "color": ACCENT_BLUE,
                        "fontFamily": FONT,
                        "fontSize": "11px",
                        "letterSpacing": "2px",
                    },
                ),
                dcc.Graph(
                    figure=make_empty_fig("Awaiting repository data..."), id="viz02-lang-pie"
                ),
            ],
            style=CARD_STYLE,
        )

    stats = [
        ("⭐ STARS", f"{metadata.get('stars', 0):,}"),
        ("🍴 FORKS", f"{metadata.get('forks', 0):,}"),
        ("👥 CONTRIBUTORS", str(metadata.get("contributors", 0))),
        ("🔒 LICENSE", metadata.get("license", "N/A")),
        ("📦 LANGUAGE", metadata.get("primary_language", "N/A")),
        ("🐛 OPEN ISSUES", str(metadata.get("open_issues", 0))),
    ]

    stat_cards = [
        html.Div(
            [
                html.Div(label, style={"color": TEXT, "fontSize": "9px", "letterSpacing": "2px"}),
                html.Div(
                    value, style={"color": ACCENT_BLUE, "fontSize": "16px", "fontWeight": "bold"}
                ),
            ],
            style={"display": "inline-block", "padding": "8px 16px", "textAlign": "center"},
        )
        for label, value in stats
    ]

    languages = metadata.get("languages", {})
    lang_fig = go.Figure()
    if languages:
        lang_fig = go.Figure(
            go.Pie(
                labels=list(languages.keys()),
                values=list(languages.values()),
                hole=0.4,
                marker_colors=[ACCENT_BLUE, SUCCESS, WARNING, CRITICAL, INFO],
            )
        )
    lang_fig.update_layout(title="Language Breakdown", **PLOTLY_THEME)

    return html.Div(
        [
            html.H4(
                "◈ VIZ02 — REPO OVERVIEW",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            html.Div(stat_cards, style={"display": "flex", "flexWrap": "wrap"}),
            dcc.Graph(figure=lang_fig, id="viz02-lang-pie"),
        ],
        style=CARD_STYLE,
    )


def render_viz03_complexity_heatmap(complexity_scores: Optional[Dict] = None) -> html.Div:
    """VIZ03: Code complexity heatmap (treemap)."""
    fig = make_empty_fig("VIZ03: Code Complexity Heatmap")
    if complexity_scores:
        files = list(complexity_scores.keys())
        values = list(complexity_scores.values())
        if files:
            fig = go.Figure(
                go.Treemap(
                    labels=[f.split("/")[-1] for f in files],
                    parents=["" for _ in files],
                    values=[max(v, 0.1) for v in values],
                    marker=dict(
                        colors=values,
                        colorscale=[[0, SUCCESS], [0.5, WARNING], [1, CRITICAL]],
                        showscale=True,
                        cmin=0,
                        cmax=20,
                    ),
                    hovertemplate="<b>%{label}</b><br>Avg Complexity: %{color:.1f}<extra></extra>",
                )
            )
            fig.update_layout(
                title="Complexity Heatmap (color=cyclomatic, size=complexity)",
                **PLOTLY_THEME,
            )
    return html.Div(
        [
            html.H4(
                "◈ VIZ03 — CODE COMPLEXITY HEATMAP",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            dcc.Graph(figure=fig, id="viz03-complexity-treemap"),
        ],
        style=CARD_STYLE,
    )


def render_viz04_doc_coverage(doc_quality_scores: Optional[Dict] = None) -> html.Div:
    """VIZ04: Documentation coverage gauge."""
    overall = 0.0
    func_cov = 0.0
    class_cov = 0.0
    module_cov = 0.0
    if doc_quality_scores:
        func_cov = doc_quality_scores.get("coverage_functions", 0.0)
        class_cov = doc_quality_scores.get("coverage_classes", 0.0)
        module_cov = doc_quality_scores.get("coverage_modules", 0.0)
        overall = (func_cov + class_cov + module_cov) / 3

    gauge_fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=overall * 100,
            title={"text": "Overall Doc Coverage %", "font": {"color": TEXT, "family": FONT}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": TEXT},
                "bar": {"color": ACCENT_BLUE},
                "steps": [
                    {"range": [0, 50], "color": CRITICAL},
                    {"range": [50, 80], "color": WARNING},
                    {"range": [80, 100], "color": SUCCESS},
                ],
                "threshold": {"line": {"color": ACCENT_BLUE, "width": 2}, "value": 80},
            },
            number={"suffix": "%", "font": {"color": TEXT}},
        )
    )
    gauge_fig.update_layout(**PLOTLY_THEME)

    bar_fig = go.Figure(
        go.Bar(
            x=["Functions", "Classes", "Modules"],
            y=[func_cov * 100, class_cov * 100, module_cov * 100],
            marker_color=[ACCENT_BLUE, SUCCESS, WARNING],
            text=[f"{v*100:.0f}%" for v in [func_cov, class_cov, module_cov]],
            textposition="auto",
        )
    )
    bar_fig.update_layout(title="Coverage by Type", yaxis_range=[0, 100], **PLOTLY_THEME)

    return html.Div(
        [
            html.H4(
                "◈ VIZ04 — DOCUMENTATION COVERAGE",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            dbc.Row(
                [
                    dbc.Col([dcc.Graph(figure=gauge_fig, id="viz04-gauge")], width=6),
                    dbc.Col([dcc.Graph(figure=bar_fig, id="viz04-bars")], width=6),
                ]
            ),
        ],
        style=CARD_STYLE,
    )


def render_viz05_doc_preview(generated_docs: Optional[Dict] = None) -> html.Div:
    """VIZ05: Generated doc preview panel."""
    entries = []
    if generated_docs:
        for key, doc in list(generated_docs.items())[:5]:
            name = key.split("::")[-1]
            entries.append(
                html.Div(
                    [
                        html.Div(
                            name,
                            style={"color": ACCENT_BLUE, "fontSize": "11px", "marginBottom": "4px"},
                        ),
                        html.Pre(
                            doc[:400],
                            style={
                                "backgroundColor": BG_PRIMARY,
                                "color": SUCCESS,
                                "fontFamily": FONT,
                                "fontSize": "10px",
                                "padding": "8px",
                                "overflow": "auto",
                                "border": f"1px solid {BORDER}",
                                "maxHeight": "100px",
                            },
                        ),
                    ],
                    style={"marginBottom": "8px"},
                )
            )

    if not entries:
        entries = [
            html.Div(
                "Awaiting generated documentation...", style={"color": TEXT, "fontFamily": FONT}
            )
        ]

    return html.Div(
        [
            html.H4(
                "◈ VIZ05 — GENERATED DOCUMENTATION PREVIEW",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            html.Div(entries, style={"maxHeight": "300px", "overflowY": "auto"}),
        ],
        style=CARD_STYLE,
    )


def render_viz06_generated_tests(generated_tests: Optional[Dict] = None) -> html.Div:
    """VIZ06: Generated tests panel."""
    entries = []
    if generated_tests:
        for key, test in list(generated_tests.items())[:3]:
            name = key.split("/")[-1]
            entries.append(
                html.Div(
                    [
                        html.Div(
                            name,
                            style={"color": SUCCESS, "fontSize": "11px", "marginBottom": "4px"},
                        ),
                        html.Pre(
                            test[:500],
                            style={
                                "backgroundColor": BG_PRIMARY,
                                "color": TEXT,
                                "fontFamily": FONT,
                                "fontSize": "10px",
                                "padding": "8px",
                                "overflow": "auto",
                                "border": f"1px solid {BORDER}",
                                "maxHeight": "120px",
                            },
                        ),
                    ],
                    style={"marginBottom": "8px"},
                )
            )

    test_count_fig = go.Figure(
        go.Bar(
            x=(
                [k.split("/")[-1][:20] for k in list(generated_tests.keys())[:10]]
                if generated_tests
                else ["No tests yet"]
            ),
            y=[1] * len(list(generated_tests.keys())[:10]) if generated_tests else [0],
            marker_color=SUCCESS,
        )
    )
    test_count_fig.update_layout(title="Tests Generated per File", **PLOTLY_THEME)

    if not entries:
        entries = [
            html.Div("Awaiting test generation...", style={"color": TEXT, "fontFamily": FONT})
        ]

    return html.Div(
        [
            html.H4(
                "◈ VIZ06 — GENERATED TESTS PANEL",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            dcc.Graph(figure=test_count_fig, id="viz06-test-count"),
            html.Div(entries, style={"maxHeight": "200px", "overflowY": "auto"}),
        ],
        style=CARD_STYLE,
    )


def render_viz07_agent_log(pipeline_trace: Optional[List] = None, tokens_used: int = 0) -> html.Div:
    """VIZ07: Agent activity log."""
    log_entries = []
    if pipeline_trace:
        for i, entry in enumerate(pipeline_trace):
            color = ACCENT_BLUE if "claude" in entry.lower() or "doc" in entry.lower() else TEXT
            log_entries.append(
                html.Div(
                    f"{i+1:03d} | {entry}",
                    style={"color": color, "fontFamily": FONT, "fontSize": "10px"},
                )
            )
    else:
        log_entries = [
            html.Div(
                "Awaiting pipeline execution...",
                style={"color": TEXT, "fontFamily": FONT, "fontSize": "10px"},
            )
        ]

    cost_usd = tokens_used * (3 + 15) / 2 / 1_000_000

    return html.Div(
        [
            html.H4(
                "◈ VIZ07 — AGENT ACTIVITY LOG",
                style={
                    "color": ACCENT_BLUE,
                    "fontFamily": FONT,
                    "fontSize": "11px",
                    "letterSpacing": "2px",
                },
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                f"TOKENS: {tokens_used:,}",
                                style={
                                    "color": ACCENT_BLUE,
                                    "fontFamily": FONT,
                                    "fontSize": "12px",
                                },
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                f"COST: ${cost_usd:.4f}",
                                style={"color": WARNING, "fontFamily": FONT, "fontSize": "12px"},
                            ),
                        ],
                        width=4,
                    ),
                ],
                className="mb-2",
            ),
            html.Div(
                log_entries,
                style={
                    "backgroundColor": BG_PRIMARY,
                    "padding": "8px",
                    "height": "200px",
                    "overflowY": "auto",
                    "border": f"1px solid {BORDER}",
                },
            ),
        ],
        style=CARD_STYLE,
    )


def render_page(state: Optional[Dict] = None) -> html.Div:
    """Render the full Repo Ops Center page."""
    if state is None:
        state = {}
    return html.Div(
        [
            render_viz01_input(),
            render_viz02_repo_overview(state.get("repo_metadata")),
            render_viz03_complexity_heatmap(state.get("complexity_scores")),
            render_viz04_doc_coverage(state.get("doc_quality_scores")),
            render_viz05_doc_preview(state.get("generated_docs")),
            render_viz06_generated_tests(state.get("generated_tests")),
            render_viz07_agent_log(state.get("pipeline_trace"), state.get("claude_tokens_used", 0)),
        ]
    )
