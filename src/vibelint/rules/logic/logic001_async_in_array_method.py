"""
AI-LOGIC-001: Async function in array method (.map / .filter / .forEach)

AI generators frequently produce:
    const results = arr.map(async (item) => { ... });

This returns Promise[], not resolved values. The most common Node.js
hallucination from code-generation tools.

Fix: Use `await Promise.all(arr.map(...))` or a `for...of` loop.
Source: eslint-plugin-llm-core, 1.75x logic error multiplier (CodeRabbit 2025)
"""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity
from vibelint.rules.base import Rule
from vibelint.rules.registry import register

_ARRAY_METHODS = frozenset({b"map", b"filter", b"forEach", b"flatMap", b"find", b"some", b"every"})


@register
class AsyncInArrayMethod(Rule):

    meta = RuleMeta(
        id="AI-LOGIC-001",
        name="Async function in array method",
        description=(
            "Passing an async callback to .map()/.filter()/.forEach() returns "
            "Promise[], not resolved values"
        ),
        severity=Severity.CRITICAL,
        multiplier="1.75x",
        source="CodeRabbit AI vs Human Code Report (Dec 2025) — 1.75x logic errors",
    )

    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        findings: list[Finding] = []

        for call_node in self.find_all(root, "call_expression"):
            func = call_node.child_by_field_name("function")
            if func is None or func.type != "member_expression":
                continue

            prop = func.child_by_field_name("property")
            if prop is None:
                continue

            method_name = source[prop.start_byte:prop.end_byte]
            if method_name not in _ARRAY_METHODS:
                continue

            args = call_node.child_by_field_name("arguments")
            if args is None:
                continue

            # Skip if already wrapped in Promise.all()
            if self._is_inside_promise_all(call_node, source):
                continue

            for arg in args.children:
                if arg.type in ("arrow_function", "function_expression"):
                    if self._is_async(arg, source):
                        findings.append(self._make_finding(
                            file_path,
                            arg,
                            source,
                            message=(
                                f"Async function in .{method_name.decode()}() "
                                f"returns Promise[], not resolved values"
                            ),
                            fix=(
                                f"Use `await Promise.all(arr.{method_name.decode()}(...))` "
                                f"or replace with a `for...of` loop"
                            ),
                        ))

        return findings

    @staticmethod
    def _is_inside_promise_all(call_node: Node, source: bytes) -> bool:
        """Check if this .map() call is an argument to Promise.all()."""
        node = call_node
        while node.parent is not None:
            parent = node.parent
            if parent.type == "call_expression":
                func = parent.child_by_field_name("function")
                if func is not None:
                    func_text = source[func.start_byte:func.end_byte]
                    if func_text == b"Promise.all":
                        return True
            node = parent
        return False

    @staticmethod
    def _is_async(node: Node, source: bytes) -> bool:
        """Check if a function node has the async keyword."""
        # tree-sitter marks async as a child node with type "async" before params
        # or it appears in the source text before the function parameters
        for child in node.children:
            if source[child.start_byte:child.end_byte] == b"async":
                return True
            # Stop looking once we hit parameters or body
            if child.type in ("formal_parameters", "identifier", "statement_block", "("):
                break
        return False
