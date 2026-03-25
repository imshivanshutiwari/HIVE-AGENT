"""All @tool functions for Claude tool_use in LangGraph agents."""

import logging

logger = logging.getLogger(__name__)

# Tool definitions as dicts for Anthropic tool_use API

TOOLS_FETCHER = [
    {
        "name": "clone_repository",
        "description": "Clone a GitHub repository to local disk",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "fetch_metadata",
        "description": "Fetch repository metadata via REST + GraphQL APIs",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "list_files",
        "description": "List all code files in cloned repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["repo_path"],
        },
    },
    {
        "name": "get_commit_history",
        "description": "Fetch commit history from GitHub REST API",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "n": {"type": "integer", "default": 100},
            },
            "required": ["owner", "repo"],
        },
    },
]

TOOLS_PARSER = [
    {
        "name": "parse_python_ast",
        "description": "Parse a Python file using stdlib ast module",
        "input_schema": {
            "type": "object",
            "properties": {"filepath": {"type": "string"}},
            "required": ["filepath"],
        },
    },
    {
        "name": "parse_with_treesitter",
        "description": "Parse a non-Python file using tree-sitter",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "language": {"type": "string"},
            },
            "required": ["filepath", "language"],
        },
    },
    {
        "name": "extract_imports",
        "description": "Extract all imports from a source file",
        "input_schema": {
            "type": "object",
            "properties": {"filepath": {"type": "string"}},
            "required": ["filepath"],
        },
    },
    {
        "name": "build_call_graph",
        "description": "Build function call graph from AST",
        "input_schema": {
            "type": "object",
            "properties": {"filepath": {"type": "string"}},
            "required": ["filepath"],
        },
    },
]

TOOLS_ANALYZER = [
    {
        "name": "build_dependency_graph",
        "description": "Build NetworkX dependency graph for a repository",
        "input_schema": {
            "type": "object",
            "properties": {"repo_path": {"type": "string"}},
            "required": ["repo_path"],
        },
    },
    {
        "name": "compute_complexity",
        "description": "Compute cyclomatic and cognitive complexity for all files",
        "input_schema": {
            "type": "object",
            "properties": {"repo_path": {"type": "string"}},
            "required": ["repo_path"],
        },
    },
    {
        "name": "detect_smells",
        "description": "Detect code smells in a Python file",
        "input_schema": {
            "type": "object",
            "properties": {"filepath": {"type": "string"}},
            "required": ["filepath"],
        },
    },
    {
        "name": "run_security_scan",
        "description": "Run bandit security scan on a directory",
        "input_schema": {
            "type": "object",
            "properties": {"dirpath": {"type": "string"}},
            "required": ["dirpath"],
        },
    },
]

TOOLS_SIMILARITY = [
    {
        "name": "embed_functions",
        "description": "Compute CodeBERT embeddings for all functions",
        "input_schema": {
            "type": "object",
            "properties": {
                "functions": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": ["functions"],
        },
    },
    {
        "name": "detect_clones",
        "description": "Detect code clones above similarity threshold",
        "input_schema": {
            "type": "object",
            "properties": {"threshold": {"type": "number", "default": 0.9}},
        },
    },
    {
        "name": "cluster_code",
        "description": "Cluster functions by semantic similarity",
        "input_schema": {
            "type": "object",
            "properties": {"n_clusters": {"type": "integer", "default": 20}},
        },
    },
    {
        "name": "find_dead_code",
        "description": "Find unreachable and unused code",
        "input_schema": {
            "type": "object",
            "properties": {"filepath": {"type": "string"}},
            "required": ["filepath"],
        },
    },
]

TOOLS_DOC = [
    {
        "name": "generate_function_doc",
        "description": "Generate Google-style docstring for a function",
        "input_schema": {
            "type": "object",
            "properties": {
                "function_name": {"type": "string"},
                "function_source": {"type": "string"},
                "args": {"type": "array", "items": {"type": "string"}},
                "return_type": {"type": "string"},
                "calls_made": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["function_name", "function_source"],
        },
    },
    {
        "name": "generate_class_doc",
        "description": "Generate documentation for a class",
        "input_schema": {
            "type": "object",
            "properties": {
                "class_name": {"type": "string"},
                "class_source": {"type": "string"},
                "bases": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["class_name", "class_source"],
        },
    },
    {
        "name": "generate_module_doc",
        "description": "Generate module-level documentation",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "module_content": {"type": "string"},
            },
            "required": ["filepath"],
        },
    },
    {
        "name": "generate_readme",
        "description": "Generate full repo README",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_metadata": {"type": "object"},
                "file_list": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["repo_metadata"],
        },
    },
]

TOOLS_REVIEW = [
    {
        "name": "review_function",
        "description": "Review a function and suggest improvements",
        "input_schema": {
            "type": "object",
            "properties": {
                "function_name": {"type": "string"},
                "function_source": {"type": "string"},
                "complexity": {"type": "integer"},
            },
            "required": ["function_name", "function_source"],
        },
    },
    {
        "name": "suggest_refactor",
        "description": "Suggest refactoring for high-complexity code",
        "input_schema": {
            "type": "object",
            "properties": {
                "function_source": {"type": "string"},
                "smells": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["function_source"],
        },
    },
    {
        "name": "flag_security_issue",
        "description": "Flag a security vulnerability in code",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "line": {"type": "integer"},
                "description": {"type": "string"},
            },
            "required": ["filepath", "description"],
        },
    },
]

TOOLS_TEST = [
    {
        "name": "generate_unit_tests",
        "description": "Generate pytest unit tests for a function",
        "input_schema": {
            "type": "object",
            "properties": {
                "function_name": {"type": "string"},
                "function_source": {"type": "string"},
                "args": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["function_name", "function_source"],
        },
    },
    {
        "name": "generate_property_tests",
        "description": "Generate Hypothesis property-based tests",
        "input_schema": {
            "type": "object",
            "properties": {
                "function_name": {"type": "string"},
                "function_source": {"type": "string"},
                "type_hints": {"type": "object"},
            },
            "required": ["function_name", "function_source"],
        },
    },
    {
        "name": "generate_integration_tests",
        "description": "Generate integration tests for a module",
        "input_schema": {
            "type": "object",
            "properties": {
                "module_name": {"type": "string"},
                "functions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["module_name"],
        },
    },
]

TOOLS_EVALUATOR = [
    {
        "name": "compute_bertscore",
        "description": "Compute BERTScore for generated documentation",
        "input_schema": {
            "type": "object",
            "properties": {
                "generated": {"type": "array", "items": {"type": "string"}},
                "reference": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["generated", "reference"],
        },
    },
    {
        "name": "compute_rouge",
        "description": "Compute ROUGE scores for documentation",
        "input_schema": {
            "type": "object",
            "properties": {
                "generated": {"type": "string"},
                "reference": {"type": "string"},
            },
            "required": ["generated", "reference"],
        },
    },
    {
        "name": "measure_coverage",
        "description": "Measure documentation coverage percentage",
        "input_schema": {
            "type": "object",
            "properties": {"repo_path": {"type": "string"}},
            "required": ["repo_path"],
        },
    },
    {
        "name": "apply_rubric",
        "description": "Apply quality rubric to a docstring",
        "input_schema": {
            "type": "object",
            "properties": {
                "docstring": {"type": "string"},
                "function_info": {"type": "object"},
            },
            "required": ["docstring"],
        },
    },
]
