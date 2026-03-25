# HIVE-AGENT

> Autonomous Codebase Analyst and Documentation Generator

## Overview
HIVE-AGENT uses Claude claude-sonnet-4-6, LangGraph, and CodeBERT to analyze GitHub repositories and automatically generate high-quality documentation and tests.

## Architecture
LangGraph 8-node StateGraph: Fetcher → Parser → Analyzer → Similarity → DocAgent → Review → TestAgent → Evaluator

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env  # add API keys
```

## Usage
```bash
make run     # Opens dashboard at localhost:8050
make analyze # Analyze psf/requests
make test    # Run 30 tests
```

## Dashboard
22 visualizations across 5 pages: Repo Ops, Code Intelligence, Agent Flow, Doc Quality, Repo Health.

## Tech Stack
- LLM: Anthropic claude-sonnet-4-6 (tool_use + streaming)
- Orchestration: LangGraph 8-node StateGraph
- Code Analysis: Python ast + tree-sitter (10 languages)
- Embeddings: CodeBERT + GraphCodeBERT
- Graph: NetworkX + PageRank
- UI: Plotly Dash 2.17.0 (dark blue theme, 22 vizualizations)
- Evaluation: BERTScore + ROUGE + quality rubric
- Testing: pytest + Hypothesis

## Pages
1. **Repo Ops Center** (VIZ01-07): Input, overview, complexity, doc coverage, doc preview, tests, agent log
2. **Code Intelligence** (VIZ08-13): Dependency graph, histogram, clone detection, call graph, security, smell radar
3. **Agent Flow** (VIZ14-17): LangGraph flow, timeline, token usage, tool call frequency
4. **Doc Quality** (VIZ18-20): BERTScore+ROUGE, rubric radar, before/after comparison
5. **Repo Health** (VIZ21-22): Commit activity, health scorecard with grade

## Configuration
All configs in `configs/`. Set `ANTHROPIC_API_KEY` and `GITHUB_TOKEN` in `.env`.

## API
FastAPI server at `http://localhost:8000`. POST `/analyze`, GET `/status/{job_id}`.

## Tests
```bash
pytest tests/ -v  # 30 tests
```

## CI/CD
GitHub Actions: `.github/workflows/ci.yml` (test + lint), `.github/workflows/lint.yml`.

## Evaluation
BERTScore F1 + ROUGE-1/2/L + 6-dimension quality rubric (Completeness, Accuracy, Clarity, Examples, Edge Cases, Consistency).

## License
MIT
