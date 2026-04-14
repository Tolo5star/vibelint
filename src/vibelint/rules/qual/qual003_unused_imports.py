"""
AI-QUAL-003: Unused imports from incomplete AI refactors

AI generators add imports for code they plan to write, then change approach
mid-generation — leaving dead imports. Also common when AI partially refactors
a file and forgets to clean up removed references.

Fix: Remove the unused import.
Source: CodeRabbit — 1.64x maintainability issues in AI code
"""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity
from vibelint.rules.base import Rule
from vibelint.rules.registry import register


@register
class UnusedImports(Rule):

    meta = RuleMeta(
        id="AI-QUAL-003",
        name="Unused import from incomplete refactor",
        description=(
            "Imported name is never referenced in the file body. Common when "
            "AI generators change approach mid-generation."
        ),
        severity=Severity.WARNING,
        multiplier="1.64x",
        source="CodeRabbit Report — 1.64x maintainability issues in AI code",
    )

    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        findings: list[Finding] = []

        # Collect all import specifier names
        imports: list[tuple[str, Node]] = []
        for node in self.find_all(root, "import_specifier"):
            # `import { Foo as Bar }` — the local name is the alias if present
            alias = node.child_by_field_name("alias")
            name_node = alias if alias else node.child_by_field_name("name")
            if name_node:
                imports.append((self.node_text(name_node, source), node))

        # Also catch default imports: `import Foo from '...'`
        for node in self.find_all(root, "import_clause"):
            for child in node.children:
                if child.type == "identifier":
                    imports.append((self.node_text(child, source), child))

        if not imports:
            return findings

        # Get the source text excluding import statements for reference checking
        body_source = self._get_body_source(root, source)

        for name, node in imports:
            # Skip type-only imports — TypeScript strips these at compile time
            # and they're commonly used for type annotations only
            parent = node.parent
            if parent and parent.type == "import_statement":
                stmt_text = self.node_text(parent, source)
                if stmt_text.startswith("import type"):
                    continue

            # Check if the name appears anywhere outside import statements
            # Use word boundary check to avoid substring false positives
            if not self._is_name_used(name, body_source):
                findings.append(self._make_finding(
                    file_path, node, source,
                    message=f"'{name}' is imported but never used",
                    fix=f"Remove the unused import of '{name}'",
                ))

        return findings

    @staticmethod
    def _get_body_source(root: Node, source: bytes) -> bytes:
        """Get source text excluding import/export statements at the top."""
        parts = []
        for child in root.children:
            if child.type not in ("import_statement", "export_statement"):
                parts.append(source[child.start_byte:child.end_byte])
        return b" ".join(parts)

    @staticmethod
    def _is_name_used(name: str, body: bytes) -> bool:
        """Check if an identifier appears in the body (word-boundary aware)."""
        import re
        pattern = re.compile(rb"\b" + re.escape(name.encode()) + rb"\b")
        return bool(pattern.search(body))
