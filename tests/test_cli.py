"""
Unit tests for CLI runner module (src/cli.py).
"""

from src.cli import build_parser


def test_cli_parser_defaults():
    """Test default CLI parser argument values."""
    parser = build_parser()
    args = parser.parse_args([])

    assert args.stage == "all"
    assert args.max_pages == 3
    assert args.no_broken_test is False
    assert "output" in args.output_dir


def test_cli_parser_custom_args():
    """Test parsing custom command-line flags."""
    parser = build_parser()
    args = parser.parse_args(["--stage", "2", "--max-pages", "5", "--no-broken-test", "--output-dir", "custom_out"])

    assert args.stage == "2"
    assert args.max_pages == 5
    assert args.no_broken_test is True
    assert args.output_dir == "custom_out"
