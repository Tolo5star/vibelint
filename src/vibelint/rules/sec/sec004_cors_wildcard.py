"""
AI-SEC-004: Over-permissive CORS defaults (wildcard origin)

AI generators routinely produce `cors({ origin: '*' })` or
`Access-Control-Allow-Origin: *` as a "works everywhere" default.
53% of AI-generated code ships with vulnerabilities.

Fix: Restrict to specific origins or use a dynamic allowlist.
Source: AI Vyuh Report — 53% ship vulnerable
"""

from __future__ import annotations

import re
from pathlib import Path

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity
from vibelint.rules.base import Rule
from vibelint.rules.registry import register

_CORS_STAR_PATTERNS = [
    re.compile(rb"""origin\s*:\s*["']\*["']"""),
    re.compile(rb"""Access-Control-Allow-Origin["']?\s*[:=,]\s*["']\*["']""", re.IGNORECASE),
    re.compile(rb"""['"]\*['"]\s*"""),  # catch as arg in cors('*')
]


@register
class CorsWildcard(Rule):

    meta = RuleMeta(
        id="AI-SEC-004",
        name="Over-permissive CORS wildcard origin",
        description=(
            "CORS configured with origin: '*' allows any website to make "
            "credentialed requests to your API."
        ),
        severity=Severity.WARNING,
        multiplier="1.57x",
        source="AI Vyuh Report — 53% of AI-generated code ships with vulnerabilities",
    )

    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        findings: list[Finding] = []

        for node in self.find_all(root, "call_expression"):
            func = node.child_by_field_name("function")
            if func is None:
                continue
            func_text = self.node_text(func, source)
            if "cors" not in func_text.lower():
                continue

            call_source = source[node.start_byte:node.end_byte]
            for pattern in _CORS_STAR_PATTERNS:
                if pattern.search(call_source):
                    findings.append(self._make_finding(
                        file_path, node, source,
                        message="CORS configured with wildcard origin '*'",
                        fix="Restrict origin to specific domains or use a dynamic allowlist",
                    ))
                    break

        # Also catch header-based CORS in string literals / template literals
        for line_idx, line in enumerate(source.split(b"\n")):
            if b"Access-Control-Allow-Origin" in line and b"*" in line:
                stripped = line.lstrip()
                if stripped.startswith(b"//") or stripped.startswith(b"*"):
                    continue
                findings.append(Finding(
                    rule_id=self.meta.id,
                    severity=self.meta.severity,
                    file=file_path,
                    line=line_idx + 1,
                    column=1,
                    message="Access-Control-Allow-Origin set to wildcard '*'",
                    fix="Restrict to specific origins or use a dynamic allowlist",
                    multiplier=self.meta.multiplier,
                    source=self.meta.source,
                    snippet=stripped.decode("utf-8", errors="replace"),
                ))

        return findings
