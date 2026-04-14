"""VibeLint CLI — `vibelint scan ./src`."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from vibelint import __version__
from vibelint.config import load_config
from vibelint.engine import Scanner
from vibelint.formatters.json_fmt import JsonFormatter
from vibelint.formatters.terminal import TerminalFormatter
from vibelint.models import Severity


@click.group()
@click.version_option(__version__, prog_name="vibelint")
def main() -> None:
    """VibeLint — AI code pattern scanner. Catch the bugs AI writes 2.74x more often."""


@main.command()
@click.argument("target", type=click.Path(exists=True), default=".")
@click.option("--format", "fmt", type=click.Choice(["terminal", "json"]), default="terminal")
@click.option("--fail-on", type=click.Choice(["critical", "warning", "info"]), default=None,
              help="Exit 1 if any finding at this severity or above (overrides config)")
@click.option("--config", "config_path", type=click.Path(), default=None,
              help="Path to .vibelint.yaml")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Expand all warnings (default: show collapsed summary table)")
def scan(target: str, fmt: str, fail_on: str | None, config_path: str | None, verbose: bool) -> None:
    """Scan files for AI-generated code patterns."""
    target_path = Path(target).resolve()
    config = load_config(Path(config_path).parent if config_path else target_path)

    if fail_on:
        config.fail_on = Severity(fail_on)

    scanner = Scanner(config)
    result = scanner.scan(target_path)

    base_dir = target_path if target_path.is_dir() else target_path.parent

    if fmt == "json":
        formatter = JsonFormatter(base_dir=base_dir)
    else:
        formatter = TerminalFormatter(base_dir=base_dir, verbose=verbose)

    formatter.format(result)

    # Exit code based on fail_on threshold
    should_fail = any(
        f.severity.value == config.fail_on.value or f.severity < config.fail_on
        for f in result.findings
    )
    if should_fail:
        sys.exit(1)


@main.command()
def rules() -> None:
    """List all available rules."""
    from vibelint.rules.registry import get_all_rules
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="VibeLint Rules", show_lines=True)
    table.add_column("ID", style="bold")
    table.add_column("Name")
    table.add_column("Severity")
    table.add_column("Multiplier", justify="right")

    for rule in sorted(get_all_rules(), key=lambda r: r.meta.id):
        sev = rule.meta.severity.value
        style = {"critical": "red", "warning": "yellow", "info": "blue"}[sev]
        table.add_row(
            rule.meta.id,
            rule.meta.name,
            f"[{style}]{sev}[/{style}]",
            rule.meta.multiplier,
        )

    console.print(table)
