"""Core scanning engine — orchestrates parsing + rules."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from vibelint.config import VibelintConfig, load_config
from vibelint.models import Finding, ScanResult
from vibelint.parsers.typescript import SUPPORTED_EXTENSIONS, TypeScriptParser
from vibelint.rules.registry import get_all_rules


class Scanner:
    """Scans a directory tree, parses files, runs rules, returns results."""

    def __init__(self, config: VibelintConfig | None = None) -> None:
        self.config = config or load_config()
        self.parser = TypeScriptParser()

    def scan(self, target: Path) -> ScanResult:
        """Scan a file or directory and return aggregated findings."""
        result = ScanResult()
        rules = [r for r in get_all_rules() if self.config.is_rule_enabled(r.meta.id)]

        if target.is_file():
            files = [target] if self.parser.supports(target) else []
        else:
            files = self._discover_files(target)

        for file_path in files:
            result.files_scanned += 1
            try:
                root, source = self.parser.parse_file(file_path)
            except Exception:
                continue  # skip unparseable files

            for rule in rules:
                findings = rule.check(root, source, file_path)
                # Apply severity overrides from config
                override = self.config.get_severity_override(rule.meta.id)
                if override is not None:
                    for f in findings:
                        f.severity = override
                result.findings.extend(findings)

        result.sort()
        return result

    def _discover_files(self, directory: Path) -> list[Path]:
        """Recursively find all supported files, respecting ignore globs."""
        files = []
        for ext in SUPPORTED_EXTENSIONS:
            for path in directory.rglob(f"*{ext}"):
                rel = str(path.relative_to(directory))
                if not any(fnmatch.fnmatch(rel, pat) for pat in self.config.ignore):
                    files.append(path)
        return sorted(files)
