"""
Terminal UI & Visual ASCII Dashboard for CLI Execution.
Provides colorized progress displays, status indicators, and clean ASCII tables
for developer experience during terminal scraping sessions.
"""

from __future__ import annotations

import os
import sys
from typing import Any


class TerminalColors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"


class TerminalUI:
    """Renders formatted visual status cards and summary tables in the console."""

    @staticmethod
    def supports_color() -> bool:
        """Check if terminal environment supports ANSI color codes."""
        if os.environ.get("NO_COLOR"):
            return False
        return sys.stdout.isatty() or os.name == "nt"

    @classmethod
    def colorize(cls, text: str, color_code: str) -> str:
        """Wrap text in ANSI color if terminal supports it."""
        if not cls.supports_color():
            return text
        return f"{color_code}{text}{TerminalColors.RESET}"

    @classmethod
    def print_banner(cls, title: str = "The Polite Web Scraper", version: str = "2.0") -> None:
        """Print stylized application banner."""
        cyan = TerminalColors.CYAN
        bold = TerminalColors.BOLD
        reset = TerminalColors.RESET
        border = "=" * 64

        print(cls.colorize(border, cyan))
        print(cls.colorize(f"   ★  {title} v{version}  ★", bold + cyan))
        print(cls.colorize("   Ethical, schema-validated, high-observability crawler", TerminalColors.DIM))
        print(cls.colorize(border, cyan))
        print()

    @classmethod
    def print_stage_header(cls, stage_num: int, title: str) -> None:
        """Print a visually distinct pipeline stage divider."""
        badge = cls.colorize(f"[Stage {stage_num}]", TerminalColors.BOLD + TerminalColors.MAGENTA)
        print(f"\n{badge} {cls.colorize(title, TerminalColors.BOLD)}")
        print(cls.colorize("-" * 64, TerminalColors.DIM))

    @classmethod
    def print_summary_table(cls, stats: dict[str, Any]) -> None:
        """Render a clean summary table of execution metrics."""
        print(cls.colorize("\n┌─ Execution Metrics Summary ──────────────────────────┐", TerminalColors.CYAN))
        for key, val in stats.items():
            formatted_key = key.replace("_", " ").title().ljust(28)
            val_str = str(val).rjust(22)
            print(f"│  {cls.colorize(formatted_key, TerminalColors.DIM)} {cls.colorize(val_str, TerminalColors.BOLD)}  │")
        print(cls.colorize("└──────────────────────────────────────────────────────┘", TerminalColors.CYAN))
