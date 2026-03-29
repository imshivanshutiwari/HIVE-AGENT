"""Full Python AST analysis using stdlib ast module."""

import ast
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class ImportInfo:
    module: str
    names: List[str]
    alias: str
    is_from: bool
    line: int


@dataclass
class FunctionInfo:
    name: str
    args: List[str]
    return_type: str
    decorators: List[str]
    docstring: str
    body_lines: int
    calls_made: List[str]
    raises: List[str]
    yields: bool
    is_async: bool
    cyclomatic_complexity: int
    cognitive_complexity: int
    lineno: int
    col_offset: int
    source: str = ""


@dataclass
class ClassInfo:
    name: str
    bases: List[str]
    methods: List[FunctionInfo]
    docstring: str
    decorators: List[str]
    lineno: int


@dataclass
class ASTResult:
    filepath: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    globals: List[str] = field(default_factory=list)
    docstrings: Dict[str, str] = field(default_factory=dict)
    type_hints: Dict[str, str] = field(default_factory=dict)
    module_docstring: str = ""
    call_graph: Optional[nx.DiGraph] = None
    parse_error: Optional[str] = None


class PythonASTParser:
    """Full Python AST analysis using stdlib ast module."""

    def parse_file(self, filepath: str) -> ASTResult:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except OSError as e:
            return ASTResult(filepath=filepath, parse_error=str(e))

        return self.parse_source(source, filepath)

    def parse_source(self, source: str, filepath: str = "<string>") -> ASTResult:
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return ASTResult(filepath=filepath, parse_error=str(e))

        result = ASTResult(filepath=filepath)
        result.module_docstring = ast.get_docstring(tree) or ""
        result.imports = self._extract_imports(tree)
        result.globals = self._extract_globals(tree)
        result.call_graph = self.extract_call_graph(tree)

        source_lines = source.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls = self._extract_class_info(node, source_lines)
                result.classes.append(cls)
                result.docstrings[f"class:{cls.name}"] = cls.docstring
                for meth in cls.methods:
                    result.type_hints[f"{cls.name}.{meth.name}"] = meth.return_type

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions (not methods)
                parent = self._get_parent(tree, node)
                if not isinstance(parent, ast.ClassDef):
                    func = self.extract_function_info(node, source_lines)
                    result.functions.append(func)
                    result.docstrings[f"func:{func.name}"] = func.docstring
                    result.type_hints[func.name] = func.return_type

        return result

    def _get_parent(self, tree: ast.AST, target: ast.AST) -> Optional[ast.AST]:
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child is target:
                    return node
        return None

    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            names=[alias.name],
                            alias=alias.asname or "",
                            is_from=False,
                            line=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [a.name for a in node.names]
                imports.append(
                    ImportInfo(
                        module=module,
                        names=names,
                        alias="",
                        is_from=True,
                        line=node.lineno,
                    )
                )
        return imports

    def _extract_globals(self, tree: ast.AST) -> List[str]:
        globals_list = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        globals_list.append(target.id)
            elif isinstance(node, (ast.AnnAssign,)):
                if isinstance(node.target, ast.Name):
                    globals_list.append(node.target.id)
        return globals_list

    def extract_function_info(
        self, node: ast.FunctionDef, source_lines: Optional[List[str]] = None
    ) -> FunctionInfo:
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        return_type = ""
        if node.returns:
            return_type = ast.unparse(node.returns)

        decorators = [ast.unparse(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node) or ""

        body_lines = (node.end_lineno or node.lineno) - node.lineno + 1

        calls_made = []
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Name):
                    calls_made.append(n.func.id)
                elif isinstance(n.func, ast.Attribute):
                    calls_made.append(n.func.attr)

        raises = []
        for n in ast.walk(node):
            if isinstance(n, ast.Raise) and n.exc:
                if isinstance(n.exc, ast.Call) and isinstance(n.exc.func, ast.Name):
                    raises.append(n.exc.func.id)
                elif isinstance(n.exc, ast.Name):
                    raises.append(n.exc.id)

        yields = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node))
        is_async = isinstance(node, ast.AsyncFunctionDef)

        cc = self.compute_cyclomatic_complexity(node)
        cog = self.compute_cognitive_complexity(node)

        source = ""
        if source_lines:
            start = node.lineno - 1
            end = node.end_lineno or node.lineno
            source = "\n".join(source_lines[start:end])

        return FunctionInfo(
            name=node.name,
            args=args,
            return_type=return_type,
            decorators=decorators,
            docstring=docstring,
            body_lines=body_lines,
            calls_made=list(set(calls_made)),
            raises=raises,
            yields=yields,
            is_async=is_async,
            cyclomatic_complexity=cc,
            cognitive_complexity=cog,
            lineno=node.lineno,
            col_offset=node.col_offset,
            source=source,
        )

    def _extract_class_info(
        self, node: ast.ClassDef, source_lines: Optional[List[str]] = None
    ) -> ClassInfo:
        bases = [ast.unparse(b) for b in node.bases]
        docstring = ast.get_docstring(node) or ""
        decorators = [ast.unparse(d) for d in node.decorator_list]
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self.extract_function_info(item, source_lines))
        return ClassInfo(
            name=node.name,
            bases=bases,
            methods=methods,
            docstring=docstring,
            decorators=decorators,
            lineno=node.lineno,
        )

    def compute_cyclomatic_complexity(self, node: ast.AST) -> int:
        """McCabe cyclomatic complexity: M = E - N + 2P."""
        complexity = 1
        for n in ast.walk(node):
            if isinstance(n, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(n, ast.BoolOp):
                complexity += len(n.values) - 1
            elif isinstance(n, (ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(n, ast.IfExp):
                complexity += 1
        return complexity

    def compute_cognitive_complexity(self, node: ast.AST) -> int:
        """SonarSource cognitive complexity algorithm."""

        def _walk(nodes, nesting: int) -> int:
            score = 0
            for n in nodes:
                if isinstance(n, (ast.If, ast.IfExp)):
                    score += 1 + nesting
                    score += _walk(ast.iter_child_nodes(n), nesting + 1)
                elif isinstance(n, (ast.For, ast.While, ast.AsyncFor)):
                    score += 1 + nesting
                    score += _walk(ast.iter_child_nodes(n), nesting + 1)
                elif isinstance(n, (ast.Try, ast.ExceptHandler)):
                    score += 1 + nesting
                    score += _walk(ast.iter_child_nodes(n), nesting + 1)
                elif isinstance(n, ast.BoolOp):
                    score += len(n.values) - 1
                    score += _walk(ast.iter_child_nodes(n), nesting)
                else:
                    score += _walk(ast.iter_child_nodes(n), nesting)
            return score

        return _walk(ast.iter_child_nodes(node), 0)

    def extract_call_graph(self, tree: ast.AST) -> nx.DiGraph:
        """Build directed call graph: caller -> callee."""
        graph = nx.DiGraph()
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] = node

        for fname, fnode in functions.items():
            graph.add_node(fname)
            for n in ast.walk(fnode):
                if isinstance(n, ast.Call):
                    if isinstance(n.func, ast.Name):
                        callee = n.func.id
                    elif isinstance(n.func, ast.Attribute):
                        callee = n.func.attr
                    else:
                        continue
                    if callee in functions:
                        graph.add_edge(fname, callee)

        return graph
