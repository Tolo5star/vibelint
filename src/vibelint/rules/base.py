"""Base class for all VibeLint rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity


class Rule(ABC):
    """Base rule that all detectors inherit from."""

    meta: RuleMeta  # subclasses must define this as a class attribute

    @abstractmethod
    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        """Run this rule against a parsed file. Return list of findings."""
        ...

    # ── AST helpers ──────────────────────────────────────────────────────

    @staticmethod
    def walk(node: Node) -> Iterator[Node]:
        """Depth-first walk of all nodes in the tree."""
        cursor = node.walk()
        visited = False

        while True:
            if not visited:
                yield cursor.node
                if cursor.goto_first_child():
                    continue
            if cursor.goto_next_sibling():
                visited = False
                continue
            if not cursor.goto_parent():
                break
            visited = True

    @staticmethod
    def find_all(node: Node, type_name: str) -> Iterator[Node]:
        """Yield all descendant nodes matching a given type."""
        for child in Rule.walk(node):
            if child.type == type_name:
                yield child

    @staticmethod
    def node_text(node: Node, source: bytes) -> str:
        """Extract the source text of a node."""
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    @staticmethod
    def get_line_snippet(source: bytes, line: int, context: int = 0) -> str:
        """Get source line(s) as a string (1-indexed)."""
        lines = source.decode("utf-8", errors="replace").splitlines()
        start = max(0, line - 1 - context)
        end = min(len(lines), line + context)
        return "\n".join(lines[start:end])

    def _make_finding(
        self,
        file_path: Path,
        node: Node,
        source: bytes,
        message: str,
        fix: str,
    ) -> Finding:
        """Helper to construct a Finding from a node."""
        return Finding(
            rule_id=self.meta.id,
            severity=self.meta.severity,
            file=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            message=message,
            fix=fix,
            multiplier=self.meta.multiplier,
            source=self.meta.source,
            snippet=self.get_line_snippet(source, node.start_point[0] + 1),
        )
