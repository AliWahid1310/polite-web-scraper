"""Tests for the centralized configuration manager (src/config.py)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import ScraperConfig, get_config, reset_config


class TestScraperConfig:
    """Test suite for ScraperConfig dataclass and its helpers."""

    def test_default_values(self):
        """Default configuration should have sensible values."""
        cfg = ScraperConfig()
        assert cfg.base_url == "https://books.toscrape.com/catalogue/page-1.html"
        assert cfg.request_timeout == 10
        assert cfg.politeness_delay == 0.5
        assert cfg.max_catalogue_pages == 3
        assert cfg.rate_limit_rps == 2.0
        assert cfg.server_port == 8080
        assert cfg.log_level == "INFO"

    def test_directories_auto_resolve(self):
        """Cache dir and output dir should auto-resolve relative to project root."""
        cfg = ScraperConfig()
        assert os.path.isabs(cfg.cache_dir)
        assert os.path.isabs(cfg.output_dir)
        assert cfg.cache_dir.endswith("cache")
        assert cfg.output_dir.endswith("output")

    def test_to_dict(self):
        """to_dict() should return a complete dictionary representation."""
        cfg = ScraperConfig()
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert "base_url" in d
        assert "server_port" in d
        assert "export_formats" in d
        assert d["max_catalogue_pages"] == 3

    def test_validate_good_config(self):
        """Default configuration should pass all validation checks."""
        cfg = ScraperConfig()
        issues = cfg.validate()
        assert issues == []

    def test_validate_bad_timeout(self):
        """Invalid timeout should produce a validation issue."""
        cfg = ScraperConfig()
        cfg.request_timeout = 0
        issues = cfg.validate()
        assert any("request_timeout" in i for i in issues)

    def test_validate_bad_port(self):
        """Invalid port should produce a validation issue."""
        cfg = ScraperConfig()
        cfg.server_port = 99999
        issues = cfg.validate()
        assert any("server_port" in i for i in issues)

    def test_validate_bad_url(self):
        """Non-HTTP URL should produce a validation issue."""
        cfg = ScraperConfig()
        cfg.base_url = "ftp://example.com"
        issues = cfg.validate()
        assert any("base_url" in i for i in issues)

    def test_validate_bad_log_level(self):
        """Invalid log level should produce a validation issue."""
        cfg = ScraperConfig()
        cfg.log_level = "VERBOSE"
        issues = cfg.validate()
        assert any("log_level" in i for i in issues)

    def test_env_override_int(self, monkeypatch):
        """Environment variable should override integer settings."""
        monkeypatch.setenv("PSC_REQUEST_TIMEOUT", "30")
        cfg = ScraperConfig()
        assert cfg.request_timeout == 30

    def test_env_override_float(self, monkeypatch):
        """Environment variable should override float settings."""
        monkeypatch.setenv("PSC_POLITENESS_DELAY", "1.5")
        cfg = ScraperConfig()
        assert cfg.politeness_delay == 1.5

    def test_env_override_string(self, monkeypatch):
        """Environment variable should override string settings."""
        monkeypatch.setenv("PSC_LOG_LEVEL", "DEBUG")
        cfg = ScraperConfig()
        assert cfg.log_level == "DEBUG"

    def test_env_override_invalid_int_ignored(self, monkeypatch):
        """Non-numeric env value for int field should be silently ignored."""
        monkeypatch.setenv("PSC_REQUEST_TIMEOUT", "not_a_number")
        cfg = ScraperConfig()
        assert cfg.request_timeout == 10  # default preserved

    def test_export_formats_default(self):
        """Default export formats should include all 4 formats."""
        cfg = ScraperConfig()
        assert "csv" in cfg.export_formats
        assert "markdown" in cfg.export_formats
        assert "ndjson" in cfg.export_formats
        assert "xml" in cfg.export_formats


class TestConfigSingleton:
    """Test the global singleton access pattern."""

    def test_get_config_returns_instance(self):
        reset_config()
        cfg = get_config()
        assert isinstance(cfg, ScraperConfig)

    def test_get_config_is_singleton(self):
        reset_config()
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_reset_clears_singleton(self):
        reset_config()
        cfg1 = get_config()
        reset_config()
        cfg2 = get_config()
        assert cfg1 is not cfg2
