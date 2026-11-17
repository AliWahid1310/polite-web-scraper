"""
Polite HTTP Headers and Self-Identification Manager.
Constructs respectful HTTP request headers that clearly identify the scraper,
provide an honest contact URL, and adhere to web scraping ethics.
"""

from __future__ import annotations

import random
from typing import Any

DEFAULT_REPO_URL = "https://github.com/AliWahid1310/polite-web-scraper"
DEFAULT_BOT_NAME = "PoliteWebScraper"
VERSION = "2.0"


class RespectfulHeaderManager:
    """
    Manages honest HTTP headers and polite bot identification.
    """

    def __init__(
        self,
        bot_name: str = DEFAULT_BOT_NAME,
        version: str = VERSION,
        repo_url: str = DEFAULT_REPO_URL,
    ):
        self.bot_name = bot_name
        self.version = version
        self.repo_url = repo_url

        self._user_agents = [
            f"{self.bot_name}/{self.version} (+{self.repo_url}; python-requests)",
            f"{self.bot_name}/{self.version} (+{self.repo_url}; research-crawler)",
            f"{self.bot_name}/{self.version} (+{self.repo_url}; polite-sandbox-bot)",
        ]

    def get_primary_user_agent(self) -> str:
        """Return the standard primary user-agent string."""
        return self._user_agents[0]

    def get_rotated_user_agent(self) -> str:
        """Return a random polite variant from the self-identifying pool."""
        return random.choice(self._user_agents)

    def get_request_headers(
        self,
        referer: str | None = None,
        custom_ua: str | None = None,
    ) -> dict[str, str]:
        """
        Build a complete dictionary of respectful HTTP headers.
        """
        ua = custom_ua or self.get_primary_user_agent()
        headers: dict[str, str] = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",  # Do Not Track
            "Sec-GPC": "1",  # Global Privacy Control
            "X-Polite-Crawler": f"{self.bot_name} - Ethical Educational Crawl",
        }

        if referer:
            headers["Referer"] = referer

        return headers
