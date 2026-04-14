"""
AI-LOGIC-004: Missing null/undefined checks on optional chain results

AI generators produce code like:
    const user = users.find(u => u.id === id);
    console.log(user.name);  // user might be undefined!

Or access deeply nested properties without optional chaining:
    const value = response.data.results[0].name;

Fix: Add optional chaining (?.) or an explicit null check.
Source: Empirical study of AI code, 1.75x logic error multiplier
"""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity
from vibelint.rules.base import Rule
from vibelint.rules.registry import register

# Methods that return T | undefined (the value might not exist)
_NULLABLE_METHODS = frozenset({b"find", b"at", b"get", b"shift", b"pop"})


@register
class MissingNullCheck(Rule):

    meta = RuleMeta(
        id="AI-LOGIC-004",
        name="Missing null check after nullable operation",
        description=(
            "Result of .find()/.at()/.get() used without null check. "
            "These methods return undefined when no match is found."
        ),
        severity=Severity.WARNING,
        multiplier="1.75x",
        source="Empirical study of AI-generated code — 1.75x logic errors",
    )

    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        findings: list[Finding] = []

        # Pattern: const x = arr.find(...); then x.prop (no ?. or if-check)
        # We look for variable declarations where the value is a nullable method call,
        # then check if the variable is later accessed without optional chaining.

        for decl in self.find_all(root, "variable_declarator"):
            name_node = decl.child_by_field_name("name")
            value_node = decl.child_by_field_name("value")

            if name_node is None or value_node is None:
                continue
            if name_node.type != "identifier":
                continue

            # Check if value is a call to a nullable method
            if not self._is_nullable_call(value_node, source):
                continue

            var_name = source[name_node.start_byte:name_node.end_byte]

            # Search subsequent siblings for unsafe property access on this var
            parent = decl.parent  # lexical_declaration or variable_declaration
            if parent is None:
                continue
            container = parent.parent
            if container is None:
                continue

            found_parent = False
            for sibling in container.children:
                if sibling == parent:
                    found_parent = True
                    continue
                if not found_parent:
                    continue

                # Look for var_name.prop (without ?.) in subsequent code
                for access in self.find_all(sibling, "member_expression"):
                    obj = access.child_by_field_name("object")
                    if obj is None:
                        continue
                    if source[obj.start_byte:obj.end_byte] != var_name:
                        continue

                    # Check it's not optional chaining (node type would be
                    # "optional_chain_expression" or contain "?.")
                    access_text = source[access.start_byte:access.end_byte]
                    if b"?." not in access_text:
                        findings.append(self._make_finding(
                            file_path, access, source,
                            message=(
                                f"'{var_name.decode()}' may be undefined "
                                f"(returned by a nullable method) — accessed without null check"
                            ),
                            fix=f"Use optional chaining: `{var_name.decode()}?.prop` or add an explicit null check",
                        ))
                        break  # one finding per variable

        return findings

    @staticmethod
    def _is_nullable_call(node: Node, source: bytes) -> bool:
        """Check if a node is a call to a known nullable method."""
        if node.type != "call_expression":
            return False
        func = node.child_by_field_name("function")
        if func is None or func.type != "member_expression":
            return False
        prop = func.child_by_field_name("property")
        if prop is None:
            return False
        return source[prop.start_byte:prop.end_byte] in _NULLABLE_METHODS
