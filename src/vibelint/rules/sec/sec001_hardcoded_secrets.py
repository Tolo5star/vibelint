"""
AI-SEC-001: Hardcoded secrets disguised as placeholders

AI generators produce code like:
    const apiKey = "sk-placeholder-key-1234567890abcdef";
    const token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";

Developers copy-paste these, forget to replace them, and ship to production.
AI code is 1.88x more likely to contain improper credential handling.

Fix: Move to environment variables or a secrets manager.
Source: CodeRabbit (1.88x), CMU Security Benchmark (10.5% pass rate)
"""

from __future__ import annotations

import re
from pathlib import Path

from tree_sitter import Node

from vibelint.models import Finding, RuleMeta, Severity
from vibelint.rules.base import Rule
from vibelint.rules.registry import register

# Patterns that look like real or near-real secrets in string literals.
_SECRET_PATTERNS: list[tuple[re.Pattern, str]] = [
    # OpenAI / Anthropic style keys
    (re.compile(rb"""["']sk-[a-zA-Z0-9_-]{10,}["']"""), "OpenAI/Anthropic-style API key"),
    # GitHub personal access tokens
    (re.compile(rb"""["']ghp_[a-zA-Z0-9]{10,}["']"""), "GitHub personal access token"),
    (re.compile(rb"""["']gho_[a-zA-Z0-9]{10,}["']"""), "GitHub OAuth token"),
    (re.compile(rb"""["']github_pat_[a-zA-Z0-9_]{10,}["']"""), "GitHub fine-grained PAT"),
    # AWS keys
    (re.compile(rb"""["']AKIA[A-Z0-9]{12,}["']"""), "AWS access key ID"),
    # Stripe
    (re.compile(rb"""["']sk_live_[a-zA-Z0-9]{10,}["']"""), "Stripe live secret key"),
    (re.compile(rb"""["']pk_live_[a-zA-Z0-9]{10,}["']"""), "Stripe live publishable key"),
    # Generic high-entropy assignment patterns
    (re.compile(
        rb"""(?:api[_-]?key|secret|token|password|auth|credential)"""
        rb"""\s*[:=]\s*["'][a-zA-Z0-9+/=_-]{16,}["']""",
        re.IGNORECASE,
    ), "Hardcoded secret/credential"),
]

# Patterns that indicate a value is a genuine placeholder (not a real secret).
_ALLOWLIST = re.compile(
    rb"""your[-_]|xxx|placeholder|example|TODO|CHANGE[-_]?ME|"""
    rb"""insert[-_]|replace[-_]|dummy|fake|test[-_]?key|sample|"""
    rb"""process\.env|os\.environ""",
    re.IGNORECASE,
)


@register
class HardcodedSecrets(Rule):

    meta = RuleMeta(
        id="AI-SEC-001",
        name="Hardcoded secret disguised as placeholder",
        description=(
            "String literal matches a known secret pattern (API key, token, "
            "credential). AI generators produce these 1.88x more often."
        ),
        severity=Severity.CRITICAL,
        multiplier="1.88x",
        source="CodeRabbit Report — 1.88x improper password/credential handling",
    )

    def check(self, root: Node, source: bytes, file_path: Path) -> list[Finding]:
        findings: list[Finding] = []
        lines = source.split(b"\n")
        flagged_lines: set[int] = set()

        for line_idx, line in enumerate(lines):
            # Skip comments
            stripped = line.lstrip()
            if stripped.startswith(b"//") or stripped.startswith(b"*") or stripped.startswith(b"/*"):
                continue

            for pattern, secret_type in _SECRET_PATTERNS:
                if line_idx in flagged_lines:
                    break  # one finding per line across all patterns

                for match in pattern.finditer(line):
                    matched_text = match.group(0)

                    # Skip if it's an obvious placeholder
                    if _ALLOWLIST.search(matched_text):
                        continue

                    # Skip if the line references env vars
                    if _ALLOWLIST.search(line):
                        continue

                    flagged_lines.add(line_idx)
                    findings.append(Finding(
                        rule_id=self.meta.id,
                        severity=self.meta.severity,
                        file=file_path,
                        line=line_idx + 1,
                        column=match.start() + 1,
                        message=f"{secret_type}: {matched_text[:40].decode(errors='replace')}...",
                        fix="Move to environment variable or secrets manager",
                        multiplier=self.meta.multiplier,
                        source=self.meta.source,
                        snippet=line.decode("utf-8", errors="replace").strip(),
                    ))
                    break  # one finding per pattern per line

        return findings
