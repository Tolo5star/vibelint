"""Rich terminal output formatter.

Layout:
  1. Header — version + scan stats
  2. Critical section — full detail, grouped by file
  3. Warning/Info section — collapsed summary table by default
     (use --verbose to expand to full detail)
  4. Final score line
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.rule import Rule as RichRule
from rich.table import Table
from rich.text import Text

from vibelint import __version__
from vibelint.models import Finding, ScanResult, Severity

_SEV_COLOR = {
    Severity.CRITICAL: "bold red",
    Severity.WARNING:  "bold yellow",
    Severity.INFO:     "bold blue",
}
_SEV_ICON = {
    Severity.CRITICAL: "✗",
    Severity.WARNING:  "⚠",
    Severity.INFO:     "ℹ",
}


class TerminalFormatter:

    def __init__(
        self,
        console: Console | None = None,
        base_dir: Path | None = None,
        verbose: bool = False,
    ) -> None:
        self.console = console or Console()
        self.base_dir = base_dir or Path.cwd()
        self.verbose = verbose

    def format(self, result: ScanResult) -> int:
        c = self.console

        # ── Header ───────────────────────────────────────────────────────
        c.print()
        c.print(f"[bold]vibelint[/bold] [dim]v{__version__}[/dim] — AI Code Pattern Scanner")
        c.print(
            f"[dim]{result.files_scanned} files scanned · "
            f"[bold red]{result.critical_count} critical[/bold red] · "
            f"[bold yellow]{result.warning_count} warning[/bold yellow] · "
            f"[bold blue]{result.info_count} info[/bold blue][/dim]"
        )
        c.print()

        if not result.findings:
            c.print("[bold green]✓ No AI-pattern issues found.[/bold green]\n")
            return 0

        criticals = [f for f in result.findings if f.severity == Severity.CRITICAL]
        warnings   = [f for f in result.findings if f.severity == Severity.WARNING]
        infos      = [f for f in result.findings if f.severity == Severity.INFO]

        # ── Critical — always shown in full, grouped by file ─────────────
        if criticals:
            c.print(RichRule(
                f"[bold red]CRITICAL  {len(criticals)} {'issue' if len(criticals) == 1 else 'issues'}[/bold red]",
                style="red",
            ))
            c.print()
            self._print_findings_grouped(criticals, Severity.CRITICAL)

        # ── Warnings — collapsed summary unless --verbose ─────────────────
        if warnings:
            if self.verbose:
                c.print(RichRule(
                    f"[bold yellow]WARNING  {len(warnings)} issues[/bold yellow]",
                    style="yellow",
                ))
                c.print()
                self._print_findings_grouped(warnings, Severity.WARNING)
            else:
                self._print_warning_summary(warnings)

        # ── Info — collapsed summary unless --verbose ─────────────────────
        if infos:
            if self.verbose:
                c.print(RichRule(
                    f"[bold blue]INFO  {len(infos)} issues[/bold blue]",
                    style="blue",
                ))
                c.print()
                self._print_findings_grouped(infos, Severity.INFO)
            else:
                self._print_info_summary(infos)

        # ── Footer ────────────────────────────────────────────────────────
        c.print(RichRule(style="dim"))
        parts: list[str] = []
        if result.critical_count:
            parts.append(f"[bold red]{result.critical_count} critical[/bold red]")
        if result.warning_count:
            parts.append(f"[bold yellow]{result.warning_count} warning[/bold yellow]")
        if result.info_count:
            parts.append(f"[bold blue]{result.info_count} info[/bold blue]")
        c.print("  " + " · ".join(parts) + f"  [dim]in {result.files_scanned} files[/dim]")
        if not self.verbose and (warnings or infos):
            c.print(
                "  [dim]Run with [bold]--verbose[/bold] to expand all warnings[/dim]"
            )
        c.print()

        return 1 if result.findings else 0

    # ── Detailed view (critical always, warnings in --verbose) ────────────

    def _print_findings_grouped(
        self,
        findings: list[Finding],
        severity: Severity,
    ) -> None:
        c = self.console
        color = _SEV_COLOR[severity]

        by_file: dict[Path, list[Finding]] = defaultdict(list)
        for f in findings:
            by_file[f.file].append(f)

        for file_path, file_findings in sorted(by_file.items(), key=lambda x: str(x[0])):
            rel = self._rel(file_path)
            c.print(f"  [bold]{rel}[/bold]  [dim]{len(file_findings)} {'issue' if len(file_findings) == 1 else 'issues'}[/dim]")

            for i, finding in enumerate(sorted(file_findings, key=lambda f: f.line)):
                is_last = i == len(file_findings) - 1
                prefix = "  └─" if is_last else "  ├─"
                end_prefix = "     " if is_last else "  │  "

                c.print(
                    f"{prefix} [dim]line {finding.line}[/dim]  "
                    f"[{color}]{finding.rule_id}[/{color}]  "
                    f"{finding.message}"
                )
                if finding.snippet:
                    snippet = finding.snippet.strip()
                    c.print(f"{end_prefix}  [dim on black] {snippet} [/dim on black]")
                c.print(f"{end_prefix}  [green]→[/green] {finding.fix}")
                c.print(
                    f"{end_prefix}  [dim]AI generates this "
                    f"[bold]{finding.multiplier}[/bold] more often — {finding.source}[/dim]"
                )
                if not is_last:
                    c.print(f"  │")

            c.print()

    # ── Collapsed summary for warnings/info ───────────────────────────────

    def _print_warning_summary(self, warnings: list[Finding]) -> None:
        c = self.console
        c.print(RichRule(
            f"[bold yellow]WARNING  {len(warnings)} issues[/bold yellow]",
            style="yellow",
        ))
        c.print()
        self._print_collapsed_table(warnings, "yellow")

    def _print_info_summary(self, infos: list[Finding]) -> None:
        c = self.console
        c.print(RichRule(
            f"[bold blue]INFO  {len(infos)} issues[/bold blue]",
            style="blue",
        ))
        c.print()
        self._print_collapsed_table(infos, "blue")

    def _print_collapsed_table(self, findings: list[Finding], color: str) -> None:
        c = self.console

        # Group by rule_id
        by_rule: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            by_rule[f.rule_id].append(f)

        table = Table(box=None, padding=(0, 2), show_header=True, header_style="dim")
        table.add_column("Rule", style=f"bold {color}", no_wrap=True)
        table.add_column("What it flags")
        table.add_column("Issues", justify="right", style="bold")
        table.add_column("Files", justify="right", style="dim")
        table.add_column("Worst file", style="dim")

        for rule_id, rule_findings in sorted(by_rule.items(), key=lambda x: -len(x[1])):
            files_affected = len({f.file for f in rule_findings})
            # find the file with the most findings
            by_file: dict[Path, int] = defaultdict(int)
            for f in rule_findings:
                by_file[f.file] += 1
            worst_file = max(by_file, key=lambda p: by_file[p])
            worst_count = by_file[worst_file]

            # Pull the message template from the first finding (strip the variable part)
            sample_msg = rule_findings[0].message
            if len(sample_msg) > 52:
                sample_msg = sample_msg[:49] + "..."

            table.add_row(
                rule_id,
                sample_msg,
                str(len(rule_findings)),
                str(files_affected),
                f"{self._rel(worst_file)} ({worst_count})",
            )

        c.print(table)
        c.print()

    def _rel(self, path: Path) -> Path | str:
        try:
            return path.relative_to(self.base_dir)
        except ValueError:
            return path
