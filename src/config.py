"""
Centralized Configuration Manager.
Provides a single source of truth for all pipeline settings with support
for environment variable overrides, sensible defaults, and runtime validation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScraperConfig:
    """
    Immutable configuration container for the scraping pipeline.
    Every setting can be overridden via environment variables prefixed with ``PSC_``.
    """

    # Network
    base_url: str = "https://books.toscrape.com/catalogue/page-1.html"
    user_agent: str = (
        "PoliteWebScraper/2.1 "
        "(+https://github.com/AliWahid1310/polite-web-scraper)"
    )
    request_timeout: int = 10
    politeness_delay: float = 0.5
    max_retries: int = 1

    # Crawl scope
    max_catalogue_pages: int = 3
    inject_broken_url: bool = True

    # Rate limiter
    rate_limit_rps: float = 2.0
    rate_limit_burst: int = 5

    # Circuit breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 30.0

    # Cache
    cache_dir: str = ""
    cache_ttl_seconds: int = 86400  # 24 hours
    cache_max_entries: int = 10000

    # Output
    output_dir: str = ""
    export_formats: list[str] = field(default_factory=lambda: ["csv", "markdown", "ndjson", "xml"])

    # Server
    server_host: str = "127.0.0.1"
    server_port: int = 8080

    # Logging
    log_level: str = "INFO"
    log_file: str = ""

    def __post_init__(self) -> None:
        """Resolve directory defaults and apply environment overrides."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if not self.cache_dir:
            self.cache_dir = os.path.join(project_root, "cache")
        if not self.output_dir:
            self.output_dir = os.path.join(project_root, "output")
        if not self.log_file:
            self.log_file = os.path.join(self.output_dir, "scraper.log.jsonl")

        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Read environment variables prefixed with PSC_ and override matching fields."""
        env_map: dict[str, str] = {
            "PSC_BASE_URL": "base_url",
            "PSC_USER_AGENT": "user_agent",
            "PSC_REQUEST_TIMEOUT": "request_timeout",
            "PSC_POLITENESS_DELAY": "politeness_delay",
            "PSC_MAX_RETRIES": "max_retries",
            "PSC_MAX_CATALOGUE_PAGES": "max_catalogue_pages",
            "PSC_RATE_LIMIT_RPS": "rate_limit_rps",
            "PSC_RATE_LIMIT_BURST": "rate_limit_burst",
            "PSC_CIRCUIT_BREAKER_THRESHOLD": "circuit_breaker_threshold",
            "PSC_CIRCUIT_BREAKER_TIMEOUT": "circuit_breaker_timeout",
            "PSC_CACHE_DIR": "cache_dir",
            "PSC_CACHE_TTL": "cache_ttl_seconds",
            "PSC_CACHE_MAX_ENTRIES": "cache_max_entries",
            "PSC_OUTPUT_DIR": "output_dir",
            "PSC_SERVER_HOST": "server_host",
            "PSC_SERVER_PORT": "server_port",
            "PSC_LOG_LEVEL": "log_level",
            "PSC_LOG_FILE": "log_file",
        }

        for env_key, attr_name in env_map.items():
            env_val = os.environ.get(env_key)
            if env_val is None:
                continue

            current_val = getattr(self, attr_name)

            if isinstance(current_val, bool):
                setattr(self, attr_name, env_val.lower() in ("1", "true", "yes"))
            elif isinstance(current_val, int):
                try:
                    setattr(self, attr_name, int(env_val))
                except ValueError:
                    pass
            elif isinstance(current_val, float):
                try:
                    setattr(self, attr_name, float(env_val))
                except ValueError:
                    pass
            else:
                setattr(self, attr_name, env_val)

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to a plain dictionary."""
        return {
            "base_url": self.base_url,
            "user_agent": self.user_agent,
            "request_timeout": self.request_timeout,
            "politeness_delay": self.politeness_delay,
            "max_retries": self.max_retries,
            "max_catalogue_pages": self.max_catalogue_pages,
            "rate_limit_rps": self.rate_limit_rps,
            "rate_limit_burst": self.rate_limit_burst,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "circuit_breaker_timeout": self.circuit_breaker_timeout,
            "cache_dir": self.cache_dir,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cache_max_entries": self.cache_max_entries,
            "output_dir": self.output_dir,
            "export_formats": self.export_formats,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "log_level": self.log_level,
            "log_file": self.log_file,
        }

    def validate(self) -> list[str]:
        """
        Validate configuration constraints and return a list of issues.
        Returns an empty list if configuration is valid.
        """
        issues: list[str] = []

        if self.request_timeout < 1:
            issues.append("request_timeout must be >= 1 second")
        if self.politeness_delay < 0:
            issues.append("politeness_delay must be >= 0")
        if self.max_catalogue_pages < 1:
            issues.append("max_catalogue_pages must be >= 1")
        if self.rate_limit_rps <= 0:
            issues.append("rate_limit_rps must be > 0")
        if self.cache_ttl_seconds < 0:
            issues.append("cache_ttl_seconds must be >= 0")
        if self.server_port < 1 or self.server_port > 65535:
            issues.append("server_port must be between 1 and 65535")
        if not self.base_url.startswith(("http://", "https://")):
            issues.append("base_url must start with http:// or https://")
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            issues.append(f"log_level '{self.log_level}' is not a valid Python logging level")

        return issues


# Singleton default configuration
_default_config: ScraperConfig | None = None


def get_config() -> ScraperConfig:
    """Return the global default configuration (lazy singleton)."""
    global _default_config
    if _default_config is None:
        _default_config = ScraperConfig()
    return _default_config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _default_config
    _default_config = None
