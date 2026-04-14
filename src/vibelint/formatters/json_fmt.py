"""JSON output formatter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from vibelint import __version__
from vibelint.models import ScanResult


class JsonFormatter:

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path.cwd()

    def format(self, result: ScanResult) -> int:
        """Write JSON to stdout. Returns exit code."""
        output = {
            "version": __version__,
            "files_scanned": result.files_scanned,
            "total_issues": len(result.findings),
            "summary": {
                "critical": result.critical_count,
                "warning": result.warning_count,
                "info": result.info_count,
            },
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "severity": f.severity.value,
                    "file": str(self._rel(f.file)),
                    "line": f.line,
                    "column": f.column,
                    "message": f.message,
                    "fix": f.fix,
                    "multiplier": f.multiplier,
                    "source": f.source,
                }
                for f in result.findings
            ],
        }
        json.dump(output, sys.stdout, indent=2)
        print()  # trailing newline
        return 1 if result.findings else 0

    def _rel(self, path: Path) -> Path:
        try:
            return path.relative_to(self.base_dir)
        except ValueError:
            return path
