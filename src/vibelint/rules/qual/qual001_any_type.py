"""
AI-QUAL-001: `any` type used when a specific type is inferrable

AI generators default to `: any` when they can't determine the type,
producing code like `const data: any = await fetch(...)`. This defeats
TypeScript's type system and hides bugs.

Fix: Replace with the actual type, `unknown`, or a generic.
Source: Common AI anti-pattern, 1.64x maintainability issues (CodeRabbit)
"""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity
from vibelint.rules.base import Rule
from vibelint.rules.registry import register


@register
class AnyTypeOveruse(Rule):

    meta = RuleMeta(
        id="AI-QUAL-001",
        name="`any` type when specific type is inferrable",
        description=(
            "Using `: any` defeats TypeScript's type system. AI generators "
            "default to `any` when unsure of the type."
        ),
        severity=Severity.WARNING,
        multiplier="1.64x",
        source="CodeRabbit Report — 1.64x maintainability issues in AI code",
        languages=("typescript",),
    )

    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        # Only applies to TypeScript files
        if file_path.suffix not in (".ts", ".tsx", ".mts"):
            return []

        findings: list[Finding] = []

        for node in self.find_all(root, "type_annotation"):
            for child in node.children:
                if child.type == "predefined_type":
                    if source[child.start_byte:child.end_byte] == b"any":
                        findings.append(self._make_finding(
                            file_path, child, source,
                            message="`any` type used — specific type is likely inferrable",
                            fix="Replace with the actual type, `unknown`, or a generic parameter",
                        ))

        # Also catch `as any` type assertions
        for node in self.find_all(root, "as_expression"):
            for child in node.children:
                if child.type == "predefined_type":
                    if source[child.start_byte:child.end_byte] == b"any":
                        findings.append(self._make_finding(
                            file_path, child, source,
                            message="`as any` type assertion — bypasses type safety",
                            fix="Use a proper type assertion or fix the underlying type mismatch",
                        ))

        return findings
