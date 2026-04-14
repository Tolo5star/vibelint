"""Tree-sitter parser for TypeScript / TSX / JavaScript / JSX."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Language, Node, Parser
import tree_sitter_typescript
import tree_sitter_javascript


# Pre-build language objects once at import time.
_TS_LANG = Language(tree_sitter_typescript.language_typescript())
_TSX_LANG = Language(tree_sitter_typescript.language_tsx())
_JS_LANG = Language(tree_sitter_javascript.language())

_EXT_TO_LANG = {
    ".ts": _TS_LANG,
    ".tsx": _TSX_LANG,
    ".js": _JS_LANG,
    ".jsx": _TSX_LANG,  # JSX parsed with TSX grammar
    ".mjs": _JS_LANG,
    ".mts": _TS_LANG,
}

SUPPORTED_EXTENSIONS = frozenset(_EXT_TO_LANG.keys())


class TypeScriptParser:
    """Parse a TS/JS file into a tree-sitter tree."""

    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {}

    def _get_parser(self, ext: str) -> Parser:
        if ext not in self._parsers:
            lang = _EXT_TO_LANG[ext]
            self._parsers[ext] = Parser(lang)
        return self._parsers[ext]

    def supports(self, path: Path) -> bool:
        return path.suffix in _EXT_TO_LANG

    def parse_file(self, path: Path) -> tuple[Node, bytes]:
        """Parse a file and return (root_node, source_bytes)."""
        source = path.read_bytes()
        parser = self._get_parser(path.suffix)
        tree = parser.parse(source)
        return tree.root_node, source

    def parse_bytes(self, source: bytes, ext: str = ".ts") -> tuple[Node, bytes]:
        """Parse raw bytes — useful for testing."""
        parser = self._get_parser(ext)
        tree = parser.parse(source)
        return tree.root_node, source
