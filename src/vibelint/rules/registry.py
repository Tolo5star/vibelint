"""Central registry of all VibeLint rules."""

from __future__ import annotations

from vibelint.rules.base import Rule

# Populated at import time by importing rule modules below.
_ALL_RULES: list[type[Rule]] = []


def register(cls: type[Rule]) -> type[Rule]:
    """Decorator to register a rule class."""
    _ALL_RULES.append(cls)
    return cls


def get_all_rules() -> list[Rule]:
    """Return instantiated copies of every registered rule."""
    # Trigger imports so @register decorators fire.
    _ensure_imported()
    return [cls() for cls in _ALL_RULES]


def get_rule_by_id(rule_id: str) -> Rule | None:
    _ensure_imported()
    for cls in _ALL_RULES:
        if cls.meta.id == rule_id:
            return cls()
    return None


def _ensure_imported() -> None:
    """Import all rule modules to trigger registration."""
    # fmt: off
    import vibelint.rules.logic.logic001_async_in_array_method  # noqa: F401
    import vibelint.rules.sec.sec001_hardcoded_secrets           # noqa: F401
    import vibelint.rules.sec.sec002_xss_inner_html              # noqa: F401
    import vibelint.rules.logic.logic002_catch_all_error         # noqa: F401
    import vibelint.rules.sec.sec004_cors_wildcard               # noqa: F401
    import vibelint.rules.qual.qual001_any_type                  # noqa: F401
    import vibelint.rules.qual.qual003_unused_imports            # noqa: F401
    import vibelint.rules.logic.logic004_missing_null_check      # noqa: F401
    # fmt: on
