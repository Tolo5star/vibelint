"""Data models for VibeLint findings and scan results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

    def __lt__(self, other: Severity) -> bool:
        order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
        return order[self] < order[other]


@dataclass(frozen=True)
class RuleMeta:
    """Static metadata for a rule — research citation, multiplier, etc."""

    id: str
    name: str
    description: str
    severity: Severity
    multiplier: str  # e.g. "2.74x"
    source: str  # research citation
    languages: tuple[str, ...] = ("typescript",)


@dataclass
class Finding:
    """A single issue found in a file."""

    rule_id: str
    severity: Severity
    file: Path
    line: int
    column: int
    message: str
    fix: str
    multiplier: str
    source: str
    end_line: int | None = None
    snippet: str = ""


@dataclass
class ScanResult:
    """Aggregated results of a full scan."""

    files_scanned: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.INFO)

    def sort(self) -> None:
        self.findings.sort(key=lambda f: (f.severity, f.file, f.line))
