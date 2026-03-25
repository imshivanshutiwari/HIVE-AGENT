"""NetworkX directed dependency graph with PageRank, coupling metrics."""

import ast
import logging
import os
from dataclasses import dataclass
from typing import List, Dict, Optional

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class CouplingMetrics:
    afferent_coupling: int = 0  # Ca: how many modules depend on this
    efferent_coupling: int = 0  # Ce: how many modules this depends on
    instability: float = 0.0  # Ce / (Ca + Ce)


class DependencyGraphBuilder:
    """Build NetworkX directed dependency graph from a repo."""

    def build_graph(self, repo_path: str) -> nx.DiGraph:
        graph = nx.DiGraph()
        py_files = self._find_python_files(repo_path)

        for filepath in py_files:
            module_name = self._path_to_module(filepath, repo_path)
            if not graph.has_node(module_name):
                loc = self._count_lines(filepath)
                graph.add_node(
                    module_name,
                    filepath=filepath,
                    language="python",
                    complexity=0,
                    loc=loc,
                    doc_coverage=0.0,
                )

        for filepath in py_files:
            module_name = self._path_to_module(filepath, repo_path)
            imports = self._extract_python_imports(filepath)
            for imp in imports:
                normalized = self._normalize_import(imp, repo_path)
                if normalized and graph.has_node(normalized) and normalized != module_name:
                    graph.add_edge(
                        module_name,
                        normalized,
                        import_type="import",
                        line_number=0,
                    )

        return graph

    def _find_python_files(self, repo_path: str) -> List[str]:
        files = []
        for root, dirs, filenames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules"}]
            for f in filenames:
                if f.endswith(".py"):
                    files.append(os.path.join(root, f))
        return files

    def _path_to_module(self, filepath: str, repo_path: str) -> str:
        rel = os.path.relpath(filepath, repo_path)
        module = rel.replace(os.sep, ".")[:-3]  # strip trailing ".py"
        return module

    def _count_lines(self, filepath: str) -> int:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except OSError:
            return 0

    def _extract_python_imports(self, filepath: str) -> List[str]:
        imports = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except SyntaxError:
            pass
        return imports

    def _normalize_import(self, import_name: str, repo_path: str) -> Optional[str]:
        """Normalize an import to a module name present in the graph."""
        parts = import_name.split(".")
        for i in range(len(parts), 0, -1):
            candidate = ".".join(parts[:i])
            filepath = os.path.join(repo_path, candidate.replace(".", os.sep) + ".py")
            if os.path.exists(filepath):
                return candidate
            init_path = os.path.join(repo_path, candidate.replace(".", os.sep), "__init__.py")
            if os.path.exists(init_path):
                return candidate
        return None

    def compute_pagerank(self, graph: nx.DiGraph) -> Dict[str, float]:
        if len(graph) == 0:
            return {}
        try:
            return nx.pagerank(graph, alpha=0.85)
        except nx.PowerIterationFailedConvergence:
            return {n: 1.0 / len(graph) for n in graph.nodes()}

    def find_circular_dependencies(self, graph: nx.DiGraph) -> List[List[str]]:
        return list(nx.simple_cycles(graph))

    def compute_coupling_metrics(self, graph: nx.DiGraph) -> Dict[str, CouplingMetrics]:
        metrics = {}
        for node in graph.nodes():
            ca = graph.in_degree(node)
            ce = graph.out_degree(node)
            instability = ce / (ca + ce) if (ca + ce) > 0 else 0.0
            metrics[node] = CouplingMetrics(
                afferent_coupling=ca,
                efferent_coupling=ce,
                instability=instability,
            )
        return metrics

    def find_god_modules(self, graph: nx.DiGraph, threshold: int = 10) -> List[str]:
        return [node for node in graph.nodes() if graph.out_degree(node) > threshold]

    def export_to_cytoscape(self, graph: nx.DiGraph) -> List[Dict]:
        elements = []
        pagerank = self.compute_pagerank(graph)
        for node in graph.nodes():
            data = dict(graph.nodes[node])
            data["id"] = node
            data["label"] = node.split(".")[-1]
            data["pagerank"] = pagerank.get(node, 0.0)
            elements.append({"data": data, "group": "nodes"})
        for u, v, edge_data in graph.edges(data=True):
            elements.append(
                {
                    "data": {
                        "id": f"{u}->{v}",
                        "source": u,
                        "target": v,
                        **edge_data,
                    },
                    "group": "edges",
                }
            )
        return elements
