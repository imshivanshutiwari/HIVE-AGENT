"""HIVE-AGENT Dev Intelligence Ops Dashboard."""

import logging
import threading
import time
import webbrowser
from typing import Dict

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html
from dotenv import load_dotenv

from dashboard.theme import (
    BG_PRIMARY,
    BG_PANEL,
    ACCENT_BLUE,
    SUCCESS,
    WARNING,
    INFO,
    TEXT,
    BORDER,
    FONT,
    HEADER_STYLE,
)

load_dotenv()
logger = logging.getLogger(__name__)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="HIVE-AGENT | Dev Intelligence Ops",
    update_title=None,
)
server = app.server


def make_header() -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "◈ HIVE-AGENT",
                        style={"color": ACCENT_BLUE, "fontWeight": "bold", "fontSize": "14px"},
                    ),
                    html.Span(
                        "  [CODEBASE INTELLIGENCE v1.0]", style={"color": TEXT, "fontSize": "11px"}
                    ),
                ]
            ),
            html.Div(
                [
                    html.Span(
                        id="header-repos",
                        children="REPOS ANALYZED: 0",
                        style={"marginRight": "16px", "color": TEXT, "fontSize": "10px"},
                    ),
                    html.Span(
                        id="header-docs",
                        children="DOCS GENERATED: 0",
                        style={"marginRight": "16px", "color": TEXT, "fontSize": "10px"},
                    ),
                    html.Span(
                        id="header-tokens",
                        children="TOKENS USED: 0",
                        style={"marginRight": "16px", "color": TEXT, "fontSize": "10px"},
                    ),
                    html.Span(
                        id="header-cost",
                        children="COST: $0.000",
                        style={"marginRight": "16px", "color": WARNING, "fontSize": "10px"},
                    ),
                    html.Span("● ONLINE", style={"color": SUCCESS, "fontSize": "10px"}),
                ]
            ),
            html.Div(
                [
                    html.Span(
                        "[CLAUDE: claude-sonnet-4-6]",
                        style={
                            "marginRight": "8px",
                            "color": ACCENT_BLUE,
                            "fontSize": "9px",
                            "border": f"1px solid {BORDER}",
                            "padding": "1px 4px",
                        },
                    ),
                    html.Span(
                        "[GITHUB: CONNECTED]",
                        style={
                            "marginRight": "8px",
                            "color": SUCCESS,
                            "fontSize": "9px",
                            "border": f"1px solid {BORDER}",
                            "padding": "1px 4px",
                        },
                    ),
                    html.Span(
                        "[CODEBERT: LOADED]",
                        style={
                            "marginRight": "8px",
                            "color": ACCENT_BLUE,
                            "fontSize": "9px",
                            "border": f"1px solid {BORDER}",
                            "padding": "1px 4px",
                        },
                    ),
                    html.Span(
                        "[LANGGRAPH: 8 NODES]",
                        style={
                            "marginRight": "8px",
                            "color": INFO,
                            "fontSize": "9px",
                            "border": f"1px solid {BORDER}",
                            "padding": "1px 4px",
                        },
                    ),
                    html.Span(
                        "[RATE: OK]",
                        style={
                            "color": SUCCESS,
                            "fontSize": "9px",
                            "border": f"1px solid {BORDER}",
                            "padding": "1px 4px",
                        },
                    ),
                ]
            ),
        ],
        style={
            **HEADER_STYLE,
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
        },
    )


app.layout = html.Div(
    [
        make_header(),
        dbc.Tabs(
            [
                dbc.Tab(
                    label="◈ REPO OPS CENTER",
                    tab_id="tab-repo-ops",
                    label_style={"fontFamily": FONT, "fontSize": "10px", "color": ACCENT_BLUE},
                ),
                dbc.Tab(
                    label="◈ CODE INTELLIGENCE",
                    tab_id="tab-code-intel",
                    label_style={"fontFamily": FONT, "fontSize": "10px", "color": ACCENT_BLUE},
                ),
                dbc.Tab(
                    label="◈ AGENT FLOW",
                    tab_id="tab-agent-flow",
                    label_style={"fontFamily": FONT, "fontSize": "10px", "color": ACCENT_BLUE},
                ),
                dbc.Tab(
                    label="◈ DOC QUALITY",
                    tab_id="tab-doc-quality",
                    label_style={"fontFamily": FONT, "fontSize": "10px", "color": ACCENT_BLUE},
                ),
                dbc.Tab(
                    label="◈ REPO HEALTH",
                    tab_id="tab-repo-health",
                    label_style={"fontFamily": FONT, "fontSize": "10px", "color": ACCENT_BLUE},
                ),
            ],
            id="main-tabs",
            active_tab="tab-repo-ops",
            style={"backgroundColor": BG_PANEL, "borderBottom": f"1px solid {BORDER}"},
        ),
        html.Div(
            id="tab-content",
            style={"backgroundColor": BG_PRIMARY, "minHeight": "100vh", "padding": "12px"},
        ),
        dcc.Store(id="global-state", data={}),
        dcc.Interval(id="header-update", interval=5000),
    ],
    style={"backgroundColor": BG_PRIMARY, "minHeight": "100vh"},
)


@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab"),
    State("global-state", "data"),
)
def render_tab(active_tab: str, global_state: Dict) -> html.Div:
    state = global_state or {}
    if active_tab == "tab-repo-ops":
        from dashboard.pages.repo_ops import render_page

        return render_page(state)
    elif active_tab == "tab-code-intel":
        from dashboard.pages.code_intel import render_page

        return render_page(state)
    elif active_tab == "tab-agent-flow":
        from dashboard.pages.agent_flow import render_page

        return render_page(state)
    elif active_tab == "tab-doc-quality":
        from dashboard.pages.doc_quality import render_page

        return render_page(state)
    elif active_tab == "tab-repo-health":
        from dashboard.pages.repo_health import render_page

        return render_page(state)
    return html.Div("Unknown tab", style={"color": TEXT})


@app.callback(
    Output("header-repos", "children"),
    Output("header-docs", "children"),
    Output("header-tokens", "children"),
    Output("header-cost", "children"),
    Input("header-update", "n_intervals"),
    State("global-state", "data"),
)
def update_header(n, global_state):
    state = global_state or {}
    docs = len(state.get("generated_docs", {}))
    tokens = state.get("claude_tokens_used", 0)
    cost = tokens * (3 + 15) / 2 / 1_000_000
    repos = 1 if state.get("repo_metadata") else 0
    return (
        f"REPOS ANALYZED: {repos}",
        f"DOCS GENERATED: {docs}",
        f"TOKENS USED: {tokens:,}",
        f"COST: ${cost:.3f}",
    )


from dashboard.callbacks.analysis_callbacks import register_callbacks as reg_analysis  # noqa: E402

reg_analysis(app)


def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8050")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, host="0.0.0.0", port=8050)
