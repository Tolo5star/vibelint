"""Configuration loading from .vibelint.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from vibelint.models import Severity


class RuleConfig(BaseModel):
    enabled: bool = True
    severity: Severity | None = None  # None = use rule default


class VibelintConfig(BaseModel):
    rules: dict[str, RuleConfig] = Field(default_factory=dict)
    ignore: list[str] = Field(default_factory=lambda: ["node_modules/**", "dist/**", ".git/**"])
    fail_on: Severity = Severity.WARNING

    def is_rule_enabled(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            return self.rules[rule_id].enabled
        return True

    def get_severity_override(self, rule_id: str) -> Severity | None:
        if rule_id in self.rules:
            return self.rules[rule_id].severity
        return None


def load_config(start_dir: Path | None = None) -> VibelintConfig:
    """Walk up from start_dir looking for .vibelint.yaml. Return defaults if not found."""
    if start_dir is None:
        start_dir = Path.cwd()

    search = start_dir.resolve()
    for directory in [search, *search.parents]:
        config_path = directory / ".vibelint.yaml"
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text()) or {}
            return _parse_raw(raw)

    return VibelintConfig()


def _parse_raw(raw: dict[str, Any]) -> VibelintConfig:
    rules = {}
    for rule_id, rule_cfg in raw.get("rules", {}).items():
        if isinstance(rule_cfg, dict):
            rules[rule_id] = RuleConfig(**rule_cfg)
    return VibelintConfig(
        rules=rules,
        ignore=raw.get("ignore", VibelintConfig.model_fields["ignore"].default_factory()),
        fail_on=Severity(raw.get("fail_on", "warning")),
    )
