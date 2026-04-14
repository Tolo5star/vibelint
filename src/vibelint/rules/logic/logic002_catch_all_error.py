"""
AI-LOGIC-002: Catch-all error handling that swallows errors silently

AI generators love to wrap code in try/catch and either:
  - Leave the catch block empty
  - Only console.log the error (no re-throw, no meaningful handling)

This hides bugs in production. 60%+ of AI-generated faults are semantic errors.

Fix: Re-throw, handle specifically, or at minimum log and propagate.
Source: Survey of Bugs in AI-Generated Code (Dec 2025) — 60% semantic errors
"""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity
from vibelint.rules.base import Rule
from vibelint.rules.registry import register


@register
class CatchAllError(Rule):

    meta = RuleMeta(
        id="AI-LOGIC-002",
        name="Catch-all error handling swallows errors",
        description=(
            "Empty catch block or catch that only logs without re-throwing. "
            "Silently hides bugs in production."
        ),
        severity=Severity.CRITICAL,
        multiplier="1.75x",
        source="Survey of Bugs in AI-Generated Code (Dec 2025) — 60% semantic errors",
    )

    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        findings: list[Finding] = []

        for catch_node in self.find_all(root, "catch_clause"):
            body = catch_node.child_by_field_name("body")
            if body is None:
                continue

            if self._is_empty_body(body):
                findings.append(self._make_finding(
                    file_path, catch_node, source,
                    message="Empty catch block — errors are silently swallowed",
                    fix="Handle the error, re-throw it, or add a comment explaining why it's safe to ignore",
                ))
            elif self._is_log_only(body, source):
                findings.append(self._make_finding(
                    file_path, catch_node, source,
                    message="Catch block only logs — error is not re-thrown or handled",
                    fix="Re-throw after logging, or handle the error condition explicitly",
                ))

        return findings

    @staticmethod
    def _is_empty_body(body: Node) -> bool:
        """Check if a statement_block has no meaningful statements (ignoring comments)."""
        for child in body.children:
            if child.type not in ("{", "}", "comment"):
                return False
        return True

    @staticmethod
    def _is_log_only(body: Node, source: bytes) -> bool:
        """Check if the catch body only contains console.log/warn/error."""
        statements = [c for c in body.children if c.type not in ("{", "}", "comment")]
        if len(statements) != 1:
            return False

        stmt = statements[0]
        text = source[stmt.start_byte:stmt.end_byte]
        return bool(
            text.startswith(b"console.log")
            or text.startswith(b"console.warn")
            or text.startswith(b"console.error")
        )
