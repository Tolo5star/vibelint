"""Rich terminal output formatter."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from vibelint import __version__
from vibelint.models import ScanResult, Severity


_SEVERITY_STYLE = {
    Severity.CRITICAL: ("bold red", "CRITICAL"),
    Severity.WARNING: ("bold yellow", "WARNING"),
    Severity.INFO: ("bold blue", "INFO"),
}


class TerminalFormatter:

    def __init__(self, console: Console | None = None, base_dir: Path | None = None) -> None:
        self.console = console or Console()
        self.base_dir = base_dir or Path.cwd()

    def format(self, result: ScanResult) -> int:
        """Print results to terminal. Returns exit code."""
        c = self.console

        c.print(f"\n[bold]vibelint[/bold] v{__version__} — AI Code Pattern Scanner\n")

        if not result.findings:
            c.print(f"[green]No AI-pattern issues found[/green] in {result.files_scanned} files.\n")
            return 0

        c.print(f"Files scanned: {result.files_scanned}")
        c.print(f"AI-pattern issues: {len(result.findings)}\n")

        # Group by severity
        for severity in (Severity.CRITICAL, Severity.WARNING, Severity.INFO):
            group = [f for f in result.findings if f.severity == severity]
            if not group:
                continue

            style, label = _SEVERITY_STYLE[severity]
            c.print(f"[{style}]{label} ({len(group)})[/{style}]")

            for finding in group:
                try:
                    rel = finding.file.relative_to(self.base_dir)
                except ValueError:
                    rel = finding.file
                loc = f"  {rel}:{finding.line}"

                c.print(f"  [{style}]{loc}[/{style}]")
                c.print(f"  {finding.rule_id}: {finding.message}")
                if finding.snippet:
                    c.print(f"  [dim]{finding.snippet}[/dim]")
                c.print(f"  [green]Fix:[/green] {finding.fix}")
                c.print(f"  [dim]AI generates this {finding.multiplier} more often than humans[/dim]")
                c.print()

        # Summary line
        parts = []
        if result.critical_count:
            parts.append(f"[bold red]{result.critical_count} critical[/bold red]")
        if result.warning_count:
            parts.append(f"[bold yellow]{result.warning_count} warning[/bold yellow]")
        if result.info_count:
            parts.append(f"[bold blue]{result.info_count} info[/bold blue]")
        c.print(" | ".join(parts))
        c.print()

        return 1 if result.findings else 0
