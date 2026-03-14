"""Tests for aegis.parser — UI code normalizer.

Tests validate that the parser correctly extracts:
- Hex colors (including Tailwind arbitrary class form)
- Inline spacing violations
- Inline typography violations
- Import statements
- JSX component names
- ARIA attributes
- Semantic elements
- Click vs keyboard handler counts
- img tags
"""
from pathlib import Path

import pytest

from aegis.parser import parse_file, parse_files, find_line_number

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Bolt sample
# ---------------------------------------------------------------------------


class TestBoltSampleParsing:
    def setup_method(self):
        self.content = (FIXTURES / "bolt_sample.tsx").read_text()
        self.parsed = parse_file("bolt_sample.tsx", self.content)

    def test_detects_tailwind_arbitrary_colors(self):
        """Should detect bg-[#6366f1] and text-[#f8fafc]."""
        assert len(self.parsed.tailwind_arbitrary_colors) >= 2
        colors_str = " ".join(self.parsed.tailwind_arbitrary_colors)
        assert "#6366f1" in colors_str
        assert "#f8fafc" in colors_str

    def test_detects_lucide_react_import(self):
        """Should extract lucide-react as an import source."""
        assert "lucide-react" in self.parsed.import_statements

    def test_detects_inline_spacing(self):
        """Should detect the marginTop: 12px inline style."""
        assert len(self.parsed.inline_spacing) >= 1
        spacing_str = " ".join(self.parsed.inline_spacing)
        assert "12" in spacing_str or "3px" in spacing_str or "marginTop" in spacing_str.lower() or "margin" in spacing_str.lower()

    def test_detects_click_handlers(self):
        """Should detect at least one onClick handler."""
        assert len(self.parsed.click_handlers) >= 1

    def test_no_keyboard_handlers(self):
        """Bolt sample has no keyboard handlers — this is a violation."""
        assert len(self.parsed.keyboard_handlers) == 0

    def test_detects_nav_semantic_element(self):
        """Should detect the <nav> element."""
        elements_str = " ".join(self.parsed.semantic_elements)
        assert "nav" in elements_str


# ---------------------------------------------------------------------------
# Lovable sample
# ---------------------------------------------------------------------------


class TestLovableSampleParsing:
    def setup_method(self):
        self.content = (FIXTURES / "lovable_sample.tsx").read_text()
        self.parsed = parse_file("lovable_sample.tsx", self.content)

    def test_detects_four_arbitrary_colors(self):
        """Should detect at least 3 Tailwind arbitrary colors (bg, text, border)."""
        assert len(self.parsed.tailwind_arbitrary_colors) >= 3

    def test_detects_shadcn_import(self):
        """Should detect the @/components/ui import path."""
        imports_str = " ".join(self.parsed.import_statements)
        assert "@/components/ui" in imports_str

    def test_detects_arbitrary_typography(self):
        """Should detect text-[14px] arbitrary typography class."""
        assert len(self.parsed.tailwind_arbitrary_typography) >= 1
        typo_str = " ".join(self.parsed.tailwind_arbitrary_typography)
        assert "14px" in typo_str

    def test_detects_button_element(self):
        """Should detect <button> element."""
        elements_str = " ".join(self.parsed.semantic_elements)
        assert "button" in elements_str


# ---------------------------------------------------------------------------
# Figma Make sample
# ---------------------------------------------------------------------------


class TestFigmaMakeSampleParsing:
    def setup_method(self):
        self.content = (FIXTURES / "figma_make_sample.tsx").read_text()
        self.parsed = parse_file("figma_make_sample.tsx", self.content)

    def test_detects_hex_colors(self):
        """Should detect #1A1A2E and #4ECCA3 as hardcoded hex colors."""
        assert len(self.parsed.hex_colors) >= 2
        hex_str = " ".join(self.parsed.hex_colors)
        assert "#1A1A2E" in hex_str or "#1a1a2e" in hex_str.lower()
        assert "#4ECCA3" in hex_str or "#4ecca3" in hex_str.lower()

    def test_detects_inline_spacing(self):
        """Should detect the gap: '24px' and padding inline styles."""
        assert len(self.parsed.inline_spacing) >= 1

    def test_detects_img_tag(self):
        """Should detect the <img> tag without alt."""
        assert len(self.parsed.img_tags) >= 1
        img_str = self.parsed.img_tags[0]
        assert "alt" not in img_str


# ---------------------------------------------------------------------------
# parse_files utility
# ---------------------------------------------------------------------------


class TestParseFiles:
    def test_parses_multiple_files(self):
        code = {
            "Button.tsx": 'const Button = () => <button className="bg-[#ff0000]">Click</button>;',
            "Card.tsx": 'const Card = () => <div style={{color: "blue"}}>Card</div>;',
        }
        results = parse_files(code)
        assert len(results) == 2
        filepaths = [r.filepath for r in results]
        assert "Button.tsx" in filepaths
        assert "Card.tsx" in filepaths

    def test_button_has_arbitrary_color(self):
        code = {"Button.tsx": 'const B = () => <button className="bg-[#ff0000]">Go</button>;'}
        results = parse_files(code)
        assert len(results[0].tailwind_arbitrary_colors) == 1


# ---------------------------------------------------------------------------
# find_line_number utility
# ---------------------------------------------------------------------------


class TestFindLineNumber:
    def test_finds_correct_line(self):
        lines = ["line one", "line two", "bg-[#6366f1] is here", "line four"]
        assert find_line_number(lines, "bg-[#6366f1]") == 3

    def test_returns_none_when_not_found(self):
        lines = ["line one", "line two"]
        assert find_line_number(lines, "not-present") is None

    def test_returns_first_occurrence(self):
        lines = ["duplicate", "other", "duplicate"]
        assert find_line_number(lines, "duplicate") == 1
