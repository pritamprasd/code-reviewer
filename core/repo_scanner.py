"""
Repository Scanner & Code Graph Module
Scans branch_main to build an in-memory knowledge graph of symbols, imports,
class hierarchies, and call relationships.
Also includes a bridge to Graphify (graphify-out/graph.json) if available.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .git_reader import GitReader


@dataclass
class CodeSymbol:
    name: str
    kind: str  # 'class', 'interface', 'method', 'function', 'component'
    file_path: str
    line_number: int
    annotations: List[str] = field(default_factory=list)
    signature: str = ""
    docstring: str = ""


@dataclass
class FileContext:
    file_path: str
    class_name: str
    imports: List[str] = field(default_factory=list)
    symbols: List[CodeSymbol] = field(default_factory=list)
    referenced_symbols: Set[str] = field(default_factory=set)
    callers: List[str] = field(default_factory=list)  # Files in main that reference this class
    raw_content: Optional[str] = None


class RepoScanner:
    """
    Analyzes codebase at branch_main to build architectural context,
    symbol dependencies, and blast-radius tracking.
    """

    def __init__(self, git_reader: GitReader):
        self.git_reader = git_reader
        self.file_contexts: Dict[str, FileContext] = {}
        self.symbol_table: Dict[str, CodeSymbol] = {}
        self.graphify_data: Optional[dict] = None
        self._check_graphify()

    def _check_graphify(self):
        """Check if pre-generated Graphify output exists in repo."""
        graph_path = os.path.join(self.git_reader.repo_path, "graphify-out", "graph.json")
        if os.path.exists(graph_path):
            try:
                with open(graph_path, "r", encoding="utf-8") as f:
                    self.graphify_data = json.load(f)
            except Exception:
                self.graphify_data = None

    def scan_file_context(self, relative_path: str, branch: Optional[str] = None) -> FileContext:
        """
        Scan a specific file at branch_main (or local working copy)
        and extract structural AST symbols.
        """
        clean_path = relative_path.replace("\\", "/").lstrip("/")
        if clean_path in self.file_contexts:
            return self.file_contexts[clean_path]

        content = self.git_reader.read_file_at_branch(clean_path, branch)
        if content is None:
            # Fallback to local file if not yet committed to main
            content = self.git_reader.read_local_working_file(clean_path)

        filename = clean_path.split("/")[-1]
        base_name = filename.rsplit(".", 1)[0]
        ctx = FileContext(file_path=clean_path, class_name=base_name, raw_content=content)

        if not content:
            self.file_contexts[clean_path] = ctx
            return ctx

        # Language-specific extraction
        if clean_path.endswith(".java"):
            self._extract_java_symbols(clean_path, content, ctx)
        elif clean_path.endswith((".tsx", ".jsx", ".ts", ".js")):
            self._extract_javascript_symbols(clean_path, content, ctx)
        elif clean_path.endswith(".py"):
            self._extract_python_symbols(clean_path, content, ctx)

        self.file_contexts[clean_path] = ctx
        return ctx

    def _extract_java_symbols(self, file_path: str, content: str, ctx: FileContext):
        """Extract Java package, imports, class annotations, methods."""
        lines = content.splitlines()
        current_annotations: List[str] = []

        import_regex = re.compile(r"^\s*import\s+([\w\.\*]+);")
        class_regex = re.compile(
            r"^\s*(public|protected|private)?\s*(abstract|final)?\s*(class|interface|enum|record)\s+(\w+)"
        )
        method_regex = re.compile(
            r"^\s*(public|protected|private)?\s*(static|final|abstract|synchronized)?\s*[\w\<\>\[\],\s]+\s+(\w+)\s*\([^\)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{?"
        )
        annotation_regex = re.compile(r"^\s*(@\w+(?:\([^\)]*\))?)")

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()

            # Imports
            imp_m = import_regex.match(stripped)
            if imp_m:
                ctx.imports.append(imp_m.group(1))
                continue

            # Annotations
            ann_m = annotation_regex.match(stripped)
            if ann_m:
                current_annotations.append(ann_m.group(1))
                continue

            # Class definition
            cls_m = class_regex.match(stripped)
            if cls_m:
                cls_kind = cls_m.group(3)
                cls_name = cls_m.group(4)
                ctx.class_name = cls_name
                sym = CodeSymbol(
                    name=cls_name,
                    kind=cls_kind,
                    file_path=file_path,
                    line_number=idx,
                    annotations=list(current_annotations),
                    signature=stripped,
                )
                ctx.symbols.append(sym)
                self.symbol_table[cls_name] = sym
                current_annotations = []
                continue

            # Method definition
            meth_m = method_regex.match(stripped)
            if meth_m and not stripped.startswith("if") and not stripped.startswith("for") and not stripped.startswith("while"):
                meth_name = meth_m.group(3)
                if meth_name not in ["new", "equals", "hashCode", "toString"]:
                    sym = CodeSymbol(
                        name=meth_name,
                        kind="method",
                        file_path=file_path,
                        line_number=idx,
                        annotations=list(current_annotations),
                        signature=stripped,
                    )
                    ctx.symbols.append(sym)
                    current_annotations = []
                continue

            if not stripped.startswith("@"):
                current_annotations = []

    def _extract_javascript_symbols(self, file_path: str, content: str, ctx: FileContext):
        """Extract React/TypeScript components, hooks, imports."""
        lines = content.splitlines()
        import_regex = re.compile(r"^\s*import\s+.*from\s+['\"](.*)['\"];?")
        fn_regex = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:function|const)\s+(\w+)")
        hook_regex = re.compile(r"\b(use[A-Z]\w+)\b")

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            # Imports
            imp_m = import_regex.match(stripped)
            if imp_m:
                ctx.imports.append(imp_m.group(1))

            # React hooks referenced
            for hook in hook_regex.findall(stripped):
                ctx.referenced_symbols.add(hook)

            # Component or function
            fn_m = fn_regex.match(stripped)
            if fn_m:
                name = fn_m.group(1)
                kind = "component" if name[0].isupper() else "function"
                sym = CodeSymbol(
                    name=name,
                    kind=kind,
                    file_path=file_path,
                    line_number=idx,
                    signature=stripped,
                )
                ctx.symbols.append(sym)
                self.symbol_table[name] = sym

    def _extract_python_symbols(self, file_path: str, content: str, ctx: FileContext):
        """Extract Python classes, methods, imports."""
        import ast

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    sym = CodeSymbol(
                        name=node.name,
                        kind="class",
                        file_path=file_path,
                        line_number=node.lineno,
                    )
                    ctx.symbols.append(sym)
                    self.symbol_table[node.name] = sym
                elif isinstance(node, ast.FunctionDef):
                    sym = CodeSymbol(
                        name=node.name,
                        kind="function",
                        file_path=file_path,
                        line_number=node.lineno,
                    )
                    ctx.symbols.append(sym)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        ctx.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        ctx.imports.append(node.module)
        except Exception:
            pass

    def find_callers_and_blast_radius(self, target_class_or_symbol: str) -> List[str]:
        """
        Search repository for files that reference or import this symbol.
        Uses local grep/ripgrep or git grep without network calls.
        """
        callers = []
        # First check Graphify data if present
        if self.graphify_data and "nodes" in self.graphify_data and "edges" in self.graphify_data:
            for edge in self.graphify_data.get("edges", []):
                if edge.get("target") == target_class_or_symbol:
                    callers.append(edge.get("source"))
            if callers:
                return list(set(callers))[:10]

        # Otherwise perform local git grep
        import subprocess

        try:
            res = subprocess.run(
                ["git", "grep", "-l", target_class_or_symbol],
                cwd=self.git_reader.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    p = line.strip()
                    if p and not p.endswith(".min.js"):
                        callers.append(p)
        except Exception:
            pass

        return callers[:10]

    def build_context_summary(self, relative_paths: List[str]) -> str:
        """
        Build an architectural context summary for a list of changed files,
        providing existing main branch context, class signatures, and blast radius.
        """
        sections = []
        for path in relative_paths:
            ctx = self.scan_file_context(path)
            callers = self.find_callers_and_blast_radius(ctx.class_name)

            sec = [f"### Context for: `{path}` (Class/Symbol: `{ctx.class_name}`)"]
            if ctx.symbols:
                sec.append("**Declared Symbols in main branch:**")
                for s in ctx.symbols[:8]:
                    ann = f"[{', '.join(s.annotations)}] " if s.annotations else ""
                    sec.append(f"- Line {s.line_number}: {ann}`{s.signature or s.name}` ({s.kind})")

            if ctx.imports:
                sec.append(f"**Key Imports:** {', '.join(ctx.imports[:10])}")

            if callers:
                sec.append(f"**Potential Blast Radius (Referenced by {len(callers)} files in repo):**")
                for c in callers[:5]:
                    sec.append(f"- `{c}`")

            # Include existing main branch implementation snippet if available
            if ctx.raw_content:
                lines = ctx.raw_content.splitlines()
                if len(lines) <= 120:
                    sec.append(f"\n```\n{ctx.raw_content}\n```")
                else:
                    sec.append(f"\n*(File is {len(lines)} lines in main branch. Showing first 60 lines for baseline reference)*\n")
                    sec.append(f"```\n" + "\n".join(lines[:60]) + "\n```")
            else:
                sec.append("*(File is newly created in this PR or does not exist in main branch)*")

            sections.append("\n".join(sec))

        return "\n\n" + ("\n" + "-" * 40 + "\n").join(sections)
