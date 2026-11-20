"""
Unit tests for Terminal UI & Status Display (src/terminal_ui.py).
"""

from src.terminal_ui import TerminalColors, TerminalUI


def test_terminal_ui_supports_color_and_colorize():
    colored = TerminalUI.colorize("Hello", TerminalColors.CYAN)
    assert "Hello" in colored


def test_terminal_ui_print_banner(capsys):
    TerminalUI.print_banner(title="Test Crawler", version="3.0")
    captured = capsys.readouterr()
    assert "Test Crawler v3.0" in captured.out
    assert "Ethical, schema-validated" in captured.out


def test_terminal_ui_print_stage_header(capsys):
    TerminalUI.print_stage_header(stage_num=2, title="Discovery Stage")
    captured = capsys.readouterr()
    assert "[Stage 2]" in captured.out
    assert "Discovery Stage" in captured.out


def test_terminal_ui_summary_table(capsys):
    stats = {"total_scraped": 60, "average_price_gbp": 35.50}
    TerminalUI.print_summary_table(stats)
    captured = capsys.readouterr()
    assert "Execution Metrics Summary" in captured.out
    assert "Total Scraped" in captured.out
    assert "60" in captured.out
