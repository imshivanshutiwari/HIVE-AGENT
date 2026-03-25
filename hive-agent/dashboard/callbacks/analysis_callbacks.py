"""Analysis-related Dash callbacks."""

import logging

import requests as http_requests
from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"


def register_callbacks(app):
    """Register analysis callbacks on the Dash app."""

    @app.callback(
        Output("current-job-id", "data"),
        Output("live-analysis-log", "children"),
        Output("analysis-poll-interval", "disabled"),
        Input("analyze-btn", "n_clicks"),
        State("repo-url-input", "value"),
        prevent_initial_call=True,
    )
    def start_analysis(n_clicks, repo_url):
        if not repo_url:
            raise PreventUpdate
        try:
            resp = http_requests.post(
                f"{API_BASE}/analyze", json={"repo_url": repo_url}, timeout=10
            )
            data = resp.json()
            job_id = data.get("job_id", "")
            return job_id, [f"[HIVE-AGENT] Analysis started: job_id={job_id}"], False
        except Exception as e:
            return no_update, [f"[ERROR] Could not start analysis: {e}"], True

    @app.callback(
        Output("live-analysis-log", "children", allow_duplicate=True),
        Output("analysis-state", "data"),
        Output("analysis-poll-interval", "disabled", allow_duplicate=True),
        Input("analysis-poll-interval", "n_intervals"),
        State("current-job-id", "data"),
        prevent_initial_call=True,
    )
    def poll_status(n_intervals, job_id):
        if not job_id:
            raise PreventUpdate
        try:
            resp = http_requests.get(f"{API_BASE}/status/{job_id}", timeout=10)
            data = resp.json()
            status = data.get("status", "unknown")
            message = data.get("message", "")
            result = data.get("result") or {}
            log_entry = f"[{status.upper()}] {message}"
            if status in ("complete", "error"):
                return [log_entry], result, True
            return [log_entry], no_update, False
        except Exception as e:
            logger.debug(f"Poll failed: {e}")
            raise PreventUpdate
