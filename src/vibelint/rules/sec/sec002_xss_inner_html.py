"""
AI-SEC-002: XSS via dangerouslySetInnerHTML or direct innerHTML assignment

AI code is 2.74x more likely to introduce XSS vulnerabilities.
Generators routinely produce `dangerouslySetInnerHTML={{ __html: userInput }}`
without any sanitization.

Static string/template literals (e.g. CSS injection via <style>) are suppressed
because they contain no user-supplied data.

Fix: Use a sanitizer (DOMPurify) or render text content instead.
Source: CodeRabbit — 2.74x XSS multiplier
"""

from __future__ import annotations

import re
from pathlib import Path

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity
from vibelint.rules.base import Rule
from vibelint.rules.registry import register

_INNER_HTML_RE = re.compile(rb"""\.innerHTML\s*=""")

# Node types that represent user-controlled / dynamic values
_DYNAMIC_VALUE_TYPES = frozenset({
    "identifier",           # variable reference
    "member_expression",    # obj.prop
    "subscript_expression", # obj[key]
    "call_expression",      # someFunc(...)
    "binary_expression",    # a + b
    "conditional_expression",  # a ? b : c
    "await_expression",
})


@register
class XssDangerousHtml(Rule):

    meta = RuleMeta(
        id="AI-SEC-002",
        name="XSS via unsanitized HTML injection",
        description=(
            "dangerouslySetInnerHTML or direct innerHTML assignment without "
            "sanitization. AI code is 2.74x more likely to introduce XSS."
        ),
        severity=Severity.CRITICAL,
        multiplier="2.74x",
        source="CodeRabbit Report — 2.74x XSS vulnerability rate",
    )

    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        findings: list[Finding] = []

        # AST check: dangerouslySetInnerHTML in JSX
        for node in self.find_all(root, "jsx_attribute"):
            attr_name = None
            for child in node.children:
                if child.type == "property_identifier":
                    attr_name = self.node_text(child, source)
                    break
            if attr_name != "dangerouslySetInnerHTML":
                continue

            html_value = self._extract_html_value(node, source)

            if html_value is None:
                # Can't determine value — flag conservatively
                findings.append(self._make_finding(
                    file_path, node, source,
                    message="dangerouslySetInnerHTML used — XSS risk",
                    fix="Use DOMPurify.sanitize() or render as text content",
                ))
            elif self._is_static(html_value, source):
                # Static string/template with no substitutions — safe (e.g. CSS injection)
                pass
            else:
                value_text = self.node_text(html_value, source)[:50]
                findings.append(self._make_finding(
                    file_path, node, source,
                    message=f"dangerouslySetInnerHTML with dynamic value — XSS risk: {value_text}",
                    fix="Sanitize with DOMPurify.sanitize() before setting __html",
                ))

        # Regex fallback: .innerHTML = ... (covers non-JSX code)
        for line_idx, line in enumerate(source.split(b"\n")):
            if _INNER_HTML_RE.search(line):
                stripped = line.lstrip()
                if stripped.startswith(b"//") or stripped.startswith(b"*"):
                    continue
                findings.append(Finding(
                    rule_id=self.meta.id,
                    severity=self.meta.severity,
                    file=file_path,
                    line=line_idx + 1,
                    column=1,
                    message="Direct innerHTML assignment — XSS risk",
                    fix="Use textContent, DOMPurify.sanitize(), or a framework-safe API",
                    multiplier=self.meta.multiplier,
                    source=self.meta.source,
                    snippet=stripped.decode("utf-8", errors="replace"),
                ))

        return findings

    def _extract_html_value(self, attr_node: Node, source: bytes) -> Node | None:
        """
        Walk dangerouslySetInnerHTML={{ __html: <value> }} and return <value>.

        JSX attribute structure:
          jsx_attribute
            property_identifier  ("dangerouslySetInnerHTML")
            jsx_expression       ({ ... })
              object
                pair
                  property_identifier  ("__html")
                  <value>
        """
        for jsx_expr in attr_node.children:
            if jsx_expr.type != "jsx_expression":
                continue
            for obj in jsx_expr.children:
                if obj.type != "object":
                    continue
                for pair in obj.children:
                    if pair.type != "pair":
                        continue
                    key = pair.child_by_field_name("key")
                    value = pair.child_by_field_name("value")
                    if key is None or value is None:
                        continue
                    if self.node_text(key, source) == "__html":
                        return value
        return None

    @staticmethod
    def _is_static(value_node: Node, source: bytes) -> bool:
        """
        Return True if the value is a provably static string with no external references.

        Static:   "some fixed string"
                  `pure template with no ${substitutions}`
        Dynamic:  identifier, member_expression, call_expression,
                  `template ${with} substitutions`
        """
        if value_node.type == "string":
            return True
        if value_node.type == "template_string":
            # Static only if there are no template_substitution children
            for child in value_node.children:
                if child.type == "template_substitution":
                    return False
            return True
        return False
