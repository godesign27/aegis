"""UI Code Parser — extract tokens, components, and ARIA from TSX/JSX/CSS source.

This module normalizes raw UI code into structured data that the audit agent
can reason about. It is intentionally kept dependency-free (regex + stdlib only)
so it can run synchronously without any I/O.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ParsedFile:
    """All extracted design-relevant entities from a single source file."""
    filepath: str

    # Token values
    hex_colors: list[str] = field(default_factory=list)
    rgb_colors: list[str] = field(default_factory=list)
    hsl_colors: list[str] = field(default_factory=list)
    named_colors: list[str] = field(default_factory=list)
    tailwind_arbitrary_colors: list[str] = field(default_factory=list)

    inline_spacing: list[str] = field(default_factory=list)
    tailwind_arbitrary_spacing: list[str] = field(default_factory=list)

    inline_typography: list[str] = field(default_factory=list)
    tailwind_arbitrary_typography: list[str] = field(default_factory=list)

    # Components and imports
    import_statements: list[str] = field(default_factory=list)
    component_names: list[str] = field(default_factory=list)

    # Accessibility
    aria_attributes: list[str] = field(default_factory=list)
    semantic_elements: list[str] = field(default_factory=list)
    click_handlers: list[str] = field(default_factory=list)
    keyboard_handlers: list[str] = field(default_factory=list)
    img_tags: list[str] = field(default_factory=list)

    # Raw lines for line-number lookup
    lines: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Colors
_HEX_RE = re.compile(r'#[0-9a-fA-F]{3,8}\b')
_RGB_RE = re.compile(r'rgba?\s*\([^)]+\)')
_HSL_RE = re.compile(r'hsla?\s*\([^)]+\)')
_CSS_NAMED_COLORS = {
    "red", "blue", "green", "yellow", "orange", "purple", "pink",
    "gray", "grey", "black", "white", "navy", "teal", "cyan", "magenta",
    "lime", "maroon", "olive", "silver", "aqua", "fuchsia",
}
_NAMED_COLOR_STYLE_RE = re.compile(
    r'(?:color|background|background-color)\s*:\s*([a-zA-Z]+)'
)
_TW_ARBITRARY_COLOR_RE = re.compile(
    r'(?:text|bg|border|ring|fill|stroke)-\[#[0-9a-fA-F]{3,8}\]'
)

# Spacing — handles both CSS (margin: 12px) and JSX camelCase (marginTop: "12px")
_INLINE_SPACING_RE = re.compile(
    r'(?:margin(?:Top|Bottom|Left|Right)?|padding(?:Top|Bottom|Left|Right)?'
    r'|gap|top|right|bottom|left)\s*:\s*[\'"]?[\d.]+'
    r'(?:px|rem|em|vh|vw)[\'"]?'
)
_TW_ARBITRARY_SPACING_RE = re.compile(
    r'(?:p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|space-x|space-y|'
    r'top|right|bottom|left|inset)-\[\d[^\]]*\]'
)

# Typography
_INLINE_TYPOGRAPHY_RE = re.compile(
    r'(?:fontSize|font-size|fontWeight|font-weight|fontFamily|font-family)'
    r'\s*[=:]\s*[\'"\{]?[\w\s,.\'"]+[\'"\}]?'
)
_TW_ARBITRARY_TYPOGRAPHY_RE = re.compile(
    r'(?:text|font)-\[(?:\d+px|[\d.]+rem|\d+)[^\]]*\]'
)

# Imports
_IMPORT_RE = re.compile(r"^import\s+.+\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)

# Components (JSX usage: <ComponentName or <ComponentName.Sub)
_COMPONENT_RE = re.compile(r'<([A-Z][a-zA-Z0-9.]*)')

# Accessibility
_ARIA_RE = re.compile(r'aria-[a-z-]+(?:=(?:"[^"]*"|\'[^\']*\'|\{[^}]*\}))?')
_SEMANTIC_RE = re.compile(
    r'<(main|nav|header|footer|aside|section|article|button|a\s|form|'
    r'label|h[1-6]|ul|ol|li|table|th|td|caption|figure|figcaption)'
)
_CLICK_HANDLER_RE = re.compile(r'onClick\s*=')
_KEY_HANDLER_RE = re.compile(r'on(?:KeyDown|KeyUp|KeyPress)\s*=')
_IMG_RE = re.compile(r'<img\b[^>]*>')


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_file(filepath: str, content: str) -> ParsedFile:
    """Parse a single file's content and return a ParsedFile."""
    result = ParsedFile(filepath=filepath)
    result.lines = content.splitlines()

    # --- Colors ---
    result.hex_colors = _HEX_RE.findall(content)
    result.rgb_colors = _RGB_RE.findall(content)
    result.hsl_colors = _HSL_RE.findall(content)
    result.tailwind_arbitrary_colors = _TW_ARBITRARY_COLOR_RE.findall(content)

    for match in _NAMED_COLOR_STYLE_RE.finditer(content):
        color_name = match.group(1).lower()
        if color_name in _CSS_NAMED_COLORS:
            result.named_colors.append(match.group(0))

    # --- Spacing ---
    result.inline_spacing = _INLINE_SPACING_RE.findall(content)
    result.tailwind_arbitrary_spacing = _TW_ARBITRARY_SPACING_RE.findall(content)

    # --- Typography ---
    result.inline_typography = _INLINE_TYPOGRAPHY_RE.findall(content)
    result.tailwind_arbitrary_typography = _TW_ARBITRARY_TYPOGRAPHY_RE.findall(content)

    # --- Imports ---
    result.import_statements = _IMPORT_RE.findall(content)

    # --- Components ---
    result.component_names = list(set(_COMPONENT_RE.findall(content)))

    # --- Accessibility ---
    result.aria_attributes = _ARIA_RE.findall(content)
    result.semantic_elements = _SEMANTIC_RE.findall(content)
    result.click_handlers = _CLICK_HANDLER_RE.findall(content)
    result.keyboard_handlers = _KEY_HANDLER_RE.findall(content)
    result.img_tags = _IMG_RE.findall(content)

    return result


def parse_files(code: dict[str, str]) -> list[ParsedFile]:
    """Parse a collection of files and return a list of ParsedFile objects."""
    return [parse_file(filepath, content) for filepath, content in code.items()]


def find_line_number(lines: list[str], snippet: str) -> int | None:
    """Return the 1-based line number of the first occurrence of snippet."""
    for i, line in enumerate(lines, start=1):
        if snippet in line:
            return i
    return None
