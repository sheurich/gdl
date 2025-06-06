"""Fetch pages from Google Groups using Playwright or requests.

This module provides a Fetcher class that handles polite scraping with
configurable delays, user agent strings, and retry logic. The preferred method
is Playwright for dynamic content, but requests can be used for static pages.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests
from playwright.async_api import async_playwright, Browser, Page

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0 Safari/537.36"
)


@dataclass
class FetcherConfig:
    delay: float = 1.0
    load_wait: float = 2.0
    user_agent: str = DEFAULT_USER_AGENT
    max_retries: int = 3
    headless: bool = True
    timeout: int = 10000  # milliseconds


class Fetcher:
    def __init__(self, config: FetcherConfig | None = None) -> None:
        self.config = config or FetcherConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._browser: Optional[Browser] = None
        self._context = None
        self._playwright = None

    async def __aenter__(self) -> "Fetcher":
        await self._ensure_browser()
        return self
    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _ensure_browser(self) -> None:
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.config.headless)
            self._context = await self._browser.new_context(ignore_https_errors=True, user_agent=self.config.user_agent)
    async def fetch_playwright(self, url: str) -> str:
        await self._ensure_browser()
        assert self._browser is not None
        page: Page = await self._context.new_page()
        retries = 0
        while True:
            try:
                await page.goto(url, timeout=self.config.timeout, wait_until="networkidle")
                await asyncio.sleep(self.config.delay)
                await page.wait_for_timeout(int(self.config.load_wait * 1000))
                content = await page.content()
                await page.close()
                return content
            except Exception as exc:
                retries += 1
                self.logger.warning("Error fetching %s: %s", url, exc)
                if retries >= self.config.max_retries:
                    await page.close()
                    raise
                await asyncio.sleep(self.config.delay * retries)
    def fetch_requests(self, url: str) -> str:
        headers = {"User-Agent": self.config.user_agent}
        retries = 0
        while True:
            try:
                resp = requests.get(url, headers=headers, timeout=self.config.timeout / 1000)
                resp.raise_for_status()
                time.sleep(self.config.delay)
                return resp.text
            except requests.RequestException as exc:
                retries += 1
                self.logger.warning("Error fetching %s: %s", url, exc)
                if retries >= self.config.max_retries:
                    raise
                time.sleep(self.config.delay * retries)

